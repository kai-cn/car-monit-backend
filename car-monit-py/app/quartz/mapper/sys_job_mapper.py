"""定时任务 mapper.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/mapper/SysJobMapper.java
# Migrated from: ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml

XML 里共 **8** 条 statement，本模块全部迁移：``selectJobVo``（sql 片段）、
``selectJobList`` / ``selectJobAll`` / ``selectJobById`` / ``deleteJobById`` /
``deleteJobByIds`` / ``updateJob`` / ``insertJob``。

``selectJobList`` **没有** ``order by``
---------------------------------------
所以 PageHelper 会把前端传来的 ``orderByColumn`` / ``isAsc`` 追加到语句末尾
（:func:`~app.common.core.page.page_helper.select_page` 的 ``_has_order_by`` 分支）。
``/monitor/job/list`` 默认走 ``order by job_id asc``，与线上一致。

``insertJob`` 是**动态列**
-------------------------
``<if test="x != null and x != ''">`` 让列本身可能缺席。这不是可选的写法，而是可观察行为：
不传 ``invokeTarget`` 时 ``invoke_target`` 列不出现，MySQL 报
``Field 'invoke_target' doesn't have a default value``（线上实测，见
``evidence/_probe_job_err_out.txt`` 第 4 行）。照抄成"按需拼列"。

``jobId != null and jobId != 0``
--------------------------------
显式给了非 0 的 ``jobId`` 就用它（``useGeneratedKeys`` 只在缺省时回填）。

事务语义（``session`` 参数）
---------------------------
Java 的 ``SysJobServiceImpl`` 每个方法都挂 ``@Transactional(rollbackFor = Exception.class)``，
``insertJob`` 里"先落库、再注册调度"是一次事务：调度失败时**插入的那行会被回滚**
（线上以 ``misfirePolicy='9'`` 验证过：报错后数据库里没有任何残留行）。

Python 没有声明式事务，``session_scope()`` 也不支持嵌套。本模块因此给每个方法加了一个
可选的 ``session`` 关键字参数：传了就复用调用方的事务（不再提交、不再关闭），
不传就自己开一个 —— 后者与其它模块的写法完全一致。这不是"顺手改进"，
而是 :meth:`~app.quartz.service.sys_job_service.SysJobService.insert_job`
还原 ``@Transactional`` 的唯一办法。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.quartz.domain.sys_job import SysJob
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysJobMapper.xml -> ``<sql id="selectJobVo">``。
SELECT_JOB_VO = """
        select job_id, job_name, job_group, invoke_target, cron_expression, misfire_policy, concurrent, status, create_by, create_time, remark
        from sys_job
