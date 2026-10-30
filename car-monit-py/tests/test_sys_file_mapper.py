"""``SysFileMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysFileMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysFileMapper.java

本模块"改错了不报错、只悄悄换结果集"的六处
-------------------------------------------
1. ``selectSysFileList`` 的 ``where t.del_flag = '0'`` 是**硬编码**的（XML 没有
   ``<where>``），所以条件片段**不带**前导 ``AND``。
2. 11 个 ``<if>`` 分两类判据：``id`` / ``original`` / ``type`` / ``bussType`` /
   ``createUser`` / ``updateUser`` 与三个 ``like`` 字段是 ``!= null and != ''``；
   ``fileSize`` / ``tenantId`` **只判 null** —— 后者传 ``""`` 会真的变成 ``= ''``。
3. ``order by t.create_time desc,t.id`` 是**自带**的，客户端的 ``orderByColumn`` 被忽略。
4. ``selectSysFileByIds`` 是**唯一**带 ``left join sys_user`` 的语句 —— 只有它能拿到
   ``createUserName``；按 id 查 / 列表查都是 ``null``。
5. ``deleteSysFileByIdNew`` 是**唯一**的物理删除（``delete from``，且原 SQL 里是两个空格）。
6. ``updateCAFile`` 把主键写死成 ``3001``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.page.page_domain import PageDomain
from app.common.core.page.page_helper import PageList, clear_page
from app.system.domain.sys_file import SysFile
from app.system.mapper.sys_file_mapper import (
    SELECT_SYS_FILE_VO,
    SysFileMapper,
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
        self.params: List[Optional[Dict[str, Any]]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> _Result:
        self.statements.append(" ".join(str(statement).split()))
        self.params.append(None if params is None else dict(params))
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
    def params(self) -> List[Optional[Dict[str, Any]]]:
        return [params for session in self.sessions for params in session.params]


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_file_mapper

    monkeypatch.setattr(sys_file_mapper, "session_scope", factory)


def _patch_take_page(monkeypatch: pytest.MonkeyPatch, page: PageDomain) -> None:
    """直接给 :func:`take_page` 一个已经拼好的 ``PageDomain``。

    ``start_page()`` 只能从请求上下文取参数（:func:`build_page_request` 走
    ``get_request()``），在纯 mapper 单测里没有请求，所以替换掉这个拦截器。
    """
    from app.system.mapper import sys_file_mapper

    monkeypatch.setattr(sys_file_mapper, "take_page", lambda: page)


@pytest.fixture(autouse=True)
def _clear_page_state() -> Any:
    clear_page()
    yield
    clear_page()


#: ``selectSysFileVo`` 的 14 列，顺序与 XML 一致。
_VO_KEYS: Sequence[str] = (
    "id",
    "file_name",
    "bucket_name",
    "original",
    "type",
    "file_size",
    "buss_type",
    "buss_name",
    "create_user",
    "create_time",
    "update_user",
    "update_time",
    "del_flag",
    "tenant_id",
)


def _list(monkeypatch: pytest.MonkeyPatch, entity: SysFile) -> _SessionFactory:
    factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
    _patch(monkeypatch, factory)
    SysFileMapper().select_sys_file_list(entity)
    return factory


# --------------------------------------------------------------------------- 投影


class TestProjection:
    def test_the_vo_selects_the_fourteen_columns(self) -> None:
        assert SELECT_SYS_FILE_VO == (
            "t.id, t.file_name, t.bucket_name, t.original, t.type, t.file_size, "
            "t.buss_type, t.buss_name, t.create_user, t.create_time, t.update_user, "
            "t.update_time, t.del_flag, t.tenant_id"
        )


# --------------------------------------------------------------------------- selectById


class TestSelectById:
    def test_there_is_no_del_flag_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """与 list 不对称：软删除的行**仍然**能按 id 查到。"""
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        SysFileMapper().select_sys_file_by_id(3001)

        assert factory.statements[0] == (
            f"select {SELECT_SYS_FILE_VO} from sys_file t where t.id = :id"
        )
        assert "del_flag" not in factory.statements[0].split("where")[1]
        assert factory.params == [{"id": 3001}]

    def test_a_missing_row_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        assert SysFileMapper().select_sys_file_by_id(1) is None

    def test_a_hit_is_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        row = (7, "a.pdf", "developer", "原文件.pdf", "pdf", 12, None, None, "2",
               None, "2", None, "0", 1)
        factory = _SessionFactory(_Result(rows=[row], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        entity = SysFileMapper().select_sys_file_by_id(7)

        assert entity is not None
        assert (entity.id, entity.file_name, entity.type) == (7, "a.pdf", "pdf")
        assert entity.file_size == 12

    def test_create_user_name_is_not_filled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """只有 ``selectSysFileByIds`` 的 join 会填它。"""
        row = (7, "a.pdf", None, None, "pdf", 1, None, None, "2",
               None, None, None, "0", None)
        factory = _SessionFactory(_Result(rows=[row], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        entity = SysFileMapper().select_sys_file_by_id(7)

        assert entity is not None
        assert entity.create_user_name is None


# --------------------------------------------------------------------------- selectByIds


class TestSelectByIds:
    def test_the_join_and_the_alias_are_the_ones_from_the_xml(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=list(_VO_KEYS) + ["createUserName"]))
        _patch(monkeypatch, factory)

        SysFileMapper().select_sys_file_by_ids(["1", "2"])

        assert factory.statements[0] == (
            f"select {SELECT_SYS_FILE_VO}, t2.nick_name createUserName "
            "from sys_file t "
            "left join sys_user t2 on t.create_user = t2.user_id and t2.del_flag='0' "
            "where t.id in (:p0, :p1) "
            "order by t.id"
        )
        assert factory.params == [{"p0": "1", "p1": "2"}]

    def test_the_create_user_name_is_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        row = (7, "a.pdf", None, None, "pdf", 1, None, None, "2",
               None, None, None, "0", None, "张三")
        factory = _SessionFactory(_Result(rows=[row], keys=list(_VO_KEYS) + ["createUserName"]))
        _patch(monkeypatch, factory)

        rows = SysFileMapper().select_sys_file_by_ids(["7"])

        assert rows[0].create_user_name == "张三"

    def test_an_empty_array_renders_an_empty_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<foreach>`` 对空数组拼出 ``in ()`` —— SQL 语法错误，照抄。"""
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        SysFileMapper().select_sys_file_by_ids([])

        assert "where t.id in ()" in factory.statements[0]


