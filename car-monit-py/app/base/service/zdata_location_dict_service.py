"""车辆位置 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataLocationDictService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataLocationDictServiceImpl.java

Java 接口只声明了两件事：``selectZdataLocationDictById(Long)`` 与
``selectZdataLocationDictList``（对应 ``ZdataLocationDictController`` 的两条只读
端点）。``IService`` 里那些 ``save`` / ``remove`` 之类在本项目**没有调用点**，
因此这里不额外实现 —— 见 ``COMPATIBILITY.md`` 的"未迁移但无调用点"清单。
"""

from __future__ import annotations

from app.base.mapper.zdata_location_dict_mapper import ZdataLocationDictMapper
from app.base.service.abstract_crud_service import AbstractCrudService


class ZdataLocationDictService(AbstractCrudService):
    """Java: ``class ZdataLocationDictServiceImpl``."""

    mapper_cls = ZdataLocationDictMapper
    #: Java: ``selectZdataLocationDictById(Long id)`` —— ``where t.id = #{id}``
    id_attribute = "id"

    # Java: ZdataLocationDict selectZdataLocationDictById(Long id)  —— 见基类 select_by_id
    # Java: List<ZdataLocationDict> selectZdataLocationDictList(...)  —— 见基类 select_list


_SERVICE: ZdataLocationDictService | None = None


def get_zdata_location_dict_service() -> ZdataLocationDictService:
    """Java: ``@Autowired IZdataLocationDictService``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ZdataLocationDictService()
    return _SERVICE


def reset_zdata_location_dict_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "ZdataLocationDictService",
    "get_zdata_location_dict_service",
    "reset_zdata_location_dict_service",
]
