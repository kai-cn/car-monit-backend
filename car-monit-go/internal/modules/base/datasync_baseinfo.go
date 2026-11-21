// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/VehicleMonitoringTask.java:17-122
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpBaseInfoApiService.java
// 类/职责: 机构/路段/门架/服务区/收费所/收费站位置/收费站 七张基础表的全量同步
// 对应 Go 文件: internal/modules/base/datasync_baseinfo.go
//
// DIFF: Java 每个方法 @Transactional(truncate + saveBatch)；MySQL 的 TRUNCATE 是 DDL 会隐式提交，
// 事务并不提供原子性（与 Java 实际行为一致）。Go 同样先截断再批量插入，异常时表可能为空，
// 日志会明确告警；如需原子替换应改为 DELETE + 事务（会改变自增与锁语义，未采用）。
// DIFF: syncSectionInfo 的 Java setCacheList 是 rightPushAll（不删旧值），每天同步会无限追加；
// Go 用 ReplaceJavaList 整份覆盖，避免 section_list 无界增长与重复元素。
package base

import (
	"context"
	"fmt"
	"time"

	"car-monit-go/internal/cache"
)

// syncBaseInfo 对应一个 VehicleMonitoringTask 方法：拉取 → 截断 → 批量插入。
func syncBaseInfo[T any](s *DataSync, ctx context.Context, table, path string) error {
	rows, err := loadBaseInfo[T](s, ctx, path)
	if err != nil {
		return err
	}
	return replaceBaseInfo(s, ctx, table, rows)
}

func loadBaseInfo[T any](s *DataSync, ctx context.Context, path string) ([]*T, error) {
	started := time.Now()
	var rows []*T
	if err := s.fetchBaseInfoList(ctx, path, &rows); err != nil {
		return nil, err
	}
	s.log.Info("基础信息拉取完成", "path", path, "count", len(rows), "costMs", time.Since(started).Milliseconds())
	return rows, nil
}

func replaceBaseInfo[T any](s *DataSync, ctx context.Context, table string, rows []*T) error {
	if len(rows) == 0 {
		s.log.Warn("上游返回 0 条记录，按 Java 语义仍会清空表", "table", table)
	}
	if err := s.db.WithContext(ctx).Exec("TRUNCATE TABLE `" + table + "`").Error; err != nil {
		return fmt.Errorf("清空 %s 失败: %w", table, err)
	}
	if len(rows) == 0 {
		return nil
	}
	if err := s.db.WithContext(ctx).Table(table).CreateInBatches(rows, 500).Error; err != nil {
		return fmt.Errorf("写入 %s 失败: %w", table, err)
	}
	s.log.Info("基础信息同步完成", "table", table, "count", len(rows))
	return nil
}

// SyncOrgInfo 对应 VehicleMonitoringTask#syncOrgInfo → GET /base/org/listAll。
func (s *DataSync) SyncOrgInfo(ctx context.Context) error {
	return syncBaseInfo[odsYhglVBaseOrg](s, ctx, "ods_yhgl_v_base_org", "/base/org/listAll")
}

// SyncSectionInfo 对应 syncSectionInfo → GET /base/section/listAll，并刷新 Redis section_list。
func (s *DataSync) SyncSectionInfo(ctx context.Context) error {
	rows, err := loadBaseInfo[odsSzdnSection](s, ctx, "/base/section/listAll")
	if err != nil {
		return err
	}
	if err := replaceBaseInfo(s, ctx, "ods_szdn_section", rows); err != nil {
		return err
	}
	if s.app.Cache == nil {
		return nil
	}
	values := make([]any, 0, len(rows))
	for _, row := range rows {
		values = append(values, row)
	}
	if err := s.app.Cache.ReplaceJavaList(ctx, sectionListKey, values, cache.OdsSzdnSectionJava); err != nil {
		s.log.Warn("刷新 section_list 缓存失败", "err", err)
	}
	return nil
}

// SyncGantryInfo 对应 syncGantryInfo → GET /base/gantry/listAll。
func (s *DataSync) SyncGantryInfo(ctx context.Context) error {
	return syncBaseInfo[odsSzdnGantry](s, ctx, "ods_szdn_gantry", "/base/gantry/listAll")
}

// SyncServiceAreaInfo 对应 syncServiceAreaInfoInfo → GET /base/fwqjcxx/listAll。
func (s *DataSync) SyncServiceAreaInfo(ctx context.Context) error {
	return syncBaseInfo[dwdLcztFwqjcxx](s, ctx, "dwd_lczt_fwqjcxx", "/base/fwqjcxx/listAll")
}

// SyncTollBoothInfo 对应 syncTollBoothInfoInfo → GET /base/sfsjcxx/listAll。
func (s *DataSync) SyncTollBoothInfo(ctx context.Context) error {
	return syncBaseInfo[dwdLcztSfsjcxx](s, ctx, "dwd_lczt_sfsjcxx", "/base/sfsjcxx/listAll")
}

// SyncSfzjcxxInfo 对应 syncSfzjcxxInfoInfo → GET /base/sfzjcxx/listAll。
func (s *DataSync) SyncSfzjcxxInfo(ctx context.Context) error {
	return syncBaseInfo[dwdLcztSfzjcxx](s, ctx, "dwd_lczt_sfzjcxx", "/base/sfzjcxx/listAll")
}

// SyncTollStationInfo 对应 syncTollStationInfo → GET /base/toll/listAll。
func (s *DataSync) SyncTollStationInfo(ctx context.Context) error {
	return syncBaseInfo[odsSzdnToll](s, ctx, "ods_szdn_toll", "/base/toll/listAll")
}
