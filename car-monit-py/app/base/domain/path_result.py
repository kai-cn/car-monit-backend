"""路网路径结果（``PathResult``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/PathResult.java
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.path import Path
from app.common.core.domain.domain_model import DomainModel


class PathResult(DomainModel):
    """Java: ``com.ruoyi.base.domain.PathResult``."""

    path: Optional[List[Path]] = None
    total_mileage: Optional[float] = None


__all__ = ["PathResult"]
