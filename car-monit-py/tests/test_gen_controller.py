"""``GenController`` -- ``/tool/gen`` 的 15 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java

这一层测什么
------------
Service 的 SQL 与模板渲染分别由 ``test_gen_table_mapper.py`` /
``test_gen_table_service.py`` 覆盖，这里全部注入假 Service，只测**控制器自己的约定**：

* 15 个映射全部注册，且 ``GET /{talbleId}`` 排在**最后**（否则会吃掉
  ``/list`` / ``/all/list`` / ``/db/list`` / ``/batchGenCode`` 这些单段字面量路由）；
* 12 个映射带 ``@PreAuthorize``，``all/list`` / ``getColumnList`` /
  ``getAllColumnList`` **没有**（登录即可）;
* ``columnList`` 的路径变量是死的（Java 没有 ``@PathVariable``），真正的 ``tableId``
  从 query 取；响应用手工构造的 ``TableDataInfo`` -> ``code = 0``、``msg = null``；
* ``importTable`` / ``batchGenCode`` 缺 ``tables`` -> Java 的 ``{"msg":null,"code":500}``，
  P1-6 起非业务异常改为统一脱敏文案；
* ``PUT`` 的 8 条 ``@NotBlank`` + ``columns`` 上的 ``@Valid`` 级联；
* 两个下载端点的 zip 响应头（文件名写死 ``ruoyi.zip``）；
* ``getInfo`` 的 ``data`` 键序是 ``HashMap`` 桶序：``tables`` / ``rows`` / ``info``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.tool import gen_controller as controller
from app.api.tool.gen_controller import (
    CHAR_COMMA,
    ZIP_CONTENT_DISPOSITION,
    ZIP_CONTENT_TYPE,
    batch_gen_code,
    column_list,
    data_list,
    download,
    edit_save,
    gen_code,
    gen_list,
    get_all_column_list,
    get_all_generate_table_list,
    get_column_list,
    get_info,
    import_table_save,
    preview,
    remove,
    synch_db,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException, CustomException
from app.config.exception_handlers import GENERIC_ERROR_MESSAGE, register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.generator.domain.gen_table import GenTable
from app.generator.domain.gen_table_column import GenTableColumn

#: 能通过 8 条 ``@NotBlank`` 的请求体。
VALID_BODY: Dict[str, Any] = {
    "tableId": 1,
    "tableName": "gen_test",
    "tableComment": "代码生成测试表",
    "className": "GenTest",
    "tplCategory": "crud",
    "packageName": "com.ruoyi.system",
    "moduleName": "system",
    "businessName": "gentest",
    "functionName": "代码生成测试",
    "functionAuthor": "ruoyi",
}


# --------------------------------------------------------------------------- fakes


class _FakeTableService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[GenTable] = []
        self.db_list_result: List[GenTable] = []
        self.by_names_result: List[GenTable] = []
        self.all_result: List[GenTable] = []
        self.by_id_result: Optional[GenTable] = None
        self.preview_result: Dict[str, str] = {}
        self.download_result: bytes = b"PK\x05\x06" + b"\x00" * 18
        self.page_taken: Any = None
        #: 打开后 ``import_gen_table`` 直接抛（复刻 ``导入失败：`` 包装）。
        self.import_exception: Optional[Exception] = None

    def select_gen_table_list(self, query: GenTable) -> List[GenTable]:
        self.calls.append(("select_gen_table_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_db_table_list(self, query: GenTable) -> List[GenTable]:
        self.calls.append(("select_db_table_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.db_list_result

    def select_db_table_list_by_names(self, table_names: Sequence[str]) -> List[GenTable]:
        self.calls.append(("select_db_table_list_by_names", list(table_names)))
        return self.by_names_result

    def select_gen_table_all(self) -> List[GenTable]:
        self.calls.append(("select_gen_table_all",))
        return self.all_result

    def select_gen_table_by_id(self, table_id: Optional[int]) -> Optional[GenTable]:
        self.calls.append(("select_gen_table_by_id", table_id))
        return self.by_id_result

    def import_gen_table(self, table_list: Sequence[GenTable]) -> None:
        self.calls.append(("import_gen_table", list(table_list)))
        if self.import_exception is not None:
            raise self.import_exception

    def validate_edit(self, gen_table: GenTable) -> None:
        self.calls.append(("validate_edit", gen_table.model_copy(deep=True)))

    def update_gen_table(self, gen_table: GenTable) -> None:
        self.calls.append(("update_gen_table", gen_table.model_copy(deep=True)))

    def delete_gen_table_by_ids(self, table_ids: Sequence[int]) -> None:
        self.calls.append(("delete_gen_table_by_ids", list(table_ids)))

    def preview_code(self, table_id: Optional[int]) -> Dict[str, str]:
        self.calls.append(("preview_code", table_id))
        return self.preview_result

    def download_code(self, table_names: Any) -> bytes:
        self.calls.append(("download_code", table_names))
        return self.download_result

    def generator_code(self, table_name: str) -> None:
        self.calls.append(("generator_code", table_name))

    def synch_db(self, table_name: str) -> None:
        self.calls.append(("synch_db", table_name))

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakeColumnService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.by_table_result: List[GenTableColumn] = []
        self.by_ids_result: Dict[str, Optional[List[GenTableColumn]]] = {}
        self.list_result: List[GenTableColumn] = []
        self.page_taken: Any = None

    def select_gen_table_column_list_by_table_id(
        self, table_id: Optional[int]
    ) -> List[GenTableColumn]:
        self.calls.append(("select_gen_table_column_list_by_table_id", table_id))
        return self.by_table_result

    def select_gen_table_column_list_by_table_column_ids(
        self, table_column_ids: Optional[str]
    ) -> Optional[List[GenTableColumn]]:
        self.calls.append(("select_gen_table_column_list_by_table_column_ids", table_column_ids))
        return self.by_ids_result.get(str(table_column_ids))

    def select_gen_table_column_list(
        self, query: GenTableColumn
    ) -> List[GenTableColumn]:
        self.calls.append(("select_gen_table_column_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def services(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    tables = _FakeTableService()
    columns = _FakeColumnService()
    monkeypatch.setattr(controller, "_TABLE_SERVICE", tables)
    monkeypatch.setattr(controller, "_COLUMN_SERVICE", columns)
    yield tables, columns
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_gen_controller()


@pytest.fixture
def table_service(services: Any) -> _FakeTableService:
    return services[0]


@pytest.fixture
def column_service(services: Any) -> _FakeColumnService:
    return services[1]


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    return TestClient(_build_app(login=False))


@pytest.fixture
def http_lenient() -> Any:
    """已登录、且**不把服务端异常当失败**的 mini app（见 ``test_sys_config_controller``）。"""
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            authenticate()
            return await call_next(request)

    application.include_router(controller.router)
    return application


def authenticate(
    user_id: int = 2, user_name: str = "ry", permissions: Optional[set] = None
) -> SysUser:
    user = SysUser(user_id=user_id, user_name=user_name)
    login_user = LoginUser(user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _table(table_id: int = 1, table_name: str = "gen_test") -> GenTable:
    return GenTable(
        table_id=table_id,
        table_name=table_name,
        table_comment="代码生成测试表",
        class_name="GenTest",
        tpl_category="crud",
        package_name="com.ruoyi.system",
        module_name="system",
        business_name="gentest",
        function_name="代码生成测试",
        function_author="ruoyi",
    )


def _column(
    column_id: int = 11,
    column_name: str = "column_id",
    dialog_search_column_ids: Optional[str] = None,
    dialog_list_column_ids: Optional[str] = None,
) -> GenTableColumn:
    return GenTableColumn(
        column_id=column_id,
        table_id=1,
        column_name=column_name,
        java_field="columnId",
        dialog_search_column_ids=dialog_search_column_ids,
        dialog_list_column_ids=dialog_list_column_ids,
    )


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_fifteen_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/tool/gen/list", ("GET",)),
            ("/tool/gen/all/list", ("GET",)),
            ("/tool/gen/db/list", ("GET",)),
            ("/tool/gen/column/{talble_id}", ("GET",)),
            ("/tool/gen/getColumnList", ("POST",)),
            ("/tool/gen/getAllColumnList", ("POST",)),
            ("/tool/gen/importTable", ("POST",)),
            ("/tool/gen", ("PUT",)),
            ("/tool/gen/{table_ids}", ("DELETE",)),
            ("/tool/gen/preview/{table_id}", ("GET",)),
            ("/tool/gen/download/{table_name}", ("GET",)),
            ("/tool/gen/genCode/{table_name}", ("GET",)),
            ("/tool/gen/synchDb/{table_name}", ("GET",)),
            ("/tool/gen/batchGenCode", ("GET",)),
            ("/tool/gen/{talble_id}", ("GET",)),
        }

    def test_the_detail_route_is_registered_last(self) -> None:
        """``/{talbleId}`` 排前面会把 ``/list`` 当成 id（int 转换失败 -> 500）。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/tool/gen/{talble_id}") == len(paths) - 1
        for literal in ("/tool/gen/list", "/tool/gen/all/list", "/tool/gen/db/list"):
            assert paths.index(literal) < paths.index("/tool/gen/{talble_id}")

    def test_the_literal_routes_beat_the_path_variable_over_http(
        self, http: TestClient
    ) -> None:
        assert http.get("/tool/gen/list").json().keys() == {"total", "rows", "code", "msg"}
        assert http.get("/tool/gen/all/list").json()["code"] == 200
        assert http.get("/tool/gen/db/list").json().keys() == {"total", "rows", "code", "msg"}

    def test_batch_gen_code_is_not_swallowed_by_the_detail_route(
        self, http: TestClient, table_service: _FakeTableService
    ) -> None:
        """``GET /batchGenCode?tables=a`` 若落到 ``/{talbleId}`` 会 int 转换失败。"""
        response = http.get("/tool/gen/batchGenCode", params={"tables": "gen_test"})

        assert response.status_code == 200
        assert table_service.of("download_code") == [("download_code", ["gen_test"])]


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: gen_list(GenTable()),
            lambda: data_list(GenTable()),
            lambda: column_list("1", 1),
            lambda: import_table_save("gen_test"),
            lambda: edit_save(_table()),
            lambda: remove("1"),
            lambda: preview(1),
            lambda: download("gen_test"),
            lambda: gen_code("gen_test"),
            lambda: synch_db("gen_test"),
            lambda: batch_gen_code("gen_test"),
            lambda: get_info(1),
        ],
    )
    def test_the_twelve_guarded_endpoints(self, services: Any, call: Any) -> None:
        tables, columns = services

        with pytest.raises(AccessDeniedException):
            call()

        assert tables.calls == []
        assert columns.calls == []

    def test_the_three_unguarded_endpoints(self, table_service: Any, column_service: Any) -> None:
        """这三条源码上就没有 ``@PreAuthorize`` —— 登录即可。"""
        assert get_all_generate_table_list(GenTable())["code"] == 200
        assert get_column_list(GenTableColumn()).code == 200
        assert get_all_column_list(GenTableColumn())["code"] == 200

        assert table_service.of("select_gen_table_list") != []
        assert column_service.of("select_gen_table_column_list") != []

    def test_a_partial_permission_does_not_pass(self) -> None:
        authenticate(permissions={"tool:gen:*"})

        with pytest.raises(AccessDeniedException):
            preview(1)

    def test_an_access_denied_becomes_http_200_code_403(
        self, http_anonymous: TestClient
    ) -> None:
        response = http_anonymous.get("/tool/gen/preview/1")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}


