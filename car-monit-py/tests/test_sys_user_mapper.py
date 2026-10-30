"""``SysUserMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUserMapper.java

为什么 Mapper 层要单独测
-----------------------
Service 层的假 Mapper 把 SQL 全遮住了。``selectUserList`` 有 18 个 ``<if>``，其中一个
（``${params.dataScope}``）在本项目里是**被注释掉的**，另有两个
（``flag == 'sjzbDept'`` / ``'sjzbDeptCg'``）会拼出带 ``exists`` 子查询的大段条件。
这些片段的顺序、连接词大小写、``like concat('%', ?, '%')`` 的写法都会出现在慢查询日志里，
改错了不会有任何报错 —— 只会悄悄换一个结果集。所以这里直接对**拼出来的 SQL** 断言。

第二个易错点是结果映射。``selectUserVo`` 一个用户三个角色返回**三行**，靠 ``resultMap``
的 ``<id>`` + ``<collection>`` 合并；``selectUserList`` 则**根本不 select 角色列**，
``roles`` 必须是空表。两者共用 ``SysUser``，很容易写串。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.page.page_domain import PageDomain
from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.mapper import sys_user_mapper
from app.system.mapper.sys_user_mapper import (
    _SELECT_USER_LIST,
    _USER_LIST_COLUMNS,
    SysUserMapper,
)

# --------------------------------------------------------------------------- fakes


class _Result:
    """One ``CursorResult``-shaped answer."""

    def __init__(
        self,
        rows: Optional[Sequence[Any]] = None,
        keys: Optional[Sequence[str]] = None,
        scalar_value: Any = None,
        rowcount: int = 0,
        lastrowid: Optional[int] = None,
    ) -> None:
        self._rows = list(rows or [])
        self._keys = list(keys or [])
        self._scalar = scalar_value
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def keys(self) -> List[str]:
        return list(self._keys)

    def all(self) -> List[Any]:
        return list(self._rows)

    def scalar(self) -> Any:
        return self._scalar


class _RecordingSession:
    def __init__(self, results: List[_Result]) -> None:
        self._results = list(results)
        self.statements: List[str] = []
        self.params: List[Dict[str, Any]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> _Result:
        self.statements.append(" ".join(str(statement).split()))
        self.params.append(dict(params or {}))
        if not self._results:
            raise AssertionError(f"unexpected extra statement: {statement}")
        return self._results.pop(0)


class _SessionScope:
    def __init__(self, session: _RecordingSession) -> None:
        self._session = session

    def __enter__(self) -> _RecordingSession:
        return self._session

    def __exit__(self, *_exc: Any) -> bool:
        return False


class _SessionFactory:
    """Stands in for ``app.config.database.session_scope``."""

    def __init__(self, *results: _Result) -> None:
        self._results = list(results)
        self.sessions: List[_RecordingSession] = []

    def __call__(self) -> _SessionScope:
        session = _RecordingSession(self._results)
        self.sessions.append(session)
        return _SessionScope(session)

    @property
    def statements(self) -> List[str]:
        return [statement for session in self.sessions for statement in session.statements]


@pytest.fixture(autouse=True)
def _clear_page_state() -> Any:
    clear_page()
    yield
    clear_page()


# --------------------------------------------------------------------------- row builders

#: ``selectUserVo`` 的列标签，顺序与 XML 一致。
#: ``d.dept_id`` 与 ``u.dept_id`` 同名，SQLAlchemy 的 ``RowMapping`` 会给第二列加 ``_1``
#: 后缀 —— 这正是 Java 侧 ``<association>`` 能拿到 ``u.dept_id``（第一个）的原因。
_USER_VO_KEYS: Sequence[str] = (
    "user_id",
    "user_no",
    "dept_id",
    "user_name",
    "nick_name",
    "email",
    "avatar",
    "phonenumber",
    "password",
    "sex",
    "status",
    "del_flag",
    "login_ip",
    "login_date",
    "create_by",
    "create_time",
    "remark",
    "user_type",
    "cert_entity_id",
    "cert_id",
    "buss_id",
    "buss_name",
    "eps_name",
    "tenant_id",
    "sub_code",
    "dept_id_1",
    "parent_id",
    "dept_name",
    "order_num",
    "leader",
    "dept_status",
    "role_id",
    "role_name",
    "role_key",
    "role_sort",
    "data_scope",
    "role_status",
)


def _vo_row(**overrides: Any) -> tuple:
    values = {key: None for key in _USER_VO_KEYS}
    values.update(overrides)
    return tuple(values[key] for key in _USER_VO_KEYS)


def _list_row(**overrides: Any) -> tuple:
    values = {key: None for key in _USER_LIST_COLUMNS}
    values.update(overrides)
    return tuple(values[key] for key in _USER_LIST_COLUMNS)


def use_session(monkeypatch: pytest.MonkeyPatch, *results: _Result) -> _SessionFactory:
    factory = _SessionFactory(*results)
    monkeypatch.setattr(sys_user_mapper, "session_scope", factory)
    return factory


# --------------------------------------------------------------------------- selectUserVo


class TestSelectUserVo:
    """``selectUserByUserName`` / ``selectUserById`` / ``selectUserByCertEntityID``."""

    def test_the_statement_is_the_shared_vo_fragment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rows=[], keys=_USER_VO_KEYS))

        SysUserMapper().select_user_by_user_name("ry")

        statement = factory.statements[0]
        assert "from sys_user u" in statement
        assert "left join sys_user_role ur on u.user_id = ur.user_id" in statement
        assert "where u.user_name = :user_name" in statement
        # ``ifnull(u.buss_id, u.user_name)`` 是业务规则，不是排版
        assert "ifnull(u.buss_id, u.user_name) buss_id" in statement

    def test_the_user_and_the_department_are_mapped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(
            monkeypatch,
            _Result(
                rows=[
                    _vo_row(
                        user_id=2,
                        dept_id=105,
                        user_name="ry",
                        nick_name="若依",
                        user_type="1",
                        tenant_id=100,
                        sub_code="SUB",
                        parent_id=100,
                        dept_name="研发部门",
                        order_num="1",
                        leader="若依",
                        dept_status="0",
                        role_id=2,
                        role_name="普通角色",
                        role_key="common",
                        role_sort="2",
                        data_scope="2",
                        role_status="0",
                    )
                ],
                keys=_USER_VO_KEYS,
            ),
        )

        user = SysUserMapper().select_user_by_user_name("ry")

        assert user is not None
        assert (user.user_id, user.user_name, user.user_type) == (2, "ry", "1")
        assert user.dept is not None
        assert (user.dept.dept_id, user.dept.dept_name) == (105, "研发部门")
        assert (user.dept.parent_id, user.dept.order_num) == (100, "1")
        assert (user.dept.leader, user.dept.status) == ("若依", "0")
        assert user.tenant_id == 100
        assert user.sub_code == "SUB"
        assert [role.role_key for role in user.roles or []] == ["common"]

    def test_three_rows_collapse_into_one_user_with_three_roles(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java: ``<collection>`` keyed on ``role_id`` -- not a new user per row."""
        use_session(
            monkeypatch,
            _Result(
                rows=[
                    _vo_row(user_id=2, user_name="ry", role_id=1, role_key="admin"),
                    _vo_row(user_id=2, user_name="ry", role_id=2, role_key="common"),
                    _vo_row(user_id=2, user_name="ry", role_id=3, role_key="auditor"),
                ],
                keys=_USER_VO_KEYS,
            ),
        )

        user = SysUserMapper().select_user_by_user_name("ry")

        assert user is not None
        assert [role.role_id for role in user.roles or []] == [1, 2, 3]

    def test_a_repeated_role_id_is_not_duplicated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(
            monkeypatch,
            _Result(
                rows=[
                    _vo_row(user_id=2, role_id=2, role_key="common"),
                    _vo_row(user_id=2, role_id=2, role_key="common"),
                ],
                keys=_USER_VO_KEYS,
            ),
        )

        user = SysUserMapper().select_user_by_user_name("ry")

        assert user is not None
        assert len(user.roles or []) == 1

    def test_a_null_role_id_leaves_the_role_list_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ``left join`` miss produces one row with all role columns null."""
        use_session(monkeypatch, _Result(rows=[_vo_row(user_id=9)], keys=_USER_VO_KEYS))

        user = SysUserMapper().select_user_by_user_name("nobody")

        assert user is not None
        assert user.roles == []

    def test_a_null_dept_id_leaves_dept_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(rows=[_vo_row(user_id=9)], keys=_USER_VO_KEYS))

        user = SysUserMapper().select_user_by_user_name("nobody")

        assert user is not None
        assert user.dept is None

    def test_no_row_means_none_not_an_empty_user(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(rows=[], keys=_USER_VO_KEYS))

        assert SysUserMapper().select_user_by_user_name("ghost") is None

    def test_the_first_dept_id_column_wins(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDBC resolves a duplicate label to the **first** column: ``u.dept_id``."""
        use_session(
            monkeypatch,
            _Result(rows=[_vo_row(user_id=2, dept_id=7, dept_id_1=999, dept_name="D")], keys=_USER_VO_KEYS),
        )

        user = SysUserMapper().select_user_by_user_name("ry")

        assert user is not None
        assert user.dept_id == 7
        assert user.dept is not None and user.dept.dept_id == 7

    def test_select_by_cert_entity_id_filters_on_the_cert_column(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rows=[], keys=_USER_VO_KEYS))

        assert SysUserMapper().select_user_by_cert_entity_id("CERT-1") is None
        assert factory.statements[0].endswith("where u.cert_entity_id = :cert_entity_id")
        assert factory.sessions[0].params[0] == {"cert_entity_id": "CERT-1"}

    def test_select_by_id_filters_on_user_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(
            monkeypatch, _Result(rows=[_vo_row(user_id=5)], keys=_USER_VO_KEYS)
        )

        user = SysUserMapper().select_user_by_id(5)

        assert user is not None and user.user_id == 5
        assert factory.statements[0].endswith("where u.user_id = :user_id")


