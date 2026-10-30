"""查询日志 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarQueryLogController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:querylog:list``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:querylog:add``
``edit``                  PUT ``""``                  ``manager:querylog:edit``
``remove``                DELETE ``/{ids}``           ``manager:querylog:remove``
``export``                GET ``/export``             ``manager:querylog:export``
========================  ==========================  ==============================

``export`` 里那段 ``if (null != dp.getCreateTime()) { dp.setCreateTime(dp.getCreateTime()); }``
是**空操作**（字段赋给自己），Java 没有转成字符串。这里同样不做事，只留注释 ——
不要"顺手"改成 ``setCreateTimeStr``，模板里没有这一列。

路由声明顺序与 Java **不同**：Java 把 ``export`` 写在 ``getInfo`` 之后，Spring 按精确路径
优先匹配所以无碍；FastAPI 按注册顺序匹配，``GET /manager/querylog/export`` 会先命中
``GET /{id}`` 而把 "export" 当成主键。因此 ``/{id}`` 必须排在所有静态 ``GET`` 之后。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.common_util import is_null
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_query_log import CarQueryLog
from app.manager.service.car_query_log_service import (
    CarQueryLogService,
    get_car_query_log_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_query_log_controller")

router = APIRouter(prefix="/manager/querylog", tags=["manager-query-log"])

#: Java: ``com.ruoyi.web.controller.manager.CarQueryLogController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarQueryLogController"

#: Java: ``String url = "templates/export/queryLog.xlsx";``
EXPORT_TEMPLATE = "templates/export/queryLog.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: Java: ``sysDictDataService.selectDictDataMap("model_type")``
MODEL_TYPE_DICT = "model_type"

#: Java: ``sysDictDataService.selectDictDataMap("menu_point")``
MENU_POINT_DICT = "menu_point"

_SERVICE: Optional[CarQueryLogService] = None


def _service() -> CarQueryLogService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_query_log_service()
    return _SERVICE


def reset_query_log_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarQueryLog:
    """Java: 形参 ``CarQueryLog carQueryLog``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarQueryLog, request.query_params)


CarQueryLogParam = Annotated[CarQueryLog, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:querylog:list")
def list_query_logs(query: CarQueryLogParam) -> TableDataInfo:
    """查询查询日志列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.post("", response_model=None)
@pre_authorize_permi("manager:querylog:add")
@log(title="查询日志", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarQueryLog) -> AjaxResult:
    """新增查询日志. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:querylog:edit")
@log(title="查询日志", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarQueryLog) -> AjaxResult:
    """修改查询日志. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:querylog:remove")
@log(title="查询日志", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除查询日志. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:querylog:export")
@log(title="日志信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarQueryLogParam) -> Response:
    """导出查询日志列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[CarQueryLog] = _service().select_list(query)
    dict_service = get_dict_data_service()
    model_type_map: Dict[str, str] = dict_service.select_dict_data_map(MODEL_TYPE_DICT)
    menu_point_map: Dict[str, str] = dict_service.select_dict_data_map(MENU_POINT_DICT)
    for item in rows:
        # Java: if (null != dp.getCreateTime()) { dp.setCreateTime(dp.getCreateTime()); }
        # —— 字段赋给自己，空操作；createTime 不转字符串（模板没有这一列）
        item.menu_point = is_null(menu_point_map.get(item.menu_point))
        item.model_type = is_null(model_type_map.get(item.model_type))

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出查询日志失败", exc_info=True)
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
    """获取查询日志详细信息. Java: ``@GetMapping(value = "/{id}")``.

    **必须**声明在所有静态 ``GET`` 路径之后（见模块 docstring）。
    """
    return AjaxResult.success_data(_service().select_by_id(id))


__all__ = [
    "router",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "MENU_POINT_DICT",
    "MODEL_TYPE_DICT",
    "OCTET_STREAM_CONTENT_TYPE",
    "add",
    "edit",
    "export",
    "get_info",
    "list_query_logs",
    "remove",
    "reset_query_log_controller",
]
