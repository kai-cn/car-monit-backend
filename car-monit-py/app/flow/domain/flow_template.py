"""流程节点 flow_template.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowTemplate.java

``extends BaseUuidEntity``。

``configCondtion`` 的拼写
------------------------
Java 字段名就是 ``configCondtion``（少了一个 ``i``），列名 ``CONFIG_CONDTION`` 同样如此。
Python 侧沿用 ``config_condtion`` —— 这是**照抄的拼写错误**，不是笔误，
改名会导致 ORM/XML 与数据库列对不上。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity


class FlowTemplate(BaseUuidEntity):
    """Java: ``com.ruoyi.flow.domain.FlowTemplate``."""

    #: 流程OID
    flow_oid: Optional[str] = None
    #: 当前流程类型(字典：1正常流程2会签流程)
    flow_type: Optional[str] = None
    #: 节点顺序（Java ``Integer``）
    node_order: Optional[int] = None
    #: 节点KEY
    node_key: Optional[str] = None
    #: 节点名称
    node_name: Optional[str] = None
    #: 下一节点OID（-1 表示当前为最后一个节点）
    next_node_oid: Optional[str] = None
    #: 上一节点OID（0 表示开始节点）
    previous_node_oid: Optional[str] = None
    #: 驳回到第几步，0 是发起人
    return_num: Optional[int] = None
    #: 驳回节点OID
    return_node_oid: Optional[str] = None
    #: 节点配置条件（拼写照抄 Java）
    config_condtion: Optional[str] = None
    #: 当前流程类型(字典：1人员2角色3其他)
    config_type: Optional[str] = None
    #: 节点配置id
    config_id: Optional[str] = None
    #: 节点配置名称
    config_name: Optional[str] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("flow_oid", Excel(name="流程OID")),
        ("flow_type", Excel(name="当前流程类型(字典：1正常流程2会签流程)")),
        ("node_order", Excel(name="节点顺序")),
        ("node_key", Excel(name="节点KEY")),
        ("node_name", Excel(name="节点名称")),
        ("next_node_oid", Excel(name="下一节点OID(-1为当前为最后一个节点)")),
        ("previous_node_oid", Excel(name="上一节点OID(0为开始节点)")),
        ("return_num", Excel(name="驳回到第几步 0 是发起人")),
        ("return_node_oid", Excel(name="驳回节点OID")),
        ("config_condtion", Excel(name="节点配置条件")),
        ("config_type", Excel(name="当前流程类型(字典：1人员2角色3其他)")),
        ("config_id", Excel(name="节点配置id")),
        ("config_name", Excel(name="节点配置名称")),
    )


__all__ = ["FlowTemplate"]
