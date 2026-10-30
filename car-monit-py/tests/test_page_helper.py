"""分页基础设施 —— ``PageDomain`` / ``TableSupport`` / ``PageHelper`` / ``PageInfo``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-common/.../core/page/PageDomain.java
#   ruoyi-common/.../core/page/TableSupport.java
#   ruoyi-common/.../core/page/TableDataInfo.java
#   ruoyi-common/.../utils/PageUtils.java
#   + com.github.pagehelper.PageHelper / PageInfo

为什么这些细节值得钉死
----------------------
分页是**隐式信道**：``startPage()`` 写 ThreadLocal，Mapper 里看不到任何分页参数。因此
"一次 startPage 只作用于紧接着的第一条 select" 这条规则只能靠测试保证 —— 写错成
"读后不清空"时，同一请求里第二条未分页的查询会被悄悄截断成 10 条，而且不会有任何报错。

第二个易错点是 ``reasonable``：它把越界页码拉回边界，前端在最后一页删光数据后不会看到空白页。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from app.common.core.page import page_helper
from app.common.core.page.page_domain import PageDomain
from app.common.core.page.page_helper import (
    PageList,
    build_page_request,
    clear_page,
    convert_to_bool,
    convert_to_int,
    page_scope,
    select_page,
    start_page,
    take_page,
)
from app.common.core.page.table_data_info import TableDataInfo, get_data_table
from app.common.utils.sql_utils import UtilException


# --------------------------------------------------------------------------- fakes


class _QueryParams(dict):
    """``request.query_params`` stand-in: ``.get`` plus ``.multi_items``."""

    def multi_items(self) -> List[tuple]:
        return list(self.items())


class _FakeRequest:
    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.query_params = _QueryParams(params or {})


class _Result:
    """One ``CursorResult``-shaped answer."""

    def __init__(self, rows: List[Any], scalar_value: Any = None) -> None:
        self._rows = rows
        self._scalar = scalar_value

    def all(self) -> List[Any]:
        return list(self._rows)

    def scalar(self) -> Any:
        return self._scalar


class _RecordingSession:
    """Records every statement, answers from a queue of prepared results."""

    def __init__(self, results: List[_Result]) -> None:
        self._results = list(results)
        self.statements: List[str] = []
        self.params: List[Dict[str, Any]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> _Result:
        self.statements.append(str(statement))
        self.params.append(dict(params or {}))
        if not self._results:
            raise AssertionError(f"unexpected extra statement: {statement}")
        return self._results.pop(0)


#: 模块导入时的原函数。收集阶段在任何用例之前，所以这里一定是干净的。
#: ``use_query`` 会直接改写模块属性，必须靠它还原（否则泄漏到整个 session）。
_ORIGINAL_GET_REQUEST = page_helper.get_request


@pytest.fixture(autouse=True)
def _clear_page_state(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java: the interceptor's ``finally`` block -- never leak a page between tests.

    同时把 ``page_helper.get_request`` 恢复回去：``use_query`` 直接改了模块属性，
    不还原的话后面所有用例的 ``start_page()`` 都会读到这里的假请求（``pageNum=2``），
    而 ``ContextVar`` 是跨用例共享的。
    """
    clear_page()
    monkeypatch.setattr(page_helper, "get_request", _ORIGINAL_GET_REQUEST)
    yield
    clear_page()
    monkeypatch.undo()


def use_query(**params: Any) -> None:
    """Point ``build_page_request`` at a synthetic query string."""
    request = _FakeRequest(params)
    page_helper.get_request = lambda: request  # type: ignore[assignment]


# --------------------------------------------------------------------------- PageDomain


class TestPageDomain:
    """Java: ``PageDomain``."""

    def test_order_by_converts_camel_to_underscore(self) -> None:
        page = PageDomain(order_by_column="createTime", is_asc="desc")
        assert page.get_order_by() == "create_time desc"

    def test_is_asc_defaults_to_asc_and_only_assigns_when_not_empty(self) -> None:
        assert PageDomain().get_order_by() == ""
        assert PageDomain(order_by_column="userId").get_order_by() == "user_id asc"
        # Java: setIsAsc("") 保留原来的 "asc"; 直接赋值不触发映射
        page = PageDomain(order_by_column="userId", is_asc="")
        assert page.get_is_asc() == "asc"

    def test_set_is_asc_maps_element_ui_vocabulary(self) -> None:
        page = PageDomain()
        page.set_is_asc("ascending")
        assert page.get_is_asc() == "asc"
        page.set_is_asc("descending")
        assert page.get_is_asc() == "desc"
        # 未知取值原样保留 —— Java 只映射这两个词
        page.set_is_asc("DESC")
        assert page.get_is_asc() == "DESC"

    def test_empty_order_by_column_produces_an_empty_string(self) -> None:
        assert PageDomain(order_by_column="").get_order_by() == ""
        assert PageDomain(order_by_column=None).get_order_by() == ""

    def test_reasonable_defaults_to_true_when_unset(self) -> None:
        """Java: ``private Boolean reasonable = true;`` -- ``null`` 也走 true 分支。"""
        assert PageDomain().get_reasonable() is True
        assert PageDomain(reasonable=None).get_reasonable() is True
        assert PageDomain(reasonable=False).get_reasonable() is False


