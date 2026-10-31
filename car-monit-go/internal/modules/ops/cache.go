// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/CacheController.java
// 类/职责: 缓存监控 — INFO / INFO commandstats / DBSIZE 组装成前端仪表盘数据
// 对应 Go 文件: internal/modules/ops/cache.go
//
// DIFF: Java 用 RedisCallback 拿裸连接，取到的是 INFO 的**原始文本**再塞进 Properties；
// go-redis 的 Info() 同样返回未解析的 bulk string，因此这里直接按行解析，形状与 Java 的
// 扁平 Properties（key -> String）一致。
// DIFF: Java 的 Properties 无序，Go 的 map[string]string 由 encoding/json 按键名排序输出；
// 键集合相同，前端按 key 取值不受影响。
// DIFF: commandStats 的 value 是 substringBetween("calls=", ",usec") 的结果，可能是 null；
// Java List<Map<String,String>> 里放 null，这里同样输出 null。
package ops

import (
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/web"
)

// commandStatsPrefix 对应 StringUtils.removeStart(key, "cmdstat_") 的前缀。
const commandStatsPrefix = "cmdstat_"

type cacheHandler struct {
	app *app.App
}

// infoPair 保留 INFO 文本里的键值顺序（commandStats 的饼图顺序依赖它）。
type infoPair struct {
	Key   string
	Value string
}

type commandStat struct {
	Name  string  `json:"name"`
	Value *string `json:"value"`
}

type cacheInfo struct {
	Info         map[string]string `json:"info"`
	DBSize       int64             `json:"dbSize"`
	CommandStats []commandStat     `json:"commandStats"`
}

// parseInfo 对应 Lettuce Connection#info() 的结果：跳过空行与 # 注释，按首个 ":" 切分。
//
// JAVA 对照: java.util.Properties.load —— 只跳前导空白与值的前导空白，行尾空白保留。
func parseInfo(text string) []infoPair {
	pairs := make([]infoPair, 0)
	for _, rawLine := range strings.Split(text, "\n") {
		line := strings.TrimLeft(rawLine, " \t\r\f\v")
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, "!") {
			continue
		}
		key, value, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		pairs = append(pairs, infoPair{Key: key, Value: strings.TrimLeft(value, " \t\r\f\v")})
	}
	return pairs
}

// substringBetween 对应 StringUtils.substringBetween(str, open, close)：找不到返回 nil。
func substringBetween(text, openToken, closeToken string) *string {
	start := strings.Index(text, openToken)
	if start < 0 {
		return nil
	}
	start += len(openToken)
	end := strings.Index(text[start:], closeToken)
	if end < 0 {
		return nil
	}
	value := text[start : start+end]
	return &value
}

// buildCommandStats 对应 CacheController 的 pieList 组装：name 去掉 cmdstat_ 前缀，
// value 取 "calls=" 与 ",usec" 之间的数字串（String，不是数字）。
func buildCommandStats(pairs []infoPair) []commandStat {
	out := make([]commandStat, 0, len(pairs))
	for _, pair := range pairs {
		name := strings.TrimPrefix(pair.Key, commandStatsPrefix)
		out = append(out, commandStat{
			Name:  name,
			Value: substringBetween(pair.Value, "calls=", ",usec"),
		})
	}
	return out
}

// GetInfo 对应 GET /monitor/cache。
func (h *cacheHandler) GetInfo(c *gin.Context) {
	ctx := c.Request.Context()
	infoText, err := h.app.Redis.Info(ctx).Result()
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	statsText, err := h.app.Redis.Info(ctx, "commandstats").Result()
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	dbSize, err := h.app.Redis.DBSize(ctx).Result()
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}

	info := make(map[string]string)
	for _, pair := range parseInfo(infoText) {
		info[pair.Key] = pair.Value
	}

	result := &cacheInfo{
		Info:         info,
		DBSize:       dbSize,
		CommandStats: buildCommandStats(parseInfo(statsText)),
	}
	web.JSON(c, web.SuccessData(result))
}

// newCacheRoutes 注册 /monitor/cache。
func newCacheRoutes(reg gin.IRouter, a *app.App) {
	h := &cacheHandler{app: a}
	g := reg.Group("/monitor/cache")
	g.GET("", middleware.Perm("monitor:cache:list"), h.GetInfo)
}
