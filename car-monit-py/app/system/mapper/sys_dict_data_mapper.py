"""字典数据表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDictDataMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/SysDictDataMapper.xml

XML 里共 11 条 statement，接口也正好 11 个方法，**严格 1:1**：

    ==========================  ===========================
    statement                    Python
    ==========================  ===========================
    selectDictDataList           :meth:`select_dict_data_list`
    selectDictDataByType         :meth:`select_dict_data_by_type`
    selectDictDataByTypeMore     :meth:`select_dict_data_by_type_more`
    selectDictLabel              :meth:`select_dict_label`
    selectDictDataById           :meth:`select_dict_data_by_id`
    countDictDataByType          :meth:`count_dict_data_by_type`
    deleteDictDataById           :meth:`delete_dict_data_by_id`
    deleteDictDataByIds          :meth:`delete_dict_data_by_ids`
    insertDictData               :meth:`insert_dict_data`
    updateDictData               :meth:`update_dict_data`
    updateDictDataType           :meth:`update_dict_data_type`
    ==========================  ===========================

``selectDictDataList`` 有两个调用方，分页只在其中一个生效
---------------------------------------------------------
``SysDictDataController#list`` 先 ``startPage()`` 再调它 -> 走
:func:`~app.common.core.page.page_helper.take_page` 的分页分支。

``SysDictDataServiceImpl#selectDictDataMap`` / ``#selectDictDataLaleMap`` 直接调它，
**没有** ``startPage()`` -> ``take_page()`` 返回 ``None`` -> 单条不分页查询。
这正是 PageHelper 的语义（"分页参数只对紧随其后的第一条 select 生效"），所以本模块
不需要为这两个调用方加开关。

``selectDictDataByTypeMore`` 的 ``<foreach collection="dictTypes.split(',')"``
------------------------------------------------------------------------------
集合表达式是**在 OGNL 里**对字符串调 ``split``，不是传进来的 List。等价于
``dict_type in ('a','b')``。两个细节：

1. Java 的 ``String.split`` 会丢掉**尾部空串**，所以 ``"a,b,"`` 拆成 ``["a","b"]``；
   Python 的 ``str.split`` 会多出一个 ``""``。用
   :func:`app.common.utils.string_utils.split_regex` 才等价。
2. ``","``（只有分隔符）在 Java 里拆成**长度 0** 的数组 -> ``<foreach>`` 拼出
   ``in ()`` -> MySQL 语法错。照抄，不"修"成 ``in (null)``。

``selectDictLabel`` 没有 ``limit``
----------------------------------
``select dict_label from sys_dict_data where dict_type = ? and dict_value = ?``
—— ``resultType="String"`` + 没有 ``limit 1``。同一个 ``(type, value)`` 有两条记录时
MyBatis 的 ``selectOne`` 会抛 ``TooManyResultsException``（HTTP 500）。这里保持
"取第一行"会让错误被静默吞掉，所以 Python 侧**显式**在多于一行时抛
``AttributeError`` —— 与 500 的最终表现一致。

``insertDictData`` 同样**没有** ``useGeneratedKeys``
----------------------------------------------------
所以插入后 ``dict.dictCode`` 仍是 ``null``（对比 ``insertPost`` / ``insertNotice``）。
不要顺手补 ``lastrowid`` 回写，见 :mod:`app.system.mapper.sys_dict_type_mapper`
里的同类说明。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.common.utils.string_utils import split_regex
from app.config.database import session_scope
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysDictDataMapper.xml -> ``<sql id="selectDictDataVo">``.
SELECT_DICT_DATA_VO = """
        select dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark 
		from sys_dict_data
