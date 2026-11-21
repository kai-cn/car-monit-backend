// 类/职责: 数据接入面离线测试 —— 分表路由、ES 文档形态、上游 HTTP 适配、幂等跳过、失败重试
// 对应 Go 文件: internal/modules/base/datasync_test.go
package base

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"regexp"
	"strings"
	"testing"
	"time"

	"github.com/DATA-DOG/go-sqlmock"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"

	"car-monit-go/internal/app"
	"car-monit-go/internal/config"
	"car-monit-go/internal/stream/kafka"
	"car-monit-go/internal/stream/sharding"
)

func testLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

func newMockDB(t *testing.T) (*gorm.DB, sqlmock.Sqlmock) {
	t.Helper()
	sqlDB, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("sqlmock: %v", err)
	}
	db, err := gorm.Open(mysql.New(mysql.Config{Conn: sqlDB, SkipInitializeWithVersion: true}),
		&gorm.Config{Logger: gormlogger.Default.LogMode(gormlogger.Silent)})
	if err != nil {
		t.Fatalf("gorm: %v", err)
	}
	t.Cleanup(func() { _ = sqlDB.Close() })
	return db, mock
}

func newTestDataSync(db *gorm.DB) *DataSync {
	return &DataSync{
		app:        &app.App{Cfg: &config.Config{}, DB: db, Log: testLogger()},
		log:        testLogger(),
		db:         db,
		prefix:     sharding.DefaultTablePrefix + "_",
		strategy:   sharding.Monthly,
		ensured:    map[string]struct{}{},
		retryDelay: 0,
	}
}

func strp(v string) *string { return &v }
func intp(v int) *int       { return &v }

func iso(t time.Time) *isoDateTime { return &isoDateTime{Time: t} }

func TestParseShardingStrategy(t *testing.T) {
	cases := map[string]sharding.Strategy{
		"month": sharding.Monthly, "MONTHLY": sharding.Monthly,
		"day": sharding.Daily, "quarter": sharding.Quarterly, "year": sharding.Yearly,
		"": sharding.Monthly, "unknown": sharding.Monthly,
	}
	for in, want := range cases {
		if got := parseShardingStrategy(in); got != want {
			t.Errorf("parseShardingStrategy(%q)=%v want %v", in, got, want)
		}
	}
}

func TestIsShardTable(t *testing.T) {
	s := &DataSync{prefix: "ods_rt_szdn_snapshot_flow_", strategy: sharding.Monthly}
	yes := []string{
		"ods_rt_szdn_snapshot_flow_202508",
		"ods_rt_szdn_snapshot_flow_202612",
	}
	no := []string{
		"ods_rt_szdn_snapshot_flow_addcode", // 模板表
		"ods_rt_szdn_snapshot_flow_view",    // 视图
		"ods_rt_szdn_snapshot_flow_2025",    // 年度后缀不是月度
		"other_table_202508",
	}
	for _, name := range yes {
		if !s.isShardTable(name) {
			t.Errorf("isShardTable(%q)=false want true", name)
		}
	}
	for _, name := range no {
		if s.isShardTable(name) {
			t.Errorf("isShardTable(%q)=true want false", name)
		}
	}
}

func TestGroupSnapshotRows(t *testing.T) {
	aug := time.Date(2025, 8, 31, 23, 59, 59, 0, time.Local)
	sep := time.Date(2025, 9, 1, 0, 0, 1, 0, time.Local)
	rows := []*odsRtSzdnSnapshotFlowAddcode{
		{BigID: strp("a"), Snapshottime: iso(aug)},
		{BigID: strp("b"), Snapshottime: iso(sep)},
		{BigID: strp("c")},
		nil,
	}
	grouped, skipped := groupSnapshotRows("ods_rt_szdn_snapshot_flow_", sharding.Monthly, rows)
	if skipped != 2 {
		t.Fatalf("skipped=%d want 2", skipped)
	}
	if len(grouped["ods_rt_szdn_snapshot_flow_202508"]) != 1 {
		t.Errorf("八月分组缺失: %v", grouped)
	}
	if len(grouped["ods_rt_szdn_snapshot_flow_202509"]) != 1 {
		t.Errorf("九月分组缺失: %v", grouped)
	}
}

func TestMonthPartitions(t *testing.T) {
	start := time.Date(2025, 11, 20, 0, 0, 0, 0, time.Local)
	end := time.Date(2026, 2, 3, 0, 0, 0, 0, time.Local)
	got := monthPartitions(start, end)
	want := []string{"202511", "202512", "202601", "202602"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("monthPartitions=%v want %v", got, want)
	}
}

