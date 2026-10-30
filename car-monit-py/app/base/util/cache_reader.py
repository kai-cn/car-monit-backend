"""``Constants.SECTION_LIST`` / ``Constants.gantry_list`` 的读取与映射.

# Migrated from: (no single Java source) -- the Redis read + ``Collectors.toMap``
#   block that ``OdsSzdnGantryController`` / ``OdsSzdnTollController`` /
#   ``OdsLwzxsfsjFeeRecords01Controller`` each duplicate verbatim.

为什么单独成文
--------------
Java 的三个控制器里，这段代码是**逐字重复**的：

.. code-block:: java

    List<OdsSzdnSection> sectionList = redisCache.getCacheList(Constants.SECTION_LIST);
    Map<String, String> roadMap = sectionList.stream()
        .collect(Collectors.toMap(OdsSzdnSection::getRoadCode, OdsSzdnSection::getRoadName, (k1, k2) -> k1));
    Map<String, String> sectionMap = sectionList.stream()
        .collect(Collectors.toMap(OdsSzdnSection::getSectionCode, OdsSzdnSection::getSectionName, (k1, k2) -> k1));

放到一处，避免三份实现各自漂移（尤其是下面这两个"坑"）。

坑一：``SECTION_LIST`` 是 **Redis list**，``gantry_list`` 是 **Redis value**
----------------------------------------------------------------------------
* ``getCacheList(key)`` -> ``LRANGE``，元素是 ``OdsSzdnSection``；
* ``getCacheObject(key)`` -> ``GET``，整个 ``List<OdsSzdnGantry>`` 序列化成一个值。

两者在 Redis 里是**不同的 key 类型**，拿错会直接 ``WRONGTYPE``。

坑二：缓存里存的是 JSON，读回来是 ``dict``
-------------------------------------------
Java 的 ``FastJson2JsonRedisSerializer`` 会把 ``@type`` 写进 JSON，反序列化后
拿到的就是 ``OdsSzdnSection`` 实例；Python 侧 ``RedisCache`` 只做 JSON，
读回来是 ``dict``。Java 代码随后会调 ``gantry.setRoadName(...)``，所以这里统一
转成实体对象（``model_validate`` 同时接受 ``roadCode`` 与 ``road_code`` 两种键名）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, TypeVar

from app.base.domain.ods_szdn_section import OdsSzdnSection
from app.common.constant.constants import SECTION_LIST
from app.common.core.redis.redis_cache import RedisCache
from app.common.utils.common_util import is_null
from app.common.utils.java_stream import first_wins, to_map

T = TypeVar("T")


def to_entities(entity_cls: Type[T], cached: Optional[Any]) -> List[T]:
    """``(List<Xxx>) redisCache.getCacheObject(key)`` 的等价物.

    * ``None`` -> 空列表（Java 里由调用方判 ``null != obj``，这里方便直接遍历）；
    * 元素已是实体 -> 原样保留；
    * 元素是 ``dict`` -> :meth:`pydantic.BaseModel.model_validate`。

    Java 侧那句强转 ``(List<OdsSzdnGantry>) obj`` 在类型不符时抛
    ``ClassCastException``；这里 ``model_validate`` 同样抛异常（``code 500``）。
    """
    if not cached:
        return []
    entities: List[T] = []
    for item in cached:
        if isinstance(item, entity_cls):
            entities.append(item)
        else:
            entities.append(entity_cls.model_validate(item))  # type: ignore[attr-defined]
    return entities


def read_section_list(redis_cache: RedisCache) -> List[OdsSzdnSection]:
    """Java: ``redisCache.getCacheList(Constants.SECTION_LIST)``."""
    return to_entities(OdsSzdnSection, redis_cache.get_cache_list(SECTION_LIST))


def road_name_map(sections: List[OdsSzdnSection]) -> Dict[str, str]:
    """Java: ``toMap(getRoadCode, getRoadName, (k1, k2) -> k1)`` —— 重复键保留先到的."""
    return to_map(sections, lambda item: item.road_code, lambda item: item.road_name, first_wins)


def section_name_map(sections: List[OdsSzdnSection]) -> Dict[str, str]:
    """Java: ``toMap(getSectionCode, getSectionName, (k1, k2) -> k1)``."""
    return to_map(
        sections, lambda item: item.section_code, lambda item: item.section_name, first_wins
    )


def section_by_code_map(sections: List[OdsSzdnSection]) -> Dict[str, OdsSzdnSection]:
    """``Map<String, OdsSzdnSection>``, 键为 ``CommonUtil.isNull(sectionCode)``.

    与上面两个方法的**两处**差异（都在 Java 原文里，不是笔误）：

    * 用的是普通 ``Map.put`` —— 重复键**后者覆盖前者**，也不抛异常；
    * 值不做 ``null`` 检查 —— ``Collectors.toMap`` 那条 ``null -> NPE`` 的规则在这里
      不成立（``Collectors.toMap`` 才对值做检查，普通 ``put`` 不做）。
    """
    result: Dict[str, OdsSzdnSection] = {}
    for item in sections:
        result[is_null(item.section_code)] = item
    return result


__all__ = [
    "read_section_list",
    "road_name_map",
    "section_by_code_map",
    "section_name_map",
    "to_entities",
]
