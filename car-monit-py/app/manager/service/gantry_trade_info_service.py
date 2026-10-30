"""门架交易查询 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/IGantryTradeInfoService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/GantryTradeInfoServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.gantry_trade_info_mapper import GantryTradeInfoMapper
from app.manager.service.manager_service import ManagerCrudService


class GantryTradeInfoService(ManagerCrudService):
    """Java: ``class GantryTradeInfoServiceImpl extends ServiceImpl<GantryTradeInfoMapper, GantryTradeInfo>``."""

    mapper_cls = GantryTradeInfoMapper


_SERVICE: Optional[GantryTradeInfoService] = None


def get_gantry_trade_info_service() -> GantryTradeInfoService:
    """Java: ``@Autowired IGantryTradeInfoService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = GantryTradeInfoService()
    return _SERVICE


def reset_gantry_trade_info_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "GantryTradeInfoService",
    "get_gantry_trade_info_service",
    "reset_gantry_trade_info_service",
]
