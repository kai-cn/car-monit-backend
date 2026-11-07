// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/KafkaConfig.java:30-177
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/SnapshotFlowKafkaConsumerV2.java:44-200
// 类/职责: 批量消费 + 手动提交 + 死信队列 + 优雅退出
// 对应 Go 文件: internal/stream/kafka/consumer.go
//
// DIFF: Spring Kafka 的 @KafkaListener + 容器工厂由框架托管；Go 显式构造 Reader/Writer 并运行消费循环。
// DIFF: 手工确认 MANUAL_IMMEDIATE → handler 成功后才 CommitMessages；失败消息写入 DLQ 后仍提交。
// DIFF: max.poll.records=500 → 每次 ReadBatch 以 MaxBytes/MaxWait 聚合，单批上限由 BatchSize 截断。
//
// 状态: **未接线**。main 未启动消费者，仓库内也没有任何调用方；Go 版本的数据接入
// （MySQL 分表写入 + ES 索引 + 幂等键）本轮不交付，归属见 docs/MAPPING.md §4。
// 启用前置条件：补齐分表写入/ES 写入/幂等键三条链路并在 main 中显式启动，且完成对拍。
package kafka

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/segmentio/kafka-go"

	"car-monit-go/internal/config"
)

// Message 对应 ConsumerRecord<String,String> 的迁移视图。
type Message struct {
	Topic     string
	Partition int
	Offset    int64
	Key       string
	Value     string
	Time      time.Time
}

// BatchHandler 对应 @KafkaListener 方法体（批量）。
type BatchHandler func(ctx context.Context, msgs []Message) (failed []Message, err error)

type Consumer struct {
	reader  *kafka.Reader
	writer  *kafka.Writer // 死信队列生产者，可为 nil
	dlq     string
	handler BatchHandler
	batch   int
	log     *slog.Logger
}

// NewConsumer 按 kafka.consumer.* 配置构造消费者。
func NewConsumer(cfg *config.Config, topic, dlqTopic string, handler BatchHandler, log *slog.Logger) *Consumer {
	startOffset := kafka.FirstOffset
	if cfg.Kafka.Consumer.AutoOffsetReset == "latest" {
		startOffset = kafka.LastOffset
	}
	batch := cfg.Kafka.Consumer.MaxPollRecords
	if batch <= 0 {
		batch = 500
	}
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        cfg.Kafka.BootstrapServers,
		GroupID:        cfg.Kafka.Consumer.GroupID,
		Topic:          topic,
		MinBytes:       1,
		MaxBytes:       50 << 20, // fetch.max.bytes=52428800
		MaxWait:        time.Second,
		CommitInterval: 0, // 手动提交
		StartOffset:    startOffset,
		Logger:         kafka.LoggerFunc(func(msg string, args ...any) { log.Debug("kafka", "msg", fmt.Sprintf(msg, args...)) }),
		ErrorLogger:    kafka.LoggerFunc(func(msg string, args ...any) { log.Warn("kafka", "msg", fmt.Sprintf(msg, args...)) }),
	})
	c := &Consumer{reader: r, handler: handler, batch: batch, dlq: dlqTopic, log: log}
	if dlqTopic != "" {
		c.writer = &kafka.Writer{
			Addr:                   kafka.TCP(cfg.Kafka.BootstrapServers...),
			Topic:                  dlqTopic,
			Balancer:               &kafka.LeastBytes{},
			AllowAutoTopicCreation: true,
		}
	}
	return c
}

// Run 对应 KafkaListener 容器：阻塞消费直至 ctx 取消。
func (c *Consumer) Run(ctx context.Context) error {
	defer c.Close()
	for {
		if ctx.Err() != nil {
			return nil
		}
		batch, err := c.readBatch(ctx)
		if err != nil {
			if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
				return nil
			}
			c.log.Error("Kafka 拉取失败", "topic", c.reader.Config().Topic, "err", err)
			continue
		}
		if len(batch) == 0 {
			continue
		}
		failed, err := c.handler(ctx, batch)
		if err != nil {
			c.log.Error("Kafka 批处理失败，消息进入死信队列", "err", err)
			failed = batch
		}
		if len(failed) > 0 {
			c.sendDLQ(ctx, failed)
		}
		raw := make([]kafka.Message, 0, len(batch))
		for _, m := range batch {
			raw = append(raw, toKafkaMessage(m))
		}
		if err := c.reader.CommitMessages(ctx, raw...); err != nil {
			c.log.Error("Kafka 提交 offset 失败", "err", err)
		}
	}
}

// readBatch 最多读取 batch 条，避免单批过大；超时视为空批。
func (c *Consumer) readBatch(ctx context.Context) ([]Message, error) {
	out := make([]Message, 0, c.batch)
	for len(out) < c.batch {
		readCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
		raw, err := c.reader.FetchMessage(readCtx)
		cancel()
		if err != nil {
			if len(out) > 0 {
				return out, nil
			}
			if errors.Is(err, context.DeadlineExceeded) {
				return out, nil
			}
			return nil, err
		}
		out = append(out, fromKafkaMessage(raw))
	}
	return out, nil
}

// sendDLQ 对应 KafkaConfig 中的死信发送（acks=all + 幂等）。
func (c *Consumer) sendDLQ(ctx context.Context, msgs []Message) {
	if c.writer == nil {
		return
	}
	wm := make([]kafka.Message, 0, len(msgs))
	for _, m := range msgs {
		wm = append(wm, kafka.Message{Key: []byte(m.Key), Value: []byte(m.Value)})
	}
	if err := c.writer.WriteMessages(ctx, wm...); err != nil {
		c.log.Error("写入死信队列失败", "topic", c.dlq, "err", err)
	}
}

// Close 关闭 reader/writer。
func (c *Consumer) Close() {
	if c.reader != nil {
		_ = c.reader.Close()
	}
	if c.writer != nil {
		_ = c.writer.Close()
	}
}

func fromKafkaMessage(m kafka.Message) Message {
	return Message{
		Topic:     m.Topic,
		Partition: m.Partition,
		Offset:    m.Offset,
		Key:       string(m.Key),
		Value:     string(m.Value),
		Time:      m.Time,
	}
}

func toKafkaMessage(m Message) kafka.Message {
	return kafka.Message{
		Topic:     m.Topic,
		Partition: m.Partition,
		Offset:    m.Offset,
		Key:       []byte(m.Key),
		Value:     []byte(m.Value),
		Time:      m.Time,
	}
}
