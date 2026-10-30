"""同步可疑车辆入参 VO（``SuspiciousCarVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/SuspiciousCarVO.java

只有 ``POST /manager/suspicious/syncSuspiciousCarTask`` 用它。

``trailInfoList`` 在 Java 里初始化为 ``new ArrayList<>()``，所以 **永远不是 null** ——
控制器里 ``if (null != trailInfoList && trailInfoList.size() > 0)`` 的 null 分支
实际是死代码。这里保持非 ``None`` 的默认值。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.trail_info import TrailInfo
from app.common.core.domain.domain_model import DomainModel


class SuspiciousCarVO(DomainModel):
    """Java: ``com.ruoyi.base.domain.SuspiciousCarVO``."""

    #: 签名 key
    signature_key: Optional[str] = None
    #: 时间戳
    time_stamp: Optional[int] = None
    #: 签名 = ``shaEncode(signatureKey + timeStamp)``
    signature: Optional[str] = None
    #: 轨迹列表（Java 初始化为空列表）
    trail_info_list: List[TrailInfo] = []


__all__ = ["SuspiciousCarVO"]
