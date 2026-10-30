"""Log formatting helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/LogUtils.java

Java's whole class is one static method. It exists because ``AsyncFactory`` builds log lines by
concatenating bracketed fields -- ``[ip][address][user][status][msg]`` -- and the brackets are
part of what log scrapers key on, so they are reproduced verbatim.
"""

from __future__ import annotations

from typing import Any


def get_block(msg: Any) -> str:
    """Java: ``LogUtils.getBlock(Object msg)``.

    ``null`` becomes the empty string, so a null field renders as ``[]`` rather than
    ``[null]`` -- the Java code assigns ``""`` before concatenating.
    """
    if msg is None:
        msg = ""
    return "[" + str(msg) + "]"


__all__ = ["get_block"]
