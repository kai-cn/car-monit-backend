"""定时任务执行（允许并发）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/QuartzJobExecution.java

Java 全文只有一个重写的 ``doExecute``：

```java
@Override
protected void doExecute(JobExecutionContext context, SysJob sysJob) throws Exception
{
    JobInvokeUtil.invokeMethod(sysJob);
}
```

也就是说这个类**不做事**，真正的反射调用在 :func:`JobInvokeUtil.invokeMethod`。
作为一个"空壳"它仍然必须存在：``ScheduleUtils.getQuartzJobClass`` 用它的**类型**
来决定调度语义（这个类没有 ``@DisallowConcurrentExecution``，另一个类有），
调度器也要 ``newInstance()`` 一个实例出来才能调 ``execute``。
"""

from __future__ import annotations

from app.quartz.domain.sys_job import SysJob
from app.quartz.util.abstract_quartz_job import AbstractQuartzJob
from app.quartz.util.job_invoke_util import invoke_method
from app.quartz.util.scheduler import JobExecutionContext


class QuartzJobExecution(AbstractQuartzJob):
    """Java: ``public class QuartzJobExecution extends AbstractQuartzJob``."""

    # Java: protected void doExecute(JobExecutionContext context, SysJob sysJob) throws Exception
    def do_execute(self, context: JobExecutionContext, sys_job: SysJob) -> None:
        invoke_method(sys_job)


__all__ = ["QuartzJobExecution"]
