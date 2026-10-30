"""收费站出口流水.

# Migrated from: com/ruoyi/base/domain/OdsLwzxsfsjFeeStationExit01.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate
from app.common.core.domain.domain_model import DomainModel


class OdsLwzxsfsjFeeStationExit01(DomainModel):
    """Java: ``com.ruoyi.base.domain.OdsLwzxsfsjFeeStationExit01``."""

    big_id: Optional[str] = None
    actualfeeclass: Optional[str] = None
    axlecount: Optional[int] = None
    discountfee: Optional[int] = None
    electricalpercentage: Optional[int] = None
    enaxlecount: Optional[int] = None
    entime: OdsDate = None
    entolllanehex: Optional[str] = None
    entolllaneid: Optional[str] = None
    entollstationid: Optional[str] = None
    entollstationname: Optional[str] = None
    envehicleclass: Optional[int] = None
    envehicleid: Optional[str] = None
    envehicletype: Optional[int] = None
    enweight: Optional[int] = None
    entryoperatorid: Optional[str] = None
    extime: OdsDate = None
    extolllaneid: Optional[str] = None
    extollstationid: Optional[str] = None
    extollstationname: Optional[str] = None
    exvehicleclass: Optional[int] = None
    exvehicleid: Optional[str] = None
    exvehicletype: Optional[int] = None
    fee: Optional[int] = None
    exweight: Optional[int] = None
    feeboardplay: Optional[str] = None
    feemileage: Optional[int] = None
    identification: Optional[str] = None
    feerate: Optional[float] = None
    identifyvehicleid: Optional[str] = None
    lanetype: Optional[str] = None
    mediano: Optional[str] = None
    mediatype: Optional[str] = None
    nocardcount: Optional[int] = None
    obuid: Optional[str] = None
    obusign: Optional[str] = None
    obutotalamount: Optional[int] = None
    obutotaldiscountamount: Optional[int] = None
    params: Optional[str] = None
    operid: Optional[str] = None
    passid: Optional[str] = None
    paycardid: Optional[str] = None
    payfee: Optional[int] = None
    paytype: Optional[str] = None
    provfee: Optional[int] = None
    provtranscount: Optional[int] = None
    provincecount: Optional[int] = None
    shift: Optional[str] = None
    receivetime: OdsDate = None
    shortfee: Optional[int] = None
    shortfeemileage: Optional[int] = None
    signstatus: Optional[str] = None
    spcrateversion: Optional[str] = None
    tac: Optional[str] = None
    specialtype: Optional[str] = None
    splitprovince: Optional[str] = None
    terminalno: Optional[str] = None
    terminaltransno: Optional[str] = None
    transfee: Optional[int] = None
    transpaytype: Optional[str] = None
    transtype: Optional[str] = None
    load_time: OdsDate = None
    vehiclesignid: Optional[str] = None
    vehiclesign: Optional[str] = None
    grade_level: Optional[str] = None
    cid: Optional[str] = None
    page_num: Optional[int] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    page_size: Optional[int] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL


__all__ = ["OdsLwzxsfsjFeeStationExit01"]