func TestSnapshotFlowESDoc(t *testing.T) {
	ts := time.Date(2025, 8, 31, 12, 30, 0, 0, time.Local)
	received := dateOnly{Time: time.Date(2025, 8, 31, 0, 0, 0, 0, time.Local)}
	row := &odsRtSzdnSnapshotFlowAddcode{
		BigID:        strp("big-1"),
		Direction:    intp(1),
		Snapshottime: iso(ts),
		Receivedtime: &received,
		ID:           strp("transient-id"),
	}
	doc := snapshotFlowESDoc(row)
	if doc["bigId"] != "big-1" {
		t.Fatalf("bigId 错误: %v", doc)
	}
	// 经 JSON 往返后数字是 float64（与 ES 接收的 JSON 一致）。
	if direction, ok := doc["direction"].(float64); !ok || direction != 1 {
		t.Fatalf("direction 错误: %v(%T)", doc["direction"], doc["direction"])
	}
	if doc["snapshottime"] != ts.UnixMilli() {
		t.Errorf("snapshottime=%v want millis %d", doc["snapshottime"], ts.UnixMilli())
	}
	if doc["receivedtime"] != received.UnixMilli() {
		t.Errorf("receivedtime=%v want millis %d", doc["receivedtime"], received.UnixMilli())
	}
	if _, ok := doc["id"]; ok {
		t.Error("transient 字段 id 不应进入 ES 文档")
	}
	if _, ok := doc["datasource"]; ok {
		t.Error("nil 字段应被省略（对齐 fastjson2 默认行为）")
	}
}

func TestHTTPSnapshotFlowSource(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/base/snapshotflow/earliest-time", func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`"2025-08-01T00:00:00.000+08:00"`))
	})
	mux.HandleFunc("/base/snapshotflow/list", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("applyTime1") != "2025-08-01 00:00:00" ||
			r.URL.Query().Get("applyTime2") != "2025-08-31 23:59:59" ||
			r.URL.Query().Get("pageNum") != "2" || r.URL.Query().Get("pageSize") != "1000" {
			t.Errorf("上游查询参数不符: %s", r.URL.RawQuery)
		}
		_, _ = w.Write([]byte(`{"total":2,"rows":[
			{"bigId":"b1","snapshottime":"2025-08-31 12:00:00","direction":1},
			{"bigId":"b2","snapshottime":1756603200000}
		],"code":0}`))
	})
	srv := httptest.NewServer(mux)
	defer srv.Close()

	source := &httpSnapshotFlowSource{baseURL: srv.URL, client: srv.Client()}
	earliest, ok, err := source.Earliest(context.Background())
	if err != nil || !ok {
		t.Fatalf("Earliest err=%v ok=%v", err, ok)
	}
	if earliest.Format("2006-01-02 15:04:05") != "2025-08-01 00:00:00" {
		t.Errorf("earliest=%v", earliest)
	}
	rows, err := source.Page(context.Background(), "2025-08-01 00:00:00", "2025-08-31 23:59:59", 2, 1000)
	if err != nil {
		t.Fatalf("Page: %v", err)
	}
	if len(rows) != 2 || strOf(rows[0].BigID) != "b1" {
		t.Fatalf("rows=%v", rows)
	}
	if rows[1].Snapshottime == nil || rows[1].Snapshottime.IsZero() {
		t.Error("毫秒时间戳未解析")
	}
}

func TestHandleSnapshotFlowBatchValidation(t *testing.T) {
	s := newTestDataSync(nil)
	msgs := []kafka.Message{
		{Offset: 1, Value: `not-json`},
		{Offset: 2, Value: `{"operationType":"INSERT"}`},
		{Offset: 3, Value: `{"operationType":"INSERT","data":{"bigId":""}}`},
		{Offset: 4, Value: `{"operationType":"INSERT","data":{"bigId":"b4"}}`},
	}
	failed, err := s.HandleSnapshotFlowBatch(context.Background(), msgs)
	if err != nil {
		t.Fatalf("handler err: %v", err)
	}
	if len(failed) != 4 {
		t.Fatalf("failed=%d want 4: %+v", len(failed), failed)
	}
	if !strings.Contains(failed[0].Reason, "JSON 解析失败") {
		t.Errorf("reason0=%q", failed[0].Reason)
	}
	if !strings.Contains(failed[1].Reason, "缺少bigId") {
		t.Errorf("reason1=%q", failed[1].Reason)
	}
	if !strings.Contains(failed[3].Reason, "snapshottime") {
		t.Errorf("reason3=%q", failed[3].Reason)
	}
}

