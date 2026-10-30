"""用户常用菜单 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexMenuController.java

7 个映射，全部迁移
--------------------
=============================  ================================  =============================
Java                           Method / Path                      权限点
=============================  ================================  =============================
``list``                       GET ``/list``                     **无**（注解被注释掉）
``getSysIndexMenulist``        GET ``/mylist``                   **无**（本来就没有）
``export``                     GET ``/export``                   ``system:indexmenu:export``
``getInfo``                    GET ``/{id}``                     ``system:indexmenu:query``
``add``                        POST ``""``                       **无**（注解被注释掉）
``edit``                       PUT ``""``                        ``system:indexmenu:edit``
``remove``                     DELETE ``/{ids}``                 **无**（注解被注释掉）
=============================  ================================  =============================

``list`` / ``add`` / ``remove`` 的 ``@PreAuthorize`` 在 Java 源码里**是被注释掉的**：

.. code-block:: java

    //    @PreAuthorize("@ss.hasPermi('system:indexmenu:list')")
    //    @PreAuthorize("@ss.hasPermi('system:indexmenu:add')")
    //    @PreAuthorize("@ss.hasPermi('system:indexmenu:remove')")

别"顺手"补回来 —— 这三个端点是首页九宫格的数据源，补上权限会让普通用户白屏。

``getInfo`` 的 ``@PathVariable("id")``
-----------------------------------
Java 显式写了 ``value = "id"``，所以形参名不影响 URL 模板；Python 侧同样用 ``{id}``。
注意这个 id 是 ``SysIndexMenu.id``（**UUID 字符串**），不是数值 —— 但 Java 声明成
``Long``，所以真实调用方传的是数字串；Python 照抄声明成 ``int``，非数字会在路由层
转失败 -> **HTTP 200 + code 500**（与 Java 的 ``MethodArgumentTypeMismatchException`` 同形）。

``export`` 返回的是**文件名**，不是文件内容
---------------------------------------------
Java 是 ``return util.exportExcel(list, "用户常用菜单数据")``，
``AjaxResult.success(filename)`` 命中 ``success(String)`` 重载，于是文件名落在
``msg``（**不是** ``data``）：``{"code": 200, "msg": "<uuid>_用户常用菜单数据.xlsx"}``。
文件本身写到 ``{ruoyi.profile}/download/``，需要再调 ``GET /common/download``
才拿到字节。

导出**不分页**（Java 侧没有 ``startPage()``），但同时实体会带上查询条件
（``menuName`` / ``menuName2``）。

``add`` / ``edit`` 都没有 ``@Validated``
--------------------------------------
实体上一个约束注解也没有（见 :mod:`app.system.domain.sys_index_menu`），
所以这里**不注入校验依赖**，也不需要 ``*_CONSTRAINTS``。

注册顺序
--------
``/list`` 、 ``/mylist`` 与 ``/export`` **必须**排在 ``/{id}`` 之前，否则会被单段路径变量吃掉。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.domain.sys_index_menu import SysIndexMenu
from app.system.service.sys_index_menu_service import (
    SysIndexMenuService,
    get_index_menu_service,
)

router = APIRouter(prefix="/system/indexmenu", tags=["system-indexmenu"])

#: Java: ``com.ruoyi.web.controller.system.SysIndexMenuController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysIndexMenuController"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysIndexMenuService sysIndexMenuService``。Spring 默认
# 单例，这里用模块级缓存复刻；测试直接替换 ``controller._INDEX_MENU_SERVICE``。

_INDEX_MENU_SERVICE: SysIndexMenuService | None = None


def _index_menu_service() -> SysIndexMenuService:
    global _INDEX_MENU_SERVICE
    if _INDEX_MENU_SERVICE is None:
        _INDEX_MENU_SERVICE = get_index_menu_service()
    return _INDEX_MENU_SERVICE


def reset_index_menu_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _INDEX_MENU_SERVICE
    _INDEX_MENU_SERVICE = None


def _query_index_menu(request: Request) -> SysIndexMenu:
    """Java: 形参 ``SysIndexMenu sysIndexMenu``（**没有** ``@RequestBody``）—— query string 绑定。"""
    return bind_query_params(SysIndexMenu, request.query_params)


#: 查询条件实体（``?menuName=...&menuName2=...``）。
IndexMenuParam = Annotated[SysIndexMenu, Depends(_query_index_menu)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
def list_index_menus(query: IndexMenuParam) -> TableDataInfo:
    """查询用户常用菜单列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysIndexMenu sysIndexMenu)``.

    **没有** ``@PreAuthorize``。Service 会用登录用户覆盖 ``userId``。
    """
    start_page()
    rows = _index_menu_service().select_sys_index_menu_list(query)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("system:indexmenu:export")
@log(title="用户常用菜单", business_type=BusinessType.EXPORT, java_method="export")
def export(query: IndexMenuParam) -> AjaxResult:
    """导出用户常用菜单. Java: ``@GetMapping("/export") public AjaxResult export(SysIndexMenu)``.

    ``msg`` 是生成的文件名（不是文件内容），见模块 docstring。
    """
    rows = _index_menu_service().select_sys_index_menu_list(query)
    return ExcelUtil(SysIndexMenu).export_excel(rows, "用户常用菜单数据")


@router.get("/mylist", response_model=None)
def get_my_list(query: IndexMenuParam) -> AjaxResult:
    """分页查询. Java: ``@GetMapping("/mylist") public AjaxResult getSysIndexMenulist(SysIndexMenu sysIndexMenu)``.

    Java 在控制器里也 ``setUserId`` 了一次（service 里又设一次）。照抄这个"设两遍"。
    返回的是"我常用的菜单"（SQL 自带 ``limit 9``），**没有**分页。
    """
    # Java: Long userId = SecurityUtils.getUserId(); sysIndexMenu.setUserId(userId);
    query.user_id = SecurityUtils.get_user_id()
    return AjaxResult.success_data(_index_menu_service().get_list(query))


@router.get("/{id}", response_model=None)
@pre_authorize_permi("system:indexmenu:query")
def get_info(id: int) -> AjaxResult:
    """获取用户常用菜单详细信息. Java: ``@GetMapping(value = "/{id}")``.

    查不到时 ``data`` 为 ``null``（不是 404）。
    """
    return AjaxResult.success_data(_index_menu_service().select_sys_index_menu_by_id(id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@log(title="用户常用菜单", business_type=BusinessType.INSERT, java_method="add")
def add(entity: SysIndexMenu) -> AjaxResult:
    """新增用户常用菜单. Java: ``@PostMapping public AjaxResult add(@RequestBody SysIndexMenu sysIndexMenu)``.

    只看 ``menuIds`` 这一个字段：把它拆成一行行记录。**没有** ``@Validated``，
    也**没有** ``@PreAuthorize``（注解被注释掉）。
    """
    # Java: String menuIds = sysIndexMenu.getMenuIds();
    return _index_menu_service().insert_sys_index_menu(entity.menu_ids)


@router.put("", response_model=None)
@pre_authorize_permi("system:indexmenu:edit")
@log(title="用户常用菜单", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: SysIndexMenu) -> AjaxResult:
    """修改用户常用菜单. Java: ``@PutMapping public AjaxResult edit(@RequestBody SysIndexMenu sysIndexMenu)``.

    有 ``id`` 就改，没有就新增。成功文案是 ``"操作成功！"``（**全角叹号**），
    ``data`` 是 ``id``。
    """
    return _index_menu_service().save_sys_index_menu(entity)


@router.delete("/{ids}", response_model=None)
@log(title="用户常用菜单", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除用户常用菜单. Java: ``@DeleteMapping("/{ids}") public AjaxResult remove(@PathVariable Long[] ids)``.

    **软删除**（``del_flag = '1'``），且 ``count == 0`` 也回 200。**没有** ``@PreAuthorize``。
    """
    return _index_menu_service().delete_sys_index_menu_by_ids(parse_id_array(ids))


__all__ = [
    "router",
    "IndexMenuParam",
    "list_index_menus",
    "get_my_list",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_index_menu_controller",
]
