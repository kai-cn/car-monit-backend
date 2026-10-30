"""``SysDeptMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDeptMapper.java

为什么对**拼出来的 SQL** 断言
------------------------------
部门 CRUD 的假 Mapper 会把 SQL 全遮住，而这几处改错了不会报错、只会换结果集：

* ``selectDeptList`` 的 14 个 ``<if>`` 顺序与判据（``!= null and != ''`` 还是 ``!= null``）；
* ``insertDept`` 的 23 个动态列里，哪些额外判了 ``!= ''``、``dept_id`` / ``parent_id``
  还多一个 ``!= 0``；
* ``updateDept`` 的 ``phone`` / ``email`` **只判 null** —— 空串会真的写进库；
* ``updateDeptStatus`` 的 ``where dept_id in (${ancestors})`` 是**字符串拼接**；
* ``selectDeptById`` / ``checkDeptNameUnique`` **不过滤** ``del_flag``；
* ``selectChildrenDeptById`` 是 ``select *``，比 ``selectDeptVo`` 多映射三列。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_dept import SysDept
from app.system.mapper.sys_dept_mapper import SELECT_DEPT_VO, SysDeptMapper

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

    @property
    def params(self) -> List[Dict[str, Any]]:
        return [params for session in self.sessions for params in session.params]

    @property
    def statement(self) -> str:
        return self.statements[0]


#: ``selectDeptVo`` 的列标签，顺序与 XML 一致（26 列）。
_DEPT_KEYS: Sequence[str] = (
    "dept_id",
    "parent_id",
    "ancestors",
    "dept_name",
    "order_num",
    "leader_id",
    "leader",
    "fgld_id",
    "fgld_name",
    "bank_name",
    "account",
    "social_code",
    "postal_code",
    "address",
    "phone",
    "email",
    "status",
    "del_flag",
    "create_by",
    "create_time",
    "is_zbzg",
    "is_uint",
    "tree_leavel",
    "sub_code",
    "dept_jc",
    "tenant_id",
)


def _row(**overrides: Any) -> tuple:
    """一行 ``selectDeptVo`` 结果，按 :data:`_DEPT_KEYS` 顺序排。"""
    values: Dict[str, Any] = {
        "dept_id": 100,
        "parent_id": 0,
        "ancestors": "0",
        "dept_name": "总公司",
        "order_num": "1",
        "leader_id": None,
        "leader": None,
        "fgld_id": None,
        "fgld_name": None,
        "bank_name": None,
        "account": None,
        "social_code": None,
        "postal_code": None,
        "address": None,
        "phone": None,
        "email": None,
        "status": "0",
        "del_flag": "0",
        "create_by": "admin",
        "create_time": None,
        "is_zbzg": "0",
        "is_uint": "1",
        "tree_leavel": 1,
        "sub_code": "001",
        "dept_jc": None,
        "tenant_id": 100,
    }
    values.update(overrides)
    return tuple(values[key] for key in _DEPT_KEYS)


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_dept_mapper

    monkeypatch.setattr(sys_dept_mapper, "session_scope", factory)


# --------------------------------------------------------------------------- selectDeptById


class TestSelectDeptById:
    def test_no_del_flag_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``selectDeptById`` 查得到已逻辑删除的部门 —— Java 原样如此。

        ``insertDept`` 要靠它读已被删掉的父节点，所以这里**不能**"顺手"加
        ``del_flag = '0'``。
        """
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_by_id(100)

        where_clause = factory.statement.split(" from sys_dept d ")[1]
        assert "del_flag" not in where_clause
        assert where_clause == "where dept_id = :dept_id"

    def test_missing_row_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)
        assert SysDeptMapper().select_dept_by_id(404) is None

    def test_all_26_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        dept = SysDeptMapper().select_dept_by_id(100)

        assert dept is not None
        assert dept.dept_id == 100
        assert dept.sub_code == "001"
        assert dept.tree_leavel == 1
        # selectDeptVo 不查这三列 -> 恒为 None
        assert dept.update_by is None
        assert dept.update_time is None
        assert dept.remark is None


