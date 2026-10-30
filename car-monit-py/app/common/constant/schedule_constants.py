"""任务调度通用常量.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/constant/ScheduleConstants.java

Java 用 ``public static final String`` 常量 + 一个 ``enum Status``；Python 侧常量
直接放模块级、枚举用 :class:`enum.Enum`，取值与 Java 逐字一致（都是**字符串**）。

``TASK_CLASS_NAME`` 是整个调度器的主键前缀
------------------------------------------
``ScheduleUtils.getJobKey(jobId, jobGroup)`` 用
``JobKey.jobKey(TASK_CLASS_NAME + jobId, jobGroup)`` 构造 Quartz 的
``(name, group)`` 二元组。``TASK_CLASS_NAME`` 的值就是字面量
``"TASK_CLASS_NAME"``（看着像"键名"其实是**名称前缀**），所以真实的 job name 是
``"TASK_CLASS_NAME1"`` 这种样子。别"优化"成 ``"TASK_CLASS_NAME_1"`` ——
那会和数据库里已经跑过的调度记录对不上。

``MISFIRE_*`` 与 ``Status`` 的取值同样是**字符串**（``"0"`` / ``"1"`` / ``"2"`` / ``"3"``），
它们既进 ``sys_job`` 的 ``char(1)`` 列，也直接出现在 ``/monitor/job/list`` 的 JSON 里。
"""

from __future__ import annotations

from enum import Enum

#: Java: ``public static final String TASK_CLASS_NAME = "TASK_CLASS_NAME"``
TASK_CLASS_NAME = "TASK_CLASS_NAME"

#: Java: ``public static final String TASK_PROPERTIES = "TASK_PROPERTIES"`` —— JobDataMap 的键
TASK_PROPERTIES = "TASK_PROPERTIES"

#: Java: ``MISFIRE_DEFAULT = "0"`` —— 默认
MISFIRE_DEFAULT = "0"

#: Java: ``MISFIRE_IGNORE_MISFIRES = "1"`` —— 立即触发执行
MISFIRE_IGNORE_MISFIRES = "1"

#: Java: ``MISFIRE_FIRE_AND_PROCEED = "2"`` —— 触发一次执行
MISFIRE_FIRE_AND_PROCEED = "2"

#: Java: ``MISFIRE_DO_NOTHING = "3"`` —— 不触发立即执行
MISFIRE_DO_NOTHING = "3"


class Status(Enum):
    """Java: ``enum Status { NORMAL("0"), PAUSE("1") }``."""

    #: 正常
    NORMAL = "0"
    #: 暂停
    PAUSE = "1"


__all__ = [
    "TASK_CLASS_NAME",
    "TASK_PROPERTIES",
    "MISFIRE_DEFAULT",
    "MISFIRE_IGNORE_MISFIRES",
    "MISFIRE_FIRE_AND_PROCEED",
    "MISFIRE_DO_NOTHING",
    "Status",
]
