"""``SysJobService`` / ``SysJobLogService`` 的行为（含 ``@Transactional`` 边界）.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/{SysJobServiceImpl,SysJobLogServiceImpl}.java

为什么不用真库
--------------
这两个 service 的方法体只有三件事：调 mapper、开事务、动调度器。用假 mapper 记录
调用顺序 + 一个**记账用**的 ``session_scope`` 替身，就能在不连 MySQL 的前提下把
Java 的语义钉死：

* ``@Transactional(rollbackFor = Exception.class)`` —— ``insertJob`` 里
  ``createScheduleJob`` 抛 ``TaskException``（``misfirePolicy='9'``）时，
  **刚插入的那行必须回滚**（``evidence/_probe_job_err_out.txt`` 实测库里没有残留行）；
* ``if (rows > 0)`` —— 改库失败/影响 0 行时**不许**碰调度器；
* ``properties.getJobGroup()`` 的顺序 —— ``updateJob`` 用**旧** ``jobGroup`` 删任务，
  而且 ``properties`` 为 ``null`` 时不判空（靠 ``rows > 0`` 兜住）。

调度器替身
----------
:class:`_FakeScheduler` 只实现 ``createScheduleJob`` 用到的那 6 个方法，并用
``str(jobKey)`` 记账（``"PROBE.TASK_CLASS_NAME7"``），所以断言读起来就是线上的
``SchedulerException`` 文案。真正的 RAMJobStore 语义已在
``tests/test_quartz_cron_and_schedule.py`` 里验过，这里不需要重复。
"""

from __future__ import annotations

import contextlib
from typing import Any, Dict, Iterator, List, Optional

import pytest

from app.common.constant.schedule_constants import TASK_PROPERTIES, Status
from app.common.exception.job.task_exception import TaskException
from app.common.utils import spring_utils as SpringUtils
from app.quartz.domain.sys_job import SysJob
from app.quartz.domain.sys_job_log import SysJobLog
from app.quartz.service import sys_job_service
from app.quartz.service.sys_job_log_service import (
    BEAN_NAME as JOB_LOG_BEAN_NAME,
    SysJobLogService,
    get_job_log_service,
    reset_job_log_service,
)
from app.quartz.service.sys_job_service import (
    SysJobService,
    get_job_service,
    reset_job_service,
)

#: ``session_scope()`` 里 ``yield`` 出来的"会话"。service 只把它原样传给 mapper，
#: 所以身份比较就足以证明"同一个事务会话"。
FAKE_SESSION = object()


# --------------------------------------------------------------------------- 替身


class _RecordingSessionScope:
    """``app.config.database.session_scope`` 的记账替身.

    真实实现是 ``with session: yield session; session.commit()`` / 异常时
    ``session.rollback(); raise``。这里只数次数 —— 用例断言的是"提交了几次、
    回滚了几次"，而不是 SQL。
    """

    def __init__(self) -> None:
        self.opened = 0
        self.committed = 0
        self.rolled_back = 0

    @contextlib.contextmanager
    def __call__(self) -> Iterator[object]:
        self.opened += 1
        try:
            yield FAKE_SESSION
        except BaseException:
            self.rolled_back += 1
            raise
        self.committed += 1


