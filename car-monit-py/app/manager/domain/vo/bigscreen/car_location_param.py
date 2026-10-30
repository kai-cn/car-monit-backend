"""车辆地图描点入参 VO（``CarLocationParam``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarLocationParam.java

10 个字符串字段全部可空；``type`` / ``code`` 在这一版业务里**没有被使用**
（``CarInfoService.carLocation`` 只读 ``roadCode`` / ``sectionCode`` / ``tollCode`` /
``gantryCode`` / ``fwqbm`` / ``escapedType`` / ``carNoQuery``），照抄保留。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class CarLocationParam(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam``."""

    #: 所属管理中心机构编码
    org_code: Optional[str] = None
    #: 所属路线编码
    road_code: Optional[str] = None
    #: 所属路段编码
    section_code: Optional[str] = None
    #: 门架编号
    gantry_code: Optional[str] = None
    #: 所属收费站编码
    toll_code: Optional[str] = None
    #: 逃费类型（字典）
    escaped_type: Optional[str] = None
    #: 服务区编码
    fwqbm: Optional[str] = None
    #: 1 收费站、2 门架、3 服务区
    type: Optional[str] = None
    #: 编码
    code: Optional[str] = None
    #: 车牌号
    car_no_query: Optional[str] = None


__all__ = ["CarLocationParam"]
