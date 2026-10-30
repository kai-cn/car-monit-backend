"""收费站基础信息 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnTollService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnTollServiceImpl.java

生成器模板的 CRUD 部分见 :class:`~app.base.service.abstract_crud_service.AbstractCrudService`；
本模块独有的是 ``selectOdsSzdnTollListNew``（去重投影）与 ``truncateTable``。
"""

from __future__ import annotations

from typing import Any, List, Sequence

from app.base.mapper.ods_szdn_toll_mapper import OdsSzdnTollMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult


class OdsSzdnTollService(AbstractCrudService):
    """Java: ``class OdsSzdnTollServiceImpl``."""

    mapper_cls = OdsSzdnTollMapper
    #: Java: ``@TableId(value = "id", type = IdType.INPUT)``
    id_attribute = "id"

    # Java: List<OdsSzdnToll> selectOdsSzdnTollListNew(OdsSzdnToll x)
    def select_list_new(self, query: Any) -> List[Any]:
        return self._mapper.select_list_new(query)

    # Java: AjaxResult deleteOdsSzdnTollByIds(String[] ids)
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_ods_szdn_toll_by_ids")

    # Java: AjaxResult deleteOdsSzdnTollById(String id)
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_by_id(entity_id))

    # Java: void truncateTable()
    def truncate_table(self) -> int:
        return self._mapper.truncate_table()


_SERVICE: OdsSzdnTollService | None = None


def get_ods_szdn_toll_service() -> OdsSzdnTollService:
    """Java: ``@Autowired IOdsSzdnTollService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsSzdnTollService()
    return _SERVICE


def reset_ods_szdn_toll_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsSzdnTollService",
    "get_ods_szdn_toll_service",
    "reset_ods_szdn_toll_service",
]
