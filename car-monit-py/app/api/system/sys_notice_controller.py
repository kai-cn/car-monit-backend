"""通知公告.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysNoticeController.java

端点清单（7 个映射，**全部迁移** —— 本切片没有 ``export``）
-----------------------------------------------------------
    ============================  =======  ==================================  ==============
    Java                           Method   Path                                Access
    ============================  =======  ==================================  ==============
    ``list(SysNotice)``            GET      ``/system/notice/list``             登录（*）
    ``listquery(SysNotice)``       GET      ``/system/notice/listquery``        登录（*）
    ``getInfo(Long)``              GET      ``/system/notice/{noticeId}``       登录
    ``getViewInfo(Long)``          GET      ``/system/notice/view/{noticeId}``  **匿名**
    ``add(SysNotice)``             POST     ``/system/notice``                  add
    ``edit(SysNotice)``            PUT      ``/system/notice``                  edit
    ``remove(Long[])``             DELETE   ``/system/notice/{noticeIds}``      remove
    ============================  =======  ==================================  ==============

只有 **3 个**权限点（``add`` / ``edit`` / ``remove``）。``list`` 上的
``@PreAuthorize("@ss.hasPermi('system:notice:list')")`` 在 Java 源码里是**注释掉的**，
``listquery`` / ``getInfo`` 本来就没有注解 —— 三者都只靠 ``anyRequest().authenticated()``
兜底，所以"登录即可"。不要"顺手"补权限点，那会让普通角色打不开公告页面。

``/view/{noticeId}`` 是匿名端点
-------------------------------
:class:`app.framework.config.security_config` 的规则表里有
``/system/notice/view/**`` -> ``AccessMode.ANONYMOUS``，与
``SecurityConfig.java`` 的 ``.antMatchers("/system/notice/view/**").anonymous()`` 一一对应。

``anonymous()`` 的含义是"**只**允许匿名"：已登录的请求会被判 **403**（不是放过）。
所以这个端点前端只在"未登录查看公告详情"的场景下用；已登录时请走 ``/{noticeId}``。

``listquery`` 与 ``list`` 的唯一差别
-----------------------------------
``listquery`` 在 ``startPage()`` 之后、查库之前**强制** ``notice.setStatus("0")``，
也就是"只看正常状态的公告"。两行顺序不能换 —— 若先写 ``status`` 再 ``startPage()``，
结果一样，但源码就是"先分页后覆盖"的顺序，保持一致便于 diff。

注意它**不会**清掉客户端传的其它条件：``?status=1`` 会被请求绑定先写成 ``"1"``，
再被这一行覆盖成 ``"0"``。

``@Validated`` 实际什么都不做
-----------------------------
``add`` / ``edit`` 上有 ``@Validated @RequestBody``，但 :class:`SysNotice` 实体
**一个约束注解都没有**（没有 ``@NotBlank`` / ``@Size``），所以 Hibernate Validator
放行一切 —— 空标题、超长标题都能入库。这里因此**没有** ``ValidNotice`` 依赖，
``notice`` 直接作为请求体绑定，与 Java 行为一致。见 ``COMPATIBILITY.md`` §31.3。

``@Log(...)`` 注解
------------------------
``add`` / ``edit`` / ``remove`` 带 ``@Log(title = "通知公告", ...)``，由
:mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``：``businessType`` 依次是
``INSERT`` / ``UPDATE`` / ``DELETE``。见 ``COMPATIBILITY.md`` §31.2。

路由声明顺序
------------
``/list`` / ``/listquery`` / ``/view/{notice_id}`` 必须写在 ``/{notice_id}`` **之前**：
FastAPI 按注册顺序匹配。 ``/list`` 这类字面量若排在后面，会被当成
``notice_id = "list"`` 而在 ``int`` 转换处 422。Spring 的 ``AntPathMatcher``
本来就优先字面量，两者最终结果一致。
"""

from __future__ import annotations

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
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.domain.sys_notice import SysNotice
from app.system.service.sys_notice_service import SysNoticeService, get_notice_service

router = APIRouter(prefix="/system/notice", tags=["system-notice"])

#: Java: ``com.ruoyi.web.controller.system.SysNoticeController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysNoticeController"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysNoticeService noticeService``。Spring 默认单例，
# 这里用模块级缓存复刻；测试直接替换 ``controller._NOTICE_SERVICE``。

