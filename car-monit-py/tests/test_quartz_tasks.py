"""六个任务 bean 与 ``AbstractQuartzJob`` 的执行契约.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/*.java
#   + ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/AbstractQuartzJob.java

覆盖什么
--------
* :mod:`app.quartz.task` 的注册表（"导入即注册" 等价于 ``@Component`` 扫描）；
* ``AbstractQuartzJob.execute`` 的四步顺序、成功/失败两条 ``sys_job_log`` 路径、
  ``2000`` 字截断、``threading.local`` 的清理；
* 每个业务任务的**协作顺序**（先 truncate 再 saveBatch、Redis 写在最后 ……）——
  这些顺序是 Java 注释里明确要求过、且错了不会报错只会脏数据的地方。

为什么用替身而不是真库
----------------------
``TrackTask`` / ``VehicleMonitoringTask`` 的协作对象最终都会打 SQL。这里用记账替身，
断言的是"调了谁、按什么顺序、给了什么参数"，与 ``COMPATIBILITY.md`` §28.3
（Python 侧不开显式事务）互不干扰。
"""

from __future__ import annotations

import logging
from concurrent.futures import Future
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import pytest

from app.common.constant.constants import FAIL, SECTION_LIST, SUCCESS
from app.common.constant.schedule_constants import TASK_PROPERTIES
from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils import spring_utils as SpringUtils
from app.quartz.domain.sys_job import SysJob
from app.quartz.domain.sys_job_log import SysJobLog
from app.quartz.service import sys_job_log_service
from app.quartz.task import (
    ORG_TASK_BEAN_NAME,
    PARTITION_MAINTENANCE_TASK_BEAN_NAME,
    RY_TASK_BEAN_NAME,
    SNAPSHOT_FLOW_SYNC_TASK_BEAN_NAME,
    TASK_BEANS,
    TRACK_TASK_BEAN_NAME,
    VEHICLE_MONITORING_TASK_BEAN_NAME,
    OrgTask,
    PartitionMaintenanceTask,
    RyTask,
    SnapshotFlowSyncTask,
    TrackTask,
    VehicleMonitoringTask,
    get_bean_by_name,
)
from app.quartz.task import partition_maintenance_task as partition_module
from app.quartz.util.abstract_quartz_job import AbstractQuartzJob
from app.quartz.util.quartz_job_execution import QuartzJobExecution
from app.quartz.util.scheduler import JobDataMap, JobExecutionContext


# --------------------------------------------------------------------------- 记账替身


class _Recorder:
    """任意方法名都记账的替身（``service.syncHistoryTrack()`` 之类）."""

    def __init__(self, name: str, log: List[tuple]) -> None:
        self.name = name
        self.log = log

    def __getattr__(self, attribute: str) -> Any:
        def record(*args: Any, **kwargs: Any) -> None:
            self.log.append((self.name, attribute, args, kwargs))

        return record

    # 断言助手
    def calls(self, method: str) -> List[tuple]:
        return [entry for entry in self.log if entry[1] == method]


class _FakeJobLogService:
    """``ISysJobLogService`` 替身：只收 ``add_job_log``."""

    def __init__(self) -> None:
        self.rows: List[SysJobLog] = []

    def add_job_log(self, job_log: SysJobLog) -> int:
        self.rows.append(job_log)
        return 1


class _ProbeJob(AbstractQuartzJob):
    """可编排成功/失败的 ``AbstractQuartzJob`` 子类."""

    def __init__(self, error: Optional[BaseException] = None) -> None:
        self.error = error
        self.executed: List[SysJob] = []

    def do_execute(self, context: JobExecutionContext, sys_job: SysJob) -> None:
        self.executed.append(sys_job)
        if self.error is not None:
            raise self.error


def _context(job: Optional[SysJob]) -> JobExecutionContext:
    data_map = JobDataMap()
    if job is not None:
        data_map[TASK_PROPERTIES] = job
    return JobExecutionContext(None, None, None, data_map)


@pytest.fixture
def job_log_service(monkeypatch: pytest.MonkeyPatch) -> _FakeJobLogService:
    """``AbstractQuartzJob`` 通过 ``get_job_log_service()`` 取单例 —— 换掉它."""
    fake = _FakeJobLogService()
    monkeypatch.setattr(sys_job_log_service, "_SERVICE", fake)
    return fake


# --------------------------------------------------------------------------- 注册表


