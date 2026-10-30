"""菜单信息.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysMenuController.java

端点清单（7 个映射，全部迁移）
-------------------------------
    ==============================  =======  ==========================================  ==========
    Java                            Method   Path                                        Access
    ==============================  =======  ==========================================  ==========
    ``list(SysMenu)``                GET      ``/system/menu/list``                       list
    ``treeselect(SysMenu)``          GET      ``/system/menu/treeselect``                 登录
    ``roleMenuTreeselect(Long)``     GET      ``/system/menu/roleMenuTreeselect/{roleId}`` 登录
    ``getInfo(Long)``                GET      ``/system/menu/{menuId}``                   query
    ``add(SysMenu)``                 POST     ``/system/menu``                            add
    ``edit(SysMenu)``                PUT      ``/system/menu``                            edit
    ``remove(Long)``                 DELETE   ``/system/menu/{menuId}``                   remove
    ==============================  =======  ==========================================  ==========

两个端点只要求登录
------------------
``treeselect`` / ``roleMenuTreeselect`` **没有** ``@PreAuthorize`` —— 角色编辑页要画菜单树，
普通用户也得能拿到。``list`` 有 ``system:menu:list``（与 ``sys_role.list`` 相反，
那边注解被注释掉了）。

``list`` 不分页
---------------
返回的是 ``AjaxResult``（``data`` 是数组），不是 ``TableDataInfo``。菜单是树形数据，
分页没有意义 —— 这一点与 ``sys_user`` / ``sys_role`` / ``sys_post`` 都不同，
不要照着它们的 ``start_page`` / ``get_data_table`` 抄。

``list`` / ``treeselect`` / ``roleMenuTreeselect`` 都要拿当前用户
--------------------------------------------------------------
Java 全都是先 ``tokenService.getLoginUser(ServletUtils.getRequest())`` 再
``loginUser.getUser().getUserId()``。**超管（userId == 1）看全表，其他人只看授权菜单**，
判据在 ``SysMenuService#selectMenuList`` 里。``loginUser`` 为 ``null`` 时 Java NPE，
这里同样不兜底。

``roleMenuTreeselect`` 的两个 ``put``
-------------------------------------
Java 先 ``AjaxResult.success()`` 再两次 ``put``，所以键序是
``code`` / ``msg`` / ``checkedKeys`` / ``menus``。``checkedKeys`` 是**菜单 id 数组**，
供角色编辑页回填勾选状态。

``@Validated @RequestBody`` 与 ``@PreAuthorize`` 的先后
-------------------------------------------------------
同其它切片：Spring 先解析参数（触发 Hibernate Validator）**再**进 ``@PreAuthorize``，
顺序是::

    安全过滤器链(401) -> 路由 -> 反序列化+校验(500) -> @PreAuthorize(403) -> 方法体

所以校验做成 FastAPI 的 ``Depends``（:data:`ValidMenu`）。约束表 ``MENU_CONSTRAINTS``
在实体旁边，与 Java 注解同位置。

路由声明顺序
------------
``/list`` / ``/treeselect`` / ``/roleMenuTreeselect/{roleId}`` 必须写在 ``/{menu_id}``
**之前**：FastAPI 按注册顺序匹配，否则 ``GET /system/menu/list`` 会被当成
``menu_id = "list"`` 并在 ``int`` 转换处炸掉（HTTP 500）。Spring 的
``AntPathMatcher`` 本来就优先字面量，两者结果一致。

注意 ``POST`` / ``PUT`` 用的是空串 ``""``（拼出 ``/system/menu``，与 Java 的
``@PostMapping`` / ``@PutMapping`` 一致），**不是** ``"/"``。

``@Log(title = "菜单管理", ...)``
--------------------------------
``add`` / ``edit`` / ``remove`` 带 ``@Log``，由
:mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``：``businessType`` 依次是
``INSERT`` / ``UPDATE`` / ``DELETE``。见 ``COMPATIBILITY.md`` §29.2。
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.common.constant.constants import HTTP, HTTPS
from app.common.constant.user_constants import NOT_UNIQUE_OLD, YES_FRAME
from app.common.core.controller.base_controller import bind_query_params, to_ajax
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_menu import MENU_CONSTRAINTS, SysMenu
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.bean_validation import validate
from app.common.utils.string_utils import starts_with_any
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.framework.web.service.token_service import TokenService, get_token_service
from app.system.service.sys_menu_service import SysMenuService, get_menu_service

logger = logging.getLogger("app.api.system.sys_menu_controller")

router = APIRouter(prefix="/system/menu", tags=["system-menu"])

#: Java: ``com.ruoyi.web.controller.system.SysMenuController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysMenuController"

#: Java: ``新增菜单'" + menu.getMenuName() + "'失败，菜单名称已存在``
ADD_MENU_NAME_EXISTS = "新增菜单'{}'失败，菜单名称已存在"
#: Java: ``新增菜单'" + menu.getMenuName() + "'失败，地址必须以http(s)://开头``
ADD_MENU_BAD_FRAME_URL = "新增菜单'{}'失败，地址必须以http(s)://开头"
#: Java: ``修改菜单'" + menu.getMenuName() + "'失败，菜单名称已存在``
EDIT_MENU_NAME_EXISTS = "修改菜单'{}'失败，菜单名称已存在"
#: Java: ``修改菜单'" + menu.getMenuName() + "'失败，地址必须以http(s)://开头``
EDIT_MENU_BAD_FRAME_URL = "修改菜单'{}'失败，地址必须以http(s)://开头"
#: Java: ``修改菜单'" + menu.getMenuName() + "'失败，上级菜单不能选择自己``
EDIT_MENU_SELF_PARENT = "修改菜单'{}'失败，上级菜单不能选择自己"
#: Java: ``存在子菜单,不允许删除`` —— 半角逗号
REMOVE_HAS_CHILD = "存在子菜单,不允许删除"
#: Java: ``菜单已分配,不允许删除`` —— 半角逗号
REMOVE_HAS_ROLE = "菜单已分配,不允许删除"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysMenuService menuService`` + ``TokenService tokenService``。
# Spring 默认单例，这里用模块级缓存复刻；测试直接替换 ``controller._MENU_SERVICE``
# 与 ``controller._TOKEN_SERVICE``。

_MENU_SERVICE: Optional[SysMenuService] = None
_TOKEN_SERVICE: Optional[TokenService] = None


def _menu_service() -> SysMenuService:
    global _MENU_SERVICE
    if _MENU_SERVICE is None:
        _MENU_SERVICE = get_menu_service()
    return _MENU_SERVICE


def _token_service() -> TokenService:
    global _TOKEN_SERVICE
    if _TOKEN_SERVICE is None:
        _TOKEN_SERVICE = get_token_service()
    return _TOKEN_SERVICE


def reset_menu_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _MENU_SERVICE, _TOKEN_SERVICE
    _MENU_SERVICE = None
    _TOKEN_SERVICE = None


def _query_menu(request: Request) -> SysMenu:
    """Java: 形参 ``SysMenu menu``（**没有** ``@RequestBody``）—— 由 query string 绑定。"""
    return bind_query_params(SysMenu, request.query_params)


#: 查询条件实体（``?menuName=...&visible=...&status=...``）。
MenuParam = Annotated[SysMenu, Depends(_query_menu)]


def _validated_menu(menu: SysMenu) -> SysMenu:
    """Java: ``@Validated @RequestBody SysMenu``.

    做成 ``Depends`` 而不是函数体第一行，是为了让校验排在 ``@PreAuthorize`` 之前 ——
    见模块 docstring 的"先后"一节。
    """
    validate(menu, MENU_CONSTRAINTS)
    return menu


#: 已校验的请求体。
ValidMenu = Annotated[SysMenu, Depends(_validated_menu)]


def _is_not_unique(result: str) -> bool:
    """Java: ``UserConstants.NOT_UNIQUE_OLD.equals(...)`` —— 字面量 ``"1"``。"""
    return NOT_UNIQUE_OLD == result


def _current_user_id(request: Request) -> int:
    """Java: ``tokenService.getLoginUser(request).getUser().getUserId()``.

    ``loginUser`` 为 ``null`` 时 Java NPE；这里抛 ``AttributeError``，落到通用处理器后
    同样是 HTTP 200 + ``code 500``。
    """
    return _token_service().get_login_user(request).user.user_id


def _has_bad_frame_url(menu: SysMenu) -> bool:
    """Java: ``YES_FRAME.equals(menu.getIsFrame()) && !startsWithAny(path, HTTP, HTTPS)``.

    ``isFrame = '0'``（是外链）时，``path`` 必须以 ``http://`` 或 ``https://`` 开头。
    ``path`` 为 ``null`` 时 ``startsWithAny`` 返回 ``false``，于是**拒绝**。
    """
    return YES_FRAME == menu.is_frame and not starts_with_any(menu.path, (HTTP, HTTPS))


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("system:menu:list")
def list_menus(menu: MenuParam, request: Request) -> AjaxResult:
    """获取菜单列表. Java: ``@GetMapping("/list") public AjaxResult list(SysMenu menu)``.

    **不分页**，返回 ``AjaxResult``；超管看全表，其他人只看授权菜单。
    """
    menus = _menu_service().select_menu_list(menu, _current_user_id(request))
    return AjaxResult.success_data(menus)


@router.get("/treeselect", response_model=None)
def treeselect(menu: MenuParam, request: Request) -> AjaxResult:
    """获取菜单下拉树列表. Java: ``@GetMapping("/treeselect")``.

    **没有权限点** —— 角色编辑页要画树。返回 ``TreeSelect`` 数组，
    叶子节点**没有** ``children`` 键。
    """
    menus = _menu_service().select_menu_list(menu, _current_user_id(request))
    return AjaxResult.success_data(_menu_service().build_menu_tree_select(menus))


@router.get("/roleMenuTreeselect/{role_id}", response_model=None)
def role_menu_treeselect(role_id: int, request: Request) -> AjaxResult:
    """加载对应角色菜单列表树. Java: ``@GetMapping("/roleMenuTreeselect/{roleId}")``.

    注意用的是**单参** ``selectMenuList(userId)``（不带查询条件），所以
    ``checkedKeys`` 与 ``menus`` 各查一次 —— 共两条 SQL，不是一条。
    """
    menus = _menu_service().select_menu_list_for_user(_current_user_id(request))
    ajax = AjaxResult.success()
    ajax.put_chain("checkedKeys", _menu_service().select_menu_list_by_role_id(role_id))
    ajax.put_chain("menus", _menu_service().build_menu_tree_select(menus))
    return ajax


@router.get("/{menu_id}", response_model=None)
@pre_authorize_permi("system:menu:query")
def get_info(menu_id: int) -> AjaxResult:
    """根据菜单编号获取详细信息.

    Java: ``@GetMapping(value = "/{menuId}")`` —— ``value`` 是单值，没有尾斜杠变体。
    菜单不存在时 ``data`` 键整体消失（Java ``AjaxResult.success(null)``）。
    """
    return AjaxResult.success_data(_menu_service().select_menu_by_id(menu_id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:menu:add")
@log(title="菜单管理", business_type=BusinessType.INSERT, java_method="add")
def add(menu: ValidMenu) -> AjaxResult:
    """新增菜单. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysMenu menu)``.

    两道闸，顺序不能变：名称判重 -> 外链地址前缀。判重只在**同一父节点**下做。
    """
    if _is_not_unique(_menu_service().check_menu_name_unique(menu)):
        return AjaxResult.error_message(ADD_MENU_NAME_EXISTS.format(menu.menu_name))
    elif _has_bad_frame_url(menu):
        return AjaxResult.error_message(ADD_MENU_BAD_FRAME_URL.format(menu.menu_name))
    menu.create_by = SecurityUtils.get_username()
    return to_ajax(_menu_service().insert_menu(menu))


@router.put("", response_model=None)
@pre_authorize_permi("system:menu:edit")
@log(title="菜单管理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(menu: ValidMenu) -> AjaxResult:
    """修改菜单. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysMenu menu)``.

    三道闸，顺序不能变：名称判重 -> 外链地址前缀 -> 上级不能是自己。
    """
    if _is_not_unique(_menu_service().check_menu_name_unique(menu)):
        return AjaxResult.error_message(EDIT_MENU_NAME_EXISTS.format(menu.menu_name))
    elif _has_bad_frame_url(menu):
        return AjaxResult.error_message(EDIT_MENU_BAD_FRAME_URL.format(menu.menu_name))
    elif _same_id(menu.menu_id, menu.parent_id):
        return AjaxResult.error_message(EDIT_MENU_SELF_PARENT.format(menu.menu_name))
    menu.update_by = SecurityUtils.get_username()
    return to_ajax(_menu_service().update_menu(menu))


@router.delete("/{menu_id}", response_model=None)
@pre_authorize_permi("system:menu:remove")
@log(title="菜单管理", business_type=BusinessType.DELETE, java_method="remove")
def remove(menu_id: int) -> AjaxResult:
    """删除菜单. Java: ``@DeleteMapping("/{menuId}")``.

    有子菜单 -> 拒绝；已被角色引用 -> 拒绝；否则**物理删除**。
    """
    if _menu_service().has_child_by_menu_id(menu_id):
        return AjaxResult.error_message(REMOVE_HAS_CHILD)
    if _menu_service().check_menu_exist_role(menu_id):
        return AjaxResult.error_message(REMOVE_HAS_ROLE)
    return to_ajax(_menu_service().delete_menu_by_id(menu_id))


__all__ = [
    "router",
    "ADD_MENU_NAME_EXISTS",
    "ADD_MENU_BAD_FRAME_URL",
    "EDIT_MENU_NAME_EXISTS",
    "EDIT_MENU_BAD_FRAME_URL",
    "EDIT_MENU_SELF_PARENT",
    "REMOVE_HAS_CHILD",
    "REMOVE_HAS_ROLE",
    "MenuParam",
    "ValidMenu",
    "list_menus",
    "treeselect",
    "role_menu_treeselect",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_menu_controller",
]


def _same_id(left: Optional[int], right: Optional[int]) -> bool:
    """Java: ``menu.getMenuId().equals(menu.getParentId())``.

    接收者为 ``null`` 时 NPE（这里抛 ``AttributeError``）；参数为 ``null`` 时返回
    ``false``。**不能**写成 ``left == right``：``None == None`` 会变成 ``True``，
    而 Java 会炸。
    """
    if left is None:
        raise AttributeError("'NoneType' object has no attribute 'equals'")
    return left == right
