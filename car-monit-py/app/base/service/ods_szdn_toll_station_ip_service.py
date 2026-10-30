"""收费站ip Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnTollStationIpService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnTollStationIpServiceImpl.java

两个方法都是纯转发（无 ``BaseMapper`` CRUD 调用），与
:mod:`app.base.service.ods_szdn_gantry_ip_service` 结构一致。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_szdn_toll_station_ip import OdsSzdnTollStationIp
from app.base.mapper.ods_szdn_toll_station_ip_mapper import OdsSzdnTollStationIpMapper


class OdsSzdnTollStationIpService:
    """Java: ``class OdsSzdnTollStationIpServiceImpl``."""

    def __init__(self, mapper: Optional[OdsSzdnTollStationIpMapper] = None) -> None:
        self._mapper = mapper or OdsSzdnTollStationIpMapper()

    # Java: OdsSzdnTollStationIp selectOdsSzdnTollStationIpById(Long id)
    def select_by_id(self, entity_id: int) -> Optional[OdsSzdnTollStationIp]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<OdsSzdnTollStationIp> selectOdsSzdnTollStationIpList(OdsSzdnTollStationIp x)
    def select_list(self, query: OdsSzdnTollStationIp) -> List[OdsSzdnTollStationIp]:
        """返回 ``PageList``（``List`` 子类），供 ``get_data_table`` 取分页元数据。"""
        return self._mapper.select_list(query)


_SERVICE: Optional[OdsSzdnTollStationIpService] = None


def get_ods_szdn_toll_station_ip_service() -> OdsSzdnTollStationIpService:
    """Java: ``@Autowired IOdsSzdnTollStationIpService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsSzdnTollStationIpService()
    return _SERVICE


def reset_ods_szdn_toll_station_ip_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsSzdnTollStationIpService",
    "get_ods_szdn_toll_station_ip_service",
    "reset_ods_szdn_toll_station_ip_service",
]
