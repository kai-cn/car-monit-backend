"""门架抓拍流水分表同步任务（``@Component``，无 Bean 名）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java

按 ``snapshottime`` 月份把 GaussDB 的流水同步进 MySQL 的分表
（``ods_rt_szdn_snapshot_flow_addcode_yyyyMM``）。两个 ``@Scheduled`` 方法
（``syncIncrementalData`` 每小时、``manualFullSync`` 每 5 分钟）**永远不会触发** ——
工程没有 ``@EnableScheduling``。

**但它是可被调用的**：裸 ``@Component`` 的 Bean 名是 ``snapshotFlowSyncTask``，
所以 ``sys_job`` 里手工加一行 ``snapshotFlowSyncTask.manualIncrementalSync()``
是能跑起来的（``syncSingleMonth`` 不行：它要一个 ``AtomicInteger`` 参数，
``JobInvokeUtil`` 造不出这种类型）。

⚠ 这个任务在 Java 里**是空转的**
--------------------------------
``syncSnapshotFlowByDateRange`` 第一步就是::

    List<OdsRtSzdnSnapshotFlowAddcode> dataList = convertToEntityList(tableDataInfo.getRows());
    ...
    private List<...> convertToEntityList(List<?> rows) {
        for (Object row : rows) {
            if (row instanceof OdsRtSzdnSnapshotFlowAddcode) { list.add(...); }
        }
    }

``TableDataInfo.rows`` 声明是 ``List<?>``，Jackson 反序列化出来的是
``ArrayList<LinkedHashMap>`` —— **没有一行**是 ``OdsRtSzdnSnapshotFlowAddcode``，
于是 ``dataList`` 恒为空、立刻 ``break``，整趟同步搬 0 条数据，
``syncFullData()`` 返回 ``"全量同步完成，共同步 0 条数据"``。

Python 侧照抄这个 ``isinstance`` 判定（Forest 返回的是 ``dict``，同样不是实体），
所以两边都是空转。**不要"顺手修好"** —— 一旦真跑起来就会往分表写数据，
而这个任务从来没人验证过。见 ``COMPATIBILITY.md`` §42.4。

线程池
------
Java 用 ``ThreadPoolExecutor(4, 8, 60s, LinkedBlockingQueue(100), 命名线程,
CallerRunsPolicy)`` 并发同步各月份。Python 的 ``ThreadPoolExecutor`` 没有
core/max 之分，这里用 ``max_workers=8``（等于 Java 的上限）+ 有界队列语义靠
``submit`` 后立即 ``result()`` 的调用方式回避 —— 实际并发度不会超过 8。
"""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import OdsRtSzdnSnapshotFlowAddcode
from app.base.mapper.ods_rt_szdn_snapshot_flow_addcode_mapper import (
    OdsRtSzdnSnapshotFlowAddcodeMapper,
)
from app.base.service.forest.http_ods_rt_szdn_snapshot_flow_addcode_service import (
    HttpOdsRtSzdnSnapshotFlowAddcodeService,
)
from app.base.sharding.sharding_table_util import ShardingTableUtil
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

logger = logging.getLogger(__name__)

#: Java: ``@Component`` 的默认 Bean 名。
BEAN_NAME = "snapshotFlowSyncTask"

#: Java: ``@Scheduled(cron = "0 0 * * * ?")`` —— 每小时整点。
INCREMENTAL_CRON = "0 0 * * * ?"

#: Java: ``@Scheduled(cron = "0 */5 * * * *")`` —— 每 5 分钟。
MANUAL_FULL_SYNC_CRON = "0 */5 * * * *"

#: Java: ``private static final`` 隐式常量 —— 分页大小。
_PAGE_SIZE = 1000

#: Java: ``new ThreadPoolExecutor(4, 8, ...)`` 的**最大**线程数。
_MAX_SYNC_WORKERS = 8


