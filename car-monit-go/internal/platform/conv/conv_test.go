// 类/职责: platform/conv 的语义回归 —— 确保 NULL/trim/CSV 行为与 Java 工具类一致
// 对应 Go 文件: internal/platform/conv/conv_test.go
package conv

import "testing"

func TestValueKeepsNullAndDoesNotTrim(t *testing.T) {
	var nilStr *string
	ten := int64(10)
	cases := []struct {
		name string
		in   any
		want string
	}{
		{"nil", nil, ""},
		{"nil string ptr", nilStr, ""},
		{"string keeps spaces", " a ", " a "},
		{"bytes", []byte("b"), "b"},
		{"int64 ptr", &ten, "10"},
	}
	for _, c := range cases {
		if got := Value(c.in); got != c.want {
			t.Errorf("Value(%s)=%q want %q", c.name, got, c.want)
		}
	}
}

func TestNullTrims(t *testing.T) {
	if got := Null("  x  "); got != "x" {
		t.Errorf("Null=%q want x", got)
	}
	if got := Null(nil); got != "" {
		t.Errorf("Null(nil)=%q", got)
	}
	if !Blank("  ") || !NotBlank(" a ") {
		t.Error("Blank/NotBlank 语义错误")
	}
}

func TestSplitCSVMatchesJavaSplit(t *testing.T) {
	cases := []struct {
		in   string
		want []string
	}{
		{"a,b", []string{"a", "b"}},
		{"a,", []string{"a"}},
		{"a,,b", []string{"a", "", "b"}},
		{"", []string{}},
	}
	for _, c := range cases {
		got := SplitCSV(c.in)
		if len(got) != len(c.want) {
			t.Fatalf("SplitCSV(%q)=%v want %v", c.in, got, c.want)
		}
		for i := range got {
			if got[i] != c.want[i] {
				t.Fatalf("SplitCSV(%q)=%v want %v", c.in, got, c.want)
			}
		}
	}
}

func TestPointerHelpers(t *testing.T) {
	if s := Str("x"); s == nil || *s != "x" {
		t.Error("Str 错误")
	}
	if n := Int64(7); n == nil || *n != 7 {
		t.Error("Int64 错误")
	}
}
