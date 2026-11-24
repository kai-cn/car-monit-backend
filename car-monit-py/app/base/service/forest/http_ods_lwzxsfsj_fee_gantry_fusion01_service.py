"""交易流水 —— Forest 客户端.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeGantryFusion01Service.java

Java 原文只有两条注解声明::

    @BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
    public interface HttpOdsLwzxsfsjFeeGantryFusion01Service {
        @Get("/base/feeGantry/list")   TableDataInfo get...(OdsLwzxsfsjFeeGantryFusion01 q);
        @Get("/base/feeGantry/{bigId}") OdsLwzxsfsjFeeGantryFusion01 select...ById(@Var String bigId);
    }

注意：这个服务的调用点**就是它自己这个服务的 ``/list`` 端点**（控制器把请求转给
``http://127.0.0.1:9901/base/feeGantry/list``）。也就是说开启本级服务后，该端点会
请求自己 —— Java 原样如此，照抄。
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from app.base.service.forest.forest_client import (
    forest_get,
    to_query_params,
    to_table_data_info,
)
from app.common.core.page.table_data_info import TableDataInfo
from app.settings import get_settings


class HttpOdsLwzxsfsjFeeGantryFusion01Service:
    """Java: ``interface HttpOdsLwzxsfsjFeeGantryFusion01Service``."""

    # Java: TableDataInfo getOdsLwzxsfsjFeeGantryFusion01Page(@Query ... q)
    @staticmethod
    def get_ods_lwzxsfsj_fee_gantry_fusion01_page(entity: Any) -> TableDataInfo:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url,
            "/base/feeGantry/list",
            to_query_params(entity),
        )
        info = to_table_data_info(payload)
        # Java 实体声明的派生字段即使为 null 也会序列化。
        for row in info.rows or []:
            if isinstance(row, dict):
                row.setdefault("plateColorMark", None)
                row.setdefault("plateColorName", None)
        return info

    # Java: OdsLwzxsfsjFeeGantryFusion01 selectOdsLwzxsfsjFeeGantryFusion01ById(
    #           @Var("bigId") String bigId)
    @staticmethod
    def select_ods_lwzxsfsj_fee_gantry_fusion01_by_id(big_id: str) -> Optional[Mapping[str, Any]]:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url, f"/base/feeGantry/{big_id}"
        )
        return payload if isinstance(payload, Mapping) else None


__all__ = ["HttpOdsLwzxsfsjFeeGantryFusion01Service"]
