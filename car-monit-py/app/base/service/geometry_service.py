"""几何对象（路线桩号 → 路径点）Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IGeometryService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/GeometryServiceImpl.java

CRUD 公共部分见 :class:`~app.base.service.abstract_crud_service.AbstractCrudService`；
本模块独有的是**缓存联动**：

* ``updateRedisList()`` —— 把 ``lxfx = '1'`` 且 ``lxbh`` / ``paths`` 都非空的记录
  写进 Redis（``Constants.lxbh_jdwd``），供「按路线取路径点」使用；
* ``getRedisList()`` —— 读缓存并按 ``lxbh`` 分组；缓存空则回填；
* ``getListByCode()`` —— Java 里整段循环被注释掉，恒返回空列表（**照抄**）。

主键判据是 ``null != geometry.getId()``（Integer），与生成器模板的
``CommonUtil.isNotBlank(...)`` 不同 —— 所以 ``blank_check = False``：
只要不是 ``None`` 就走 ``updateById``，``0`` 也算有主键。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.base.mapper.geometry_mapper import GeometryMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.constant.constants import lxbh_jdwd
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.common_util import is_not_blank, is_null


def _read_field(item: Any, name: str) -> Any:
    """``item.name`` / ``item[name]`` 双通道读取.

    Java 侧缓存里是 ``List<Geometry>``（FastJson2 反序列化后仍是 ``Geometry``）；
    Python 侧 ``RedisCache`` 存的是 JSON，取回来是 ``dict``，所以两种形态都要认。
    """
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)


class GeometryService(AbstractCrudService):
    """Java: ``class GeometryServiceImpl``."""

    mapper_cls = GeometryMapper
    #: Java: ``@TableId(value = "id", type = IdType.INPUT)``
    id_attribute = "id"
    #: Java: ``if (null != geometry.getId())`` —— **不是** ``isNotBlank``
    blank_check = False

    def __init__(self, mapper: Any = None, redis_cache: Optional[RedisCache] = None) -> None:
        super().__init__(mapper)
        self._redis_cache = redis_cache

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache``."""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    # Java: AjaxResult saveGeometry(Geometry geometry)
    def save(self, entity: Any) -> AjaxResult:
        result = super().save(entity)
        # Java: this.updateRedisList();  —— 写库之后无条件刷新整份缓存
        self.update_redis_list()
        return result

    # Java: AjaxResult deleteGeometryByIds(Integer[] IDs)
    def delete_by_ids(self, ids: Sequence[int]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_geometry_by_ids")

    # Java: AjaxResult deleteGeometryById(Integer ID)
    def delete_by_id(self, entity_id: int) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_geometry_by_id(entity_id))

    # Java: List<Geometry> updateRedisList()
    def update_redis_list(self) -> List[Any]:
        """回源查询 ``lxfx = '1'`` 的几何数据，过滤后整份写入缓存.

        返回值是**未过滤**的全量查询结果（Java 原文 ``return list;``），
        而写进 Redis 的是过滤后的 ``rtnlist`` —— 这个不对称是 Java 的既有行为。
        """
        query = self._mapper.entity_cls()
        query.lxfx = "1"
        rows: List[Any] = list(self._mapper.select_list(query))

        cached: List[Any] = []
        for item in rows:
            road_code = is_null(_read_field(item, "lxbh"))
            pile_no = is_null(_read_field(item, "paths"))
            # Java: rtn.setLxbh(roadCode); —— 把 trim 后的值写回对象
            if isinstance(item, dict):
                item["lxbh"] = road_code
            else:
                item.lxbh = road_code
            if is_not_blank(road_code) and is_not_blank(pile_no):
                cached.append(item)

        self.redis_cache.set_cache_object(lxbh_jdwd, cached)
        return rows

    # Java: Map<String, List<Geometry>> getRedisList()
    def get_redis_list(self) -> Dict[str, List[Any]]:
        """按路线编号分组；缓存缺失时回填并**使用回填的返回值**分组.

        Java 原文：

        .. code-block:: java

            if (null != obj) { list = (List) obj; } else { list = this.updateRedisList(); }

        ``updateRedisList()`` 返回的是**未过滤**的全量列表，因此缓存刚回填的那一次
        调用可能把 ``paths`` 为空的记录也分组进来 —— 照抄，不做修正。
        """
        cached = self.redis_cache.get_cache_object(lxbh_jdwd)
        if cached is not None:
            rows: List[Any] = list(cached)
        else:
            rows = self.update_redis_list()

        grouped: Dict[str, List[Any]] = {}
        for item in rows:
            key = _read_field(item, "lxbh")
            grouped.setdefault(key, []).append(item)
        return grouped

    # Java: List<Geometry> getListByCode(List<String> roadCodeList)
    def get_list_by_code(self, road_code_list: Sequence[str]) -> List[Any]:
        """Java 里整段实现被注释掉，恒返回空列表 —— 保留原样（不是遗漏）."""
        return []

    # Java: List<Geometry> syncAllGeometry()
    def sync_all_geometry(self) -> List[Any]:
        return self._mapper.sync_all_geometry()


_SERVICE: GeometryService | None = None


def get_geometry_service() -> GeometryService:
    """Java: ``@Autowired IGeometryService``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = GeometryService()
    return _SERVICE


def reset_geometry_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["GeometryService", "get_geometry_service", "reset_geometry_service"]
