// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java:32-439
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/task/ShardingTableTask.java:23-103
// 类/职责: GaussDB → MySQL 月度分表的历史/增量同步、单月同步、未来分表预创建
// 对应 Go 文件: internal/modules/base/datasync_sync.go
//
// DIFF: Java 的 @Scheduled 在本仓库从未生效（全局没有 @EnableScheduling，ScheduleConfig 也被注释），
// 因此 Go 版本不自行挂 cron，而是把方法注册为 quartz 任务 Bean（sys_job 可配、可手动触发）。
// DIFF: Java syncSingleMonth 的第二个参数是 AtomicInteger，JobInvokeUtil 无法解析；
// Go 版本只接收月份一个参数，返回值/日志承担计数职责。
// DIFF: Java 单个方法内部吞掉异常只记日志；Go 版本会返回 error，让 sys_job_log 能看到失败。
package base

import (
	"context"
	"fmt"
	"sync"
	"time"

	"car-monit-go/internal/stream/sharding"
)

// SyncFullData 对应 SnapshotFlowSyncTask#syncFullData：按最早抓拍时间到当前月份并发全量同步。
func (s *DataSync) SyncFullData(ctx context.Context) (int, error) {
	started := time.Now()
	earliest, ok, err := s.source.Earliest(ctx)
	if err != nil {
		return 0, err
	}
	if !ok || earliest.IsZero() {
		s.log.Warn("GaussDB 中未查询到最早的 snapshottime，跳过分表同步")
		return 0, nil
	}
	partitions := monthPartitions(earliest, time.Now())
	s.log.Info("门架流水全量同步开始",
		"earliest", earliest.Format("2006-01-02 15:04:05"), "partitions", len(partitions), "source", s.source.Name())

	workers := s.app.Cfg.Snapshot.Flow.Sync.Workers
	if workers <= 0 {
		workers = 4
	}
	sem := make(chan struct{}, workers)
	var (
		wg       sync.WaitGroup
		mu       sync.Mutex
		total    int
		failures []string
	)
	for _, month := range partitions {
		month := month
		wg.Add(1)
		go func() {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			count, err := s.SyncSingleMonth(ctx, month)
			mu.Lock()
			defer mu.Unlock()
			if err != nil {
				failures = append(failures, month+": "+err.Error())
				return
			}
			total += count
		}()
	}
	wg.Wait()
	s.log.Info("门架流水全量同步结束",
		"total", total, "failedMonths", len(failures), "costMs", time.Since(started).Milliseconds())
	if len(failures) > 0 {
		return total, fmt.Errorf("%d 个月份同步失败: %v", len(failures), failures)
	}
	return total, nil
}

// SyncSingleMonth 对应 syncSingleMonth：月份格式 yyyyMM。
func (s *DataSync) SyncSingleMonth(ctx context.Context, month string) (int, error) {
	start, err := time.ParseInLocation("200601", month, time.Local)
	if err != nil {
		return 0, fmt.Errorf("月份格式非法（应为 yyyyMM）: %s", month)
	}
	start = time.Date(start.Year(), start.Month(), 1, 0, 0, 0, 0, start.Location())
	end := start.AddDate(0, 1, 0).Add(-time.Second)
	count, err := s.syncRange(ctx, start, end)
	if err != nil {
		return count, err
	}
	s.log.Info("门架流水单月同步完成", "month", month, "count", count)
	return count, nil
}

// SyncIncrementalData 对应 syncIncrementalData：从当前月分表的最大 snapshottime 同步到当前时间。
func (s *DataSync) SyncIncrementalData(ctx context.Context) (int, error) {
	now := time.Now()
	table := sharding.TableNameByDate(s.prefix, now, s.strategy)
	last, ok, err := s.maxSnapshottime(ctx, table)
	if err != nil {
		return 0, fmt.Errorf("查询 %s 最新 snapshottime 失败: %w", table, err)
	}
	start := last
	if !ok {
		start = time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())
	}
	s.log.Info("门架流水增量同步开始", "table", table,
		"start", start.Format("2006-01-02 15:04:05"), "end", now.Format("2006-01-02 15:04:05"))
	count, err := s.syncRange(ctx, start, now)
	if err != nil {
		return count, err
	}
	s.log.Info("门架流水增量同步完成", "count", count)
	return count, nil
}

// PreCreateTables 对应 ShardingTableTask：提前创建未来 N 个月的分表（含当前月）。
func (s *DataSync) PreCreateTables(ctx context.Context, months int) (string, error) {
	if months <= 0 {
		months = 4
	}
	m := sharding.NewMaintenance(s.db, s.prefix, s.strategy, s.log)
	created, existed, err := m.CreateFutureTables(ctx, months)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("创建完成，已存在表: %d, 新创建表: %d", existed, created), nil
}

// syncRange 对应 syncSnapshotFlowByDateRange：按页从上游拉取，按 snapshottime 分组写分表。
func (s *DataSync) syncRange(ctx context.Context, start, end time.Time) (int, error) {
	pageSize := s.app.Cfg.Snapshot.Flow.Sync.PageSize
	if pageSize <= 0 {
		pageSize = 1000
	}
	layout := "2006-01-02 15:04:05"
	startText, endText := start.Format(layout), end.Format(layout)
	total := 0
	for pageNum := 1; ; pageNum++ {
		if err := ctx.Err(); err != nil {
			return total, err
		}
		rows, err := s.source.Page(ctx, startText, endText, pageNum, pageSize)
		if err != nil {
			return total, err
		}
		if len(rows) == 0 {
			break
		}
		batch, skipped := groupSnapshotRows(s.prefix, s.strategy, rows)
		if skipped > 0 {
			s.log.Warn("同步数据缺少 snapshottime，已跳过", "count", skipped)
		}
		for table, list := range batch {
			if err := s.ensureShardTable(ctx, table); err != nil {
				return total, fmt.Errorf("创建分表 %s 失败: %w", table, err)
			}
			if err := s.insertShardRows(ctx, table, list); err != nil {
				return total, fmt.Errorf("写入分表 %s 失败: %w", table, err)
			}
		}
		total += len(rows) - skipped
		if len(rows) < pageSize {
			break
		}
	}
	return total, nil
}

// groupSnapshotRows 对应 groupByMonth：按 snapshottime 落到月度分表，null 行被跳过。
func groupSnapshotRows(prefix string, strategy sharding.Strategy,
	rows []*odsRtSzdnSnapshotFlowAddcode) (map[string][]*odsRtSzdnSnapshotFlowAddcode, int) {
	grouped := make(map[string][]*odsRtSzdnSnapshotFlowAddcode)
	skipped := 0
	for _, row := range rows {
		if row == nil || row.Snapshottime == nil || row.Snapshottime.IsZero() {
			skipped++
			continue
		}
		table := sharding.TableNameByDate(prefix, row.Snapshottime.Time, strategy)
		grouped[table] = append(grouped[table], row)
	}
	return grouped, skipped
}

// monthPartitions 对应 getMonthPartitions：返回 yyyyMM 列表（含首尾月份）。
func monthPartitions(start, end time.Time) []string {
	cur := time.Date(start.Year(), start.Month(), 1, 0, 0, 0, 0, start.Location())
	last := time.Date(end.Year(), end.Month(), 1, 0, 0, 0, 0, end.Location())
	out := make([]string, 0, 12)
	for !cur.After(last) {
		out = append(out, cur.Format("200601"))
		cur = cur.AddDate(0, 1, 0)
	}
	return out
}
