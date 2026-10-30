"""``SysDictTypeController`` -- ``/system/dict/type`` 的 8 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysDictTypeController.java

这一层测什么
------------
Service 已被 ``test_sys_dict_type_service.py`` 覆盖，所以全部注入假 Service，只测
**控制器自己的约定**：

* 8 个映射全部注册（``export`` 在 Phase 3.18 补上，返回文件名）；
* 权限点：``list`` / ``query`` / ``add`` / ``edit`` / ``remove``，而 ``optionselect``
  **没有** ``@PreAuthorize``（前端下拉框要用，加权限会白屏）；
* ``clearCache`` 是 ``DELETE /clearCache``，必须注册在 ``DELETE /{dictIds}`` **之前** ——
  否则会被当成 ``dictIds = "clearCache"`` 而在 ``parse_id_array`` 处抛错；
* 唯一性校验在写库**之前**，提示文案插的是 ``dictName``（不是 ``dictType``）。

``export`` 与 ``/{dictId}`` 的冲突
---------------------------------
两者都是 ``GET`` 且都是单段。Java 下由 ``AntPathMatcher`` 优先匹配字面量，Python 下
靠**注册顺序**，所以 ``/export`` 必须写在 ``/{dictId}`` 之前 —— 否则 ``"export"``
会转 ``int`` 失败 -> ``HTTP 200 + code 500``。:class:`TestRouteTable` 两边都钉住了。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_dict_type_controller as controller
from app.api.system.sys_dict_type_controller import (
    ADD_DICT_TYPE_EXISTS,
    EDIT_DICT_TYPE_EXISTS,
    add,
    clear_cache,
    edit,
    get_info,
    list_dict_types,
    optionselect,
    remove,
)
from app.common.core.domain.entity.sys_dict_type import SysDictType
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException, CustomException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

#: 一个能通过 ``@Validated`` 的请求体（``dictName`` / ``dictType`` 都是 ``@NotBlank``）。
VALID_BODY: Dict[str, Any] = {"dictName": "用户性别", "dictType": "sys_user_sex", "status": "0"}


# --------------------------------------------------------------------------- fakes


class _FakeDictTypeService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysDictType] = []
        self.all_result: List[SysDictType] = []
        self.by_id_result: Optional[SysDictType] = None
        self.unique_result = "0"
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        #: 打开后 ``delete_dict_type_by_ids`` 直接抛（复刻"已分配"的 ``CustomException``）。
        self.delete_exception: Optional[Exception] = None
        #: ``select_dict_type_list`` 被调用时挂起中的分页参数。
        self.page_taken: Any = None

    def select_dict_type_list(self, query: SysDictType) -> List[SysDictType]:
        self.calls.append(("select_dict_type_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_dict_type_all(self) -> List[SysDictType]:
        self.calls.append(("select_dict_type_all",))
        return self.all_result

    def select_dict_type_by_id(self, dict_id: int) -> Optional[SysDictType]:
        self.calls.append(("select_dict_type_by_id", dict_id))
        return self.by_id_result

    def check_dict_type_unique(self, entity: SysDictType) -> str:
        self.calls.append(("check_dict_type_unique", entity.model_copy(deep=True)))
        return self.unique_result

    def insert_dict_type(self, entity: SysDictType) -> int:
        self.calls.append(("insert_dict_type", entity.model_copy(deep=True)))
        return self.insert_result

    def update_dict_type(self, entity: SysDictType) -> int:
        self.calls.append(("update_dict_type", entity.model_copy(deep=True)))
        return self.update_result

    def clear_cache(self) -> None:
        self.calls.append(("clear_cache",))

    def delete_dict_type_by_ids(self, dict_ids: Sequence[int]) -> int:
        self.calls.append(("delete_dict_type_by_ids", list(dict_ids)))
        if self.delete_exception is not None:
            raise self.delete_exception
        return self.delete_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeDictTypeService()
    monkeypatch.setattr(controller, "_DICT_TYPE_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_dict_type_controller()


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


def _dict_type(dict_id: int = 1, dict_name: str = "用户性别") -> SysDictType:
    return SysDictType(dict_id=dict_id, dict_name=dict_name, dict_type="sys_user_sex")


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_eight_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/dict/type/list", ("GET",)),
            ("/system/dict/type/export", ("GET",)),
            ("/system/dict/type/optionselect", ("GET",)),
            ("/system/dict/type/{dict_id}", ("GET",)),
            ("/system/dict/type", ("POST",)),
            ("/system/dict/type", ("PUT",)),
            ("/system/dict/type/clearCache", ("DELETE",)),
            ("/system/dict/type/{dict_ids}", ("DELETE",)),
        }

    def test_export_comes_before_the_path_variable(self) -> None:
        """``/export`` 排在 ``/{dict_id}`` 后面的话 ``"export"`` 会转 int 失败。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/dict/type/export") < paths.index("/system/dict/type/{dict_id}")

    def test_clear_cache_comes_before_the_path_variable(self) -> None:
        """两个都是 ``DELETE``，顺序反了 ``clearCache`` 会被当成 id 列表。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/dict/type/clearCache") < paths.index(
            "/system/dict/type/{dict_ids}"
        )

    def test_literal_get_paths_come_before_the_path_variable(self) -> None:
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/dict/type/list") < paths.index("/system/dict/type/{dict_id}")
        assert paths.index("/system/dict/type/optionselect") < paths.index(
            "/system/dict/type/{dict_id}"
        )

    def test_the_list_beats_the_path_variable_over_http(self, http: TestClient) -> None:
        response = http.get("/system/dict/type/list")

        assert response.json().keys() == {"total", "rows", "code", "msg"}

    def test_optionselect_beats_the_path_variable_too(
        self, http: TestClient, service: Any
    ) -> None:
        response = http.get("/system/dict/type/optionselect")

        assert response.json()["code"] == 200
        assert service.of("select_dict_type_all") != []

    def test_clear_cache_is_not_treated_as_an_id_list(
        self, http: TestClient, service: Any
    ) -> None:
        response = http.delete("/system/dict/type/clearCache")

        assert response.json() == {"code": 200, "msg": "操作成功"}
        assert service.of("clear_cache") == [("clear_cache",)]
        assert service.of("delete_dict_type_by_ids") == []

    def test_export_does_not_fall_into_the_path_variable(
        self, http: TestClient, service: Any
    ) -> None:
        """``/export`` 不再被 ``/{dictId}`` 兜住，返回**文件名**（落在 ``msg``）。"""
        response = http.get("/system/dict/type/export")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"].endswith("_字典类型.xlsx")
        assert "data" not in body
        assert [call[0] for call in service.calls] == ["select_dict_type_list"]


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: list_dict_types(SysDictType()),
            lambda: get_info(1),
            lambda: add(SysDictType(dict_name="用户性别", dict_type="sys_user_sex")),
            lambda: edit(_dict_type()),
            lambda: remove("1"),
            lambda: clear_cache(),
        ],
    )
    def test_the_six_guarded_endpoints(self, service: Any, call: Any) -> None:
        with pytest.raises(AccessDeniedException):
            call()

        assert service.calls == []

    def test_optionselect_needs_no_permission(self, service: Any) -> None:
        """前端"字典类型"下拉框要用 —— 加权限会白屏。"""
        service.all_result = [_dict_type()]

        response = optionselect()

        assert response["code"] == 200
        assert [row.dict_id for row in response["data"]] == [1]

    def test_a_partial_permission_does_not_pass(self) -> None:
        authenticate(permissions={"system:dict:*"})

        with pytest.raises(AccessDeniedException):
            add(SysDictType(dict_name="用户性别", dict_type="sys_user_sex"))

    def test_an_access_denied_becomes_http_200_code_403(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.delete("/system/dict/type/1")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}


# --------------------------------------------------------------------------- list / optionselect


class TestListAndOptionselect:
    def test_the_page_is_started_before_the_query(self, service: Any) -> None:
        authenticate()

        list_dict_types(SysDictType())

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1

    def test_the_filters_are_passed_through(self, service: Any) -> None:
        authenticate()

        list_dict_types(SysDictType(dict_name="性别", status="0"))

        query = service.of("select_dict_type_list")[0][1]
        assert query.dict_name == "性别"
        assert query.status == "0"

    def test_optionselect_returns_the_full_list(self, service: Any) -> None:
        service.all_result = [_dict_type(1), _dict_type(2)]

        response = optionselect()

        assert len(response["data"]) == 2
        assert response["data"][0].dict_id == 1

    def test_optionselect_does_not_start_a_page(self, service: Any) -> None:
        """不分页 —— 它调的是 ``selectDictTypeAll``。"""
        optionselect()

        assert take_page() is None
        assert service.page_taken is None


# --------------------------------------------------------------------------- 详情


class TestGetInfo:
    def test_a_hit_returns_the_entity(self, service: Any) -> None:
        authenticate()
        service.by_id_result = _dict_type(5)

        response = get_info(5)

        assert response["code"] == 200
        assert response["data"].dict_id == 5

    def test_a_miss_omits_the_data_key(self, service: Any) -> None:
        """Java ``success(null)`` -> ``{"code":200,"msg":"操作成功"}``。"""
        authenticate()

        assert get_info(404) == {"code": 200, "msg": "操作成功"}


# --------------------------------------------------------------------------- add / edit


class TestAddAndEdit:
    def test_add_writes_the_user_name(self, service: Any) -> None:
        authenticate(user_name="ry")

        response = add(SysDictType(dict_name="用户性别", dict_type="sys_user_sex"))

        assert response["code"] == 200
        assert service.of("insert_dict_type")[0][1].create_by == "ry"

    def test_edit_writes_the_user_name(self, service: Any) -> None:
        authenticate(user_name="ry")

        edit(_dict_type())

        assert service.of("update_dict_type")[0][1].update_by == "ry"

    def test_add_rejects_a_duplicate_type(self, service: Any) -> None:
        authenticate()
        service.unique_result = "1"

        response = add(SysDictType(dict_name="用户性别", dict_type="sys_user_sex"))

        assert response == {"code": 500, "msg": ADD_DICT_TYPE_EXISTS.format("用户性别")}
        assert service.of("insert_dict_type") == []

    def test_edit_rejects_a_duplicate_type(self, service: Any) -> None:
        authenticate()
        service.unique_result = "1"

        response = edit(_dict_type())

        assert response == {"code": 500, "msg": EDIT_DICT_TYPE_EXISTS.format("用户性别")}
        assert service.of("update_dict_type") == []

    def test_the_conflict_message_shows_the_name_not_the_type(self, service: Any) -> None:
        """文案插的是 ``dictName`` —— Java 原文如此，别"修正"。"""
        authenticate()
        service.unique_result = "1"

        response = add(SysDictType(dict_name="用户性别", dict_type="sys_user_sex"))

        assert "用户性别" in response["msg"]
        assert "sys_user_sex" not in response["msg"]

    def test_the_unique_check_precedes_the_insert(self, service: Any) -> None:
        authenticate()

        add(SysDictType(dict_name="用户性别", dict_type="sys_user_sex"))

        names = [call[0] for call in service.calls]
        assert names == ["check_dict_type_unique", "insert_dict_type"]

    def test_a_new_entity_keeps_its_id_none(self, service: Any) -> None:
        """``insertDictType`` 没有 ``useGeneratedKeys``，所以 id 不会被回填。"""
        authenticate()
        entity = SysDictType(dict_name="用户性别", dict_type="sys_user_sex")

        add(entity)

        assert entity.dict_id is None

    def test_add_reports_a_failure_when_nothing_was_inserted(self, service: Any) -> None:
        authenticate()
        service.insert_result = 0

        assert add(SysDictType(dict_name="用户性别", dict_type="sys_user_sex"))["code"] == 500

    def test_edit_reports_a_failure_when_nothing_was_updated(self, service: Any) -> None:
        authenticate()
        service.update_result = 0

        assert edit(_dict_type())["code"] == 500


# --------------------------------------------------------------------------- remove / clearCache


class TestRemove:
    def test_comma_separated_ids_are_parsed(self, service: Any) -> None:
        authenticate()

        remove("1,2,3")

        assert service.of("delete_dict_type_by_ids") == [("delete_dict_type_by_ids", [1, 2, 3])]

    def test_a_single_id_is_a_one_element_array(self, service: Any) -> None:
        authenticate()

        remove("7")

        assert service.of("delete_dict_type_by_ids") == [("delete_dict_type_by_ids", [7])]

    def test_an_assigned_type_becomes_code_500(self, http: TestClient, service: Any) -> None:
        """Service 抛 ``CustomException`` -> 全局处理器渲染成 200 + 500，整批不删。"""
        service.delete_exception = CustomException("用户性别已分配,不能删除")

        response = http.delete("/system/dict/type/1")

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "用户性别已分配,不能删除"}

    def test_the_batch_failure_is_reported(self, service: Any) -> None:
        authenticate()
        service.delete_result = 0

        assert remove("1,2")["code"] == 500

    def test_clear_cache_returns_success_without_a_data_key(self, service: Any) -> None:
        authenticate()

        assert clear_cache() == {"code": 200, "msg": "操作成功"}
        assert service.calls == [("clear_cache",)]


# --------------------------------------------------------------------------- 校验


class TestValidationRunsBeforePermission:
    """未登录 + 非法请求体 -> 500（校验先跑）；合法请求体 -> 403。"""

    def test_a_missing_name_is_reported_before_the_403(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post("/system/dict/type", json={"dictType": "sys_user_sex"})

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "字典名称不能为空"}

    def test_a_missing_type_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post("/system/dict/type", json={"dictName": "用户性别"})

        assert response.json() == {"code": 500, "msg": "字典类型不能为空"}

    def test_the_first_violation_wins(self, http_anonymous: TestClient) -> None:
        """全部为空时报 ``dictName`` —— ``DICT_TYPE_CONSTRAINTS`` 的顺序即 getter 顺序。"""
        response = http_anonymous.post("/system/dict/type", json={})

        assert response.json() == {"code": 500, "msg": "字典名称不能为空"}

    def test_an_overlong_name_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dict/type", json={"dictName": "名" * 101, "dictType": "sys_user_sex"}
        )

        assert response.json() == {"code": 500, "msg": "字典类型名称长度不能超过100个字符"}

    def test_an_overlong_type_carries_the_doubled_word(self, http_anonymous: TestClient) -> None:
        """原文就是"字典类型**类型**长度..." —— 复制粘贴笔误，照抄。"""
        response = http_anonymous.post(
            "/system/dict/type", json={"dictName": "用户性别", "dictType": "t" * 101}
        )

        assert response.json() == {"code": 500, "msg": "字典类型类型长度不能超过100个字符"}

    def test_a_valid_body_reaches_the_permission_check(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post("/system/dict/type", json=dict(VALID_BODY))

        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}

    def test_the_full_body_round_trips(self, http: TestClient) -> None:
        response = http.post("/system/dict/type", json=dict(VALID_BODY))

        assert response.json() == {"code": 200, "msg": "操作成功"}
