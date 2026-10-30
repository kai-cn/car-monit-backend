"""门架信息控制器 —— 列表补路段名，导出走 easypoi 模板.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryController.java

**7** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **无**（登录即可）
``listAll``               GET ``/listAll``            **无**
``export``                GET ``/export``             ``base:gantry:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``base:gantry:add``
``edit``                  PUT ``""``                  ``base:gantry:edit``
``remove``                DELETE ``/{ids}``           ``base:gantry:remove``
========================  ==========================  ==============================

``list`` 与 ``listAll`` 的唯一差别
----------------------------------
``list`` 会用 Redis ``SECTION_LIST`` 给每条门架补上 ``roadName`` / ``sectionName``
（查不到时是**空串**，不是 ``null``）；``listAll`` 只是 ``startPage()`` + 查库，
给"选择门架"弹窗用。

``export`` 的九个动作
---------------------
1. 数据源**不是数据库**，而是 Redis 对象 ``Constants.gantry_list``（一个
   ``List<OdsSzdnGantry>``）；取不到就当空列表。
2. 列表为空 -> **什么都不做**，`return null`（200 + 空 body + 无响应头）。
3. 路段表 + 收费站表 + 机构表全量查出来建三张映射
   （``tollMap`` / ``orgMap`` 用的是**没有 merge 函数**的 ``toMap``：``tollCode`` 重复
   抛 ``IllegalStateException``，``tollName`` 为 ``null`` 抛 ``NPE`` —— 都是 500）。
4. 逐条翻译 ``boundaryGantryType``（``"0"`` -> 边界入口门架 / 否则 边界出口门架）、
   ``isVirtual``（``"0"`` -> 否 / 否则 是）。
5. ``isData``：读 ``Constants.gantry_list_data + gantryCode``，能解析成整数且 > 0
   才是 ``"是"``，否则 ``"否"``。**解析失败不兜底**，``Integer.parseInt`` 直接抛
   ``NumberFormatException``（这一段**不在** ``try`` 里）。
6. 按 ``orgCode`` -> ``roadCode`` -> ``sectionCode`` -> ``tollCode`` -> ``gantryCode``
   排序（``Comparator.comparing`` 链，**任何一级为 null 都 NPE**）。
7. ``templates/export/gantry.xlsx`` 渲染，字节写进响应，Java ``return null``。

被注释掉的过滤条件
------------------
Java 里这两行是注释的（不是遗漏）：

.. code-block:: java

    // list = list.stream().filter(item -> "1".equals(item.getBoundaryGantryType())
    //         && "0".equals(item.getIsVirtual())).collect(Collectors.toList());

所以导出的是**全部门架**，含虚拟门架。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.base.domain.ods_szdn_gantry import OdsSzdnGantry
from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.domain.ods_yhgl_v_base_org import OdsYhglVBaseOrg
from app.base.service.ods_szdn_gantry_service import (
    OdsSzdnGantryService,
    get_ods_szdn_gantry_service,
)
from app.base.service.ods_szdn_toll_service import OdsSzdnTollService, get_ods_szdn_toll_service
from app.base.service.ods_yhgl_v_base_org_service import (
    OdsYhglVBaseOrgService,
    get_ods_yhgl_v_base_org_service,
)
from app.base.util.cache_reader import (
    read_section_list,
    road_name_map,
    section_name_map,
    to_entities,
)
from app.common.constant.constants import gantry_list, gantry_list_data
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
from app.common.utils.common_util import is_null
from app.common.utils.java_stream import sorted_by, to_map
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi

logger = logging.getLogger("app.api.base.ods_szdn_gantry_controller")

router = APIRouter(prefix="/base/gantry", tags=["base-gantry"])

#: Java: ``com.ruoyi.web.controller.base.OdsSzdnGantryController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.OdsSzdnGantryController"

#: Java: ``String url = "templates/export/gantry.xlsx";``
EXPORT_TEMPLATE = "templates/export/gantry.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: ``boundaryGantryType`` / ``isVirtual`` / ``isData`` 的文案。
BOUNDARY_ENTRY = "边界入口门架"
BOUNDARY_EXIT = "边界出口门架"
YES = "是"
NO = "否"

_COLLABORATORS: Optional[Dict[str, Any]] = None


def _collaborators() -> Dict[str, Any]:
    """Java 的四个 ``@Autowired`` / ``@Resource``（进程内单例）。"""
    global _COLLABORATORS
    if _COLLABORATORS is None:
        _COLLABORATORS = {
            "service": get_ods_szdn_gantry_service(),
            "redis_cache": get_redis_cache(),
            "toll_service": get_ods_szdn_toll_service(),
            "base_org_service": get_ods_yhgl_v_base_org_service(),
        }
    return _COLLABORATORS


def reset_gantry_controller(
    service: Optional[OdsSzdnGantryService] = None,
    redis_cache: Optional[RedisCache] = None,
    toll_service: Optional[OdsSzdnTollService] = None,
    base_org_service: Optional[OdsYhglVBaseOrgService] = None,
) -> None:
    """Test helper: drop / inject the cached collaborators."""
    global _COLLABORATORS
    if service is None and redis_cache is None and toll_service is None and base_org_service is None:
        _COLLABORATORS = None
        return
    current = dict(_collaborators())
    if service is not None:
        current["service"] = service
    if redis_cache is not None:
        current["redis_cache"] = redis_cache
    if toll_service is not None:
        current["toll_service"] = toll_service
    if base_org_service is not None:
        current["base_org_service"] = base_org_service
    _COLLABORATORS = current


def _query(request: Request) -> OdsSzdnGantry:
    """Java: 形参 ``OdsSzdnGantry odsSzdnGantry``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(OdsSzdnGantry, request.query_params)


