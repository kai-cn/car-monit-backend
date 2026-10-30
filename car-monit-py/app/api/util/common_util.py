"""Controller-layer helpers.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/util/CommonUtil.java

Only the methods with a live call site are ported here; the Java class also carries
``isInteger`` / ``isDouble`` / ``isNum`` / ``randomGen`` / ``subStrLentg`` /
``getProjectUrl`` / ``getInnerText`` / ``isNullInteger`` / ``isMobileDevice``, which are
unused by Milestone 1 and land together with their first consumer. Nothing is dropped --
this module is simply the subset that ``SysLoginController`` needs.

``check_password`` returns ``true`` when the password is **bad**
---------------------------------------------------------------
That inverted sense is Java's:

    public static boolean checkPassword(String curPassword) {
        if (!curPassword.matches(passwordGz)) return true; else return false;
    }

Call sites read ``if (CommonUtil.checkPassword(pwd)) { return error(...); }``, so the name
means "needs to be rejected", not "is valid".
"""

from __future__ import annotations

import re
from typing import Any, Optional

from app.common.utils.string_utils import java_trim

#: Java: ``"^(?![A-Za-z0-9]+$)(?![a-z0-9\\W]+$)(?![A-Za-z\\W]+$)(?![A-Z0-9\\W]+$)[a-zA-Z0-9\\W]{8,20}$"``
#:
#: The four lookaheads are an "at least one of each class" test written as negations:
#:
#: * ``(?![A-Za-z0-9]+$)``     -> must contain something outside letters+digits (a symbol)
#: * ``(?![a-z0-9\W]+$)``      -> must contain an uppercase letter
#: * ``(?![A-Za-z\W]+$)``      -> must contain a digit
#: * ``(?![A-Z0-9\W]+$)``      -> must contain a lowercase letter
#:
#: ``re.ASCII`` is required, not cosmetic. Java's ``\W`` is the ASCII class
#: ``[^a-zA-Z0-9_]``; Python's default ``\W`` is Unicode-aware, so a CJK character is a
#: Unicode *word* character and would **not** match ``\W`` -- an 8-character password such
#: as ``Abc1234中`` contains no symbol for Python but does for Java. ``re.ASCII`` restores
#: Java's class and therefore Java's verdict.
#:
#: Residual difference: ``{8,20}`` counts UTF-16 code units in Java and code points in
#: Python, so a password containing emoji can land on opposite sides of the bounds.
#: Recorded in COMPATIBILITY.md; unreachable for the passwords this system issues.
_PASSWORD_PATTERN = re.compile(
    r"^(?![A-Za-z0-9]+$)(?![a-z0-9\W]+$)(?![A-Za-z\W]+$)(?![A-Z0-9\W]+$)[a-zA-Z0-9\W]{8,20}$",
    re.ASCII,
)


def is_null(names: Any) -> str:
    """对面默认为空 -- 空字符串. Java: ``CommonUtil.isNull(Object)``.

    ``null`` -> ``""``; anything else -> ``String.valueOf(x).trim()``.
    """
    if names is None:
        return ""
    # Java uses String.valueOf(names). Python's str() spells booleans "True"/"False";
    # every call site passes a String, so the difference is unreachable in practice.
    return java_trim(str(names)) or ""


def is_not_blank(value: Optional[str]) -> bool:
    """Java: ``CommonUtil.isNotBlank(String)`` -- delegates to ``StringUtils.isNotBlank``."""
    from app.common.utils.string_utils import is_not_blank as _is_not_blank

    return _is_not_blank(value)


def is_blank(value: Optional[str]) -> bool:
    """Java: ``CommonUtil.isBlank(String)`` -- delegate to ``StringUtils.isBlank``."""
    from app.common.utils.string_utils import is_blank as _is_blank

    return _is_blank(value)


def delete_end(obj: Any) -> str:
    """删除结尾的逗号. Java: ``CommonUtil.deleteEnd(Object)`` -- at most one comma removed."""
    value = is_null(obj)
    if value.endswith(","):
        value = value[:-1]
    return value


def check_password(cur_password: str) -> bool:
    """验证密码长度与复杂度 -- ``True`` means **invalid**, see the module docstring.

    Java: ``CommonUtil.checkPassword(String)``.
    """
    return _PASSWORD_PATTERN.fullmatch(cur_password) is None


__all__ = ["is_null", "is_not_blank", "is_blank", "delete_end", "check_password"]
