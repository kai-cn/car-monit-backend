"""门架拍识查询 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/IGantryCarService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/GantryCarServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.gantry_car_mapper import GantryCarMapper
from app.manager.service.manager_service import ManagerCrudService


class GantryCarService(ManagerCrudService):
    """Java: ``class GantryCarServiceImpl extends ServiceImpl<GantryCarMapper, GantryCar>``."""

    mapper_cls = GantryCarMapper


_SERVICE: Optional[GantryCarService] = None


def get_gantry_car_service() -> GantryCarService:
    """Java: ``@Autowired IGantryCarService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = GantryCarService()
    return _SERVICE


def reset_gantry_car_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "GantryCarService",
    "get_gantry_car_service",
    "reset_gantry_car_service",
]
