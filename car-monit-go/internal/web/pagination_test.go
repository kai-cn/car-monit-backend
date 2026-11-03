// 分页语义的期望值全部照抄 PageHelper 5.3.3 源码：
// Page.calculateStartAndEndRow / Page.setTotal / Page.setReasonable / AbstractHelperDialect.afterCount，
// 参数解析部分照抄 TableSupport.getPageDomain（Convert.toInt）与 PageDomain.setIsAsc/setReasonable。
package web

import (
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestClampAndSkipQuery(t *testing.T) {
	cases := []struct {
		name       string
		pd         PageDomain
		total      int64
		wantPage   int
		wantOffset int
		wantSkip   bool
	}{
		{"不分页时一切照原样", PageDomain{PageNum: 7, PageSize: 5}, 100, 7, 0, false},
		{"不分页且 total=0 也不能跳过（Java 仍执行查询取行数）", PageDomain{PageSize: 3}, 0, 0, 0, false},
		{"首页", PageDomain{HasPage: true, PageNum: 1, PageSize: 3, Reasonable: true}, 11106, 1, 0, false},
		{"reasonable 把 0 页拉回第一页", PageDomain{HasPage: true, PageNum: 0, PageSize: 3, Reasonable: true}, 185, 1, 0, false},
		{"reasonable=false 时 0 页不钳且跳过查询", PageDomain{HasPage: true, PageNum: 0, PageSize: 3}, 185, 0, 0, true},
		{"reasonable=false 时负页码同样跳过", PageDomain{HasPage: true, PageNum: -1, PageSize: 3}, 185, -1, 0, true},
		{"reasonable 越界回末页", PageDomain{HasPage: true, PageNum: 9999, PageSize: 3, Reasonable: true}, 185, 62, 183, false},
		{"reasonable=false 越界直接跳过", PageDomain{HasPage: true, PageNum: 9999, PageSize: 3}, 185, 9999, 29994, true},
		{"count=0 跳过", PageDomain{HasPage: true, PageNum: 1, PageSize: 3, Reasonable: true}, 0, 1, 0, true},
		{"count=0 且页码大于 0 也跳过", PageDomain{HasPage: true, PageNum: 2, PageSize: 3, Reasonable: true}, 0, 2, 3, true},
		{"count=0 时 pages=0，reasonable 不改页码", PageDomain{HasPage: true, PageNum: 9999, PageSize: 3, Reasonable: true}, 0, 9999, 29994, true},
		{"pageSize=0 仍执行（Java 只在 pageSize<0 时跳过）", PageDomain{HasPage: true, PageNum: 1, PageSize: 0, Reasonable: true}, 185, 1, 0, false},
		{"pageSize=0 时越界页不做上界钳位", PageDomain{HasPage: true, PageNum: 9999, PageSize: 0, Reasonable: true}, 185, 9999, 0, false},
		{"pageSize=0 且 count=0 跳过", PageDomain{HasPage: true, PageNum: 1, PageSize: 0, Reasonable: true}, 0, 1, 0, true},
		{"末页恰好取完", PageDomain{HasPage: true, PageNum: 2, PageSize: 3, Reasonable: true}, 6, 2, 3, false},
		{"起始行等于总数时跳过", PageDomain{HasPage: true, PageNum: 3, PageSize: 3}, 6, 3, 6, true},
	}
	for _, c := range cases {
		clamped := c.pd.Clamp(c.total)
		if clamped.PageNum != c.wantPage {
			t.Errorf("%s: 页码 = %d，期望 %d", c.name, clamped.PageNum, c.wantPage)
		}
		if got := clamped.Offset(); got != c.wantOffset {
			t.Errorf("%s: offset = %d，期望 %d", c.name, got, c.wantOffset)
		}
		if got := c.pd.SkipQuery(c.total); got != c.wantSkip {
			t.Errorf("%s: SkipQuery = %v，期望 %v", c.name, got, c.wantSkip)
		}
	}
}

func TestLimitOffsetKeepsLimit(t *testing.T) {
	pd := PageDomain{HasPage: true, PageNum: 9999, PageSize: 3, Reasonable: true}
	if lim, off := pd.LimitOffset(185); lim != 3 || off != 183 {
		t.Errorf("LimitOffset = (%d, %d)，期望 (3, 183)", lim, off)
	}
	if lim, off := (PageDomain{HasPage: true, PageNum: 1, PageSize: 0}).LimitOffset(185); lim != 0 || off != 0 {
		t.Errorf("pageSize=0 时 LimitOffset = (%d, %d)，期望 (0, 0)", lim, off)
	}
	// 不分页时不能给出 LIMIT（调用方靠 HasPage 决定是否拼 LIMIT/OFFSET）
	if lim, off := (PageDomain{PageNum: 1, PageSize: 10}).LimitOffset(0); lim != 0 || off != 0 {
		t.Errorf("不分页时 LimitOffset = (%d, %d)，期望 (0, 0)", lim, off)
	}
}

// TestPageFromRequest 钉的是 `web.Page(c)` 的取值规则：
// Java 侧是 TableSupport.getPageDomain 的 Convert.toInt(参数, 默认) + PageDomain 的 setter。
func TestPageFromRequest(t *testing.T) {
	gin.SetMode(gin.TestMode)
	cases := []struct {
		query string
		want  PageDomain
	}{
		// 缺省：Java 仍然给 1/10（所以「Java 调过 startPage」的端点要用 PageAlways）
		{"", PageDomain{PageNum: 1, PageSize: 10, IsAsc: "asc", Reasonable: true}},
		// 只传一个参数：值照用，但不算「请求要求分页」
		{"?pageNum=3", PageDomain{PageNum: 3, PageSize: 10, IsAsc: "asc", Reasonable: true}},
		{"?pageSize=7", PageDomain{PageNum: 1, PageSize: 7, IsAsc: "asc", Reasonable: true}},
		{"?pageNum=3&pageSize=7", PageDomain{PageNum: 3, PageSize: 7, HasPage: true, IsAsc: "asc", Reasonable: true}},
		// Convert.toInt：解析不出数字才回落默认；显式 0/负数是合法入参
		{"?pageNum=abc&pageSize=3", PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "asc", Reasonable: true}},
		{"?pageNum=0&pageSize=3", PageDomain{PageNum: 0, PageSize: 3, HasPage: true, IsAsc: "asc", Reasonable: true}},
		{"?pageNum=-5&pageSize=3", PageDomain{PageNum: -5, PageSize: 3, HasPage: true, IsAsc: "asc", Reasonable: true}},
		// Java 的 pageSizeZero=true 让 pageSize<0 得到空结果，这里归一成 LIMIT 0 等价
		{"?pageNum=1&pageSize=-1", PageDomain{PageNum: 1, PageSize: 0, HasPage: true, IsAsc: "asc", Reasonable: true}},
		// PageDomain.setReasonable：Boolean.valueOf，只有 "true" 才是真；不传保持默认 TRUE
		{"?pageNum=1&pageSize=3&reasonable=false", PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "asc"}},
		{"?pageNum=1&pageSize=3&reasonable=true", PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "asc", Reasonable: true}},
		{"?pageNum=1&pageSize=3&reasonable=1", PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "asc"}},
		// PageDomain.setIsAsc：兼容前端的排序别名
		{"?pageNum=1&pageSize=3&orderByColumn=createTime&isAsc=descending",
			PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "desc", Reasonable: true, OrderByColumn: "createTime"}},
		{"?pageNum=1&pageSize=3&orderByColumn=carNo&isAsc=ascending",
			PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "asc", Reasonable: true, OrderByColumn: "carNo"}},
		// 空 isAsc：Java 的 setter 有 isNotEmpty 保护，保持字段默认 asc
		{"?pageNum=1&pageSize=3&isAsc=", PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "asc", Reasonable: true}},
		// 非法方向原样保留（交给 MySQL 报错）
		{"?pageNum=1&pageSize=3&orderByColumn=carNo&isAsc=bogus",
			PageDomain{PageNum: 1, PageSize: 3, HasPage: true, IsAsc: "bogus", Reasonable: true, OrderByColumn: "carNo"}},
	}
	for _, c := range cases {
		got := pageFromQuery(c.query)
		if got != c.want {
			t.Errorf("Page(%q) = %+v，期望 %+v", c.query, got, c.want)
		}
	}
}

