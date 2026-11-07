"""服务区基础信息 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztFwqjcxxService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztFwqjcxxServiceImpl.java

主键是 ``agent_pk``；CRUD 公共部分见
:class:`~app.base.service.abstract_crud_service.AbstractCrudService`。
本模块独有的是 ``selectDwdLcztFwqjcxxListNew``（``distinct fwqbm, fwqmc``）与
``truncateTable``（Java 用 ``@Update("TRUNCATE TABLE dwd_lczt_fwqjcxx")``）。
"""

from __future__ import annotations

from typing import Any, List, Sequence

from app.base.mapper.dwd_lczt_fwqjcxx_mapper import DwdLcztFwqjcxxMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult
from app.config.database import transactional


class DwdLcztFwqjcxxService(AbstractCrudService):
    """Java: ``class DwdLcztFwqjcxxServiceImpl``."""

    mapper_cls = DwdLcztFwqjcxxMapper
    #: Java: ``@TableId(value = "agent_pk", type = IdType.INPUT)``
    id_attribute = "agent_pk"

    # Java: List<DwdLcztFwqjcxx> selectDwdLcztFwqjcxxListNew(DwdLcztFwqjcxx x)
    def select_list_new(self, query: Any) -> List[Any]:
        return self._mapper.select_list_new(query)

    # Java: AjaxResult deleteDwdLcztFwqjcxxByIds(String[] agentPks)
    @transactional
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_dwd_lczt_fwqjcxx_by_ids")

    # Java: AjaxResult deleteDwdLcztFwqjcxxById(String agentPk)
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_by_id(entity_id))

    # Java: void truncateTable()
    def truncate_table(self) -> int:
        return self._mapper.truncate_table()


_SERVICE: DwdLcztFwqjcxxService | None = None


def get_dwd_lczt_fwqjcxx_service() -> DwdLcztFwqjcxxService:
    """Java: ``@Autowired IDwdLcztFwqjcxxService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = DwdLcztFwqjcxxService()
    return _SERVICE


def reset_dwd_lczt_fwqjcxx_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "DwdLcztFwqjcxxService",
    "get_dwd_lczt_fwqjcxx_service",
    "reset_dwd_lczt_fwqjcxx_service",
]
