"""Paged table payload.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableDataInfo.java

Java serializes the four fields in declaration order: ``total``, ``rows``, ``code``, ``msg``.
Jackson omits nothing (there are no ``@JsonInclude`` annotations), so ``code`` defaults
to ``0`` and ``msg`` to ``null`` when not set -- that quirk is preserved.
"""

from __future__ import annotations

from typing import Any, List, Optional


class TableDataInfo:
    """表格分页数据对象 / paged table data object."""

    def __init__(self, rows: Optional[List[Any]] = None, total: int = 0) -> None:
        # Java: private long total;  -> serialized first
        self.total: int = total
        # Java: private List<?> rows;  -> no initialiser, so null when unset
        self.rows: Optional[List[Any]] = rows
        # Java: private int code;    -> primitive default 0 when not set
        self.code: int = 0
        # Java: private String msg;  -> null when not set
        self.msg: Optional[str] = None

    # Java: TableDataInfo(List<?> list, int total)
    @classmethod
    def of(cls, rows: List[Any], total: int) -> "TableDataInfo":
        return cls(rows=rows, total=total)

    # ---- Java getters / setters (kept 1:1 so call sites translate literally) ----
    def get_total(self) -> int:
        return self.total

    def set_total(self, total: int) -> None:
        self.total = total

    def get_rows(self) -> Optional[List[Any]]:
        return self.rows

    def set_rows(self, rows: Optional[List[Any]]) -> None:
        self.rows = rows

    def get_code(self) -> int:
        return self.code

    def set_code(self, code: int) -> None:
        self.code = code

    def get_msg(self) -> Optional[str]:
        return self.msg

    def set_msg(self, msg: Optional[str]) -> None:
        self.msg = msg

    def to_dict(self) -> dict:
        """Serialize in the exact Java field order."""
        return {"total": self.total, "rows": self.rows, "code": self.code, "msg": self.msg}


def get_data_table(rows: Optional[List[Any]], total: Optional[int] = None) -> TableDataInfo:
    """Java: ``BaseController#getDataTable(List<?> list)``.

    Java 原实现::

        TableDataInfo rspData = new TableDataInfo();
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(list);
        rspData.setTotal(new PageInfo(list).getTotal());

    ``total`` 省略时按 ``new PageInfo(list).getTotal()`` 的规则取值：

    * ``list`` 是 :class:`app.common.core.page.page_helper.PageList`（PageHelper 的 ``Page``）
      -> 用它携带的 ``total``；
    * 普通列表 -> ``PageInfo`` 把 ``total`` 记成列表长度（未分页时的行为）。

    显式传入 ``total`` 仅在调用方已单独执行过 count 时使用（本项目未使用）。
    """
    from app.common.constant.http_status import HttpStatus

    if total is None:
        total = int(getattr(rows, "total", len(rows) if rows is not None else 0))

    response = TableDataInfo()
    response.set_code(HttpStatus.SUCCESS)
    response.set_msg("查询成功")
    response.set_rows(rows)
    response.set_total(total)
    return response

