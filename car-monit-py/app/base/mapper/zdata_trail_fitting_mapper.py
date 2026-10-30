"""车辆出入口拟合轨迹.

# Migrated from: com/ruoyi/base/mapper/ZdataTrailFittingMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/ZdataTrailFittingMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.zdata_trail_fitting import ZdataTrailFitting
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ZDATA_TRAIL_FITTING_VO = """
        t.cid,
        t.enaxlecount,
        t.entime,
        t.entolllaneid,
        t.entollstationid,
        t.entollstationname,
        t.envehicleclass,
        t.envehicleid,
        t.envehicletype,
        t.enweight,
        t.extime,
        t.extolllaneid,
        t.extollstationid,
        t.extollstationname,
        t.exvehicleclass,
        t.exvehicleid,
        t.exvehicletype,
        t.exweight,
        t.trailpoints
    
"""

#: resultMap 声明的 19 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "cid",
    "enaxlecount",
    "entime",
    "entolllaneid",
    "entollstationid",
    "entollstationname",
    "envehicleclass",
    "envehicleid",
    "envehicletype",
    "enweight",
    "extime",
    "extolllaneid",
    "extollstationid",
    "extollstationname",
    "exvehicleclass",
    "exvehicleid",
    "exvehicletype",
    "exweight",
    "trailpoints",
)

#: ``selectZdataTrailFittingList`` 的 19 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("enaxlecount", "enaxlecount", null_only=True),
    If("entime", "entime", null_only=True),
    If("entolllaneid", "entolllaneid"),
    If("entollstationid", "entollstationid"),
    If("entollstationname", "entollstationname", like=True),
    If("envehicleclass", "envehicleclass", null_only=True),
    If("envehicleid", "envehicleid"),
    If("envehicletype", "envehicletype", null_only=True),
    If("enweight", "enweight", null_only=True),
    If("extime", "extime", null_only=True),
    If("extolllaneid", "extolllaneid"),
    If("extollstationid", "extollstationid"),
    If("extollstationname", "extollstationname", like=True),
    If("exvehicleclass", "exvehicleclass", null_only=True),
    If("exvehicleid", "exvehicleid"),
    If("exvehicletype", "exvehicletype", null_only=True),
    If("exweight", "exweight", null_only=True),
    If("trailpoints", "trailpoints"),
)


class ZdataTrailFittingMapper(OdsListMapper):
    """Java: ``interface ZdataTrailFittingMapper``."""

    table = "zdata_trail_fitting"
    select_vo = SELECT_ZDATA_TRAIL_FITTING_VO
    entity_cls = ZdataTrailFitting
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = None
    # XML 里没有 order by —— PageHelper 会追加客户端排序。
    detail_column = "cid"

    def delete_zdata_trail_fitting_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "cid", entity_ids)


__all__ = ["ZdataTrailFittingMapper", "RESULT_COLUMNS", "CONDITIONS"]
