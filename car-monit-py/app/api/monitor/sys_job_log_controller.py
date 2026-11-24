"""``/monitor/jobLog`` -- 调度日志.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobLogController.java

端点清单（5 个映射，**全部迁移**）
--------------------------------
    ===========================  =======  ================================  ==========================
    Java                          Method   Path                              Access
    ===========================  =======  ================================  ==========================
    ``list(SysJobLog)``           GET      ``/monitor/jobLog/list``           ``monitor:job:list``
    ``export(SysJobLog)``         GET      ``/monitor/jobLog/export``         ``monitor:job:export``
    ``getInfo(Long)``             GET      ``/monitor/jobLog/{configId}``     ``monitor:job:query``
    ``remove(Long[])``            DELETE   ``/monitor/jobLog/{jobLogIds}``    ``monitor:job:remove``
    ``clean()``                   DELETE   ``/monitor/jobLog/clean``          ``monitor:job:remove``
    ===========================  =======  ================================  ==========================

``GET /{configId}`` **永远返回 500** —— 这是 Java 的一个真 bug，照抄
--------------------------------------------------------------
``@GetMapping(value = "/{configId}")`` 配的是 ``@PathVariable Long jobLogId``，**没有写名字**。
Spring 从参数名推出变量名 ``jobLogId``，而 URI 模板里只有 ``configId``，于是
``PathVariableMethodArgumentResolver#resolveName`` 取不到值 ->
``MissingPathVariableException``。线上实测（``evidence/_probe_job_err_out.txt`` 第 14/15 行）::

    GET /monitor/jobLog/1    -> HTTP 200 {"msg":"请求路径中缺少必需的路径变量[jobLogId]","code":500}
    GET /monitor/jobLog/abc  -> HTTP 200 {"msg":"请求路径中缺少必需的路径变量[jobLogId]","code":500}

注意 ``abc`` 也是同一句 —— **参数缺失发生在类型转换之前**，所以根本轮不到
``Long`` 转换失败。``jobLogService.selectJobLogById(...)`` 因此**永远走不到**，
方法本身在 :mod:`app.quartz.service.sys_job_log_service` 里照搬保留。

Python 侧无法复刻"路径变量对不上"，只能显式抛同样的文案。**不要**把它改成像样的
详情接口 —— 前端调这个接口拿到的一直是 500。

``@PreAuthorize`` 与参数解析的先后顺序（唯一的偏差）
----------------------------------------------------
Java 的 ``@PreAuthorize`` 由 AOP 拦截**方法调用**，而参数解析在
``InvocableHandlerMethod#getMethodArgumentValues`` 里、**调用之前**就做完了。所以
Java 的判定顺序是"路径变量缺失(500) -> 权限(403)"，连没权限的人拿到的也是 500。

Python 的 ``@pre_authorize_permi`` 是函数装饰器，先于函数体执行，于是
"有权限 -> 500、没权限 -> 403"。对线上唯一的真实调用方（有 ``monitor:job:query`` 的
管理员）两者一致；差异记在 ``COMPATIBILITY.md`` §43。

``/clean`` 必须排在 ``/{jobLogIds}`` 之前
-----------------------------------------
``DELETE /monitor/jobLog/clean`` 与 ``DELETE /monitor/jobLog/{jobLogIds}`` 只有
**注册顺序**能区分：FastAPI 按顺序匹配，``/{job_log_ids}`` 会把 ``"clean"`` 当成 id
再在 ``int()`` 处报错。Java 靠 ``AntPathMatcher`` 的"字面量优先"规则，即使 ``remove``
声明在前也仍然命中 ``clean``；两种机制结果一致。

``clean`` 的实现是 ``truncate table sys_job_log``（DDL、隐式提交、不可回滚），
返回 ``AjaxResult.success()``，不看影响行数。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_long_array,
    start_page,
    to_ajax,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.exception.exceptions import ServiceException
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.quartz.domain.sys_job_log import SysJobLog
from app.quartz.service.sys_job_log_service import SysJobLogService, get_job_log_service

router = APIRouter(prefix="/monitor/jobLog", tags=["monitor-jobLog"])

#: Java: ``com.ruoyi.quartz.controller.SysJobLogController`` —— 审计日志 ``method`` 列需要全类名.
JAVA_CONTROLLER = "com.ruoyi.quartz.controller.SysJobLogController"

#: Java: ``util.exportExcel(list, "调度日志")`` 的 sheet 名。
EXPORT_SHEET_NAME = "调度日志"

#: Java: ``String.format("请求路径中缺少必需的路径变量[%s]", e.getVariableName())``
#: —— ``getVariableName()`` 是参数名 ``jobLogId``，不是模板里的 ``configId``。
MISSING_PATH_VARIABLE_MESSAGE = "请求路径中缺少必需的路径变量[jobLogId]"


# --------------------------------------------------------------------------- 依赖

_JOB_LOG_SERVICE: Optional[SysJobLogService] = None


def _job_log_service() -> SysJobLogService:
    """Java: ``@Autowired private ISysJobLogService jobLogService``（Spring 单例）."""
    global _JOB_LOG_SERVICE
    if _JOB_LOG_SERVICE is None:
        _JOB_LOG_SERVICE = get_job_log_service()
    return _JOB_LOG_SERVICE


def reset_job_log_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _JOB_LOG_SERVICE
    _JOB_LOG_SERVICE = None


# --------------------------------------------------------------------------- 参数绑定


def _query_job_log(request: Request) -> SysJobLog:
    """Java: 形参 ``SysJobLog sysJobLog``（**没有** ``@RequestBody``）—— query string 绑定."""
    return bind_query_params(SysJobLog, request.query_params)


#: 查询条件实体（``?jobName=...&jobGroup=...&status=...``）。
JobLogParam = Annotated[SysJobLog, Depends(_query_job_log)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("monitor:job:list")
def list_job_logs(job_log: JobLogParam) -> TableDataInfo:
    """查询定时任务调度日志列表. Java: ``@GetMapping("/list")``.

    权限点是 ``monitor:job:list``（**不是** ``monitor:jobLog:list``，这个串不存在）；
    ``selectJobLogList`` 自带 ``order by job_log_id desc``，PageHelper 不会追加排序。
    """
    start_page()
    rows = _job_log_service().select_job_log_list(job_log)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("monitor:job:export")
@log(title="任务调度日志", business_type=BusinessType.EXPORT, java_method="export")
def export(job_log: JobLogParam) -> AjaxResult:
    """导出调度日志. Java: ``@GetMapping("/export")``.

    没有 ``startPage()``。``msg`` 是文件名，不是文件内容。
    """
    rows = _job_log_service().select_job_log_list(job_log)
    return ExcelUtil(SysJobLog).export_excel(rows, EXPORT_SHEET_NAME)


@router.get("/{config_id}", response_model=None)
@pre_authorize_permi("monitor:job:query")
def get_info(config_id: str) -> AjaxResult:
    """根据调度编号获取详细信息. Java: ``@GetMapping(value = "/{configId}")``.

    **永远 500**：路径变量叫 ``configId``，参数名却是 ``jobLogId``，Spring 解析不到 ->
    ``MissingPathVariableException``。见模块 docstring。

    路径参数声明成 ``str`` 是刻意的：Java 连 ``abc`` 都回同一句（参数缺失在类型转换之前），
    若在这里写 ``int``，非数字路径会变成 FastAPI 自己的 422，反而偏离。
    """
    row = _job_log_service().select_job_log_by_id(config_id)
    return AjaxResult.success_data(row)


# --------------------------------------------------------------------------- 删除


@router.delete("/clean", response_model=None)
@pre_authorize_permi("monitor:job:remove")
@log(title="调度日志", business_type=BusinessType.CLEAN, java_method="clean")
def clean() -> AjaxResult:
    """清空定时任务调度日志. Java: ``@DeleteMapping("/clean")``.

    权限点与 ``remove`` 相同（``monitor:job:remove``）。实现是
    ``truncate table sys_job_log``：DDL、隐式提交、**不可回滚**，恒回成功。
    注意 ``@Log`` 的 ``title`` 是「调度日志」（比类注释的「任务调度日志」少两个字，
    Java 原文如此）。
    """
    _job_log_service().clean_job_log()
    return AjaxResult.success()


@router.delete("/{job_log_ids}", response_model=None)
@pre_authorize_permi("monitor:job:remove")
@log(title="定时任务调度日志", business_type=BusinessType.DELETE, java_method="remove")
def remove(job_log_ids: str) -> AjaxResult:
    """删除定时任务调度日志. Java: ``@DeleteMapping("/{jobLogIds}")``.

    这里是 ``toAjax(deleteJobLogByIds(...))`` —— 与 ``SysJobController#remove``
    不同，**不是**无条件成功：删 0 行时回 ``{"msg":"操作失败","code":500}``
    （线上第 16 行）。批量删除语句本身不区分 id 是否存在。
    """
    return to_ajax(
        _job_log_service().delete_job_log_by_ids(parse_long_array(job_log_ids, "jobLogIds"))
    )


__all__ = [
    "router",
    "JobLogParam",
    "JAVA_CONTROLLER",
    "EXPORT_SHEET_NAME",
    "MISSING_PATH_VARIABLE_MESSAGE",
    "list_job_logs",
    "export",
    "get_info",
    "clean",
    "remove",
    "reset_job_log_controller",
]
