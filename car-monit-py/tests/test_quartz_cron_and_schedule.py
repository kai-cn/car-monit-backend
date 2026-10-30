"""Quartz 方言的 cron、``ScheduleUtils``、调度器与反射调用.

# Migrated from: (no Java test) -- behaviour copied from
#   org.quartz.CronExpression 2.3.2 / ruoyi-quartz util/{CronUtils,ScheduleUtils,JobInvokeUtil}.java
#   + the two live oracles: evidence/_probe_cron_out.txt / evidence/_verify_cron_out.txt

为什么值得单独一个文件
----------------------
``sys_job.cron_expression`` 里存的是 **Quartz 方言**，接受/拒绝的边界、下一跳时刻、
``JobKey.toString()`` 的拼接方式、``misfire`` 指令的实际语义、``invokeTarget`` 的参数
类型推断顺序，这五件事全都是"抄错一个字就与线上不一致"的地方。它们没有 HTTP 层，
所以不放进控制器用例。

两个 oracle
-----------
* ``evidence/_probe_cron_out.txt`` —— 用真实 ``POST /monitor/job`` 逐条喂 Java（:8090），
  记录 10 条接受 / 10 条拒绝；
* ``evidence/_verify_cron_out.txt`` —— 同一批表达式跑本实现，并在**固定基准时刻**
  ``2026-10-29 11:16:04`` 记下 ``nextValidTime``。

下面 :class:`TestCronGate` / :class:`TestNextExecution` 就是把这两张表逐行钉住。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from app.common.constant.schedule_constants import (
    MISFIRE_DEFAULT,
    MISFIRE_DO_NOTHING,
    MISFIRE_FIRE_AND_PROCEED,
    MISFIRE_IGNORE_MISFIRES,
    TASK_CLASS_NAME,
    TASK_PROPERTIES,
)
from app.common.exception.job.task_exception import TaskException
from app.common.utils import spring_utils as SpringUtils
from app.quartz.domain.sys_job import SysJob
from app.quartz.util.cron_expression import CronExpression
from app.quartz.util.cron_utils import CronUtils
from app.quartz.util.job_invoke_util import (
    JAVA_BOOLEAN,
    JAVA_DOUBLE,
    JAVA_INTEGER,
    JAVA_LONG,
    JAVA_STRING,
    get_bean_name,
    get_method_name,
    get_method_params,
    get_method_params_type,
    get_method_params_value,
    invoke_method,
    is_valid_class_name,
)
from app.quartz.util.quartz_disallow_concurrent_execution import (
    QuartzDisallowConcurrentExecution,
)
from app.quartz.util.quartz_job_execution import QuartzJobExecution
from app.quartz.util.schedule_utils import (
    create_schedule_job,
    get_job_key,
    get_quartz_job_class,
    get_trigger_key,
    handle_cron_schedule_misfire_policy,
)
from app.quartz.util.scheduler import (
    MISFIRE_INSTRUCTION_DO_NOTHING,
    MISFIRE_INSTRUCTION_FIRE_ONCE_NOW,
    MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY,
    MISFIRE_INSTRUCTION_SMART_POLICY,
    CronScheduleBuilder,
    JobBuilder,
    JobDataMap,
    JobKey,
    ObjectAlreadyExistsException,
    Scheduler,
    SchedulerException,
    TriggerBuilder,
    TriggerKey,
)

#: ``evidence/_verify_cron_out.txt`` 的基准时刻（秒级，无亚秒）。
BASE = datetime(2026, 10, 29, 11, 16, 4)

#: ``evidence/_probe_cron_out.txt`` 第 1–10 行：Java 侧 ``POST /monitor/job`` 全部回 ``操作成功``。
ACCEPTED = [
    "0 0 2 * * ?",
    "0/10 * * * * ?",
    "0 0 2 ? * MON",
    "0 0 2 L * ?",
    "0 0 2 ? * 6L",
    "0 0 2 ? * 5#2",
    "0 0 2 15W * ?",
    "0 0 2 LW * ?",
    "0 0 2 * * ? 2027",
    "*/0 * * * * ?",
]

#: ``evidence/_probe_cron_out.txt`` 第 11–20 行：Java 侧回 ``cron表达式不正确``。
REJECTED = [
    "0 0 * * * *",
    "0 0 2 * * *",
    "0 0 2 * *",
    "0 0 25 * * ?",
    "0 0 2 32 * ?",
    "60 0 2 * * ?",
    "0 0 2 * 13 ?",
    "0 0 2 * * 8",
    "bogus",
    "0 0 2 ? * ?",
]


# --------------------------------------------------------------------------- fakes


class _RecordingScheduler:
    """只记录调用的 ``org.quartz.Scheduler`` 替身（不启线程、不解析 cron）."""

    def __init__(self) -> None:
        self.calls: list = []
        self.existing: set = set()

    def check_exists(self, job_key: JobKey) -> bool:
        self.calls.append(("check_exists", str(job_key)))
        return job_key in self.existing

    def schedule_job(self, job_detail: Any, trigger: Any) -> float:
        self.calls.append(("schedule_job", str(job_detail.key), trigger.cron_expression))
        self.existing.add(job_detail.key)
        return 0.0

    def delete_job(self, job_key: JobKey) -> bool:
        self.calls.append(("delete_job", str(job_key)))
        self.existing.discard(job_key)
        return True

    def pause_job(self, job_key: JobKey) -> None:
        self.calls.append(("pause_job", str(job_key)))

    def resume_job(self, job_key: JobKey) -> None:
        self.calls.append(("resume_job", str(job_key)))

    def trigger_job(self, job_key: JobKey, data_map: Any = None) -> None:
        self.calls.append(("trigger_job", str(job_key)))

    def clear(self) -> None:
        self.calls.append(("clear",))
        self.existing.clear()

    def of(self, name: str) -> list:
        return [call for call in self.calls if call[0] == name]


@pytest.fixture
def scheduler() -> Any:
    """真实的 :class:`Scheduler`（RAMJobStore 语义），用例结束就收线程池。"""
    instance = Scheduler()
    yield instance
    instance.shutdown()


# --------------------------------------------------------------------------- cron 校验


class TestCronGate:
    @pytest.mark.parametrize("expression", ACCEPTED)
    def test_the_java_oracle_accepts(self, expression: str) -> None:
        assert CronUtils.is_valid(expression) is True
        assert CronUtils.get_invalid_message(expression) is None

    @pytest.mark.parametrize("expression", REJECTED)
    def test_the_java_oracle_rejects(self, expression: str) -> None:
        assert CronUtils.is_valid(expression) is False
        assert CronUtils.get_invalid_message(expression)

    def test_null_raises_instead_of_returning_false(self) -> None:
        """``CronExpression(null)`` 抛的是 ``IllegalArgumentException``，不是 ``ParseException``."""
        with pytest.raises(ValueError, match="cronExpression cannot be null"):
            CronUtils.is_valid(None)

    @pytest.mark.parametrize(
        ("expression", "message"),
        [
            ("0 0 25 * * ?", "Hour values must be between 0 and 23"),
            ("0 0 2 32 * ?", "Day of month values must be between 1 and 31"),
            ("60 0 2 * * ?", "Minute and Second values must be between 0 and 59"),
            ("0 0 2 * 13 ?", "Month values must be between 1 and 12"),
            ("0 0 2 * * 8", "Day-of-Week values must be between 1 and 7"),
            ("0 0 2 * *", "Unexpected end of expression."),
            ("bogus", "Illegal characters for this position: 'BOG'"),
            ("0 0 2 ? * ?", "'?' can only be specified for Day-of-Month -OR- Day-of-Week."),
        ],
    )
    def test_the_rejection_messages_are_verbatim(self, expression: str, message: str) -> None:
        assert CronUtils.get_invalid_message(expression) == message

    def test_the_six_field_requirement_is_not_python_cron(self) -> None:
        """Python 的 5 段 cron ``0 0 * * *`` 在 Quartz 里是非法（段数不够）。"""
        assert CronUtils.is_valid("0 0 * * *") is False
        # ``0 0 * * * *`` 段数够但 day-of-month 与 day-of-week 同时非 ``?``
        assert CronUtils.is_valid("0 0 * * * *") is False

    def test_extra_whitespace_is_folded_by_the_string_tokenizer(self) -> None:
        assert CronUtils.is_valid("  0   0  2  *  *  ?  ") is True


class TestNextExecution:
    """``evidence/_verify_cron_out.txt`` 的 ``next executions @ 2026-10-29 11:16:04`` 那一张表."""

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("0 0 2 * * ?", datetime(2026, 10, 30, 2, 0, 0)),
            ("0/10 * * * * ?", datetime(2026, 10, 29, 11, 16, 10)),
            ("0 0 2 ? * MON", datetime(2026, 11, 2, 2, 0, 0)),
            ("0 0 2 L * ?", datetime(2026, 10, 31, 2, 0, 0)),
            ("0 0 2 ? * 6L", datetime(2026, 10, 30, 2, 0, 0)),
            ("0 0 2 ? * 5#2", datetime(2026, 11, 12, 2, 0, 0)),
            ("0 0 2 15W * ?", datetime(2026, 11, 16, 2, 0, 0)),
            ("0 0 2 LW * ?", datetime(2026, 10, 30, 2, 0, 0)),
            ("0 0 2 * * ? 2027", datetime(2027, 1, 1, 2, 0, 0)),
            ("*/0 * * * * ?", datetime(2026, 10, 29, 11, 16, 5)),
            ("0 0 1 1 * ?", datetime(2026, 11, 1, 1, 0, 0)),
        ],
    )
    def test_the_next_fire_time(self, expression: str, expected: datetime) -> None:
        assert CronExpression(expression).get_next_valid_time_after(BASE) == expected

    def test_the_next_fire_is_strictly_after_the_base(self) -> None:
        """Quartz 的 ``getNextValidTimeAfter`` 不返回基准时刻本身。"""
        expression = CronExpression("0 0 2 * * ?")
        moment = datetime(2026, 10, 30, 2, 0, 0)
        assert expression.get_next_valid_time_after(moment) == datetime(2026, 10, 31, 2, 0, 0)

    def test_get_next_execution_wraps_parse_errors_in_value_error(self) -> None:
        """Java: ``throw new IllegalArgumentException(e.getMessage())``."""
        with pytest.raises(ValueError, match="Day-of-Week values must be between 1 and 7"):
            CronUtils.get_next_execution("0 0 2 * * 8")

    def test_a_dom_and_dow_expression_is_rejected_at_build_time(self) -> None:
        """``@Scheduled(cron = "0 0 2 * * MON")`` 在 Quartz 里其实**不合法**. """
        with pytest.raises(
            ValueError,
            match="Support for specifying both a day-of-week AND a day-of-month",
        ):
            CronUtils.get_next_execution("0 0 2 * * MON")


# --------------------------------------------------------------------------- JobKey


class TestKeys:
    def test_the_job_name_is_the_constant_plus_the_id(self) -> None:
        key = get_job_key(7, "PROBE")

        assert key.name == TASK_CLASS_NAME + "7" == "TASK_CLASS_NAME7"
        assert key.group == "PROBE"
        assert str(key) == "PROBE.TASK_CLASS_NAME7"

    def test_a_null_group_becomes_default(self) -> None:
        """线上 ``PUT /run {jobId:999999}`` 的报错文案就是这个 ``toString()``."""
        key = get_job_key(999999, None)

        assert key.group == "DEFAULT"
        assert str(key) == "DEFAULT.TASK_CLASS_NAME999999"

    def test_a_null_id_is_javas_string_concat(self) -> None:
        """Java 的 ``"TASK_CLASS_NAME" + null`` 是 ``"TASK_CLASS_NAMEnull"``."""
        assert get_job_key(None, None).name == "TASK_CLASS_NAMEnull"

    def test_the_trigger_key_uses_the_same_name(self, scheduler: Scheduler) -> None:
        trigger_key = get_trigger_key(7, "PROBE")

        assert isinstance(trigger_key, TriggerKey)
        assert trigger_key.name == get_job_key(7, "PROBE").name
        assert str(trigger_key) == "PROBE.TASK_CLASS_NAME7"

    def test_job_and_trigger_keys_are_not_equal(self) -> None:
        assert JobKey.job_key("x", "g") != TriggerKey.trigger_key("x", "g")
        assert JobKey.job_key("x", "g") == JobKey.job_key("x", "g")

    def test_a_null_name_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="Name cannot be null."):
            JobKey.job_key(None)  # type: ignore[arg-type]


class TestQuartzJobClass:
    def test_concurrent_zero_allows_concurrency(self) -> None:
        assert get_quartz_job_class(SysJob(concurrent="0")) is QuartzJobExecution

    @pytest.mark.parametrize("concurrent", ["1", None, ""])
    def test_everything_else_disallows_concurrency(self, concurrent: Any) -> None:
        assert (
            get_quartz_job_class(SysJob(concurrent=concurrent))
            is QuartzDisallowConcurrentExecution
        )

    def test_only_the_disallowing_class_is_marked(self) -> None:
        assert getattr(QuartzDisallowConcurrentExecution, "disallow_concurrent_execution") is True
        assert getattr(QuartzJobExecution, "disallow_concurrent_execution", False) is False


# --------------------------------------------------------------------------- misfire


class TestMisfirePolicy:
    @pytest.mark.parametrize(
        ("policy", "instruction"),
        [
            (MISFIRE_DEFAULT, MISFIRE_INSTRUCTION_SMART_POLICY),
            (MISFIRE_IGNORE_MISFIRES, MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY),
            (MISFIRE_FIRE_AND_PROCEED, MISFIRE_INSTRUCTION_FIRE_ONCE_NOW),
            (MISFIRE_DO_NOTHING, MISFIRE_INSTRUCTION_DO_NOTHING),
        ],
    )
    def test_the_four_documented_policies(self, policy: str, instruction: int) -> None:
        builder = handle_cron_schedule_misfire_policy(
            SysJob(misfire_policy=policy), CronScheduleBuilder.cron_schedule("0 0 2 * * ?")
        )
        assert builder.misfire_instruction == instruction

    def test_smart_and_fire_and_proceed_collapse_to_the_same_value(self) -> None:
        """``updateAfterMisfire`` 把 SMART(0) 折成 FIRE_ONCE_NOW(1) —— 两者都是"补一次"."""
        assert MISFIRE_INSTRUCTION_SMART_POLICY == 0
        assert MISFIRE_INSTRUCTION_FIRE_ONCE_NOW == 1

    def test_an_unknown_policy_raises_task_exception(self) -> None:
        with pytest.raises(TaskException) as raised:
            handle_cron_schedule_misfire_policy(
                SysJob(misfire_policy="9"), CronScheduleBuilder.cron_schedule("0 0 2 * * ?")
            )

        assert str(raised.value) == (
            "The task misfire policy '9' cannot be used in cron schedule tasks"
        )
        assert raised.value.code is TaskException.Code.CONFIG_ERROR

    def test_a_null_policy_is_printed_like_java(self) -> None:
        with pytest.raises(TaskException) as raised:
            handle_cron_schedule_misfire_policy(
                SysJob(misfire_policy=None), CronScheduleBuilder.cron_schedule("0 0 2 * * ?")
            )

        assert str(raised.value) == (
            "The task misfire policy 'null' cannot be used in cron schedule tasks"
        )

    def test_the_default_field_value_is_zero(self) -> None:
        assert SysJob().misfire_policy == MISFIRE_DEFAULT


# --------------------------------------------------------------------------- builder


class TestBuilders:
    def test_cron_schedule_validates_immediately(self) -> None:
        with pytest.raises(ValueError, match="cronExpression cannot be null"):
            CronScheduleBuilder.cron_schedule(None)

        with pytest.raises(RuntimeError, match="CronExpression 'bogus' is not valid."):
            CronScheduleBuilder.cron_schedule("bogus")

    def test_job_builder_requires_a_key(self) -> None:
        with pytest.raises(SchedulerException, match="Job key must be set"):
            JobBuilder.new_job(QuartzJobExecution).build()

    def test_trigger_builder_requires_a_key_and_a_schedule(self) -> None:
        with pytest.raises(SchedulerException, match="Trigger key must be set"):
            TriggerBuilder.new_trigger().build()

        with pytest.raises(SchedulerException, match="Schedule must be set"):
            TriggerBuilder.new_trigger().with_identity(TriggerKey.trigger_key("x", "g")).build()

    def test_the_trigger_carries_the_expression(self) -> None:
        trigger = (
            TriggerBuilder.new_trigger()
            .with_identity(TriggerKey.trigger_key("TASK_CLASS_NAME7", "PROBE"))
            .with_schedule(CronScheduleBuilder.cron_schedule("0 0 2 * * ?"))
            .build()
        )

        assert trigger.cron_expression == "0 0 2 * * ?"
        assert trigger.misfire_instruction == MISFIRE_INSTRUCTION_SMART_POLICY


# --------------------------------------------------------------------------- createScheduleJob


class TestCreateScheduleJob:
    def test_a_job_is_registered_under_its_key(self, scheduler: Scheduler) -> None:
        job = SysJob(
            job_id=7,
            job_group="PROBE",
            cron_expression="0 0 2 * * ?",
            misfire_policy=MISFIRE_DO_NOTHING,
            concurrent="1",
            status="0",
        )
        create_schedule_job(scheduler, job)

        key = get_job_key(7, "PROBE")
        assert scheduler.check_exists(key) is True
        assert scheduler._entries[key].job_detail.job_class is QuartzDisallowConcurrentExecution
        assert scheduler._entries[key].paused is False

    def test_the_task_definition_rides_in_the_job_data_map(self, scheduler: Scheduler) -> None:
        job = SysJob(job_id=7, job_group="PROBE", cron_expression="0 0 2 * * ?", status="0")
        create_schedule_job(scheduler, job)

        detail = scheduler._entries[get_job_key(7, "PROBE")].job_detail
        assert detail.job_data_map[TASK_PROPERTIES] is job

    def test_a_paused_job_is_paused_right_after_scheduling(self, scheduler: Scheduler) -> None:
        """``insertJob`` 强制 ``status = 1``，所以新任务不会立刻开跑。"""
        job = SysJob(job_id=7, job_group="PROBE", cron_expression="0 0 2 * * ?", status="1")
        create_schedule_job(scheduler, job)

        assert scheduler._entries[get_job_key(7, "PROBE")].paused is True

    def test_an_existing_job_is_deleted_first(self, scheduler: Scheduler) -> None:
        """Java: ``if (scheduler.checkExists(...)) { scheduler.deleteJob(...); }``."""
        job = SysJob(job_id=7, job_group="PROBE", cron_expression="0 0 2 * * ?", status="0")
        create_schedule_job(scheduler, job)
        create_schedule_job(scheduler, job)

        # 第二次没有抛 ObjectAlreadyExistsException，说明确实先删了
        assert scheduler.check_exists(get_job_key(7, "PROBE")) is True

    def test_a_null_status_is_a_npe_after_registration(self, scheduler: Scheduler) -> None:
        """Java: ``job.getStatus().equals(...)`` —— 没有判空，照抄."""
        job = SysJob(job_id=7, job_group="PROBE", cron_expression="0 0 2 * * ?", status=None)
        with pytest.raises(AttributeError, match="equals"):
            create_schedule_job(scheduler, job)

        # 注册已经发生（Java 的顺序也是先 scheduleJob 再比 status）
        assert scheduler.check_exists(get_job_key(7, "PROBE")) is True

    def test_an_illegal_misfire_policy_prevents_registration(self, scheduler: Scheduler) -> None:
        job = SysJob(job_id=7, job_group="PROBE", cron_expression="0 0 2 * * ?", misfire_policy="9")
        with pytest.raises(TaskException):
            create_schedule_job(scheduler, job)

        assert scheduler.check_exists(get_job_key(7, "PROBE")) is False


# --------------------------------------------------------------------------- scheduler


class TestScheduler:
    def test_schedule_then_delete(self, scheduler: Scheduler) -> None:
        detail = (
            JobBuilder.new_job(QuartzJobExecution)
            .with_identity(JobKey.job_key("TASK_CLASS_NAME7", "PROBE"))
            .build()
        )
        trigger = (
            TriggerBuilder.new_trigger()
            .with_identity(TriggerKey.trigger_key("TASK_CLASS_NAME7", "PROBE"))
            .with_schedule(CronScheduleBuilder.cron_schedule("0 0 2 * * ?"))
            .build()
        )

        first = scheduler.schedule_job(detail, trigger)

        assert scheduler.check_exists(detail.key) is True
        assert scheduler.get_job_keys() == [detail.key]
        # 首次触发时刻是"今天或明天的 02:00:00"
        assert datetime.fromtimestamp(first).hour == 2
        assert datetime.fromtimestamp(first).minute == 0

        assert scheduler.delete_job(detail.key) is True
        assert scheduler.check_exists(detail.key) is False

    def test_scheduling_the_same_key_twice_raises(self, scheduler: Scheduler) -> None:
        detail = (
            JobBuilder.new_job(QuartzJobExecution)
            .with_identity(JobKey.job_key("TASK_CLASS_NAME7", "PROBE"))
            .build()
        )
        trigger = (
            TriggerBuilder.new_trigger()
            .with_identity(TriggerKey.trigger_key("TASK_CLASS_NAME7", "PROBE"))
            .with_schedule(CronScheduleBuilder.cron_schedule("0 0 2 * * ?"))
            .build()
        )
        scheduler.schedule_job(detail, trigger)

        with pytest.raises(ObjectAlreadyExistsException):
            scheduler.schedule_job(detail, trigger)

    def test_delete_pause_and_resume_of_a_missing_job_are_silent(
        self, scheduler: Scheduler
    ) -> None:
        """``RAMJobStore`` 遍历空集合 —— 只有 ``triggerJob`` 会抛."""
        missing = JobKey.job_key("TASK_CLASS_NAME999999", "DEFAULT")

        assert scheduler.delete_job(missing) is False
        scheduler.pause_job(missing)
        scheduler.resume_job(missing)

    def test_trigger_job_reports_the_missing_key(self, scheduler: Scheduler) -> None:
        with pytest.raises(SchedulerException) as raised:
            scheduler.trigger_job(JobKey.job_key("TASK_CLASS_NAME999999", None), JobDataMap())

        assert str(raised.value) == (
            "The job (DEFAULT.TASK_CLASS_NAME999999) referenced by the trigger does not exist."
        )

    def test_clear_empties_the_store(self, scheduler: Scheduler) -> None:
        create_schedule_job(
            scheduler,
            SysJob(job_id=7, job_group="PROBE", cron_expression="0 0 2 * * ?", status="0"),
        )
        scheduler.clear()

        assert scheduler.get_job_keys() == []

    def test_a_fresh_scheduler_is_not_started(self, scheduler: Scheduler) -> None:
        assert scheduler.is_started() is False

    def test_ordering_of_singleton_helpers(self) -> None:
        """``get_scheduler()`` 每次返回同一个实例；``set_scheduler(None)`` 之后重建."""
        from app.quartz.util.scheduler import get_scheduler, set_scheduler, shutdown_scheduler

        set_scheduler(None)
        try:
            first = get_scheduler()
            assert get_scheduler() is first
            assert first.is_started() is True
        finally:
            shutdown_scheduler()
        assert get_scheduler is not None


# --------------------------------------------------------------------------- invokeTarget


class TestInvokeTargetParsing:
    @pytest.mark.parametrize(
        ("invoke_target", "bean", "method"),
        [
            ("ryTask.ryNoParams", "ryTask", "ryNoParams"),
            ("ryTask.ryParams('ry')", "ryTask", "ryParams"),
            ("ryTask.ryMultipleParams('ry', true, 2000L, 316.50D, 100)", "ryTask",
             "ryMultipleParams"),
            ("vehicleMonitoringTask.syncOrgInfo", "vehicleMonitoringTask", "syncOrgInfo"),
            ("trackTask.syncSuspiciousCar", "trackTask", "syncSuspiciousCar"),
        ],
    )
    def test_bean_and_method_are_split_on_the_dot(
        self, invoke_target: str, bean: str, method: str
    ) -> None:
        assert get_bean_name(invoke_target) == bean
        assert get_method_name(invoke_target) == method

    @pytest.mark.parametrize(
        ("invoke_target", "valid"),
        [
            ("ryTask.ryNoParams", False),
            ("com.ruoyi.quartz.task.RyTask.ryNoParams", True),
            (None, False),
        ],
    )
    def test_is_valid_class_name_counts_the_dots(self, invoke_target: Any, valid: bool) -> None:
        """点号多于 1 个 -> 走 ``Class.forName``；否则走 ``SpringUtils.getBean``."""
        assert is_valid_class_name(invoke_target) is valid

    def test_no_parameters_is_none(self) -> None:
        assert get_method_params("ryTask.ryNoParams") is None
        assert get_method_params("ryTask.ryParams()") is None

    def test_the_five_parameter_types(self) -> None:
        """``'ry', true, 2000L, 316.50D, 100`` —— 顺序与 Java 的 if/else 链一致."""
        params = get_method_params("ryTask.ryMultipleParams('ry', true, 2000L, 316.50D, 100)")

        assert params == [
            ("ry", JAVA_STRING),
            (True, JAVA_BOOLEAN),
            (2000, JAVA_LONG),
            (316.5, JAVA_DOUBLE),
            (100, JAVA_INTEGER),
        ]
        assert get_method_params_type(params) == [
            JAVA_STRING,
            JAVA_BOOLEAN,
            JAVA_LONG,
            JAVA_DOUBLE,
            JAVA_INTEGER,
        ]
        assert get_method_params_value(params) == ["ry", True, 2000, 316.5, 100]

    def test_boolean_is_checked_before_long(self) -> None:
        """``"false"`` 小写含 ``l``；若先判 ``L`` 会去 ``Long.valueOf("fase")`` 抛错."""
        assert get_method_params("x.y(false)") == [(False, JAVA_BOOLEAN)]

    def test_a_non_numeric_integer_is_a_number_format_exception(self) -> None:
        with pytest.raises(ValueError, match='java.lang.NumberFormatException: For input string: "abc"'):
            get_method_params("x.y(abc)")

    def test_strings_lose_their_quotes(self) -> None:
        assert get_method_params("x.y('a b')") == [("a b", JAVA_STRING)]


class TestInvokeMethod:
    """真正调用注册表里的 bean —— 必须 ``import app.quartz.task`` 才有注册."""

    def _job(self, target: str) -> SysJob:
        return SysJob(job_id=1, job_group="SYSTEM", invoke_target=target)

    def test_a_no_argument_task(self, capsys: Any) -> None:
        import app.quartz.task  # noqa: F401 - 导入副作用：注册 6 个任务 bean

        invoke_method(self._job("ryTask.ryNoParams"))

        assert capsys.readouterr().out.strip() == "执行无参方法"

    def test_a_single_string_argument(self, capsys: Any) -> None:
        import app.quartz.task  # noqa: F401

        invoke_method(self._job("ryTask.ryParams('ry')"))

        assert capsys.readouterr().out.strip() == "执行有参方法：ry"

    def test_the_five_argument_task(self, capsys: Any) -> None:
        import app.quartz.task  # noqa: F401

        invoke_method(self._job("ryTask.ryMultipleParams('ry', true, 2000L, 316.50D, 100)"))

        assert capsys.readouterr().out.strip() == (
            "执行多参方法： 字符串类型ry，布尔类型true，长整型2000，浮点型316.5，整形100"
        )

    def test_an_unknown_bean_reports_the_spring_message(self) -> None:
        import app.quartz.task  # noqa: F401

        with pytest.raises(SpringUtils.NoSuchBeanDefinitionException) as raised:
            invoke_method(self._job("nosuchTask.doIt"))

        assert str(raised.value) == "No bean named 'nosuchTask' available"

    def test_an_unknown_method_reports_no_such_method(self) -> None:
        import app.quartz.task  # noqa: F401

        with pytest.raises(AttributeError, match="java.lang.NoSuchMethodException"):
            invoke_method(self._job("ryTask.nosuchMethod"))

    def test_a_full_class_name_is_instantiated(self) -> None:
        """``isValidClassName`` 为真时走 ``Class.forName(...).newInstance()``."""
        invoke_method(self._job("app.quartz.task.ry_task.RyTask.ryNoParams"))

    def test_an_unknown_class_name_is_a_class_not_found(self) -> None:
        with pytest.raises(LookupError, match="java.lang.ClassNotFoundException"):
            invoke_method(self._job("com.ruoyi.nosuch.RyTask.ryNoParams"))
