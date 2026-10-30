"""收费流水 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarFeeRecordService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarFeeRecordServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.car_fee_record_mapper import CarFeeRecordMapper
from app.manager.service.manager_service import ManagerCrudService


class CarFeeRecordService(ManagerCrudService):
    """Java: ``class CarFeeRecordServiceImpl extends ServiceImpl<CarFeeRecordMapper, CarFeeRecord>``."""

    mapper_cls = CarFeeRecordMapper


_SERVICE: Optional[CarFeeRecordService] = None


def get_car_fee_record_service() -> CarFeeRecordService:
    """Java: ``@Autowired ICarFeeRecordService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarFeeRecordService()
    return _SERVICE


def reset_car_fee_record_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarFeeRecordService",
    "get_car_fee_record_service",
    "reset_car_fee_record_service",
]
