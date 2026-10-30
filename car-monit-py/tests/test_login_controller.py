"""``SysLoginController`` -- ``/login`` / ``/getInfo`` / ``/getRouters``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysLoginController.java
#   + ruoyi-admin/.../web/util/CommonUtil.java (password gate)

Why the password gate gets its own class
----------------------------------------
It is the one check that runs **before** ``SysLoginService``, so it decides three things at
once: whether a captcha is consumed, whether a ``sys_logininfor`` row is written, and whether
``"username"/"password"`` are even looked at. Java puts it in the controller, and several
"why is my audit log empty" reports trace back to it. Pinned here so a future refactor that
moves it into the service is caught.

Why ``/getInfo`` and ``/getRouters`` are tested against the real service
-----------------------------------------------------------------------
``getRouters`` returns ``List<RouterVo>``, and whether ``"name"`` / ``"meta"`` appear in the
JSON is decided by ``@JsonInclude(NON_EMPTY)`` on the VO, not by the service. The assertions
therefore go through ``RouterVo.to_json_dict()`` -- the same dump FastAPI's
``jsonable_encoder`` performs -- so the omission rules are verified, not assumed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

import pytest
from fastapi.encoders import jsonable_encoder

from app.api.system import sys_login_controller as controller
from app.api.system.sys_login_controller import (
    NO_USER_ID_FALLBACK,
    PASSWORD_INVALID_MESSAGE,
    get_info,
    get_routers,
    login,
    reset_login_controller,
)
from app.common.core.domain.entity.sys_menu import SysMenu
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_body import LoginBody
from app.common.core.domain.model.login_user import LoginUser
from app.common.exception.exceptions import CustomException
from app.common.utils import security_utils as security_utils_module
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.framework.web.service.sys_permission_service import SysPermissionService
from app.system.service.sys_menu_service import SysMenuService

#: Java: the literal in ``SysLoginController#login``. Spelled out rather than imported from
#: ``CommonUtil`` so a change to the message fails a test instead of following silently.
EXPECTED_PASSWORD_MESSAGE = (
    "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！"
)


# --------------------------------------------------------------------------- fakes


class _RecordingLoginService:
    """``SysLoginService`` that records its arguments and returns a fixed token."""

    def __init__(self, token: str = "eyJhbGciOiJIUzI1NiJ9.token", error: Optional[BaseException] = None) -> None:
        self.token = token
        self.error = error
        self.calls: List[Dict[str, Any]] = []

    def login(
        self,
        username: Optional[str],
        password: Optional[str],
        code: Optional[str] = None,
        uuid: Optional[str] = None,
    ) -> str:
        # Positional order matters: Java passes (username, password, code, uuid).
        self.calls.append(
            {"username": username, "password": password, "code": code, "uuid": uuid}
        )
        if self.error is not None:
            raise self.error
        return self.token


class _StubPermissionService:
    """``SysPermissionService`` returning fixed sets and recording its arguments."""

    def __init__(self, roles: Optional[Set[str]] = None, perms: Optional[Set[str]] = None) -> None:
        self._roles = roles if roles is not None else set()
        self._perms = perms if perms is not None else set()
        self.role_calls: List[Optional[SysUser]] = []
        self.menu_calls: List[Optional[SysUser]] = []

    def get_role_permission(self, user: Optional[SysUser]) -> Set[str]:
        self.role_calls.append(user)
        return self._roles

    def get_menu_permission(self, user: Optional[SysUser]) -> Set[str]:
        self.menu_calls.append(user)
        return self._perms


class _TreeMapper:
    """``SysMenuMapper`` returning prepared rows for the two tree queries."""

    def __init__(self, rows: List[SysMenu], all_rows: Optional[List[SysMenu]] = None) -> None:
        self._rows = rows
        self._all_rows = all_rows if all_rows is not None else rows
        self.user_calls: List[int] = []
        self.all_calls = 0

    def select_menu_tree_all(self) -> List[SysMenu]:
        self.all_calls += 1
        return list(self._all_rows)

    def select_menu_tree_by_user_id(self, user_id: int) -> List[SysMenu]:
        self.user_calls.append(user_id)
        return list(self._rows)


# --------------------------------------------------------------------------- helpers


def make_user(user_id: int = 2, user_name: str = "ry") -> SysUser:
    return SysUser(user_id=user_id, user_name=user_name, nick_name=user_name)


def make_menu(
    menu_id: int,
    parent_id: int,
    menu_name: str,
    menu_type: str = "C",
    path: Optional[str] = None,
    component: Optional[str] = None,
    visible: str = "0",
    is_frame: str = "1",
    is_cache: str = "0",
) -> SysMenu:
    return SysMenu(
        menu_id=menu_id,
        parent_id=parent_id,
        menu_name=menu_name,
        menu_type=menu_type,
        path=path,
        component=component,
        visible=visible,
        is_frame=is_frame,
        is_cache=is_cache,
        status="0",
    )


def authenticate(user: SysUser) -> LoginUser:
    """Install ``user`` as the authenticated principal, as the JWT filter would."""
    login_user = LoginUser(user=user, permissions=set())
    # Three-argument constructor -> ``authenticated = True``, like Spring's.
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return login_user


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def _isolate() -> Any:
    """Java ``@DirtiesContext``: no principal and no cached collaborators leak between tests."""
    SecurityContextHolder.clear_context()
    reset_login_controller()
    yield
    SecurityContextHolder.clear_context()
    reset_login_controller()


def use_login_service(
    monkeypatch: pytest.MonkeyPatch, service: _RecordingLoginService
) -> _RecordingLoginService:
    monkeypatch.setattr(controller, "_LOGIN_SERVICE", service)
    return service


def use_permission_service(
    monkeypatch: pytest.MonkeyPatch, service: _StubPermissionService
) -> _StubPermissionService:
    monkeypatch.setattr(controller, "_PERMISSION_SERVICE", service)
    return service


def use_menu_service(
    monkeypatch: pytest.MonkeyPatch, mapper: _TreeMapper
) -> SysMenuService:
    service = SysMenuService(mapper=mapper)  # type: ignore[arg-type]
    monkeypatch.setattr(controller, "_MENU_SERVICE", service)
    return service


# --------------------------------------------------------------------------- /login: password gate


class TestLoginPasswordGate:
    """``CommonUtil.checkPassword`` runs before anything else -- see the module docstring."""

    def test_a_weak_password_is_rejected_with_the_java_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = use_login_service(monkeypatch, _RecordingLoginService())

        result = login(LoginBody(username="ry", password="abc"))

        assert result == {"code": 500, "msg": PASSWORD_INVALID_MESSAGE}
        assert service.calls == []

    def test_the_message_is_the_one_the_frontend_matches(self) -> None:
        assert PASSWORD_INVALID_MESSAGE == EXPECTED_PASSWORD_MESSAGE

    def test_a_missing_password_is_rejected_with_the_same_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``isNull(null)`` -> ``""`` -> pattern fails. No 400, no "password required"."""
        service = use_login_service(monkeypatch, _RecordingLoginService())

        result = login(LoginBody(username="ry"))

        assert result["code"] == 500
        assert result["msg"] == PASSWORD_INVALID_MESSAGE
        assert service.calls == []

    @pytest.mark.parametrize(
        ("password", "why"),
        [
            ("Ab1!", "shorter than 8"),
            ("Abcdefg1!Abcdefg1!Abc", "longer than 20"),
            ("abc1234!", "no uppercase letter"),
            ("ABC1234!", "no lowercase letter"),
            ("Abcdefg!", "no digit"),
            ("Abcdefg1", "no symbol"),
            ("abcdefgh", "letters only"),
            ("", "empty"),
        ],
    )
    def test_each_missing_character_class_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, password: str, why: str
    ) -> None:
        service = use_login_service(monkeypatch, _RecordingLoginService())

        assert login(LoginBody(username="ry", password=password))["code"] == 500, why
        assert service.calls == []

    @pytest.mark.parametrize(
        ("password", "why"),
        [
            ("Abcde1!x", "exactly 8 characters -- the lower bound is inclusive"),
            ("Abcdefg1!Abcdefg1!Ab", "exactly 20 characters -- the upper bound is inclusive"),
            ("Abcdefg1!", "the ordinary case"),
        ],
    )
    def test_a_compliant_password_passes_the_gate(
        self, monkeypatch: pytest.MonkeyPatch, password: str, why: str
    ) -> None:
        service = use_login_service(monkeypatch, _RecordingLoginService())

        assert login(LoginBody(username="ry", password=password))["code"] == 200, why
        assert len(service.calls) == 1

    def test_the_length_is_measured_after_trimming(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """21 raw characters, 9 after ``trim()``: Java accepts it, so must we."""
        service = use_login_service(monkeypatch, _RecordingLoginService())
        padded = " " * 22 + "Abc12345!"

        assert len(padded) == 31
        assert login(LoginBody(username="ry", password=padded))["code"] == 200
        assert len(service.calls) == 1

    def test_the_password_is_forwarded_untrimmed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The gate trims; ``login()`` gets the raw value. Both halves are Java's."""
        service = use_login_service(monkeypatch, _RecordingLoginService())
        padded = "  Abc12345!  "

        login(LoginBody(username="ry", password=padded))

        assert service.calls[0]["password"] == padded

    def test_a_rejected_password_never_reaches_the_audit_log(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No captcha is consumed either -- ``SysLoginService.login`` is the only writer."""
        service = use_login_service(monkeypatch, _RecordingLoginService())

        login(LoginBody(username="ry", password="abc", code="1", uuid="u"))

        assert service.calls == []


# --------------------------------------------------------------------------- /login: success


class TestLoginEnvelope:
    """``AjaxResult.success()`` + ``put(Constants.TOKEN, token)``."""

    def test_the_token_lands_under_the_key_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_login_service(monkeypatch, _RecordingLoginService(token="a.b.c"))

        result = login(LoginBody(username="ry", password="Abcdefg1!"))

        assert result["token"] == "a.b.c"
        assert result["code"] == 200
        assert result["msg"] == "操作成功"

    def test_the_key_order_is_msg_code_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``AjaxResult`` 是 ``HashMap``，所以键序是**桶序**：msg(0) -> code(3) -> token(15)。"""
        use_login_service(monkeypatch, _RecordingLoginService())

        result = login(LoginBody(username="ry", password="Abcdefg1!"))

        assert list(result.keys()) == ["msg", "code", "token"]

    def test_the_response_carries_no_data_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_login_service(monkeypatch, _RecordingLoginService())

        assert "data" not in login(LoginBody(username="ry", password="Abcdefg1!"))

    def test_the_four_arguments_are_forwarded_in_java_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = use_login_service(monkeypatch, _RecordingLoginService())

        login(
            LoginBody(
                username="ry", password="Abcdefg1!", code="12", uuid="8f3c-uuid"
            )
        )

        assert service.calls == [
            {"username": "ry", "password": "Abcdefg1!", "code": "12", "uuid": "8f3c-uuid"}
        ]

    def test_an_omitted_uuid_is_forwarded_as_the_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``LoginBody.uuid`` is initialised to ``""`` in Java, not left null."""
        service = use_login_service(monkeypatch, _RecordingLoginService())

        login(LoginBody(username="ry", password="Abcdefg1!"))

        assert service.calls[0]["uuid"] == ""

    def test_an_explicit_null_uuid_is_forwarded_as_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A JSON ``"uuid": null`` overrides the initialiser -- Redis key becomes ``...null``."""
        service = use_login_service(monkeypatch, _RecordingLoginService())

        login(LoginBody.model_validate({"username": "ry", "password": "Abcdefg1!", "uuid": None}))

        assert service.calls[0]["uuid"] is None

    def test_login_failures_are_not_swallowed_by_the_controller(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java has no ``try`` here: the exception must reach ``GlobalExceptionHandler``."""
        from app.common.exception.user import UserPasswordNotMatchException

        use_login_service(
            monkeypatch, _RecordingLoginService(error=UserPasswordNotMatchException())
        )

        with pytest.raises(UserPasswordNotMatchException):
            login(LoginBody(username="ry", password="Abcdefg1!"))


class TestLoginBody:
    """``LoginBody`` is a plain DTO -- no validation annotations in Java."""

    def test_uuid_defaults_to_the_empty_string(self) -> None:
        assert LoginBody().uuid == ""

    def test_username_and_password_default_to_none(self) -> None:
        body = LoginBody()
        assert body.username is None
        assert body.password is None
        assert body.code is None

    def test_unknown_properties_are_ignored(self) -> None:
        """Spring Boot disables ``FAIL_ON_UNKNOWN_PROPERTIES`` -- no 400 for an extra key."""
        body = LoginBody.model_validate(
            {"username": "ry", "password": "x", "rememberMe": True}
        )
        assert body.username == "ry"

    def test_the_four_wire_names_are_lower_case(self) -> None:
        dumped = LoginBody(username="ry", password="p", code="c", uuid="u").to_json_dict()
        assert set(dumped) == {"username", "password", "code", "uuid"}


# --------------------------------------------------------------------------- /getInfo


class TestGetInfo:
    """``GET /getInfo`` -- the payload the Vue store unpacks on every page load."""

    def test_an_admin_gets_the_admin_role_and_the_star_permission(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=1, user_name="admin"))
        # The real service, so the ``admin`` shortcut is exercised rather than stubbed.
        monkeypatch.setattr(controller, "_PERMISSION_SERVICE", SysPermissionService())

        result = get_info()

        assert result["roles"] == ["admin"]
        assert result["permissions"] == ["*:*:*"]

    def test_a_regular_user_gets_sorted_lists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        use_permission_service(
            monkeypatch,
            _StubPermissionService(
                roles={"common", "auditor"}, perms={"system:user:edit", "system:user:list"}
            ),
        )

        result = get_info()

        # Java emits a HashSet -> unspecified order; sorted here so the body is stable.
        assert result["roles"] == ["auditor", "common"]
        assert result["permissions"] == ["system:user:edit", "system:user:list"]

    def test_an_empty_permission_set_is_an_empty_array(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        use_permission_service(monkeypatch, _StubPermissionService())

        result = get_info()

        assert result["roles"] == []
        assert result["permissions"] == []

    def test_the_key_order_matches_java(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        use_permission_service(monkeypatch, _StubPermissionService())

        # Java: ``HashMap`` 桶序 —— msg(0) -> code(3) -> pjFlag(3) -> overdue(4)
        # -> permissions(6) -> roles(7) -> user(13)；pjFlag/code 同桶时保持 put 序。
        # 这与线上 RuoYi ``getInfo`` 的真实负载顺序一致（msg、code 打头）。
        assert list(get_info().keys()) == [
            "msg",
            "code",
            "pjFlag",
            "overdue",
            "permissions",
            "roles",
            "user",
        ]

    def test_pj_flag_and_overdue_are_hard_coded_literals(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        use_permission_service(monkeypatch, _StubPermissionService())

        result = get_info()

        assert result["pjFlag"] == 0
        assert result["overdue"] is False

    def test_the_user_object_is_the_authenticated_one(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user = make_user(user_id=7, user_name="zhangsan")
        authenticate(user)
        permissions = use_permission_service(monkeypatch, _StubPermissionService())

        get_info()

        assert permissions.role_calls == [user]
        assert permissions.menu_calls == [user]

    def test_the_user_payload_is_camel_case_and_hides_the_password(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(SysUser(user_id=2, user_name="ry", password="$2a$10$hash"))
        use_permission_service(monkeypatch, _StubPermissionService())

        payload = get_info()["user"].to_json_dict()

        assert payload["userName"] == "ry"
        assert payload["userId"] == 2
        # ``@JsonIgnore`` + ``@JsonProperty`` on the getter -> write-only.
        assert "password" not in payload
        # ``isAdmin()`` is a virtual Jackson property, always emitted.
        assert payload["admin"] is False

    def test_the_user_payload_survives_the_fastapi_encoder(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The controller hands the *model* to ``AjaxResult``; prove FastAPI can dump it.

        ``jsonable_encoder`` is what ``serialize_response`` runs when ``response_model`` is
        ``None``, so this is the last mile of ``GET /getInfo`` without needing a live token.
        """
        authenticate(SysUser(user_id=2, user_name="ry", password="$2a$10$hash"))
        use_permission_service(
            monkeypatch, _StubPermissionService(roles={"common"}, perms={"system:user:list"})
        )

        encoded = jsonable_encoder(get_info())

        assert encoded["user"]["userName"] == "ry"
        assert encoded["user"]["userId"] == 2
        assert "password" not in encoded["user"]
        assert encoded["user"]["admin"] is False
        assert encoded["roles"] == ["common"]
        assert encoded["permissions"] == ["system:user:list"]
        assert encoded["pjFlag"] == 0
        assert encoded["overdue"] is False

    def test_without_an_authentication_the_call_raises_custom_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``SecurityUtils.getLoginUser()`` -> ``CustomException("获取用户信息异常")``."""
        use_permission_service(monkeypatch, _StubPermissionService())

        with pytest.raises(CustomException) as caught:
            get_info()

        assert "获取用户信息异常" in str(caught.value)


# --------------------------------------------------------------------------- /getRouters


class TestGetRouters:
    """``GET /getRouters`` -- flat rows -> tree -> ``RouterVo``."""

    def test_the_tree_query_uses_the_authenticated_user_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        mapper = use_menu_service(monkeypatch, _TreeMapper([])).mapper

        get_routers()

        assert mapper.user_calls == [2]
        assert mapper.all_calls == 0

    def test_an_admin_reads_every_menu(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=1, user_name="admin"))
        mapper = use_menu_service(
            monkeypatch, _TreeMapper(rows=[], all_rows=[make_menu(1, 0, "系统管理", "M", "system")])
        ).mapper

        get_routers()

        assert mapper.all_calls == 1
        assert mapper.user_calls == []

    def test_the_envelope_wraps_the_list_in_data(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``AjaxResult.success(menus)`` -> ``data``, never the top-level key."""
        authenticate(make_user(user_id=2))
        use_menu_service(monkeypatch, _TreeMapper([make_menu(5, 0, "工具", "M", "tool")]))

        result = get_routers()

        assert set(result) == {"code", "msg", "data"}
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 1

    def test_no_menu_at_all_yields_an_empty_data_array(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        use_menu_service(monkeypatch, _TreeMapper([]))

        assert get_routers()["data"] == []

    def test_a_directory_with_children_becomes_a_nested_route(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        use_menu_service(
            monkeypatch,
            _TreeMapper(
                [
                    make_menu(1, 0, "系统管理", "M", "system"),
                    make_menu(100, 1, "用户管理", "C", "user", "system/user/index"),
                ]
            ),
        )

        payload = get_routers()["data"][0].to_json_dict()

        assert payload["name"] == "System"
        assert payload["path"] == "/system"
        assert payload["component"] == "Layout"
        assert payload["redirect"] == "noRedirect"
        assert payload["alwaysShow"] is True
        assert payload["hidden"] is False
        assert payload["meta"] == {"title": "系统管理", "icon": None, "noCache": False, "link": None}
        child = payload["children"][0]
        assert child["name"] == "User"
        assert child["path"] == "user"
        assert child["component"] == "system/user/index"

    def test_a_top_level_menu_item_loses_name_and_meta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``@JsonInclude(NON_EMPTY)`` on ``RouterVo``: ``""``/``null`` keys disappear."""
        authenticate(make_user(user_id=2))
        use_menu_service(
            monkeypatch,
            _TreeMapper([make_menu(5, 0, "工具", "C", "tool", "tool/index")]),
        )

        payload = get_routers()["data"][0].to_json_dict()

        assert payload["path"] == "/"
        assert payload["component"] == "Layout"
        # ``getRouteName`` returns "" for a menu frame -> omitted.
        assert "name" not in payload
        # ``router.setMeta(null)`` -> omitted.
        assert "meta" not in payload
        # A primitive boolean is never suppressed by NON_EMPTY.
        assert payload["hidden"] is False
        child = payload["children"][0]
        assert child["name"] == "Tool"
        assert child["path"] == "tool"
        assert child["meta"]["title"] == "工具"

    def test_a_hidden_menu_sets_the_hidden_flag(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        authenticate(make_user(user_id=2))
        use_menu_service(
            monkeypatch, _TreeMapper([make_menu(5, 0, "工具", "M", "tool", visible="1")])
        )

        assert get_routers()["data"][0].to_json_dict()["hidden"] is True

    def test_the_missing_user_id_fallback_is_preserved(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``-9999L`` is dead code in Java; keep it and prove it still works."""
        authenticate(make_user(user_id=2))
        monkeypatch.setattr(security_utils_module, "get_user_id", lambda: None)
        mapper = use_menu_service(monkeypatch, _TreeMapper([])).mapper

        get_routers()

        assert mapper.user_calls == [NO_USER_ID_FALLBACK]

    def test_the_router_list_survives_the_fastapi_encoder(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The ``NON_EMPTY`` omissions must still hold after FastAPI dumps the list."""
        authenticate(make_user(user_id=2))
        use_menu_service(
            monkeypatch,
            _TreeMapper([make_menu(5, 0, "工具", "C", "tool", "tool/index")]),
        )

        encoded = jsonable_encoder(get_routers())

        root = encoded["data"][0]
        assert root["path"] == "/"
        assert "name" not in root
        assert "meta" not in root
        assert root["hidden"] is False
        assert root["children"][0]["meta"]["title"] == "工具"

    def test_without_an_authentication_the_call_raises_custom_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``SecurityUtils.getUserId()`` -> ``CustomException("获取用户账户异常")``."""
        use_menu_service(monkeypatch, _TreeMapper([]))

        with pytest.raises(CustomException) as caught:
            get_routers()

        assert "获取用户账户异常" in str(caught.value)


# --------------------------------------------------------------------------- HTTP wiring


class TestRoutesOverHttp:
    """The routes are registered and protected exactly like the Java endpoints.

    These go through ``TestClient`` (session-scoped ``client`` fixture) so the
    ``SecurityMiddleware`` rule table and the exception handlers are in the loop. None of
    them needs a database: one short-circuits on the password gate, the others are refused
    by the filter chain before routing.
    """

    def test_a_weak_password_answers_http_200_with_code_500(self, client: Any) -> None:
        response = client.post("/login", json={"username": "ry", "password": "abc"})

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": PASSWORD_INVALID_MESSAGE}

    def test_a_missing_body_is_an_error_envelope_not_a_400(self, client: Any) -> None:
        """Java: ``HttpMessageNotReadableException`` -> generic handler -> HTTP 200."""
        response = client.post("/login")

        assert response.status_code == 200
        assert response.json()["code"] == 500

    def test_get_info_without_a_token_is_unauthorized(self, client: Any) -> None:
        response = client.get("/getInfo")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 401
        assert "认证失败" in body["msg"]

    def test_get_routers_without_a_token_is_unauthorized(self, client: Any) -> None:
        response = client.get("/getRouters")

        assert response.status_code == 200
        assert response.json()["code"] == 401

    def test_login_only_accepts_post(self, client: Any) -> None:
        """``@PostMapping`` -> a GET is a 405 rendered as HTTP 200 + code 500."""
        response = client.get("/login")

        assert response.status_code == 200
        assert response.json() == {
            "code": 500,
            "msg": "Request method 'GET' not supported",
        }

    def test_get_info_only_accepts_get(self, client: Any) -> None:
        """A POST never reaches the route: the rule table refuses it first."""
        response = client.post("/getInfo")

        assert response.status_code == 200
        assert response.json()["code"] == 401
