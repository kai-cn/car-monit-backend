"""``manager`` 包「代码生成器模板」Mapper 的公共骨架.

# Migrated from: (no single Java source) -- faithful re-implementation of the
#   ``ruoyi-generator`` template that produced every ``<Table>Mapper.xml`` in
#   ``ruoyi-system/src/main/resources/mapper/manager``.

与 ``base`` 包的 ``OdsListMapper`` 的差异
-----------------------------------------
``manager`` 包的 18 份 XML 用的是**另一套模板**（同一份生成器、不同的表约定）：

.. code-block:: xml

    <select id="selectXxxList" ...>
        SELECT <include refid="selectXxxVo"/>
        FROM xxx t
        WHERE t.del_flag = '0'                 <!-- 不是 WHERE 1 = 1 -->
        <if test="a != null  and a != ''"> and t.a = #{a}</if>
        ...
        order by t.create_time desc,t.id       <!-- 双列 -->
    </select>

1. 固定前缀 ``WHERE t.del_flag = '0'``；
2. 固定排序 ``order by t.create_time desc,t.id``；
3. 实体带 ``@TableLogic`` —— ``updateById`` 要带 ``del_flag = '0'`` 条件；
4. 删除语句是 ``update ... set del_flag = '1' where id in (...)`` 而不是 ``delete``。

四份 XML 还有额外成分（用类属性表达，不写 SQL 拼串）：
``select_suffix``（``CarInfo`` 的 ``concat(sd.dept_name,' ',su.nick_name)``）、
``from_clause``（``CarInfo`` / ``CarWarningInfo`` 的 left join）、``extra_where``
（``CarInfo`` 的 ``not exists ...``）、``fragment_before``（``CarWarningInfo`` 的
``flag == 'curDate'`` 字符串等值判断与 ``<foreach>`` 多值 OR）。

两条必须照抄的地方
------------------
1. ``resultMap`` 只显式映射声明过的列；**没声明**的列不会被丢掉，而是按 MyBatis 的
   ``autoMappingBehavior=PARTIAL``（默认值）拿列名去比属性名、忽略大小写地自动映射。
   ``CarInfo`` 列表里的 ``,concat(...) createInfo`` 就是这么进响应体的。
   详见 :func:`~app.base.mapper.ods_sql.map_row`。
2. 详情语句**不带** ``del_flag`` 条件（``where t.id = #{id}``），所以已逻辑删除的
   行仍能被 ``GET /{id}`` 查出来。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Type

from sqlalchemy import text

from app.base.mapper.ods_sql import If, build_conditions, map_row
from app.base.mapper.plus_mapper import PlusMapper, logic_delete_by_id, logic_delete_by_ids
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope

#: 所有 manager XML 列表语句的固定前缀。
DEFAULT_WHERE_PREFIX = "t.del_flag = '0'"

#: 所有 manager XML 列表语句的固定排序。
DEFAULT_ORDER_BY = "t.create_time desc,t.id"

#: :meth:`ManagerListMapper.build_list_sql` 的 ``order_by`` 缺省值哨兵。
#: 用哨兵而不是 ``None``，因为 ``None`` 在 XML 语义里表示"这条语句没有 order by"。
_ORDER_BY_UNSET = object()


class ManagerListMapper:
    """Java: ``interface XxxMapper extends BaseMapper<Xxx>`` 里的 XML 语句集合."""

    #: ``@TableName("...")``
    table: str = ""
    #: ``<sql id="selectXxxVo">`` 的原文（含 ``t.`` 前缀与换行）。
    select_vo: str = ""
    #: 实体类（``BasePlusEntity`` 家族）。
    entity_cls: Type[Any] | None = None
    #: ``resultMap`` 声明的属性名，顺序与 XML 一致。
    result_columns: Tuple[str, ...] = ()
    #: ``<if>`` 列表，顺序与 XML 一致。
    conditions: Tuple[If, ...] = ()
    #: XML 末尾的 ``order by``；``None`` 表示语句**没有** order by。
    order_by: Optional[str] = DEFAULT_ORDER_BY
    #: ``FROM`` 后面的整段（表名 + 别名 + join）。``None`` -> ``f"{table} t"``。
    from_clause: Optional[str] = None
    #: ``WHERE`` 的第一段条件。``None`` -> :data:`DEFAULT_WHERE_PREFIX`。
    where_prefix: Optional[str] = DEFAULT_WHERE_PREFIX
    #: 永远拼在 ``<if>`` **之前**的静态片段（``CarInfo`` 的 ``not exists ...``）。
    extra_where: Tuple[str, ...] = ()
    #: 投影后缀（``CarInfo`` 的 ``,concat(...) createInfo``）。
    select_suffix: str = ""
    #: 详情语句的过滤列：``where t.<detail_column> = :id``。
    detail_column: str = "id"
    #: 详情语句的额外投影后缀（``CarInfo`` 的 ``,t.track_josn``）。
    detail_suffix: str = ""
    #: 详情语句的 ``FROM`` 段。``None`` -> 与列表共用 :attr:`from_clause`。
    #: 反例：``FlowName`` / ``FlowMessageInfo`` 的列表要连表，而详情只查主表。
    detail_from: Optional[str] = None

    # --------------------------------------------------------------- 查询

    # Java: List<Xxx> selectXxxList(Xxx x)
    def select_list(self, query: Any, order_by: Any = _ORDER_BY_UNSET) -> List[Any]:
        """列表（分页点在这里：``startPage()`` 之后的第一条 select）。

        ``order_by`` 只在**同一个 Mapper 有两条仅排序不同**的列表语句时传
        （``FlowListMapper`` 的 ``selectFlowListList`` / ``selectFlowListListNew``）。
        """
        data_sql, params = self.build_list_sql(query, order_by)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [self.map_row(row) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    def build_list_sql(
        self, query: Any, order_by: Any = _ORDER_BY_UNSET
    ) -> Tuple[str, Dict[str, Any]]:
        """列表 SQL —— 供单元测试直接断言（等价于读 XML）。

        ``<if>`` **逐条**处理后拼接，每个条件前面留一个 :meth:`fragment_before`
        插入点：``CarWarningInfo`` 的 4 条非常规 ``<if>`` 需要维持 XML 里的相对
        顺序（``flag`` 那两条夹在 ``carNoQuery`` 与 ``escapedType`` 之间，
        ``<foreach>`` 那两条在 ``plateColor`` 之后），而 :class:`If` 只能表达
        "一个属性 -> 一个片段"。
        """
        suffix, suffix_params = self.select_suffix_for(query)
        sql = f"SELECT {self.select_vo}{suffix} FROM {self._from()}"
        prefix = self.where_prefix
        if prefix:
            sql = f"{sql} WHERE {prefix}"
        for fragment in self.extra_where:
            sql = f"{sql} {fragment}"

        params: Dict[str, Any] = dict(suffix_params)
        pieces: List[str] = []
        for item in self.conditions:
            extra, extra_params = self.fragment_before(item.attribute, query)
            if extra:
                pieces.append(extra)
                params.update(extra_params)
            fragments, item_params = build_conditions(query, (item,))
            if fragments:
                pieces.extend(fragments)
                params.update(item_params)
        tail, tail_params = self.fragment_before(None, query)
        if tail:
            pieces.append(tail)
            params.update(tail_params)

        for fragment in pieces:
            sql = f"{sql} {fragment}"
        effective_order = self.order_by if order_by is _ORDER_BY_UNSET else order_by
        if effective_order:
            sql = sql + f" order by {effective_order}"
        return sql, params

    # Java: Xxx selectXxxById(String id)
    def select_by_id(self, entity_id: Any) -> Optional[Any]:
        """详情语句 —— 不带 ``del_flag`` 条件（与 XML 一致）。"""
        sql = (
            f"select {self.select_vo}{self.detail_suffix} from {self.detail_from or self._from()} "
            f"where t.{self.detail_column} = :id"
        )
        with session_scope() as session:
            row = session.execute(text(sql), {"id": entity_id}).first()
        return None if row is None else self.map_row(row)

    # --------------------------------------------------------------- 钩子

    def map_row(self, row: Any) -> Any:
        """Java: ``resultMap="XxxResult"`` —— 只取声明过的列，其余丢弃。

        ``manager`` 包直接调用 :func:`~app.base.mapper.ods_sql.map_row`；
        ``flow`` 包覆写它，改用大小写不敏感的 :func:`map_result_row`
        （理由见 :mod:`app.flow.mapper.flow_mapper`）。
        """
        return map_row(self.entity_cls, self.result_columns, row)

    def select_suffix_for(self, query: Any) -> Tuple[str, Dict[str, Any]]:
        """列表投影后缀（可带命名参数）。

        默认就是静态的 :attr:`select_suffix`。``FlowMessageInfoMapper`` 需要
        按 ``flag`` 动态追加一整列子查询，覆写本方法即可。
        """
        return self.select_suffix, {}

    def _from(self) -> str:
        return self.from_clause or f"{self.table} t"

    def fragment_before(
        self, anchor: Optional[str], query: Any
    ) -> Tuple[str, Dict[str, Any]]:
        """在 ``anchor`` 属性对应的 ``<if>`` **之前**插入的片段。

        ``anchor is None`` 表示所有 ``<if>`` **之后**（即 XML 的 ``order by`` 之前）。
        返回 ``(片段, 命名参数)``；默认不插任何东西。

        用于无法用 :class:`~app.base.mapper.ods_sql.If` 表达的条件：

        * ``CarWarningInfo`` 的 ``<if test="flag != null and flag == 'curDate'">``
          —— 判据是 ``flag`` 的**字符串等值**，绑定参数却是 ``flagTime``；
        * ``CarWarningInfo`` 的 ``<foreach ... separator="or">`` —— 多值 OR
          （**不是** ``in``，空列表整条跳过）。
        """
        return "", {}

    # --------------------------------------------------------------- 写入

    # Java: BaseMapper.insert(T entity)
    def insert(self, entity: Any) -> int:
        return self._plus().insert(entity)

    # Java: BaseMapper.updateById(T entity)
    def update_by_id(self, entity: Any) -> int:
        return self._plus().update_by_id(entity)

    # Java: int deleteXxxByIds(String[] ids)
    def delete_by_ids(self, entity_ids: Sequence[Any]) -> int:
        return logic_delete_by_ids(self.table, self.detail_column, entity_ids)

    # Java: int deleteXxxById(String id)
    def delete_by_id(self, entity_id: Any) -> int:
        return logic_delete_by_id(self.table, self.detail_column, entity_id)

    def _plus(self) -> PlusMapper:
        mapper = PlusMapper()
        mapper.table = self.table
        mapper.entity_cls = self.entity_cls
        mapper.columns = self.result_columns
        mapper.id_column = "id"
        mapper.id_type = getattr(self.entity_cls, "id_type", "ASSIGN_UUID")
        # Java: ``@TableLogic`` 在这些实体上 —— updateById 带 del_flag = '0'
        mapper.logic_delete_column = "del_flag"
        return mapper


__all__ = ["DEFAULT_ORDER_BY", "DEFAULT_WHERE_PREFIX", "ManagerListMapper"]
