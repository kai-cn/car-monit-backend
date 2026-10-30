"""``SysUpgradeInfoController`` -- ``/system/upgradeInfo`` 的 7 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysUpgradeInfoController.java

这一层测什么
------------
Service 已被 ``test_sys_upgrade_info_service.py`` 覆盖，所以全部注入假 Service，只测
**控制器自己的约定**：

* 7 个映射全部注册（``export`` 在 Phase 3.18 补上）；
* **一个权限点都没有** —— 整个模块只有 ``anyRequest().authenticated()``，
  补权限会让没有"系统升级信息"菜单的普通用户看不到升级公告；
* ``/list`` 与 ``/newest`` **必须**排在 ``/{id}`` 之前；
* ``/list`` 在**控制器**里盖 ``tenantId``（Service 只做纯转发，与 indexmenu 相反）；
* ``remove`` 用 ``parse_str_array``（``String[]``），**不做** ``int`` 转换；
* ``add`` / ``edit`` 都没有 ``@Validated``。

``export`` 在这个模块里的奇怪之处
--------------------------------
其它模块的 ``/{id}`` 是 ``Long``，若 ``/export`` 没注册就会把 ``"export"`` 当 id
（转 ``int`` 失败 -> ``HTTP 200 + code 500``）。本模块 ``getInfo`` 的参数是
**``String``**（主键是 UUID），所以即使没注册也能平平安安落进 ``get_info("export")``。
现在路由有了，但这提两类陷阱：

1. ``/export`` **必须**排在 ``/{id}`` 之前，否则会被静默吃掉；
2. 实体上**零** ``@Excel`` —— 导出的 xlsx 里**一列也没有**，只有空 sheet。
   这是 Java 原样行为，不是缺陷。
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_upgrade_info_controller as controller
from app.api.system.sys_upgrade_info_controller import (
    add,
    edit,
    get_info,
    list_upgrade_infos,
    newest,
    remove,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_upgrade_info import SysUpgradeInfo

# --------------------------------------------------------------------------- fakes


class _FakeUpgradeInfoService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysUpgradeInfo] = []
        self.newest_result: Optional[SysUpgradeInfo] = None
        self.by_id_result: Optional[SysUpgradeInfo] = None
        self.save_result: Dict[str, Any] = {
            "code": 200,
            "msg": "操作成功！",
            "data": "abc",
        }
        self.delete_result: Dict[str, Any] = {"code": 200, "msg": "操作成功", "data": 1}
        #: ``select_sys_upgrade_info_list`` 被调用时挂起中的分页参数。
        self.page_taken: Any = None

    def select_sys_upgrade_info_list(self, query: SysUpgradeInfo) -> List[SysUpgradeInfo]:
        self.calls.append(("select_sys_upgrade_info_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_sys_upgrade_info_newest(self, query: SysUpgradeInfo) -> Optional[SysUpgradeInfo]:
        self.calls.append(("select_sys_upgrade_info_newest", query.model_copy(deep=True)))
        return self.newest_result

    def select_sys_upgrade_info_by_id(self, entity_id: Any) -> Optional[SysUpgradeInfo]:
        self.calls.append(("select_sys_upgrade_info_by_id", entity_id))
        return self.by_id_result

    def save_sys_upgrade_info(self, entity: SysUpgradeInfo) -> Dict[str, Any]:
        self.calls.append(("save_sys_upgrade_info", entity.model_copy(deep=True)))
        return self.save_result

    def delete_sys_upgrade_info_by_ids(self, ids: Sequence[Any]) -> Dict[str, Any]:
        self.calls.append(("delete_sys_upgrade_info_by_ids", list(ids)))
        return self.delete_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeUpgradeInfoService()
    monkeypatch.setattr(controller, "_UPGRADE_INFO_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_upgrade_info_controller()


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    return TestClient(_build_app(login=False))


@pytest.fixture
def http_lenient() -> Any:
    """已登录、且**不把服务端异常当失败**的 mini app。

    ``@ExceptionHandler(Exception)`` 挂在 Starlette 的 ``ServerErrorMiddleware`` 上：
    响应发出后它还会再重抛一次。只有 ``TestClient`` 需要关掉
    ``raise_server_exceptions`` 才看得到同一个响应体。
    """
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(
                    LoginUser(
                        user=SysUser(
                            user_id=2, user_name="ry", dept_id=103, tenant_id=100
                        ),
                        permissions={"*:*:*"},
                    ),
                    None,
                    [],
                )
            )
            return await call_next(request)

    application.include_router(controller.router)
    return application


def authenticate(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[set] = None,
    tenant_id: int = 100,
) -> SysUser:
    user = SysUser(user_id=user_id, user_name=user_name, tenant_id=tenant_id)
    login_user = LoginUser(user=user, permissions=permissions if permissions is not None else set())
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _info(ver: str = "1.2.3") -> SysUpgradeInfo:
    return SysUpgradeInfo(id="u-1", ver=ver, info="修复若干问题", back_col1="1")


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_seven_routes_share_five_paths(self) -> None:
        """POST 与 PUT 都挂在 ``/system/upgradeInfo``（无尾斜杠）。"""
        registered = [
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        ]

        assert registered == [
            ("/system/upgradeInfo/list", ("GET",)),
            ("/system/upgradeInfo/export", ("GET",)),
            ("/system/upgradeInfo/newest", ("GET",)),
            ("/system/upgradeInfo/{id}", ("GET",)),
            ("/system/upgradeInfo", ("POST",)),
            ("/system/upgradeInfo", ("PUT",)),
            ("/system/upgradeInfo/{ids}", ("DELETE",)),
        ]

    def test_export_comes_before_the_path_variable(self) -> None:
        """``/{id}`` 收 ``String``，不排在前面就会把 ``"export"`` 当 id 查库。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/upgradeInfo/export") < paths.index("/system/upgradeInfo/{id}")

    def test_the_literal_get_paths_come_first(self) -> None:
        """``/{id}`` 收 ``String``，能吃掉**任何**单段路径 —— 顺序错了两条字面量路由不可达。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/upgradeInfo/list") < paths.index("/system/upgradeInfo/{id}")
        assert paths.index("/system/upgradeInfo/newest") < paths.index("/system/upgradeInfo/{id}")

    def test_the_list_beats_the_path_variable_over_http(self, http: TestClient) -> None:
        response = http.get("/system/upgradeInfo/list")

        assert response.json().keys() == {"total", "rows", "code", "msg"}
        assert response.json()["msg"] == "查询成功"

    def test_newest_beats_the_path_variable_over_http(
        self, http: TestClient, service: Any
    ) -> None:
        response = http.get("/system/upgradeInfo/newest")

        assert response.json()["code"] == 200
        assert service.of("select_sys_upgrade_info_by_id") == []
        assert len(service.of("select_sys_upgrade_info_newest")) == 1

    def test_export_does_not_fall_into_the_string_path_variable(
        self, http: TestClient, service: Any
    ) -> None:
        """``/export`` 不再被 ``/{id}`` 吃掉 —— 即使 ``/{id}`` 收 ``String`` 也不允许。

        实体的 ``EXCEL_FIELDS`` 是空的，所以 xlsx 里**只有 sheet 名、没有任何列**。
        这是 Java 原样行为（``getFields()`` 返回空列表，``ExcelUtil`` 容忍它）。
        """
        response = http.get("/system/upgradeInfo/export")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"].endswith("_系统升级信息数据.xlsx")
        assert "data" not in body
        assert service.of("select_sys_upgrade_info_by_id") == []
        assert [call[0] for call in service.calls] == ["select_sys_upgrade_info_list"]


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    def test_the_controller_declares_no_permission_at_all(self) -> None:
        """**一个 ``@PreAuthorize`` 都没有**（不是被注释，是本来就没写）。"""
        assert "pre_authorize_permi" not in inspect.getsource(controller)

    @pytest.mark.parametrize(
        "call",
        [
            lambda: list_upgrade_infos(SysUpgradeInfo()),
            lambda: newest(SysUpgradeInfo()),
            lambda: get_info("u-1"),
            lambda: add(_info()),
            lambda: edit(_info()),
            lambda: remove("u-1"),
        ],
    )
    def test_every_endpoint_passes_with_an_empty_permission_set(
        self, service: Any, call: Any
    ) -> None:
        authenticate(permissions=set())

        response = call()

        # ``list`` 回的是 TableDataInfo，其余五个回 AjaxResult
        code = response.get_code() if hasattr(response, "get_code") else response["code"]
        assert code == 200
        assert service.calls != []

    def test_an_anonymous_newest_still_answers(self, http_anonymous: TestClient) -> None:
        """``/newest`` 不碰登录上下文，所以未登录也能正常回。控制器不鉴权；
        真实链路由 ``SecurityConfig`` 的 ``anyRequest().authenticated()`` 兜（未登录 401）。"""
        response = http_anonymous.get("/system/upgradeInfo/newest")

        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "操作成功"}

    def test_an_anonymous_list_fails_on_the_tenant_stamp(
        self, http_anonymous: TestClient
    ) -> None:
        """``/list`` 要 ``getTenantId()``，未登录时抛 ``CustomException`` -> code 500。"""
        response = http_anonymous.get("/system/upgradeInfo/list")

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "获取用户账户异常"}

    def test_an_anonymous_delete_is_not_blocked(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.delete("/system/upgradeInfo/u-1")

        assert response.json() == {"code": 200, "msg": "操作成功", "data": 1}

    def test_an_anonymous_get_info_is_not_blocked(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.get("/system/upgradeInfo/u-1")

        assert response.json() == {"code": 200, "msg": "操作成功"}


# --------------------------------------------------------------------------- list


class TestList:
    def test_the_page_is_started_before_the_query(self, service: Any, http: TestClient) -> None:
        http.get("/system/upgradeInfo/list")

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1

    def test_the_tenant_comes_from_the_login_context(self, service: Any) -> None:
        """客户端传 ``tenantId=999`` 也会被登录上下文覆盖成 100。"""
        authenticate(tenant_id=100)

        list_upgrade_infos(SysUpgradeInfo(tenant_id=999))

        assert service.of("select_sys_upgrade_info_list")[0][1].tenant_id == 100

    def test_the_over_http_tenant_is_overridden_too(self, http: TestClient, service: Any) -> None:
        http.get("/system/upgradeInfo/list", params={"tenantId": "999"})

        assert service.of("select_sys_upgrade_info_list")[0][1].tenant_id == 100

    def test_a_missing_tenant_in_the_login_becomes_none(self, service: Any) -> None:
        """登录用户没租户 -> ``tenantId`` 被盖成 ``None``；
        ``<if test="tenantId != null">`` 因此**不生效**。"""
        authenticate(tenant_id=None)  # type: ignore[arg-type]

        list_upgrade_infos(SysUpgradeInfo(tenant_id=999))

        assert service.of("select_sys_upgrade_info_list")[0][1].tenant_id is None

    def test_the_camel_case_filters_are_bound(self, http: TestClient, service: Any) -> None:
        http.get(
            "/system/upgradeInfo/list",
            params={"ver": "1.2.3", "info": "修复", "backCol1": "1"},
        )

        query = service.of("select_sys_upgrade_info_list")[0][1]
        assert (query.ver, query.info, query.back_col1) == ("1.2.3", "修复", "1")

    def test_an_unknown_query_parameter_is_ignored(self, http: TestClient, service: Any) -> None:
        """Java: ``WebDataBinder`` 的 ``ignoreUnknownFields=true``。"""
        response = http.get("/system/upgradeInfo/list", params={"nope": "1"})

        assert response.status_code == 200
        assert service.of("select_sys_upgrade_info_list") != []

    def test_the_rows_and_total_come_from_the_service(self, service: Any) -> None:
        authenticate()
        service.list_result = [_info("1.2.3"), _info("1.2.4")]

        response = list_upgrade_infos(SysUpgradeInfo())

        assert response.get_total() == 2
        assert [row.ver for row in response.get_rows()] == ["1.2.3", "1.2.4"]

    def test_an_empty_list_is_still_a_zero_total(self, service: Any) -> None:
        authenticate()

        response = list_upgrade_infos(SysUpgradeInfo())

        assert response.get_total() == 0
        assert response.get_rows() == []


# --------------------------------------------------------------------------- newest


class TestNewest:
    def test_a_miss_omits_the_data_key(self, http: TestClient) -> None:
        """``success(null)`` -> ``data`` 整键消失，不是 ``"data": null``。"""
        body = http.get("/system/upgradeInfo/newest").json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert "data" not in body

    def test_a_hit_is_wrapped_in_a_success_envelope(self, http: TestClient, service: Any) -> None:
        service.newest_result = _info("2.0.0")

        body = http.get("/system/upgradeInfo/newest").json()

        assert body["code"] == 200
        assert body["data"]["ver"] == "2.0.0"
        assert body["data"]["backCol1"] == "1"

    def test_it_returns_200_not_404_when_nothing_matches(
        self, http: TestClient
    ) -> None:
        response = http.get("/system/upgradeInfo/newest")

        assert response.status_code == 200
        assert response.json()["code"] == 200

    def test_the_query_params_reach_the_service_but_the_sql_ignores_them(
        self, http: TestClient, service: Any
    ) -> None:
        http.get("/system/upgradeInfo/newest", params={"ver": "9.9.9"})

        assert service.of("select_sys_upgrade_info_newest")[0][1].ver == "9.9.9"


# --------------------------------------------------------------------------- getInfo


class TestGetInfo:
    def test_a_uuid_path_is_taken_verbatim(self, http: TestClient, service: Any) -> None:
        """``id`` 是 ``String`` —— 不是 ``Long``，不会被 ``int()`` 拒掉。"""
        response = http.get("/system/upgradeInfo/1d3f0b9c4e5a4b6c8d7e9f0a1b2c3d4e")

        assert response.status_code == 200
        assert service.of("select_sys_upgrade_info_by_id") == [
            ("select_sys_upgrade_info_by_id", "1d3f0b9c4e5a4b6c8d7e9f0a1b2c3d4e")
        ]

    def test_a_non_numeric_id_does_not_500(self, http: TestClient) -> None:
        """其它模块这里会 500（``int("abc")``），本模块不会。"""
        response = http.get("/system/upgradeInfo/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 200

    def test_a_miss_omits_the_data_key(self, http: TestClient) -> None:
        body = http.get("/system/upgradeInfo/u-1").json()

        assert body == {"code": 200, "msg": "操作成功"}

    def test_a_hit_serialises_the_whole_entity(self, http: TestClient, service: Any) -> None:
        service.by_id_result = SysUpgradeInfo(
            id="u-1", ver="1.2.3", info="修复", back_col1="1", eps_id=103, tenant_id=100
        )

        data = http.get("/system/upgradeInfo/u-1").json()["data"]

        assert (data["id"], data["ver"], data["info"], data["backCol1"]) == (
            "u-1",
            "1.2.3",
            "修复",
            "1",
        )
        assert (data["epsId"], data["tenantId"]) == (103, 100)

    def test_the_base_uuid_fields_are_present(self, http: TestClient, service: Any) -> None:
        """``BaseUuidEntity`` 的 ``params`` **没有** ``NON_EMPTY`` 注解 -> 序列化成 ``null``。"""
        service.by_id_result = SysUpgradeInfo(id="u-1")

        data = http.get("/system/upgradeInfo/u-1").json()["data"]

        assert data["params"] is None
        assert data["delFlag"] is None
        assert data["deptSubCode"] is None

    def test_the_direct_call_returns_the_ajax_result(self, service: Any) -> None:
        """直接调用时 ``data`` 里是**实体本身**（序列化发生在 FastAPI 那一层）。"""
        authenticate()
        hit = _info()
        service.by_id_result = hit

        assert get_info("u-1") == {"code": 200, "msg": "操作成功", "data": hit}


# --------------------------------------------------------------------------- add / edit


class TestAddAndEdit:
    def test_add_returns_the_service_response_verbatim(self, http: TestClient) -> None:
        body = http.post("/system/upgradeInfo", json={"ver": "1.2.3"}).json()

        assert body == {"code": 200, "msg": "操作成功！", "data": "abc"}

    def test_add_passes_the_camel_case_fields_through(
        self, http: TestClient, service: Any
    ) -> None:
        http.post(
            "/system/upgradeInfo",
            json={"ver": "1.2.3", "info": "修复", "backCol1": "1"},
        )

        entity = service.of("save_sys_upgrade_info")[0][1]
        assert (entity.ver, entity.info, entity.back_col1) == ("1.2.3", "修复", "1")

    def test_the_controller_does_not_stamp_the_tenant_on_add(
        self, http: TestClient, service: Any
    ) -> None:
        """盖 ``epsId`` / ``tenantId`` 是 **Service** 的活 —— 控制器原样透传。"""
        http.post("/system/upgradeInfo", json={"tenantId": 999, "epsId": 7})

        entity = service.of("save_sys_upgrade_info")[0][1]
        assert (entity.tenant_id, entity.eps_id) == (999, 7)

    def test_an_empty_body_is_accepted(self, http: TestClient, service: Any) -> None:
        """没有 ``@Validated`` —— ``{}`` 也能进 Service（之后由 Service 补 id 新增）。"""
        response = http.post("/system/upgradeInfo", json={})

        assert response.status_code == 200
        assert response.json()["code"] == 200
        assert service.of("save_sys_upgrade_info")[0][1].ver is None

    def test_edit_calls_the_same_service_method(self, http: TestClient, service: Any) -> None:
        body = http.put("/system/upgradeInfo", json={"id": "u-1", "ver": "1.2.4"}).json()

        assert body == {"code": 200, "msg": "操作成功！", "data": "abc"}
        entity = service.of("save_sys_upgrade_info")[0][1]
        assert (entity.id, entity.ver) == ("u-1", "1.2.4")

    def test_edit_without_an_id_would_insert(self, http: TestClient, service: Any) -> None:
        """控制器不判断有没有 id —— 判断在 Service 里。"""
        http.put("/system/upgradeInfo", json={"ver": "1.2.4"})

        assert service.of("save_sys_upgrade_info")[0][1].id is None

    def test_a_non_json_body_keeps_http_200_with_code_500(self, http: TestClient) -> None:
        """``RequestValidationError`` 被统一处理器改写成 ``HTTP 200 + code 500``。"""
        response = http.post(
            "/system/upgradeInfo", content="not-json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        assert response.json()["code"] == 500

    def test_add_is_not_bound_to_the_get_route(self, http: TestClient, service: Any) -> None:
        """``POST /system/upgradeInfo`` 不带尾斜杠 —— 带斜杠会 307。"""
        assert http.post("/system/upgradeInfo/", json={}).status_code in (200, 307)


# --------------------------------------------------------------------------- remove


class TestRemove:
    def test_a_single_uuid_is_not_cast_to_int(self, service: Any) -> None:
        """``parse_str_array`` —— 用 ``parse_id_array`` 会让**每个** UUID 请求回 500。"""
        authenticate()

        remove("u-1")

        assert service.of("delete_sys_upgrade_info_by_ids") == [
            ("delete_sys_upgrade_info_by_ids", ["u-1"])
        ]

    def test_a_comma_separated_list_is_split(self, service: Any) -> None:
        authenticate()

        remove("u-1,u-2")

        assert service.of("delete_sys_upgrade_info_by_ids")[0][1] == ["u-1", "u-2"]

    def test_a_real_uuid_survives_the_round_trip(self, http: TestClient, service: Any) -> None:
        uuid = "1d3f0b9c4e5a4b6c8d7e9f0a1b2c3d4e"

        response = http.delete(f"/system/upgradeInfo/{uuid}")

        assert response.status_code == 200
        assert service.of("delete_sys_upgrade_info_by_ids")[0][1] == [uuid]

    def test_a_non_numeric_id_does_not_500(self, http: TestClient) -> None:
        response = http.delete("/system/upgradeInfo/abc")

        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "操作成功", "data": 1}

    def test_an_empty_middle_segment_is_kept(self, service: Any) -> None:
        """``split(",")`` 不丢中间的空段 —— ``"u-1,,u-2"`` -> ``["u-1", "", "u-2"]``。"""
        authenticate()

        remove("u-1,,u-2")

        assert service.of("delete_sys_upgrade_info_by_ids")[0][1] == ["u-1", "", "u-2"]

    def test_a_zero_count_is_still_a_success(self, http: TestClient, service: Any) -> None:
        service.delete_result = {"code": 200, "msg": "操作成功", "data": 0}

        body = http.delete("/system/upgradeInfo/u-1").json()

        assert body == {"code": 200, "msg": "操作成功", "data": 0}


# --------------------------------------------------------------------------- 其它


class TestMisc:
    def test_the_router_prefix_and_tags(self) -> None:
        assert controller.router.prefix == "/system/upgradeInfo"
        assert list(controller.router.tags) == ["system-upgrade-info"]

    def test_the_service_singleton_is_lazily_created(self) -> None:
        """``reset`` 之后重新取，拿到的仍是模块级那一份。"""
        controller.reset_upgrade_info_controller()
        first = controller._upgrade_info_service()
        try:
            assert controller._upgrade_info_service() is first
        finally:
            controller.reset_upgrade_info_controller()
