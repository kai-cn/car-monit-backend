"""收费站 / 门架 / 服务区三合一 VO（大屏用，``TollGantryFwqVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/TollGantryFwqVO.java

``/manager/bigScreen/tollGantryFwqList`` 用 ``type`` 区分三类设施，字段名保持
Java 的 ``type`` / ``code`` / ``name``（不是 ``tollCode`` 之类的具体名）。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class TollGantryFwqVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.TollGantryFwqVO``."""

    #: 1 收费站、2 门架、3 服务区
    type: Optional[str] = None
    #: 编码
    code: Optional[str] = None
    #: 名称
    name: Optional[str] = None


__all__ = ["TollGantryFwqVO"]