class TestTaskRegistry:
    EXPECTED: Dict[str, type] = {
        "ryTask": RyTask,
        "orgTask": OrgTask,
        "trackTask": TrackTask,
        "vehicleMonitoringTask": VehicleMonitoringTask,
        "partitionMaintenanceTask": PartitionMaintenanceTask,
        "snapshotFlowSyncTask": SnapshotFlowSyncTask,
    }

    def test_six_beans_are_registered_under_their_java_names(self) -> None:
        """``@Component("xxx")`` 的 value 就是 ``invoke_target`` 的第一段."""
        assert set(TASK_BEANS) == set(self.EXPECTED)
        for name, expected_type in self.EXPECTED.items():
            bean = SpringUtils.get_bean(name)
            assert isinstance(bean, expected_type)
            assert bean is TASK_BEANS[name]

    def test_the_bean_name_constants_match_the_registry(self) -> None:
        assert {
            RY_TASK_BEAN_NAME,
            ORG_TASK_BEAN_NAME,
            TRACK_TASK_BEAN_NAME,
            VEHICLE_MONITORING_TASK_BEAN_NAME,
            PARTITION_MAINTENANCE_TASK_BEAN_NAME,
            SNAPSHOT_FLOW_SYNC_TASK_BEAN_NAME,
        } == set(self.EXPECTED)

    @pytest.mark.parametrize("name", list(EXPECTED))
    def test_every_bean_is_a_singleton(self, name: str) -> None:
        """Spring 默认 ``singleton`` 作用域."""
        assert SpringUtils.get_bean(name) is get_bean_by_name(name)

    @pytest.mark.parametrize("name", list(EXPECTED))
    def test_every_task_class_is_a_leaf(self, name: str) -> None:
        """六个任务类都没有基类 —— 这就是 ``getattr`` 能代替 ``getDeclaredMethod`` 的前提."""
        assert self.EXPECTED[name].__bases__ == (object,)

    def test_get_bean_by_name_raises_for_an_unknown_key(self) -> None:
        with pytest.raises(KeyError):
            get_bean_by_name("nosuchTask")


# --------------------------------------------------------------------------- AbstractQuartzJob


