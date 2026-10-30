"""参数配置表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysConfigMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml

XML 里共 7 条 statement，本模块**全部迁移**：``deleteConfigById`` 在 Java 侧
没有任何调用方（控制器只调 ``deleteConfigByIds``），但按迁移原则第 4 条照留。

``selectConfig`` 与 ``selectConfigList`` 是两条不同的语句
---------------------------------------------------------
``selectConfig`` 用的是 ``<sql id="sqlwhereSearch">`` 片段，只有 **2** 个条件
（``configId != null`` / ``configKey != null and != ''``），没有 ``order by``。
它是 ``selectConfigById`` 与 ``selectConfigByKey`` 共用的"按主键/按键名取单行"。

``selectConfigList`` 有 **5** 个 ``<if>``（``configName`` / ``configType`` /
``configKey`` / ``params.beginTime`` / ``params.endTime``），**也没有** ``order by``。
没有排序意味着：

* 分页的 ``LIMIT`` 结果顺序由 MySQL 决定（Java 一样，不要"顺手"补 ``order by``）；
* 语句不带 ``ORDER BY`` 时 PageHelper 会把客户端的 ``orderByColumn`` /
  ``isAsc`` 追加进来（见 :mod:`app.common.core.page.page_helper` 的
  ``_has_order_by`` 分支），所以前端点表头排序是生效的。

``insertConfig`` 不回写主键
---------------------------
``<insert id="insertConfig">`` **没有** ``useGeneratedKeys`` / ``keyProperty``
（对比 ``insertNotice`` / ``insertPost`` 都有），所以插入后 ``config.config_id``
仍是入参里的值（通常是 ``None``）。照抄 —— 补上会改变
``add`` 之后任何依赖 ``configId`` 的行为。

``updateConfig`` 里 ``remark`` 只判 ``!= null``
-----------------------------------------------
``<set>`` 里其它 5 列都是 ``!= null and != ''``，只有 ``remark`` 是
``<if test="remark != null">`` —— 于是传 ``""`` 会**清列**（写成空串而不是跳过）。
这是本模块唯一一列"空串有语义"的字段，见 ``_UPDATE_CONFIG_COLUMNS``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_config import SysConfig
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysConfigMapper.xml -> ``<sql id="selectConfigVo">``.
SELECT_CONFIG_VO = """
        select config_id, config_name, config_key, config_value, config_type, create_by, create_time, update_by, update_time, remark 
		from sys_config