# --------------------------------------------------------------------------- selectUserList


class TestSelectUserListConditions:
    """``selectUserList`` 的 18 个 ``<if>``，逐条钉死。"""

    def _statement(self, monkeypatch: pytest.MonkeyPatch, user: SysUser) -> str:
        factory = use_session(
            monkeypatch, _Result(rows=[], keys=_USER_LIST_COLUMNS), _Result(scalar_value=0)
        )
        SysUserMapper().select_user_list(user)
        # 第一次 execute 是 count（select_page 先数总数），第二次才是数据语句。
        return factory.statements[-1]

    def _params(self, monkeypatch: pytest.MonkeyPatch, user: SysUser) -> Dict[str, Any]:
        factory = use_session(
            monkeypatch, _Result(rows=[], keys=_USER_LIST_COLUMNS), _Result(scalar_value=0)
        )
        SysUserMapper().select_user_list(user)
        return factory.sessions[-1].params[-1]

    def test_only_the_soft_delete_filter_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(monkeypatch, SysUser())

        assert statement.count("where u.del_flag = '0'") == 1
        assert "order by" not in statement.lower()

    def test_the_two_dept_joins_are_present(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``d2`` 是"上级单位"，与 ``d`` 不是同一个 join。"""
        statement = self._statement(monkeypatch, SysUser())

        assert "left join sys_dept d on u.dept_id = d.dept_id" in statement
        assert "left join sys_dept d2 on d.tenant_id = d2.dept_id" in statement
        assert "d2.dept_name tenant_name" in statement

    def test_user_id_and_user_no_are_equals(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(monkeypatch, SysUser(user_id=3, user_no=9))

        assert "AND u.user_id = :user_id" in statement
        assert "AND u.user_no = :user_no" in statement

    def test_user_name_and_phonenumber_are_like(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(
            monkeypatch, SysUser(user_name="ry", phonenumber="158")
        )

        assert "AND u.user_name like concat('%', :user_name, '%')" in statement
        assert "AND u.phonenumber like concat('%', :phonenumber, '%')" in statement

    def test_status_is_an_equals(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert "AND u.status = :status" in self._statement(
            monkeypatch, SysUser(status="0")
        )

    def test_the_date_range_uses_date_format_on_both_sides(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """逐字保留 ``date_format(...,'%y%m%d')``：这是索引失效的元凶，但也是现状。"""
        statement = self._statement(
            monkeypatch, SysUser(params={"beginTime": "2024-01-01", "endTime": "2024-12-31"})
        )

        assert (
            "AND date_format(u.create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')"
            in statement
        )
        assert (
            "AND date_format(u.create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')"
            in statement
        )

    def test_dept_id_expands_to_its_children(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(monkeypatch, SysUser(dept_id=105))

        assert "AND (u.dept_id = :dept_id OR u.dept_id IN ( SELECT t.dept_id FROM sys_dept t" in statement
        assert "WHERE find_in_set(:dept_id, ancestors) ))" in statement

    def test_dept_id_zero_means_every_department(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java: ``deptId != null and deptId != 0`` -- 0 是"不限"的哨兵值。"""
        assert "u.dept_id = :dept_id" not in self._statement(
            monkeypatch, SysUser(dept_id=0)
        )

    def test_the_business_identifier_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(
            monkeypatch,
            SysUser(
                user_type="1",
                cert_entity_id="CERT",
                cert_id="SN",
                buss_id="B1",
                buss_name="机构",
                eps_name="公司",
            ),
        )

        assert "AND u.user_type = :user_type" in statement
        assert "AND u.cert_entity_id = :cert_entity_id" in statement
        assert "AND u.cert_id = :cert_id" in statement
        assert "AND u.buss_id = :buss_id" in statement
        assert "AND u.buss_name like concat('%', :buss_name, '%')" in statement
        assert "AND u.eps_name like concat('%', :eps_name, '%')" in statement

    def test_tenant_id_only_checks_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java: ``<if test="tenantId != null ">`` -- 空串也照拼。"""
        assert "AND d.tenant_id = :tenant_id" in self._statement(
            monkeypatch, SysUser(tenant_id=100)
        )
        statement = self._statement(monkeypatch, SysUser(tenant_id=0))
        assert "AND d.tenant_id = :tenant_id" in statement

    def test_role_code_becomes_an_exists_subquery(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(monkeypatch, SysUser(role_code="cgjl_manager"))

        assert "AND EXISTS (select 1 from sys_user_role t1,sys_role t2" in statement
        assert "t2.role_key = :role_code )" in statement

    def test_sjzb_dept_joins_the_tenant_department_tree(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(
            monkeypatch, SysUser(flag="sjzbDept", data_id="100")
        )

        assert "AND exists ( select 1 from sys_dept tb,sys_dept tb1" in statement
        # XML 里 ``tb.del_flag = '0'`` 写了两遍，原文如此
        assert "tb.del_flag = '0' and tb.del_flag = '0'" in statement
        assert "and tb1.dept_id = d.tenant_id )" in statement
        # 纯 sjzbDept 不带采购经理过滤
        assert "cgjl_manager" not in statement

    def test_sjzb_dept_cg_adds_the_procurement_manager_exists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(
            monkeypatch, SysUser(flag="sjzbDeptCg", data_id="100")
        )

        assert "sys_dept tb,sys_dept tb1" in statement
        assert "r.role_key = 'cgjl_manager'" in statement

    def test_my_dept_cg_only_filters_by_role(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(monkeypatch, SysUser(flag="myDeptCg"))

        assert "r.role_key = 'cgjl_manager'" in statement
        assert "sys_dept tb,sys_dept tb1" not in statement

    def test_an_unknown_flag_adds_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(monkeypatch, SysUser(flag="allDept"))

        assert "cgjl_manager" not in statement
        assert "sys_dept tb" not in statement

    def test_query_nick_name_uses_an_upper_case_like(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """大小写与其它条件不同（``LIKE`` / ``CONCAT``），原文如此。"""
        statement = self._statement(monkeypatch, SysUser(query_nick_name="若"))

        assert "AND u.nick_name LIKE CONCAT('%', :query_nick_name, '%')" in statement

    def test_exclude_id_is_a_not_equal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert "AND u.user_id != :exclude_id" in self._statement(
            monkeypatch, SysUser(exclude_id=2)
        )

    def test_the_commented_out_data_scope_never_reaches_the_sql(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """XML 里 ``<!-- 数据范围过滤${params.dataScope} -->`` 是注释。

        切面往 ``params["dataScope"]`` 写了片段也没用 —— 这里证明它确实没进 SQL。
        """
        statement = self._statement(
            monkeypatch, SysUser(params={"dataScope": " AND (d.dept_id = 100)"})
        )

        assert "dataScope" not in statement
        assert "d.dept_id = 100" not in statement

    def test_the_conditions_keep_the_xml_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._statement(
            monkeypatch,
            SysUser(
                user_id=2,
                user_name="ry",
                status="0",
                user_type="1",
                buss_id="B1",
                exclude_id=9,
            ),
        )

        positions = [
            statement.index("AND u.user_id = :user_id"),
            statement.index("AND u.user_name like"),
            statement.index("AND u.status = :status"),
            statement.index("AND u.user_type = :user_type"),
            statement.index("AND u.buss_id = :buss_id"),
            statement.index("AND u.user_id != :exclude_id"),
        ]
        assert positions == sorted(positions)


class TestSelectUserListMapping:
    """``selectUserList`` 的行映射与 ``selectUserVo`` 不同。"""

    def test_rows_map_without_roles_and_with_a_three_column_dept(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(
            monkeypatch,
            _Result(
                rows=[
                    _list_row(
                        user_id=2,
                        user_name="ry",
                        dept_id=105,
                        dept_name="研发部门",
                        leader="若依",
                        tenant_id=100,
                        tenant_name="总公司",
                        image_id="IMG-1",
                    )
                ],
                keys=_USER_LIST_COLUMNS,
            ),
            _Result(scalar_value=1),
        )

        rows = SysUserMapper().select_user_list(SysUser())

        assert len(rows) == 1
        user = rows[0]
        assert user.user_id == 2
        assert user.roles == []
        assert user.tenant_name == "总公司"
        assert user.image_id == "IMG-1"
        # 扁平的 ``deptName`` **不**填：``SysUserResult`` 有 ``<association>``，MyBatis 的
        # ``autoMappingBehavior=PARTIAL`` 遇到嵌套映射会整体关掉自动映射，于是 ``dept_name``
        # 只进 ``dept.deptName``。实测 Java 的 ``/system/user/list`` 也是 ``"deptName": null``。
        assert user.dept_name is None
        assert user.dept is not None
        assert (user.dept.dept_id, user.dept.dept_name, user.dept.leader) == (105, "研发部门", "若依")
        # 这三个列没被 select，所以是 null
        assert user.dept.parent_id is None
        assert user.dept.order_num is None
        assert user.dept.status is None

    def test_a_missing_department_leaves_dept_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(
            monkeypatch,
            _Result(rows=[_list_row(user_id=2, tenant_id=-1)], keys=_USER_LIST_COLUMNS),
            _Result(scalar_value=1),
        )

        rows = SysUserMapper().select_user_list(SysUser())

        assert rows[0].dept is None
        # ifnull(d.tenant_id, -1) 落到 -1，前端靠它判"无租户"
        assert rows[0].tenant_id == -1

    def test_the_projection_matches_the_column_list(self) -> None:
        """``_USER_LIST_COLUMNS`` 必须与 ``_SELECT_USER_LIST`` 的 select 列同序同数。"""
        assert len(_USER_LIST_COLUMNS) == 28
        assert _USER_LIST_COLUMNS[0] == "user_id"
        assert _USER_LIST_COLUMNS[-1] == "image_id"
        # 投影里唯一的两个"别名"列
        assert "tenant_name" in _USER_LIST_COLUMNS
        assert "tenant_id" in _USER_LIST_COLUMNS


class TestSelectUserListPagination:
    """PageHelper 的隐式分页：``startPage()`` 之后的第一条 select 被改写。"""

    def test_without_start_page_there_is_no_count_and_no_limit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(
            monkeypatch, _Result(rows=[_list_row(user_id=2)], keys=_USER_LIST_COLUMNS)
        )

        rows = SysUserMapper().select_user_list(SysUser())

        assert len(factory.statements) == 1
        assert "LIMIT" not in factory.statements[0]
        assert isinstance(rows, PageList)
        assert rows.total == 1

    def test_start_page_adds_a_count_then_a_limit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            sys_user_mapper,
            "take_page",
            lambda: PageDomain(page_num=2, page_size=10, reasonable=False),
        )
        factory = use_session(
            monkeypatch,
            _Result(scalar_value=25),
            _Result(rows=[_list_row(user_id=12)], keys=_USER_LIST_COLUMNS),
        )

        rows = SysUserMapper().select_user_list(SysUser())

        assert factory.statements[0].startswith("select count(0) from (")
        assert factory.statements[1].endswith("LIMIT 10, 10")
        assert rows.total == 25
        assert rows.page_num == 2
        assert rows.pages == 3

    def test_the_second_call_is_no_longer_paged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``take_page()`` 读后即清 —— 与 PageHelper 的拦截器一致。"""
        factory = use_session(
            monkeypatch,
            _Result(scalar_value=1),
            _Result(rows=[_list_row(user_id=2)], keys=_USER_LIST_COLUMNS),
            _Result(rows=[_list_row(user_id=2)], keys=_USER_LIST_COLUMNS),
        )
        start_page()

        SysUserMapper().select_user_list(SysUser())
        SysUserMapper().select_user_list(SysUser())

        assert len(factory.statements) == 3
        assert "LIMIT" not in factory.statements[2]


# --------------------------------------------------------------------------- insertUser


class TestInsertUser:
    def _sql_and_params(
        self, monkeypatch: pytest.MonkeyPatch, user: SysUser, lastrowid: int = 42
    ) -> Any:
        factory = use_session(monkeypatch, _Result(rowcount=1, lastrowid=lastrowid))
        SysUserMapper().insert_user(user)
        return factory.statements[0], factory.sessions[0].params[0]

    def test_only_non_null_columns_are_listed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sql, params = self._sql_and_params(
            monkeypatch,
            SysUser(user_name="ry", nick_name="若依", user_type="1", create_by="admin"),
        )

        assert sql.startswith("insert into sys_user (")
        assert "user_name" in sql
        assert "nick_name" in sql
        assert "create_by" in sql
        # 没有赋值的列不该出现
        assert "dept_id" not in sql
        assert "password" not in sql
        assert params == {
            "user_name": "ry",
            "nick_name": "若依",
            "user_type": "1",
            "create_by": "admin",
        }

    def test_an_empty_string_is_skipped_for_required_text_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<if test="userName != null and userName != ''">``."""
        sql, _ = self._sql_and_params(monkeypatch, SysUser(user_name="", nick_name=""))

        assert "user_name" not in sql
        assert "nick_name" not in sql

    def test_an_empty_password_is_still_inserted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<if test="password != null ">`` -- 只判 null，空串照写。"""
        sql, params = self._sql_and_params(
            monkeypatch, SysUser(user_name="ry", password="")
        )

        assert "password" in sql
        assert params["password"] == ""

    def test_the_generated_key_is_written_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java: ``useGeneratedKeys="true" keyProperty="userId"``."""
        user = SysUser(user_name="ry")
        self._sql_and_params(monkeypatch, user, lastrowid=7)

        assert user.user_id == 7

    def test_the_rowcount_is_returned(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(rowcount=1, lastrowid=1))

        assert SysUserMapper().insert_user(SysUser(user_name="ry")) == 1


# --------------------------------------------------------------------------- updates


class TestUpdateUser:
    def test_only_non_null_columns_are_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().update_user(SysUser(user_id=2, nick_name="新昵称", update_by="admin"))

        sql = factory.statements[0]
        assert sql.startswith("update sys_user set ")
        assert "nick_name = :nick_name" in sql
        assert "update_by = :update_by" in sql
        assert "user_name" not in sql
        assert sql.endswith("where user_id = :user_id")
        assert factory.sessions[0].params[0]["user_id"] == 2

    def test_empty_required_text_columns_are_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``updateUser`` 对 ``userName`` / ``nickName`` / ``password`` 都要求非空串。"""
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().update_user(
            SysUser(user_id=2, user_name="", nick_name="", password="", status="0")
        )

        sql = factory.statements[0]
        assert "user_name" not in sql
        assert "nick_name" not in sql
        assert "password" not in sql
        assert "status = :status" in sql

    def test_update_by_buss_id_never_touches_password_buss_id_or_image(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """这三列"看起来漏了"，其实是 XML 里就没有 —— 不能补齐。"""
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().update_user_info_by_buss_id(
            SysUser(
                buss_id="B1",
                user_name="ry",
                nick_name="若依",
                password="hash",
                image_id="IMG",
                tenant_id=100,
            )
        )

        sql = factory.statements[0]
        # SET 子句里没有这三列（where 子句里的 ``buss_id = :buss_id`` 不算）
        sets = sql[: sql.index(" where ")]
        assert "password" not in sets
        assert "image_id" not in sets
        assert "buss_id" not in sets
        assert sql.endswith("where buss_id = :buss_id")
        assert "tenant_id = :tenant_id" in sql
        assert factory.sessions[0].params[0]["buss_id"] == "B1"

    def test_update_by_buss_id_and_user_type_adds_the_type_predicate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().update_user_info_by_buss_id_and_user_type(
            SysUser(buss_id="B1", user_type="2", nick_name="专家")
        )

        sql = factory.statements[0]
        assert sql.endswith("where buss_id = :buss_id AND user_type = :user_type")
        assert factory.sessions[0].params[0]["user_type"] == "2"

    def test_update_user_status_is_the_dead_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """XML 里那条 ``updateUserStatus`` 没有调用者；这里只证明它存在且只改 status。"""
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().update_user_status(SysUser(user_id=3, status="1"))

        assert factory.statements[0] == (
            "update sys_user set status = :status where user_id = :user_id"
        )

    def test_update_user_pwd_needs_both_phone_and_user_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().update_user_pwd("158", "hash", "ry")

        sql = factory.statements[0]
        assert "set password = :password, update_time = now()" in sql
        assert sql.endswith("where phonenumber = :phonenumber and user_name = :user_name")

    def test_reset_user_pwd_only_needs_the_account(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().reset_user_pwd("ry", "hash")

        assert factory.statements[0].endswith("where user_name = :user_name")

    def test_update_avatar_returns_the_rowcount(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(rowcount=1))

        assert SysUserMapper().update_user_avatar("ry", "/profile/a.png") == 1


# --------------------------------------------------------------------------- unique checks


class TestUniqueChecks:
    def test_check_user_name_unique_returns_a_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(scalar_value=1))

        assert SysUserMapper().check_user_name_unique("ry") == 1

    def test_check_user_name_unique_ignores_deleted_rows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(scalar_value=0))

        SysUserMapper().check_user_name_unique("ry")

        assert "and del_flag = '0' limit 1" in factory.statements[0]

    def test_check_phone_unique_returns_a_slim_user(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(
            monkeypatch,
            _Result(rows=[(5, "15800000000")], keys=["user_id", "phonenumber"]),
        )

        info = SysUserMapper().check_phone_unique("15800000000")

        assert info is not None
        assert (info.user_id, info.phonenumber) == (5, "15800000000")
        assert info.user_name is None

    def test_check_phone_unique_returns_none_when_free(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(rows=[], keys=["user_id", "phonenumber"]))

        assert SysUserMapper().check_phone_unique("158") is None

    def test_check_email_unique_returns_a_slim_user(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(
            monkeypatch, _Result(rows=[(6, "a@b.c")], keys=["user_id", "email"])
        )

        info = SysUserMapper().check_email_unique("a@b.c")

        assert info is not None
        assert (info.user_id, info.email) == (6, "a@b.c")

    def test_a_null_column_drops_the_whole_slim_object(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(rows=[], keys=["user_id", "email"]))

        assert SysUserMapper().check_email_unique("a@b.c") is None


# --------------------------------------------------------------------------- deletes


class TestDeletes:
    def test_delete_user_by_id_is_a_soft_delete(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().delete_user_by_id(3)

        assert factory.statements[0] == (
            "update sys_user set del_flag = '1' where user_id = :user_id"
        )

    def test_delete_user_by_ids_expands_the_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=3))

        assert SysUserMapper().delete_user_by_ids([1, 2, 3]) == 3
        assert factory.statements[0].endswith("where user_id in (:p0, :p1, :p2)")
        assert factory.sessions[0].params[0] == {"p0": 1, "p1": 2, "p2": 3}

    def test_delete_by_buss_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=1))

        SysUserMapper().delete_user_by_buss_id("B1")

        assert factory.statements[0].endswith("where buss_id = :buss_id")

    def test_delete_by_buss_ids_expands_the_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(rowcount=2))

        SysUserMapper().delete_user_by_buss_ids(["B1", "B2"])

        assert factory.statements[0].endswith("where buss_id in (:p0, :p1)")


