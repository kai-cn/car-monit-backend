"""岗位信息.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysPostController.java

端点清单（7 个映射，全部迁移）
------------------------------------
    ===========================  =======  ==============================  ==========
    Java                          Method   Path                            Access
    ===========================  =======  ==============================  ==========
    ``list(SysPost)``              GET      ``/system/post/list``           list
    ``export(SysPost)``            GET      ``/system/post/export``         export
    ``getInfo(Long)``              GET      ``/system/post/{postId}``       query
    ``add(SysPost)``               POST     ``/system/post``                add
    ``edit(SysPost)``              PUT      ``/system/post``                edit
    ``remove(Long[])``             DELETE   ``/system/post/{postIds}``      remove
    ``optionselect()``             GET      ``/system/post/optionselect``   登录
    ===========================  =======  ==============================  ==========

``export`` 返回的是**文件名**，不是文件内容
---------------------------------------------
Java 是 ``return util.exportExcel(list, "岗位数据")``，``AjaxResult.success(filename)``
命中 ``success(String)`` 重载，于是文件名落在 ``msg``（**不是** ``data``）：
``{"code": 200, "msg": "<uuid>_岗位数据.xlsx"}``。文件本身写到
``{ruoyi.profile}/download/``，需要再调 ``GET /common/download`` 才拿到字节。

不分页：Java 侧 ``export`` 直接调 ``selectPostList``，没有 ``startPage()``，
所以导出的是符合条件全量数据。

``@Log(...)`` 注解
------------------------
``add`` / ``edit`` / ``remove`` / ``export`` 带 ``@Log(title = "岗位管理", ...)``，
由 :mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``：``businessType``
依次是 ``INSERT`` / ``UPDATE`` / ``DELETE`` / ``EXPORT``，``method`` 列取本模块
``JAVA_CONTROLLER`` 声明的 Java 全类名。见 ``COMPATIBILITY.md`` §25。

``@Validated @RequestBody`` 与 ``@PreAuthorize`` 的先后
-------------------------------------------------------
Spring MVC 先解析参数（触发 Hibernate Validator），**再**进入 ``@PreAuthorize``
的方法代理，所以顺序是::

    安全过滤器链(401) -> 路由 -> 反序列化+校验(500) -> @PreAuthorize(403) -> 方法体

把校验写成方法体的第一条语句很容易，但那样就变成了"没权限的人先撞 403" ——
``pre_authorize_permi`` 装饰器的检查在函数体之前执行，永远等不到那句校验。
这里把校验做成 FastAPI 的 ``Depends``（:data:`ValidPost`），依赖在端点函数体之前解析，
顺序与 Spring 一致。:class:`app.common.utils.bean_validation.BeanValidationError`
继承 ``RuntimeError``，落到通用处理器后是 ``{"code": 500, "msg": "岗位编码不能为空"}``。

路由声明顺序
------------
``/list`` 与 ``/optionselect`` 必须写在 ``/{post_id}`` 之前：FastAPI 按注册顺序匹配，
否则 ``GET /system/post/list`` 会被当成 ``post_id = "list"``。Spring 的
``AntPathMatcher`` 本来就优先字面量，两者结果一致。``/export`` 同理。

文案里的坑
----------
``add`` / ``edit`` 的"编码已存在"提示里插的是 **岗位名称**（``post.getPostName()``），
不是编码 —— Java 源码就是这样的，别"修正"。
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
    to_ajax,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.bean_validation import validate
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.domain.sys_post import POST_CONSTRAINTS, SysPost
from app.system.service.sys_post_service import SysPostService, get_post_service

logger = logging.getLogger("app.api.system.sys_post_controller")

router = APIRouter(prefix="/system/post", tags=["system-post"])

#: Java: ``com.ruoyi.web.controller.system.SysPostController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysPostController"

#: Java: ``新增岗位'" + post.getPostName() + "'失败，岗位名称已存在``
ADD_POST_NAME_EXISTS = "新增岗位'{}'失败，岗位名称已存在"
#: Java: ``新增岗位'" + post.getPostName() + "'失败，岗位编码已存在``（插的确实是名称）
ADD_POST_CODE_EXISTS = "新增岗位'{}'失败，岗位编码已存在"
#: Java: ``修改岗位'" + post.getPostName() + "'失败，岗位名称已存在``
EDIT_POST_NAME_EXISTS = "修改岗位'{}'失败，岗位名称已存在"
#: Java: ``修改岗位'" + post.getPostName() + "'失败，岗位编码已存在``
EDIT_POST_CODE_EXISTS = "修改岗位'{}'失败，岗位编码已存在"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysPostService postService``。Spring 默认单例，
# 这里用模块级缓存复刻；测试直接替换 ``controller._POST_SERVICE``。

_POST_SERVICE: Optional[SysPostService] = None


def _post_service() -> SysPostService:
    global _POST_SERVICE
    if _POST_SERVICE is None:
        _POST_SERVICE = get_post_service()
    return _POST_SERVICE


def reset_post_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _POST_SERVICE
    _POST_SERVICE = None


def _query_post(request: Request) -> SysPost:
    """Java: 形参 ``SysPost post``（**没有** ``@RequestBody``）—— 由 query string 绑定。"""
    return bind_query_params(SysPost, request.query_params)


#: 查询条件实体（``?postCode=...&status=...``）。
PostParam = Annotated[SysPost, Depends(_query_post)]


def _validated_post(post: SysPost) -> SysPost:
    """Java: ``@Validated @RequestBody SysPost``.

    做成 ``Depends`` 而不是函数体第一行，是为了让校验排在 ``@PreAuthorize`` 之前 ——
    见模块 docstring 的"先后"一节。约束表来自实体旁边，与 Java 注解同位置。
    """
    validate(post, POST_CONSTRAINTS)
    return post


#: 已校验的请求体。
ValidPost = Annotated[SysPost, Depends(_validated_post)]


def _is_not_unique(result: str) -> bool:
    """Java: ``UserConstants.NOT_UNIQUE_OLD.equals(...)``。

    ``NOT_UNIQUE_OLD`` 是字面量 ``"1"``，``UNIQUE_OLD`` 是 ``"0"``
    （见 :mod:`app.common.constant.user_constants`）。
    """
    from app.common.constant.user_constants import NOT_UNIQUE_OLD

    return NOT_UNIQUE_OLD == result


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("system:post:list")
def list_posts(post: PostParam) -> TableDataInfo:
    """获取岗位列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysPost post)``."""
    start_page()
    rows = _post_service().select_post_list(post)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("system:post:export")
@log(title="岗位管理", business_type=BusinessType.EXPORT, java_method="export")
def export(post: PostParam) -> AjaxResult:
    """导出岗位数据. Java: ``@GetMapping("/export") public AjaxResult export(SysPost post)``.

    ``msg`` 是生成的文件名（不是文件内容），见模块 docstring。
    """
    rows = _post_service().select_post_list(post)
    return ExcelUtil(SysPost).export_excel(rows, "岗位数据")


@router.get("/optionselect", response_model=None)
def optionselect() -> AjaxResult:
    """获取岗位选择框列表. Java: ``@GetMapping("/optionselect")``.

    没有 ``@PreAuthorize``，只要求登录；返回**全量**岗位（不分页）。
    """
    return AjaxResult.success_data(_post_service().select_post_all())


@router.get("/{post_id}", response_model=None)
@pre_authorize_permi("system:post:query")
def get_info(post_id: int) -> AjaxResult:
    """根据岗位编号获取详细信息.

    Java: ``@GetMapping(value = "/{postId}")`` —— ``value`` 是单值，没有尾斜杠变体。
    """
    return AjaxResult.success_data(_post_service().select_post_by_id(post_id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:post:add")
@log(title="岗位管理", business_type=BusinessType.INSERT, java_method="add")
def add(post: ValidPost) -> AjaxResult:
    """新增岗位. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysPost post)``."""
    if _is_not_unique(_post_service().check_post_name_unique(post)):
        return AjaxResult.error_message(ADD_POST_NAME_EXISTS.format(post.post_name))
    elif _is_not_unique(_post_service().check_post_code_unique(post)):
        return AjaxResult.error_message(ADD_POST_CODE_EXISTS.format(post.post_name))
    post.create_by = SecurityUtils.get_username()
    return to_ajax(_post_service().insert_post(post))


@router.put("", response_model=None)
@pre_authorize_permi("system:post:edit")
@log(title="岗位管理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(post: ValidPost) -> AjaxResult:
    """修改岗位. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysPost post)``."""
    if _is_not_unique(_post_service().check_post_name_unique(post)):
        return AjaxResult.error_message(EDIT_POST_NAME_EXISTS.format(post.post_name))
    elif _is_not_unique(_post_service().check_post_code_unique(post)):
        return AjaxResult.error_message(EDIT_POST_CODE_EXISTS.format(post.post_name))
    post.update_by = SecurityUtils.get_username()
    return to_ajax(_post_service().update_post(post))


@router.delete("/{post_ids}", response_model=None)
@pre_authorize_permi("system:post:remove")
@log(title="岗位管理", business_type=BusinessType.DELETE, java_method="remove")
def remove(post_ids: str) -> AjaxResult:
    """删除岗位. Java: ``@DeleteMapping("/{postIds}") public AjaxResult remove(@PathVariable Long[] postIds)``.

    "已分配给用户"时 Service 抛 ``CustomException`` -> HTTP 200 + ``code 500`` +
    ``"xx已分配,不能删除"``，整批都不删。
    """
    return to_ajax(_post_service().delete_post_by_ids(parse_id_array(post_ids)))


__all__ = [
    "router",
    "ADD_POST_NAME_EXISTS",
    "ADD_POST_CODE_EXISTS",
    "EDIT_POST_NAME_EXISTS",
    "EDIT_POST_CODE_EXISTS",
    "PostParam",
    "ValidPost",
    "list_posts",
    "export",
    "optionselect",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_post_controller",
]
