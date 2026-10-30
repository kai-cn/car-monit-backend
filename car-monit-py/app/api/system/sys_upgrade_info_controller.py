"""系统升级信息 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUpgradeInfoController.java

7 个映射，全部迁移
--------------------
=============================  ==============================  ======================
Java                           Method / Path                   权限点
=============================  ==============================  ======================
``list``                       GET ``/list``                   **无**
``newest``                     GET ``/newest``                 **无**
``export``                     GET ``/export``                 **无**
``getInfo``                    GET ``/{id}``                   **无**
``add``                        POST ``""``                     **无**
``edit``                       PUT ``""``                      **无**
``remove``                     DELETE ``/{ids}``               **无**
=============================  ==============================  ======================

这个控制器**一个 ``@PreAuthorize`` 都没有**（不是被注释掉，是本来就没写）。
所以整个模块的鉴权只有 ``anyRequest().authenticated()``：登录即可，不查权限点。
别"顺手"补 —— 补了会让没有"系统升级信息"菜单权限的普通用户看不到升级公告。

``export`` 导出一张**只有表头以外什么都没有**的表
--------------------------------------------------
``SysUpgradeInfo`` 实体上一个 ``@Excel`` 都没有（见
:mod:`app.system.domain.sys_upgrade_info`），所以 ``getFields()`` 返回空列表：
工作集里只建了 sheet、sheet 名是 ``"系统升级信息数据"``，**没有表头行、没有数据行**。

Java 下同样如此（``ExcelUtil`` 不会因为字段为空而报错），所以两端行为一致。
若以后要给本表加导出列，必须在实体上补 ``EXCEL_FIELDS``（而不是改这里）。

返回值是**文件名**不是文件内容：``AjaxResult.success(filename)`` 命中
``success(String)`` 重载，文件名落在 ``msg``（**不是** ``data``）：
``{"code": 200, "msg": "<uuid>_系统升级信息数据.xlsx"}``。

注意本端点**没有** ``@PreAuthorize``（与整个控制器一致），登录即可。

``list`` 在控制器里盖 ``tenantId``
--------------------------------
Java:

.. code-block:: java

    startPage();
    sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户

也就是说：客户端传的 ``?tenantId=xxx`` 会被**登录上下文**覆盖，SQL 的
``<if test="tenantId != null">`` 因此总是生效。照抄。

这与 ``SysIndexMenuController`` 把覆盖放在 **Service** 里不同 —— 本模块放在
**控制器**里，Service 只是纯转发。

``remove`` 的 ``String[]``
--------------------------
Java 声明的是 ``@PathVariable String[] ids``（**其它模块都是 ``Long[]``**），所以
Python 用 :func:`app.common.core.controller.base_controller.parse_str_array`，
**不做** ``int`` 转换 —— 用 ``parse_id_array`` 会让所有 UUID 请求回 500。

注册顺序
--------
``/list`` 、 ``/newest`` 与 ``/export`` **必须**排在 ``/{id}`` 之前。注意这里的 ``/{id}`` 是
``String``，它能吃掉**任何**单段路径（包括 ``export``），所以顺序错了两条字面量
路由会彻底不可达。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.system.domain.sys_upgrade_info import SysUpgradeInfo
from app.system.service.sys_upgrade_info_service import (
    SysUpgradeInfoService,
    get_upgrade_info_service,
)

router = APIRouter(prefix="/system/upgradeInfo", tags=["system-upgrade-info"])

#: Java: ``com.ruoyi.web.controller.system.SysUpgradeInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysUpgradeInfoController"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysUpgradeInfoService sysUpgradeInfoService``。Spring 默认
# 单例，这里用模块级缓存复刻；测试直接替换 ``controller._UPGRADE_INFO_SERVICE``。

_UPGRADE_INFO_SERVICE: SysUpgradeInfoService | None = None


def _upgrade_info_service() -> SysUpgradeInfoService:
    global _UPGRADE_INFO_SERVICE
    if _UPGRADE_INFO_SERVICE is None:
        _UPGRADE_INFO_SERVICE = get_upgrade_info_service()
    return _UPGRADE_INFO_SERVICE


def reset_upgrade_info_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _UPGRADE_INFO_SERVICE
    _UPGRADE_INFO_SERVICE = None


def _query_upgrade_info(request: Request) -> SysUpgradeInfo:
    """Java: 形参 ``SysUpgradeInfo sysUpgradeInfo``（**没有** ``@RequestBody``）—— query string 绑定。"""
    return bind_query_params(SysUpgradeInfo, request.query_params)


#: 查询条件实体（``?ver=...&backCol1=...``）。
UpgradeInfoParam = Annotated[SysUpgradeInfo, Depends(_query_upgrade_info)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
def list_upgrade_infos(query: UpgradeInfoParam) -> TableDataInfo:
    """查询系统升级信息列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysUpgradeInfo)``.

    ``tenantId`` 被登录上下文覆盖（客户端传什么都会被无视）。
    """
    start_page()
    # Java: sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId());
    query.tenant_id = SecurityUtils.get_tenant_id()
    rows = _upgrade_info_service().select_sys_upgrade_info_list(query)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@log(title="系统升级信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: UpgradeInfoParam) -> AjaxResult:
    """导出系统升级信息. Java: ``@GetMapping("/export") public AjaxResult export(SysUpgradeInfo)``.

    **没有** ``@PreAuthorize``（整个控制器都没有）。

    ⚠️ 实体上零 ``@Excel``，所以导出的 xlsx 里**没有任何列** —— 只有一个名为
    ``"系统升级信息数据"`` 的空 sheet。这是 Java 的原样行为，不是缺陷。

    ``msg`` 是生成的文件名（不是文件内容）。
    """
    rows = _upgrade_info_service().select_sys_upgrade_info_list(query)
    return ExcelUtil(SysUpgradeInfo).export_excel(rows, "系统升级信息数据")


@router.get("/newest", response_model=None)
def newest(query: UpgradeInfoParam) -> AjaxResult:
    """获取最新的更新日志. Java: ``@GetMapping("/newest") public AjaxResult newest(SysUpgradeInfo)``.

    Java 的 SQL **无视入参**（没有 ``#{...}``），所以 ``?ver=...`` 之类不影响结果。
    查不到时 ``data`` 为 ``null``（键消失），不是 404。
    """
    return AjaxResult.success_data(_upgrade_info_service().select_sys_upgrade_info_newest(query))


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:
    """获取系统升级信息详细信息. Java: ``@GetMapping(value = "/{id}")``.

    ``id`` 是 **UUID 字符串**（不是 ``Long``）；查不到时 ``data`` 为 ``null``。
    因为能收任意字符串，所以 ``/export`` / ``/list`` / ``/newest`` 必须注册在它之前。
    """
    return AjaxResult.success_data(_upgrade_info_service().select_sys_upgrade_info_by_id(id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@log(title="系统升级信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: SysUpgradeInfo) -> AjaxResult:
    """新增系统升级信息. Java: ``@PostMapping public AjaxResult add(@RequestBody SysUpgradeInfo)``.

    没有 ``@Validated``，也没有 ``@PreAuthorize``；返回的是 service 的
    ``success("操作成功！", id)``。
    """
    return _upgrade_info_service().save_sys_upgrade_info(entity)


@router.put("", response_model=None)
@log(title="系统升级信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: SysUpgradeInfo) -> AjaxResult:
    """修改系统升级信息. Java: ``@PutMapping public AjaxResult edit(@RequestBody SysUpgradeInfo)``.

    与 ``add`` 走**同一个** service 方法：有 ``id`` 就改，没 ``id`` 就新增。
    """
    return _upgrade_info_service().save_sys_upgrade_info(entity)


@router.delete("/{ids}", response_model=None)
@log(title="系统升级信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除系统升级信息. Java: ``@DeleteMapping("/{ids}") public AjaxResult remove(@PathVariable String[] ids)``.

    软删除（``del_flag = '1'``），``count == 0`` 也回 200。
    """
    return _upgrade_info_service().delete_sys_upgrade_info_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "UpgradeInfoParam",
    "list_upgrade_infos",
    "newest",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_upgrade_info_controller",
]
