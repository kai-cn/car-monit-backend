"""管理中心 VO（大屏用，``OrgVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/OrgVO.java

``/manager/bigScreen/orgList`` 的返回元素。Java 侧是 MyBatis-Plus 的
``lambdaQuery().select(orgCode, orgName).list()`` —— 只查两列，**不带**
``org_is_deleted`` 之类的过滤条件（``OdsYhglVBaseOrg`` 上没有 ``@TableLogic``）。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class OrgVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.OrgVO``."""

    #: 管理中心编码
    org_code: Optional[str] = None
    #: 管理中心名称
    org_name: Optional[str] = None


__all__ = ["OrgVO"]
