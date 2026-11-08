// JAVA 对照: ruoyi-system/src/main/resources/mapper/base/*.xml 的 <if> 条件段
// 类/职责: 把 XML 里的动态条件声明为 Go 数据，供通用 CRUD 处理器使用
// 对应 Go 文件: internal/modules/base/query.go
//
// DIFF: MyBatis 按 OGNL 判空（String 判 null/”，Long/Date 判 null）；Spring 把空串绑定到
// 非 String 类型时得到 null，因此这里统一「String 参数为空即跳过 / 数值参数只看是否出现」。
package base

import (
	"reflect"
	"strings"

	"github.com/gin-gonic/gin"
)

type condKind int

const (
	// condEq 对应 <if test="x != null and x != ''"> and t.col = #{x}</if>
	condEq condKind = iota
	// condLike 对应 <if test="x != null and x != ''"> and t.col like concat('%',#{x},'%')</if>
	condLike
	// condNumber 对应 Long/Integer/BigDecimal/Date 的 <if test="x != null">（0 也生效）。
	condNumber
	// condNumberNonZero 对应 Long 字段却写成 x != null and x != '' 的 OGNL 边界（0 被跳过）。
	condNumberNonZero
	// condTemplate 对应自定义片段（{p} 为占位符）。
	condTemplate
	// condRaw 对应原样追加的片段（含片段自带的前导 and，不做 AND 拼接）。
	condRaw
	// condInList 对应 <foreach> 的 in 条件（空集合整条跳过）。
	condInList
)

type cond struct {
	param    string
	column   string
	kind     condKind
	template string
}

func eqCond(param, column string) cond   { return cond{param: param, column: column, kind: condEq} }
func likeCond(param, column string) cond { return cond{param: param, column: column, kind: condLike} }
func numCond(param, column string) cond {
	return cond{param: param, column: column, kind: condNumber}
}
func zeroSkipCond(param, column string) cond {
	return cond{param: param, column: column, kind: condNumberNonZero}
}
func tmplCond(param, template string) cond {
	return cond{param: param, kind: condTemplate, template: template}
}
func rawCond(param, fragment string) cond {
	return cond{param: param, kind: condRaw, template: fragment}
}

// 常用日期条件（照抄各 XML 的模板）。
func dateGe(param, column string) cond {
	return tmplCond(param, "t."+column+" >= STR_TO_DATE(?, '%Y-%m-%d')")
}
func dateLtNextDay(param, column string) cond {
	return tmplCond(param, "t."+column+" < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)")
}

// whereClause 对应 mapper XML 里那一串条件。
type whereClause struct {
	clause string
	args   []any
}

func (w *whereClause) SQL() string { return w.clause }
func (w *whereClause) Args() []any { return w.args }

// buildWhere 把 cond 列表翻译成 WHERE 片段（含固定前缀）。
//
// JAVA 对照: selectXxxList 的 WHERE 前缀有两种 —— 绝大多数是 "WHERE 1=1"，
// 只有 ZdataTrailFittingMapper 是 "WHERE t.del_flag = '0'"。
func buildWhere(c *gin.Context, prefix string, conds []cond) (string, []any) {
	return buildWhereWith(prefix, conds, func(name string) string { return c.Query(name) })
}

// buildWhereMap 是 buildWhere 的「已摊平参数」版本（分表查询用）。
func buildWhereMap(prefix string, conds []cond, params map[string]string) (string, []any) {
	return buildWhereWith(prefix, conds, func(name string) string { return params[name] })
}

