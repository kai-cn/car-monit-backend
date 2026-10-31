// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/RyTask.java:11-34
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/OrgTask.java:18-62
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/TrackTask.java:24-114
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/VehicleMonitoringTask.java:17-122
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/PartitionMaintenanceTask.java:20-114
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java:32-439
// 类/职责: 通过 invokeTarget 暴露给调度器的任务 Bean（ryTask / orgTask / trackTask / ...）
// 对应 Go 文件: internal/modules/quartz/tasks.go
// 关键映射: @Component("xxx") -> taskBean{name: "xxx"}；公开方法 -> TaskFunc
//
// DIFF: 任务方法的参数由 JobInvokeUtil 规则推断（Java 用反射按声明类型精确匹配），
// Go 侧在方法内显式断言参数个数与类型，个数/类型不符时返回与 Java 反射一致的语义错误。
// DIFF: 依赖尚未迁移业务服务（carTrackInfoService / httpBaseInfoApiService / GaussDB 同步等）的任务
// 以 "not migrated" 错误占位：调用会被写入 sys_job_log（status=1，exception_info 说明原因），
// 不会 panic，也不会静默成功。唯一天然空实现的是 OrgTask.syncOrgInfo（Java 方法体已被注释掉）
// 与 TrackTask.syncHistoryTrackNoCar（同样被注释掉）。
package quartz

import (
	"context"
	"fmt"
	"time"

	"car-monit-go/internal/app"
	"car-monit-go/internal/modules/manager"
)

