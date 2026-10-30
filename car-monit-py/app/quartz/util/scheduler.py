"""Quartz 调度器的最小等价实现.

# Migrated from: org.quartz（第三方库 org.quartz-scheduler:quartz 2.3.2，非本工程源码）

本工程对 Quartz 的**全部**用法都在
:mod:`app.quartz.util.schedule_utils` 和 :mod:`app.quartz.service.sys_job_service` 里，
加起来只有 12 个 API。这里按 Quartz 2.3.2 的语义实现这 12 个，而不是引入一个
Python 调度库 —— 换库意味着 ``JobKey.toString()``、``SchedulerException`` 的文案、
"删除不存在的任务不报错"这些**可观察行为**都会漂移。

被复刻的行为清单
----------------
    ==============================  ======================================
    Quartz                          Python
    ==============================  ======================================
    ``JobKey.jobKey(name, group)``           :class:`JobKey`
    ``TriggerKey.triggerKey(name, group)``   :class:`TriggerKey`
    ``Key.toString()`` -> ``group.name``     ``JobKey.__str__``
    ``Scheduler.checkExists(JobKey)``        :meth:`Scheduler.check_exists`
    ``Scheduler.deleteJob(JobKey)``          :meth:`Scheduler.delete_job`
    ``Scheduler.scheduleJob(JobDetail,
    Trigger)``                               :meth:`Scheduler.schedule_job`
    ``Scheduler.pauseJob(JobKey)``           :meth:`Scheduler.pause_job`
    ``Scheduler.resumeJob(JobKey)``          :meth:`Scheduler.resume_job`
    ``Scheduler.triggerJob(JobKey, dataMap)`` :meth:`Scheduler.trigger_job`
    ``Scheduler.clear()``                    :meth:`Scheduler.clear`
    ``JobDetail.getJobDataMap()``            :attr:`JobDetail.job_data_map`
    ``JobExecutionContext#getMergedJobDataMap()``
                                             :attr:`JobExecutionContext.merged_job_data_map`
    ==============================  ======================================

三个必须照抄的细节
------------------
1. **``Key`` 的 group 可以为 null**。``ScheduleUtils.getJobKey(jobId, jobGroup)`` 里
   ``jobGroup`` 直接来自请求体，``POST /monitor/job`` 不带 ``jobGroup`` 时是 ``null``。
   Quartz 的 ``Key(String name, String group)`` 把 null 换成 ``"DEFAULT"``，所以 job name
   是 ``"TASK_CLASS_NAME7"`` 而 group 是 ``"DEFAULT"`` —— 线上报错
   ``The job (DEFAULT.TASK_CLASS_NAME999999) referenced by the trigger does not exist.``
   就是这个 ``toString()`` 拼出来的。
2. **``pauseJob`` / ``resumeJob`` / ``deleteJob`` 对不存在的 key 不抛异常**
   （``RAMJobStore`` 内部遍历空集合）。只有 ``triggerJob`` 会抛
   ``SchedulerException``，文案见 :meth:`Scheduler.trigger_job`。
3. **``misfire`` 指令**。``CronScheduleBuilder`` 的默认值是
   ``MISFIRE_INSTRUCTION_SMART_POLICY``(0)，``CronTriggerImpl#updateAfterMisfire`` 把
   SMART 折成 ``FIRE_ONCE_NOW``(1)；``withMisfireHandlingInstructionDoNothing()`` 是 2；
   ``withMisfireHandlingInstructionIgnoreMisfires()`` 是 -1；``...FireAndProceed()`` 也是 1。
   因此 ``sys_job.misfire_policy`` 的三个"有值"分支在实际行为上只区分
   **"补一次"** 与 **"跳过"** 两类。

``misfireThreshold`` 取 Quartz 默认的 60000 ms（``org.quartz.jobStore.misfireThreshold``
未在 ``application.yml`` 里配置）。

``@DisallowConcurrentExecution``
--------------------------------
``SysJob.concurrent != "0"`` 时任务类带这个注解，Quartz 不会让**同一个** JobDetail
并发执行。这里用一把 per-job 锁：锁被占住就**推迟**本次触发（保留 fire time，下个
tick 再试）；推迟超过 ``misfireThreshold`` 后按 misfire 指令处理 —— 与
``QuartzSchedulerThread`` 先 ``acquireNextTriggers`` 后 ``releaseIfScheduleChangedSignificantly``
的结果一致。
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.quartz.util.cron_expression import CronExpression

logger = logging.getLogger("app.quartz.scheduler")

#: Java: ``Key.DEFAULT_GROUP``
DEFAULT_GROUP = "DEFAULT"

#: Java: ``Trigger.MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY``
MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY = -1
#: Java: ``Trigger.MISFIRE_INSTRUCTION_SMART_POLICY``（``CronScheduleBuilder`` 的默认值）
MISFIRE_INSTRUCTION_SMART_POLICY = 0
#: Java: ``CronTrigger.MISFIRE_INSTRUCTION_FIRE_ONCE_NOW``
MISFIRE_INSTRUCTION_FIRE_ONCE_NOW = 1
#: Java: ``CronTrigger.MISFIRE_INSTRUCTION_DO_NOTHING``
MISFIRE_INSTRUCTION_DO_NOTHING = 2

#: Java: ``org.quartz.jobStore.misfireThreshold`` 默认 60 秒。
MISFIRE_THRESHOLD_MS = 60_000

#: Java: Spring Boot 的 ``org.quartz.threadPool.threadCount`` 默认值。
THREAD_COUNT = 10

#: 调度线程的轮询步长（秒）。Quartz 用 ``idleWaitTime``（默认 30s）+ 信号量唤醒。
_IDLE_WAIT_SECONDS = 1.0


class SchedulerException(Exception):
    """Java: ``org.quartz.SchedulerException``."""


class ObjectAlreadyExistsException(SchedulerException):
    """Java: ``org.quartz.ObjectAlreadyExistsException``."""


class Key:
    """Java: ``org.quartz.utils.Key`` —— ``JobKey`` / ``TriggerKey`` 的共同父类."""

    __slots__ = ("name", "group")

    def __init__(self, name: str, group: Optional[str] = None) -> None:
        if name is None:
            # Java: ``throw new IllegalArgumentException("Name cannot be null.")``
            raise ValueError("Name cannot be null.")
        self.name = name
        # Java: ``this.group = (group != null) ? group : DEFAULT_GROUP;``
        self.group = group if group is not None else DEFAULT_GROUP

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Key)
            and type(other) is type(self)
            and other.name == self.name
            and other.group == self.group
        )

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.name, self.group))

    def __str__(self) -> str:
        # Java: ``Key.toString()`` 返回 ``group + '.' + name``
        return f"{self.group}.{self.name}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r}, {self.group!r})"


class JobKey(Key):
    """Java: ``org.quartz.JobKey``."""

    # Java: ``public static JobKey jobKey(String name, String group)``
    @staticmethod
    def job_key(name: str, group: Optional[str] = None) -> "JobKey":
        return JobKey(name, group)


class TriggerKey(Key):
    """Java: ``org.quartz.TriggerKey``."""

    # Java: ``public static TriggerKey triggerKey(String name, String group)``
    @staticmethod
    def trigger_key(name: str, group: Optional[str] = None) -> "TriggerKey":
        return TriggerKey(name, group)


class JobDataMap(dict):
    """Java: ``org.quartz.JobDataMap`` —— 字符串键的 Map."""


class JobDetail:
    """Java: ``org.quartz.JobDetail`` —— 只保留本工程用到的部分."""

    def __init__(self, job_class: type, key: JobKey) -> None:
        self.job_class = job_class
        self.key = key
        self.job_data_map = JobDataMap()

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"JobDetail({self.job_class.__name__}, {self.key})"


class CronTrigger:
    """Java: ``org.quartz.CronTrigger`` —— 只保留本工程用到的部分."""

    def __init__(
        self,
        key: TriggerKey,
        cron_expression: str,
        misfire_instruction: int = MISFIRE_INSTRUCTION_SMART_POLICY,
    ) -> None:
        self.key = key
        self.cron_expression = cron_expression
        self.misfire_instruction = misfire_instruction
        self.next_fire_time: Optional[float] = None

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"CronTrigger({self.key}, {self.cron_expression!r})"


class JobExecutionContext:
    """Java: ``org.quartz.JobExecutionContext``.

    ``getMergedJobDataMap()`` 在 Quartz 里是 ``jobDetail.getJobDataMap()`` 与
    触发器自带 ``dataMap`` 的合并结果；``triggerJob`` 时传入的 map **覆盖**
    ``jobDetail`` 里的同名键。
    """

    def __init__(
        self,
        scheduler: "Scheduler",
        trigger: CronTrigger,
        job_detail: JobDetail,
        merged_job_data_map: JobDataMap,
    ) -> None:
        self.scheduler = scheduler
        self.trigger = trigger
        self.job_detail = job_detail
        self.merged_job_data_map = merged_job_data_map

    def get_merged_job_data_map(self) -> JobDataMap:
        """Java: ``getMergedJobDataMap()``."""
        return self.merged_job_data_map

    def get_job_detail(self) -> JobDetail:
        """Java: ``getJobDetail()``."""
        return self.job_detail

    def get_trigger(self) -> CronTrigger:
        """Java: ``getTrigger()``."""
        return self.trigger


class _Entry:
    """调度器内部的一条记录：``(JobDetail, CronTrigger, 状态)``."""

    __slots__ = (
        "job_detail",
        "trigger",
        "expression",
        "paused",
        "running",
        "deferred_at",
        "disallow_concurrent",
    )

    def __init__(self, job_detail: JobDetail, trigger: CronTrigger) -> None:
        self.job_detail = job_detail
        self.trigger = trigger
        self.expression = CronExpression(trigger.cron_expression)
        self.paused = False
        self.running = False
        self.deferred_at: Optional[float] = None
        # Java: ``jobClass.isAnnotationPresent(DisallowConcurrentExecution.class)``
        self.disallow_concurrent = bool(
            getattr(job_detail.job_class, "disallow_concurrent_execution", False)
        )


class Scheduler:
    """Java: ``org.quartz.Scheduler``（``RAMJobStore`` + ``SimpleThreadPool`` 子集）."""

    def __init__(self, thread_count: int = THREAD_COUNT) -> None:
        self._lock = threading.RLock()
        self._entries: Dict[JobKey, _Entry] = {}
        self._executor = ThreadPoolExecutor(
            max_workers=thread_count, thread_name_prefix="quartz-worker"
        )
        self._thread: Optional[threading.Thread] = None
        self._shutdown = False
        self._wake = threading.Event()

    # ---------------------------------------------------------------- 生命周期

    def start(self) -> None:
        """Java: ``scheduler.start()`` —— Spring Boot 的 ``SchedulerFactoryBean`` 自动调用."""
        with self._lock:
            if self._thread is not None:
                return
            self._shutdown = False
            thread = threading.Thread(
                target=self._dispatch_loop, name="quartz-dispatcher", daemon=True
            )
            self._thread = thread
        thread.start()
        logger.info("[调度器] 已启动 (thread_count=%s)", self._executor._max_workers)

    def shutdown(self, wait: bool = False) -> None:
        """Java: ``scheduler.shutdown()`` —— Spring 关闭容器时调用."""
        with self._lock:
            self._shutdown = True
            self._wake.set()
            thread = self._thread
            self._thread = None
        if thread is not None:
            thread.join(timeout=5 if wait else 0)
        self._executor.shutdown(wait=wait)

    def is_started(self) -> bool:
        """Java: ``scheduler.isStarted()``."""
        return self._thread is not None and not self._shutdown

    # ---------------------------------------------------------------- 查询

    def check_exists(self, job_key: JobKey) -> bool:
        """Java: ``scheduler.checkExists(JobKey)``."""
        with self._lock:
            return job_key in self._entries

    def get_job_keys(self) -> List[JobKey]:
        """Java: ``scheduler.getJobKeys(GroupMatcher)`` 的全量形态（测试/诊断用）."""
        with self._lock:
            return list(self._entries)

    # ---------------------------------------------------------------- 增删

    def schedule_job(self, job_detail: JobDetail, trigger: CronTrigger) -> float:
        """Java: ``scheduler.scheduleJob(JobDetail, Trigger)`` —— 返回首次触发时刻(epoch 秒)."""
        entry = _Entry(job_detail, trigger)
        first = _next_fire_time(entry.expression, time.time())
        trigger.next_fire_time = first
        with self._lock:
            if job_detail.key in self._entries:
                raise ObjectAlreadyExistsException(
                    f"ObjectAlreadyExistsException: Key {job_detail.key}"
                )
            self._entries[job_detail.key] = entry
        self._wake.set()
        return first

    def delete_job(self, job_key: JobKey) -> bool:
        """Java: ``scheduler.deleteJob(JobKey)`` —— 不存在时返回 ``False``，不抛异常."""
        with self._lock:
            return self._entries.pop(job_key, None) is not None

    def clear(self) -> None:
        """Java: ``scheduler.clear()`` —— 清空全部任务（``@PostConstruct init()`` 第一句）."""
        with self._lock:
            self._entries.clear()
        self._wake.set()

    # ---------------------------------------------------------------- 暂停 / 恢复

    def pause_job(self, job_key: JobKey) -> None:
        """Java: ``scheduler.pauseJob(JobKey)`` —— 不存在时是**空操作**."""
        with self._lock:
            entry = self._entries.get(job_key)
            if entry is not None:
                entry.paused = True

    def resume_job(self, job_key: JobKey) -> None:
        """Java: ``scheduler.resumeJob(JobKey)`` —— 不存在时是**空操作**."""
        with self._lock:
            entry = self._entries.get(job_key)
            if entry is None:
                return
            entry.paused = False
            # 暂停期间错过的触发不补：恢复时重新对齐到下一个有效时刻。
            entry.trigger.next_fire_time = _next_fire_time(entry.expression, time.time())
        self._wake.set()

    # ---------------------------------------------------------------- 立即执行

    def trigger_job(self, job_key: JobKey, data_map: Optional[JobDataMap] = None) -> None:
        """Java: ``scheduler.triggerJob(JobKey, JobDataMap)``.

        任务不存在时抛 ``SchedulerException``，文案与 Quartz 逐字一致 ——
        线上 ``PUT /monitor/job/run``（``jobId=999999``）返回的就是这一句。
        """
        with self._lock:
            entry = self._entries.get(job_key)
        if entry is None:
            # Java: ``throw new SchedulerException("The job (" + jobKey + ") referenced by the trigger does not exist.")``
            raise SchedulerException(
                f"The job ({job_key}) referenced by the trigger does not exist."
            )
        _submit(self, entry, _merge_data_map(entry.job_detail, data_map))

    # ---------------------------------------------------------------- 内部

    def _dispatch_loop(self) -> None:
        """Java: ``QuartzSchedulerThread#run()`` 的主循环."""
        while True:
            with self._lock:
                if self._shutdown:
                    return
                entries = list(self._entries.values())

            now = time.time()
            wait = _IDLE_WAIT_SECONDS
            for entry in entries:
                fire_at = entry.trigger.next_fire_time
                if entry.paused or fire_at is None:
                    continue
                if fire_at > now:
                    wait = min(wait, max(fire_at - now, 0.01))
                    continue
                if not self._acquire(entry, now):
                    continue
                _submit(self, entry, JobDataMap(entry.job_detail.job_data_map))

            self._wake.wait(wait)
            self._wake.clear()

    def _acquire(self, entry: _Entry, now: float) -> bool:
        """占用一条记录；返回 ``True`` 表示"本次应当真的执行"."""
        with self._lock:
            overdue_ms = (now - entry.trigger.next_fire_time) * 1000

            if entry.running and entry.disallow_concurrent:
                # Java: ``@DisallowConcurrentExecution`` —— 任务还在跑，推迟本次触发。
                if entry.deferred_at is None:
                    entry.deferred_at = now
                if overdue_ms < MISFIRE_THRESHOLD_MS:
                    return False
                # 超过阈值：不再等锁，按 misfire 指令推进时间轴（本次丢掉）。
                self._apply_misfire(entry, now)
                return False

            entry.running = True
            entry.deferred_at = None
            if overdue_ms >= MISFIRE_THRESHOLD_MS and not self._apply_misfire(entry, now):
                entry.running = False
                return False
            entry.trigger.next_fire_time = _next_fire_time(entry.expression, now)
            return True

    def _apply_misfire(self, entry: _Entry, now: float) -> bool:
        """Java: ``CronTriggerImpl#updateAfterMisfire(Calendar)``.

        返回值 ``True`` 表示"补执行一次"，``False`` 表示"跳过本次"。
        无论哪种，``nextFireTime`` 都会推进到 ``now`` 之后的第一个有效时刻。
        """
        instruction = entry.trigger.misfire_instruction
        entry.trigger.next_fire_time = _next_fire_time(entry.expression, now)
        if instruction == MISFIRE_INSTRUCTION_DO_NOTHING:
            # Java: ``setNextFireTime(getFireTimeAfter(new Date()))`` —— 不补。
            return False
        # SMART(0) 被 ``updateAfterMisfire`` 折成 FIRE_ONCE_NOW(1)；
        # IGNORE_MISFIRE_POLICY(-1) 与 FIRE_AND_PROCEED(1) 同样"补一次"。
        return True

    def _release(self, entry: _Entry) -> None:
        with self._lock:
            entry.running = False
            entry.deferred_at = None


