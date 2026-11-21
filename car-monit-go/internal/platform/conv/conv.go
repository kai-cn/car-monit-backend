// 类/职责: 跨模块共用的 Java 语义工具 —— 可空字符串指针、String.valueOf、trim、CSV split
// 对应 Go 文件: internal/platform/conv/conv.go
//
// DIFF: Java 的 CommonUtil / StringUtils 是全局静态工具；Go 各业务模块原先各写一份
// strPtr/isNull/splitCSV，语义逐渐漂移（有的 trim、有的不 trim，有的只接受 *string）。
// 这里收敛为唯一实现，各模块只保留同签名的薄包装，调用点不变。
package conv

import (
	"fmt"
	"strings"
)

// Str 返回字符串指针，对应给 *string 字段赋值。
func Str(v string) *string { return &v }

// Int64 返回 int64 指针。
func Int64(v int64) *int64 { return &v }

// Int 返回 int 指针。
func Int(v int) *int { return &v }

// Float64 返回 float64 指针。
func Float64(v float64) *float64 { return &v }

// Bool 返回 bool 指针。
func Bool(v bool) *bool { return &v }

// Value 对应 Java 的 String.valueOf 在实体取值场景的语义：nil / nil 指针 -> ""，
// 其余按原值输出。**不做 trim**（CommonUtil.toString 本身也不 trim）。
func Value(v any) string {
	switch x := v.(type) {
	case nil:
		return ""
	case string:
		return x
	case *string:
		if x == nil {
			return ""
		}
		return *x
	case []byte:
		return string(x)
	case *int:
		if x == nil {
			return ""
		}
		return fmt.Sprint(*x)
	case *int64:
		if x == nil {
			return ""
		}
		return fmt.Sprint(*x)
	case *float64:
		if x == nil {
			return ""
		}
		return fmt.Sprint(*x)
	case *bool:
		if x == nil {
			return ""
		}
		return fmt.Sprint(*x)
	default:
		return fmt.Sprint(v)
	}
}

// Null 对应 CommonUtil.isNull：null -> ""，否则 toString().trim()。
func Null(v any) string { return strings.TrimSpace(Value(v)) }

// NotBlank 对应 CommonUtil.isNotBlank / StringUtils.isNotBlank。
func NotBlank(v any) bool { return Null(v) != "" }

// Blank 对应 CommonUtil.isBlank / StringUtils.isBlank。
func Blank(v any) bool { return Null(v) == "" }

// SplitCSV 对应 Java 的 String.split(",")：丢弃结果中的尾部空串。
//
// Java 的 split 用正则且默认 limit=0，Go 的 strings.Split 保留空串；
// 这里手工裁剪，保证 "a," -> ["a"]、"a,,b" -> ["a","","b"] 与 Java 一致。
func SplitCSV(s string) []string {
	parts := strings.Split(s, ",")
	for len(parts) > 0 && parts[len(parts)-1] == "" {
		parts = parts[:len(parts)-1]
	}
	return parts
}