// builtinTaskBeans 等价于 Spring 容器里所有 @Component 任务 Bean。
func builtinTaskBeans(a *app.App) []*taskBean {
	return []*taskBean{
		{name: "ryTask", methods: map[string]TaskFunc{
			"ryMultipleParams": func(ctx context.Context, args []any) error {
				if err := wantArgs("ryTask.ryMultipleParams", args, 5); err != nil {
					return err
				}
				s, err := argString(args, 0)
				if err != nil {
					return err
				}
				b, err := argBool(args, 1)
				if err != nil {
					return err
				}
				l, err := argInt64(args, 2)
				if err != nil {
					return err
				}
				d, err := argFloat64(args, 3)
				if err != nil {
					return err
				}
				i, err := argInt(args, 4)
				if err != nil {
					return err
				}
				// JAVA 对照: System.out.println(StringUtils.format("执行多参方法： ..."))
				logInfo(a, fmt.Sprintf("执行多参方法： 字符串类型%s，布尔类型%v，长整型%d，浮点型%v，整形%d", s, b, l, d, i))
				return nil
			},
			"ryParams": func(ctx context.Context, args []any) error {
				if err := wantArgs("ryTask.ryParams", args, 1); err != nil {
					return err
				}
				s, err := argString(args, 0)
				if err != nil {
					return err
				}
				logInfo(a, "执行有参方法："+s)
				return nil
			},
			"ryNoParams": func(ctx context.Context, args []any) error {
				if err := wantArgs("ryTask.ryNoParams", args, 0); err != nil {
					return err
				}
				logInfo(a, "执行无参方法")
				return nil
			},
			"autoBuildGoodsHb": func(ctx context.Context, args []any) error {
				// JAVA 对照: RyTask.autoBuildGoodsHb() —— 空方法。
				return wantArgs("ryTask.autoBuildGoodsHb", args, 0)
			},
		}},

		{name: "orgTask", methods: map[string]TaskFunc{
			"syncOrgInfo": func(ctx context.Context, args []any) error {
				// JAVA 对照: OrgTask.syncOrgInfo() 的方法体整体被注释，等价于空实现。
				return wantArgs("orgTask.syncOrgInfo", args, 0)
			},
		}},

		{name: "trackTask", methods: map[string]TaskFunc{
			// JAVA 对照: TrackTask.syncCurrentTrack -> carTrackInfoService.syncCurrentTrack()
			"syncCurrentTrack": func(ctx context.Context, args []any) error {
				if err := wantArgs("trackTask.syncCurrentTrack", args, 0); err != nil {
					return err
				}
				return manager.RunSyncCurrentTrack(a)
			},
			// JAVA 对照: TrackTask.syncSuspiciousCar -> carSuspiciousService.syncSuspiciousCar("redis", list)
			"syncSuspiciousCar": func(ctx context.Context, args []any) error {
				if err := wantArgs("trackTask.syncSuspiciousCar", args, 0); err != nil {
					return err
				}
				return manager.RunSyncSuspiciousCar(a)
			},
			// JAVA 对照: TrackTask.syncHistoryTrack -> carTrackInfoService.syncHistoryTrack + geometryService.updateRedisList()
			"syncHistoryTrack": notMigrated(a, "trackTask.syncHistoryTrack", "历史轨迹同步（ICarTrackInfoService/IGeometryService 未迁移）"),
			// JAVA 对照: TrackTask.saveCarExcept -> carExceptRecordService.saveCarExcept(...)
			"saveCarExcept": func(ctx context.Context, args []any) error {
				if err := wantArgs("trackTask.saveCarExcept", args, 0); err != nil {
					return err
				}
				return manager.RunSaveCarExcept(a)
			},
			"syncHistoryTrackNoCar": func(ctx context.Context, args []any) error {
				// JAVA 对照: TrackTask.syncHistoryTrackNoCar() 方法体被注释，等价于空实现。
				return wantArgs("trackTask.syncHistoryTrackNoCar", args, 0)
			},
			// JAVA 对照: TrackTask.changeCarSuspicious -> carSuspiciousService.changeCarSuspicious()
			"changeCarSuspicious": func(ctx context.Context, args []any) error {
				if err := wantArgs("trackTask.changeCarSuspicious", args, 0); err != nil {
					return err
				}
				return manager.RunChangeCarSuspicious(a)
			},
		}},

		{name: "vehicleMonitoringTask", methods: map[string]TaskFunc{
			"syncOrgInfo":             notMigrated(a, "vehicleMonitoringTask.syncOrgInfo", "机构信息同步（HttpBaseInfoApiService 未迁移）"),
			"syncSectionInfo":         notMigrated(a, "vehicleMonitoringTask.syncSectionInfo", "路段信息同步（HttpBaseInfoApiService 未迁移）"),
			"syncGantryInfo":          notMigrated(a, "vehicleMonitoringTask.syncGantryInfo", "门架信息同步（HttpBaseInfoApiService 未迁移）"),
			"syncServiceAreaInfoInfo": notMigrated(a, "vehicleMonitoringTask.syncServiceAreaInfoInfo", "服务区信息同步（HttpBaseInfoApiService 未迁移）"),
			"syncTollBoothInfoInfo":   notMigrated(a, "vehicleMonitoringTask.syncTollBoothInfoInfo", "收费所信息同步（HttpBaseInfoApiService 未迁移）"),
			"syncSfzjcxxInfoInfo":     notMigrated(a, "vehicleMonitoringTask.syncSfzjcxxInfoInfo", "收费站位置同步（HttpBaseInfoApiService 未迁移）"),
			"syncTollStationInfo":     notMigrated(a, "vehicleMonitoringTask.syncTollStationInfo", "收费站信息同步（HttpBaseInfoApiService 未迁移）"),
		}},

		{name: "partitionMaintenanceTask", methods: map[string]TaskFunc{
			"createFuturePartitions": func(ctx context.Context, args []any) error {
				if err := wantArgs("partitionMaintenanceTask.createFuturePartitions", args, 0); err != nil {
					return err
				}
				return createFuturePartitions(ctx, a)
			},
			"checkPartitionHealth": func(ctx context.Context, args []any) error {
				if err := wantArgs("partitionMaintenanceTask.checkPartitionHealth", args, 0); err != nil {
					return err
				}
				return checkPartitionHealth(ctx, a)
			},
		}},

		{name: "snapshotFlowSyncTask", methods: map[string]TaskFunc{
			"syncFullData":          notMigrated(a, "snapshotFlowSyncTask.syncFullData", "门架抓拍流水全量同步（GaussDB/分表 Mapper 未迁移）"),
			"manualFullSync":        notMigrated(a, "snapshotFlowSyncTask.manualFullSync", "门架抓拍流水全量同步（GaussDB/分表 Mapper 未迁移）"),
			"manualIncrementalSync": notMigrated(a, "snapshotFlowSyncTask.manualIncrementalSync", "门架抓拍流水增量同步（GaussDB/分表 Mapper 未迁移）"),
			"syncIncrementalData":   notMigrated(a, "snapshotFlowSyncTask.syncIncrementalData", "门架抓拍流水增量同步（GaussDB/分表 Mapper 未迁移）"),
			"syncSingleMonth":       notMigrated(a, "snapshotFlowSyncTask.syncSingleMonth", "门架抓拍流水单月同步（GaussDB/分表 Mapper 未迁移）"),
			"preCreateTables":       notMigrated(a, "snapshotFlowSyncTask.preCreateTables", "分表预创建（ShardingTableUtil 未迁移）"),
		}},
	}
}

// notMigrated 生成占位实现：方法存在（可通过保存校验），但执行时明确失败。
func notMigrated(a *app.App, name, reason string) TaskFunc {
	return func(ctx context.Context, args []any) error {
		return fmt.Errorf("%s 未迁移：%s", name, reason)
	}
}

func logInfo(a *app.App, msg string) {
	if a != nil && a.Log != nil {
		a.Log.Info(msg)
	}
}

func wantArgs(name string, args []any, n int) error {
	if len(args) != n {
		return fmt.Errorf("NoSuchMethodException: %s 需要 %d 个参数，实际 %d 个", name, n, len(args))
	}
	return nil
}

func argString(args []any, idx int) (string, error) {
	s, ok := args[idx].(string)
	if !ok {
		return "", fmt.Errorf("参数 %d 不是 String（Java 侧需使用单引号）: %v", idx+1, args[idx])
	}
	return s, nil
}

