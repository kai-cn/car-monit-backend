"""路网节点（``Path``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/Path.java
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class Path(DomainModel):
    """Java: ``com.ruoyi.base.domain.Path``."""

    node_id: Optional[str] = None
    label: Optional[str] = None
    title: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    after_mileage: Optional[float] = None
    front_mileage: Optional[float] = None
    mileage: Optional[float] = None
    org_name: Optional[str] = None
    section: Optional[str] = None
    direction: Optional[int] = None


__all__ = ["Path"]
