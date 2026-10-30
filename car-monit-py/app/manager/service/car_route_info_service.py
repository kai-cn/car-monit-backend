"""常用路线 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarRouteInfoService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarRouteInfoServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.car_route_info_mapper import CarRouteInfoMapper
from app.manager.service.manager_service import ManagerCrudService


class CarRouteInfoService(ManagerCrudService):
    """Java: ``class CarRouteInfoServiceImpl extends ServiceImpl<CarRouteInfoMapper, CarRouteInfo>``."""

    mapper_cls = CarRouteInfoMapper


_SERVICE: Optional[CarRouteInfoService] = None


def get_car_route_info_service() -> CarRouteInfoService:
    """Java: ``@Autowired ICarRouteInfoService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarRouteInfoService()
    return _SERVICE


def reset_car_route_info_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarRouteInfoService",
    "get_car_route_info_service",
    "reset_car_route_info_service",
]
