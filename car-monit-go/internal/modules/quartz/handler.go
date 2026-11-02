// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java:32-142
// 类/职责: 调度任务 HTTP 入口
// 对应 Go 文件: internal/modules/quartz/handler.go
// 关键映射: @RestController @RequestMapping("/monitor/job") -> reg.Authed 上的显式路由
//
//	@PreAuthorize("@ss.hasPermi('monitor:job:xxx')") -> middleware.Perm
//	@Log(title, businessType) -> middleware.OperLog
//
// DIFF: @PathVariable Long[] jobIds -> gin :jobIds 逗号分隔解析（路径不变）。
// DIFF: @Valid 校验在 Service 中显式执行（见 validateJobForWrite），错误仍以 AjaxResult 返回。
package quartz

import (
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// JobHandler 对应 SysJobController。
type JobHandler struct {
	a   *app.App
	svc *Service
}

func NewJobHandler(a *app.App, svc *Service) *JobHandler {
	return &JobHandler{a: a, svc: svc}
}

// List 对应 SysJobController.list（第 42-49 行）：/monitor/job/list
func (h *JobHandler) List(c *gin.Context) {
	filter := JobFilter{
		JobName:      c.Query("jobName"),
		JobGroup:     c.Query("jobGroup"),
		Status:       c.Query("status"),
		InvokeTarget: c.Query("invokeTarget"),
	}
	rows, total, err := h.svc.ListJobs(c.Request.Context(), filter, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 SysJobController.export（第 54-62 行）：/monitor/job/export
func (h *JobHandler) Export(c *gin.Context) {
	filter := JobFilter{
		JobName:      c.Query("jobName"),
		JobGroup:     c.Query("jobGroup"),
		Status:       c.Query("status"),
		InvokeTarget: c.Query("invokeTarget"),
	}
	filename, err := h.svc.ExportJobs(c.Request.Context(), filter)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(filename))
}

// GetInfo 对应 SysJobController.getInfo（第 67-72 行）：/monitor/job/:jobId
func (h *JobHandler) GetInfo(c *gin.Context) {
	jobID, err := strconv.ParseInt(c.Param("jobId"), 10, 64)
	if err != nil {
		web.JSON(c, web.ErrorMsg("任务ID格式不正确"))
		return
	}
	job, err := h.svc.GetJob(c.Request.Context(), jobID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(job))
}

// Add 对应 SysJobController.add（第 77-88 行）：POST /monitor/job
func (h *JobHandler) Add(c *gin.Context) {
	var job SysJob
	if err := c.ShouldBindJSON(&job); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析失败："+err.Error()))
		return
	}
	if !IsValidCronExpression(job.CronExpression) {
		web.JSON(c, web.ErrorMsg("cron表达式不正确"))
		return
	}
	// JAVA 对照: sysJob.setCreateBy(SecurityUtils.getUsername())
	job.CreateBy = model.Ptr(auth.CurrentUsername(c))
	rows, err := h.svc.InsertJob(c.Request.Context(), &job)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 SysJobController.edit（第 93-104 行）：PUT /monitor/job
func (h *JobHandler) Edit(c *gin.Context) {
	var job SysJob
	if err := c.ShouldBindJSON(&job); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析失败："+err.Error()))
		return
	}
	if !IsValidCronExpression(job.CronExpression) {
		web.JSON(c, web.ErrorMsg("cron表达式不正确"))
		return
	}
	job.UpdateBy = model.Ptr(auth.CurrentUsername(c))
	rows, err := h.svc.UpdateJob(c.Request.Context(), &job)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// ChangeStatus 对应 SysJobController.changeStatus（第 109-117 行）：PUT /monitor/job/changeStatus
func (h *JobHandler) ChangeStatus(c *gin.Context) {
	var payload SysJob
	if err := c.ShouldBindJSON(&payload); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析失败："+err.Error()))
		return
	}
	rows, err := h.svc.ChangeStatus(c.Request.Context(), payload.JobID, payload.Status)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Run 对应 SysJobController.run（第 122-129 行）：PUT /monitor/job/run
func (h *JobHandler) Run(c *gin.Context) {
	var payload SysJob
	if err := c.ShouldBindJSON(&payload); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析失败："+err.Error()))
		return
	}
	if err := h.svc.Run(c.Request.Context(), &payload); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// Remove 对应 SysJobController.remove（第 134-141 行）：DELETE /monitor/job/:jobIds
func (h *JobHandler) Remove(c *gin.Context) {
	ids, err := parseInt64List(c.Param("jobIds"))
	if err != nil {
		web.JSON(c, web.ErrorMsg("任务ID格式不正确"))
		return
	}
	if err := h.svc.DeleteJobs(c.Request.Context(), ids); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// JobLogHandler 对应 SysJobLogController。
type JobLogHandler struct {
	a   *app.App
	svc *Service
}

func NewJobLogHandler(a *app.App, svc *Service) *JobLogHandler {
	return &JobLogHandler{a: a, svc: svc}
}

// List 对应 SysJobLogController.list（第 32-42 行）：/monitor/jobLog/list
func (h *JobLogHandler) List(c *gin.Context) {
	rows, total, err := h.svc.ListJobLogs(c.Request.Context(), jobLogFilter(c), web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 SysJobLogController.export（第 44-55 行）：/monitor/jobLog/export
func (h *JobLogHandler) Export(c *gin.Context) {
	filename, err := h.svc.ExportJobLogs(c.Request.Context(), jobLogFilter(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(filename))
}

// GetInfo 对应 SysJobLogController.getInfo（第 57-65 行）：/monitor/jobLog/:jobLogId
func (h *JobLogHandler) GetInfo(c *gin.Context) {
	// JAVA 对照: @PathVariable Long jobLogId —— Java 原代码方法参数名与 {configId} 不一致，
	// 依赖 -parameters 编译参数生效；这里按前端实际调用的 jobLogId 处理。
	logID, err := strconv.ParseInt(c.Param("jobLogId"), 10, 64)
	if err != nil {
		web.JSON(c, web.ErrorMsg("调度日志ID格式不正确"))
		return
	}
	row, err := h.svc.GetJobLog(c.Request.Context(), logID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// Remove 对应 SysJobLogController.remove（第 68-77 行）：DELETE /monitor/jobLog/:jobLogIds
func (h *JobLogHandler) Remove(c *gin.Context) {
	ids, err := parseInt64List(c.Param("jobLogIds"))
	if err != nil {
		web.JSON(c, web.ErrorMsg("调度日志ID格式不正确"))
		return
	}
	rows, err := h.svc.DeleteJobLogs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Clean 对应 SysJobLogController.clean（第 79-89 行）：DELETE /monitor/jobLog/clean
func (h *JobLogHandler) Clean(c *gin.Context) {
	if err := h.svc.CleanJobLog(c.Request.Context()); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// jobLogFilter 读取日志查询条件。
// JAVA 对照: SysJobLog 继承 BaseEntity 的 params.beginTime / params.endTime
// （前端以 params[beginTime] 形式提交）。
func jobLogFilter(c *gin.Context) JobFilter {
	return JobFilter{
		JobName:      c.Query("jobName"),
		JobGroup:     c.Query("jobGroup"),
		Status:       c.Query("status"),
		InvokeTarget: c.Query("invokeTarget"),
		BeginTime:    firstNonEmpty(c.Query("params[beginTime]"), c.Query("beginTime")),
		EndTime:      firstNonEmpty(c.Query("params[endTime]"), c.Query("endTime")),
	}
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if v != "" {
			return v
		}
	}
	return ""
}

// parseInt64List 解析 Long[]（路径中逗号分隔），对应 Spring 的数组路径参数绑定。
func parseInt64List(raw string) ([]int64, error) {
	parts := strings.Split(raw, ",")
	out := make([]int64, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		v, err := strconv.ParseInt(p, 10, 64)
		if err != nil {
			return nil, err
		}
		out = append(out, v)
	}
	return out, nil
}
