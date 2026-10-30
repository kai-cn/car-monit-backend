"""收费站入口数据 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeStationEnter01Service.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeStationEnter01ServiceImpl.java

纯转发，没有业务逻辑。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_lwzxsfsj_fee_station_enter01 import (
    OdsLwzxsfsjFeeStationEnter01,
)
from app.base.mapper.ods_lwzxsfsj_fee_station_enter01_mapper import (
    OdsLwzxsfsjFeeStationEnter01Mapper,
)


class OdsLwzxsfsjFeeStationEnter01Service:
    """Java: ``class OdsLwzxsfsjFeeStationEnter01ServiceImpl``."""

    def __init__(
        self, mapper: Optional[OdsLwzxsfsjFeeStationEnter01Mapper] = None
    ) -> None:
        self._mapper = mapper or OdsLwzxsfsjFeeStationEnter01Mapper()

    # Java: OdsLwzxsfsjFeeStationEnter01 selectOdsLwzxsfsjFeeStationEnter01ById(Long bigId)
    def select_by_id(self, entity_id: int) -> Optional[OdsLwzxsfsjFeeStationEnter01]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<OdsLwzxsfsjFeeStationEnter01> selectOdsLwzxsfsjFeeStationEnter01List(...)
    def select_list(
        self, query: OdsLwzxsfsjFeeStationEnter01
    ) -> List[OdsLwzxsfsjFeeStationEnter01]:
        return self._mapper.select_list(query)


_SERVICE: Optional[OdsLwzxsfsjFeeStationEnter01Service] = None


def get_ods_lwzxsfsj_fee_station_enter01_service() -> OdsLwzxsfsjFeeStationEnter01Service:
    """Java: ``@Autowired IOdsLwzxsfsjFeeStationEnter01Service``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsLwzxsfsjFeeStationEnter01Service()
    return _SERVICE


def reset_ods_lwzxsfsj_fee_station_enter01_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsLwzxsfsjFeeStationEnter01Service",
    "get_ods_lwzxsfsj_fee_station_enter01_service",
    "reset_ods_lwzxsfsj_fee_station_enter01_service",
]