func argBool(args []any, idx int) (bool, error) {
	b, ok := args[idx].(bool)
	if !ok {
		return false, fmt.Errorf("参数 %d 不是 Boolean: %v", idx+1, args[idx])
	}
	return b, nil
}

func argInt(args []any, idx int) (int, error) {
	v, ok := args[idx].(int)
	if !ok {
		return 0, fmt.Errorf("参数 %d 不是 Integer: %v", idx+1, args[idx])
	}
	return v, nil
}

func argInt64(args []any, idx int) (int64, error) {
	v, ok := args[idx].(int64)
	if !ok {
		return 0, fmt.Errorf("参数 %d 不是 Long（Java 侧需带 L 后缀）: %v", idx+1, args[idx])
	}
	return v, nil
}

func argFloat64(args []any, idx int) (float64, error) {
	v, ok := args[idx].(float64)
	if !ok {
		return 0, fmt.Errorf("参数 %d 不是 Double（Java 侧需带 D 后缀）: %v", idx+1, args[idx])
	}
	return v, nil
}

// ---------------------------------------------------------------------------
// PartitionMaintenanceTask
// JAVA 对照: PartitionMaintenanceTask.java:28-114
// DIFF: Java 通过 Spring @Scheduled(cron="0 0 1 1 * ?") 自动注册，与 sys_job 表无关。
// Go 侧不自动挂载（任务清单由 sys_job 驱动），改为把方法注册为可被 invokeTarget 调用的 Bean：
//   partitionMaintenanceTask.createFuturePartitions() / partitionMaintenanceTask.checkPartitionHealth()
// 如需恢复“每月 1 号”的触发，可在 sys_job 中新增对应记录（cron: 0 0 1 1 * ?）。
// ---------------------------------------------------------------------------

const preCreateMonths = 6

// partitionTables 对应 PARTITION_TABLES。
var partitionTables = [][2]string{
	{"ods_rt_szdn_snapshot_flow_addcode", "snapshottime"},
	{"ods_lwzxsfsj_fee_records_01", "transtime"},
	{"zdata_trail_fitting", "extime"},
}

// createFuturePartitions 对应 PartitionMaintenanceTask.createFuturePartitions（第 49-84 行）。
func createFuturePartitions(ctx context.Context, a *app.App) error {
	logInfo(a, fmt.Sprintf("[分区维护] 开始创建未来%d个月的分区", preCreateMonths))
	current := time.Now()
	base := time.Date(current.Year(), current.Month(), 1, 0, 0, 0, 0, current.Location())

	for i := 1; i <= preCreateMonths; i++ {
		startMonth := base.AddDate(0, i, 0)
		endMonth := startMonth.AddDate(0, 1, 0)
		startDate := startMonth.Format("2006-01-02")
		endDate := endMonth.Format("2006-01-02")
		monthSuffix := startMonth.Format("200601")

		for _, cfg := range partitionTables {
			tableName := cfg[0]
			partitionName := tableName + "_p" + monthSuffix
			sql := fmt.Sprintf(
				"CREATE TABLE IF NOT EXISTS %s PARTITION OF %s FOR VALUES FROM ('%s') TO ('%s')",
				partitionName, tableName, startDate, endDate)
			// JAVA 对照: try { jdbcTemplate.execute(sql); } catch (Exception e) { log.warn(...) }
			if err := a.DB.WithContext(ctx).Exec(sql).Error; err != nil {
				logWarn(a, fmt.Sprintf("[分区维护] 分区可能已存在: %s - %v", partitionName, err))
				continue
			}
			logInfo(a, fmt.Sprintf("[分区维护] 创建分区成功: %s (范围: %s ~ %s)", partitionName, startDate, endDate))
		}
	}
	logInfo(a, "[分区维护] 分区创建任务完成")
	return nil
}

// checkPartitionHealth 对应 PartitionMaintenanceTask.checkPartitionHealth（第 90-113 行）。
func checkPartitionHealth(ctx context.Context, a *app.App) error {
	logInfo(a, "[分区维护] 开始检查分区健康状态")
	for _, cfg := range partitionTables {
		tableName := cfg[0]
		checkSQL := fmt.Sprintf(
			"SELECT inhrelid::regclass AS partition_name FROM pg_inherits WHERE inhparent = '%s'::regclass ORDER BY partition_name",
			tableName)
		var names []string
		if err := a.DB.WithContext(ctx).Raw(checkSQL).Scan(&names).Error; err != nil {
			logError(a, fmt.Sprintf("[分区维护] 检查表分区失败: %s", tableName), err)
			continue
		}
		for _, n := range names {
			logInfo(a, fmt.Sprintf("[分区维护] %s 分区: %s", tableName, n))
		}
	}
	logInfo(a, "[分区维护] 分区健康检查完成")
	return nil
}

func logWarn(a *app.App, msg string) {
	if a != nil && a.Log != nil {
		a.Log.Warn(msg)
	}
}

func logError(a *app.App, msg string, err error) {
	if a != nil && a.Log != nil {
		a.Log.Error(msg, "err", err)
	}
}