func buildWhereWith(prefix string, conds []cond, get func(string) string) (string, []any) {
	clause := prefix
	args := make([]any, 0, len(conds))
	for _, item := range conds {
		value := strings.TrimSpace(get(item.param))
		switch item.kind {
		case condEq, condLike:
			if value == "" {
				continue
			}
			if item.kind == condEq {
				clause += " AND " + item.column + " = ?"
			} else {
				clause += " AND " + item.column + " LIKE CONCAT('%', ?, '%')"
			}
			args = append(args, value)
		case condNumber:
			if value == "" {
				continue
			}
			clause += " AND " + item.column + " = ?"
			args = append(args, value)
		case condNumberNonZero:
			// OGNL: 数字与 '' 比较等价于 != 0，故 0 被跳过。
			if value == "" || value == "0" {
				continue
			}
			clause += " AND " + item.column + " = ?"
			args = append(args, value)
		case condTemplate:
			if value == "" {
				continue
			}
			if idx := strings.Index(item.template, "{p}"); idx >= 0 {
				clause += " AND " + item.template[:idx] + "?" + item.template[idx+3:]
			} else {
				clause += " AND " + item.template
			}
			args = append(args, value)
		case condRaw:
			// 原样追加（XML 里这条片段自己带了 "and"，甚至带两个 —— 照抄）。
			if value == "" {
				continue
			}
			clause += " " + item.template
			args = append(args, value)
		case condInList:
			if value == "" {
				continue
			}
			values := splitCSV(value)
			if len(values) == 0 {
				continue
			}
			clause += " AND " + item.column + " IN (" + placeholders(len(values)) + ")"
			for _, v := range values {
				args = append(args, strings.TrimSpace(v))
			}
		}
	}
	return clause, args
}

// placeholders 生成 "?, ?, ?"。
func placeholders(n int) string {
	if n <= 0 {
		return ""
	}
	return strings.TrimSuffix(strings.Repeat("?,", n), ",")
}

// ---------------------------------------------------------------------------
// 反射工具
// ---------------------------------------------------------------------------

// newSliceOf 返回 *[]*T（T 为 prototype 的元素类型），供 GORM Scan 使用。
func newSliceOf(prototype any) any {
	t := reflect.TypeOf(prototype).Elem()
	return reflect.New(reflect.SliceOf(reflect.PointerTo(t))).Interface()
}

// newElemOf 返回 *T。
func newElemOf(prototype any) any {
	return reflect.New(reflect.TypeOf(prototype).Elem()).Interface()
}

// reflectTypeOf 取指针/切片指向的元素类型。
func reflectTypeOf(dest any) reflect.Type {
	t := reflect.TypeOf(dest)
	for t.Kind() == reflect.Ptr || t.Kind() == reflect.Slice {
		t = t.Elem()
	}
	return t
}

// structFields 建立 "json 名 -> 列名" 的索引（跳过没有 gorm column 标签的瞬态字段）。
// 匿名嵌入结构（entityBase）按提升字段展开。
func structFields(t reflect.Type) map[string]string {
	for t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	out := make(map[string]string)
	var walk func(rt reflect.Type)
	walk = func(rt reflect.Type) {
		for i := 0; i < rt.NumField(); i++ {
			field := rt.Field(i)
			if field.Anonymous && field.Type.Kind() == reflect.Struct {
				walk(field.Type)
				continue
			}
			name := strings.Split(field.Tag.Get("json"), ",")[0]
			column := field.Tag.Get("gorm")
			if name == "" || name == "-" {
				continue
			}
			if idx := strings.Index(column, "column:"); idx >= 0 {
				column = strings.TrimPrefix(column[idx+len("column:"):], ":")
				if sp := strings.Index(column, ";"); sp >= 0 {
					column = column[:sp]
				}
			} else {
				continue
			}
			if column == "" || column == "-" {
				continue
			}
			out[name] = column
		}
	}
	walk(t)
	return out
}

// pickColumns 把请求体 JSON 的键（驼峰）翻译成列名，未列入白名单的键直接丢弃。
//
// DIFF: MyBatis-Plus 的 updateById/insert 只写「非 null」属性；这里用「请求体里出现过」
// 代替「Java 侧非 null」，语义一致（未传 = 不改）。
func pickColumns(body map[string]any, allowed map[string]string) map[string]any {
	cols := make(map[string]any, len(body))
	for key, value := range body {
		column, ok := allowed[key]
		if !ok || value == nil {
			continue
		}
		cols[column] = value
	}
	return cols
}
