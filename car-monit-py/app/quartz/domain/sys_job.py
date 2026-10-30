"""定时任务调度表 sys_job / scheduled job definition.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJob.java

字段与 JSON 形状（线上 ``GET /monitor/job/list`` 实测）
------------------------------------------------------
.. code-block:: json

    {"createBy":"admin","createTime":"2021-05-06 00:36:44","updateBy":null,
     "updateTime":null,"remark":"","jobId":1,"jobName":"系统默认（无参）",
     "jobGroup":"DEFAULT","invokeTarget":"ryTask.ryNoParams",
     "cronExpression":"0/10 * * * * ?","misfirePolicy":"3","concurrent":"1",
     "status":"1","nextValidTime":"2026-10-29 10:59:00"}

基类字段先输出、子类字段后输出，pydantic 与 Jackson 的顺序天然一致（见
``DomainModel`` 的说明）。``null`` 和 ``""`` 都**保留**（除非某字段声明了
``@JsonInclude``），所以 ``remark: ""`` 与 ``updateBy: null`` 必须原样出现。

``nextValidTime`` 是**只读计算属性**
------------------------------------
Java 里只有 ``getNextValidTime()``、没有对应字段，Jackson 靠 getter 把它当成一个属性。
Python 用 ``@computed_field`` 复刻同一件事：每次序列化都按当前时间重算，永远出现在 JSON
的**最后一个键**，并且不参与 ``model_fields``。

``cronExpression`` 为空串时 getter 返回 ``null``；非空时调
:meth:`CronUtils.get_next_execution`。表达式非法会抛出（Java 侧同样会让序列化失败）。

``misfirePolicy`` 有**默认值 ``"0"``**
--------------------------------------
Java 字段初始化 ``= ScheduleConstants.MISFIRE_DEFAULT``，所以客户端不传时 JSON 里也是
``"0"`` 而不是 ``null``。照抄。

``@NotBlank`` / ``@Size`` 是**惰性的**
--------------------------------------
注解挂在 getter 上，而控制器没有 ``@Validated``，所以一条都不生效 —— 线上实测
``POST /monitor/job`` 不带 ``jobName`` 照样插入成功。这里因此**不加**任何 pydantic
约束，否则会凭空多出一个 Java 没有的 400/500。长度上限由 ``varchar(64)`` 兜底。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import computed_field

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.constant.schedule_constants import MISFIRE_DEFAULT
from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.json_utils import format_date_time
from app.quartz.util.cron_utils import CronUtils


class SysJob(BaseEntity):
    """Java: ``SysJob extends BaseEntity implements Serializable``."""

    #: 任务ID
    job_id: Optional[int] = None
    #: 任务名称
    job_name: Optional[str] = None
    #: 任务组名
    job_group: Optional[str] = None
    #: 调用目标字符串
    invoke_target: Optional[str] = None
    #: cron执行表达式
    cron_expression: Optional[str] = None
    #: cron计划策略（0默认 1立即触发执行 2触发一次执行 3不触发立即执行）
    misfire_policy: Optional[str] = MISFIRE_DEFAULT
    #: 是否并发执行（0允许 1禁止）
    concurrent: Optional[str] = None
    #: 任务状态（0正常 1暂停）
    status: Optional[str] = None

    #: ``@Excel`` 注解表，**顺序与 Java 字段声明顺序逐字一致**（共 8 列）。
    #: 注意 ``"执行表达式 "`` / ``"计划策略 "`` 带**尾随空格**，Java 原文如此 ——
    #: 导出的表头就是这两个带空格的字符串，别去 trim。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("job_id", Excel(name="任务序号", cell_type=ColumnType.NUMERIC)),
        ("job_name", Excel(name="任务名称")),
        ("job_group", Excel(name="任务组名")),
        ("invoke_target", Excel(name="调用目标字符串")),
        ("cron_expression", Excel(name="执行表达式 ")),
        (
            "misfire_policy",
            Excel(
                name="计划策略 ",
                read_converter_exp="0=默认,1=立即触发执行,2=触发一次执行,3=不触发立即执行",
            ),
        ),
        ("concurrent", Excel(name="并发执行", read_converter_exp="0=允许,1=禁止")),
        ("status", Excel(name="任务状态", read_converter_exp="0=正常,1=暂停")),
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def next_valid_time(self) -> Optional[str]:
        """下一次执行时间. Java: ``getNextValidTime()`` + ``@JsonFormat("yyyy-MM-dd HH:mm:ss")``.

        只读计算属性：Java 只有 getter，没有字段，也不落库。空串/``None`` 时返回
        ``None``（JSON 里是 ``null``），与 ``StringUtils.isNotEmpty`` 的判断一致。
        """
        if not self.cron_expression:
            return None
        return format_date_time(CronUtils.get_next_execution(self.cron_expression))

    def java_to_string(self) -> str:
        """Java: ``toString()`` —— ``ToStringBuilder`` 多行风格，仅日志用.

        顺序与 Java 原文一致（注意它**没有** ``invokeTarget``，原文如此）。
        """
        lines = [
            ("jobId", self.job_id),
            ("jobName", self.job_name),
            ("jobGroup", self.job_group),
            ("cronExpression", self.cron_expression),
            ("nextValidTime", self.next_valid_time),
            ("misfirePolicy", self.misfire_policy),
            ("concurrent", self.concurrent),
            ("status", self.status),
            ("createBy", self.create_by),
            ("createTime", self.create_time),
            ("updateBy", self.update_by),
            ("updateTime", self.update_time),
            ("remark", self.remark),
        ]
        body = ",".join("%s=%s" % (name, _java_str(value)) for name, value in lines)
        return "%s[%s]" % (type(self).__name__, body)


def _java_str(value: Any) -> str:
    """Java ``ToStringBuilder`` 的 null 写法是 ``<null>``。"""
    if value is None:
        return "<null>"
    if isinstance(value, datetime):
        return format_date_time(value) or ""
    return str(value)


__all__ = ["SysJob"]
