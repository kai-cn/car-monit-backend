"""String helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/StringUtils.java

Java original
-------------
``com.ruoyi.common.utils.StringUtils extends org.apache.commons.lang3.StringUtils``. It adds
RuoYi-specific helpers (``hide``, ``str2Set``, ``toUnderScoreCase``, ``isMatch``...) and inherits
the Commons-Lang ones (``isBlank``, ``split``, ``startsWithAny``...).

Python translation notes -- read before changing anything
---------------------------------------------------------
1. **Overloads collapse into one dispatching function.** Java resolves
   ``isEmpty(Collection)`` / ``isEmpty(Object[])`` / ``isEmpty(Map)`` / ``isEmpty(String)`` at
   compile time. Python cannot, so :func:`is_empty` dispatches on the runtime type. The table is
   documented on the function; every call site is therefore still readable as
   "Java's ``StringUtils.isEmpty(x)``".
2. **``trim()`` is Java's, not Python's.** ``String.trim()`` strips characters ``<= U+0020``;
   ``str.strip()`` strips the whole Unicode whitespace set (including ``\\u3000`` and
   ``\\xa0``). With Chinese input a full-width space would silently change
   "is this field empty?" answers, so :func:`java_trim` is used everywhere.
3. **``split`` keeps Java's trailing-empty removal.** ``"a,b,,".split(",")`` is ``["a","b"]``
   in Java and ``["a","b","",""]`` in Python. :func:`split_regex` mirrors the Java behaviour.
4. **``hashCode``-backed sets are plain ``set``.** Java ``HashSet`` insertion order is
   unspecified; Python ``set`` iteration order is also unspecified, and both are only used for
   membership tests here.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Any, Collection, List, Optional, Sequence, Set, TypeVar

#: Java: ``StringUtils.NULLSTR``
NULLSTR = ""
#: Java: ``StringUtils.SEPARATOR``
SEPARATOR = "_"
#: Java: ``StringUtils.ASTERISK``
ASTERISK = "*"

_T = TypeVar("_T")

#: Java: ``Constants.HTTP`` / ``Constants.HTTPS`` (inlined to avoid a constant import cycle).
_HTTP_PREFIXES = ("http://", "https://")


# --------------------------------------------------------------------------- Java 字符语义


def _is_java_whitespace(char: str) -> bool:
    """Java: ``Character.isWhitespace(char)``.

    Differs from ``str.isspace()`` in two places that matter for this project:

    * ``\\xa0`` (NBSP) -- Java says **not** whitespace, Python says whitespace. NBSP arrives in
      copy-pasted Chinese form input, so the difference is observable.
    * ``\\u2007`` / ``\\u202f`` -- same story (non-breaking spaces excluded by Java).

    Escapes ``\\t \\n \\x0b \\f \\r`` and the isISOControl spaces ``\\x1c``-``\\x1f`` are
    whitespace in both languages.
    """
    if char in "\t\n\x0b\f\r\x1c\x1d\x1e\x1f":
        return True
    if char in "\xa0\u2007\u202f":
        return False
    return unicodedata.category(char) == "Zs"


def java_trim(value: Optional[str]) -> Optional[str]:
    """Java: ``String.trim()`` -- strips leading/trailing chars ``<= `` ``' '`` (U+0020).

    ``None`` stays ``None`` (Java would NPE; callers guard with :func:`trim`).
    """
    if value is None:
        return None
    start = 0
    end = len(value)
    while start < end and value[start] <= " ":
        start += 1
    while end > start and value[end - 1] <= " ":
        end -= 1
    return value[start:end]


def _java_char_is_upper(char: str) -> bool:
    """Java: ``Character.isUpperCase(char)``."""
    return char.isupper()


def _java_char_to_lower(char: str) -> str:
    """Java: ``Character.toLowerCase(char)`` -- always a single character.

    Python's ``str.lower()`` may expand (e.g. ``'İ'`` -> ``'i̇'``); Java's ``char`` overload
    cannot, so the first code point is kept.
    """
    lowered = char.lower()
    return lowered[0] if lowered else char


def _java_char_to_upper(char: str) -> str:
    """Java: ``Character.toUpperCase(char)``."""
    uppered = char.upper()
    return uppered[0] if uppered else char


def split_regex(value: Optional[str], pattern: str, limit: int = 0) -> List[str]:
    """Java: ``String.split(String regex, int limit)``.

    ``limit == 0`` (the Java default) removes **all** trailing empty strings; Python's
    ``re.split`` keeps them. This is the single most common source of "why does the list have an
    extra empty element?" drift, hence a dedicated helper.
    """
    if value is None:
        # Java throws NullPointerException; callers always guard. Returning an empty list keeps
        # the failure local and loud only where it matters.
        raise AttributeError("java.lang.NullPointerException: split on null string")
    if limit > 0:
        # maxsplit = limit - 1 -> at most ``limit`` parts, the last one holding the remainder.
        return re.split(pattern, value, maxsplit=limit - 1)
    parts = re.split(pattern, value)
    if limit == 0:
        while parts and parts[-1] == "":
            parts.pop()
    return parts


# --------------------------------------------------------------------------- 空值判断


def is_null(obj: Any) -> bool:
    """Java: ``StringUtils.isNull(Object)`` -- ``object == null``."""
    return obj is None


def is_not_null(obj: Any) -> bool:
    """Java: ``StringUtils.isNotNull(Object)``."""
    return obj is not None


def is_array(obj: Any) -> bool:
    """Java: ``StringUtils.isArray(Object)`` -- ``object.getClass().isArray()``.

    Python has no primitive arrays; ``list``/``tuple``/``set`` are the closest analogue.
    """
    return obj is not None and isinstance(obj, (list, tuple, set, frozenset))


def is_empty(value: Any = None) -> bool:
    """Java: the four ``StringUtils.isEmpty`` overloads, resolved at runtime.

    ==================  ==================================================
    runtime type        Java overload applied
    ==================  ==================================================
    ``None``            every overload returns ``true``
    ``str``             ``isEmpty(String)`` -> ``None`` or blank after ``trim()``
    ``list``/``tuple``  ``isEmpty(Object[])`` -> ``None`` or length ``0``
    ``set``/``dict``    ``isEmpty(Collection)`` / ``isEmpty(Map)``
    ==================  ==================================================

    Deliberate deviation: Python's ``isinstance(True, int)`` and the absence of a ``CharSequence``
    interface mean non-empty scalars (``int``, ``bool``, objects) answer ``False`` -- the same
    answer Java gives for a non-null object that is not a collection.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return java_trim(value) == NULLSTR
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return len(value) == 0
    return False


