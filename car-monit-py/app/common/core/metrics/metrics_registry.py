# -*- coding: utf-8 -*-
"""进程内指标注册表（Java V3 新增）。

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/metrics/MetricsRegistry.java

【Java→Python 差异】
* Java ``ConcurrentHashMap<String, LongAdder>`` → Python ``dict[str, int]`` + ``threading.Lock``。
  GIL 下 ``dict`` 的单个 ``get/set`` 原子，但 ``get + set`` 复合操作不原子，故显式加锁。
* Java ``AtomicLong`` → Python ``int``（同样靠锁保护）。
* Java 返回 ``TreeMap``（按名称排序）→ Python ``dict(sorted(...))``，JSON 输出顺序一致。
* Java ``Collections.unmodifiableMap`` → Python 返回新 dict（调用方改不到内部状态）。
"""
from __future__ import annotations

import threading
from typing import Dict

_LOCK = threading.RLock()
_COUNTERS: Dict[str, int] = {}
_GAUGES: Dict[str, int] = {}


def increment(name: str) -> None:
    add(name, 1)


def add(name: str, delta: int) -> None:
    if not name or delta == 0:
        return
    with _LOCK:
        _COUNTERS[name] = _COUNTERS.get(name, 0) + delta


def set_gauge(name: str, value: int) -> None:
    if not name:
        return
    with _LOCK:
        _GAUGES[name] = value


def counter(name: str) -> int:
    with _LOCK:
        return _COUNTERS.get(name, 0)


def gauge(name: str) -> int:
    with _LOCK:
        return _GAUGES.get(name, 0)


def counters() -> Dict[str, int]:
    with _LOCK:
        return dict(sorted(_COUNTERS.items()))


def gauges() -> Dict[str, int]:
    with _LOCK:
        return dict(sorted(_GAUGES.items()))


def reset() -> None:
    """Java 无此方法；仅供测试隔离使用。"""
    with _LOCK:
        _COUNTERS.clear()
        _GAUGES.clear()
