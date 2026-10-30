"""数据字典信息 —— 字典类型.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictTypeController.java

端点清单（8 个映射，全部迁移）
------------------------------
    ===========================  =======  ==================================  ==========
    Java                          Method   Path                                Access
    ===========================  =======  ==================================  ==========
    ``list(SysDictType)``          GET      ``/system/dict/type/list``          dict:list
    ``export(SysDictType)``        GET      ``/system/dict/type/export``        dict:export
    ``getInfo(Long)``              GET      ``/system/dict/type/{dictId}``      dict:query
    ``add(SysDictType)``           POST     ``/system/dict/type``               dict:add
    ``edit(SysDictType)``          PUT      ``/system/dict/type``               dict:edit
    ``remove(Long[])``             DELETE   ``/system/dict/type/{dictIds}``     dict:remove
    ``clearCache()``               DELETE   ``/system/dict/type/clearCache``    dict:remove
    ``optionselect()``             GET      ``/system/dict/type/optionselect``  登录
    ===========================  =======  ==================================  ==========

计数说明：``SysDictTypeController`` 源码里是 **8** 个 ``@XxxMapping``（不是 10 个）。
早前 ``MIGRATION_PROGRESS.md`` §2.2 里写的 10 是把 ``SysDictDataController`` 的
2 个额外映射（``/type/{dictType}``、``/typemore/{dictType}``）算重复了。

``export`` 返回的是**文件名**，不是文件内容
---------------------------------------------
Java 是 ``return util.exportExcel(list, "字典类型")``，``AjaxResult.success(filename)``
命中 ``success(String)`` 重载，于是文件名落在 ``msg``（**不是** ``data``）：
``{"code": 200, "msg": "<uuid>_字典类型.xlsx"}``。文件本身写到
``{ruoyi.profile}/download/``，需要再调 ``GET /common/download`` 才拿到字节。

导出不分页：Java 侧直接调 ``selectDictTypeList``，没有 ``startPage()``。

``@Log(...)`` 注解
------------------------
``export`` / ``add`` / ``edit`` / ``remove`` / ``clearCache`` 带
``@Log(title = "字典类型", ...)``，由 :mod:`app.framework.aspectj.log_aspect` 异步写
``sys_oper_log``：``businessType`` 依次是 ``EXPORT`` / ``INSERT`` / ``UPDATE`` /
``DELETE`` / ``CLEAN``。``clearCache`` 的 ``CLEAN`` 这个枚举值在整个 Java 工程里
只在这一处出现。

``clearCache`` 与 ``/{dictIds}`` 的注册顺序
-------------------------------------------
两个都是 ``DELETE``，一个是一段字面量、一个是单段变量。Spring 的
``AntPathMatcher`` 优先字面量，FastAPI 按**注册顺序**匹配 —— 所以
``/clearCache`` 必须写在 ``/{dict_ids}`` 之前，否则会被当成
``dict_ids = "clearCache"`` 而在 ``parse_id_array`` 处抛错。
同理 ``/export`` / ``/list`` / ``/optionselect`` 都必须在 ``/{dict_id}`` 之前。

``add`` / ``edit`` 的唯一性校验在写库之前
-----------------------------------------
``checkDictTypeUnique`` 返回 ``"1"``（已存在）时直接 ``AjaxResult.error(...)``，
**HTTP 200 + code 500**，且**不写库**。文案插的是 ``dictName``（字典名称），不是
``dictType`` —— 提示"字典类型已存在"但显示的是名称，Java 原文如此，别"修正"。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.common.constant.user_constants import NOT_UNIQUE_OLD
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
    to_ajax,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_dict_type import DICT_TYPE_CONSTRAINTS, SysDictType
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.bean_validation import validate
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.service.sys_dict_type_service import SysDictTypeService, get_dict_type_service

router = APIRouter(prefix="/system/dict/type", tags=["system-dict-type"])

#: Java: ``com.ruoyi.web.controller.system.SysDictTypeController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysDictTypeController"

#: Java: ``"新增字典'" + dict.getDictName() + "'失败，字典类型已存在"``
ADD_DICT_TYPE_EXISTS = "新增字典'{}'失败，字典类型已存在"
#: Java: ``"修改字典'" + dict.getDictName() + "'失败，字典类型已存在"``
EDIT_DICT_TYPE_EXISTS = "修改字典'{}'失败，字典类型已存在"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysDictTypeService dictTypeService``。Spring 默认单例，
# 这里用模块级缓存复刻；测试直接替换 ``controller._DICT_TYPE_SERVICE``。

_DICT_TYPE_SERVICE: Optional[SysDictTypeService] = None


def _dict_type_service() -> SysDictTypeService:
    global _DICT_TYPE_SERVICE
    if _DICT_TYPE_SERVICE is None:
        _DICT_TYPE_SERVICE = get_dict_type_service()
    return _DICT_TYPE_SERVICE


def reset_dict_type_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _DICT_TYPE_SERVICE
    _DICT_TYPE_SERVICE = None


def _query_dict_type(request: Request) -> SysDictType:
    """Java: 形参 ``SysDictType dictType``（**没有** ``@RequestBody``）—— query string 绑定。"""
    return bind_query_params(SysDictType, request.query_params)


#: 查询条件实体（``?dictName=...&status=...&params[beginTime]=...``）。
DictTypeParam = Annotated[SysDictType, Depends(_query_dict_type)]


def _validated_dict_type(dict_type: SysDictType) -> SysDictType:
    """Java: ``@Validated @RequestBody SysDictType``.

    做成 ``Depends`` 而不是函数体第一行，是为了让校验排在 ``@PreAuthorize`` **之前** ——
    Spring MVC 先解析/校验参数，再进入方法代理，顺序见
    :mod:`app.api.system.sys_post_controller` 的模块 docstring。
    """
    validate(dict_type, DICT_TYPE_CONSTRAINTS)
    return dict_type


#: 已校验的请求体。
ValidDictType = Annotated[SysDictType, Depends(_validated_dict_type)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("system:dict:list")
def list_dict_types(dict_type: DictTypeParam) -> TableDataInfo:
    """获取字典类型列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysDictType dictType)``."""
    start_page()
    rows = _dict_type_service().select_dict_type_list(dict_type)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("system:dict:export")
@log(title="字典类型", business_type=BusinessType.EXPORT, java_method="export")
def export(dict_type: DictTypeParam) -> AjaxResult:
    """导出字典类型. Java: ``@GetMapping("/export") public AjaxResult export(SysDictType dictType)``.

    ``msg`` 是生成的文件名（不是文件内容），见模块 docstring。
    权限点与 ``SysDictDataController#export`` 共用 ``system:dict:export``。
    """
    rows = _dict_type_service().select_dict_type_list(dict_type)
    return ExcelUtil(SysDictType).export_excel(rows, "字典类型")


@router.get("/optionselect", response_model=None)
def optionselect() -> AjaxResult:
    """获取字典类型选择框列表. Java: ``@GetMapping("/optionselect")``.

    没有 ``@PreAuthorize``，登录即可；返回**全量**类型（不分页，按 ``create_time`` 倒序）。
    前端"字典类型"下拉框用它 —— 注意它读的是**库**，不是缓存。
    """
    return AjaxResult.success_data(_dict_type_service().select_dict_type_all())


@router.get("/{dict_id}", response_model=None)
@pre_authorize_permi("system:dict:query")
def get_info(dict_id: int) -> AjaxResult:
    """查询字典类型详细. Java: ``@GetMapping(value = "/{dictId}")``.

    查不到时 ``data`` 为 ``null``（不是 404）。
    """
    return AjaxResult.success_data(_dict_type_service().select_dict_type_by_id(dict_id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:dict:add")
@log(title="字典类型", business_type=BusinessType.INSERT, java_method="add")
def add(dict_type: ValidDictType) -> AjaxResult:
    """新增字典类型. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysDictType dict)``.

    唯一性校验失败时返回 ``AjaxResult.error(...)``（HTTP 200 + code 500），**不写库**。
    """
    if NOT_UNIQUE_OLD == _dict_type_service().check_dict_type_unique(dict_type):
        return AjaxResult.error_message(ADD_DICT_TYPE_EXISTS.format(dict_type.dict_name))
    dict_type.create_by = SecurityUtils.get_username()
    return to_ajax(_dict_type_service().insert_dict_type(dict_type))


@router.put("", response_model=None)
@pre_authorize_permi("system:dict:edit")
@log(title="字典类型", business_type=BusinessType.UPDATE, java_method="edit")
def edit(dict_type: ValidDictType) -> AjaxResult:
    """修改字典类型. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysDictType dict)``.

    Service 会**先**用旧类型名把所有子项改成新名字，再改主表（Java 带 ``@Transactional``，
    Python 侧没有事务，见 ``COMPATIBILITY.md`` §32）。
    """
    if NOT_UNIQUE_OLD == _dict_type_service().check_dict_type_unique(dict_type):
        return AjaxResult.error_message(EDIT_DICT_TYPE_EXISTS.format(dict_type.dict_name))
    dict_type.update_by = SecurityUtils.get_username()
    return to_ajax(_dict_type_service().update_dict_type(dict_type))


@router.delete("/clearCache", response_model=None)
@pre_authorize_permi("system:dict:remove")
@log(title="字典类型", business_type=BusinessType.CLEAN, java_method="clearCache")
def clear_cache() -> AjaxResult:
    """清空缓存. Java: ``@DeleteMapping("/clearCache")``.

    只删 Redis 里的 ``sys_dict:*``，**不动库**。下一次读字典会回源重新填充。
    必须注册在 ``/{dict_ids}`` 之前。
    """
    _dict_type_service().clear_cache()
    return AjaxResult.success()


@router.delete("/{dict_ids}", response_model=None)
@pre_authorize_permi("system:dict:remove")
@log(title="字典类型", business_type=BusinessType.DELETE, java_method="remove")
def remove(dict_ids: str) -> AjaxResult:
    """删除字典类型. Java: ``@DeleteMapping("/{dictIds}") public AjaxResult remove(@PathVariable Long[] dictIds)``.

    类型下还有字典数据时 Service 抛 ``CustomException("xx已分配,不能删除")`` ->
    HTTP 200 + code 500，**整批都不删**。
    """
    return to_ajax(_dict_type_service().delete_dict_type_by_ids(parse_id_array(dict_ids)))


__all__ = [
    "router",
    "ADD_DICT_TYPE_EXISTS",
    "EDIT_DICT_TYPE_EXISTS",
    "DictTypeParam",
    "ValidDictType",
    "list_dict_types",
    "optionselect",
    "get_info",
    "add",
    "edit",
    "clear_cache",
    "remove",
    "reset_dict_type_controller",
]
