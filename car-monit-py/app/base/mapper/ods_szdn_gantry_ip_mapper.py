"""省界设备ip mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnGantryIpMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryIpMapper.xml

Java 的接口是 ``extends BaseMapper<OdsSzdnGantryIp>``，但 XML 只声明了 2 条
``<select>``，Service 也只调这两个方法 —— ``BaseMapper`` 的 insert / updateById /
deleteById / selectById 在本模块**没有调用点**。所以这里不继承
:class:`~app.base.mapper.plus_mapper.PlusMapper`（继承过来只是一堆死代码）。

与 ``BaseConfigServiceAreaMapper`` 的四处差异
--------------------------------------------
1. 有 ``WHERE 1 = 1``（不是 ``<where>``）—— 所以 ``<if>`` 片段自带前导 ``and``，
   不需要"吃掉首个 AND"的处理。
2. 有 ``order by t.id`` —— PageHelper 的 ``orderByColumn`` **不会**覆盖它，
   而是在后面再拼一层（前端点表头排序对本接口**不生效**）。
3. 没有 ``del_flag``、没有租户过滤、没有审计列：这张表压根没有这些列。
4. ``gantryName`` 是模糊匹配（``like concat('%', ?, '%')``），其余是等值。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from sqlalchemy import text

from app.base.domain.ods_szdn_gantry_ip import OdsSzdnGantryIp
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope

#: Verbatim from ``<sql id="selectOdsSzdnGantryIpVo">``（注意 ``t.`` 前缀）。
SELECT_ODS_SZDN_GANTRY_IP_VO = """
        t.id,
        t.gantry_code,
        t.gantry_name,
        t.org_code,
        t.ip,
        t.brand,
        t.type
"""

#: resultMap 声明的 7 个属性（列名 == 属性名，无别名）。
_RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "gantry_code",
    "gantry_name",
    "org_code",
    "ip",
    "brand",
    "type",
)


class OdsSzdnGantryIpMapper:
    """Java: ``interface OdsSzdnGantryIpMapper extends BaseMapper<OdsSzdnGantryIp>``."""

    # Java: List<OdsSzdnGantryIp> selectOdsSzdnGantryIpList(OdsSzdnGantryIp x)
    def select_list(self, query: OdsSzdnGantryIp) -> List[OdsSzdnGantryIp]:
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

    # Java: OdsSzdnGantryIp selectOdsSzdnGantryIpById(Long id)
    def select_by_id(self, entity_id: int) -> Optional[OdsSzdnGantryIp]:
        """XML 的 ``select...ById`` —— 与 ``BaseMapper.selectById`` 无关（无逻辑删除条件）。"""
        sql = f"select {SELECT_ODS_SZDN_GANTRY_IP_VO} from ods_szdn_gantry_ip t where t.id = :id"
        with session_scope() as session:
            row = session.execute(text(sql), {"id": entity_id}).first()
        return None if row is None else _map_row(row)


def build_list_sql(query: OdsSzdnGantryIp) -> Tuple[str, Dict[str, Any]]:
    """``selectOdsSzdnGantryIpList`` 的 ``WHERE 1 = 1`` 段。

    片段**自带宽前导 ``and``**（源码就是 ``and t.xxx = #{xxx}``），因此直接拼在
    ``where 1 = 1 `` 后面；这与 ``<where>`` 的写法不同，别"顺手"改成 ``<where>``。

    ``id`` 的 OGNL 判据是 ``id != null and id != ''``。``id`` 是 ``Long``：OGNL 在
    拿数字和 ``""`` 比较时会把 ``""`` 转成 ``0``，所以 ``id = 0`` 也会被**跳过**
    （不是"发一条 ``where t.id = 0``"）。照抄这个边界。
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
        # Java: and t.xxx like concat('%', #{xxx}, '%') —— 通配符由 SQL 拼，传原始值。
        conditions.append(f"and t.{column} like concat('%', :{attribute}, '%')")
        params[attribute] = value

    # Java: <if test="id != null  and id != ''"> and t.id = #{id}</if>
    # Long 与 "" 的 OGNL 比较等价于 "!= 0"，故 0 被跳过。
    if query.id is not None and query.id != 0:
        conditions.append("and t.id = :id")
        params["id"] = query.id
    equals("gantry_code", "gantry_code")
    like("gantry_name", "gantry_name")
    equals("org_code", "org_code")
    equals("ip", "ip")
    equals("brand", "brand")
    equals("type", "type")

    sql = f"SELECT {SELECT_ODS_SZDN_GANTRY_IP_VO} FROM ods_szdn_gantry_ip t where 1 = 1"
    if conditions:
        sql = sql + " " + " ".join(conditions)
    # ``order by t.id`` 写在 XML 里，PageHelper 只在**没有** order by 时才追加客户端排序。
    return sql + " order by t.id", params


def _map_row(row: Any) -> OdsSzdnGantryIp:
    """One result row -> one entity (Java: ``resultMap="OdsSzdnGantryIpResult"``)."""
    keys = list(row._mapping.keys())
    values: Mapping[str, Any] = dict(row._mapping)
    fields = {name: values[name] for name in _RESULT_COLUMNS if name in keys}
    return OdsSzdnGantryIp(**fields)


__all__ = [
    "OdsSzdnGantryIpMapper",
    "SELECT_ODS_SZDN_GANTRY_IP_VO",
    "build_list_sql",
]
