"""路段信息 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnSectionService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnSectionServiceImpl.java

四个 Xxx 方法是同一段生成器模板（``isNotBlank(id) ? updateById : insert``），
公共部分在 :class:`~app.base.service.abstract_crud_service.AbstractCrudService`；
这里只写本模块**独有**的语句：

* ``selectOdsSzdnSectionListNew`` —— distinct 的轻量投影，供大屏 / 下拉框用；
* ``truncateTable`` —— 全表清空。

``@Transactional(rollbackFor = Exception.class)`` 未复刻（见 ``COMPATIBILITY.md``
§28.3）：本类每个方法只发一条 SQL，没有原子性问题。
"""

from __future__ import annotations

from typing import Any, List, Sequence

from app.base.mapper.ods_szdn_section_mapper import OdsSzdnSectionMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult
from app.config.database import transactional


class OdsSzdnSectionService(AbstractCrudService):
    """Java: ``class OdsSzdnSectionServiceImpl``."""

    mapper_cls = OdsSzdnSectionMapper
    #: Java: ``@TableId(value = "id", type = IdType.INPUT)`` —— INPUT 表示主键由调用方给。
    id_attribute = "id"

    # Java: AjaxResult saveOdsSzdnSection(OdsSzdnSection x) —— 见基类 save()
    # Java: List<OdsSzdnSection> selectOdsSzdnSectionList(OdsSzdnSection x) —— 见基类

    # Java: List<OdsSzdnSection> selectOdsSzdnSectionListNew(OdsSzdnSection x)
    def select_list_new(self, query: Any) -> List[Any]:
        """不分页：``distinct section_code, concat(road_code,'',section_name)``。"""
        return self._mapper.select_list_new(query)

    # Java: AjaxResult deleteOdsSzdnSectionByIds(String[] ids)
    @transactional
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_ods_szdn_section_by_ids")

    # Java: AjaxResult deleteOdsSzdnSectionById(String id)
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_by_id(entity_id))

    # Java: void truncateTable()
    def truncate_table(self) -> int:
        return self._mapper.truncate_table()


_SERVICE: OdsSzdnSectionService | None = None


def get_ods_szdn_section_service() -> OdsSzdnSectionService:
    """Java: ``@Autowired IOdsSzdnSectionService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsSzdnSectionService()
    return _SERVICE


def reset_ods_szdn_section_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsSzdnSectionService",
    "get_ods_szdn_section_service",
    "reset_ods_szdn_section_service",
]
