"""ODS 只读表（``WHERE 1 = 1`` + ``<if>``）的列表 / 详情语句拼装.

# Migrated from: (no Java source) -- faithful re-implementation of the template that
#   ruoyi-generator emits into every ``<Table>Mapper.xml`` of this project.

为什么有这个文件
----------------
``base`` 包里有二十多张 ``ods_*`` / ``zdata_*`` 表，它们的 XML 语句是**同一个模板**：

.. code-block:: xml

    <select id="selectXxxList" parameterType="...Xxx">
        SELECT <include refid="selectXxxVo"/>
        FROM xxx t
        WHERE 1 = 1
        <if test="a != null  and a != ''"> and t.a = #{a}</if>
        <if test="b != null  and b != ''"> and t.b like concat('%', #{b}, '%')</if>
        ...
        order by t.pk
    </select>

    <select id="selectXxxById" parameterType="Long">
         select <include refid="selectXxxVo"/>
         from xxx t
         where t.pk = #{pk}
    </select>

每份 XML 之间只有 4 个变量：**表名**、**投影**（``<sql>``）、**``<if>`` 列表**、
**排序列**。把拼装逻辑写在这里一次，每个 Mapper 于是退化成一串声明（与 XML 逐行
对齐），既不会让 20 份复制粘贴各自漂移，也不用改动任何可观察行为。

三条硬约束
----------
1. ``WHERE 1 = 1`` 后面的片段**自带** ``and`` —— 不做"吃掉首个 AND"的处理
   （那是 ``<where>`` 的行为，本包一条都没用到）。
2. ``order by`` **只**来自 XML。PageHelper 仅在语句本身没有 ``order by`` 时追加
   客户端 ``orderByColumn`` / ``isAsc``，所以"有/无 order by"是行为差异，不能统一。
3. 投影里出现、但 ``resultMap`` 没有映射的列（例如 ``FeeStationEnter`` 的
   ``t.id``）—— 若列名与某个属性名相同（忽略大小写），仍会按 MyBatis 的
   ``autoMappingBehavior=PARTIAL`` 自动映射进去，见 :func:`map_row`。

``<if>`` 的两种判据
-------------------
生成器按字段的 Java 类型写判据：

* ``String`` -> ``x != null  and x != ''``（空串跳过）；
* ``Long`` / ``Integer`` / ``BigDecimal`` / ``Date`` -> ``x != null``（``0`` **会**生效）。

所以 :class:`If` 的 ``null_only`` 必须逐条照抄 XML，不能按"看起来像数字"推断。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple, Type

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.base.mapper.plus_mapper import PlusMapper, logic_delete_by_id, truncate_table
from app.config.database import session_scope


class If(NamedTuple):
    """Java: 列表语句里的一条 ``<if test="...">``。

    ==============  =========================================================
    字段             含义
    ==============  =========================================================
    ``attribute``   实体属性（snake_case）；同时作为 SQL 命名参数名
    ``column``      物理列名（不带 ``t.`` 前缀）
    ``like``        片段是否用 ``like concat('%', :x, '%')``
    ``null_only``   判据是否只有 ``x != null``（数值 / 日期类型的生成器写法）
    ``template``    自定义片段模板（``{p}`` = ``:attribute``），覆盖 column + like
    ==============  =========================================================

    ``template`` 用于 ``ZdataTrailTracks`` 那种 ``STR_TO_DATE(...)`` / 不等式条件，
    这类片段在 XML 里本来就不是 ``=`` 形式。

    ``in_list`` 对应 XML 里的 ``<if> ... and t.x in <foreach ...>`` 写法：Java 的
    判据是 ``list != null and list.size() > 0``（空列表**不发**条件，不是 ``in ()``）。
    """

    attribute: str
    column: str
    like: bool = False
    null_only: bool = False
    template: Optional[str] = None
    in_list: bool = False


def build_conditions(query: Any, spec: Sequence[If]) -> Tuple[List[str], Dict[str, Any]]:
    """把声明表翻译成 ``and ...`` 片段列表 + 命名参数。

    判据与 OGNL 一致：

    * ``null_only`` 为真 -> 只跳过 ``None``（``0`` / ``0.0`` 都生效）；
    * 否则 -> ``None`` 与 ``""`` 都跳过（Java 的 ``x != ''``）。

    ``JavaString`` 字段收到数字时下游已转成字符串（见 ``domain_model._coerce_to_java_string``），
    空串判断因此仍然成立。
    """
    fragments: List[str] = []
    params: Dict[str, Any] = {}
    for item in spec:
        value = getattr(query, item.attribute, None)
        if value is None:
            continue
        if item.in_list:
            # Java: list != null and list.size() > 0 —— 空列表整条跳过。
            values = list(value)
            if not values:
                continue
            placeholders = []
            for index, element in enumerate(values):
                name = f"{item.attribute}_{index}"
                placeholders.append(f":{name}")
                params[name] = element
            fragments.append(f"and t.{item.column} in ({', '.join(placeholders)})")
            continue
        if not item.null_only and value == "":
            continue
        placeholder = f":{item.attribute}"
        if item.template is not None:
            fragments.append(item.template.format(p=placeholder))
        elif item.like:
            fragments.append(
                f"and t.{item.column} like concat('%', {placeholder}, '%')"
            )
        else:
            fragments.append(f"and t.{item.column} = {placeholder}")
        params[item.attribute] = value
    return fragments, params


def assemble_list(
    select_vo: str,
    table: str,
    spec: Sequence[If],
    query: Any,
    order_by: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """拼出 ``selectXxxList`` 的完整 SQL（含 ``order by``）。"""
    fragments, params = build_conditions(query, spec)
    sql = f"SELECT {select_vo} FROM {table} t where 1 = 1"
    if fragments:
        sql = sql + " " + " ".join(fragments)
    if order_by:
        # 单列（``"big_id"``）补 ``t.`` 前缀；已带前缀 / 多列（``"t.a, t.b"``）原样拼。
        qualified = order_by if (" " in order_by or "." in order_by) else f"t.{order_by}"
        sql = sql + f" order by {qualified}"
    return sql, params


#: ``entity_cls`` -> ``{属性名小写: Python 字段名}``，供 :func:`map_row` 的自动映射用。
_AUTO_MAPPING_CACHE: Dict[Type[Any], Dict[str, str]] = {}


def _auto_mapping_targets(entity_cls: Type[Any]) -> Dict[str, str]:
    """Java 属性名（小写） -> Python 字段名。

    ``resultMap`` 的自动映射是按**属性名**比较的，所以这里只登记 Java 侧的属性名，
    也就是 pydantic 字段的 camelCase ``alias``；``mapUnderscoreToCamelCase`` 在本项目
    是关闭的，下划线的列名（``back_col1``）**不会**被拿来匹配 ``backCol1``。
    """
    cached = _AUTO_MAPPING_CACHE.get(entity_cls)
    if cached is not None:
        return cached

    mapping: Dict[str, str] = {}
    model_fields = getattr(entity_cls, "model_fields", None) or {}
    for name, info in model_fields.items():
        alias = getattr(info, "alias", None)
        attribute = alias if isinstance(alias, str) and alias else name
        mapping.setdefault(attribute.lower(), name)
    _AUTO_MAPPING_CACHE[entity_cls] = mapping
    return mapping


def map_row(
    entity_cls: Type[Any],
    result_columns: Sequence[str],
    row: Any,
    auto_mapping: bool = True,
) -> Any:
    """Java: ``resultMap="XxxResult"`` + ``autoMappingBehavior=PARTIAL``（MyBatis 默认）。

    两步，与 MyBatis 完全一致：

    1. ``result_columns`` 里声明的列按 ``<result property=... column=...>`` 映射；
    2. **剩下的列**再做自动映射 —— 用列名去比属性名，大小写不敏感。

    第 2 步不是可选项：``selectCarInfoList`` 的投影比 ``resultMap`` 多一列
    ``,concat(sd.dept_name, ' ', su.nick_name) createInfo``，它没被声明过，却因为
    自动映射落到了 ``createInfo`` 属性上 —— 实测 Java 响应里该字段有值。早先
    "别名列一律丢弃"的判断是错的。

    ``auto_mapping=False`` 对应 ``PARTIAL`` 的例外：``resultMap`` 里一旦出现
    ``<association>`` / ``<collection>``，MyBatis 会**整体关闭**自动映射。本项目只有
    ``SysUserMapper.SysUserResult`` 与生成器的 ``GenTableResult`` 属于这种情况 ——
    ``SysUserResult`` 用 ``<association property="dept">`` 把 ``dept_name`` 送进了
    ``dept.deptName``，扁平的那个 ``SysUser.deptName`` 因此实测为 ``null``。
    """
    values: Mapping[str, Any] = dict(row._mapping)
    fields = {name: values[name] for name in result_columns if name in values}

    targets = _auto_mapping_targets(entity_cls) if auto_mapping else {}
    if targets:
        for column, value in values.items():
            if column in fields or column in result_columns:
                continue
            target = targets.get(str(column).lower())
            if target is not None and target not in fields:
                fields[target] = value
    return entity_cls(**fields)


def to_camel(name: str) -> str:
    """``escaped_amount`` -> ``escapedAmount``（Java 的属性名）。"""
    head, *rest = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest if part)


def map_result_row(entity_cls: Type[Any], properties: Sequence[str], row: Any) -> Any:
    """Java: ``resultType="..."`` 的自动映射。

    与 :func:`map_row`（``resultMap``）的区别：``resultType`` 没有显式的
    列 -> 属性声明，MyBatis 拿**列名**去匹配属性名 —— ``mapUnderscoreToCamelCase``
    打开时 ``back_col1`` 与 ``backCol1`` 都算命中，且比较**大小写不敏感**。

    ``properties`` 传的是属性名（snake_case）。查找顺序：原样 -> 驼峰别名 ->
    忽略大小写。都不是的列丢弃（与 MyBatis 一致）。

    典型用途：``sum(...) escapedAmount`` / ``count(...) number`` 这类**别名即属性名**
    的聚合语句（``getPCCarStatistics`` / ``incomeDetailList`` …）。
    """
    values: Mapping[str, Any] = dict(row._mapping)
    lowered = {str(key).lower(): value for key, value in values.items()}
    fields: Dict[str, Any] = {}
    for name in properties:
        if name in values:
            fields[name] = values[name]
            continue
        alias = to_camel(name)
        if alias in values:
            fields[name] = values[alias]
            continue
        for candidate in (name, alias):
            if candidate.lower() in lowered:
                fields[name] = lowered[candidate.lower()]
                break
    return entity_cls(**fields)


class OdsListMapper:
    """Java: ``interface XxxMapper extends BaseMapper<Xxx>`` 里的**两条 XML 语句**。

    子类只声明 :attr:`table` / :attr:`select_vo` / :attr:`entity_cls` /
    :attr:`result_columns` / :attr:`conditions` / :attr:`order_by` /
    :attr:`detail_column`，不写任何 SQL 字符串拼接。

    ``BaseMapper`` 自带的 ``insert`` / ``updateById`` / ``deleteById`` 在这些模块
    **没有调用点**（Service 只做转发），所以这里**不**继承
    :class:`~app.base.mapper.plus_mapper.PlusMapper`。
    """

    #: ``@TableName("...")``
    table: str = ""
    #: ``<sql id="selectXxxVo">`` 的原文（含 ``t.`` 前缀与换行）。
    select_vo: str = ""
    #: 实体类。
    entity_cls: Type[Any] | None = None
    #: ``resultMap`` 声明的属性名，顺序与 XML 一致。
    result_columns: Tuple[str, ...] = ()
    #: ``<if>`` 列表，顺序与 XML 一致。
    conditions: Tuple[If, ...] = ()
    #: XML 末尾的 ``order by t.???``；``None`` 表示语句**没有** order by
    #: （此时 PageHelper 会追加客户端排序）。
    order_by: Optional[str] = None
    #: 详情语句的过滤列：``where t.<detail_column> = :id``。
    detail_column: str = "big_id"
    #: ``BaseMapper`` 的主键列（``@TableId``）：``insert`` / ``updateById`` / ``deleteById``
    #: 用它。``None`` -> 与 :attr:`detail_column` 相同（绝大多数表两者一致）。
    #: 反例：``OdsLwzxsfsjFeeGantryFusion01`` 没有 ``@TableId``，MP 按字段名
    #: 自动识别出主键 ``id``，而 XML 的详情 / 删除语句用的是业务键 ``big_id``。
    pk_column: Optional[str] = None
    #: ``@TableId(type = ...)`` —— ``ods_*`` / ``dwd_*`` 实体几乎都是 ``INPUT``
    #: （主键由 ETL 写入）；只有显式申明的才用 ``ASSIGN_UUID``。
    id_type: str = "INPUT"

    # Java: List<Xxx> selectXxxList(Xxx x)
    def select_list(self, query: Any) -> List[Any]:
        """列表（分页点在这里：``startPage()`` 之后的第一条 select）。"""
        data_sql, params = self.build_list_sql(query)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [map_row(self.entity_cls, self.result_columns, row) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: Xxx selectXxxById(<pk type> pk)
    def select_by_id(self, entity_id: Any) -> Optional[Any]:
        """详情语句 —— 与 ``BaseMapper.selectById`` 无关（这些表没有逻辑删除列）。"""
        sql = (
            f"select {self.select_vo} from {self.table} t "
            f"where t.{self.detail_column} = :id"
        )
        with session_scope() as session:
            row = session.execute(text(sql), {"id": entity_id}).first()
        return None if row is None else map_row(self.entity_cls, self.result_columns, row)

    def build_list_sql(self, query: Any) -> Tuple[str, Dict[str, Any]]:
        """列表 SQL —— 供单元测试直接断言（等价于读 XML）。"""
        return assemble_list(
            self.select_vo, self.table, self.conditions, query, self.order_by
        )

    # ------------------------------------------------- BaseMapper 的两个写方法

    def insert(self, entity: Any) -> int:
        """Java: ``BaseMapper.insert(T entity)``（见 :class:`PlusMapper`）。"""
        return self._plus().insert(entity)

    def update_by_id(self, entity: Any) -> int:
        """Java: ``BaseMapper.updateById(T entity)``（非 null 列才进 SET）。"""
        return self._plus().update_by_id(entity)

    # Java: int deleteXxxById(String id)
    def delete_by_id(self, entity_id: Any) -> int:
        """XML 里的单行删除 —— 这些表都是 ``update t set del_flag='1'``（逻辑删）。"""
        return logic_delete_by_id(self.table, self.detail_column, entity_id)

    # Java: void truncateTable()
    def truncate_table(self) -> int:
        return truncate_table(self.table)

    def _plus(self) -> PlusMapper:
        """把本 Mapper 的声明转成一次性的 :class:`PlusMapper`。

        ``OdsListMapper`` **不继承** ``PlusMapper``：两者的 ``select_by_id`` 语义
        不同（这里用 XML 的 ``<sql>`` 投影 + ``detail_column``，那里用实体全列 +
        ``@TableLogic``）。只在 ``insert`` / ``updateById`` 上借用一次，避免复制
        ``NOT_NULL`` 字段策略的实现。

        ``logic_delete_column = None``：``base`` 包的实体都没有 ``@TableLogic``，
        所以 ``updateById`` 的 WHERE 只有主键，不带 ``del_flag = '0'``。
        """
        mapper = PlusMapper()
        mapper.table = self.table
        mapper.entity_cls = self.entity_cls
        mapper.columns = self.result_columns
        mapper.id_column = self.pk_column or self.detail_column
        mapper.id_type = self.id_type
        mapper.logic_delete_column = None
        return mapper


__all__ = [
    "If",
    "OdsListMapper",
    "assemble_list",
    "build_conditions",
    "map_result_row",
    "map_row",
    "to_camel",
]
