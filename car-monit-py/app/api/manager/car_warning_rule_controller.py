"""预警规则 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningRuleController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:warningrule:list``
``export``                GET ``/export``             ``manager:warningrule:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:warningrule:add``
``edit``                  PUT ``""``                  ``manager:warningrule:edit``
``remove``                DELETE ``/{ids}``           ``manager:warningrule:remove``
========================  ==========================  ==============================

``export`` 的两个细节
---------------------
1. 数据源是**数据库**（``selectCarWarningRuleList``），不受分页影响 ——
   Java 没有 ``startPage()``。
2. ``noticeType`` 的字典翻译写在 ``if (null != dp.getCreateTime())`` **里面**：
   没有创建时间的行，``noticeType`` 保持原始字典值（通常是 ``"1"``），不会被翻译成
   ``null``。照抄这个位置。
3. 模板 ``templates/export/carWarningRule.xlsx`` 渲染后把字节写进响应，
   Java ``return null`` —— 这里返回 ``Response``。
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
from app.common.utils.date_utils import YYYY_MM_DD_HH_MM_SS, parse_date_to_str
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_warning_rule import CarWarningRule
from app.manager.service.car_warning_rule_service import (
    CarWarningRuleService,
    get_car_warning_rule_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_warning_rule_controller")

router = APIRouter(prefix="/manager/warningrule", tags=["manager-warning-rule"])

#: Java: ``com.ruoyi.web.controller.manager.CarWarningRuleController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarWarningRuleController"

#: Java: ``String url = "templates/export/carWarningRule.xlsx";``
EXPORT_TEMPLATE = "templates/export/carWarningRule.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: 字典类型 —— ``sysDictDataService.selectDictDataMap("notice_type")``
NOTICE_TYPE_DICT = "notice_type"

_SERVICE: Optional[CarWarningRuleService] = None


def _service() -> CarWarningRuleService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_warning_rule_service()
    return _SERVICE


def reset_warning_rule_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarWarningRule:
    """Java: 形参 ``CarWarningRule carWarningRule``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarWarningRule, request.query_params)


WarningRuleParam = Annotated[CarWarningRule, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:warningrule:list")
def list_warning_rules(query: WarningRuleParam) -> TableDataInfo:
    """查询预警规则列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的**，
    所以跨租户可见 —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:warningrule:export")
@log(title="预警规则", business_type=BusinessType.EXPORT, java_method="export")
def export(query: WarningRuleParam) -> Response:
    """导出预警规则列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[CarWarningRule] = _service().select_list(query)
    notice_type_map: Dict[str, str] = get_dict_data_service().select_dict_data_map(
        NOTICE_TYPE_DICT
    )
    for item in rows:
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.create_time)
            # Java 把字典翻译写在 if 里面 —— 没有 createTime 的行不翻译
            item.notice_type = notice_type_map.get(item.notice_type)

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出预警规则失败", exc_info=True)
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
    """获取预警规则详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:warningrule:add")
@log(title="预警规则", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarWarningRule) -> AjaxResult:
    """新增预警规则. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:warningrule:edit")
@log(title="预警规则", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarWarningRule) -> AjaxResult:
    """修改预警规则. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:warningrule:remove")
@log(title="预警规则", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除预警规则. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "NOTICE_TYPE_DICT",
    "OCTET_STREAM_CONTENT_TYPE",
    "add",
    "edit",
    "export",
    "get_info",
    "list_warning_rules",
    "remove",
    "reset_warning_rule_controller",
]
