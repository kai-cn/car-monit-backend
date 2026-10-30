"""可疑车辆人工核实 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousCheckService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousCheckServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.ajax_result import AjaxResult
from app.manager.mapper.car_suspicious_check_mapper import CarSuspiciousCheckMapper
from app.manager.service.manager_service import ManagerCrudService


class CarSuspiciousCheckService(ManagerCrudService):
    """Java: ``class CarSuspiciousCheckServiceImpl extends ServiceImpl<CarSuspiciousCheckMapper, CarSuspiciousCheck>``."""

    mapper_cls = CarSuspiciousCheckMapper

    # Java: AjaxResult deleteCarSuspiciousCheckBySuspiciousId(String fkId)
    def delete_by_suspicious_id(self, fk_id: str) -> AjaxResult:
        """根据外键（可疑车辆 id）删除核实明细 —— **物理删除**。"""
        count = self._mapper.delete_by_suspicious_id(fk_id)
        return AjaxResult.success_data(count)


_SERVICE: Optional[CarSuspiciousCheckService] = None


def get_car_suspicious_check_service() -> CarSuspiciousCheckService:
    """Java: ``@Autowired ICarSuspiciousCheckService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarSuspiciousCheckService()
    return _SERVICE


def reset_car_suspicious_check_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarSuspiciousCheckService",
    "get_car_suspicious_check_service",
    "reset_car_suspicious_check_service",
]
