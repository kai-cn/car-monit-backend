"""服务区车辆流水 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsCxztFwqcllsService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsCxztFwqcllsServiceImpl.java

Java 的 ``OdsCxztFwqcllsServiceImpl extends ServiceImpl<Mapper, Entity>``，实现类里
只有两个方法、都是**纯转发**给 XML 语句（没有任何 ``BaseMapper`` CRUD 调用），
所以这里也只保留这两个方法。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_cxzt_fwqclls import OdsCxztFwqclls
from app.base.mapper.ods_cxzt_fwqclls_mapper import OdsCxztFwqcllsMapper


class OdsCxztFwqcllsService:
    """Java: ``class OdsCxztFwqcllsServiceImpl``."""

    def __init__(self, mapper: Optional[OdsCxztFwqcllsMapper] = None) -> None:
        self._mapper = mapper or OdsCxztFwqcllsMapper()

    # Java: OdsCxztFwqclls selectOdsCxztFwqcllsById(Long bigId)
    def select_by_id(self, entity_id: int) -> Optional[OdsCxztFwqclls]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<OdsCxztFwqclls> selectOdsCxztFwqcllsList(OdsCxztFwqclls x)
    def select_list(self, query: OdsCxztFwqclls) -> List[OdsCxztFwqclls]:
        """返回 ``PageList``（``List`` 子类），供 ``get_data_table`` 取分页元数据。"""
        return self._mapper.select_list(query)


_SERVICE: Optional[OdsCxztFwqcllsService] = None


def get_ods_cxzt_fwqclls_service() -> OdsCxztFwqcllsService:
    """Java: ``@Autowired IOdsCxztFwqcllsService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsCxztFwqcllsService()
    return _SERVICE


def reset_ods_cxzt_fwqclls_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsCxztFwqcllsService",
    "get_ods_cxzt_fwqclls_service",
    "reset_ods_cxzt_fwqclls_service",
]