# --------------------------------------------------------------------------- selectDeptList


class TestSelectDeptList:
    def test_without_filters_only_the_soft_delete_guard(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept())

        sql = factory.statement
        assert "where d.del_flag = '0' order by d.parent_id, d.order_num" in sql
        assert factory.params[0] == {}

    def test_text_filters_are_added_in_xml_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<if>`` 序列：parentId -> deptName -> status -> deptId -> isZbzg -> ..."""
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(
            SysDept(
                parent_id=0,
                dept_name="总",
                status="0",
                dept_id=100,
                is_zbzg="1",
                is_uint="1",
                tree_leavel=1,
                sub_code="001",
                dept_jc="总",
                tenant_id=100,
                leader_id=7,
                leader="张三",
                fgld_id=8,
                fgld_name="李四",
                dept_sub_code="001-",
            )
        )

        sql = factory.statement
        order = [
            "AND d.parent_id = :parent_id",
            "AND d.dept_name like concat('%', :dept_name, '%')",
            "AND d.status = :status",
            "AND d.dept_id = :dept_id",
            "and d.is_zbzg = :is_zbzg",
            "and d.is_uint = :is_uint",
            "and d.tree_leavel = :tree_leavel",
            "and d.sub_code = :sub_code",
            "and d.dept_jc = :dept_jc",
            "and d.tenant_id = :tenant_id",
            "and d.leader_id = :leader_id",
            "and d.leader = :leader",
            "and d.fgld_id = :fgld_id",
            "and d.fgld_name like concat('%', :fgld_name, '%')",
        ]
        positions = [sql.index(fragment) for fragment in order]
        assert positions == sorted(positions)

    def test_dept_sub_code_matches_a_prefix_not_a_contains(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``concat(#{deptSubCode}, '%')`` —— 没有前导 ``%``，是前缀匹配。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept(dept_sub_code="001-"))

        assert "concat(:dept_sub_code, '%')" in factory.statement
        assert "%:dept_sub_code" not in factory.statement

    def test_a_single_space_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """OGNL 的 ``x != ''`` **不 trim**，所以单个空格是有效条件。

        换成 ``string_utils.is_not_empty``（内部会 trim）就会漏掉这个条件。
        """
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept(dept_name=" ", status=" "))

        assert "d.dept_name like" in factory.statement
        assert "AND d.status = :status" in factory.statement
        assert factory.params[0] == {"dept_name": " ", "status": " "}

    def test_empty_string_does_not_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept(dept_name="", status="", dept_jc=""))

        assert factory.params[0] == {}

    def test_zero_tree_leavel_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<if test="treeLeavel != null ">`` 只判 null —— ``0`` 不是"没传"。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept(tree_leavel=0))

        assert factory.params[0] == {"tree_leavel": 0}

    def test_the_sjzb_dept_flag_adds_an_exists_subquery(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``flag == 'sjzbDept'`` 走"上级有资格的招标单位"那段 ``exists``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept(flag="sjzbDept", data_id="100"))

        assert "and exists (" in factory.statement
        assert "tb1.dept_id = d.tenant_id" in factory.statement
        assert factory.params[0] == {"data_id": "100"}

    @pytest.mark.parametrize("flag", ["myDept", "sjzbDeptCg", "allDept", None, ""])
    def test_other_flags_do_not_touch_the_sql(
        self, monkeypatch: pytest.MonkeyPatch, flag: Optional[str]
    ) -> None:
        """只有 ``flag == 'sjzbDept'`` 生效；其余 flag 由 Controller 事前处理。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept(flag=flag, data_id="100"))

        assert "exists" not in factory.statement
        assert factory.params[0] == {}

    def test_the_projection_is_shared_verbatim(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list(SysDept())

        assert factory.statement.startswith(" ".join(SELECT_DEPT_VO.split()))


# --------------------------------------------------------------------------- selectDeptListByRoleId


class TestSelectDeptListByRoleId:
    def test_not_strict_skips_the_parent_exclusion(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[(100,), (101,)]))
        _patch(monkeypatch, factory)

        ids = SysDeptMapper().select_dept_list_by_role_id(2, False)

        assert "not in" not in factory.statement
        assert "left join sys_role_dept rd on d.dept_id = rd.dept_id" in factory.statement
        assert factory.params[0] == {"role_id": 2}
        assert ids == [100, 101]

    def test_strict_excludes_departments_whose_parent_is_also_checked(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        SysDeptMapper().select_dept_list_by_role_id(2, True)

        assert "and d.dept_id not in (select d.parent_id from sys_dept d" in factory.statement

    def test_returns_the_first_column_as_a_plain_int(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[(100,), (101,)]))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().select_dept_list_by_role_id(2, False) == [100, 101]


