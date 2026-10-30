"""``base`` 包 ODS 实体用的日期 / 金额标量类型.

# Migrated from: (no Java source) -- mirrors the two Jackson behaviours the ODS entities rely on

Java 的 ``java.util.Date`` 有两种输出形态，取决于有没有 ``@JsonFormat``：

=========================================  ==============================================
Java 声明                                     JSON 形态
=========================================  ==============================================
``@JsonFormat(pattern = "yyyy-MM-dd")``      ``"2025-09-18"``（字符串，**日期被截断**）
``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``  ``"2025-09-18 16:30:59"``（墙上时间原样）
没有任何 ``@JsonFormat``                      ``"2025-09-18T16:30:59.000+08:00"``（ISO 字符串）
=========================================  ==============================================

"没写注解"这条不是 epoch 毫秒 —— Spring Boot 默认关闭了
``SerializationFeature.WRITE_DATES_AS_TIMESTAMPS``，``StdDateFormat`` 输出带毫秒和偏移
量的 ISO 文本。实测自运行中的 ``ruoyi-admin.jar``（``OdsRtSzdnSnapshotFlowProvcaptureAddcode``
的 ``loadtime`` / ``tailcapturetime`` 就没有注解）。

``BigDecimal`` 一律用 ``float``
-------------------------------
Java 的 ``BigDecimal`` 序列化成 JSON **数字**，并保留标度（``1234.50`` 带两个尾零）。
这里用 ``float`` 输出数字，尾零会被丢掉（``1234.5``）：值相同、类型相同，只有文本
长度不同，记在 ``COMPATIBILITY.md``。
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional

from pydantic import BeforeValidator, PlainSerializer

from app.common.utils.date_utils import parse_date_to_str
from app.common.utils.json_utils import format_iso_date_time, parse_date_time

#: ``SimpleDateFormat`` 的日期形态（``@Excel(dateFormat=...)`` 与 ``@JsonFormat`` 共用）。
YYYY_MM_DD = "yyyy-MM-dd"

#: 带时分秒的形态（``ZdataTrailTracks.enterTime`` 用的就是这个）。
YYYY_MM_DD_HH_MM_SS = "yyyy-MM-dd HH:mm:ss"


def _parse(value: Any) -> Optional[datetime]:
    """宽松解析（``DateUtils.parseDate`` 的语义：多格式尝试，失败返回 ``None``）。"""
    if value is None or value == "":
        return None
    return parse_date_time(value)


def _serialize_ymd(value: Optional[datetime]) -> Optional[str]:
    """``@JsonFormat(pattern = "yyyy-MM-dd")``。"""
    return parse_date_to_str(YYYY_MM_DD, value)


def _serialize_date_time(value: Optional[datetime]) -> Optional[str]:
    """``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``。"""
    return parse_date_to_str(YYYY_MM_DD_HH_MM_SS, value)


def _serialize_iso(value: Optional[datetime]) -> Optional[str]:
    """没有 ``@JsonFormat`` 的 ``Date``：Jackson ``StdDateFormat`` 的 ISO 文本。"""
    return format_iso_date_time(value)


#: Java: ``@JsonFormat(pattern = "yyyy-MM-dd") private Date x;``
OdsDate = Annotated[
    Optional[datetime],
    BeforeValidator(_parse),
    PlainSerializer(_serialize_ymd, when_used="json"),
]

#: Java: ``private Date x;``（**没有** ``@JsonFormat``）-> ``"2025-09-18T16:30:59.000+08:00"``。
#: 名字沿用历史（早先误以为是 epoch 毫秒），语义见 :func:`_serialize_iso`。
OdsEpochDate = Annotated[
    Optional[datetime],
    BeforeValidator(_parse),
    PlainSerializer(_serialize_iso, when_used="json"),
]

#: Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss") private Date x;``
OdsDateTime = Annotated[
    Optional[datetime],
    BeforeValidator(_parse),
    PlainSerializer(_serialize_date_time, when_used="json"),
]


__all__ = ["OdsDate", "OdsDateTime", "OdsEpochDate", "YYYY_MM_DD", "YYYY_MM_DD_HH_MM_SS"]
