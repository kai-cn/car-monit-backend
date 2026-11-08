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
	"car-monit-go/internal/idgen"
	"car-monit-go/internal/logx"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/modules/base"
	"car-monit-go/internal/modules/quartz"
	"car-monit-go/internal/router"
	"car-monit-go/internal/stream/kafka"

	// 业务模块通过 init() 向 router 注册路由。
	_ "car-monit-go/internal/modules/flow"
	_ "car-monit-go/internal/modules/generator"
	_ "car-monit-go/internal/modules/manager"
	_ "car-monit-go/internal/modules/ops"
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

	// 雪花 ID 的实例标识必须在任何写入之前确定：多副本共用 (datacenterId, workerId)
	// 会在同一毫秒内生成重复主键。未配置时按主机名自动推导并打印，便于排障。
	idSource, err := idgen.Init(cfg.Instance.WorkerID, cfg.Instance.DatacenterID)
	if err != nil {
		logger.Error("初始化雪花 ID 生成器失败", "err", err)
		os.Exit(1)
	}
	workerID, datacenterID := idgen.IDs()
	logger.Info("雪花 ID 实例标识", "workerId", workerID, "datacenterId", datacenterID, "source", idSource)

	// 数据接入：Kafka 消费者把门架抓拍流水写入 MySQL 月度分表与 ES。
	// 关闭时（默认）数据接入仍由 Java 服务承担，Go 只提供查询/同步任务入口。

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
	defer func() { _ = c.Close() }()

	a := app.New(cfg, db, c, logger)

	var ingestCancel context.CancelFunc
	ingestDone := make(chan struct{})
	if cfg.Kafka.Enabled {
		dataSync := base.NewDataSync(a)
		consumer := kafka.NewConsumer(cfg, cfg.Kafka.Topic.SnapshotFlow, cfg.Kafka.Topic.SnapshotFlowDLQ,
			dataSync.HandleSnapshotFlowBatch, logger)
		ingestCtx, cancel := context.WithCancel(context.Background())
		ingestCancel = cancel
		go func() {
			defer close(ingestDone)
			logger.Info("Kafka 消费者已启动",
				"topic", cfg.Kafka.Topic.SnapshotFlow, "dlq", cfg.Kafka.Topic.SnapshotFlowDLQ,
				"group", cfg.Kafka.Consumer.GroupID, "esEnabled", cfg.Elasticsearch.Enabled)
			if err := consumer.Run(ingestCtx); err != nil {
				logger.Error("Kafka 消费者异常退出", "err", err)
			}
		}()
	} else {
		close(ingestDone)
		logger.Info("Kafka 未启用（kafka.enabled=false），门架抓拍流水接入仍由 Java 服务承担")
		if cfg.Elasticsearch.Enabled {
			logger.Warn("Elasticsearch 已启用但 Kafka 未启用：Go 不会写入索引")
		}
	}

	engine := router.Setup(a)

	addr := fmt.Sprintf(":%d", cfg.Server.Port)
	srv := &http.Server{
		Addr:              addr,
		Handler:           engine,
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       60 * time.Second,
		// 导出类接口（xlsx 生成 + 附件流）可能耗时较长，写超时放宽到 5 分钟。
		WriteTimeout: 5 * time.Minute,
		IdleTimeout:  120 * time.Second,
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
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	// 先停 HTTP 入口，不再接收新请求。
	if err := srv.Shutdown(shutdownCtx); err != nil {
		logger.Error("优雅停机失败", "err", err)
	}
	// 再收敛 Kafka 消费者（限 15s）：停止拉取并提交当前批次的 offset。
	if ingestCancel != nil {
		ingestCancel()
		select {
		case <-ingestDone:
		case <-time.After(15 * time.Second):
			logger.Warn("Kafka 消费者未在 15s 内退出")
		}
	}
	// 再收敛定时任务（限 15s），避免任务写到一半被进程退出打断。
	schedCtx, schedCancel := context.WithTimeout(context.Background(), 15*time.Second)
	quartz.ShutdownShared(schedCtx)
	schedCancel()
	// 最后排空操作日志队列（限 5s）。
	logCtx, logCancel := context.WithTimeout(context.Background(), 5*time.Second)
	middleware.StopOperLog(logCtx)
	logCancel()
	logger.Info("服务已退出")
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