# --------------------------------------------------------------------------- misc statements


class TestExistsByBussId:
    def test_the_comparison_is_not_equal_on_purpose(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """XML: ``t.buss_id != #{bussId}`` —— 统计的是"被别人占用"的登录名。"""
        factory = use_session(monkeypatch, _Result(scalar_value=1))

        assert SysUserMapper().exists_by_buss_id(SysUser(buss_id="B1", user_name="ry")) == 1

        sql = factory.statements[0]
        assert "t.buss_id != :buss_id" in sql
        assert "and t.user_name = :user_name" in sql
        assert sql.startswith("select count(1) from sys_user t where t.del_flag='0'")

    def test_blank_fields_are_dropped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(scalar_value=0))

        SysUserMapper().exists_by_buss_id(SysUser(buss_id="", user_name=None))

        assert factory.statements[0] == (
            "select count(1) from sys_user t where t.del_flag='0'"
        )


class TestSelectPwdJudge:
    def test_the_flag_is_mapped_into_the_primitive_field(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(scalar_value=3))

        user = SysUserMapper().select_pwd_judge(2)

        assert user is not None
        assert user.pj_flag == 3
        assert user.user_id is None

    def test_a_missing_user_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_session(monkeypatch, _Result(scalar_value=None))

        assert SysUserMapper().select_pwd_judge(999) is None

    def test_the_statement_is_the_90_day_rule(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = use_session(monkeypatch, _Result(scalar_value=0))

        SysUserMapper().select_pwd_judge(2)

        assert "TIMESTAMPDIFF(DAY,t.update_time" in factory.statements[0]
        assert ">= 90 then 3" in factory.statements[0]


class TestSelectUserListSqlConstant:
    def test_the_base_statement_has_no_where_condition_beyond_del_flag(self) -> None:
        assert "where u.del_flag = '0'" in _SELECT_USER_LIST
        assert "${" not in _SELECT_USER_LIST
