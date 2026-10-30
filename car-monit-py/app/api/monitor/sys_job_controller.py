"""``/monitor/job`` -- 定时任务调度.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java

端点清单（8 个映射，**全部迁移**）
--------------------------------
    ==========================  =======  ==============================  ==========================
    Java                         Method   Path                            Access
    ==========================  =======  ==============================  ==========================
    ``list(SysJob)``             GET      ``/monitor/job/list``            ``monitor:job:list``
    ``export(SysJob)``           GET      ``/monitor/job/export``          ``monitor:job:export``
    ``getInfo(Long)``            GET      ``/monitor/job/{jobId}``         ``monitor:job:query``
    ``add(SysJob)``              POST     ``/monitor/job``                 ``monitor:job:add``
    ``edit(SysJob)``             PUT      ``/monitor/job``                 ``monitor:job:edit``
    ``changeStatus(SysJob)``     PUT      ``/monitor/job/changeStatus``    ``monitor:job:changeStatus``
    ``run(SysJob)``              PUT      ``/monitor/job/run``             ``monitor:job:changeStatus``
    ``remove(Long[])``           DELETE   ``/monitor/job/{jobIds}``        ``monitor:job:remove``
    ==========================  =======  ==============================  ==========================

注意 ``run`` 用的是 **``changeStatus`` 的权限点**（不是 ``monitor:job:run``，压根没有这个串）。
Java 原文如此，照抄。

线上实测（``evidence/_probe_job_err_out.txt``，逐条对齐）
------------------------------------------------
==============================  ====================================================  ==========
请求                             响应                                                   代码位置
==============================  ====================================================  ==========
``POST {}``                      ``{"msg":"cronExpression cannot be null"}``            第 1 行
``POST cron=""``                 ``{"msg":"cron表达式不正确"}``                          第 2 行
``POST misfirePolicy="9"``       ``{"msg":"The task misfire policy '9' cannot be ...``   第 5 行
``POST 缺 invokeTarget``          ``Field 'invoke_target' doesn't have a default value``  第 4 行
``PUT {jobId:999999}``           ``{"msg":"操作失败"}``（``toAjax(0)``）                  第 8 行
``PUT /changeStatus 999999``     ``{"msg":null}``（NPE）                                 第 9 行
``PUT /run {jobId:999999}``      ``{"msg":"The job (DEFAULT.TASK_CLASS_NAME999999) ...`` 第 10 行
``DELETE /999999``               ``{"msg":null}``（NPE）                                 第 11 行
``DELETE /abc``                  ``{"msg":"请求参数类型不匹配，参数[jobIds]...``            第 12 行
``GET /999999``                  ``{"msg":"操作成功","code":200}``（**没有 ``data`` 键**）   第 13 行
==============================  ====================================================  ==========

三个"看起来像 bug、但必须照抄"的点
-----------------------------------
1. **``GET /{jobId}`` 查不到时没有 ``data`` 键**。``AjaxResult.success(Object)`` 里
   ``if (StringUtils.isNotNull(data))`` 成立才放 ``data``，``null`` 被吞掉，所以响应
   就是 ``{"code":200,"msg":"操作成功"}`` —— 不是 ``{"data":null}``。见
   :meth:`AjaxResult._create`。
2. **cron 校验在落库之前**，且 ``isValid(null)`` 不是返回 ``false`` 而是**抛**
   ``IllegalArgumentException``（``CronExpression`` 构造器），所以缺
   ``cronExpression`` 的报错文案是英文的 ``cronExpression cannot be null``，
   而空串 ``""`` 才是中文的 ``cron表达式不正确``。两条路径必须分开。
3. **``misfirePolicy`` 非法时插入的那一行会回滚**。``@Transactional`` 让
   ``insertJob`` -> ``createScheduleJob`` -> ``TaskException`` 把刚落库的行撤掉；
   线上验证过报错后数据库没有残留行。Python 侧由
   :meth:`~app.quartz.service.sys_job_service.SysJobService.insert_job` 的
   ``with session_scope()`` 复刻，见该方法的 docstring。

``@Log`` 与 ``method`` 列
-------------------------
``export`` / ``add`` / ``edit`` / ``changeStatus`` / ``run`` / ``remove`` 六个映射带
``@Log``，``businessType`` 依次是 ``EXPORT`` / ``INSERT`` / ``UPDATE`` / ``UPDATE`` /
``UPDATE`` / ``DELETE``；``title`` 全是「定时任务」（只有日志导出是「定时任务」，
调度日志那边才是「调度日志」，别混）。
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
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.quartz.domain.sys_job import SysJob
from app.quartz.service.sys_job_service import SysJobService, get_job_service
from app.quartz.util.cron_utils import CronUtils

router = APIRouter(prefix="/monitor/job", tags=["monitor-job"])

#: Java: ``com.ruoyi.quartz.controller.SysJobController`` —— 审计日志 ``method`` 列需要全类名.
#:
#: 注意它在 **quartz** 模块里，不是 ``com.ruoyi.web.controller.monitor`` —— RuoYi 只有
#: ``SysJob`` / ``SysJobLog`` 两个控制器留在 quartz 包，其余 monitor 控制器都在 admin 模块。
JAVA_CONTROLLER = "com.ruoyi.quartz.controller.SysJobController"

#: Java: ``util.exportExcel(list, "定时任务")`` 的 sheet 名。
EXPORT_SHEET_NAME = "定时任务"

#: Java: ``AjaxResult.error("cron表达式不正确")`` —— 非法表达式（**非 null**）的固定文案。
INVALID_CRON_MESSAGE = "cron表达式不正确"


# --------------------------------------------------------------------------- 依赖

_JOB_SERVICE: Optional[SysJobService] = None


def _job_service() -> SysJobService:
    """Java: ``@Autowired private ISysJobService jobService``（Spring 单例）."""
    global _JOB_SERVICE
    if _JOB_SERVICE is None:
        _JOB_SERVICE = get_job_service()
    return _JOB_SERVICE


def reset_job_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _JOB_SERVICE
    _JOB_SERVICE = None


# --------------------------------------------------------------------------- 参数绑定


def _query_job(request: Request) -> SysJob:
    """Java: 形参 ``SysJob sysJob``（**没有** ``@RequestBody``）—— query string 绑定."""
    return bind_query_params(SysJob, request.query_params)


#: 查询条件实体（``?jobName=...&jobGroup=...``）。
JobParam = Annotated[SysJob, Depends(_query_job)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("monitor:job:list")
def list_jobs(job: JobParam) -> TableDataInfo:
    """查询定时任务列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysJob sysJob)``.

    ``selectJobList`` 没有 ``order by``，所以 PageHelper 会追加
    ``orderByColumn`` / ``isAsc``（默认 ``job_id asc``），见
    :mod:`app.quartz.mapper.sys_job_mapper`。
    """
    start_page()
    rows = _job_service().select_job_list(job)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("monitor:job:export")
@log(title="定时任务", business_type=BusinessType.EXPORT, java_method="export")
def export(job: JobParam) -> AjaxResult:
    """导出定时任务列表. Java: ``@GetMapping("/export") public AjaxResult export(SysJob sysJob)``.

    没有 ``startPage()`` —— 导出的是**全量**命中行。``msg`` 是生成的文件名
    （``AjaxResult.success(String)`` 重载），要拿字节还得再调
    ``GET /common/download?fileName=...``。
    """
    rows = _job_service().select_job_list(job)
    return ExcelUtil(SysJob).export_excel(rows, EXPORT_SHEET_NAME)


@router.get("/{job_id}", response_model=None)
@pre_authorize_permi("monitor:job:query")
def get_info(job_id: int) -> AjaxResult:
    """获取定时任务详细信息. Java: ``@GetMapping(value = "/{jobId}")``.

    查不到时响应里**没有 ``data`` 键**（``AjaxResult.success(Object)`` 的 null 判断），
    见模块 docstring 第 1 条。
    """
    return AjaxResult.success_data(_job_service().select_job_by_id(job_id))


# --------------------------------------------------------------------------- 增改


@router.post("", response_model=None)
@pre_authorize_permi("monitor:job:add")
@log(title="定时任务", business_type=BusinessType.INSERT, java_method="add")
def add(job: SysJob) -> AjaxResult:
    """新增定时任务. Java: ``@PostMapping public AjaxResult add(@RequestBody SysJob sysJob)``.

    顺序是 Java 的、不能换：先 ``CronUtils.isValid``（``null`` 会**抛**、空串返回
    ``false``），再 ``setCreateBy(当前用户名)``，最后 ``insertJob``。
    ``insertJob`` 里会把 ``status`` 强制成 ``PAUSE``，并把「落库 + 注册调度」放进
    同一个事务 —— ``misfirePolicy`` 非法导致 ``TaskException`` 时插入行会被回滚。
    """
    if not CronUtils.is_valid(job.cron_expression):
        return AjaxResult.error_message(INVALID_CRON_MESSAGE)
    job.create_by = SecurityUtils.get_username()
    return to_ajax(_job_service().insert_job(job))


@router.put("", response_model=None)
@pre_authorize_permi("monitor:job:edit")
@log(title="定时任务", business_type=BusinessType.UPDATE, java_method="edit")
def edit(job: SysJob) -> AjaxResult:
    """修改定时任务. Java: ``@PutMapping public AjaxResult edit(@RequestBody SysJob sysJob)``.

    ``jobId`` 不存在时 ``update_job`` 的影响行数是 0 -> ``toAjax(0)`` ->
    ``{"msg":"操作失败","code":500}``。注意 ``properties``（旧值）为 ``null`` 时
    ``properties.job_group`` 会 NPE，但 ``if (rows > 0)`` 挡在前面，走不到 —— 照抄这个
    顺序，**不要**提前判空。
    """
    if not CronUtils.is_valid(job.cron_expression):
        return AjaxResult.error_message(INVALID_CRON_MESSAGE)
    job.update_by = SecurityUtils.get_username()
    return to_ajax(_job_service().update_job(job))


@router.put("/changeStatus", response_model=None)
@pre_authorize_permi("monitor:job:changeStatus")
@log(title="定时任务", business_type=BusinessType.UPDATE, java_method="changeStatus")
def change_status(job: SysJob) -> AjaxResult:
    """任务状态修改. Java: ``@PutMapping("/changeStatus") public AjaxResult changeStatus(@RequestBody SysJob job)``.

    只认请求体里的 ``jobId`` 与 ``status``，**其余字段丢弃**：先按 id 查出完整旧值，
    再把 ``status`` 覆盖上去。``jobId`` 不存在时 ``newJob`` 为 ``null``，这一行就是
    线上 ``{"msg":null,"code":500}`` 的 NPE（``AttributeError`` 承担 NPE 的角色）。
    """
    new_job = _job_service().select_job_by_id(job.job_id)
    # Java: newJob.setStatus(job.getStatus());  —— newJob 为 null 时 NPE，照抄不判空
    new_job.status = job.status
    return to_ajax(_job_service().change_status(new_job))


@router.put("/run", response_model=None)
@pre_authorize_permi("monitor:job:changeStatus")
@log(title="定时任务", business_type=BusinessType.UPDATE, java_method="run")
def run(job: SysJob) -> AjaxResult:
    """定时任务立即执行一次. Java: ``@PutMapping("/run") public AjaxResult run(@RequestBody SysJob job)``.

    任务不在调度器里时 ``triggerJob`` 抛 ``SchedulerException``，文案是
    ``The job (DEFAULT.TASK_CLASS_NAME999999) referenced by the trigger does not exist.``
    —— 括号里是 ``JobKey.toString()``（``group.name``），**名字是**
    ``TASK_CLASS_NAME + jobId``。响应永远是 ``AjaxResult.success()``，不看任务是否
    真的执行成功（Quartz 是异步的）。
    """
    _job_service().run(job)
    return AjaxResult.success()


# --------------------------------------------------------------------------- 删除


@router.delete("/{job_ids}", response_model=None)
@pre_authorize_permi("monitor:job:remove")
@log(title="定时任务", business_type=BusinessType.DELETE, java_method="remove")
def remove(job_ids: str) -> AjaxResult:
    """删除定时任务. Java: ``@DeleteMapping("/{jobIds}") public AjaxResult remove(@PathVariable Long[] jobIds)``.

    逐条「查 -> 删」；**任何一条查不到就是 NPE**（``deleteJob(null)`` 里
    ``job.getJobId()``），响应 ``{"msg":null,"code":500}``，后面的 id 也不会被处理。
    删除成功后对应的 trigger 一并移除。
    """
    _job_service().delete_job_by_ids(parse_long_array(job_ids, "jobIds"))
    return AjaxResult.success()


__all__ = [
    "router",
    "JobParam",
    "JAVA_CONTROLLER",
    "EXPORT_SHEET_NAME",
    "INVALID_CRON_MESSAGE",
    "list_jobs",
    "export",
    "get_info",
    "add",
    "edit",
    "change_status",
    "run",
    "remove",
    "reset_job_controller",
]