class _FakeScheduler:
    """只实现 ``createScheduleJob`` / ``pauseJob`` / ``resumeJob`` 用到的方法."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.entries: Dict[Any, Any] = {}

    # -- 查询
    def check_exists(self, job_key: Any) -> bool:
        self.calls.append(("check_exists", str(job_key)))
        return job_key in self.entries

    def get_job_keys(self) -> List[Any]:
        return list(self.entries)

    # -- 变更
    def schedule_job(self, job_detail: Any, trigger: Any) -> float:
        self.calls.append(("schedule_job", str(job_detail.key), trigger.cron_expression))
        self.entries[job_detail.key] = job_detail
        return 0.0

    def delete_job(self, job_key: Any) -> bool:
        self.calls.append(("delete_job", str(job_key)))
        return self.entries.pop(job_key, None) is not None

    def pause_job(self, job_key: Any) -> None:
        self.calls.append(("pause_job", str(job_key)))

    def resume_job(self, job_key: Any) -> None:
        self.calls.append(("resume_job", str(job_key)))

    def trigger_job(self, job_key: Any, data_map: Any = None) -> None:
        self.calls.append(("trigger_job", str(job_key), data_map))

    def clear(self) -> None:
        self.calls.append(("clear",))
        self.entries.clear()

    # -- 断言助手
    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]

    def names(self) -> List[str]:
        return [call[0] for call in self.calls]


class _FakeJobMapper:
    """``SysJobMapper`` 的记账替身（返回行数可调）."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.rows = 1
        self.jobs: Dict[int, SysJob] = {}
        self.all_jobs: List[SysJob] = []
        self.sessions: List[Any] = []

    def select_job_all(self, session: Optional[Any] = None) -> List[SysJob]:
        self.calls.append(("select_job_all",))
        return list(self.all_jobs)

    def select_job_list(self, job: SysJob, session: Optional[Any] = None) -> List[SysJob]:
        self.calls.append(("select_job_list", job))
        return [job]

    def select_job_by_id(self, job_id: int, session: Optional[Any] = None) -> Optional[SysJob]:
        self.calls.append(("select_job_by_id", job_id))
        return self.jobs.get(job_id)

    def insert_job(self, job: SysJob, session: Optional[Any] = None) -> int:
        self.calls.append(("insert_job", job.model_copy(deep=True)))
        self.sessions.append(session)
        return self.rows

    def update_job(self, job: SysJob, session: Optional[Any] = None) -> int:
        self.calls.append(("update_job", job.model_copy(deep=True)))
        self.sessions.append(session)
        return self.rows

    def delete_job_by_id(self, job_id: int, session: Optional[Any] = None) -> int:
        self.calls.append(("delete_job_by_id", job_id))
        self.sessions.append(session)
        return self.rows


