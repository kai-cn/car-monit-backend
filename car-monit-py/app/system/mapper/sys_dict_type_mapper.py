"""字典类型表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDictTypeMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysDictTypeMapper.xml

XML 里共 9 条 statement，接口也正好 9 个方法，**严格 1:1**：

    =========================  =========================
    statement                  Python
    =========================  =========================
    selectDictTypeList         :meth:`select_dict_type_list`
    selectDictTypeAll          :meth:`select_dict_type_all`
    selectDictTypeById         :meth:`select_dict_type_by_id`
    selectDictTypeByType       :meth:`select_dict_type_by_type`
    checkDictTypeUnique        :meth:`check_dict_type_unique`
    deleteDictTypeById         :meth:`delete_dict_type_by_id`
    deleteDictTypeByIds        :meth:`delete_dict_type_by_ids`
    insertDictType             :meth:`insert_dict_type`
    updateDictType             :meth:`update_dict_type`
    =========================  =========================

``insertDictType`` **没有** ``useGeneratedKeys``
------------------------------------------------
对比 ``insertPost`` / ``insertNotice``：这两条都带 ``useGeneratedKeys="true"
keyProperty="postId|noticeId"``，插入后实体的 id 会被回填。字典类型**没有**，所以
Java 里 ``dictType.getDictId()`` 在 insert 之后**仍是 null**。

Python 侧同样**不回写** ``dict_type.dict_id``。别看到"其它 mapper 都写了
``lastrowid``"就顺手补上 —— 一旦回写，``add`` 之后再调
``checkDictTypeUnique(dict)`` 的判定就会从"新增"变成"改自己"，边界行为随之改变。

``selectDictTypeVo`` 的列清单
-----------------------------
``select dict_id, dict_name, dict_type, status, create_by, create_time, remark``
—— 只有 7 列，**没有** ``update_by`` / ``update_time``，所以查询出来的
``SysDictType.updateBy`` 恒为 ``null``（JSON 里照样输出 ``"updateBy":null``）。
``remark`` 在 ``<resultMap>`` 里没有声明，靠 MyBatis 的自动映射补上；Python 侧
一起映射（见 ``_DICT_TYPE_COLUMNS``）。

``order by create_time desc`` 由语句自带
----------------------------------------
见 :mod:`app.common.core.page.page_helper` 的 ``_has_order_by`` 分支：语句自己带
``order by`` 时**不追加**客户端的 ``orderByColumn`` / ``isAsc``
（``COMPATIBILITY.md`` §25.6，待确认 #7）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.domain.entity.sys_dict_type import SysDictType
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysDictTypeMapper.xml -> ``<sql id="selectDictTypeVo">``.
SELECT_DICT_TYPE_VO = """
        select dict_id, dict_name, dict_type, status, create_by, create_time, remark 
		from sys_dict_type