# --------------------------------------------------------------------------- list


class TestList:
    def test_list_starts_the_page(self, http: TestClient, table_service: Any) -> None:
        http.get("/tool/gen/list")

        # 分页参数走 RequestContextMiddleware（见 ``get_page_params``），mini app 里没有，
        # 所以只能断言"页面已开启 + 采用默认值"。
        page = table_service.page_taken
        assert page is not None
        assert page.get_page_num() == 1
        assert page.get_page_size() == 10

    def test_list_returns_the_paging_envelope(self, http: TestClient, table_service: Any) -> None:
        table_service.list_result = [_table()]

        body = http.get("/tool/gen/list").json()

        assert body["total"] == 1
        assert body["code"] == 200
        assert body["msg"] == "查询成功"

    def test_the_query_is_bound_from_the_query_string(
        self, http: TestClient, table_service: Any
    ) -> None:
        http.get("/tool/gen/list", params={"tableName": "gen_test", "tableComment": "测试"})

        query = table_service.of("select_gen_table_list")[0][1]
        assert (query.table_name, query.table_comment) == ("gen_test", "测试")

    def test_the_rows_carry_the_derived_keys(
        self, http: TestClient, table_service: Any
    ) -> None:
        """``sub`` / ``tree`` / ``crud`` 是 Jackson 派生属性，必须出现。"""
        table_service.list_result = [_table()]

        row = http.get("/tool/gen/list").json()["rows"][0]

        assert row["sub"] is False
        assert row["tree"] is False
        assert row["crud"] is True

    def test_all_list_does_not_page_and_has_no_permission(
        self, http: TestClient, table_service: Any
    ) -> None:
        table_service.list_result = [_table()]

        body = http.get("/tool/gen/all/list").json()

        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert body["data"] == [_table().to_json_dict()]
        assert table_service.page_taken is None

    def test_db_list_uses_the_info_schema_query(
        self, http: TestClient, table_service: Any
    ) -> None:
        table_service.db_list_result = [GenTable(table_name="biz_table")]

        body = http.get("/tool/gen/db/list").json()

        assert body["total"] == 1
        assert body["code"] == 200
        assert table_service.of("select_db_table_list") != []