def _next_fire_time(expression: CronExpression, after_epoch: float) -> Optional[float]:
    """``CronExpression#getNextValidTimeAfter(Date)`` 的 epoch 秒形态."""
    base = datetime.fromtimestamp(after_epoch)
    # Quartz 的 ``getNextValidTimeAfter`` 是**严格大于**，精度到秒；
    # 先用整秒去掉亚秒部分，行为与 ``Date`` 的毫秒截断一致。
    base = base.replace(microsecond=0)
    nxt = expression.get_next_valid_time_after(base)
    if nxt is None:
        return None
    return nxt.timestamp()


def _merge_data_map(job_detail: JobDetail, data_map: Optional[JobDataMap]) -> JobDataMap:
    merged = JobDataMap(job_detail.job_data_map)
    if data_map:
        merged.update(data_map)
    return merged


def _submit(scheduler: Scheduler, entry: _Entry, data_map: JobDataMap) -> None:
    """把一次执行丢进线程池（Java: ``SimpleThreadPool.runInThread(Runnable)``）."""
    context = JobExecutionContext(scheduler, entry.trigger, entry.job_detail, data_map)
    try:
        scheduler._executor.submit(_run_job, scheduler, entry, context)
    except RuntimeError:  # 线程池已关闭
        scheduler._release(entry)
        logger.warning("[调度器] 线程池已关闭，丢弃一次触发: %s", entry.job_detail.key)


