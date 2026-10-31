// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/DruidConfig.java
// JAVA 对照: ruoyi-admin/src/main/resources/application-druid.yml
// 类/职责: 数据源 — 对应 DruidDataSource + MyBatis SqlSessionFactory
// 对应 Go 文件: internal/database/database.go
//
// DIFF: Java 由 Druid 管理连接池、P6Spy 打印 SQL；Go 由 database/sql 连接池 + GORM Logger 承担。
// DIFF: 多数据源 @DataSource(AOP) 在 Go 中简化为单一主库；从库配置保留但默认关闭。
package database

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"

	"car-monit-go/internal/config"
)

func Open(cfg *config.Config, log *slog.Logger) (*gorm.DB, error) {
	gcfg := &gorm.Config{
		SkipDefaultTransaction: true,
		Logger: gormlogger.New(
			slogWriter{log: log},
			gormlogger.Config{
				SlowThreshold:             time.Duration(cfg.Database.Pool.SlowSQLMillis) * time.Millisecond,
				LogLevel:                  gormlogger.Warn,
				IgnoreRecordNotFoundError: true,
				Colorful:                  false,
			},
		),
	}
	db, err := gorm.Open(mysql.Open(cfg.Database.Master.DSN), gcfg)
	if err != nil {
		return nil, fmt.Errorf("连接 MySQL 失败: %w", err)
	}
	sqlDB, err := db.DB()
	if err != nil {
		return nil, err
	}
	sqlDB.SetMaxOpenConns(orDefault(cfg.Database.Pool.MaxOpenConns, 100))
	sqlDB.SetMaxIdleConns(orDefault(cfg.Database.Pool.MaxIdleConns, 10))
	sqlDB.SetConnMaxLifetime(time.Duration(orDefault(cfg.Database.Pool.ConnMaxLifetime, 900)) * time.Second)
	sqlDB.SetConnMaxIdleTime(time.Duration(orDefault(cfg.Database.Pool.ConnMaxIdleTime, 300)) * time.Second)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := sqlDB.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("MySQL ping 失败: %w", err)
	}
	return db, nil
}

func orDefault(v, def int) int {
	if v > 0 {
		return v
	}
	return def
}

// slogWriter 把 GORM 日志桥接到 slog（对应 P6Spy 的 SQL 输出）。
type slogWriter struct{ log *slog.Logger }

func (w slogWriter) Printf(format string, args ...any) {
	w.log.Debug(fmt.Sprintf(format, args...), "component", "gorm")
}
