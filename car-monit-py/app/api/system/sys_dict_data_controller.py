"""数据字典信息 —— 字典数据.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictDataController.java

端点清单（8 个映射，全部迁移）
------------------------------
    ==============================  =======  ====================================  ==========
    Java                             Method   Path                                  Access
    ==============================  =======  ====================================  ==========
    ``list(SysDictData)``            GET      ``/system/dict/data/list``            dict:list
    ``export(SysDictData)``          GET      ``/system/dict/data/export``          dict:export
    ``getInfo(Long)``                GET      ``/system/dict/data/{dictCode}``      dict:query
    ``dictType(String)``             GET      ``/system/dict/data/type/{dictType}`` 登录
    ``dictTypeMore(String)``         GET      ``/system/dict/data/typemore/{dictType}`` 登录
    ``add(SysDictData)``             POST     ``/system/dict/data``                 dict:add
    ``edit(SysDictData)``            PUT      ``/system/dict/data``                 dict:edit
    ``remove(Long[])``               DELETE   ``/system/dict/data/{dictCodes}``     dict:remove
    ==============================  =======  ====================================  ==========

``/type/{dictType}`` 与 ``/typemore/{dictType}`` 是**两段**路径
----------------------------------------------------------------
所以它们不会被单段的 ``/{dictCode}`` 吃掉（Spring 和 FastAPI 都不会）。但按"字面量
在前"的统一规则，仍然写在 ``/{dict_code}`` 之前 —— 与
:mod:`app.api.system.sys_notice_controller` 的处理方式一致。``/export`` 同理。

这两个端点**没有权限点**，登录即可 —— 前端每个页面都会调它们，加权限会白屏。

``/type/{dictType}`` 走缓存，``/typemore`` 也走缓存（但缓存键是原始入参）
-----------------------------------------------------------------------
两者都委托给 :class:`~app.system.service.sys_dict_type_service.SysDictTypeService`
（注意**不是** ``SysDictDataService``）。这个交叉依赖是 Java 原样：
``SysDictDataController`` 注入了 ``ISysDictDataService`` 和 ``ISysDictTypeService``
两个 bean。

``null`` 变空数组
-----------------
Service 未命中时返回 ``None``，控制器用 ``StringUtils.isNull(data)`` 换成
``new ArrayList<>()``。所以 ``/type/{dictType}`` 永远给客户端 ``"data": []`` 而不是
``"data": null``（也不会像 ``AjaxResult.success(null)`` 那样**整个 data 键消失**）。

``/typemore`` 的 ``null`` 还会被分组
-----------------------------------
Java 是先把 ``null`` 换成空 List，**再** ``collect(groupingBy(...))``：
``Collections.emptyList().stream().collect(groupingBy(x -> x.getDictType()))`` 得到空
``HashMap``，所以未命中时 ``/typemore`` 回的是 ``"data": {}`` 而不是 ``"data": []``。
"null 变空数组" 这一步在 ``/typemore`` 上其实被分组吞掉了。

``/typemore`` 额外做了一次分组
------------------------------
``data.stream().collect(Collectors.groupingBy(SysDictData::getDictType))`` ->
``Map<String, List<SysDictData>>``，响应体形如::

    {"msg":"操作成功","code":200,"data":{"car_type":[{...},{...}],"plate_color":[{...}]}}

Java 的 ``groupingBy`` 默认用 ``HashMap``，**键顺序不确定**；Python 的 ``dict``
保留"首次出现"的顺序，而 SQL 自带 ``order by dict_type,dict_sort asc``，所以
Python 侧的顺序是确定的字典序。这属于"更可预期"而不是行为差异，见 §32。

``export`` 返回的是**文件名**，不是文件内容
---------------------------------------------
Java 是 ``return util.exportExcel(list, "字典数据")``，``AjaxResult.success(filename)``
命中 ``success(String)`` 重载，于是文件名落在 ``msg``（**不是** ``data``）：
``{"code": 200, "msg": "<uuid>_字典数据.xlsx"}``。文件本身写到
``{ruoyi.profile}/download/``，需要再调 ``GET /common/download`` 才拿到字节。

导出不分页：Java 侧直接调 ``selectDictDataList``，没有 ``startPage()``。
权限点 ``system:dict:export`` 与 ``SysDictTypeController#export`` 共用。

``@Log(...)`` 注解
------------------------
``add`` / ``edit`` / ``remove`` / ``export`` 带 ``@Log``，由
:mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``：``businessType`` 依次是
``INSERT`` / ``UPDATE`` / ``DELETE`` / ``EXPORT``。
注意 ``remove`` 上的注解写的是 ``@Log(title = "字典类型", ...)`` —— 而本类叫"字典数据"，
是 Java 的复制粘贴笔误，操作日志里会显示"字典类型"。照抄。
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
    to_ajax,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_dict_data import DICT_DATA_CONSTRAINTS, SysDictData
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.bean_validation import validate
from app.common.utils.poi.excel_util import ExcelUtil
from app.common.utils.string_utils import is_null
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.service.sys_dict_data_service import SysDictDataService, get_dict_data_service
from app.system.service.sys_dict_type_service import SysDictTypeService, get_dict_type_service

router = APIRouter(prefix="/system/dict/data", tags=["system-dict-data"])

#: Java: ``com.ruoyi.web.controller.system.SysDictDataController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysDictDataController"


# --------------------------------------------------------------------------- 依赖
#
# Java 注入了两个 bean：``dictDataService`` + ``dictTypeService``。
# 模块级缓存复刻 Spring 的单例；测试直接替换 ``_DICT_DATA_SERVICE`` / ``_DICT_TYPE_SERVICE``。

_DICT_DATA_SERVICE: Optional[SysDictDataService] = None
_DICT_TYPE_SERVICE: Optional[SysDictTypeService] = None


def _dict_data_service() -> SysDictDataService:
    global _DICT_DATA_SERVICE
    if _DICT_DATA_SERVICE is None:
        _DICT_DATA_SERVICE = get_dict_data_service()
    return _DICT_DATA_SERVICE


def _dict_type_service() -> SysDictTypeService:
    global _DICT_TYPE_SERVICE
    if _DICT_TYPE_SERVICE is None:
        _DICT_TYPE_SERVICE = get_dict_type_service()
    return _DICT_TYPE_SERVICE


def reset_dict_data_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _DICT_DATA_SERVICE, _DICT_TYPE_SERVICE
    _DICT_DATA_SERVICE = None
    _DICT_TYPE_SERVICE = None


def _query_dict_data(request: Request) -> SysDictData:
    """Java: 形参 ``SysDictData dictData``（**没有** ``@RequestBody``）—— query string 绑定。"""
    return bind_query_params(SysDictData, request.query_params)


#: 查询条件实体（``?dictType=...&dictLabel=...&status=...``）。
DictDataParam = Annotated[SysDictData, Depends(_query_dict_data)]


def _validated_dict_data(dict_data: SysDictData) -> SysDictData:
    """Java: ``@Validated @RequestBody SysDictData`` —— 校验排在 ``@PreAuthorize`` 之前。"""
    validate(dict_data, DICT_DATA_CONSTRAINTS)
    return dict_data


#: 已校验的请求体。
ValidDictData = Annotated[SysDictData, Depends(_validated_dict_data)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("system:dict:list")
def list_dict_data(dict_data: DictDataParam) -> TableDataInfo:
    """获取字典数据列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysDictData dictData)``."""
    start_page()
    rows = _dict_data_service().select_dict_data_list(dict_data)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("system:dict:export")
@log(title="字典数据", business_type=BusinessType.EXPORT, java_method="export")
def export(dict_data: DictDataParam) -> AjaxResult:
    """导出字典数据. Java: ``@GetMapping("/export") public AjaxResult export(SysDictData dictData)``.

    ``msg`` 是生成的文件名（不是文件内容），见模块 docstring。
    """
    rows = _dict_data_service().select_dict_data_list(dict_data)
    return ExcelUtil(SysDictData).export_excel(rows, "字典数据")


@router.get("/type/{dict_type}", response_model=None)
def dict_type(dict_type: str) -> AjaxResult:
    """根据字典类型查询字典数据. Java: ``@GetMapping(value = "/type/{dictType}")``.

    没有 ``@PreAuthorize``。走缓存（未命中回源并写回），**只返回 ``status='0'``** 的项。
    查不到时返回空数组而不是 ``null``。
    """
    data = _dict_type_service().select_dict_data_by_type(dict_type)
    if is_null(data):
        data = []
    return AjaxResult.success_data(data)


@router.get("/typemore/{dict_type}", response_model=None)
def dict_type_more(dict_type: str) -> AjaxResult:
    """根据（逗号分隔的）字典类型查询并按类型分组. Java: ``@GetMapping(value = "/typemore/{dictType}")``.

    ``dictType`` 可以是 ``"car_type,plate_color"``。分组见模块 docstring。
    """
    data = _dict_type_service().select_dict_data_by_type_more(dict_type)
    if is_null(data):
        # Java: if (StringUtils.isNull(data)) { data = new ArrayList<>(); }
        data = []
    return AjaxResult.success_data(_group_by_dict_type(data))


@router.get("/{dict_code}", response_model=None)
@pre_authorize_permi("system:dict:query")
def get_info(dict_code: int) -> AjaxResult:
    """查询字典数据详细. Java: ``@GetMapping(value = "/{dictCode}")``.

    查不到时 ``data`` 为 ``null``（不是 404）。
    """
    return AjaxResult.success_data(_dict_data_service().select_dict_data_by_id(dict_code))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:dict:add")
@log(title="字典数据", business_type=BusinessType.INSERT, java_method="add")
def add(dict_data: ValidDictData) -> AjaxResult:
    """新增字典数据. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysDictData dict)``.

    没有唯一性校验（Java 也没有）—— 同一类型下可以存在两条相同 ``dictValue``，
    ``selectDictLabel`` 撞上就得抛 ``TooManyResultsException``。见 §32。
    """
    dict_data.create_by = SecurityUtils.get_username()
    return to_ajax(_dict_data_service().insert_dict_data(dict_data))


@router.put("", response_model=None)
@pre_authorize_permi("system:dict:edit")
@log(title="字典数据", business_type=BusinessType.UPDATE, java_method="edit")
def edit(dict_data: ValidDictData) -> AjaxResult:
    """修改保存字典数据. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysDictData dict)``.

    改完会清空**整个**字典缓存（``sys_dict:*``），不只是本类型。
    """
    dict_data.update_by = SecurityUtils.get_username()
    return to_ajax(_dict_data_service().update_dict_data(dict_data))


@router.delete("/{dict_codes}", response_model=None)
@pre_authorize_permi("system:dict:remove")
@log(title="字典类型", business_type=BusinessType.DELETE, java_method="remove")
def remove(dict_codes: str) -> AjaxResult:
    """删除字典数据. Java: ``@DeleteMapping("/{dictCodes}") public AjaxResult remove(@PathVariable Long[] dictCodes)``.

    逗号串 -> ``Long[]``（``parse_id_array``）；物理删除，没有回收站。
    """
    return to_ajax(_dict_data_service().delete_dict_data_by_ids(parse_id_array(dict_codes)))


def _group_by_dict_type(rows: List[SysDictData]) -> Dict[str, List[SysDictData]]:
    """Java: ``.collect(Collectors.groupingBy(SysDictData::getDictType))``.

    ``HashMap`` 的键顺序在 Java 里不可依赖；这里保留"首次出现"的顺序，而查询自带
    ``order by dict_type, dict_sort asc``，所以实际是字典序。见模块 docstring。
    """
    grouped: Dict[str, List[SysDictData]] = {}
    for row in rows:
        key: Any = row.dict_type
        grouped.setdefault(key, []).append(row)
    return grouped


__all__ = [
    "router",
    "DictDataParam",
    "ValidDictData",
    "list_dict_data",
    "dict_type",
    "dict_type_more",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_dict_data_controller",
]
