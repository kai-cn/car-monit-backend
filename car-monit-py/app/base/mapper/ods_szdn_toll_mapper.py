"""收费站信息.

# Migrated from: com/ruoyi/base/mapper/OdsSzdnTollMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.mapper.ods_sql import If, OdsListMapper
from sqlalchemy import text
from app.base.mapper.ods_sql import assemble_list, map_row
from app.config.database import session_scope

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ODS_SZDN_TOLL_VO = """
        t.id,
        t.road_code,
        t.id_card,
        t.toll_code,
        t.toll_name,
        t.pile_no,
        t.org_name,
        t.hex_code,
        t.state_code,
        t.org_code,
        t.longitude,
        t.latitude,
        t.open_date,
        t.toll_alias_name,
        t.in_monitor_resource,
        t.lane_monitor_resource,
        t.square_monitor_resource,
        t.dynamic_monitor_resource,
        t.toll_code_merge,
        t.state_code_merge,
        t.toll_name_merge,
        t.section_code,
        t.toll_org_code,
        t.is_access
    
"""

#: resultMap 声明的 24 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "road_code",
    "id_card",
    "toll_code",
    "toll_name",
    "pile_no",
    "org_name",
    "hex_code",
    "state_code",
    "org_code",
    "longitude",
    "latitude",
    "open_date",
    "toll_alias_name",
    "in_monitor_resource",
    "lane_monitor_resource",
    "square_monitor_resource",
    "dynamic_monitor_resource",
    "toll_code_merge",
    "state_code_merge",
    "toll_name_merge",
    "section_code",
    "toll_org_code",
    "is_access",
)

#: ``selectOdsSzdnTollList`` 的 25 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("road_code", "road_code"),
    If("id_card", "id_card"),
    If("toll_code", "toll_code"),
    If("toll_name", "toll_name", like=True),
    If("pile_no", "pile_no"),
    If("org_name", "org_name", like=True),
    If("hex_code", "hex_code"),
    If("state_code", "state_code"),
    If("org_code", "org_code"),
    If("longitude", "longitude"),
    If("latitude", "latitude"),
    If("open_date", "open_date", null_only=True),
    If("toll_alias_name", "toll_alias_name", like=True),
    If("in_monitor_resource", "in_monitor_resource"),
    If("lane_monitor_resource", "lane_monitor_resource"),
    If("square_monitor_resource", "square_monitor_resource"),
    If("dynamic_monitor_resource", "dynamic_monitor_resource"),
    If("toll_code_merge", "toll_code_merge"),
    If("state_code_merge", "state_code_merge"),
    If("toll_name_merge", "toll_name_merge", like=True),
    If("section_code", "section_code"),
    If("toll_org_code", "toll_org_code"),
    If("is_access", "is_access"),
    If("section_name", "section_code", like=True),
)


#: ``selectOdsSzdnTollListNew`` 投影（与 ``List`` 不同：distinct / 自定义列）。
SELECT_ODS_SZDN_TOLL_NEW_VO = """
distinct t.toll_code,t.toll_name
"""

CONDITIONS_NEW: Tuple[If, ...] = (
    If("id", "id"),
    If("road_code", "road_code"),
    If("id_card", "id_card"),
    If("toll_code", "toll_code"),
    If("toll_name", "toll_name", like=True),
    If("pile_no", "pile_no"),
    If("org_name", "org_name", like=True),
    If("hex_code", "hex_code"),
    If("state_code", "state_code"),
    If("org_code", "org_code"),
    If("longitude", "longitude"),
    If("latitude", "latitude"),
    If("open_date", "open_date", null_only=True),
    If("toll_alias_name", "toll_alias_name", like=True),
    If("in_monitor_resource", "in_monitor_resource"),
    If("lane_monitor_resource", "lane_monitor_resource"),
    If("square_monitor_resource", "square_monitor_resource"),
    If("dynamic_monitor_resource", "dynamic_monitor_resource"),
    If("toll_code_merge", "toll_code_merge"),
    If("state_code_merge", "state_code_merge"),
    If("toll_name_merge", "toll_name_merge", like=True),
    If("section_code", "section_code"),
    If("toll_org_code", "toll_org_code"),
    If("is_access", "is_access"),
    If("section_code_list", "section_code", in_list=True),
)


class OdsSzdnTollMapper(OdsListMapper):
    """Java: ``interface OdsSzdnTollMapper``."""

    table = "ods_szdn_toll"
    select_vo = SELECT_ODS_SZDN_TOLL_VO
    entity_cls = OdsSzdnToll
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.toll_name"
    detail_column = "id"

    # Java: List<OdsSzdnToll> selectOdsSzdnTollListNew(OdsSzdnToll x)
    def select_list_new(self, query):
        """不分页：大屏 / 下拉框用的轻量投影。"""
        sql, params = assemble_list(
            SELECT_ODS_SZDN_TOLL_NEW_VO, self.table, CONDITIONS_NEW, query
        )
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    def delete_ods_szdn_toll_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "id", entity_ids)


__all__ = ["OdsSzdnTollMapper", "RESULT_COLUMNS", "CONDITIONS"]
