// 分页语义的期望值全部照抄 PageHelper 5.3.3 源码：
// Page.calculateStartAndEndRow / Page.setTotal / Page.setReasonable / AbstractHelperDialect.afterCount。
package web

import "testing"

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
		{"首页", PageDomain{HasPage: true, PageNum: 1, PageSize: 3, Reasonable: true}, 11106, 1, 0, false},
		{"reasonable 把 0 页拉回第一页", PageDomain{HasPage: true, PageNum: 0, PageSize: 3, Reasonable: true}, 185, 1, 0, false},
		{"reasonable=false 时 0 页不钳且跳过查询", PageDomain{HasPage: true, PageNum: 0, PageSize: 3}, 185, 0, 0, true},
		{"reasonable=false 时负页码同样跳过", PageDomain{HasPage: true, PageNum: -1, PageSize: 3}, 185, -1, 0, true},
		{"reasonable 越界回末页", PageDomain{HasPage: true, PageNum: 9999, PageSize: 3, Reasonable: true}, 185, 62, 183, false},
		{"reasonable=false 越界直接跳过", PageDomain{HasPage: true, PageNum: 9999, PageSize: 3}, 185, 9999, 29994, true},
		{"count=0 跳过", PageDomain{HasPage: true, PageNum: 1, PageSize: 3, Reasonable: true}, 0, 1, 0, true},
		{"count=0 且页码大于 0 也跳过", PageDomain{HasPage: true, PageNum: 2, PageSize: 3, Reasonable: true}, 0, 2, 3, true},
		{"pageSize=0 仍执行（Java 只在 pageSize<0 时跳过）", PageDomain{HasPage: true, PageNum: 1, PageSize: 0, Reasonable: true}, 185, 1, 0, false},
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
