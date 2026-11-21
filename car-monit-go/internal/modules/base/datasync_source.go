// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsRtSzdnSnapshotFlowAddcodeService.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpBaseInfoApiService.java
// 类/职责: 数据接入的上游 HTTP 适配层（vehicleMonitor.baseUrl）
// 对应 Go 文件: internal/modules/base/datasync_source.go
//
// DIFF: Java Forest 声明式客户端 → net/http 显式请求；超时取 forest.timeout（毫秒）。
// DIFF: Forest 的 BackOffRetryer（重试 2 次）未实现，失败由调用方（Kafka 重试/下次调度）承担。
// 未验证点: 本地无 vehicleMonitor/GaussDB 实例，/base/snapshotflow/earliest-time 与
// /base/snapshotflow/list 的响应结构只按 Java 声明（Date / TableDataInfo）做兼容解析，
// 上线前必须在真实环境复核（见 docs/MIGRATION_GUIDE.md「数据接入边界」）。
package base

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"car-monit-go/internal/config"
	"car-monit-go/internal/web"
)

// newSnapshotFlowSource 依据 snapshot.flow.sync.* 构造可配置的数据源。
func newSnapshotFlowSource(cfg *config.Config) SnapshotFlowSource {
	syncCfg := cfg.Snapshot.Flow.Sync
	source := strings.ToLower(strings.TrimSpace(syncCfg.Source))
	if source == "" {
		source = "http"
	}
	if source == "disabled" {
		return disabledSnapshotFlowSource{}
	}
	baseURL := strings.TrimSpace(syncCfg.BaseURL)
	if baseURL == "" {
		baseURL = strings.TrimSpace(cfg.VehicleMonitor.BaseURL)
	}
	timeout := cfg.Forest.Timeout
	if timeout <= 0 {
		timeout = 60000
	}
	if baseURL == "" {
		return disabledSnapshotFlowSource{reason: "snapshot.flow.sync.base-url 与 vehicleMonitor.baseUrl 均为空"}
	}
	return &httpSnapshotFlowSource{
		baseURL: strings.TrimRight(baseURL, "/"),
		client:  &http.Client{Timeout: time.Duration(timeout) * time.Millisecond},
	}
}

// disabledSnapshotFlowSource 表示同步未配置：所有方法返回明确错误，绝不静默成功。
type disabledSnapshotFlowSource struct {
	reason string
}

func (d disabledSnapshotFlowSource) Name() string { return "disabled" }

func (d disabledSnapshotFlowSource) Earliest(context.Context) (time.Time, bool, error) {
	reason := d.reason
	if reason == "" {
		reason = "snapshot.flow.sync.source=disabled"
	}
	return time.Time{}, false, fmt.Errorf("门架流水同步数据源未启用: %s", reason)
}

func (d disabledSnapshotFlowSource) Page(context.Context, string, string, int, int) ([]*odsRtSzdnSnapshotFlowAddcode, error) {
	reason := d.reason
	if reason == "" {
		reason = "snapshot.flow.sync.source=disabled"
	}
	return nil, fmt.Errorf("门架流水同步数据源未启用: %s", reason)
}

// httpSnapshotFlowSource 对应 HttpOdsRtSzdnSnapshotFlowAddcodeService。
type httpSnapshotFlowSource struct {
	baseURL string
	client  *http.Client
}

func (s *httpSnapshotFlowSource) Name() string { return "http:" + s.baseURL }

// Earliest 对应 GET /base/snapshotflow/earliest-time（返回 java.util.Date，可为 null）。
func (s *httpSnapshotFlowSource) Earliest(ctx context.Context) (time.Time, bool, error) {
	body, err := s.get(ctx, "/base/snapshotflow/earliest-time", nil)
	if err != nil {
		return time.Time{}, false, err
	}
	trimmed := strings.TrimSpace(string(body))
	if trimmed == "" || trimmed == "null" {
		return time.Time{}, false, nil
	}
	// 兼容 Jackson 的三种形态：ISO 字符串、毫秒时间戳、AjaxResult{data:...}。
	var text string
	if err := json.Unmarshal(body, &text); err == nil {
		return parseTimeValue(text), text != "", nil
	}
	var number json.Number
	if err := json.Unmarshal(body, &number); err == nil {
		if n, err := number.Int64(); err == nil {
			return time.UnixMilli(n), true, nil
		}
	}
	var wrapped struct {
		Data json.RawMessage `json:"data"`
		Msg  string          `json:"msg"`
	}
	if err := json.Unmarshal(body, &wrapped); err == nil && len(wrapped.Data) > 0 {
		var inner string
		if json.Unmarshal(wrapped.Data, &inner) == nil && inner != "" {
			return parseTimeValue(inner), true, nil
		}
		var innerNum json.Number
		if json.Unmarshal(wrapped.Data, &innerNum) == nil {
			if n, err := innerNum.Int64(); err == nil {
				return time.UnixMilli(n), true, nil
			}
		}
	}
	return time.Time{}, false, fmt.Errorf("无法解析 earliest-time 响应: %s", limit(trimmed, 200))
}

