"""GaussDB 分区维护任务（``@Component``，**无 Bean 名**）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/PartitionMaintenanceTask.java

两个 ``@Scheduled`` 方法：每月 1 号 01:00 预建未来 6 个月的分区、每周一 02:00 巡检分区。
**在 Java 里永远不会被调用** —— 整个工程没有 ``@EnableScheduling``（见
:mod:`app.settings` 的 ``app.scheduled_annotations_enabled``，与
``app.main._log_startup_state`` 的启动警告）。所以这是一个**死任务**。

迁移而不删的理由
----------------
1. 它是 ``sys_job`` 之外唯一还在写 DDL 的地方，本工程的 Python 部署若改用 GaussDB
   会直接需要这段逻辑；
2. 表/列清单（``PARTITION_TABLES``）本身就是一份"哪些是大表、按哪列分区"的文档。

三个必须点明的差异
------------------
1. **``JdbcTemplate`` -> SQLAlchemy Core**：Java 的 ``jdbcTemplate.execute(sql)`` 执行
   任意 DDL，这里用 ``session_scope()`` + ``text(sql)``。两者都**不开事务语义**
   （PostgreSQL 支持 DDL 事务，MySQL 不支持；本方法的 SQL 本来就是 PostgreSQL 方言）。
2. **``jdbcTemplate.query(sql, rs -> ...)``** 是 ``ResultSetExtractor``，回调里逐行
   ``log.info``。这里用 ``session.execute`` 拿到 ``Row`` 逐行打印，语义一致。
3. **这些 SQL 在 MySQL 上必然失败**（``CREATE TABLE ... PARTITION OF`` /
   ``pg_inherits`` 都是 GaussDB/PostgreSQL 专有）。Java 侧同样如此 —— 若真的启用
   ``@EnableScheduling``，Java 也会每天抛 6×3 条异常并被 catch 吞掉。所以这里的
   异常处理与 Java 一样"只记日志"。

Bean 名
-------
Java 是裸 ``@Component``，Bean 名 = 类名首字母小写 ``partitionMaintenanceTask``。
它**没有**出现在 ``sys_job.invoke_target`` 里；万一有人手工加一行
``partitionMaintenanceTask.createFuturePartitions()``，``JobInvokeUtil`` 是能调到它的。
所以下面仍然导出 :data:`BEAN_NAME`。
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, List, Optional

from sqlalchemy import text

from app.config.database import session_scope

logger = logging.getLogger(__name__)

#: Java: ``@Component`` 的默认 Bean 名（``AnnotationBeanNameGenerator``）。
BEAN_NAME = "partitionMaintenanceTask"

#: Java: ``private static final int PRE_CREATE_MONTHS = 6;``
PRE_CREATE_MONTHS = 6

#: Java: ``private static final String[][] PARTITION_TABLES`` —— ``(表名, 分区键字段名)``.
#:
#: 三张大表，按时间列做**月分区**。顺序即 Java 数组顺序（建分区时按此顺序逐个执行）。
PARTITION_TABLES = (
    ("ods_rt_szdn_snapshot_flow_addcode", "snapshottime"),
    ("ods_lwzxsfsj_fee_records_01", "transtime"),
    ("zdata_trail_fitting", "extime"),
)

#: Java: ``@Scheduled(cron = "0 0 1 1 * ?")`` —— 每月 1 号 01:00。
CREATE_PARTITIONS_CRON = "0 0 1 1 * ?"

#: Java: ``@Scheduled(cron = "0 0 2 * * MON")`` —— 每周一 02:00。
CHECK_PARTITION_HEALTH_CRON = "0 0 2 * * MON"


class PartitionMaintenanceTask:
    """Java: ``class PartitionMaintenanceTask``（``@Slf4j @Component``）."""

    def __init__(self, jdbc_template: Optional[Any] = None) -> None:
        # Java: @Autowired private JdbcTemplate jdbcTemplate;
        # Python 没有 JdbcTemplate：默认走 ``session_scope()``；测试可注入替身
        # （只要它有 ``execute(sql)`` 方法即可）。
        self._jdbc_template_override = jdbc_template

    @property
    def jdbc_template(self) -> Any:
        return self._jdbc_template_override

    # ------------------------------------------------------------ 执行器

    def _execute(self, sql: str) -> None:
        """Java: ``jdbcTemplate.execute(String sql)``."""
        if self._jdbc_template_override is not None:
            self._jdbc_template_override.execute(sql)
            return
        with session_scope() as session:
            session.execute(text(sql))

    def _query_partition_names(self, sql: str) -> List[str]:
        """Java: ``jdbcTemplate.query(sql, rs -> { log.info(...rs.getString("partition_name")); })``.

        ``ResultSetExtractor`` 的返回值被丢弃（``void``），回调里只打日志；
        这里返回名字列表仅为便于用例断言。
        """
        if self._jdbc_template_override is not None:
            return list(self._jdbc_template_override.query(sql) or [])
        with session_scope() as session:
            rows = session.execute(text(sql)).all()
        return [row._mapping.get("partition_name") for row in rows]

    # ------------------------------------------------------------ 建分区

    # Java: @Scheduled(cron = "0 0 1 1 * ?") public void createFuturePartitions()
    def create_future_partitions(self) -> None:
        """每月 1 号预建未来 6 个月的分区（已存在的分区会报错，按 Java 原样只记 warn）."""
        logger.info("[分区维护] 开始创建未来%s个月的分区", PRE_CREATE_MONTHS)

        current = date.today().replace(day=1)

        for offset in range(1, PRE_CREATE_MONTHS + 1):
            start_month = _plus_months(current, offset)
            end_month = _plus_months(start_month, 1)

            start_date = start_month.strftime("%Y-%m-%d")
            end_date = end_month.strftime("%Y-%m-%d")
            month_suffix = start_month.strftime("%Y%m")

            for table_name, _partition_key in PARTITION_TABLES:
                partition_name = table_name + "_p" + month_suffix
                sql = (
                    f"CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF {table_name} "
                    f"FOR VALUES FROM ('{start_date}') TO ('{end_date}')"
                )
                try:
                    self._execute(sql)
                    logger.info(
                        "[分区维护] 创建分区成功: %s (范围: %s ~ %s)",
                        partition_name,
                        start_date,
                        end_date,
                    )
                except Exception as exc:  # noqa: BLE001 - Java 同样 catch Exception
                    # 分区已存在时会报错，忽略
                    logger.warning("[分区维护] 分区可能已存在: %s - %s", partition_name, exc)

        logger.info("[分区维护] 分区创建任务完成")

    # ------------------------------------------------------------ 巡检

    # Java: @Scheduled(cron = "0 0 2 * * MON") public void checkPartitionHealth()
    def check_partition_health(self) -> None:
        """每周一 02:00 巡检分区（``pg_inherits`` 是 PostgreSQL 专有系统表）."""
        logger.info("[分区维护] 开始检查分区健康状态")

        for table_name, _partition_key in PARTITION_TABLES:
            sql = (
                "SELECT inhrelid::regclass AS partition_name "
                "FROM pg_inherits WHERE inhparent = '%s'::regclass "
                "ORDER BY partition_name" % table_name
            )
            try:
                for partition_name in self._query_partition_names(sql):
                    logger.info("[分区维护] %s 分区: %s", table_name, partition_name)
            except Exception:  # noqa: BLE001 - Java 同样 catch Exception
                logger.error("[分区维护] 检查表分区失败: %s", table_name, exc_info=True)

        logger.info("[分区维护] 分区健康检查完成")


def _plus_months(value: date, months: int) -> date:
    """``LocalDate.plusMonths``（``value`` 恒为当月 1 号，不会遇到月末溢出）."""
    total = value.year * 12 + (value.month - 1) + months
    return date(total // 12, total % 12 + 1, value.day)


__all__ = [
    "BEAN_NAME",
    "CHECK_PARTITION_HEALTH_CRON",
    "CREATE_PARTITIONS_CRON",
    "PARTITION_TABLES",
    "PRE_CREATE_MONTHS",
    "PartitionMaintenanceTask",
]
