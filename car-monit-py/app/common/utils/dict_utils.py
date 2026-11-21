"""字典工具类.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/DictUtils.java

Java 是"静态方法 + ``SpringUtils.getBean(RedisCache.class)``"这种服务定位器写法；
Python 侧没有容器，直接调 :func:`app.common.core.redis.redis_cache.get_redis_cache`
拿进程级单例（与 :class:`~app.common.core.redis.redis_cache.RedisCache` 的注释一致）。

缓存键的组成
------------
``CacheConstants.SYS_DICT_KEY`` = ``"sys_dict:"``，拼上字典类型就是最终键，例如
``sys_dict:sys_user_sex``。``clearDictCache()`` 调 ``RedisCache.keys("sys_dict:*")``
拿到全部键再批量删；底层用 ``SCAN`` 增量遍历，不会像 Java 的 ``KEYS`` 那样阻塞 Redis。

``getDictLabel`` / ``getDictValue`` 的两个分支
----------------------------------------------
判据是 ``StringUtils.containsAny(separator, dictValue)`` —— 注意**两个参数是反的**：
Commons Lang 的 ``containsAny(CharSequence cs, CharSequence searchChars)`` 问的是
"``cs`` 里有没有 ``searchChars`` 中的任意字符"。传入 ``(separator, dictValue)`` 得

    "``separator`` 是否含有 ``dictValue`` 的任意一个字符"

因为 ``separator`` 固定是 ``","``，实际效果就是"``dictValue`` 里有没有逗号"：

* 有逗号 -> 走"多值"分支：遍历**字典项**、再遍历 ``dictValue.split(",")``，
  命中就往 ``StringBuilder`` 里追加 ``label + ","``；最后 ``stripEnd`` 去掉尾逗号。
  注意外层是**字典项**，所以输出顺序是"字典表顺序"，不是入参顺序。
* 没逗号 -> 走"单值"分支，命中直接 ``return``，**不做** ``stripEnd``。

``getDictValue`` 还有一处不对称：多值分支的条件里多了 ``&& StringUtils.isNotEmpty(datas)``，
但 ``else`` 分支照样遍历 ``datas`` —— 缓存为空时 ``null`` 会被 foreach 判空跳过
（Java 的 for-each 对 null 迭代器抛 NPE，这里其实是 ``containsAny`` 短路了，
真正为 null 时 ``isNotEmpty(datas)`` 为 false 后走 else 才 NPE）。照抄成同一件事：
缓存为 ``None`` 时两个分支都退化成"返回空串"，见下面的实现说明。
"""

from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence

from app.common.constant.cache_constants import SYS_DICT_KEY
from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.core.redis.redis_cache import get_redis_cache
from app.common.utils.string_utils import is_empty, is_not_empty, split_regex, strip_end

#: Java: ``public static final String SEPARATOR = ","``
SEPARATOR = ","


# Java: public static void setDictCache(String key, List<SysDictData> dictDatas)
def set_dict_cache(key: Optional[str], dict_datas: Optional[Sequence[SysDictData]]) -> None:
    """写缓存。``dictDatas`` 为 ``None`` 时 Java 写的是 ``"null"``（不是删除键）。

    fastjson2 把 ``null`` 序列化成 ``"null"`` 四个字节，``RedisCache.setCacheObject``
    照写不误 —— 于是 ``getDictCache`` 读回来拿到的是 ``null``，等于"没有缓存"。
    Python 侧 :class:`FastJson2JsonRedisSerializer` 把 ``None`` 序列化成**空串**
    （见 ``RedisCache`` 的说明），``redis-py`` 对空串照写不误，读回来同样是"没有值"。
    两者最终语义一致，都是"未命中"，所以这里不特判。
    """
    get_redis_cache().set_cache_object(get_cache_key(key or ""), list(dict_datas or []))


# Java: public static List<SysDictData> getDictCache(String key)
def get_dict_cache(key: Optional[str]) -> Optional[List[SysDictData]]:
    """读缓存；未命中返回 ``None``（Java 的 ``null``），不是空列表。

    这个区别很要命：``SysDictTypeServiceImpl.selectDictDataByType`` 用的是
    ``StringUtils.isNotEmpty(dictDatas)``，空列表与 ``None`` 在那里同样"未命中"，
    但在 ``getDictLabel`` 里 ``isNotNull(datas)`` 才决定要不要遍历。保持 ``None``。
    """
    array_cache = get_redis_cache().get_cache_object(get_cache_key(key or ""))
    if isinstance(array_cache, list):
        # Java: arrayCache.toList(SysDictData.class)
        return [item if isinstance(item, SysDictData) else SysDictData.model_validate(item) for item in array_cache]
    return None


# Java: public static String getDictLabel(String dictType, String dictValue)
def get_dict_label(dict_type: Optional[str], dict_value: Optional[str]) -> str:
    return get_dict_label_with_separator(dict_type, dict_value, SEPARATOR)


