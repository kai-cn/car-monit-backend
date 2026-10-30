"""收费站基础信息控制器 —— 列表补路段名，导出走 ExcelUtil.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollController.java

**7** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **无**（登录即可）
``listAll``               GET ``/listAll``            **无**
``export``                GET ``/export``             ``base:toll:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``base:toll:add``
``edit``                  PUT ``""``                  ``base:toll:edit``
``remove``                DELETE ``/{ids}``           ``base:toll:remove``
========================  ==========================  ==============================

``list`` 只补 ``sectionName``
-----------------------------
Java 里建了**两张**映射，但只用了一张：

.. code-block:: java

    Map<String, String> roadMap    = ...;  // 建完之后一次都没用
    Map<String, String> sectionMap = ...;
    for (OdsSzdnToll t : list) { t.setSectionName(sectionMap.getOrDefault(t.getSectionCode(), "")); }

``roadMap`` 是死代码，但**不能删**：它的 ``Collectors.toMap`` 同样会在
``roadName`` 为 ``null`` 时抛 ``NPE``（500）。照抄。

``export`` 走 ``ExcelUtil``（不是 easypoi 模板）：文件名在 ``msg`` 里，
客户端再走 ``GET /common/download?fileName=...``。
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.service.ods_szdn_toll_service import (
    OdsSzdnTollService,
    get_ods_szdn_toll_service,
)
from app.base.util.cache_reader import (
    read_section_list,
    road_name_map,
    section_name_map,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.enums.business_type import BusinessType
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi

router = APIRouter(prefix="/base/toll", tags=["base-toll"])

#: Java: ``com.ruoyi.web.controller.base.OdsSzdnTollController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.OdsSzdnTollController"

#: Java: ``util.exportExcel(list, "收费站基础信息数据")``
EXPORT_SHEET_NAME = "收费站基础信息数据"

_COLLABORATORS: Optional[Dict[str, Any]] = None


def _collaborators() -> Dict[str, Any]:
    """Java 的两个 ``@Autowired``（进程内单例）。"""
    global _COLLABORATORS
    if _COLLABORATORS is None:
        _COLLABORATORS = {
            "service": get_ods_szdn_toll_service(),
            "redis_cache": get_redis_cache(),
        }
    return _COLLABORATORS


def reset_toll_controller(
    service: Optional[OdsSzdnTollService] = None,
    redis_cache: Optional[RedisCache] = None,
) -> None:
    """Test helper: drop / inject the cached collaborators."""
    global _COLLABORATORS
    if service is None and redis_cache is None:
        _COLLABORATORS = None
        return
    current = dict(_collaborators())
    if service is not None:
        current["service"] = service
    if redis_cache is not None:
        current["redis_cache"] = redis_cache
    _COLLABORATORS = current


def _query(request: Request) -> OdsSzdnToll:
    """Java: 形参 ``OdsSzdnToll odsSzdnToll``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(OdsSzdnToll, request.query_params)


TollParam = Annotated[OdsSzdnToll, Depends(_query)]


@router.get("/list", response_model=None)
def list_tolls(query: TollParam) -> TableDataInfo:
    """查询收费站基础信息列表：菜单列表界面. Java: ``@GetMapping("/list")``."""
    collaborators = _collaborators()
    start_page()
    # Java: // odsSzdnToll.setTenantId(SecurityUtils.getTenantId()); —— 注释掉的租户过滤

    section_list = read_section_list(collaborators["redis_cache"])
    # Java: roadMap 建完之后从未使用（死代码，但 null 值仍会 NPE，照抄）
    road_name_map(section_list)
    section_map = section_name_map(section_list)

    rows = collaborators["service"].select_list(query)
    for toll in rows:
        toll.section_name = section_map.get(toll.section_code, "")
    return get_data_table(rows)


@router.get("/listAll", response_model=None)
def list_all_tolls(query: TollParam) -> TableDataInfo:
    """查询收费站基础信息列表：弹出界面窗口. Java: ``@GetMapping("/listAll")``."""
    start_page()
    return get_data_table(_collaborators()["service"].select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:toll:export")
@log(title="收费站基础信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: TollParam) -> AjaxResult:
    """导出收费站基础信息列表. Java: ``@GetMapping("/export")``."""
    rows = _collaborators()["service"].select_list(query)
    return ExcelUtil(OdsSzdnToll).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取收费站基础信息详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_collaborators()["service"].select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("base:toll:add")
@log(title="收费站基础信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: OdsSzdnToll) -> AjaxResult:
    """新增收费站基础信息. Java: ``@PostMapping``."""
    return _collaborators()["service"].save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:toll:edit")
@log(title="收费站基础信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: OdsSzdnToll) -> AjaxResult:
    """修改收费站基础信息. Java: ``@PutMapping``."""
    return _collaborators()["service"].save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("base:toll:remove")
@log(title="收费站基础信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除收费站基础信息. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _collaborators()["service"].delete_by_ids(parse_str_array(ids))


__all__ = [
    "EXPORT_SHEET_NAME",
    "TollParam",
    "add",
    "edit",
    "export",
    "get_info",
    "list_all_tolls",
    "list_tolls",
    "remove",
    "reset_toll_controller",
    "router",
]
