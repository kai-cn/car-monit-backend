"""服务区判定规则 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/ICarWarningConfigService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/CarWarningConfigServiceImpl.java

CRUD 公共部分见 :class:`~app.base.service.abstract_crud_service.AbstractCrudService`；
本模块独有的是**缓存联动**：任何一次保存 / 删除之后都调 ``cacheWarningConfig()``，
把全表重新写入 Redis（``Constants.CAR_WARNING_CONFIG_LIST``）。

主键是 ``String`` + ``ASSIGN_UUID``（见
:class:`~app.base.mapper.car_warning_config_mapper.CarWarningConfigMapper`），
判据是 ``CommonUtil.isNotBlank(id)`` —— 即基类默认的 ``blank_check = True``。
删除是**物理删除**（``delete from ...``），不是逻辑删除。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.base.mapper.car_warning_config_mapper import CarWarningConfigMapper
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.constant.constants import CAR_WARNING_CONFIG_LIST
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache


class CarWarningConfigService(AbstractCrudService):
    """Java: ``class CarWarningConfigServiceImpl``."""

    mapper_cls = CarWarningConfigMapper
    #: Java: ``@TableId(value = "id", type = IdType.ASSIGN_UUID)``
    id_attribute = "id"

    def __init__(self, mapper: Any = None, redis_cache: Optional[RedisCache] = None) -> None:
        super().__init__(mapper)
        self._redis_cache = redis_cache

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache``."""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    # Java: AjaxResult saveCarWarningConfig(CarWarningConfig carWarningConfig)
    def save(self, entity: Any) -> AjaxResult:
        result = super().save(entity)
        # Java: this.cacheWarningConfig();
        self.cache_warning_config()
        return result

    # Java: private void cacheWarningConfig()
    def cache_warning_config(self) -> None:
        """空实体查全表（``<where>`` 无片段），整份覆盖缓存."""
        query = self._mapper.entity_cls()
        self.redis_cache.set_cache_object(CAR_WARNING_CONFIG_LIST, list(self._mapper.select_list(query)))

    # Java: AjaxResult deleteCarWarningConfigByIds(String[] ids)
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        result = super().delete_by_ids(ids, "delete_car_warning_config_by_ids")
        # Java: this.cacheWarningConfig();
        self.cache_warning_config()
        return result

    # Java: AjaxResult deleteCarWarningConfigById(String id)
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_car_warning_config_by_id(entity_id)
        # Java: this.cacheWarningConfig();
        self.cache_warning_config()
        return AjaxResult.success_data(count)

    # Java: List<CarWarningConfig> getRedisCarWarningConfig()
    def get_redis_car_warning_config(self) -> List[Any]:
        """读缓存；缺失则回源并回填（与 ``getRedisList`` 不同，这里回填后返回同一份）."""
        cached = self.redis_cache.get_cache_object(CAR_WARNING_CONFIG_LIST)
        if cached is not None:
            return list(cached)
        query = self._mapper.entity_cls()
        rows = list(self._mapper.select_list(query))
        self.redis_cache.set_cache_object(CAR_WARNING_CONFIG_LIST, rows)
        return rows


_SERVICE: CarWarningConfigService | None = None


def get_car_warning_config_service() -> CarWarningConfigService:
    """Java: ``@Autowired ICarWarningConfigService``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarWarningConfigService()
    return _SERVICE


def reset_car_warning_config_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarWarningConfigService",
    "get_car_warning_config_service",
    "reset_car_warning_config_service",
]
