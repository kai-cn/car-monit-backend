"""JSON wire-format helpers that reproduce Jackson's / Spring Boot's output exactly.

# Migrated from: (no single Java file) -- consolidates the serialization rules that
# Java expresses through annotations on ``BaseEntity`` / ``SysUser`` / ``SysRole``.

Why this module exists
----------------------
Java spreads its JSON contract over annotations (``@JsonFormat``, ``@JsonIgnore``,
``@JsonInclude``) that Jackson applies at runtime. Python has no annotation processor,
so the same rules are re-stated here as explicit helpers and applied by
:class:`app.common.core.domain.domain_model.DomainModel`.

Measured Java behaviour
-----------------------
Everything below was **measured**, not read off documentation, by running Jackson
2.11.4 (the version resolved by Spring Boot 2.5.15) and Spring's
``Jackson2ObjectMapperBuilder`` against a stand-in for ``SysUser``::

    JVM default TimeZone : Asia/Shanghai
    bare ObjectMapper    : {"createTime":"2025-10-23 13:25:09","userName":"admin",
                            "email":null,"loginDate":1761225909123}
    Spring builder       : (identical)

Conclusions, each of which is load-bearing:

1. A ``java.util.Date`` **with** ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
   (``BaseEntity.createTime`` / ``updateTime``) is served as the **stored wall clock,
   unchanged**: a ``datetime`` column holding ``2021-05-06 00:36:41`` comes back as
   ``"2021-05-06 00:36:41"``. Two effects cancel out. ``serverTimezone=GMT+8`` makes
   the driver read the wall clock as ``+08:00``, and Jackson renders the resulting
   instant in ``+08:00`` as well because the ``ObjectMapper`` that the running
   application uses (Spring Boot's ``Jackson2ObjectMapperBuilder``) carries the JVM
   zone, not Jackson's bare-mapper default of UTC.
2. A ``java.util.Date`` **without** ``@JsonFormat`` (``SysUser.loginDate``,
   ``OdsProvcapture.loadtime`` / ``tailcapturetime``) becomes an **ISO-8601 string
   with milliseconds and offset**: ``"2024-05-17T14:15:52.000+08:00"`` -- *not* an
   integer of epoch milliseconds. Spring Boot sets
   ``SerializationFeature.WRITE_DATES_AS_TIMESTAMPS`` to **disabled** by default, so
   a ``Date`` is written by ``StdDateFormat``. Both facts were re-measured against the
   running ``ruoyi-admin.jar`` on 2026-10-28; the earlier "measured" notes above
   described a **bare** mapper and were wrong for the deployed application.
3. ``null`` fields are emitted (``"email":null``): Jackson's default inclusion is
   ``ALWAYS``.
4. ``@JsonInclude(NON_EMPTY)`` drops ``BaseEntity.params`` when it is an empty map.
5. ``@JsonIgnore`` drops ``BaseEntity.searchValue`` in both directions.
6. ``@JsonIgnore`` + ``@JsonProperty`` **on a getter** (``SysUser.getPassword()``)
   makes the property write-only: absent from output, still accepted on input.
   NOTE the asymmetry -- the same pair **on a field** is serialized. ``SysUser``
   puts them on the getter, so the bcrypt hash never leaves the process. Verified
   both ways; see ``COMPATIBILITY.md``.
7. A public ``isXxx()`` method becomes a property even with no backing field, so
   ``SysUser.isAdmin()`` adds ``"admin": true|false`` to every user payload.

Two zones, two jobs
-------------------
``java.util.Date`` is an instant; a naive Python ``datetime`` is a wall clock. Because
MySQL columns are ``datetime`` (zone-less) and the JDBC URL pins ``serverTimezone=GMT+8``,
the driver turns a stored ``13:25:09`` into the instant ``2025-10-23T05:25:09Z``. That
conversion uses the **JVM/server zone** (:func:`jvm_timezone`). Rendering that instant for
``@JsonFormat`` then uses the **Jackson zone** (:func:`json_format_timezone`), which in the
running application is the same JVM zone -- that is why a wall clock survives the round
trip unchanged. Mixing the two without checking is how you get a silent 8-hour error, so
they are separate functions with separate names on purpose.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, tzinfo
import json
from typing import Any, Optional

#: Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")`` (kept for documentation and tests)
JSON_DATE_TIME_PATTERN = "yyyy-MM-dd HH:mm:ss"

#: ``SimpleDateFormat`` equivalent of :data:`JSON_DATE_TIME_PATTERN`. Using the Java
#: pattern directly in ``strftime`` silently yields the literal text "yyyy-MM-dd ...".
_STRFTIME_DATE_TIME = "%Y-%m-%d %H:%M:%S"

#: Java: ``@JsonFormat(pattern = "yyyy-MM-dd")``.
_STRFTIME_DATE = "%Y-%m-%d"

#: The zone the running application's ``ObjectMapper`` renders in. Spring Boot's
#: ``Jackson2ObjectMapperBuilder`` hands the mapper the JVM default zone, so a
#: ``@JsonFormat`` without an explicit ``timezone`` attribute inherits *that* -- not the
#: bare ``ObjectMapper`` default of UTC.
JACKSON_TIME_ZONE_NAME = "Asia/Shanghai"

#: Spring's ``DateTimeFormat`` falls back to this when ``serverTimezone`` is absent.
_DEFAULT_OFFSET = "+08:00"

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

_accepted_layouts = (
    # ``@JsonFormat`` round-trip format, then the two shapes Jackson's lenient
    # ``StdDateFormat`` accepts for the same logical value.
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
)


def _offset_to_tzinfo(offset: str) -> tzinfo:
    """Turn ``"+08:00"`` / ``"GMT+8"`` / ``"8"`` into a fixed-offset ``tzinfo``.

    A fixed offset (not ``ZoneInfo``) is deliberate: it needs no ``tzdata`` package --
    Windows Python ships no IANA database -- and China has observed no DST since 1991,
    so a fixed offset is exact for every timestamp this service can produce.
    """
    text = (offset or _DEFAULT_OFFSET).strip()
    if text.upper().startswith("GMT"):
        text = text[3:]
    elif text.upper().startswith("UTC"):
        text = text[3:]
    sign = 1
    if text.startswith(("+", "-")):
        if text[0] == "-":
            sign = -1
        text = text[1:]
    hours_text, _, minutes_text = text.partition(":")
    try:
        hours = int(hours_text or 0)
        minutes = int(minutes_text or 0)
    except ValueError:
        hours, minutes = 8, 0
        sign = 1
    return timezone(timedelta(hours=hours, minutes=minutes) * sign)


def jvm_timezone() -> tzinfo:
    """The JVM default zone, borrowed from the JDBC ``serverTimezone`` setting.

    Java's ``TimeZone.getDefault()`` is the platform zone; the JDBC URL pins the same
    value (``GMT+8``) because MySQL stores wall-clock ``datetime``. Reusing the configured
    offset keeps Python and Java agreeing on which instant a ``datetime`` column means.
    """
    from app.settings import get_settings  # local import: keeps this module dependency-free

    try:
        return _offset_to_tzinfo(get_settings().database_timezone)
    except Exception:  # noqa: BLE001 - config may not be loadable (e.g. unit tests)
        return _offset_to_tzinfo(_DEFAULT_OFFSET)


def json_format_timezone() -> tzinfo:
    """The zone Jackson renders ``@JsonFormat`` patterns in.

    The running application's ``ObjectMapper`` carries the **JVM zone**, so a pattern
    without an explicit ``timezone`` attribute renders the instant in ``+08:00``. Because
    the JDBC driver also *reads* ``datetime`` columns as ``+08:00``, the two conversions
    cancel and a stored wall clock is served back unchanged.

    Measured against the running ``ruoyi-admin.jar``: ``createTime`` in the database is
    ``2021-05-06 00:36:41`` and the response says ``"2021-05-06 00:36:41"``.

    This is the single place to change if the Java side ever pins
    ``spring.jackson.time-zone``: doing it here **without** the same change in Java would
    break parity, which is why it is a named function rather than an inline literal.
    """
    return jvm_timezone()


def format_date_time(value: Any) -> Optional[str]:
    """Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")`` -> ``"2021-05-06 00:36:41"``.

    The instant is rendered in :func:`json_format_timezone`, which equals the zone the
    driver used to read the wall clock, so a ``datetime`` column comes out unchanged.

    ``None`` stays ``None`` (Jackson emits ``null``); a ``str`` passes through so the
    helper is idempotent when a value has already been formatted.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            # A naive value is the wall clock JDBC would have read in the server zone.
            value = value.replace(tzinfo=jvm_timezone())
        return value.astimezone(json_format_timezone()).strftime(_STRFTIME_DATE_TIME)
    return str(value)


