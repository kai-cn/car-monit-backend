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
//
// 取值规则照抄 Java：`Convert.toInt(参数, 默认)` —— 只有「没传 / 传了但解析不出数字」才回落默认值，
// 显式的 0 与负数是合法入参，PageHelper 会照用（实测 pageSize=0 与 pageSize=-1 都返回 0 行，
// 而 total 仍按真实条数给）。
// DIFF: 不设 pageSize 上限（Java 也没有，原来 Go 的 500 上限会让大页请求少返回数据）。
func Page(c *gin.Context) PageDomain {
	pd := PageDomain{IsAsc: "asc", Reasonable: true}
	pn, ps := c.Query("pageNum"), c.Query("pageSize")
	pd.PageNum = paramInt(pn, DefaultPageNum)
	pd.PageSize = paramInt(ps, DefaultPageSize)
	if pd.PageSize < 0 {
		pd.PageSize = 0
	}
	if pn != "" && ps != "" {
		pd.HasPage = true
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

func paramInt(raw string, def int) int {
	if raw == "" {
		return def
	}
	v, err := strconv.Atoi(raw)
	if err != nil {
		return def
	}
	return v
}

// PageAlways 对应 Java 里无条件调用 startPage() 的端点：
// TableSupport.getPageDomain 对缺省参数取 pageNum=1、pageSize=10，
// 因此请求里不带分页参数时同样只返回一页（Go 只用 Page() 会退化成「不分页」）。
func PageAlways(c *gin.Context) PageDomain {
	pd := Page(c)
	pd.HasPage = true
	return pd
}

// Clamp 对应 PageHelper 的 reasonable：页码小于 1 回到第一页，超过总页数回到最后一页。
// reasonable=false 时不钳（此时越界页返回空，与 Java 一致）。
func (p PageDomain) Clamp(total int64) PageDomain {
	if !p.HasPage {
		return p
	}
	if p.PageNum < 1 {
		p.PageNum = 1
	}
	if !p.Reasonable || p.PageSize <= 0 || total <= 0 {
		return p
	}
	last := int((total + int64(p.PageSize) - 1) / int64(p.PageSize))
	if p.PageNum > last {
		p.PageNum = last
	}
	return p
}

// SkipQuery 对应 PageHelper 的空结果短路：count=0 时拦截器不再执行分页查询。
//
// DIFF: 因此 Java 在「总数为 0 + 非法排序列」时根本不解析 ORDER BY，不会报错；
// Go 若照常执行就会把 SQL 错误暴露出来。所有分页查询都先问这一句。
func (p PageDomain) SkipQuery(total int64) bool {
	return p.HasPage && total == 0
}

// LimitOffset 是调用方该用的入口：先按总条数做 reasonable 钳位再算 LIMIT/OFFSET。
func (p PageDomain) LimitOffset(total int64) (int, int) {
	c := p.Clamp(total)
	return c.Limit(), c.Offset()
}

func (p PageDomain) Offset() int {
	if !p.HasPage {
		return 0
	}
	page := p.PageNum
	if page < 1 {
		page = 1
	}
	return (page - 1) * p.PageSize
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
