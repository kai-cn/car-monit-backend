"""定时任务工具类.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/ScheduleUtils.java

5 个静态方法，全部 1:1 迁移：

    ====================================================  ==================================
    Java                                                   Python
    ====================================================  ==================================
    ``getQuartzJobClass(SysJob)``                          :func:`get_quartz_job_class`
    ``getTriggerKey(Long jobId, String jobGroup)``          :func:`get_trigger_key`
    ``getJobKey(Long jobId, String jobGroup)``              :func:`get_job_key`
    ``createScheduleJob(Scheduler, SysJob)``                :func:`create_schedule_job`
    ``handleCronScheduleMisfirePolicy(SysJob, CBS)``        :func:`handle_cron_schedule_misfire_policy`
    ====================================================  ==================================

``TASK_CLASS_NAME + jobId`` 是**字符串拼接**
--------------------------------------------
Java 的 ``ScheduleConstants.TASK_CLASS_NAME + jobId`` 里 ``jobId`` 是 ``Long``：
``null`` 拼出来是字面量 ``"TASK_CLASS_NAME" + "null"``。Python 的 ``str(None)`` 是
``"None"``，所以这里用 :func:`_java_concat` 复刻 Java 的拼接语义 ——
否则 ``jobGroup``/``jobId`` 缺失时的 Key 会和线上对不上。

``job.getStatus().equals(PAUSE)`` 会 NPE
---------------------------------------
``createScheduleJob`` 最后一句是 ``if (job.getStatus().equals(...))``，**没有** null 判断。
``PUT /monitor/job`` 的请求体不带 ``status`` 时，``updateJob`` -> ``updateSchedulerJob``
-> ``createScheduleJob`` 会在这里抛 ``NullPointerException``，``GlobalExceptionHandler``
回 ``{"code":500,"msg":null}``。这是 Java 侧真实的可观察行为，照抄（见
``_require_non_null``）。只有 ``insertJob`` 和 ``init()`` 能活下来，因为前者把
``status`` 强制设成 ``PAUSE``，后者的 ``status`` 来自 ``char(1)`` 非空列。
"""

from __future__ import annotations

from typing import Any, Optional

from app.common.constant.schedule_constants import (
    MISFIRE_DEFAULT,
    MISFIRE_DO_NOTHING,
    MISFIRE_FIRE_AND_PROCEED,
    MISFIRE_IGNORE_MISFIRES,
    TASK_CLASS_NAME,
    TASK_PROPERTIES,
    Status,
)
from app.common.exception.job.task_exception import TaskException
from app.quartz.domain.sys_job import SysJob
from app.quartz.util.quartz_disallow_concurrent_execution import (
    QuartzDisallowConcurrentExecution,
)
from app.quartz.util.quartz_job_execution import QuartzJobExecution
from app.quartz.util.scheduler import (
    CronScheduleBuilder,
    JobBuilder,
    JobKey,
    Scheduler,
    TriggerBuilder,
    TriggerKey,
)


# Java: private static Class<? extends Job> getQuartzJobClass(SysJob sysJob)
def get_quartz_job_class(sys_job: SysJob) -> type:
    """``concurrent == "0"`` -> 允许并发；其余（含 ``null``）-> 禁止并发."""
    is_concurrent = "0" == sys_job.concurrent
    return QuartzJobExecution if is_concurrent else QuartzDisallowConcurrentExecution


# Java: public static TriggerKey getTriggerKey(Long jobId, String jobGroup)
def get_trigger_key(job_id: Optional[int], job_group: Optional[str]) -> TriggerKey:
    """构建任务触发对象."""
    return TriggerKey.trigger_key(_job_name(job_id), job_group)


# Java: public static JobKey getJobKey(Long jobId, String jobGroup)
def get_job_key(job_id: Optional[int], job_group: Optional[str]) -> JobKey:
    """构建任务键对象（``TASK_CLASS_NAME + jobId``，group 缺省为 ``DEFAULT``）。"""
    return JobKey.job_key(_job_name(job_id), job_group)


