"""流程名称 flow_name.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowName.java

``extends BaseUuidEntity``，其中：

* ``tenantName`` 是列表语句的联表别名
  ``,IFNULL(sd.dept_name,'系统默认') tenantName``（``left join sys_dept sd``），
  不在 ``resultMap`` 里；``<if test="tenantName != null">`` 也是拿这个别名做过滤的。
* ``flowBusinessType`` 对应 ``flow_name.flow_business_type`` 列
  （见 :class:`app.common.enums.flow_business_type_enum.FlowBusinessTypeEnum`）。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity


class FlowName(BaseUuidEntity):
    """Java: ``com.ruoyi.flow.domain.FlowName``."""

    #: 流程KEY
    flow_key: Optional[str] = None
    #: 流程名称
    flow_title: Optional[str] = None
    #: 内容
    flow_context: Optional[str] = None
    #: 业务名称
    buss_name: Optional[str] = None
    #: 单位名称（联表别名，见模块文档）
    tenant_name: Optional[str] = None
    #: 流程业务类型
    flow_business_type: Optional[str] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("flow_key", Excel(name="流程KEY")),
        ("flow_title", Excel(name="流程名称")),
        ("flow_context", Excel(name="内容")),
        ("buss_name", Excel(name="业务名称")),
        ("tenant_name", Excel(name="单位名称")),
    )


__all__ = ["FlowName"]