def is_not_empty(value: Any = None) -> bool:
    """Java: ``StringUtils.isNotEmpty(...)`` -- negation of :func:`is_empty`."""
    return not is_empty(value)


def is_blank(value: Optional[str]) -> bool:
    """Java: ``org.apache.commons.lang3.StringUtils.isBlank(CharSequence)``.

    Unlike :func:`is_empty` this also treats an all-whitespace string as blank -- but with
    ``Character.isWhitespace`` semantics, not ``str.isspace()``.
    """
    if value is None:
        return True
    for char in value:
        if not _is_java_whitespace(char):
            return False
    return True


def is_not_blank(value: Optional[str]) -> bool:
    """Java: ``StringUtils.isNotBlank(CharSequence)``."""
    return not is_blank(value)


def has_text(value: Optional[str]) -> bool:
    """Java: ``StringUtils.hasText(String)`` -- non-null, non-empty and contains a non-space."""
    if value is None or value == "":
        return False
    for char in value:
        if not _is_java_whitespace(char):
            return True
    return False


def nvl(value: Optional[_T], default_value: Optional[_T]) -> Optional[_T]:
    """Java: ``StringUtils.nvl(T, T)``."""
    return value if value is not None else default_value


def trim(value: Optional[str]) -> str:
    """Java: ``StringUtils.trim(String)`` -- null becomes ``""``, **not** ``None``."""
    if value is None:
        return NULLSTR
    return java_trim(value) or NULLSTR


def length(value: Optional[str]) -> int:
    """Java: ``StringUtils.length(CharSequence)`` -- ``null`` has length ``0``."""
    return 0 if value is None else len(value)


