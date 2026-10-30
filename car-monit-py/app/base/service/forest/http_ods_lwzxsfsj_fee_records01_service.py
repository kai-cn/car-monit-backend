"""基础-收费流水 —— Forest 客户端.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeRecords01Service.java

Java 原文::

    @BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
    public interface HttpOdsLwzxsfsjFeeRecords01Service {
        @Get("/base/feerecords/list")            TableDataInfo get...Page(@Query q);
        @Get("/base/feerecords/listToExport")    List<...> get...ListToExport(@Query q);
        @Get("/base/feerecords/{bigId}")         ... select...ById(@Var String bigId);
    }
"""

from __future__ import annotations

from typing import Any, List, Mapping, Optional

from app.base.service.forest.forest_client import (
    forest_get,
    to_query_params,
    to_table_data_info,
)
from app.common.core.page.table_data_info import TableDataInfo
from app.settings import get_settings


class HttpOdsLwzxsfsjFeeRecords01Service:
    """Java: ``interface HttpOdsLwzxsfsjFeeRecords01Service``."""

    # Java: TableDataInfo getOdsLwzxsfsjFeeRecords01Page(@Query ... q)
    @staticmethod
    def get_ods_lwzxsfsj_fee_records01_page(entity: Any) -> TableDataInfo:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url,
            "/base/feerecords/list",
            to_query_params(entity),
        )
        return to_table_data_info(payload)

    # Java: List<OdsLwzxsfsjFeeRecords01> getOdsLwzxsfsjFeeRecords01ListToExport(@Query ... q)
    @staticmethod
    def get_ods_lwzxsfsj_fee_records01_list_to_export(entity: Any) -> List[Mapping[str, Any]]:
        """注意：上游返回的是**裸数组**（不是 ``TableDataInfo`` 信封）。

        控制器随后用 ``List<OdsLwzxsfsjFeeRecords01>`` 接收，所以这里保留原始 dict
        列表、由调用方按需转成实体（与 Java 的 ``JSON.parseArray`` 等价）。
        """
        payload = forest_get(
            get_settings().vehicle_monitor.base_url,
            "/base/feerecords/listToExport",
            to_query_params(entity),
        )
        return payload if isinstance(payload, list) else []

    # Java: OdsLwzxsfsjFeeRecords01 selectOdsLwzxsfsjFeeRecords01ById(@Var("bigId") String bigId)
    @staticmethod
    def select_ods_lwzxsfsj_fee_records01_by_id(big_id: str) -> Optional[Mapping[str, Any]]:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url, f"/base/feerecords/{big_id}"
        )
        return payload if isinstance(payload, Mapping) else None


__all__ = ["HttpOdsLwzxsfsjFeeRecords01Service"]
