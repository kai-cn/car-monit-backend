"""收费站入口数据 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsLwzxsfsjFeeStationEnter01Mapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationEnter01Mapper.xml

投影里那个多余的 ``t.id``
------------------------
``<sql id="selectOdsLwzxsfsjFeeStationEnter01Vo">`` 在 ``t.enweight`` 与
``t.identifyvehicleid`` 之间夹了 ``t.id``，但：

* 实体没有 ``id`` 字段；
* ``resultMap`` 也没有 ``id`` 映射。

MyBatis 用 ``resultMap`` 回填时发现"找不到同名属性"，直接忽略这一列。所以
:data:`RESULT_COLUMNS` 里**不含** ``id`` —— 若加上，``map_row`` 会把它塞进
``OdsLwzxsfsjFeeStationEnter01(**fields)``，而 pydantic 的 ``extra="ignore"``
会静默丢掉，看起来"没坏"，其实是在靠巧合工作，所以显式排除。

有 ``order by t.big_id``
------------------------
因此 PageHelper **不会**追加客户端 ``orderByColumn`` —— 前端点表头排序对这个
接口无效。与 ``OdsCxztFwqcllsMapper`` 正好相反。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.domain.ods_lwzxsfsj_fee_station_enter01 import (
    OdsLwzxsfsjFeeStationEnter01,
)
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql id="selectOdsLwzxsfsjFeeStationEnter01Vo">``（含多余的 ``t.id``）。
SELECT_ODS_LWZXSFSJ_FEE_STATION_ENTER01_VO = """
        t.big_id,
        t.cardid,
        t.electricalpercentage,
        t.enaxlecount,
        t.entime,
        t.entolllanehex,
        t.entolllaneid,
        t.entollstationid,
        t.enweight,
        t.id,
        t.identifyvehicleid,
        t.lanetype,
        t.mediatype,
        t.operid,
        t.operationmedia,
        t.params,
        t.passid,
        t.receivetime,
        t.shift,
        t.signstatus,
        t.specialtype,
        t.tac,
        t.terminalno,
        t.terminaltransno,
        t.transfee,
        t.transtype,
        t.vcount,
        t.vehicleclass,
        t.vehicleid,
        t.vehiclesign,
        t.vehiclesignid,
        t.vehicletype,
        t.load_time,
        t.grade_level,
        t.cid
"""

#: ``resultMap`` 的 34 条 ``<result>``（**没有** ``id``）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "big_id",
    "cardid",
    "electricalpercentage",
    "enaxlecount",
    "entime",
    "entolllanehex",
    "entolllaneid",
    "entollstationid",
    "enweight",
    "identifyvehicleid",
    "lanetype",
    "mediatype",
    "operid",
    "operationmedia",
    "params",
    "passid",
    "receivetime",
    "shift",
    "signstatus",
    "specialtype",
    "tac",
    "terminalno",
    "terminaltransno",
    "transfee",
    "transtype",
    "vcount",
    "vehicleclass",
    "vehicleid",
    "vehiclesign",
    "vehiclesignid",
    "vehicletype",
    "load_time",
    "grade_level",
    "cid",
)

#: ``<if>`` 列表，顺序与 XML 一致（33 条，全部是等值）。
CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id", null_only=True),
    If("cardid", "cardid"),
    If("electricalpercentage", "electricalpercentage", null_only=True),
    If("enaxlecount", "enaxlecount", null_only=True),
    If("entime", "entime", null_only=True),
    If("entolllanehex", "entolllanehex"),
    If("entolllaneid", "entolllaneid"),
    If("entollstationid", "entollstationid"),
    If("enweight", "enweight", null_only=True),
    If("identifyvehicleid", "identifyvehicleid"),
    If("lanetype", "lanetype"),
    If("mediatype", "mediatype"),
    If("operid", "operid"),
    If("operationmedia", "operationmedia"),
    If("params", "params"),
    If("passid", "passid"),
    If("receivetime", "receivetime", null_only=True),
    If("shift", "shift"),
    If("signstatus", "signstatus"),
    If("specialtype", "specialtype"),
    If("tac", "tac"),
    If("terminalno", "terminalno"),
    If("terminaltransno", "terminaltransno"),
    If("transfee", "transfee", null_only=True),
    If("transtype", "transtype"),
    If("vcount", "vcount", null_only=True),
    If("vehicleclass", "vehicleclass"),
    If("vehicleid", "vehicleid"),
    If("vehiclesign", "vehiclesign"),
    If("vehiclesignid", "vehiclesignid"),
    If("vehicletype", "vehicletype"),
    If("load_time", "load_time", null_only=True),
    If("grade_level", "grade_level"),
)


class OdsLwzxsfsjFeeStationEnter01Mapper(OdsListMapper):
    """Java: ``interface OdsLwzxsfsjFeeStationEnter01Mapper``."""

    table = "ods_lwzxsfsj_fee_station_enter_01"
    select_vo = SELECT_ODS_LWZXSFSJ_FEE_STATION_ENTER01_VO
    entity_cls = OdsLwzxsfsjFeeStationEnter01
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    #: XML 末尾的 ``order by t.big_id``。
    order_by: Optional[str] = "big_id"
    #: ``where t.big_id = #{bigId}``.
    detail_column = "big_id"


__all__ = [
    "CONDITIONS",
    "OdsLwzxsfsjFeeStationEnter01Mapper",
    "RESULT_COLUMNS",
    "SELECT_ODS_LWZXSFSJ_FEE_STATION_ENTER01_VO",
]
