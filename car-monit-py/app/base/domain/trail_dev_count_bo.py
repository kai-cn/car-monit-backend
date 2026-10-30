"""轨迹设备统计 VO（``TrailDevCountBO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailDevCountBO.java

Java 字段名 ``TrailDevList`` 是**大写开头**的（``getTrailDevList()``），所以 JSON
键就是 ``trailDevList``；Python 侧字段名写 ``trail_dev_list``，别名生成器会得到
``trailDevList`` —— 一致。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.trail_bo import TrailBo
from app.base.domain.trail_dev_bo import TrailDevBO
from app.common.core.domain.domain_model import DomainModel


class TrailDevCountBO(DomainModel):
    """Java: ``com.ruoyi.base.domain.TrailDevCountBO``."""

    #: 异常数量
    except_num: Optional[int] = None
    #: 设备集合
    trail_dev_list: Optional[List[TrailDevBO]] = None
    #: 轨迹详情
    trail_list: Optional[List[TrailBo]] = None
    #: 路线提醒
    except_msg: Optional[str] = None


__all__ = ["TrailDevCountBO"]
