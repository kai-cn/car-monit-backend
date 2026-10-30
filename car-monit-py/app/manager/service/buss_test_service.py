"""业务测试 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/IBussTestService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/BussTestServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.mapper.buss_test_mapper import BussTestMapper
from app.manager.service.manager_service import ManagerCrudService


class BussTestService(ManagerCrudService):
    """Java: ``class BussTestServiceImpl extends ServiceImpl<BussTestMapper, BussTest>``."""

    mapper_cls = BussTestMapper


_SERVICE: Optional[BussTestService] = None


def get_buss_test_service() -> BussTestService:
    """Java: ``@Autowired IBussTestService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = BussTestService()
    return _SERVICE


def reset_buss_test_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "BussTestService",
    "get_buss_test_service",
    "reset_buss_test_service",
]
