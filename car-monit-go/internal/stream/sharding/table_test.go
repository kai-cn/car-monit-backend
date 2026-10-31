package sharding

import (
	"testing"
	"time"
)

func TestTableNameByDate(t *testing.T) {
	d := time.Date(2025, 8, 15, 10, 30, 0, 0, time.Local)
	cases := []struct {
		prefix   string
		strategy Strategy
		want     string
	}{
		{"ods_rt_szdn_snapshot_flow", Monthly, "ods_rt_szdn_snapshot_flow_202508"},
		{"ods_rt_szdn_snapshot_flow_", Monthly, "ods_rt_szdn_snapshot_flow_202508"},
		{"t", Daily, "t_20250815"},
		{"t", Quarterly, "t_2025Q3"},
		{"t", Yearly, "t_2025"},
	}
	for _, c := range cases {
		if got := TableNameByDate(c.prefix, d, c.strategy); got != c.want {
			t.Errorf("TableNameByDate(%q,%v)=%q, want %q", c.prefix, c.strategy, got, c.want)
		}
	}
}

func TestTableNamesByDateRange(t *testing.T) {
	// 与 Java 相同：从开始日按月推进（8-15 → 9-15 → 10-15），10-15 已超过结束日，
	// 因此不包含 202510。这是原实现的边界行为，测试用于锁定语义。
	got := TableNamesByDateRangeDefault("2025-08-15", "2025-10-02")
	want := []string{
		"ods_rt_szdn_snapshot_flow_202508",
		"ods_rt_szdn_snapshot_flow_202509",
	}
	if len(got) != len(want) {
		t.Fatalf("len=%d, want %d (%v)", len(got), len(want), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("got[%d]=%q, want %q", i, got[i], want[i])
		}
	}
}

func TestPeriodEnd(t *testing.T) {
	d := time.Date(2025, 2, 10, 12, 0, 0, 0, time.Local)
	end := PeriodEnd(d, Monthly)
	if end.Month() != time.February || end.Day() != 28 || end.Hour() != 23 || end.Minute() != 59 || end.Second() != 59 {
		t.Errorf("unexpected month end: %v", end)
	}
}

func TestIsOverMonths(t *testing.T) {
	if !IsOverMonths("2025-01-01", "2025-08-01", 6) {
		t.Error("expected over 6 months")
	}
	if IsOverMonths("2025-07-01", "2025-08-01", 6) {
		t.Error("not over 6 months")
	}
}
