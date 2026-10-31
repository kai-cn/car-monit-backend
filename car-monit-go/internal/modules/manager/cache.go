// JAVA 对照: com.ruoyi.common.constant.Constants（manager 相关缓存键）
// JAVA 对照: CarWhiteInfoServiceImpl#updateRedisCarWhiteList / CarWarningRuleServiceImpl#cacheWarningRule
// 类/职责: manager 模块的 Redis 缓存读写
// 对应 Go 文件: internal/modules/manager/cache.go
//
// DIFF: Java 的 RedisCache 把对象序列化成 JSON；Go 的 cache.Set 同样以 JSON 存储。
package manager

import (
	"context"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

const (
	carListKey         = "car_list"
	carListJcKey       = "car_list_jc"
	whiteCarListKey    = "white_car_list"
	carWarningListKey  = "car_warning_list"
	carHistoryTrailKey = "car_history_trail:"
	carSuspiciousKey   = "car_uspicious"
	carWarningRuleKey  = "car_warning_rule:"
	cacheTTL           = 0 // Java RedisCache 未设置过期时间
)

// refreshWhiteList 对应 updateRedisCarWhiteList：空条件查全量后整份覆盖。
func (h *handler) refreshWhiteList(c *gin.Context) error {
	rows := newSliceOf(&carWhiteInfo{})
	clause, args := buildWhere(c, whiteInfoSpec.prefix(), nil)
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: whiteInfoSpec.selectSQL + whiteInfoSpec.selectSuffix,
		FromSQL:   whiteInfoSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   whiteInfoSpec.orderBy,
	}, rows); err != nil {
		return err
	}
	return h.app.Cache.Set(c.Request.Context(), whiteCarListKey, rows, time.Duration(cacheTTL))
}

// getRedisWhiteList 对应 getRedisCarWhiteList：命中直接返回，未命中回源并回写。
func (h *handler) getRedisWhiteList(c *gin.Context) []*carWhiteInfo {
	var cached []*carWhiteInfo
	if h.app.Cache.Get(c.Request.Context(), whiteCarListKey, &cached) {
		return cached
	}
	rows := newSliceOf(&carWhiteInfo{})
	clause, args := buildWhere(c, whiteInfoSpec.prefix(), nil)
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: whiteInfoSpec.selectSQL + whiteInfoSpec.selectSuffix,
		FromSQL:   whiteInfoSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   whiteInfoSpec.orderBy,
	}, rows); err != nil {
		return nil
	}
	out := *(rows.(*[]*carWhiteInfo))
	_ = h.app.Cache.Set(c.Request.Context(), whiteCarListKey, out, time.Duration(cacheTTL))
	return out
}

// cacheWarningRule 对应 cacheWarningRule()：先清空旧键，再按 (人员, 通知方式) 聚合预警范围。
func (h *handler) cacheWarningRule(c *gin.Context) error {
	ctx := c.Request.Context()
	for _, key := range h.app.Cache.Keys(ctx, carWarningRuleKey+"*") {
		h.app.Cache.Delete(ctx, key)
	}
	rows := newSliceOf(&carWarningRule{})
	clause, args := buildWhere(c, warningRuleSpec.prefix(), nil)
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: warningRuleSpec.selectSQL,
		FromSQL:   warningRuleSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   warningRuleSpec.orderBy,
	}, rows); err != nil {
		return err
	}
	for _, rule := range *(rows.(*[]*carWarningRule)) {
		if !isNotBlank(rule.NoticeUserID) || !isNotBlank(rule.NoticeRangeID) || !isNotBlank(rule.NoticeType) {
			continue
		}
		noticeType := isNull(rule.NoticeType)
		userIDs := strings.Split(deleteEnd(rule.NoticeUserID), ",")
		rangeIDs := strings.Split(deleteEnd(rule.NoticeRangeID), ",")
		for _, rawUserID := range userIDs {
			userID := isNull(rawUserID)
			if !isNotBlank(userID) || len(rangeIDs) <= 0 {
				continue
			}
			redisKey := carWarningRuleKey + userID + "type" + noticeType
			var existing []string
			h.app.Cache.Get(ctx, redisKey, &existing)
			for _, rangeID := range rangeIDs {
				existing = append(existing, isNull(rangeID))
			}
			_ = h.app.Cache.Set(ctx, redisKey, existing, time.Duration(cacheTTL))
		}
	}
	return nil
}

// successMsg 对应 AjaxResult.success(String msg)。
func successMsg(msg string) *web.AjaxResult { return web.SuccessMsg(msg) }
