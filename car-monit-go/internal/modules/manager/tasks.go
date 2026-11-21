// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/TrackTask.java
// 类/职责: 供 quartz 调度器调用的车辆监管任务（不依赖 gin.Context）
// 对应 Go 文件: internal/modules/manager/tasks.go
//
// DIFF: Java 通过 Spring 注入 Service；这里由 quartz 传入 *app.App，内部构造 handler。
package manager

import (
	"context"
	"time"

	"car-monit-go/internal/app"
)

// RunSyncCurrentTrack 对应 trackTask.syncCurrentTrack。
func RunSyncCurrentTrack(a *app.App) error {
	h := newHandler(a)
	ctx := context.Background()
	cars := h.loadCarListContext(ctx)
	for _, car := range cars {
		carNo := isNull(car.CarNo)
		var trail trailInfo
		found := a.Cache.Get(ctx, carCurrentTrailKey+carNo, &trail)
		cols := map[string]any{"status": "0", "track_josn": nil}
		if found {
			cols["status"] = "1"
			cols["track_josn"] = mustMarshal(trail)
			if points, ok := trail.TrailList.([]any); ok && len(points) > 0 {
				if point, ok := points[len(points)-1].(map[string]any); ok {
					cols["last_pass_longitude"] = stringValue(point["lon"])
					cols["last_pass_latitude"] = stringValue(point["lat"])
					cols["last_pass_time"] = stringValue(point["captureTime"])
					cols["last_pass_address"] = stringValue(point["devName"])
					cols["last_pass_type"] = stringValue(point["stateType"])
				}
			}
		}
		if _, err := h.updateRow(ctx, carInfoTable, strOf(car.ID), cols); err != nil {
			a.Log.Warn("同步实时轨迹失败", "carNo", carNo, "err", err)
		}
	}
	return h.refreshCarListContext(ctx)
}

// RunSyncSuspiciousCar 对应 trackTask.syncSuspiciousCar("redis", emptyList)。
//
// JAVA 对照: syncSuspiciousCar 会把 Redis 结果无条件覆盖成入参列表；Java 任务传的是空列表，
// 因此该方法在 Java 里实际不写任何数据。这里保持同样的「无操作」语义。
func RunSyncSuspiciousCar(a *app.App) error {
	a.Log.Info("可疑车俩数据同步（入参为空，按 Java 语义不产生数据）")
	return nil
}

// RunChangeCarSuspicious 对应 trackTask.changeCarSuspicious（保留 30 天）。
func RunChangeCarSuspicious(a *app.App) error {
	queryStartTime := time.Now().AddDate(0, 0, -30).Format("2006-01-02") + " 00:00:00"
	err := a.DB.Exec(
		"insert into car_suspicious_back select * from car_suspicious t "+
			"where t.del_flag = '0' and t.in_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
		queryStartTime).Error
	if err != nil {
		return err
	}
	return a.DB.Exec(
		"delete from car_suspicious where in_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
		queryStartTime).Error
}

// RunSaveCarExcept 对应 trackTask.saveCarExcept（全量车牌回写重点车辆库）。
func RunSaveCarExcept(a *app.App) error {
	h := newHandler(a)
	ctx := context.Background()
	var carNos []string
	if err := a.DB.WithContext(ctx).Raw(
		"SELECT DISTINCT car_no FROM car_except_record WHERE del_flag = '0'").Scan(&carNos).Error; err != nil {
		return err
	}
	for _, carNo := range carNos {
		// 单个车牌失败不中断整批（任务型回写，与 Java 的 try/catch 语义一致），但要留痕。
		if err := h.saveCarExcept(ctx, carNo); err != nil {
			a.Log.Warn("回写车辆逃费金额失败", "carNo", carNo, "err", err)
		}
	}
	return nil
}

// loadCarListContext 是 getRedisCarList 的非 HTTP 版本。
func (h *handler) loadCarListContext(ctx context.Context) []*carInfo {
	var cached []*carInfo
	if h.app.Cache.Get(ctx, carListKey, &cached) {
		return cached
	}
	if err := h.refreshCarListContext(ctx); err != nil {
		return nil
	}
	h.app.Cache.Get(ctx, carListKey, &cached)
	return cached
}