class SnapshotFlowSyncTask:
    """Java: ``class SnapshotFlowSyncTask``（``@Slf4j @Component``）."""

    def __init__(
        self,
        snapshot_flow_mapper: Optional[Any] = None,
        http_service: Optional[Any] = None,
        sync_executor: Optional[Any] = None,
    ) -> None:
        # Java: @Autowired private OdsRtSzdnSnapshotFlowAddcodeMapper snapshotFlowMapper;
        self._mapper = snapshot_flow_mapper or OdsRtSzdnSnapshotFlowAddcodeMapper()
        # Java: @Resource private HttpOdsRtSzdnSnapshotFlowAddcodeService http...;
        self._http_service_override = http_service
        # Java: private ExecutorService syncExecutor;  —— @PostConstruct 里创建
        self._sync_executor_override = sync_executor
        self._sync_executor: Optional[ThreadPoolExecutor] = None

    # ------------------------------------------------------------ 依赖

    @property
    def snapshot_flow_mapper(self) -> Any:
        return self._mapper

    @property
    def http_service(self) -> Any:
        # Forest 接口在 Python 里是一组静态方法，没有实例状态。
        return self._http_service_override or HttpOdsRtSzdnSnapshotFlowAddcodeService

    @property
    def sync_executor(self) -> Any:
        if self._sync_executor_override is not None:
            return self._sync_executor_override
        if self._sync_executor is None:
            self.init()
        return self._sync_executor

    # Java: @PostConstruct public void init()
    def init(self) -> None:
        """线程池初始化（Java: ``ThreadPoolExecutor(4, 8, 60s, queue(100), 命名, CallerRuns)``）."""
        self._sync_executor = ThreadPoolExecutor(
            max_workers=_MAX_SYNC_WORKERS,
            thread_name_prefix="snapshot-sync-worker",
        )
        logger.info("【分表同步任务】线程池初始化完成")

    def shutdown(self) -> None:
        """Java: Spring 关闭时 ``ExecutorService`` 由容器回收；这里显式收尾。"""
        if self._sync_executor is not None:
            self._sync_executor.shutdown(wait=False)
            self._sync_executor = None

    # ------------------------------------------------------------ 全量同步

    # Java: public AjaxResult syncFullData()
    def sync_full_data(self) -> AjaxResult:
        """全量同步（查到最早 ``snapshottime`` -> 逐月并发搬数据）."""
        logger.info("【全量同步任务】开始执行全量同步")
        start_time = int(time.time() * 1000)

        try:
            # 步骤1: 查询 GaussDB 中最早的 snapshottime
            earliest = self.query_earliest_snapshottime()
            if earliest is None:
                logger.warning("【全量同步任务】未查询到最早的snapshottime，可能GaussDB中无数据")
                return AjaxResult.success_message("GaussDB中暂无数据")

            # 步骤2: 获取当前时间
            now = datetime.now()

            # 步骤3: 根据时间范围获取月份分区列表
            month_partitions = self.get_month_partitions(earliest, now)
            logger.info(
                "【全量同步任务】时间范围: %s 至 %s, 月份分区数: %s, 分区列表: %s",
                self.format_date(earliest),
                self.format_date(now),
                len(month_partitions),
                month_partitions,
            )

            # 步骤4: 并发同步每个月份的数据
            total_count = self.sync_by_month_partitions(month_partitions)

            end_time = int(time.time() * 1000)
            logger.info(
                "【全量同步任务】完成全量同步，同步记录数: %s, 耗时: %s ms",
                total_count,
                end_time - start_time,
            )
            return AjaxResult.success_message(
                "全量同步完成，共同步 %s 条数据" % total_count
            )
        except Exception as exc:  # noqa: BLE001 - Java 同样 catch Exception
            logger.error("【全量同步任务】全量同步失败: %s", exc, exc_info=True)
            return AjaxResult.error_message("全量同步失败: %s" % exc)

    # Java: private Date queryEarliestSnapshottime()
    def query_earliest_snapshottime(self) -> Optional[Any]:
        """GaussDB 中最早的 ``snapshottime``（失败返回 ``None``，异常被吞）."""
        try:
            return self.http_service.get_earliest_snapshottime()
        except Exception as exc:  # noqa: BLE001 - Java 同样 catch Exception
            logger.error("【全量同步任务】查询最早snapshottime失败: %s", exc)
            return None

    # Java: private List<String> getMonthPartitions(Date startDate, Date endDate)
    def get_month_partitions(self, start_date: Any, end_date: Any) -> List[str]:
        """把 ``[startDate, endDate]`` 展开成 ``yyyyMM`` 列表（**含首尾**两月）."""
        partitions: List[str] = []
        start = _to_datetime(start_date)
        end = _to_datetime(end_date)
        if start is None or end is None:
            return partitions
        cursor = start
        # Java: while (!startCal.after(endCal)) —— 含等号
        while cursor <= end:
            partitions.append(cursor.strftime("%Y%m"))
            cursor = _add_months(cursor, 1)
        return partitions

    # Java: private int syncByMonthPartitions(List<String> monthPartitions)
    def sync_by_month_partitions(self, month_partitions: List[str]) -> int:
        """并发同步各月份，返回总条数（单个月份失败只记日志，不影响其它月份）."""
        total_count = _AtomicInt()
        exceptions: List[Exception] = []
        futures: List[Future] = []

        executor = self.sync_executor
        for month in month_partitions:
            futures.append(
                executor.submit(self._sync_one_month_guarded, month, total_count, exceptions)
            )

        for future in futures:
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001 - Java 同样 catch InterruptedException/ExecutionException
                logger.error("【全量同步任务】等待任务完成时发生异常: %s", exc)
                exceptions.append(exc)

        if exceptions:
            logger.warning("【全量同步任务】有 %s 个月份同步失败", len(exceptions))
        return total_count.get()

    def _sync_one_month_guarded(
        self, month: str, total_count: "_AtomicInt", exceptions: List[Exception]
    ) -> int:
        """``syncExecutor.submit(() -> { try { return syncSingleMonth(...); } catch ... })``."""
        try:
            return self.sync_single_month(month, total_count)
        except Exception as exc:  # noqa: BLE001
            logger.error("【全量同步任务】月份 %s 同步失败: %s", month, exc)
            exceptions.append(exc)
            return 0

    # Java: @Transactional public int syncSingleMonth(String month, AtomicInteger totalCount)
    def sync_single_month(self, month: str, total_count: "_AtomicInt") -> int:
        """同步单个月份（``month`` 形如 ``202610``）."""
        logger.info("【全量同步任务】开始同步月份: %s", month)
        start_time = int(time.time() * 1000)

        # 构建该月份的时间范围
        start_date = month[0:4] + "-" + month[4:6] + "-01 00:00:00"

        # 获取该月份的最后一天（Calendar.getActualMaximum(DAY_OF_MONTH)）
        year = int(month[0:4])
        month_no = int(month[4:6])
        last_day = _last_day_of_month(year, month_no)
        end_date = month[0:4] + "-" + month[4:6] + "-" + str(last_day) + " 23:59:59"

        count = self.sync_snapshot_flow_by_date_range(start_date, end_date)
        total_count.add_and_get(count)

        end_time = int(time.time() * 1000)
        logger.info(
            "【全量同步任务】月份 %s 同步完成，记录数: %s, 耗时: %s ms",
            month,
            count,
            end_time - start_time,
        )
        return count

    # Java: private int syncSnapshotFlowByDateRange(String startDate, String endDate)
    def sync_snapshot_flow_by_date_range(self, start_date: str, end_date: str) -> int:
        """按日期范围分页搬运（每页 1000 条，直到不足一页）.

        ⚠ **空转**：``convert_to_entity_list`` 只保留实体实例，而 Forest 返回的是
        ``dict``，所以第一页就 ``break``（见模块 docstring 与 ``COMPATIBILITY.md`` §42.4）。
        """
        total_count = 0
        page_num = 1
        page_size = _PAGE_SIZE

        while True:
            table_data_info = self.fetch_from_gauss_db(start_date, end_date, page_num, page_size)

            if (
                table_data_info is None
                or table_data_info.get_rows() is None
                or not table_data_info.get_rows()
            ):
                break

            data_list = self.convert_to_entity_list(table_data_info.get_rows())
            if not data_list:
                break

            grouped_by_month = self.group_by_month(data_list)

            for table_name, rows in grouped_by_month.items():
                self.ensure_table_exists(table_name)
                self.insert_batch_to_table(table_name, rows)
                total_count += len(rows)
                logger.debug("【全量同步任务】表 %s 插入 %s 条数据", table_name, len(rows))

            if len(data_list) < page_size:
                break

            page_num += 1

        return total_count

    # ------------------------------------------------------------ 增量同步

    # Java: @Scheduled(cron = "0 0 * * * ?") @Transactional public void syncIncrementalData()
    def sync_incremental_data(self) -> None:
        """增量同步（每小时整点）：从 MySQL 当前月表的水位线往后搬."""
        logger.info("【增量同步任务】开始执行增量同步")
        start_time = int(time.time() * 1000)

        try:
            # 步骤1: 获取当前月份表名
            current_month_table = ShardingTableUtil.get_table_name_by_date(datetime.now())

            # 步骤2: 查询 MySQL 中当前月份表的最新 snapshottime
            last_sync_time = self.query_last_sync_time(current_month_table)

            # 步骤3: 构建查询范围（从上次同步时间到当前时间）
            if last_sync_time is None:
                # 如果是首次同步，从本月1号开始
                start_date = self.format_date_time(
                    datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, day=1)
                )
            else:
                start_date = self.format_date_time(last_sync_time)

            end_date = self.format_date_time(datetime.now())
            logger.info("【增量同步任务】同步时间范围: %s 至 %s", start_date, end_date)

            # 步骤4: 执行同步
            sync_count = self.sync_snapshot_flow_by_date_range(start_date, end_date)

            end_time = int(time.time() * 1000)
            logger.info(
                "【增量同步任务】完成增量同步，同步记录数: %s, 耗时: %s ms",
                sync_count,
                end_time - start_time,
            )
        except Exception as exc:  # noqa: BLE001 - Java 同样 catch Exception
            logger.error("【增量同步任务】增量同步失败: %s", exc, exc_info=True)

    # Java: private Date queryLastSyncTime(String tableName)
    def query_last_sync_time(self, table_name: str) -> Optional[Any]:
        """分表里最大 ``snapshottime``；表不存在时返回 ``None``（从本月 1 号起）."""
        try:
            exists = self.snapshot_flow_mapper.check_table_exists(table_name)
            if exists == 0:
                logger.warning("【增量同步任务】表 %s 不存在，将从本月初开始同步", table_name)
                return None
            return self.snapshot_flow_mapper.get_max_snapshottime(table_name)
        except Exception as exc:  # noqa: BLE001 - Java 同样 catch Exception
            logger.error("【增量同步任务】查询最新snapshottime失败: %s", exc)
            return None

    # ------------------------------------------------------------ 辅助方法

    # Java: private TableDataInfo fetchFromGaussDB(String, String, int, int)
    def fetch_from_gauss_db(
        self, start_date: str, end_date: str, page_num: int, page_size: int
    ) -> Optional[TableDataInfo]:
        """从 GaussDB 拉一页（失败返回 ``None``，异常被吞）."""
        try:
            query_param = OdsRtSzdnSnapshotFlowAddcode()
            query_param.apply_time1 = start_date
            query_param.apply_time2 = end_date
            query_param.page_num = page_num
            query_param.page_size = page_size
            return self.http_service.get_ods_rt_szdn_snapshot_flow_addcode_page(query_param)
        except Exception as exc:  # noqa: BLE001 - Java 同样 catch Exception
            logger.error("【分表同步任务】从GaussDB拉取数据失败: %s", exc)
            return None

    # Java: private List<...> convertToEntityList(List<?> rows)
    def convert_to_entity_list(self, rows: List[Any]) -> List[OdsRtSzdnSnapshotFlowAddcode]:
        """**只**保留 ``isinstance(row, OdsRtSzdnSnapshotFlowAddcode)`` 的行.

        这是 Java ``if (row instanceof OdsRtSzdnSnapshotFlowAddcode)`` 的逐字对应 ——
        也是整个任务空转的原因（见模块 docstring）。**不要改成 `model_validate`**：
        改了就会真的往分表写数据，与 Java 行为不一致。
        """
        entities: List[OdsRtSzdnSnapshotFlowAddcode] = []
        for row in rows:
            if isinstance(row, OdsRtSzdnSnapshotFlowAddcode):
                entities.append(row)
        return entities

    # Java: private Map<String, List<...>> groupByMonth(List<...> dataList)
    def group_by_month(
        self, data_list: List[OdsRtSzdnSnapshotFlowAddcode]
    ) -> Dict[str, List[OdsRtSzdnSnapshotFlowAddcode]]:
        """按 ``snapshottime`` 落到对应的月份分表（``LinkedHashMap`` -> ``dict`` 保序）."""
        grouped: Dict[str, List[OdsRtSzdnSnapshotFlowAddcode]] = {}
        for data in data_list:
            if data.snapshottime is not None:
                table_name = ShardingTableUtil.get_table_name_by_date(data.snapshottime)
                grouped.setdefault(table_name, []).append(data)
        return grouped

    # Java: private void ensureTableExists(String tableName)
    def ensure_table_exists(self, table_name: str) -> None:
        """分表不存在就建（``CREATE TABLE ... LIKE``，与主表同构）."""
        try:
            exists = self.snapshot_flow_mapper.check_table_exists(table_name)
            if exists == 0:
                self.snapshot_flow_mapper.create_sharding_table(table_name)
                logger.info("【分表同步任务】创建分表: %s", table_name)
        except Exception as exc:  # noqa: BLE001 - Java 同样 catch Exception
            logger.error("【分表同步任务】创建分表失败: %s", exc)

    # Java: private void insertBatchToTable(String tableName, List<...> list)
    def insert_batch_to_table(
        self, table_name: str, entity_list: List[OdsRtSzdnSnapshotFlowAddcode]
    ) -> None:
        """批量插入；**失败会重抛**（本类是唯一一处 ``catch`` 后再 ``throw`` 的地方）."""
        try:
            self.snapshot_flow_mapper.insert_batch_to_table(table_name, entity_list)
        except Exception as exc:  # noqa: BLE001
            logger.error("【分表同步任务】批量插入失败: %s", exc)
            raise

    # Java: private String formatDate(Date date)
    def format_date(self, value: Any) -> str:
        moment = _to_datetime(value)
        return "" if moment is None else moment.strftime("%Y-%m-%d")

    # Java: private String formatDateTime(Date date)
    def format_date_time(self, value: Any) -> str:
        moment = _to_datetime(value)
        return "" if moment is None else moment.strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------ 手工入口

    # Java: @Scheduled(cron = "0 */5 * * * *") public AjaxResult manualFullSync()
    def manual_full_sync(self) -> AjaxResult:
        """手工触发全量同步（Java 上还挂着每 5 分钟一次的 ``@Scheduled``，但不生效）."""
        return self.sync_full_data()

    # Java: public AjaxResult manualIncrementalSync()
    def manual_incremental_sync(self) -> AjaxResult:
        """手工触发增量同步（返回值文案固定为"已触发"，不反映真实结果）."""
        self.sync_incremental_data()
        return AjaxResult.success_message("增量同步任务已触发")

    # Java: public void preCreateTables(int months)
    def pre_create_tables(self, months: int) -> None:
        """提前创建未来 N 个月的分表."""
        future_table_names = ShardingTableUtil.get_future_table_names(months)
        for table_name in future_table_names:
            self.ensure_table_exists(table_name)
        logger.info("【分表同步任务】已提前创建 %s 个未来分表", len(future_table_names))


