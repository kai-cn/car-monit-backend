"""车辆位置字典.

# Migrated from: com/ruoyi/base/mapper/ZdataLocationDictMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/ZdataLocationDictMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.zdata_location_dict import ZdataLocationDict
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ZDATA_LOCATION_DICT_VO = """
        t.id,
        t.type,
        t.name,
        t.raw_code,
        t.standard_code,
        t.roadcode,
        t.roadname,
        t.sectioncode,
        t.sectionname,
        t.tollcode,
        t.tollname,
        t.orgcode,
        t.orgname,
        t.created_at,
        t.updated_at
    
"""

#: resultMap 声明的 15 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "type",
    "name",
    "raw_code",
    "standard_code",
    "roadcode",
    "roadname",
    "sectioncode",
    "sectionname",
    "tollcode",
    "tollname",
    "orgcode",
    "orgname",
    "created_at",
    "updated_at",
)

#: ``selectZdataLocationDictList`` 的 15 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("type", "type"),
    If("name", "name", like=True),
    If("raw_code", "raw_code"),
    If("standard_code", "standard_code"),
    If("roadcode", "roadcode"),
    If("roadname", "roadname", like=True),
    If("sectioncode", "sectioncode"),
    If("sectionname", "sectionname", like=True),
    If("tollcode", "tollcode"),
    If("tollname", "tollname", like=True),
    If("orgcode", "orgcode"),
    If("orgname", "orgname", like=True),
    If("created_at", "created_at", null_only=True),
    If("updated_at", "updated_at", null_only=True),
)


class ZdataLocationDictMapper(OdsListMapper):
    """Java: ``interface ZdataLocationDictMapper``."""

    table = "zdata_location_dict"
    select_vo = SELECT_ZDATA_LOCATION_DICT_VO
    entity_cls = ZdataLocationDict
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = None
    # XML 里没有 order by —— PageHelper 会追加客户端排序。
    detail_column = "id"

    def delete_zdata_location_dict_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "id", entity_ids)


__all__ = ["ZdataLocationDictMapper", "RESULT_COLUMNS", "CONDITIONS"]
