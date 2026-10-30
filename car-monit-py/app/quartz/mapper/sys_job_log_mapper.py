"""定时任务日志 mapper.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/mapper/SysJobLogMapper.java
# Migrated from: ruoyi-quartz/src/main/resources/mapper/quartz/SysJobLogMapper.xml

XML 里共 **7** 条 statement，本模块全部迁移：``selectJobLogVo``（sql 片段）、
``selectJobLogList`` / ``selectJobLogAll`` / ``selectJobLogById`` /
``deleteJobLogById`` / ``deleteJobLogByIds`` / ``cleanJobLog`` / ``insertJobLog``。

``selectJobLogList`` **自带** ``order by create_time desc``
----------------------------------------------------------
所以 PageHelper **不会**追加客户端排序（``orderByColumn`` / ``isAsc`` 被忽略），
分页的 ``LIMIT`` 永远按 ``create_time`` 倒序切片 —— 线上第 1 页第 1 行就是最新的
``job_log_id``（见 ``evidence/_probe_job2_out.txt``）。

``params.beginTime`` / ``params.endTime``
-----------------------------------------
判据是 ``date_format(create_time,'%y%m%d') >= date_format(#{params.beginTime},'%y%m%d')``。
注意格式串是 **``%y%m%d``（两位年）**，Java 原文如此；不是 ``%Y%m%d``。

``cleanJobLog`` 是 ``truncate``
-------------------------------
DDL、隐式提交、**不可回滚**，且重置 ``AUTO_INCREMENT``。照抄。

``insertJobLog`` 不写 ``start_time`` / ``stop_time``
---------------------------------------------------
插入列里只有 ``create_time = sysdate()``；``SysJobLog.startTime`` / ``stopTime`` 虽然在
``AbstractQuartzJob#after`` 里被赋值，却**不会**落库（线上 1500+ 行日志里这两列全为
``NULL`` 即可印证）。照抄，不去"补全"。

事务语义见 :mod:`app.quartz.mapper.sys_job_mapper` 的说明：``session`` 参数用来复用
调用方事务。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.quartz.domain.sys_job_log import SysJobLog
from app.quartz.mapper.sys_job_mapper import shared_session
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysJobLogMapper.xml -> ``<sql id="selectJobLogVo">``。
SELECT_JOB_LOG_VO = """
        select job_log_id, job_name, job_group, invoke_target, job_message, status, exception_info, create_time
        from sys_job_log
