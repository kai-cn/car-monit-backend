"""收费所基础信息 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztSfsjcxxService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztSfsjcxxServiceImpl.java

主键是 ``agent_pk``；CRUD 公共部分见
:class:`~app.base.service.abstract_crud_service.AbstractCrudService`。
本模块没有 ``selectXxxListNew``（XML 里没有这条语句）。
"""

from __future__ import annotations

from typing import Sequence

from app.base.mapper.dwd_lczt_sfsjcxx_mapper import DwdLcztSfsjcxxMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult
from app.config.database import transactional


class DwdLcztSfsjcxxService(AbstractCrudService):
    """Java: ``class DwdLcztSfsjcxxServiceImpl``."""

    mapper_cls = DwdLcztSfsjcxxMapper
    #: Java: ``@TableId(value = "agent_pk", type = IdType.INPUT)``
    id_attribute = "agent_pk"

    # Java: AjaxResult deleteDwdLcztSfsjcxxByIds(String[] agentPks)
    @transactional
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_dwd_lczt_sfsjcxx_by_ids")

    # Java: AjaxResult deleteDwdLcztSfsjcxxById(String agentPk)
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_by_id(entity_id))

    # Java: void truncateTable()
    def truncate_table(self) -> int:
        return self._mapper.truncate_table()


_SERVICE: DwdLcztSfsjcxxService | None = None


def get_dwd_lczt_sfsjcxx_service() -> DwdLcztSfsjcxxService:
    """Java: ``@Autowired IDwdLcztSfsjcxxService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = DwdLcztSfsjcxxService()
    return _SERVICE


def reset_dwd_lczt_sfsjcxx_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "DwdLcztSfsjcxxService",
    "get_dwd_lczt_sfsjcxx_service",
    "reset_dwd_lczt_sfsjcxx_service",
]
