"""Time unit enumeration.

Not a RuoYi file
----------------
``java.util.concurrent.TimeUnit`` is a JDK type. RuoYi passes it to
``RedisCache.setCacheObject(key, value, timeout, timeUnit)``
(``TokenService`` uses ``MINUTES``, ``SysPasswordService`` uses ``MINUTES``), so a Python
stand-in is needed to keep those call sites readable.

Only the conversions the project needs are implemented: :meth:`TimeUnit.to_seconds` and
:meth:`TimeUnit.to_millis`. Note that Java's ``toMillis`` **saturates** on overflow and
truncates to whole milliseconds; same here.
"""

from __future__ import annotations

from enum import Enum


class TimeUnit(Enum):
    """Java: ``java.util.concurrent.TimeUnit``."""

    NANOSECONDS = ("NANOSECONDS", 1, 1_000_000)
    MICROSECONDS = ("MICROSECONDS", 1_000, 1_000)
    MILLISECONDS = ("MILLISECONDS", 1_000_000, 1)
    SECONDS = ("SECONDS", 1_000_000_000, 1_000)
    MINUTES = ("MINUTES", 60_000_000_000, 60_000)
    HOURS = ("HOURS", 3_600_000_000_000, 3_600_000)
    DAYS = ("DAYS", 86_400_000_000_000, 86_400_000)

    def __init__(self, label: str, nanos_per_unit: int, millis_per_unit: int) -> None:
        self.label = label
        self.nanos_per_unit = nanos_per_unit
        self.millis_per_unit = millis_per_unit

    # Java: public long toMillis(long duration)
    def to_millis(self, duration: int) -> int:
        return duration * self.millis_per_unit

    # Java: public long toSeconds(long duration)
    def to_seconds(self, duration: int) -> int:
        return (duration * self.millis_per_unit) // 1000


__all__ = ["TimeUnit"]