"""

#: Verbatim from SysConfigMapper.xml -> ``<select id="checkConfigKeyUnique">`` 的 where.
_CHECK_CONFIG_KEY_UNIQUE_WHERE = "where config_key = :config_key limit 1"

#: Verbatim from SysConfigMapper.xml -> ``<delete id="deleteConfigById">``.
_DELETE_CONFIG_BY_ID = "delete from sys_config where config_id = :config_id"

#: ``insertConfig`` 里带 ``<if>`` 的列，顺序与 XML 一致；``create_time`` 无条件。
#: 六列全是 ``!= null and != ''`` —— 本语句没有"只判 null"的特例。
_INSERT_CONFIG_COLUMNS: Tuple[str, ...] = (
    "config_name",
    "config_key",
    "config_value",
    "config_type",
    "create_by",
    "remark",
)

#: ``updateConfig`` 的 ``<set>`` 分支，顺序与 XML 一致。
#: 第三项 ``require_text`` 对应 ``!= null and != ''``；``remark`` 只有 ``!= null``。
_UPDATE_CONFIG_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("config_name", "config_name", True),
    ("config_key", "config_key", True),
    ("config_value", "config_value", True),
    ("config_type", "config_type", True),
    ("update_by", "update_by", True),
    ("remark", "remark", False),
)

#: ``selectConfigVo`` 实际投影的 10 列。
#: ``SysConfigResult`` resultMap 只声明了 9 个属性（**没有** ``remark``），
#: 靠 MyBatis 的 ``autoMappingBehavior=PARTIAL`` 自动映射补上。
_CONFIG_COLUMNS: Tuple[str, ...] = (
    "config_id",
    "config_name",
    "config_key",
    "config_value",
    "config_type",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "remark",
)


class SysConfigMapper:
    """Java: ``interface SysConfigMapper``."""

    # Java: SysConfig selectConfig(SysConfig config)
    def select_config(self, config: SysConfig) -> Optional[SysConfig]:
        """``<include refid="sqlwhereSearch"/>`` —— 2 个条件，无序。

        ``selectOne`` 语义：无行返回 ``None``；有两行以上 Java 会抛
        ``TooManyResultsException``，这里只在 ``check_config_key_unique`` 处
        显式处理（那条语句自带 ``limit 1``，不会多行）。
        """
        sql, params = _build_select_config_sql(config)
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_config(rows[0], keys)

    # Java: List<SysConfig> selectConfigList(SysConfig config)
    def select_config_list(self, config: SysConfig) -> List[SysConfig]:
        """参数配置列表（``startPage()`` 之后的第一条 select，分页点在这里）。"""
        data_sql, params = _build_config_list_sql(config)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_config(row, list(_CONFIG_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: SysConfig checkConfigKeyUnique(String configKey)
    def check_config_key_unique(self, config_key: Optional[str]) -> Optional[SysConfig]:
        """Java 的入参是**键名**（不是实体），SQL 自带 ``limit 1``。"""
        sql = SELECT_CONFIG_VO + " " + _CHECK_CONFIG_KEY_UNIQUE_WHERE
        with session_scope() as session:
            result = session.execute(text(sql), {"config_key": config_key})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_config(rows[0], keys)

    # Java: int insertConfig(SysConfig config)
    def insert_config(self, config: SysConfig) -> int:
        """动态列插入；**不回写** ``config.config_id``（XML 没有 ``useGeneratedKeys``）。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute in _INSERT_CONFIG_COLUMNS:
            value = getattr(config, attribute)
            if value is None or value == "":
                continue
            columns.append(attribute)
            names.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        names.append("sysdate()")

        sql = f"insert into sys_config ({','.join(columns)}) values ({','.join(names)})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateConfig(SysConfig config)
    def update_config(self, config: SysConfig) -> int:
        sql, params = _build_update_sql(config)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteConfigById(Long configId)
    def delete_config_by_id(self, config_id: int) -> int:
        with session_scope() as session:
            return session.execute(text(_DELETE_CONFIG_BY_ID), {"config_id": config_id}).rowcount or 0

    # Java: int deleteConfigByIds(Long[] configIds)
    def delete_config_by_ids(self, config_ids: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("config_id", config_ids, "p")
        with session_scope() as session:
            return session.execute(text(f"delete from sys_config where {clause}"), params).rowcount or 0


def _build_select_config_sql(config: SysConfig) -> Tuple[str, Dict[str, Any]]:
    """``<sql id="sqlwhereSearch">`` —— 2 个 ``<if>``。

    ``configId`` 的判据是 ``!= null``（**不是** ``!= 0``）：传 ``0`` 会真的去
    ``where config_id = 0``，查不到任何行（主键从 1 开始）。
    ``configKey`` 才是 ``!= null and != ''``。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    if config.config_id is not None:
        conditions.append("config_id = :config_id")
        params["config_id"] = config.config_id
    if config.config_key is not None and config.config_key != "":
        conditions.append("config_key = :config_key")
        params["config_key"] = config.config_key

    sql = SELECT_CONFIG_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    return sql, params


def _build_config_list_sql(config: SysConfig) -> Tuple[str, Dict[str, Any]]:
    """``selectConfigList`` 的 ``<where>``；**没有** ``order by``（照抄）。

    条件判据严格照抄 OGNL 的 ``x != null and x != ''``（**不是** ``isBlank``），
    所以 ``configName = " "`` 会真的去 ``like '% %'``。

    片段**不带**前导 ``AND``：MyBatis 的 ``<where>`` 会吃掉首个 ``AND``，
    这里直接把片段按顺序 ``and`` 拼接（否则会拼出非法的 ``where AND a``）。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}
    config_params: Mapping[str, Any] = config.params or {}

    def text_equals(attribute: str, fragment: str) -> None:
        """``<if test="x != null and x != ''">``。"""
        value = getattr(config, attribute, None)
        if value is None or value == "":
            return
        conditions.append(fragment.format(name=f":{attribute}"))
        params[attribute] = value

    def param_equals(key: str, placeholder: str, fragment: str) -> None:
        """``<if test="params.x != null and params.x != ''">``.

        ``params`` 字典的键是 **camelCase**（``params[beginTime]`` 是前端传的
        原文），而 SQL 占位符用 snake_case（``:begin_time``）—— 与
        :mod:`app.system.mapper.sys_dict_type_mapper` 的写法保持一致。
        """
        value = config_params.get(key)
        if value is None or value == "":
            return
        conditions.append(fragment.format(name=f":{placeholder}"))
        params[placeholder] = value

    # 顺序与 XML 的 <if> 序列一致
    text_equals("config_name", "config_name like concat('%', {name}, '%')")
    text_equals("config_type", "config_type = {name}")
    text_equals("config_key", "config_key like concat('%', {name}, '%')")
    param_equals(
        "beginTime",
        "begin_time",
        "date_format(create_time,'%y%m%d') >= date_format({name},'%y%m%d')",
    )
    param_equals(
        "endTime",
        "end_time",
        "date_format(create_time,'%y%m%d') <= date_format({name},'%y%m%d')",
    )

    sql = SELECT_CONFIG_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    return sql, params


def _build_update_sql(config: SysConfig) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_config set ... where config_id = :config_id``（Java: ``<set>``）。

    ``update_time = sysdate()`` 是**无条件**的，所以 ``<set>`` 永不为空。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, column, require_text in _UPDATE_CONFIG_COLUMNS:
        value = getattr(config, attribute)
        if value is None:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{column} = :{attribute}")
        params[attribute] = value

    sets.append("update_time = sysdate()")
    params["config_id"] = config.config_id

    sql = "update sys_config set " + ", ".join(sets) + " where config_id = :config_id"
    return sql, params


def _map_config(row: Any, keys: Sequence[str]) -> SysConfig:
    """One result row -> one ``SysConfig`` (Java: ``resultMap="SysConfigResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields = {name: values[name] for name in _CONFIG_COLUMNS if name in values}
    return SysConfig(**fields)


__all__ = ["SysConfigMapper", "SELECT_CONFIG_VO"]
