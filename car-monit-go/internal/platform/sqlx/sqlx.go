// 类/职责: 数据库访问的公共小工具 —— 占位符、IN 参数、软删除条件
// 对应 Go 文件: internal/platform/sqlx/sqlx.go
//
// DIFF: Java 由 MyBatis 的 <foreach>/@Param 生成 in (?,?,?)；Go 侧各模块原先各写一份，
// 现收敛到本包，避免占位符行为在 6 个模块间漂移。
package sqlx

import "strings"

// Placeholders 生成 n 个逗号分隔的占位符（n<=0 返回空串）。
// 例：Placeholders(3) == "?,?,?"
func Placeholders(n int) string {
	if n <= 0 {
		return ""
	}
	return strings.TrimSuffix(strings.Repeat("?,", n), ",")
}

// SpacePlaceholders 生成带空格的占位符（"?, ?, ?"），部分既有 SQL 使用该形态。
func SpacePlaceholders(n int) string {
	if n <= 0 {
		return ""
	}
	return strings.TrimSuffix(strings.Repeat("?, ", n), " ")
}

// AnySlice 把 []string 转成 []any，供 database/sql 的可变参数展开。
func AnySlice(values []string) []any {
	out := make([]any, len(values))
	for i, v := range values {
		out[i] = v
	}
	return out
}

// Int64Slice 把 []int64 转成 []any。
func Int64Slice(values []int64) []any {
	out := make([]any, len(values))
	for i, v := range values {
		out[i] = v
	}
	return out
}