# --------------------------------------------------------------------------- columnList


class TestColumnList:
    def test_the_envelope_is_hand_made(self, http: TestClient, column_service: Any) -> None:
        """``code`` 是 ``0``、``msg`` 是 ``null``（没走 ``getDataTable``）。"""
        column_service.by_table_result = [_column(), _column(column_id=12, column_name="sort")]

        body = http.get("/tool/gen/column/1", params={"tableId": 1}).json()

        assert list(body.keys()) == ["total", "rows", "code", "msg"]
        assert body["total"] == 2
        assert body["code"] == 0
        assert body["msg"] is None

    def test_the_table_id_comes_from_the_query_string(
        self, http: TestClient, column_service: Any
    ) -> None:
        """Java 的路径变量没有 ``@PathVariable``，只有 query 上的 ``tableId`` 生效。"""
        http.get("/tool/gen/column/999", params={"tableId": 7})

        assert column_service.of("select_gen_table_column_list_by_table_id") == [
            ("select_gen_table_column_list_by_table_id", 7)
        ]

    def test_the_path_variable_is_never_parsed_as_a_number(
        self, http: TestClient, column_service: Any
    ) -> None:
        """``/column/anything`` 也能进（Java 不做 ``Long`` 转换也不会 404）。"""
        response = http.get("/tool/gen/column/anything")

        assert response.status_code == 200
        assert response.json()["rows"] == []
        assert column_service.of("select_gen_table_column_list_by_table_id") == [
            ("select_gen_table_column_list_by_table_id", None)
        ]

    def test_an_empty_result_is_an_empty_array_not_null(
        self, http: TestClient, column_service: Any
    ) -> None:
        """``setRows(list)`` 里 ``list`` 永远不是 ``null``（mapper 返回空集合）。"""
        body = http.get("/tool/gen/column/1", params={"tableId": 1}).json()

        assert body["rows"] == []
        assert body["total"] == 0


