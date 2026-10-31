// JAVA 对照: 无（Java 项目未提供健康检查端点；Spring Boot Actuator 未启用）
// 类/职责: 运维探活接口
// 对应 Go 文件: internal/handler/health.go
//
// DIFF: Go 版新增 /healthz，便于容器探活与迁移验收；不影响既有业务端点。
package handler

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/web"
)

// Health 返回进程状态、数据库与 Redis 连通性。
func Health(a *app.App) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx := c.Request.Context()
		status := "UP"
		dbStatus := "UP"
		if sqlDB, err := a.DB.DB(); err != nil || sqlDB.PingContext(ctx) != nil {
			dbStatus = "DOWN"
		}
		redisStatus := "UP"
		if err := a.Cache.Client().Ping(ctx).Err(); err != nil {
			redisStatus = "DOWN"
		}
		if dbStatus == "DOWN" || redisStatus == "DOWN" {
			status = "DOWN"
		}
		web.JSON(c, web.AJ(web.StatusSuccess, status, gin.H{
			"database": dbStatus,
			"redis":    redisStatus,
			"version":  a.Cfg.RuoYi.Version,
		}))
	}
}
