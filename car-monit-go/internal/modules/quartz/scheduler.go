// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/ScheduleUtils.java:24-113
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/AbstractQuartzJob.java:24-107
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/QuartzJobExecution.java
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/QuartzDisallowConcurrentExecution.java
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/config/ScheduleConfig.java（被注释，走内存 JobStore）
// 类/职责: 内存调度器 —— 对应 org.quartz.Scheduler + JobDetail/Trigger
// 对应 Go 文件: internal/modules/quartz/scheduler.go
// 关键映射: Scheduler.scheduleJob/pauseJob/resumeJob/triggerJob/deleteJob/checkExists -> 同名方法
//
//	ThreadLocal<Date> + before/after 计时 -> execute() 内局部变量
//
// DIFF: Quartz 有 JobStore（这里是内存 RAMJobStore），trigger 以 cron 表达式驱动；
// Go 用「每个任务一个 goroutine + 按 Next() 计算的定时器」实现同等语义：
//  1. 单一 jobId+jobGroup 唯一（JobKey = TASK_CLASS_NAME+jobId @ jobGroup）
//  2. concurrent != "0" 时同一任务不会并发执行（Quartz @DisallowConcurrentExecution 语义：
//     上一次未结束则本次触发被跳过）
//  3. paused 状态下不触发，resume 时按 misfire 策略补一次
//
// DIFF: 进程重启后 Quartz 的 DB JobStore 可以对比 next_fire_time 判断 misfire；内存实现只能
// 从“当前时间”重新计算下次触发，因此跨重启的 missed fire 不补（与 RuoYi 注释掉的
// ScheduleConfig 中“单机部署走内存”的说明一致）。运行期卡顿造成的 misfire 按策略处理，见 misfire。
package quartz

import (
	"context"
	"fmt"
	"log/slog"
	"runtime/debug"
	"sync"
	"sync/atomic"
	"time"

	"car-monit-go/internal/app"
)

// misfireThreshold 对应 ScheduleConfig 中的 org.quartz.jobStore.misfireThreshold=12000。
const misfireThreshold = 12 * time.Second

// jobEntry 等价于一个 JobDetail + CronTrigger。
type jobEntry struct {
	sched *Scheduler

	mu     sync.Mutex
	job    *SysJob
	spec   *cronSchedule
	paused bool
	next   time.Time

	running atomic.Bool
	wake    chan struct{}
	kick    chan struct{}
	ctx     context.Context
	cancel  context.CancelFunc
}

// Scheduler 是内存调度器。
type Scheduler struct {
	a    *app.App
	log  *slog.Logger
	loc  *time.Location
	inv  *Invoker
	ctx  context.Context
	stop context.CancelFunc

	mu      sync.Mutex
	entries map[string]*jobEntry
	wg      sync.WaitGroup
	started bool
}

// NewScheduler 构造调度器（对应 Spring 注入 Scheduler Bean）。
func NewScheduler(a *app.App) *Scheduler {
	ctx, cancel := context.WithCancel(context.Background())
	return &Scheduler{
		a:       a,
		log:     a.Log,
		loc:     time.Local,
		inv:     NewInvoker(a),
		ctx:     ctx,
		stop:    cancel,
		entries: map[string]*jobEntry{},
	}
}

var (
	schedOnce sync.Once
	schedInst *Scheduler
)

// SharedScheduler 返回进程内唯一的调度器实例（懒加载），供路由注册与 Service 共用。
func SharedScheduler(a *app.App) *Scheduler {
	schedOnce.Do(func() { schedInst = NewScheduler(a) })
	return schedInst
}

// Invoker 返回任务调用器（保存任务时做 invokeTarget 校验用）。
func (s *Scheduler) Invoker() *Invoker { return s.inv }

// Start 对应 SysJobServiceImpl.init()（@PostConstruct）：清空调度器并按 sys_job 全量重建。
// DIFF: Java 中 selectJobAll 失败会让 Bean 初始化失败、进程启动失败；Go 侧记录错误后继续，
// 避免调度器不可用导致整个 API 服务无法启动。
func (s *Scheduler) Start(ctx context.Context) error {
	s.mu.Lock()
	if s.started {
		s.mu.Unlock()
		return nil
	}
	s.started = true
	s.mu.Unlock()

	// JAVA 对照: scheduler.clear()
	s.Clear()

	var jobs []SysJob
	if err := s.a.DB.WithContext(ctx).Find(&jobs).Error; err != nil {
		s.log.Error("调度器初始化失败：读取 sys_job 出错", "err", err)
		return err
	}
	for i := range jobs {
		job := &jobs[i]
		// JAVA 对照: ScheduleUtils.createScheduleJob(scheduler, job)
		if err := s.Add(job); err != nil {
			s.log.Error("调度器初始化失败：任务配置非法，已跳过", "jobId", job.JobID, "jobName", job.JobName, "err", err)
		}
	}
	s.log.Info("调度器启动完成", "jobs", len(jobs))
	return nil
}