# --------------------------------------------------------------------------- the three counts


class TestCountStatements:
    def test_check_dept_exist_user_ignores_deleted_users(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(scalar_value=3))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().check_dept_exist_user(100) == 3
        assert (
            factory.statement
            == "select count(1) from sys_user where dept_id = :dept_id and del_flag = '0'"
        )

    def test_has_child_by_dept_id_stops_at_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(scalar_value=1))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().has_child_by_dept_id(100) == 1
        assert factory.statement.endswith("and parent_id = :dept_id limit 1")

    def test_normal_children_compares_status_to_an_integer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``status = 0``（不带引号）—— varchar 列比数字，MySQL 隐式转换。"""
        factory = _SessionFactory(_Result(scalar_value=0))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().select_normal_children_dept_by_id(100) == 0
        assert "where status = 0 and del_flag = '0'" in factory.statement
        assert "find_in_set(:dept_id, ancestors)" in factory.statement

    def test_a_null_scalar_becomes_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(scalar_value=None))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().check_dept_exist_user(100) == 0


# --------------------------------------------------------------------------- unique / tenant


class TestCheckDeptNameUnique:
    def test_unique_is_scoped_to_the_parent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """判重键是 ``(dept_name, parent_id)`` —— 不同分公司下允许同名部门。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        result = SysDeptMapper().check_dept_name_unique("财务部", 100)

        assert result is None
        assert "where dept_name=:dept_name and parent_id = :parent_id limit 1" in (
            factory.statement
        )
        assert factory.params[0] == {"dept_name": "财务部", "parent_id": 100}

    def test_a_null_parent_id_matches_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``parent_id = null`` 在 SQL 里永假（Java 同样查不到）。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().check_dept_name_unique("财务部", None) is None
        assert factory.params[0]["parent_id"] is None


