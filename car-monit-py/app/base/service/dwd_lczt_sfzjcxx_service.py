"""收费站基础信息 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztSfzjcxxService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztSfzjcxxServiceImpl.java

主键是 ``agent_pk``；CRUD 公共部分见
:class:`~app.base.service.abstract_crud_service.AbstractCrudService`。
"""

from __future__ import annotations

from typing import Sequence

from app.base.mapper.dwd_lczt_sfzjcxx_mapper import DwdLcztSfzjcxxMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult


class DwdLcztSfzjcxxService(AbstractCrudService):
    """Java: ``class DwdLcztSfzjcxxServiceImpl``."""

    mapper_cls = DwdLcztSfzjcxxMapper
    #: Java: ``@TableId(value = "agent_pk", type = IdType.INPUT)``
    id_attribute = "agent_pk"

    # Java: AjaxResult deleteDwdLcztSfzjcxxByIds(String[] agentPks)
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_dwd_lczt_sfzjcxx_by_ids")

    # Java: AjaxResult deleteDwdLcztSfzjcxxById(String agentPk)
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_by_id(entity_id))

    # Java: void truncateTable()
    def truncate_table(self) -> int:
        return self._mapper.truncate_table()


_SERVICE: DwdLcztSfzjcxxService | None = None


def get_dwd_lczt_sfzjcxx_service() -> DwdLcztSfzjcxxService:
    """Java: ``@Autowired IDwdLcztSfzjcxxService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = DwdLcztSfzjcxxService()
    return _SERVICE


def reset_dwd_lczt_sfzjcxx_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "DwdLcztSfzjcxxService",
    "get_dwd_lczt_sfzjcxx_service",
    "reset_dwd_lczt_sfzjcxx_service",
]
