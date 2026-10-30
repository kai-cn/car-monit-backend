"""SQL-injection guards for dynamically built clauses.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/sql/SqlUtil.java

Java original
-------------
``escapeOrderBySql`` is called from every MyBatis mapper that accepts a client-supplied
``orderByColumn``. It allows only ``[a-zA-Z0-9_ ,.]`` and caps the length at 500 characters.

Important: MyBatis ``${}`` substitution is the only place these values reach SQL. In Python the
same rule applies -- **only** interpolate a value into a ``text()`` statement after it has passed
through :func:`escape_order_by_sql`. Everything else must use bind parameters.
"""

from __future__ import annotations

import re
from typing import Optional

from app.common.utils.string_utils import is_empty, is_not_empty, length, split

#: 定义常用的 sql关键字
SQL_REGEX = (
    "and |extractvalue|updatexml|exec |insert |select |delete |update |drop |count |chr |mid "
    "|master |truncate |char |declare |or |+|user()"
)

#: 仅支持字母、数字、下划线、空格、逗号、小数点（支持多个字段排序）
SQL_PATTERN = re.compile(r"[a-zA-Z0-9_ ,\.]+")

#: 限制orderBy最大长度
ORDER_BY_MAX_LENGTH = 500


class UtilException(RuntimeError):
    """Java: ``com.ruoyi.common.exception.UtilException`` -- a plain ``RuntimeException``."""


def escape_order_by_sql(value: Optional[str]) -> Optional[str]:
    """Java: ``SqlUtil.escapeOrderBySql(String)``.

    Returns ``value`` unchanged on success -- callers rely on ``None`` staying ``None`` so an
    absent ``orderByColumn`` keeps the mapper's default ordering.
    """
    if is_not_empty(value) and not is_valid_order_by_sql(value or ""):
        raise UtilException("参数不符合规范，不能进行查询")
    if length(value) > ORDER_BY_MAX_LENGTH:
        raise UtilException("参数已超过最大限制，不能进行查询")
    return value


def is_valid_order_by_sql(value: str) -> bool:
    """Java: ``SqlUtil.isValidOrderBySql(String)``."""
    return SQL_PATTERN.fullmatch(value) is not None


def filter_keyword(value: Optional[str]) -> None:
    """Java: ``SqlUtil.filterKeyword(String)`` -- raise when a keyword is present."""
    if is_empty(value):
        return
    assert value is not None
    for keyword in split(SQL_REGEX, "\\|") or []:
        if keyword.lower() in value.lower():
            raise UtilException("参数存在SQL注入风险")


__all__ = [
    "SQL_REGEX",
    "SQL_PATTERN",
    "ORDER_BY_MAX_LENGTH",
    "UtilException",
    "escape_order_by_sql",
    "is_valid_order_by_sql",
    "filter_keyword",
]
