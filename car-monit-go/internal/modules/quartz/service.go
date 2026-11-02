// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobServiceImpl.java:25-254
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobLogServiceImpl.java:16-87
// JAVA 对照: ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml
// JAVA 对照: ruoyi-quartz/src/main/resources/mapper/quartz/SysJobLogMapper.xml
// 类/职责: 定时任务 / 调度日志的服务层（CRUD + 调度器联动）
// 对应 Go 文件: internal/modules/quartz/service.go
// 关键映射: MyBatis Mapper -> GORM；@Transactional -> db.Transaction；Scheduler -> *Scheduler
//
// DIFF: Java 的 pauseJob/resumeJob/deleteJob/changeStatus 都是 @Transactional 且抛 SchedulerException；
// Go 用 db.Transaction 包住写库 + 调度器动作，调度器动作失败即回滚。
// DIFF: selectJobList 的 SQL 只查询 12 个列（不含 update_by/update_time），GORM 会查全表列；
// 多出的 updateBy/updateTime 在 Java JSON 中也是存在的字段（值为 null/空），语义等价。
// DIFF: PageHelper 在没有 orderByColumn 时不追加 ORDER BY；这里默认 job_id asc / create_time desc
// 以保证分页稳定。
package quartz

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// Service 对应 ISysJobService + ISysJobLogService 的实现类。
type Service struct {
	a     *app.App
	sched *Scheduler
	db    *gorm.DB
}

func NewService(a *app.App) *Service {
	return &Service{a: a, sched: SharedScheduler(a), db: a.DB}
}

// ---------------------------------------------------------------------------
// 定时任务
// ---------------------------------------------------------------------------

// ListJobs 对应 SysJobServiceImpl.selectJobList（+ startPage）。
func (s *Service) ListJobs(ctx context.Context, f JobFilter, p web.PageDomain) ([]*SysJob, int64, error) {
	q := s.jobQuery(ctx, f)
	var total int64
	if err := q.Count(&total).Error; err != nil {
		return nil, 0, err
	}
	rows := make([]*SysJob, 0, 16)
	if p.SkipQuery(total) {
		return rows, total, nil
	}
	listQ := s.jobQuery(ctx, f).Order(p.OrderByWithDefault("job_id asc"))
	if p.HasPage {
		lim, off := p.LimitOffset(total)
		listQ = listQ.Offset(off).Limit(lim)
	}
	if err := listQ.Find(&rows).Error; err != nil {
		return nil, 0, err
	}
	fillNextValidTime(rows)
	return rows, total, nil
}

// ListAllJobs 供导出使用（Java 导出不分页）。
func (s *Service) ListAllJobs(ctx context.Context, f JobFilter) ([]*SysJob, error) {
	rows := make([]*SysJob, 0, 16)
	if err := s.jobQuery(ctx, f).Order("job_id asc").Find(&rows).Error; err != nil {
		return nil, err
	}
	fillNextValidTime(rows)
	return rows, nil
}

func (s *Service) jobQuery(ctx context.Context, f JobFilter) *gorm.DB {
	// JAVA 对照: selectJobVo 只查 12 列（不含 update_by/update_time）。
	q := s.db.WithContext(ctx).Model(&SysJob{}).
		Select("job_id, job_name, job_group, invoke_target, cron_expression, misfire_policy, concurrent, status, create_by, create_time, remark")
	if f.JobName != "" {
		q = q.Where("job_name like ?", "%"+f.JobName+"%")
	}
	if f.JobGroup != "" {
		q = q.Where("job_group = ?", f.JobGroup)
	}
	if f.Status != "" {
		q = q.Where("status = ?", f.Status)
	}
	if f.InvokeTarget != "" {
		q = q.Where("invoke_target like ?", "%"+f.InvokeTarget+"%")
	}
	return q
}

func fillNextValidTime(rows []*SysJob) {
	for _, r := range rows {
		r.FillNextValidTime()
	}
}

// GetJob 对应 SysJobServiceImpl.selectJobById。
func (s *Service) GetJob(ctx context.Context, jobID int64) (*SysJob, error) {
	var job SysJob
	// JAVA 对照: selectJobById 使用 selectJobVo 的 12 列。
	err := s.db.WithContext(ctx).
		Select("job_id, job_name, job_group, invoke_target, cron_expression, misfire_policy, concurrent, status, create_by, create_time, remark").
		Where("job_id = ?", jobID).First(&job).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	job.FillNextValidTime()
	return &job, nil
}

