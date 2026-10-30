"""定时任务配置 —— **Java 原文整文件被注释掉**，这里只做存档.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/config/ScheduleConfig.java

这个模块**没有**任何运行期行为，也没有导出任何对象。它存在的唯一理由是
"不删除 Java 里看似无用的代码"：``ScheduleConfig`` 虽然一行都不生效，却是
"集群部署该配什么"的唯一书面依据。

为什么 Java 里它不生效
----------------------
``ScheduleConfig.java`` 的 **58 行全部以 ``//`` 开头**（连 ``package`` 声明都是），
所以编译产物里根本没有这个类，Spring 不会注册 ``SchedulerFactoryBean``。于是
Spring Boot 的 ``QuartzAutoConfiguration`` 接管，落地成：

===============================  ==========================================
配置项                           实际生效值
===============================  ==========================================
``org.quartz.jobStore.class``    ``RAMJobStore``（内存，重启即丢）
``org.quartz.threadPool.class``  ``SimpleThreadPool``
``threadPool.threadCount``       ``10``（Spring Boot 默认，不是下面的 20）
``jobStore.misfireThreshold``    ``60000`` ms（不是下面的 12000）
``isClustered``                  ``false``
===============================  ==========================================

上面这些默认值在 :mod:`app.quartz.util.scheduler` 里被逐条复刻
（``THREAD_COUNT = 10`` / ``MISFIRE_THRESHOLD_MS = 60_000`` / 进程内字典当 JobStore）。

如果将来真要启用集群
--------------------
把下面的 ``CLUSTERED_SCHEDULER_PROPERTIES`` 抄进配置、并把 JobStore 换成
``LocalDataSourceJobStore`` + ``QRTZ_`` 表（``sql/quartz.sql``）即可 —— 但那时
:mod:`app.quartz.util.scheduler` 的内存实现就**不再等价**了，必须换成
``APScheduler`` 的 ``SQLAlchemyJobStore`` 或直接上 ``pyquartz``，并且重新验证
``Key.toString()`` / ``SchedulerException`` 文案这些可观察行为。
"""

from __future__ import annotations

from typing import Dict, Tuple

#: Java 原文（**被注释掉**的）``prop.put(...)`` 逐条转写，键值一字不改。
#: ``None`` 值那两项在 Java 里也是注释掉的（sqlserver 专用），保留为说明。
CLUSTERED_SCHEDULER_PROPERTIES: Dict[str, str] = {
    "org.quartz.scheduler.instanceName": "RuoyiScheduler",
    "org.quartz.scheduler.instanceId": "AUTO",
    # 线程池配置
    "org.quartz.threadPool.class": "org.quartz.simpl.SimpleThreadPool",
    "org.quartz.threadPool.threadCount": "20",
    "org.quartz.threadPool.threadPriority": "5",
    # JobStore 配置
    "org.quartz.jobStore.class": (
        "org.springframework.scheduling.quartz.LocalDataSourceJobStore"
    ),
    # 集群配置
    "org.quartz.jobStore.isClustered": "true",
    "org.quartz.jobStore.clusterCheckinInterval": "15000",
    "org.quartz.jobStore.maxMisfiresToHandleAtATime": "10",
    "org.quartz.jobStore.txIsolationLevelSerializable": "true",
    # sqlserver 启用（Java 里同样是注释状态）
    # "org.quartz.jobStore.selectWithLockSQL": "SELECT * FROM {0}LOCKS UPDLOCK WHERE LOCK_NAME = ?"
    "org.quartz.jobStore.misfireThreshold": "12000",
    "org.quartz.jobStore.tablePrefix": "QRTZ_",
}

#: Java: ``factory.setSchedulerName("RuoyiScheduler")`` 等四个 setter。
#: ``startupDelay`` 是**秒**（``SchedulerFactoryBean#setStartupDelay(int seconds)``）。
SCHEDULER_FACTORY_SETTINGS: Tuple[Tuple[str, object], ...] = (
    ("scheduler_name", "RuoyiScheduler"),
    ("startup_delay", 1),
    ("application_context_scheduler_context_key", "applicationContextKey"),
    ("overwrite_existing_jobs", True),
    ("auto_startup", True),
)

__all__ = [
    "CLUSTERED_SCHEDULER_PROPERTIES",
    "SCHEDULER_FACTORY_SETTINGS",
]
