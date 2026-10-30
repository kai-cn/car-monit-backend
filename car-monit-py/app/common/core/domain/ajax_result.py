"""Operation result envelope returned by every RuoYi controller.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/AjaxResult.java

Java original
-------------
``AjaxResult extends HashMap<String, Object>`` with keys ``code`` / ``msg`` / ``data``.
``data`` is omitted entirely when ``null`` (not serialized as ``"data": null``).

Python equivalent
-----------------
``AjaxResult`` subclasses :class:`dict`, so it serializes to exactly the same JSON
object. **键序不是插入序**：Java 侧 ``AjaxResult extends HashMap``，迭代序是桶号升序，
所以真实响应永远是 ``msg`` 在前、``code`` 其后（详见
:mod:`app.common.core.domain.java_hash_map`）。``put_chain`` 也按同一规则插入位置 ——
否则 ``login`` 的 ``token`` 会跑到 ``data`` 前面。

Method-overload mapping (Java overloads have no Python counterpart, so each arity
gets an explicit name -- this table is the authoritative reference):

    | Java                                        | Python                                                  |
    |---------------------------------------------|---------------------------------------------------------|
    | ``AjaxResult.success()``                     | ``AjaxResult.success()``                                |
    | ``AjaxResult.success(Object data)``          | ``AjaxResult.success_data(data)``                       |
    | ``AjaxResult.success(String msg)``           | ``AjaxResult.success_message(msg)``                     |
    | ``AjaxResult.success(String msg, Object d)`` | ``AjaxResult.success_message_data(msg, data)``          |
    | ``AjaxResult.warn(String msg)``              | ``AjaxResult.warn(msg)``                                |
    | ``AjaxResult.warn(String msg, Object data)`` | ``AjaxResult.warn_data(msg, data)``                     |
    | ``AjaxResult.error()``                       | ``AjaxResult.error()``                                  |
    | ``AjaxResult.error(String msg)``             | ``AjaxResult.error_message(msg)``                       |
    | ``AjaxResult.error(String msg, Object d)``   | ``AjaxResult.error_data(msg, data)``                    |
    | ``AjaxResult.error(int code, String msg)``   | ``AjaxResult.error_code(code, msg)``                    |
"""

from __future__ import annotations

from typing import Any, Optional

from app.common.constant.http_status import HttpStatus
from app.common.core.domain.java_hash_map import put_in_order

_UNSET = object()


class AjaxResult(dict):
    """操作消息提醒 / operation message envelope."""

    CODE_TAG = "code"
    MSG_TAG = "msg"
    DATA_TAG = "data"

    # Java: public AjaxResult()
    def __init__(self) -> None:
        super().__init__()

    # Java: public AjaxResult(int code, String msg)
    # Java: public AjaxResult(int code, String msg, Object data)
    @classmethod
    def _create(cls, code: int, msg: str, data: Any = _UNSET) -> "AjaxResult":
        result = cls()
        # Java: HashMap 的迭代序 —— msg(桶 0) -> code(桶 3) -> data(桶 4)
        put_in_order(result, cls.MSG_TAG, msg)
        put_in_order(result, cls.CODE_TAG, code)
        # Java: if (StringUtils.isNotNull(data)) { super.put(DATA_TAG, data); }
        if data is not _UNSET and data is not None:
            put_in_order(result, cls.DATA_TAG, data)
        return result

    # Java: AjaxResult.success()
    @classmethod
    def success(cls) -> "AjaxResult":
        return cls.success_message("操作成功")

    # Java: AjaxResult.success(Object data)
    @classmethod
    def success_data(cls, data: Any) -> "AjaxResult":
        return cls.success_message_data("操作成功", data)

    # Java: AjaxResult.success(String msg)
    @classmethod
    def success_message(cls, msg: str) -> "AjaxResult":
        return cls._create(HttpStatus.SUCCESS, msg)

    # Java: AjaxResult.success(String msg, Object data)
    @classmethod
    def success_message_data(cls, msg: str, data: Any) -> "AjaxResult":
        return cls._create(HttpStatus.SUCCESS, msg, data)

    # Java: AjaxResult.warn(String msg)
    @classmethod
    def warn(cls, msg: str) -> "AjaxResult":
        return cls._create(HttpStatus.WARN, msg)

    # Java: AjaxResult.warn(String msg, Object data)
    @classmethod
    def warn_data(cls, msg: str, data: Any) -> "AjaxResult":
        return cls._create(HttpStatus.WARN, msg, data)

    # Java: AjaxResult.error()
    @classmethod
    def error(cls) -> "AjaxResult":
        return cls.error_message("操作失败")

    # Java: AjaxResult.error(String msg)
    @classmethod
    def error_message(cls, msg: Optional[str]) -> "AjaxResult":
        """``msg`` 允许为 ``null`` —— Java 的 ``AjaxResult.error(e.getMessage())`` 在
        ``e.getMessage()`` 为 ``null`` 时（典型是 ``NullPointerException``）就是
        ``{"msg":null,"code":500}``。见 :func:`app.config.exception_handlers._java_message`.
        """
        return cls._create(HttpStatus.ERROR, msg)

    # Java: AjaxResult.error(String msg, Object data)
    @classmethod
    def error_data(cls, msg: str, data: Any) -> "AjaxResult":
        return cls._create(HttpStatus.ERROR, msg, data)

    # Java: AjaxResult.error(int code, String msg)
    @classmethod
    def error_code(cls, code: int, msg: str) -> "AjaxResult":
        return cls._create(code, msg)

    # Java: public boolean isSuccess()
    def is_success(self) -> bool:
        return self.get(self.CODE_TAG) == HttpStatus.SUCCESS

    # Java: public boolean isWarn()
    def is_warn(self) -> bool:
        return self.get(self.CODE_TAG) == HttpStatus.WARN

    # Java: public boolean isError()
    def is_error(self) -> bool:
        return self.get(self.CODE_TAG) == HttpStatus.ERROR

    # Java: @Override public AjaxResult put(String key, Object value)
    # Renamed: overriding ``put`` in Python is possible but breaks ``dict`` protocol
    # expectations; ``put_chain`` keeps the fluent style used by Java call sites.
    def put_chain(self, key: str, value: Any) -> "AjaxResult":
        # Java: ``super.put(key, value)`` —— 位置由 HashMap 的桶号决定，不是追加到末尾
        put_in_order(self, key, value)
        return self

    # Java: BaseController.toAjax(int rows)
    @classmethod
    def from_rows(cls, rows: int) -> "AjaxResult":
        return cls.success() if rows > 0 else cls.error()


def to_ajax(rows: int) -> AjaxResult:
    """模块 convenience mirror of ``BaseController.toAjax(int rows)``."""
    return AjaxResult.from_rows(rows)


__all__ = ["AjaxResult", "to_ajax", "HttpStatus", "Optional"]
