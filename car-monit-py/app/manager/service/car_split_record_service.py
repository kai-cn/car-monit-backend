"""拆分流水 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSplitRecordService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSplitRecordServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.car_split_record_mapper import CarSplitRecordMapper
from app.manager.service.manager_service import ManagerCrudService


class CarSplitRecordService(ManagerCrudService):
    """Java: ``class CarSplitRecordServiceImpl extends ServiceImpl<CarSplitRecordMapper, CarSplitRecord>``."""

    mapper_cls = CarSplitRecordMapper


_SERVICE: Optional[CarSplitRecordService] = None


def get_car_split_record_service() -> CarSplitRecordService:
    """Java: ``@Autowired ICarSplitRecordService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarSplitRecordService()
    return _SERVICE


def reset_car_split_record_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarSplitRecordService",
    "get_car_split_record_service",
    "reset_car_split_record_service",
]
