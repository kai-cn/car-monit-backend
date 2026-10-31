// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CdcController.java
// JAVA 对照: com.ruoyi.base.service.cdc.DeadLetterQueueService / CdcSyncService / CdcConfig
// 类/职责: CDC 同步管理 —— 队列状态、死信/重试消息、手动重试、配置查询
// 对应 Go 文件: internal/modules/base/cdc.go
//
// DIFF: Java 用 Spring Data Redis（RedisTemplate<String,String>）存 cdc:retry:* / cdc:dead:*，
// Go 用 go-redis 裸客户端读写同样的键与纯文本 JSON。
// DIFF: CdcConfig 在 Java 里绑定 cdc.*（本仓库 application.yml 没有该段，全部取默认值）；
// Go 没有 cdc.* 配置，Kafka 三项尽量取 app.Cfg.Kafka，其余沿用 Java 默认值。
package base

import (
	"encoding/json"
	"strconv"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

const (
	cdcRetryKeyPrefix = "cdc:retry:"
	cdcDeadKeyPrefix  = "cdc:dead:"
)

// cdcKafkaConfig 对应 CdcConfig.KafkaConfig。
type cdcKafkaConfig struct {
	BootstrapServers   string `json:"bootstrapServers"`
	ConsumerGroupID    string `json:"consumerGroupId"`
	Topic              string `json:"topic"`
	AutoCommit         bool   `json:"autoCommit"`
	AutoCommitInterval int    `json:"autoCommitInterval"`
	SessionTimeout     int    `json:"sessionTimeout"`
	Concurrency        int    `json:"concurrency"`
}

// cdcEsSyncConfig 对应 CdcConfig.EsSyncConfig。
type cdcEsSyncConfig struct {
	Enabled       bool  `json:"enabled"`
	BatchSize     int   `json:"batchSize"`
	BatchInterval int64 `json:"batchInterval"`
	AsyncThreads  int   `json:"asyncThreads"`
}

// cdcRetryConfig 对应 CdcConfig.RetryConfig。
type cdcRetryConfig struct {
	MaxAttempts int     `json:"maxAttempts"`
	Interval    int64   `json:"interval"`
	Multiplier  float64 `json:"multiplier"`
	MaxInterval int64   `json:"maxInterval"`
}

// cdcConfig 对应 CdcConfig（@ConfigurationProperties(prefix = "cdc")）。
type cdcConfig struct {
	Kafka  cdcKafkaConfig  `json:"kafka"`
	EsSync cdcEsSyncConfig `json:"esSync"`
	Retry  cdcRetryConfig  `json:"retry"`
}

// loadCDCConfig 构造 CDC 配置。
//
// JAVA 对照: CdcConfig.java 的字段默认值。
// DIFF: 本仓库 application.yml 没有 cdc.* 段，Java 的 CdcConfig 因此全部取默认值；
// 这里也不读 kafka.*（否则 /base/cdc/status 会与 Java 不一致）。
func (h *handler) loadCDCConfig() cdcConfig {
	cfg := cdcConfig{
		Kafka: cdcKafkaConfig{
			BootstrapServers:   "localhost:9092",
			ConsumerGroupID:    "snapshot-flow-cdc-group",
			Topic:              "snapshot-flow-cdc",
			AutoCommit:         true,
			AutoCommitInterval: 1000,
			SessionTimeout:     30000,
			Concurrency:        3,
		},
		EsSync: cdcEsSyncConfig{Enabled: true, BatchSize: 500, BatchInterval: 5000, AsyncThreads: 2},
		Retry:  cdcRetryConfig{MaxAttempts: 3, Interval: 1000, Multiplier: 2.0, MaxInterval: 30000},
	}
	return cfg
}

// cdcQueueStatus 对应 getQueueStatus 的 5 个键。
// JAVA 对照: CdcController#getQueueStatus
func (h *handler) cdcQueueStatus(c *gin.Context) {
	cfg := h.loadCDCConfig()
	ctx := c.Request.Context()
	status := map[string]any{
		"retryQueueSize":      len(h.app.Cache.Keys(ctx, cdcRetryKeyPrefix+"*")),
		"deadLetterQueueSize": len(h.app.Cache.Keys(ctx, cdcDeadKeyPrefix+"*")),
		"kafkaTopic":          cfg.Kafka.Topic,
		"consumerGroupId":     cfg.Kafka.ConsumerGroupID,
		"maxRetryAttempts":    cfg.Retry.MaxAttempts,
	}
	web.JSON(c, web.SuccessData(status))
}

// cdcDeadLetters 对应 GET /dead-letters。
func (h *handler) cdcDeadLetters(c *gin.Context) {
	web.JSON(c, web.SuccessData(h.cdcMessages(c, cdcDeadKeyPrefix)))
}

// cdcRetryMessages 对应 GET /retry-messages。
func (h *handler) cdcRetryMessages(c *gin.Context) {
	web.JSON(c, web.SuccessData(h.cdcMessages(c, cdcRetryKeyPrefix)))
}

// cdcRetryOne 对应 POST /retry/{messageId}。
func (h *handler) cdcRetryOne(c *gin.Context) {
	messageID := c.Param("messageId")
	if h.cdcRetryMessage(c, messageID) {
		web.JSON(c, web.SuccessMsg("重试成功"))
		return
	}
	web.JSON(c, web.ErrorMsg("重试失败，消息不存在或处理失败"))
}

// cdcRetryAll 对应 POST /retry-all（恒返回成功文案）。
// JAVA 对照: CdcController#retryAllDeadMessages
func (h *handler) cdcRetryAll(c *gin.Context) {
	success := 0
	for _, message := range h.cdcMessages(c, cdcDeadKeyPrefix) {
		if h.cdcRetryMessage(c, cellText(message, "messageId")) {
			success++
		}
	}
	web.JSON(c, web.SuccessMsg("批量重试完成，成功 "+strconv.Itoa(success)+" 条"))
}

// cdcDeleteDeadLetter 对应 DELETE /dead-letters/{messageId}。
func (h *handler) cdcDeleteDeadLetter(c *gin.Context) {
	h.cdcRemove(c, cdcDeadKeyPrefix, c.Param("messageId"))
	web.JSON(c, web.SuccessMsg("删除成功"))
}

// cdcClearDeadLetters 对应 DELETE /dead-letters/clear（逐条删除，解析失败的会被漏下 —— 与 Java 一致）。
// JAVA 对照: CdcController#clearDeadLetterQueue
func (h *handler) cdcClearDeadLetters(c *gin.Context) {
	for _, message := range h.cdcMessages(c, cdcDeadKeyPrefix) {
		h.cdcRemove(c, cdcDeadKeyPrefix, cellText(message, "messageId"))
	}
	web.JSON(c, web.SuccessMsg("已清空死信队列"))
}

// cdcGetConfig 对应 GET /config。
func (h *handler) cdcGetConfig(c *gin.Context) {
	web.JSON(c, web.SuccessData(h.loadCDCConfig()))
}

// cdcMessages 对应 DeadLetterQueueService#getRetryMessages/#getDeadLetterMessages：
// keys(prefix*) -> GET -> JSON 解析，解析失败的丢弃。
func (h *handler) cdcMessages(c *gin.Context, prefix string) []map[string]any {
	ctx := c.Request.Context()
	out := make([]map[string]any, 0)
	for _, key := range h.app.Cache.Keys(ctx, prefix+"*") {
		raw, ok := h.app.Cache.GetString(ctx, key)
		if !ok {
			continue
		}
		var message map[string]any
		if err := json.Unmarshal([]byte(raw), &message); err != nil {
			h.app.Log.Error("【死信队列】解析消息失败", "key", key, "err", err)
			continue
		}
		out = append(out, message)
	}
	return out
}

// cdcRemove 对应 removeFromRetryQueue / removeFromDeadLetterQueue。
func (h *handler) cdcRemove(c *gin.Context, prefix, messageID string) {
	h.app.Cache.Delete(c.Request.Context(), prefix+isNull(messageID))
}

// cdcRetryMessage 对应 CdcSyncService#retryMessage：
// 找到死信 -> retryCount 置 0 -> 重新处理 -> 成功则移出死信队列。
func (h *handler) cdcRetryMessage(c *gin.Context, messageID string) bool {
	for _, message := range h.cdcMessages(c, cdcDeadKeyPrefix) {
		if cellText(message, "messageId") != messageID {
			continue
		}
		message["retryCount"] = 0
		if h.cdcProcess(message) {
			h.cdcRemove(c, cdcDeadKeyPrefix, messageID)
			return true
		}
		return false
	}
	h.app.Log.Warn("【CDC重试】未找到死信消息", "messageId", messageID)
	return false
}

// cdcProcess 对应 CdcSyncService#processCdcMessage。
//
// JAVA 对照: handleInsert/handleUpdate/handleDelete 里的 elasticsearchService 调用在
// Java 源码中是注释掉的，方法体只打日志并 return true。这里照抄（无外部副作用）。
func (h *handler) cdcProcess(message map[string]any) bool {
	operation := cellText(message, "operationType")
	switch operation {
	case "INSERT", "UPDATE", "DELETE":
		return true
	case "":
		// Java: switch(null) -> NPE -> 被 catch -> false
		h.app.Log.Error("【CDC处理】操作类型为空")
		return false
	default:
		h.app.Log.Warn("【CDC处理】未知操作类型", "operationType", operation)
		return true
	}
}
