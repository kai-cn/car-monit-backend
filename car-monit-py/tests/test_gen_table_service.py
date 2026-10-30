# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java

"""``GenTableServiceImpl`` —— 五个 ``init*`` 的顺序、三段校验、导入的包装.

这一层为什么值钱
----------------
1. **五处 ``init*`` 的调用顺序互不相同**（Java 原样，不是笔误）：
   ``previewCode`` 是 filter→richText→upload→dict→link，
   ``generatorCode(String)`` 是 dict→richText→filter→link→upload，
   ``generatorCode(String, Zip)`` 是 dict→upload→richText→link→filter。
   顺序决定 ``initLinkTableInfo`` 读到的字典驼峰与过滤后的列集合，抽成公共的
   ``_init_all`` 就会改结果。
2. ``validateEdit`` 里的 ``TPL_SUB`` 分支嵌在 ``TPL_TREE`` 分支内部 —— 永远不成立，
   主子表**从不**校验子表名与外键名。那两条错误文案是死代码。
3. ``importGenTable`` 把任何异常包成 ``"导入失败：" + e.getMessage()``，而 NPE 的
   ``getMessage()`` 是 ``null`` -> 文案是 ``"导入失败：null"``。
4. ``updateGenTable`` 先写 ``options``（``params`` 整体序列化）再更新列，且
   **只有主表更新到行**才去更新列。
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest

from app.common.exception.exceptions import CustomException
from app.generator.domain.gen_table import GenTable
from app.generator.domain.gen_table_column import GenTableColumn
from app.generator.service import gen_table_service as service_module
from app.generator.service.gen_table_service import FILTER_COLUMN_NAME_LIST, GenTableService

# --------------------------------------------------------------------------- fakes


class _FakeTableMapper:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, tuple]] = []
        self.table_by_id: Optional[GenTable] = None
        self.table_by_name: Optional[GenTable] = None
        #: 按表名取不同实体（``downloadCode(String[])`` 那种一次处理多张表的场景）
        self.by_name_map: Optional[Dict[str, GenTable]] = None
        self.insert_row = 1
        self.update_row = 1
        self.list_result: List[GenTable] = []
        self.db_result: List[GenTable] = []
        self.by_names_result: List[GenTable] = []
        self.all_result: List[GenTable] = []

    def select_gen_table_by_id(self, table_id: Optional[int]) -> Optional[GenTable]:
        self.calls.append(("select_gen_table_by_id", (table_id,)))
        return self.table_by_id

    def select_gen_table_by_name(self, table_name: Optional[str]) -> Optional[GenTable]:
        self.calls.append(("select_gen_table_by_name", (table_name,)))
        if self.by_name_map is not None:
            return self.by_name_map.get(str(table_name))
        return self.table_by_name

    def select_gen_table_list(self, gen_table: GenTable) -> List[GenTable]:
        self.calls.append(("select_gen_table_list", (gen_table,)))
        return self.list_result

    def select_db_table_list(self, gen_table: GenTable) -> List[GenTable]:
        self.calls.append(("select_db_table_list", (gen_table,)))
        return self.db_result

    def select_db_table_list_by_names(self, names: Sequence[str]) -> List[GenTable]:
        self.calls.append(("select_db_table_list_by_names", (tuple(names),)))
        return self.by_names_result

    def select_gen_table_all(self) -> List[GenTable]:
        self.calls.append(("select_gen_table_all", ()))
        return self.all_result

    def insert_gen_table(self, gen_table: GenTable) -> int:
        self.calls.append(("insert_gen_table", (gen_table,)))
        return self.insert_row

    def update_gen_table(self, gen_table: GenTable) -> int:
        self.calls.append(("update_gen_table", (gen_table,)))
        return self.update_row

    def delete_gen_table_by_ids(self, table_ids: Sequence[int]) -> int:
        self.calls.append(("delete_gen_table_by_ids", (tuple(table_ids),)))
        return 1


class _FakeColumnMapper:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, tuple]] = []
        self.db_columns: List[GenTableColumn] = []

    def select_db_table_columns_by_name(self, table_name: str) -> List[GenTableColumn]:
        self.calls.append(("select_db_table_columns_by_name", (table_name,)))
        return self.db_columns

    def insert_gen_table_column(self, column: GenTableColumn) -> int:
        self.calls.append(("insert_gen_table_column", (column,)))
        return 1

    def update_gen_table_column(self, column: GenTableColumn) -> int:
        self.calls.append(("update_gen_table_column", (column,)))
        return 1

    def delete_gen_table_columns(self, columns: Sequence[GenTableColumn]) -> int:
        self.calls.append(("delete_gen_table_columns", (tuple(columns),)))
        return 1

    def delete_gen_table_column_by_ids(self, table_ids: Sequence[int]) -> int:
        self.calls.append(("delete_gen_table_column_by_ids", (tuple(table_ids),)))
        return 1

    def select_gen_table_column_list_by_table_column_ids(
        self, ids: Sequence[str]
    ) -> List[GenTableColumn]:
        self.calls.append(("select_gen_table_column_list_by_table_column_ids", (tuple(ids),)))
        return []

    def select_gen_table_column_list_by_table_column_id_list(
        self, ids: Sequence[Optional[int]]
    ) -> List[GenTableColumn]:
        raise AssertionError("service 应该走 GenTableColumnService，不该直接碰 mapper")


class _FakeColumnService:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, tuple]] = []
        self.by_column_id_list: List[GenTableColumn] = []
        self.by_column_ids: Optional[List[GenTableColumn]] = None

    def select_gen_table_column_list_by_table_column_id_list(
        self, ids: Optional[Sequence[Optional[int]]]
    ) -> Optional[List[GenTableColumn]]:
        self.calls.append(("by_id_list", (tuple(ids or ()),)))
        return self.by_column_id_list

    def select_gen_table_column_list_by_table_column_ids(
        self, ids: Optional[str]
    ) -> Optional[List[GenTableColumn]]:
        self.calls.append(("by_ids", (ids,)))
        return self.by_column_ids


class _Services:
    def __init__(self) -> None:
        self.tables = _FakeTableMapper()
        self.columns = _FakeColumnMapper()
        self.column_service = _FakeColumnService()
        self.service = GenTableService(
            table_mapper=self.tables,  # type: ignore[arg-type]
            column_mapper=self.columns,  # type: ignore[arg-type]
            column_service=self.column_service,  # type: ignore[arg-type]
        )


@pytest.fixture()
def services() -> _Services:
    return _Services()


def _recorder(sink: List[str], name: str) -> Any:
    def _stub(*_args: Any, **_kwargs: Any) -> None:
        sink.append(name)

    return _stub


def _stub_init_chain(monkeypatch: pytest.MonkeyPatch, names: Sequence[str]) -> List[str]:
    """把若干 ``init*`` / ``set*`` 换成只记名的桩."""
    sink: List[str] = []
    for name in names:
        monkeypatch.setattr(GenTableService, name, _recorder(sink, name))
    return sink


class _Template:
    def __init__(self, name: str) -> None:
        self.name = name

    def merge(self, _context: Any) -> str:
        return f"// {self.name}"


class _TemplateStubs:
    """``get_template_list`` / ``get_template`` / ``prepare_context`` 的替身."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, templates: Sequence[str]) -> None:
        self.templates = list(templates)
        self.list_calls: List[Tuple[Any, Any]] = []
        monkeypatch.setattr(service_module, "get_template_list", self._get_template_list)
        monkeypatch.setattr(service_module, "get_template", self._get_template)
        monkeypatch.setattr(service_module, "prepare_context", lambda _table: object())

    def _get_template_list(self, tpl_category: Any, is_mybatis_plus: Any) -> List[str]:
        self.list_calls.append((tpl_category, is_mybatis_plus))
        return list(self.templates)

    def _get_template(self, template: str) -> _Template:
        return _Template(template)


