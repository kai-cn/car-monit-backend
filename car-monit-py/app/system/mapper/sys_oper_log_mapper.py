"""操作日志 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysOperLogMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysOperLogMapper.xml

XML 里共 **5** 条 statement，本模块全部迁移。

``businessType`` 的 ``<if>`` 藏着一个 OGNL 陷阱
----------------------------------------------
XML 写的是 ``<if test="businessType != null and businessType != ''">``，而
``businessType`` 是 ``Integer``。OGNL 做 ``!=`` 比较时会先走
``OgnlOps.compareWithConversion``，对"数字 vs 字符串"统一转 ``double``；而
``OgnlOps.doubleValue("")`` 的实现是

.. code-block:: java

    String s = stringValue(value, true);
    return (s.length() == 0) ? 0.0 : Double.parseDouble(s);

也就是**空串等于 0.0**。于是 ``businessType = 0``（"其它"）时条件为
``0 != 0`` → **假**，这个筛选条件被丢掉 —— 选"其它"会查出**全部**记录。

这是 Java 的既有行为（不是本项目的笔误），照抄：``business_type != 0`` 才算生效。
``status`` 用的是 ``<if test="status != null">``，没有这个问题。

``selectOperLogList`` 自带 ``order by oper_id desc``
--------------------------------------------------
所以 PageHelper **不会**追加客户端排序（``orderByColumn`` / ``isAsc`` 被忽略），
分页的 ``LIMIT`` 永远按 ``oper_id`` 倒序切片。见
:func:`app.common.core.page.page_helper.select_page` 的 ``_has_order_by`` 分支。

``cleanOperLog`` 是 ``truncate``
-------------------------------
``<update id="cleanOperLog">`` 里是 ``truncate table sys_oper_log`` —— DDL，隐式提交，
**不自增归零以外没有任何过滤**，且无法回滚。照抄。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_oper_log import SysOperLog
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysOperLogMapper.xml -> ``<sql id="selectOperLogVo">``。
SELECT_OPER_LOG_VO = """
        select oper_id, title, business_type, method, request_method, operator_type, oper_name, dept_name, oper_url, oper_ip, oper_location, oper_param, json_result, status, error_msg, oper_time
        from sys_oper_log
"""

#: ``selectOperLogVo`` 投影的 16 列，顺序与 XML 一致。
_OPER_LOG_COLUMNS: Tuple[str, ...] = (
    "oper_id",
    "title",
    "business_type",
    "method",
    "request_method",
    "operator_type",
    "oper_name",
    "dept_name",
    "oper_url",
    "oper_ip",
    "oper_location",
    "oper_param",
    "json_result",
    "status",
    "error_msg",
    "oper_time",
)

#: Verbatim from SysOperLogMapper.xml -> ``<insert id="insertOperlog">``。
#: 插入列里**没有** ``oper_time``（值固定是 ``sysdate()``），也**没有** ``business_types``。
_INSERT_OPER_LOG = """
        insert into sys_oper_log(title, business_type, method, request_method, operator_type, oper_name, dept_name, oper_url, oper_ip, oper_location, oper_param, json_result, status, error_msg, oper_time)
        values (:title, :business_type, :method, :request_method, :operator_type, :oper_name, :dept_name, :oper_url, :oper_ip, :oper_location, :oper_param, :json_result, :status, :error_msg, sysdate())