// Page 对应 GET /base/snapshotflow/list（TableDataInfo.rows）。
func (s *httpSnapshotFlowSource) Page(ctx context.Context, start, end string, pageNum, pageSize int) ([]*odsRtSzdnSnapshotFlowAddcode, error) {
	params := map[string]string{
		"applyTime1": start,
		"applyTime2": end,
		"pageNum":    fmt.Sprint(pageNum),
		"pageSize":   fmt.Sprint(pageSize),
	}
	body, err := s.get(ctx, "/base/snapshotflow/list", params)
	if err != nil {
		return nil, err
	}
	if len(strings.TrimSpace(string(body))) == 0 {
		return nil, nil
	}
	var table struct {
		Total int64                           `json:"total"`
		Rows  []*odsRtSzdnSnapshotFlowAddcode `json:"rows"`
	}
	if err := json.Unmarshal(body, &table); err != nil {
		return nil, fmt.Errorf("解析 snapshotflow/list 失败: %w（响应: %s）", err, limit(string(body), 200))
	}
	return table.Rows, nil
}

func (s *httpSnapshotFlowSource) get(ctx context.Context, path string, params map[string]string) ([]byte, error) {
	target := s.baseURL + path
	if len(params) > 0 {
		query := url.Values{}
		for k, v := range params {
			query.Set(k, v)
		}
		target += "?" + query.Encode()
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Connection", "close")
	resp, err := s.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("请求 vehicleMonitor 失败(%s): %w", path, err)
	}
	defer func() { _ = resp.Body.Close() }()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("读取 vehicleMonitor 响应失败(%s): %w", path, err)
	}
	if resp.StatusCode < 200 || resp.StatusCode > 299 {
		return nil, fmt.Errorf("vehicleMonitor %s 返回 HTTP %d: %s", path, resp.StatusCode, limit(string(body), 200))
	}
	return body, nil
}

// fetchBaseInfoList 对应 Forest 的 List<Domain> 反序列化（/base/xxx/listAll 返回裸数组）。
func (s *DataSync) fetchBaseInfoList(ctx context.Context, path string, dest any) error {
	baseURL := strings.TrimSpace(s.app.Cfg.VehicleMonitor.BaseURL)
	if baseURL == "" {
		return fmt.Errorf("vehicleMonitor.baseUrl 未配置")
	}
	timeout := s.app.Cfg.Forest.Timeout
	if timeout <= 0 {
		timeout = 60000
	}
	client := &http.Client{Timeout: time.Duration(timeout) * time.Millisecond}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, strings.TrimRight(baseURL, "/")+path, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Connection", "close")
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("请求 %s 失败: %w", path, err)
	}
	defer func() { _ = resp.Body.Close() }()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("读取 %s 响应失败: %w", path, err)
	}
	if resp.StatusCode < 200 || resp.StatusCode > 299 {
		return fmt.Errorf("%s 返回 HTTP %d: %s", path, resp.StatusCode, limit(string(body), 200))
	}
	trimmed := bytes.TrimSpace(body)
	if len(trimmed) == 0 || string(trimmed) == "null" {
		return nil
	}
	if trimmed[0] == '[' {
		if err := json.Unmarshal(trimmed, dest); err != nil {
			return fmt.Errorf("解析 %s 列表失败: %w", path, err)
		}
		return nil
	}
	// 容错：部分部署会在列表外再包一层 {code,msg,data|rows}。
	var wrapped struct {
		Data json.RawMessage `json:"data"`
		Rows json.RawMessage `json:"rows"`
	}
	if err := json.Unmarshal(trimmed, &wrapped); err != nil {
		return fmt.Errorf("解析 %s 响应失败: %w", path, err)
	}
	payload := wrapped.Data
	if len(payload) == 0 || string(payload) == "null" {
		payload = wrapped.Rows
	}
	if len(payload) == 0 || string(payload) == "null" {
		return fmt.Errorf("%s 响应既不是数组也没有 data/rows: %s", path, limit(string(trimmed), 200))
	}
	if err := json.Unmarshal(payload, dest); err != nil {
		return fmt.Errorf("解析 %s 列表失败: %w", path, err)
	}
	return nil
}

// parseTimeValue 解析 Date 的文本形态（ISO / yyyy-MM-dd HH:mm:ss / 毫秒数字串）。
func parseTimeValue(value string) time.Time {
	value = strings.TrimSpace(value)
	if value == "" {
		return time.Time{}
	}
	if t, err := web.ParseDate(value); err == nil {
		return t
	}
	if n, err := strconv.ParseInt(value, 10, 64); err == nil {
		return time.UnixMilli(n)
	}
	return time.Time{}
}

func limit(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}
