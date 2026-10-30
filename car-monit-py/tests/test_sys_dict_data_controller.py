"""``SysDictDataController`` -- ``/system/dict/data`` 的 8 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysDictDataController.java

这一层测什么
------------
Service 已被 ``test_sys_dict_data_service.py`` 覆盖，只测**控制器自己的约定**：

* 8 个映射全部注册（``export`` 在 Phase 3.18 补上，返回文件名）；
* ``/type/{dictType}`` 与 ``/typemore/{dictType}`` **没有**权限点 —— 前端每个页面都
  调它们，加权限会白屏；其余 5 个都有；
* ``/type`` 与 ``/typemore`` 委托给 **``SysDictTypeService``**（不是 DataService）——
  Java 就是这个交叉依赖；
* ``null`` 变空数组：未命中时返回 ``"data": []`` 而**不是** ``"data": null``，也不是
  ``AjaxResult.success(null)`` 那样整个 ``data`` 键消失；
* ``/typemore`` 额外按 ``dictType`` 分组。

``/type/{dictType}`` 与 ``/{dictCode}`` 的冲突
---------------------------------------------
前者是两段、后者是一段，不会互相吃掉。但仍按"字面量在前"的规则注册，与
``sys_notice_controller`` 的 ``/view/{id}`` 处理方式一致。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_dict_data_controller as controller
from app.api.system.sys_dict_data_controller import (
    add,
    dict_type,
    dict_type_more,
    edit,
    get_info,
    list_dict_data,
    remove,
)
from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

#: 一个能通过 ``@Validated`` 的请求体。
VALID_BODY: Dict[str, Any] = {
    "dictLabel": "男",
    "dictValue": "0",
    "dictType": "sys_user_sex",
    "dictSort": 1,
    "status": "0",
}


# --------------------------------------------------------------------------- fakes


class _FakeDictDataService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysDictData] = []
        self.by_id_result: Optional[SysDictData] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.page_taken: Any = None

    def select_dict_data_list(self, query: SysDictData) -> List[SysDictData]:
        self.calls.append(("select_dict_data_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_dict_data_by_id(self, dict_code: int) -> Optional[SysDictData]:
        self.calls.append(("select_dict_data_by_id", dict_code))
        return self.by_id_result

    def insert_dict_data(self, entity: SysDictData) -> int:
        self.calls.append(("insert_dict_data", entity.model_copy(deep=True)))
        return self.insert_result

    def update_dict_data(self, entity: SysDictData) -> int:
        self.calls.append(("update_dict_data", entity.model_copy(deep=True)))
        return self.update_result

    def delete_dict_data_by_ids(self, dict_codes: Sequence[int]) -> int:
        self.calls.append(("delete_dict_data_by_ids", list(dict_codes)))
        return self.delete_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakeDictTypeService:
    """``/type`` 与 ``/typemore`` 的**真实**协作者（Java 注入的是 TypeService）。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.by_type_result: Optional[List[SysDictData]] = None
        self.by_type_more_result: Optional[List[SysDictData]] = None

    def select_dict_data_by_type(self, dict_type: Optional[str]) -> Optional[List[SysDictData]]:
        self.calls.append(("select_dict_data_by_type", dict_type))
        return self.by_type_result

    def select_dict_data_by_type_more(self, dict_types: Optional[str]) -> Optional[List[SysDictData]]:
        self.calls.append(("select_dict_data_by_type_more", dict_types))
        return self.by_type_more_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def services(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    data_fake = _FakeDictDataService()
    type_fake = _FakeDictTypeService()
    monkeypatch.setattr(controller, "_DICT_DATA_SERVICE", data_fake)
    monkeypatch.setattr(controller, "_DICT_TYPE_SERVICE", type_fake)
    yield data_fake, type_fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_dict_data_controller()


@pytest.fixture
def data_service(services: Any) -> _FakeDictDataService:
    return services[0]


@pytest.fixture
def type_service(services: Any) -> _FakeDictTypeService:
    return services[1]


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    return TestClient(_build_app(login=False))


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(
                    LoginUser(user=SysUser(user_id=2, user_name="ry"), permissions={"*:*:*"}),
                    None,
                    [],
                )
            )
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


