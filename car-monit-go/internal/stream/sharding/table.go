// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingTableUtil.java:21-363
// 类/职责: 通用分表工具 —— 按月/日/季/年生成分表名、时间范围与周期边界
// 对应 Go 文件: internal/stream/sharding/table.go
//
// DIFF: Java 用 Calendar 推进周期；Go 用 time.AddDate。
// DIFF: 配置中的 table-prefix 可能已带尾部下划线（如 ods_rt_szdn_snapshot_flow_），
//
//	TableNameByDate 会避免重复添加下划线，保证与 ShardingSphere 实际表名一致。
package sharding

import (
	"fmt"
	"strings"
	"time"
)

// Strategy 对应 ShardingConfig.ShardingStrategy。
type Strategy string

const (
	Daily     Strategy = "DAILY"
	Monthly   Strategy = "MONTHLY"
	Quarterly Strategy = "QUARTERLY"
	Yearly    Strategy = "YEARLY"

	// DefaultTablePrefix 对应 ShardingTableUtil.DEFAULT_TABLE_PREFIX。
	DefaultTablePrefix = "ods_rt_szdn_snapshot_flow"
	// DefaultStrategy 对应 DEFAULT_STRATEGY。
	DefaultStrategy = Monthly
)

// TableNameByDate 对应 ShardingTableUtil.getTableNameByDate(String, Date, ShardingStrategy):58-61。
func TableNameByDate(prefix string, d time.Time, strategy Strategy) string {
	suffix := tableSuffix(d, strategy)
	if prefix == "" {
		return suffix
	}
	if strings.HasSuffix(prefix, "_") {
		return prefix + suffix
	}
	return prefix + "_" + suffix
}

// TableNameByDateDefault 对应 getTableNameByDate(Date):46-48。
func TableNameByDateDefault(d time.Time) string {
	return TableNameByDate(DefaultTablePrefix, d, DefaultStrategy)
}

// TableNameByDateStr 对应 getTableNameByDateStr:71-74；日期无法解析时返回空串。
func TableNameByDateStr(prefix, dateStr string, strategy Strategy) string {
	d, ok := ParseDate(dateStr)
	if !ok {
		return ""
	}
	return TableNameByDate(prefix, d, strategy)
}

// TableNamesByDateRange 对应 getTableNamesByDateRange:96-123；按周期推进并去重。
func TableNamesByDateRange(prefix, startDateStr, endDateStr string, strategy Strategy) []string {
	start, ok1 := ParseDate(startDateStr)
	end, ok2 := ParseDate(endDateStr)
	if !ok1 || !ok2 {
		return []string{}
	}
	return tableNamesBetween(prefix, start, end, strategy)
}

// TableNamesByDateRangeDefault 对应 getTableNamesByDateRange:83-85。
func TableNamesByDateRangeDefault(startDateStr, endDateStr string) []string {
	return TableNamesByDateRange(DefaultTablePrefix, startDateStr, endDateStr, DefaultStrategy)
}

// FutureTableNames 对应 getFutureTableNames:143-156。
func FutureTableNames(prefix string, periods int, strategy Strategy) []string {
	out := make([]string, 0, periods)
	seen := make(map[string]struct{}, periods)
	cur := time.Now()
	for i := 0; i < periods; i++ {
		name := TableNameByDate(prefix, cur, strategy)
		if _, ok := seen[name]; !ok {
			seen[name] = struct{}{}
			out = append(out, name)
		}
		cur = advance(cur, strategy)
	}
	return out
}

// FutureTableNamesDefault 对应 getFutureTableNames:131-133。
func FutureTableNamesDefault(periods int) []string {
	return FutureTableNames(DefaultTablePrefix, periods, DefaultStrategy)
}

// IsOverMonths 对应 isOverMonths:166-181。
func IsOverMonths(startDateStr, endDateStr string, months int) bool {
	start, ok1 := ParseDate(startDateStr)
	end, ok2 := ParseDate(endDateStr)
	if !ok1 || !ok2 {
		return false
	}
	return start.Before(end.AddDate(0, -months, 0))
}

