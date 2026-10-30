"""错误信息处理类.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/ExceptionUtil.java

``getExceptionMessage`` 是**唯一**被业务代码调用的方法（``AbstractQuartzJob#after``），
用途是把异常写成多行堆栈存进 ``sys_job_log.exception_info``：Java 用
``StringWriter`` + ``printStackTrace``。

Python 的等价物是 :func:`traceback.format_exc` / ``traceback.TracebackException``，
输出同样是"首行 ``类名: 消息`` + 每个 frame 一行 + ``Caused by`` 链"的多行文本。

为什么用 ``TracebackException.format()`` 而不是 ``format_exc()``
--------------------------------------------------------------
``format_exc()`` 读的是**当前**正在处理的异常（``sys.exc_info()``）。``after()`` 在
``except`` 块里被调用，两者等价；但用 ``TracebackException`` 可以把 ``e`` 当参数传，
不依赖隐式状态 —— 行为一致，可读性更好。链式异常（``raise ... from ...``）由
``__cause__`` / ``__context__`` 自动展开，对应 Java 的 ``Caused by``。

``getRootErrorMessage`` 的等价物
--------------------------------
``ExceptionUtils.getRootCause(e)`` + ``getMessage()``。``_root_cause`` 沿
``__cause__`` / ``__context__`` 走到底，与 Commons-Lang 的
``getThrowableList`` 一致；没有根因时返回 ``"null"`` 字面量（Java 原文如此）。
"""

from __future__ import annotations

import traceback
from typing import Optional


def get_exception_message(e: BaseException) -> str:
    """Java: ``getExceptionMessage(Throwable e)`` —— 完整堆栈文本（多行）。"""
    return "".join(traceback.TracebackException.from_exception(e).format())


def get_root_error_message(e: Optional[BaseException]) -> str:
    """Java: ``getRootErrorMessage(Exception e)``."""
    root = _root_cause(e)
    if root is None:
        return ""
    message = str(root) if str(root) else None
    if message is None:
        return "null"
    return message


def _root_cause(e: Optional[BaseException]) -> Optional[BaseException]:
    """Java: ``ExceptionUtils.getRootCause`` —— 沿 ``getCause()`` 走到最深处。"""
    current = e
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        nested = current.__cause__ or current.__context__
        if nested is None:
            return current
        current = nested
    return current


__all__ = ["get_exception_message", "get_root_error_message"]
