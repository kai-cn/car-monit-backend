"""Twitter Snowflake 主键生成器.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/SnowflakeIdWorker.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/config/IdWorkerConfig.java

位布局（与 Java 完全一致，**不能**改）
------------------------------------
::

    0 - 0000000000 0000000000 0000000000 0000000000 0 - 00000 - 00000 - 000000000000
    |   41 位时间戳（毫秒差值）                          |  5 位  |  5 位  |  12 位序列  |
   符号位                                              数据中心  机器号

* 起始时间戳 ``twepoch = 1420041600000L``（2015-01-01）；
* ``timestamp`` 是"当前毫秒 - twepoch"，所以生成出来的 id 是 41+22 位以内的正数，
  也就是 18~19 位十进制数 —— ``sys_file.id`` 是 ``bigint``，客户端看到的是
  ``@JsonSerialize(using = ToStringSerializer.class)`` 之后的**字符串**；
* 同一毫秒内序列 +1，溢出（4096）就阻塞到下一毫秒。

与原版唯一的不同：``synchronized`` 换成 :class:`threading.Lock`
---------------------------------------------------------------
Java 的 ``public synchronized long nextId()`` 锁的是**实例**，Spring 单例 => 进程内
全局串行。Python 侧用一把模块级锁复刻同样的语义（单例见 :func:`get_id_worker`）。

**这个 id 与数据库自增没有任何关系**：``SysFileServiceImpl.saveSysFile`` 在插入前
手工赋值，XML 里的 ``useGeneratedKeys`` 只对"没赋值"的情况起作用 —— 而本模块的
调用点全部赋了值。
"""

from __future__ import annotations

import threading
import time
from typing import Optional

#: Java: ``private final long twepoch = 1420041600000L`` —— 2015-01-01 00:00:00 UTC+8
TWEPOCH: int = 1420041600000

#: Java: ``workerIdBits`` / ``datacenterIdBits`` / ``sequenceBits``
WORKER_ID_BITS: int = 5
DATACENTER_ID_BITS: int = 5
SEQUENCE_BITS: int = 12

#: Java: ``maxWorkerId = -1L ^ (-1L << workerIdBits)`` = 31
MAX_WORKER_ID: int = -1 ^ (-1 << WORKER_ID_BITS)
#: Java: ``maxDatacenterId = -1L ^ (-1L << datacenterIdBits)`` = 31
MAX_DATACENTER_ID: int = -1 ^ (-1 << DATACENTER_ID_BITS)

#: Java: ``sequenceMask = -1L ^ (-1L << sequenceBits)`` = 4095
SEQUENCE_MASK: int = -1 ^ (-1 << SEQUENCE_BITS)

#: Java: ``workerIdShift = sequenceBits``
WORKER_ID_SHIFT: int = SEQUENCE_BITS
#: Java: ``datacenterIdShift = sequenceBits + workerIdBits``
DATACENTER_ID_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS
#: Java: ``timestampLeftShift = sequenceBits + workerIdBits + datacenterIdBits``
TIMESTAMP_LEFT_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS


class SnowflakeIdWorker:
    """Java: ``class SnowflakeIdWorker``."""

    def __init__(self, worker_id: int, datacenter_id: int) -> None:
        # Java 的构造器用两段 if 抛 IllegalArgumentException，文案带占位符替换结果。
        if worker_id > MAX_WORKER_ID or worker_id < 0:
            raise ValueError(
                f"worker Id can't be greater than {MAX_WORKER_ID} or less than 0"
            )
        if datacenter_id > MAX_DATACENTER_ID or datacenter_id < 0:
            raise ValueError(
                f"datacenter Id can't be greater than {MAX_DATACENTER_ID} or less than 0"
            )
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        #: Java: ``private long sequence = 0L``
        self.sequence = 0
        #: Java: ``private long lastTimestamp = -1L``
        self.last_timestamp = -1
        self._lock = threading.Lock()

    # Java: public synchronized long nextId()
    def next_id(self) -> int:
        """获得下一个 ID（线程安全）。"""
        with self._lock:
            timestamp = self._time_gen()

            # 时钟回拨：Java 抛 RuntimeException（**不是** IllegalStateException）
            if timestamp < self.last_timestamp:
                raise RuntimeError(
                    "Clock moved backwards.  Refusing to generate id for "
                    f"{self.last_timestamp - timestamp} milliseconds"
                )

            if self.last_timestamp == timestamp:
                self.sequence = (self.sequence + 1) & SEQUENCE_MASK
                if self.sequence == 0:
                    timestamp = self._til_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return (
                ((timestamp - TWEPOCH) << TIMESTAMP_LEFT_SHIFT)
                | (self.datacenter_id << DATACENTER_ID_SHIFT)
                | (self.worker_id << WORKER_ID_SHIFT)
                | self.sequence
            )

    # Java: protected long tilNextMillis(long lastTimestamp)
    def _til_next_millis(self, last_timestamp: int) -> int:
        timestamp = self._time_gen()
        while timestamp <= last_timestamp:
            timestamp = self._time_gen()
        return timestamp

    # Java: protected long timeGen()
    def _time_gen(self) -> int:
        """Java: ``System.currentTimeMillis()``."""
        return int(time.time() * 1000)


#: Java: ``@Bean public SnowflakeIdWorker snowflakeIdWorker() { return new SnowflakeIdWorker(0, 0); }``
_WORKER: Optional[SnowflakeIdWorker] = None


def get_id_worker() -> SnowflakeIdWorker:
    """``IdWorkerConfig`` 的那个单例（``workerId = 0``, ``datacenterId = 0``）。

    Spring 的 ``@Bean`` 默认单例，所以进程内共用一个实例 —— 这点很关键：
    ``sequence`` / ``lastTimestamp`` 是实例状态，多实例会让同一毫秒出现重复序列。
    """
    global _WORKER
    if _WORKER is None:
        _WORKER = SnowflakeIdWorker(0, 0)
    return _WORKER


def next_id() -> int:
    """便捷函数：``get_id_worker().next_id()``。"""
    return get_id_worker().next_id()


def reset_id_worker() -> None:
    """Test helper: 丢掉单例，下一次调用重新 ``new SnowflakeIdWorker(0, 0)``。"""
    global _WORKER
    _WORKER = None


__all__ = [
    "TWEPOCH",
    "MAX_WORKER_ID",
    "MAX_DATACENTER_ID",
    "SEQUENCE_MASK",
    "SnowflakeIdWorker",
    "get_id_worker",
    "next_id",
    "reset_id_worker",
]
