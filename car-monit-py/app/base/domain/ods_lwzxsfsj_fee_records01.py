"""通行交易流水.

# Migrated from: com/ruoyi/base/domain/OdsLwzxsfsjFeeRecords01.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_types import OdsDateTime
from app.common.core.domain.domain_model import DomainModel


class OdsLwzxsfsjFeeRecords01(DomainModel):
    """Java: ``com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01``."""

    big_id: Optional[str] = None
    algorithmidentifier: Optional[str] = None
    antennaid: Optional[str] = None
    axlecount: Optional[int] = None
    balanceafter: Optional[float] = None
    balancebefore: Optional[float] = None
    cardfeesumafter: Optional[float] = None
    cardfeesumbefore: Optional[float] = None
    computerorder: Optional[str] = None
    consumetime: Optional[int] = None
    cpucardid: Optional[str] = None
    cpucardtype: Optional[str] = None
    cpuenddate: Optional[str] = None
    cpuissueid: Optional[str] = None
    cpunetid: Optional[str] = None
    cpustartdate: Optional[str] = None
    cpuvehicleplate: Optional[str] = None
    cpuvehicletype: Optional[str] = None
    cpuversion: Optional[str] = None
    dealstatus: Optional[str] = None
    discountfee: Optional[float] = None
    discountfeegroup: Optional[str] = None
    enlanetype: Optional[str] = None
    entime: OdsDateTime = None
    entolllaneid: Optional[str] = None
    entollstationhex: Optional[str] = None
    fee: Optional[float] = None
    feecalcresult: Optional[str] = None
    feecalcspecial: Optional[str] = None
    feecalcspecials: Optional[str] = None
    feegroup: Optional[str] = None
    feeinfo1: Optional[str] = None
    feeinfo2: Optional[str] = None
    feeinfo3: Optional[str] = None
    feemileage: Optional[float] = None
    feeprovbeginhex: Optional[str] = None
    feespare1: Optional[str] = None
    feespare2: Optional[str] = None
    feevehicletype: Optional[str] = None
    gantryhex: Optional[str] = None
    gantryhexopposite: Optional[str] = None
    gantryid: Optional[str] = None
    gantryordernum: Optional[int] = None
    gantrytype: Optional[str] = None
    holidaystate: Optional[str] = None
    hourbatchno: Optional[str] = None
    keyversion: Optional[str] = None
    lastgantryhex: Optional[str] = None
    lastgantrytime: OdsDateTime = None
    matchstatus: Optional[str] = None
    mediatype: Optional[str] = None
    nocardtimesafter: Optional[int] = None
    nocardtimesbefore: Optional[int] = None
    obuelectrical: Optional[int] = None
    obuenddate: Optional[str] = None
    obufeesumafter: Optional[float] = None
    obufeesumbefore: Optional[float] = None
    obuinfotyperead: Optional[str] = None
    obuinfotypewrite: Optional[str] = None
    obuissueid: Optional[str] = None
    obulastgantryhex: Optional[str] = None
    obulastgantrytime: OdsDateTime = None
    obumac: Optional[str] = None
    obumileageafter: Optional[float] = None
    obumileagebefore: Optional[float] = None
    obupassstate: Optional[str] = None
    obupayfeesumafter: Optional[float] = None
    obupayfeesumbefore: Optional[float] = None
    obuprovfeesumafter: Optional[float] = None
    obuprovfeesumbefore: Optional[float] = None
    obuprovpayfeesumafter: Optional[float] = None
    obuprovpayfeesumbefore: Optional[float] = None
    obuprovtradesuccnumafter: Optional[int] = None
    obuprovtradesuccnumbefore: Optional[int] = None
    obusign: Optional[str] = None
    obusn: Optional[str] = None
    obustartdate: Optional[str] = None
    obustate: Optional[str] = None
    obutotaltradesuccnumafter: Optional[int] = None
    obutotaltradesuccnumbefore: Optional[int] = None
    obutraderesult: Optional[str] = None
    obuvehicleplate: Optional[str] = None
    obuvehicletype: Optional[str] = None
    obuversion: Optional[str] = None
    params: Optional[str] = None
    passid: Optional[str] = None
    passstate: Optional[str] = None
    pathfitflag: Optional[str] = None
    payfee: Optional[float] = None
    payfeegroup: Optional[str] = None
    pcrsuversion: Optional[str] = None
    provminfee: Optional[float] = None
    provincenumafter: Optional[int] = None
    provincenumbefore: Optional[int] = None
    ratecompute: Optional[str] = None
    ratefitcount: Optional[int] = None
    rateversion: Optional[str] = None
    readciphertextverify: Optional[str] = None
    receivetime: OdsDateTime = None
    servicetype: Optional[str] = None
    stationdbtime: OdsDateTime = None
    stationdealtime: OdsDateTime = None
    stationmatchtime: OdsDateTime = None
    stationvalidtime: OdsDateTime = None
    tac: Optional[str] = None
    terminalno: Optional[str] = None
    terminaltransno: Optional[str] = None
    tollintervalid: Optional[str] = None
    tollintervalsign: Optional[str] = None
    totalweight: Optional[float] = None
    tradeid: Optional[str] = None
    tradereadciphertext: Optional[str] = None
    traderesult: Optional[str] = None
    tradetype: Optional[str] = None
    tradewriteciphertext: Optional[str] = None
    transfee: Optional[float] = None
    transno: Optional[str] = None
    transtime: OdsDateTime = None
    transtype: Optional[str] = None
    validstatus: Optional[str] = None
    vehicleclass: Optional[str] = None
    vehiclehight: Optional[float] = None
    vehiclelength: Optional[float] = None
    vehicleplate: Optional[str] = None
    vehicleseat: Optional[str] = None
    vehiclesign: Optional[str] = None
    vehicletype: Optional[str] = None
    vehicleusertype: Optional[str] = None
    vehiclewidth: Optional[float] = None
    verifycode: Optional[str] = None
    load_time: OdsDateTime = None
    grade_level: Optional[int] = None
    cid: Optional[str] = None
    cid_list: Optional[List[str]] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    in_apply_time1: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    in_apply_time2: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    out_apply_time1: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    out_apply_time2: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    page_num: Optional[int] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    page_size: Optional[int] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    plate_color: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    gantry_name: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    receivetime_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    section_code_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    type: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    code: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    section_name: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    roadname: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    transtime_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    lastgantrytime_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    charge_status: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    entime_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL


__all__ = ["OdsLwzxsfsjFeeRecords01"]
