"""门架抓拍流水 —— Forest 客户端.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsRtSzdnSnapshotFlowAddcodeService.java

Java 原文::

    @BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
    public interface HttpOdsRtSzdnSnapshotFlowAddcodeService {
        @Get("/base/snapshotflow/list")           TableDataInfo get...Page(@Query q);
        @Get("/base/snapshotflow/listToExport")   List<...> get...ListToExport(@Query q);
        @Get("/base/snapshotflow/{bigId}")        ... select...ById(@Var String bigId);
        @Get("/base/snapshotflow/earliest-time")  Date getEarliestSnapshottime();
    }

``earliest-time`` 的返回值 Java 声明为 ``Date``，Forest 会把 JSON 值转成
``java.util.Date``，再由 Jackson 序列化回响应体。本工程**没有**配置
``spring.jackson.date-format``，所以 Java 侧理论上会走 ISO-8601。这里改为
**原样透传**上游字段（不解析成 ``datetime`` 再格式化），避免引入一个 Java 侧
并不稳定的格式 —— 见 ``COMPATIBILITY.md``。
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


class HttpOdsRtSzdnSnapshotFlowAddcodeService:
    """Java: ``interface HttpOdsRtSzdnSnapshotFlowAddcodeService``."""

    # Java: TableDataInfo getOdsRtSzdnSnapshotFlowAddcodePage(@Query ... q)
    @staticmethod
    def get_ods_rt_szdn_snapshot_flow_addcode_page(entity: Any) -> TableDataInfo:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url,
            "/base/snapshotflow/list",
            to_query_params(entity),
        )
        info = to_table_data_info(payload)
        # Java 实体声明的派生字段即使为 null 也会序列化。
        for row in info.rows or []:
            if isinstance(row, dict):
                row.setdefault("plateColorMark", None)
                row.setdefault("plateColorName", None)
        return info

    # Java: List<OdsRtSzdnSnapshotFlowAddcode> getOdsRtSzdnSnapshotFlowAddcodeListToExport(@Query q)
    @staticmethod
    def get_ods_rt_szdn_snapshot_flow_addcode_list_to_export(
        entity: Any,
    ) -> List[Mapping[str, Any]]:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url,
            "/base/snapshotflow/listToExport",
            to_query_params(entity),
        )
        return payload if isinstance(payload, list) else []

    # Java: OdsRtSzdnSnapshotFlowAddcode selectOdsRtSzdnSnapshotFlowAddcodeById(@Var String bigId)
    @staticmethod
    def select_ods_rt_szdn_snapshot_flow_addcode_by_id(
        big_id: str,
    ) -> Optional[Mapping[str, Any]]:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url, f"/base/snapshotflow/{big_id}"
        )
        return payload if isinstance(payload, Mapping) else None

    # Java: Date getEarliestSnapshottime()
    @staticmethod
    def get_earliest_snapshottime() -> Any:
        """返回上游原值（可能是 ISO 字符串 / ``yyyy-MM-dd HH:mm:ss`` / 数字 / ``null``）。"""
        return forest_get(
            get_settings().vehicle_monitor.base_url, "/base/snapshotflow/earliest-time"
        )


__all__ = ["HttpOdsRtSzdnSnapshotFlowAddcodeService"]
