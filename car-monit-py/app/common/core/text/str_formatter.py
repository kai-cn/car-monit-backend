"""Placeholder formatting, ``{}`` style.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/text/StrFormatter.java

Java original
-------------
Replaces ``{}`` occurrences left-to-right with ``argArray[i].toString()``. Two escape forms are
supported:

    format("this is {} for {}", "a", "b")      -> "this is a for b"
    format("this is \\{} for {}", "a", "b")    -> "this is \\{} for a"   (placeholder escaped)
    format("this is \\\\{} for {}", "a", "b")  -> "this is \\a for b"    (double backslash -> one)

Semantics that are easy to get wrong, all preserved here
--------------------------------------------------------
1. **Missing arguments are not an error.** After the last argument the remaining template is
   appended verbatim, so ``format("{} and {}", 1)`` yields ``"1 and {}"``.
2. **``None`` renders as the literal text ``null``.** Java calls
   ``Convert.utf8Str(null)`` (returns ``null``) then ``StringBuilder.append((String) null)``,
   which writes ``"null"``. Python's ``str(None)`` would write ``"None"`` -- a visible
   behaviour change in every ``"用户 {} 不存在"`` style message, so it is special-cased.
3. **Escaped placeholders consume no argument** (``argIndex--`` in Java); the same argument is
   re-used by the next placeholder.
"""

from __future__ import annotations

from typing import Any, List, Optional

#: Java: ``StrFormatter.EMPTY_JSON``
EMPTY_JSON = "{}"
#: Java: ``StrFormatter.C_BACKSLASH``
C_BACKSLASH = "\\"
#: Java: ``StrFormatter.C_DELIM_START``
C_DELIM_START = "{"
#: Java: ``StrFormatter.C_DELIM_END``
C_DELIM_END = "}"


def _utf8_str(value: Any) -> Optional[str]:
    """Java: ``Convert.utf8Str(Object)`` -- ``obj.toString()``, or ``None`` for a null object.

    Returning ``None`` (rather than the string ``"None"``) is deliberate: the caller appends
    Java's null rendering, which is the four characters ``null``.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _append(parts: List[str], value: Optional[str]) -> None:
    """Java: ``StringBuilder.append((String) null)`` writes ``"null"``, not ``"None"``."""
    parts.append("null" if value is None else value)


def format(str_pattern: Optional[str], *arg_array: Any) -> Optional[str]:
    """Java: ``StrFormatter.format(String strPattern, Object... argArray)``.

    ``str_pattern`` is returned unchanged when it is blank or the argument array is empty --
    the caller (``StringUtils.format``) relies on that identity, not just on the value.
    """
    # Local import keeps the ``string_utils`` <-> ``str_formatter`` pair acyclic.
    from app.common.utils.string_utils import is_empty

    if is_empty(str_pattern) or len(arg_array) == 0:
        return str_pattern

    pattern: str = str_pattern
    pattern_length = len(pattern)
    parts: List[str] = []

    handled_position = 0
    arg_index = 0
    # Java uses ``for (argIndex = 0; argIndex < argArray.length; argIndex++)`` with an
    # ``argIndex--`` branch, i.e. one placeholder may be skipped without consuming an
    # argument. A while loop expresses that directly.
    while arg_index < len(arg_array):
        delim_index = pattern.find(EMPTY_JSON, handled_position)
        if delim_index == -1:
            if handled_position == 0:
                # No placeholder at all -> return the original instance.
                return str_pattern
            parts.append(pattern[handled_position:pattern_length])
            return "".join(parts)

        if delim_index > 0 and pattern[delim_index - 1] == C_BACKSLASH:
            if delim_index > 1 and pattern[delim_index - 2] == C_BACKSLASH:
                # 转义符之前还有一个转义符，占位符依旧有效 (\\{} -> \ + argument)
                parts.append(pattern[handled_position:delim_index - 1])
                _append(parts, _utf8_str(arg_array[arg_index]))
                handled_position = delim_index + 2
            else:
                # 占位符被转义 (\{} -> {}) -- no argument consumed.
                parts.append(pattern[handled_position:delim_index - 1])
                parts.append(C_DELIM_START)
                handled_position = delim_index + 1
                arg_index -= 1
        else:
            # 正常占位符
            parts.append(pattern[handled_position:delim_index])
            _append(parts, _utf8_str(arg_array[arg_index]))
            handled_position = delim_index + 2

        arg_index += 1

    # 加入最后一个占位符后所有的字符
    parts.append(pattern[handled_position:pattern_length])
    return "".join(parts)


__all__ = [
    "EMPTY_JSON",
    "C_BACKSLASH",
    "C_DELIM_START",
    "C_DELIM_END",
    "format",
]
