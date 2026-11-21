// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java:33-141
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobLogController.java:26-89
// 类/职责: quartz 模块路由注册 + 调度器启动钩子
// 对应 Go 文件: internal/modules/quartz/register.go
// 关键映射: @RequestMapping("/monitor/job")/@RequestMapping("/monitor/jobLog") -> 显式路径
//
//	@PreAuthorize("@ss.hasPermi(...)") -> middleware.Perm(...)
//	@Log(title, businessType) -> middleware.OperLog(...)
//
// DIFF: Spring 在 Bean 初始化时（@PostConstruct init）启动调度器；Go 在首次 Register 时
// 懒创建单例并 Start（main.go 由并行协作方维护，本模块不能改）。
// DIFF: 优雅停机由 main 调用 quartz.ShutdownShared 触发，限时等待在途任务收敛后再退出。
package quartz

import (
	"context"

	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
)

func init() {
	router.RegisterModule(Register)
}

// Register 挂载 /monitor/job、/monitor/jobLog 全部端点。
func Register(reg *router.Registry) {
	a := reg.App

	sched := SharedScheduler(a)
	if err := sched.Start(context.Background()); err != nil {
		a.Log.Error("调度器启动失败，接口仍可用（任务不会自动触发）", "err", err)
	}

	svc := NewService(a)
	job := NewJobHandler(a, svc)
	jobLog := NewJobLogHandler(a, svc)

	g := reg.Authed

	// JAVA 对照: SysJobController
	g.GET("/monitor/job/list", middleware.Perm("monitor:job:list"), job.List)
	g.GET("/monitor/job/export", middleware.Perm("monitor:job:export"),
		middleware.OperLog(a, "定时任务", middleware.BusinessExport), job.Export)
	g.GET("/monitor/job/:jobId", middleware.Perm("monitor:job:query"), job.GetInfo)
	g.POST("/monitor/job", middleware.Perm("monitor:job:add"),
		middleware.OperLog(a, "定时任务", middleware.BusinessInsert), job.Add)
	g.PUT("/monitor/job", middleware.Perm("monitor:job:edit"),
		middleware.OperLog(a, "定时任务", middleware.BusinessUpdate), job.Edit)
	g.PUT("/monitor/job/changeStatus", middleware.Perm("monitor:job:changeStatus"),
		middleware.OperLog(a, "定时任务", middleware.BusinessUpdate), job.ChangeStatus)
	g.PUT("/monitor/job/run", middleware.Perm("monitor:job:changeStatus"),
		middleware.OperLog(a, "定时任务", middleware.BusinessUpdate), job.Run)
	g.DELETE("/monitor/job/:jobIds", middleware.Perm("monitor:job:remove"),
		middleware.OperLog(a, "定时任务", middleware.BusinessDelete), job.Remove)

	// JAVA 对照: SysJobLogController
	g.GET("/monitor/jobLog/list", middleware.Perm("monitor:job:list"), jobLog.List)
	g.GET("/monitor/jobLog/export", middleware.Perm("monitor:job:export"),
		middleware.OperLog(a, "任务调度日志", middleware.BusinessExport), jobLog.Export)
	g.GET("/monitor/jobLog/:jobLogId", middleware.Perm("monitor:job:query"), jobLog.GetInfo)
	g.DELETE("/monitor/jobLog/:jobLogIds", middleware.Perm("monitor:job:remove"),
		middleware.OperLog(a, "定时任务调度日志", middleware.BusinessDelete), jobLog.Remove)
	g.DELETE("/monitor/jobLog/clean", middleware.Perm("monitor:job:remove"),
		middleware.OperLog(a, "调度日志", middleware.BusinessClean), jobLog.Clean)
}
