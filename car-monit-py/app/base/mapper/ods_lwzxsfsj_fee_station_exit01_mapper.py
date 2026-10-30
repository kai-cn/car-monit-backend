"""收费站出口流水.

# Migrated from: com/ruoyi/base/mapper/OdsLwzxsfsjFeeStationExit01Mapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationExit01Mapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.ods_lwzxsfsj_fee_station_exit01 import OdsLwzxsfsjFeeStationExit01
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ODS_LWZXSFSJ_FEE_STATION_EXIT01_VO = """
        t.big_id,
        t.actualfeeclass,
        t.axlecount,
        t.discountfee,
        t.electricalpercentage,
        t.enaxlecount,
        t.entime,
        t.entolllanehex,
        t.entolllaneid,
        t.entollstationid,
        t.entollstationname,
        t.envehicleclass,
        t.envehicleid,
        t.envehicletype,
        t.enweight,
        t.entryoperatorid,
        t.extime,
        t.extolllaneid,
        t.extollstationid,
        t.extollstationname,
        t.exvehicleclass,
        t.exvehicleid,
        t.exvehicletype,
        t.fee,
        t.exweight,
        t.feeboardplay,
        t.feemileage,
        t.id,
        t.identification,
        t.feerate,
        t.identifyvehicleid,
        t.lanetype,
        t.mediano,
        t.mediatype,
        t.nocardcount,
        t.obuid,
        t.obusign,
        t.obutotalamount,
        t.obutotaldiscountamount,
        t.params,
        t.operid,
        t.passid,
        t.paycardid,
        t.payfee,
        t.paytype,
        t.provfee,
        t.provtranscount,
        t.provincecount,
        t.shift,
        t.receivetime,
        t.shortfee,
        t.shortfeemileage,
        t.signstatus,
        t.spcrateversion,
        t.tac,
        t.specialtype,
        t.splitprovince,
        t.terminalno,
        t.terminaltransno,
        t.transfee,
        t.transpaytype,
        t.transtype,
        t.load_time,
        t.vehiclesign,
        t.grade_level,
        t.vehiclesignid
    
"""

#: resultMap 声明的 65 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "big_id",
    "actualfeeclass",
    "axlecount",
    "discountfee",
    "electricalpercentage",
    "enaxlecount",
    "entime",
    "entolllanehex",
    "entolllaneid",
    "entollstationid",
    "entollstationname",
    "envehicleclass",
    "envehicleid",
    "envehicletype",
    "enweight",
    "entryoperatorid",
    "extime",
    "extolllaneid",
    "extollstationid",
    "extollstationname",
    "exvehicleclass",
    "exvehicleid",
    "exvehicletype",
    "fee",
    "exweight",
    "feeboardplay",
    "feemileage",
    "identification",
    "feerate",
    "identifyvehicleid",
    "lanetype",
    "mediano",
    "mediatype",
    "nocardcount",
    "obuid",
    "obusign",
    "obutotalamount",
    "obutotaldiscountamount",
    "params",
    "operid",
    "passid",
    "paycardid",
    "payfee",
    "paytype",
    "provfee",
    "provtranscount",
    "provincecount",
    "shift",
    "receivetime",
    "shortfee",
    "shortfeemileage",
    "signstatus",
    "spcrateversion",
    "tac",
    "specialtype",
    "splitprovince",
    "terminalno",
    "terminaltransno",
    "transfee",
    "transpaytype",
    "transtype",
    "load_time",
    "vehiclesign",
    "grade_level",
    "vehiclesignid",
)

#: ``selectOdsLwzxsfsjFeeStationExit01List`` 的 65 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id"),
    If("actualfeeclass", "actualfeeclass"),
    If("axlecount", "axlecount", null_only=True),
    If("discountfee", "discountfee", null_only=True),
    If("electricalpercentage", "electricalpercentage", null_only=True),
    If("enaxlecount", "enaxlecount", null_only=True),
    If("entime", "entime", null_only=True),
    If("entolllanehex", "entolllanehex"),
    If("entolllaneid", "entolllaneid"),
    If("entollstationid", "entollstationid"),
    If("entollstationname", "entollstationname", like=True),
    If("envehicleclass", "envehicleclass", null_only=True),
    If("envehicleid", "envehicleid"),
    If("envehicletype", "envehicletype", null_only=True),
    If("enweight", "enweight", null_only=True),
    If("entryoperatorid", "entryoperatorid"),
    If("extime", "extime", null_only=True),
    If("extolllaneid", "extolllaneid"),
    If("extollstationid", "extollstationid"),
    If("extollstationname", "extollstationname", like=True),
    If("exvehicleclass", "exvehicleclass", null_only=True),
    If("exvehicleid", "exvehicleid"),
    If("exvehicletype", "exvehicletype", null_only=True),
    If("fee", "fee", null_only=True),
    If("exweight", "exweight", null_only=True),
    If("feeboardplay", "feeboardplay"),
    If("feemileage", "feemileage", null_only=True),
    If("identification", "identification"),
    If("feerate", "feerate", null_only=True),
    If("identifyvehicleid", "identifyvehicleid"),
    If("lanetype", "lanetype"),
    If("mediano", "mediano"),
    If("mediatype", "mediatype"),
    If("nocardcount", "nocardcount", null_only=True),
    If("obuid", "obuid"),
    If("obusign", "obusign"),
    If("obutotalamount", "obutotalamount", null_only=True),
    If("obutotaldiscountamount", "obutotaldiscountamount", null_only=True),
    If("params", "params"),
    If("operid", "operid"),
    If("passid", "passid"),
    If("paycardid", "paycardid"),
    If("payfee", "payfee", null_only=True),
    If("paytype", "paytype"),
    If("provfee", "provfee", null_only=True),
    If("provtranscount", "provtranscount", null_only=True),
    If("provincecount", "provincecount", null_only=True),
    If("shift", "shift"),
    If("receivetime", "receivetime", null_only=True),
    If("shortfee", "shortfee", null_only=True),
    If("shortfeemileage", "shortfeemileage", null_only=True),
    If("signstatus", "signstatus"),
    If("spcrateversion", "spcrateversion"),
    If("tac", "tac"),
    If("specialtype", "specialtype"),
    If("splitprovince", "splitprovince"),
    If("terminalno", "terminalno"),
    If("terminaltransno", "terminaltransno"),
    If("transfee", "transfee", null_only=True),
    If("transpaytype", "transpaytype"),
    If("transtype", "transtype"),
    If("load_time", "load_time", null_only=True),
    If("vehiclesign", "vehiclesign"),
    If("grade_level", "grade_level"),
    If("vehiclesignid", "vehiclesignid"),
)


class OdsLwzxsfsjFeeStationExit01Mapper(OdsListMapper):
    """Java: ``interface OdsLwzxsfsjFeeStationExit01Mapper``."""

    table = "ods_lwzxsfsj_fee_station_exit_01"
    select_vo = SELECT_ODS_LWZXSFSJ_FEE_STATION_EXIT01_VO
    entity_cls = OdsLwzxsfsjFeeStationExit01
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.big_id"
    detail_column = "big_id"

    def delete_ods_lwzxsfsj_fee_station_exit01_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "big_id", entity_ids)


__all__ = ["OdsLwzxsfsjFeeStationExit01Mapper", "RESULT_COLUMNS", "CONDITIONS"]
