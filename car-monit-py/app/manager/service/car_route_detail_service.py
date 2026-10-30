"""常用路线明细 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarRouteDetailService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarRouteDetailServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.car_route_detail_mapper import CarRouteDetailMapper
from app.manager.service.manager_service import ManagerCrudService


class CarRouteDetailService(ManagerCrudService):
    """Java: ``class CarRouteDetailServiceImpl extends ServiceImpl<CarRouteDetailMapper, CarRouteDetail>``."""

    mapper_cls = CarRouteDetailMapper


_SERVICE: Optional[CarRouteDetailService] = None


def get_car_route_detail_service() -> CarRouteDetailService:
    """Java: ``@Autowired ICarRouteDetailService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarRouteDetailService()
    return _SERVICE


def reset_car_route_detail_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarRouteDetailService",
    "get_car_route_detail_service",
    "reset_car_route_detail_service",
]
