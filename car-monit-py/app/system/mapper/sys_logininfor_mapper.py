"""系统访问记录 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysLogininforMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysLogininforMapper.xml

XML 里共 **4** 条 statement，本模块全部迁移。

``insertLogininfor`` 是登录/登出/注册三条路径共用的唯一写入口；其余三条
（``selectLogininforList`` / ``deleteLogininforByIds`` / ``cleanLogininfor``）
由 ``/monitor/logininfor`` 控制器使用。

``selectLogininforList`` 的投影顺序与 ``resultMap`` 不一致
-----------------------------------------------------
XML 里 ``select`` 列是 ``info_id, user_name, ipaddr, login_location, browser, os, status,
msg, login_time``，而 resultMap 声明的是 ``infoId, userName, status, ipaddr, ...`` ——
**status 在第 7 位**，不是第 3 位。MyBatis 是按**列名**回填的，所以没问题；
Python 侧必须同样按列名取值，按位置取值会把 ``status`` 与 ``ipaddr`` 弄反。

``cleanLogininfor`` 是 ``truncate``
----------------------------------
DDL，隐式提交、无法回滚（Java 同样是 ``<update>`` 标签包 ``truncate``）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_logininfor import SysLogininfor
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysLogininforMapper.xml -> ``<select id="selectLogininforList">`` 的投影部分。
#: 顺序照抄 XML（与 resultMap 的声明顺序**不同**，见模块 docstring）。
SELECT_LOGININFOR_COLUMNS = (
    "info_id, user_name, ipaddr, login_location, browser, os, status, msg, login_time"
)

#: 实际可回填到实体的 9 列。
_LOGININFOR_COLUMNS: Tuple[str, ...] = (
    "info_id",
    "user_name",
    "ipaddr",
    "login_location",
    "browser",
    "os",
    "status",
    "msg",
    "login_time",
)

#: Verbatim from SysLogininforMapper.xml -> ``<insert id="insertLogininfor">``.
#: ``sysdate()`` is deliberate: the audit timestamp is the **database** clock.
_INSERT_LOGININFOR = """
    insert into sys_logininfor (user_name, status, ipaddr, login_location, browser, os, msg, login_time)
    values (:user_name, :status, :ipaddr, :login_location, :browser, :os, :msg, sysdate())
"""


#: Verbatim from SysLogininforMapper.xml -> ``<update id="cleanLogininfor">``（DDL，隐式提交）。
_CLEAN_LOGININFOR = "truncate table sys_logininfor"


class SysLogininforMapper:
    """Java: ``interface SysLogininforMapper``."""

    # Java: int insertLogininfor(SysLogininfor logininfor)
    def insert_logininfor(self, logininfor: SysLogininfor) -> int:
        """Insert one audit row; returns the affected row count (MyBatis' ``int``)."""
        with session_scope() as session:
            result = session.execute(
                text(_INSERT_LOGININFOR),
                {
                    "user_name": logininfor.user_name,
                    "status": logininfor.status,
                    "ipaddr": logininfor.ipaddr,
                    "login_location": logininfor.login_location,
                    "browser": logininfor.browser,
                    "os": logininfor.os,
                    "msg": logininfor.msg,
                },
            )
            return int(result.rowcount or 0)

    # Java: List<SysLogininfor> selectLogininforList(SysLogininfor logininfor)
    def select_logininfor_list(self, logininfor: SysLogininfor) -> List[SysLogininfor]:
        """登录日志列表（``startPage()`` 之后的第一条 select，分页点在这里）。"""
        data_sql, params = _build_logininfor_list_sql(logininfor)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_logininfor(_row_dict(row)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: int deleteLogininforByIds(Long[] infoIds)
    def delete_logininfor_by_ids(self, info_ids: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("info_id", info_ids, "p")
        with session_scope() as session:
            return session.execute(text(f"delete from sys_logininfor where {clause}"), params).rowcount or 0

    # Java: void cleanLogininfor()
    def clean_logininfor(self) -> None:
        with session_scope() as session:
            session.execute(text(_CLEAN_LOGININFOR))


def _build_logininfor_list_sql(logininfor: SysLogininfor) -> Tuple[str, Dict[str, Any]]:
    """``selectLogininforList`` 的 ``<where>`` + 固定的 ``order by info_id desc``。

    判据严格照抄 OGNL 的 ``x != null and x != ''``（**不 trim**）。语句自带 ``order by``,
    所以 PageHelper **不会**追加客户端排序。

    片段**不带**前导 ``AND``：MyBatis 的 ``<where>`` 会吃掉首个 ``AND``。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}
    login_params: Mapping[str, Any] = logininfor.params or {}

    # 顺序与 XML 的 <if> 序列一致：ipaddr -> status -> userName -> beginTime -> endTime
    if logininfor.ipaddr is not None and logininfor.ipaddr != "":
        conditions.append("ipaddr like concat('%', :ipaddr, '%')")
        params["ipaddr"] = logininfor.ipaddr
    if logininfor.status is not None and logininfor.status != "":
        conditions.append("status = :status")
        params["status"] = logininfor.status
    if logininfor.user_name is not None and logininfor.user_name != "":
        conditions.append("user_name like concat('%', :user_name, '%')")
        params["user_name"] = logininfor.user_name

    begin_time = login_params.get("beginTime")
    if begin_time is not None and begin_time != "":
        conditions.append("date_format(login_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')")
        params["begin_time"] = begin_time
    end_time = login_params.get("endTime")
    if end_time is not None and end_time != "":
        conditions.append("date_format(login_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')")
        params["end_time"] = end_time

    sql = f"select {SELECT_LOGININFOR_COLUMNS} from sys_logininfor"
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    sql = sql + " order by info_id desc"
    return sql, params


def _row_dict(row: Any) -> Mapping[str, Any]:
    """一行结果 -> 列名到值的映射（兼容 SQLAlchemy ``Row`` 与测试里的假行）。"""
    mapping = getattr(row, "_mapping", None)
    return dict(mapping) if mapping is not None else dict(row)


def _map_logininfor(values: Mapping[str, Any]) -> SysLogininfor:
    """One result row -> one ``SysLogininfor`` (Java: ``resultMap="SysLogininforResult"``)."""
    fields = {column: values.get(column) for column in _LOGININFOR_COLUMNS if column in values}
    return SysLogininfor(**fields)


__all__ = ["SysLogininforMapper"]
