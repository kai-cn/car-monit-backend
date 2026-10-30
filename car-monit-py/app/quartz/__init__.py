"""定时任务模块（``com.ruoyi.quartz``）的 Python 镜像.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/package-info.java

目录 -> Java 包
---------------
    ==================  ===========================================================
    Python                Java
    ==================  ===========================================================
    ``domain``           ``com.ruoyi.quartz.domain``          （SysJob / SysJobLog）
    ``mapper``           ``com.ruoyi.quartz.mapper``          ＋ ``mapper/quartz/*.xml``
    ``service``          ``com.ruoyi.quartz.service[.impl]``
    ``util``             ``com.ruoyi.quartz.util``            （调度/反射/cron）
    ``task``             ``com.ruoyi.quartz.task``            （业务任务 bean）
    ``controller``       ``com.ruoyi.web.controller.monitor`` （SysJob / SysJobLog）
    ==================  ===========================================================

``config.ScheduleConfig`` 是**整文件注释掉**的（集群 ``LocalDataSourceJobStore`` 配置），
本工程在 :mod:`app.quartz.config.schedule_config` 里逐行转写为文档，不产生任何运行期行为。
真正的调度器实例由 :mod:`app.quartz.util.scheduler` 提供。
"""

from __future__ import annotations

__all__: list[str] = []