// Stop 停止调度器（对应 scheduler.shutdown()）。
// DIFF: main.go 不属于本模块，优雅停机时不会调用 Stop；进程退出由操作系统回收。
func (s *Scheduler) Stop() {
	s.stop()
	s.mu.Lock()
	for key, e := range s.entries {
		e.cancel()
		delete(s.entries, key)
	}
	s.mu.Unlock()
}

// Clear 对应 scheduler.clear()：移除全部任务。
func (s *Scheduler) Clear() {
	s.mu.Lock()
	entries := s.entries
	s.entries = map[string]*jobEntry{}
	s.mu.Unlock()
	for _, e := range entries {
		e.cancel()
	}
}

// Add 对应 ScheduleUtils.createScheduleJob：已存在则先删除再创建。
func (s *Scheduler) Add(job *SysJob) error {
	if job == nil {
		return fmt.Errorf("任务不能为空")
	}
	spec, err := parseCronExpression(job.CronExpression, s.loc)
	if err != nil {
		return err
	}
	key := jobKeyString(job.JobID, job.JobGroup)

	s.mu.Lock()
	if old, ok := s.entries[key]; ok {
		old.cancel()
		delete(s.entries, key)
	}
	ctx, cancel := context.WithCancel(s.ctx)
	e := &jobEntry{
		sched:  s,
		job:    cloneJob(job),
		spec:   spec,
		paused: job.IsPaused(),
		wake:   make(chan struct{}, 1),
		kick:   make(chan struct{}, 1),
		ctx:    ctx,
		cancel: cancel,
	}
	e.next = e.computeNext(time.Now())
	s.entries[key] = e
	s.mu.Unlock()

	s.wg.Add(1)
	go e.loop()
	return nil
}

// Remove 对应 scheduler.deleteJob(JobKey)。
func (s *Scheduler) Remove(jobID int64, group string) {
	key := jobKeyString(jobID, group)
	s.mu.Lock()
	e, ok := s.entries[key]
	if ok {
		delete(s.entries, key)
	}
	s.mu.Unlock()
	if ok {
		e.cancel()
	}
}

// Pause 对应 scheduler.pauseJob(JobKey)。
func (s *Scheduler) Pause(jobID int64, group string) {
	if e := s.entry(jobID, group); e != nil {
		e.setPaused(true)
	}
}

// Resume 对应 scheduler.resumeJob(JobKey)：恢复后按 misfire 策略决定是否立即补一次。
func (s *Scheduler) Resume(jobID int64, group string) {
	if e := s.entry(jobID, group); e != nil {
		e.resume()
	}
}

// Trigger 对应 scheduler.triggerJob(JobKey, dataMap)：立即执行一次（与暂停状态无关）。
func (s *Scheduler) Trigger(job *SysJob) error {
	if job == nil {
		return fmt.Errorf("任务不能为空")
	}
	e := s.entry(job.JobID, job.JobGroup)
	if e == nil {
		return fmt.Errorf("任务未在调度器中注册（jobId=%d, jobGroup=%s）", job.JobID, job.JobGroup)
	}
	e.kickNow()
	return nil
}

// Has 对应 scheduler.checkExists(JobKey)。
func (s *Scheduler) Has(jobID int64, group string) bool { return s.entry(jobID, group) != nil }

func (s *Scheduler) entry(jobID int64, group string) *jobEntry {
	key := jobKeyString(jobID, group)
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.entries[key]
}

func cloneJob(job *SysJob) *SysJob {
	cp := *job
	return &cp
}

// computeNext 计算下一次触发时间。
func (e *jobEntry) computeNext(from time.Time) time.Time {
	next, ok := e.spec.Next(from)
	if !ok {
		return time.Time{}
	}
	return next
}

func (e *jobEntry) setPaused(paused bool) {
	e.mu.Lock()
	e.paused = paused
	e.mu.Unlock()
	e.poke()
}

// resume 对应 resumeJob：Quartz 恢复时会处理 misfire——
// 策略 3（不触发立即执行）跳过错过的触发，其余策略立即补跑一次。
func (e *jobEntry) resume() {
	e.mu.Lock()
	e.paused = false
	policy := e.job.MisfirePolicy
	if policy == MisfireDoNothing {
		e.next = e.computeNext(time.Now())
	} else {
		e.next = time.Now()
	}
	e.mu.Unlock()
	e.poke()
}

func (e *jobEntry) kickNow() {
	select {
	case e.kick <- struct{}{}:
	default:
	}
}

func (e *jobEntry) poke() {
	select {
	case e.wake <- struct{}{}:
	default:
	}
}