# --------------------------------------------------------------------- 小工具


class _AtomicInt:
    """Java: ``java.util.concurrent.atomic.AtomicInteger``（本类只用到两个方法）."""

    __slots__ = ("_value",)

    def __init__(self, value: int = 0) -> None:
        self._value = value

    def get(self) -> int:
        return self._value

    def add_and_get(self, delta: int) -> int:
        self._value += delta
        return self._value


_DATE_ONLY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _to_datetime(value: Any) -> Optional[datetime]:
    """把 ``Date`` / ISO 字符串 / ``"yyyy-MM-dd HH:mm:ss"`` 统一成 ``datetime``.

    Forest 的 ``Date`` 返回值在本工程里是**原样透传**（见
    :mod:`app.base.service.forest.http_ods_rt_szdn_snapshot_flow_addcode_service`），
    可能是字符串也可能是数字，所以这里做一次宽容解析。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000.0 if value > 1e11 else value)
    text_value = str(value).strip()
    if not text_value:
        return None
    if _DATE_ONLY.match(text_value):
        try:
            return datetime.strptime(text_value, "%Y-%m-%d")
        except ValueError:
            return None
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text_value[: len(pattern) + 7], pattern)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text_value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _add_months(value: datetime, months: int) -> datetime:
    """``Calendar.add(Calendar.MONTH, n)`` —— 月末溢出时按 ``min(day, 当月天数)`` 处理."""
    total = value.year * 12 + (value.month - 1) + months
    year, month = total // 12, total % 12 + 1
    day = min(value.day, _last_day_of_month(year, month))
    return value.replace(year=year, month=month, day=day)


def _last_day_of_month(year: int, month: int) -> int:
    """``Calendar.getActualMaximum(Calendar.DAY_OF_MONTH)``."""
    if month == 12:
        first_of_next = datetime(year + 1, 1, 1)
    else:
        first_of_next = datetime(year, month + 1, 1)
    return (first_of_next - _ONE_DAY).day


_ONE_DAY = timedelta(days=1)


__all__ = [
    "BEAN_NAME",
    "INCREMENTAL_CRON",
    "MANUAL_FULL_SYNC_CRON",
    "SnapshotFlowSyncTask",
]