def strip_end(value: Optional[str], strip_chars: Optional[str]) -> str:
    """Java: ``StringUtils.stripEnd(String, String)`` -- strip trailing characters.

    ``strip_chars`` 是**字符集合**而不是后缀子串（Commons Lang 语义）：
    ``strip_end("a,,b,,", ",")`` -> ``"a,,b"``，而 ``strip_end("abcba", "ab")``
    -> ``"abc"``（末尾的 ``a`` / ``b`` 逐个剥掉，直到遇到集合外的字符）。

    ``None`` 输入返回 ``""``（RuoYi 的 ``StringUtils`` 把 null 当空串，不抛 NPE）。
    :func:`app.common.utils.dict_utils.get_dict_label` 依赖这一点返回 ``""`` 而不是 ``None``。
    """
    if value is None:
        return NULLSTR
    if not strip_chars:
        return value
    end = len(value)
    while end > 0 and value[end - 1] in strip_chars:
        end -= 1
    return value[:end]


# --------------------------------------------------------------------------- 字符串处理


def hide(value: Optional[str], start_include: int, end_exclude: int) -> str:
    """Java: ``StringUtils.hide(CharSequence, int, int)`` -- mask ``[start, end)`` with ``*``."""
    if is_empty(value):
        return NULLSTR
    assert value is not None
    value_length = len(value)
    if start_include > value_length:
        return NULLSTR
    if end_exclude > value_length:
        end_exclude = value_length
    if start_include > end_exclude:
        return NULLSTR
    chars: List[str] = []
    for index in range(value_length):
        if start_include <= index < end_exclude:
            chars.append(ASTERISK)
        else:
            chars.append(value[index])
    return "".join(chars)


def substring(value: Optional[str], start: int, end: Optional[int] = None) -> str:
    """Java: ``StringUtils.substring(String, int[, int])``.

    Negative indexes count from the end; out-of-range indexes are clamped instead of raising
    (that clamping is why callers can pass unvalidated request values).
    """
    if value is None:
        return NULLSTR

    if end is None:
        if start < 0:
            start = len(value) + start
        if start < 0:
            start = 0
        if start > len(value):
            return NULLSTR
        return value[start:]

    if end < 0:
        end = len(value) + end
    if start < 0:
        start = len(value) + start
    if end > len(value):
        end = len(value)
    if start > end:
        return NULLSTR
    if start < 0:
        start = 0
    if end < 0:
        end = 0
    return value[start:end]