// InsertJob 对应 SysJobServiceImpl.insertJob：状态固定为「暂停」后再注册到调度器。
func (s *Service) InsertJob(ctx context.Context, job *SysJob) (int64, error) {
	if err := validateJobForWrite(job); err != nil {
		return 0, err
	}
	if err := s.sched.Invoker().ValidateTarget(job.InvokeTarget); err != nil {
		return 0, web.NewServiceError("%s", err.Error())
	}
	normalizeJobDefaults(job, nil)
	job.Status = StatusPause
	now := web.Now()
	// JAVA 对照: SysJobMapper.insertJob 只写入 create_by / create_time（update_* 保持为空）。
	job.CreateTime = &now

	var rows int64
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := tx.Create(job).Error; err != nil {
			return err
		}
		rows = 1
		// JAVA 对照: ScheduleUtils.createScheduleJob(scheduler, job)
		return s.sched.Add(job)
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}

// UpdateJob 对应 SysJobServiceImpl.updateJob + updateSchedulerJob。
func (s *Service) UpdateJob(ctx context.Context, job *SysJob) (int64, error) {
	if job.JobID == 0 {
		return 0, web.NewServiceError("任务ID不能为空")
	}
	if err := validateJobForWrite(job); err != nil {
		return 0, err
	}
	if err := s.sched.Invoker().ValidateTarget(job.InvokeTarget); err != nil {
		return 0, web.NewServiceError("%s", err.Error())
	}
	props, err := s.GetJob(ctx, job.JobID)
	if err != nil {
		return 0, err
	}
	if props == nil {
		return 0, web.NewServiceError("任务不存在")
	}
	normalizeJobDefaults(job, props)

	var rows int64
	err = s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		n, err := updateJobColumns(ctx, tx, job)
		rows = n
		return err
	})
	if err != nil {
		return rows, err
	}
	if rows > 0 {
		// JAVA 对照: updateSchedulerJob —— 先删旧 JobKey（可能换组），再重建。
		s.sched.Remove(job.JobID, props.JobGroup)
		if err := s.sched.Add(job); err != nil {
			return rows, err
		}
	}
	return rows, nil
}

// updateJobColumns 复刻 SysJobMapper.updateJob 的 <set><if> 语义：空值不更新。
func updateJobColumns(ctx context.Context, tx *gorm.DB, job *SysJob) (int64, error) {
	updates := map[string]any{}
	if job.JobName != "" {
		updates["job_name"] = job.JobName
	}
	if job.JobGroup != "" {
		updates["job_group"] = job.JobGroup
	}
	if job.InvokeTarget != "" {
		updates["invoke_target"] = job.InvokeTarget
	}
	if job.CronExpression != "" {
		updates["cron_expression"] = job.CronExpression
	}
	if job.MisfirePolicy != "" {
		updates["misfire_policy"] = job.MisfirePolicy
	}
	if job.Concurrent != "" {
		updates["concurrent"] = job.Concurrent
	}
	if job.Status != "" {
		updates["status"] = job.Status
	}
	if model.Str(job.Remark) != "" {
		updates["remark"] = model.Str(job.Remark)
	}
	if model.Str(job.UpdateBy) != "" {
		updates["update_by"] = model.Str(job.UpdateBy)
	}
	updates["update_time"] = web.Now()
	res := tx.WithContext(ctx).Model(&SysJob{}).Where("job_id = ?", job.JobID).Updates(updates)
	return res.RowsAffected, res.Error
}

// PauseJob 对应 SysJobServiceImpl.pauseJob。
func (s *Service) PauseJob(ctx context.Context, job *SysJob) (int64, error) {
	job.Status = StatusPause
	rows, err := s.updateJobStatus(ctx, job)
	if err != nil {
		return rows, err
	}
	if rows > 0 {
		s.sched.Pause(job.JobID, job.JobGroup)
	}
	return rows, nil
}

// ResumeJob 对应 SysJobServiceImpl.resumeJob。
func (s *Service) ResumeJob(ctx context.Context, job *SysJob) (int64, error) {
	job.Status = StatusNormal
	rows, err := s.updateJobStatus(ctx, job)
	if err != nil {
		return rows, err
	}
	if rows > 0 {
		s.sched.Resume(job.JobID, job.JobGroup)
	}
	return rows, nil
}