# --------------------------------------------------------------------------- TableSupport


class TestBuildPageRequest:
    """Java: ``TableSupport.buildPageRequest()`` + ``Convert.toInt/toBool``."""

    def test_defaults_match_java(self) -> None:
        use_query()
        page = build_page_request()
        assert page.get_page_num() == 1
        assert page.get_page_size() == 10
        assert page.get_order_by_column() is None
        assert page.get_reasonable() is True

    def test_reads_the_five_parameter_names(self) -> None:
        use_query(pageNum="3", pageSize="25", orderByColumn="userName", isAsc="descending", reasonable="false")
        page = build_page_request()
        assert page.get_page_num() == 3
        assert page.get_page_size() == 25
        assert page.get_order_by() == "user_name desc"
        assert page.get_reasonable() is False

    def test_non_numeric_falls_back_to_the_default(self) -> None:
        """Java: ``Convert.toInt("abc", 1)`` -> 1, **not** an exception."""
        use_query(pageNum="abc", pageSize="")
        page = build_page_request()
        assert page.get_page_num() == 1
        assert page.get_page_size() == 10

    def test_convert_helpers(self) -> None:
        assert convert_to_int(None, 7) == 7
        assert convert_to_int(" 5 ", 7) == 5
        assert convert_to_int("5.9", 7) == 7
        assert convert_to_bool("TRUE", None) is True
        assert convert_to_bool("0", None) is False
        assert convert_to_bool("maybe", None) is None
        assert convert_to_bool(None, False) is False

    def test_without_a_request_context_everything_is_default(self) -> None:
        page_helper.get_request = lambda: None  # type: ignore[assignment]
        page = build_page_request()
        assert (page.get_page_num(), page.get_page_size()) == (1, 10)


# --------------------------------------------------------------------------- PageHelper


class TestStartPageLifecycle:
    """Java: ``PageHelper.startPage`` -> interceptor -> ``ThreadLocal`` 清理."""

    def test_take_page_reads_and_clears(self) -> None:
        use_query(pageNum="2", pageSize="5")
        start_page()
        first = take_page()
        assert first is not None and first.get_page_num() == 2
        # 第二次取不到 —— 一次 startPage 只作用于紧随其后的一条 select
        assert take_page() is None

    def test_clear_page_drops_a_pending_page(self) -> None:
        use_query(pageNum="2")
        start_page()
        clear_page()
        assert take_page() is None

    def test_page_scope_clears_on_exit(self) -> None:
        use_query(pageNum="2")
        with page_scope():
            start_page()
        assert take_page() is None


# --------------------------------------------------------------------------- select_page