GantryParam = Annotated[OdsSzdnGantry, Depends(_query)]


def _java_equals_zero(value: Optional[str]) -> bool:
    """Java: ``"0".equals(value)`` —— ``value`` 为 ``null`` 时是 ``false``（不 NPE）."""
    return value == "0"


@router.get("/list", response_model=None)
def list_gantries(query: GantryParam) -> TableDataInfo:
    """查询门架信息列表. Java: ``@GetMapping("/list")``."""
    collaborators = _collaborators()
    start_page()

    section_list = read_section_list(collaborators["redis_cache"])
    road_map = road_name_map(section_list)
    section_map = section_name_map(section_list)

    rows: List[OdsSzdnGantry] = collaborators["service"].select_list(query)
    for gantry in rows:
        gantry.road_name = road_map.get(gantry.road_code, "")
        gantry.section_name = section_map.get(gantry.section_code, "")
    return get_data_table(rows)


@router.get("/listAll", response_model=None)
def list_all_gantries(query: GantryParam) -> TableDataInfo:
    """查询门架信息列表：选择门架弹窗. Java: ``@GetMapping("/listAll")``."""
    start_page()
    return get_data_table(_collaborators()["service"].select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:gantry:export")
@log(title="门架信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: GantryParam) -> Response:
    """导出门架信息列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``.

    ``query`` 在 Java 里也是形参，但**整个方法体没用到它**（数据来自 Redis）。
    保留形参以维持端点签名（QueryString 仍会被绑定、非法值仍会 500）。
    """
    collaborators = _collaborators()

    rows: List[OdsSzdnGantry] = []
    cached = collaborators["redis_cache"].get_cache_object(gantry_list)
    if cached is not None:
        # Java: list = (List<OdsSzdnGantry>) obj;
        rows = to_entities(OdsSzdnGantry, cached)

    if not rows:
        # Java: 列表为空 -> 不写任何字节，直接 return null
        return Response(content=b"")

    section_list = read_section_list(collaborators["redis_cache"])
    road_map = road_name_map(section_list)
    section_map = section_name_map(section_list)

    # tollService.list() / baseOrgService.list() —— MyBatis-Plus 的"全表 list()"，
    # 这里用 XML 的 selectXxxList(空实体)：条件全为 false，等价于全表。
    toll_map = to_map(
        collaborators["toll_service"].select_list(OdsSzdnToll()),
        lambda item: item.toll_code,
        lambda item: item.toll_name,
    )
    org_map = to_map(
        collaborators["base_org_service"].select_list(OdsYhglVBaseOrg()),
        lambda item: item.org_code,
        lambda item: item.org_name,
    )

    for gantry in rows:
        gantry.road_name = road_map.get(gantry.road_code, "")
        gantry.section_name = section_map.get(gantry.section_code, "")
        gantry.toll_name = toll_map.get(gantry.toll_code, "")
        gantry.org_name = org_map.get(gantry.org_code, "")
        gantry.boundary_gantry_type = (
            BOUNDARY_ENTRY if _java_equals_zero(gantry.boundary_gantry_type) else BOUNDARY_EXIT
        )
        gantry.is_virtual = NO if _java_equals_zero(gantry.is_virtual) else YES
        gantry.is_data = NO
        cache_key = gantry_list_data + is_null(gantry.gantry_code)
        obj_num = collaborators["redis_cache"].get_cache_object(cache_key)
        if obj_num is not None:
            # Java: Integer.parseInt(objNum.toString()) —— 非数字抛 NumberFormatException
            int_count_num = int(str(obj_num))
            if int_count_num > 0:
                gantry.is_data = YES

    rows = sorted_by(
        rows,
        lambda item: item.org_code,
        lambda item: item.road_code,
        lambda item: item.section_code,
        lambda item: item.toll_code,
        lambda item: item.gantry_code,
    )

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出门架信息失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取门架信息详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_collaborators()["service"].select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("base:gantry:add")
@log(title="门架信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: OdsSzdnGantry) -> AjaxResult:
    """新增门架信息. Java: ``@PostMapping``."""
    return _collaborators()["service"].save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:gantry:edit")
@log(title="门架信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: OdsSzdnGantry) -> AjaxResult:
    """修改门架信息. Java: ``@PutMapping``."""
    return _collaborators()["service"].save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("base:gantry:remove")
@log(title="门架信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除门架信息. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _collaborators()["service"].delete_by_ids(parse_str_array(ids))


__all__ = [
    "BOUNDARY_ENTRY",
    "BOUNDARY_EXIT",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "GantryParam",
    "NO",
    "OCTET_STREAM_CONTENT_TYPE",
    "YES",
    "add",
    "edit",
    "export",
    "get_info",
    "list_all_gantries",
    "list_gantries",
    "remove",
    "reset_gantry_controller",
    "router",
]
