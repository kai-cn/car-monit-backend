"""``com.ruoyi.web.util.CommonUtil`` 的增量迁移.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/util/CommonUtil.java

已迁移成员
----------
================  ===========================================================
Java              Python
================  ===========================================================
isNull(Object)    :func:`is_null`
isNotBlank(str)   :func:`is_not_blank`
isBlank(str)      :func:`is_blank`
deleteEnd(Object) :func:`delete_end`
isExitsStr(s,p)   :func:`is_exits_str`
================  ===========================================================

其余成员（``isInteger`` / ``isDouble`` / ``randomGen`` / ``getInnerText`` /
``checkPassword`` …）随各自的调用方迁移 —— 它们不是"没用"，只是这一层还没有
人调用。

注意这个类的 ``isNull`` 和 ``StringUtils.isNull`` **不是一回事**：后者只判 null
（返回 ``boolean``），前者返回 ``toString().trim()`` 后的字符串。
"""

from __future__ import annotations

from typing import Any, Optional

from app.common.utils.string_utils import java_trim, is_blank as _is_blank
from app.common.utils.string_utils import is_not_blank as _is_not_blank
from app.common.utils.string_utils import split_regex


def is_null(names: Any) -> str:
    """Java: ``public static String isNull(Object names)``.

    ``null`` -> ``""``；其余 -> ``names.toString().trim()``。

    这里的 ``trim`` 是 Java 的 ``String.trim()``（只削 ``<= U+0020``），
    不是 Python 的 ``str.strip()``（会连全角空格一起削），所以走
    :func:`app.common.utils.string_utils.java_trim`。
    """
    if names is None:
        return ""
    trimmed = java_trim(str(names))
    return trimmed if trimmed is not None else ""


def is_not_blank(value: Optional[str]) -> bool:
    """Java: ``public static boolean isNotBlank(String str)``.

    直接转发 ``StringUtils.isNotBlank`` —— 见
    :func:`app.common.utils.string_utils.is_not_blank`。
    """
    return _is_not_blank(value)


def is_blank(value: Optional[str]) -> bool:
    """Java: ``public static boolean isBlank(String str)``."""
    return _is_blank(value)


def delete_end(obj: Any) -> str:
    """Java: ``public static String deleteEnd(Object obj)``.

    ``null`` -> ``""``；**末尾只有一个**逗号时削掉它。

    注意 Java 原文只削**一次**（``if (str.endsWith(","))`` 不是 ``while``），
    所以 ``"a,,"`` -> ``"a,"``。照抄。
    """
    text = is_null(obj)
    if text.endswith(","):
        return text[: len(text) - 1]
    return text


def is_exits_str(sql_str: Any, para_str: Any) -> bool:
    """Java: ``public static boolean isExitsStr(String sqlStr, String paraStr)``.

    ``paraStr`` 按逗号拆开后，只要**任一**元素出现在 ``sqlStr`` 里就返回 ``True``；
    ``paraStr`` 为空（含 ``null``）返回 ``True`` —— 即「不传条件就不过滤」。

    两个照抄点：

    1. ``paraStr`` 先过 :func:`delete_end`（只削**一个**尾逗号）；
    2. 拆分用 Java ``String.split`` 语义（丢弃尾部空串），见
       :func:`app.common.utils.string_utils.split_regex`。
    """
    para = delete_end(para_str)
    haystack = is_null(sql_str)
    if is_not_blank(para):
        for item in split_regex(para, ","):
            if item in haystack:
                return True
        return False
    return True


__all__ = ["delete_end", "is_blank", "is_exits_str", "is_not_blank", "is_null"]