def capitalize(value: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.capitalize(String)`` -- uppercase the **first code unit only**.

    ``null`` and ``""`` are returned unchanged (not ``None``/``""`` swapped), because
    callers pass the result straight into ``RouterVo#setName`` where ``null`` is
    meaningful (``@JsonInclude(NON_EMPTY)`` then drops the key).

    Java uses ``Character.toTitleCase``; for the route names this is applied to
    (``system``, ``user``... i.e. lower-case ASCII) title case and upper case agree.
    """
    if value is None or value == NULLSTR:
        return value
    return _java_char_to_upper(value[0]) + value[1:]


def uncapitalize(value: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.uncapitalize(String)`` -- lowercase the **first code unit only**.

    Commons Lang 的对称函数（本项目的 ``StringUtils`` 继承了它）。代码生成器用它把
    ``SysUser`` 变成 ``sysUser``（模板里的 ``${className}``），所以 ``None``/``""``
    必须原样返回 —— ``None`` 进去再变成 ``""`` 会让 ``#if`` 判断与 Java 分叉。
    """
    if value is None or value == NULLSTR:
        return value
    return _java_char_to_lower(value[0]) + value[1:]


def ends_with_ignore_case(value: Optional[str], suffix: Optional[str]) -> bool:
    """Java: ``StringUtils.endsWithIgnoreCase(CharSequence, CharSequence)``.

    ``GenUtils#initColumnField`` 用它按列名后缀推断控件类型（``status`` -> 单选、
    ``file`` -> 文件上传）。任一侧为 ``null`` 时为 false，空后缀会命中**任意**字符串
    （与 Java 一致，所以调用点都不传空串）。
    """
    if value is None or suffix is None:
        return False
    return value.lower().endswith(suffix.lower())


def join(values: Optional[Sequence[Any]], separator: Optional[str]) -> str:
    """Java: ``StringUtils.join(Object[] array, String separator)``.

    ``null`` 元素写成空串（Commons Lang 的行为，**不是** ``str(None)``），
    ``null`` 数组返回空串。
    """
    if values is None:
        return NULLSTR
    parts = [NULLSTR if item is None else str(item) for item in values]
    return (separator or NULLSTR).join(parts)


def format(template: Optional[str], *params: Any) -> Optional[str]:
    """Java: ``StringUtils.format(String, Object...)`` -> :func:`str_formatter.format`."""
    # Local import: str_formatter imports this module for its emptiness check.
    from app.common.core.text.str_formatter import format as _format

    if len(params) == 0 or is_empty(template):
        return template
    return _format(template, *params)


def is_http(link: Optional[str]) -> bool:
    """Java: ``StringUtils.ishttp(String)``."""
    return starts_with_any(link, _HTTP_PREFIXES)


def get_uuid() -> str:
    """Java: ``StringUtils.getUUID()`` -- random UUID without dashes."""
    return str(uuid.uuid4()).replace("-", "")


# --------------------------------------------------------------------------- 集合转换


def split_regex_list(value: str, sep: str) -> List[str]:
    """Java: ``str.split(sep)`` inside :func:`str2_list`."""
    return split_regex(value, sep)


def str2_list(value: Optional[str], sep: str, filter_blank: bool, do_trim: bool) -> List[str]:
    """Java: ``StringUtils.str2List(String, String, boolean, boolean)``."""
    result: List[str] = []
    if is_empty(value):
        return result
    assert value is not None
    if filter_blank and is_blank(value):
        return result
    for item in split_regex(value, sep):
        if filter_blank and is_blank(item):
            continue
        if do_trim:
            item = java_trim(item) or ""
        result.append(item)
    return result


def str2_set(value: Optional[str], sep: str) -> Set[str]:
    """Java: ``StringUtils.str2Set(String, String)``."""
    return set(str2_list(value, sep, True, False))


def string_to_list(content: Optional[str]) -> List[str]:
    """Java: ``StringUtils.stringToList(String)`` -- comma separated -> mutable list."""
    if is_not_empty(content):
        assert content is not None
        return split_regex(content, ",")
    return []


def contains_any(collection: Optional[Collection[str]], *array: str) -> bool:
    """Java: ``StringUtils.containsAny(Collection<String>, String...)``."""
    if is_empty(collection) or len(array) == 0:
        return False
    assert collection is not None
    for item in array:
        if item in collection:
            return True
    return False


def contains_any_ignore_case(value: Optional[str], *search: str) -> bool:
    """Java: ``StringUtils.containsAnyIgnoreCase(CharSequence, CharSequence...)``."""
    if is_empty(value) or len(search) == 0:
        return False
    assert value is not None
    for candidate in search:
        if contains_ignore_case(value, candidate):
            return True
    return False


def in_string_ignore_case(value: Optional[str], *candidates: str) -> bool:
    """Java: ``StringUtils.inStringIgnoreCase(String, String...)``."""
    if value is not None:
        for candidate in candidates:
            if value.lower() == trim(candidate).lower():
                return True
    return False


def matches(value: Optional[str], patterns: Optional[Sequence[str]]) -> bool:
    """Java: ``StringUtils.matches(String, List<String>)`` -- any Ant pattern matches."""
    if is_empty(value) or is_empty(patterns):
        return False
    assert value is not None and patterns is not None
    for pattern in patterns:
        if is_match(pattern, value):
            return True
    return False


def cast(value: Any) -> Any:
    """Java: ``StringUtils.cast(Object)`` -- an unchecked cast, i.e. a no-op in Python."""
    return value


# --------------------------------------------------------------------------- 命名风格转换


def to_under_score_case(value: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.toUnderScoreCase(String)`` -- ``AbcDef`` -> ``abc_def``."""
    if value is None:
        return None
    parts: List[str] = []
    # Java initialises this to true *before* the loop and only reassigns it while i < len-1,
    # so on the last character it still holds the case of the second-to-last lookahead == the
    # case of the last character. Keeping it outside the loop reproduces that exactly.
    next_char_is_upper = True
    value_length = len(value)
    for index, char in enumerate(value):
        if index > 0:
            pre_char_is_upper = _java_char_is_upper(value[index - 1])
        else:
            pre_char_is_upper = False
        current_is_upper = _java_char_is_upper(char)
        if index < value_length - 1:
            next_char_is_upper = _java_char_is_upper(value[index + 1])
        if pre_char_is_upper and current_is_upper and not next_char_is_upper:
            parts.append(SEPARATOR)
        elif index != 0 and not pre_char_is_upper and current_is_upper:
            parts.append(SEPARATOR)
        parts.append(_java_char_to_lower(char))
    return "".join(parts)


def convert_to_camel_case(name: Optional[str]) -> str:
    """Java: ``StringUtils.convertToCamelCase(String)`` -- ``HELLO_WORLD`` -> ``HelloWorld``."""
    if name is None or name == "":
        return ""
    if "_" not in name:
        return name[0].upper() + name[1:]
    result: List[str] = []
    for camel in split_regex(name, "_"):
        if camel == "":
            continue
        result.append(camel[0].upper())
        result.append(camel[1:].lower())
    return "".join(result)


def to_camel_case(value: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.toCamelCase(String)`` -- ``user_name`` -> ``userName``."""
    if value is None:
        return None
    if SEPARATOR not in value:
        return value
    lowered = value.lower()
    result: List[str] = []
    upper_case = False
    for char in lowered:
        if char == SEPARATOR:
            upper_case = True
        elif upper_case:
            result.append(_java_char_to_upper(char))
            upper_case = False
        else:
            result.append(char)
    return "".join(result)


# --------------------------------------------------------------------------- 左侧补齐


def padl_number(num: Any, size: int) -> str:
    """Java: ``StringUtils.padl(Number, int)``."""
    return padl(str(num), size, "0")


def padl(value: Optional[str], size: int, pad_char: str) -> str:
    """Java: ``StringUtils.padl(String, int, char)`` -- keep the *last* ``size`` chars."""
    if value is not None:
        value_length = len(value)
        if value_length <= size:
            return pad_char * (size - value_length) + value
        return value[value_length - size:]
    return pad_char * size


# --------------------------------------------------------------------------- Commons-Lang 子集


def is_any_blank(*values: Optional[str]) -> bool:
    """Java: ``StringUtils.isAnyBlank(CharSequence...)``."""
    for value in values:
        if is_blank(value):
            return True
    return False


def equals(value1: Optional[str], value2: Optional[str]) -> bool:
    """Java: ``StringUtils.equals(CharSequence, CharSequence)`` -- null-safe."""
    return value1 == value2


def equals_ignore_case(value1: Optional[str], value2: Optional[str]) -> bool:
    """Java: ``StringUtils.equalsIgnoreCase(CharSequence, CharSequence)``."""
    if value1 is None or value2 is None:
        return value1 is value2
    return value1.lower() == value2.lower()


def contains(value: Optional[str], search: Optional[str]) -> bool:
    """Java: ``StringUtils.contains(CharSequence, CharSequence)``."""
    if value is None or search is None:
        return False
    return search in value


def contains_ignore_case(value: Optional[str], search: Optional[str]) -> bool:
    """Java: ``StringUtils.containsIgnoreCase(CharSequence, CharSequence)``."""
    if value is None or search is None:
        return False
    return search.lower() in value.lower()


def index_of_ignore_case(value: str, search: str) -> int:
    """Java: ``StringUtils.indexOfIgnoreCase(CharSequence, CharSequence)``."""
    return value.lower().find(search.lower())


def starts_with(value: Optional[str], prefix: Optional[str]) -> bool:
    """Java: ``StringUtils.startsWith(CharSequence, CharSequence)``."""
    if value is None or prefix is None:
        return False
    return value.startswith(prefix)


def starts_with_any(value: Optional[str], prefixes: Optional[Sequence[str]]) -> bool:
    """Java: ``StringUtils.startsWithAny(CharSequence, CharSequence...)``."""
    if value is None or not prefixes:
        return False
    return value.startswith(tuple(prefixes))


def split(value: Optional[str], separator_chars: Optional[str]) -> Optional[List[str]]:
    """Java: ``StringUtils.split(String str, String separatorChars)``.

    Splits on **any** character of ``separatorChars`` and drops empty tokens; returns ``None``
    for ``None`` input. This is *not* the same as :func:`split_regex` -- keep both.
    """
    if value is None:
        return None
    if separator_chars is None:
        separator_chars = " \t\n\r\f"
    parts: List[str] = []
    current: List[str] = []
    for char in value:
        if char in separator_chars:
            if current:
                parts.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current))
    return parts