def format_date(value: Any) -> Optional[str]:
    """Java: ``@JsonFormat(pattern = "yyyy-MM-dd")`` on a ``java.util.Date``.

    -> ``"2025-11-13"``. A ``Date`` always carries a time component; the pattern simply
    does not print it, so a value stored as ``2025-11-13 22:38:28`` renders as
    ``"2025-11-13"``. Nothing is rounded and nothing is truncated in the database.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=jvm_timezone())
        return value.astimezone(json_format_timezone()).strftime(_STRFTIME_DATE)
    if isinstance(value, date):
        return value.strftime(_STRFTIME_DATE)
    return str(value)[:10]


def format_iso_date_time(value: Any) -> Optional[str]:
    """Java: a ``java.util.Date`` **without** ``@JsonFormat`` -> Jackson's ``StdDateFormat``.

    ``"2024-05-17T14:15:52.000+08:00"`` -- ``T`` separator, **always** three fraction
    digits and a colon-separated offset. Spring Boot disables
    ``WRITE_DATES_AS_TIMESTAMPS`` by default, so a plain ``Date`` property is written as
    text, not as epoch milliseconds. Call sites: ``SysUser.loginDate`` and the
    ``OdsProvcapture`` ``loadtime`` / ``tailcapturetime`` columns.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if not isinstance(value, datetime):
        raise TypeError(f"Expected datetime, got {type(value)!r}")
    if value.tzinfo is None:
        value = value.replace(tzinfo=jvm_timezone())
    value = value.astimezone(json_format_timezone())
    offset = value.utcoffset() or timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return "%s.%03d%s%02d:%02d" % (
        value.strftime("%Y-%m-%dT%H:%M:%S"),
        value.microsecond // 1000,
        sign,
        total_minutes // 60,
        total_minutes % 60,
    )