def _crud_table(**overrides: Any) -> GenTable:
    fields: Dict[str, Any] = {
        "table_id": 7,
        "table_name": "sys_user",
        "class_name": "SysUser",
        "tpl_category": "crud",
        "package_name": "com.ruoyi.system",
        "module_name": "system",
        "business_name": "user",
        "function_name": "用户",
        "gen_path": "/",
        "columns": [
            GenTableColumn(column_id=11, column_name="user_id", java_field="userId", is_pk="1"),
            GenTableColumn(column_id=12, column_name="user_name", java_field="userName"),
        ],
    }
    fields.update(overrides)
    return GenTable(**fields)


# --------------------------------------------------------------------------- 配置

def test_is_mybatis_plus_is_true(services: _Services) -> None:
    """``generator-code.mybatis-plus.enable: true`` -> 走 ``vmplus/`` 模板."""
    assert services.service._is_mybatis_plus() is True


def test_get_gen_path_root_goes_to_cwd(services: _Services) -> None:
    path = GenTableService.get_gen_path(_crud_table(gen_path="/"), "vmplus/java/domain.java.vm")

    assert path.startswith(service_module.os.getcwd())
    assert f"src{service_module.os.sep}" in path


def test_get_gen_path_custom(services: _Services) -> None:
    path = GenTableService.get_gen_path(
        _crud_table(gen_path="D:/out"), "vmplus/java/domain.java.vm"
    )

    assert path.startswith(f"D:/out{service_module.os.sep}")
    assert not path.startswith(f"D:/out{service_module.os.sep}src")


