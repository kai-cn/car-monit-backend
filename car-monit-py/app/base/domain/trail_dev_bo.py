"""轨迹设备 VO（``TrailDevBO``）—— "设备 + 该设备下的轨迹点".

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailDevBO.java

``status`` 是字符串（``"0"`` 正常 / ``"1"`` 异常），不是数字 —— 与
:class:`~app.base.domain.trail_dev_count_bo.TrailDevCountBO` 的 ``exceptNum`` 不同。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.trail_bo import TrailBo
from app.common.core.domain.domain_model import DomainModel


class TrailDevBO(DomainModel):
    """Java: ``com.ruoyi.base.domain.TrailDevBO``."""

    #: 状态：0 正常 1 异常
    status: Optional[str] = None
    #: 设备信息
    dev_name: Optional[str] = None
    #: 轨迹详情
    trail_list: Optional[List[TrailBo]] = None


__all__ = ["TrailDevBO"]