def to_epoch_millis(value: Any) -> Optional[int]:
    """Epoch milliseconds -- the shape of a Java ``Long`` that stores an instant.

    **Not** how a ``java.util.Date`` is serialized (that is :func:`format_iso_date_time`);
    it is used where Java declares a ``Long`` rather than a ``Date``:
    ``LoginUser.loginTime`` / ``expireTime``, ``MonitorOnline``'s ``loginTime`` and the
    ``CarQueryLog`` timestamps.

    Naive datetimes are interpreted in :func:`jvm_timezone`. Integer arithmetic is used
    instead of ``timestamp() * 1000`` because a float round-trip can land on ``...998``.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("bool is not a java.util.Date")
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        parsed = parse_date_time(value)
        if parsed is None:
            raise ValueError(f"Unparseable date: {value!r}")
        return to_epoch_millis(parsed)
    if not isinstance(value, datetime):
        raise TypeError(f"Expected datetime, got {type(value)!r}")

    if value.tzinfo is None:
        value = value.replace(tzinfo=jvm_timezone())
    delta = value.astimezone(timezone.utc) - _EPOCH
    return delta.days * 86_400_000 + delta.seconds * 1000 + delta.microseconds // 1000


def from_epoch_millis(millis: Optional[int]) -> Optional[datetime]:
    """Inverse of :func:`to_epoch_millis`: epoch millis -> **naive** wall clock in the JVM zone.

    Naive output matches what PyMySQL returns for a ``datetime`` column, so the result
    can be compared with (and written back to) database values without conversion.
    """
    if millis is None:
        return None
    moment = _EPOCH + timedelta(milliseconds=int(millis))
    return moment.astimezone(jvm_timezone()).replace(tzinfo=None)


def parse_date_time(value: Any) -> Optional[datetime]:
    """Parse the shapes Jackson accepts for a ``Date`` property.

    Covers ``"2025-10-23 05:25:09"`` (``@JsonFormat``, i.e. the JVM zone), ISO-8601 with
    or without a zone, ``"2025-10-23"``, and epoch milliseconds. Always returns a
    **naive** datetime expressed in the JVM/server zone -- the representation used
    throughout the entity layer and the one PyMySQL produces for a ``datetime`` column.

    Zone handling mirrors the Java round trip: ``@JsonFormat`` reads in
    :func:`json_format_timezone` (the JVM zone), so
    ``parse_date_time(format_date_time(x)) == x`` for any wall clock ``x``.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value
        return value.astimezone(jvm_timezone()).replace(tzinfo=None)
    if isinstance(value, bool):
        raise ValueError("bool is not a java.util.Date")
    if isinstance(value, (int, float)):
        return from_epoch_millis(int(value))
    if not isinstance(value, str):
        raise ValueError(f"Unparseable date: {value!r}")

    text = value.strip()
    if not text:
        return None
    if text.isdigit():  # Jackson also accepts a numeric timestamp written as a string
        return from_epoch_millis(int(text))

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is None:
        for layout in _accepted_layouts:
            try:
                parsed = datetime.strptime(text, layout)
                break
            except ValueError:
                continue
    if parsed is None:
        raise ValueError(f"Unparseable date: {value!r}")

    if parsed.tzinfo is None:
        # No offset in the text -> ``@JsonFormat`` would have read it in the Jackson zone.
        parsed = parsed.replace(tzinfo=json_format_timezone())
    return parsed.astimezone(jvm_timezone()).replace(tzinfo=None)