// loop 是每个任务的调度循环。
func (e *jobEntry) loop() {
	defer e.sched.wg.Done()
	for {
		e.mu.Lock()
		paused, next := e.paused, e.next
		e.mu.Unlock()

		if !paused && !next.IsZero() && !next.After(time.Now()) {
			e.fire()
			e.advance(next)
			continue
		}

		var timerC <-chan time.Time
		var timer *time.Timer
		if !paused && !next.IsZero() {
			if d := time.Until(next); d > 0 {
				timer = time.NewTimer(d)
				timerC = timer.C
			}
		}
		select {
		case <-e.ctx.Done():
			if timer != nil {
				timer.Stop()
			}
			return
		case <-e.kick:
			if timer != nil {
				timer.Stop()
			}
			// 立即执行一次，不改变既定调度。
			e.fire()
			continue
		case <-e.wake:
			if timer != nil {
				timer.Stop()
			}
			continue
		case <-timerC:
			// 到点，交由下一轮循环的 due 分支处理。
		}
	}
}

// advance 计算下一次触发时间，并按 misfire 策略处理“已经错过”的触发点。
// JAVA 对照: CronTrigger 的 misfire 指令。
//
// DIFF: 精确复刻 Quartz 需要重放每一次错过的触发；这里收敛为“错过的触发最多补跑一次”：
//   - 0（默认 / smart policy）：补跑一次后继续
//   - 1（ignore misfires，忽略错过、立即触发执行）：补跑一次后继续
//   - 2（fire and proceed，触发一次执行）：补跑一次后继续
//   - 3（do nothing，不触发立即执行）：直接跳到下一个未来触发点
func (e *jobEntry) advance(scheduled time.Time) {
	now := time.Now()
	e.mu.Lock()
	missed := !scheduled.IsZero() && now.Sub(scheduled) > misfireThreshold
	policy := e.job.MisfirePolicy
	jobID, jobName := e.job.JobID, e.job.JobName
	e.mu.Unlock()

	if missed {
		e.sched.log.Warn("任务错过触发时间，按 misfire 策略处理",
			"jobId", jobID, "jobName", jobName,
			"misfirePolicy", policy, "delay", now.Sub(scheduled).String())
		if policy != MisfireDoNothing {
			e.fire() // 补跑一次
		}
	}

	e.mu.Lock()
	e.next = e.computeNext(time.Now())
	e.mu.Unlock()
}

// fire 触发一次执行，处理并发限制。
func (e *jobEntry) fire() {
	e.mu.Lock()
	job := *e.job
	e.mu.Unlock()

	// JAVA 对照: concurrent == "0" -> QuartzJobExecution（允许并发），否则
	// QuartzDisallowConcurrentExecution（同一 JobKey 不并发）。
	if job.IsConcurrentAllowed() {
		e.sched.wg.Add(1)
		go func() {
			defer e.sched.wg.Done()
			e.sched.execute(job)
		}()
		return
	}
	if !e.running.CompareAndSwap(false, true) {
		e.sched.log.Warn("任务禁止并发执行，跳过本次触发", "jobId", job.JobID, "jobName", job.JobName)
		return
	}
	e.sched.wg.Add(1)
	go func() {
		defer e.sched.wg.Done()
		defer e.running.Store(false)
		e.sched.execute(job)
	}()
}

// execute 对应 AbstractQuartzJob.execute：执行前后计时、异常捕获、写 sys_job_log。
func (s *Scheduler) execute(job SysJob) {
	start := time.Now()

	// JAVA 对照: try { before(); doExecute(); after(null) } catch (Exception e) { after(e) }
	var runErr error
	func() {
		defer func() {
			if r := recover(); r != nil {
				// 业务代码不应 panic；这里兜底避免拖垮整个进程。
				runErr = fmt.Errorf("panic: %v\n%s", r, string(debug.Stack()))
			}
		}()
		runErr = s.inv.Invoke(s.ctx, &job)
	}()
	stop := time.Now()

	jobLog := &SysJobLog{
		JobName:      job.JobName,
		JobGroup:     job.JobGroup,
		InvokeTarget: job.InvokeTarget,
		StartTime:    timePtr(start),
		StopTime:     timePtr(stop),
		JobMessage:   fmt.Sprintf("%s 总共耗时：%d毫秒", job.JobName, stop.Sub(start).Milliseconds()),
	}
	if runErr != nil {
		s.log.Error("任务执行异常  - ：", "jobId", job.JobID, "jobName", job.JobName, "err", runErr)
		jobLog.Status = Fail
		jobLog.ExceptionInfo = truncateRunes(runErr.Error(), 2000)
	} else {
		jobLog.Status = Success
	}
	jobLog.CreateTime = nowPtr()

	// JAVA 对照: SpringUtils.getBean(ISysJobLogService.class).addJobLog(sysJobLog)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := s.a.DB.WithContext(ctx).Create(jobLog).Error; err != nil {
		s.log.Error("写入调度日志失败", "jobId", job.JobID, "err", err)
	}
}

// truncateRunes 对应 StringUtils.substring(s, 0, n) 的等价截断（按字符而非字节）。
func truncateRunes(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}
