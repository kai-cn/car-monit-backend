"""基础-收费流水 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeRecords01Service.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeRecords01ServiceImpl.java

生成器模板的四段 CRUD，公共部分见
:class:`~app.base.service.abstract_crud_service.AbstractCrudService`；
主键是 ``big_id``（``@TableId(type = IdType.INPUT)``），判据 ``isNotBlank(bigId)``。
"""

from __future__ import annotations

from typing import Sequence

from app.base.mapper.ods_lwzxsfsj_fee_records01_mapper import OdsLwzxsfsjFeeRecords01Mapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult


class OdsLwzxsfsjFeeRecords01Service(AbstractCrudService):
    """Java: ``class OdsLwzxsfsjFeeRecords01ServiceImpl``."""

    mapper_cls = OdsLwzxsfsjFeeRecords01Mapper
    #: Java: ``@TableId(value = "big_id", type = IdType.INPUT)``
    id_attribute = "big_id"

    # Java: AjaxResult deleteOdsLwzxsfsjFeeRecords01ByIds(String[] bigIds)
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_ods_lwzxsfsj_fee_records01_by_ids")


_SERVICE: OdsLwzxsfsjFeeRecords01Service | None = None


def get_ods_lwzxsfsj_fee_records01_service() -> OdsLwzxsfsjFeeRecords01Service:
    """Java: ``@Autowired IOdsLwzxsfsjFeeRecords01Service``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsLwzxsfsjFeeRecords01Service()
    return _SERVICE


def reset_ods_lwzxsfsj_fee_records01_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsLwzxsfsjFeeRecords01Service",
    "get_ods_lwzxsfsj_fee_records01_service",
    "reset_ods_lwzxsfsj_fee_records01_service",
]
