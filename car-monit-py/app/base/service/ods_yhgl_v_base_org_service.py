"""机构信息 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsYhglVBaseOrgService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsYhglVBaseOrgServiceImpl.java

生成器模板的 CRUD 部分见 :class:`~app.base.service.abstract_crud_service.AbstractCrudService`。
本表主键是 ``big_id``（不是 ``id``），所以 ``id_attribute`` 要显式覆盖。
"""

from __future__ import annotations

from typing import Any, List, Sequence

from app.base.mapper.ods_yhgl_v_base_org_mapper import OdsYhglVBaseOrgMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult


class OdsYhglVBaseOrgService(AbstractCrudService):
    """Java: ``class OdsYhglVBaseOrgServiceImpl``."""

    mapper_cls = OdsYhglVBaseOrgMapper
    #: Java: ``@TableId(value = "big_id", type = IdType.INPUT)``
    id_attribute = "big_id"

    # Java: AjaxResult deleteOdsYhglVBaseOrgByIds(String[] bigIds)
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_ods_yhgl_v_base_org_by_ids")

    # Java: AjaxResult deleteOdsYhglVBaseOrgById(String bigId)
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_by_id(entity_id))

    # Java: void truncateTable()
    def truncate_table(self) -> int:
        return self._mapper.truncate_table()

    # Java: ``baseOrgService.lambdaQuery().select(orgCode, orgName).list()``
    def select_org_list(self) -> List[Any]:
        """大屏 ``/orgList`` 用的两列投影（``org_code`` / ``org_name``）。"""
        return self._mapper.select_org_list()


_SERVICE: OdsYhglVBaseOrgService | None = None


def get_ods_yhgl_v_base_org_service() -> OdsYhglVBaseOrgService:
    """Java: ``@Autowired IOdsYhglVBaseOrgService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsYhglVBaseOrgService()
    return _SERVICE


def reset_ods_yhgl_v_base_org_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsYhglVBaseOrgService",
    "get_ods_yhgl_v_base_org_service",
    "reset_ods_yhgl_v_base_org_service",
]
