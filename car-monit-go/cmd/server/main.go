// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/RuoYiApplication.java
// 类/职责: 进程入口 — 加载配置、初始化数据源/缓存、装配路由、优雅停机
// 对应 Go 文件: cmd/server/main.go
//
// DIFF: Spring Boot 由 SpringApplication.run 完成容器启动、内嵌 Tomcat 监听；
// Go 显式按顺序构造依赖，net/http.Server + signal.Notify 实现优雅停机。
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"car-monit-go/internal/app"
	"car-monit-go/internal/cache"
	"car-monit-go/internal/config"
	"car-monit-go/internal/database"
	"car-monit-go/internal/logx"
	"car-monit-go/internal/router"

	// 业务模块通过 init() 向 router 注册路由。
	_ "car-monit-go/internal/modules/base"
	_ "car-monit-go/internal/modules/flow"
	_ "car-monit-go/internal/modules/generator"
	_ "car-monit-go/internal/modules/manager"
	_ "car-monit-go/internal/modules/ops"
	_ "car-monit-go/internal/modules/quartz"
	_ "car-monit-go/internal/modules/system"
	_ "car-monit-go/internal/modules/systemaux"
)

func main() {
	configPath := flag.String("c", envOr("CARMONIT_CONFIG", "configs/config.yaml"), "配置文件路径")
	flag.Parse()

	cfg, err := config.LoadConfig(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	logger := logx.New(cfg)

	db, err := database.Open(cfg, logger)
	if err != nil {
		logger.Error("初始化数据库失败", "err", err)
		os.Exit(1)
	}
	sqlDB, err := db.DB()
	if err != nil {
		logger.Error("获取数据库连接池失败", "err", err)
		os.Exit(1)
	}
	defer sqlDB.Close()

	c, err := cache.New(cfg)
	if err != nil {
		logger.Error("初始化 Redis 失败", "err", err)
		os.Exit(1)
	}
	defer c.Close()

	a := app.New(cfg, db, c, logger)
	engine := router.Setup(a)

	addr := fmt.Sprintf(":%d", cfg.Server.Port)
	srv := &http.Server{
		Addr:              addr,
		Handler:           engine,
		ReadHeaderTimeout: 10 * time.Second,
	}

	go func() {
		logger.Info("服务启动", "addr", addr, "config", cfg.ConfigFile)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("HTTP 服务异常退出", "err", err)
			os.Exit(1)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("收到退出信号，开始优雅停机")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		logger.Error("优雅停机失败", "err", err)
	}
	logger.Info("服务已退出")
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