func (s *Service) updateJobStatus(ctx context.Context, job *SysJob) (int64, error) {
	var rows int64
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		n, err := updateJobColumns(ctx, tx, job)
		rows = n
		return err
	})
	return rows, err
}

// ChangeStatus 对应 SysJobServiceImpl.changeStatus。
func (s *Service) ChangeStatus(ctx context.Context, jobID int64, status string) (int64, error) {
	job, err := s.GetJob(ctx, jobID)
	if err != nil {
		return 0, err
	}
	if job == nil {
		// JAVA 对照: newJob.setStatus(...) 会 NPE -> 500；这里返回业务错误。
		return 0, web.NewServiceError("任务不存在")
	}
	job.Status = status
	switch status {
	case StatusNormal:
		return s.ResumeJob(ctx, job)
	case StatusPause:
		return s.PauseJob(ctx, job)
	}
	return 0, nil
}

// Run 对应 SysJobServiceImpl.run：立即执行一次。
// DIFF: Java 用请求体里的 jobId/jobGroup 构造 JobKey（Properties 从库里取）；这里统一以库里的
// jobGroup 为准，避免请求体缺字段导致 SchedulerException。
func (s *Service) Run(ctx context.Context, job *SysJob) error {
	if job == nil || job.JobID == 0 {
		return web.NewServiceError("任务ID不能为空")
	}
	props, err := s.GetJob(ctx, job.JobID)
	if err != nil {
		return err
	}
	if props == nil {
		return web.NewServiceError("任务不存在")
	}
	if err := s.sched.Trigger(props); err != nil {
		return web.NewServiceError("%s", err.Error())
	}
	return nil
}

// DeleteJob 对应 SysJobServiceImpl.deleteJob：删除库记录并移除调度。
func (s *Service) DeleteJob(ctx context.Context, job *SysJob) (int64, error) {
	var rows int64
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		res := tx.Where("job_id = ?", job.JobID).Delete(&SysJob{})
		if res.Error != nil {
			return res.Error
		}
		rows = res.RowsAffected
		if rows > 0 {
			s.sched.Remove(job.JobID, job.JobGroup)
		}
		return nil
	})
	return rows, err
}

// DeleteJobs 对应 SysJobServiceImpl.deleteJobByIds。
// DIFF: Java 查不到任务时会 NPE；这里跳过不存在的 ID。
func (s *Service) DeleteJobs(ctx context.Context, jobIDs []int64) error {
	for _, id := range jobIDs {
		job, err := s.GetJob(ctx, id)
		if err != nil {
			return err
		}
		if job == nil {
			continue
		}
		if _, err := s.DeleteJob(ctx, job); err != nil {
			return err
		}
	}
	return nil
}

// CheckCronExpressionIsValid 对应 SysJobServiceImpl.checkCronExpressionIsValid。
func (s *Service) CheckCronExpressionIsValid(expr string) bool { return IsValidCronExpression(expr) }

// validateJobForWrite 复刻 SysJob 上的 JSR-303 约束（@NotBlank / @Size）。
func validateJobForWrite(job *SysJob) error {
	if strings.TrimSpace(job.JobName) == "" {
		return web.NewServiceError("任务名称不能为空")
	}
	if len([]rune(job.JobName)) > 64 {
		return web.NewServiceError("任务名称不能超过64个字符")
	}
	if strings.TrimSpace(job.InvokeTarget) == "" {
		return web.NewServiceError("调用目标字符串不能为空")
	}
	if len(job.InvokeTarget) > 500 {
		return web.NewServiceError("调用目标字符串长度不能超过500个字符")
	}
	if strings.TrimSpace(job.CronExpression) == "" {
		return web.NewServiceError("Cron执行表达式不能为空")
	}
	if len(job.CronExpression) > 255 {
		return web.NewServiceError("Cron执行表达式不能超过255个字符")
	}
	if err := ValidateCronExpression(job.CronExpression); err != nil {
		return web.NewServiceError("cron表达式不正确")
	}
	return nil
}

