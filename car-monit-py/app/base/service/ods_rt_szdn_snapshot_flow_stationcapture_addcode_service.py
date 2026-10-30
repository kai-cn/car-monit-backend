"""收费站抓拍 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowStationcaptureAddcodeService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowStationcaptureAddcodeServiceImpl.java

纯转发，没有业务逻辑。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_rt_szdn_snapshot_flow_stationcapture_addcode import (
    OdsRtSzdnSnapshotFlowStationcaptureAddcode,
)
from app.base.mapper.ods_rt_szdn_snapshot_flow_stationcapture_addcode_mapper import (
    OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper,
)


class OdsRtSzdnSnapshotFlowStationcaptureAddcodeService:
    """Java: ``class OdsRtSzdnSnapshotFlowStationcaptureAddcodeServiceImpl``."""

    def __init__(
        self,
        mapper: Optional[OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper] = None,
    ) -> None:
        self._mapper = mapper or OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper()

    # Java: OdsRtSzdnSnapshotFlowStationcaptureAddcode select...ById(Long bigId)
    def select_by_id(
        self, entity_id: int
    ) -> Optional[OdsRtSzdnSnapshotFlowStationcaptureAddcode]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<OdsRtSzdnSnapshotFlowStationcaptureAddcode> select...List(...)
    def select_list(
        self, query: OdsRtSzdnSnapshotFlowStationcaptureAddcode
    ) -> List[OdsRtSzdnSnapshotFlowStationcaptureAddcode]:
        return self._mapper.select_list(query)


_SERVICE: Optional[OdsRtSzdnSnapshotFlowStationcaptureAddcodeService] = None


def get_ods_rt_szdn_snapshot_flow_stationcapture_addcode_service() -> (
    OdsRtSzdnSnapshotFlowStationcaptureAddcodeService
):
    """Java: ``@Autowired IOdsRtSzdnSnapshotFlowStationcaptureAddcodeService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsRtSzdnSnapshotFlowStationcaptureAddcodeService()
    return _SERVICE


def reset_ods_rt_szdn_snapshot_flow_stationcapture_addcode_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsRtSzdnSnapshotFlowStationcaptureAddcodeService",
    "get_ods_rt_szdn_snapshot_flow_stationcapture_addcode_service",
    "reset_ods_rt_szdn_snapshot_flow_stationcapture_addcode_service",
]
