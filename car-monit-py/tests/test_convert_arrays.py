# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/text/Convert.java
#   -> ``toStrArray(String str)`` / ``toStrArray(String split, String str)``
#   -> ``toLongArray(String str)`` / ``toLongArray(String split, String str)``

"""``Convert`` 的两个数组转换 —— 全部风险都在 ``String.split`` 的边角上.

为什么要单独钉这张表
--------------------
``toStrArray`` 的 Java 原实现只有一行::

    public static String[] toStrArray(String split, String str) {
        return str.split(split);
    }

所以它的行为**完全**等于 ``String.split(regex)``，而 ``String.split`` 有三条反直觉
的规则（都跟 Python 的 ``re.split`` 默认行为不同或容易被手写错）：

1. **尾部空串全部丢掉**：``"1,2,,".split(",")`` -> ``["1", "2"]``；
2. **全分隔符时结果整个空掉**：``",".split(",")`` -> ``[]``、``",,,".split(",")`` -> ``[]``。
   JDK 里那行收尾是 ``while (resultSize > 0 && "".equals(matchList.get(resultSize - 1)))
   resultSize--;`` —— 没有"至少留一个"的保底，所以能一路减到 0；
3. **没有匹配时返回原串**：``"".split(",")`` -> ``[""]``。

第 2 条一旦写错（例如把循环条件写成 ``len(parts) > 1``），``to_long_array(",")`` 就会
从 ``[]`` 变成 ``[None]``，而它正是
``GenTableColumnServiceImpl#deleteGenTableColumnByIds`` 的入参 ——
``[]`` 拼出 ``table_id in ()`` 让 MySQL 报语法错（Java 的 500），
``[None]`` 则安静地删掉 0 行。错误因此完全不可见，只能靠这张表兜住。

``toLongArray`` 与 ``toStrArray`` 的三点差异也都是 Java 原样：空值返回**空数组**（不抛
NPE）、每个元素走 ``toLong(x, null)``（转换失败得 ``null`` 元素）、以及
``new BigDecimal(x).longValue()`` 的向零截断/科学计数法支持。
"""

from __future__ import annotations

from typing import Any, List, Optional

import pytest

from app.common.core.text.convert import to_long_array, to_str_array

# --------------------------------------------------------------------------- toStrArray

#: ``to_str_array`` 与 ``String.split(",")`` 的逐项对照表（默认分隔符）。
#: 每一条都能在 JDK 上直接验证，不需要"大概是这样"。
_SPLIT_CASES: List[Any] = [
    # 常规
    ("a,b,c", ["a", "b", "c"]),
    ("a", ["a"]),
    # 尾部空串被丢弃（规则 1）
    ("a,b,", ["a", "b"]),
    ("a,b,,", ["a", "b"]),
    ("a,b,,,", ["a", "b"]),
    # 中间空串保留
    ("a,,b", ["a", "", "b"]),
    (",a", ["", "a"]),
    # 全分隔符 -> 空数组（规则 2）
    (",", []),
    (",,", []),
    (",,,", []),
    # 空串 -> 单元素数组（规则 3）
    ("", [""]),
    # 不做 trim —— Java 的 split 只管切，不洗数据
    (" a , b ", [" a ", " b "]),
    ("a, ,b", ["a", " ", "b"]),
]


@pytest.mark.parametrize("value,expected", _SPLIT_CASES)
def test_to_str_array_matches_string_split(value: str, expected: List[str]) -> None:
    assert to_str_array(value) == expected


def test_to_str_array_keeps_regex_semantics() -> None:
    """``str.split(split)`` 的 ``split`` 是**正则**，不是字面量.

    照抄要点：不能用 ``str.split(split)``（字面量）实现，否则 ``"\\d"`` 这类分隔符
    会失效。本工程唯一的调用方只传 ``","``，但差异在这里记着。
    """
    assert to_str_array("a1b22c", r"\d+") == ["a", "b", "c"]


def test_to_str_array_custom_split() -> None:
    assert to_str_array("a;b;c", ";") == ["a", "b", "c"]
    assert to_str_array("a;b;", ";") == ["a", "b"]
    assert to_str_array(";", ";") == []


def test_to_str_array_none_raises_java_npe() -> None:
    """``null.split(",")`` 是 NPE，抛 ``AttributeError`` + Java 异常哨兵文案.

    抛 ``TypeError`` 会让日志里出现 Python 的英文文案；哨兵文案保证日志可读。
    P1-6 起非业务异常不再回传客户端，HTTP 层统一返回 ``系统繁忙，请稍后重试``，
    NPE 的原始文案只进 ``sys-error.log``。
    """
    with pytest.raises(AttributeError) as error:
        to_str_array(None)
    assert "java.lang.NullPointerException" in str(error.value)


def test_to_long_array_does_not_raise_on_none() -> None:
    """与 ``to_str_array`` 相反 —— ``StringUtils.isEmpty(str)`` 先兜住了."""
    assert to_long_array(None) == []
    assert to_long_array("") == []


# --------------------------------------------------------------------------- toLongArray

_LONG_CASES: List[Any] = [
    # 常规
    ("1,2,3", [1, 2, 3]),
    ("1", [1]),
    # 尾部空串 / 全分隔符：split 先丢干净，所以不会出现"空串转数字"
    ("1,2,", [1, 2]),
    (",", []),
    (",,", []),
    # 中间空串 -> toLong("", null) -> null（**数组里带 null 元素**，不是 0）
    ("1,,2", [1, None, 2]),
    # 转换失败也是 null
    ("1,abc,3", [1, None, 3]),
    ("abc", [None]),
    # 字符串先 trim（toLong 里的 valueStr.trim()）
    (" 1 , 2 ", [1, 2]),
    # new BigDecimal(x).longValue() —— 向零截断
    ("1.9,-1.9", [1, -1]),
    # 科学计数法能解析（Long.parseLong 不行，这里走 BigDecimal，所以能）
    ("1E5", [100000]),
    # 负零与前后空格
    ("-0", [0]),
]


@pytest.mark.parametrize("value,expected", _LONG_CASES)
def test_to_long_array_matches_convert(value: str, expected: List[Optional[int]]) -> None:
    assert to_long_array(value) == expected


def test_to_long_array_saturates_on_overflow() -> None:
    """``BigDecimal.longValue()`` 是**饱和**截断，不抛 ``NumberFormatException``."""
    assert to_long_array("9223372036854775808") == [9223372036854775807]
    assert to_long_array("-9223372036854775809") == [-9223372036854775808]


def test_to_long_array_custom_split() -> None:
    assert to_long_array("1;2", ";") == [1, 2]
    assert to_long_array("1;2;", ";") == [1, 2]
    assert to_long_array(";", ";") == []


def test_to_long_array_all_separators_does_not_yield_none_element() -> None:
    """回归钉子：``","`` 必须得到 ``[]``，不能是 ``[None]``.

    这条一旦破，``deleteGenTableColumnByIds`` 的 ``in ()`` 语法错就消失了 ——
    Java 报 500，Python 静默删 0 行。
    """
    assert to_long_array(",") == []
    assert to_long_array(",,") == []
    assert to_long_array(",,,") == []


def test_split_helpers_are_independent_of_input_object() -> None:
    """两个函数都不修改入参（Python 字符串本来就不可变，这条防的是"改写返回列表"）."""
    first = to_str_array("a,b")
    second = to_str_array("a,b")
    assert first == second
    first.append("mutated")
    assert to_str_array("a,b") == ["a", "b"]