# --------------------------------------------------------------------------- 三个 init 顺序

def test_preview_code_init_order(services: _Services, monkeypatch: pytest.MonkeyPatch) -> None:
    """filter -> richText -> upload -> dict -> link（Java 原样，不统一）."""
    services.tables.table_by_id = _crud_table()
    order = _stub_init_chain(
        monkeypatch,
        (
            "init_filter_column_info",
            "init_rich_text_info",
            "init_upload_info",
            "dictionary_key_to_camel_case",
            "init_link_table_info",
            "set_sub_table",
            "set_pk_column",
        ),
    )
    stubs = _TemplateStubs(monkeypatch, ["vmplus/java/domain.java.vm", "vmplus/sql/sql.vm"])

    data = services.service.preview_code(7)

    assert order == [
        "init_filter_column_info",
        "init_rich_text_info",
        "init_upload_info",
        "dictionary_key_to_camel_case",
        "init_link_table_info",
        "set_sub_table",
        "set_pk_column",
    ]
    assert services.tables.calls == [("select_gen_table_by_id", (7,))]
    # 键序 = 模板列表序（LinkedHashMap）
    assert list(data) == ["vmplus/java/domain.java.vm", "vmplus/sql/sql.vm"]
    assert data["vmplus/java/domain.java.vm"] == "// vmplus/java/domain.java.vm"
    # 第二个入参来自配置，本项目恒为 True
    assert stubs.list_calls == [("crud", True)]


