#pragma once
// 最小 Kafka 客户端（消费者 + DLQ 生产者）。
//
// 对应 Java：
//   * KafkaConfig.consumerFactory / kafkaListenerContainerFactory（batch + MANUAL_IMMEDIATE）
//   * SnapshotFlowKafkaConsumerV2（消费/重试/死信）
//   * KafkaTemplate<String,String>（仅用于发送 DLQ）
//
// 选择非 flexible 协议版本（Metadata v1 / JoinGroup v2 / SyncGroup v1 / Heartbeat v1 /
// OffsetFetch v3 / OffsetCommit v2 / ListOffsets v1 / Fetch v4 / Produce v3），
// Kafka 0.10~2.8 全支持，没有 tagged fields，报文可逐字节核对。
#include <chrono>
#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "cm/framework/kafka/KafkaCodec.hpp"

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
    int heartbeatIntervalMs{20000}; // 同步心跳（Java 3s，这里在两次 poll 之间发）
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

/** 单条 TCP 连接，请求/响应同步往返（header v1） */
class KafkaConnection {
public:
    KafkaConnection() = default;
    ~KafkaConnection();
    KafkaConnection(const KafkaConnection&) = delete;
    KafkaConnection& operator=(const KafkaConnection&) = delete;

    bool connect(const std::string& clientId, const BrokerAddr& addr, int connectTimeoutMs,
                 int socketTimeoutMs, std::string& err);
    void close();
    bool isOpen() const { return fd_ >= 0; }

    /** 发送请求并读回完整响应体（去掉 4 字节长度前缀） */
    bool request(int16_t apiKey, int16_t apiVersion, const std::string& body, std::string& payload,
                 std::string& err);

    const BrokerAddr& addr() const { return addr_; }

private:
    long long fd_{-1};
    BrokerAddr addr_;
    std::string clientId_{"car-monit-cpp"};
    int32_t correlation_{0};
};

/**
 * 消费者：单 topic、单 group、range 分配、手动提交。
 * 线程不安全（每个消费线程一个实例，与 Java concurrency=3 一致）。
 */
class KafkaConsumer {
public:
    explicit KafkaConsumer(KafkaConfig cfg);
    ~KafkaConsumer();

    /** 连接 broker + 加入消费组 + 拉取已提交位点。失败可重试调用。 */
    bool open(std::string& err);

    /** 拉取一批（最多 maxPollRecords 条）；返回 false 表示本次无数据/需重建连接 */
    bool poll(std::vector<ConsumedRecord>& out, int maxWaitMs, std::string& err);

    /** 提交上次 poll 返回记录的下一个位点（MANUAL_IMMEDIATE 语义） */
    bool commit(std::string& err);

    void close();

    bool joined() const { return joined_; }
    const KafkaConfig& config() const { return cfg_; }

private:
    bool ensureCoordinator(std::string& err);
    bool refreshMetadata(std::string& err);
    bool joinGroup(std::string& err);
    bool syncGroup(std::string& err);
    bool heartbeat(std::string& err);
    bool fetchOffsets(std::string& err);
    bool listOffsets(std::string& err);
    bool runFetch(int maxWaitMs, std::string& err);
    BrokerAddr firstBootstrap() const;
    void resetSession();

    KafkaConfig cfg_;
    std::unique_ptr<KafkaConnection> coord_;
    std::unique_ptr<KafkaConnection> fetchConn_;
    BrokerAddr coordAddr_;
    BrokerAddr leaderAddr_;
    std::string memberId_;
    std::string leaderId_;
    int32_t generation_{-1};
    std::vector<int32_t> partitions_;
    std::map<int32_t, int64_t> nextOffset_;
    std::map<int32_t, int64_t> pendingCommit_;
    std::vector<ConsumedRecord> pending_;
    std::chrono::steady_clock::time_point lastHeartbeat_{};
    bool joined_{false};
};

/** 仅用于 DLQ：acks=all、retries=3、无 key */
class KafkaProducer {
public:
    explicit KafkaProducer(KafkaConfig cfg);
    ~KafkaProducer();

    bool send(const std::string& topic, const std::string& value, std::string& err);
    void close();

private:
    bool ensureLeader(const std::string& topic, std::string& err);

    KafkaConfig cfg_;
    std::unique_ptr<KafkaConnection> conn_;
    BrokerAddr leader_;
    std::string topic_;
};

/** "host1:port1,host2:port2" -> 列表 */
std::vector<BrokerAddr> parseBootstrapServers(const std::string& text);

} // namespace cm::kafka
