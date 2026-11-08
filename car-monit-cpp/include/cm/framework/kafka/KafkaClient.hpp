#pragma once
// Kafka 客户端（传输层 = librdkafka，C API）。
//
// 对应 Java：
//   * KafkaConfig.consumerFactory / kafkaListenerContainerFactory（batch + MANUAL_IMMEDIATE）
//   * SnapshotFlowKafkaConsumerV2（消费/重试/死信）
//   * KafkaTemplate<String,String>（仅用于发送 DLQ）
//
// 这里只保留“配置 + 消费者/生产者门面”，协议、组协调、再平衡、压缩、CRC 全部交给
// librdkafka；业务语义（批量 500、手动提交、幂等、重试 3×1s、DLQ、写库失败不提交）
// 仍在 cm::base::kafka::SnapshotFlowKafkaConsumer。
//
// 与 Java 配置的逐项对应（见 KafkaConfig 注释）：
//   enable.auto.commit=false + enable.auto.offset.store=false ⇒ MANUAL_IMMEDIATE
//   max.poll.records=500 由 poll() 每次最多返回 500 条实现
//   max.poll.interval.ms / session.timeout.ms / fetch.max.bytes 直接透传
#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace cm::kafka {

struct KafkaConfig {
    /** 逗号分隔的 host:port 列表（对应 kafka.bootstrap-servers） */
    std::string bootstrapServers{"127.0.0.1:9092"};
    std::string clientId{"car-monit-cpp"};
    /** 对应 kafka.consumer.group-id */
    std::string groupId{"snapshot-flow-consumer-group"};
    /** 对应 kafka.topic.snapshot-flow / snapshot-flow-dlq */
    std::string topic{"ods-rt-szdn-snapshot-flow"};
    std::string dlqTopic{"ods-rt-szdn-snapshot-flow-dlq"};

    int sessionTimeoutMs{60000};    // kafka.consumer.session-timeout-ms
    int fetchMaxBytes{52428800};    // kafka.consumer.fetch-max-bytes
    int maxPollRecords{500};        // kafka.consumer.max-poll-records
    int maxPollIntervalMs{300000};  // kafka.consumer.max-poll-interval-ms
    int connectTimeoutMs{5000};
    int socketTimeoutMs{60000};
    bool fromBeginning{true};       // auto-offset-reset=earliest
    int concurrency{3};             // kafka.listener.concurrency

    // ---- 业务侧（SnapshotFlowKafkaConsumerV2 / IdempotentUtil）----
    std::string idempotentPrefix{"snapshot:flow:idempotent_"};
    int idempotentTtlSeconds{86400};
};

struct BrokerAddr {
    std::string host;
    int port{0};
    std::string toString() const { return host + ":" + std::to_string(port); }
};

struct ConsumedRecord {
    std::string key;
    bool hasKey{false};
    std::string value;
    int32_t partition{0};
    int64_t offset{0};
    int64_t timestamp{0};
};

/**
 * 消费者：单 topic、单 group、手动提交。
 * 线程不安全（每个消费线程一个实例，与 Java concurrency=3 一致）。
 */
class KafkaConsumer {
public:
    explicit KafkaConsumer(KafkaConfig cfg);
    ~KafkaConsumer();
    KafkaConsumer(const KafkaConsumer&) = delete;
    KafkaConsumer& operator=(const KafkaConsumer&) = delete;

    /** 创建消费者 + 订阅 + 等待首次分区分配。失败可重试调用。 */
    bool open(std::string& err);

    /** 拉取一批（最多 maxPollRecords 条）；返回 false 表示需要重建消费者 */
    bool poll(std::vector<ConsumedRecord>& out, int maxWaitMs, std::string& err);

    /** 提交上次 poll 返回记录的下一个位点（MANUAL_IMMEDIATE 语义） */
    bool commit(std::string& err);

    /** 查询当前分组的已提交位点（partition -> 下一条位点）；无提交的分区不返回 */
    bool committedOffsets(std::map<int32_t, int64_t>& out, std::string& err);

    /** 把一批消息回退到各分区的最小位点（写库失败时用于立即重投，不丢消息） */
    void rewind(const std::vector<ConsumedRecord>& records);

    void close();

    bool joined() const;
    const KafkaConfig& config() const { return cfg_; }

private:
    struct Impl;
    KafkaConfig cfg_;
    std::unique_ptr<Impl> impl_;
};

/** 仅用于 DLQ：acks=all、enable.idempotence=true、retries=3 */
class KafkaProducer {
public:
    /** 定义在 .cpp；投递回调需要访问，故在 public 段前置声明 */
    struct Impl;
    explicit KafkaProducer(KafkaConfig cfg);
    ~KafkaProducer();
    KafkaProducer(const KafkaProducer&) = delete;
    KafkaProducer& operator=(const KafkaProducer&) = delete;

    bool send(const std::string& topic, const std::string& value, std::string& err);
    void close();

private:
    KafkaConfig cfg_;
    std::unique_ptr<Impl> impl_;
};

/** "host1:port1,host2:port2" -> 列表（配置校验/日志用） */
std::vector<BrokerAddr> parseBootstrapServers(const std::string& text);

} // namespace cm::kafka