"""

#: Verbatim from SysDictDataMapper.xml -> ``<select id="selectDictDataByType">``.
#: ``status = '0'`` 是写死的 —— 停用的字典项不进缓存，也就不会出现在下拉框里。
_SELECT_DICT_DATA_BY_TYPE = (
    SELECT_DICT_DATA_VO + " where status = '0' and dict_type = :dict_type order by dict_sort asc\n"
)

#: Verbatim from SysDictDataMapper.xml -> ``<select id="selectDictLabel">``.
_SELECT_DICT_LABEL = (
    "select dict_label from sys_dict_data\n"
    "\t\twhere dict_type = :dict_type and dict_value = :dict_value\n"
)

#: Verbatim from SysDictDataMapper.xml -> ``<select id="selectDictDataById">`` 的 where.
_SELECT_DICT_DATA_BY_ID_WHERE = "where dict_code = :dict_code"

#: Verbatim from SysDictDataMapper.xml -> ``<select id="countDictDataByType">``.
_COUNT_DICT_DATA_BY_TYPE = "select count(1) from sys_dict_data where dict_type=:dict_type"

#: Verbatim from SysDictDataMapper.xml -> ``<delete id="deleteDictDataById">``.
_DELETE_DICT_DATA_BY_ID = "delete from sys_dict_data where dict_code = :dict_code"

#: Verbatim from SysDictDataMapper.xml -> ``<update id="updateDictDataType">``.
_UPDATE_DICT_DATA_TYPE = "update sys_dict_data set dict_type = :new_dict_type where dict_type = :old_dict_type"

#: Verbatim from SysDictDataMapper.xml -> ``<select id="selectDictDataList">`` 的排序.
_ORDER_BY_DICT_SORT = "order by dict_sort asc"

#: ``insertDictData`` 里带 ``<if>`` 的列，顺序与 XML 一致；``create_time`` 无条件。
#: 第三项 ``require_text`` 对应 ``!= null and != ''``；``dict_sort`` / ``status`` 只有 ``!= null``。
_INSERT_DICT_DATA_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("dict_sort", "dict_sort", False),
    ("dict_label", "dict_label", True),
    ("dict_value", "dict_value", True),
    ("dict_type", "dict_type", True),
    ("css_class", "css_class", True),
    ("list_class", "list_class", True),
    ("is_default", "is_default", True),
    ("status", "status", False),
    ("remark", "remark", True),
    ("create_by", "create_by", True),
)

#: ``updateDictData`` 的 ``<set>`` 分支，顺序与 XML 一致。
#: ``dict_sort`` / ``css_class`` / ``list_class`` / ``status`` / ``remark`` 只有 ``!= null``。
_UPDATE_DICT_DATA_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("dict_sort", "dict_sort", False),
    ("dict_label", "dict_label", True),
    ("dict_value", "dict_value", True),
    ("dict_type", "dict_type", True),
    ("css_class", "css_class", False),
    ("list_class", "list_class", False),
    ("is_default", "is_default", True),
    ("status", "status", False),
    ("remark", "remark", False),
    ("update_by", "update_by", True),
)

#: ``selectDictDataVo`` 实际投影的 12 列（``remark`` 也在里面，靠自动映射补上）。
_DICT_DATA_COLUMNS: Tuple[str, ...] = (
    "dict_code",
    "dict_sort",
    "dict_label",
    "dict_value",
    "dict_type",
    "css_class",
    "list_class",
    "is_default",
    "status",
    "create_by",
    "create_time",
    "remark",
)


class SysDictDataMapper:
    """Java: ``interface SysDictDataMapper``."""

    # Java: List<SysDictData> selectDictDataList(SysDictData dictData)
    def select_dict_data_list(self, dict_data: SysDictData) -> List[SysDictData]:
        """字典数据列表。有 ``startPage()`` 就分页，没有就整表（见模块 docstring）。"""
        data_sql, params = _build_dict_data_list_sql(dict_data)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_dict_data(row, list(_DICT_DATA_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<SysDictData> selectDictDataByType(String dictType)
    def select_dict_data_by_type(self, dict_type: Optional[str]) -> List[SysDictData]:
        """只返回 ``status = '0'`` 的项，按 ``dict_sort`` 升序（缓存回源的唯一入口）。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_DICT_DATA_BY_TYPE), {"dict_type": dict_type})
            keys = list(result.keys())
            return [_map_dict_data(row, keys) for row in result.all()]

    # Java: List<SysDictData> selectDictDataByTypeMore(String dictTypes)
    def select_dict_data_by_type_more(self, dict_types: Optional[str]) -> List[SysDictData]:
        """多类型查询（``dict_type in (...)``），按 ``dict_type, dict_sort`` 升序。"""
        values = _java_split(dict_types)
        clause, params = _in_clause("dict_type", values, "t")
        sql = (
            SELECT_DICT_DATA_VO
            + " where status = '0' and "
            + clause
            + "\n\t\torder by dict_type,dict_sort asc\n"
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            return [_map_dict_data(row, keys) for row in result.all()]

    # Java: String selectDictLabel(@Param("dictType") String, @Param("dictValue") String)
    def select_dict_label(self, dict_type: Optional[str], dict_value: Optional[str]) -> Optional[str]:
        """没有 ``limit``；多于一行时 Java 的 ``selectOne`` 抛异常，这里同样抛。"""
        with session_scope() as session:
            rows = session.execute(
                text(_SELECT_DICT_LABEL), {"dict_type": dict_type, "dict_value": dict_value}
            ).all()
        if not rows:
            return None
        if len(rows) > 1:
            # Java: org.apache.ibatis.exceptions.TooManyResultsException
            raise AttributeError(
                "org.apache.ibatis.exceptions.TooManyResultsException: "
                f"Expected one result (or null) to be returned by selectOne(), but found: {len(rows)}"
            )
        return rows[0][0]

    # Java: SysDictData selectDictDataById(Long dictCode)
    def select_dict_data_by_id(self, dict_code: int) -> Optional[SysDictData]:
        sql = SELECT_DICT_DATA_VO + " " + _SELECT_DICT_DATA_BY_ID_WHERE
        with session_scope() as session:
            result = session.execute(text(sql), {"dict_code": dict_code})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_dict_data(rows[0], keys)

    # Java: int countDictDataByType(String dictType)
    def count_dict_data_by_type(self, dict_type: Optional[str]) -> int:
        """删除字典类型前的"是否已分配"判定。注意**不**过滤 ``status``。"""
        with session_scope() as session:
            value = session.execute(text(_COUNT_DICT_DATA_BY_TYPE), {"dict_type": dict_type}).scalar()
        return int(value or 0)

    # Java: int deleteDictDataById(Long dictCode)
    def delete_dict_data_by_id(self, dict_code: int) -> int:
        """Java 侧没有调用方（Service 只用批量版），按迁移原则第 4 条照留。"""
        with session_scope() as session:
            return session.execute(text(_DELETE_DICT_DATA_BY_ID), {"dict_code": dict_code}).rowcount or 0

    # Java: int deleteDictDataByIds(Long[] dictCodes)
    def delete_dict_data_by_ids(self, dict_codes: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("dict_code", dict_codes, "p")
        with session_scope() as session:
            return session.execute(text(f"delete from sys_dict_data where {clause}"), params).rowcount or 0

    # Java: int insertDictData(SysDictData dictData)  -- **没有** useGeneratedKeys
    def insert_dict_data(self, dict_data: SysDictData) -> int:
        """动态列插入；**不回写** ``dict_data.dict_code``（XML 里没有 ``useGeneratedKeys``）。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute, column, require_text in _INSERT_DICT_DATA_COLUMNS:
            value = getattr(dict_data, attribute)
            if value is None:
                continue
            if require_text and value == "":
                continue
            columns.append(column)
            names.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        names.append("sysdate()")

        sql = f"insert into sys_dict_data({','.join(columns)})values({','.join(names)})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateDictData(SysDictData dictData)
    def update_dict_data(self, dict_data: SysDictData) -> int:
        sql, params = _build_update_sql(dict_data)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateDictDataType(@Param("oldDictType") String, @Param("newDictType") String)
    def update_dict_data_type(self, old_dict_type: Optional[str], new_dict_type: Optional[str]) -> int:
        """改字典类型名时同步改所有子项 —— 这条就是 ``sys_dict_type`` 与
        ``sys_dict_data`` 的一致性来源，也是 ``updateDictType`` 必须事务的原因。"""
        with session_scope() as session:
            return session.execute(
                text(_UPDATE_DICT_DATA_TYPE),
                {"old_dict_type": old_dict_type, "new_dict_type": new_dict_type},
            ).rowcount or 0


def _build_dict_data_list_sql(dict_data: SysDictData) -> Tuple[str, Dict[str, Any]]:
    """``selectDictDataList`` 的 ``<where>``：3 个 ``<if>`` + 固定 ``order by``。

    顺序与 XML 严格一致：``dictType``（**等值**，不是 like）-> ``dictLabel``（like）
    -> ``status``。判据是 OGNL 的 ``x != null and x != ''``。

    片段**不带**前导 ``AND``：MyBatis 的 ``<where>`` 会吃掉首个 ``AND``，这里按顺序
    ``and`` 拼接才能得到合法的 ``where a and b``。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    if _text(dict_data.dict_type):
        conditions.append("dict_type = :dict_type")
        params["dict_type"] = dict_data.dict_type

    if _text(dict_data.dict_label):
        conditions.append("dict_label like concat('%', :dict_label, '%')")
        params["dict_label"] = dict_data.dict_label

    if _text(dict_data.status):
        conditions.append("status = :status")
        params["status"] = dict_data.status

    sql = SELECT_DICT_DATA_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    sql = sql + " " + _ORDER_BY_DICT_SORT + "\n"
    return sql, params


def _build_update_sql(dict_data: SysDictData) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_dict_data set ... where dict_code = :dict_code``（Java: ``<set>``）。"""
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, column, require_text in _UPDATE_DICT_DATA_COLUMNS:
        value = getattr(dict_data, attribute)
        if value is None:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{column} = :{attribute}")
        params[attribute] = value

    sets.append("update_time = sysdate()")
    params["dict_code"] = dict_data.dict_code

    sql = "update sys_dict_data set " + ", ".join(sets) + " where dict_code = :dict_code"
    return sql, params


def _java_split(dict_types: Optional[str]) -> List[str]:
    """``<foreach collection="dictTypes.split(',')">`` 的集合表达式。

    OGNL 对 ``null`` 调 ``split`` 会抛 ``NullPointerException``（-> 500），这里保持。
    """
    if dict_types is None:
        raise AttributeError("java.lang.NullPointerException: dictTypes is null")
    return split_regex(dict_types, ",")


def _text(value: Any) -> bool:
    """``test="x != null and x != ''"`` 的等价判断（``None`` 与空串都为假）。"""
    return value is not None and value != ""


def _map_dict_data(row: Any, keys: Sequence[str]) -> SysDictData:
    """One result row -> one ``SysDictData`` (Java: ``resultMap="SysDictDataResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields = {name: values[name] for name in _DICT_DATA_COLUMNS if name in values}
    return SysDictData(**fields)


__all__ = ["SysDictDataMapper", "SELECT_DICT_DATA_VO"]
