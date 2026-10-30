"""抽象 quartz 调用.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/AbstractQuartzJob.java

Java 是 ``public abstract class AbstractQuartzJob implements Job``，两个子类
（:class:`~app.quartz.util.quartz_job_execution.QuartzJobExecution` 与
:class:`~app.quartz.util.quartz_disallow_concurrent_execution.QuartzDisallowConcurrentExecution`）
只重写 ``doExecute``。

执行流程（**顺序即语义**）
--------------------------
1. ``new SysJob()`` + ``BeanUtils.copyBeanProp(sysJob, dataMap.get(TASK_PROPERTIES))``
   —— 从 ``JobDataMap`` 里捞任务定义；
2. ``before(context, sysJob)`` —— 把当前时间写进 ``ThreadLocal``；
3. ``doExecute(context, sysJob)``；
4. ``after(context, sysJob, null)`` —— 写一条 ``sys_job_log``（成功）；
5. 第 3 步抛任何异常 -> ``catch`` -> ``after(context, sysJob, e)``（失败 +
   2000 字截断的堆栈）。

``after`` 里的作业日志
----------------------
``jobMessage = jobName + " 总共耗时：" + runMs + "毫秒"``。线上
``evidence/_probe_job2_out.txt`` 的 ``"可疑车俩数据同步 总共耗时：8毫秒"`` 就是这个格式；
``jobName`` 为 ``null`` 时 Java 的字符串拼接会得到 ``"null 总共耗时：0毫秒"``，
这里用 :func:`_java_concat` 复刻。

``getExceptionMessage`` 是**完整堆栈**（``printStackTrace``），不是 ``getMessage()``；
线上 ``sys_job_log.exception_info`` 里那一大段 ``org.springframework...`` 就是它。
截断用 ``StringUtils.substring(msg, 0, 2000)`` —— 超长时**没有省略号**。

``ThreadLocal`` -> ``threading.local``
-------------------------------------
调度器每个任务在独立线程里跑（``ThreadPoolExecutor``），``ThreadLocal`` 的作用
只是"把开始时间从 ``before`` 传到 ``after``"。``threading.local`` 语义一致，且
``after`` 末尾同样会 ``remove``（Java 原文有 ``threadLocal.remove()``）。
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Optional

from app.common.constant.constants import FAIL, SUCCESS
from app.common.constant.schedule_constants import TASK_PROPERTIES
from app.common.utils.bean_utils import copy_bean_prop
from app.common.utils.exception_util import get_exception_message
from app.common.utils.string_utils import substring
from app.quartz.domain.sys_job import SysJob
from app.quartz.domain.sys_job_log import SysJobLog
from app.quartz.util.scheduler import JobExecutionContext

logger = logging.getLogger("app.quartz.util.abstract_quartz_job")

#: Java: ``private static ThreadLocal<Date> threadLocal = new ThreadLocal<>();``
_thread_local = threading.local()

#: Java: ``StringUtils.substring(msg, 0, 2000)`` 的上界。
_EXCEPTION_INFO_MAX_LENGTH = 2000


class AbstractQuartzJob:
    """Java: ``public abstract class AbstractQuartzJob implements Job``."""

    # Java: public void execute(JobExecutionContext context) throws JobExecutionException
    def execute(self, context: JobExecutionContext) -> None:
        sys_job = SysJob()
        # Java: BeanUtils.copyBeanProp(sysJob, context.getMergedJobDataMap().get(TASK_PROPERTIES));
        copy_bean_prop(sys_job, context.get_merged_job_data_map().get(TASK_PROPERTIES))
        try:
            self.before(context, sys_job)
            # Java: if (sysJob != null) —— sys_job 永远是新建的对象，条件恒真，照抄
            if sys_job is not None:
                self.do_execute(context, sys_job)
            self.after(context, sys_job, None)
        except Exception as e:  # noqa: BLE001 - Java 同样是 catch (Exception e)
            logger.error("任务执行异常  - ：", exc_info=e)
            self.after(context, sys_job, e)

    # Java: protected void before(JobExecutionContext context, SysJob sysJob)
    def before(self, context: JobExecutionContext, sys_job: SysJob) -> None:
        _thread_local.start_time = datetime.now()

    # Java: protected void after(JobExecutionContext context, SysJob sysJob, Exception e)
    def after(
        self,
        context: JobExecutionContext,
        sys_job: SysJob,
        error: Optional[BaseException],
    ) -> None:
        start_time: Optional[datetime] = getattr(_thread_local, "start_time", None)
        # Java: threadLocal.remove();
        if hasattr(_thread_local, "start_time"):
            del _thread_local.start_time

        job_log = SysJobLog()
        job_log.job_name = sys_job.job_name
        job_log.job_group = sys_job.job_group
        job_log.invoke_target = sys_job.invoke_target
        job_log.start_time = start_time
        job_log.stop_time = datetime.now()
        # Java: long runMs = stopTime.getTime() - startTime.getTime();
        run_ms = _millis(job_log.stop_time) - _millis(job_log.start_time)
        # Java: jobName + " 总共耗时：" + runMs + "毫秒"
        job_log.job_message = f"{_java_concat(job_log.job_name)} 总共耗时：{run_ms}毫秒"

        if error is not None:
            job_log.status = FAIL
            # Java: StringUtils.substring(ExceptionUtil.getExceptionMessage(e), 0, 2000)
            job_log.exception_info = substring(get_exception_message(error), 0, _EXCEPTION_INFO_MAX_LENGTH)
        else:
            job_log.status = SUCCESS

        # Java: SpringUtils.getBean(ISysJobLogService.class).addJobLog(sysJobLog);
        _job_log_service().add_job_log(job_log)

    # Java: protected abstract void doExecute(JobExecutionContext context, SysJob sysJob)
    def do_execute(self, context: JobExecutionContext, sys_job: SysJob) -> None:
        raise NotImplementedError


def _job_log_service() -> Any:
    """Java: ``SpringUtils.getBean(ISysJobLogService.class)``.

    局部导入：``sys_job_log_service`` 依赖 ``mapper`` -> ``domain``，与本模块不构成环，
    但本模块被 ``abstract_quartz_job`` 的**子类**在 import 期引用，局部导入更安全。
    """
    from app.quartz.service.sys_job_log_service import get_job_log_service

    return get_job_log_service()


def _millis(value: Optional[datetime]) -> int:
    """Java: ``Date#getTime()`` —— 毫秒时间戳；``null`` 时 NPE（这里显式抛）."""
    if value is None:
        raise AttributeError("'NoneType' object has no attribute 'getTime'")
    return int(value.timestamp() * 1000)


def _java_concat(value: Optional[str]) -> str:
    """Java 字符串拼接：``null`` -> 字面量 ``"null"``."""
    return "null" if value is None else value


__all__ = ["AbstractQuartzJob"]