# Java: public static String getDictValue(String dictType, String dictLabel)
def get_dict_value(dict_type: Optional[str], dict_label: Optional[str]) -> str:
    return get_dict_value_with_separator(dict_type, dict_label, SEPARATOR)


# Java: public static String getDictLabel(String dictType, String dictValue, String separator)
def get_dict_label_with_separator(
    dict_type: Optional[str], dict_value: Optional[str], separator: str
) -> str:
    """按类型 + 键值取标签；多值用 ``separator`` 拼接（**字典表顺序**）。

    ``dictValue`` 为 ``None`` 时 Java 会在 ``StringUtils.containsAny(separator, null)``
    返回 ``false`` 后走 else 分支，再在 ``dictValue.equals(...)`` 处 NPE。这里保持
    "没缓存就返回空串、有缓存就抛"的边界：``dict_value`` 为 ``None`` 且缓存非空时
    抛 ``AttributeError``，等价于 NPE -> 500。
    """
    datas = get_dict_cache(dict_type)
    if datas is None:
        return ""

    if _contains_any_char(separator, dict_value):
        pieces: List[str] = []
        # Java: for (SysDictData dict : datas) { for (String value : dictValue.split(separator)) ... }
        for item in datas:
            for value in _split(dict_value, separator):
                if value == item.dict_value:
                    pieces.append(f"{item.dict_label}{separator}")
                    break
        return strip_end("".join(pieces), separator)

    # 单个值：命中直接返回，**不做** stripEnd，所以 label 末尾的逗号会原样带出去
    target = _require(dict_value, "dict_value")
    for item in datas:
        if target == item.dict_value:
            return item.dict_label or ""
    return ""


# Java: public static String getDictValue(String dictType, String dictLabel, String separator)
def get_dict_value_with_separator(
    dict_type: Optional[str], dict_label: Optional[str], separator: str
) -> str:
    """按类型 + 标签取值；与 :func:`get_dict_label_with_separator` 镜像。"""
    datas = get_dict_cache(dict_type)

    if _contains_any_char(separator, dict_label) and is_not_empty(datas):
        pieces: List[str] = []
        for item in datas:
            for label in _split(dict_label, separator):
                if label == item.dict_label:
                    pieces.append(f"{item.dict_value}{separator}")
                    break
        return strip_end("".join(pieces), separator)

    # Java 的 else 分支在这里没有判空，``datas == null`` 时 for-each 抛 NPE；
    # ``selectDictCache`` 未命中就返回 null，所以"没缓存 + 没逗号"是 500 而不是空串。
    target = _require(dict_label, "dict_label")
    for item in _require(datas, "dict_cache"):
        if target == item.dict_label:
            return item.dict_value or ""
    return ""


# Java: public static void removeDictCache(String key)
def remove_dict_cache(key: Optional[str]) -> None:
    get_redis_cache().delete_object(get_cache_key(key or ""))


# Java: public static void clearDictCache()
def clear_dict_cache() -> None:
    """``keys("sys_dict:*")`` + 批量删；``RedisCache.keys`` 内部用 ``SCAN`` 增量遍历。"""
    cache = get_redis_cache()
    keys = cache.keys(f"{SYS_DICT_KEY}*")
    cache.delete_object(keys)


# Java: public static String getCacheKey(String configKey)
def get_cache_key(config_key: str) -> str:
    return SYS_DICT_KEY + config_key


def _split(value: Optional[str], separator: str) -> List[str]:
    """Java: ``String.split(separator)`` —— 用 :func:`split_regex` 的 Java 语义。

    ``"a,b,".split(",")`` 在 Java 里是 ``["a","b"]``（尾部空串被丢弃），Python 的
    ``str.split`` 会多出一个 ``""``。字典多值缓存靠这个差异决定要不要多拼一个逗号。
    """
    return split_regex(_require(value, "split argument"), _regex_escape(separator))


def _regex_escape(separator: str) -> str:
    """``String.split`` 的参数是**正则**，``.`` / ``|`` 之类必须转义。"""
    return re.escape(separator)


def _contains_any_char(chars: Optional[str], probe: Optional[str]) -> bool:
    """Java: ``StringUtils.containsAny(CharSequence cs, CharSequence searchChars)``.

    "``cs`` 里是否含有 ``searchChars`` 中的任意一个字符"。带逗号判据的两处调用都是
    ``containsAny(separator, value)``，参数顺序不要"修"。
    """
    if is_empty(chars) or is_empty(probe):
        return False
    assert chars is not None and probe is not None
    return any(char in chars for char in probe)


def _require(value: Any, name: str) -> Any:
    """Java 在这些位置会 NPE；Python 侧显式抛 ``AttributeError``（同样落到 500）。"""
    if value is None:
        raise AttributeError(f"java.lang.NullPointerException: {name} is null")
    return value


__all__ = [
    "SEPARATOR",
    "set_dict_cache",
    "get_dict_cache",
    "get_dict_label",
    "get_dict_value",
    "get_dict_label_with_separator",
    "get_dict_value_with_separator",
    "remove_dict_cache",
    "clear_dict_cache",
    "get_cache_key",
]