// normalizeJobDefaults 补齐 Java 域对象上的默认值（misfirePolicy 默认 "0"、jobGroup 默认沿用旧值）。
func normalizeJobDefaults(job *SysJob, old *SysJob) {
	if job.MisfirePolicy == "" {
		if old != nil && old.MisfirePolicy != "" {
			job.MisfirePolicy = old.MisfirePolicy
		} else {
			job.MisfirePolicy = MisfireDefault
		}
	}
	if job.Concurrent == "" {
		if old != nil && old.Concurrent != "" {
			job.Concurrent = old.Concurrent
		} else {
			job.Concurrent = "0"
		}
	}
	if job.JobGroup == "" && old != nil {
		job.JobGroup = old.JobGroup
	}
}

// ---------------------------------------------------------------------------
// 调度日志
// JAVA 对照: SysJobLogServiceImpl.java:16-87
// ---------------------------------------------------------------------------

// ListJobLogs 对应 SysJobLogServiceImpl.selectJobLogList。
func (s *Service) ListJobLogs(ctx context.Context, f JobFilter, p web.PageDomain) ([]*SysJobLog, int64, error) {
	q := s.jobLogQuery(ctx, f)
	var total int64
	if err := q.Count(&total).Error; err != nil {
		return nil, 0, err
	}
	rows := make([]*SysJobLog, 0, 16)
	if p.SkipQuery(total) {
		return rows, total, nil
	}
	listQ := s.jobLogQuery(ctx, f).Order(p.OrderByWithDefault("create_time desc"))
	if p.HasPage {
		lim, off := p.LimitOffset(total)
		listQ = listQ.Offset(off).Limit(lim)
	}
	if err := listQ.Find(&rows).Error; err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

func (s *Service) jobLogQuery(ctx context.Context, f JobFilter) *gorm.DB {
	// JAVA 对照: selectJobLogVo 只查 8 列。
	q := s.db.WithContext(ctx).Model(&SysJobLog{}).
		Select("job_log_id, job_name, job_group, invoke_target, job_message, status, exception_info, create_time")
	if f.JobName != "" {
		q = q.Where("job_name like ?", "%"+f.JobName+"%")
	}
	if f.JobGroup != "" {
		q = q.Where("job_group = ?", f.JobGroup)
	}
	if f.Status != "" {
		q = q.Where("status = ?", f.Status)
	}
	if f.InvokeTarget != "" {
		q = q.Where("invoke_target like ?", "%"+f.InvokeTarget+"%")
	}
	// JAVA 对照: SysJobLogMapper.xml:38-43 的 date_format 比较，保持 MySQL 方言一致。
	if f.BeginTime != "" {
		q = q.Where("date_format(create_time,'%y%m%d') >= date_format(?, '%y%m%d')", f.BeginTime)
	}
	if f.EndTime != "" {
		q = q.Where("date_format(create_time,'%y%m%d') <= date_format(?, '%y%m%d')", f.EndTime)
	}
	return q
}

// GetJobLog 对应 SysJobLogServiceImpl.selectJobLogById。
func (s *Service) GetJobLog(ctx context.Context, jobLogID int64) (*SysJobLog, error) {
	var row SysJobLog
	// JAVA 对照: selectJobLogById 使用 selectJobLogVo 的 8 列。
	err := s.db.WithContext(ctx).
		Select("job_log_id, job_name, job_group, invoke_target, job_message, status, exception_info, create_time").
		Where("job_log_id = ?", jobLogID).First(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &row, nil
}

// AddJobLog 对应 SysJobLogServiceImpl.addJobLog。
func (s *Service) AddJobLog(ctx context.Context, row *SysJobLog) error {
	return s.db.WithContext(ctx).Create(row).Error
}

// DeleteJobLogs 对应 SysJobLogServiceImpl.deleteJobLogByIds。
func (s *Service) DeleteJobLogs(ctx context.Context, ids []int64) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	res := s.db.WithContext(ctx).Where("job_log_id in ?", ids).Delete(&SysJobLog{})
	return res.RowsAffected, res.Error
}

// CleanJobLog 对应 SysJobLogServiceImpl.cleanJobLog（truncate table sys_job_log）。
func (s *Service) CleanJobLog(ctx context.Context) error {
	if err := s.db.WithContext(ctx).Exec("truncate table sys_job_log").Error; err != nil {
		return fmt.Errorf("清空调度日志失败: %w", err)
	}
	return nil
}
