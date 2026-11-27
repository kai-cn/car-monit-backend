// JAVA 对照: ruoyi-system/src/main/resources/mapper/manager/*.xml 的 <if> 条件段
// 类/职责: 把 manager XML 里的动态条件声明为 Go 数据，供通用 CRUD 处理器使用
// 对应 Go 文件: internal/modules/manager/query.go
//
// DIFF: MyBatis 按 OGNL 判空（String 判 null/”，Long/Date 判 null）；Spring 把空串绑定到
// 非 String 类型时得到 null，因此这里统一「参数为空即跳过」，与 XML 等价。
package manager

import (
	"fmt"
	"reflect"
	"strings"

	"github.com/gin-gonic/gin"
)

type condKind int

const (
	condEq condKind = iota
	condLike
	// condNullable 对应 Long/BigDecimal/Date 的 <if test="x != null">
	condNullable
	// condTemplate 对应带自定义 SQL 片段的 <if>，片段里用 {p} 表示占位符。
	condTemplate
	// condFindInSet 对应 find_in_set(t.id, #{x}) > 0
	condFindInSet
)

type cond struct {
	param    string
	column   string
	kind     condKind
	template string
}

func eqCond(param, column string) cond   { return cond{param: param, column: column, kind: condEq} }
func likeCond(param, column string) cond { return cond{param: param, column: column, kind: condLike} }
func nullCond(param, column string) cond {
	return cond{param: param, column: column, kind: condNullable}
}
func tmplCond(param, template string) cond {
	return cond{param: param, kind: condTemplate, template: template}
}
func inSetCond(param string) cond { return cond{param: param, kind: condFindInSet} }

// 常用日期条件（照抄各 XML 的模板）。
func dateGe(param, column string) cond {
	return tmplCond(param, "t."+column+" >= STR_TO_DATE(?, '%Y-%m-%d')")
}
func dateLtNextDay(param, column string) cond {
	return tmplCond(param, "t."+column+" < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)")
}
func dateTimeGe(param, column string) cond {
	return tmplCond(param, "t."+column+" >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')")
}
func dateTimeLe(param, column string) cond {
	return tmplCond(param, "t."+column+" <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')")
}

// buildWhere 把 cond 列表翻译成 WHERE 片段（含固定前缀）。
func buildWhere(c *gin.Context, prefix string, conds []cond) (string, []any) {
	clause := prefix
	args := make([]any, 0, len(conds))
	for _, item := range conds {
		value := queryParam(c, item.param)
		if value == "" {
			continue
		}
		switch item.kind {
		case condEq:
			clause += " AND " + item.column + " = ?"
		case condLike:
			clause += " AND " + item.column + " LIKE CONCAT('%', ?, '%')"
		case condNullable:
			clause += " AND " + item.column + " = ?"
		case condFindInSet:
			clause += " AND find_in_set(t.id, ?) > 0"
		case condTemplate:
			clause += " AND " + item.template
		}
		args = append(args, value)
	}
	return clause, args
}

// argString 读取查询参数（含覆盖表，已 trim）。
func argString(c *gin.Context, name string) string { return queryParam(c, name) }

// newSliceOf 返回 *[]*T（T 为 prototype 的元素类型），供 GORM Scan 使用。
func newSliceOf(prototype any) any {
	t := reflect.TypeOf(prototype).Elem()
	return reflect.New(reflect.SliceOf(reflect.PointerTo(t))).Interface()
}

// newElemOf 返回 *T。
func newElemOf(prototype any) any {
	return reflect.New(reflect.TypeOf(prototype).Elem()).Interface()
}

// jsonTagIndex 建立 "json 名 -> 字段访问路径" 的索引（用于导出取值）。
// 匿名嵌入结构（entityBase）按提升字段展开。
func jsonTagIndex(t reflect.Type) map[string][]int {
	for t.Kind() == reflect.Pointer {
		t = t.Elem()
	}
	index := make(map[string][]int, t.NumField())
	var walk func(rt reflect.Type, prefix []int)
	walk = func(rt reflect.Type, prefix []int) {
		for i := 0; i < rt.NumField(); i++ {
			field := rt.Field(i)
			path := append(append([]int{}, prefix...), i)
			if field.Anonymous && field.Type.Kind() == reflect.Struct {
				walk(field.Type, path)
				continue
			}
			tag := field.Tag.Get("json")
			name := strings.Split(tag, ",")[0]
			if name == "" || name == "-" {
				continue
			}
			index[name] = path
		}
	}
	walk(t, nil)
	return index
}

// fieldValue 读取结构体（或指针）上 json 名为 key 的字段值。
func fieldValue(row reflect.Value, index map[string][]int, key string) any {
	path, ok := index[key]
	if !ok {
		return nil
	}
	v := row
	for _, i := range path {
		for v.Kind() == reflect.Pointer {
			if v.IsNil() {
				return nil
			}
			v = v.Elem()
		}
		if v.Kind() != reflect.Struct || i >= v.NumField() {
			return nil
		}
		v = v.Field(i)
	}
	return v.Interface()
}

// reflectTypeOf 取指针/切片指向的元素类型。
func reflectTypeOf(dest any) reflect.Type {
	t := reflect.TypeOf(dest)
	for t.Kind() == reflect.Pointer || t.Kind() == reflect.Slice {
		t = t.Elem()
	}
	return t
}

// forEachElement 遍历 *[]T 的每个元素（导出用）。
func forEachElement(dest any, fn func(any)) error {
	v := reflect.ValueOf(dest)
	if v.Kind() != reflect.Pointer || v.IsNil() || v.Elem().Kind() != reflect.Slice {
		return fmt.Errorf("dest 不是切片指针")
	}
	slice := v.Elem()
	for i := 0; i < slice.Len(); i++ {
		fn(slice.Index(i).Interface())
	}
	return nil
}

// fieldValueAny 是 fieldValue 的 any 入参版本。
func fieldValueAny(row any, index map[string][]int, key string) any {
	return fieldValue(reflect.ValueOf(row), index, key)
}
