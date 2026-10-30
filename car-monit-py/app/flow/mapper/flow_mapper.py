"""``flow`` 包 Mapper 的公共骨架.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/*.java
#               + ruoyi-system/src/main/resources/mapper/flow/*.xml

与 manager 包的三处关键差别
--------------------------
1. **7 个 Mapper 接口都不继承 ``BaseMapper``**，语句全部写在 XML 里
   （``insertFlowXxx`` / ``updateFlowXxx`` / ``deleteFlowXxx``）。所以：

   * 没有 ``MetaObjectHandler`` 自动填充 —— ``createTime`` / ``createBy`` / ``epsId`` /
     ``tenantId`` 全由 Service 自己 ``set``，没 set 就是 ``null``；
   * 没有 ``@TableId`` 的 ``ASSIGN_UUID`` —— 主键由 Service 调
     ``StringUtils.getUUID()`` 生成；
   * ``update`` 的 WHERE **只有** ``ID = #{id}``，**不带** ``del_flag = '0'``
     （与 ``PlusMapper.update_by_id`` 相反）。

   因此本类覆写 :meth:`insert` / :meth:`update_by_id`，按 XML 的
   ``<if test="x != null">`` 逐列拼装，不去碰 :class:`~app.base.mapper.plus_mapper.PlusMapper`。

2. **列名大小写不敏感地匹配**：XML 里写的是 ``t.ID`` / ``t.BILL_OID``，而 PyMySQL
   回传的列标签大小写取决于服务端/驱动，且列表语句还会带
   ``t.BACK_COL1 auitEmpName`` 这类**别名**。MyBatis 的 ``resultMap`` + ``PARTIAL``
   自动映射（见下）本身就是"按名字、忽略大小写、别名优先"的语义，
   所以这里统一用 :func:`~app.base.mapper.ods_sql.map_result_row`，
   而不是只认精确列名的 ``map_row``。

3. **``PARTIAL`` 自动映射**：``mybatis-config.xml`` 里 ``mapUnderscoreToCamelCase``
   被注释掉了，但 MyBatis-Plus 默认打开它；``autoMappingBehavior`` 默认 ``PARTIAL``
   —— ``resultMap`` **没有**声明、但 SQL 里带了别名的列，仍会按"列标签 -> 属性名"
   落进实体。本工程里有 5 个这样的属性：

   =========================  ==================================================
   属性                       列表语句里的别名
   =========================  ==================================================
   ``auitEmpName``            ``t.BACK_COL1 auitEmpName``（flow_apply_info）
   ``tenantName``             ``IFNULL(sd.dept_name,'系统默认') tenantName``
   ``flowStatus``             ``app.FLOW_STATUS flowStatus``
   ``curEmpNames``            ``app.BACK_COL1 curEmpNames``
   ``msgStatus``              ``(子查询) msgStatus``
   =========================  ==================================================

   这些属性名登记在子类的 :attr:`extra_properties` 里。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import text

from app.base.mapper.ods_sql import map_result_row
from app.config.database import session_scope
from app.manager.mapper.manager_mapper import ManagerListMapper


def execute_update(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
    """执行一条 ``<insert>`` / ``<update>`` / ``<delete>``，返回影响行数。"""
    with session_scope() as session:
        return session.execute(text(sql), params or {}).rowcount or 0


def execute_rows(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
    """执行一条 ``<select>`` 并返回全部原始行（由调用方决定怎么映射）。"""
    with session_scope() as session:
        return list(session.execute(text(sql), params or {}).all())


def execute_count(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
    """执行 ``select count(1) ...`` 并返回整数（``isExitsKey`` / ``isExitsSort``）。"""
    with session_scope() as session:
        row = session.execute(text(sql), params or {}).first()
    return 0 if row is None else int(row[0] or 0)


class FlowMapper(ManagerListMapper):
    """Java: ``interface XxxMapper``（纯 XML 语句集合）的公共部分."""

    #: ``resultMap`` **没有**声明、但列表投影会以别名带出的属性（见模块文档）。
    extra_properties: Tuple[str, ...] = ()

    #: ``<insert id="insertXxx">`` 里的 ``(属性名, 物理列名)``，顺序与 XML 一致。
    insert_columns: Tuple[Tuple[str, str], ...] = ()

    #: ``<update id="updateXxx">`` 的 ``<trim prefix="SET">`` 段，顺序与 XML 一致。
    #: **不含** ``id``（它只在 ``where ID = #{id}`` 里出现）。
    update_columns: Tuple[Tuple[str, str], ...] = ()

    # ----------------------------------------------------------------- 查询

    # Java: Xxx selectXxxById(String id)
    def map_row(self, row: Any) -> Any:
        """``resultMap`` 声明的列 + ``PARTIAL`` 自动映射的别名列。"""
        properties: Sequence[str] = (*self.result_columns, *self.extra_properties)
        return map_result_row(self.entity_cls, properties, row)

    # --------------------------------------------------------------- 写入

    # Java: int insertXxx(Xxx entity)
    def insert(self, entity: Any) -> int:
        """XML 的 ``insert``：``<if test="x != null">`` 逐列，**不**自动填充、不生成主键。"""
        columns: List[str] = []
        placeholders: List[str] = []
        params: Dict[str, Any] = {}
        for attribute, column in self.insert_columns:
            value = getattr(entity, attribute, None)
            if value is None:
                continue
            columns.append(column)
            placeholders.append(f":{column}")
            params[column] = value
        sql = (
            f"insert into {self.table} ({', '.join(columns)}) "
            f"values ({', '.join(placeholders)})"
        )
        return execute_update(sql, params)

    # Java: int updateXxx(Xxx entity)
    def update_by_id(self, entity: Any) -> int:
        """XML 的 ``update``：非 ``null`` 列进 ``SET``，WHERE 只有 ``ID = #{id}``。"""
        sets: List[str] = []
        params: Dict[str, Any] = {"id": getattr(entity, "id", None)}
        for attribute, column in self.update_columns:
            value = getattr(entity, attribute, None)
            if value is None:
                continue
            sets.append(f"{column} = :{column}")
            params[column] = value
        sql = f"update {self.table} set {', '.join(sets)} where ID = :id"
        return execute_update(sql, params)


__all__ = ["FlowMapper", "execute_count", "execute_rows", "execute_update"]
