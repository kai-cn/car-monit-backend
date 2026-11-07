// JAVA 对照: 无（Java 侧用 Flyway/Liquibase 之外的 DBA 手工脚本，仓库内没有迁移框架）
// 类/职责: 数据库版本化迁移执行器 —— 按 migrations/NNNN_*.sql 顺序执行并记录 schema_migrations
// 对应 Go 文件: cmd/migrate/main.go
//
// DIFF: Java 仓库没有版本化迁移，表结构靠外部 carmonitdb.sql 导入；Go 侧补一个最小执行器，
// 让「基线导入 + 增量 DDL」可复现，且不引入第三方迁移库。
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"sort"
	"strings"
	"time"

	"gorm.io/gorm"

	"car-monit-go/internal/config"
	"car-monit-go/internal/database"
	"car-monit-go/internal/logx"
	"car-monit-go/internal/migrations"
)

const migrateTableDDL = `create table if not exists schema_migrations (
	version varchar(191) not null primary key,
	applied_at datetime not null
) engine=InnoDB default charset=utf8mb4`

func main() {
	configPath := flag.String("c", envOr("CARMONIT_CONFIG", "configs/config.yaml"), "配置文件路径")
	dryRun := flag.Bool("dry-run", false, "只打印待执行的迁移，不落库")
	flag.Parse()

	cfg, err := config.LoadConfig(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}
	logger := logx.New(cfg)
	db, err := database.Open(cfg, logger)
	if err != nil {
		logger.Error("连接数据库失败", "err", err)
		os.Exit(1)
	}
	sqlDB, err := db.DB()
	if err != nil {
		logger.Error("获取连接池失败", "err", err)
		os.Exit(1)
	}
	defer sqlDB.Close()

	files, err := loadMigrations()
	if err != nil {
		logger.Error("读取迁移文件失败", "err", err)
		os.Exit(1)
	}
	applied, err := appliedVersions(db)
	if err != nil {
		logger.Error("读取 schema_migrations 失败", "err", err)
		os.Exit(1)
	}

	pending := 0
	for _, f := range files {
		if applied[f.version] {
			continue
		}
		pending++
		if *dryRun {
			fmt.Printf("pending: %s\n", f.name)
			continue
		}
		if err := apply(db, f); err != nil {
			logger.Error("迁移执行失败", "file", f.name, "err", err)
			os.Exit(1)
		}
		logger.Info("迁移已应用", "file", f.name)
	}
	if pending == 0 {
		logger.Info("没有待执行的迁移", "total", len(files))
	}
}

type migration struct {
	version string
	name    string
	sql     string
}

func loadMigrations() ([]migration, error) {
	entries, err := migrations.FS.ReadDir(migrations.Dir)
	if err != nil {
		return nil, err
	}
	out := make([]migration, 0, len(entries))
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".sql") {
			continue
		}
		body, err := migrations.FS.ReadFile(migrations.Dir + "/" + e.Name())
		if err != nil {
			return nil, err
		}
		version := strings.TrimSuffix(e.Name(), ".sql")
		if idx := strings.IndexByte(version, '_'); idx > 0 {
			version = version[:idx]
		}
		out = append(out, migration{version: version, name: e.Name(), sql: string(body)})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].name < out[j].name })
	return out, nil
}

func appliedVersions(db *gorm.DB) (map[string]bool, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := db.WithContext(ctx).Exec(migrateTableDDL).Error; err != nil {
		return nil, err
	}
	var versions []string
	if err := db.WithContext(ctx).Raw("select version from schema_migrations").Scan(&versions).Error; err != nil {
		return nil, err
	}
	out := make(map[string]bool, len(versions))
	for _, v := range versions {
		out[v] = true
	}
	return out, nil
}

// apply 在单个事务内执行一个迁移文件并登记版本。
//
// 注意：MySQL 的 DDL 会隐式提交，事务对 DDL 不可回滚；这里仍包事务以保证
// “DML 与版本登记”要么都成功要么都不写，DDL 失败需人工修复后重跑。
func apply(db *gorm.DB, f migration) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	return db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// 逐条执行，便于定位失败语句（文件内以分号结尾的语句）。
		for _, stmt := range splitStatements(f.sql) {
			if err := tx.Exec(stmt).Error; err != nil {
				return fmt.Errorf("%s: %w", firstLine(stmt), err)
			}
		}
		return tx.Exec("insert into schema_migrations (version, applied_at) values (?, ?)",
			f.version, time.Now()).Error
	})
}

// splitStatements 去掉整行注释后按分号切分；迁移文件里没有存储过程/触发器，
// 该简化足够，并在 migrations/README.md 中约定不要写含内部分号的 DDL。
func splitStatements(script string) []string {
	var b strings.Builder
	for _, line := range strings.Split(script, "\n") {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "--") {
			continue
		}
		b.WriteString(line)
		b.WriteByte('\n')
	}
	parts := strings.Split(b.String(), ";")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if s := strings.TrimSpace(p); s != "" {
			out = append(out, s)
		}
	}
	return out
}

func firstLine(s string) string {
	if idx := strings.IndexByte(s, '\n'); idx >= 0 {
		s = s[:idx]
	}
	if len(s) > 80 {
		s = s[:80]
	}
	return s
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
