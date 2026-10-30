"""收费站入口数据 ``ods_lwzxsfsj_fee_station_enter_01``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationEnter01.java

⚠ 投影里多出一个 ``t.id``
--------------------------
``<sql id="selectOdsLwzxsfsjFeeStationEnter01Vo">`` 里在 ``t.enweight`` 和
``t.identifyvehicleid`` 之间夹了一行 ``t.id``，但：

* 实体**没有** ``id`` 字段；
* ``resultMap`` 也**没有** ``<result property="id" .../>``。

MyBatis 会把这列读出来再丢掉，所以它对 JSON 完全不可见。这里把 ``id`` 从
``result_columns`` 里排除即可，**不要**给它建字段。

类型速查
--------
* ``BigDecimal``： ``enweight`` / ``transfee`` —— 本实现用 ``float``（见
  :mod:`app.base.domain.ods_types` 的说明）。
* ``Date``（``@JsonFormat("yyyy-MM-dd")``）： ``entime`` / ``receivetime`` / ``loadTime``。
* ``Long``： ``bigId`` / ``electricalpercentage`` / ``enaxlecount`` / ``vcount``。
* ``gradeLevel`` 是 **String**（对比 ``Stationcapture`` 的 ``gradelevel`` 是 Integer）。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate
from app.common.core.domain.domain_model import DomainModel


class OdsLwzxsfsjFeeStationEnter01(DomainModel):
    """Java: ``public class OdsLwzxsfsjFeeStationEnter01 implements Custom``."""

    #: 主键. Java: ``@TableId(value = "bigId", type = IdType.ASSIGN_UUID) private Long bigId;``
    big_id: Optional[int] = None

    #: CPC卡或ETC卡的编号.
    cardid: Optional[str] = None

    #: 单片式OBU/CPC卡电量百分比.
    electricalpercentage: Optional[int] = None

    #: 入站车轴数.
    enaxlecount: Optional[int] = None

    #: 入站时间 ``@JsonFormat("yyyy-MM-dd")``.
    entime: OdsDate = None

    #: 入口车道hex.
    entolllanehex: Optional[str] = None

    #: 入口车道id.
    entolllaneid: Optional[str] = None

    #: 入口收费站编码.
    entollstationid: Optional[str] = None

    #: 入口称重（BigDecimal）.
    enweight: Optional[float] = None

    #: 车牌号+车牌类型.
    identifyvehicleid: Optional[str] = None

    #: 车道类型.
    lanetype: Optional[str] = None

    #: 介质类型.
    mediatype: Optional[str] = None

    #: 操作id.
    operid: Optional[str] = None

    #: 作业媒介.
    operationmedia: Optional[str] = None

    #: 参数.
    params: Optional[str] = None

    #: 通行id.
    passid: Optional[str] = None

    #: 接收时间 ``@JsonFormat("yyyy-MM-dd")``.
    receivetime: OdsDate = None

    #: 工班号.
    shift: Optional[str] = None

    #: 标记状态.
    signstatus: Optional[str] = None

    #: 特殊类型.
    specialtype: Optional[str] = None

    #: TAC码.
    tac: Optional[str] = None

    #: 终端机编号.
    terminalno: Optional[str] = None

    #: PSAM卡脱机交易序列号.
    terminaltransno: Optional[str] = None

    #: 交易金额（BigDecimal）.
    transfee: Optional[float] = None

    #: 交易类型.
    transtype: Optional[str] = None

    #: 总数.
    vcount: Optional[int] = None

    #: 车种.
    vehicleclass: Optional[str] = None

    #: 车牌号+车牌类型.
    vehicleid: Optional[str] = None

    #: 车辆识别标识.
    vehiclesign: Optional[str] = None

    #: 车牌识别流水号.
    vehiclesignid: Optional[str] = None

    #: 车辆类型.
    vehicletype: Optional[str] = None

    #: 加载时间 ``@JsonFormat("yyyy-MM-dd")``.
    load_time: OdsDate = None

    #: 分类分级（**String**）.
    grade_level: Optional[str] = None

    #: cid.
    cid: Optional[str] = None


__all__ = ["OdsLwzxsfsjFeeStationEnter01"]
