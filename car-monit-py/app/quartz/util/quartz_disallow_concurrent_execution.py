"""定时任务执行（禁止并发）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/QuartzDisallowConcurrentExecution.java

与 :class:`~app.quartz.util.quartz_job_execution.QuartzJobExecution` 的差别**只有**
类上的 ``@DisallowConcurrentExecution``：

```java
@DisallowConcurrentExecution
public class QuartzDisallowConcurrentExecution extends AbstractQuartzJob
{
    @Override
    protected void doExecute(JobExecutionContext context, SysJob sysJob) throws Exception
    {
        JobInvokeUtil.invokeMethod(sysJob);
    }
}
```

Python 没有注解，所以"禁止并发"由调度器按 ``sys_job.concurrent != "0"`` 施加
per-job 锁实现（见 :mod:`app.quartz.util.scheduler` 的模块 docstring）。
这个类本身仍然存在，因为 ``ScheduleUtils.getQuartzJobClass`` 是按**类型**
二选一的，删掉它那条分支就没有落点了。
"""

from __future__ import annotations

from app.quartz.domain.sys_job import SysJob
from app.quartz.util.abstract_quartz_job import AbstractQuartzJob
from app.quartz.util.job_invoke_util import invoke_method
from app.quartz.util.scheduler import JobExecutionContext


class QuartzDisallowConcurrentExecution(AbstractQuartzJob):
    """Java: ``@DisallowConcurrentExecution public class QuartzDisallowConcurrentExecution``."""

    #: Java: 类级注解 ``@DisallowConcurrentExecution`` —— 调度器据此加锁。
    disallow_concurrent_execution = True

    # Java: protected void doExecute(JobExecutionContext context, SysJob sysJob) throws Exception
    def do_execute(self, context: JobExecutionContext, sys_job: SysJob) -> None:
        invoke_method(sys_job)


__all__ = ["QuartzDisallowConcurrentExecution"]