# Java: public static void createScheduleJob(Scheduler scheduler, SysJob job)
def create_schedule_job(scheduler: Scheduler, job: SysJob) -> None:
    """创建定时任务（存在则先删后建，最后按 ``status`` 决定是否暂停）."""
    job_class = get_quartz_job_class(job)
    job_id = job.job_id
    job_group = job.job_group

    # Java: JobDetail jobDetail = JobBuilder.newJob(jobClass).withIdentity(getJobKey(jobId, jobGroup)).build();
    job_detail = (
        JobBuilder.new_job(job_class).with_identity(get_job_key(job_id, job_group)).build()
    )

    # Java: CronScheduleBuilder cronScheduleBuilder = CronScheduleBuilder.cronSchedule(job.getCronExpression());
    cron_schedule_builder = CronScheduleBuilder.cron_schedule(job.cron_expression)
    cron_schedule_builder = handle_cron_schedule_misfire_policy(job, cron_schedule_builder)

    # Java: CronTrigger trigger = TriggerBuilder.newTrigger().withIdentity(getTriggerKey(jobId, jobGroup)).withSchedule(cronScheduleBuilder).build();
    trigger = (
        TriggerBuilder.new_trigger()
        .with_identity(get_trigger_key(job_id, job_group))
        .with_schedule(cron_schedule_builder)
        .build()
    )

    # Java: jobDetail.getJobDataMap().put(ScheduleConstants.TASK_PROPERTIES, job);
    job_detail.job_data_map[TASK_PROPERTIES] = job

    job_key = get_job_key(job_id, job_group)
    # Java: if (scheduler.checkExists(getJobKey(jobId, jobGroup))) { scheduler.deleteJob(...); }
    if scheduler.check_exists(job_key):
        # 防止创建时存在数据问题 先移除，然后在执行创建操作
        scheduler.delete_job(job_key)

    scheduler.schedule_job(job_detail, trigger)

    # Java: if (job.getStatus().equals(ScheduleConstants.Status.PAUSE.getValue()))
    if _equals(job.status, Status.PAUSE.value):
        scheduler.pause_job(job_key)


# Java: public static CronScheduleBuilder handleCronScheduleMisfirePolicy(SysJob job, CronScheduleBuilder cb)
def handle_cron_schedule_misfire_policy(
    job: SysJob, cb: CronScheduleBuilder
) -> CronScheduleBuilder:
    """``sys_job.misfire_policy`` 的四个分支，其余值抛 :class:`TaskException`."""
    policy = job.misfire_policy
    if policy == MISFIRE_DEFAULT:
        return cb
    if policy == MISFIRE_IGNORE_MISFIRES:
        return cb.with_misfire_handling_instruction_ignore_misfires()
    if policy == MISFIRE_FIRE_AND_PROCEED:
        return cb.with_misfire_handling_instruction_fire_and_proceed()
    if policy == MISFIRE_DO_NOTHING:
        return cb.with_misfire_handling_instruction_do_nothing()
    # Java: throw new TaskException("The task misfire policy '" + job.getMisfirePolicy()
    #         + "' cannot be used in cron schedule tasks", Code.CONFIG_ERROR);
    raise TaskException(
        "The task misfire policy '%s' cannot be used in cron schedule tasks"
        % _java_concat(policy),
        TaskException.Code.CONFIG_ERROR,
    )


def _job_name(job_id: Optional[int]) -> str:
    """Java: ``ScheduleConstants.TASK_CLASS_NAME + jobId``（``Long`` 拼接）."""
    return TASK_CLASS_NAME + _java_concat(job_id)


def _java_concat(value: Any) -> str:
    """Java 的 ``String + Object``：``null`` -> ``"null"``."""
    if value is None:
        return "null"
    return str(value)


def _equals(left: Optional[str], right: str) -> bool:
    """Java: ``left.equals(right)`` —— ``left`` 为 ``null`` 时 NPE（照抄）."""
    _require_non_null(left)
    return left == right


def _require_non_null(value: Any) -> None:
    """复刻 ``NullPointerException``：``GlobalExceptionHandler`` 会把它变成 ``msg: null``."""
    if value is None:
        raise AttributeError("'NoneType' object has no attribute 'equals'")


__all__ = [
    "get_quartz_job_class",
    "get_trigger_key",
    "get_job_key",
    "create_schedule_job",
    "handle_cron_schedule_misfire_policy",
]
