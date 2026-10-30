"""``/monitor/operlog`` -- 操作日志记录.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysOperlogController.java

端点清单（4 个映射，**全部迁移**）
--------------------------------
    =======================  =======  ==================================  ==========
    Java                      Method   Path                                Access
    =======================  =======  ==================================  ==========
    ``list(SysOperLog)``      GET      ``/monitor/operlog/list``            list
    ``export(SysOperLog)``    GET      ``/monitor/operlog/export``          export
    ``remove(Long[])``        DELETE   ``/monitor/operlog/{operIds}``       remove
    ``clean()``               DELETE   ``/monitor/operlog/clean``           remove
    =======================  =======  ==================================  ==========

与 ``system`` 包的关系
----------------------
``sys_oper_log`` 这张表**有写有读**：写入方是
:mod:`app.framework.aspectj.log_aspect`（各控制器上的 ``@log``），本控制器负责查与删。

``/clean`` 必须排在 ``/{operIds}`` 之前
---------------------------------------
``DELETE /monitor/operlog/clean`` 与 ``DELETE /monitor/operlog/{operIds}`` 只有
**注册顺序**能区分：FastAPI 按顺序匹配，``/{oper_ids}`` 会把 ``"clean"`` 当成
id 并在 ``int()`` 处 422。Java 侧靠 ``AntPathMatcher`` 的"字面量优先"规则，
即使 ``remove`` 声明在前也仍然命中 ``clean``；两种机制结果一致。

注意 Java 源码里 ``remove``（含 ``@Log``）在 ``clean`` **之前**声明，但
``/export`` 与 ``/list`` 都是 GET，与两个 DELETE 不冲突。

``export`` 没有 ``startPage()``
-------------------------------
Java 的 ``export`` 直接调 ``selectOperLogList``，**不分页**（也不 ``clearPage``）。
``startPage()`` 只在 ``list`` 里出现，而 FastAPI 是每请求独立的进程上下文，
所以只要 ``list`` 里挂起的分页参数在它自己的 mapper 调用里被 ``take_page()`` 消费，
``export`` 就天然是全量。返回的文件名落在 ``msg``（``AjaxResult.success(String)``
重载），要拿到字节还得再调 ``GET /common/download?fileName=...``。

``businessTypes`` 的绑定
------------------------
Java 的 ``private Integer[] businessTypes`` 是**只用于查询**的数组字段（不落库），
前端发的是重复参数 ``businessTypes=0&businessTypes=1``。Spring 的
``ServletModelAttributeMethodProcessor`` 取 ``getParameterValues`` 得到 ``String[]``
再逐元素转 ``Integer``。这里手工做同一件事，**且额外容忍逗号分隔**
（``businessTypes=0,1``）—— Java 在这种情况下会因 ``NumberFormatException``
回 500，Python 侧会正常查出结果。差异记在 ``COMPATIBILITY.md`` §39。

它**不能**交给 :func:`bind_query_params`：那里只认 ``str`` / ``int`` / ``bool`` /
``datetime`` 四种标量，``List[int]`` 会把原始字符串直接塞给 pydantic 而报错。
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

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
from app.system.domain.sys_oper_log import SysOperLog
from app.system.service.sys_oper_log_service import SysOperLogService, get_oper_log_service

router = APIRouter(prefix="/monitor/operlog", tags=["monitor-operlog"])

#: Java: ``com.ruoyi.web.controller.monitor.SysOperlogController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.monitor.SysOperlogController"

#: Java: ``@Excel(name = "操作日志")`` 的 sheet 名 —— 与 ``export`` 里的字面量一致。
EXPORT_SHEET_NAME = "操作日志"


# --------------------------------------------------------------------------- 依赖

_OPER_LOG_SERVICE: Optional[SysOperLogService] = None


def _oper_log_service() -> SysOperLogService:
    global _OPER_LOG_SERVICE
    if _OPER_LOG_SERVICE is None:
        _OPER_LOG_SERVICE = get_oper_log_service()
    return _OPER_LOG_SERVICE


def reset_oper_log_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _OPER_LOG_SERVICE
    _OPER_LOG_SERVICE = None


# --------------------------------------------------------------------------- 参数绑定


def _parse_business_types(values: List[str]) -> Optional[List[int]]:
    """``String[]`` -> ``Integer[]``（Java: ``StringToArrayConverter`` 逐元素转）。

    空列表返回 ``None``（不是 ``[]``）：Java 的 ``getParameterValues`` 返回
    ``null`` 时数组保持 ``null``，而 XML 的判据是
    ``businessTypes != null and businessTypes.length > 0``，两者等价。
    """
    if not values:
        return None
    parsed: List[int] = []
    for value in values:
        for part in value.split(","):
            if part == "":
                # Java: NumberFormatException -> BindException -> code 500
                raise ValueError(
                    'Failed to convert property value of type \'java.lang.String[]\' '
                    "to required type 'java.lang.Integer[]' for property 'businessTypes'; "
                    'nested exception is java.lang.NumberFormatException: For input string: ""'
                )
            parsed.append(int(part))
    return parsed


def _query_oper_log(request: Request) -> SysOperLog:
    """Java: 形参 ``SysOperLog operLog``（**没有** ``@RequestBody``）—— query string 绑定."""
    # ``businessTypes`` 单独处理（见模块 docstring），其余字段交给通用绑定器。
    # 重复参数取**第一个**，与 ``HttpServletRequest#getParameter`` 一致。
    scalars: Dict[str, Any] = {}
    for key, value in request.query_params.multi_items():
        if key == "businessTypes":
            continue
        scalars.setdefault(key, value)
    oper_log = bind_query_params(SysOperLog, scalars)
    oper_log.business_types = _parse_business_types(
        request.query_params.getlist("businessTypes")
    )
    return oper_log


#: 查询条件实体（``?title=...&status=0&businessTypes=1``）。
OperLogParam = Annotated[SysOperLog, Depends(_query_oper_log)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("monitor:operlog:list")
def list_oper_logs(oper_log: OperLogParam) -> TableDataInfo:
    """查询系统操作日志集合. Java: ``@GetMapping("/list")``.

    ``selectOperLogList`` 自带 ``order by oper_id desc``，所以 PageHelper
    **不会**追加客户端排序（``orderByColumn`` / ``isAsc`` 被忽略），见 mapper docstring。
    """
    start_page()
    rows = _oper_log_service().select_oper_log_list(oper_log)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("monitor:operlog:export")
@log(title="操作日志", business_type=BusinessType.EXPORT, java_method="export")
def export(oper_log: OperLogParam) -> AjaxResult:
    """导出操作日志. Java: ``@GetMapping("/export") public AjaxResult export(SysOperLog operLog)``.

    没有 ``startPage()`` —— 导出的是**全量**命中行。``msg`` 是生成的文件名
    （``AjaxResult.success(String)`` 重载），不是文件内容。
    """
    rows = _oper_log_service().select_oper_log_list(oper_log)
    return ExcelUtil(SysOperLog).export_excel(rows, EXPORT_SHEET_NAME)


# --------------------------------------------------------------------------- 删除


@router.delete("/clean", response_model=None)
@pre_authorize_permi("monitor:operlog:remove")
@log(title="操作日志", business_type=BusinessType.CLEAN, java_method="clean")
def clean() -> AjaxResult:
    """清空操作日志. Java: ``@DeleteMapping("/clean")``.

    权限点与 ``remove`` **相同**（``monitor:operlog:remove``），Java 原文如此 ——
    能删一条就能清空整表，没有更细的权限。

    实现是 ``truncate table sys_oper_log``：DDL、隐式提交、**不可回滚**，
    返回 ``AjaxResult.success()``（不看影响行数）。
    """
    _oper_log_service().clean_oper_log()
    return AjaxResult.success()


@router.delete("/{oper_ids}", response_model=None)
@pre_authorize_permi("monitor:operlog:remove")
def remove(oper_ids: str) -> AjaxResult:
    """删除操作日志. Java: ``@DeleteMapping("/{operIds}") public AjaxResult remove(@PathVariable Long[] operIds)``.

    ``"1,2"`` -> ``[1, 2]``（``parse_id_array``）；空串会在这里抛 ``ValueError``，
    落到通用处理器回 HTTP 200 + ``code 500``（Java 同样是
    ``MethodArgumentTypeMismatchException``）。
    """
    return to_ajax(_oper_log_service().delete_oper_log_by_ids(parse_id_array(oper_ids)))


__all__ = [
    "router",
    "OperLogParam",
    "EXPORT_SHEET_NAME",
    "list_oper_logs",
    "export",
    "clean",
    "remove",
    "reset_oper_log_controller",
]
