// JAVA 对照: com.fasterxml.jackson.annotation.JsonFormat(pattern = "yyyy-MM-dd")
// 类/职责: 只输出日期的可空时间类型
// 对应 Go 文件: internal/modules/base/types.go
//
// DIFF: 基础库只有 web.DateTime（yyyy-MM-dd HH:mm:ss）。base 包的若干实体字段带
// @JsonFormat(pattern = "yyyy-MM-dd")，需要单独一个只输出日期的类型才能与 Jackson 对齐。
package base

import (
	"database/sql/driver"
	"fmt"
	"strconv"
	"strings"
	"time"

	"car-monit-go/internal/web"
)

const dateOnlyLayout = "2006-01-02"

// dateOnly 对应 Jackson 的 @JsonFormat(pattern = "yyyy-MM-dd")。
type dateOnly struct {
	time.Time
}

func (d dateOnly) MarshalJSON() ([]byte, error) {
	if d.IsZero() {
		return []byte("null"), nil
	}
	return []byte(`"` + d.Format(dateOnlyLayout) + `"`), nil
}

func (d *dateOnly) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), `"`)
	if s == "" || s == "null" {
		d.Time = time.Time{}
		return nil
	}
	// 数值形态：fastjson2/Jackson 默认把 java.util.Date 写成毫秒时间戳。
	if n, err := strconv.ParseInt(s, 10, 64); err == nil {
		d.Time = time.UnixMilli(n)
		return nil
	}
	t, err := web.ParseDate(s)
	if err != nil {
		return err
	}
	d.Time = t
	return nil
}

func (d dateOnly) Value() (driver.Value, error) {
	if d.IsZero() {
		return nil, nil
	}
	return d.Time, nil
}

func (d *dateOnly) Scan(v any) error {
	if v == nil {
		d.Time = time.Time{}
		return nil
	}
	switch x := v.(type) {
	case time.Time:
		d.Time = x
	case []byte:
		t, err := web.ParseDate(string(x))
		if err != nil {
			return err
		}
		d.Time = t
	case string:
		t, err := web.ParseDate(x)
		if err != nil {
			return err
		}
		d.Time = t
	default:
		return fmt.Errorf("不支持的日期类型 %T", v)
	}
	return nil
}

// String 便于导出与日志输出。
func (d dateOnly) String() string {
	if d.IsZero() {
		return ""
	}
	return d.Format(dateOnlyLayout)
}

// isoDateTime 对应 Java 里「没有 @JsonFormat 的 java.util.Date」：
// Jackson 默认按 ISO-8601 输出，带毫秒与本地时区偏移，例：2025-08-29T16:30:59.000+08:00。
type isoDateTime struct {
	time.Time
}

const isoDateTimeLayout = "2006-01-02T15:04:05.000-07:00"

func (d isoDateTime) MarshalJSON() ([]byte, error) {
	if d.IsZero() {
		return []byte("null"), nil
	}
	return []byte(`"` + d.Format(isoDateTimeLayout) + `"`), nil
}

func (d *isoDateTime) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), `"`)
	if s == "" || s == "null" {
		d.Time = time.Time{}
		return nil
	}
	// 数值形态：fastjson2/Jackson 默认把 java.util.Date 写成毫秒时间戳。
	if n, err := strconv.ParseInt(s, 10, 64); err == nil {
		d.Time = time.UnixMilli(n)
		return nil
	}
	t, err := web.ParseDate(s)
	if err != nil {
		return err
	}
	d.Time = t
	return nil
}

func (d isoDateTime) Value() (driver.Value, error) {
	if d.IsZero() {
		return nil, nil
	}
	return d.Time, nil
}

func (d *isoDateTime) Scan(v any) error {
	if v == nil {
		d.Time = time.Time{}
		return nil
	}
	switch x := v.(type) {
	case time.Time:
		d.Time = x
	case []byte:
		t, err := web.ParseDate(string(x))
		if err != nil {
			return err
		}
		d.Time = t
	case string:
		t, err := web.ParseDate(x)
		if err != nil {
			return err
		}
		d.Time = t
	default:
		return fmt.Errorf("不支持的日期类型 %T", v)
	}
	return nil
}

// String 便于导出与日志输出（导出用日期时间文本，与 ExcelUtil 的 dateFormat 对齐）。
func (d isoDateTime) String() string {
	if d.IsZero() {
		return ""
	}
	return d.Format("2006-01-02 15:04:05")
}