func pageFromQuery(query string) PageDomain {
	c, _ := gin.CreateTestContext(httptest.NewRecorder())
	c.Request = httptest.NewRequest("GET", "/x"+query, nil)
	return Page(c)
}

// TestPageAlwaysForcesPaging 对应 §4 第 6 项：Java 调过 startPage() 的端点不带参数也只给一页。
func TestPageAlwaysForcesPaging(t *testing.T) {
	gin.SetMode(gin.TestMode)
	c, _ := gin.CreateTestContext(httptest.NewRecorder())
	c.Request = httptest.NewRequest("GET", "/x", nil)
	if got := PageAlways(c); !got.HasPage || got.PageNum != 1 || got.PageSize != 10 {
		t.Errorf("PageAlways(无参数) = %+v，期望 HasPage=true、1/10", got)
	}
}

func TestOrderByMirrorsPageDomain(t *testing.T) {
	cases := []struct {
		column, asc, want string
	}{
		{"createTime", "desc", "create_time desc"},
		{"carNo", "DESC", "car_no DESC"},
		{"carNo", "ascending", "car_no ascending"},
		{"car_no", "asc", "car_no asc"},
		// 非法方向：Java 原样拼进 SQL 由 MySQL 报错（两端都 code=500），Go 同样交给 SQL
		{"carNo", "bogus", "car_no bogus"},
		// 非法字符：Java 抛 UtilException，Go 忽略该排序（DIFF 见 OrderBy 注释）
		{"1;drop", "desc", ""},
		{"carNo", "desc;drop", ""},
		{"", "desc", ""},
	}
	for _, c := range cases {
		pd := PageDomain{OrderByColumn: c.column, IsAsc: c.asc}
		if got := pd.OrderBy(); got != c.want {
			t.Errorf("OrderBy(%q, %q) = %q，期望 %q", c.column, c.asc, got, c.want)
		}
	}
	if got := (PageDomain{}).OrderByWithDefault("t.id desc"); got != "t.id desc" {
		t.Errorf("OrderByWithDefault = %q，期望服务端默认排序", got)
	}
	if got := (PageDomain{OrderByColumn: "id", IsAsc: "desc"}).OrderByWithDefault("t.id desc"); got != "id desc" {
		t.Errorf("客户端排序应覆盖默认排序，得到 %q", got)
	}
}
