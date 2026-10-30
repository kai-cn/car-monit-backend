"""序列生成类 / sequence generator.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/uuid/Seq.java

Java 原版
---------
``com.ruoyi.common.utils.uuid`` 包里有两个类：``IdUtils`` 与 ``Seq``。Python 侧
``IdUtils`` 落成 :mod:`app.common.utils.uuid_utils`（包被拍平），``Seq`` 独立成
本模块 —— 两者没有互相引用，拍平到一个文件反而看不清边界，因此保持两个模块。

输出格式
--------
``getId(type)`` = ``yyyyMMddHHmmss`` + 机器标识 ``"A"`` + 3 位左补零循环序列::

    20261026143001A001
    └── 14 位 ──┘ │└ 3 ┘
                 机器标识

Java 的注释写的是"默认16位序列号 yyMMddHHmmss"，**注释与代码不一致**（``yy`` 只有
2 位，实际用的是 14 位的 ``yyyyMMddHHmmss``，总长 18）。这里按**代码**实现，注释保持
原样留档，因为上传后的文件名会进 ``sys_user.avatar``，长度不能变。

循环语义（容易写错的地方）
--------------------------
``getSeq`` 是"先取值再 +1，若 **+1 之后** 的值 >= 10^length 则重置为 1"::

    第 1 次 -> value=1,   counter=2
    ...
    第 999 次 -> value=999, counter=1000 -> 重置为 1
    第 1000 次 -> value=1

也就是说序列是 **1..999**（999 个值），永远不会输出 ``000``，也永远不会输出 ``1000``。
按"value >= max 则归零"的直觉去写会错一位。

并发
----
Java 用 ``AtomicInteger`` + ``synchronized static``。Python 的 ``+=`` 不是原子的，
这里用模块级 :class:`threading.Lock` 复刻"同一时刻只有一个线程能取号"。
"""

from __future__ import annotations

import threading
from typing import Dict, Final

from app.common.utils.date_utils import date_time_now
from app.common.utils.string_utils import padl_number

#: 通用序列类型
COMM_SEQ_TYPE: Final[str] = "COMMON"
#: 上传序列类型
UPLOAD_SEQ_TYPE: Final[str] = "UPLOAD"
#: 机器标识
MACHINE_CODE: Final[str] = "A"

#: Java: ``private static AtomicInteger commSeq = new AtomicInteger(1)``
#: Java: ``private static AtomicInteger uploadSeq = new AtomicInteger(1)``
#: 两个计数器合并在一个 dict 里；键只有这两个，其它类型一律落到 ``COMMON``。
_COUNTERS: Dict[str, int] = {COMM_SEQ_TYPE: 1, UPLOAD_SEQ_TYPE: 1}
_LOCK = threading.Lock()


def get_id(seq_type: str = COMM_SEQ_TYPE, length: int = 3) -> str:
    """Java: ``Seq.getId()`` / ``Seq.getId(String type)`` / ``Seq.getId(AtomicInteger, int)``.

    三个重载在这里合成一个函数：Java 的 1 参重载只是 ``getId(commSeqType)`` 的转发，
    3 参重载的 ``AtomicInteger`` 形参在 Python 里没有对应物（计数器由模块私有），
    因此保留 ``seq_type`` + ``length`` 两个参数即可覆盖全部调用形态。

    本项目的调用点只有一个：``FileUploadUtils.extractFilename`` 用
    ``get_id(UPLOAD_SEQ_TYPE)`` 生成上传文件名。
    """
    return date_time_now() + MACHINE_CODE + _get_seq(seq_type, length)


def _get_seq(seq_type: str, length: int) -> str:
    """Java: ``private synchronized static String getSeq(AtomicInteger, int)``.

    注释里的"序列循环递增字符串[1, 10 的 (length)幂次方)"是准确的：上界开区间。
    """
    # Java: AtomicInteger atomicInt = commSeq; if (uploadSeqType.equals(type)) atomicInt = uploadSeq;
    key = UPLOAD_SEQ_TYPE if seq_type == UPLOAD_SEQ_TYPE else COMM_SEQ_TYPE
    with _LOCK:
        # 先取值再 +1
        value = _COUNTERS[key]
        _COUNTERS[key] = value + 1
        # 如果更新后值 >= 10 的 (length) 幂次方则重置为 1
        max_seq = 10 ** length
        if _COUNTERS[key] >= max_seq:
            _COUNTERS[key] = 1
    # 转字符串，用 0 左补齐
    return padl_number(value, length)


def reset_seq() -> None:
    """Test helper: 把两个计数器恢复成 Java 类初始化的状态（都是 1）。"""
    with _LOCK:
        _COUNTERS[COMM_SEQ_TYPE] = 1
        _COUNTERS[UPLOAD_SEQ_TYPE] = 1


__all__ = [
    "COMM_SEQ_TYPE",
    "UPLOAD_SEQ_TYPE",
    "MACHINE_CODE",
    "get_id",
    "reset_seq",
]
