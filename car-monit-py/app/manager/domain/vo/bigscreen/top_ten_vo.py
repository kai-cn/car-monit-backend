"""路段车辆数排行 VO（大屏 Top10）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/TopTenVO.java

Java 侧是 ``@Data`` 的普通 POJO，字段顺序即 JSON 顺序：
``roadCode`` / ``sectionName`` / ``carNum`` / ``rank`` / ``rate``。

``rank`` 在 Python 里虽是内置函数名，但作为**字段名**不会与之冲突；
``carNum`` / ``rate`` 由业务代码二次加工（见
:meth:`app.base.service.ods_rt_szdn_snapshot_flow_addcode_service.OdsRtSzdnSnapshotFlowAddcodeService.get_top_ten`）。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class TopTenVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.TopTenVO``."""

    #: 路线编号
    road_code: Optional[str] = None
    #: 路段名称
    section_name: Optional[str] = None
    #: 车辆数量
    car_num: Optional[int] = None
    #: 排名（1 起）
    rank: Optional[int] = None
    #: 百分比（字符串，最高位固定 "100"）
    rate: Optional[str] = None


__all__ = ["TopTenVO"]