# --------------------------------------------------------------------------- getColumnList


class TestColumnListByBody:
    def test_get_column_list_pages(self, http: TestClient, column_service: Any) -> None:
        response = http.post(
            "/tool/gen/getColumnList",
            params={"pageNum": "1", "pageSize": "10"},
            json={"tableId": 1},
        )

        body = response.json()
        assert body.keys() == {"total", "rows", "code", "msg"}
        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        assert column_service.page_taken is not None

    def test_the_body_is_bound_to_the_entity(
        self, http: TestClient, column_service: Any
    ) -> None:
        http.post("/tool/gen/getColumnList", json={"tableId": 1, "columnName": "sort"})

        query = column_service.of("select_gen_table_column_list")[0][1]
        assert query.table_id == 1
        assert query.column_name == "sort"

    def test_get_all_column_list_does_not_page(
        self, http: TestClient, column_service: Any
    ) -> None:
        column_service.list_result = [_column()]

        body = http.post("/tool/gen/getAllColumnList", json={"tableId": 1}).json()

        assert body["code"] == 200
        assert len(body["data"]) == 1
        assert column_service.page_taken is None


# --------------------------------------------------------------------------- getInfo


class TestGetInfo:
    def test_the_data_key_order_is_the_hash_map_bucket_order(
        self, http: TestClient, table_service: Any
    ) -> None:
        """``HashMap`` 桶位 ``tables``=2 < ``rows``=12 < ``info``=15 —— 照抄。"""
        table_service.by_id_result = _table()

        body = http.get("/tool/gen/1").json()

        # AjaxResult 是 HashMap 子类 —— msg(桶 0) -> code(桶 3) -> data(桶 4)
        assert list(body.keys()) == ["msg", "code", "data"]
        assert list(body["data"].keys()) == ["tables", "rows", "info"]

    def test_all_three_parts_are_filled(
        self, http: TestClient, table_service: Any, column_service: Any
    ) -> None:
        table_service.by_id_result = _table()
        table_service.all_result = [_table(), _table(table_id=2, table_name="other")]
        column_service.by_table_result = [_column()]

        data = http.get("/tool/gen/1").json()["data"]

        assert data["info"]["tableName"] == "gen_test"
        assert len(data["rows"]) == 1
        assert len(data["tables"]) == 2

    def test_the_dialog_names_are_joined_with_commas(
        self, http: TestClient, table_service: Any, column_service: Any
    ) -> None:
        column_service.by_table_result = [
            _column(dialog_search_column_ids="11,12", dialog_list_column_ids="13")
        ]
        column_service.by_ids_result = {
            "11,12": [_column(11, "a"), _column(12, "b")],
            "13": [_column(13, "c")],
        }

        row = http.get("/tool/gen/1").json()["data"]["rows"][0]

        assert row["dialogSearchColumnNames"] == "a" + CHAR_COMMA + "b"
        assert row["dialogListColumnNames"] == "c"

    def test_an_empty_lookup_leaves_the_names_null(
        self, http: TestClient, table_service: Any, column_service: Any
    ) -> None:
        """``CollectionUtils.isNotEmpty(columnList)`` 为假时**不**覆盖 —— 键保持 ``null``。"""
        column_service.by_table_result = [_column(dialog_search_column_ids="11,12")]
        column_service.by_ids_result = {"11,12": []}

        row = http.get("/tool/gen/1").json()["data"]["rows"][0]

        assert row["dialogSearchColumnNames"] is None

    def test_a_null_id_list_skips_the_lookup(
        self, http: TestClient, table_service: Any, column_service: Any
    ) -> None:
        column_service.by_table_result = [_column()]

        http.get("/tool/gen/1")

        assert column_service.of("select_gen_table_column_list_by_table_column_ids") == []

    def test_a_non_numeric_id_is_an_http_200_code_500(self, http: TestClient) -> None:
        response = http.get("/tool/gen/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- importTable


class TestImportTable:
    def test_the_names_are_split_on_commas(
        self, http: TestClient, table_service: Any
    ) -> None:
        table_service.by_names_result = [_table()]

        response = http.post("/tool/gen/importTable", params={"tables": "a,b"})

        assert response.json() == {"code": 200, "msg": "操作成功"}
        assert table_service.of("select_db_table_list_by_names") == [
            ("select_db_table_list_by_names", ["a", "b"])
        ]
        assert len(table_service.of("import_gen_table")) == 1

    def test_a_single_name_is_a_one_element_array(
        self, http: TestClient, table_service: Any
    ) -> None:
        http.post("/tool/gen/importTable", params={"tables": "gen_test"})

        assert table_service.of("select_db_table_list_by_names") == [
            ("select_db_table_list_by_names", ["gen_test"])
        ]

    def test_a_trailing_comma_is_dropped(
        self, http: TestClient, table_service: Any
    ) -> None:
        """Java ``String#split`` 丢弃尾部空串。"""
        http.post("/tool/gen/importTable", params={"tables": "a,b,"})

        assert table_service.of("select_db_table_list_by_names") == [
            ("select_db_table_list_by_names", ["a", "b"])
        ]

    def test_a_missing_tables_parameter_is_an_npe(
        self, http_lenient: TestClient, table_service: Any
    ) -> None:
        """``Convert.toStrArray(null)`` -> NPE -> ``{"msg":null,"code":500}``。"""
        response = http_lenient.post("/tool/gen/importTable")

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": GENERIC_ERROR_MESSAGE}
        assert table_service.of("select_db_table_list_by_names") == []

    def test_an_import_failure_keeps_the_custom_message(
        self, http_lenient: TestClient, table_service: Any
    ) -> None:
        table_service.by_names_result = [_table()]
        table_service.import_exception = CustomException("导入失败：表已存在")

        response = http_lenient.post("/tool/gen/importTable", params={"tables": "a"})

        assert response.json() == {"code": 500, "msg": "导入失败：表已存在"}


# --------------------------------------------------------------------------- 修改


class TestEditSave:
    def test_validation_edit_runs_before_the_update(
        self, table_service: Any
    ) -> None:
        authenticate()

        assert edit_save(_table()) == {"code": 200, "msg": "操作成功"}
        assert [call[0] for call in table_service.calls] == ["validate_edit", "update_gen_table"]

    def test_the_body_is_bound_from_json(self, http: TestClient, table_service: Any) -> None:
        response = http.put("/tool/gen", json=VALID_BODY)

        assert response.json() == {"code": 200, "msg": "操作成功"}
        stored = table_service.of("update_gen_table")[0][1]
        assert stored.table_name == "gen_test"
        assert stored.function_author == "ruoyi"

    def test_columns_are_cascaded(self, http: TestClient, table_service: Any) -> None:
        body = dict(VALID_BODY)
        body["columns"] = [
            {"columnId": 11, "columnName": "a", "javaField": "a"},
            {"columnId": 12, "columnName": "b", "javaField": "b"},
        ]

        http.put("/tool/gen", json=body)

        stored = table_service.of("update_gen_table")[0][1]
        assert [column.java_field for column in stored.columns or []] == ["a", "b"]


class TestValidation:
    @pytest.mark.parametrize(
        "field, message",
        [
            ("tableName", "表名称不能为空"),
            ("tableComment", "表描述不能为空"),
            ("className", "实体类名称不能为空"),
            ("packageName", "生成包路径不能为空"),
            ("moduleName", "生成模块名不能为空"),
            ("businessName", "生成业务名不能为空"),
            ("functionName", "生成功能名不能为空"),
            ("functionAuthor", "作者不能为空"),
        ],
    )
    def test_the_eight_not_blank_constraints(
        self, http: TestClient, table_service: Any, field: str, message: str
    ) -> None:
        body = dict(VALID_BODY)
        body.pop(field)

        response = http.put("/tool/gen", json=body)

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": message}
        assert table_service.of("update_gen_table") == []

    def test_the_first_missing_field_wins(self, http: TestClient) -> None:
        """约束按源码声明序检查，``tableName`` 在最前。"""
        response = http.put("/tool/gen", json={})

        assert response.json()["msg"] == "表名称不能为空"

    def test_a_blank_value_is_rejected_too(self, http: TestClient) -> None:
        body = dict(VALID_BODY)
        body["tableName"] = "   "

        assert http.put("/tool/gen", json=body).json()["msg"] == "表名称不能为空"

    def test_a_cascaded_java_field_is_required(self, http: TestClient, table_service: Any) -> None:
        """``GenTable.columns`` 上的 ``@Valid`` —— 任意一列缺 ``javaField`` 就拒。"""
        body = dict(VALID_BODY)
        body["columns"] = [{"columnId": 11, "columnName": "a"}]

        response = http.put("/tool/gen", json=body)

        assert response.json() == {"code": 500, "msg": "Java属性不能为空"}
        assert table_service.of("update_gen_table") == []

    def test_validation_runs_before_the_permission_check(
        self, http_anonymous: TestClient
    ) -> None:
        """Spring MVC 先解析/校验参数，再进方法代理（``@PreAuthorize``）。"""
        response = http_anonymous.put("/tool/gen", json={})

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "表名称不能为空"}


