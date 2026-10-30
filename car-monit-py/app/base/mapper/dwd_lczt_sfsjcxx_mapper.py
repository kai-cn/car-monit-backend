"""收费站基础信息.

# Migrated from: com/ruoyi/base/mapper/DwdLcztSfsjcxxMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/DwdLcztSfsjcxxMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.dwd_lczt_sfsjcxx import DwdLcztSfsjcxx
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_DWD_LCZT_SFSJCXX_VO = """
        t.agent_pk,
        t.yxtzj,
        t.sfsbm,
        t.sfsmc,
        t.jd,
        t.wd,
        t.sslxbh,
        t.sslxmc,
        t.ssldbh,
        t.ssldmc,
        t.sczh_k,
        t.sczh_n,
        t.ssglzxbm,
        t.ssglzxmc,
        t.lyxt,
        t.load_time,
        t.all_col_pk
    
"""

#: resultMap 声明的 17 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "agent_pk",
    "yxtzj",
    "sfsbm",
    "sfsmc",
    "jd",
    "wd",
    "sslxbh",
    "sslxmc",
    "ssldbh",
    "ssldmc",
    "sczh_k",
    "sczh_n",
    "ssglzxbm",
    "ssglzxmc",
    "lyxt",
    "load_time",
    "all_col_pk",
)

#: ``selectDwdLcztSfsjcxxList`` 的 17 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("agent_pk", "agent_pk", template="and and t.agent_pk = #{id}"),
    If("yxtzj", "yxtzj"),
    If("sfsbm", "sfsbm"),
    If("sfsmc", "sfsmc", like=True),
    If("jd", "jd"),
    If("wd", "wd"),
    If("sslxbh", "sslxbh"),
    If("sslxmc", "sslxmc"),
    If("ssldbh", "ssldbh"),
    If("ssldmc", "ssldmc", like=True),
    If("sczh_k", "sczh_k"),
    If("sczh_n", "sczh_n"),
    If("ssglzxbm", "ssglzxbm"),
    If("ssglzxmc", "ssglzxmc"),
    If("lyxt", "lyxt"),
    If("load_time", "load_time"),
    If("all_col_pk", "all_col_pk"),
)


class DwdLcztSfsjcxxMapper(OdsListMapper):
    """Java: ``interface DwdLcztSfsjcxxMapper``."""

    table = "dwd_lczt_sfsjcxx"
    select_vo = SELECT_DWD_LCZT_SFSJCXX_VO
    entity_cls = DwdLcztSfsjcxx
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.agent_pk"
    detail_column = "agent_pk"

    def delete_dwd_lczt_sfsjcxx_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "agent_pk", entity_ids)


__all__ = ["DwdLcztSfsjcxxMapper", "RESULT_COLUMNS", "CONDITIONS"]
