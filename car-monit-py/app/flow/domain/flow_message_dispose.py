"""系统消息处理人 flow_message_dispose.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageDispose.java

``extends BaseUuidEntity``。

``hangTime`` 上的 ``@JsonFormat(pattern = "flow_message_dispose")`` 是**非法 pattern**
------------------------------------------------------------------------
实测（JDK 1.8）：

    new SimpleDateFormat("flow_message_dispose")
      -> java.lang.IllegalArgumentException: Illegal pattern character 'f'

Jackson 在 ``DateSerializer#createContextual`` 里正是这么建 ``SimpleDateFormat`` 的，
所以只要 ``HANG_TIME`` 非空，``/flow/messagedispose/list`` 在 Java 侧会直接抛异常
（HTTP 500）。现实中这条路径踩不到：唯一给 ``HANG_TIME`` 赋值的
``FlowMessageDisposeMapper.updateBusinessByMessageId`` 只被
``FlowMessageInfoServiceImpl#dealBusinessMessage`` 调用，而后者**没有任何调用点**；
插入路径也从不设置 ``hangTime``，因此该列恒为 ``NULL``，Jackson 输出 ``null`` 时不走
格式化，注解从未生效。

Python 侧的处理：按注解"想要"的 ``yyyy-MM-dd HH:mm:ss`` 输出，并在
``COMPATIBILITY.md`` 记录这处差异。**不**复刻 500 —— 那只会让一个本来能用的列表接口
因为一条脏数据整页失败。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import field_serializer, field_validator

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity
from app.common.utils.json_utils import format_date_time, parse_date_time


class FlowMessageDispose(BaseUuidEntity):
    """Java: ``com.ruoyi.flow.domain.FlowMessageDispose``."""

    #: 消息外键
    mid: Optional[str] = None
    #: 处理对象ID
    buss_id: Optional[str] = None
    #: 处理对象名称 / 业务消息-处理人id
    buss_name: Optional[str] = None
    #: 消息状态（1：已办理，2：未办理）
    msg_status: Optional[str] = None
    #: 处理时间（Java ``java.util.Date``）
    hang_time: Optional[datetime] = None
    #: 其他
    dispose_other: Optional[str] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("mid", Excel(name="消息外键")),
        ("buss_id", Excel(name="处理对象ID")),
        ("buss_name", Excel(name="处理对象名称")),
        ("msg_status", Excel(name="消息状态", read_converter_exp="1=：已办理，2：未办理")),
        ("hang_time", Excel(name="处理时间", width=30, date_format="yyyy-MM-dd HH:mm:ss")),
        ("dispose_other", Excel(name="其他")),
    )

    # Java: @JsonFormat(pattern = "flow_message_dispose") -- 非法 pattern，见模块文档
    @field_serializer("hang_time")
    def _serialize_hang_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        return format_date_time(value)

    @field_validator("hang_time", mode="before")
    @classmethod
    def _parse_hang_time(cls, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        return parse_date_time(value)


__all__ = ["FlowMessageDispose"]