def _run_job(scheduler: Scheduler, entry: _Entry, context: JobExecutionContext) -> None:
    try:
        # Java: 每次触发都 ``newInstance()`` 一个 Job 实例（SimpleJobFactory）
        job = entry.job_detail.job_class()
        job.execute(context)
    except BaseException:  # noqa: BLE001 - ``execute`` 内部已兜底，这里只防线程泄漏
        logger.exception("[调度器] 任务执行异常: %s", entry.job_detail.key)
    finally:
        scheduler._release(entry)


# --------------------------------------------------------------------------- Builder

class CronScheduleBuilder:
    """Java: ``org.quartz.CronScheduleBuilder``.

    Java 里是**可变 + 链式**（``withMisfireHandlingInstruction...`` 返回 ``this``），
    所以 ``ScheduleUtils`` 才能写成 ``cb = handleCronScheduleMisfirePolicy(job, cb)``。
    这里同样是可变对象，返回 ``self``。
    """

    def __init__(self, cron_expression: str) -> None:
        self.cron_expression = cron_expression
        self.misfire_instruction = MISFIRE_INSTRUCTION_SMART_POLICY

    # Java: public static CronScheduleBuilder cronSchedule(String cronExpression)
    @staticmethod
    def cron_schedule(cron_expression: Optional[str]) -> "CronScheduleBuilder":
        """构造时**立即校验**表达式，与 Java 一致。

        * ``null`` -> ``IllegalArgumentException("cronExpression cannot be null")``
          （``CronExpression`` 构造函数抛的，不是 ``ParseException``，原样外抛）；
        * 非法表达式 -> ``RuntimeException("CronExpression '...' is not valid.")``。
        """
        try:
            CronExpression(cron_expression)
        except ValueError:
            raise
        except Exception as exc:  # noqa: BLE001 - CronParseException
            raise RuntimeError(
                f"CronExpression '{cron_expression}' is not valid."
            ) from exc
        return CronScheduleBuilder(cron_expression)  # type: ignore[arg-type]

    # Java: withMisfireHandlingInstructionIgnoreMisfires()
    def with_misfire_handling_instruction_ignore_misfires(self) -> "CronScheduleBuilder":
        self.misfire_instruction = MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY
        return self

    # Java: withMisfireHandlingInstructionFireAndProceed()
    def with_misfire_handling_instruction_fire_and_proceed(self) -> "CronScheduleBuilder":
        self.misfire_instruction = MISFIRE_INSTRUCTION_FIRE_ONCE_NOW
        return self

    # Java: withMisfireHandlingInstructionDoNothing()
    def with_misfire_handling_instruction_do_nothing(self) -> "CronScheduleBuilder":
        self.misfire_instruction = MISFIRE_INSTRUCTION_DO_NOTHING
        return self

    # Java: CronTrigger build()
    def build(self, trigger_key: TriggerKey) -> CronTrigger:
        return CronTrigger(trigger_key, self.cron_expression, self.misfire_instruction)