class TestSelectPage:
    """Java: PageHelper 的 count-then-LIMIT 改写."""

    def test_no_page_runs_one_statement_and_totals_by_length(self) -> None:
        session = _RecordingSession([_Result([("a",), ("b",)])])
        result = select_page(session, "select count(0) from t", "select * from t", {}, None)
        assert isinstance(result, PageList)
        assert list(result) == [("a",), ("b",)]
        assert result.total == 2
        assert session.statements == ["select * from t"]

    def test_counts_first_then_applies_limit(self) -> None:
        session = _RecordingSession([_Result([], scalar_value=42), _Result([("a",)])])
        page = PageDomain(page_num=3, page_size=10, reasonable=True)
        result = select_page(session, "select count(0) from t", "select * from t", {}, page)
        assert session.statements[0] == "select count(0) from t"
        # PageHelper 生成的是 ``LIMIT offset, size``（MySQL 方言）
        assert session.statements[1] == "select * from t LIMIT 20, 10"
        assert result.total == 42
        assert result.pages == 5

    def test_reasonable_clamps_a_page_past_the_end(self) -> None:
        session = _RecordingSession([_Result([], scalar_value=12), _Result([])])
        page = PageDomain(page_num=99, page_size=10, reasonable=True)
        select_page(session, "select count(0) from t", "select * from t", {}, page)
        assert session.statements[1].endswith("LIMIT 10, 10")

    def test_unreasonable_keeps_the_out_of_range_page(self) -> None:
        session = _RecordingSession([_Result([], scalar_value=12), _Result([])])
        page = PageDomain(page_num=99, page_size=10, reasonable=False)
        select_page(session, "select count(0) from t", "select * from t", {}, page)
        assert session.statements[1].endswith("LIMIT 980, 10")

    def test_page_num_below_one_is_clamped_even_when_unreasonable(self) -> None:
        """PageHelper: ``pageNum < 1`` 一律回到第 1 页（offset 不能为负）。"""
        session = _RecordingSession([_Result([], scalar_value=5), _Result([])])
        page = PageDomain(page_num=0, page_size=10, reasonable=False)
        select_page(session, "select count(0) from t", "select * from t", {}, page)
        assert session.statements[1].endswith("LIMIT 0, 10")

    def test_empty_table_still_returns_an_empty_page_list(self) -> None:
        session = _RecordingSession([_Result([], scalar_value=0), _Result([])])
        page = PageDomain(page_num=2, page_size=10, reasonable=True)
        result = select_page(session, "select count(0) from t", "select * from t", {}, page)
        assert list(result) == []
        assert result.total == 0
        assert result.pages == 0

    def test_page_size_zero_means_no_paging_but_still_counts(self) -> None:
        session = _RecordingSession([_Result([("a",)]), _Result([], scalar_value=99)])
        page = PageDomain(page_num=1, page_size=0)
        result = select_page(session, "select count(0) from t", "select * from t", {}, page)
        assert "LIMIT" not in session.statements[0]
        assert result.total == 99

    def test_order_by_is_appended_with_the_escape_guard(self) -> None:
        # count 必须 > 0：PageHelper 在 count 为 0 时**不执行** data 语句，
        # 那几个用例验的是 data 语句被改写的样子，所以不能拿空表来测。
        session = _RecordingSession([_Result([], scalar_value=7), _Result([])])
        page = PageDomain(page_num=1, page_size=10, order_by_column="userName", is_asc="desc")
        select_page(session, "select count(0) from t", "select * from t", {}, page)
        assert session.statements[1] == "select * from t ORDER BY user_name desc LIMIT 0, 10"

    def test_order_by_is_not_duplicated_when_the_statement_has_one(self) -> None:
        """``selectRoleList`` 自带 ``order by r.role_sort``；再追加会造出两个 ORDER BY。"""
        session = _RecordingSession([_Result([], scalar_value=7), _Result([])])
        page = PageDomain(page_num=1, page_size=10, order_by_column="roleSort")
        select_page(session, "select count(0) from t", "select * from t order by r.role_sort", {}, page)
        assert session.statements[1].count("order by") == 1

    def test_an_illegal_order_by_is_rejected(self) -> None:
        session = _RecordingSession([_Result([], scalar_value=7), _Result([])])
        page = PageDomain(page_num=1, page_size=10, order_by_column="userName;drop table sys_user")
        with pytest.raises(UtilException):
            select_page(session, "select count(0) from t", "select * from t", {}, page)

    def test_params_are_passed_to_both_statements(self) -> None:
        session = _RecordingSession([_Result([], scalar_value=7), _Result([])])
        page = PageDomain(page_num=1, page_size=10)
        select_page(session, "select count(0) from t where a = :a", "select * from t where a = :a", {"a": 1}, page)
        assert session.params == [{"a": 1}, {"a": 1}]


# --------------------------------------------------------------------------- PageInfo


class TestGetDataTable:
    """Java: ``BaseController.getDataTable`` + ``new PageInfo(list).getTotal()``."""

    def test_page_list_supplies_the_total(self) -> None:
        rows = PageList([1, 2], total=57)
        table = get_data_table(rows)
        assert (table.total, table.rows, table.code, table.msg) == (57, [1, 2], 200, "查询成功")

    def test_a_plain_list_totals_by_length(self) -> None:
        table = get_data_table([1, 2, 3])
        assert table.total == 3

    def test_none_rows_totals_zero(self) -> None:
        table = get_data_table(None)
        assert table.total == 0
        assert table.rows is None

    def test_serialisation_order_matches_the_java_field_order(self) -> None:
        table: TableDataInfo = get_data_table([], 0)
        assert list(table.to_dict()) == ["total", "rows", "code", "msg"]