"""

#: ``selectJobLogVo`` 投影的 8 列，顺序与 XML 一致。
#: ``start_time`` / ``stop_time`` **不在**里面 —— 所以 JSON 里它们永远是 ``null``。
_JOB_LOG_COLUMNS: Tuple[str, ...] = (
    "job_log_id",
    "job_name",
    "job_group",
    "invoke_target",
    "job_message",
    "status",
    "exception_info",
    "create_time",
)

#: Verbatim from SysJobLogMapper.xml -> ``<update id="cleanJobLog">``（DDL，隐式提交）。
_CLEAN_JOB_LOG = "truncate table sys_job_log"


class SysJobLogMapper:
    """Java: ``interface SysJobLogMapper``."""

    # Java: List<SysJobLog> selectJobLogList(SysJobLog jobLog)
    def select_job_log_list(
        self, job_log: SysJobLog, session: Optional[Session] = None
    ) -> List[SysJobLog]:
        """调度日志列表（分页点在 ``take_page()``，排序固定 ``create_time desc``）。"""
        data_sql, params = _build_job_log_list_sql(job_log)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with shared_session(session) as active:
            page_list: PageList = select_page(active, count_sql, data_sql, params, page)
        mapped = [_map_job_log(_row_dict(row)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<SysJobLog> selectJobLogAll()
    def select_job_log_all(self, session: Optional[Session] = None) -> List[SysJobLog]:
        """全量日志 —— **控制器没有调用点**。按原则第 4 条照搬，不删。"""
        with shared_session(session) as active:
            rows = active.execute(text(SELECT_JOB_LOG_VO)).all()
        return [_map_job_log(_row_dict(row)) for row in rows]

    # Java: SysJobLog selectJobLogById(Long jobLogId)
    def select_job_log_by_id(
        self, job_log_id: int, session: Optional[Session] = None
    ) -> Optional[SysJobLog]:
        """按 ID 查日志.

        线上 ``GET /monitor/jobLog/{id}`` **永远 500**，因为 ``SysJobLogController`` 的
        ``@GetMapping("/{configId}")`` 与 ``@PathVariable Long jobLogId`` 变量名不匹配，
        Spring 抛 ``MissingPathVariableException``，根本走不到这里。方法本身照搬。
        """
        sql = SELECT_JOB_LOG_VO + " where job_log_id = :job_log_id"
        with shared_session(session) as active:
            rows = active.execute(text(sql), {"job_log_id": job_log_id}).all()
        if not rows:
            return None
        return _map_job_log(_row_dict(rows[0]))

    # Java: int deleteJobLogById(Long jobLogId)
    def delete_job_log_by_id(self, job_log_id: int, session: Optional[Session] = None) -> int:
        with shared_session(session) as active:
            result = active.execute(
                text("delete from sys_job_log where job_log_id = :job_log_id"),
                {"job_log_id": job_log_id},
            )
            return result.rowcount or 0

    # Java: int deleteJobLogByIds(Long[] jobLogIds)
    def delete_job_log_by_ids(
        self, job_log_ids: Sequence[int], session: Optional[Session] = None
    ) -> int:
        """``<foreach collection="array">`` —— 空数组拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("job_log_id", job_log_ids, "p")
        with shared_session(session) as active:
            result = active.execute(text(f"delete from sys_job_log where {clause}"), params)
            return result.rowcount or 0

    # Java: void cleanJobLog()
    def clean_job_log(self, session: Optional[Session] = None) -> None:
        with shared_session(session) as active:
            active.execute(text(_CLEAN_JOB_LOG))

    # Java: void insertJobLog(SysJobLog jobLog)
    def insert_job_log(self, job_log: SysJobLog, session: Optional[Session] = None) -> int:
        """插入一行调度日志；``create_time`` 取数据库时钟（``sysdate()``）."""
        columns: List[str] = []
        placeholders: List[str] = []
        params: Dict[str, Any] = {}

        # ``<if test="jobLogId != null and jobLogId != 0">``
        if job_log.job_log_id is not None and job_log.job_log_id != 0:
            columns.append("job_log_id")
            placeholders.append(":job_log_id")
            params["job_log_id"] = job_log.job_log_id

        for attribute in (
            "job_name",
            "job_group",
            "invoke_target",
            "job_message",
            "status",
            "exception_info",
        ):
            value = getattr(job_log, attribute, None)
            if value is None or value == "":
                continue
            columns.append(attribute)
            placeholders.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        placeholders.append("sysdate()")

        sql = "insert into sys_job_log(%s)values(%s)" % (
            ", ".join(columns),
            ", ".join(placeholders),
        )
        with shared_session(session) as active:
            return int(active.execute(text(sql), params).rowcount or 0)


def _build_job_log_list_sql(job_log: SysJobLog) -> Tuple[str, Dict[str, Any]]:
    """``selectJobLogList`` 的 ``<where>`` + 固定的 ``order by create_time desc``."""
    conditions: List[str] = []
    params: Dict[str, Any] = {}
    log_params: Mapping[str, Any] = job_log.params or {}

    def text_like(attribute: str) -> None:
        value = getattr(job_log, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"{attribute} like concat('%', :{attribute}, '%')")
        params[attribute] = value

    def text_equals(attribute: str) -> None:
        value = getattr(job_log, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"{attribute} = :{attribute}")
        params[attribute] = value

    def param_bound(key: str, placeholder: str, comparator: str) -> None:
        """``<if test="params.x != null and params.x != ''">``（``params`` 的键是 camelCase）。"""
        value = log_params.get(key)
        if value is None or value == "":
            return
        conditions.append(
            "date_format(create_time,'%%y%%m%%d') %s date_format(:%s,'%%y%%m%%d')"
            % (comparator, placeholder)
        )
        params[placeholder] = value

    # 顺序与 XML 的 <if> 序列一致
    text_like("job_name")
    text_equals("job_group")
    text_equals("status")
    text_like("invoke_target")
    param_bound("beginTime", "begin_time", ">=")
    param_bound("endTime", "end_time", "<=")

    sql = SELECT_JOB_LOG_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    sql = sql + " order by create_time desc"
    return sql, params


def _row_dict(row: Any) -> Mapping[str, Any]:
    """一行结果 -> 列名到值的映射（兼容 SQLAlchemy ``Row`` 与测试里的假行）。"""
    mapping = getattr(row, "_mapping", None)
    return dict(mapping) if mapping is not None else dict(row)


def _map_job_log(values: Mapping[str, Any]) -> SysJobLog:
    """One result row -> one ``SysJobLog`` (Java: ``resultMap="SysJobLogResult"``).

    按**列名**取值；``start_time`` / ``stop_time`` 不在投影里，保持 ``None``。
    """
    fields = {column: values.get(column) for column in _JOB_LOG_COLUMNS if column in values}
    return SysJobLog(**fields)


__all__ = ["SysJobLogMapper", "SELECT_JOB_LOG_VO"]