class JobBuilder:
    """Java: ``org.quartz.JobBuilder``（只用 ``newJob`` / ``withIdentity`` / ``build``）."""

    def __init__(self, job_class: type) -> None:
        self._job_class = job_class
        self._key: Optional[JobKey] = None

    # Java: public static JobBuilder newJob(Class<? extends Job> jobClass)
    @staticmethod
    def new_job(job_class: type) -> "JobBuilder":
        return JobBuilder(job_class)

    # Java: public JobBuilder withIdentity(JobKey jobKey)
    def with_identity(self, job_key: JobKey) -> "JobBuilder":
        self._key = job_key
        return self

    # Java: public JobDetail build()
    def build(self) -> JobDetail:
        if self._key is None:
            raise SchedulerException("Job key must be set before build().")
        return JobDetail(self._job_class, self._key)


class TriggerBuilder:
    """Java: ``org.quartz.TriggerBuilder``（只用 ``newTrigger`` / ``withIdentity`` /
    ``withSchedule`` / ``build``）."""

    def __init__(self) -> None:
        self._key: Optional[TriggerKey] = None
        self._schedule: Optional[CronScheduleBuilder] = None

    # Java: public static TriggerBuilder newTrigger()
    @staticmethod
    def new_trigger() -> "TriggerBuilder":
        return TriggerBuilder()

    # Java: public TriggerBuilder withIdentity(String name, String group)
    def with_identity(self, trigger_key: TriggerKey) -> "TriggerBuilder":
        self._key = trigger_key
        return self

    # Java: public <S extends ScheduleBuilder<T>> TriggerBuilder withSchedule(S scheduleBuilder)
    def with_schedule(self, schedule_builder: CronScheduleBuilder) -> "TriggerBuilder":
        self._schedule = schedule_builder
        return self

    # Java: public CronTrigger build()
    def build(self) -> CronTrigger:
        if self._key is None:
            raise SchedulerException("Trigger key must be set before build().")
        if self._schedule is None:
            raise SchedulerException("Schedule must be set before build().")
        return self._schedule.build(self._key)


