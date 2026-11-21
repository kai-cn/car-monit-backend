package quartz

import (
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
)

func d(s string) time.Time {
	t, err := time.ParseInLocation("2006-01-02 15:04:05", s, time.Local)
	if err != nil {
		panic(err)
	}
	return t
}

func TestCron(t *testing.T) {
	cases := []struct {
		expr string
		from string
		want string
	}{
		{"0 0/5 * * * ?", "2026-01-01 10:02:30", "2026-01-01 10:05:00"},
		{"0 0 1 1 * ?", "2026-01-01 02:00:00", "2026-02-01 01:00:00"},
		{"0 0 2 ? * MON", "2026-01-01 02:00:00", "2026-01-05 02:00:00"},
		{"0 0 0 L * ?", "2026-02-01 00:00:00", "2026-02-28 00:00:00"},
		{"0 0 12 15W * ?", "2026-02-01 00:00:00", "2026-02-16 12:00:00"},
		{"0 15 10 ? * 6L", "2026-01-01 00:00:00", "2026-01-30 10:15:00"},
		{"0 15 10 ? * 6#3", "2026-01-01 00:00:00", "2026-01-16 10:15:00"},
		{"0 0 2 ? * MON", "2026-01-05 03:00:00", "2026-01-12 02:00:00"},
		{"*/10 * * * * ?", "2026-01-01 00:00:01", "2026-01-01 00:00:10"},
		{"0 0 2 ? * SUN", "2026-01-01 00:00:00", "2026-01-04 02:00:00"},
	}
	for _, c := range cases {
		spec, err := ParseCronExpression(c.expr)
		if err != nil {
			t.Fatalf("%s: %v", c.expr, err)
		}
		got, ok := spec.Next(d(c.from))
		if !ok {
			t.Fatalf("%s: no next", c.expr)
		}
		if got.Format("2006-01-02 15:04:05") != c.want {
			t.Errorf("%s from %s: got %s want %s", c.expr, c.from, got.Format("2006-01-02 15:04:05"), c.want)
		}
	}
}

func TestCronInvalid(t *testing.T) {
	bad := []string{
		"", "* * * * *", "0 0 12 * * ? * *", "0 0 12 ? * ?", "0 0 12 * * *",
		"61 * * * * ?", "0 0 25 * * ?", "0 0 12 32 * ?", "0 0 12 * 13 ?",
		"0 0 12 ? * 8", "0 0 12 ? * MOO", "*/0 * * * * ?", "0 0 12 10-5 * ?",
		"0 0 12 ? * 6#6", "abc", "0 0 12 * * ? #",
	}
	for _, expr := range bad {
		if IsValidCronExpression(expr) {
			t.Errorf("expected invalid: %q", expr)
		}
	}
	good := []string{
		"0 0/3 * * * ?", "0 0 5 * * ?", "0 0 1 1 * ?", "0 0 2 * * ?", "0 0 2 ? * MON",
		"0 0 12 ? * 2-6", "0 0 12 ? * MON-FRI", "0 0 12 1,15 * ?",
		"0 0 0 L-3 * ?", "0 0 0 LW * ?", "0 0 12 ? * 5L", "0 0 12 ? * 6#3",
		"0 */5 * * * ?", "0 0 1 1 * ? 2026",
	}
	for _, expr := range good {
		if !IsValidCronExpression(expr) {
			t.Errorf("expected valid: %q (%v)", expr, ValidateCronExpression(expr))
		}
	}
}

func TestInvokeParse(t *testing.T) {
	target := "ryTask.ryMultipleParams('ry', true, 2L, 3.5D, 4)"
	if !IsValidClassName(target) {
		t.Fatal("want class name false?")
	}
	if got := GetBeanName(target); got != "ryTask" {
		t.Fatalf("bean=%s", got)
	}
	if got := GetMethodName(target); got != "ryMultipleParams" {
		t.Fatalf("method=%s", got)
	}
	params, err := GetMethodParams(target)
	if err != nil {
		t.Fatal(err)
	}
	if len(params) != 5 {
		t.Fatalf("params=%v", params)
	}
	if params[0] != "ry" || params[1] != true || params[2] != int64(2) || params[3] != 3.5 || params[4] != 4 {
		t.Fatalf("params=%#v", params)
	}
	cls := "com.ruoyi.quartz.task.RyTask.ryParams('x')"
	if !IsValidClassName(cls) {
		t.Fatal("want class name")
	}
	if GetBeanName(cls) != "com.ruoyi.quartz.task.RyTask" {
		t.Fatalf("bean=%s", GetBeanName(cls))
	}
	if err := CheckInvokeTarget("java.net.URL('http://x')"); err == nil {
		t.Fatal("blocklist not applied")
	}
	if err := CheckInvokeTarget("com.ruoyi.quartz.task.RyTask.ryParams('x')"); err != nil {
		t.Fatal(err)
	}
	if err := CheckInvokeTarget("org.springframework.Foo.bar()"); err == nil {
		t.Fatal("blocklist not applied")
	}
}

func TestRouteShape(t *testing.T) {
	g := gin.New()
	hit := ""
	h := func(name string) gin.HandlerFunc {
		return func(c *gin.Context) { hit = name }
	}
	g.GET("/monitor/job/list", h("job-list"))
	g.GET("/monitor/job/export", h("job-export"))
	g.GET("/monitor/job/:jobId", h("job-info"))
	g.POST("/monitor/job", h("job-add"))
	g.PUT("/monitor/job", h("job-edit"))
	g.PUT("/monitor/job/changeStatus", h("job-status"))
	g.PUT("/monitor/job/run", h("job-run"))
	g.DELETE("/monitor/job/:jobIds", h("job-remove"))
	g.GET("/monitor/jobLog/list", h("log-list"))
	g.GET("/monitor/jobLog/export", h("log-export"))
	g.GET("/monitor/jobLog/:jobLogId", h("log-info"))
	g.DELETE("/monitor/jobLog/:jobLogIds", h("log-remove"))
	g.DELETE("/monitor/jobLog/clean", h("log-clean"))

	cases := map[string]string{
		"GET /monitor/job/list":        "job-list",
		"GET /monitor/job/export":      "job-export",
		"GET /monitor/job/1":           "job-info",
		"DELETE /monitor/job/1,2":      "job-remove",
		"DELETE /monitor/jobLog/clean": "log-clean",
		"DELETE /monitor/jobLog/3,4":   "log-remove",
		"GET /monitor/jobLog/export":   "log-export",
		"GET /monitor/jobLog/9":        "log-info",
	}
	for req, want := range cases {
		method, path, _ := strings.Cut(req, " ")
		r := httptest.NewRequest(method, path, nil)
		w := httptest.NewRecorder()
		g.ServeHTTP(w, r)
		if hit != want {
			t.Errorf("%s -> %s want %s (status %d)", req, hit, want, w.Code)
		}
	}
}
