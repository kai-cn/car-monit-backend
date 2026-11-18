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
	// startPage 标记「Java 侧无条件调用 startPage()」的端点（由 PageAlways 置位）。
	// 只有这类端点才会走 SqlUtil.escapeOrderBySql，非法排序参数在那里就被拒掉；
	// 不分页的端点（导出、listAll）Java 根本不校验，所以 Go 也不能校验。
	startPage bool
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
		// JAVA 对照: TableSupport → ServletUtils.getParameterToBool → Convert.toBool(值, null)，
		// 再由 PageDomain.getReasonable() 把 null 回落成 TRUE；PageHelper 的全局默认也是 TRUE。
		switch strings.ToLower(strings.TrimSpace(v)) {
		case "false", "no", "0":
			pd.Reasonable = false
		default:
			// true/yes/ok/1 为真；空、乱值 → Convert 给 null → getReasonable() 给 TRUE
			pd.Reasonable = true
		}
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
	pd.startPage = true
	return pd
}

// rawOrderBy 对应 PageDomain.getOrderBy：客户端给了排序列时拼成「列名 方向」。
// 与 OrderBy() 的区别是不做校验 —— 校验结果要交给 StartPageError 决定报不报错。
func (p PageDomain) rawOrderBy() string {
	if p.OrderByColumn == "" {
		return ""
	}
	return toUnderScoreCase(p.OrderByColumn) + " " + p.IsAsc
}

// StartPageError 复刻 SqlUtil.escapeOrderBySql 的两条拒绝规则（顺序也一致）：
//   - 非空且字符不在白名单 `^[a-zA-Z0-9_ ,.]+$` → UtilException("参数不符合规范，不能进行查询")
//   - 长度超过 500 → UtilException("参数已超过最大限制，不能进行查询")
//
// UtilException 经 GlobalExceptionHandler 变成 `{code:500, msg:上面那句}`。
// 只对 Java 侧调过 startPage() 的端点生效：其余端点 Java 不读这两个参数，也不校验。
func (p PageDomain) StartPageError() error {
	if !p.startPage {
		return nil
	}
	order := p.rawOrderBy()
	if order == "" {
		return nil
	}
	if !orderByPattern.MatchString(order) {
		return NewServiceError("参数不符合规范，不能进行查询")
	}
	if len(order) > orderByMaxLength {
		return NewServiceError("参数已超过最大限制，不能进行查询")
	}
	return nil
}

// Clamp 对应 PageHelper 的两处页码修正：
//   - Page.setReasonable / Page.pageNum：`reasonable && pageNum<=0` 才回到第一页
//     （reasonable=false 时不钳，Java 之后会因 `pageNum > 0` 不成立而直接返回空）；
//   - Page.setTotal：`reasonable && pageNum > pages` 回到最后一页（pages=0 时不改页码）。
func (p PageDomain) Clamp(total int64) PageDomain {
	if !p.HasPage {
		return p
	}
	if p.Reasonable && p.PageNum <= 0 {
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

// SkipQuery 复刻 PageHelper 的 afterCount：先 setTotal(count)，再决定要不要执行数据查询。
// Java 的放行条件是
//   - `pageSizeZero=false`（本工程 pagehelper 没配这个属性，默认就是 false）⇒ `pageSize<=0` 一律不放行；
//   - 否则 `pageNum > 0 && count > startRow`。
//
// 不放行时拦截器直接 `afterPage(new ArrayList())`，数据查询一次都不执行，
// 因此「空结果/零页长 + 非法排序列」在 Java 侧不会报错。
//
// 实测依据：`/base/geometry/list?pageNum=1&pageSize=0&orderByColumn=createTime`
// Java 是 200/total=11106/rows=0，若照常执行 `LIMIT 0` 就会把 MySQL 的未知列错误暴露出来。
func (p PageDomain) SkipQuery(total int64) bool {
	if !p.HasPage {
		return false
	}
	c := p.Clamp(total)
	if c.PageSize <= 0 {
		return true
	}
	return c.PageNum <= 0 || total <= int64(c.startRow())
}

// startRow 对应 Page.calculateStartAndEndRow：pageNum<=0 时起始行为 0。
func (p PageDomain) startRow() int {
	if p.PageNum > 0 {
		return (p.PageNum - 1) * p.PageSize
	}
	return 0
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
	return p.startRow()
}

func (p PageDomain) Limit() int {
	if !p.HasPage {
		return 0
	}
	return p.PageSize
}

var orderByPattern = regexp.MustCompile(`^[a-zA-Z0-9_\ \,\.]+$`)

// orderByMaxLength 对应 SqlUtil.ORDER_BY_MAX_LENGTH。
const orderByMaxLength = 500

// OrderBy 对应 PageDomain.getOrderBy + SqlUtil.escapeOrderBySql。
// 返回空串表示不排序。
//
// 方向值**原样拼接**（Java 就是 `列名 + " " + isAsc`）：`isAsc=bogus` 这类合法字符但非法的
// 方向会进到 SQL 里让 MySQL 报语法错，两端都是 code=500（仅错误文本形态不同）。
// DIFF: 校验不通过时 Java 抛 UtilException("参数不符合规范，不能进行查询")，Go 忽略该排序
// 继续正常返回 —— 这类入参基本都是注入探测，不返回 500 更安全，也不影响合法请求。
func (p PageDomain) OrderBy() string {
	if p.OrderByColumn == "" {
		return ""
	}
	order := toUnderScoreCase(p.OrderByColumn) + " " + p.IsAsc
	if !orderByPattern.MatchString(order) {
		return ""
	}
	return order
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
