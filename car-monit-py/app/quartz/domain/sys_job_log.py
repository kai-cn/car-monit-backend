"""定时任务调度日志表 sys_job_log / scheduled job execution log.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJobLog.java

字段与 JSON 形状（线上 ``GET /monitor/jobLog/list`` 实测）
----------------------------------------------------------
.. code-block:: json

    {"createBy":null,"createTime":"2026-05-20 15:15:03","updateBy":null,
     "updateTime":null,"remark":null,"jobLogId":1507,"jobName":"可疑车俩数据同步",
     "jobGroup":"SYSTEM","invokeTarget":"trackTask.syncSuspiciousCar",
     "jobMessage":"可疑车俩数据同步 总共耗时：8毫秒","status":"0",
     "exceptionInfo":"","startTime":null,"stopTime":null}

``startTime`` / ``stopTime`` 永远是 ``null``
-------------------------------------------
``SysJobLogMapper.xml`` 的 ``resultMap`` 里**没有**这两列，``selectJobLogVo`` 也没查它们。
所以列表/详情接口吐出来的始终是 ``null`` —— 除非走"写日志"那条路（
:class:`~app.quartz.util.abstract_quartz_job.AbstractQuartzJob` 的 ``after``），
而那一路只写库、不进 JSON。照抄：字段保留、查询不填。

``insertJobLog`` 也不写这两列（XML 的插入列表里没有），所以即便填了也会被丢掉。

``status`` 是 ``String``（不是 ``Integer``）
-------------------------------------------
与 ``SysOperLog.status``（``Integer``）不同，这里和 ``SysJob.status`` 一致都是
``char(1)`` 映射成的字符串，``readConverterExp`` 也是按字符串比对。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import field_serializer

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_entity import BaseEntity


class SysJobLog(BaseEntity):
    """Java: ``SysJobLog extends BaseEntity``."""

    #: ID
    job_log_id: Optional[int] = None
    #: 任务名称
    job_name: Optional[str] = None
    #: 任务组名
    job_group: Optional[str] = None
    #: 调用目标字符串
    invoke_target: Optional[str] = None
    #: 日志信息
    job_message: Optional[str] = None
    #: 执行状态（0正常 1失败）
    status: Optional[str] = None
    #: 异常信息
    exception_info: Optional[str] = None
    #: 开始时间
    start_time: Optional[datetime] = None
    #: 停止时间
    stop_time: Optional[datetime] = None

    #: ``@Excel`` 注解表，**顺序与 Java 字段声明顺序逐字一致**（共 7 列）。
    #: ``startTime`` / ``stopTime`` 没有 ``@Excel``，所以不是导出的列。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("job_log_id", Excel(name="日志序号")),
        ("job_name", Excel(name="任务名称")),
        ("job_group", Excel(name="任务组名")),
        ("invoke_target", Excel(name="调用目标字符串")),
        ("job_message", Excel(name="日志信息")),
        ("status", Excel(name="执行状态", read_converter_exp="0=正常,1=失败")),
        ("exception_info", Excel(name="异常信息")),
    )

    @field_serializer("start_time", "stop_time")
    def _serialize_plain_date(self, value: Optional[datetime], _info: Any) -> Optional[int]:
        """Java 的裸 ``Date``（**没有** ``@JsonFormat``）被 Jackson 写成 **epoch 毫秒数字**.

        ``job_log_id`` 之类都有 ``@JsonFormat`` 或本来就是数字；这两个字段没有注解，
        所以默认序列化器是 ``DateSerializer``，输出的是 ``1750000000000`` 而不是字符串。
        实际查询永远是 ``null``（见模块 docstring），这里只是把形状钉死，避免以后接了
        真实值却输出成 ISO 串。
        """
        if value is None:
            return None
        return int(value.timestamp() * 1000)


__all__ = ["SysJobLog"]
