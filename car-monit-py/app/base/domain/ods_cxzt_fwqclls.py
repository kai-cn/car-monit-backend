"""服务区车辆流水 ``ods_cxzt_fwqclls``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsCxztFwqclls.java

两个注意点
----------
1. ``crosstime`` 是 ``Date`` 且**没有** ``@JsonFormat`` -> JSON 里是 **epoch 毫秒数字**，
   不是时间字符串（见 :mod:`app.base.domain.ods_types`）。
2. ``loadTime`` / ``gradeLevel`` 是 **String**（不是 Date / 数字），XML 里也按字符串判
   ``!= null and != ''``，别按字段名猜。
3. ``bigId`` 没有 ``@TableId`` 注解，但 XML 的详情语句按 ``t.big_id`` 查。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsEpochDate
from app.common.core.domain.domain_model import DomainModel


class OdsCxztFwqclls(DomainModel):
    """Java: ``public class OdsCxztFwqclls implements Custom``."""

    #: 主键（详情语句的过滤列是 ``big_id``）。
    big_id: Optional[int] = None

    #: 数据唯一标识。
    datauuid: Optional[str] = None

    #: 抓拍照片url。
    targetpicurl: Optional[str] = None

    #: 车辆品牌。
    vehiclebrand: Optional[str] = None

    #: 车牌照片。
    platepicurl: Optional[str] = None

    #: 车类型。
    rollvehiclestype: Optional[str] = None

    #: 车牌。
    plateno: Optional[str] = None

    #: 方向名称（列表条件是 **like**）。
    directionname: Optional[str] = None

    #: 车牌类型。
    platetype: Optional[str] = None

    #: 是否危化品车。
    dangmark: Optional[str] = None

    #: 通过时间。Java: ``private Date crosstime;``（无 ``@JsonFormat``）
    crosstime: OdsEpochDate = None

    #: 坐标。
    axles: Optional[str] = None

    #: 设备名称（列表条件是 **like**）。
    devicename: Optional[str] = None

    #: IP地址。
    ipaddress: Optional[str] = None

    #: 服务区名称（列表条件是 **like**）。
    servicename: Optional[str] = None

    #: 车辆类型。
    vehicletype: Optional[str] = None

    #: 加载时间（**String**，不是 Date）。
    load_time: Optional[str] = None

    #: 分类分级（**String**，不是数字）。
    grade_level: Optional[str] = None


__all__ = ["OdsCxztFwqclls"]
