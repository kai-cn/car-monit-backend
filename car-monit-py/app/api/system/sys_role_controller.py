"""角色信息.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysRoleController.java

端点清单（10 个映射，全部迁移）
-------------------------------------------
    ===========================  =======  ===============================  ==========
    Java                          Method   Path                             Access
    ===========================  =======  ===============================  ==========
    ``list(SysRole)``              GET      ``/system/role/list``            **登录**
    ``export(SysRole)``            GET      ``/system/role/export``          export
    ``getInfo(Long)``              GET      ``/system/role/{roleId}``        query
    ``add(SysRole)``               POST     ``/system/role``                 add
    ``edit(SysRole)``              PUT      ``/system/role``                 edit
    ``dataScope(SysRole)``         PUT      ``/system/role/dataScope``       edit
    ``changeStatus(SysRole)``      PUT      ``/system/role/changeStatus``    edit
    ``remove(Long[])``             DELETE   ``/system/role/{roleIds}``       remove
    ``optionselect()``             GET      ``/system/role/optionselect``    query
    ``selectlist(SysRole)``        GET      ``/system/role/selectlist``      **登录**
    ===========================  =======  ===============================  ==========

``list`` 的 ``@PreAuthorize`` 在 Java 里是**注释掉**的
------------------------------------------------------
Java 源码第 47 行是 ``// @PreAuthorize("@ss.hasPermi('system:role:list')")``，所以
"角色管理"列表页任何**登录用户**都能访问 —— 与本项目其它模块（post/dept 都真的校验了
``:list``）不同。这里照抄：不加 ``@pre_authorize_permi``。``selectlist`` 同样没有注解
（它是本项目加的"下拉角色"接口）。

未迁移的端点：``export`` 已补齐
------------------------------
``export`` 返回的是**文件名**，不是文件内容：Java 是
``return util.exportExcel(list, "角色数据")``，``AjaxResult.success(filename)`` 命中
``success(String)`` 重载，于是文件名落在 ``msg``（**不是** ``data``）：
``{"code": 200, "msg": "<uuid>_角色数据.xlsx"}``。文件本身写到
``{ruoyi.profile}/download/``，需要再调 ``GET /common/download`` 才拿到字节。

导出不分页：Java 侧直接调 ``selectRoleList``，没有 ``startPage()``。

``@Log(...)`` 注解
------------------------
``export`` / ``add`` / ``edit`` / ``dataScope`` / ``changeStatus`` / ``remove`` 带
``@Log(title = "角色管理", ...)``，由 :mod:`app.framework.aspectj.log_aspect` 异步写
``sys_oper_log``：``businessType`` 依次是 ``EXPORT`` / ``INSERT`` / ``UPDATE`` /
``UPDATE`` / ``UPDATE`` / ``DELETE``。见 ``COMPATIBILITY.md`` §28。

``edit`` 里的"刷新当前登录用户缓存"
-----------------------------------
Java::

    if (roleService.updateRole(role) > 0)
    {
        LoginUser loginUser = tokenService.getLoginUser(ServletUtils.getRequest());
        if (StringUtils.isNotNull(loginUser.getUser()) && !loginUser.getUser().isAdmin())
        {
            loginUser.setPermissions(permissionService.getMenuPermission(loginUser.getUser()));
            loginUser.setUser(userService.selectUserByUserName(loginUser.getUser().getUserName()));
            tokenService.setLoginUser(loginUser);
        }
        return AjaxResult.success();
    }

三点必须保留的细节：

1. 刷新的是**当前请求者**的缓存，不是被修改的那个角色的成员。改完别人的角色，
   自己的 ``login_tokens:<uuid>`` 会被重写（顺带续期 120 分钟）。
2. ``loginUser`` 为 ``null`` 时 Java 直接 NPE（``loginUser.getUser()``）—— 理论上
   走不到（路由要求认证），但这里**不**加 ``if login_user is not None`` 兜底，
   保持"没登录就 500"的现状。
3. 分支条件是 ``!user.isAdmin()``，即 ``userId != 1``。超管改角色不会刷新缓存
   （他的权限本来就是 ``*:*:*``）。

``@Validated @RequestBody`` 与 ``@PreAuthorize`` 的先后
-------------------------------------------------------
与岗位/部门切片相同：Spring 先解析参数（触发 Hibernate Validator）**再**进
``@PreAuthorize``，所以顺序是::

    安全过滤器链(401) -> 路由 -> 反序列化+校验(500) -> @PreAuthorize(403) -> 方法体

校验做成 FastAPI 的 ``Depends``（:data:`ValidRole`）才能保住这个顺序。
``dataScope`` / ``changeStatus`` 是裸 ``@RequestBody``，**不做**校验。

路由声明顺序
------------
``/list`` / ``/optionselect`` / ``/selectlist`` / ``/export`` 必须写在 ``/{role_id}`` **之前**：
FastAPI 按注册顺序匹配，否则 ``GET /system/role/list`` 会被当成 ``roleId = "list"``。
Spring 的 ``AntPathMatcher`` 本来就优先字面量，两者结果一致。

文案里的坑
----------
``add`` / ``edit`` 的"属性已存在"提示里插的是 **角色名称**（``role.getRoleName()``），
不是重复的那个字段值 —— Java 原文如此。
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
    to_ajax,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_role import ROLE_CONSTRAINTS, SysRole
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.bean_validation import validate
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.framework.web.service.sys_permission_service import (
    SysPermissionService,
    get_permission_service,
)
from app.framework.web.service.token_service import TokenService, get_token_service
from app.system.service.sys_role_service import SysRoleService, get_role_service
from app.system.service.sys_user_service import SysUserService, get_user_service

logger = logging.getLogger("app.api.system.sys_role_controller")

router = APIRouter(prefix="/system/role", tags=["system-role"])

#: Java: ``com.ruoyi.web.controller.system.SysRoleController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysRoleController"

#: Java: ``新增角色'" + role.getRoleName() + "'失败，角色名称已存在``
ADD_ROLE_NAME_EXISTS = "新增角色'{}'失败，角色名称已存在"
#: Java: ``新增角色'" + role.getRoleName() + "'失败，角色权限已存在``
ADD_ROLE_KEY_EXISTS = "新增角色'{}'失败，角色权限已存在"
#: Java: ``修改角色'" + role.getRoleName() + "'失败，角色名称已存在``
EDIT_ROLE_NAME_EXISTS = "修改角色'{}'失败，角色名称已存在"
#: Java: ``修改角色'" + role.getRoleName() + "'失败，角色权限已存在``
EDIT_ROLE_KEY_EXISTS = "修改角色'{}'失败，角色权限已存在"
#: Java: ``修改角色'" + role.getRoleName() + "'失败，请联系管理员`` —— updateRole 返回 0 时
EDIT_ROLE_FAILED = "修改角色'{}'失败，请联系管理员"


# --------------------------------------------------------------------------- 依赖
#
# Java 四个 ``@Autowired`` 字段。Spring 默认单例，这里用模块级缓存复刻；
# 测试直接替换 ``controller._ROLE_SERVICE`` 等缓存对象即可注入假实现。

_ROLE_SERVICE: Optional[SysRoleService] = None
_TOKEN_SERVICE: Optional[TokenService] = None
_PERMISSION_SERVICE: Optional[SysPermissionService] = None
_USER_SERVICE: Optional[SysUserService] = None


# Java: @Autowired private ISysRoleService roleService
def _role_service() -> SysRoleService:
    global _ROLE_SERVICE
    if _ROLE_SERVICE is None:
        _ROLE_SERVICE = get_role_service()
    return _ROLE_SERVICE


# Java: @Autowired private TokenService tokenService
def _token_service() -> TokenService:
    global _TOKEN_SERVICE
    if _TOKEN_SERVICE is None:
        _TOKEN_SERVICE = get_token_service()
    return _TOKEN_SERVICE


# Java: @Autowired private SysPermissionService permissionService
def _permission_service() -> SysPermissionService:
    global _PERMISSION_SERVICE
    if _PERMISSION_SERVICE is None:
        _PERMISSION_SERVICE = get_permission_service()
    return _PERMISSION_SERVICE


# Java: @Autowired private ISysUserService userService
def _user_service() -> SysUserService:
    global _USER_SERVICE
    if _USER_SERVICE is None:
        _USER_SERVICE = get_user_service()
    return _USER_SERVICE


def reset_role_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _ROLE_SERVICE, _TOKEN_SERVICE, _PERMISSION_SERVICE, _USER_SERVICE
    _ROLE_SERVICE = None
    _TOKEN_SERVICE = None
    _PERMISSION_SERVICE = None
    _USER_SERVICE = None


def _query_role(request: Request) -> SysRole:
    """Java: 形参 ``SysRole role``（**没有** ``@RequestBody``）—— 由 query string 绑定。

    规则见 :func:`app.common.core.controller.base_controller.bind_query_params`；
    ``params[beginTime]`` / ``params[endTime]`` 走同一个绑定器写进 ``role.params``。
    """
    return bind_query_params(SysRole, request.query_params)


#: 查询条件实体（``?roleName=...&status=...&params[beginTime]=...``）。
RoleParam = Annotated[SysRole, Depends(_query_role)]


def _validated_role(role: SysRole) -> SysRole:
    """Java: ``@Validated @RequestBody SysRole``.

    做成 ``Depends`` 而不是函数体第一行，是为了让校验排在 ``@PreAuthorize`` 之前。
    约束表 :data:`ROLE_CONSTRAINTS` 与 Java 注解同位置（实体旁边）。
    """
    validate(role, ROLE_CONSTRAINTS)
    return role


#: 已校验的请求体。
ValidRole = Annotated[SysRole, Depends(_validated_role)]


def _is_not_unique(result: str) -> bool:
    """Java: ``UserConstants.NOT_UNIQUE_OLD.equals(...)``.

    ``NOT_UNIQUE_OLD`` 是字面量 ``"1"``，``UNIQUE_OLD`` 是 ``"0"``
    （见 :mod:`app.common.constant.user_constants`）。
    """
    from app.common.constant.user_constants import NOT_UNIQUE_OLD

    return NOT_UNIQUE_OLD == result


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
def list_roles(role: RoleParam) -> TableDataInfo:
    """获取角色列表.

    Java: ``@GetMapping("/list") public TableDataInfo list(SysRole role)``.
    ``@PreAuthorize`` 在 Java 里被注释掉了，所以**只要求登录**（见模块 docstring）。
    """
    start_page()
    rows = _role_service().select_role_list(role)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("system:role:export")
@log(title="角色管理", business_type=BusinessType.EXPORT, java_method="export")
def export(role: RoleParam) -> AjaxResult:
    """导出角色数据. Java: ``@GetMapping("/export") public AjaxResult export(SysRole role)``.

    ``msg`` 是生成的文件名（不是文件内容），见模块 docstring。
    """
    rows = _role_service().select_role_list(role)
    return ExcelUtil(SysRole).export_excel(rows, "角色数据")


@router.get("/optionselect", response_model=None)
@pre_authorize_permi("system:role:query")
def optionselect() -> AjaxResult:
    """获取角色选择框列表. Java: ``@GetMapping("/optionselect")``.

    返回全量角色（不分页、不带分页信封）。注意这个分支**会**经过
    ``@DataScope``：``selectRoleAll`` 内部转调 ``selectRoleList``。
    """
    return AjaxResult.success_data(_role_service().select_role_all())


@router.get("/selectlist", response_model=None)
def selectlist(role: RoleParam) -> AjaxResult:
    """获取下拉角色. Java: ``@GetMapping("/selectlist")``.

    没有 ``@PreAuthorize``，也没有 ``startPage()`` —— 返回**全量**列表（但带
    ``selectRoleList`` 的数据权限过滤），不要"顺手"补分页。
    """
    return AjaxResult.success_data(_role_service().select_role_list(role))


@router.get("/{role_id}", response_model=None)
@pre_authorize_permi("system:role:query")
def get_info(role_id: int) -> AjaxResult:
    """根据角色编号获取详细信息.

    Java: ``@GetMapping(value = "/{roleId}")`` —— ``value`` 是单值，没有尾斜杠变体。
    角色不存在时 ``data`` 缺失（``AjaxResult.success(null)`` 不输出 ``data``）。
    """
    return AjaxResult.success_data(_role_service().select_role_by_id(role_id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:role:add")
@log(title="角色管理", business_type=BusinessType.INSERT, java_method="add")
def add(role: ValidRole) -> AjaxResult:
    """新增角色. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysRole role)``.

    ``role.menuIds`` 为 ``null`` 时 Service 的 ``for-each`` 会 NPE -> 500，
    与 Java 一致（前端始终传 ``menuIds: []``）。
    """
    if _is_not_unique(_role_service().check_role_name_unique(role)):
        return AjaxResult.error_message(ADD_ROLE_NAME_EXISTS.format(role.role_name))
    elif _is_not_unique(_role_service().check_role_key_unique(role)):
        return AjaxResult.error_message(ADD_ROLE_KEY_EXISTS.format(role.role_name))
    role.create_by = SecurityUtils.get_username()
    return to_ajax(_role_service().insert_role(role))


@router.put("", response_model=None)
@pre_authorize_permi("system:role:edit")
@log(title="角色管理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(role: ValidRole, request: Request) -> AjaxResult:
    """修改角色. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysRole role)``.

    ``checkRoleAllowed`` 会抛 ``CustomException``（"不允许操作超级管理员角色"），
    由通用处理器翻成 HTTP 200 + ``code 500``。
    """
    role_service = _role_service()
    role_service.check_role_allowed(role)
    if _is_not_unique(role_service.check_role_name_unique(role)):
        return AjaxResult.error_message(EDIT_ROLE_NAME_EXISTS.format(role.role_name))
    elif _is_not_unique(role_service.check_role_key_unique(role)):
        return AjaxResult.error_message(EDIT_ROLE_KEY_EXISTS.format(role.role_name))
    role.update_by = SecurityUtils.get_username()

    if role_service.update_role(role) > 0:
        # 更新缓存用户权限
        login_user = _token_service().get_login_user(request)
        # Java: loginUser 为 null 时这里就是 NPE，不做兜底。
        if login_user.user is not None and not login_user.user.admin:
            login_user.permissions = _permission_service().get_menu_permission(login_user.user)
            login_user.user = _user_service().select_user_by_user_name(login_user.user.user_name)
            _token_service().set_login_user(login_user)
        return AjaxResult.success()
    return AjaxResult.error_message(EDIT_ROLE_FAILED.format(role.role_name))


@router.put("/dataScope", response_model=None)
@pre_authorize_permi("system:role:edit")
@log(title="角色管理", business_type=BusinessType.UPDATE, java_method="dataScope")
def data_scope(role: SysRole) -> AjaxResult:
    """修改保存数据权限. Java: ``@PutMapping("/dataScope")``.

    裸 ``@RequestBody`` —— 不校验、也不设 ``updateBy``（Java 原文如此）。
    """
    _role_service().check_role_allowed(role)
    return to_ajax(_role_service().auth_data_scope(role))


@router.put("/changeStatus", response_model=None)
@pre_authorize_permi("system:role:edit")
@log(title="角色管理", business_type=BusinessType.UPDATE, java_method="changeStatus")
def change_status(role: SysRole) -> AjaxResult:
    """状态修改. Java: ``@PutMapping("/changeStatus")``."""
    _role_service().check_role_allowed(role)
    role.update_by = SecurityUtils.get_username()
    return to_ajax(_role_service().update_role_status(role))


@router.delete("/{role_ids}", response_model=None)
@pre_authorize_permi("system:role:remove")
@log(title="角色管理", business_type=BusinessType.DELETE, java_method="remove")
def remove(role_ids: str) -> AjaxResult:
    """删除角色. Java: ``@DeleteMapping("/{roleIds}") public AjaxResult remove(@PathVariable Long[] roleIds)``.

    两道业务拦截（超管角色 / 已分配用户）都在 Service 里，抛 ``CustomException``
    -> HTTP 200 + ``code 500``，整批都不删。
    """
    return to_ajax(_role_service().delete_role_by_ids(parse_id_array(role_ids)))


__all__ = [
    "router",
    "ADD_ROLE_NAME_EXISTS",
    "ADD_ROLE_KEY_EXISTS",
    "EDIT_ROLE_NAME_EXISTS",
    "EDIT_ROLE_KEY_EXISTS",
    "EDIT_ROLE_FAILED",
    "RoleParam",
    "ValidRole",
    "list_roles",
    "optionselect",
    "selectlist",
    "get_info",
    "add",
    "edit",
    "data_scope",
    "change_status",
    "remove",
    "reset_role_controller",
]