class TestAbstractQuartzJob:
    def test_a_successful_run_writes_one_log_row(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        job = SysJob(
            job_name="可疑车俩数据同步",
            job_group="SYSTEM",
            invoke_target="trackTask.syncSuspiciousCar",
        )
        probe = _ProbeJob()

        probe.execute(_context(job))

        assert len(probe.executed) == 1
        row = job_log_service.rows[0]
        assert row.status == SUCCESS
        assert row.job_name == "可疑车俩数据同步"
        assert row.job_group == "SYSTEM"
        assert row.invoke_target == "trackTask.syncSuspiciousCar"
        assert row.exception_info is None
        assert row.start_time is not None and row.stop_time is not None
        assert row.stop_time >= row.start_time

    def test_the_job_message_is_the_java_concatenation(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        """``jobName + " 总共耗时：" + runMs + "毫秒"``."""
        probe = _ProbeJob()

        probe.execute(_context(SysJob(job_name="可疑车俩数据同步")))

        message = job_log_service.rows[0].job_message
        prefix, _, suffix = message.partition(" 总共耗时：")
        assert prefix == "可疑车俩数据同步"
        assert suffix.endswith("毫秒")
        assert suffix[: -len("毫秒")].isdigit()

    def test_a_null_job_name_is_printed_as_the_literal_null(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        """Java 的字符串拼接把 ``null`` 变成 ``"null"``."""
        probe = _ProbeJob()

        probe.execute(_context(SysJob()))

        assert job_log_service.rows[0].job_message.startswith("null 总共耗时：")

    def test_a_failing_task_is_recorded_as_failed(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        """``catch (Exception e)`` -> ``after(context, sysJob, e)``."""
        probe = _ProbeJob(RuntimeError("boom"))

        probe.execute(_context(SysJob(job_name="探测任务")))

        row = job_log_service.rows[0]
        assert row.status == FAIL
        assert row.exception_info is not None
        assert "boom" in row.exception_info
        assert row.job_message.startswith("探测任务 总共耗时：")

    def test_the_exception_info_is_truncated_to_2000_characters(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        """``StringUtils.substring(msg, 0, 2000)`` —— 没有省略号."""
        probe = _ProbeJob(RuntimeError("X" * 5000))

        probe.execute(_context(SysJob(job_name="探测任务")))

        exception_info = job_log_service.rows[0].exception_info
        assert len(exception_info) == 2000
        assert not exception_info.endswith("...")

    def test_the_base_class_cannot_execute(self, job_log_service: _FakeJobLogService) -> None:
        """``doExecute`` 是抽象方法：``NotImplementedError`` 也被 ``catch`` 住."""
        with pytest.raises(NotImplementedError):
            AbstractQuartzJob().do_execute(_context(SysJob()), SysJob())

        AbstractQuartzJob().execute(_context(SysJob(job_name="抽象任务")))

        assert job_log_service.rows[0].status == FAIL

    def test_the_thread_local_is_removed_after_each_run(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        probe = _ProbeJob()

        probe.execute(_context(SysJob(job_name="第一次")))
        probe.execute(_context(SysJob(job_name="第二次")))

        assert len(job_log_service.rows) == 2
        # 第二次仍然拿到自己的开始时间（不是上一次的残留）
        for row in job_log_service.rows:
            assert row.start_time is not None

    def test_a_missing_task_properties_is_not_an_error(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        """``copyBeanProp(dest, null)`` 什么都不做，``sysJob`` 保持全 null."""
        probe = _ProbeJob()

        probe.execute(_context(None))

        assert job_log_service.rows[0].job_message.startswith("null 总共耗时：")

    def test_the_quartz_wrapper_delegates_to_the_invoke_util(
        self, job_log_service: _FakeJobLogService, capsys: Any
    ) -> None:
        """``QuartzJobExecution.doExecute`` 只有一句 ``JobInvokeUtil.invokeMethod``."""
        import app.quartz.task  # noqa: F401 - 注册 ryTask

        QuartzJobExecution().execute(
            _context(SysJob(job_name="无参任务", invoke_target="ryTask.ryNoParams"))
        )

        assert capsys.readouterr().out.strip() == "执行无参方法"
        assert job_log_service.rows[0].status == SUCCESS

    def test_a_broken_invoke_target_is_logged_as_failed(
        self, job_log_service: _FakeJobLogService
    ) -> None:
        QuartzJobExecution().execute(
            _context(SysJob(job_name="坏任务", invoke_target="nosuchTask.doIt"))
        )

        row = job_log_service.rows[0]
        assert row.status == FAIL
        assert "No bean named 'nosuchTask' available" in row.exception_info


# --------------------------------------------------------------------------- RyTask


class TestRyTask:
    def test_the_no_argument_message(self, capsys: Any) -> None:
        RyTask().ry_no_params()

        assert capsys.readouterr().out.strip() == "执行无参方法"

    def test_the_single_argument_message(self, capsys: Any) -> None:
        RyTask().ry_params("ry")

        assert capsys.readouterr().out.strip() == "执行有参方法：ry"

    def test_a_null_argument_is_printed_as_null(self, capsys: Any) -> None:
        """Java 的 ``"执行有参方法：" + null`` -> ``执行有参方法：null``."""
        RyTask().ry_params(None)

        assert capsys.readouterr().out.strip() == "执行有参方法：null"

    def test_the_five_argument_message_uses_java_tostrings(self, capsys: Any) -> None:
        """``Boolean`` 是小写 ``true``（``str(True)`` 会是 ``True``）."""
        RyTask().ry_multiple_params("ry", True, 2000, 316.5, 100)

        assert capsys.readouterr().out.strip() == (
            "执行多参方法： 字符串类型ry，布尔类型true，长整型2000，浮点型316.5，整形100"
        )

    def test_the_empty_method_does_nothing(self, capsys: Any) -> None:
        """``autoBuildGoodsHb`` 在 Java 里就是空方法体."""
        RyTask().auto_build_goods_hb()

        assert capsys.readouterr().out == ""


# --------------------------------------------------------------------------- TrackTask


def _track_task() -> Tuple[TrackTask, List[tuple]]:
    log: List[tuple] = []
    return (
        TrackTask(
            car_track_info_service=_Recorder("carTrackInfoService", log),
            car_suspicious_service=_Recorder("carSuspiciousService", log),
            geometry_service=_Recorder("geometryService", log),
            car_except_record_service=_Recorder("carExceptRecordService", log),
        ),
        log,
    )


class TestTrackTask:
    def test_sync_current_track(self) -> None:
        task, log = _track_task()

        task.sync_current_track()

        assert [(entry[0], entry[1]) for entry in log] == [
            ("carTrackInfoService", "sync_current_track")
        ]

    def test_sync_suspicious_car_passes_an_empty_list(self) -> None:
        """Java 传的是 ``new ArrayList<>()``，不是 ``null``."""
        task, log = _track_task()

        task.sync_suspicious_car()

        name, method, args, _kwargs = log[0]
        assert (name, method) == ("carSuspiciousService", "sync_suspicious_car")
        assert args[0] == "redis"
        assert args[1] == []

    def test_sync_history_track_refreshes_the_cache_after_the_tracks(self) -> None:
        """顺序不能颠倒：先同步轨迹，再刷 ``lxfx='1'`` 的几何缓存."""
        task, log = _track_task()

        task.sync_history_track()

        assert [(entry[0], entry[1]) for entry in log] == [
            ("carTrackInfoService", "sync_history_track"),
            ("geometryService", "update_redis_list"),
        ]

    def test_save_car_except_passes_an_empty_entity(self) -> None:
        from app.manager.domain.car_except_record import CarExceptRecord

        task, log = _track_task()

        task.save_car_except()

        name, method, args, _kwargs = log[0]
        assert (name, method) == ("carExceptRecordService", "save_car_except")
        assert isinstance(args[0], CarExceptRecord)

    def test_change_car_suspicious(self) -> None:
        task, log = _track_task()

        task.change_car_suspicious()

        assert [(entry[0], entry[1]) for entry in log] == [
            ("carSuspiciousService", "change_car_suspicious")
        ]

    def test_the_commented_out_task_is_inert(self) -> None:
        """``syncHistoryTrackNoCar`` 整段被注释 —— 一个协作对象都不碰."""
        task, log = _track_task()

        assert task.sync_history_track_no_car() is None
        assert log == []

    def test_the_log_text_matches_java(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Java 的**结束**日志写的是 ``"可疑车辆迁移同步！"``（没有"结束"二字）."""
        task, _log = _track_task()
        with caplog.at_level(logging.INFO, logger="app.quartz.task.track_task"):
            task.change_car_suspicious()

        messages = [record.getMessage() for record in caplog.records]
        assert messages[0].startswith("可疑车辆迁移开始同步！")
        assert messages[-1].startswith("可疑车辆迁移同步！")

    def test_the_seven_cron_expressions_come_from_the_database(self) -> None:
        """任务类自己不写 cron —— 触发时刻全在 ``sys_job.cron_expression`` 里."""
        assert not hasattr(TrackTask, "create_scheduled_tasks")


# --------------------------------------------------------------------------- VehicleMonitoringTask


class _FakeBaseInfoApi:
    """``HttpBaseInfoApiService`` 替身：每个 ``getXxxList`` 都返回同一份 list."""

    def __init__(self, rows: List[Any]) -> None:
        self.rows = rows
        self.calls: List[str] = []

    def __getattr__(self, attribute: str) -> Any:
        def record() -> List[Any]:
            self.calls.append(attribute)
            return self.rows

        return record


class _FakeSyncService:
    def __init__(self, name: str, log: List[tuple]) -> None:
        self.name = name
        self.log = log

    def truncate_table(self) -> None:
        self.log.append((self.name, "truncate_table", None))

    def save_batch(self, rows: List[Any]) -> None:
        self.log.append((self.name, "save_batch", rows))


class _FakeRedisCache:
    def __init__(self, log: List[tuple]) -> None:
        self.log = log

    def set_cache_list(self, key: str, values: List[Any]) -> None:
        self.log.append(("redis", "set_cache_list", (key, values)))


@pytest.fixture
def vehicle_task() -> Any:
    rows = [{"id": 1}, {"id": 2}]
    api = _FakeBaseInfoApi(rows)
    log: List[tuple] = []
    services = {
        name: _FakeSyncService(name, log)
        for name in (
            "odsSzdnSectionService",
            "odsYhglVBaseOrgService",
            "odsSzdnGantryService",
            "odsSzdnTollService",
            "dwdLcztSfzjcxxService",
            "dwdLcztFwqjcxxService",
            "dwdLcztSfsjcxxService",
        )
    }
    task = VehicleMonitoringTask(
        http_base_info_api_service=api,
        redis_cache=_FakeRedisCache(log),
        **{
            _snake(service_name): service
            for service_name, service in services.items()
        },
    )
    return task, api, log, rows


def _snake(name: str) -> str:
    from app.common.utils.string_utils import to_under_score_case

    return to_under_score_case(name)


class TestVehicleMonitoringTask:
    @pytest.mark.parametrize(
        ("method", "api_method", "service"),
        [
            ("sync_org_info", "get_org_info_list", "odsYhglVBaseOrgService"),
            ("sync_section_info", "get_section_info_list", "odsSzdnSectionService"),
            ("sync_gantry_info", "get_gantry_info_list", "odsSzdnGantryService"),
            ("sync_service_area_info_info", "get_service_area_info_list", "dwdLcztFwqjcxxService"),
            ("sync_toll_booth_info_info", "get_toll_booth_info_list", "dwdLcztSfsjcxxService"),
            ("sync_sfzjcxx_info_info", "get_sfzjcxx_info_list", "dwdLcztSfzjcxxService"),
            ("sync_toll_station_info", "get_toll_station_info_list", "odsSzdnTollService"),
        ],
    )
    def test_the_seven_identical_shapes(
        self, vehicle_task: Any, method: str, api_method: str, service: str
    ) -> None:
        """``getXxxList()`` -> ``truncateTable()`` -> ``saveBatch(list)``，顺序固定."""
        task, api, log, rows = vehicle_task

        getattr(task, method)()

        assert api.calls == [api_method]
        assert log[0] == (service, "truncate_table", None)
        assert log[1] == (service, "save_batch", rows)
        # saveBatch 收到的就是接口刚给的那份 list
        assert log[1][2] is rows

    def test_only_the_section_sync_touches_the_cache(self, vehicle_task: Any) -> None:
        task, _api, log, _rows = vehicle_task

        task.sync_org_info()
        assert [entry[0] for entry in log] == ["odsYhglVBaseOrgService"] * 2

        log.clear()
        task.sync_section_info()
        assert [entry[0] for entry in log] == [
            "odsSzdnSectionService",
            "odsSzdnSectionService",
            "redis",
        ]

    def test_the_cache_write_is_last_and_carries_the_inserted_rows(
        self, vehicle_task: Any
    ) -> None:
        """插入失败就不该污染缓存 —— ``setCacheList`` 在最后一行."""
        task, _api, log, rows = vehicle_task

        task.sync_section_info()

        key, values = log[-1][2]
        assert key == SECTION_LIST
        assert values is rows

    def test_all_seven_methods_exist(self) -> None:
        """方法名里的双 ``Info`` 是 Java 原文，``invoke_target`` 依赖它."""
        for name in (
            "sync_toll_booth_info_info",
            "sync_org_info",
            "sync_toll_station_info",
            "sync_gantry_info",
            "sync_sfzjcxx_info_info",
            "sync_service_area_info_info",
            "sync_section_info",
        ):
            assert callable(getattr(VehicleMonitoringTask, name))


# --------------------------------------------------------------------------- PartitionMaintenanceTask


class _FakeJdbc:
    def __init__(self, rows: Optional[List[str]] = None, fail_on: Tuple[str, ...] = ()) -> None:
        self.executed: List[str] = []
        self.queried: List[str] = []
        self.rows = rows or []
        self.fail_on = fail_on

    def execute(self, sql: str) -> None:
        if any(token in sql for token in self.fail_on):
            raise RuntimeError("boom")
        self.executed.append(sql)

    def query(self, sql: str) -> List[str]:
        self.queried.append(sql)
        if any(token in sql for token in self.fail_on):
            raise RuntimeError("boom")
        return self.rows


class _FrozenDate(date):
    """把 ``date.today()`` 钉在 ``2026-10-29``（只影响本模块的 ``date`` 名字）."""

    @classmethod
    def today(cls) -> "_FrozenDate":
        return cls(2026, 10, 29)


@pytest.fixture
def frozen_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(partition_module, "date", _FrozenDate)


class TestPartitionMaintenanceTask:
    def test_six_months_times_three_tables(self, frozen_today: None) -> None:
        """``PRE_CREATE_MONTHS = 6`` × ``PARTITION_TABLES`` 3 张表 = 18 条 DDL."""
        jdbc = _FakeJdbc()

        PartitionMaintenanceTask(jdbc_template=jdbc).create_future_partitions()

        assert len(jdbc.executed) == 18
        names = [sql.split(" ")[5] for sql in jdbc.executed]
        assert names[0] == "ods_rt_szdn_snapshot_flow_addcode_p202611"
        assert names[-1] == "zdata_trail_fitting_p202704"

    def test_the_sql_is_the_gaussdb_partition_clause(self, frozen_today: None) -> None:
        jdbc = _FakeJdbc()

        PartitionMaintenanceTask(jdbc_template=jdbc).create_future_partitions()

        assert jdbc.executed[0] == (
            "CREATE TABLE IF NOT EXISTS ods_rt_szdn_snapshot_flow_addcode_p202611 "
            "PARTITION OF ods_rt_szdn_snapshot_flow_addcode "
            "FOR VALUES FROM ('2026-11-01') TO ('2026-12-01')"
        )
        # 列表里三张表都出现，顺序与 PARTITION_TABLES 一致
        assert [sql.split(" ")[5].rsplit("_p", 1)[0] for sql in jdbc.executed[:3]] == [
            "ods_rt_szdn_snapshot_flow_addcode",
            "ods_lwzxsfsj_fee_records_01",
            "zdata_trail_fitting",
        ]

    def test_a_failing_ddl_is_swallowed(self, frozen_today: None) -> None:
        """分区已存在会报错 —— Java ``catch (Exception e)`` 只记日志，继续下一个."""
        jdbc = _FakeJdbc(fail_on=("PARTITION OF",))

        PartitionMaintenanceTask(jdbc_template=jdbc).create_future_partitions()

        assert jdbc.executed == []

    def test_the_health_check_queries_three_tables(self) -> None:
        jdbc = _FakeJdbc(rows=["a_p202610", "a_p202609"])

        PartitionMaintenanceTask(jdbc_template=jdbc).check_partition_health()

        assert len(jdbc.queried) == 3
        assert jdbc.queried[0] == (
            "SELECT inhrelid::regclass AS partition_name "
            "FROM pg_inherits WHERE inhparent = 'ods_rt_szdn_snapshot_flow_addcode'::regclass "
            "ORDER BY partition_name"
        )

    def test_a_failing_health_query_is_swallowed(self) -> None:
        jdbc = _FakeJdbc(fail_on=("pg_inherits",))

        PartitionMaintenanceTask(jdbc_template=jdbc).check_partition_health()

        assert len(jdbc.queried) == 3

    def test_the_two_cron_expressions_are_the_java_ones(self) -> None:
        """``@Scheduled`` 在 Java 里**从不触发**（没有 ``@EnableScheduling``），常量照抄."""
        assert partition_module.CREATE_PARTITIONS_CRON == "0 0 1 1 * ?"
        assert partition_module.CHECK_PARTITION_HEALTH_CRON == "0 0 2 * * MON"
        assert partition_module.PRE_CREATE_MONTHS == 6
        assert len(partition_module.PARTITION_TABLES) == 3


# --------------------------------------------------------------------------- OrgTask


class TestOrgTask:
    def test_the_sync_is_an_empty_method(self) -> None:
        """方法体整段被注释 —— 一个协作对象都不碰，连事务都不开."""
        log: List[tuple] = []
        task = OrgTask(
            ods_yhgl_v_base_org_service=_Recorder("odsYhglVBaseOrgService", log),
            sys_dept_service=_Recorder("sysDeptService", log),
        )

        assert task.sync_org_info() is None
        assert log == []

    def test_the_two_unused_dependencies_still_resolve(self) -> None:
        log: List[tuple] = []
        org_service = _Recorder("a", log)
        dept_service = _Recorder("b", log)

        task = OrgTask(
            ods_yhgl_v_base_org_service=org_service, sys_dept_service=dept_service
        )
        assert task.ods_yhgl_v_base_org_service is org_service
        assert task.sys_dept_service is dept_service


# --------------------------------------------------------------------------- SnapshotFlowSyncTask


class _FakeTableData:
    def __init__(self, rows: List[Any]) -> None:
        self._rows = rows

    def get_rows(self) -> List[Any]:
        return self._rows


class _FakeSnapshotApi:
    def __init__(self, pages: List[Optional[List[Any]]]) -> None:
        self.pages = pages
        self.requests: List[Any] = []

    def get_ods_rt_szdn_snapshot_flow_addcode_page(self, query_param: Any) -> Any:
        self.requests.append(query_param)
        rows = self.pages.pop(0) if self.pages else []
        return None if rows is None else _FakeTableData(rows)

    def get_earliest_snapshottime(self) -> Any:
        return getattr(self, "earliest", None)


class _FakeSnapshotMapper:
    def __init__(self) -> None:
        self.exists = 1
        self.calls: List[tuple] = []

    def check_table_exists(self, table_name: str) -> int:
        self.calls.append(("check_table_exists", table_name))
        return self.exists

    def create_sharding_table(self, table_name: str) -> None:
        self.calls.append(("create_sharding_table", table_name))

    def insert_batch_to_table(self, table_name: str, rows: List[Any]) -> None:
        self.calls.append(("insert_batch_to_table", table_name, len(rows)))

    def get_max_snapshottime(self, table_name: str) -> Any:
        self.calls.append(("get_max_snapshottime", table_name))
        return datetime(2026, 10, 29, 9, 0, 0)


class _InlineExecutor:
    """``ThreadPoolExecutor`` 替身：就地执行，保证断言顺序确定."""

    def __init__(self) -> None:
        self.submitted: List[tuple] = []
        self.stopped = False

    def submit(self, function: Any, *args: Any) -> Future:
        self.submitted.append((function.__name__, args))
        future: Future = Future()
        try:
            future.set_result(function(*args))
        except Exception as exc:  # noqa: BLE001 - 与真实 Future 一致：异常存进对象
            future.set_exception(exc)
        return future

    def shutdown(self, wait: bool = True) -> None:
        self.stopped = True


def _snapshot_task(
    pages: Optional[List[Optional[List[Any]]]] = None,
    mapper: Optional[_FakeSnapshotMapper] = None,
    executor: Optional[_InlineExecutor] = None,
) -> Tuple[SnapshotFlowSyncTask, _FakeSnapshotApi, _FakeSnapshotMapper, _InlineExecutor]:
    api = _FakeSnapshotApi(pages if pages is not None else [])
    mapper = mapper or _FakeSnapshotMapper()
    executor = executor or _InlineExecutor()
    task = SnapshotFlowSyncTask(
        snapshot_flow_mapper=mapper, http_service=api, sync_executor=executor
    )
    return task, api, mapper, executor


class TestSnapshotFlowSyncTask:
    def test_dict_rows_are_dropped_which_makes_the_whole_task_a_no_op(self) -> None:
        """``convertToEntityList`` 只留实体实例 —— Forest 返回 ``dict``，于是空转."""
        from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import (
            OdsRtSzdnSnapshotFlowAddcode,
        )

        entity = OdsRtSzdnSnapshotFlowAddcode(snapshottime=datetime(2026, 10, 29, 1, 0, 0))
        task, _api, _mapper, _executor = _snapshot_task()

        assert task.convert_to_entity_list([{"snapshottime": "2026-10-29"}, entity]) == [entity]

    def test_the_date_range_sync_returns_zero_for_dict_rows(self) -> None:
        task, api, mapper, _executor = _snapshot_task(
            pages=[[{"snapshottime": "2026-10-29 01:00:00"}]]
        )

        assert task.sync_snapshot_flow_by_date_range("2026-10-01 00:00:00", "2026-10-31 23:59:59") == 0
        assert mapper.calls == []  # 连分表都没查
        assert len(api.requests) == 1  # 第一页就 break

    def test_the_query_param_is_the_java_page_object(self) -> None:
        task, api, _mapper, _executor = _snapshot_task(pages=[])

        task.sync_snapshot_flow_by_date_range("2026-10-01 00:00:00", "2026-10-31 23:59:59")

        param = api.requests[0]
        assert param.apply_time1 == "2026-10-01 00:00:00"
        assert param.apply_time2 == "2026-10-31 23:59:59"
        assert (param.page_num, param.page_size) == (1, 1000)

    def test_entity_rows_are_grouped_and_inserted(self) -> None:
        from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import (
            OdsRtSzdnSnapshotFlowAddcode,
        )

        entity = OdsRtSzdnSnapshotFlowAddcode(snapshottime=datetime(2026, 10, 29, 1, 0, 0))
        task, _api, mapper, _executor = _snapshot_task(pages=[[entity]])

        assert task.sync_snapshot_flow_by_date_range("2026-10-01 00:00:00", "2026-10-31 23:59:59") == 1
        assert mapper.calls == [
            ("check_table_exists", "ods_rt_szdn_snapshot_flow_202610"),
            ("insert_batch_to_table", "ods_rt_szdn_snapshot_flow_202610", 1),
        ]

    def test_a_missing_sharding_table_is_created_first(self) -> None:
        from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import (
            OdsRtSzdnSnapshotFlowAddcode,
        )

        mapper = _FakeSnapshotMapper()
        mapper.exists = 0
        entity = OdsRtSzdnSnapshotFlowAddcode(snapshottime=datetime(2026, 10, 29, 1, 0, 0))
        task, _api, _mapper, _executor = _snapshot_task(pages=[[entity]], mapper=mapper)

        task.sync_snapshot_flow_by_date_range("2026-10-01 00:00:00", "2026-10-31 23:59:59")

        assert mapper.calls[0] == ("check_table_exists", "ods_rt_szdn_snapshot_flow_202610")
        assert mapper.calls[1] == ("create_sharding_table", "ods_rt_szdn_snapshot_flow_202610")

    def test_an_insert_failure_is_rethrown(self) -> None:
        """``insertBatchToTable`` 是全类唯一 ``catch`` 后再 ``throw`` 的地方."""

        class _ExplodingMapper(_FakeSnapshotMapper):
            def insert_batch_to_table(self, table_name: str, rows: List[Any]) -> None:
                raise RuntimeError("insert failed")

        from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import (
            OdsRtSzdnSnapshotFlowAddcode,
        )

        entity = OdsRtSzdnSnapshotFlowAddcode(snapshottime=datetime(2026, 10, 29, 1, 0, 0))
        task, _api, _mapper, _executor = _snapshot_task(
            pages=[[entity]], mapper=_ExplodingMapper()
        )

        with pytest.raises(RuntimeError, match="insert failed"):
            task.sync_snapshot_flow_by_date_range("2026-10-01 00:00:00", "2026-10-31 23:59:59")

    @pytest.mark.parametrize(
        ("start", "end", "expected"),
        [
            (datetime(2026, 10, 1), datetime(2026, 10, 31), ["202610"]),
            (datetime(2026, 10, 1), datetime(2027, 1, 2), ["202610", "202611", "202612", "202701"]),
            (datetime(2026, 12, 31), datetime(2026, 12, 31), ["202612"]),
            # Calendar.add(MONTH) 保留 day-of-month：10-15 -> 01-15 已经越过 01-02
            (datetime(2026, 10, 15), datetime(2027, 1, 2), ["202610", "202611", "202612"]),
        ],
    )
    def test_the_month_partitions_include_both_ends(
        self, start: datetime, end: datetime, expected: List[str]
    ) -> None:
        task, _api, _mapper, _executor = _snapshot_task()

        assert task.get_month_partitions(start, end) == expected

    def test_the_boundary_is_day_of_month_sensitive(self) -> None:
        """照抄 ``Calendar.add(MONTH, 1)`` —— 不把日期截到 1 号.

        所以 ``start`` 的"日"大于 ``end`` 的"日"时，最后一个月会被跳过。
        ``sync_full_data`` 传的是 ``earliest`` 与 ``now``，线上同样有这个行为。
        """
        task, _api, _mapper, _executor = _snapshot_task()

        assert task.get_month_partitions(
            datetime(2026, 10, 29, 11, 16, 4), datetime(2027, 1, 2, 0, 0, 0)
        ) == ["202610", "202611", "202612"]

    def test_an_unparsable_bound_yields_no_partitions(self) -> None:
        task, _api, _mapper, _executor = _snapshot_task()

        assert task.get_month_partitions(None, datetime(2026, 10, 1)) == []
        assert task.get_month_partitions("not-a-date", datetime(2026, 10, 1)) == []

    def test_sync_full_data_without_data_reports_the_java_message(self) -> None:
        task, _api, _mapper, _executor = _snapshot_task()

        result = task.sync_full_data()

        assert result["msg"] == "GaussDB中暂无数据"
        assert result["code"] == 200

    def test_sync_full_data_aggregates_the_month_counts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 冻结生产模块的“当前时间”，避免测试随挂钟漂移（earliest=2026-08-15
        # 在 8/9/10 月跑是 3 个月，跨到 11 月会变成 4 个月导致断言失效）。
        import app.quartz.task.snapshot_flow_sync_task as sfs_module

        class _FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz: Any = None) -> datetime:
                return datetime(2026, 10, 31, 12, 0, 0)

        monkeypatch.setattr(sfs_module, "datetime", _FrozenDatetime)
        task, api, _mapper, executor = _snapshot_task(pages=[])
        api.earliest = datetime(2026, 8, 15)

        def five_per_month(_month: str, total: Any) -> int:
            total.add_and_get(5)
            return 5

        task.sync_single_month = five_per_month  # type: ignore[assignment]

        result = task.sync_full_data()

        assert result["msg"] == "全量同步完成，共同步 15 条数据"
        assert len(executor.submitted) == 3  # 202608 / 202609 / 202610

    def test_sync_full_data_turns_an_exception_into_an_error_result(self) -> None:
        task, api, _mapper, _executor = _snapshot_task(pages=[])
        api.earliest = datetime(2026, 8, 15)

        def explode(_earliest: Any, _now: Any) -> List[str]:
            raise RuntimeError("boom")

        task.get_month_partitions = explode  # type: ignore[assignment]

        result = task.sync_full_data()

        assert result["code"] == 500
        assert result["msg"] == "全量同步失败: boom"

    def test_a_failing_month_does_not_stop_the_others(self) -> None:
        task, _api, _mapper, executor = _snapshot_task()

        def half_broken(month: str, total: Any) -> int:
            if month.endswith("09"):
                raise RuntimeError("boom")
            total.add_and_get(2)
            return 2

        task.sync_single_month = half_broken  # type: ignore[assignment]

        assert task.sync_by_month_partitions(["202608", "202609", "202610"]) == 4
        assert len(executor.submitted) == 3

    def test_query_last_sync_time_returns_none_for_a_missing_table(self) -> None:
        mapper = _FakeSnapshotMapper()
        mapper.exists = 0
        task, _api, _mapper, _executor = _snapshot_task(mapper=mapper)

        assert task.query_last_sync_time("ods_rt_szdn_snapshot_flow_202610") is None
        assert mapper.calls == [("check_table_exists", "ods_rt_szdn_snapshot_flow_202610")]

    def test_query_last_sync_time_reads_the_watermark(self) -> None:
        task, _api, mapper, _executor = _snapshot_task()

        assert task.query_last_sync_time("ods_rt_szdn_snapshot_flow_202610") == datetime(
            2026, 10, 29, 9, 0, 0
        )
        assert mapper.calls[-1] == ("get_max_snapshottime", "ods_rt_szdn_snapshot_flow_202610")

    def test_manual_incremental_sync_always_reports_triggered(self) -> None:
        """返回值文案固定，不反映真实结果（Java 原文如此）."""
        task, _api, _mapper, _executor = _snapshot_task()

        def explode(_table: str) -> Any:
            raise RuntimeError("boom")

        task.query_last_sync_time = explode  # type: ignore[assignment]

        result = task.manual_incremental_sync()

        assert result["msg"] == "增量同步任务已触发"

    def test_manual_full_sync_delegates(self) -> None:
        task, _api, _mapper, _executor = _snapshot_task()

        result = task.manual_full_sync()

        assert isinstance(result, AjaxResult)
        assert result["msg"] == "GaussDB中暂无数据"

    def test_pre_create_tables_ensures_every_future_table(self) -> None:
        task, _api, mapper, _executor = _snapshot_task()
        mapper.exists = 0

        task.pre_create_tables(2)

        created = [entry[1] for entry in mapper.calls if entry[0] == "create_sharding_table"]
        assert len(created) == 2
        for table_name in created:
            assert table_name.startswith("ods_rt_szdn_snapshot_flow_")

    def test_the_formatters_match_the_java_patterns(self) -> None:
        task, _api, _mapper, _executor = _snapshot_task()

        assert task.format_date(datetime(2026, 10, 29, 11, 16, 4)) == "2026-10-29"
        assert task.format_date_time(datetime(2026, 10, 29, 11, 16, 4)) == "2026-10-29 11:16:04"
        assert task.format_date(None) == ""
        assert task.format_date_time("not-a-date") == ""

    def test_init_and_shutdown_manage_the_thread_pool(self) -> None:
        task = SnapshotFlowSyncTask(
            snapshot_flow_mapper=_FakeSnapshotMapper(),
            http_service=_FakeSnapshotApi([]),
        )

        task.init()
        executor = task.sync_executor
        assert executor is not None

        task.shutdown()
        assert task._sync_executor is None  # noqa: SLF001 - 白盒断言

    def test_the_two_scheduled_cron_expressions(self) -> None:
        """``@Scheduled`` 在 Java 里从不触发，常量仍要一致."""
        from app.quartz.task import snapshot_flow_sync_task as module

        assert module.INCREMENTAL_CRON == "0 0 * * * ?"
        assert module.MANUAL_FULL_SYNC_CRON == "0 */5 * * * *"
        assert module._PAGE_SIZE == 1000  # noqa: SLF001