// CurrentPeriodTable 对应 getCurrentPeriodTable:268-270。
func CurrentPeriodTable(prefix string, strategy Strategy) string {
	return TableNameByDate(prefix, time.Now(), strategy)
}

// PeriodStart 对应 getPeriodStart:279-318。
func PeriodStart(d time.Time, strategy Strategy) time.Time {
	y, m, _ := d.Date()
	loc := d.Location()
	switch strategy {
	case Daily:
		return time.Date(y, m, d.Day(), 0, 0, 0, 0, loc)
	case Monthly:
		return time.Date(y, m, 1, 0, 0, 0, 0, loc)
	case Quarterly:
		qm := time.Month((int(m)-1)/3*3 + 1)
		return time.Date(y, qm, 1, 0, 0, 0, 0, loc)
	case Yearly:
		return time.Date(y, time.January, 1, 0, 0, 0, 0, loc)
	default:
		return d
	}
}

// PeriodEnd 对应 getPeriodEnd:327-348（周期最后一毫秒）。
func PeriodEnd(d time.Time, strategy Strategy) time.Time {
	start := PeriodStart(d, strategy)
	var next time.Time
	switch strategy {
	case Daily:
		next = start.AddDate(0, 0, 1)
	case Monthly:
		next = start.AddDate(0, 1, 0)
	case Quarterly:
		next = start.AddDate(0, 3, 0)
	case Yearly:
		next = start.AddDate(1, 0, 0)
	default:
		next = start
	}
	return next.Add(-time.Millisecond)
}

// ParseDate 对应 parseDate:235-259：支持 yyyy-MM-dd HH:mm:ss、yyyy-MM-dd、yyyyMMdd。
func ParseDate(s string) (time.Time, bool) {
	s = strings.TrimSpace(s)
	if s == "" {
		return time.Time{}, false
	}
	var layouts []string
	switch {
	case len(s) >= 19:
		layouts = []string{"2006-01-02 15:04:05"}
	case len(s) == 10:
		layouts = []string{"2006-01-02"}
	case len(s) == 8:
		layouts = []string{"20060102"}
	default:
		return time.Time{}, false
	}
	for _, layout := range layouts {
		if d, err := time.ParseInLocation(layout, s, time.Local); err == nil {
			return d, true
		}
	}
	return time.Time{}, false
}

// FormatDate 对应 formatDate:353-355。
func FormatDate(d time.Time) string { return d.Format("2006-01-02 15:04:05") }

// FormatDateOnly 对应 formatDateOnly:360-362。
func FormatDateOnly(d time.Time) string { return d.Format("2006-01-02") }

func tableSuffix(d time.Time, strategy Strategy) string {
	y, m, day := d.Date()
	switch strategy {
	case Daily:
		return fmt.Sprintf("%04d%02d%02d", y, int(m), day)
	case Quarterly:
		return fmt.Sprintf("%04dQ%d", y, (int(m)-1)/3+1)
	case Yearly:
		return fmt.Sprintf("%04d", y)
	default:
		return fmt.Sprintf("%04d%02d", y, int(m))
	}
}

func advance(d time.Time, strategy Strategy) time.Time {
	switch strategy {
	case Daily:
		return d.AddDate(0, 0, 1)
	case Monthly:
		return d.AddDate(0, 1, 0)
	case Quarterly:
		return d.AddDate(0, 3, 0)
	case Yearly:
		return d.AddDate(1, 0, 0)
	default:
		return d
	}
}

func tableNamesBetween(prefix string, start, end time.Time, strategy Strategy) []string {
	out := make([]string, 0)
	seen := make(map[string]struct{})
	for !start.After(end) {
		name := TableNameByDate(prefix, start, strategy)
		if _, ok := seen[name]; !ok {
			seen[name] = struct{}{}
			out = append(out, name)
		}
		start = advance(start, strategy)
	}
	return out
}
