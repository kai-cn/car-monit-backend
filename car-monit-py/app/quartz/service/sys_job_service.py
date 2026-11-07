"""定时任务调度信息 service.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/ISysJobService.java
# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobServiceImpl.java

十一个方法全部迁移，其中三个带 ``@Transactional``，实现要点：

``insertJob`` 是一**次**事务
----------------------------
Java::

    job.setStatus(Status.PAUSE.getValue());
    int rows = jobMapper.insertJob(job);          // 落库（useGeneratedKeys 回填 jobId）
    if (rows > 0) {
        ScheduleUtils.createScheduleJob(scheduler, job);   // 可能抛 TaskException
    }
    return rows;

``@Transactional(rollbackFor = Exception.class)`` 让 ``createScheduleJob`` 抛出的
``TaskException`` 把刚插入的那行**回滚掉**。线上以 ``misfirePolicy='9'`` 验证过：
报错之后数据库里没有任何残留行（``evidence/_probe_job_err_out.txt`` 的 ``cleanup ids`` 只剩
两条确实成功的插入）。

Python 侧把这个事务显式化：``with session_scope() as session`` + ``insert_job(session=...)``，
``createScheduleJob`` 仍在 with 块内，抛异常 -> ``session_scope`` 回滚。见
:mod:`app.quartz.mapper.sys_job_mapper` 的 ``shared_session``。

``updateJob`` 里 ``properties`` 可能是 ``null``
----------------------------------------------
Java::

    SysJob properties = selectJobById(job.getJobId());
    int rows = jobMapper.updateJob(job);
    if (rows > 0) {
        updateSchedulerJob(job, properties.getJobGroup());
    }

``properties`` 为 null 时 ``properties.getJobGroup()`` 会 NPE —— 但**走不到**，因为
主键不存在时 ``updateJob`` 的影响行数是 0，``rows > 0`` 不成立。所以线上
``PUT /monitor/job``（``jobId=999999``）回的是 ``{"msg":"操作失败","code":500}``
（``toAjax(0)``），不是 NPE。照抄这个顺序，不要"提前判空"。

``deleteJobByIds`` 的 NPE
-------------------------
Java::

    for (Long jobId : jobIds) {
        SysJob job = jobMapper.selectJobById(jobId);
        deleteJob(job);          // job 为 null -> deleteJob 里 job.getJobId() NPE
    }

线上 ``DELETE /monitor/job/999999`` 回 ``{"msg":null,"code":500}`` 就是这个 NPE
（``SysJobLog``/``SysJob`` 都**没有**判空）。照抄。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.constant.schedule_constants import TASK_PROPERTIES, Status
from app.config.database import session_scope
from app.quartz.domain.sys_job import SysJob
from app.quartz.mapper.sys_job_mapper import SysJobMapper
from app.quartz.util.cron_utils import CronUtils
from app.quartz.util.schedule_utils import (
    create_schedule_job,
    get_job_key,
)
from app.quartz.util.scheduler import JobDataMap, Scheduler, get_scheduler
from app.config.database import transactional


class SysJobService:
    """Java: ``ISysJobService`` (impl: ``SysJobServiceImpl``)."""

    def __init__(
        self,
        mapper: Optional[SysJobMapper] = None,
        scheduler: Optional[Scheduler] = None,
    ) -> None:
        self._mapper = mapper or SysJobMapper()
        # Java: ``@Autowired private Scheduler scheduler;``
        # 这里保留 None 并延迟到调用时取全局单例，方便测试注入假调度器。
        self._scheduler_override = scheduler

    @property
    def mapper(self) -> SysJobMapper:
        return self._mapper

    @property
    def scheduler(self) -> Scheduler:
        """Java: ``@Autowired Scheduler scheduler``."""
        if self._scheduler_override is not None:
            return self._scheduler_override
        return get_scheduler()

    # ---------------------------------------------------------------- 启动

    # Java: @PostConstruct public void init() throws SchedulerException, TaskException
    def init(self) -> None:
        """项目启动时初始化定时器（``scheduler.clear()`` + 逐条重建）.

        主要防止手动修改数据库导致未同步到定时任务处理（注：不能手动修改数据库 ID
        和任务组名，否则会导致脏数据）。
        """
        scheduler = self.scheduler
        scheduler.clear()
        for job in self._mapper.select_job_all():
            create_schedule_job(scheduler, job)

    # ---------------------------------------------------------------- 查询

    # Java: public List<SysJob> selectJobList(SysJob job)
    def select_job_list(self, job: SysJob) -> List[SysJob]:
        """获取调度器的计划任务列表（分页点在 mapper 内部）。"""
        return self._mapper.select_job_list(job)

    # Java: public SysJob selectJobById(Long jobId)
    def select_job_by_id(self, job_id: int) -> Optional[SysJob]:
        """通过任务 ID 查询调度信息."""
        return self._mapper.select_job_by_id(job_id)

    # ---------------------------------------------------------------- 暂停 / 恢复

    # Java: @Transactional public int pauseJob(SysJob job) throws SchedulerException
    @transactional
    def pause_job(self, job: SysJob) -> int:
        """暂停任务：先改库，**改成功才**动调度器（``if (rows > 0)``）."""
        job_id = job.job_id
        job_group = job.job_group
        job.status = Status.PAUSE.value
        with session_scope() as session:
            rows = self._mapper.update_job(job, session=session)
        if rows > 0:
            self.scheduler.pause_job(get_job_key(job_id, job_group))
        return rows

    # Java: @Transactional public int resumeJob(SysJob job) throws SchedulerException
    @transactional
    def resume_job(self, job: SysJob) -> int:
        """恢复任务：先改库，改成功才动调度器."""
        job_id = job.job_id
        job_group = job.job_group
        job.status = Status.NORMAL.value
        with session_scope() as session:
            rows = self._mapper.update_job(job, session=session)
        if rows > 0:
            self.scheduler.resume_job(get_job_key(job_id, job_group))
        return rows

    # ---------------------------------------------------------------- 删除

    # Java: @Transactional public int deleteJob(SysJob job) throws SchedulerException
    @transactional
    def delete_job(self, job: SysJob) -> int:
        """删除任务后，所对应的 trigger 也将被删除.

        ``job`` 为 ``null`` 时 ``job.job_id`` 抛 ``AttributeError``（对应 Java 的 NPE），
        这是线上 ``DELETE /monitor/job/999999`` 的真实响应，照抄。
        """
        job_id = job.job_id
        job_group = job.job_group
        with session_scope() as session:
            rows = self._mapper.delete_job_by_id(job_id, session=session)
        if rows > 0:
            self.scheduler.delete_job(get_job_key(job_id, job_group))
        return rows

    # Java: @Transactional public void deleteJobByIds(Long[] jobIds) throws SchedulerException
    @transactional
    def delete_job_by_ids(self, job_ids: List[int]) -> None:
        """批量删除调度信息（逐条查、逐条删；查不到就是 NPE，见模块 docstring）."""
        for job_id in job_ids:
            job = self._mapper.select_job_by_id(job_id)
            self.delete_job(job)

    # ---------------------------------------------------------------- 状态

    # Java: @Transactional public int changeStatus(SysJob job) throws SchedulerException
    @transactional
    def change_status(self, job: SysJob) -> int:
        """任务调度状态修改：只认 ``"0"`` / ``"1"``，其余返回 0."""
        rows = 0
        status = job.status
        if Status.NORMAL.value == status:
            rows = self.resume_job(job)
        elif Status.PAUSE.value == status:
            rows = self.pause_job(job)
        return rows

    # ---------------------------------------------------------------- 立即执行

    # Java: @Transactional public void run(SysJob job) throws SchedulerException
    @transactional
    def run(self, job: SysJob) -> None:
        """立即运行任务一次.

        任务不在调度器里时 ``triggerJob`` 抛 ``SchedulerException``，文案是
        ``The job (group.name) referenced by the trigger does not exist.``。
        """
        job_id = job.job_id
        job_group = job.job_group
        properties = self.select_job_by_id(job.job_id)
        data_map = JobDataMap()
        data_map[TASK_PROPERTIES] = properties
        self.scheduler.trigger_job(get_job_key(job_id, job_group), data_map)

    # ---------------------------------------------------------------- 新增 / 修改

    # Java: @Transactional public int insertJob(SysJob job) throws SchedulerException, TaskException
    @transactional
    def insert_job(self, job: SysJob) -> int:
        """新增任务（**强制** ``status = PAUSE``，插入与注册在同一个事务里）."""
        job.status = Status.PAUSE.value
        with session_scope() as session:
            rows = self._mapper.insert_job(job, session=session)
            if rows > 0:
                # 抛 TaskException / SchedulerException 时 session_scope 回滚本次插入
                create_schedule_job(self.scheduler, job)
        return rows

    # Java: @Transactional public int updateJob(SysJob job) throws SchedulerException, TaskException
    @transactional
    def update_job(self, job: SysJob) -> int:
        """更新任务的时间表达式（先查旧值拿 ``jobGroup``，再改库，改成功才动调度器）."""
        properties = self.select_job_by_id(job.job_id)
        with session_scope() as session:
            rows = self._mapper.update_job(job, session=session)
        if rows > 0:
            self.update_scheduler_job(job, properties.job_group)
        return rows

    # Java: public void updateSchedulerJob(SysJob job, String jobGroup)
    def update_scheduler_job(self, job: SysJob, job_group: Optional[str]) -> None:
        """先按**旧** ``jobGroup`` 删掉旧任务，再按新定义重建."""
        job_id = job.job_id
        job_key = get_job_key(job_id, job_group)
        if self.scheduler.check_exists(job_key):
            # 防止创建时存在数据问题 先移除，然后在执行创建操作
            self.scheduler.delete_job(job_key)
        create_schedule_job(self.scheduler, job)

    # ---------------------------------------------------------------- 校验

    # Java: public boolean checkCronExpressionIsValid(String cronExpression)
    def check_cron_expression_is_valid(self, cron_expression: Optional[str]) -> bool:
        """校验 cron 表达式是否有效（**控制器没有调用点**，Java 侧同样没有）."""
        return CronUtils.is_valid(cron_expression)


_SERVICE: Optional[SysJobService] = None


def get_job_service() -> SysJobService:
    """Java: ``@Autowired ISysJobService`` —— Spring 默认单例."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysJobService()
    return _SERVICE


def reset_job_service() -> None:
    """Test helper: drop the cached service so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysJobService", "get_job_service", "reset_job_service"]
