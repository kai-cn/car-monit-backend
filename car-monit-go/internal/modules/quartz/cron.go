// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/CronUtils.java:1-63
// 类/职责: Quartz cron 表达式解析 / 校验 / 下次执行时间计算
// 对应 Go 文件: internal/modules/quartz/cron.go
// 关键映射: org.quartz.CronExpression.isValidExpression -> IsValidCronExpression；
//
//	CronExpression.getNextValidTimeAfter -> cronSchedule.Next
//
// DIFF: 原计划使用 github.com/robfig/cron/v3，但 go.mod（并行协作方维护，本模块不得修改）中
// 并未声明该依赖，模块缓存中也不存在。为了不触碰 go.mod，这里按 Quartz 语义实现了一个
// 最小但完整的解析器：6/7 段、'?'、'*'、列表、区间、步长、月份/星期英文缩写、L/W/#。
// DIFF: 第 7 段（year）会被校验但不参与计算（Quartz 中 year 极少使用）。
// DIFF: Quartz 支持 "L-3W" 这类组合写法，这里只支持 L、L-n、nW、LW、nL、n#k，其余判为非法。
package quartz

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"
)

const (
	cronFieldSeconds = iota
	cronFieldMinutes
	cronFieldHours
	cronFieldDayOfMonth
	cronFieldMonth
	cronFieldDayOfWeek
	cronFieldYear
)

