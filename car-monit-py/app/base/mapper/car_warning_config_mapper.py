"""服务区判定规则 —— **手写** Mapper（生成器模板装不下）。

# Migrated from: com/ruoyi/base/mapper/CarWarningConfigMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/CarWarningConfigMapper.xml

与 ``base`` 包其它 20 多份 XML 相比，这一份有三处不同，因此不复用
:meth:`~app.base.mapper.ods_sql.OdsListMapper.build_list_sql` 的默认拼装：

1. ``FROM car_warning_config t **join** base_config_service_area t1 on t.fwqbm = t1.fwqbm``
   —— 投影里有一半列来自 ``t1``（``fwqmc`` / ``lon`` / ``lat`` / ``road_code`` /
   ``section_code`` / ``pile_no``）。
2. 用的是 ``<where>`` 而不是 ``where 1 = 1``：**全部条件都为空时不输出 where 关键字**
   （``where 1 = 1`` 会留下一个恒真条件）。两者结果集相同，但 SQL 文本不同，
   这里按 ``<where>`` 生成。
3. ``deleteCarWarningConfigById`` / ``ByIds`` 是**物理删除**（``delete from``），
   不是 ``update ... set del_flag = '1'``。

照抄下来的 Java 缺陷
--------------------
第 55~59 行的 ``<if>`` 写的是 ``t.lon`` / ``t.lat`` / ``t.road_code`` /
``t.section_code`` / ``t.pile_no``，但这 5 列**不在** ``car_warning_config``
表上（它们在 ``t1`` 上）。只要请求带上这 5 个参数之一，MySQL 就会报
``Unknown column 't.lon'`` -> 500。Java 侧就是这个行为，这里不修。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import text

from app.base.domain.car_warning_config import CarWarningConfig
from app.base.mapper.ods_sql import If, OdsListMapper, map_row
from app.config.database import session_scope

#: Verbatim from ``<sql id="selectCarWarningConfigVo">``（``t.`` 与 ``t1.`` 混排）。
SELECT_CAR_WARNING_CONFIG_VO = """
        t.id,
        t.gantry_code_in,
        t.gantry_name_in,
        t.gantry_code_out,
        t.gantry_name_out,
        t.time_span,
        t.remark,
        t.fwqbm,
        t1.fwqmc,
        t1.lon,
        t1.lat,
        t1.road_code,
        t1.section_code,
        t1.pile_no
    
"""

#: ``FROM`` 子句（含 join）—— 列表与详情**共用**。
FROM_CLAUSE = (
    "car_warning_config t "
    "join base_config_service_area t1 on t.fwqbm = t1.fwqbm"
)

#: resultMap 声明的 14 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "gantry_code_in",
    "gantry_name_in",
    "gantry_code_out",
    "gantry_name_out",
    "time_span",
    "fwqbm",
    "fwqmc",
    "lon",
    "lat",
    "road_code",
    "section_code",
    "pile_no",
    "remark",
)

#: ``selectCarWarningConfigList`` 的 13 条 ``<if>``。
#:
#: 有 5 条刻意指向 ``t.lon`` 等不存在的列（见模块文档），**不要**"修好"它们。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("gantry_code_in", "gantry_code_in"),
    If("gantry_name_in", "gantry_name_in", like=True),
    If("gantry_code_out", "gantry_code_out"),
    If("gantry_name_out", "gantry_name_out", like=True),
    If("time_span", "time_span", null_only=True),
    If("fwqbm", "fwqbm"),
    If("fwqmc", "fwqmc", like=True, template="and t1.fwqmc like concat('%', {p}, '%')"),
    If("lon", "lon"),
    If("lat", "lat"),
    If("road_code", "road_code"),
    If("section_code", "section_code"),
    If("pile_no", "pile_no"),
)


class CarWarningConfigMapper(OdsListMapper):
    """Java: ``interface CarWarningConfigMapper extends BaseMapper<CarWarningConfig>``."""

    table = "car_warning_config"
    select_vo = SELECT_CAR_WARNING_CONFIG_VO
    entity_cls = CarWarningConfig
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    # XML 里没有 order by —— PageHelper 会追加客户端排序。
    order_by = None
    detail_column = "id"
    # Java: ``@TableId(value = "id", type = IdType.ASSIGN_UUID)``
    id_type = "ASSIGN_UUID"

    # Java: List<CarWarningConfig> selectCarWarningConfigList(CarWarningConfig x)
    def build_list_sql(self, query: Any) -> Tuple[str, Dict[str, Any]]:
        """``<where>`` 语义：无任何条件时**不输出** ``where`` 关键字。"""
        fragments, params = self._build_fragments(query)
        sql = f"SELECT {self.select_vo} FROM {FROM_CLAUSE}"
        if fragments:
            sql = sql + " where " + " ".join(fragments)
        return sql, params

    # Java: CarWarningConfig selectCarWarningConfigById(String id)
    def select_by_id(self, entity_id: Any) -> Optional[CarWarningConfig]:
        sql = (
            f"select {self.select_vo} from {FROM_CLAUSE} "
            f"where t.{self.detail_column} = :id"
        )
        with session_scope() as session:
            row = session.execute(text(sql), {"id": entity_id}).first()
        return None if row is None else map_row(self.entity_cls, self.result_columns, row)

    def _build_fragments(self, query: Any) -> Tuple[List[str], Dict[str, Any]]:
        """等价于 ``build_conditions``，但剥掉每条片段开头的 ``and``（``<where>`` 行为）。"""
        from app.base.mapper.ods_sql import build_conditions

        fragments, params = build_conditions(query, self.conditions)
        stripped = [_strip_leading_and(fragment) for fragment in fragments]
        return stripped, params

    # -------------------------------------------------------------- 物理删除

    # Java: int deleteCarWarningConfigById(String id)
    def delete_car_warning_config_by_id(self, entity_id: str) -> int:
        sql = f"delete from {self.table} where {self.detail_column} = :id"
        with session_scope() as session:
            return session.execute(text(sql), {"id": entity_id}).rowcount or 0

    # Java: int deleteCarWarningConfigByIds(String[] ids)
    def delete_car_warning_config_by_ids(self, entity_ids: Sequence[str]) -> int:
        """空数组 -> ``where id in ()``，MySQL 语法错误（与 Java 一致）。"""
        placeholders = ", ".join(f":id{index}" for index in range(len(entity_ids)))
        params = {f"id{index}": value for index, value in enumerate(entity_ids)}
        sql = f"delete from {self.table} where {self.detail_column} in ({placeholders})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0


def _strip_leading_and(fragment: str) -> str:
    text_ = fragment.lstrip()
    if text_.lower().startswith("and "):
        return text_[4:]
    return text_


__all__ = ["CarWarningConfigMapper", "RESULT_COLUMNS", "CONDITIONS", "FROM_CLAUSE"]
