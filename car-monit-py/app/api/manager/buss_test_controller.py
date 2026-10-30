"""业务测试 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/BussTestController.java

**7** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:busstest:list``
``export``                GET ``/export``             ``manager:busstest:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:busstest:add``
``edit``                  PUT ``""``                  ``manager:busstest:edit``
``remove``                DELETE ``/{ids}``           ``manager:busstest:remove``
``syncCurrentTrack``      POST ``/syncCurrentTrack``  ``manager:busstest:syncTest``
========================  ==========================  ==============================

``syncCurrentTrack`` 返回 Java ``void``
--------------------------------------
Java 签名是 ``public void syncCurrentTrack()``：Spring 写回 **HTTP 200 + 空 body**，
没有 ``Content-Type``，也不是 ``AjaxResult``。这里用 ``Response(status_code=200)``
精确复刻（不能返回 ``None`` —— 那会变成 JSON ``null``）。

``BusTestController`` 还注入了 ``ICarSuspiciousService`` 与 ``IGeometryService``，
但两个字段在类里**从未被使用** —— 照抄为不注入（Python 没有 Spring 的字段注入语义，
未使用即不存在）。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Optional

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
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.buss_test import BussTest
from app.manager.service.buss_test_service import (
    BussTestService,
    get_buss_test_service,
)
from app.manager.service.car_track_info_service import get_car_track_info_service

logger = logging.getLogger("app.api.manager.buss_test_controller")

router = APIRouter(prefix="/manager/busstest", tags=["manager-buss-test"])

#: Java: ``com.ruoyi.web.controller.manager.BussTestController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.BussTestController"

#: Java: ``util.exportExcel(list, "业务测试数据")``
EXPORT_SHEET_NAME = "业务测试数据"

_SERVICE: Optional[BussTestService] = None


def _service() -> BussTestService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_buss_test_service()
    return _SERVICE


def reset_buss_test_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> BussTest:
    """Java: 形参 ``BussTest bussTest``（**没有** ``@RequestBody``）."""
    return bind_query_params(BussTest, request.query_params)


BussTestParam = Annotated[BussTest, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:busstest:list")
def list_buss_tests(query: BussTestParam) -> TableDataInfo:
    """查询业务测试列表. Java: ``@GetMapping("/list")``.

    ``bussTest.setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的**，
    所以跨租户可见 —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:busstest:export")
@log(title="业务测试", business_type=BusinessType.EXPORT, java_method="export")
def export(query: BussTestParam) -> AjaxResult:
    """导出业务测试列表. Java: ``@GetMapping("/export")``.

    不受分页影响（Java 没有 ``startPage()``）；``msg`` 是生成的文件名。
    """
    rows = _service().select_list(query)
    return ExcelUtil(BussTest).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取业务测试详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:busstest:add")
@log(title="业务测试", business_type=BusinessType.INSERT, java_method="add")
def add(entity: BussTest) -> AjaxResult:
    """新增业务测试. Java: ``@PostMapping`` —— ``@RequestBody BussTest``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:busstest:edit")
@log(title="业务测试", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: BussTest) -> AjaxResult:
    """修改业务测试. Java: ``@PutMapping`` —— ``@RequestBody BussTest``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:busstest:remove")
@log(title="业务测试", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除业务测试. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


@router.post("/syncCurrentTrack", response_model=None)
@pre_authorize_permi("manager:busstest:syncTest")
def sync_current_track() -> Response:
    """车辆实时轨迹同步. Java: ``@PostMapping("/syncCurrentTrack")`` —— ``public void``.

    Java 方法体只有两行日志夹一次调用，**忽略** ``syncCurrentTrack()`` 的返回值
    （``AjaxResult`` 被丢弃）。返回 HTTP 200 空 body。
    """
    logger.info("车俩实时轨迹同步开始同步！%s", datetime.now())
    get_car_track_info_service().sync_current_track()
    logger.info("车俩实时轨迹同步结束同步！%s", datetime.now())
    return Response(status_code=200)


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "list_buss_tests",
    "remove",
    "reset_buss_test_controller",
    "sync_current_track",
]
