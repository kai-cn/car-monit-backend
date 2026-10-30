"""系统内部消息 flow_message_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageInfo.java

``extends BaseUuidEntity``。三个字段是**联表/子查询带出来的别名**，不在
``resultMap`` 里，靠 MyBatis 的 ``PARTIAL`` 自动映射落到属性上（详见
:mod:`app.flow.domain.flow_apply_info` 的说明）：

    app.FLOW_STATUS  flowStatus
    app.BACK_COL1    curEmpNames
    (子查询)          msgStatus    -- 仅当 flag == 'myxx'

``disposeList`` 是 ``List<FlowMessageDispose>``，服务层在
``saveFlowMessageInfo`` 里用它承载"这批处理人"，但 XML 从不嵌套查询它，
所以列表接口返回的 ``disposeList`` 始终是 ``null``。
"""

from __future__ import annotations

from typing import ClassVar, List, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity
from app.flow.domain.flow_message_dispose import FlowMessageDispose


class FlowMessageInfo(BaseUuidEntity):
    """Java: ``com.ruoyi.flow.domain.FlowMessageInfo``."""

    #: 消息编号（格式：时间戳+userId）
    message_no: Optional[str] = None
    #: 单据OID
    bill_oid: Optional[str] = None
    #: 业务类型-字典
    buss_type: Optional[str] = None
    #: 流程实例ID
    flow_ruid: Optional[str] = None
    #: 标题
    msg_title: Optional[str] = None
    #: 内容
    msg_context: Optional[str] = None
    #: 消息类型(1:通知业务，2:办理业务)
    msg_type: Optional[str] = None
    #: 处理的URL
    msg_url: Optional[str] = None
    #: 批次OID
    pc_oid: Optional[str] = None
    #: 申请人
    apply_name: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 备用字段3
    back_col3: Optional[str] = None
    #: 处理对象ID（Java ``Long``；Controller 里用 ``SecurityUtils.getUserId()`` 赋值）
    user_id: Optional[int] = None
    #: 消息状态（别名，见模块文档）
    msg_status: Optional[str] = None
    #: 当前状态（别名 ``app.FLOW_STATUS``）
    flow_status: Optional[str] = None
    #: 当前处理人（别名 ``app.BACK_COL1``）
    cur_emp_names: Optional[str] = None
    #: 消息
    dispose_list: Optional[List[FlowMessageDispose]] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("bill_oid", Excel(name="单据OID")),
        ("buss_type", Excel(name="业务类型-字典")),
        ("flow_ruid", Excel(name="流程实例ID")),
        ("msg_title", Excel(name="标题")),
        ("msg_context", Excel(name="内容")),
        ("msg_type", Excel(name="消息类型(1:通知业务，2:办理业务)")),
        ("msg_url", Excel(name="处理的URL")),
        ("pc_oid", Excel(name="批次OID")),
        ("apply_name", Excel(name="申请人")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("back_col3", Excel(name="备用字段3")),
    )


__all__ = ["FlowMessageInfo"]
