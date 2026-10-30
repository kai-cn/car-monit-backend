"""收费站ip mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnTollStationIpMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml

``BaseMapper`` 同样**没有**调用点（只有 2 条 ``<select>``），所以不继承
:class:`~app.base.mapper.plus_mapper.PlusMapper`。

⚠ ``order by t.big_id``
-----------------------
XML 的列表语句末尾写的是 ``order by t.big_id``，而：

* ``big_id`` **不在** ``<sql id="selectOdsSzdnTollStationIpVo">`` 的投影里；
* ``OdsSzdnTollStationIp`` 实体里**没有**这个字段；
* 对比 ``OdsSzdnGantryIpMapper.xml``，那边写的是 ``order by t.id``。

也就是说这大概率是生成器留下的笔误。但只要 ``ods_szdn_toll_station_ip`` 表里真的
存在 ``big_id`` 列，MySQL 就会正常执行（排序列可以不在投影里），Java 侧因此**从未
报错**。所以这里**逐字照抄**：既不改成 ``t.id``，也不删掉。若目标库缺这一列，
Java 与本实现会以完全相同的方式抛 ``Unknown column 't.big_id'``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from sqlalchemy import text

from app.base.domain.ods_szdn_toll_station_ip import OdsSzdnTollStationIp
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope

#: Verbatim from ``<sql id="selectOdsSzdnTollStationIpVo">``.
SELECT_ODS_SZDN_TOLL_STATION_IP_VO = """
        t.id,
        t.toll_code,
        t.toll_name,
        t.org_code,
        t.ip,
        t.brand
"""

#: resultMap 声明的 6 个属性。
_RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "toll_code",
    "toll_name",
    "org_code",
    "ip",
    "brand",
)


class OdsSzdnTollStationIpMapper:
    """Java: ``interface OdsSzdnTollStationIpMapper extends BaseMapper<OdsSzdnTollStationIp>``."""

    # Java: List<OdsSzdnTollStationIp> selectOdsSzdnTollStationIpList(OdsSzdnTollStationIp x)
    def select_list(self, query: OdsSzdnTollStationIp) -> List[OdsSzdnTollStationIp]:
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

    # Java: OdsSzdnTollStationIp selectOdsSzdnTollStationIpById(Long id)
    def select_by_id(self, entity_id: int) -> Optional[OdsSzdnTollStationIp]:
        sql = (
            f"select {SELECT_ODS_SZDN_TOLL_STATION_IP_VO} "
            "from ods_szdn_toll_station_ip t where t.id = :id"
        )
        with session_scope() as session:
            row = session.execute(text(sql), {"id": entity_id}).first()
        return None if row is None else _map_row(row)


def build_list_sql(query: OdsSzdnTollStationIp) -> Tuple[str, Dict[str, Any]]:
    """``selectOdsSzdnTollStationIpList`` 的 ``WHERE 1 = 1`` 段。

    注意这里**没有** ``id`` 条件（对比 ``OdsSzdnGantryIp`` 有）—— 前端拿主键查详情
    走的是 ``/base/tollStationIp/{id}``，不靠列表过滤。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    def equals(attribute: str, column: str) -> None:
        value = getattr(query, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"and t.{column} = :{attribute}")
        params[attribute] = value

    def like(attribute: str, column: str) -> None:
        value = getattr(query, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"and t.{column} like concat('%', :{attribute}, '%')")
        params[attribute] = value

    equals("toll_code", "toll_code")
    like("toll_name", "toll_name")
    equals("org_code", "org_code")
    equals("ip", "ip")
    equals("brand", "brand")

    sql = (
        f"SELECT {SELECT_ODS_SZDN_TOLL_STATION_IP_VO} "
        "FROM ods_szdn_toll_station_ip t where 1 = 1"
    )
    if conditions:
        sql = sql + " " + " ".join(conditions)
    return sql + " order by t.big_id", params


def _map_row(row: Any) -> OdsSzdnTollStationIp:
    """One result row -> one entity (Java: ``resultMap="OdsSzdnTollStationIpResult"``)."""
    keys = list(row._mapping.keys())
    values: Mapping[str, Any] = dict(row._mapping)
    fields = {name: values[name] for name in _RESULT_COLUMNS if name in keys}
    return OdsSzdnTollStationIp(**fields)


__all__ = [
    "OdsSzdnTollStationIpMapper",
    "SELECT_ODS_SZDN_TOLL_STATION_IP_VO",
    "build_list_sql",
]
