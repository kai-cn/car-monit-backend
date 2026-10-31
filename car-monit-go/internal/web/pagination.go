// JAVA 对照: com/ruoyi/common/core/page/PageDomain.java
// JAVA 对照: com/ruoyi/common/core/page/TableSupport.java
// JAVA 对照: com/ruoyi/common/utils/PageUtils.java
// 类/职责: 分页参数 — 对应 PageHelper.startPage()
// 对应 Go 文件: internal/web/pagination.go
//
// DIFF: Java PageHelper 把分页参数放在 ThreadLocal，由 MyBatis 拦截器改写 SQL；
// Go 没有隐式拦截，handler 显式读取 PageDomain 并在 SQL 末尾追加 LIMIT/OFFSET，
// 同时执行 COUNT 查询得到 total（对应 PageInfo.getTotal()）。
package web

import (
	"regexp"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

const (
	DefaultPageNum  = 1
	DefaultPageSize = 10
	MaxPageSize     = 500
)

type PageDomain struct {
	PageNum       int
	PageSize      int
	OrderByColumn string
	IsAsc         string
	Reasonable    bool
	HasPage       bool
}

// Page 从请求参数读取分页信息，等价 TableSupport.buildPageRequest + PageUtils.startPage。
func Page(c *gin.Context) PageDomain {
	pd := PageDomain{IsAsc: "asc", Reasonable: true}
	pn := c.Query("pageNum")
	ps := c.Query("pageSize")
	if pn != "" && ps != "" {
		pd.PageNum, _ = strconv.Atoi(pn)
		pd.PageSize, _ = strconv.Atoi(ps)
		pd.HasPage = true
	}
	if pd.PageNum <= 0 {
		pd.PageNum = DefaultPageNum
	}
	if pd.PageSize <= 0 {
		pd.PageSize = DefaultPageSize
	}
	if pd.PageSize > MaxPageSize {
		pd.PageSize = MaxPageSize
	}
	pd.OrderByColumn = c.Query("orderByColumn")
	if v := c.Query("isAsc"); v != "" {
		switch v {
		case "ascending":
			pd.IsAsc = "asc"
		case "descending":
			pd.IsAsc = "desc"
		default:
			pd.IsAsc = v
		}
	}
	if v := c.Query("reasonable"); v != "" {
		pd.Reasonable = v == "true"
	}
	return pd
}

func (p PageDomain) Offset() int {
	if !p.HasPage {
		return 0
	}
	return (p.PageNum - 1) * p.PageSize
}

func (p PageDomain) Limit() int {
	if !p.HasPage {
		return 0
	}
	return p.PageSize
}

var orderByPattern = regexp.MustCompile(`^[a-zA-Z0-9_\ \,\.]+$`)

// OrderBy 对应 PageDomain.getOrderBy + SqlUtil.escapeOrderBySql。
// 返回空串表示不排序。非法列名会被忽略（Java 侧抛异常，此处保守降级并记录 DIFF）。
func (p PageDomain) OrderBy() string {
	if p.OrderByColumn == "" || !orderByPattern.MatchString(p.OrderByColumn) {
		return ""
	}
	col := toUnderScoreCase(p.OrderByColumn)
	dir := strings.ToLower(p.IsAsc)
	if dir != "desc" {
		dir = "asc"
	}
	return col + " " + dir
}

// OrderByWithDefault 在客户端未指定排序列时使用服务端默认排序。
func (p PageDomain) OrderByWithDefault(defaultOrder string) string {
	if o := p.OrderBy(); o != "" {
		return o
	}
	return defaultOrder
}

func toUnderScoreCase(s string) string {
	var b strings.Builder
	for i, r := range s {
		if r >= 'A' && r <= 'Z' {
			if i > 0 && s[i-1] != '_' {
				b.WriteByte('_')
			}
			b.WriteRune(r + ('a' - 'A'))
			continue
		}
		b.WriteRune(r)
	}
	return b.String()
}
