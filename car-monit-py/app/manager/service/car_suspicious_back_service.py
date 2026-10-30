"""可疑车辆备份 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousBackService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousBackServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.car_suspicious_back_mapper import CarSuspiciousBackMapper
from app.manager.service.manager_service import ManagerCrudService


class CarSuspiciousBackService(ManagerCrudService):
    """Java: ``class CarSuspiciousBackServiceImpl extends ServiceImpl<CarSuspiciousBackMapper, CarSuspiciousBack>``."""

    mapper_cls = CarSuspiciousBackMapper


_SERVICE: Optional[CarSuspiciousBackService] = None


def get_car_suspicious_back_service() -> CarSuspiciousBackService:
    """Java: ``@Autowired ICarSuspiciousBackService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarSuspiciousBackService()
    return _SERVICE


def reset_car_suspicious_back_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarSuspiciousBackService",
    "get_car_suspicious_back_service",
    "reset_car_suspicious_back_service",
]
