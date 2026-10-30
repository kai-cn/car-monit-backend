"""车辆出入口拟合轨迹 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataTrailFittingService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailFittingServiceImpl.java

Java 接口只声明了 ``selectZdataTrailFittingById(String cid)`` 与
``selectZdataTrailFittingList``（对应控制器两条只读端点）。主键列是 ``cid``，
不是 ``id``。``IService`` 的写方法在本项目没有调用点，故不实现。
"""

from __future__ import annotations

from app.base.mapper.zdata_trail_fitting_mapper import ZdataTrailFittingMapper
from app.base.service.abstract_crud_service import AbstractCrudService


class ZdataTrailFittingService(AbstractCrudService):
    """Java: ``class ZdataTrailFittingServiceImpl``."""

    mapper_cls = ZdataTrailFittingMapper
    #: Java: ``selectZdataTrailFittingById(String cid)`` —— ``where t.cid = #{cid}``
    id_attribute = "cid"

    # Java: ZdataTrailFitting selectZdataTrailFittingById(String cid)  —— 见基类
    # Java: List<ZdataTrailFitting> selectZdataTrailFittingList(...)  —— 见基类


_SERVICE: ZdataTrailFittingService | None = None


def get_zdata_trail_fitting_service() -> ZdataTrailFittingService:
    """Java: ``@Autowired IZdataTrailFittingService``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ZdataTrailFittingService()
    return _SERVICE


def reset_zdata_trail_fitting_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "ZdataTrailFittingService",
    "get_zdata_trail_fitting_service",
    "reset_zdata_trail_fitting_service",
]
