"""Simple ``*`` pattern matching.

Not a RuoYi file
----------------
``org.springframework.util.PatternMatchUtils`` is Spring Framework code. It is ported
because :meth:`app.common.utils.security_utils.SecurityUtils.has_permi` and
``has_role`` depend on its exact semantics.

Why not ``fnmatch`` or :func:`re`
---------------------------------
``PatternMatchUtils.simpleMatch(String pattern, String str)`` supports **only** the
asterisk; ``?`` is *not* a wildcard, and there is no escaping. ``fnmatch`` would treat
``?`` and ``[...]`` as wildcards and ``re`` would treat ``.``/``+`` as metacharacters, so
both would grant permissions Java denies. The algorithm below is a line-by-line port of
the Java method, including its recursive backtracking.

Behaviour worth remembering
--------------------------
* Both arguments null-checked: a ``None`` pattern or value matches nothing.
* Pattern without ``*`` degenerates to ``equals``.
* ``pattern == "*"`` matches everything, including the empty string.
* Matching is case-sensitive and anchored at both ends.
"""

from __future__ import annotations

from typing import Optional, Sequence


def simple_match(pattern: Optional[str], value: Optional[str]) -> bool:
    """Java: ``PatternMatchUtils.simpleMatch(String pattern, String str)``."""
    if pattern is None or value is None:
        return False
    first_index = pattern.find("*")
    if first_index == -1:
        # No wildcard at all -> plain equality.
        return pattern == value
    if first_index == 0:
        # Leading '*': "abc*" is impossible here, only "*", "**...", "*suffix".
        if len(pattern) == 1:
            return True
        next_index = pattern.find("*", first_index + 1)
        if next_index == -1:
            return value.endswith(pattern[1:])
        part = pattern[1:next_index]
        if part == "":
            return simple_match(pattern[next_index:], value)
        part_index = value.find(part)
        while part_index != -1:
            if simple_match(pattern[next_index:], value[part_index + len(part):]):
                return True
            part_index = value.find(part, part_index + 1)
        return False
    # Trailing or middle '*' with a fixed prefix: consume the prefix, recurse.
    return (
        len(value) >= first_index
        and pattern[:first_index] == value[:first_index]
        and simple_match(pattern[first_index:], value[first_index:])
    )


def simple_match_any(patterns: Optional[Sequence[str]], value: Optional[str]) -> bool:
    """Java: ``PatternMatchUtils.simpleMatch(String[] patterns, String str)``."""
    if patterns is None or value is None:
        return False
    return any(simple_match(pattern, value) for pattern in patterns)


__all__ = ["simple_match", "simple_match_any"]