# --------------------------------------------------------------------------- 删除


class TestRemove:
    def test_the_id_list_is_split_on_commas(self, table_service: Any) -> None:
        authenticate()

        assert remove("1,2,3") == {"code": 200, "msg": "操作成功"}
        assert table_service.of("delete_gen_table_by_ids") == [
            ("delete_gen_table_by_ids", [1, 2, 3])
        ]

    def test_a_non_numeric_id_is_an_http_200_code_500(
        self, http_lenient: TestClient, table_service: Any
    ) -> None:
        response = http_lenient.delete("/tool/gen/1,abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500
        assert table_service.of("delete_gen_table_by_ids") == []


# --------------------------------------------------------------------------- 预览 / 生成


class TestPreview:
    def test_the_template_map_is_returned_verbatim(self, table_service: Any) -> None:
        authenticate()
        table_service.preview_result = {
            "vmplus/java/domain.java.vm": "package com.ruoyi;\n",
            "vmplus/java/mapper.java.vm": "package com.ruoyi;\n",
        }

        response = preview(1)

        assert response["code"] == 200
        assert list(response["data"].keys()) == [
            "vmplus/java/domain.java.vm",
            "vmplus/java/mapper.java.vm",
        ]

    def test_the_key_order_follows_the_template_list(
        self, http: TestClient, table_service: Any
    ) -> None:
        table_service.preview_result = {
            "vmplus/sql/sql.vm": "a",
            "vmplus/java/domain.java.vm": "b",
        }

        data = http.get("/tool/gen/preview/1").json()["data"]

        assert list(data.keys()) == ["vmplus/sql/sql.vm", "vmplus/java/domain.java.vm"]


class TestDownload:
    def test_the_zip_headers_match_java(self, http: TestClient, table_service: Any) -> None:
        response = http.get("/tool/gen/download/gen_test")

        assert response.status_code == 200
        assert response.headers["content-type"] == ZIP_CONTENT_TYPE
        assert response.headers["content-disposition"] == ZIP_CONTENT_DISPOSITION
        assert response.headers["access-control-expose-headers"] == "Content-Disposition"
        assert response.headers["content-length"] == str(len(table_service.download_result))
        assert response.content == table_service.download_result

    def test_the_filename_is_hard_coded(self) -> None:
        assert ZIP_CONTENT_DISPOSITION == 'attachment; filename="ruoyi.zip"'

    def test_one_table_name_is_passed_through(self, table_service: Any) -> None:
        authenticate()

        download("gen_test")

        assert table_service.of("download_code") == [("download_code", "gen_test")]

    def test_batch_passes_the_array(self, table_service: Any) -> None:
        authenticate()

        batch_gen_code("a,b")

        assert table_service.of("download_code") == [("download_code", ["a", "b"])]

    def test_batch_without_tables_is_an_npe(self, http_lenient: TestClient) -> None:
        """NPE 发生在写响应头**之前** —— 客户端拿到的是 JSON 错误信封。"""
        response = http_lenient.get("/tool/gen/batchGenCode")

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": GENERIC_ERROR_MESSAGE}
        assert "content-disposition" not in response.headers


class TestGenCode:
    def test_generate_to_the_custom_path(self, table_service: Any) -> None:
        authenticate()

        assert gen_code("gen_test") == {"code": 200, "msg": "操作成功"}
        assert table_service.of("generator_code") == [("generator_code", "gen_test")]

    def test_synch_db(self, table_service: Any) -> None:
        authenticate()

        assert synch_db("gen_test") == {"code": 200, "msg": "操作成功"}
        assert table_service.of("synch_db") == [("synch_db", "gen_test")]

    def test_an_error_is_an_http_200_code_500(
        self, http_lenient: TestClient, table_service: Any
    ) -> None:
        table_service.download_result = b""
        table_service.generator_code = _raise(CustomException("模板不存在"))  # type: ignore[method-assign]

        response = http_lenient.get("/tool/gen/genCode/gen_test")

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "模板不存在"}


def _raise(error: Exception) -> Any:
    def _raiser(*_: Any, **__: Any) -> None:
        raise error

    return _raiser
