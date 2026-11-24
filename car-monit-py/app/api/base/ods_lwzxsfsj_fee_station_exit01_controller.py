"""收费站出口流水控制器 —— Forest 代理 + 手工校验上游 ``code``.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java

**2** 个映射
------------
=====================  ==============================  ==============================
Java                   Method / Path                   权限点
=====================  ==============================  ==============================
``list``               GET ``/list``                   ``base:feestationexit:list``
``getInfo``            GET ``/{bigId}``                **无**（登录即可）
=====================  ==============================  ==============================

为什么这里要手工判 ``code``
---------------------------
这个客户端的方法返回的是 **hutool 的 ``JSONObject``**（不是 ``TableDataInfo``），
所以控制器自己做三件事：

.. code-block:: java

    JSONObject jsonObject = http...getPage(q);
    if (null == jsonObject || 200 != jsonObject.getInt("code")) {
        logger.error("交易流水数据获取异常：" + jsonObject);
        throw new ServiceException("获取数据异常,请联系管理员");
    }
    return JSONUtil.toBean(jsonObject, TableDataInfo.class);

三处必须照抄的细节：

1. ``jsonObject.getInt("code")`` 返回 ``Integer``；**响应体里没有 ``code`` 时**
   ``200 != null`` 会拆箱 ``NPE`` -> ``code 500``，**不会**走到 ``ServiceException``。
   所以"缺 code"与"code != 200"是两种结局。
2. ``ServiceException`` 由 ``GlobalExceptionHandler`` 渲染成
   ``{"code":500,"msg":"获取数据异常,请联系管理员"}``（HTTP 200）。
3. ``JSONUtil.toBean`` 不校验类型，``rows`` 原样保留为 ``List<JSONObject>``。

与 ``/base/feeGantry/list`` 的区别
----------------------------------
那边**直接**返回 ``TableDataInfo``、不查 ``code``；这边多一层人工校验。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Mapping, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_lwzxsfsj_fee_station_exit01 import OdsLwzxsfsjFeeStationExit01
from app.base.service.forest.http_ods_lwzxsfsj_fee_station_exit01_service import (
    HttpOdsLwzxsfsjFeeStationExit01Service,
)
from app.common.core.controller.base_controller import bind_query_params
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.constant.http_status import HttpStatus
from app.common.exception.exceptions import ServiceException
from app.framework.web.service.permission_service import pre_authorize_permi

logger = logging.getLogger("app.api.base.ods_lwzxsfsj_fee_station_exit01_controller")

router = APIRouter(prefix="/base/feestationexit", tags=["base-fee-station-exit"])

#: Java: ``throw new ServiceException("获取数据异常,请联系管理员")``
FETCH_ERROR_MESSAGE = "获取数据异常,请联系管理员"


def _query(request: Request) -> OdsLwzxsfsjFeeStationExit01:
    """Java: 形参 ``OdsLwzxsfsjFeeStationExit01 q``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(OdsLwzxsfsjFeeStationExit01, request.query_params)


FeeStationExitParam = Annotated[OdsLwzxsfsjFeeStationExit01, Depends(_query)]


def _client() -> HttpOdsLwzxsfsjFeeStationExit01Service:
    """Java: ``@Resource HttpOdsLwzxsfsjFeeStationExit01Service``."""
    return HttpOdsLwzxsfsjFeeStationExit01Service()


def to_table_data_info(json_object: Optional[Mapping[str, Any]]) -> TableDataInfo:
    """Java: ``JSONUtil.toBean(jsonObject, TableDataInfo.class)``.

    hutool 按属性名（``total`` / ``rows`` / ``code`` / ``msg``）逐字段赋值，缺失字段
    保留 Java 默认值（``total=0``、``rows=null``、``code=0``、``msg=null``）。
    """
    info = TableDataInfo()
    if not isinstance(json_object, Mapping):
        return info
    info.set_total(int(json_object.get("total") or 0))
    rows = json_object.get("rows")
    info.set_rows(rows if isinstance(rows, list) else None)
    code = json_object.get("code")
    info.set_code(int(code) if code is not None else 0)
    info.set_msg(json_object.get("msg"))
    return info


@router.get("/list", response_model=None)
@pre_authorize_permi("base:feestationexit:list")
def list_fee_station_exits(query: FeeStationExitParam) -> TableDataInfo:
    """查询收费站出口流水列表. Java: ``@GetMapping("/list")``."""
    # 当前页面
    if query.page_num is None:
        query.page_num = 1
    # 分页大小
    if query.page_size is None:
        query.page_size = 10

    json_object = _client().get_ods_lwzxsfsj_fee_station_exit01_page(query)
    if json_object is None:
        # Java: "...异常：" + jsonObject —— 拼接 null 得到字面量 "null"
        logger.error("交易流水数据获取异常：null")
        raise ServiceException(FETCH_ERROR_MESSAGE)

    code = json_object.get("code")
    if code is None:
        # Java: 200 != jsonObject.getInt("code") —— 拆箱 null -> NPE
        raise TypeError("java.lang.NullPointerException")
    if HttpStatus.SUCCESS != int(code):
        logger.error("交易流水数据获取异常：%s", json_object)
        raise ServiceException(FETCH_ERROR_MESSAGE)
    info = to_table_data_info(json_object)
    # Java 基准声明的可空字段，即使值为 null 也必须出现在 JSON 中。
    for row in info.rows or []:
        if isinstance(row, dict):
            for field in ("cid", "enaxlecount", "entryoperatorid", "enweight", "obuid", "obusign", "paycardid", "provfee", "specialtype"):
                row.setdefault(field, None)
        return to_table_data_info(json_object)


@router.get("/{big_id}", response_model=None)
def get_info(big_id: str) -> AjaxResult:
    """获取收费站出口流水详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    return AjaxResult.success_data(
        _client().select_ods_lwzxsfsj_fee_station_exit01_by_id(big_id)
    )


__all__ = [
    "FETCH_ERROR_MESSAGE",
    "FeeStationExitParam",
    "get_info",
    "list_fee_station_exits",
    "router",
    "to_table_data_info",
]
