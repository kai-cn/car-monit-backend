// 类/职责: platform/sqlx 占位符语义回归 —— 分页/IN 查询的空集合行为不能漂移
// 对应 Go 文件: internal/platform/sqlx/sqlx_test.go
package sqlx

import "testing"

func TestPlaceholders(t *testing.T) {
	if got := Placeholders(3); got != "?,?,?" {
		t.Errorf("Placeholders(3)=%q", got)
	}
	if got := SpacePlaceholders(3); got != "?, ?, ?" {
		t.Errorf("SpacePlaceholders(3)=%q", got)
	}
	if got := PlaceholdersOrNull(0); got != "NULL" {
		t.Errorf("PlaceholdersOrNull(0)=%q want NULL", got)
	}
	if got := PlaceholdersOrNull(2); got != "?,?" {
		t.Errorf("PlaceholdersOrNull(2)=%q", got)
	}
	if got := Placeholders(0); got != "" {
		t.Errorf("Placeholders(0)=%q want empty", got)
	}
}

func TestArgsConverters(t *testing.T) {
	ss := AnySlice([]string{"a", "b"})
	if len(ss) != 2 || ss[1] != "b" {
		t.Errorf("AnySlice=%v", ss)
	}
	ii := Int64Slice([]int64{1, 2})
	if len(ii) != 2 || ii[0] != int64(1) {
		t.Errorf("Int64Slice=%v", ii)
	}
}