class TestSelectTenantId:
    def test_the_sub_code_sits_on_the_left_of_like(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``:sub_code like concat(d.sub_code, '%')`` —— 找自己的祖先单位。"""
        factory = _SessionFactory(_Result(rows=[_row(dept_id=100, is_uint="1")], keys=_DEPT_KEYS))
        _patch(monkeypatch, factory)

        found = SysDeptMapper().select_tenant_id(SysDept(sub_code="001-001"))

        assert found is not None and found.dept_id == 100
        assert ":sub_code like concat(d.sub_code, '%')" in factory.statement
        assert "and d.is_uint = '1'" in factory.statement
        assert "order by d.tree_leavel desc limit 1" in factory.statement


# --------------------------------------------------------------------------- insertDept


class TestInsertDept:
    def test_the_full_column_list_follows_the_xml_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=101))
        _patch(monkeypatch, factory)

        dept = SysDept(
            parent_id=100,
            dept_name="财务部",
            ancestors="0,100",
            order_num="1",
            leader_id=7,
            leader="张三",
            fgld_id=8,
            fgld_name="李四",
            bank_name="工行",
            account="6222",
            social_code="SC",
            postal_code="PC",
            address="某路 1 号",
            phone="13800000000",
            email="a@b.c",
            status="0",
            create_by="admin",
            is_zbzg="0",
            is_uint="0",
            tree_leavel=2,
            sub_code="001-001",
            dept_jc="财务",
            tenant_id=100,
        )

        assert SysDeptMapper().insert_dept(dept) == 1

        sql = factory.statement
        assert sql.startswith("insert into sys_dept(")
        assert "create_time" in sql and "sysdate()" in sql
        columns = sql[sql.index("(") + 1 : sql.index(")values")]
        assert columns.split(",") == [
            "parent_id",
            "dept_name",
            "ancestors",
            "order_num",
            "leader_id",
            "leader",
            "fgld_id",
            "fgld_name",
            "bank_name",
            "account",
            "social_code",
            "postal_code",
            "address",
            "phone",
            "email",
            "status",
            "create_by",
            "is_zbzg",
            "is_uint",
            "tree_leavel",
            "sub_code",
            "dept_jc",
            "tenant_id",
            "create_time",
        ]
        # MyBatis keyProperty="deptId"
        assert dept.dept_id == 101

    def test_dept_id_zero_is_not_inserted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<if test="deptId != null and deptId != 0">`` —— 0 当"未设置"。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().insert_dept(SysDept(dept_id=0, parent_id=0, dept_name="x"))

        columns = factory.statement[
            factory.statement.index("(") + 1 : factory.statement.index(")values")
        ].split(",")
        assert "dept_id" not in columns
        assert "parent_id" not in columns

    def test_empty_strings_follow_each_column_rule(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().insert_dept(
            SysDept(dept_name="", ancestors="", order_num="", phone="", email="", leader="")
        )

        columns = factory.statement[
            factory.statement.index("(") + 1 : factory.statement.index(")values")
        ].split(",")
        # leader 只判 null -> 空串照样插入；其余判 != '' -> 被丢掉
        assert columns == ["leader", "create_time"]

    def test_a_non_empty_leader_is_kept_even_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().insert_dept(SysDept(leader=""))

        assert factory.params[0] == {"leader": ""}


# --------------------------------------------------------------------------- updateDept


class TestUpdateDept:
    def test_update_time_is_always_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<set>`` 里有 ``update_time = sysdate()`` 兜底，所以 SQL 永不非法。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().update_dept(SysDept(dept_id=100))

        assert factory.statement == (
            "update sys_dept set update_time = sysdate() where dept_id = :dept_id"
        )
        assert factory.params[0] == {"dept_id": 100}

    def test_empty_phone_and_email_are_written_over(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """**最容易踩的一处**：``updateDept`` 的 phone/email 只判 ``!= null``。

        所以清空邮箱（``""``）是真的写库；而 ``insertDept`` 里同样传 ``""`` 则不会插
        这两列。同一列两条语句判据不同，是 XML 原文如此。
        """
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().update_dept(SysDept(dept_id=100, phone="", email=""))

        assert "phone = :phone" in factory.statement
        assert "email = :email" in factory.statement
        assert factory.params[0] == {"phone": "", "email": "", "dept_id": 100}

    def test_parent_id_zero_is_not_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<if test="parentId != null and parentId != 0">`` —— 0 表示"不改父级"。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().update_dept(SysDept(dept_id=100, parent_id=0))

        assert "parent_id" not in factory.statement

    def test_the_set_clause_order_matches_the_xml(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().update_dept(
            SysDept(
                dept_id=100,
                parent_id=50,
                dept_name="财务部",
                ancestors="0,50",
                order_num="2",
                leader_id=7,
                leader="张三",
                fgld_id=8,
                fgld_name="李四",
                bank_name="工行",
                account="6222",
                social_code="SC",
                postal_code="PC",
                address="某路",
                phone="138",
                email="a@b.c",
                status="0",
                update_by="admin",
                is_zbzg="0",
                is_uint="0",
                tree_leavel=2,
                sub_code="001-001",
                dept_jc="财务",
                tenant_id=100,
            )
        )

        assignments = factory.statement[
            factory.statement.index("set ") + 4 : factory.statement.index(" where ")
        ].split(", ")
        assert assignments == [
            "parent_id = :parent_id",
            "dept_name = :dept_name",
            "ancestors = :ancestors",
            "order_num = :order_num",
            "leader_id = :leader_id",
            "leader = :leader",
            "fgld_id = :fgld_id",
            "fgld_name = :fgld_name",
            "bank_name = :bank_name",
            "account = :account",
            "social_code = :social_code",
            "postal_code = :postal_code",
            "address = :address",
            "phone = :phone",
            "email = :email",
            "status = :status",
            "update_by = :update_by",
            "is_zbzg = :is_zbzg",
            "is_uint = :is_uint",
            "tree_leavel = :tree_leavel",
            "sub_code = :sub_code",
            "dept_jc = :dept_jc",
            "tenant_id = :tenant_id",
            "update_time = sysdate()",
        ]


# --------------------------------------------------------------------------- children / status


class TestUpdateDeptChildren:
    def test_one_case_per_row(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, factory)

        rows = [
            SysDept(dept_id=101, ancestors="0,50,101"),
            SysDept(dept_id=102, ancestors="0,50,102"),
        ]

        assert SysDeptMapper().update_dept_children(rows) == 2

        assert factory.statement == (
            "update sys_dept set ancestors = case dept_id "
            "when :dept_id_0 then :ancestors_0 when :dept_id_1 then :ancestors_1 "
            "end where dept_id in (:dept_id_0,:dept_id_1)"
        )
        assert factory.params[0] == {
            "dept_id_0": 101,
            "ancestors_0": "0,50,101",
            "dept_id_1": 102,
            "ancestors_1": "0,50,102",
        }


class TestSelectChildrenDeptById:
    def test_select_star_maps_three_extra_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``select *`` + MyBatis 的 PARTIAL autoMapping 会把这三列也映射上。"""
        keys = tuple(_DEPT_KEYS) + ("update_by", "update_time", "remark")
        row = _row() + ("admin", None, "备注")
        factory = _SessionFactory(_Result(rows=[row], keys=keys))
        _patch(monkeypatch, factory)

        children = SysDeptMapper().select_children_dept_by_id(100)

        assert factory.statement == (
            "select * from sys_dept where find_in_set(:dept_id, ancestors)"
        )
        assert children[0].update_by == "admin"
        assert children[0].remark == "备注"


class TestUpdateDeptStatus:
    def test_ancestors_are_spliced_not_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``where dept_id in (${ancestors})`` —— 值直接进 SQL 文本。"""
        factory = _SessionFactory(_Result(rowcount=3))
        _patch(monkeypatch, factory)

        dept = SysDept(ancestors="0,100,101", status="1", update_by="admin")
        assert SysDeptMapper().update_dept_status(dept) == 3

        assert factory.statement == (
            "update sys_dept set status = :status, update_by = :update_by, "
            "update_time = sysdate() where dept_id in (0,100,101)"
        )
        assert factory.params[0] == {"status": "1", "update_by": "admin"}

    def test_a_null_ancestors_renders_the_literal_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MyBatis 的 ``${}`` 对 null 渲染成字面量 ``null``（不是空串）。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysDeptMapper().update_dept_status(SysDept(dept_id=100))

        assert "where dept_id in (null)" in factory.statement

    def test_only_update_time_when_nothing_else_is_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDeptMapper().update_dept_status(SysDept(ancestors="0", status="", update_by=""))

        assert factory.statement.startswith(
            "update sys_dept set update_time = sysdate() where dept_id in (0)"
        )


# --------------------------------------------------------------------------- deletes / tenant


class TestDeleteStatements:
    def test_delete_dept_by_id_is_a_logical_delete(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().delete_dept_by_id(100) == 1
        assert factory.statement == "update sys_dept set del_flag = '2' where dept_id = :dept_id"

    def test_delete_dept_all_only_touches_the_seed_rows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=4))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().delete_dept_all() == 4
        assert factory.statement == "delete from sys_dept where create_by = '-9999'"


class TestUpdateTenantId:
    def test_tenant_id_is_both_the_value_and_the_predicate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, factory)

        assert SysDeptMapper().update_tenant_id(SysDept(tenant_id=100)) == 2

        assert factory.statement == (
            "update sys_dept set tenant_id = :tenant_id "
            "where is_uint = '0' and parent_id = :tenant_id"
        )
        assert factory.params[0] == {"tenant_id": 100}