def to_jsonable(value: Any) -> Any:
    """Recursively convert domain models into plain JSON-ready structures.

    ``AjaxResult`` is a ``dict`` subclass, so any value placed inside it must already be a
    plain type by the time ``ORJSONResponse`` encodes it. This is the bridge: Pydantic
    models become dicts **with Java's camelCase aliases** and Java's serialization rules
    applied, while ``datetime`` and ``Decimal`` are left to the pydantic machinery.
    """
    from pydantic import BaseModel

    if isinstance(value, BaseModel):
        # ``by_alias`` is what renames user_id -> userId; ``mode="json"`` runs the
        # field serializers so dates become the exact Java shapes.
        return value.model_dump(by_alias=True, mode="json")
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [to_jsonable(item) for item in value]
    return value


def to_json_string(value: Any) -> str:
    """Java: ``com.alibaba.fastjson2.JSON.toJSONString(Object)``.

    FastJson2 writes **compact** JSON -- no space after ``:`` or ``,`` -- and does not escape
    non-ASCII characters (``ensure_ascii=False``). ``json.dumps`` defaults to ``", "`` /
    ``": "`` separators, so ``separators=(",", ":")`` is required for identical output.

    Needed by the code outside the MVC dispatch, which rebuilds exactly the Java pairing
    ``JSON.toJSONString(AjaxResult...)`` -> ``ServletUtils.renderString(response, json)``:
    the security handlers (:mod:`app.framework.security.handle`). Controllers do not need it --
    they return ``AjaxResult`` and ``ORJSONResponse`` serialises it.
    """
    return json.dumps(to_jsonable(value), ensure_ascii=False, separators=(",", ":"))


def to_json_string_without_null(value: Any) -> str:
    """Java: ``JSON.toJSONString(Object)`` **含默认的 null 省略**.

    fastjson2 默认不开 ``JSONWriter.Feature.WriteMapNullValue``，所以 ``toJSONString``
    输出的 JSON **不包含**值为 ``null`` 的属性。:func:`to_json_string` 走的是
    ``model_dump()``（保留 ``null``），两者的差别只在这一个 feature 上。

    调用点只有 ``CarQueryLog`` 的 ``queryCondition`` 字段：
    ``carQueryLogService.queryLog(JSON.toJSONString(entity), ...)`` —— 日志里存的是
    "客户端实际传了哪些条件"，带上 ``"plateColor":null`` 会让筛选条件看起来比实际更多。
    """
    plain = to_jsonable(value)
    if isinstance(plain, dict):
        plain = {key: item for key, item in plain.items() if item is not None}
    return json.dumps(plain, ensure_ascii=False, separators=(",", ":"))


__all__ = [
    "JACKSON_TIME_ZONE_NAME",
    "JSON_DATE_TIME_PATTERN",
    "format_date",
    "format_date_time",
    "format_iso_date_time",
    "from_epoch_millis",
    "json_format_timezone",
    "jvm_timezone",
    "parse_date_time",
    "to_epoch_millis",
    "to_jsonable",
    "to_json_string",
    "to_json_string_without_null",
]
