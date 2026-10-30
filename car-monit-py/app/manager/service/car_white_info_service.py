"""车俩白名单 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWhiteInfoService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWhiteInfoServiceImpl.java

``save`` / ``delete`` 之后调用 :meth:`update_redis_car_white_list`：回源查全量
（空实体 -> 条件全为 false）后**整份覆盖** Redis 值 ``Constants.white_car_list``。

``getRedisCarWhiteList`` 是给其它包（门架抓拍、出口流水等）读白名单用的：
缓存命中就把 JSON 反序列化出来的 ``list[dict]`` 直接返回（**不**转实体 ——
Java 里也是裸 ``(List) obj``），所以调用方拿到的是 ``dict`` 列表。
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.constant.constants import white_car_list
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.manager.domain.car_white_info import CarWhiteInfo
from app.manager.mapper.car_white_info_mapper import CarWhiteInfoMapper
from app.manager.service.manager_service import ManagerCrudService


class CarWhiteInfoService(ManagerCrudService):
    """Java: ``class CarWhiteInfoServiceImpl extends ServiceImpl<CarWhiteInfoMapper, CarWhiteInfo>``."""

    mapper_cls = CarWhiteInfoMapper

    def __init__(
        self, mapper: Any = None, redis_cache: Optional[RedisCache] = None
    ) -> None:
        super().__init__(mapper)
        self._redis_cache = redis_cache

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache``."""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    def after_change(self) -> None:
        """Java: ``this.updateRedisCarWhiteList();``"""
        self.update_redis_car_white_list()

    # Java: public void updateRedisCarWhiteList()
    def update_redis_car_white_list(self) -> None:
        rows = self._mapper.select_list(CarWhiteInfo())
        self.redis_cache.set_cache_object(white_car_list, list(rows))

    # Java: public List<CarWhiteInfo> getRedisCarWhiteList()
    def get_redis_car_white_list(self) -> List[Any]:
        cached = self.redis_cache.get_cache_object(white_car_list)
        if cached is not None:
            return list(cached)
        rows = self._mapper.select_list(CarWhiteInfo())
        self.redis_cache.set_cache_object(white_car_list, list(rows))
        return list(rows)


_SERVICE: Optional[CarWhiteInfoService] = None


def get_car_white_info_service() -> CarWhiteInfoService:
    """Java: ``@Autowired ICarWhiteInfoService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarWhiteInfoService()
    return _SERVICE


def reset_car_white_info_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarWhiteInfoService",
    "get_car_white_info_service",
    "reset_car_white_info_service",
]