_NOTICE_SERVICE: Optional[SysNoticeService] = None


def _notice_service() -> SysNoticeService:
    global _NOTICE_SERVICE
    if _NOTICE_SERVICE is None:
        _NOTICE_SERVICE = get_notice_service()
    return _NOTICE_SERVICE


def reset_notice_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _NOTICE_SERVICE
    _NOTICE_SERVICE = None


def _query_notice(request: Request) -> SysNotice:
    """Java: 形参 ``SysNotice notice``（**没有** ``@RequestBody``）—— 由 query string 绑定。"""
    return bind_query_params(SysNotice, request.query_params)


#: 查询条件实体（``?noticeTitle=...&status=...``）。
NoticeParam = Annotated[SysNotice, Depends(_query_notice)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
def list_notices(notice: NoticeParam) -> TableDataInfo:
    """获取通知公告列表. Java: ``@GetMapping("/list")``.

    ``@PreAuthorize`` 在 Java 里是注释掉的 -> 登录即可，**没有**权限点。
    """
    start_page()
    rows = _notice_service().select_notice_list(notice)
    return get_data_table(rows)


@router.get("/listquery", response_model=None)
def listquery(notice: NoticeParam) -> TableDataInfo:
    """获取通知公告列表（只含 ``status = "0"``）. Java: ``@GetMapping("/listquery")``.

    ``status`` 的覆盖发生在 ``startPage()`` **之后**、查库之前，照抄源码顺序。
    """
    start_page()
    notice.status = "0"
    rows = _notice_service().select_notice_list(notice)
    return get_data_table(rows)


@router.get("/view/{notice_id}", response_model=None)
def get_view_info(notice_id: int) -> AjaxResult:
    """根据通知公告编号获取详细信息（不需要登录）. Java: ``@GetMapping("/view/{noticeId}")``.

    安全过滤器把它归入 ``/system/notice/view/**`` -> ``anonymous()``：匿名放行、
    已登录反而 403。与 ``/{noticeId}`` 查的是同一个 service 方法，响应体完全相同。
    """
    return AjaxResult.success_data(_notice_service().select_notice_by_id(notice_id))


@router.get("/{notice_id}", response_model=None)
def get_info(notice_id: int) -> AjaxResult:
    """根据通知公告编号获取详细信息. Java: ``@GetMapping(value = "/{noticeId}")``.

    没有 ``@PreAuthorize``，登录即可；查不到时 ``data`` 为 ``null``（不是 404）。
    """
    return AjaxResult.success_data(_notice_service().select_notice_by_id(notice_id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:notice:add")
@log(title="通知公告", business_type=BusinessType.INSERT, java_method="add")
def add(notice: SysNotice) -> AjaxResult:
    """新增通知公告. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysNotice notice)``.

    这里写 ``createBy = userName``，但紧接着 Service 的 ``insertNotice`` 会用
    ``userId`` **覆盖**它；``noticeType`` 也会被强制成 ``"1"``。
    两句都是 Java 原样，见 :mod:`app.system.service.sys_notice_service`。
    """
    notice.create_by = SecurityUtils.get_username()
    return to_ajax(_notice_service().insert_notice(notice))


@router.put("", response_model=None)
@pre_authorize_permi("system:notice:edit")
@log(title="通知公告", business_type=BusinessType.UPDATE, java_method="edit")
def edit(notice: SysNotice) -> AjaxResult:
    """修改通知公告. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysNotice notice)``.

    ``updateBy = userName`` 同样会被 Service 覆盖成 ``userId``。
    """
    notice.update_by = SecurityUtils.get_username()
    return to_ajax(_notice_service().update_notice(notice))


@router.delete("/{notice_ids}", response_model=None)
@pre_authorize_permi("system:notice:remove")
@log(title="通知公告", business_type=BusinessType.DELETE, java_method="remove")
def remove(notice_ids: str) -> AjaxResult:
    """删除通知公告. Java: ``@DeleteMapping("/{noticeIds}") public AjaxResult remove(@PathVariable Long[] noticeIds)``.

    逗号串 -> ``Long[]``（``parse_id_array``）。物理删除，没有回收站。
    """
    return to_ajax(_notice_service().delete_notice_by_ids(parse_id_array(notice_ids)))


__all__ = [
    "router",
    "NoticeParam",
    "list_notices",
    "listquery",
    "get_view_info",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_notice_controller",
]
