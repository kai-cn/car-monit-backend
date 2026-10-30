"""省界设备ip Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnGantryIpService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnGantryIpServiceImpl.java

Java 的 ``OdsSzdnGantryIpServiceImpl extends ServiceImpl<Mapper, Entity>``，但实现类
只有两个方法、都是**纯转发**给 XML 语句（没有任何 ``BaseMapper`` CRUD 调用），
所以这里也只保留这两个方法，不做多余封装。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_szdn_gantry_ip import OdsSzdnGantryIp
from app.base.mapper.ods_szdn_gantry_ip_mapper import OdsSzdnGantryIpMapper


class OdsSzdnGantryIpService:
    """Java: ``class OdsSzdnGantryIpServiceImpl``."""

    def __init__(self, mapper: Optional[OdsSzdnGantryIpMapper] = None) -> None:
        self._mapper = mapper or OdsSzdnGantryIpMapper()

    # Java: OdsSzdnGantryIp selectOdsSzdnGantryIpById(Long id)
    def select_by_id(self, entity_id: int) -> Optional[OdsSzdnGantryIp]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<OdsSzdnGantryIp> selectOdsSzdnGantryIpList(OdsSzdnGantryIp x)
    def select_list(self, query: OdsSzdnGantryIp) -> List[OdsSzdnGantryIp]:
        """返回 ``PageList``（``List`` 子类），供 ``get_data_table`` 取分页元数据。"""
        return self._mapper.select_list(query)


_SERVICE: Optional[OdsSzdnGantryIpService] = None


def get_ods_szdn_gantry_ip_service() -> OdsSzdnGantryIpService:
    """Java: ``@Autowired IOdsSzdnGantryIpService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsSzdnGantryIpService()
    return _SERVICE


def reset_ods_szdn_gantry_ip_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsSzdnGantryIpService",
    "get_ods_szdn_gantry_ip_service",
    "reset_ods_szdn_gantry_ip_service",
]
