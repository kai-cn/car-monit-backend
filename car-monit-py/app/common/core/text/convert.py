# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/text/Convert.java
"""类型转换工具（只搬了本项目用到的方法）.

Java 的 ``Convert`` 有十几个 ``toXxx`` 重载，本工程迁到 Python 后只有
``toStr`` 被调用（``SysConfigServiceImpl#selectConfigByKey``）。其余方法在
Java 里也有调用方，但那些调用方都还没迁 —— 等它们迁过来时再逐个补，
**不要**提前写一堆没人用的转换函数（写错了也没人发现）。

``toStr`` 的三个分支
--------------------
```java
public static String toStr(Object value, String defaultValue) {
    if (null == value) return defaultValue;
    if (value instanceof String) return (String) value;
    return value.toString();
}
```

注意第三分支：**任何非字符串对象都走 ``toString()``**，包括 ``Integer`` /
``List`` / ``Map``。所以缓存里存了 ``123`` 时取回来是 ``"123"``，存了 ``null``
时取回来是 ``defaultValue``（``toStr(value)`` 的默认值是 ``null``）。

其余 ``toXxx`` 是 ``ExcelUtil`` 迁入时补的
------------------------------------------
``ExcelUtil`` 的 ``setCellVo`` / ``importExcel`` 用到 ``toInt`` / ``toLong`` /
``toDouble`` / ``toFloat`` / ``toBigDecimal`` / ``toBool``，所以这一批一并搬过来。

三个共同点必须照抄：

1. **转换失败不抛异常**，返回 ``defaultValue``（单参重载传的是 ``null``，于是返回
   ``None``）—— 例如 ``Convert.toInt("abc")`` 是 ``null``，不是 ``0``。
   ``ExcelUtil.setCellVo`` 的 ``NUMERIC`` 分支正是靠这个 ``null`` 在
   ``cell.setCellValue(Integer)`` 处抛 NPE，被 ``addCell`` 的 ``catch`` 吞掉，
   最后落成"有样式、没值"的空单元格。这里保持返回 ``None``。
2. ``Number`` 入参走 ``intValue()`` / ``longValue()`` / ``doubleValue()`` /
   ``floatValue()`` —— 即**向零截断**，不做四舍五入。
3. 字符串入参先 ``trim()``；``toLong`` / ``toDouble`` 走 ``new BigDecimal(...)``，
   所以 ``"1E5"`` 这类科学计数法能解析。

注意 ``toBool`` 的取舍：Java 里 ``1`` / ``0`` 分别是 ``true`` / ``false``（不是
"非零即真"），且不认识的字符串返回 ``defaultValue``。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

_MAX_INT = 2147483647
_MIN_INT = -2147483648
_MAX_LONG = 9223372036854775807
_MIN_LONG = -9223372036854775808


# Java: public static String toStr(Object value)
def to_str(value: Any) -> Optional[str]:
    """Java: ``Convert.toStr(value)`` —— ``None`` 进 ``None`` 出。"""
    return to_str_with_default(value, None)


# Java: public static String toStr(Object value, String defaultValue)
def to_str_with_default(value: Any, default_value: Optional[str]) -> Optional[str]:
    """Java: ``Convert.toStr(value, defaultValue)``。"""
    if value is None:
        return default_value
    if isinstance(value, str):
        return value
    return str(value)


# --------------------------------------------------------------------------- 数值


def _is_number(value: Any) -> bool:
    """Java: ``value instanceof Number`` —— ``bool`` 在 Java 里**不是** ``Number``."""
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _is_empty_str(value: Optional[str]) -> bool:
    """Java: ``StringUtils.isEmpty(valueStr)`` —— ``null`` 或 ``""``."""
    return value is None or value == ""


# Java: public static Integer toInt(Object value, Integer defaultValue)
def to_int_with_default(value: Any, default_value: Optional[int]) -> Optional[int]:
    """Java: ``Convert.toInt(value, defaultValue)``.

    ``Number`` 分支是 ``intValue()``：``3.9`` -> ``3``，``-3.9`` -> ``-3``。
    字符串分支是 ``Integer.parseInt(trim())``，超出 int 范围 Java 抛
    ``NumberFormatException`` -> 返回默认值；这里同样用范围判断收口。
    """
    if value is None:
        return default_value
    if isinstance(value, bool):
        # Java: Boolean 不是 Number，会走 toString 分支 -> "true" 解析失败
        return default_value
    if _is_number(value):
        return _saturate(int(value), _MIN_INT, _MAX_INT)
    value_str = to_str(value)
    if _is_empty_str(value_str):
        return default_value
    assert value_str is not None
    try:
        return _saturate(int(value_str.strip()), _MIN_INT, _MAX_INT)
    except (ValueError, TypeError):
        return default_value


# Java: public static Integer toInt(Object value)
def to_int(value: Any) -> Optional[int]:
    return to_int_with_default(value, None)


# Java: public static Long toLong(Object value, Long defaultValue)
def to_long_with_default(value: Any, default_value: Optional[int]) -> Optional[int]:
    """Java: ``Convert.toLong(value, defaultValue)``.

    字符串分支是 ``new BigDecimal(valueStr.trim()).longValue()``，所以支持科学计数法，
    且同样向零截断（``"1.9"`` -> ``1``）。
    """
    if value is None:
        return default_value
    if isinstance(value, bool):
        return default_value
    if _is_number(value):
        return _saturate(int(value), _MIN_LONG, _MAX_LONG)
    value_str = to_str(value)
    if _is_empty_str(value_str):
        return default_value
    assert value_str is not None
    try:
        return _saturate(int(Decimal(value_str.strip())), _MIN_LONG, _MAX_LONG)
    except (InvalidOperation, ValueError, TypeError):
        return default_value


# Java: public static Long toLong(Object value)
def to_long(value: Any) -> Optional[int]:
    return to_long_with_default(value, None)


# Java: public static Double toDouble(Object value, Double defaultValue)
def to_double_with_default(value: Any, default_value: Optional[float]) -> Optional[float]:
    """Java: ``Convert.toDouble(value, defaultValue)``."""
    if value is None:
        return default_value
    if isinstance(value, bool):
        return default_value
    if _is_number(value):
        return float(value)
    value_str = to_str(value)
    if _is_empty_str(value_str):
        return default_value
    assert value_str is not None
    try:
        return float(value_str.strip())
    except (ValueError, TypeError):
        return default_value


# Java: public static Double toDouble(Object value)
def to_double(value: Any) -> Optional[float]:
    return to_double_with_default(value, None)


# Java: public static Float toFloat(Object value, Float defaultValue)
def to_float_with_default(value: Any, default_value: Optional[float]) -> Optional[float]:
    """Java: ``Convert.toFloat(value, defaultValue)`` —— 字符串走 ``Float.parseFloat``."""
    if value is None:
        return default_value
    if isinstance(value, bool):
        return default_value
    if _is_number(value):
        return float(value)
    value_str = to_str(value)
    if _is_empty_str(value_str):
        return default_value
    assert value_str is not None
    try:
        return float(value_str.strip())
    except (ValueError, TypeError):
        return default_value


# Java: public static Float toFloat(Object value)
def to_float(value: Any) -> Optional[float]:
    return to_float_with_default(value, None)


# Java: public static BigDecimal toBigDecimal(Object value, BigDecimal defaultValue)
def to_big_decimal_with_default(value: Any, default_value: Optional[Decimal]) -> Optional[Decimal]:
    """Java: ``Convert.toBigDecimal(value, defaultValue)``.

    ``Long`` / ``Integer`` -> ``new BigDecimal(long/int)``；``Double`` ->
    ``BigDecimal.valueOf(double)``（即 ``Double.toString`` 之后再构造，不走二进制展开）。
    这里统一用 ``Decimal(str(value))``，避免把 ``0.1`` 展开成 55 位小数。
    """
    if value is None:
        return default_value
    if isinstance(value, bool):
        return default_value
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    value_str = to_str(value)
    if _is_empty_str(value_str):
        return default_value
    assert value_str is not None
    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError, TypeError):
        return default_value


# Java: public static BigDecimal toBigDecimal(Object value)
def to_big_decimal(value: Any) -> Optional[Decimal]:
    return to_big_decimal_with_default(value, None)


# Java: public static Boolean toBool(Object value, Boolean defaultValue)
def to_bool_with_default(value: Any, default_value: Optional[bool]) -> Optional[bool]:
    """Java: ``Convert.toBool(value, defaultValue)``.

    认得的字符串只有 ``true/yes/ok/1`` -> ``True``、``false/no/0`` -> ``False``，
    其余（含 ``"y"``、``"是"``）返回 ``defaultValue``。**不是** Python 的 
    ``bool(value)``。
    """
    if value is None:
        return default_value
    if isinstance(value, bool):
        return value
    value_str = to_str(value)
    if _is_empty_str(value_str):
        return default_value
    assert value_str is not None
    lowered = value_str.strip().lower()
    if lowered in ("true", "yes", "ok", "1"):
        return True
    if lowered in ("false", "no", "0"):
        return False
    return default_value


# Java: public static Boolean toBool(Object value)
def to_bool(value: Any) -> Optional[bool]:
    return to_bool_with_default(value, None)


# --------------------------------------------------------------------------- 数组


# Java: public static String[] toStrArray(String str)
def to_str_array(value: Optional[str], split: str = ",") -> List[str]:
    """Java: ``Convert.toStrArray(str)`` / ``toStrArray(split, str)``.

    Java 原实现只有一行 ``str.split(split)``，**没有任何空值保护** ——
    传 ``null`` 就是 ``NullPointerException``。调用方
    ``GenController#importTableSave`` / ``batchGenCode`` 在 ``tables`` 缺失时会真的抛
    NPE（Spring 把未标注的 ``String tables`` 绑成 ``null``），最终响应
    ``{"msg":null,"code":500}``。这里抛 ``AttributeError`` 并带上
    ``java.lang.NullPointerException`` 哨兵 —— :func:`app.config.exception_handlers._java_message`
    据此把 ``msg`` 还原成 **``null``**（本工程约定，见 ``_require_non_null`` 等）。
    换成 ``TypeError`` 会把 Python 自己的英文文案塞进 ``msg``，与 Java 不一致。

    ``str.split`` 的三条 Java 语义要照抄：

    * 末尾的空串被**丢弃**：``"1,2,".split(",")`` -> ``["1", "2"]``；
    * 全是分隔符时结果**整个空掉**：``",".split(",")`` -> ``[]``、
      ``",,,".split(",")`` -> ``[]``（Java 的 ``resultSize`` 可以一路减到 0）；
    * 空串输入返回**单元素数组**：``"".split(",")`` -> ``[""]``（不是空数组）——
      这是 ``String.split`` 里"没有匹配到就直接返回原串"那条特例。
    """
    if value is None:
        # Java: str.split(split) 在 str == null 时抛 NPE（getMessage() 为 null）
        raise AttributeError("java.lang.NullPointerException: Convert.toStrArray: str 为 null")
    return _java_split(value, split)


# Java: public static Long[] toLongArray(String str)
def to_long_array(value: Optional[str], split: str = ",") -> List[Optional[int]]:
    """Java: ``Convert.toLongArray(str)`` / ``toLongArray(split, str)``.

    与 :func:`to_str_array` 的两点差异（都是 Java 原样）：

    * 空值**不抛异常**，返回空数组 —— ``if (StringUtils.isEmpty(str)) return new Long[] {}``；
    * 每个元素走 ``toLong(arr[i], null)``，转换失败得到 ``null``（数组里带 null 元素，
      不是 0）。
    """
    if _is_empty_str(value):
        return []
    assert value is not None
    return [to_long(item) for item in _java_split(value, split)]


def _java_split(value: str, split: str) -> List[str]:
    """``String.split(regex)`` 的复刻：丢弃**末尾**空串，保留中间空串. 

    Java 的 ``split`` 正则语义与 Python 的 ``re.split`` 基本一致，差别只在尾部：
    Java 的 ``limit == 0`` 会把结果尾部的空串全部删掉。
    """
    if value == "":
        # Java: "".split(",") -> [""]（一个空串元素）
        return [""]
    parts = re.split(split, value)
    # Java: ``while (resultSize > 0 && "".equals(matchList.get(resultSize - 1))) resultSize--;``
    # —— 条件里没有"至少留一个"的保底，所以 ``",".split(",")`` 是**空数组**。
    while parts and parts[-1] == "":
        parts.pop()
    return parts


def _saturate(number: int, minimum: int, maximum: int) -> int:
    """Java 的 ``(int)`` / ``(long)`` 转换在越界时饱和到边界值.

    ``Integer.parseInt`` 越界是抛异常（走默认值），而 ``double -> int`` 是饱和；
    两者都收在这里，调用方不需要区分。
    """
    return max(minimum, min(maximum, number))


__all__ = [
    "to_str",
    "to_str_with_default",
    "to_int",
    "to_int_with_default",
    "to_long",
    "to_long_with_default",
    "to_double",
    "to_double_with_default",
    "to_float",
    "to_float_with_default",
    "to_big_decimal",
    "to_big_decimal_with_default",
    "to_bool",
    "to_bool_with_default",
    "to_str_array",
    "to_long_array",
]
