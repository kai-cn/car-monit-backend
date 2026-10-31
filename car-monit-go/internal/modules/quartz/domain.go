// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJob.java:22-172
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJobLog.java:14-155
// JAVA 对照: ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml:7-21
// JAVA 对照: ruoyi-quartz/src/main/resources/mapper/quartz/SysJobLogMapper.xml:7-16
// 类/职责: 定时任务 / 调度日志领域模型与查询条件
// 对应 Go 文件: internal/modules/quartz/domain.go
// 关键映射: BaseEntity 复用 internal/model.BaseEntity（未修改 foundation），
//
//	实体 -> 本地 struct + gorm column 标签 + TableName()
//
// DIFF: 按任务约定不修改 internal/model，因此 sys_job / sys_job_log 的实体定义在本模块内。
// DIFF: Java 的 Long 包装类型可为 null，Go 用 int64 零值 0；前端按 0/空处理，差异等价。
// DIFF: Java 通过 getNextValidTime() 在序列化时实时计算 nextValidTime；Go 在返回前调用
//
//	FillNextValidTime 显式填充（gorm:"-" 不落库）。
package quartz

import (
	"strconv"
	"time"

	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// ScheduleConstants 对应 com.ruoyi.common.constant.ScheduleConstants。
const (
	TaskClassName  = "TASK_CLASS_NAME"
	TaskProperties = "TASK_PROPERTIES"

	MisfireDefault        = "0" // 默认（Quartz smart policy，错过则立即补一次）
	MisfireIgnoreMisfires = "1" // 立即触发执行（忽略错过，补一次）
	MisfireFireAndProceed = "2" // 触发一次执行
	MisfireDoNothing      = "3" // 不触发立即执行

	StatusNormal = "0" // 正常
	StatusPause  = "1" // 暂停

	Success = "0" // Constants.SUCCESS
	Fail    = "1" // Constants.FAIL
)

// SysJob 对应 com.ruoyi.quartz.domain.SysJob。
type SysJob struct {
	model.BaseEntity
	JobID          int64         `json:"jobId" gorm:"column:job_id;primaryKey;autoIncrement"`
	JobName        string        `json:"jobName" gorm:"column:job_name"`
	JobGroup       string        `json:"jobGroup" gorm:"column:job_group"`
	InvokeTarget   string        `json:"invokeTarget" gorm:"column:invoke_target"`
	CronExpression string        `json:"cronExpression" gorm:"column:cron_expression"`
	MisfirePolicy  string        `json:"misfirePolicy" gorm:"column:misfire_policy"`
	Concurrent     string        `json:"concurrent" gorm:"column:concurrent"`
	Status         string        `json:"status" gorm:"column:status"`
	NextValidTime  *web.DateTime `json:"nextValidTime" gorm:"-"`
}

func (SysJob) TableName() string { return "sys_job" }

// FillNextValidTime 对应 SysJob.getNextValidTime()（Jackson 序列化时调用）。
func (j *SysJob) FillNextValidTime() {
	if j == nil {
		return
	}
	if t := NextValidTime(j.CronExpression); t != nil {
		dt := web.NewDateTime(*t)
		j.NextValidTime = &dt
		return
	}
	j.NextValidTime = nil
}

// IsConcurrentAllowed 对应 ScheduleUtils.getQuartzJobClass 的布尔判断：concurrent == "0" 允许并发。
func (j *SysJob) IsConcurrentAllowed() bool { return j.Concurrent == "0" }

// IsPaused 对应 status.equals(ScheduleConstants.Status.PAUSE.getValue())。
func (j *SysJob) IsPaused() bool { return j.Status == StatusPause }

// SysJobLog 对应 com.ruoyi.quartz.domain.SysJobLog。
// DIFF: 未嵌入 model.BaseEntity —— sys_job_log 表只有 create_time，没有 create_by/update_* 列，
// 嵌入后 GORM 生成 INSERT 会包含不存在的列。Java 的 mapper 也是显式列清单。
type SysJobLog struct {
	model.BaseEntity
	JobLogID      int64         `json:"jobLogId" gorm:"column:job_log_id;primaryKey;autoIncrement"`
	JobName       string        `json:"jobName" gorm:"column:job_name"`
	JobGroup      string        `json:"jobGroup" gorm:"column:job_group"`
	InvokeTarget  string        `json:"invokeTarget" gorm:"column:invoke_target"`
	JobMessage    string        `json:"jobMessage" gorm:"column:job_message"`
	Status        string        `json:"status" gorm:"column:status"`
	ExceptionInfo string        `json:"exceptionInfo" gorm:"column:exception_info"`
	StartTime     *web.DateTime `json:"startTime" gorm:"-"`
	StopTime      *web.DateTime `json:"stopTime" gorm:"-"`
}

func (SysJobLog) TableName() string { return "sys_job_log" }

// JobFilter 对应 Controller 中 SysJob / SysJobLog 作为查询对象时的字段
// （selectJobList / selectJobLogList 的 <if> 条件）。
type JobFilter struct {
	JobName      string
	JobGroup     string
	Status       string
	InvokeTarget string
	BeginTime    string
	EndTime      string
}

// jobKeyString 对应 ScheduleUtils.getJobKey(jobId, jobGroup) 的字符串化表示。
func jobKeyString(jobID int64, group string) string {
	return group + ":" + strconv.FormatInt(jobID, 10)
}

// nowPtr 返回当前时间的 web.DateTime 指针，等价 Java new Date()。
func nowPtr() *web.DateTime {
	n := web.Now()
	return &n
}

// timePtr 把 time.Time 转为 web.DateTime 指针。
func timePtr(t time.Time) *web.DateTime {
	d := web.NewDateTime(t)
	return &d
}