# --------------------------------------------------------------------------- 单例

_SCHEDULER: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """Java: ``@Autowired Scheduler scheduler`` —— Spring 里的单例 Bean."""
    global _SCHEDULER
    if _SCHEDULER is None:
        _SCHEDULER = Scheduler()
        _SCHEDULER.start()
    return _SCHEDULER


def set_scheduler(scheduler: Optional[Scheduler]) -> None:
    """Test helper: 换掉（或清空）全局调度器."""
    global _SCHEDULER
    _SCHEDULER = scheduler


def shutdown_scheduler() -> None:
    """Java: ``SchedulerFactoryBean`` 的 ``destroy()`` —— 容器关闭时停止调度."""
    global _SCHEDULER
    if _SCHEDULER is not None:
        _SCHEDULER.shutdown(wait=False)
        _SCHEDULER = None


__all__ = [
    "DEFAULT_GROUP",
    "MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY",
    "MISFIRE_INSTRUCTION_SMART_POLICY",
    "MISFIRE_INSTRUCTION_FIRE_ONCE_NOW",
    "MISFIRE_INSTRUCTION_DO_NOTHING",
    "MISFIRE_THRESHOLD_MS",
    "SchedulerException",
    "ObjectAlreadyExistsException",
    "Key",
    "JobKey",
    "TriggerKey",
    "JobDataMap",
    "JobDetail",
    "CronTrigger",
    "JobExecutionContext",
    "Scheduler",
    "CronScheduleBuilder",
    "JobBuilder",
    "TriggerBuilder",
    "get_scheduler",
    "set_scheduler",
    "shutdown_scheduler",
]