def _item(value: str, label: str, dict_type: str = "sys_user_sex", dict_code: int = 1) -> SysDictData:
    return SysDictData(dict_code=dict_code, dict_value=value, dict_label=label, dict_type=dict_type)


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_eight_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/dict/data/list", ("GET",)),
            ("/system/dict/data/export", ("GET",)),
            ("/system/dict/data/type/{dict_type}", ("GET",)),
            ("/system/dict/data/typemore/{dict_type}", ("GET",)),
            ("/system/dict/data/{dict_code}", ("GET",)),
            ("/system/dict/data", ("POST",)),
            ("/system/dict/data", ("PUT",)),
            ("/system/dict/data/{dict_codes}", ("DELETE",)),
        }

    def test_export_comes_before_the_path_variable(self) -> None:
        """``/export`` 排在 ``/{dict_code}`` 后面的话 ``"export"`` 会转 int 失败。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/dict/data/export") < paths.index(
            "/system/dict/data/{dict_code}"
        )

    def test_literal_paths_come_before_the_path_variable(self) -> None:
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/dict/data/list") < paths.index("/system/dict/data/{dict_code}")
        assert paths.index("/system/dict/data/type/{dict_type}") < paths.index(
            "/system/dict/data/{dict_code}"
        )
        assert paths.index("/system/dict/data/typemore/{dict_type}") < paths.index(
            "/system/dict/data/{dict_code}"
        )

    def test_the_list_beats_the_path_variable_over_http(self, http: TestClient) -> None:
        response = http.get("/system/dict/data/list")

        assert response.json().keys() == {"total", "rows", "code", "msg"}

    def test_type_is_its_own_two_segment_route(self, http: TestClient, type_service: Any) -> None:
        type_service.by_type_result = [_item("0", "男")]

        response = http.get("/system/dict/data/type/sys_user_sex")

        assert response.json()["data"][0]["dictLabel"] == "男"
        assert type_service.of("select_dict_data_by_type") == [
            ("select_dict_data_by_type", "sys_user_sex")
        ]

    def test_export_does_not_fall_into_the_path_variable(
        self, http: TestClient, data_service: Any
    ) -> None:
        """``GET /system/dict/data/export`` 现在有自己的路由，不再被 ``/{dictCode}`` 兜住.

        Phase 3.18 之前这里回的是 HTTP 200 + ``code 500``（``"export"`` 转 ``int``
        失败）。现在返回的是**文件名** —— 落在 ``msg`` 里，没有 ``data`` 键，因为
        ``AjaxResult.success(String)`` 命中的是 ``success(String msg)`` 重载。
        """
        response = http.get("/system/dict/data/export")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"].endswith("_字典数据.xlsx")
        assert "data" not in body
        # 走的是全量 ``selectDictDataList``，控制器没有 ``startPage()``
        assert [call[0] for call in data_service.calls] == ["select_dict_data_list"]


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: list_dict_data(SysDictData()),
            lambda: get_info(1),
            lambda: add(SysDictData(dict_label="男", dict_value="0", dict_type="sys_user_sex")),
            lambda: edit(_item("0", "男")),
            lambda: remove("1"),
        ],
    )
    def test_the_five_guarded_endpoints(self, services: Any, call: Any) -> None:
        data_service, type_service = services

        with pytest.raises(AccessDeniedException):
            call()

        assert data_service.calls == []
        assert type_service.calls == []

    def test_type_needs_no_permission(self, type_service: Any) -> None:
        """前端每个页面都调 —— 加权限会白屏。"""
        type_service.by_type_result = [_item("0", "男")]

        response = dict_type("sys_user_sex")

        assert response["code"] == 200
        assert len(response["data"]) == 1

    def test_typemore_needs_no_permission(self, type_service: Any) -> None:
        type_service.by_type_more_result = [_item("0", "男")]

        response = dict_type_more("sys_user_sex")

        assert response["code"] == 200

    def test_a_partial_permission_does_not_pass(self) -> None:
        authenticate(permissions={"system:dict:*"})

        with pytest.raises(AccessDeniedException):
            remove("1")

    def test_an_access_denied_becomes_http_200_code_403(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.delete("/system/dict/data/1")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}


# --------------------------------------------------------------------------- /type


class TestDictTypeEndpoint:
    def test_a_hit_is_returned_verbatim(self, type_service: Any) -> None:
        type_service.by_type_result = [_item("0", "男"), _item("1", "女")]

        response = dict_type("sys_user_sex")

        assert [row.dict_value for row in response["data"]] == ["0", "1"]

    def test_a_miss_returns_an_empty_array_not_none(self, type_service: Any) -> None:
        """``StringUtils.isNull(data)`` -> ``new ArrayList<>()``：客户端拿到 ``[]``。"""
        type_service.by_type_result = None

        response = dict_type("unknown")

        assert response["data"] == []
        assert response == {"code": 200, "msg": "操作成功", "data": []}

    def test_an_empty_list_is_passed_through(self, type_service: Any) -> None:
        type_service.by_type_result = []

        assert dict_type("unknown")["data"] == []

    def test_it_uses_the_type_service(self, type_service: Any, data_service: Any) -> None:
        """交叉依赖照抄：``ISysDictTypeService``（读缓存），不是 ``ISysDictDataService``。"""
        dict_type("sys_user_sex")

        assert type_service.of("select_dict_data_by_type") != []
        assert data_service.calls == []


# --------------------------------------------------------------------------- /typemore


class TestDictTypeMoreEndpoint:
    def test_the_rows_are_grouped_by_type(self, type_service: Any) -> None:
        type_service.by_type_more_result = [
            _item("1", "轿车", "car_type", 1),
            _item("2", "客车", "car_type", 2),
            _item("3", "蓝", "plate_color", 3),
        ]

        response = dict_type_more("car_type,plate_color")

        assert list(response["data"].keys()) == ["car_type", "plate_color"]
        assert [row.dict_label for row in response["data"]["car_type"]] == ["轿车", "客车"]
        assert len(response["data"]["plate_color"]) == 1

    def test_a_miss_returns_an_empty_object(self, type_service: Any) -> None:
        """``null`` -> 空 List -> ``groupingBy`` -> 空 ``HashMap`` -> ``"data": {}``。"""
        type_service.by_type_more_result = None

        assert dict_type_more("unknown")["data"] == {}

    def test_the_cache_key_is_the_raw_argument(self, type_service: Any) -> None:
        """尾逗号 / 空格都原样传给 Service（见 ``SysDictTypeService`` 的空操作说明）。"""
        dict_type_more("car_type,")

        assert type_service.of("select_dict_data_by_type_more") == [
            ("select_dict_data_by_type_more", "car_type,")
        ]

    def test_a_row_without_a_type_is_grouped_under_none(self, type_service: Any) -> None:
        """``groupingBy`` 允许 null 键（``HashMap``）；JSON 里会变成 ``"null"``。"""
        type_service.by_type_more_result = [SysDictData(dict_value="0", dict_label="男")]

        response = dict_type_more("x")

        assert None in response["data"]


# --------------------------------------------------------------------------- list / 详情


class TestListAndDetail:
    def test_the_page_is_started_before_the_query(self, data_service: Any) -> None:
        authenticate()

        list_dict_data(SysDictData())

        assert data_service.page_taken is not None
        assert data_service.page_taken.get_page_size() == 10

    def test_the_filters_are_passed_through(self, data_service: Any) -> None:
        authenticate()

        list_dict_data(SysDictData(dict_type="sys_user_sex", dict_label="男", status="0"))

        query = data_service.of("select_dict_data_list")[0][1]
        assert query.dict_type == "sys_user_sex"
        assert query.dict_label == "男"
        assert query.status == "0"

    def test_a_detail_hit_is_returned(self, data_service: Any) -> None:
        authenticate()
        data_service.by_id_result = _item("0", "男", dict_code=5)

        response = get_info(5)

        assert response["code"] == 200
        assert response["data"].dict_code == 5

    def test_a_detail_miss_omits_the_data_key(self, data_service: Any) -> None:
        authenticate()

        assert get_info(404) == {"code": 200, "msg": "操作成功"}


# --------------------------------------------------------------------------- 增删改


class TestWrites:
    def test_add_writes_the_user_name(self, data_service: Any) -> None:
        authenticate(user_name="ry")

        response = add(SysDictData(dict_label="男", dict_value="0", dict_type="sys_user_sex"))

        assert response["code"] == 200
        assert data_service.of("insert_dict_data")[0][1].create_by == "ry"

    def test_add_has_no_uniqueness_check(self, data_service: Any) -> None:
        """Java 也不查重 —— 同一类型下允许两条相同 ``dictValue``（后果见 ``selectDictLabel``）。"""
        authenticate()

        for _ in range(2):
            add(SysDictData(dict_label="男", dict_value="0", dict_type="sys_user_sex"))

        assert len(data_service.of("insert_dict_data")) == 2

    def test_add_reports_a_failure_when_nothing_was_inserted(self, data_service: Any) -> None:
        authenticate()
        data_service.insert_result = 0

        response = add(SysDictData(dict_label="男", dict_value="0", dict_type="sys_user_sex"))

        assert response["code"] == 500

    def test_edit_writes_the_user_name(self, data_service: Any) -> None:
        authenticate(user_name="ry")

        edit(_item("0", "男"))

        assert data_service.of("update_dict_data")[0][1].update_by == "ry"

    def test_edit_reports_a_failure_when_nothing_was_updated(self, data_service: Any) -> None:
        authenticate()
        data_service.update_result = 0

        assert edit(_item("0", "男"))["code"] == 500

    def test_remove_parses_the_comma_separated_ids(self, data_service: Any) -> None:
        authenticate()

        remove("1,2,3")

        assert data_service.of("delete_dict_data_by_ids") == [
            ("delete_dict_data_by_ids", [1, 2, 3])
        ]

    def test_remove_reports_a_failure(self, data_service: Any) -> None:
        authenticate()
        data_service.delete_result = 0

        assert remove("1")["code"] == 500


# --------------------------------------------------------------------------- 校验


class TestValidationRunsBeforePermission:
    """未登录 + 非法请求体 -> 500（校验先跑）；合法请求体 -> 403。"""

    def test_a_missing_label_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dict/data", json={"dictValue": "0", "dictType": "sys_user_sex"}
        )

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "字典标签不能为空"}

    def test_a_missing_value_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dict/data", json={"dictLabel": "男", "dictType": "sys_user_sex"}
        )

        assert response.json() == {"code": 500, "msg": "字典键值不能为空"}

    def test_a_missing_type_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dict/data", json={"dictLabel": "男", "dictValue": "0"}
        )

        assert response.json() == {"code": 500, "msg": "字典类型不能为空"}

    def test_the_first_violation_wins(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post("/system/dict/data", json={})

        assert response.json() == {"code": 500, "msg": "字典标签不能为空"}

    def test_css_class_is_optional(self, http_anonymous: TestClient) -> None:
        """``cssClass`` 只有 ``@Size``，缺省/空串都合法 —— 会走到权限校验。"""
        response = http_anonymous.post("/system/dict/data", json=dict(VALID_BODY))

        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}

    def test_an_overlong_css_class_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dict/data", json=dict(VALID_BODY, cssClass="c" * 101)
        )

        assert response.json() == {"code": 500, "msg": "样式属性长度不能超过100个字符"}

    def test_an_overlong_value_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dict/data", json=dict(VALID_BODY, dictValue="v" * 101)
        )

        assert response.json() == {"code": 500, "msg": "字典键值长度不能超过100个字符"}

    def test_the_full_body_round_trips(self, http: TestClient) -> None:
        response = http.post("/system/dict/data", json=dict(VALID_BODY))

        assert response.json() == {"code": 200, "msg": "操作成功"}

    def test_the_computed_default_key_is_emitted(
        self, http: TestClient, data_service: Any
    ) -> None:
        """``getDefault()`` 是 Jackson 的只读属性 —— 响应里必须带 ``"default"``。"""
        data_service.by_id_result = SysDictData(
            dict_code=1, dict_value="0", dict_label="男", is_default="Y"
        )

        payload = http.get("/system/dict/data/1").json()["data"]

        assert payload["isDefault"] == "Y"
        assert payload["default"] is True
