"""补缴处理 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarAduitFreeController.java

**10** 个映射
-------------
==========================  ====================================  ==========
Java                        Method / Path                         权限点
==========================  ====================================  ==========
``list``                    GET ``/list``                        **无**
``export``                  GET ``/export``                      **无**
``getInfo``                 GET ``/{id}``                        **无**
``add``                     POST ``""``                          **无**
``edit``                    PUT ``""``                           **无**
``remove``                  DELETE ``/{ids}``                    **无**
``incomeStatics``           GET ``/incomeStatics``               **无**
``exportIncomeStatics``     GET ``/exportIncomeStatics``         **无**
``incomeDetailList``        GET ``/incomeDetailList``            **无**
``exportIncomeDetailList``  GET ``/exportIncomeDetailList``      **无**
==========================  ====================================  **无**

（Java 引了 ``@PreAuthorize`` 但**一个都没用** —— 照抄，全部只要登录。）

四处必须照抄的地方
------------------
1. ``export`` 走 ``ExcelUtil<CarAduitFree>``（按 ``@Excel`` 注解出列，sheet 名
   ``补缴处理数据``），**不是** easypoi 模板；返回体里 ``msg`` 是文件名、无 ``data``；
2. ``incomeDetailList`` / ``exportIncomeDetailList`` 在 ``orgId`` 为空时把它改成
   ``"-1"``（查不到数据），而不是"不过滤"；
3. ``incomeStatics`` 用 ``CarConfimFreeQueryRo`` 接参数，``incomeDetailList`` 用
   ``CarConfimFree`` 接参数 —— 两个不同的绑定对象，别混；
4. 模板导出写响应头后 ``return null``：渲染抛异常时回**空 body + 无响应头**。

路由声明顺序与 Java **不同**：``GET /{id}`` 必须排在所有静态 ``GET`` 之后
（FastAPI 按声明顺序匹配，Spring 是精确路径优先）。
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
from app.common.utils.common_util import is_blank
from app.common.utils.poi.excel_util import ExcelUtil
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.framework.aspectj.log_aspect import log
from app.manager.domain.car_aduit_free import CarAduitFree
from app.manager.domain.car_confim_free import CarConfimFree
from app.manager.domain.vo.car_confim_free_query_ro import CarConfimFreeQueryRo
from app.manager.service.car_aduit_free_service import (
    CarAduitFreeService,
    get_car_aduit_free_service,
)

logger = logging.getLogger("app.api.manager.car_aduit_free_controller")

router = APIRouter(prefix="/manager/aduitfree", tags=["manager-aduit-free"])

#: Java: ``com.ruoyi.web.controller.manager.CarAduitFreeController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarAduitFreeController"

#: Java: ``util.exportExcel(list, "补缴处理数据")`` —— sheet 名与文件名前缀
EXPORT_SHEET_NAME = "补缴处理数据"
#: Java: ``String url = "templates/export/incomeStatics.xlsx";``
EXPORT_INCOME_STATICS_TEMPLATE = "templates/export/incomeStatics.xlsx"
#: Java: ``String url = "templates/export/exportIncomeDetailList.xlsx";``
EXPORT_INCOME_DETAIL_TEMPLATE = "templates/export/exportIncomeDetailList.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"
#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"
#: ``incomeDetailList`` 在单位为空时替换成的魔数
EMPTY_ORG_ID_PLACEHOLDER = "-1"

_SERVICE: Optional[CarAduitFreeService] = None


def _service() -> CarAduitFreeService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_aduit_free_service()
    return _SERVICE


def reset_car_aduit_free_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarAduitFree:
    """Java: 形参 ``CarAduitFree carAduitFree``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarAduitFree, request.query_params)


CarAduitFreeParam = Annotated[CarAduitFree, Depends(_query)]


def _confim_free_query(request: Request) -> CarConfimFree:
    """Java: 形参 ``CarConfimFree carConfimFree``（明细接口用）."""
    return bind_query_params(CarConfimFree, request.query_params)


CarConfimFreeParam = Annotated[CarConfimFree, Depends(_confim_free_query)]


def _statistics_query(request: Request) -> CarConfimFreeQueryRo:
    """Java: 形参 ``CarConfimFreeQueryRo queryRo``."""
    return bind_query_params(CarConfimFreeQueryRo, request.query_params)


CarConfimFreeQueryRoParam = Annotated[CarConfimFreeQueryRo, Depends(_statistics_query)]


# --------------------------------------------------------------------------- 列表 / 导出


@router.get("/list", response_model=None)
def list_aduit_frees(query: CarAduitFreeParam) -> TableDataInfo:
    """查询补缴处理列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@log(title="补缴处理", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarAduitFreeParam) -> AjaxResult:
    """导出补缴处理列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(CarAduitFree).export_excel(list(rows), EXPORT_SHEET_NAME)


# --------------------------------------------------------------------------- PC 统计


@router.get("/incomeStatics", response_model=None)
def income_statics(query_ro: CarConfimFreeQueryRoParam) -> TableDataInfo:
    """pc 统计：堵漏增收. Java: ``@GetMapping(value = "/incomeStatics")``."""
    start_page()
    return get_data_table(_service().get_pc_income_statics(query_ro))


@router.get("/exportIncomeStatics", response_model=None)
def export_income_statics(query_ro: CarConfimFreeQueryRoParam) -> Response:
    """pc 统计导出：堵漏增收. Java: ``@GetMapping(value = "/exportIncomeStatics")``."""
    rows = _service().get_pc_income_statics(query_ro)
    return _export_excel(EXPORT_INCOME_STATICS_TEMPLATE, rows)


@router.get("/incomeDetailList", response_model=None)
def income_detail_list(query: CarConfimFreeParam) -> TableDataInfo:
    """堵漏增收明细. Java: ``@GetMapping("/incomeDetailList")``."""
    start_page()
    if is_blank(query.org_id):
        query.org_id = EMPTY_ORG_ID_PLACEHOLDER
    return get_data_table(_service().income_detail_list(query))


@router.get("/exportIncomeDetailList", response_model=None)
def export_income_detail_list(query: CarConfimFreeParam) -> Response:
    """堵漏增收明细导出. Java: ``@GetMapping(value = "/exportIncomeDetailList")``."""
    if is_blank(query.org_id):
        query.org_id = EMPTY_ORG_ID_PLACEHOLDER
    rows = _service().income_detail_list(query)
    return _export_excel(EXPORT_INCOME_DETAIL_TEMPLATE, rows)


# --------------------------------------------------------------------------- 详情 / 增删改


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取补缴处理详细信息. Java: ``@GetMapping(value = "/{id}")``.

    **必须**声明在所有静态 ``GET`` 路径之后（见模块 docstring）。
    """
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@log(title="补缴处理", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarAduitFree) -> AjaxResult:
    """新增补缴处理. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@log(title="补缴处理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarAduitFree) -> AjaxResult:
    """修改补缴处理. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@log(title="补缴处理", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除补缴处理. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


def _export_excel(template: str, rows: Any) -> Response:
    """模板导出共用的 easypoi 渲染（失败时回空 body、无响应头）。"""
    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(template)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出补缴处理失败: %s", template, exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


__all__ = [
    "router",
    "EXPORT_INCOME_DETAIL_TEMPLATE",
    "EXPORT_INCOME_STATICS_TEMPLATE",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "export_income_detail_list",
    "export_income_statics",
    "get_info",
    "income_detail_list",
    "income_statics",
    "list_aduit_frees",
    "remove",
    "reset_car_aduit_free_controller",
]
