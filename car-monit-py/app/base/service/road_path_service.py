"""路网最短路径 Service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IRoadPathService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/RoadPathImpl.java

``getShortestRoadPath`` 把接口响应里所有分段的所有坐标点按顺序摊平成一个
**字符串化的 JSON 数组**（``JSONArray.toString()``），失败一律返回 ``None``。

Java 里 ``pathList`` / ``routePoints`` 为 ``null`` 时会 NPE —— 整段被
``catch (Exception e)`` 兜住并返回 ``null``，这里照做（``TypeError`` 也是
``Exception``）。
"""

from __future__ import annotations

import json
from typing import Any, List, Optional

from app.base.domain.path_query_ro import PathQueryRo
from app.base.domain.res_data import ResData
from app.base.service.forest.road_path_api import RoadPathApi


class RoadPathService:
    """Java: ``class RoadPathImpl implements IRoadPathService``."""

    def __init__(self, road_path_api: Any = None) -> None:
        self._road_path_api = road_path_api or RoadPathApi

    # Java: public String getShortestRoadPath(List<String> nodeIds)
    def get_shortest_road_path(self, node_ids: List[str]) -> Optional[str]:
        ro = PathQueryRo()
        ro.node_ids = node_ids
        ro.path_type = "SHORTEST"
        ro.include_coordinates = "TRUE"
        ro.query_mode = "LENIENT"
        try:
            obj = self._road_path_api.get_road_path(ro)
            if obj is not None:
                success = obj.get("success")
                if success is not None and bool(success):
                    data = obj.get("data")
                    if data is not None:
                        array = data.get("data")
                        if array:
                            rtn: List[Any] = []
                            for item in array:
                                res_data = ResData.model_validate(item)
                                for segment in res_data.segment_routes or []:
                                    for point in segment.route_points or []:
                                        rtn.append(point)
                            if rtn:
                                return json.dumps(rtn, separators=(",", ":"))
        except Exception:  # noqa: BLE001 - Java 原文 catch (Exception e) { return null; }
            return None
        return None


_SERVICE: Optional[RoadPathService] = None


def get_road_path_service() -> RoadPathService:
    """Java: ``@Autowired IRoadPathService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = RoadPathService()
    return _SERVICE


def reset_road_path_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["RoadPathService", "get_road_path_service", "reset_road_path_service"]
