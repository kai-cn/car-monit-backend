"""路网接口响应体（``ResData``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/ResData.java
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.path_result import PathResult
from app.base.domain.segment_routes import SegmentRoutes
from app.common.core.domain.domain_model import DomainModel


class ResData(DomainModel):
    """Java: ``com.ruoyi.base.domain.ResData``."""

    path_result: Optional[PathResult] = None
    segment_routes: Optional[List[SegmentRoutes]] = None
    path_index: Optional[int] = None
    node_count: Optional[int] = None
    total_point_count: Optional[int] = None
    total_mileage: Optional[float] = None


__all__ = ["ResData"]