# --------------------------------------------------------------------------- selectList


class TestSelectList:
    def test_the_hardcoded_condition_is_the_only_one_for_an_empty_query(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _list(monkeypatch, SysFile())

        assert factory.statements[0] == (
            f"select {SELECT_SYS_FILE_VO} from sys_file t "
            "where t.del_flag = '0' "
            "order by t.create_time desc,t.id"
        )
        assert factory.params == [{}]

    def test_the_conditions_join_with_and_and_never_emit_where_and(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = _list(monkeypatch, SysFile(original="a.pdf")).statements[0]

        assert "where t.del_flag = '0' and t.original = :original" in statement
        assert "where and" not in statement

    def test_the_three_like_conditions_use_concat(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = _list(
            monkeypatch,
            SysFile(file_name="a", bucket_name="b", buss_name="c"),
        ).statements[0]

        assert "t.file_name like concat('%', :file_name, '%')" in statement
        assert "t.bucket_name like concat('%', :bucket_name, '%')" in statement
        assert "t.buss_name like concat('%', :buss_name, '%')" in statement

    def test_an_empty_string_drops_the_equality_condition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``!= null and != ''`` 的那一组：空串等于"不筛"。"""
        statement = _list(monkeypatch, SysFile(original="")).statements[0]

        where_part = statement.split("where ", 1)[1]
        assert "t.original" not in where_part

    def test_the_null_only_condition_would_keep_an_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``!= null`` 的那一组：``""`` 会真的拼进 SQL（原样照抄）。

        ``model_construct`` 绕过 pydantic 的 ``"" -> None`` 转换，用于直击这条
        ``<if>``：从 HTTP 进来时 ``Long tenantId`` 收到 ``""`` 同样变成 ``null``，
        所以线上其实到不了这里 —— 但 XML 的判据确实是"只判 null"。
        """
        factory = _list(monkeypatch, SysFile.model_construct(tenant_id=""))

        assert "t.tenant_id = :tenant_id" in factory.statements[0]
        assert factory.params == [{"tenant_id": ""}]

    def test_zero_is_not_treated_as_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``fileSize = 0`` 是合法筛选值（判据只有 ``!= null``）。"""
        factory = _list(monkeypatch, SysFile(file_size=0))

        assert "t.file_size = :file_size" in factory.statements[0]
        assert factory.params == [{"file_size": 0}]

    def test_the_built_in_order_by_is_kept(self, monkeypatch: pytest.MonkeyPatch) -> None:
        statement = _list(monkeypatch, SysFile()).statements[0]

        assert statement.endswith("order by t.create_time desc,t.id")
        assert "file_name desc" not in statement

    def test_the_client_order_by_is_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """语句自带 ``order by``，``startPage()`` 的 ``orderByColumn`` 不会追加。"""
        _patch_take_page(
            monkeypatch,
            PageDomain(page_num=1, page_size=10, order_by_column="file_name", is_asc="desc"),
        )
        factory = _SessionFactory(_Result(scalar_value=1), _Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        SysFileMapper().select_sys_file_list(SysFile())

        assert "order by t.create_time desc,t.id" in factory.statements[1]
        assert "file_name desc" not in factory.statements[1]

    def test_the_conditions_keep_the_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """11 个 ``<if>`` 的**顺序**与 XML 一致 —— 拼出的 SQL 与 MyBatis 逐字相同。"""
        entity = SysFile(
            id=1,
            file_name="a",
            bucket_name="b",
            original="c",
            type="pdf",
            file_size=2,
            buss_type="t",
            buss_name="n",
            create_user="3",
            update_user="4",
            tenant_id=5,
        )
        statement = _list(monkeypatch, entity).statements[0]

        order = [
            "t.id = :id",
            "t.file_name like concat('%', :file_name, '%')",
            "t.bucket_name like concat('%', :bucket_name, '%')",
            "t.original = :original",
            "t.type = :type",
            "t.file_size = :file_size",
            "t.buss_type = :buss_type",
            "t.buss_name like concat('%', :buss_name, '%')",
            "t.create_user = :create_user",
            "t.update_user = :update_user",
            "t.tenant_id = :tenant_id",
        ]
        positions = [statement.index(fragment) for fragment in order]
        assert positions == sorted(positions)

    def test_the_row_is_mapped_through_the_vo_keys(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        row = (7, "a.pdf", "developer", "原文件.pdf", "pdf", 12, "s", "b", "2",
               None, None, None, "0", 1)
        factory = _SessionFactory(_Result(rows=[row], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        page = SysFileMapper().select_sys_file_list(SysFile())

        assert isinstance(page, PageList)
        assert page[0].file_name == "a.pdf"


# --------------------------------------------------------------------------- insert


class TestInsert:
    def test_only_the_non_null_columns_are_written(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().insert_sys_file(SysFile(id=7, file_name="a.pdf"))

        assert factory.statements[0] == (
            "insert into sys_file (id,file_name) values (:id,:file_name)"
        )
        assert factory.params == [{"id": 7, "file_name": "a.pdf"}]

    def test_the_column_order_is_the_xml_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().insert_sys_file(
            SysFile(
                id=7,
                file_name="a.pdf",
                bucket_name="b",
                original="o",
                type="pdf",
                file_size=1,
                buss_type="t",
                buss_name="n",
                create_user="2",
                update_user="2",
                del_flag="0",
                tenant_id=1,
            )
        )

        columns = factory.statements[0].split("(", 1)[1].split(")", 1)[0]
        assert columns == (
            "id,file_name,bucket_name,original,type,file_size,buss_type,buss_name,"
            "create_user,update_user,del_flag,tenant_id"
        )

    def test_the_generated_key_is_written_back_only_when_id_is_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=99))
        _patch(monkeypatch, factory)
        entity = SysFile(file_name="a.pdf")

        SysFileMapper().insert_sys_file(entity)

        assert entity.id == 99

    def test_an_explicit_id_is_never_overwritten(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """service 插入前已赋雪花 id，所以 ``useGeneratedKeys`` 实际永不触发。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=99))
        _patch(monkeypatch, factory)
        entity = SysFile(id=7, file_name="a.pdf")

        SysFileMapper().insert_sys_file(entity)

        assert entity.id == 7


# --------------------------------------------------------------------------- update


class TestUpdate:
    def test_only_the_non_null_columns_are_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().update_sys_file(SysFile(id=7, file_name="a.pdf"))

        assert factory.statements[0] == (
            "update sys_file set file_name = :file_name where id = :id"
        )
        assert factory.params == [{"file_name": "a.pdf", "id": 7}]

    def test_an_empty_string_clears_the_column(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """13 个 set 全是 ``!= null``，没有 ``!= ''`` 的特例。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().update_sys_file(SysFile(id=7, original=""))

        assert "original = :original" in factory.statements[0]
        assert factory.params == [{"original": "", "id": 7}]

    def test_the_id_is_not_a_set_column(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().update_sys_file(SysFile(id=7, file_name="a.pdf"))

        assert "set id" not in factory.statements[0]


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_the_single_delete_is_soft(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().delete_sys_file_by_id(7)

        assert factory.statements[0] == "update sys_file set del_flag = '1' where id = :id"
        assert factory.params == [{"id": 7}]

    def test_the_batch_delete_is_soft(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, factory)

        SysFileMapper().delete_sys_file_by_ids([1, 2])

        assert factory.statements[0] == (
            "update sys_file set del_flag = '1' where id in (:p0, :p1)"
        )
        assert factory.params == [{"p0": 1, "p1": 2}]

    def test_delete_by_id_new_is_the_only_physical_delete(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """原 SQL 里 ``delete from`` 与 ``sys_file`` 之间是**两个**空格。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().delete_sys_file_by_id_new(7)

        assert factory.statements[0] == "delete from sys_file where id = :id"
        assert factory.params == [{"id": 7}]

    def test_update_ca_file_hardcodes_the_primary_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysFileMapper().update_ca_file(SysFile(id=7))

        assert factory.statements[0] == "update sys_file set id = 3001 where id = :id"
        assert factory.params == [{"id": 7}]


# --------------------------------------------------------------------------- 分页


class TestPaging:
    def test_the_count_wraps_the_list_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_take_page(
            monkeypatch, PageDomain(page_num=2, page_size=5, reasonable=True)
        )
        factory = _SessionFactory(
            _Result(scalar_value=7),
            _Result(rows=[], keys=_VO_KEYS),
        )
        _patch(monkeypatch, factory)

        page = SysFileMapper().select_sys_file_list(SysFile())

        assert factory.statements[0].startswith(
            f"select count(0) from (select {SELECT_SYS_FILE_VO} from sys_file t"
        )
        assert factory.statements[0].endswith(") table_count")
        assert factory.statements[1].endswith("LIMIT 5, 5")
        assert (page.total, page.page_num, page.page_size) == (7, 2, 5)
