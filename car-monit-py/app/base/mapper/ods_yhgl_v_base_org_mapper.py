"""机构信息.

# Migrated from: com/ruoyi/base/mapper/OdsYhglVBaseOrgMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsYhglVBaseOrgMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Any, List, Tuple

from sqlalchemy import text

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.ods_yhgl_v_base_org import OdsYhglVBaseOrg
from app.config.database import session_scope
from app.base.mapper.ods_sql import If, OdsListMapper, map_result_row

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ODS_YHGL_V_BASE_ORG_VO = """
        t.big_id,
        t.org_code,
        t.org_name,
        t.org_short_name,
        t.org_parent_id,
        t.org_level_code,
        t.org_is_virtual,
        t.org_maintenance,
        t.org_sequence,
        t.org_is_manager,
        t.org_is_deleted,
        t.org_category,
        t.org_is_authorized,
        t.org_address,
        t.org_is_yh_autarky,
        t.load_time,
        t.grade_level,
        (select t1.big_id from  ods_yhgl_v_base_org t1 where t1.org_code = t.org_parent_id) parentId
    
"""

#: resultMap 声明的 17 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "big_id",
    "org_code",
    "org_name",
    "org_short_name",
    "org_parent_id",
    "org_level_code",
    "org_is_virtual",
    "org_maintenance",
    "org_sequence",
    "org_is_manager",
    "org_is_deleted",
    "org_category",
    "org_is_authorized",
    "org_address",
    "org_is_yh_autarky",
    "load_time",
    "grade_level",
)

#: ``selectOdsYhglVBaseOrgList`` 的 17 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id"),
    If("org_code", "org_code"),
    If("org_name", "org_name", like=True),
    If("org_short_name", "org_short_name", like=True),
    If("org_parent_id", "org_parent_id"),
    If("org_level_code", "org_level_code"),
    If("org_is_virtual", "org_is_virtual"),
    If("org_maintenance", "org_maintenance"),
    If("org_sequence", "org_sequence", null_only=True),
    If("org_is_manager", "org_is_manager"),
    If("org_is_deleted", "org_is_deleted"),
    If("org_category", "org_category", null_only=True),
    If("org_is_authorized", "org_is_authorized"),
    If("org_address", "org_address"),
    If("org_is_yh_autarky", "org_is_yh_autarky"),
    If("load_time", "load_time", null_only=True),
    If("grade_level", "grade_level", null_only=True),
)


class OdsYhglVBaseOrgMapper(OdsListMapper):
    """Java: ``interface OdsYhglVBaseOrgMapper``."""

    table = "ods_yhgl_v_base_org"
    select_vo = SELECT_ODS_YHGL_V_BASE_ORG_VO
    entity_cls = OdsYhglVBaseOrg
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.big_id"
    detail_column = "big_id"

    def delete_ods_yhgl_v_base_org_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "big_id", entity_ids)

    # MyBatis-Plus: ``lambdaQuery().select(OdsYhglVBaseOrg::getOrgCode,
    # OdsYhglVBaseOrg::getOrgName).list()`` —— 大屏 ``/orgList`` 专用。
    def select_org_list(self) -> List[Any]:
        """只取 ``org_code`` / ``org_name`` 两列。

        MP 的 ``select(...)`` 是**投影**，不会展开 ``selectOdsYhglVBaseOrgVo`` 的
        17 列（含那个相关子查询），也不会追加任何过滤条件 —— 实体上没有
        ``@TableLogic``，所以软删除的行同样会出现在结果里。
        """
        sql = "select t.org_code, t.org_name from ods_yhgl_v_base_org t"
        with session_scope() as session:
            rows = session.execute(text(sql), {}).all()
        return [
            map_result_row(OdsYhglVBaseOrg, ("org_code", "org_name"), row) for row in rows
        ]


__all__ = ["OdsYhglVBaseOrgMapper", "RESULT_COLUMNS", "CONDITIONS"]
