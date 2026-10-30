"""Date/time helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/DateUtils.java

Java original
-------------
``DateUtils extends org.apache.commons.lang3.time.DateUtils`` and works with ``java.util.Date``
(millisecond precision). Format strings are ``SimpleDateFormat`` patterns such as
``"yyyy-MM-dd HH:mm:ss"``.

Python translation
------------------
``java.util.Date`` -> ``datetime.datetime`` (naive, local time). Naive-on-purpose: Java's
``Date`` carries no zone, and every consumer here formats it with the JVM default zone, which is
the same thing Python's ``datetime.now()`` produces.

``SimpleDateFormat`` patterns are translated at call time (:func:`_format_java`) instead of being
rewritten to ``strftime`` by hand, so a pattern copied from Java keeps working. Only the letters
this codebase uses are translated; anything else is emitted verbatim, exactly like
``SimpleDateFormat`` does for quoted literals.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Any, List, Optional

#: Java: ``DateUtils.YYYY``
YYYY = "yyyy"
#: Java: ``DateUtils.YYYY_MM``
YYYY_MM = "yyyy-MM"
#: Java: ``DateUtils.YYYY_MM_DD``
YYYY_MM_DD = "yyyy-MM-dd"
#: Java: ``DateUtils.YYYYMMDDHHMMSS``
YYYYMMDDHHMMSS = "yyyyMMddHHmmss"
#: Java: ``DateUtils.YYYY_MM_DD_HH_MM_SS``
YYYY_MM_DD_HH_MM_SS = "yyyy-MM-dd HH:mm:ss"

#: Java: ``DateUtils.parsePatterns`` -- tried in order by :func:`parse_date`.
PARSE_PATTERNS: List[str] = [
    "yyyy-MM-dd",
    "yyyy-MM-dd HH:mm:ss",
    "yyyy-MM-dd HH:mm",
    "yyyy-MM",
    "yyyy/MM/dd",
    "yyyy/MM/dd HH:mm:ss",
    "yyyy/MM/dd HH:mm",
    "yyyy/MM",
    "yyyy.MM.dd",
    "yyyy.MM.dd HH:mm:ss",
    "yyyy.MM.dd HH:mm",
    "yyyy.MM",
]

#: Placeholder for ``SSS`` -- ``strftime`` has no millisecond directive (``%f`` is microsecond).
_MILLIS_TOKEN = "\x00SSS\x00"

#: ``SimpleDateFormat`` letter -> ``strftime`` directive. Longer tokens must come first.
_PATTERN_TOKEN = re.compile(r"SSS|yyyy|yy|MM|dd|HH|mm|ss|S")

_PATTERN_REPLACEMENTS = {
    "SSS": _MILLIS_TOKEN,
    "yyyy": "%Y",
    "yy": "%y",
    "MM": "%m",
    "dd": "%d",
    "HH": "%H",
    "mm": "%M",
    "ss": "%S",
    "S": _MILLIS_TOKEN,
}

#: Server start time, captured at import -- Java reads the JVM's ``RuntimeMXBean`` start time.
_SERVER_START_DATE: datetime = datetime.now()


def _format_java(pattern: str, value: datetime) -> str:
    """Format ``value`` using a ``SimpleDateFormat`` pattern."""
    rendered = _PATTERN_TOKEN.sub(lambda match: _PATTERN_REPLACEMENTS[match.group(0)], pattern)
    text = value.strftime(rendered)
    if _MILLIS_TOKEN in text:
        text = text.replace(_MILLIS_TOKEN, f"{value.microsecond // 1000:03d}")
    return text


def _parse_java(pattern: str, text: str) -> datetime:
    """Parse ``text`` with a ``SimpleDateFormat`` pattern.

    ``SimpleDateFormat`` is lenient by default in Commons-Lang's
    ``DateUtils.parseDate``; ``strptime`` rejects e.g. ``2026-02-31``. Silently rolling invalid
    dates over would hide data errors, so strictness is kept here and the caller decides
    (see :func:`parse_date`, which swallows the error like Java does).
    """
    rendered = _PATTERN_TOKEN.sub(lambda match: _PATTERN_REPLACEMENTS[match.group(0)], pattern)
    rendered = rendered.replace(_MILLIS_TOKEN, "%f")
    return datetime.strptime(text, rendered)


# --------------------------------------------------------------------------- 当前时间


def get_now_date() -> datetime:
    """Java: ``DateUtils.getNowDate()``."""
    return datetime.now()


def get_year_month() -> str:
    """Java: ``DateUtils.getYearMonth()`` -> ``yyyy-MM``."""
    return date_time_now(YYYY_MM)


def get_date() -> str:
    """Java: ``DateUtils.getDate()`` -> ``yyyy-MM-dd``."""
    return date_time_now(YYYY_MM_DD)


def get_time() -> str:
    """Java: ``DateUtils.getTime()`` -> ``yyyy-MM-dd HH:mm:ss``."""
    return date_time_now(YYYY_MM_DD_HH_MM_SS)


def date_time_now(fmt: str = YYYYMMDDHHMMSS) -> str:
    """Java: ``DateUtils.dateTimeNow([String format])``."""
    return parse_date_to_str(fmt, datetime.now())


def date_time_str(value: Optional[datetime]) -> Optional[str]:
    """Java: ``DateUtils.dateTime(Date date)`` -> ``yyyy-MM-dd``."""
    return parse_date_to_str(YYYY_MM_DD, value)


def parse_date_to_str(fmt: Optional[str], value: Optional[datetime]) -> Optional[str]:
    """Java: ``DateUtils.parseDateToStr(String format, Date date)``.

    Returns ``None`` when the pattern is blank or the date is null (Java does the same, which is
    why callers must tolerate ``null`` here).
    """
    from app.common.utils.string_utils import is_blank

    if is_blank(fmt) or value is None:
        return None
    assert fmt is not None
    return _format_java(fmt, value)


def date_time_parse(fmt: str, text: str) -> datetime:
    """Java: ``DateUtils.dateTime(String format, String ts)``.

    Java wraps ``ParseException`` in ``RuntimeException``; Python's ``ValueError`` is already
    unchecked, so it propagates unchanged.
    """
    return _parse_java(fmt, text)


def date_path() -> str:
    """Java: ``DateUtils.datePath()`` -> ``yyyy/MM/dd`` (used to build upload directories)."""
    return _format_java("yyyy/MM/dd", datetime.now())


def date_time_ymd() -> str:
    """Java: ``DateUtils.dateTime()`` -> ``yyyyMMdd``."""
    return _format_java("yyyyMMdd", datetime.now())


def parse_date(value: Any) -> Optional[datetime]:
    """Java: ``DateUtils.parseDate(Object)`` -- try every pattern, return ``None`` on failure."""
    if value is None:
        return None
    text = value if isinstance(value, str) else str(value)
    for pattern in PARSE_PATTERNS:
        try:
            return _parse_java(pattern, text)
        except ValueError:
            continue
    return None


# --------------------------------------------------------------------------- 时间差


def get_server_start_date() -> datetime:
    """Java: ``DateUtils.getServerStartDate()`` -- JVM start time, here the process start."""
    return _SERVER_START_DATE


def different_days_by_millisecond(date1: datetime, date2: datetime) -> int:
    """Java: ``DateUtils.differentDaysByMillisecond(Date, Date)``.

    Java truncates towards zero **before** ``Math.abs`` (``(int)`` cast happens first), so
    ``-7`` days becomes ``7`` while ``-0.5`` days becomes ``0`` -- not ``1``.
    """
    delta_ms = _millis(date2) - _millis(date1)
    return abs(int(delta_ms / (1000 * 3600 * 24)))


def time_distance(end_date: datetime, start_time: datetime) -> str:
    """Java: ``DateUtils.timeDistance(Date endDate, Date startTime)`` -> ``"x天x小时x分钟"``."""
    nd = 1000 * 24 * 60 * 60
    nh = 1000 * 60 * 60
    nm = 1000 * 60
    diff = _millis(end_date) - _millis(start_time)
    day = int(diff / nd)
    hour = int(diff % nd / nh)
    minute = int(diff % nd % nh / nm)
    return f"{day}天{hour}小时{minute}分钟"


def get_timestamp() -> datetime:
    """Java: ``DateUtils.getTimestamp()`` -- now, truncated to milliseconds.

    Python keeps microseconds, so the value is intentionally floored to 1000 µs to match
    ``Timestamp.valueOf("yyyy-MM-dd HH:mm:ss.SSS")``.
    """
    return _truncate_to_millis(datetime.now())


def get_timestamp_new() -> datetime:
    """Java: ``DateUtils.getTimestampNew()`` -- identical body to :func:`get_timestamp`."""
    return get_timestamp()


def get_timestamp_new2() -> datetime:
    """Java: ``DateUtils.getTimestampNew2()`` -- now minus two days, to the millisecond."""
    return _truncate_to_millis(datetime.now() - timedelta(days=2))


def current_time_millis() -> int:
    """Java: ``System.currentTimeMillis()``.

    Not a ``DateUtils`` member -- Java calls the JDK method directly -- but it lives here
    because this module already owns the ``Date`` <-> epoch-millisecond conversions.

    ``time.time()`` is used instead of ``datetime.now().timestamp()``: the latter reads the
    naive local clock and then lets ``timestamp()`` interpret it in the host time zone, so a
    misconfigured ``TZ`` would shift the value. ``System.currentTimeMillis()`` never depends
    on the zone, and neither does this.
    """
    return int(time.time() * 1000)


def java_date_to_string(value: Optional[datetime] = None) -> str:
    """Java: ``java.util.Date#toString()`` -- ``"EEE MMM dd HH:mm:ss zzz yyyy"``.

    形如 ``Thu Oct 29 11:05:31 CST 2026``。只用于**日志文案**（``"..." + new Date()``
    这类拼接），不参与任何 JSON 序列化 —— 所以格式差异不影响接口。

    三点与 ``str(datetime)`` 的区别：
    * 星期 / 月份是**英文三字母缩写**且**不本地化**（``Date.toString`` 用的是
      ``DateUtils`` 内置的英文表，与 JVM 的 ``Locale`` 无关）；
    * 日**补零两位**（``Oct 05``）；
    * 时区是**短名**（``Asia/Shanghai`` -> ``CST``），不是 ``+08:00``。
      传进来的若是 naive ``datetime``（本工程的全部约定），取本机偏移判断。
    """
    moment = value if value is not None else datetime.now()
    weekday = _JAVA_WEEKDAYS[moment.weekday()]
    month = _JAVA_MONTHS[moment.month - 1]
    zone = moment.tzname() or ""
    if not zone:
        zone = _local_zone_abbreviation()
    return "%s %s %02d %02d:%02d:%02d %s %04d" % (
        weekday,
        month,
        moment.day,
        moment.hour,
        moment.minute,
        moment.second,
        zone,
        moment.year,
    )


#: ``Date.toString`` 的星期表（``Calendar.SUNDAY`` 起）。
_JAVA_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

#: ``Date.toString`` 的月份表。
_JAVA_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

#: ``Asia/Shanghai`` 的 JDK 短名；本工程所有部署都在 ``+08:00``。
_DEFAULT_ZONE_ABBREVIATION = "CST"


def _local_zone_abbreviation() -> str:
    """取本机时区的 JDK 短名（``Asia/Shanghai`` -> ``CST``）。"""
    offset = datetime.now().astimezone().utcoffset()
    if offset is not None and offset == timedelta(hours=8):
        return _DEFAULT_ZONE_ABBREVIATION
    return datetime.now().astimezone().tzname() or _DEFAULT_ZONE_ABBREVIATION


def _millis(value: datetime) -> int:
    """``Date.getTime()`` -- epoch milliseconds."""
    return int(value.timestamp() * 1000)


def _truncate_to_millis(value: datetime) -> datetime:
    return value.replace(microsecond=(value.microsecond // 1000) * 1000)


__all__ = [
    "YYYY",
    "YYYY_MM",
    "YYYY_MM_DD",
    "YYYYMMDDHHMMSS",
    "YYYY_MM_DD_HH_MM_SS",
    "PARSE_PATTERNS",
    "get_now_date",
    "get_year_month",
    "get_date",
    "get_time",
    "date_time_now",
    "date_time_str",
    "parse_date_to_str",
    "date_time_parse",
    "date_path",
    "date_time_ymd",
    "parse_date",
    "get_server_start_date",
    "different_days_by_millisecond",
    "time_distance",
    "get_timestamp",
    "get_timestamp_new",
    "get_timestamp_new2",
    "current_time_millis",
    "java_date_to_string",
]
