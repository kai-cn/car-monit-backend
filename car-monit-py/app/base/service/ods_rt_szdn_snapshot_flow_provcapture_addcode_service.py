"""省界抓拍 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowProvcaptureAddcodeServiceImpl.java

纯转发，没有业务逻辑。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_rt_szdn_snapshot_flow_provcapture_addcode import (
    OdsRtSzdnSnapshotFlowProvcaptureAddcode,
)
from app.base.mapper.ods_rt_szdn_snapshot_flow_provcapture_addcode_mapper import (
    OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper,
)


class OdsRtSzdnSnapshotFlowProvcaptureAddcodeService:
    """Java: ``class OdsRtSzdnSnapshotFlowProvcaptureAddcodeServiceImpl``."""

    def __init__(
        self,
        mapper: Optional[OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper] = None,
    ) -> None:
        self._mapper = mapper or OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper()

    # Java: OdsRtSzdnSnapshotFlowProvcaptureAddcode select...ById(Long bigId)
    def select_by_id(
        self, entity_id: int
    ) -> Optional[OdsRtSzdnSnapshotFlowProvcaptureAddcode]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<OdsRtSzdnSnapshotFlowProvcaptureAddcode> select...List(...)
    def select_list(
        self, query: OdsRtSzdnSnapshotFlowProvcaptureAddcode
    ) -> List[OdsRtSzdnSnapshotFlowProvcaptureAddcode]:
        return self._mapper.select_list(query)


_SERVICE: Optional[OdsRtSzdnSnapshotFlowProvcaptureAddcodeService] = None


def get_ods_rt_szdn_snapshot_flow_provcapture_addcode_service() -> (
    OdsRtSzdnSnapshotFlowProvcaptureAddcodeService
):
    """Java: ``@Autowired IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsRtSzdnSnapshotFlowProvcaptureAddcodeService()
    return _SERVICE


def reset_ods_rt_szdn_snapshot_flow_provcapture_addcode_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsRtSzdnSnapshotFlowProvcaptureAddcodeService",
    "get_ods_rt_szdn_snapshot_flow_provcapture_addcode_service",
    "reset_ods_rt_szdn_snapshot_flow_provcapture_addcode_service",
]