def test_generator_code_init_order(
    services: _Services, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """dict -> richText -> filter -> link -> upload."""
    services.tables.table_by_name = _crud_table(gen_path=str(tmp_path))
    order = _stub_init_chain(
        monkeypatch,
        (
            "dictionary_key_to_camel_case",
            "init_rich_text_info",
            "init_filter_column_info",
            "init_link_table_info",
            "init_upload_info",
            "set_sub_table",
            "set_pk_column",
        ),
    )
    _TemplateStubs(monkeypatch, ["vmplus/java/domain.java.vm"])
    monkeypatch.setattr(
        service_module, "get_file_name", lambda template, _table: template.replace("/", "_")
    )

    services.service.generator_code("sys_user")

    assert order == [
        "dictionary_key_to_camel_case",
        "init_rich_text_info",
        "init_filter_column_info",
        "init_link_table_info",
        "init_upload_info",
        "set_sub_table",
        "set_pk_column",
    ]
    assert services.tables.calls == [("select_gen_table_by_name", ("sys_user",))]
    assert (tmp_path / "vmplus_java_domain.java.vm").read_text(encoding="utf-8") == (
        "// vmplus/java/domain.java.vm"
    )


def test_generator_code_skips_four_templates_but_keeps_index_form(
    services: _Services, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """``containsAny`` 是**子串**匹配 —— ``index-form.vue.vm`` 不含 ``index.vue.vm``."""
    services.tables.table_by_name = _crud_table(gen_path=str(tmp_path))
    _stub_init_chain(monkeypatch, ("set_pk_column",))
    _TemplateStubs(
        monkeypatch,
        [
            "vmplus/java/domain.java.vm",
            "vmplus/sql/sql.vm",
            "vmplus/js/api.js.vm",
            "vmplus/vue/index.vue.vm",
            "vmplus/vue/index-tree.vue.vm",
            "vmplus/vue/index-form.vue.vm",
        ],
    )
    monkeypatch.setattr(
        service_module, "get_file_name", lambda template, _table: template.replace("/", "_")
    )

    services.service.generator_code("sys_user")

    written = {path.name for path in tmp_path.iterdir()}
    assert written == {"vmplus_java_domain.java.vm", "vmplus_vue_index-form.vue.vm"}


def test_zip_generation_init_order(services: _Services, monkeypatch: pytest.MonkeyPatch) -> None:
    """zip 那条是 dict -> upload -> richText -> link -> filter."""
    services.tables.table_by_name = _crud_table()
    order = _stub_init_chain(
        monkeypatch,
        (
            "dictionary_key_to_camel_case",
            "init_upload_info",
            "init_rich_text_info",
            "init_link_table_info",
            "init_filter_column_info",
            "set_sub_table",
            "set_pk_column",
        ),
    )
    _TemplateStubs(monkeypatch, ["vmplus/java/domain.java.vm", "vmplus/sql/sql.vm"])
    monkeypatch.setattr(
        service_module, "get_file_name", lambda template, _table: template.replace("/", "_")
    )

    payload = services.service.download_code("sys_user")

    assert order == [
        "dictionary_key_to_camel_case",
        "init_upload_info",
        "init_rich_text_info",
        "init_link_table_info",
        "init_filter_column_info",
        "set_sub_table",
        "set_pk_column",
    ]
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert archive.namelist() == ["vmplus_java_domain.java.vm", "vmplus_sql_sql.vm"]


def test_download_code_accepts_array(services: _Services, monkeypatch: pytest.MonkeyPatch) -> None:
    """``downloadCode(String[])`` —— 每张表都进同一个 zip."""
    services.tables.by_name_map = {
        "sys_user": _crud_table(table_name="sys_user"),
        "sys_role": _crud_table(table_name="sys_role", class_name="SysRole"),
    }
    _stub_init_chain(monkeypatch, ("set_pk_column",))
    _TemplateStubs(monkeypatch, ["vmplus/java/domain.java.vm"])
    monkeypatch.setattr(
        service_module,
        "get_file_name",
        lambda template, table: f"{table.table_name}.{template.replace('/', '_')}",
    )

    payload = services.service.download_code(["sys_user", "sys_role"])

    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert archive.namelist() == [
            "sys_user.vmplus_java_domain.java.vm",
            "sys_role.vmplus_java_domain.java.vm",
        ]
    assert [call[1][0] for call in services.tables.calls] == ["sys_user", "sys_role"]


# --------------------------------------------------------------------------- validateEdit

def test_validate_edit_ignores_crud(services: _Services) -> None:
    services.service.validate_edit(GenTable(tpl_category="crud"))


def test_validate_edit_tree_requires_three_fields(services: _Services) -> None:
    with pytest.raises(CustomException) as error:
        services.service.validate_edit(GenTable(tpl_category="tree", params={}))
    assert str(error.value) == "树编码字段不能为空"

    with pytest.raises(CustomException) as error:
        services.service.validate_edit(
            GenTable(tpl_category="tree", params={"treeCode": "dept_id"})
        )
    assert str(error.value) == "树父编码字段不能为空"

    with pytest.raises(CustomException) as error:
        services.service.validate_edit(
            GenTable(
                tpl_category="tree",
                params={"treeCode": "dept_id", "treeParentCode": "parent_id"},
            )
        )
    assert str(error.value) == "树名称字段不能为空"


def test_validate_edit_tree_passes(services: _Services) -> None:
    services.service.validate_edit(
        GenTable(
            tpl_category="tree",
            params={"treeCode": "dept_id", "treeParentCode": "parent_id", "treeName": "dept_name"},
        )
    )


def test_validate_edit_sub_branch_is_dead_code(services: _Services) -> None:
    """``TPL_SUB`` 的两条校验嵌在 ``TPL_TREE`` 里 —— 主子表**从不**校验."""
    services.service.validate_edit(
        GenTable(tpl_category="sub", sub_table_name=None, sub_table_fk_name=None)
    )


# --------------------------------------------------------------------------- importGenTable

def test_import_gen_table_happy_path(
    services: _Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    table = _crud_table(columns=None)
    services.columns.db_columns = [
        GenTableColumn(column_name="user_id"),
        GenTableColumn(column_name="user_name"),
    ]
    init_calls: List[Tuple[str, Any]] = []

    def _init_table(target: GenTable, oper_name: str) -> None:
        init_calls.append(("init_table", oper_name))
        # 故意改名：service 必须在 init 之**前**就把 tableName 取出来
        target.table_name = "MUTATED"

    monkeypatch.setattr(service_module.GenUtils, "init_table", _init_table)
    monkeypatch.setattr(
        service_module.GenUtils,
        "init_column_field",
        lambda column, _table: init_calls.append(("init_column_field", column.column_name)),
    )
    monkeypatch.setattr(service_module, "get_username", lambda: "admin")

    services.service.import_gen_table([table])

    assert init_calls == [
        ("init_table", "admin"),
        ("init_column_field", "user_id"),
        ("init_column_field", "user_name"),
    ]
    assert services.columns.calls[0] == ("select_db_table_columns_by_name", ("sys_user",))
    assert [call[0] for call in services.columns.calls].count("insert_gen_table_column") == 2


def test_import_gen_table_skips_columns_when_insert_fails(
    services: _Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    services.tables.insert_row = 0
    monkeypatch.setattr(service_module.GenUtils, "init_table", lambda *args: None)
    monkeypatch.setattr(service_module, "get_username", lambda: "admin")

    services.service.import_gen_table([_crud_table(columns=None)])

    assert services.columns.calls == []


def test_import_gen_table_wraps_exception(
    services: _Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*_args: Any) -> None:
        raise ValueError("bad table")

    monkeypatch.setattr(service_module.GenUtils, "init_table", _boom)
    monkeypatch.setattr(service_module, "get_username", lambda: "admin")

    with pytest.raises(CustomException) as error:
        services.service.import_gen_table([_crud_table(columns=None)])

    assert str(error.value) == "导入失败：bad table"


def test_import_gen_table_wraps_npe_as_null(
    services: _Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    """NPE 的 ``getMessage()`` 是 null -> ``"导入失败：null"``（不是 Java 类名）."""

    def _boom(*_args: Any) -> None:
        raise AttributeError("java.lang.NullPointerException: column is null")

    monkeypatch.setattr(service_module.GenUtils, "init_table", _boom)
    monkeypatch.setattr(service_module, "get_username", lambda: "admin")

    with pytest.raises(CustomException) as error:
        services.service.import_gen_table([_crud_table(columns=None)])

    assert str(error.value) == "导入失败：null"


def test_java_exception_message_keeps_other_attribute_errors() -> None:
    """非 NPE 哨兵的 ``AttributeError`` 自带 Java 文案，必须原样透出."""
    error = AttributeError("TooManyResultsException: expected one result")

    assert service_module._java_exception_message(error) == (
        "TooManyResultsException: expected one result"
    )


# --------------------------------------------------------------------------- updateGenTable

def test_update_gen_table_serialises_params_into_options(services: _Services) -> None:
    table = _crud_table(params={"treeCode": "dept_id"})

    services.service.update_gen_table(table)

    assert table.options == '{"treeCode":"dept_id"}'
    assert services.tables.calls == [("update_gen_table", (table,))]
    assert [call[0] for call in services.columns.calls] == [
        "update_gen_table_column",
        "update_gen_table_column",
    ]


def test_update_gen_table_empty_params_is_brace_pair(services: _Services) -> None:
    table = _crud_table()

    services.service.update_gen_table(table)

    assert table.options == "{}"


def test_update_gen_table_skips_columns_when_master_row_not_updated(
    services: _Services,
) -> None:
    services.tables.update_row = 0

    services.service.update_gen_table(_crud_table())

    assert services.columns.calls == []


def test_update_gen_table_none_columns_is_npe(services: _Services) -> None:
    services.tables.update_row = 1

    with pytest.raises(TypeError):
        services.service.update_gen_table(_crud_table(columns=None))


def test_delete_gen_table_by_ids_touches_both_mappers(services: _Services) -> None:
    services.service.delete_gen_table_by_ids([3, 5])

    assert services.tables.calls == [("delete_gen_table_by_ids", ((3, 5),))]
    assert services.columns.calls == [("delete_gen_table_column_by_ids", ((3, 5),))]


# --------------------------------------------------------------------------- synchDb

def test_synch_db_inserts_new_and_deletes_missing(services: _Services) -> None:
    table = _crud_table(
        columns=[
            GenTableColumn(column_id=11, column_name="user_id"),
            GenTableColumn(column_id=12, column_name="gone"),
        ]
    )
    services.tables.table_by_name = table
    services.columns.db_columns = [
        GenTableColumn(column_name="user_id"),
        GenTableColumn(column_name="added"),
    ]
    added: List[str] = []

    def _init_column(column: GenTableColumn, _table: GenTable) -> None:
        added.append(column.column_name)

    original = service_module.GenUtils.init_column_field
    service_module.GenUtils.init_column_field = _init_column  # type: ignore[assignment]
    try:
        services.service.synch_db("sys_user")
    finally:
        service_module.GenUtils.init_column_field = original  # type: ignore[assignment]

    assert added == ["added"]
    assert ("select_db_table_columns_by_name", ("sys_user",)) in services.columns.calls
    deletes = [call for call in services.columns.calls if call[0] == "delete_gen_table_columns"]
    assert len(deletes) == 1
    assert [column.column_name for column in deletes[0][1][0]] == ["gone"]


def test_synch_db_missing_table_raises(services: _Services) -> None:
    services.tables.table_by_name = _crud_table(columns=[])
    services.columns.db_columns = []

    with pytest.raises(CustomException) as error:
        services.service.synch_db("sys_user")

    assert str(error.value) == "同步数据失败，原表结构不存在"


def test_synch_db_without_columns_to_delete(services: _Services) -> None:
    table = _crud_table(columns=[GenTableColumn(column_id=11, column_name="user_id")])
    services.tables.table_by_name = table
    services.columns.db_columns = [GenTableColumn(column_name="user_id")]

    services.service.synch_db("sys_user")

    assert [call[0] for call in services.columns.calls] == ["select_db_table_columns_by_name"]


# --------------------------------------------------------------------------- options / 主键

def test_set_table_from_options_fills_tree_fields(services: _Services) -> None:
    table = _crud_table(
        options='{"treeCode":"dept_id","treeParentCode":"parent_id","treeName":"dept_name",'
        '"parentMenuId":"3","parentMenuName":"系统工具"}'
    )

    services.service.set_table_from_options(table)

    assert (table.tree_code, table.tree_parent_code, table.tree_name) == (
        "dept_id",
        "parent_id",
        "dept_name",
    )
    assert (table.parent_menu_id, table.parent_menu_name) == ("3", "系统工具")


def test_set_table_from_options_none_is_noop(services: _Services) -> None:
    table = _crud_table(options=None)

    services.service.set_table_from_options(table)

    assert table.tree_code is None


def test_set_table_from_options_missing_table_is_npe(services: _Services) -> None:
    with pytest.raises(AttributeError):
        services.service.set_table_from_options(None)  # type: ignore[arg-type]


def test_select_gen_table_by_id_missing_is_npe(services: _Services) -> None:
    """``setTableFromOptions`` 在 ``genTable == null`` 时 NPE -> 500."""
    services.tables.table_by_id = None

    with pytest.raises(AttributeError):
        services.service.select_gen_table_by_id(999)


def test_set_pk_column_prefers_flagged_column(services: _Services) -> None:
    table = _crud_table(
        columns=[
            GenTableColumn(column_id=11, java_field="userName"),
            GenTableColumn(column_id=12, java_field="userId", is_pk="1"),
        ]
    )

    services.service.set_pk_column(table)

    assert table.pk_column is table.columns[1]


def test_set_pk_column_falls_back_to_first(services: _Services) -> None:
    table = _crud_table(columns=[GenTableColumn(column_id=11, java_field="userName")])

    services.service.set_pk_column(table)

    assert table.pk_column is table.columns[0]


def test_set_pk_column_empty_columns_is_index_error(services: _Services) -> None:
    """Java 在 ``get(0)`` 处抛 ``IndexOutOfBoundsException``."""
    with pytest.raises(IndexError):
        services.service.set_pk_column(_crud_table(columns=[]))


def test_set_sub_table_only_when_named(services: _Services) -> None:
    services.service.set_sub_table(_crud_table(sub_table_name=None))
    assert services.tables.calls == []

    sub_table = _crud_table()
    services.tables.table_by_name = sub_table
    table = _crud_table(sub_table_name="sys_user")
    services.service.set_sub_table(table)

    assert table.sub_table is sub_table


# --------------------------------------------------------------------------- 列初始化

def test_dictionary_key_to_camel_case(services: _Services) -> None:
    table = _crud_table(
        columns=[
            GenTableColumn(column_id=11, java_field="userId", dict_type="sys_user_sex"),
            GenTableColumn(column_id=12, java_field="userName"),
        ]
    )

    GenTableService.dictionary_key_to_camel_case(table)

    assert table.columns[0].dict_type_camel_case == "sysUserSex"
    assert table.columns[1].dict_type_camel_case is None
    assert table.dictionary_info_string == "sys_user_sex"
    assert table.dictionary_list_key_suffix == service_module.Constants.GENERATE_CODE_DICTIONARY_LIST_KEY_SUFFIX


def test_dictionary_key_to_camel_case_without_dicts(services: _Services) -> None:
    """一个 dictType 都没有时仍要设 suffix —— 模板依赖它."""
    table = _crud_table(columns=[GenTableColumn(column_id=11, java_field="userId")])

    GenTableService.dictionary_key_to_camel_case(table)

    assert table.dictionary_info_list is None
    assert table.dictionary_list_key_suffix is not None


def test_init_filter_column_info(services: _Services) -> None:
    table = _crud_table(
        columns=[
            GenTableColumn(column_id=1, java_field="userId"),
            GenTableColumn(column_id=2, java_field=None),
            GenTableColumn(column_id=3, java_field=""),
            GenTableColumn(column_id=4, java_field="id", java_type="String"),
            GenTableColumn(column_id=5, java_field="sort"),
            GenTableColumn(column_id=6, java_field="epsId"),
            GenTableColumn(column_id=7, java_field="delFlag"),
            GenTableColumn(column_id=8, java_field="tenantId"),
        ]
    )

    GenTableService.init_filter_column_info(table)

    assert [column.java_field for column in table.filter_column_list] == ["userId"]
    assert FILTER_COLUMN_NAME_LIST == ["sort", "epsId", "delFlag", "tenantId"]


def test_init_filter_column_info_id_long_is_kept(services: _Services) -> None:
    """只有 ``id`` **且** ``javaType == String`` 才过滤."""
    table = _crud_table(
        columns=[GenTableColumn(column_id=1, java_field="id", java_type="Long")]
    )

    GenTableService.init_filter_column_info(table)

    assert [column.java_field for column in table.filter_column_list] == ["id"]


def test_init_rich_text_info(services: _Services) -> None:
    table = _crud_table(
        columns=[
            GenTableColumn(column_id=1, java_field="content", html_type="editor"),
            GenTableColumn(column_id=2, java_field="remark", html_type="textarea"),
        ]
    )

    GenTableService.init_rich_text_info(table)

    assert table.rich_text_info.rich_text_count == 1
    assert [column.java_field for column in table.rich_text_info.column_list] == ["content"]


def test_init_rich_text_info_without_editor(services: _Services) -> None:
    table = _crud_table(columns=[GenTableColumn(column_id=1, java_field="remark")])

    GenTableService.init_rich_text_info(table)

    assert table.rich_text_info.rich_text_count == 0
    assert table.rich_text_info.column_list is None


def test_init_upload_info_joins_field_names(services: _Services) -> None:
    table = _crud_table(
        columns=[
            GenTableColumn(column_id=1, java_field="fileA", html_type="fileUpload"),
            GenTableColumn(column_id=2, java_field="fileB", html_type="fileUpload"),
        ]
    )

    GenTableService.init_upload_info(table)

    assert table.upload_info.upload_count == 2
    assert table.upload_info.upload_filed_names == "fileA,fileB"


def test_init_upload_info_without_files(services: _Services) -> None:
    table = _crud_table(columns=[GenTableColumn(column_id=1, java_field="remark")])

    GenTableService.init_upload_info(table)

    assert table.upload_info.upload_count == 0
    assert table.upload_info.upload_filed_names is None


def test_init_link_table_info_missing_link_table_is_npe(services: _Services) -> None:
    """``linkTable`` 查不到时 ``setPkColumn(null)`` 直接 NPE -> 500."""
    table = _crud_table(
        columns=[
            GenTableColumn(
                column_id=11,
                java_field="userId",
                link_table_id=8,
                field_map_string='[{"fieldType":"10","currentTableFileId":11}]',
            )
        ]
    )
    services.tables.table_by_id = None

    with pytest.raises(AttributeError):
        services.service.init_link_table_info(table)


def test_init_link_table_info_requires_major_mapping(services: _Services) -> None:
    """关联列在 ``fieldMapString`` 里找不到自己 -> ``findFirst().get()`` 抛 NoSuchElement."""
    table = _crud_table(
        columns=[
            GenTableColumn(
                column_id=11,
                java_field="userId",
                link_table_id=8,
                field_map_string='[{"fieldType":"10","currentTableFileId":999}]',
            )
        ]
    )
    services.tables.table_by_id = _crud_table(
        columns=[GenTableColumn(column_id=1, java_field="id", is_pk="1")]
    )

    with pytest.raises(LookupError):
        services.service.init_link_table_info(table)
