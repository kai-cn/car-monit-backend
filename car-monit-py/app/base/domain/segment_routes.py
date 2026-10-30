"""路网分段路径（``SegmentRoutes``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/SegmentRoutes.java

``route_points`` 是 ``List<List<Double>>`` —— 每段是一串 ``[lon, lat]`` 点对。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.core.domain.domain_model import DomainModel


class SegmentRoutes(DomainModel):
    """Java: ``com.ruoyi.base.domain.SegmentRoutes``."""

    start_node_id: Optional[str] = None
    end_node_id: Optional[str] = None
    start_title: Optional[str] = None
    end_title: Optional[str] = None
    route_points: Optional[List[List[float]]] = None


__all__ = ["SegmentRoutes"]
