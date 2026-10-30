"""``java.util.stream.Collectors`` / ``java.util.Comparator`` 的最小等价物.

# Migrated from: (no single Java source) -- ``java.util.stream.Collectors`` and
#   ``java.util.Comparator`` from the JDK, used directly in the controllers.

为什么需要这个模块
------------------
``base`` 包有三个控制器（``/base/gantry``、``/base/toll``、``/base/feerecords``）
都写了同一段流水线：

.. code-block:: java

    Map<String, String> roadMap = sectionList.stream()
        .collect(Collectors.toMap(OdsSzdnSection::getRoadCode,
                                  OdsSzdnSection::getRoadName,
                                  (k1, k2) -> k1));

    Map<String, String> tollMap = tollService.list().stream()
        .collect(Collectors.toMap(OdsSzdnToll::getTollCode, OdsSzdnToll::getTollName));

    list = list.stream().sorted(Comparator.comparing(OdsSzdnGantry::getOrgCode)
                                             .thenComparing(OdsSzdnGantry::getRoadCode))
        .collect(Collectors.toList());

Python 的字典推导 / ``sorted(key=...)`` 看起来能做同样的事，但**失败行为不同**，
这三个差异都会变成"线上 500 变成静默的错数据"，所以必须显式复刻：

``Collectors.toMap`` 的两条硬规则
---------------------------------
1. **值不能是 ``null``**。``toMap`` 走 ``HashMap#merge``，而 ``merge`` 的第一行就是
   ``if (value == null) throw new NullPointerException()``。也就是说某条路段
   ``road_name`` 为空 -> ``NPE`` -> HTTP 200 + ``code 500``。
2. **没有 merge 函数时键不能重复**。``toMap(k, v)`` 用的是 ``throwingMerger()``，
   重复键抛 ``IllegalStateException: Duplicate key ...``；有 merge 函数
   （``(k1, k2) -> k1``）时**保留先到的那个值**。

``Comparator.comparing`` 的 ``null`` 行为
-----------------------------------------
``Comparator.comparing(keyExtractor)`` 展开成
``(c1, c2) -> keyExtractor.apply(c1).compareTo(keyExtractor.apply(c2))`` ——
键为 ``null`` 时 ``compareTo`` 抛 ``NPE``（**不是**把 null 排到最前/最后）。
:func:`sorted_by` 因此对 ``null`` 抛 :class:`TypeError`，而不是像
``sorted(key=lambda x: (x is None, x))`` 那样"容忍"。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, TypeVar

T = TypeVar("T")

#: Java 抛出的两个异常在 Python 侧的替身消息（与 :mod:`app.system.service.sys_dict_data_service`
#: 里 ``_put_unique`` 的写法保持一致，便于全局处理器按 ``code 500`` 渲染）。
_NULL_POINTER = "java.lang.NullPointerException"


def to_map(
    rows: Iterable[T],
    key_mapper: Callable[[T], Any],
    value_mapper: Callable[[T], Any],
    merge_function: Optional[Callable[[Any, Any], Any]] = None,
) -> Dict[Any, Any]:
    """Java: ``Collectors.toMap(keyMapper, valueMapper[, mergeFunction])``.

    ``merge_function(old_value, new_value)`` —— 参数顺序与 Java 的
    ``BiFunction<V, V, V>`` 一致（先旧后新）。常见的 ``(k1, k2) -> k1`` 就是
    :func:`first_wins`。
    """
    result: Dict[Any, Any] = {}
    for row in rows:
        key = key_mapper(row)
        value = value_mapper(row)
        # Java: HashMap#merge —— if (value == null) throw new NullPointerException();
        if value is None:
            raise TypeError(_NULL_POINTER)
        if key in result:
            if merge_function is None:
                # Java: Collectors.throwingMerger()
                raise AttributeError(
                    "java.lang.IllegalStateException: Duplicate key "
                    f"{key} (attempted merging values {result[key]} and {value})"
                )
            result[key] = merge_function(result[key], value)
            continue
        result[key] = value
    return result


def first_wins(old_value: Any, new_value: Any) -> Any:
    """Java: ``(k1, k2) -> k1`` —— ``toMap`` 的合并函数：保留先到的值."""
    return old_value


def sorted_by(rows: Sequence[T], *key_mappers: Callable[[T], Any]) -> List[T]:
    """Java: ``Comparator.comparing(a).thenComparing(b)....`` + ``Stream.sorted``.

    ``Stream.sorted`` 是**稳定**排序，``sorted`` 也是 —— 相同键的相对顺序保持不变。
    任何一级键为 ``null`` 都抛 :class:`TypeError`（Java 侧是 ``NPE``）。
    """

    def _key(row: T) -> tuple:
        values = []
        for mapper in key_mappers:
            value = mapper(row)
            if value is None:
                # Java: keyExtractor.apply(c).compareTo(...) —— 接收者是 null
                raise TypeError(_NULL_POINTER)
            values.append(value)
        return tuple(values)

    return sorted(rows, key=_key)


__all__ = ["first_wins", "sorted_by", "to_map"]
