"""``/monitor/logininfor`` -- 系统访问记录（登录日志）.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysLogininforController.java

端点清单（4 个映射，**全部迁移**）
--------------------------------
    =======================  =======  ====================================  ==========
    Java                      Method   Path                                  Access
    =======================  =======  ====================================  ==========
    ``list(SysLogininfor)``   GET      ``/monitor/logininfor/list``            list
    ``export(SysLogininfor)`` GET      ``/monitor/logininfor/export``          export
    ``remove(Long[])``        DELETE   ``/monitor/logininfor/{infoIds}``       remove
    ``clean()``               DELETE   ``/monitor/logininfor/clean``           remove
    =======================  =======  ====================================  ==========

与 ``/monitor/operlog`` 的两处差别
----------------------------------
1. ``remove`` 上有 ``@Log(title = "登录日志", businessType = BusinessType.DELETE)``，
   ``operlog`` 的 ``remove`` **没有**。两边照 Java 原样，只有本控制器会写审计行。
2. 两个删除端点共用 ``monitor:logininfor:remove``，与 operlog 相同。

``clean`` / ``remove`` 的注册顺序
---------------------------------
``DELETE /monitor/logininfor/clean`` 必须排在 ``/{infoIds}`` 之前，理由与
``/monitor/operlog`` 完全一致（FastAPI 按顺序匹配；Spring 靠字面量优先）。

``status`` 是 ``String``
------------------------
``SysLogininfor.status`` 是 ``"0"``（成功）/ ``"1"``（失败）的**字符串**，而
``SysOperLog.status`` 是 ``Integer`` —— 两者不是同一类型，别把查询参数写成数字
再"顺手"统一。``?status=0`` 在两边都能命中，但实体字段类型不同。
"""

from __future__ import annotations

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
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.domain.sys_logininfor import SysLogininfor
from app.system.service.sys_logininfor_service import (
    SysLogininforService,
    get_logininfor_service,
)

router = APIRouter(prefix="/monitor/logininfor", tags=["monitor-logininfor"])

#: Java: ``com.ruoyi.web.controller.monitor.SysLogininforController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.monitor.SysLogininforController"

#: Java: ``util.exportExcel(list, "登录日志")`` 的 sheet 名。
EXPORT_SHEET_NAME = "登录日志"


# --------------------------------------------------------------------------- 依赖

_LOGININFOR_SERVICE: Optional[SysLogininforService] = None


def _logininfor_service() -> SysLogininforService:
    global _LOGININFOR_SERVICE
    if _LOGININFOR_SERVICE is None:
        _LOGININFOR_SERVICE = get_logininfor_service()
    return _LOGININFOR_SERVICE


def reset_logininfor_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _LOGININFOR_SERVICE
    _LOGININFOR_SERVICE = None


def _query_logininfor(request: Request) -> SysLogininfor:
    """Java: 形参 ``SysLogininfor logininfor``（**没有** ``@RequestBody``）。"""
    return bind_query_params(SysLogininfor, request.query_params)


#: 查询条件实体（``?ipaddr=...&status=0&userName=admin``）。
LogininforParam = Annotated[SysLogininfor, Depends(_query_logininfor)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("monitor:logininfor:list")
def list_logininfor(logininfor: LogininforParam) -> TableDataInfo:
    """查询系统登录日志集合. Java: ``@GetMapping("/list")``.

    语句自带 ``order by info_id desc``，客户端排序参数被忽略（与 operlog 相同）。
    """
    start_page()
    rows = _logininfor_service().select_logininfor_list(logininfor)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("monitor:logininfor:export")
@log(title="登录日志", business_type=BusinessType.EXPORT, java_method="export")
def export(logininfor: LogininforParam) -> AjaxResult:
    """导出登录日志. Java: ``@GetMapping("/export")``.

    不分页；``msg`` 是文件名（9 列的 ``@Excel`` 表，见 :class:`SysLogininfor`）。
    """
    rows = _logininfor_service().select_logininfor_list(logininfor)
    return ExcelUtil(SysLogininfor).export_excel(rows, EXPORT_SHEET_NAME)


# --------------------------------------------------------------------------- 删除


@router.delete("/clean", response_model=None)
@pre_authorize_permi("monitor:logininfor:remove")
@log(title="登录日志", business_type=BusinessType.CLEAN, java_method="clean")
def clean() -> AjaxResult:
    """清空系统登录日志. Java: ``@DeleteMapping("/clean")``.

    ``truncate table sys_logininfor``：DDL、隐式提交、**不可回滚**。
    """
    _logininfor_service().clean_logininfor()
    return AjaxResult.success()


@router.delete("/{info_ids}", response_model=None)
@pre_authorize_permi("monitor:logininfor:remove")
@log(title="登录日志", business_type=BusinessType.DELETE, java_method="remove")
def remove(info_ids: str) -> AjaxResult:
    """删除系统登录日志. Java: ``@DeleteMapping("/{infoIds}") public AjaxResult remove(@PathVariable Long[] infoIds)``."""
    return to_ajax(_logininfor_service().delete_logininfor_by_ids(parse_id_array(info_ids)))


__all__ = [
    "router",
    "LogininforParam",
    "EXPORT_SHEET_NAME",
    "list_logininfor",
    "export",
    "clean",
    "remove",
    "reset_logininfor_controller",
]
