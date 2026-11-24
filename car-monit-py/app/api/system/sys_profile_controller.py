"""个人信息 业务处理.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysProfileController.java

端点清单（4 个映射，全部迁移）
-------------------------------
    ==================================  =======  ================================  ==========
    Java                                Method   Path                              Access
    ==================================  =======  ================================  ==========
    ``profile()``                        GET      ``/system/user/profile``          登录
    ``updateProfile(SysUser)``           PUT      ``/system/user/profile``          登录
    ``updatePwd(String, String)``        PUT      ``/system/user/profile/updatePwd`` 登录
    ``avatar(MultipartFile)``            POST     ``/system/user/profile/avatar``   登录
    ==================================  =======  ================================  ==========

**四个端点都没有 ``@PreAuthorize``** —— 改自己的资料不该要求"用户管理"权限。它们能
被调用是因为 ``SecurityConfig`` 的 ``anyRequest().authenticated()``；未登录仍然是
安全过滤器给的 401。

路由注册顺序（本切片唯一的坑）
------------------------------
``SysUserController`` 有一条 ``GET /system/user/{userId}``。FastAPI 按**注册顺序**匹配，
所以本路由器必须在 ``sys_user_router`` **之前** ``include_router``，否则
``GET /system/user/profile`` 会先命中 ``/{user_id}``，在 ``int`` 转换处炸掉
（HTTP 422 / Java 那边是 200）。见 ``app/main.py``。

``loginUser`` 从哪来
--------------------
与其他控制器不同，这里**不**读 ``SecurityContextHolder``，而是逐字照抄 Java：

    LoginUser loginUser = tokenService.getLoginUser(ServletUtils.getRequest());

``getLoginUser`` 在令牌过期时会返回 ``null``，随后 ``loginUser.getUser()`` NPE。
本阶段的鉴权在路由之前，所以这里拿到的永远非空；即便为 ``null``，Python 的
``AttributeError`` 也会落到同一个处理器（HTTP 200 + ``code 500``）。

``updateProfile`` 的缓存回写
----------------------------
``updateUserProfile`` 成功后**再查一次当前登录用户**并把 4 个字段写回缓存
（``nickName`` / ``phonenumber`` / ``email`` / ``sex``），然后 ``setLoginUser`` 刷新
Redis。注意 ``roleGroup`` / ``postGroup`` 这类派生字段不在缓存里，每次都要查库。

``updatePwd`` 的两个坑
----------------------
1. **强密码校验的位置**：Java 先比对旧密码、再比对"新旧是否相同"，**最后**才做复杂度
   校验。所以"旧密码错 + 新密码太弱"回的是"旧密码错误"，不是复杂度提示。
2. **两次加密**：``resetUserPwd(userName, SecurityUtils.encryptPassword(newPassword))``
   与 ``loginUser.getUser().setPassword(SecurityUtils.encryptPassword(newPassword))``
   是**两次独立调用**，BCrypt 每次生成不同的 salt，所以写进数据库的哈希与写进缓存的
   哈希**不是同一个字符串**（两者都能校验通过同一个明文）。这是 Java 的既有行为，
   已记在 ``COMPATIBILITY.md`` §30.4；不要"优化"成一次。

``updatePwd`` 的入参绑定
------------------------
Java 形参没有 ``@RequestBody``（也没有 ``@RequestParam``），由
``ServletRequest#getParameter`` 绑定 —— **query string 优先，其次 form-urlencoded
body，同名取第一个值**。FastAPI 的 ``Query`` 只读 query、``Form`` 只读 body，单独用
任何一个都覆盖不了这两种来源，所以用 :func:`_request_parameters` 复刻
``getParameter`` 的聚合顺序。

``avatar`` 的文件校验链（全部在 ``FileUploadUtils`` 里）
--------------------------------------------------------
1. 原文件名长度 > 100 -> ``FileNameLengthLimitExceededException``（i18n 文案）；
2. 字节数 > 50M -> ``FileSizeLimitExceededException``（i18n 文案，MB 数）；
3. 后缀不在 ``DEFAULT_ALLOWED_EXTENSION`` 里 -> ``InvalidExtensionException``（拼装文案）；
4. 落盘到 ``{profile}/avatar/yyyy/MM/dd/{原名}_{序列号}.{后缀}``；
5. 数据库存的是 ``/profile/avatar/yyyy/MM/dd/...`` 这个**相对 url**。

前三步的异常都被 2 参 ``upload`` 包成 ``OSError``（Java 的 ``IOException``），所以
客户端看到的统一是 HTTP 200 + ``code 500`` + 原始文案。

``@Log(title = "个人信息", businessType = UPDATE)``
--------------------------------------------------
``updateProfile`` / ``updatePwd``（title=个人信息）与 ``avatar``（title=用户头像）带
``@Log``，由 :mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``，
三者 ``businessType`` 都是 ``UPDATE``。见 ``COMPATIBILITY.md`` §30.1。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.common.constant.user_constants import NOT_UNIQUE_OLD
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.enums.business_type import BusinessType
from app.common.utils import file_upload_utils as FileUploadUtils
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.string_utils import is_not_empty
from app.api.util.common_util import check_password
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.token_service import TokenService, get_token_service
from app.settings import get_settings
from app.system.service.sys_user_service import SysUserService, get_user_service

logger = logging.getLogger("app.api.system.sys_profile_controller")

router = APIRouter(prefix="/system/user/profile", tags=["system-profile"])

#: Java: ``com.ruoyi.web.controller.system.SysProfileController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysProfileController"

#: Java: ``修改用户'" + user.getUserName() + "'失败，手机号码已存在``
EDIT_PHONE_EXISTS = "修改用户'{}'失败，手机号码已存在"
#: Java: ``修改用户'" + user.getUserName() + "'失败，邮箱账号已存在``
EDIT_EMAIL_EXISTS = "修改用户'{}'失败，邮箱账号已存在"
#: Java: ``修改个人信息异常，请联系管理员``
UPDATE_PROFILE_FAILED = "修改个人信息异常，请联系管理员"
#: Java: ``修改密码失败，旧密码错误``
OLD_PASSWORD_ERROR = "修改密码失败，旧密码错误"
#: Java: ``新密码不能与旧密码相同``
SAME_PASSWORD = "新密码不能与旧密码相同"
#: Java: ``对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！``
#: 注意结尾是**全角感叹号**；``SysUserController`` 里那句（add / resetPwd）没有感叹号。
PASSWORD_INVALID_MESSAGE = "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！"
#: Java: ``修改密码异常，请联系管理员``
UPDATE_PWD_FAILED = "修改密码异常，请联系管理员"
#: Java: ``上传图片异常，请联系管理员``
UPLOAD_AVATAR_FAILED = "上传图片异常，请联系管理员"


# --------------------------------------------------------------------------- 依赖
# Java: ``@Autowired private ISysUserService userService`` + ``TokenService tokenService``。
# Spring 默认单例，这里用模块级缓存复刻；测试直接替换 ``_USER_SERVICE`` / ``_TOKEN_SERVICE``。

_USER_SERVICE: Optional[SysUserService] = None
_TOKEN_SERVICE: Optional[TokenService] = None


def _user_service() -> SysUserService:
    global _USER_SERVICE
    if _USER_SERVICE is None:
        _USER_SERVICE = get_user_service()
    return _USER_SERVICE


def _token_service() -> TokenService:
    global _TOKEN_SERVICE
    if _TOKEN_SERVICE is None:
        _TOKEN_SERVICE = get_token_service()
    return _TOKEN_SERVICE


def reset_profile_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _USER_SERVICE, _TOKEN_SERVICE
    _USER_SERVICE = None
    _TOKEN_SERVICE = None


def _current_login_user(request: Request) -> LoginUser:
    """Java: ``tokenService.getLoginUser(ServletUtils.getRequest())``.

    返回 ``None`` 时**不兜底**：调用方接着读 ``.user`` 会得到 ``AttributeError``，
    与 Java 的 NPE 落在同一个处理器上。
    """
    return _token_service().get_login_user(request)


async def _request_parameters(request: Request) -> Dict[str, str]:
    """Java: ``HttpServletRequest#getParameter`` —— query string 优先，其次 body。

    Servlet 规范把两处参数聚合成一个 Map，**query string 排在 form body 之前**，
    且 ``getParameter(name)`` 只返回第一个值，所以这里用 ``setdefault``。
    """
    values: Dict[str, str] = {}
    for key, value in request.query_params.multi_items():
        values.setdefault(key, value)

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/x-www-form-urlencoded") or content_type.startswith(
        "multipart/form-data"
    ):
        form = await request.form()
        for key, value in form.multi_items():
            # multipart 里的文件项不是字符串，``getParameter`` 同样拿不到它们。
            if isinstance(value, str):
                values.setdefault(key, value)
    return values


#: ``updatePwd`` 的入参（``?oldPassword=...&newPassword=...`` 或同名表单字段）。
RequestParameters = Annotated[Dict[str, str], Depends(_request_parameters)]


# --------------------------------------------------------------------------- 查询


@router.get("", response_model=None)
def profile(request: Request) -> AjaxResult:
    """个人信息. Java: ``@GetMapping public AjaxResult profile()``.

    返回的是**缓存里的** ``SysUser``（``login_tokens:<uuid>`` 里那份），不是重新查库。
    角色组 / 岗位组是逗号分隔的**名称**串，每次实时查。
    """
    login_user = _current_login_user(request)
    user = login_user.user
    user_payload = user.to_json_dict() if hasattr(user, "to_json_dict") else dict(user)
    user_payload["params"] = {"@type": "java.util.HashMap"}
    if isinstance(user_payload.get("dept"), dict):
        user_payload["dept"]["params"] = {"@type": "java.util.HashMap"}
    for role in user_payload.get("roles") or []:
        if isinstance(role, dict):
            role.setdefault("params", {"@type": "java.util.HashMap"})
    ajax = AjaxResult.success_data(user_payload)
    ajax.put_chain("roleGroup", _user_service().select_user_role_group(login_user.get_username()))
    ajax.put_chain("postGroup", _user_service().select_user_post_group(login_user.get_username()))
    return ajax


# --------------------------------------------------------------------------- 改资料


@router.put("", response_model=None)
@log(title="个人信息", business_type=BusinessType.UPDATE, java_method="updateProfile")
def update_profile(request: Request, user: SysUser) -> AjaxResult:
    """修改用户. Java: ``@PutMapping public AjaxResult updateProfile(@RequestBody SysUser user)``.

    两道唯一性闸门都只在**表单送了非空值**时才生效（``StringUtils.isNotEmpty``，不
    trim），所以清空手机号/邮箱不会被拦。
    """
    if is_not_empty(user.phonenumber) and NOT_UNIQUE_OLD == _user_service().check_phone_unique(user):
        return AjaxResult.error_message(EDIT_PHONE_EXISTS.format(user.user_name))
    if is_not_empty(user.email) and NOT_UNIQUE_OLD == _user_service().check_email_unique(user):
        return AjaxResult.error_message(EDIT_EMAIL_EXISTS.format(user.user_name))

    if _user_service().update_user_profile(user) > 0:
        login_user = _current_login_user(request)
        # 更新缓存用户信息 —— 只回写这 4 个字段（可见 Java 的 updateUserProfile 也只
        # 允许改这 4 个；其余字段即使传了也不会被前端用上）。
        login_user.user.nick_name = user.nick_name
        login_user.user.phonenumber = user.phonenumber
        login_user.user.email = user.email
        login_user.user.sex = user.sex
        _token_service().set_login_user(login_user)
        return AjaxResult.success()
    return AjaxResult.error_message(UPDATE_PROFILE_FAILED)


# --------------------------------------------------------------------------- 改密码


@router.put("/updatePwd", response_model=None)
@log(title="个人信息", business_type=BusinessType.UPDATE, java_method="updatePwd")
def update_pwd(request: Request, parameters: RequestParameters) -> AjaxResult:
    """重置密码. Java: ``@PutMapping("/updatePwd") public AjaxResult updatePwd(String oldPassword, String newPassword)``.

    注意顺序：**旧密码 -> 新旧相同 -> 复杂度**。三个分支的文案各不相同，别合并。
    """
    old_password = parameters.get("oldPassword")
    new_password = parameters.get("newPassword")

    login_user = _current_login_user(request)
    user_name = login_user.get_username()
    password = login_user.get_password()
    if not SecurityUtils.matches_password(old_password, password):
        return AjaxResult.error_message(OLD_PASSWORD_ERROR)
    if SecurityUtils.matches_password(new_password, password):
        return AjaxResult.error_message(SAME_PASSWORD)

    # 密码强密码（``check_password`` 返回 True 表示**不合法**）
    if check_password(new_password):
        return AjaxResult.error_message(PASSWORD_INVALID_MESSAGE)

    if _user_service().reset_user_pwd(user_name, SecurityUtils.encrypt_password(new_password)) > 0:
        # 更新缓存用户密码 —— 这里是**第二次**独立加密，与上面那句的哈希不同（见模块
        # docstring）。两者都能校验通过同一个明文，所以不影响后续登录。
        login_user.user.password = SecurityUtils.encrypt_password(new_password)
        _token_service().set_login_user(login_user)
        return AjaxResult.success()
    return AjaxResult.error_message(UPDATE_PWD_FAILED)


# --------------------------------------------------------------------------- 头像


@router.post("/avatar", response_model=None)
@log(title="用户头像", business_type=BusinessType.UPDATE, java_method="avatar")
def avatar(request: Request, avatarfile: Annotated[UploadFile, File()]) -> AjaxResult:
    """头像上传. Java: ``@PostMapping("/avatar") public AjaxResult avatar(@RequestParam("avatarfile") MultipartFile file)``.

    ``file.isEmpty()``（即 0 字节）直接走到最后的失败分支，**不会**动磁盘、也不会
    更新数据库 —— 与 Java 一致。
    """
    if not _is_empty_file(avatarfile):
        login_user = _current_login_user(request)
        # Java: FileUploadUtils.upload(RuoYiConfig.getAvatarPath(), file)
        avatar_url = FileUploadUtils.upload(get_settings().ruoyi.avatar_path, avatarfile)
        if _user_service().update_user_avatar(login_user.get_username(), avatar_url):
            ajax = AjaxResult.success()
            ajax.put_chain("imgUrl", avatar_url)
            # 更新缓存用户头像
            login_user.user.avatar = avatar_url
            _token_service().set_login_user(login_user)
            return ajax
    return AjaxResult.error_message(UPLOAD_AVATAR_FAILED)


def _is_empty_file(file: Any) -> bool:
    """Java: ``MultipartFile#isEmpty()`` -> ``getSize() == 0``.

    复用 ``FileUploadUtils`` 里的同一个尺寸取值逻辑（``UploadFile.size`` 可能为
    ``None``，此时退回到底层文件长度）。
    """
    return FileUploadUtils.size_of(file) == 0


__all__ = [
    "router",
    "profile",
    "update_profile",
    "update_pwd",
    "avatar",
    "reset_profile_controller",
    "EDIT_PHONE_EXISTS",
    "EDIT_EMAIL_EXISTS",
    "UPDATE_PROFILE_FAILED",
    "OLD_PASSWORD_ERROR",
    "SAME_PASSWORD",
    "PASSWORD_INVALID_MESSAGE",
    "UPDATE_PWD_FAILED",
    "UPLOAD_AVATAR_FAILED",
]