"""

#: Verbatim from SysOperLogMapper.xml -> ``<update id="cleanOperLog">``（DDL，隐式提交）。
_CLEAN_OPER_LOG = "truncate table sys_oper_log"


class SysOperLogMapper:
    """Java: ``interface SysOperLogMapper``."""

    # Java: int insertOperlog(SysOperLog operLog)
    def insert_operlog(self, oper_log: SysOperLog) -> int:
        """写入一行操作日志；``oper_time`` 取数据库时钟（``sysdate()``）。"""
        with session_scope() as session:
            result = session.execute(
                text(_INSERT_OPER_LOG),
                {
                    "title": oper_log.title,
                    "business_type": oper_log.business_type,
                    "method": oper_log.method,
                    "request_method": oper_log.request_method,
                    "operator_type": oper_log.operator_type,
                    "oper_name": oper_log.oper_name,
                    "dept_name": oper_log.dept_name,
                    "oper_url": oper_log.oper_url,
                    "oper_ip": oper_log.oper_ip,
                    "oper_location": oper_log.oper_location,
                    "oper_param": oper_log.oper_param,
                    "json_result": oper_log.json_result,
                    "status": oper_log.status,
                    "error_msg": oper_log.error_msg,
                },
            )
            return int(result.rowcount or 0)

    # Java: List<SysOperLog> selectOperLogList(SysOperLog operLog)
    def select_oper_log_list(self, oper_log: SysOperLog) -> List[SysOperLog]:
        """操作日志列表（``startPage()`` 之后的第一条 select，分页点在这里）。"""
        data_sql, params = _build_oper_log_list_sql(oper_log)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_oper_log(_row_dict(row)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: int deleteOperLogByIds(Long[] operIds)
    def delete_oper_log_by_ids(self, oper_ids: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("oper_id", oper_ids, "p")
        with session_scope() as session:
            return session.execute(text(f"delete from sys_oper_log where {clause}"), params).rowcount or 0

    # Java: SysOperLog selectOperLogById(Long operId)
    def select_oper_log_by_id(self, oper_id: int) -> Optional[SysOperLog]:
        sql = SELECT_OPER_LOG_VO + " where oper_id = :oper_id"
        with session_scope() as session:
            rows = session.execute(text(sql), {"oper_id": oper_id}).all()
        if not rows:
            return None
        return _map_oper_log(_row_dict(rows[0]))

    # Java: void cleanOperLog()
    def clean_oper_log(self) -> None:
        with session_scope() as session:
            session.execute(text(_CLEAN_OPER_LOG))


def _build_oper_log_list_sql(oper_log: SysOperLog) -> Tuple[str, Dict[str, Any]]:
    """``selectOperLogList`` 的 ``<where>`` + 固定的 ``order by oper_id desc``。

    判据严格照抄 OGNL：``!= null and != ''``（**不 trim**，所以 ``title = " "``
    会真的去 ``like '% %'``）。唯一的例外是 ``business_type``，它作为 ``Integer``
    在 OGNL 里与 ``''`` 比较等于与 ``0`` 比较，见模块 docstring。

    片段**不带**前导 ``AND``：MyBatis 的 ``<where>`` 会吃掉首个 ``AND``，
    这里按顺序 ``and`` 拼接才能得到合法的 ``where a and b``。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}
    oper_params: Mapping[str, Any] = oper_log.params or {}

    def text_like(attribute: str, column: str) -> None:
        """``<if test="x != null and x != ''">`` + ``like concat('%', #{x}, '%')``."""
        value = getattr(oper_log, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"{column} like concat('%', :{attribute}, '%')")
        params[attribute] = value

    def param_equals(key: str, placeholder: str, fragment: str) -> None:
        """``<if test="params.x != null and params.x != ''">``（``params`` 的键是 camelCase）。"""
        value = oper_params.get(key)
        if value is None or value == "":
            return
        conditions.append(fragment.format(name=f":{placeholder}"))
        params[placeholder] = value

    # 顺序与 XML 的 <if> 序列一致
    text_like("title", "title")

    # Java: <if test="businessType != null and businessType != ''"> —— OGNL 把 '' 折成 0.0
    if oper_log.business_type is not None and oper_log.business_type != 0:
        conditions.append("business_type = :business_type")
        params["business_type"] = oper_log.business_type

    # Java: <if test="businessTypes != null and businessTypes.length > 0">
    if oper_log.business_types:
        clause, in_params = _in_clause("business_type", list(oper_log.business_types), "bt")
        conditions.append(clause)
        params.update(in_params)

    # Java: <if test="status != null"> —— 注意没有 != ''
    if oper_log.status is not None:
        conditions.append("status = :status")
        params["status"] = oper_log.status

    text_like("oper_name", "oper_name")

    param_equals(
        "beginTime",
        "begin_time",
        "date_format(oper_time,'%y%m%d') >= date_format({name},'%y%m%d')",
    )
    param_equals(
        "endTime",
        "end_time",
        "date_format(oper_time,'%y%m%d') <= date_format({name},'%y%m%d')",
    )

    sql = SELECT_OPER_LOG_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    sql = sql + " order by oper_id desc"
    return sql, params


def _row_dict(row: Any) -> Mapping[str, Any]:
    """一行结果 -> 列名到值的映射（兼容 SQLAlchemy ``Row`` 与测试里的假行）。"""
    mapping = getattr(row, "_mapping", None)
    return dict(mapping) if mapping is not None else dict(row)


def _map_oper_log(values: Mapping[str, Any]) -> SysOperLog:
    """One result row -> one ``SysOperLog`` (Java: ``resultMap="SysOperLogResult"``).

    按**列名**取值而不是按位置：``selectOperLogList`` 与 ``selectOperLogById`` 的
    投影顺序虽然相同，但 ``businessTypes`` 不在结果集里，位置映射会整体错一格。
    """
    fields = {column: values.get(column) for column in _OPER_LOG_COLUMNS if column in values}
    return SysOperLog(**fields)


__all__ = ["SysOperLogMapper", "SELECT_OPER_LOG_VO"]
