"""分页拦截器（PageHelper 的等价实现）.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/PageUtils.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableSupport.java
# Migrated from: com.github.pagehelper.PageHelper (mybatis 分页插件)

Java 是怎么做的
---------------
``BaseController.startPage()`` 把 ``pageNum`` / ``pageSize`` / ``orderBy`` 塞进
PageHelper 的 **ThreadLocal**，随后 ``SysUserServiceImpl.selectUserList`` 里那句
``userMapper.selectUserList(user)`` 被 MyBatis 拦截器改写：

1. 先跑一遍 ``count`` 语句（``PageHelper#count``）；
2. 再把 ``LIMIT ?, ?`` 拼到原 SQL 末尾；
3. 返回的 ``List`` 其实是 ``com.github.pagehelper.Page``（``ArrayList`` 子类），
   额外携带 ``total`` / ``pageNum`` / ``pageSize`` / ``pages``；
4. ``BaseController.getDataTable(list)`` 用 ``new PageInfo(list).getTotal()`` 取出总数。

因此 **Service / Mapper 的签名里根本看不到分页参数**，分页是"隐式"的。

Python 是怎么做的
-----------------
用同样的隐式信道，只是把 ThreadLocal 换成 ``ContextVar``：

* :func:`start_page`     -- ``PageUtils.startPage()``：读取当前请求参数并写入 ``_PAGE``；
* :func:`take_page`      -- 拦截器：**取出并清空** ``_PAGE``，所以一次 ``startPage()``
  只对紧随其后的第一条 select 生效（与 PageHelper 完全一致）；
* :func:`select_page`    -- 先 count 再 ``LIMIT``，返回 :class:`PageList`。

Mapper 方法保持 Java 的签名（例如 ``select_user_list(user)``），分页在其内部完成。

``reasonable`` 的语义
--------------------
``reasonable=true``（Ruoyi 默认）时 PageHelper 会纠正越界页码：

* ``pageNum < 1``  -> 取第 1 页；
* ``pageNum > pages`` -> 取最后一页（``total == 0`` 时仍返回空列表）。

这解释了为什么前端在最后一页删掉全部数据后不会看到空白页——页码被自动回退。
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence

from sqlalchemy import text

from app.common.core.context.request_context import get_request
from app.common.core.page.page_domain import PageDomain
from app.common.utils.sql_utils import escape_order_by_sql

logger = logging.getLogger("app.common.core.page.page_helper")

#: Java: PageHelper 的 ThreadLocal（``LOCAL_PAGE``）。
_PAGE: ContextVar[Optional[PageDomain]] = ContextVar("page_helper_page", default=None)

#: Java: ``TableSupport.PAGE_NUM`` 等四个参数名。
PAGE_NUM = "pageNum"
PAGE_SIZE = "pageSize"
ORDER_BY_COLUMN = "orderByColumn"
IS_ASC = "isAsc"
REASONABLE = "reasonable"

#: Java: ``TableSupport.getPageDomain()`` 的默认值（``Convert.toInt(param, 1)`` / ``10``）。
DEFAULT_PAGE_NUM = 1
DEFAULT_PAGE_SIZE = 10

_TRUE_WORDS = frozenset({"true", "ok", "yes", "1"})
_FALSE_WORDS = frozenset({"false", "no", "0"})


def convert_to_int(value: Any, default_value: int) -> int:
    """Java: ``Convert.toInt(Object, Integer)`` -- 空白或非法数字都退回默认值."""
    if value is None:
        return default_value
    raw = str(value).strip()
    if raw == "":
        return default_value
    try:
        return int(raw)
    except ValueError:
        return default_value


def convert_to_bool(value: Any, default_value: Optional[bool] = None) -> Optional[bool]:
    """Java: ``Convert.toBool(Object, Boolean)``."""
    if value is None:
        return default_value
    raw = str(value).strip().lower()
    if raw == "":
        return default_value
    if raw in _TRUE_WORDS:
        return True
    if raw in _FALSE_WORDS:
        return False
    return default_value


def build_page_request() -> PageDomain:
    """Java: ``TableSupport.buildPageRequest()`` -- 从 query string 组装 ``PageDomain``.

    请求参数名与 Java 完全一致：``pageNum`` / ``pageSize`` / ``orderByColumn`` /
    ``isAsc`` / ``reasonable``。没有请求上下文（启动任务、定时任务、单元测试）时
    等同于"所有参数都缺省"，即第 1 页、每页 10 条。
    """
    request = get_request()
    params: Mapping[str, str] = request.query_params if request is not None else {}

    return PageDomain(
        page_num=convert_to_int(params.get(PAGE_NUM), DEFAULT_PAGE_NUM),
        page_size=convert_to_int(params.get(PAGE_SIZE), DEFAULT_PAGE_SIZE),
        order_by_column=params.get(ORDER_BY_COLUMN),
        is_asc=params.get(IS_ASC),
        reasonable=convert_to_bool(params.get(REASONABLE), None),
    )


def start_page() -> None:
    """Java: ``BaseController.startPage()`` -> ``PageUtils.startPage()``.

    只**记录**分页请求，不发 SQL；真正生效点在 :func:`take_page`。
    """
    _PAGE.set(build_page_request())


def take_page() -> Optional[PageDomain]:
    """PageHelper 拦截器：取出本次查询的分页参数，并立即清空。

    清空是刻意的：``startPage()`` 之后若执行了多条 select，只有第一条被分页，
    与 PageHelper 的行为一致。
    """
    page = _PAGE.get()
    if page is not None:
        _PAGE.set(None)
    return page


def clear_page() -> None:
    """Java: ``PageUtils.clearPage()`` -- 丢弃尚未消费的分页参数."""
    _PAGE.set(None)


@contextmanager
def page_scope() -> Iterator[None]:
    """测试辅助：退出时保证 ``_PAGE`` 不残留（Java 里由拦截器 ``finally`` 保证）."""
    try:
        yield
    finally:
        clear_page()


class PageList(List[Any]):
    """Java: ``com.github.pagehelper.Page<E> extends ArrayList<E>``.

    Service / Mapper 的返回类型仍然是"列表"，但多带了四个只读属性，
    由 :func:`get_data_table` 读取。注意它**不是** ``list`` 的替代品：
    ``isinstance(rows, list)`` 为真，序列化出来也仍是数组。
    """

    def __init__(
        self,
        items: Optional[Sequence[Any]] = None,
        total: int = 0,
        page_num: int = 1,
        page_size: int = 10,
    ) -> None:
        super().__init__(items or [])
        self.total: int = total
        self.page_num: int = page_num
        self.page_size: int = page_size
        self.pages: int = _pages_of(total, page_size)


def _pages_of(total: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return (total + page_size - 1) // page_size


def _has_order_by(statement: str) -> bool:
    return "order by" in " ".join(statement.split()).lower()


#: 本工程所有 Mapper 生成的 count 语句形状：``select count(0) from (<data_sql>) table_count``。
_COUNT_PREFIX = "select count(0) from ("
_COUNT_SUFFIX = ") table_count"

#: 引号字符：单引号、双引号、反引号。扫描时要整体跳过，否则 ``'order by'`` 会被误判。
_QUOTES = frozenset("'\"`")


def _top_level_tokens(statement: str) -> List[tuple]:
    """返回**括号深度为 0** 的单词及其起始下标 ``[(word, index), ...]``。

    跳过所有引号字面量，并跟踪 ``(`` / ``)`` 深度 —— 子查询里的关键字不属于本层，
    PageHelper 的 ``CountSqlParser`` 同样只处理最外层的 ``order by``。
    """
    tokens: List[tuple] = []
    depth = 0
    index = 0
    length = len(statement)
    while index < length:
        char = statement[index]
        if char in _QUOTES:
            closing = char
            index += 1
            while index < length:
                if statement[index] == "\\":
                    index += 2
                    continue
                if statement[index] == closing:
                    index += 1
                    break
                index += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and (char.isalpha() or char == "_"):
            end = index
            while end < length and (statement[end].isalnum() or statement[end] == "_"):
                end += 1
            tokens.append((statement[index:end].lower(), index))
            index = end
            continue
        index += 1
    return tokens


def strip_order_by(statement: str) -> str:
    """删掉语句**最外层**结尾处的 ``order by`` 子句。Java: ``CountSqlParser#removeOrderBy``.

    这不是"排序对总数没意义"的优化，而是可观察行为：``order by`` 允许引用**不在投影里**
    的列，一旦被套进 ``select count(0) from (...)`` 的派生表，MySQL 就会报
    ``Unknown column 't.big_id' in 'order clause'``；而 PageHelper 在生成 count 语句前
    已经把 ``order by`` 摘掉了，所以 Java 的 SQL 日志里只有
    ``SELECT count(0) FROM ods_szdn_toll_station_ip t WHERE 1 = 1``，接口正常返回
    ``{"total":0,"rows":[]}``。

    带 ``limit`` 的语句**不动**：那时 ``order by`` 决定行序，属于语义的一部分
    （PageHelper 对 ``limit`` 语句同样保留排序，改走派生表包装）。
    """
    tokens = _top_level_tokens(statement)
    order_at: Optional[int] = None
    for position, (word, index) in enumerate(tokens):
        if word == "order" and position + 1 < len(tokens) and tokens[position + 1][0] == "by":
            order_at = index
            break
    if order_at is None:
        return statement
    for word, index in tokens:
        if index > order_at and word in ("limit", "offset"):
            return statement
    return statement[:order_at].rstrip().rstrip(";").rstrip()


def normalise_count_sql(count_sql: str) -> str:
    """把 Mapper 拼好的 count 语句整理成 PageHelper 真正发给 MySQL 的样子.

    两种形状都处理：
    * ``select count(0) from (<data_sql>) table_count`` —— 脱掉外壳，对**内层**去
      ``order by``，再套回去；
    * 任意普通语句 —— 直接对最外层去 ``order by``。
    """
    stripped = count_sql.strip()
    lowered = stripped.lower()
    if lowered.startswith(_COUNT_PREFIX) and lowered.endswith(_COUNT_SUFFIX):
        head_length = len(_COUNT_PREFIX)
        inner = stripped[head_length:len(stripped) - len(_COUNT_SUFFIX)]
        return _COUNT_PREFIX + strip_order_by(inner) + _COUNT_SUFFIX
    return strip_order_by(stripped)


def select_page(
    session: Any,
    count_sql: str,
    data_sql: str,
    params: Mapping[str, Any],
    page: Optional[PageDomain],
) -> PageList:
    """执行"count + LIMIT"两步查询并返回 :class:`PageList`.

    ``page is None`` 时退化成一次普通查询（``total = len(rows)``），这正是
    PageHelper 在没有 ``startPage()`` 时的行为。

    参数
    ----
    count_sql
        统计总数的语句。MyBatis 由 ``pagehelper.params=count=countSql`` 生成，
        这里由调用方直接给出（例如 ``select count(1) from (...) t`` 形式）。
    data_sql
        **不含** ``LIMIT`` 的原语句。
    params
        绑定参数；count 与 data 共用同一份。
    page
        分页参数。

    关于 ``orderBy``
    ----------------
    PageHelper 会把 ``orderBy`` 追加到语句末尾。这里额外做了一条保护：
    若原语句**已经**带 ``order by``（例如 ``selectRoleList`` 的
    ``order by r.role_sort``），则不再追加，避免出现两个 ``ORDER BY``
    （MySQL 会直接报语法错误）。
    """
    if page is None:
        rows = session.execute(text(data_sql), dict(params)).all()
        return PageList(rows, total=len(rows))

    page_num = convert_to_int(page.get_page_num(), DEFAULT_PAGE_NUM)
    page_size = convert_to_int(page.get_page_size(), DEFAULT_PAGE_SIZE)
    # Java: CountSqlParser 在发 SQL 之前改写 count 语句（去掉最外层 order by）。
    count_sql = normalise_count_sql(count_sql)
    # PageHelper: pageSize 为 0 时表示"不分页"（count 仍然执行，total 照返回）。
    if page_size <= 0:
        rows = session.execute(text(data_sql), dict(params)).all()
        total = session.execute(text(count_sql), dict(params)).scalar() or 0
        return PageList(rows, total=int(total), page_num=page_num, page_size=page_size)

    total = int(session.execute(text(count_sql), dict(params)).scalar() or 0)
    pages = _pages_of(total, page_size)

    # Java: PageInterceptor#intercept -> ``if (count > 0) { ...查询... } else { 返回空列表 }``
    # total 为 0 时 PageHelper **根本不执行** data 语句，直接给一个空 Page。这不是优化
    # 细节而是可观察行为：``/base/tollStationIp/list`` 的 ``order by t.big_id`` 引用了
    # 一个不存在的列，Java 照样返回 ``{"total":0,"rows":[]}``（SQL 日志里只有 COUNT），
    # 而先跑 data 语句的实现会 500。
    if total <= 0:
        return PageList([], total=0, page_num=page_num, page_size=page_size)

    if page.get_reasonable():
        if page_num < 1:
            page_num = 1
        if pages > 0 and page_num > pages:
            page_num = pages

    order_by = escape_order_by_sql(page.get_order_by())
    statement = data_sql
    if order_by:
        if _has_order_by(statement):
            logger.debug("[分页] 语句已自带 order by，忽略请求排序: %s", order_by)
        else:
            statement = f"{statement.rstrip().rstrip(';')} ORDER BY {order_by}"

    # Java: ``Page#calculateStartAndEndRow()``
    #   ``startRow = pageNum > 0 ? (pageNum - 1) * pageSize : 0``
    # 注意 ``pageNum <= 0`` 时是 **归零**，而不是取负数：所以 ``reasonable=false``
    # 虽然不会把页码纠正成 1，`LIMIT` 的起点仍然是 0（见 PageHelper 单测）。
    offset = (page_num - 1) * page_size if page_num > 0 else 0
    # MySQL 方言：PageHelper 生成的是 ``LIMIT ?, ?``（offset, size）。
    statement = f"{statement.rstrip().rstrip(';')} LIMIT {int(offset)}, {int(page_size)}"

    rows = session.execute(text(statement), dict(params)).all()
    return PageList(rows, total=total, page_num=page_num, page_size=page_size)


__all__ = [
    "PAGE_NUM",
    "PAGE_SIZE",
    "ORDER_BY_COLUMN",
    "IS_ASC",
    "REASONABLE",
    "DEFAULT_PAGE_NUM",
    "DEFAULT_PAGE_SIZE",
    "PageList",
    "build_page_request",
    "start_page",
    "take_page",
    "clear_page",
    "page_scope",
    "select_page",
    "convert_to_int",
    "convert_to_bool",
    "strip_order_by",
    "normalise_count_sql",
]