def count_matches(value: Optional[str], sub: Optional[str]) -> int:
    """Java: ``StringUtils.countMatches(CharSequence, CharSequence)`` -- non-overlapping count."""
    if is_empty(value) or is_empty(sub):
        return 0
    assert value is not None and sub is not None
    return value.count(sub)


def substring_before(value: Optional[str], separator: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.substringBefore(String, String)``.

    The separator-less / empty-separator cases keep Java's exact semantics: ``None`` in ->
    ``None`` out, and an empty separator returns ``""`` (not the whole string).
    """
    if is_empty(value):
        return value
    if separator is None:
        return value
    assert value is not None
    if separator == NULLSTR:
        return NULLSTR
    index = value.find(separator)
    return value if index == -1 else value[:index]


def substring_after(value: Optional[str], separator: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.substringAfter(String, String)``."""
    if is_empty(value):
        return value
    if separator is None:
        return NULLSTR
    assert value is not None
    if separator == NULLSTR:
        return value
    index = value.find(separator)
    return NULLSTR if index == -1 else value[index + len(separator):]


def substring_before_last(value: Optional[str], separator: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.substringBeforeLast(String, String)``.

    ``substringBeforeLast("abcde", "b")`` -> ``"a"``; when the separator is absent the whole
    value comes back (this is what makes a bare ``"ryTask"`` bean name survive). Java 的
    判据是 ``isEmpty(separator)``（不是 ``== null``），空分隔符同样返回原串。
    """
    if is_empty(value) or is_empty(separator):
        return value
    assert value is not None and separator is not None
    index = value.rfind(separator)
    return value if index == -1 else value[:index]


def substring_after_last(value: Optional[str], separator: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.substringAfterLast(String, String)``.

    分隔符缺失、为空、或正好落在末尾时都返回 ``""`` —— Java 原文用
    ``pos == str.length() - separator.length()`` 显式挡掉末位。
    """
    if is_empty(value):
        return value
    if separator is None or separator == NULLSTR:
        return NULLSTR
    assert value is not None
    index = value.rfind(separator)
    if index == -1 or index == len(value) - len(separator):
        return NULLSTR
    return value[index + len(separator):]


def substring_between(
    value: Optional[str], open_token: Optional[str], close_token: Optional[str]
) -> Optional[str]:
    """Java: ``StringUtils.substringBetween(String, String, String)``.

    Java 原文是先 ``indexOf(open)``、再 ``indexOf(close, start + open.length())`` ——
    配对的是**第一个** close，不是最后一个（``rfind`` 是错的）。三段有一段缺失就返回
    ``None``。``"a(b)c(d"`` 因此返回 ``"b"``。``JobInvokeUtil#getMethodParams`` 靠它
    取括号内的参数串。
    """
    if value is None or open_token is None or close_token is None:
        return None
    start = value.find(open_token)
    if start == -1:
        return None
    start += len(open_token)
    end = value.find(close_token, start)
    if end == -1:
        return None
    return value[start:end]


def trim_to_empty(value: Optional[str]) -> str:
    """Java: ``StringUtils.trimToEmpty(String)`` -- ``None`` -> ``""``."""
    return NULLSTR if value is None else value.strip(" \t\n\r\f\v")


def replace(value: Optional[str], search: Optional[str], replacement: Optional[str]) -> Optional[str]:
    """Java: ``StringUtils.replace(String, String, String)`` -- literal, all occurrences."""
    if is_empty(value) or is_empty(search) or replacement is None:
        return value
    assert value is not None and search is not None
    return value.replace(search, replacement)


def replace_ignore_case(
    value: Optional[str], search: Optional[str], replacement: Optional[str]
) -> Optional[str]:
    """Java: ``StringUtils.replaceIgnoreCase(String, String, String)``."""
    if is_empty(value) or is_empty(search) or replacement is None:
        return value
    assert value is not None and search is not None
    pattern = re.compile(re.escape(search), re.IGNORECASE)
    return pattern.sub(lambda _m: replacement, value)


# --------------------------------------------------------------------------- Ant 路径匹配


def is_match(pattern: str, url: str) -> bool:
    """Java: ``StringUtils.isMatch(String pattern, String url)`` using Spring's AntPathMatcher.

    Token rules (Spring ``AntPathMatcher``):
      ``?``  exactly one character
      ``*``  zero or more characters **within** one path segment
      ``**`` zero or more path segments
    """
    return _ant_path_match(pattern, url)


def _ant_path_match(pattern: str, path: str, full_match: bool = True) -> bool:
    """Ported 1:1 from ``AntPathMatcher.doMatch`` (caseSensitive=true, trimTokens=false).

    The algorithm has four stages and every one of them matters:

    1. compare segments left to right until the first ``**``;
    2. if the path ran out, the remaining pattern must be ``*``/``**`` (plus Spring's
       trailing-separator rule);
    3. compare segments **right to left** until the last ``**`` -- this is what makes
       ``/**/*.html`` match ``/a/b/index.html``;
    4. walk the ``**`` blocks in the middle by searching for the literal run between them.

    Stage 3 is the one people forget when re-implementing this from memory, and without it
    ``/**/*.html`` silently stops matching. Stage 2's trailing-separator rule is why
    ``/login`` does **not** match ``/login/`` -- clients hitting the wrong trailing slash must be
    rejected exactly like in Java.
    """
    if path.startswith("/") != pattern.startswith("/"):
        return False

    patt_dirs = _tokenize_path(pattern)
    path_dirs = _tokenize_path(path)

    patt_idx_start = 0
    patt_idx_end = len(patt_dirs) - 1
    path_idx_start = 0
    path_idx_end = len(path_dirs) - 1

    # 1) Match all elements up to the first '**'.
    while patt_idx_start <= patt_idx_end and path_idx_start <= path_idx_end:
        patt_dir = patt_dirs[patt_idx_start]
        if patt_dir == "**":
            break
        if not _match_strings(patt_dir, path_dirs[path_idx_start]):
            return False
        patt_idx_start += 1
        path_idx_start += 1

    # 2) Path exhausted -- only match if the rest of the pattern is '*' or '**'.
    if path_idx_start > path_idx_end:
        if patt_idx_start > patt_idx_end:
            # Spring: pattern.endsWith("/") ? path.endsWith("/") : !path.endsWith("/")
            if pattern.endswith("/"):
                return path.endswith("/")
            return not path.endswith("/")
        if not full_match:
            return True
        if (
            patt_idx_start == patt_idx_end
            and patt_dirs[patt_idx_start] == "*"
            and path.endswith("/")
        ):
            return True
        for index in range(patt_idx_start, patt_idx_end + 1):
            if patt_dirs[index] != "**":
                return False
        return True

    if patt_idx_start > patt_idx_end:
        # Path not exhausted, but pattern is.
        return False
    if not full_match and patt_dirs[patt_idx_start] == "**":
        return True

    # 3) Match back to the last '**'.
    while patt_idx_start <= patt_idx_end and path_idx_start <= path_idx_end:
        patt_dir = patt_dirs[patt_idx_end]
        if patt_dir == "**":
            break
        if not _match_strings(patt_dir, path_dirs[path_idx_end]):
            return False
        patt_idx_end -= 1
        path_idx_end -= 1

    if path_idx_start > path_idx_end:
        for index in range(patt_idx_start, patt_idx_end + 1):
            if patt_dirs[index] != "**":
                return False
        return True

    # 4) Walk the '**' blocks in the middle.
    while patt_idx_start != patt_idx_end and path_idx_start <= path_idx_end:
        pat_idx_tmp = -1
        for index in range(patt_idx_start + 1, patt_idx_end + 1):
            if patt_dirs[index] == "**":
                pat_idx_tmp = index
                break
        if pat_idx_tmp == patt_idx_start + 1:
            # '**/**' situation, so skip one
            patt_idx_start += 1
            continue
        pat_length = pat_idx_tmp - patt_idx_start - 1
        str_length = path_idx_end - path_idx_start + 1
        found_idx = -1
        for offset in range(0, str_length - pat_length + 1):
            matched = True
            for step in range(pat_length):
                if not _match_strings(
                    patt_dirs[patt_idx_start + step + 1],
                    path_dirs[path_idx_start + offset + step],
                ):
                    matched = False
                    break
            if matched:
                found_idx = path_idx_start + offset
                break
        if found_idx == -1:
            return False
        patt_idx_start = pat_idx_tmp
        path_idx_start = found_idx + pat_length

    for index in range(patt_idx_start, patt_idx_end + 1):
        if patt_dirs[index] != "**":
            return False
    return True


def _tokenize_path(path: str) -> List[str]:
    """Java: ``StringUtils.tokenizeToStringArray(path, \"/\", false, true)`` -- drop empties."""
    return [segment for segment in path.split("/") if segment != ""]


#: Java: ``AntPathMatcher.GLOB_PATTERN``; only the constructs RuoYi patterns use are handled.
_GLOB_PATTERN = re.compile(r"\?|\*|\{((?:\{[^/]+?\}|[^/{}]|\\[{}])+?)\}")
#: Java: ``AntPathMatcher.DEFAULT_VARIABLE_PATTERN``
_DEFAULT_VARIABLE_PATTERN = "([^/]*)"


def _match_strings(pattern: str, value: str) -> bool:
    """Java: ``AntPathMatcher.matchStrings(String, String)`` on a single path segment.

    ``?`` -> one character, ``*`` -> any run of characters, ``{name}`` / ``{name:regex}`` -> URI
    template variable. Everything else is escaped and matched literally.
    """
    builder: List[str] = []
    end = 0
    for match in _GLOB_PATTERN.finditer(pattern):
        builder.append(re.escape(pattern[end:match.start()]))
        token = match.group(0)
        if token == "?":
            builder.append(".")
        elif token == "*":
            builder.append(".*")
        elif token.startswith("{") and token.endswith("}"):
            colon_idx = token.find(":")
            if colon_idx == -1:
                builder.append(_DEFAULT_VARIABLE_PATTERN)
            else:
                builder.append("(")
                builder.append(token[colon_idx + 1:-1])
                builder.append(")")
        end = match.end()
    builder.append(re.escape(pattern[end:]))
    return re.fullmatch("".join(builder), value) is not None


__all__ = [
    "NULLSTR",
    "SEPARATOR",
    "ASTERISK",
    "java_trim",
    "split_regex",
    "is_null",
    "is_not_null",
    "is_array",
    "is_empty",
    "is_not_empty",
    "is_blank",
    "is_not_blank",
    "has_text",
    "nvl",
    "trim",
    "length",
    "strip_end",
    "hide",
    "substring",
    "capitalize",
    "uncapitalize",
    "ends_with_ignore_case",
    "join",
    "format",
    "is_http",
    "get_uuid",
    "str2_list",
    "str2_set",
    "string_to_list",
    "contains_any",
    "contains_any_ignore_case",
    "in_string_ignore_case",
    "matches",
    "cast",
    "to_under_score_case",
    "convert_to_camel_case",
    "to_camel_case",
    "padl_number",
    "padl",
    "is_any_blank",
    "equals",
    "equals_ignore_case",
    "contains",
    "contains_ignore_case",
    "index_of_ignore_case",
    "starts_with",
    "starts_with_any",
    "split",
    "count_matches",
    "substring_before",
    "substring_after",
    "substring_before_last",
    "substring_after_last",
    "substring_between",
    "trim_to_empty",
    "replace",
    "replace_ignore_case",
    "is_match",
]
