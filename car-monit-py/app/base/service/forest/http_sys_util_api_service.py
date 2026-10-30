"""车辆轨迹查询接口（上游车辆监控服务）—— Forest 客户端.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpSysUtilApiService.java

Java 原文里 3 个方法被注释掉了（``syncTrack`` / ``syncSuspiciousCar`` /
``changeTrailInfo``），所以只保留下面 3 个。

``baseURL`` 是 ``#{vehicleMonitor.baseUrl}/base/sysutil``，注意末尾**没有**
``/base``（与 ``HttpOdsLwzxsfsjFeeStationExit01Service`` 不同）。
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


def _base_url() -> str:
    return get_settings().vehicle_monitor.base_url + "/base/sysutil"


class HttpSysUtilApiService:
    """Java: ``interface HttpSysUtilApiService``."""

    # Java: TableDataInfo carTrackQueryByCarNo(@Query CarParaVO carParaVO)
    @staticmethod
    def car_track_query_by_car_no(car_para_vo: Any) -> TableDataInfo:
        payload = forest_get(
            _base_url(), "/carTrackQueryByCarNo", to_query_params(car_para_vo)
        )
        return to_table_data_info(payload)

    # Java: TableDataInfo carTrackQueryByTime(@Query CarParaVO carParaVO)
    @staticmethod
    def car_track_query_by_time(car_para_vo: Any) -> TableDataInfo:
        payload = forest_get(
            _base_url(), "/carTrackQueryByTime", to_query_params(car_para_vo)
        )
        return to_table_data_info(payload)

    # Java: TrailBo getByTrailBo(@Query TrailBo trailBo)
    @staticmethod
    def get_by_trail_bo(trail_bo: Any) -> Optional[Mapping[str, Any]]:
        payload = forest_get(_base_url(), "/getByTrailBo", to_query_params(trail_bo))
        return payload if isinstance(payload, Mapping) else None


__all__ = ["HttpSysUtilApiService"]