func TestHandleSnapshotFlowBatchInsert(t *testing.T) {
	db, mock := newMockDB(t)
	table := "ods_rt_szdn_snapshot_flow_202508"

	mock.ExpectQuery("SELECT COUNT\\(\\*\\) FROM INFORMATION_SCHEMA.TABLES").
		WithArgs(table).
		WillReturnRows(sqlmock.NewRows([]string{"count"}).AddRow(0))
	mock.ExpectExec("CREATE TABLE IF NOT EXISTS").
		WillReturnResult(sqlmock.NewResult(0, 0))
	mock.ExpectExec("INSERT INTO " + regexp.QuoteMeta("`"+table+"`")).
		WillReturnResult(sqlmock.NewResult(0, 1))

	s := newTestDataSync(db)
	body := `{"operationType":"INSERT","data":{"bigId":"b1","snapshottime":"2025-08-15 10:00:00","direction":1}}`
	failed, err := s.HandleSnapshotFlowBatch(context.Background(), []kafka.Message{{Offset: 1, Value: body}})
	if err != nil {
		t.Fatalf("handler err: %v", err)
	}
	if len(failed) != 0 {
		t.Fatalf("unexpected failed: %+v", failed)
	}
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("SQL 期望未满足: %v", err)
	}
}

func TestHandleSnapshotFlowBatchInsertFailureRetries(t *testing.T) {
	db, mock := newMockDB(t)
	table := "ods_rt_szdn_snapshot_flow_202508"

	mock.ExpectQuery("SELECT COUNT\\(\\*\\) FROM INFORMATION_SCHEMA.TABLES").
		WithArgs(table).
		WillReturnRows(sqlmock.NewRows([]string{"count"}).AddRow(1))
	// 首轮 + 3 次重试，全部写入失败。
	for i := 0; i < 4; i++ {
		mock.ExpectExec("INSERT INTO " + regexp.QuoteMeta("`"+table+"`")).
			WillReturnError(io.ErrUnexpectedEOF)
	}

	s := newTestDataSync(db)
	body := `{"operationType":"INSERT","data":{"bigId":"b2","snapshottime":"2025-08-16 10:00:00"}}`
	failed, err := s.HandleSnapshotFlowBatch(context.Background(), []kafka.Message{{Offset: 2, Value: body}})
	if err != nil {
		t.Fatalf("handler err: %v", err)
	}
	if len(failed) != 1 {
		t.Fatalf("failed=%d want 1", len(failed))
	}
	if !strings.Contains(failed[0].Reason, "分表写入失败") || !strings.Contains(failed[0].Reason, "重试失败") {
		t.Errorf("reason=%q", failed[0].Reason)
	}
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("SQL 期望未满足: %v", err)
	}
}

func TestSyncOrgInfoTruncateThenInsert(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/base/org/listAll" {
			t.Errorf("path=%s", r.URL.Path)
		}
		_, _ = w.Write([]byte(`[{"bigId":"o1","orgCode":"001","orgName":"机构一","orgSequence":3,
			"loadTime":"2025-08-01T00:00:00.000+08:00"}]`))
	}))
	defer srv.Close()

	db, mock := newMockDB(t)
	mock.ExpectExec("TRUNCATE TABLE " + regexp.QuoteMeta("`ods_yhgl_v_base_org`")).
		WillReturnResult(sqlmock.NewResult(0, 0))
	// GORM 的 CreateInBatches 默认包在事务里。
	mock.ExpectBegin()
	mock.ExpectExec("INSERT INTO " + regexp.QuoteMeta("`ods_yhgl_v_base_org`")).
		WillReturnResult(sqlmock.NewResult(0, 1))
	mock.ExpectCommit()

	s := newTestDataSync(db)
	s.app.Cfg.VehicleMonitor.BaseURL = srv.URL
	if err := s.SyncOrgInfo(context.Background()); err != nil {
		t.Fatalf("SyncOrgInfo: %v", err)
	}
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("SQL 期望未满足: %v", err)
	}
}

func TestFetchBaseInfoListWrapped(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"code":0,"rows":[{"sectionCode":"S1","openDate":"2025-08-01"}]}`))
	}))
	defer srv.Close()

	s := newTestDataSync(nil)
	s.app.Cfg.VehicleMonitor.BaseURL = srv.URL
	var rows []*odsSzdnSection
	if err := s.fetchBaseInfoList(context.Background(), "/base/section/listAll", &rows); err != nil {
		t.Fatalf("fetch: %v", err)
	}
	if len(rows) != 1 || strOf(rows[0].SectionCode) != "S1" {
		t.Fatalf("rows=%v", rows)
	}
	if rows[0].OpenDate == nil || rows[0].OpenDate.Format("2006-01-02") != "2025-08-01" {
		t.Errorf("openDate=%v", rows[0].OpenDate)
	}
}

func TestSnapshotFlowESDocIsJSONSerializable(t *testing.T) {
	row := &odsRtSzdnSnapshotFlowAddcode{BigID: strp("b1"),
		Snapshottime: iso(time.Date(2025, 8, 1, 0, 0, 0, 0, time.Local))}
	if _, err := json.Marshal(snapshotFlowESDoc(row)); err != nil {
		t.Fatalf("doc 不可序列化: %v", err)
	}
}