var cronMonthNames = map[string]int{
	"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
	"JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

// Quartz 中 1=SUN ... 7=SAT（与 Go 的 time.Sunday=0 不同，转换见 weekdayNumber）。
var cronDayNames = map[string]int{
	"SUN": 1, "MON": 2, "TUE": 3, "WED": 4, "THU": 5, "FRI": 6, "SAT": 7,
}

// cronFieldDef 描述单个字段的取值范围与可用名称。
type cronFieldDef struct {
	min, max int
	names    map[string]int
}

func cronFieldDefOf(idx int) cronFieldDef {
	switch idx {
	case cronFieldSeconds, cronFieldMinutes:
		return cronFieldDef{min: 0, max: 59}
	case cronFieldHours:
		return cronFieldDef{min: 0, max: 23}
	case cronFieldDayOfMonth:
		return cronFieldDef{min: 1, max: 31}
	case cronFieldMonth:
		return cronFieldDef{min: 1, max: 12, names: cronMonthNames}
	case cronFieldDayOfWeek:
		return cronFieldDef{min: 1, max: 7, names: cronDayNames}
	case cronFieldYear:
		return cronFieldDef{min: 1970, max: 2199}
	}
	return cronFieldDef{min: 0, max: 0}
}

// dayOfMonthSpec 对应 CronExpression 的 DayOfMonth 特殊语法。
type dayOfMonthSpec struct {
	any         bool // "*" 或 "?"
	set         []bool
	last        bool // "L" 或 "L-n"
	lastOffset  int
	lastWeekday bool // "LW"
	nearestDay  int  // "nW"，0 表示未设置
}

// dayOfWeekSpec 对应 CronExpression 的 DayOfWeek 特殊语法。
type dayOfWeekSpec struct {
	any  bool
	set  []bool
	last []bool      // "nL"
	nth  map[int]int // "n#k"
}

// cronSchedule 是解析后的 Quartz cron 表达式。
type cronSchedule struct {
	source  string
	loc     *time.Location
	seconds []bool
	minutes []bool
	hours   []bool
	months  []bool // 下标 1..12
	useDOM  bool
	dom     dayOfMonthSpec
	dow     dayOfWeekSpec
}

// IsValidCronExpression 对应 CronUtils.isValid(CronExpression.isValidExpression)。
func IsValidCronExpression(expr string) bool {
	_, err := ParseCronExpression(expr)
	return err == nil
}

// ValidateCronExpression 对应 CronUtils.getInvalidMessage 的非空分支：返回解析错误描述。
func ValidateCronExpression(expr string) error {
	_, err := ParseCronExpression(expr)
	return err
}

// ParseCronExpression 解析 Quartz cron 表达式（6 或 7 段）。
// JAVA 对照: CronUtils.java:32-43（new CronExpression(...) 的异常分支）
func ParseCronExpression(expr string) (*cronSchedule, error) {
	return parseCronExpression(expr, time.Local)
}

func parseCronExpression(expr string, loc *time.Location) (*cronSchedule, error) {
	expr = strings.TrimSpace(expr)
	if expr == "" {
		return nil, errors.New("cron 表达式不能为空")
	}
	if loc == nil {
		loc = time.Local
	}
	fields := strings.Fields(expr)
	if len(fields) != 6 && len(fields) != 7 {
		return nil, fmt.Errorf("cron 表达式必须由 6 或 7 段组成，实际 %d 段: %s", len(fields), expr)
	}

	s := &cronSchedule{source: expr, loc: loc}

	var err error
	if s.seconds, _, err = parseCronField(fields[cronFieldSeconds], cronFieldSeconds); err != nil {
		return nil, fmt.Errorf("秒字段非法: %w", err)
	}
	if s.minutes, _, err = parseCronField(fields[cronFieldMinutes], cronFieldMinutes); err != nil {
		return nil, fmt.Errorf("分字段非法: %w", err)
	}
	if s.hours, _, err = parseCronField(fields[cronFieldHours], cronFieldHours); err != nil {
		return nil, fmt.Errorf("时字段非法: %w", err)
	}
	if s.months, _, err = parseCronField(fields[cronFieldMonth], cronFieldMonth); err != nil {
		return nil, fmt.Errorf("月字段非法: %w", err)
	}

	domField := strings.ToUpper(strings.TrimSpace(fields[cronFieldDayOfMonth]))
	dowField := strings.ToUpper(strings.TrimSpace(fields[cronFieldDayOfWeek]))

	// JAVA 对照: CronExpression.buildExpression —— 日/周必须且只能有一个为 "?"。
	if domField == "?" && dowField == "?" {
		return nil, errors.New("日（月内第几天）与星期不能同时使用 '?'")
	}
	if domField != "?" && dowField != "?" {
		return nil, errors.New("日（月内第几天）与星期必须有一个使用 '?'，Quartz 不支持同时指定")
	}

	s.useDOM = dowField == "?"
	if s.useDOM {
		if s.dom, err = parseDayOfMonth(domField); err != nil {
			return nil, err
		}
	} else {
		if s.dow, err = parseDayOfWeek(dowField); err != nil {
			return nil, err
		}
	}

	// 第 7 段 year：只做语法校验，不参与计算（DIFF: Quartz 会用 year 限制年份范围）。
	if len(fields) == 7 {
		if _, _, err = parseCronField(fields[cronFieldYear], cronFieldYear); err != nil {
			return nil, fmt.Errorf("年字段非法: %w", err)
		}
	}
	return s, nil
}

// parseCronField 解析普通字段：*、a、a-b、a/n、a-b/n、列表。
// 返回的 set 下标即字段取值（月份/星期下标从 1 开始，0 号位置留空）。
func parseCronField(field string, defIdx int) ([]bool, bool, error) {
	def := cronFieldDefOf(defIdx)
	set := make([]bool, def.max+1)
	field = strings.ToUpper(strings.TrimSpace(field))
	if field == "" {
		return nil, false, errors.New("字段不能为空")
	}
	if field == "*" {
		for i := def.min; i <= def.max; i++ {
			set[i] = true
		}
		return set, true, nil
	}
	all := false
	for _, part := range strings.Split(field, ",") {
		part = strings.TrimSpace(part)
		if part == "" {
			return nil, false, fmt.Errorf("非法的表达式段: %s", field)
		}
		rangePart := part
		step := 1
		if idx := strings.IndexByte(part, '/'); idx >= 0 {
			rangePart = part[:idx]
			n, err := strconv.Atoi(part[idx+1:])
			if err != nil || n <= 0 {
				return nil, false, fmt.Errorf("步长非法: %s", part)
			}
			step = n
		}

		var lo, hi int
		switch {
		case rangePart == "*":
			lo, hi = def.min, def.max
			if step == 1 {
				all = true
			}
		case strings.Contains(rangePart, "-"):
			segs := strings.SplitN(rangePart, "-", 2)
			var err error
			if lo, err = def.value(segs[0]); err != nil {
				return nil, false, err
			}
			if hi, err = def.value(segs[1]); err != nil {
				return nil, false, err
			}
			if lo > hi {
				return nil, false, fmt.Errorf("区间起始值大于结束值: %s", part)
			}
		default:
			v, err := def.value(rangePart)
			if err != nil {
				return nil, false, err
			}
			lo = v
			hi = v
			if step > 1 {
				hi = def.max
			}
		}
		for v := lo; v <= hi; v += step {
			if v < 0 || v >= len(set) {
				return nil, false, fmt.Errorf("取值超出范围: %s", part)
			}
			set[v] = true
		}
	}
	return set, all, nil
}

func (d cronFieldDef) value(s string) (int, error) {
	s = strings.TrimSpace(s)
	if d.names != nil {
		if v, ok := d.names[strings.ToUpper(s)]; ok {
			return v, nil
		}
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0, fmt.Errorf("非法取值: %s", s)
	}
	if n < d.min || n > d.max {
		return 0, fmt.Errorf("取值 %d 超出范围 %d-%d", n, d.min, d.max)
	}
	return n, nil
}

func parseDayOfMonth(field string) (dayOfMonthSpec, error) {
	var d dayOfMonthSpec
	switch {
	case field == "*":
		d.any = true
		return d, nil
	case field == "LW":
		d.lastWeekday = true
		return d, nil
	case field == "L":
		d.last = true
		return d, nil
	case strings.HasPrefix(field, "L-"):
		n, err := strconv.Atoi(field[2:])
		if err != nil || n < 0 || n > 30 {
			return d, fmt.Errorf("非法的日字段: %s", field)
		}
		d.last = true
		d.lastOffset = n
		return d, nil
	case strings.HasSuffix(field, "W"):
		n, err := strconv.Atoi(field[:len(field)-1])
		if err != nil || n < 1 || n > 31 {
			return d, fmt.Errorf("非法的日字段: %s", field)
		}
		d.nearestDay = n
		return d, nil
	}
	set, _, err := parseCronField(field, cronFieldDayOfMonth)
	if err != nil {
		return d, fmt.Errorf("日字段非法: %w", err)
	}
	d.set = set
	return d, nil
}

func parseDayOfWeek(field string) (dayOfWeekSpec, error) {
	var d dayOfWeekSpec
	d.nth = map[int]int{}
	switch {
	case field == "*":
		d.any = true
		return d, nil
	case field == "?":
		d.any = true
		return d, nil
	case field == "L":
		// Quartz 中 DOW 的 "L" 等价于 SAT（7）。
		d.last = make([]bool, 8)
		d.last[7] = true
		return d, nil
	case strings.HasSuffix(field, "L"):
		wd, err := cronFieldDefOf(cronFieldDayOfWeek).value(field[:len(field)-1])
		if err != nil {
			return d, fmt.Errorf("星期字段非法: %w", err)
		}
		d.last = make([]bool, 8)
		d.last[wd] = true
		return d, nil
	case strings.Contains(field, "#"):
		segs := strings.SplitN(field, "#", 2)
		wd, err := cronFieldDefOf(cronFieldDayOfWeek).value(segs[0])
		if err != nil {
			return d, fmt.Errorf("星期字段非法: %w", err)
		}
		n, err := strconv.Atoi(segs[1])
		if err != nil || n < 1 || n > 5 {
			return d, fmt.Errorf("非法的星期字段: %s", field)
		}
		d.nth[wd] = n
		return d, nil
	}
	set, _, err := parseCronField(field, cronFieldDayOfWeek)
	if err != nil {
		return d, fmt.Errorf("星期字段非法: %w", err)
	}
	d.set = set
	return d, nil
}

// weekdayNumber 把 Go 的 Weekday 转成 Quartz 的 1(SUN)..7(SAT)。
func weekdayNumber(t time.Time) int {
	return int(t.Weekday()) + 1
}

func (s *cronSchedule) monthMatches(t time.Time) bool { return s.months[int(t.Month())] }

func (s *cronSchedule) dayMatches(t time.Time) bool {
	if s.useDOM {
		return domMatches(s.dom, t)
	}
	return dowMatches(s.dow, t)
}

func domMatches(d dayOfMonthSpec, t time.Time) bool {
	day := t.Day()
	if d.any {
		return true
	}
	last := daysInMonth(t)
	if d.last {
		return day == last-d.lastOffset
	}
	if d.lastWeekday {
		return day == lastWeekdayOfMonth(t)
	}
	if d.nearestDay > 0 {
		target := d.nearestDay
		if target > last {
			target = last
		}
		return day == nearestWeekday(t, target, last)
	}
	if d.set == nil {
		return true
	}
	if day < len(d.set) {
		return d.set[day]
	}
	return false
}

func dowMatches(d dayOfWeekSpec, t time.Time) bool {
	if d.any {
		return true
	}
	wd := weekdayNumber(t)
	if d.set != nil && wd < len(d.set) && d.set[wd] {
		return true
	}
	last := daysInMonth(t)
	if d.last != nil && wd < len(d.last) && d.last[wd] {
		return t.Day()+7 > last
	}
	if n, ok := d.nth[wd]; ok {
		return (t.Day()-1)/7+1 == n
	}
	return false
}

func daysInMonth(t time.Time) int {
	return time.Date(t.Year(), t.Month(), 1, 0, 0, 0, 0, t.Location()).AddDate(0, 1, -1).Day()
}

// nearestWeekday 对应 Quartz 的 "nW"：取离 n 最近的工作日，且不跨月。
func nearestWeekday(t time.Time, day, last int) int {
	loc := t.Location()
	offset := func(d int) int {
		switch time.Date(t.Year(), t.Month(), d, 12, 0, 0, 0, loc).Weekday() {
		case time.Saturday:
			if d == 1 {
				return d + 2
			}
			return d - 1
		case time.Sunday:
			if d == last {
				return d - 2
			}
			return d + 1
		}
		return d
	}
	return offset(day)
}

func lastWeekdayOfMonth(t time.Time) int {
	last := daysInMonth(t)
	loc := t.Location()
	for d := last; d >= last-2; d-- {
		if wd := time.Date(t.Year(), t.Month(), d, 12, 0, 0, 0, loc).Weekday(); wd != time.Saturday && wd != time.Sunday {
			return d
		}
	}
	return last
}

// Next 返回严格晚于 from 的下一个触发时间，对应 CronExpression.getNextValidTimeAfter。
func (s *cronSchedule) Next(from time.Time) (time.Time, bool) {
	loc := s.loc
	t := from.In(loc)
	// 对齐到整秒并前进 1 秒，保证返回严格大于 from。
	t = time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(), 0, loc).Add(time.Second)
	limit := from.AddDate(5, 0, 0)

	for t.Before(limit) {
		if !s.monthMatches(t) {
			t = time.Date(t.Year(), t.Month(), 1, 0, 0, 0, 0, loc).AddDate(0, 1, 0)
			continue
		}
		if !s.dayMatches(t) {
			t = time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, loc).AddDate(0, 0, 1)
			continue
		}
		if !s.hours[t.Hour()] {
			t = time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), 0, 0, 0, loc).Add(time.Hour)
			continue
		}
		if !s.minutes[t.Minute()] {
			t = time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), 0, 0, loc).Add(time.Minute)
			continue
		}
		if !s.seconds[t.Second()] {
			t = time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(), 0, loc).Add(time.Second)
			continue
		}
		return t, true
	}
	return time.Time{}, false
}

// NextValidTime 对应 SysJob.getNextValidTime()：空表达式返回 nil。
func NextValidTime(expr string) *time.Time {
	if strings.TrimSpace(expr) == "" {
		return nil
	}
	spec, err := ParseCronExpression(expr)
	if err != nil {
		return nil
	}
	next, ok := spec.Next(time.Now())
	if !ok {
		return nil
	}
	return &next
}
