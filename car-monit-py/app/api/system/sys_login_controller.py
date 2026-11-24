"""登录验证.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysLoginController.java

Three endpoints, and the security rules that apply to each:

=============  ==============  ===========================================
Java           Access          Notes
=============  ==============  ===========================================
``POST /login``     ``permitAll``   the only unauthenticated write endpoint
``GET /getInfo``    authenticated   ``anyRequest().authenticated()``
``GET /getRouters`` authenticated   ``anyRequest().authenticated()``
=============  ==============  ===========================================

``POST /login`` does two things Java's ``SysLoginService`` does **not**
------------------------------------------------------------------------
The password-strength check lives in the *controller*, before any captcha or
credential check::

    String curPassword = CommonUtil.isNull(loginBody.getPassword());
    if (CommonUtil.checkPassword(curPassword)) {
        return AjaxResult.error("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！");
    }

Consequences that are easy to get wrong when reading ``SysLoginService`` alone:

* a short/weak password never reaches ``login()``, so **no captcha is consumed**
  and **no ``sys_logininfor`` row is written** -- the answer is still
  ``{"code":500,...}`` with HTTP 200, but it is not an audit event;
* a password with surrounding whitespace is validated on the *trimmed* value
  (``isNull`` trims) and then passed to ``login()`` **untrimmed**, so
  ``" Abc1234! "`` passes the pattern but is compared against bcrypt with its
  spaces. Mirrored exactly -- do not "fix" either half.
* the check runs on an **absent** password too: ``null`` -> ``""`` -> pattern
  fails -> the same message. There is no 400 for a missing field.

``getInfo`` payload
-------------------
``{code, msg, user, roles, permissions, pjFlag, overdue}`` -- in that order.
``pjFlag`` (``0``) and ``overdue`` (``false``) are hard-coded literals in Java; the
frontend reads them to decide whether to show the "overdue password" modal. The
commented-out tenant block above them in Java is a comment, not behaviour.

``roles`` / ``permissions`` are ``HashSet<String>`` in Java, so Jackson emits them in an
**unspecified** order. They are sorted here: same JSON shape, but a stable body. No client
can depend on the Java order, so this cannot break one.

``getRouters`` and the ``-9999`` fallback
-----------------------------------------
``SecurityUtils.getUserId()`` never returns ``null`` (it returns ``-1`` or raises
``CustomException``), so the ``-9999L`` branch is dead code. It is kept because deleting
it would be a silent behaviour change should ``SecurityUtils`` ever return null.

Response serialization
----------------------
``user`` is placed into the ``AjaxResult`` **as a pydantic model**, not as a dict. FastAPI
runs ``jsonable_encoder`` over the returned envelope, which dumps nested models with
``by_alias=True`` and ``mode="json"`` -- i.e. camelCase keys, ``@JsonIgnore`` fields
dropped, ``NON_EMPTY`` applied. That is precisely ``DomainModel.to_json_dict()``, so the
object can be handed over directly, exactly like ``ajax.put("user", user)`` in Java.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from app.api.util.common_util import check_password, is_null
from app.common.constant.constants import TOKEN
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.model.login_body import LoginBody
from app.common.utils import security_utils as SecurityUtils
from app.framework.web.service.sys_login_service import SysLoginService, get_login_service
from app.framework.web.service.sys_permission_service import (
    SysPermissionService,
    get_permission_service,
)
from app.system.service.sys_menu_service import SysMenuService, get_menu_service

router = APIRouter(tags=["system-login"])

#: Java: ``if (CommonUtil.checkPassword(curPassword))`` -- verbatim message, including the
#: full-width Chinese punctuation.
PASSWORD_INVALID_MESSAGE = "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！"

#: Java: ``if (null == userId) { userId = -9999L; }`` -- unreachable, see the module docstring.
NO_USER_ID_FALLBACK = -9999


# --------------------------------------------------------------------------- 依赖
#
# Java declares three ``@Autowired`` fields. Spring's default scope is singleton, so the
# fields are resolved once per context; module-level caches reproduce that. Tests swap the
# cached object (``_LOGIN_SERVICE = fake``) or reset and monkeypatch the provider.

_LOGIN_SERVICE: Optional[SysLoginService] = None
_MENU_SERVICE: Optional[SysMenuService] = None
_PERMISSION_SERVICE: Optional[SysPermissionService] = None


# Java: @Autowired private SysLoginService loginService
def _login_service() -> SysLoginService:
    global _LOGIN_SERVICE
    if _LOGIN_SERVICE is None:
        _LOGIN_SERVICE = get_login_service()
    return _LOGIN_SERVICE


# Java: @Autowired private ISysMenuService menuService
def _menu_service() -> SysMenuService:
    global _MENU_SERVICE
    if _MENU_SERVICE is None:
        _MENU_SERVICE = get_menu_service()
    return _MENU_SERVICE


# Java: @Autowired private SysPermissionService permissionService
def _permission_service() -> SysPermissionService:
    global _PERMISSION_SERVICE
    if _PERMISSION_SERVICE is None:
        _PERMISSION_SERVICE = get_permission_service()
    return _PERMISSION_SERVICE


def reset_login_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _LOGIN_SERVICE, _MENU_SERVICE, _PERMISSION_SERVICE
    _LOGIN_SERVICE = None
    _MENU_SERVICE = None
    _PERMISSION_SERVICE = None


# --------------------------------------------------------------------------- 端点
#
# ``response_model=None`` on every route: ``AjaxResult`` subclasses ``dict``, so FastAPI
# cannot derive a response model from the annotation and fails at import time. Java's
# ``AjaxResult extends HashMap`` is serialized verbatim by Jackson -- disabling the response
# model is the exact analogue (same reason as ``CaptchaController``).


@router.post("/login", response_model=None)
def login(login_body: LoginBody) -> AjaxResult:
    """登录方法. Java: ``@PostMapping("/login") public AjaxResult login(@RequestBody LoginBody)``.

    ``@RequestBody`` is required in Spring, so a missing body is an error, not an empty
    ``LoginBody``. FastAPI mirrors that: the model parameter has no default.

    A malformed/missing body is answered ``{"code":500,...}`` with HTTP 200 on both sides --
    Java through ``HttpMessageNotReadableException`` -> the generic
    ``@ExceptionHandler(Exception.class)``, here through ``RequestValidationError``. Only the
    message text differs (``"Required request body is missing: ..."`` vs ``"body Field
    required"``), which no client parses.
    """
    # Java: String curPassword = CommonUtil.isNull(loginBody.getPassword());
    cur_password = is_null(login_body.password)
    if check_password(cur_password):
        # 密码长度/复杂度不合法：不再校验验证码，也不写登录日志
        return AjaxResult.error_message(PASSWORD_INVALID_MESSAGE)

    ajax = AjaxResult.success()
    # 生成令牌 -- Java passes the *raw* password, not ``curPassword``.
    token = _login_service().login(
        login_body.username,
        login_body.password,
        login_body.code,
        login_body.uuid,
    )
    ajax.put_chain(TOKEN, token)
    return ajax


@router.get("/getInfo", response_model=None)
def get_info() -> AjaxResult:
    """获取用户信息. Java: ``@GetMapping("/getInfo")``."""
    # Java: SysUser user = SecurityUtils.getLoginUser().getUser();
    # ``get_login_user()`` raises ``CustomException("获取用户信息异常")`` if the principal is
    # missing -- unreachable here because the route is ``authenticated``.
    user = SecurityUtils.get_login_user().user
    # 角色集合
    roles = _permission_service().get_role_permission(user)
    # 权限集合
    permissions = _permission_service().get_menu_permission(user)

    # Java 基准中 SysUser.params 经 Jackson 类型化后输出 @type 标记；Python 默认按
    # @JsonInclude(NON_EMPTY) 删除空 params，这里只对 /getInfo 的用户投影保留该键。
    user_payload = user.to_json_dict() if hasattr(user, "to_json_dict") else dict(user)
    user_payload["params"] = {"@type": "java.util.HashMap"}
    ajax = AjaxResult.success()
    ajax.put_chain("user", user_payload)
    if isinstance(user_payload.get("dept"), dict):
        user_payload["dept"]["params"] = {"@type": "java.util.HashMap"}
    # Java SysRole also serializes inherited params as {"@type":"java.util.HashMap"}.
    # Java SysUser.roles 是嵌套 SysRole 列表：空 params 也会输出 @type 标记。
    for nested_role in user_payload.get("roles") or []:
        if isinstance(nested_role, dict):
            nested_role.setdefault("params", {"@type": "java.util.HashMap"})
    ajax.put_chain("roles", sorted(roles))
    ajax.put_chain("permissions", sorted(permissions))
    # Java: ajax.put("pjFlag", 0); ajax.put("overdue", false);
    ajax.put_chain("pjFlag", 0)
    ajax.put_chain("overdue", False)
    return ajax


@router.get("/getRouters", response_model=None)
def get_routers() -> AjaxResult:
    """获取路由信息. Java: ``@GetMapping("/getRouters")``."""
    user_id = SecurityUtils.get_user_id()
    if user_id is None:
        # Dead code in Java, preserved -- see the module docstring.
        user_id = NO_USER_ID_FALLBACK
    menus = _menu_service().select_menu_tree_by_user_id(user_id)
    # Java: AjaxResult.success(Object data) -> success_data
    return AjaxResult.success_data(_menu_service().build_menus(menus))


__all__ = [
    "router",
    "login",
    "get_info",
    "get_routers",
    "reset_login_controller",
    "PASSWORD_INVALID_MESSAGE",
    "NO_USER_ID_FALLBACK",
]
