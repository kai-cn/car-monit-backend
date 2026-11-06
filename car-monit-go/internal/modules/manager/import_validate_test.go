package manager

import (
	"reflect"
	"testing"
	"time"
)

// JAVA 对照: fastjson 按 JVM 默认时区解析 yyyy-MM-dd HH:mm:ss，DSN 又带 loc=Local，
// 所以这里必须按本地时区解析；用 time.Parse 会得到 UTC，入库钟点整体平移。
func TestParseExceptImportRowKeepsWallClockInLocalZone(t *testing.T) {
	vals := make([]string, len(exceptImportCols))
	vals[2], vals[8] = "2025-01-02 10:00:00", "2025-01-01 09:00:00"
	vals[4], vals[13], vals[16] = "PARITYJ挂", "1.00", "2.00"
	item := parseExceptImportRow(vals)
	want := time.Date(2025, 1, 1, 9, 0, 0, 0, time.Local)
	if item.InTime == nil || !item.InTime.Equal(want) {
		t.Fatalf("inTime 不是本地时区的 09:00: %+v", item.InTime)
	}
	out := time.Date(2025, 1, 2, 10, 0, 0, 0, time.Local)
	if item.OutTime == nil || !item.OutTime.Equal(out) {
		t.Fatalf("outTime 不是本地时区的 10:00: %+v", item.OutTime)
	}
	if strOf(item.SupplementaryStatus) != "0" {
		t.Fatalf("supplementaryStatus 应带 Java 的字段初值 0: %+v", item.SupplementaryStatus)
	}
}

func TestValidateImportRowRequiredAndFormat(t *testing.T) {
	cols := []importCol{{Name: "出口时间", Rules: "1,8"}}
	var got []importError
	validateImportRow(&got, cols, 0, []string{"2025-01-02"})
	want := []importError{{RowNum: 2, ColName: "出口时间", Message: "日期格式（年月日时分秒）不正确"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %+v", got)
	}

	got = nil
	validateImportRow(&got, cols, 0, []string{"2025-01-02 03:04:05"})
	if len(got) != 0 {
		t.Fatalf("合法值报错 %+v", got)
	}
}

func TestValidateImportRowEmptyOnlyChecksRequired(t *testing.T) {
	cols := []importCol{{Name: "", Rules: "1,2"}, {Name: "轴数", Rules: "3"}}
	var got []importError
	validateImportRow(&got, cols, 2, []string{"", ""})
	want := []importError{{RowNum: 4, ColName: "", Message: "不能为空"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %+v want %+v", got, want)
	}
}

func TestValidateImportRowPerTokenOneErrorEach(t *testing.T) {
	// JAVA 对照: 每个规则 token 独立一轮，非空值在一轮里最多命中一条（else-if 链）。
	cols := []importCol{{Name: "x", Rules: "2,3"}}
	var got []importError
	validateImportRow(&got, cols, 0, []string{"abc"})
	if len(got) != 2 {
		t.Fatalf("期望 2 条，实际 %+v", got)
	}
	if got[0].Message != "不是小数" || got[1].Message != "不是正整数" {
		t.Fatalf("消息不对 %+v", got)
	}
}

func TestValidateImportRowRuleRegexes(t *testing.T) {
	cases := []struct {
		rule string
		val  string
		ok   bool
	}{
		{"2", "1.00", true}, {"2", "-1.5", true}, {"2", "1.", false}, {"2", "01x", false},
		{"3", "0", true}, {"3", "", true}, {"3", "-1", false}, {"3", "1.0", false},
		{"4", "2025-01-02", true}, {"4", "2025-1-2", false}, {"4", "2025-01-02 00:00:00", false},
		{"5", "11010119900307345X", true}, {"5", "11010119900307345", false},
		{"6", "2025-01", true}, {"6", "2025/1", true}, {"6", "2025.1", true}, {"6", "202501", false},
		{"7", "+1", true}, {"7", "-1.25", true}, {"7", "1e3", false},
		{"8", "2025-01-02 03:04:05", true}, {"8", "2025-1-2 3:4:5", false},
	}
	cols := []importCol{{Name: "c", Rules: ""}}
	for _, tc := range cases {
		cols[0].Rules = tc.rule
		var got []importError
		validateImportRow(&got, cols, 0, []string{tc.val})
		if (len(got) == 0) != tc.ok {
			t.Errorf("规则 %s 值 %q 期望 ok=%v，实际 %+v", tc.rule, tc.val, tc.ok, got)
		}
	}
}

func TestValidateImportRowTrimsValues(t *testing.T) {
	cols := []importCol{{Name: "c", Rules: "3"}}
	var got []importError
	validateImportRow(&got, cols, 0, []string{" 4 "})
	if len(got) != 0 {
		t.Fatalf("前后空白应被 trim: %+v", got)
	}
}

func TestCollectImportRowsPresence(t *testing.T) {
	// 缺行（POI 的 null row）才是收尾；「行在、值全空」要照常送校验。
	if got := collectImportRows([][]string{{"1", "x"}, nil, {"3", "y"}}); len(got) != 1 {
		t.Fatalf("缺行之后不该再读: %+v", got)
	}
	if got := collectImportRows([][]string{{"", ""}}); len(got) != 1 {
		t.Fatalf("空格行仍是一行数据: %+v", got)
	}
	if got := collectImportRows([][]string{{"x"}, {"break"}, {"y"}}); len(got) != 1 {
		t.Fatalf("break 行应当收尾: %+v", got)
	}
	if got := collectImportRows([][]string{{"x"}, {"结束"}, {"y"}}); len(got) != 1 {
		t.Fatalf("结束 行应当收尾: %+v", got)
	}
}
