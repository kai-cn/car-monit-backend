// JAVA 对照: com/ruoyi/common/core/controller/BaseController.java:75-95 (startPage/getDataTable)
// JAVA 对照: com/ruoyi/common/core/page/PageDomain.java
// JAVA 对照: com/ruoyi/common/core/domain/BaseEntity.java:14-20 (params map)
// 类/职责: 查询参数绑定 + 分页 SQL 执行 — 对应 Spring 的 ServletModelAttributeMethodProcessor
//
//	（形参没有 @RequestBody 时把 query string 绑到实体）+ PageHelper.startPage
//
// 对应 Go 文件: internal/modules/ops/params.go
//
// DIFF: Java 由 Spring DataBinder 把 query 参数反射写入实体字段，PageHelper 用 ThreadLocal
// 拦截下一条 SQL 追加 LIMIT；Go 侧没有隐式绑定，这里逐字段显式读取，并在查询函数里
// 显式执行 COUNT + LIMIT/OFFSET（与 web.Page 的约定一致）。
// DIFF: `params[beginTime]` 这类嵌套 map 参数取自 query string 字面量（RuoYi 前端即如此发送），
// Java 由 BeanWrapper 按 `params[beginTime]` 属性路径写入 BaseEntity.params。
package ops

import (
	"context"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/platform/sqlx"
	"car-monit-go/internal/web"
)

// typeMismatch 对应 GlobalExceptionHandler.handleMethodArgumentTypeMismatchException 的文案。
// JAVA 对照: ruoyi-framework/.../web/exception/GlobalExceptionHandler.java:78-84
func typeMismatch(name, javaType, value string) *web.ServiceError {
	return web.NewServiceError("请求参数类型不匹配，参数[%s]要求类型为：'%s'，但输入值为：'%s'", name, javaType, value)
}

// intPtr 对应形参里的 Integer 属性（缺省/空串 -> null，非法数字 -> 类型不匹配异常）。
// Spring 的 TypeConverterDelegate 会把 String 空串转成 null（requiredType != String）。
func intPtr(c *gin.Context, name, javaType string) (*int, error) {
	raw, ok := c.GetQuery(name)
	if !ok || strings.TrimSpace(raw) == "" {
		return nil, nil
	}
	n, err := strconv.Atoi(strings.TrimSpace(raw))
	if err != nil {
		return nil, typeMismatch(name, javaType, raw)
	}
	return &n, nil
}

// intArray 对应形参里的 Integer[] 属性（重复参数 businessTypes=0&businessTypes=1）。
//
// DIFF: Java 的 StringToArrayConverter 逐元素转 Integer，"0,1" 会 NumberFormatException；
// 这里额外容忍逗号分隔（与 Python 版一致），只在错误路径上与 Java 不同。
func intArray(c *gin.Context, name, javaType string) ([]int, error) {
	values, ok := c.GetQueryArray(name)
	if !ok || len(values) == 0 {
		return nil, nil
	}
	var out []int
	for _, v := range values {
		for _, part := range strings.Split(v, ",") {
			part = strings.TrimSpace(part)
			if part == "" {
				continue
			}
			n, err := strconv.Atoi(part)
			if err != nil {
				return nil, typeMismatch(name, javaType, v)
			}
			out = append(out, n)
		}
	}
	return out, nil
}

// timeParam 读取 `params[beginTime]` / `params[endTime]`（BaseEntity.params 的键）。
func timeParam(c *gin.Context, name string) string {
	return c.Query("params[" + name + "]")
}

// parsePathIDs 对应 `@PathVariable Long[] operIds`：Spring 按逗号切分路径变量。
func parsePathIDs(raw, name string) ([]int64, error) {
	parts := strings.Split(raw, ",")
	ids := make([]int64, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			return nil, typeMismatch(name, "java.lang.Long", raw)
		}
		id, err := strconv.ParseInt(part, 10, 64)
		if err != nil {
			return nil, typeMismatch(name, "java.lang.Long", part)
		}
		ids = append(ids, id)
	}
	return ids, nil
}

// springBool 对应 Spring 的 StringToBooleanConverter：true/on/yes/1 与 false/off/no/0。
// present 为 false 表示请求里没有该参数 —— 返回 nil（Java 侧是 null，`if (delete)` 会 NPE）。
func springBool(raw string, present bool) (*bool, error) {
	if !present {
		return nil, nil
	}
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case "true", "on", "yes", "1":
		v := true
		return &v, nil
	case "false", "off", "no", "0":
		v := false
		return &v, nil
	}
	return nil, typeMismatch("delete", "java.lang.Boolean", raw)
}

// orderFor 对应 PageHelper：客户端给了 orderByColumn 就覆盖语句自带的排序
// （startPage(pageNum, pageSize, orderBy) 的 orderBy 会替换 XML 里的 order by）。
func orderFor(defaultOrder string, pd web.PageDomain) string {
	if o := pd.OrderBy(); o != "" {
		return "order by " + o
	}
	return defaultOrder
}

// queryPage 等价于 PageHelper.startPage(...) + PageInfo.getTotal():
//   - 不分页时（pageNum/pageSize 缺任一）直接返回全部行，total = 行数；
//   - 分页时先 `select count(0) from (原语句) table_count`，再追加 limit/offset。
//
// DIFF: PageHelper 的 count 语句会去掉 ORDER BY（count 优化），这里同样只对 count 语句
// 使用不含排序的 baseSQL；count=0 时同样跳过数据查询（web.PageDomain.SkipQuery）。
func queryPage[T any](ctx context.Context, db *gorm.DB, baseSQL string, args []any, orderBy string, pd web.PageDomain) ([]T, int64, error) {
	if err := pd.StartPageError(); err != nil {
		return nil, 0, err
	}
	dataSQL := baseSQL
	if strings.TrimSpace(orderBy) != "" {
		dataSQL += " " + orderBy
	}
	if !pd.HasPage {
		var rows []T
		if err := db.WithContext(ctx).Raw(dataSQL, args...).Scan(&rows).Error; err != nil {
			return nil, 0, err
		}
		if rows == nil {
			rows = make([]T, 0)
		}
		return rows, int64(len(rows)), nil
	}

	countSQL := "select count(0) from (" + baseSQL + ") table_count"
	var total int64
	if err := db.WithContext(ctx).Raw(countSQL, args...).Scan(&total).Error; err != nil {
		return nil, 0, err
	}

	if pd.SkipQuery(total) {
		return make([]T, 0), total, nil
	}

	var rows []T
	pageArgs := make([]any, 0, len(args)+2)
	pageArgs = append(pageArgs, args...)
	lim, off := pd.LimitOffset(total)
	pageArgs = append(pageArgs, lim, off)
	if err := db.WithContext(ctx).Raw(dataSQL+" limit ? offset ?", pageArgs...).Scan(&rows).Error; err != nil {
		return nil, 0, err
	}
	if rows == nil {
		rows = make([]T, 0)
	}
	return rows, total, nil
}

// inPlaceholders 生成 `?, ?, ?` 形式的占位符，替代 MyBatis 的 <foreach>。
func inPlaceholders(n int) string { return sqlx.SpacePlaceholders(n) }
