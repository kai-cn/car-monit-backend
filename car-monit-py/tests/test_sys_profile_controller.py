"""``SysProfileController`` -- ``/system/user/profile`` 的 4 个映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysProfileController.java
#   + ruoyi-common/.../core/controller/BaseController.java

这一层测什么
------------
Service 已被 ``test_sys_user_service.py`` 覆盖、工具被 ``test_file_upload_utils.py``
覆盖，所以这里全部注入假 Service，只测**控制器自己的判断**：

* 路由注册：4 条，且**必须在 ``sys_user_router`` 之前**（否则 ``/system/user/profile``
  会被 ``/{user_id}`` 吃掉）；
* **四个端点都只有登录要求**，没有任何 ``@PreAuthorize``；
* ``profile`` 返回的是**缓存里的** ``SysUser`` + 两个 group 串；
* ``updateProfile`` 的两道唯一性闸门与 4 个字段的缓存回写；
* ``updatePwd`` 的**判断顺序**（旧密码 -> 新旧相同 -> 复杂度）；
* ``avatar`` 的空文件短路、落盘 url、缓存回写。

登录态从哪来
------------
与其他控制器不同，本控制器**不读** ``SecurityContextHolder``，而是
``tokenService.getLoginUser(request)``。所以用例里只替换 ``_TOKEN_SERVICE``，
不需要 ``authenticate()`` —— 这一点本身就是被测行为（见
``TestProfile::test_the_login_user_comes_from_the_token_service``）。

两种驱动方式
------------
* 直调函数：能拿到 ``AjaxResult`` 对象本身，断言键序最直观；
* ``TestClient``：只有走 ASGI 栈才会真正解析``query``/``form``/``multipart`` 绑定。
  用**独立的 mini app**（只挂本控制器的 router + 异常处理器），避开
  ``SecurityMiddleware`` 对 MySQL/Redis 的依赖。
"""

from __future__ import annotations

import io
import os
import re
from typing import Any, Dict, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import Headers, UploadFile
from starlette.requests import Request

