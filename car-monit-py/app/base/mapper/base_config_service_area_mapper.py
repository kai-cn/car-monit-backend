"""服务区 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/BaseConfigServiceAreaMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/BaseConfigServiceAreaMapper.xml

XML 里共 4 条 statement，全部迁移：

=======================  ======================================  ==========================
Java                     说明                                     Python
=======================  ======================================  ==========================
``select...List``        列表（8 个 ``<if>``，**没有** order by）  :meth:`select_list`
``select...ById``        按 ``fwqbm`` 取单行                      :meth:`select_by_id`
``delete...ById``        按 ``fwqbm`` 删（物理 delete）           :meth:`delete_by_id`
``delete...ByIds``       ``<foreach>`` 批量（物理 delete）        :meth:`delete_by_ids`
=======================  ======================================  ==========================

两条 ``<update>`` 标签里写的其实是 ``delete from`` —— MyBatis 不看标签名只看 SQL，
所以执行的是**物理删除**，不是 ``@TableLogic`` 的逻辑删。照抄。

列表语句**不带** ``order by``，所以 PageHelper 会把客户端的 ``orderByColumn`` /
``isAsc`` 追加进来（前端点表头排序生效）。同理**不带** ``del_flag = '0'``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.base.domain.base_config_service_area import BaseConfigServiceArea
from app.base.mapper.plus_mapper import PlusMapper
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from ``<sql id="selectBaseConfigServiceAreaVo">``（注意 ``t.`` 前缀）。
SELECT_BASE_CONFIG_SERVICE_AREA_VO = """
        t.fwqbm,
        t.fwqmc,
        t.lon,
        t.lat,
        t.road_code,
        t.section_code,
        t.pile_no
"""

#: resultMap 声明的 7 个属性（列名 == 属性名，无别名）。
_RESULT_COLUMNS: Tuple[str, ...] = (
    "fwqbm",
    "fwqmc",
    "lon",
    "lat",
    "road_code",
    "section_code",
    "pile_no",
)


class BaseConfigServiceAreaMapper(PlusMapper):
    """Java: ``interface BaseConfigServiceAreaMapper extends BaseMapper<...>``."""

    table = "base_config_service_area"
    entity_cls = BaseConfigServiceArea
    #: ``BasePlusEntity`` 的 9 列 + 本实体的 7 列（顺序 = Java 字段声明顺序）。
    columns = (
        "id",
        "eps_id",
        "del_flag",
        "create_by",
        "create_time",
        "update_by",
        "update_time",
        "sort",
        "tenant_id",
        "fwqbm",
        "fwqmc",
        "lon",
        "lat",
        "road_code",
        "section_code",
        "pile_no",
    )

    # Java: List<BaseConfigServiceArea> selectBaseConfigServiceAreaList(BaseConfigServiceArea x)
    def select_list(self, query: BaseConfigServiceArea) -> List[BaseConfigServiceArea]:
        """列表（分页点在这里：``startPage()`` 之后的第一条 select）。"""
        data_sql, params = build_list_sql(query)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_row(row) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: BaseConfigServiceArea selectBaseConfigServiceAreaById(String fwqbm)
    def select_by_fwqbm(self, fwqbm: str) -> Optional[BaseConfigServiceArea]:
        sql = f"select {SELECT_BASE_CONFIG_SERVICE_AREA_VO} from base_config_service_area t where t.fwqbm = :fwqbm"
        with session_scope() as session:
            result = session.execute(text(sql), {"fwqbm": fwqbm})
            row = result.first()
        return None if row is None else _map_row(row)

    # Java: int deleteBaseConfigServiceAreaById(String fwqbm)
    def delete_by_fwqbm(self, fwqbm: str) -> int:
        sql = "delete from base_config_service_area where fwqbm = :fwqbm"
        with session_scope() as session:
            return session.execute(text(sql), {"fwqbm": fwqbm}).rowcount or 0

    # Java: int deleteBaseConfigServiceAreaByIds(String[] fwqbms)
    def delete_by_fwqbms(self, fwqbms: Sequence[str]) -> int:
        """``<foreach collection="array" open="(" separator="," close=")">``。

        空数组会拼出 ``where fwqbm in ()`` —— Java 侧同样是 SQL 语法错（回 code 500）。
        """
        clause, params = _in_clause("fwqbm", fwqbms, "p")
        with session_scope() as session:
            return session.execute(
                text(f"delete from base_config_service_area where {clause}"), params
            ).rowcount or 0


def build_list_sql(query: BaseConfigServiceArea) -> Tuple[str, Dict[str, Any]]:
    """``selectBaseConfigServiceAreaList`` 的 ``<where>``。

    判据严格照抄 OGNL：前 7 个 ``<if>`` 是 ``x != null and x != ''``，
    只有 ``createBy`` 是 ``x != null``（传 ``0`` 也会真的去 ``where t.create_by = 0``）。

    片段**不带**前导 ``AND``：MyBatis 的 ``<where>`` 会吃掉首个 ``AND``。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    def text_equals(attribute: str, column: str) -> None:
        value = getattr(query, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"t.{column} = :{attribute}")
        params[attribute] = value

    def value_not_null(attribute: str, column: str) -> None:
        value = getattr(query, attribute, None)
        if value is None:
            return
        conditions.append(f"t.{column} = :{attribute}")
        params[attribute] = value

    text_equals("id", "id")
    text_equals("fwqbm", "fwqbm")
    text_equals("fwqmc", "fwqmc")
    text_equals("lon", "lon")
    text_equals("lat", "lat")
    text_equals("road_code", "road_code")
    text_equals("section_code", "section_code")
    text_equals("pile_no", "pile_no")
    value_not_null("create_by", "create_by")

    sql = f"SELECT {SELECT_BASE_CONFIG_SERVICE_AREA_VO} FROM base_config_service_area t"
    if conditions:
        sql = sql + " where " + " and ".join(conditions)
    return sql + "\n", params


def _map_row(row: Any) -> BaseConfigServiceArea:
    """One result row -> one entity (Java: ``resultMap="BaseConfigServiceAreaResult"``)."""
    keys = list(row._mapping.keys())
    values: Mapping[str, Any] = dict(row._mapping)
    fields = {name: values[name] for name in _RESULT_COLUMNS if name in keys}
    return BaseConfigServiceArea(**fields)


__all__ = [
    "BaseConfigServiceAreaMapper",
    "SELECT_BASE_CONFIG_SERVICE_AREA_VO",
    "build_list_sql",
]
