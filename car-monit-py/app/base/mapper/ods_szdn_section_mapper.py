"""路段信息.

# Migrated from: com/ruoyi/base/mapper/OdsSzdnSectionMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsSzdnSectionMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.ods_szdn_section import OdsSzdnSection
from app.base.mapper.ods_sql import If, OdsListMapper
from sqlalchemy import text
from app.base.mapper.ods_sql import assemble_list, map_row
from app.config.database import session_scope

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ODS_SZDN_SECTION_VO = """
        t.id,
        t.road_code,
        t.road_name,
        t.section_code,
        t.section_name,
        t.start_pile_no,
        t.end_pile_no,
        t.org_code,
        t.org_name,
        t.org_level_code,
        t.org_category,
        t.mileage,
        t.open_date
    
"""

#: resultMap 声明的 13 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "road_code",
    "road_name",
    "section_code",
    "section_name",
    "start_pile_no",
    "end_pile_no",
    "org_code",
    "org_name",
    "org_level_code",
    "org_category",
    "mileage",
    "open_date",
)

#: ``selectOdsSzdnSectionList`` 的 13 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("road_code", "road_code"),
    If("road_name", "road_name", like=True),
    If("section_code", "section_code"),
    If("section_name", "section_name", like=True),
    If("start_pile_no", "start_pile_no", null_only=True),
    If("end_pile_no", "end_pile_no", null_only=True),
    If("org_code", "org_code"),
    If("org_name", "org_name", like=True),
    If("org_level_code", "org_level_code"),
    If("org_category", "org_category"),
    If("mileage", "mileage", null_only=True),
    If("open_date", "open_date", null_only=True),
)


#: ``selectOdsSzdnSectionListNew`` 投影（与 ``List`` 不同：distinct / 自定义列）。
SELECT_ODS_SZDN_SECTION_NEW_VO = """
distinct t.section_code, concat(t.road_code, '', t.section_name) section_name
"""

CONDITIONS_NEW: Tuple[If, ...] = (
    If("id", "id"),
    If("road_code", "road_code"),
    If("road_name", "road_name", like=True),
    If("section_code", "section_code"),
    If("section_name", "section_name", like=True),
    If("start_pile_no", "start_pile_no", null_only=True),
    If("end_pile_no", "end_pile_no", null_only=True),
    If("org_code", "org_code"),
    If("org_name", "org_name", like=True),
    If("org_level_code", "org_level_code"),
    If("org_category", "org_category"),
    If("mileage", "mileage", null_only=True),
    If("open_date", "open_date", null_only=True),
)


class OdsSzdnSectionMapper(OdsListMapper):
    """Java: ``interface OdsSzdnSectionMapper``."""

    table = "ods_szdn_section"
    select_vo = SELECT_ODS_SZDN_SECTION_VO
    entity_cls = OdsSzdnSection
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.road_code,t.section_code"
    detail_column = "id"

    # Java: List<OdsSzdnSection> selectOdsSzdnSectionListNew(OdsSzdnSection x)
    def select_list_new(self, query):
        """不分页：大屏 / 下拉框用的轻量投影。"""
        sql, params = assemble_list(
            SELECT_ODS_SZDN_SECTION_NEW_VO, self.table, CONDITIONS_NEW, query
        )
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    def delete_ods_szdn_section_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "id", entity_ids)


__all__ = ["OdsSzdnSectionMapper", "RESULT_COLUMNS", "CONDITIONS"]
