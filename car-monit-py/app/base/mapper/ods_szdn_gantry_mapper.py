"""门架信息.

# Migrated from: com/ruoyi/base/mapper/OdsSzdnGantryMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.ods_szdn_gantry import OdsSzdnGantry
from app.base.mapper.ods_sql import If, OdsListMapper
from sqlalchemy import text
from app.base.mapper.ods_sql import assemble_list, map_row
from app.config.database import session_scope

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ODS_SZDN_GANTRY_VO = """
        t.id,
        t.gantry_code,
        t.gantry_name,
        t.road_code,
        t.section_code,
        t.toll_code,
        t.org_code,
        t.hex_code,
        t.direction,
        t.pile_no,
        t.lon,
        t.lat,
        t.remark,
        t.is_virtual,
        t.mileage,
        t.boundary_gantry_type,
        t.gantry_type,
        t.city_code,
        t.district_name,
        t.belong_group,
        t.gantry_code_merge,
        t.gantry_name_alias
    
"""

#: resultMap 声明的 22 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "gantry_code",
    "gantry_name",
    "road_code",
    "section_code",
    "toll_code",
    "org_code",
    "hex_code",
    "direction",
    "pile_no",
    "lon",
    "lat",
    "remark",
    "is_virtual",
    "mileage",
    "boundary_gantry_type",
    "gantry_type",
    "city_code",
    "district_name",
    "belong_group",
    "gantry_code_merge",
    "gantry_name_alias",
)

#: ``selectOdsSzdnGantryList`` 的 22 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("gantry_code", "gantry_code"),
    If("gantry_name", "gantry_name", like=True),
    If("road_code", "road_code"),
    If("section_code", "section_code"),
    If("toll_code", "toll_code"),
    If("org_code", "org_code"),
    If("hex_code", "hex_code"),
    If("direction", "direction"),
    If("pile_no", "pile_no", like=True),
    If("lon", "lon"),
    If("lat", "lat"),
    If("is_virtual", "is_virtual"),
    If("mileage", "mileage"),
    If("boundary_gantry_type", "boundary_gantry_type"),
    If("gantry_type", "gantry_type"),
    If("city_code", "city_code"),
    If("district_name", "district_name", like=True),
    If("belong_group", "belong_group"),
    If("gantry_code_merge", "gantry_code_merge"),
    If("gantry_name_alias", "gantry_name_alias"),
    If("section_name", "section_code", like=True),
)


#: ``selectOdsSzdnGantryListNew`` 投影（与 ``List`` 不同：distinct / 自定义列）。
SELECT_ODS_SZDN_GANTRY_NEW_VO = """
distinct t.gantry_code, t.gantry_name
"""

CONDITIONS_NEW: Tuple[If, ...] = (
    If("id", "id"),
    If("gantry_code", "gantry_code"),
    If("gantry_name", "gantry_name", like=True),
    If("road_code", "road_code"),
    If("section_code", "section_code"),
    If("toll_code", "toll_code"),
    If("org_code", "org_code"),
    If("hex_code", "hex_code"),
    If("direction", "direction"),
    If("pile_no", "pile_no", like=True),
    If("lon", "lon"),
    If("lat", "lat"),
    If("is_virtual", "is_virtual"),
    If("mileage", "mileage"),
    If("boundary_gantry_type", "boundary_gantry_type"),
    If("gantry_type", "gantry_type"),
    If("city_code", "city_code"),
    If("district_name", "district_name", like=True),
    If("belong_group", "belong_group"),
    If("gantry_code_merge", "gantry_code_merge"),
    If("gantry_name_alias", "gantry_name_alias"),
    If("section_code_list", "section_code", in_list=True),
)


class OdsSzdnGantryMapper(OdsListMapper):
    """Java: ``interface OdsSzdnGantryMapper``."""

    table = "ods_szdn_gantry"
    select_vo = SELECT_ODS_SZDN_GANTRY_VO
    entity_cls = OdsSzdnGantry
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.gantry_name"
    detail_column = "id"

    # Java: List<OdsSzdnGantry> selectOdsSzdnGantryListNew(OdsSzdnGantry x)
    def select_list_new(self, query):
        """不分页：大屏 / 下拉框用的轻量投影。"""
        sql, params = assemble_list(
            SELECT_ODS_SZDN_GANTRY_NEW_VO, self.table, CONDITIONS_NEW, query
        )
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    def delete_ods_szdn_gantry_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "id", entity_ids)


__all__ = ["OdsSzdnGantryMapper", "RESULT_COLUMNS", "CONDITIONS"]
