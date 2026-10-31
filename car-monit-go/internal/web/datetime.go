// JAVA 对照: com/ruoyi/common/core/domain/BaseEntity.java:27-36 (createTime/updateTime)
// 类/职责: 时间类型 — 对应 Jackson @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
// 对应 Go 文件: internal/web/datetime.go
//
// DIFF: Java 用 Date + Jackson 格式化；Go 的 time.Time 默认 RFC3339，
// 这里用 DateTime 自定义 JSON/DB 编解码，输出与前端约定一致的 "yyyy-MM-dd HH:mm:ss"。
package web

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

const dateTimeLayout = "2006-01-02 15:04:05"

type DateTime struct {
	time.Time
}

func NewDateTime(t time.Time) DateTime { return DateTime{Time: t} }

// Now 返回当前时间，对应 Java new Date()。
func Now() DateTime { return DateTime{Time: time.Now()} }

func (d DateTime) MarshalJSON() ([]byte, error) {
	if d.IsZero() {
		return []byte("null"), nil
	}
	return []byte(`"` + d.Format(dateTimeLayout) + `"`), nil
}

func (d *DateTime) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), `"`)
	if s == "" || s == "null" {
		d.Time = time.Time{}
		return nil
	}
	t, err := ParseDate(s)
	if err != nil {
		return err
	}
	d.Time = t
	return nil
}

func (d DateTime) Value() (driver.Value, error) {
	if d.IsZero() {
		return nil, nil
	}
	return d.Time, nil
}

func (d *DateTime) Scan(v any) error {
	if v == nil {
		d.Time = time.Time{}
		return nil
	}
	switch x := v.(type) {
	case time.Time:
		d.Time = x
	case []byte:
		t, err := ParseDate(string(x))
		if err != nil {
			return err
		}
		d.Time = t
	case string:
		t, err := ParseDate(x)
		if err != nil {
			return err
		}
		d.Time = t
	default:
		return fmt.Errorf("unsupported datetime type %T", v)
	}
	return nil
}

// ParseDate 兼容 Java DateUtils 支持的常见格式。
func ParseDate(s string) (time.Time, error) {
	s = strings.TrimSpace(s)
	layouts := []string{
		dateTimeLayout,
		"2006-01-02T15:04:05",
		"2006-01-02",
		"2006/01/02 15:04:05",
		"2006/01/02",
		time.RFC3339,
	}
	for _, layout := range layouts {
		if t, err := time.ParseInLocation(layout, s, time.Local); err == nil {
			return t, nil
		}
	}
	return time.Time{}, fmt.Errorf("无法解析日期: %s", s)
}

// FormatNow 返回当前时间的标准字符串。
func FormatNow() string { return time.Now().Format(dateTimeLayout) }

// ParseOptional 空串返回 nil，其余解析为 DateTime。
func ParseOptional(s string) *DateTime {
	if strings.TrimSpace(s) == "" {
		return nil
	}
	if t, err := ParseDate(s); err == nil {
		return &DateTime{Time: t}
	}
	return nil
}

// String 便于日志输出。
func (d DateTime) String() string {
	if d.IsZero() {
		return ""
	}
	return d.Format(dateTimeLayout)
}

var _ json.Marshaler = DateTime{}

// ISODateTime 对应 Java 里「没有 @JsonFormat 的 java.util.Date」：
// Jackson 默认按 ISO-8601 输出（毫秒 + 本地时区偏移），例：2024-05-17T14:15:52.000+08:00。
type ISODateTime struct {
	time.Time
}

const isoDateTimeLayout = "2006-01-02T15:04:05.000-07:00"

func (d ISODateTime) MarshalJSON() ([]byte, error) {
	if d.IsZero() {
		return []byte("null"), nil
	}
	return []byte(`"` + d.Format(isoDateTimeLayout) + `"`), nil
}

func (d *ISODateTime) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), `"`)
	if s == "" || s == "null" {
		d.Time = time.Time{}
		return nil
	}
	t, err := ParseDate(s)
	if err != nil {
		return err
	}
	d.Time = t
	return nil
}

func (d ISODateTime) Value() (driver.Value, error) {
	if d.IsZero() {
		return nil, nil
	}
	return d.Time, nil
}

func (d *ISODateTime) Scan(v any) error {
	if v == nil {
		d.Time = time.Time{}
		return nil
	}
	switch x := v.(type) {
	case time.Time:
		d.Time = x
	case []byte:
		t, err := ParseDate(string(x))
		if err != nil {
			return err
		}
		d.Time = t
	case string:
		t, err := ParseDate(x)
		if err != nil {
			return err
		}
		d.Time = t
	default:
		return fmt.Errorf("不支持的日期类型 %T", v)
	}
	return nil
}

func (d ISODateTime) String() string {
	if d.IsZero() {
		return ""
	}
	return d.Format(dateTimeLayout)
}

var _ json.Marshaler = ISODateTime{}