class _FakeJobLogMapper:
    """``SysJobLogMapper`` 的记账替身."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.rows = 1
        self.logs: List[SysJobLog] = []

    def select_job_log_list(self, job_log: SysJobLog, session: Optional[Any] = None) -> List[SysJobLog]:
        self.calls.append(("select_job_log_list", job_log))
        return list(self.logs)

    def select_job_log_by_id(
        self, job_log_id: int, session: Optional[Any] = None
    ) -> Optional[SysJobLog]:
        self.calls.append(("select_job_log_by_id", job_log_id))
        return self.logs[0] if self.logs else None

    def insert_job_log(self, job_log: SysJobLog, session: Optional[Any] = None) -> int:
        self.calls.append(("insert_job_log", job_log))
        return self.rows

    def delete_job_log_by_ids(self, log_ids: Any, session: Optional[Any] = None) -> int:
        self.calls.append(("delete_job_log_by_ids", list(log_ids)))
        return self.rows

    def delete_job_log_by_id(self, job_log_id: int, session: Optional[Any] = None) -> int:
        self.calls.append(("delete_job_log_by_id", job_log_id))
        return self.rows

    def clean_job_log(self, session: Optional[Any] = None) -> None:
        self.calls.append(("clean_job_log",))


# --------------------------------------------------------------------------- fixtures


@pytest.fixture
def tx(monkeypatch: pytest.MonkeyPatch) -> _RecordingSessionScope:
    """把 service 模块里的 ``session_scope`` 换成记账替身."""
    scope = _RecordingSessionScope()
    monkeypatch.setattr(sys_job_service, "session_scope", scope)
    return scope


@pytest.fixture
def mapper() -> _FakeJobMapper:
    return _FakeJobMapper()


@pytest.fixture
def scheduler() -> _FakeScheduler:
    return _FakeScheduler()


@pytest.fixture
def service(mapper: _FakeJobMapper, scheduler: _FakeScheduler) -> SysJobService:
    return SysJobService(mapper=mapper, scheduler=scheduler)


@pytest.fixture(autouse=True)
def clean_singletons() -> Iterator[None]:
    """单例与 Spring 注册表都不能跨用例泄漏."""
    reset_job_service()
    reset_job_log_service()
    yield
    reset_job_service()
    reset_job_log_service()


def _job(**overrides: Any) -> SysJob:
    """一条能通过 ``createScheduleJob`` 的合法任务定义."""
    fields: Dict[str, Any] = {
        "job_id": 7,
        "job_name": "探测任务",
        "job_group": "PROBE",
        "invoke_target": "ryTask.ryNoParams",
        "cron_expression": "0 0 2 * * ?",
        "misfire_policy": "0",
        "concurrent": "0",
        "status": Status.NORMAL.value,
    }
    fields.update(overrides)
    return SysJob(**fields)


# =========================================================================== SysJobService


class TestProperties:
    def test_the_scheduler_is_the_injected_one(
        self, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        service = SysJobService(mapper=mapper, scheduler=scheduler)

        assert service.mapper is mapper
        assert service.scheduler is scheduler

    def test_without_an_override_the_global_singleton_is_used(
        self, mapper: _FakeJobMapper
    ) -> None:
        service = SysJobService(mapper=mapper)

        from app.quartz.util.scheduler import get_scheduler

        assert service.scheduler is get_scheduler()


class TestInsertJob:
    def test_the_status_is_forced_to_pause(
        self, service: SysJobService, mapper: _FakeJobMapper, tx: _RecordingSessionScope
    ) -> None:
        """Java: ``job.setStatus(Status.PAUSE.getValue())`` —— 不管调用方传什么."""
        job = _job(status=Status.NORMAL.value)

        assert service.insert_job(job) == 1
        assert job.status == Status.PAUSE.value == "1"
        assert mapper.calls[0][1].status == "1"

    def test_the_insert_and_the_registration_share_one_transaction(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
        tx: _RecordingSessionScope,
    ) -> None:
        service.insert_job(_job())

        assert tx.opened == 1
        assert tx.committed == 1
        assert mapper.sessions == [FAKE_SESSION]
        # 新任务被强制暂停，所以注册完立刻 pauseJob
        assert scheduler.names() == ["check_exists", "schedule_job", "pause_job"]

    def test_an_illegal_misfire_policy_rolls_the_insert_back(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
        tx: _RecordingSessionScope,
    ) -> None:
        """``@Transactional(rollbackFor = Exception.class)`` 的核心断言."""
        with pytest.raises(TaskException) as raised:
            service.insert_job(_job(misfire_policy="9"))

        assert raised.value.code is TaskException.Code.CONFIG_ERROR
        # 插入语句执行过，但事务回滚了 —— 线上库里没有任何残留行
        assert mapper.calls[0][0] == "insert_job"
        assert tx.opened == 1
        assert tx.committed == 0
        assert tx.rolled_back == 1
        # ``createScheduleJob`` 在 handleCronScheduleMisfirePolicy 就炸了，没注册成功
        assert scheduler.entries == {}

    def test_zero_rows_skips_the_scheduler_and_still_commits(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
        tx: _RecordingSessionScope,
    ) -> None:
        mapper.rows = 0

        assert service.insert_job(_job()) == 0
        assert scheduler.calls == []
        assert tx.committed == 1


class TestPauseAndResume:
    def test_pause_writes_the_pause_status_then_pauses(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        job = _job()

        assert service.pause_job(job) == 1
        assert job.status == "1"
        assert mapper.calls[0][1].status == "1"
        assert scheduler.calls == [("pause_job", "PROBE.TASK_CLASS_NAME7")]

    def test_pause_with_zero_rows_leaves_the_scheduler_alone(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        mapper.rows = 0
        job = _job()

        assert service.pause_job(job) == 0
        # Java 也在动调度器之前就改了对象上的 status
        assert job.status == "1"
        assert scheduler.calls == []

    def test_resume_writes_the_normal_status_then_resumes(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        job = _job(status=Status.PAUSE.value)

        assert service.resume_job(job) == 1
        assert job.status == "0"
        assert mapper.calls[0][1].status == "0"
        assert scheduler.calls == [("resume_job", "PROBE.TASK_CLASS_NAME7")]

    def test_resume_with_zero_rows_leaves_the_scheduler_alone(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        mapper.rows = 0

        assert service.resume_job(_job(status=Status.PAUSE.value)) == 0
        assert scheduler.calls == []


class TestChangeStatus:
    def test_normal_resumes(self, service: SysJobService, mapper: _FakeJobMapper) -> None:
        assert service.change_status(_job(status="0")) == 1
        assert mapper.calls[0][0] == "update_job"

    def test_pause_pauses(self, service: SysJobService, mapper: _FakeJobMapper) -> None:
        assert service.change_status(_job(status="1")) == 1
        assert mapper.calls[0][1].status == "1"

    @pytest.mark.parametrize("status", ["2", "", None])
    def test_anything_else_returns_zero_without_touching_the_database(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
        tx: _RecordingSessionScope,
        status: Any,
    ) -> None:
        assert service.change_status(_job(status=status)) == 0
        assert mapper.calls == []
        assert scheduler.calls == []
        assert tx.opened == 0


class TestDeleteJob:
    def test_a_deleted_row_takes_its_trigger_with_it(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        assert service.delete_job(_job()) == 1
        assert mapper.calls == [("delete_job_by_id", 7)]
        assert scheduler.calls == [("delete_job", "PROBE.TASK_CLASS_NAME7")]

    def test_zero_rows_keeps_the_trigger(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        mapper.rows = 0

        assert service.delete_job(_job()) == 0
        assert scheduler.calls == []

    def test_a_null_job_is_the_java_npe(self, service: SysJobService) -> None:
        """线上 ``DELETE /monitor/job/999999`` 的 ``{"msg":null,"code":500}``."""
        with pytest.raises(AttributeError, match="job_id"):
            service.delete_job(None)

    def test_the_batch_delete_stops_at_the_first_missing_id(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        mapper.jobs[7] = _job()
        mapper.jobs[8] = _job(job_id=8)

        with pytest.raises(AttributeError):
            service.delete_job_by_ids([7, 999999, 8])

        # 7 删掉了，999999 抛 NPE，8 永远走不到（Java 的 for 循环同样中断）
        assert mapper.calls == [
            ("select_job_by_id", 7),
            ("delete_job_by_id", 7),
            ("select_job_by_id", 999999),
        ]
        assert scheduler.of("delete_job") == [("delete_job", "PROBE.TASK_CLASS_NAME7")]

    def test_the_batch_delete_walks_every_id(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        mapper.jobs[7] = _job()
        mapper.jobs[8] = _job(job_id=8)

        service.delete_job_by_ids([7, 8])

        assert scheduler.of("delete_job") == [
            ("delete_job", "PROBE.TASK_CLASS_NAME7"),
            ("delete_job", "PROBE.TASK_CLASS_NAME8"),
        ]


class TestUpdateJob:
    def test_the_old_group_is_used_to_drop_the_old_trigger(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
    ) -> None:
        """Java: ``updateSchedulerJob(job, properties.getJobGroup())`` —— 用**旧**分组."""
        mapper.jobs[7] = _job(job_group="OLD")
        scheduler.entries.clear()
        scheduler.schedule_job(
            _seed_job_detail(7, "OLD"), _seed_trigger("OLD")
        )
        scheduler.calls.clear()

        rows = service.update_job(_job(job_group="NEW", invoke_target="ryTask.ryParams('x')"))

        assert rows == 1
        # updateSchedulerJob 自己 checkExists 一次，createScheduleJob 内部**又**查一次
        assert scheduler.names() == [
            "check_exists",
            "delete_job",
            "check_exists",
            "schedule_job",
        ]
        # 删的是旧 key，建的是新 key
        assert scheduler.calls[1] == ("delete_job", "OLD.TASK_CLASS_NAME7")
        assert scheduler.calls[3][1] == "NEW.TASK_CLASS_NAME7"

    def test_zero_rows_never_touches_the_scheduler(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
    ) -> None:
        mapper.rows = 0
        mapper.jobs[7] = _job(job_group="OLD")

        assert service.update_job(_job(job_group="NEW")) == 0
        assert scheduler.calls == []

    def test_a_missing_row_returns_zero_instead_of_an_npe(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
    ) -> None:
        """``properties`` 为 ``null`` 时靠 ``rows > 0`` 兜住 —— 线上 ``PUT /monitor/job`` 的回包."""
        mapper.rows = 0

        assert service.update_job(_job(job_id=999999)) == 0
        assert scheduler.calls == []
        assert mapper.calls == [
            ("select_job_by_id", 999999),
            ("update_job", _job(job_id=999999, status="0")),
        ]

    def test_update_scheduler_job_does_not_delete_a_missing_trigger(
        self, service: SysJobService, scheduler: _FakeScheduler
    ) -> None:
        service.update_scheduler_job(_job(), "PROBE")

        assert scheduler.names() == ["check_exists", "check_exists", "schedule_job"]


class TestRun:
    def test_the_data_map_carries_the_row_loaded_from_the_database(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
    ) -> None:
        """Java: ``dataMap.put(TASK_PROPERTIES, properties)`` —— properties 是**重新查**出来的."""
        stored = _job(invoke_target="ryTask.ryParams('db')")
        mapper.jobs[7] = stored

        service.run(_job(invoke_target="ryTask.ryParams('arg')"))

        name, key, data_map = scheduler.calls[0]
        assert name == "trigger_job"
        assert key == "PROBE.TASK_CLASS_NAME7"
        assert data_map[TASK_PROPERTIES] is stored

    def test_the_key_uses_the_group_of_the_argument(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
    ) -> None:
        """投给调度器的 ``jobGroup`` 来自入参（``job.getJobGroup()``），不是库里那行."""
        mapper.jobs[7] = _job(job_group="DB_GROUP")

        service.run(_job(job_group="ARG_GROUP"))

        assert scheduler.calls[0][1] == "ARG_GROUP.TASK_CLASS_NAME7"

    def test_a_deleted_row_is_still_put_into_the_data_map_as_null(
        self,
        service: SysJobService,
        mapper: _FakeJobMapper,
        scheduler: _FakeScheduler,
    ) -> None:
        """``selectJobById`` 回 ``null`` 时没有判空，``put`` 进去就是 ``null``."""
        service.run(_job(job_id=999999))

        data_map = scheduler.calls[0][2]
        assert TASK_PROPERTIES in data_map
        assert data_map[TASK_PROPERTIES] is None


class TestInit:
    def test_the_store_is_cleared_then_rebuilt(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        """``@PostConstruct`` —— 先 ``scheduler.clear()`` 再逐条重建."""
        mapper.all_jobs = [_job(), _job(job_id=8)]
        scheduler.entries[object()] = None  # 脏数据：启动时应被 clear 掉

        service.init()

        assert scheduler.names()[0] == "clear"
        assert len(scheduler.entries) == 2
        assert mapper.calls == [("select_job_all",)]

    def test_paused_rows_are_registered_as_paused(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        mapper.all_jobs = [_job(status="1")]

        service.init()

        assert scheduler.of("pause_job") == [("pause_job", "PROBE.TASK_CLASS_NAME7")]

    def test_an_empty_table_leaves_an_empty_scheduler(
        self, service: SysJobService, mapper: _FakeJobMapper, scheduler: _FakeScheduler
    ) -> None:
        service.init()

        assert scheduler.names() == ["clear"]


class TestQueries:
    def test_select_job_list_delegates(
        self, service: SysJobService, mapper: _FakeJobMapper
    ) -> None:
        query = _job()

        assert service.select_job_list(query) == [query]
        assert mapper.calls == [("select_job_list", query)]

    def test_select_job_by_id_delegates(
        self, service: SysJobService, mapper: _FakeJobMapper
    ) -> None:
        mapper.jobs[7] = _job()

        assert service.select_job_by_id(7).job_id == 7
        assert service.select_job_by_id(8) is None

    def test_check_cron_expression_is_valid(self, service: SysJobService) -> None:
        """Java 里这个方法**没有调用点**，但照抄."""
        assert service.check_cron_expression_is_valid("0 0 2 * * ?") is True
        assert service.check_cron_expression_is_valid("0 0 2 * *") is False


class TestJobServiceSingleton:
    def test_get_job_service_caches(self) -> None:
        first = get_job_service()

        assert get_job_service() is first
        assert isinstance(first, SysJobService)

    def test_reset_drops_the_cache(self) -> None:
        first = get_job_service()
        reset_job_service()

        assert get_job_service() is not first


# =========================================================================== SysJobLogService


class TestJobLogService:
    @pytest.fixture
    def log_mapper(self) -> _FakeJobLogMapper:
        return _FakeJobLogMapper()

    @pytest.fixture
    def log_service(self, log_mapper: _FakeJobLogMapper) -> SysJobLogService:
        return SysJobLogService(mapper=log_mapper)

    def test_every_method_is_a_pure_delegation(
        self, log_service: SysJobLogService, log_mapper: _FakeJobLogMapper
    ) -> None:
        """六个方法体全是 ``return jobLogMapper.xxx(...)``，没有任何业务判断."""
        log = SysJobLog(job_log_id=3, job_name="探测任务")
        log_mapper.logs = [log]

        assert log_service.select_job_log_list(log) == [log]
        assert log_service.select_job_log_by_id(3) is log
        assert log_service.add_job_log(log) == 1
        assert log_service.delete_job_log_by_ids([3, 4]) == 1
        assert log_service.delete_job_log_by_id(3) == 1
        assert log_service.clean_job_log() is None

        assert [call[0] for call in log_mapper.calls] == [
            "select_job_log_list",
            "select_job_log_by_id",
            "insert_job_log",
            "delete_job_log_by_ids",
            "delete_job_log_by_id",
            "clean_job_log",
        ]

    def test_the_id_lists_are_passed_through_as_lists(
        self, log_service: SysJobLogService, log_mapper: _FakeJobLogMapper
    ) -> None:
        log_service.delete_job_log_by_ids([3, 4, 5])

        assert log_mapper.calls[0] == ("delete_job_log_by_ids", [3, 4, 5])

    def test_a_missing_log_is_null_not_an_exception(
        self, log_service: SysJobLogService
    ) -> None:
        assert log_service.select_job_log_by_id(404) is None

    def test_the_mapper_is_exposed(self, log_mapper: _FakeJobLogMapper) -> None:
        assert SysJobLogService(mapper=log_mapper).mapper is log_mapper


class TestJobLogServiceBean:
    def test_the_bean_name_is_the_java_interface_simple_name(self) -> None:
        """``SpringUtils.getBean(ISysJobLogService.class)`` 的键."""
        assert JOB_LOG_BEAN_NAME == "ISysJobLogService"

    def test_get_job_log_service_registers_itself(self) -> None:
        service = get_job_log_service()

        assert isinstance(service, SysJobLogService)
        assert SpringUtils.get_bean(JOB_LOG_BEAN_NAME) is service
        # 按**类型**取也要命中 —— AbstractQuartzJob 就是这么取的
        assert SpringUtils.get_bean(SysJobLogService) is service
        assert get_job_log_service() is service

    def test_reset_unregisters_the_bean(self) -> None:
        get_job_log_service()
        reset_job_log_service()

        with pytest.raises(SpringUtils.NoSuchBeanDefinitionException) as raised:
            SpringUtils.get_bean(JOB_LOG_BEAN_NAME)

        assert str(raised.value) == "No bean named 'ISysJobLogService' available"
        assert get_job_log_service() is not None


# --------------------------------------------------------------------------- 辅助


def _seed_job_detail(job_id: int, job_group: str) -> Any:
    from app.quartz.util.schedule_utils import get_job_key
    from app.quartz.util.scheduler import JobBuilder
    from app.quartz.util.quartz_job_execution import QuartzJobExecution

    return JobBuilder.new_job(QuartzJobExecution).with_identity(get_job_key(job_id, job_group)).build()


def _seed_trigger(job_group: str) -> Any:
    from app.quartz.util.schedule_utils import get_trigger_key
    from app.quartz.util.scheduler import CronScheduleBuilder, TriggerBuilder

    return (
        TriggerBuilder.new_trigger()
        .with_identity(get_trigger_key(7, job_group))
        .with_schedule(CronScheduleBuilder.cron_schedule("0 0 2 * * ?"))
        .build()
    )
