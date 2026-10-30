"""服务区基础信息.

# Migrated from: com/ruoyi/base/mapper/DwdLcztFwqjcxxMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/DwdLcztFwqjcxxMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.plus_mapper import logic_delete_by_ids
from app.base.domain.dwd_lczt_fwqjcxx import DwdLcztFwqjcxx
from app.base.mapper.ods_sql import If, OdsListMapper
from sqlalchemy import text
from app.base.mapper.ods_sql import assemble_list, map_row
from app.config.database import session_scope

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_DWD_LCZT_FWQJCXX_VO = """
        t.agent_pk,
        t.yxtzj,
        t.fwqbm,
        t.fwqmc,
        t.wd,
        t.fxmc,
        t.fxdm,
        t.jd,
        t.sslxbh,
        t.sslxmc,
        t.ssldbh,
        t.ssldmc,
        t.sczhkgs,
        t.sczhszgs,
        t.ssglzxbm,
        t.ssglzxmc,
        t.xzqhmc,
        t.yyrq,
        t.cws,
        t.sfszlkk,
        t.cdzs,
        t.sfcyfw,
        t.sftgzsfw,
        t.sftgqxfw,
        t.sftgcsfw,
        t.sftgjyfw,
        t.mj,
        t.sftgcshfw,
        t.xzqhdm,
        t.synx,
        t.lyxt,
        t.load_time,
        t.all_col_pk
    
"""

#: resultMap 声明的 33 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "agent_pk",
    "yxtzj",
    "fwqbm",
    "fwqmc",
    "wd",
    "fxmc",
    "fxdm",
    "jd",
    "sslxbh",
    "sslxmc",
    "ssldbh",
    "ssldmc",
    "sczhkgs",
    "sczhszgs",
    "ssglzxbm",
    "ssglzxmc",
    "xzqhmc",
    "yyrq",
    "cws",
    "sfszlkk",
    "cdzs",
    "sfcyfw",
    "sftgzsfw",
    "sftgqxfw",
    "sftgcsfw",
    "sftgjyfw",
    "mj",
    "sftgcshfw",
    "xzqhdm",
    "synx",
    "lyxt",
    "load_time",
    "all_col_pk",
)

#: ``selectDwdLcztFwqjcxxList`` 的 33 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("agent_pk", "agent_pk"),
    If("yxtzj", "yxtzj"),
    If("fwqbm", "fwqbm"),
    If("fwqmc", "fwqmc", like=True),
    If("wd", "wd"),
    If("fxmc", "fxmc"),
    If("fxdm", "fxdm"),
    If("jd", "jd"),
    If("sslxbh", "sslxbh"),
    If("sslxmc", "sslxmc"),
    If("ssldbh", "ssldbh"),
    If("ssldmc", "ssldmc", like=True),
    If("sczhkgs", "sczhkgs"),
    If("sczhszgs", "sczhszgs"),
    If("ssglzxbm", "ssglzxbm"),
    If("ssglzxmc", "ssglzxmc"),
    If("xzqhmc", "xzqhmc"),
    If("yyrq", "yyrq"),
    If("cws", "cws"),
    If("sfszlkk", "sfszlkk"),
    If("cdzs", "cdzs"),
    If("sfcyfw", "sfcyfw"),
    If("sftgzsfw", "sftgzsfw"),
    If("sftgqxfw", "sftgqxfw"),
    If("sftgcsfw", "sftgcsfw"),
    If("sftgjyfw", "sftgjyfw"),
    If("mj", "mj"),
    If("sftgcshfw", "sftgcshfw"),
    If("xzqhdm", "xzqhdm"),
    If("synx", "synx"),
    If("lyxt", "lyxt"),
    If("load_time", "load_time"),
    If("all_col_pk", "all_col_pk"),
)


#: ``selectDwdLcztFwqjcxxListNew`` 投影（与 ``List`` 不同：distinct / 自定义列）。
SELECT_DWD_LCZT_FWQJCXX_NEW_VO = """
distinct t.fwqbm,t.fwqmc
"""

CONDITIONS_NEW: Tuple[If, ...] = (
    If("agent_pk", "agent_pk"),
    If("yxtzj", "yxtzj"),
    If("fwqbm", "fwqbm"),
    If("fwqmc", "fwqmc", like=True),
    If("wd", "wd"),
    If("fxmc", "fxmc"),
    If("fxdm", "fxdm"),
    If("jd", "jd"),
    If("sslxbh", "sslxbh"),
    If("sslxmc", "sslxmc"),
    If("ssldbh", "ssldbh"),
    If("ssldmc", "ssldmc"),
    If("sczhkgs", "sczhkgs"),
    If("sczhszgs", "sczhszgs"),
    If("ssglzxbm", "ssglzxbm"),
    If("ssglzxmc", "ssglzxmc"),
    If("xzqhmc", "xzqhmc"),
    If("yyrq", "yyrq"),
    If("cws", "cws"),
    If("sfszlkk", "sfszlkk"),
    If("cdzs", "cdzs"),
    If("sfcyfw", "sfcyfw"),
    If("sftgzsfw", "sftgzsfw"),
    If("sftgqxfw", "sftgqxfw"),
    If("sftgcsfw", "sftgcsfw"),
    If("sftgjyfw", "sftgjyfw"),
    If("mj", "mj"),
    If("sftgcshfw", "sftgcshfw"),
    If("xzqhdm", "xzqhdm"),
    If("synx", "synx"),
    If("lyxt", "lyxt"),
    If("load_time", "load_time"),
    If("all_col_pk", "all_col_pk"),
    If("section_code_list", "ssldbh", in_list=True),
    If("section_code_list", "section_code", in_list=True),
)


class DwdLcztFwqjcxxMapper(OdsListMapper):
    """Java: ``interface DwdLcztFwqjcxxMapper``."""

    table = "dwd_lczt_fwqjcxx"
    select_vo = SELECT_DWD_LCZT_FWQJCXX_VO
    entity_cls = DwdLcztFwqjcxx
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.fwqmc"
    detail_column = "agent_pk"

    # Java: List<DwdLcztFwqjcxx> selectDwdLcztFwqjcxxListNew(DwdLcztFwqjcxx x)
    def select_list_new(self, query):
        """不分页：大屏 / 下拉框用的轻量投影。"""
        sql, params = assemble_list(
            SELECT_DWD_LCZT_FWQJCXX_NEW_VO, self.table, CONDITIONS_NEW, query
        )
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    def delete_dwd_lczt_fwqjcxx_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "agent_pk", entity_ids)


__all__ = ["DwdLcztFwqjcxxMapper", "RESULT_COLUMNS", "CONDITIONS"]