"""

#: Verbatim from SysDictTypeMapper.xml -> ``<select id="selectDictTypeById">`` 的 where.
_SELECT_DICT_TYPE_BY_ID_WHERE = "where dict_id = :dict_id"

#: Verbatim from SysDictTypeMapper.xml -> ``<select id="selectDictTypeByType">`` 的 where.
_SELECT_DICT_TYPE_BY_TYPE_WHERE = "where dict_type = :dict_type"

#: Verbatim from SysDictTypeMapper.xml -> ``<select id="checkDictTypeUnique">`` 的 where.
_CHECK_DICT_TYPE_UNIQUE_WHERE = "where dict_type = :dict_type limit 1"

#: Verbatim from SysDictTypeMapper.xml -> 两条 ``<select>`` 共用的排序.
_ORDER_BY_CREATE_TIME_DESC = "order by create_time desc"

#: Verbatim from SysDictTypeMapper.xml -> ``<delete id="deleteDictTypeById">``.
_DELETE_DICT_TYPE_BY_ID = "delete from sys_dict_type where dict_id = :dict_id"

#: ``insertDictType`` 里带 ``<if>`` 的列，顺序与 XML 一致；``create_time`` 无条件。
#: 第三项 ``require_text`` 对应 ``!= null and != ''``；``status`` 只有 ``!= null``。
_INSERT_DICT_TYPE_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("dict_name", "dict_name", True),
    ("dict_type", "dict_type", True),
    ("status", "status", False),
    ("remark", "remark", True),
    ("create_by", "create_by", True),
)

#: ``updateDictType`` 的 ``<set>`` 分支，顺序与 XML 一致。
_UPDATE_DICT_TYPE_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("dict_name", "dict_name", True),
    ("dict_type", "dict_type", True),
    ("status", "status", False),
    ("remark", "remark", False),
    ("update_by", "update_by", True),
)

#: ``selectDictTypeVo`` 实际投影的 7 列（``remark`` 靠自动映射补上）。
_DICT_TYPE_COLUMNS: Tuple[str, ...] = (
    "dict_id",
    "dict_name",
    "dict_type",
    "status",
    "create_by",
    "create_time",
    "remark",
)


class SysDictTypeMapper:
    """Java: ``interface SysDictTypeMapper``."""

    # Java: List<SysDictType> selectDictTypeList(SysDictType dictType)
    def select_dict_type_list(self, dict_type: SysDictType) -> List[SysDictType]:
        """字典类型列表。``startPage()`` 之后的第一条 select，分页点在这里。"""
        data_sql, params = _build_dict_type_list_sql(dict_type)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_dict_type(row, list(_DICT_TYPE_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<SysDictType> selectDictTypeAll()
    def select_dict_type_all(self) -> List[SysDictType]:
        """``/system/dict/type/optionselect`` 与启动时的缓存预热都走这条（不分页）。"""
        sql = SELECT_DICT_TYPE_VO + " " + _ORDER_BY_CREATE_TIME_DESC + "\n"
        with session_scope() as session:
            result = session.execute(text(sql))
            keys = list(result.keys())
            return [_map_dict_type(row, keys) for row in result.all()]

    # Java: SysDictType selectDictTypeById(Long dictId)
    def select_dict_type_by_id(self, dict_id: int) -> Optional[SysDictType]:
        """``selectOne`` 语义：无行时返回 ``None``（Java 返回 ``null``）。"""
        return self._select_one(
            SELECT_DICT_TYPE_VO + " " + _SELECT_DICT_TYPE_BY_ID_WHERE, {"dict_id": dict_id}
        )

    # Java: SysDictType selectDictTypeByType(String dictType)
    def select_dict_type_by_type(self, dict_type: Optional[str]) -> Optional[SysDictType]:
        return self._select_one(
            SELECT_DICT_TYPE_VO + " " + _SELECT_DICT_TYPE_BY_TYPE_WHERE, {"dict_type": dict_type}
        )

    # Java: SysDictType checkDictTypeUnique(String dictType)
    def check_dict_type_unique(self, dict_type: Optional[str]) -> Optional[SysDictType]:
        """``limit 1`` —— 同名多条时只取第一条（唯一索引理论上保证只有一条）。"""
        return self._select_one(
            SELECT_DICT_TYPE_VO + " " + _CHECK_DICT_TYPE_UNIQUE_WHERE, {"dict_type": dict_type}
        )

    # Java: int deleteDictTypeById(Long dictId)
    def delete_dict_type_by_id(self, dict_id: int) -> int:
        """Java 侧没有调用方（Service 只用批量版），按迁移原则第 4 条照留。"""
        with session_scope() as session:
            return session.execute(text(_DELETE_DICT_TYPE_BY_ID), {"dict_id": dict_id}).rowcount or 0

    # Java: int deleteDictTypeByIds(Long[] dictIds)
    def delete_dict_type_by_ids(self, dict_ids: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("dict_id", dict_ids, "p")
        with session_scope() as session:
            return session.execute(text(f"delete from sys_dict_type where {clause}"), params).rowcount or 0

    # Java: int insertDictType(SysDictType dictType)  -- **没有** useGeneratedKeys
    def insert_dict_type(self, dict_type: SysDictType) -> int:
        """动态列插入。

        **不回写** ``dict_type.dict_id``：XML 里没有 ``useGeneratedKeys``，Java 插入后
        主键仍是 ``null``。见模块 docstring。
        """
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute, column, require_text in _INSERT_DICT_TYPE_COLUMNS:
            value = getattr(dict_type, attribute)
            if value is None:
                continue
            if require_text and value == "":
                continue
            columns.append(column)
            names.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        names.append("sysdate()")

        sql = f"insert into sys_dict_type({','.join(columns)})values({','.join(names)})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateDictType(SysDictType dictType)
    def update_dict_type(self, dict_type: SysDictType) -> int:
        sql, params = _build_update_sql(dict_type)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    def _select_one(self, sql: str, params: Mapping[str, Any]) -> Optional[SysDictType]:
        with session_scope() as session:
            result = session.execute(text(sql), dict(params))
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_dict_type(rows[0], keys)


def _text(value: Any) -> bool:
    """``test="x != null and x != ''"`` 的等价判断（``None`` 与空串都为假）。

    **不能**换成 :func:`app.common.utils.string_utils.is_not_empty`：那个实现照抄的是
    RuoYi 的 ``StringUtils.isEmpty``，它会先 ``trim``，于是 ``dictName = " "``（单个
    空格）会被当成空串而**漏掉** ``like '% %'`` 条件 —— OGNL 里 ``" " != ''`` 是真。
    """
    return value is not None and value != ""


def _build_dict_type_list_sql(dict_type: SysDictType) -> Tuple[str, Dict[str, Any]]:
    """``selectDictTypeList`` 的 ``<where>``：5 个 ``<if>`` + 固定 ``order by``。

    顺序与 XML 严格一致：``dictName`` -> ``status`` -> ``dictType`` -> ``beginTime``
    -> ``endTime``。判据是 OGNL 的 ``x != null and x != ''``（**不是** ``isBlank``）。

    片段**不带**前导 ``AND``：MyBatis 的 ``<where>`` 会吃掉首个 ``AND`` / ``OR``，
    这里直接按顺序 ``and`` 拼接，才能拼出合法的 ``where a and b``。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    dict_name = dict_type.dict_name
    if _text(dict_name):
        conditions.append("dict_name like concat('%', :dict_name, '%')")
        params["dict_name"] = dict_name

    status = dict_type.status
    if _text(status):
        conditions.append("status = :status")
        params["status"] = status

    code = dict_type.dict_type
    if _text(code):
        conditions.append("dict_type like concat('%', :dict_type, '%')")
        params["dict_type"] = code

    # Java: <if test="params.beginTime != null and params.beginTime != ''">
    begin_time = dict_type.params.get("beginTime") if dict_type.params else None
    if _text(begin_time):
        conditions.append(
            "date_format(create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')"
        )
        params["begin_time"] = begin_time

    end_time = dict_type.params.get("endTime") if dict_type.params else None
    if _text(end_time):
        conditions.append(
            "date_format(create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')"
        )
        params["end_time"] = end_time

    sql = SELECT_DICT_TYPE_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    sql = sql + " " + _ORDER_BY_CREATE_TIME_DESC + "\n"
    return sql, params


def _build_update_sql(dict_type: SysDictType) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_dict_type set ... where dict_id = :dict_id``（Java: ``<set>``）。

    ``update_time = sysdate()`` 无条件，所以 ``<set>`` 永不为空。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, column, require_text in _UPDATE_DICT_TYPE_COLUMNS:
        value = getattr(dict_type, attribute)
        if value is None:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{column} = :{attribute}")
        params[attribute] = value

    sets.append("update_time = sysdate()")
    params["dict_id"] = dict_type.dict_id

    sql = "update sys_dict_type set " + ", ".join(sets) + " where dict_id = :dict_id"
    return sql, params


def _map_dict_type(row: Any, keys: Sequence[str]) -> SysDictType:
    """One result row -> one ``SysDictType`` (Java: ``resultMap="SysDictTypeResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields = {name: values[name] for name in _DICT_TYPE_COLUMNS if name in values}
    return SysDictType(**fields)


__all__ = ["SysDictTypeMapper", "SELECT_DICT_TYPE_VO"]
