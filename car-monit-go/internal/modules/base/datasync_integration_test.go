//go:build integration

// 类/职责: 数据接入的真实依赖集成测试（默认不参与 go test ./...）
// 对应 Go 文件: internal/modules/base/datasync_integration_test.go
//
// 运行方式：
//
//	$env:CARMONIT_TEST_DSN="root:root@tcp(127.0.0.1:3307)/carmonit_ingest_test?charset=utf8mb4&parseTime=True&loc=Local"
//	go test -tags=integration -run TestDataSyncSyncSingleMonth -v ./internal/modules/base
//
// 前置条件：测试库里存在模板表 ods_rt_szdn_snapshot_flow_addcode（与 Java 表结构一致）。
// 本测试只写入 runID 前缀的分表，不会触碰真实业务表。
package base

import (
	"context"
	"io"
	"log/slog"
	"os"
	"testing"
	"time"

	gormmysql "gorm.io/driver/mysql"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"

	"car-monit-go/internal/app"
	"car-monit-go/internal/config"
	"car-monit-go/internal/stream/sharding"
)

// stubSource 模拟 vehicleMonitor 的 /base/snapshotflow/* 响应（GaussDB 适配层的替身）。
type stubSource struct {
	earliest time.Time
	pages    [][]*odsRtSzdnSnapshotFlowAddcode
	calls    int
}

func (s *stubSource) Name() string { return "stub" }

func (s *stubSource) Earliest(context.Context) (time.Time, bool, error) {
	return s.earliest, !s.earliest.IsZero(), nil
}

func (s *stubSource) Page(context.Context, string, string, int, int) ([]*odsRtSzdnSnapshotFlowAddcode, error) {
	if s.calls >= len(s.pages) {
		return nil, nil
	}
	rows := s.pages[s.calls]
	s.calls++
	return rows, nil
}

func TestDataSyncSyncSingleMonthIntegration(t *testing.T) {
	dsn := os.Getenv("CARMONIT_TEST_DSN")
	if dsn == "" {
		t.Skip("未设置 CARMONIT_TEST_DSN，跳过真实 MySQL 集成测试")
	}
	db, err := gorm.Open(gormmysql.Open(dsn),
		&gorm.Config{Logger: gormlogger.Default.LogMode(gormlogger.Silent)})
	if err != nil {
		t.Fatalf("连接测试库失败: %v", err)
	}
	if sqlDB, err := db.DB(); err == nil {
		defer func() { _ = sqlDB.Close() }()
	}

	runID := "e2e_" + time.Now().Format("20060102150405")
	prefix := runID + "_snapshot_"
	cfg := &config.Config{}
	cfg.Snapshot.Flow.Sharding.TablePrefix = prefix
	cfg.Snapshot.Flow.Sharding.ShardingType = "month"
	cfg.Snapshot.Flow.Sync.PageSize = 1000
	a := &app.App{Cfg: cfg, DB: db, Log: slog.New(slog.NewTextHandler(io.Discard, nil))}
	s := NewDataSync(a)

	ts := time.Date(2026, 1, 15, 10, 0, 0, 0, time.Local)
	s.source = &stubSource{pages: [][]*odsRtSzdnSnapshotFlowAddcode{
		{
			{BigID: strPtr("it-1"), Snapshottime: &isoDateTime{Time: ts}, Platenumber: strPtr("IT-1")},
			{BigID: strPtr("it-2"), Snapshottime: &isoDateTime{Time: ts}, Platenumber: strPtr("IT-2")},
		},
		// 第二页故意加入缺 snapshottime 的行，应被跳过而不是写入。
		{{BigID: strPtr("it-3")}},
		{},
	}}

	count, err := s.SyncSingleMonth(context.Background(), "202601")
	if err != nil {
		t.Fatalf("SyncSingleMonth: %v", err)
	}
	if count != 2 {
		t.Fatalf("同步计数=%d want 2（缺 snapshottime 的行应被跳过）", count)
	}

	table := sharding.TableNameByDate(prefix, ts, sharding.Monthly)
	var got int64
	if err := db.Raw("SELECT COUNT(*) FROM `" + table + "`").Scan(&got).Error; err != nil {
		t.Fatalf("查询分表失败: %v", err)
	}
	if got != 2 {
		t.Fatalf("%s 行数=%d want 2", table, got)
	}

	// 重叠同步必须幂等：再跑一次，行数不变。
	if _, err := s.SyncSingleMonth(context.Background(), "202601"); err != nil {
		t.Fatalf("重复 SyncSingleMonth: %v", err)
	}
	if err := db.Raw("SELECT COUNT(*) FROM `" + table + "`").Scan(&got).Error; err != nil {
		t.Fatalf("重复同步后查询失败: %v", err)
	}
	if got != 2 {
		t.Fatalf("重复同步后行数=%d want 2（ON DUPLICATE KEY UPDATE 应保持幂等）", got)
	}

	// 分表预创建：对应 ShardingTableUtil.getFutureTableNames(N)，从当前月开始共 N 个周期。
	result, err := s.PreCreateTables(context.Background(), 2)
	if err != nil {
		t.Fatalf("PreCreateTables: %v", err)
	}
	t.Logf("PreCreateTables: %s", result)
	now := time.Now()
	for i := 0; i < 2; i++ {
		name := sharding.TableNameByDate(prefix, now.AddDate(0, i, 0), sharding.Monthly)
		var exists int64
		if err := db.Raw(`SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
			WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?`, name).Scan(&exists).Error; err != nil {
			t.Fatalf("检查分表存在性失败: %v", err)
		}
		if exists == 0 {
			t.Errorf("预创建分表 %s 不存在", name)
		}
	}
}
