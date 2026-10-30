"""省界称重 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnProvinceBorderVehicleWeightNewstructureService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnProvinceBorderVehicleWeightNewstructureServiceImpl.java

纯转发，没有业务逻辑。注意详情方法的入参是 **``String dataSource``**（不是
``datauuid``），与 XML 的 ``where t.dataSource = #{dataSource}`` 对应。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_szdn_province_border_vehicle_weight_newstructure import (
    OdsSzdnProvinceBorderVehicleWeightNewstructure,
)
from app.base.mapper.ods_szdn_province_border_vehicle_weight_newstructure_mapper import (
    OdsSzdnProvinceBorderVehicleWeightNewstructureMapper,
)


class OdsSzdnProvinceBorderVehicleWeightNewstructureService:
    """Java: ``class OdsSzdnProvinceBorderVehicleWeightNewstructureServiceImpl``."""

    def __init__(
        self,
        mapper: Optional[OdsSzdnProvinceBorderVehicleWeightNewstructureMapper] = None,
    ) -> None:
        self._mapper = mapper or OdsSzdnProvinceBorderVehicleWeightNewstructureMapper()

    # Java: OdsSzdnProvinceBorderVehicleWeightNewstructure select...ById(String dataSource)
    def select_by_id(
        self, data_source: str
    ) -> Optional[OdsSzdnProvinceBorderVehicleWeightNewstructure]:
        return self._mapper.select_by_id(data_source)

    # Java: List<OdsSzdnProvinceBorderVehicleWeightNewstructure> select...List(...)
    def select_list(
        self, query: OdsSzdnProvinceBorderVehicleWeightNewstructure
    ) -> List[OdsSzdnProvinceBorderVehicleWeightNewstructure]:
        return self._mapper.select_list(query)


_SERVICE: Optional[OdsSzdnProvinceBorderVehicleWeightNewstructureService] = None


def get_ods_szdn_province_border_vehicle_weight_newstructure_service() -> (
    OdsSzdnProvinceBorderVehicleWeightNewstructureService
):
    """Java: ``@Autowired IOdsSzdnProvinceBorderVehicleWeightNewstructureService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsSzdnProvinceBorderVehicleWeightNewstructureService()
    return _SERVICE


def reset_ods_szdn_province_border_vehicle_weight_newstructure_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsSzdnProvinceBorderVehicleWeightNewstructureService",
    "get_ods_szdn_province_border_vehicle_weight_newstructure_service",
    "reset_ods_szdn_province_border_vehicle_weight_newstructure_service",
]
