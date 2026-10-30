"""审核历史记录 flow_list.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowList.java

``extends BaseUuidEntity``。注意有两个列表语句（``selectFlowListList`` 升序 /
``selectFlowListListNew`` 降序），排序差异在 Mapper 里处理，实体本身无差别。

``shKey`` 是「审核结论KEY」（T/F/R/S/entrust），``shValue`` 是给人看的中文结论
（同意/拒绝/退回/提交/委托）—— 两者都由 ``FlowCurrentNodeServiceImpl#saveFlowList``
按 ``FlowTypeEnum`` 及 ``Constants.FLOW_RESULT_ENTRUST_KEY`` 赋值。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity


class FlowList(BaseUuidEntity):
    """Java: ``com.ruoyi.flow.domain.FlowList``."""

    #: 单据OID
    bill_oid: Optional[str] = None
    #: 流程类型
    buss_type: Optional[str] = None
    #: 任务ID
    task_id: Optional[str] = None
    #: 流程实例ID
    flow_ruid: Optional[str] = None
    #: 当前节点OID(流程节点OID)
    current_oid: Optional[str] = None
    #: 审核人
    sh_user: Optional[str] = None
    #: 审核结论KEY（T同意F拒绝R退回S提交）
    sh_key: Optional[str] = None
    #: 审核结论（T同意F拒绝R退回S提交）
    sh_value: Optional[str] = None
    #: 内容
    sh_context: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 备用字段3
    back_col3: Optional[str] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("bill_oid", Excel(name="单据OID")),
        ("buss_type", Excel(name="流程类型")),
        ("task_id", Excel(name="任务ID")),
        ("flow_ruid", Excel(name="流程实例ID")),
        ("current_oid", Excel(name="当前节点OID(流程节点OID)")),
        ("sh_user", Excel(name="审核人")),
        ("sh_key", Excel(name="审核结论KEY", read_converter_exp="T=同意F拒绝R退回S提交")),
        ("sh_value", Excel(name="审核结论", read_converter_exp="T=同意F拒绝R退回S提交")),
        ("sh_context", Excel(name="内容")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("back_col3", Excel(name="备用字段3")),
    )


__all__ = ["FlowList"]
