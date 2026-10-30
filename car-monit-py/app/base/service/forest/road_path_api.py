"""路网路径接口 —— Forest 客户端.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/RoadPathApi.java

Java 原文::

    @BaseRequest(baseURL = "#{roadPathUrl}")
    public interface RoadPathApi {
        @Post(url = "/api/routes/query")
        public JSONObject getRoadPath(@JSONBody PathQueryRo queryRo);
    }

``baseURL`` 取自 ``application.yml`` 的 ``roadPathUrl``（Python 侧
``settings.road_path_url``）。返回裸 ``JSONObject``，不做强类型转换 ——
``RoadPathImpl`` 自己一层层往下取 ``data.data[].segmentRoutes[].routePoints``。
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from app.base.service.forest.forest_client import forest_post
from app.settings import get_settings


class RoadPathApi:
    """Java: ``interface RoadPathApi``."""

    # Java: JSONObject getRoadPath(@JSONBody PathQueryRo queryRo)
    @staticmethod
    def get_road_path(query_ro: Any) -> Optional[Mapping[str, Any]]:
        payload = forest_post(get_settings().road_path_url, "/api/routes/query", query_ro)
        return payload if isinstance(payload, Mapping) else None


__all__ = ["RoadPathApi"]