"""

#: ``selectJobVo`` 投影的 12 列，顺序与 XML 一致（``update_by`` / ``update_time`` **不在**里面 ——
#: 它们只被 ``updateJob`` 写，任何查询都没读，所以 JSON 里永远是 ``null``）。
_JOB_COLUMNS: Tuple[str, ...] = (
    "job_id",
    "job_name",
    "job_group",
    "invoke_target",
    "cron_expression",
    "misfire_policy",
    "concurrent",
    "status",
    "create_by",
    "create_time",
    "remark",
)

#: Verbatim from SysJobMapper.xml -> ``<insert id="insertJob">`` 的固定尾巴。
_INSERT_JOB_TAIL = "create_time"

#: ``updateJob`` 的 ``<set>`` 片段（顺序与 XML 一致）。``status`` 只判 ``!= null``。
_UPDATE_JOB_FIELDS: Tuple[Tuple[str, bool], ...] = (
    ("job_name", True),
    ("job_group", True),
    ("invoke_target", True),
    ("cron_expression", True),
    ("misfire_policy", True),
    ("concurrent", True),
    ("status", False),
    ("remark", True),
    ("update_by", True),
)


@contextmanager
def shared_session(external: Optional[Session] = None) -> Iterator[Session]:
    """复用调用方事务（``external`` 非空）或自建一个 :func:`session_scope`."""
    if external is not None:
        yield external
        return
    with session_scope() as session:
        yield session


class SysJobMapper:
    """Java: ``interface SysJobMapper``."""

    # Java: List<SysJob> selectJobList(SysJob job)
    def select_job_list(self, job: SysJob, session: Optional[Session] = None) -> List[SysJob]:
        """定时任务列表（``startPage()`` 之后的第一条 select，分页点在这里）。"""
        data_sql, params = _build_job_list_sql(job)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with shared_session(session) as active:
            page_list: PageList = select_page(active, count_sql, data_sql, params, page)
        mapped = [_map_job(_row_dict(row)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<SysJob> selectJobAll()
    def select_job_all(self, session: Optional[Session] = None) -> List[SysJob]:
        """全量任务 —— ``@PostConstruct init()`` 启动时重载任务用（**不分页**）。

        注意 ``init()`` 走的是这条语句，但它被调用的时机在 ``PageHelper`` 之外，
        所以即便当前有分页上下文也不受影响（这里也**没有** ``take_page()``）。
        """
        with shared_session(session) as active:
            rows = active.execute(text(SELECT_JOB_VO)).all()
        return [_map_job(_row_dict(row)) for row in rows]

    # Java: SysJob selectJobById(Long jobId)
    def select_job_by_id(self, job_id: int, session: Optional[Session] = None) -> Optional[SysJob]:
        sql = SELECT_JOB_VO + " where job_id = :job_id"
        with shared_session(session) as active:
            rows = active.execute(text(sql), {"job_id": job_id}).all()
        if not rows:
            return None
        return _map_job(_row_dict(rows[0]))

    # Java: int deleteJobById(Long jobId)
    def delete_job_by_id(self, job_id: int, session: Optional[Session] = None) -> int:
        with shared_session(session) as active:
            result = active.execute(
                text("delete from sys_job where job_id = :job_id"), {"job_id": job_id}
            )
            return result.rowcount or 0

    # Java: int deleteJobByIds(Long[] jobIds)
    def delete_job_by_ids(self, job_ids: Sequence[int], session: Optional[Session] = None) -> int:
        """``<foreach collection="array">`` —— 空数组拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("job_id", job_ids, "p")
        with shared_session(session) as active:
            result = active.execute(text(f"delete from sys_job where {clause}"), params)
            return result.rowcount or 0

    # Java: int updateJob(SysJob job)
    def update_job(self, job: SysJob, session: Optional[Session] = None) -> int:
        """按 ``<set>`` 的 ``<if>`` 逐列更新，末尾固定 ``update_time = sysdate()``.

        ``status`` 的判据是 ``!= null``（**没有** ``!= ''``）—— 所以传空串时 ``status = ''``
        会真的写进 ``char(1)`` 列，与 Java 一致。
        """
        assignments: List[str] = []
        params: Dict[str, Any] = {"job_id": job.job_id}
        for attribute, needs_non_empty in _UPDATE_JOB_FIELDS:
            value = getattr(job, attribute, None)
            if value is None:
                continue
            if needs_non_empty and value == "":
                continue
            assignments.append(f"{attribute} = :{attribute}")
            params[attribute] = value
        assignments.append("update_time = sysdate()")
        sql = "update sys_job set " + ", ".join(assignments) + " where job_id = :job_id"
        with shared_session(session) as active:
            result = active.execute(text(sql), params)
            return result.rowcount or 0

    # Java: int insertJob(SysJob job)  —— ``useGeneratedKeys="true" keyProperty="jobId"``
    def insert_job(self, job: SysJob, session: Optional[Session] = None) -> int:
        """插入一行任务；成功后把自增主键回填到 ``job.job_id``（Java 的 ``useGeneratedKeys``）."""
        columns: List[str] = []
        placeholders: List[str] = []
        params: Dict[str, Any] = {}

        # ``<if test="jobId != null and jobId != 0">``
        if job.job_id is not None and job.job_id != 0:
            columns.append("job_id")
            placeholders.append(":job_id")
            params["job_id"] = job.job_id

        for attribute in (
            "job_name",
            "job_group",
            "invoke_target",
            "cron_expression",
            "misfire_policy",
            "concurrent",
            "status",
            "remark",
            "create_by",
        ):
            value = getattr(job, attribute, None)
            if value is None or value == "":
                continue
            columns.append(attribute)
            placeholders.append(f":{attribute}")
            params[attribute] = value

        columns.append(_INSERT_JOB_TAIL)
        placeholders.append("sysdate()")

        sql = "insert into sys_job(%s)values(%s)" % (", ".join(columns), ", ".join(placeholders))
        with shared_session(session) as active:
            result = active.execute(text(sql), params)
            generated = getattr(result, "lastrowid", None)
            if generated:
                job.job_id = int(generated)
                return 1
            # 理论上不会走到这里（MySQL + AUTO_INCREMENT 一定有 lastrowid）；
            # 保留兜底只是为了不让 job.job_id 停在被回滚的旧值上。
            job.job_id = int(active.execute(text("select LAST_INSERT_ID()")).scalar() or 0)
            return 1


def _build_job_list_sql(job: SysJob) -> Tuple[str, Dict[str, Any]]:
    """``selectJobList`` 的 ``<where>``（**没有** ``order by``，交给 PageHelper 追加）."""
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    def text_like(attribute: str) -> None:
        """``<if test="x != null and x != ''">`` + ``like concat('%', #{x}, '%')``."""
        value = getattr(job, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"{attribute} like concat('%', :{attribute}, '%')")
        params[attribute] = value

    def text_equals(attribute: str) -> None:
        value = getattr(job, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"{attribute} = :{attribute}")
        params[attribute] = value

    # 顺序与 XML 的 <if> 序列一致
    text_like("job_name")
    text_equals("job_group")
    text_equals("status")
    text_like("invoke_target")

    sql = SELECT_JOB_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    return sql, params


def _row_dict(row: Any) -> Mapping[str, Any]:
    """一行结果 -> 列名到值的映射（兼容 SQLAlchemy ``Row`` 与测试里的假行）。"""
    mapping = getattr(row, "_mapping", None)
    return dict(mapping) if mapping is not None else dict(row)


def _map_job(values: Mapping[str, Any]) -> SysJob:
    """One result row -> one ``SysJob`` (Java: ``resultMap="SysJobResult"``).

    按**列名**取值，与 ``SysJobResult`` 的 ``<result property column>`` 一一对应。
    ``update_by`` / ``update_time`` 不在投影里，所以保持 ``None``。
    """
    fields = {column: values.get(column) for column in _JOB_COLUMNS if column in values}
    return SysJob(**fields)


__all__ = ["SysJobMapper", "SELECT_JOB_VO", "shared_session"]