from app.api.system import sys_profile_controller as controller
from app.api.system.sys_profile_controller import (
    EDIT_EMAIL_EXISTS,
    EDIT_PHONE_EXISTS,
    OLD_PASSWORD_ERROR,
    PASSWORD_INVALID_MESSAGE,
    SAME_PASSWORD,
    UPLOAD_AVATAR_FAILED,
    UPDATE_PROFILE_FAILED,
    UPDATE_PWD_FAILED,
    avatar,
    profile,
    update_profile,
    update_pwd,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.utils import security_utils as SecurityUtils
from app.config.exception_handlers import (
    PARAMETER_ERROR_MESSAGE,
    register_exception_handlers,
)
from app.framework.web.service.permission_service import pre_authorize_permi
from app.settings import get_settings, reset_settings_cache

#: Java: ``UserConstants.UNIQUE_OLD`` / ``NOT_UNIQUE_OLD``
UNIQUE = "0"
NOT_UNIQUE = "1"

#: 能通过 ``CommonUtil.checkPassword`` 的密码（大/小写 + 数字 + 特殊符号，8 位以上）
NEW_PASSWORD = "Newpass1!"
#: 当前登录用户的（明文）旧密码
OLD_PASSWORD = "Oldpass1!"


# --------------------------------------------------------------------------- fakes


class _FakeUserService:
    """记录每一次调用；答案由用例配置。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.role_group = "超级管理员"
        self.post_group = "董事长"
        self.phone_unique = UNIQUE
        self.email_unique = UNIQUE
        self.profile_rows = 1
        self.avatar_updated = True
        self.reset_rows = 1

    # -- 查询 --------------------------------------------------------------
    def select_user_role_group(self, user_name: str) -> str:
        self.calls.append(("select_user_role_group", user_name))
        return self.role_group

    def select_user_post_group(self, user_name: str) -> str:
        self.calls.append(("select_user_post_group", user_name))
        return self.post_group

    # -- 校验 --------------------------------------------------------------
    def check_phone_unique(self, user: SysUser) -> str:
        self.calls.append(("check_phone_unique", user.phonenumber))
        return self.phone_unique

    def check_email_unique(self, user: SysUser) -> str:
        self.calls.append(("check_email_unique", user.email))
        return self.email_unique

    # -- 写 ----------------------------------------------------------------
    def update_user_profile(self, user: SysUser) -> int:
        self.calls.append(("update_user_profile", user.model_copy(deep=True)))
        return self.profile_rows

    def update_user_avatar(self, user_name: str, avatar_url: str) -> bool:
        self.calls.append(("update_user_avatar", user_name, avatar_url))
        return self.avatar_updated

    def reset_user_pwd(self, user_name: str, password: str) -> int:
        self.calls.append(("reset_user_pwd", user_name, password))
        return self.reset_rows

    # ----------------------------------------------------------------------
    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]

    def names(self) -> List[str]:
        return [call[0] for call in self.calls]


class _FakeTokenService:
    """Java: ``@Autowired TokenService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        #: ``None`` 用来模拟"令牌已过期" -> Java NPE。
        self.login_user: Optional[LoginUser] = _login_user()

    def get_login_user(self, request: Any) -> Optional[LoginUser]:
        self.calls.append(("get_login_user", request))
        return self.login_user

    def set_login_user(self, login_user: Optional[LoginUser]) -> None:
        self.calls.append(("set_login_user", login_user))

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _Fakes:
    def __init__(self) -> None:
        self.user = _FakeUserService()
        self.token = _FakeTokenService()


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def fakes(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者。"""
    bundle = _Fakes()
    monkeypatch.setattr(controller, "_USER_SERVICE", bundle.user)
    monkeypatch.setattr(controller, "_TOKEN_SERVICE", bundle.token)
    yield bundle
    controller.reset_profile_controller()


@pytest.fixture
def service(fakes: _Fakes) -> _FakeUserService:
    return fakes.user


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app())


@pytest.fixture
def http_lenient() -> Any:
    """把服务端异常也变成响应体的 mini app（``avatar`` 走 ``OSError`` 时需要）。"""
    return TestClient(_build_app(), raise_server_exceptions=False)


@pytest.fixture
def profile_dir(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> str:
    """把 ``ruoyi.profile`` 指到临时目录，头像才会真的写到可控的位置。"""
    target = (tmp_path / "uploadPath").as_posix()
    monkeypatch.setenv("RUOYI__PROFILE", target)
    reset_settings_cache()
    yield target
    monkeypatch.delenv("RUOYI__PROFILE", raising=False)
    reset_settings_cache()


def _build_app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(controller.router)
    return application


def _login_user(
    user_id: int = 2,
    user_name: str = "ry",
    password: Optional[str] = None,
    nick_name: str = "若依",
    phonenumber: str = "15888888888",
    email: str = "ry@qq.com",
    sex: str = "1",
    avatar_url: str = "",
) -> LoginUser:
    return LoginUser(
        token="uuid-of-session",
        user=SysUser(
            user_id=user_id,
            user_name=user_name,
            nick_name=nick_name,
            phonenumber=phonenumber,
            email=email,
            sex=sex,
            avatar=avatar_url,
            password=password if password is not None else SecurityUtils.encrypt_password(OLD_PASSWORD),
        ),
        permissions={"*:*:*"},
    )


def _request() -> Any:
    """直调函数时用的最小 ``Request``（``get_login_user`` 被替换，不会读它）。"""
    return Request({"type": "http", "method": "GET", "path": "/system/user/profile", "headers": []})


def _picture(
    data: bytes = b"png-bytes",
    filename: str = "avatar.png",
    content_type: Optional[str] = "image/png",
) -> UploadFile:
    """构造与 multipart 解析结果同形的 ``UploadFile``。"""
    headers = Headers({"content-type": content_type}) if content_type is not None else None
    return UploadFile(
        file=io.BytesIO(data), size=len(data), filename=filename, headers=headers
    )


def _body(**overrides: Any) -> SysUser:
    fields: Dict[str, Any] = {
        "user_name": "ry",
        "nick_name": "新昵称",
        "phonenumber": "15900000000",
        "email": "new@qq.com",
        "sex": "0",
    }
    fields.update(overrides)
    return SysUser(**fields)


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    """4 个映射的路径 / 动词，以及"没有权限点"。"""

    def test_the_four_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/user/profile", ("GET",)),
            ("/system/user/profile", ("PUT",)),
            ("/system/user/profile/updatePwd", ("PUT",)),
            ("/system/user/profile/avatar", ("POST",)),
        }

    def test_the_profile_router_is_registered_before_the_user_router(self) -> None:
        """``GET /system/user/{user_id}`` 会把 ``/system/user/profile`` 吃掉。

        app.main 用 ``_IncludedRouter`` 包装子路由，顶层 ``create_app().routes``
        没有 ``path`` 属性；直接检查 app.router 展开后的实际匹配顺序。
        """
        from app.main import create_app

        # app.main 用 _IncludedRouter 延迟装配，create_app().routes 顶层拿不到展平路径；
        # 直接断言 include_router 的调用顺序（app/main.py 有对应注释与守卫）。
        import inspect
        from app import main as app_main

        source = inspect.getsource(app_main.create_app)
        assert source.index("include_router(sys_profile_router)") < source.index(
            "include_router(sys_user_router)"
        )

    def test_no_endpoint_carries_a_permission_point(self) -> None:
        """Java 里这四个方法**一个 ``@PreAuthorize`` 都没有** —— 改自己的资料不需要授权。"""
        for route in controller.router.routes:
            dependencies = [dep.call for dep in route.dependant.dependencies]
            assert pre_authorize_permi not in dependencies, route.path

    def test_the_router_prefix_is_the_java_request_mapping(self) -> None:
        assert controller.router.prefix == "/system/user/profile"


# --------------------------------------------------------------------------- 个人信息


class TestProfile:
    """``GET /system/user/profile``."""

    def test_it_returns_the_cached_user_as_data(self, service: _FakeUserService) -> None:
        result = profile(_request())

        assert result["code"] == 200
        assert result["msg"] == "操作成功"
        # data 是**缓存里的那个** SysUser 投影（parity commit 62b8dbec 起输出 camelCase dict，
        # 与 Java Jackson 形状一致），不是重新查库的结果。
        assert isinstance(result["data"], dict)
        assert result["data"]["userName"] == "ry"

    def test_it_adds_the_role_and_post_groups(self, service: _FakeUserService) -> None:
        service.role_group = "普通角色"
        service.post_group = "项目经理"

        result = profile(_request())

        assert result["roleGroup"] == "普通角色"
        assert result["postGroup"] == "项目经理"

    def test_the_key_order_matches_the_hash_map_bucket_order(self) -> None:
        """``AjaxResult`` 是 ``HashMap``：msg(0) -> postGroup(0) -> code(3) -> data(4)

        -> roleGroup(13)。msg 与 postGroup 同桶时，保持先 msg 后 postGroup 的 put 序。
        """
        result = profile(_request())

        assert list(result.keys()) == ["msg", "postGroup", "code", "data", "roleGroup"]

    def test_the_groups_are_queried_by_user_name(self, service: _FakeUserService) -> None:
        profile(_request())

        assert service.of("select_user_role_group") == [("select_user_role_group", "ry")]
        assert service.of("select_user_post_group") == [("select_user_post_group", "ry")]

    def test_the_login_user_comes_from_the_token_service(self, fakes: _Fakes) -> None:
        """不读 ``SecurityContextHolder``：换掉 token 里的人，返回的 data 就跟着变。"""
        fakes.token.login_user = _login_user(user_id=9, user_name="other")

        result = profile(_request())

        assert result["data"]["userId"] == 9
        assert result["data"]["userName"] == "other"
        # 每次调用都重新问一次 tokenService（Java 也是逐次 getLoginUser）
        assert len(fakes.token.of("get_login_user")) == 1

    def test_a_null_login_user_is_not_guarded(self, fakes: _Fakes) -> None:
        """令牌过期时 Java 在 ``loginUser.getUser()`` 处 NPE，这里同样是未捕获的异常。"""
        fakes.token.login_user = None

        with pytest.raises(AttributeError):
            profile(_request())

    def test_over_http_the_user_is_serialised_in_camel_case(
        self, http: TestClient
    ) -> None:
        payload = http.get("/system/user/profile").json()

        assert payload["code"] == 200
        assert payload["data"]["userName"] == "ry"
        assert payload["data"]["nickName"] == "若依"
        assert payload["roleGroup"] == "超级管理员"
        assert payload["postGroup"] == "董事长"


# --------------------------------------------------------------------------- 改资料


class TestUpdateProfile:
    """``PUT /system/user/profile``."""

    def test_a_taken_phone_number_is_refused(self, service: _FakeUserService) -> None:
        service.phone_unique = NOT_UNIQUE

        result = update_profile(_request(), _body())

        assert result["code"] == 500
        assert result["msg"] == EDIT_PHONE_EXISTS.format("ry")
        # 第一道闸就返回，后面的写一次都没发生
        assert service.names() == ["check_phone_unique"]

    def test_a_taken_email_is_refused(self, service: _FakeUserService) -> None:
        service.email_unique = NOT_UNIQUE

        result = update_profile(_request(), _body())

        assert result["msg"] == EDIT_EMAIL_EXISTS.format("ry")
        assert service.names() == ["check_phone_unique", "check_email_unique"]

    def test_an_empty_phone_and_email_skip_the_uniqueness_checks(
        self, service: _FakeUserService
    ) -> None:
        # Java: StringUtils.isNotEmpty -> "" 不查重（清空手机号/邮箱是合法操作）
        result = update_profile(_request(), _body(phonenumber="", email=""))

        assert result["code"] == 200
        assert service.of("check_phone_unique") == []
        assert service.of("check_email_unique") == []

    def test_it_writes_the_four_fields_back_into_the_cache(self, fakes: _Fakes) -> None:
        user = _body(nick_name="改名了", phonenumber="15900000001", email="n@qq.com", sex="0")

        result = update_profile(_request(), user)

        assert result == {"code": 200, "msg": "操作成功"}
        cached = fakes.token.login_user.user
        assert cached.nick_name == "改名了"
        assert cached.phonenumber == "15900000001"
        assert cached.email == "n@qq.com"
        assert cached.sex == "0"
        # 回写之后必须刷新 Redis，否则下次拿到的还是旧资料
        assert len(fakes.token.of("set_login_user")) == 1

    def test_a_zero_row_update_returns_the_failure_message(
        self, service: _FakeUserService, fakes: _Fakes
    ) -> None:
        service.profile_rows = 0

        result = update_profile(_request(), _body())

        assert result["msg"] == UPDATE_PROFILE_FAILED
        # 失败时**不**回写缓存
        assert fakes.token.of("set_login_user") == []
        assert fakes.token.login_user.user.nick_name == "若依"

    def test_the_message_uses_the_user_name_from_the_request_body(
        self, service: _FakeUserService
    ) -> None:
        service.phone_unique = NOT_UNIQUE

        result = update_profile(_request(), _body(user_name="someone-else"))

        assert result["msg"] == "修改用户'someone-else'失败，手机号码已存在"

    def test_it_serialises_the_body_as_camel_case_over_http(
        self, http: TestClient, service: _FakeUserService
    ) -> None:
        response = http.put(
            "/system/user/profile",
            json={"userName": "ry", "nickName": "HTTP", "phonenumber": "", "sex": "1"},
        )

        assert response.json()["code"] == 200
        assert service.of("update_user_profile")[0][1].nick_name == "HTTP"


# --------------------------------------------------------------------------- 改密码


class TestUpdatePwd:
    """``PUT /system/user/profile/updatePwd``."""

    def _call(self, old: Optional[str], new: Optional[str], fakes: _Fakes) -> Any:
        """直调时绕开依赖注入：把 ``getParameter`` 的结果手工喂进去。"""
        parameters: Dict[str, str] = {}
        if old is not None:
            parameters["oldPassword"] = old
        if new is not None:
            parameters["newPassword"] = new
        return update_pwd(_request(), parameters)

    def test_a_wrong_old_password_is_refused(self, service: _FakeUserService, fakes: _Fakes) -> None:
        result = self._call("wrong", NEW_PASSWORD, fakes)

        assert result["msg"] == OLD_PASSWORD_ERROR
        assert service.names() == []

    def test_the_new_password_may_not_equal_the_old_one(
        self, service: _FakeUserService, fakes: _Fakes
    ) -> None:
        result = self._call(OLD_PASSWORD, OLD_PASSWORD, fakes)

        assert result["msg"] == SAME_PASSWORD
        assert service.names() == []

    def test_the_old_password_gate_runs_before_the_complexity_check(
        self, service: _FakeUserService, fakes: _Fakes
    ) -> None:
        """旧密码错 + 新密码太弱 -> 回"旧密码错误"（Java 的顺序）。"""
        result = self._call("wrong", "weak", fakes)

        assert result["msg"] == OLD_PASSWORD_ERROR

    def test_a_weak_new_password_is_refused_after_the_first_two_gates(
        self, service: _FakeUserService, fakes: _Fakes
    ) -> None:
        result = self._call(OLD_PASSWORD, "weak", fakes)

        assert result["msg"] == PASSWORD_INVALID_MESSAGE
        # 结尾是全角感叹号；SysUserController 那句没有
        assert result["msg"].endswith("！")
        assert service.names() == []

    def test_it_stores_an_encrypted_password_and_refreshes_the_cache(
        self, service: _FakeUserService, fakes: _Fakes
    ) -> None:
        result = self._call(OLD_PASSWORD, NEW_PASSWORD, fakes)

        assert result == {"code": 200, "msg": "操作成功"}
        stored = service.of("reset_user_pwd")[0]
        assert stored[1] == "ry"
        assert SecurityUtils.matches_password(NEW_PASSWORD, stored[2]) is True
        cached = fakes.token.login_user.user.password
        assert SecurityUtils.matches_password(NEW_PASSWORD, cached) is True
        # Java 两次独立加密：入库的哈希与缓存的哈希**不是同一个字符串**
        assert cached != stored[2]
        assert len(fakes.token.of("set_login_user")) == 1

    def test_a_zero_row_update_returns_the_failure_message(
        self, service: _FakeUserService, fakes: _Fakes
    ) -> None:
        service.reset_rows = 0

        result = self._call(OLD_PASSWORD, NEW_PASSWORD, fakes)

        assert result["msg"] == UPDATE_PWD_FAILED
        assert fakes.token.of("set_login_user") == []

    def test_the_two_passwords_are_read_from_the_query_string(
        self, http: TestClient, service: _FakeUserService
    ) -> None:
        response = http.put(
            "/system/user/profile/updatePwd",
            params={"oldPassword": OLD_PASSWORD, "newPassword": NEW_PASSWORD},
        )

        assert response.json()["code"] == 200
        assert service.of("reset_user_pwd")[0][1] == "ry"

    def test_the_two_passwords_are_also_read_from_a_form_body(
        self, http: TestClient, service: _FakeUserService
    ) -> None:
        """Java 走 ``getParameter``，form-urlencoded body 同样能绑上。"""
        response = http.put(
            "/system/user/profile/updatePwd",
            data={"oldPassword": OLD_PASSWORD, "newPassword": NEW_PASSWORD},
        )

        assert response.json()["code"] == 200
        assert len(service.of("reset_user_pwd")) == 1

    def test_a_missing_old_password_is_a_parameter_error(
        self, http_lenient: TestClient, service: _FakeUserService
    ) -> None:
        """缺参不是"旧密码错误"：Spring 抛 ``IllegalArgumentException``，落成 500.

        ValueError 归入"参数错误"（P1-6 的文案分流），原始异常只进日志。
        用 ``http_lenient`` 兼容两种 TestClient 行为。
        """
        response = http_lenient.put("/system/user/profile/updatePwd")

        payload = response.json()
        assert payload["code"] == 500
        assert payload["msg"] == PARAMETER_ERROR_MESSAGE
        assert service.names() == []

    def test_a_wrong_old_password_still_answers_the_business_message(
        self, http: TestClient, service: _FakeUserService
    ) -> None:
        """只要传了值（哪怕不对），就是业务文案而不是 500。"""
        response = http.put("/system/user/profile/updatePwd", params={"oldPassword": "wrong"})

        assert response.json()["msg"] == OLD_PASSWORD_ERROR
        assert service.names() == []


# --------------------------------------------------------------------------- 头像


class TestAvatar:
    """``POST /system/user/profile/avatar``."""

    def test_a_zero_byte_file_falls_through_to_the_failure_message(
        self, service: _FakeUserService, profile_dir: str
    ) -> None:
        result = avatar(_request(), _picture(data=b""))

        assert result["msg"] == UPLOAD_AVATAR_FAILED
        # 空文件既不动磁盘也不碰数据库
        assert service.names() == []

    def test_a_successful_upload_returns_the_url_and_refreshes_the_cache(
        self, service: _FakeUserService, fakes: _Fakes, profile_dir: str
    ) -> None:
        result = avatar(_request(), _picture())

        assert result["code"] == 200
        url = result["imgUrl"]
        assert re.fullmatch(r"/profile/avatar/\d{4}/\d{2}/\d{2}/avatar_\d{14}A\d{3}\.png", url)
        # 数据库里存的是相对 url
        stored = service.of("update_user_avatar")[0]
        assert stored[1] == "ry"
        assert stored[2] == url
        # 缓存里的头像同步更新
        assert fakes.token.login_user.user.avatar == url
        assert len(fakes.token.of("set_login_user")) == 1

    def test_a_failed_avatar_update_returns_the_failure_message(
        self, service: _FakeUserService, fakes: _Fakes, profile_dir: str
    ) -> None:
        service.avatar_updated = False

        result = avatar(_request(), _picture(data=b"x"))

        assert result["msg"] == UPLOAD_AVATAR_FAILED
        assert fakes.token.of("set_login_user") == []

    def test_over_http_the_part_name_is_avatarfile(
        self, http: TestClient, service: _FakeUserService, profile_dir: str
    ) -> None:
        response = http.post(
            "/system/user/profile/avatar",
            files={"avatarfile": ("avatar.png", b"png-bytes", "image/png")},
        )

        payload = response.json()
        assert payload["code"] == 200
        url = payload["imgUrl"]
        assert url.startswith("/profile/avatar/")
        written = get_settings().ruoyi.avatar_path + os.sep + url[len("/profile/avatar/") :]
        assert os.path.isfile(written)

    def test_a_disallowed_extension_keeps_the_upload_hint(
        self, http_lenient: TestClient, profile_dir: str
    ) -> None:
        response = http_lenient.post(
            "/system/user/profile/avatar",
            files={"avatarfile": ("a.exe", b"MZ", "application/x-msdownload")},
        )

        payload = response.json()
        # 校验类错误提升为业务异常后，客户端仍能看到"允许哪些后缀"的提示。
        assert payload["code"] == 500
        assert payload["msg"].startswith("文件[a.exe]后缀[exe]不正确，请上传")

    def test_a_missing_part_is_a_validation_error(
        self, http: TestClient, service: _FakeUserService
    ) -> None:
        """已知差异：Spring 对缺失的 ``@RequestParam`` part 回 **HTTP 400**（默认错误体），
        本项目的 ``RequestValidationError`` 处理器统一翻成 **HTTP 200 + code 500**。
        文案带上了字段名（``avatarfile Field required``），见 ``COMPATIBILITY.md`` §30.8。
        """
        response = http.post("/system/user/profile/avatar")

        payload = response.json()
        assert response.status_code == 200
        assert payload["code"] == 500
        assert "avatarfile" in payload["msg"]
        assert service.names() == []
