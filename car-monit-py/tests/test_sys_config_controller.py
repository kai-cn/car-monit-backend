"""``SysConfigController`` -- ``/system/config`` 的 7 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysConfigController.java

这一层测什么
------------
Service 已被 ``test_sys_config_service.py`` 覆盖，所以全部注入假 Service，只测
**控制器自己的约定**：

* 8 个映射全部注册；
* 权限点：``list`` / ``query`` / ``add`` / ``edit`` / ``remove`` / ``export`` 六个，
  ``getConfigKey`` **没有** ``@PreAuthorize``（前端"按参数键名取值"要用）；
* ``clearCache`` 是 ``DELETE /clearCache``，必须注册在 ``DELETE /{configIds}`` **之前**；
* 唯一性校验在写库**之前**，提示文案插的是 ``configName``（不是 ``configKey``）；
* ``add`` / ``edit`` 的 ``@Validated`` 排在 ``@PreAuthorize`` 之前（依赖注入实现）。

``export`` 的形状
-----------------
``GET /system/config/export`` 返回的是**文件名**（在 ``msg`` 里，不是 ``data``），
文件本身写到 ``{ruoyi.profile}/download/``。这一层只断言响应的形状，xlsx 的字节级
内容由 ``test_excel_util.py`` 覆盖。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_config_controller as controller
from app.api.system.sys_config_controller import (
    ADD_CONFIG_EXISTS,
    EDIT_CONFIG_EXISTS,
    add,
    clear_cache,
    edit,
    get_config_key,
    get_info,
    list_configs,
    remove,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException, CustomException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_config import SysConfig

#: 一个能通过 ``@Validated`` 的请求体（``configName`` / ``configKey`` / ``configValue``
#: 三个 ``@NotBlank``）。
VALID_BODY: Dict[str, Any] = {
    "configName": "主框架页-默认皮肤样式名称",
    "configKey": "sys.index.skinName",
    "configValue": "skin-blue",
    "configType": "Y",
}


# --------------------------------------------------------------------------- fakes


class _FakeConfigService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysConfig] = []
        self.by_id_result: Optional[SysConfig] = None
        self.by_key_result: Optional[str] = None
        self.unique_result = "0"
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        #: 打开后 ``delete_config_by_ids`` 直接抛（复刻"内置参数"的 ``CustomException``）。
        self.delete_exception: Optional[Exception] = None
        #: ``select_config_list`` 被调用时挂起中的分页参数。
        self.page_taken: Any = None

    def select_config_list(self, query: SysConfig) -> List[SysConfig]:
        self.calls.append(("select_config_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_config_by_id(self, config_id: int) -> Optional[SysConfig]:
        self.calls.append(("select_config_by_id", config_id))
        return self.by_id_result

    def select_config_by_key(self, config_key: str) -> Optional[str]:
        self.calls.append(("select_config_by_key", config_key))
        return self.by_key_result

    def check_config_key_unique(self, config: SysConfig) -> str:
        self.calls.append(("check_config_key_unique", config.model_copy(deep=True)))
        return self.unique_result

    def insert_config(self, config: SysConfig) -> int:
        self.calls.append(("insert_config", config.model_copy(deep=True)))
        return self.insert_result

    def update_config(self, config: SysConfig) -> int:
        self.calls.append(("update_config", config.model_copy(deep=True)))
        return self.update_result

    def delete_config_by_ids(self, config_ids: Sequence[int]) -> int:
        self.calls.append(("delete_config_by_ids", list(config_ids)))
        if self.delete_exception is not None:
            raise self.delete_exception
        return self.delete_result

    def clear_cache(self) -> None:
        self.calls.append(("clear_cache",))

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeConfigService()
    monkeypatch.setattr(controller, "_CONFIG_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_config_controller()


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
    响应发出后它还会再重抛一次。Uvicorn 下客户端拿到的就是 ``{"code":500,...}``；
    只有 ``TestClient`` 需要关掉 ``raise_server_exceptions`` 才看得到同一个响应体。
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


def _config(config_id: int = 1, config_key: str = "sys.index.skinName") -> SysConfig:
    return SysConfig(
        config_id=config_id,
        config_name="主框架页-默认皮肤样式名称",
        config_key=config_key,
        config_value="skin-blue",
        config_type="Y",
    )


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_eight_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/config/list", ("GET",)),
            ("/system/config/export", ("GET",)),
            ("/system/config/configKey/{config_key}", ("GET",)),
            ("/system/config/{config_id}", ("GET",)),
            ("/system/config", ("POST",)),
            ("/system/config", ("PUT",)),
            ("/system/config/clearCache", ("DELETE",)),
            ("/system/config/{config_ids}", ("DELETE",)),
        }

    def test_export_comes_before_the_path_variable(self) -> None:
        """``/export`` 排在 ``/{config_id}`` 后面的话 ``"export"`` 会转 int 失败。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/config/export") < paths.index("/system/config/{config_id}")

    def test_clear_cache_comes_before_the_path_variable(self) -> None:
        """两个都是 ``DELETE``，顺序反了 ``clearCache`` 会被当成 id 列表。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/config/clearCache") < paths.index(
            "/system/config/{config_ids}"
        )

    def test_literal_get_paths_come_before_the_path_variable(self) -> None:
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/config/list") < paths.index("/system/config/{config_id}")
        assert paths.index("/system/config/configKey/{config_key}") < paths.index(
            "/system/config/{config_id}"
        )

    def test_the_list_beats_the_path_variable_over_http(self, http: TestClient) -> None:
        response = http.get("/system/config/list")

        assert response.json().keys() == {"total", "rows", "code", "msg"}

    def test_config_key_beats_the_path_variable_too(
        self, http: TestClient, service: Any
    ) -> None:
        """``/configKey/{key}`` 不能被 ``/{configId}`` 吃掉（后者只收数字）。"""
        service.by_key_result = "skin-blue"

        response = http.get("/system/config/configKey/sys.index.skinName")

        assert response.json() == {"code": 200, "msg": "操作成功", "data": "skin-blue"}
        assert service.of("select_config_by_key") == [
            ("select_config_by_key", "sys.index.skinName")
        ]

    def test_clear_cache_is_not_treated_as_an_id_list(
        self, http: TestClient, service: Any
    ) -> None:
        response = http.delete("/system/config/clearCache")

        assert response.json() == {"code": 200, "msg": "操作成功"}
        assert service.of("clear_cache") == [("clear_cache",)]
        assert service.of("delete_config_by_ids") == []

    def test_export_returns_the_filename_in_msg(self, http: TestClient, service: Any) -> None:
        """``export`` 现在有自己的路由：文件名在 ``msg``，且**没有** ``data`` 键。

        这是 ``AjaxResult.success(String)`` 重载的后果，不是笔误 —— 与 Java 一致。
        """
        response = http.get("/system/config/export")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"].endswith("_参数数据.xlsx")
        assert "data" not in body
        assert [call[0] for call in service.calls] == ["select_config_list"]


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: list_configs(SysConfig()),
            lambda: get_info(1),
            lambda: add(SysConfig(config_name="a", config_key="b", config_value="c")),
            lambda: edit(_config()),
            lambda: remove("1"),
            lambda: clear_cache(),
        ],
    )
    def test_the_six_guarded_endpoints(self, service: Any, call: Any) -> None:
        with pytest.raises(AccessDeniedException):
            call()

        assert service.calls == []

    def test_get_config_key_needs_no_permission(self, service: Any) -> None:
        """前端"按参数键名取值"要用 —— 加权限会让没有参数管理权限的用户白屏。"""
        service.by_key_result = "skin-blue"

        response = get_config_key("sys.index.skinName")

        assert response["code"] == 200
        assert response["data"] == "skin-blue"

    def test_a_partial_permission_does_not_pass(self) -> None:
        authenticate(permissions={"system:config:*"})

        with pytest.raises(AccessDeniedException):
            add(SysConfig(config_name="a", config_key="b", config_value="c"))

    def test_an_access_denied_becomes_http_200_code_403(
        self, http_anonymous: TestClient
    ) -> None:
        response = http_anonymous.delete("/system/config/1")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}


# --------------------------------------------------------------------------- list


class TestList:
    def test_the_page_is_started_before_the_query(self, service: Any) -> None:
        authenticate()

        list_configs(SysConfig())

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1

    def test_an_unknown_query_parameter_is_ignored(
        self, http: TestClient, service: Any
    ) -> None:
        """Java: ``WebDataBinder.setIgnoreUnknownFields(true)`` 是默认值。"""
        http.get("/system/config/list", params={"nonsense": "x", "configType": "Y"})

        query = service.of("select_config_list")[0][1]
        assert query.config_type == "Y"
        assert not hasattr(query, "nonsense")

    def test_the_camel_case_filters_are_bound(self, http: TestClient, service: Any) -> None:
        http.get(
            "/system/config/list",
            params={"configName": "皮肤", "configKey": "skin", "configType": "Y"},
        )

        query = service.of("select_config_list")[0][1]
        assert (query.config_name, query.config_key, query.config_type) == ("皮肤", "skin", "Y")

    def test_params_begin_and_end_time_land_in_the_map(
        self, http: TestClient, service: Any
    ) -> None:
        """``params[beginTime]`` 进 ``BaseEntity.params``，键名保持 camelCase。"""
        http.get(
            "/system/config/list",
            params={"params[beginTime]": "2024-01-01", "params[endTime]": "2024-12-31"},
        )

        query = service.of("select_config_list")[0][1]
        assert query.params == {"beginTime": "2024-01-01", "endTime": "2024-12-31"}

    def test_an_empty_string_survives_binding(self, http: TestClient, service: Any) -> None:
        """``String`` 属性原样保留空串（包装类型才会变 ``null``）—— 这是 SQL 里
        ``!= ''`` 判据能被真正触发的入口。"""
        http.get("/system/config/list", params={"configName": ""})

        query = service.of("select_config_list")[0][1]
        assert query.config_name == ""

    def test_the_rows_are_returned_verbatim(self, http: TestClient, service: Any) -> None:
        service.list_result = [_config()]

        response = http.get("/system/config/list")

        body = response.json()
        assert body["total"] == 1
        assert body["rows"] == [
            {
                "configId": 1,
                "configName": "主框架页-默认皮肤样式名称",
                "configKey": "sys.index.skinName",
                "configValue": "skin-blue",
                "configType": "Y",
                "createBy": None,
                "createTime": None,
                "updateBy": None,
                "updateTime": None,
                "remark": None,
            }
        ]

    def test_params_is_not_serialized(self, http: TestClient, service: Any) -> None:
        """``BaseEntity.params`` 是查询条件的运输工具，不进响应体。"""
        service.list_result = [_config()]

        assert "params" not in http.get("/system/config/list").json()["rows"][0]


# --------------------------------------------------------------------------- 详情


class TestGetInfo:
    def test_the_id_is_passed_as_an_integer(self, service: Any) -> None:
        authenticate()

        get_info(7)

        assert service.of("select_config_by_id") == [("select_config_by_id", 7)]

    def test_a_miss_omits_the_data_key(self, service: Any) -> None:
        """``AjaxResult.success(null)`` 不写 ``data``（``isNotNull`` 才 put）。"""
        authenticate()

        response = get_info(999)

        assert response == {"code": 200, "msg": "操作成功"}
        assert "data" not in response

    def test_a_hit_returns_the_camel_case_entity(self, http: TestClient, service: Any) -> None:
        service.by_id_result = _config()

        body = http.get("/system/config/1").json()

        assert body["data"]["configKey"] == "sys.index.skinName"
        assert body["data"]["configType"] == "Y"

    def test_a_non_numeric_id_is_an_http_200_code_500(self, http: TestClient) -> None:
        response = http.get("/system/config/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- getConfigKey


class TestGetConfigKey:
    def test_a_miss_returns_an_empty_string_not_null(self, service: Any) -> None:
        """Java 最后一行是 ``StringUtils.EMPTY``。"""
        service.by_key_result = ""

        response = get_config_key("sys.absent")

        assert response["data"] == ""
        assert "data" in response

    def test_a_hit_returns_the_stored_value(self, service: Any) -> None:
        service.by_key_result = "true"

        assert get_config_key("sys.account.captchaEnabled")["data"] == "true"

    def test_the_key_is_not_trimmed(self, service: Any) -> None:
        """``@PathVariable`` 不做 trim；缓存键就是原样的串。"""
        get_config_key("sys.index.skinName")

        assert service.of("select_config_by_key") == [
            ("select_config_by_key", "sys.index.skinName")
        ]


# --------------------------------------------------------------------------- 新增


class TestAdd:
    def test_a_duplicate_key_returns_an_error_and_does_not_write(self, service: Any) -> None:
        authenticate()
        service.unique_result = "1"

        response = add(
            SysConfig(config_name="皮肤", config_key="sys.index.skinName", config_value="x")
        )

        assert response == {"code": 500, "msg": ADD_CONFIG_EXISTS.format("皮肤")}
        assert service.of("insert_config") == []

    def test_the_message_uses_the_config_name(self) -> None:
        """文案插的是 ``configName``（参数名称），**不是** ``configKey``。"""
        assert ADD_CONFIG_EXISTS.format("皮肤") == "新增参数'皮肤'失败，参数键名已存在"

    def test_create_by_is_the_login_user(self, service: Any) -> None:
        authenticate(user_name="alice")

        add(SysConfig(config_name="a", config_key="b", config_value="c"))

        stored = service.of("insert_config")[0][1]
        assert stored.create_by == "alice"

    def test_a_zero_row_count_is_a_failure(self, service: Any) -> None:
        authenticate()
        service.insert_result = 0

        assert add(SysConfig(config_name="a", config_key="b", config_value="c")) == {
            "code": 500,
            "msg": "操作失败",
        }

    def test_a_positive_row_count_is_a_success(self, service: Any) -> None:
        authenticate()

        assert add(SysConfig(config_name="a", config_key="b", config_value="c")) == {
            "code": 200,
            "msg": "操作成功",
        }

    def test_the_body_is_bound_from_json(self, http: TestClient, service: Any) -> None:
        response = http.post("/system/config", json=VALID_BODY)

        assert response.json() == {"code": 200, "msg": "操作成功"}
        stored = service.of("insert_config")[0][1]
        assert stored.config_key == "sys.index.skinName"
        assert stored.create_by == "ry"


# --------------------------------------------------------------------------- 修改


class TestEdit:
    def test_a_duplicate_key_returns_an_error_and_does_not_write(self, service: Any) -> None:
        authenticate()
        service.unique_result = "1"

        response = edit(_config())

        assert response == {"code": 500, "msg": EDIT_CONFIG_EXISTS.format("主框架页-默认皮肤样式名称")}
        assert service.of("update_config") == []

    def test_update_by_is_the_login_user(self, service: Any) -> None:
        authenticate(user_name="bob")

        edit(_config())

        assert service.of("update_config")[0][1].update_by == "bob"

    def test_a_zero_row_count_is_a_failure(self, service: Any) -> None:
        authenticate()
        service.update_result = 0

        assert edit(_config()) == {"code": 500, "msg": "操作失败"}

    def test_the_unique_check_receives_the_id_so_it_can_exclude_itself(
        self, service: Any
    ) -> None:
        """``checkConfigKeyUnique`` 用实体里的 ``configId`` 排除自身，别丢了这个字段。"""
        authenticate()

        edit(_config(config_id=42))

        assert service.of("check_config_key_unique")[0][1].config_id == 42


# --------------------------------------------------------------------------- 删除


class TestRemove:
    def test_the_id_list_is_split_on_commas(self, service: Any) -> None:
        authenticate()

        assert remove("1,2,3") == {"code": 200, "msg": "操作成功"}
        assert service.of("delete_config_by_ids") == [("delete_config_by_ids", [1, 2, 3])]

    def test_a_zero_row_count_is_a_failure(self, service: Any) -> None:
        authenticate()
        service.delete_result = 0

        assert remove("1") == {"code": 500, "msg": "操作失败"}

    def test_a_builtin_config_blocks_the_whole_batch(
        self, http: TestClient, service: Any
    ) -> None:
        """``CustomException`` -> HTTP 200 + code 500；文案**末尾带一个空格**。"""
        service.delete_exception = CustomException("内置参数【sys.index.skinName】不能删除 ")

        response = http.delete("/system/config/1,2")

        assert response.status_code == 200
        assert response.json() == {
            "code": 500,
            "msg": "内置参数【sys.index.skinName】不能删除 ",
        }

    def test_the_exception_propagates_out_of_the_service(self, service: Any) -> None:
        """控制器不 catch —— 交给全局处理器转成 ``code 500``。"""
        authenticate()
        service.delete_exception = CustomException("内置参数【a】不能删除 ")

        with pytest.raises(CustomException):
            remove("1")

    def test_a_non_numeric_id_is_an_http_200_code_500(
        self, http_lenient: TestClient
    ) -> None:
        """``Long[]`` 绑定失败 -> Spring 回 500 错误体（不是 404 / 422）。"""
        response = http_lenient.delete("/system/config/1,abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- 校验


class TestValidation:
    @pytest.mark.parametrize(
        "body, message",
        [
            ({"configKey": "k", "configValue": "v"}, "参数名称不能为空"),
            ({"configName": "n", "configValue": "v"}, "参数键名长度不能为空"),
            ({"configName": "n", "configKey": "k"}, "参数键值不能为空"),
            (
                {"configName": "n" * 101, "configKey": "k", "configValue": "v"},
                "参数名称不能超过100个字符",
            ),
            (
                {"configName": "n", "configKey": "k" * 101, "configValue": "v"},
                "参数键名长度不能超过100个字符",
            ),
            (
                {"configName": "n", "configKey": "k", "configValue": "v" * 501},
                "参数键值长度不能超过500个字符",
            ),
        ],
    )
    def test_the_six_constraints(
        self, http: TestClient, service: Any, body: Dict[str, Any], message: str
    ) -> None:
        response = http.post("/system/config", json=body)

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": message}
        assert service.of("insert_config") == []

    def test_the_name_is_checked_before_the_key(self, http: TestClient, service: Any) -> None:
        """getter 的声明顺序决定多字段同时违规时报哪一条。"""
        response = http.post("/system/config", json={})

        assert response.json()["msg"] == "参数名称不能为空"

    def test_a_blank_name_is_rejected_too(self, http: TestClient) -> None:
        """``@NotBlank`` 会 trim：``"   "`` 与 ``""`` 同样被拒。"""
        body = {"configName": "   ", "configKey": "k", "configValue": "v"}

        assert http.post("/system/config", json=body).json()["msg"] == "参数名称不能为空"

    def test_config_type_has_no_constraint(self, http: TestClient, service: Any) -> None:
        """``configType`` 一个注解都没有 —— 传 ``"X"`` 也能入库。"""
        body = {"configName": "n", "configKey": "k", "configValue": "v", "configType": "X"}

        assert http.post("/system/config", json=body).json()["code"] == 200
        assert service.of("insert_config")[0][1].config_type == "X"

    def test_validation_runs_before_the_permission_check(
        self, http_anonymous: TestClient
    ) -> None:
        """Spring MVC 先解析/校验参数，再进方法代理（``@PreAuthorize``）。"""
        response = http_anonymous.post("/system/config", json={})

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "参数名称不能为空"}
