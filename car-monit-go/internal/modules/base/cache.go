// JAVA 对照: com.ruoyi.common.constant.Constants（base 相关缓存键）
// JAVA 对照: ruoyi-quartz/.../VehicleMonitoringTask#syncSectionInfo（setCacheList）
// JAVA 对照: CarWarningConfigServiceImpl#cacheWarningConfig
// JAVA 对照: GeometryServiceImpl#updateRedisList
// 类/职责: base 模块的 Redis 缓存读写
// 对应 Go 文件: internal/modules/base/cache.go
//
// DIFF: Java 的 RedisCache 用 fastjson2 序列化成 JSON；Go 的 Cache.Set 同样以 JSON 存储。
// DIFF: section_list 在 Java 里是 Redis List（rightPushAll），这里用 LRange 逐条反序列化。
package base

import (
	"context"
	"encoding/json"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	sectionListKey          = "section_list"
	gantryListKey           = "gantry_list"
	gantryListDataKey       = "gantry_list_data:"
	carWarningConfigListKey = "car_warning_config_list"
	geometryCacheKey        = "lxbh_jdwd:"
	cacheTTL                = 0 // Java RedisCache 未设置过期时间
)

// loadSectionList 对应 redisCache.getCacheList(Constants.SECTION_LIST)。
//
// DIFF: Java 在缓存为空时直接得到空列表（路段名称留空）；这里在缓存缺失时回源查库，
// 保证 /base/gantry/list、/base/toll/list 的 roadName/sectionName 可用。
func (h *handler) loadSectionList(ctx context.Context) []*odsSzdnSection {
	if h.app.Redis != nil {
		values, err := h.app.Redis.LRange(ctx, sectionListKey, 0, -1).Result()
		if err == nil && len(values) > 0 {
			out := make([]*odsSzdnSection, 0, len(values))
			for _, raw := range values {
				var row odsSzdnSection
				if json.Unmarshal([]byte(raw), &row) == nil {
					out = append(out, &row)
				}
			}
			if len(out) > 0 {
				return out
			}
		}
	}
	rows := newSliceOf(&odsSzdnSection{})
	if _, err := h.list(ctx, listQuery{
		SelectSQL: sectionSpec.selectSQL,
		FromSQL:   "FROM " + sectionSpec.from() + " ",
		Where:     &whereClause{clause: "WHERE 1=1"},
		OrderBy:   sectionSpec.orderBy,
	}, rows); err != nil {
		return nil
	}
	return *(rows.(*[]*odsSzdnSection))
}

// roadNameMap 对应 sectionList.stream().collect(toMap(getRoadCode, getRoadName, (k1,k2)->k1))。
func roadNameMap(list []*odsSzdnSection) map[string]string {
	m := make(map[string]string, len(list))
	for _, row := range list {
		key := strOf(row.RoadCode)
		if _, ok := m[key]; !ok {
			m[key] = strOf(row.RoadName)
		}
	}
	return m
}

// sectionNameMap 对应 sectionList.stream().collect(toMap(getSectionCode, getSectionName, ...))。
func sectionNameMap(list []*odsSzdnSection) map[string]string {
	m := make(map[string]string, len(list))
	for _, row := range list {
		key := strOf(row.SectionCode)
		if _, ok := m[key]; !ok {
			m[key] = strOf(row.SectionName)
		}
	}
	return m
}

// loadGantryCache 对应 redisCache.getCacheObject(Constants.gantry_list)。
//
// DIFF: Java 侧这个键在整个仓库里没有任何写入点（导出因此恒为空）；
// 这里缓存缺失时回源查库，让 /base/gantry/export 可用。
func (h *handler) loadGantryCache(ctx context.Context) []*odsSzdnGantry {
	var cached []*odsSzdnGantry
	if h.app.Cache.Get(ctx, gantryListKey, &cached) && len(cached) > 0 {
		return cached
	}
	rows := newSliceOf(&odsSzdnGantry{})
	if _, err := h.list(ctx, listQuery{
		SelectSQL: gantrySpec.selectSQL,
		FromSQL:   "FROM " + gantrySpec.from() + " ",
		Where:     &whereClause{clause: "WHERE 1=1"},
		OrderBy:   gantrySpec.orderBy,
	}, rows); err != nil {
		return nil
	}
	return *(rows.(*[]*odsSzdnGantry))
}

// gantryDataFlag 对应 redisCache.getCacheObject(Constants.gantry_list_data + gantryCode) > 0。
func (h *handler) gantryDataFlag(ctx context.Context, gantryCode string) bool {
	if h.app.Redis == nil {
		return false
	}
	raw, err := h.app.Redis.Get(ctx, gantryListDataKey+isNull(gantryCode)).Result()
	if err != nil {
		return false
	}
	n, err := parseInt64(raw)
	if err != nil {
		return false
	}
	return n > 0
}

// refreshWarningConfigCache 对应 CarWarningConfigServiceImpl#cacheWarningConfig：
// 无条件查全量后整份覆盖 car_warning_config_list。
func refreshWarningConfigCache(h *handler, c *gin.Context) {
	ctx := c.Request.Context()
	rows := newSliceOf(&carWarningConfig{})
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: carWarningConfigSpec.selectSQL,
		FromSQL:   "FROM " + carWarningConfigSpec.from() + " ",
		Where:     &whereClause{clause: "WHERE 1=1"},
	}, rows); err != nil {
		h.app.Log.Warn("刷新服务区判定规则缓存失败", "err", err)
		return
	}
	if err := h.app.Cache.Set(ctx, carWarningConfigListKey, rows, time.Duration(cacheTTL)); err != nil {
		h.app.Log.Warn("写入服务区判定规则缓存失败", "err", err)
	}
}

// refreshGeometryCache 对应 GeometryServiceImpl#updateRedisList：
// 取 lxfx='1' 且 lxbh/paths 非空的行，整份覆盖 lxbh_jdwd:。
func refreshGeometryCache(h *handler, c *gin.Context) {
	ctx := c.Request.Context()
	rows := newSliceOf(&geometry{})
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: geometrySpec.selectSQL,
		FromSQL:   "FROM " + geometrySpec.from() + " ",
		Where:     &whereClause{clause: "WHERE 1=1 AND t.lxfx = ?", args: []any{"1"}},
		OrderBy:   geometrySpec.orderBy,
	}, rows); err != nil {
		h.app.Log.Warn("刷新路线经纬度缓存失败", "err", err)
		return
	}
	out := make([]*geometry, 0, len(*(rows.(*[]*geometry))))
	for _, row := range *(rows.(*[]*geometry)) {
		if isNotBlank(row.Lxbh) && isNotBlank(row.Paths) {
			out = append(out, row)
		}
	}
	if err := h.app.Cache.Set(ctx, geometryCacheKey, out, time.Duration(cacheTTL)); err != nil {
		h.app.Log.Warn("写入路线经纬度缓存失败", "err", err)
	}
}
