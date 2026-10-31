// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/elasticsearch/service/SnapshotFlowElasticsearchService.java:48-200
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/elasticsearch/document/SnapshotFlowDocument.java
// 类/职责: Elasticsearch 写入与检索（REST/JSON 方式，无需官方 SDK）
// 对应 Go 文件: internal/stream/es/client.go
//
// DIFF: Java 使用 RestHighLevelClient + QueryBuilders；Go 直接调用 _doc/_bulk/_search REST API，
// 查询 DSL 由调用方传入（模块内按 Java 查询条件构造），响应返回原始命中文档。
// DIFF: 未实现 HTTPS/账号认证（application.yml 未配置）；如启用安全集群，在此扩展 Transport。
package es

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"car-monit-go/internal/config"
)

type Client struct {
	base    string
	index   string
	enabled bool
	http    *http.Client
}

// New 对应 RestHighLevelClient Bean 的构造。
func New(cfg *config.Config) *Client {
	return &Client{
		base:    fmt.Sprintf("http://%s:%d", cfg.Elasticsearch.Host, cfg.Elasticsearch.Port),
		index:   cfg.Elasticsearch.Index.SnapshotFlow,
		enabled: cfg.Elasticsearch.Enabled,
		http:    &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *Client) Enabled() bool { return c != nil && c.enabled }

// Index 对应 saveOrUpdate：以 bigId 为文档 ID，实现幂等覆盖。
func (c *Client) Index(ctx context.Context, id string, doc any) error {
	if !c.Enabled() {
		return nil
	}
	body, err := json.Marshal(doc)
	if err != nil {
		return err
	}
	url := fmt.Sprintf("%s/%s/_doc/%s", c.base, c.index, urlPathEscape(id))
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, url, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	return c.do(req)
}

// BulkIndex 对应 batchSave：NDJSON _bulk，id 为 bigId。
func (c *Client) BulkIndex(ctx context.Context, docs map[string]any) error {
	if !c.Enabled() || len(docs) == 0 {
		return nil
	}
	var buf bytes.Buffer
	for id, doc := range docs {
		meta, _ := json.Marshal(map[string]any{"index": map[string]any{"_index": c.index, "_id": id}})
		data, err := json.Marshal(doc)
		if err != nil {
			return err
		}
		buf.Write(meta)
		buf.WriteByte('\n')
		buf.Write(data)
		buf.WriteByte('\n')
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.base+"/_bulk", &buf)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/x-ndjson")
	return c.do(req)
}

// Delete 对应按文档 ID 删除。
func (c *Client) Delete(ctx context.Context, id string) error {
	if !c.Enabled() {
		return nil
	}
	url := fmt.Sprintf("%s/%s/_doc/%s", c.base, c.index, urlPathEscape(id))
	req, err := http.NewRequestWithContext(ctx, http.MethodDelete, url, nil)
	if err != nil {
		return err
	}
	return c.do(req)
}

// Search 对应 searchPage 的检索部分：返回总数与原始 _source 列表。
func (c *Client) Search(ctx context.Context, query any) (int64, []json.RawMessage, error) {
	if !c.Enabled() {
		return 0, nil, nil
	}
	body, err := json.Marshal(query)
	if err != nil {
		return 0, nil, err
	}
	url := fmt.Sprintf("%s/%s/_search", c.base, c.index)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return 0, nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.http.Do(req)
	if err != nil {
		return 0, nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		msg, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return 0, nil, fmt.Errorf("es search %d: %s", resp.StatusCode, string(msg))
	}
	var out struct {
		Hits struct {
			Total struct {
				Value int64 `json:"value"`
			} `json:"total"`
			Hits []struct {
				Source json.RawMessage `json:"_source"`
			} `json:"hits"`
		} `json:"hits"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return 0, nil, err
	}
	hits := make([]json.RawMessage, 0, len(out.Hits.Hits))
	for _, h := range out.Hits.Hits {
		hits = append(hits, h.Source)
	}
	return out.Hits.Total.Value, hits, nil
}

// urlPathEscape 对文档 ID 做路径转义，避免 "../" 改变请求路径。
func urlPathEscape(id string) string {
	return url.PathEscape(strings.TrimSpace(id))
}

func (c *Client) do(req *http.Request) error {
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		msg, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return fmt.Errorf("es %s %s: %d %s", req.Method, req.URL.Path, resp.StatusCode, string(msg))
	}
	return nil
}
