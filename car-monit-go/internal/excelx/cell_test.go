// 钉住 xlsx 落格规则：这三条都是"看代码想不出来、只能靠双端对拍反推"的行为，
// 每条都给了 Java 侧出处，改动前先跑本文件。
package excelx

import "testing"

func TestUnbox(t *testing.T) {
	s := "abc"
	n := int64(7)
	var nilStr *string
	cases := []struct {
		name string
		in   any
		want any
	}{
		{"string", s, "abc"},
		{"*string", &s, "abc"},
		{"nil *string", nilStr, ""},
		{"nil any", nil, ""},
		{"*int64", &n, int64(7)},
		{"int", 5, 5},
	}
	for _, c := range cases {
		if got := Unbox(c.in); got != c.want {
			t.Errorf("%s: Unbox(%v)=%v want %v", c.name, c.in, got, c.want)
		}
	}
	pp := &s // **string
	if got := Unbox(&pp); got != "abc" {
		t.Errorf("多级指针应解到底: %v", got)
	}
}

// TestConvertByExp 覆盖 RuoYi 里大量存在的"残缺表达式"（作者本意是写字典说明，
// 结果被 ExcelUtil 当成 1=机构用户2专家3供应商 这样的单项）：未命中一律空串。
func TestConvertByExp(t *testing.T) {
	cases := []struct {
		value, exp, want string
	}{
		{"1", "1=机构用户2专家3供应商", "机构用户2专家3供应商"},
		{"2", "1=机构用户2专家3供应商", ""},
		{"0", "0=正常,1=停用", "正常"},
		{"1", "0=正常,1=停用", "停用"},
		{"2", "0=正常,1=停用", ""},       // 未命中不是原值
		{"G1517", "内=部", ""},         // /base/toll 的残骸表达式
		{"1", "1=：是，0否", "：是，0否"},    // 全角逗号不算分隔符，整串就是文案
		{"0", "0=:,上=行，1:,下=行", ":"}, // 第一项按 ASCII 逗号拆开
		{"1", "0=:,上=行，1:,下=行", ""},
		{"0,1", "0=正常,1=停用", "正常,停用"}, // 多值：命中的标签用分隔符连接后去掉尾部
		{"", "0=正常,1=停用", ""},
		{"字", "字=典：1白色2黑色", "典：1白色2黑色"},
		{"9", "字=典：1白色2黑色", ""},
	}
	for _, c := range cases {
		if got := ConvertByExp(c.value, c.exp); got != c.want {
			t.Errorf("ConvertByExp(%q,%q)=%q want %q", c.value, c.exp, got, c.want)
		}
	}
}

func TestDictLabel(t *testing.T) {
	dict := map[string]string{"0": "男", "1": "女"}
	if got := DictLabel(dict, "1"); got != "女" {
		t.Errorf("命中应取标签: %q", got)
	}
	if got := DictLabel(dict, "2"); got != "" {
		t.Errorf("未命中要给空串（DictUtils.getDictLabel 的兜底）: %q", got)
	}
	if got := DictLabel(dict, "0,1"); got != "男,女" {
		t.Errorf("多值要逐个翻译: %q", got)
	}
	if got := DictLabel(dict, "0,9"); got != "男" {
		t.Errorf("多值里未命中的项要丢弃: %q", got)
	}
}

func TestSanitize(t *testing.T) {
	// POI/xmlbeans 把 XML 1.0 非法字符写成 '?'（Java 侧实测），Go 的 encoding/xml 会给 U+FFFD。
	in := "a\x1Ab\x00c\td\ne\u0001f"
	want := "a?b?c\td\ne?f"
	if got := Sanitize(in); got != want {
		t.Errorf("Sanitize=%q want %q", got, want)
	}
	if got := Sanitize("中文 emoji \U0001F600"); got != "中文 emoji \U0001F600" {
		t.Errorf("合法字符不能被改动: %q", got)
	}
}

func TestCellAndUtilCell(t *testing.T) {
	n := int64(-1)
	// 数值走数字格：Java 只在 cellType 默认 STRING 的列上做 TAB 前缀，
	// 需要 STRING 形态的列由调用点用 TextValue 落成字符串。
	if got := UtilCell(&n); got != int64(-1) {
		t.Errorf("UtilCell 对指针数值只解引用: %#v", got)
	}
	if got := UtilCell("-1"); got != "\t-1" {
		t.Errorf("UtilCell 对文本要加注入前缀: %q", got)
	}
	if got := UtilCell("ok"); got != "ok" {
		t.Errorf("普通文本不该被加前缀: %q", got)
	}
	if got := UtilCell("=HYPERLINK(\"x\")"); got != "\t=HYPERLINK(\"x\")" {
		t.Errorf("公式注入前缀规则: %q", got)
	}
	// Cell 只做解引用/清洗/超长置空，不加 TAB（EasyPOI 模板导出没有这一步）
	if got := Cell("x\x1Ay"); got != "x?y" {
		t.Errorf("Cell 清洗: %q", got)
	}
	if got := Cell("-1"); got != "-1" {
		t.Errorf("Cell 不加注入前缀: %q", got)
	}
	long := make([]rune, maxCellRunes+1)
	for i := range long {
		long[i] = 'a'
	}
	if got := Cell(string(long)); got != "" {
		t.Errorf("超过 32767 字符的格 Java 是整格留空，不是截断: len=%d", len(got.(string)))
	}
}

func TestTextValue(t *testing.T) {
	n := int64(-1)
	z := int64(0)
	p := 1.5
	if got := TextValue(&n); got != "\t-1" {
		t.Errorf("负数按 Java 落成 TAB 前缀字符串: %q", got)
	}
	if got := TextValue(&z); got != "0" {
		t.Errorf("非负数不加前缀: %q", got)
	}
	if got := TextValue(&p); got != "1.5" {
		t.Errorf("浮点用最短形式: %q", got)
	}
	var nilPtr *int64
	if got := TextValue(nilPtr); got != "" {
		t.Errorf("nil 给空串: %q", got)
	}
}
