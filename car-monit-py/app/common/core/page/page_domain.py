"""分页数据.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/page/PageDomain.java

Java 原始字段

    private Integer pageNum;          // 当前页码
    private Integer pageSize;         // 每页显示记录数
    private String  orderByColumn;    // 排序列（前端传驼峰列名）
    private String  isAsc = "asc";    // 排序方向
    private Boolean reasonable = true;// 页码合理化

``getOrderBy()`` 是本类的核心：把前端传来的**驼峰列名**转换成**下划线列名**，
再拼上方向，例如 ``orderByColumn=createTime&isAsc=desc`` -> ``create_time desc``。
它只返回**列名和方向**，真正拼进 SQL 的时机由调用方掌握（见
:mod:`app.common.core.page.page_helper`），并且必须先过一次
:func:`app.common.utils.sql_utils.escape_order_by_sql`。

``setIsAsc`` 的兼容逻辑
----------------------
前端 Element-UI 的 ``sort-change`` 事件传的是 ``ascending`` / ``descending``，
所以 setter 里做了两次映射。注意它是**在 setter 里**完成的：直接给属性赋值
（``page_domain.is_asc = "ascending"``）**不会**触发映射，必须调用
:meth:`PageDomain.set_is_asc`。这一点与 Java 一致，不要"顺手"改成 property setter。
"""

from __future__ import annotations

from typing import Optional

from app.common.utils.string_utils import is_empty, is_not_empty, to_under_score_case


class PageDomain:
    """Java: ``PageDomain``."""

    # Java: private String isAsc = "asc";
    IS_ASC_DEFAULT = "asc"

    def __init__(
        self,
        page_num: Optional[int] = None,
        page_size: Optional[int] = None,
        order_by_column: Optional[str] = None,
        is_asc: Optional[str] = None,
        reasonable: Optional[bool] = None,
    ) -> None:
        self.page_num: Optional[int] = page_num
        self.page_size: Optional[int] = page_size
        self.order_by_column: Optional[str] = order_by_column
        # Java 字段初始化为 "asc"；只有 isAsc 非空时 setter 才会覆盖它。
        self.is_asc: str = self.IS_ASC_DEFAULT
        if is_asc is not None:
            self.set_is_asc(is_asc)
        self.reasonable: Optional[bool] = reasonable

    # Java: public String getOrderBy()
    def get_order_by(self) -> str:
        """``createTime`` + ``desc`` -> ``create_time desc``; empty column -> ``""``."""
        if is_empty(self.order_by_column):
            return ""
        return f"{to_under_score_case(self.order_by_column)} {self.is_asc}"

    # Java: public Integer getPageNum()
    def get_page_num(self) -> Optional[int]:
        return self.page_num

    # Java: public void setPageNum(Integer pageNum)
    def set_page_num(self, page_num: Optional[int]) -> None:
        self.page_num = page_num

    # Java: public Integer getPageSize()
    def get_page_size(self) -> Optional[int]:
        return self.page_size

    # Java: public void setPageSize(Integer pageSize)
    def set_page_size(self, page_size: Optional[int]) -> None:
        self.page_size = page_size

    # Java: public String getOrderByColumn()
    def get_order_by_column(self) -> Optional[str]:
        return self.order_by_column

    # Java: public void setOrderByColumn(String orderByColumn)
    def set_order_by_column(self, order_by_column: Optional[str]) -> None:
        self.order_by_column = order_by_column

    # Java: public String getIsAsc()
    def get_is_asc(self) -> str:
        return self.is_asc

    # Java: public void setIsAsc(String isAsc)
    def set_is_asc(self, is_asc: Optional[str]) -> None:
        """兼容前端排序类型：``ascending`` -> ``asc``，``descending`` -> ``desc``.

        Java 只在 ``isAsc`` 非空时赋值；空串 / ``None`` 会**保留**原来的 ``"asc"``。
        """
        if is_not_empty(is_asc):
            if is_asc == "ascending":
                is_asc = "asc"
            elif is_asc == "descending":
                is_asc = "desc"
            self.is_asc = is_asc  # type: ignore[assignment]

    # Java: public Boolean getReasonable()
    def get_reasonable(self) -> bool:
        """``null`` -> ``TRUE``（Java 的装箱 Boolean 可能为 null，这里收敛成 bool）。"""
        if self.reasonable is None:
            return True
        return self.reasonable

    # Java: public void setReasonable(Boolean reasonable)
    def set_reasonable(self, reasonable: Optional[bool]) -> None:
        self.reasonable = reasonable


__all__ = ["PageDomain"]
