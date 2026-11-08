#pragma once
// 门架抓拍流水 Kafka 消费链路（对应 Java SnapshotFlowKafkaConsumerV2）。
//
// 逐条对齐 Java 的语义：
//   * 批量消费（max.poll.records=500）、MANUAL_IMMEDIATE（处理完才提交位点）
//   * 消息体 {"operationType":"INSERT|UPDATE|DELETE","data":{...}}，以 bigId 为幂等键
//   * 幂等：Redis `snapshot:flow:idempotent_<bigId>` = 1，TTL 86400s（SET NX EX，原子）
//   * INSERT/UPDATE → 按 snapshottime 月份写分表 + ES bulk；DELETE → 广播删除
//   * 单条失败 → 本地重试 3 次（每次间隔 1s）→ 仍失败发 DLQ
//   * DLQ：{"originalTopic","partition","offset","timestamp","reason","value"}
//
// 与 Java 的一处**有意收紧**（已在 COMPATIBILITY 记录）：Java 的 batchSaveData 把 MySQL
// 异常吞掉后照常 ack，会造成静默丢消息；这里 MySQL 写失败 ⇒ 不提交位点，Kafka 重投。
#include <atomic>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"
#include "cm/framework/kafka/KafkaClient.hpp"

namespace cm::base::kafka {

class SnapshotFlowKafkaConsumer {
public:
    static SnapshotFlowKafkaConsumer& instance();

    void configure(const cm::kafka::KafkaConfig& cfg);
    /** 启动 concurrency 个消费线程（对应 kafka.listener.concurrency=3） */
    void start();
    void stop();
    bool running() const { return running_.load(); }

    struct BatchOutcome {
        int parsed{0};    // 收到的消息数
        int success{0};   // 成功入库/删除
        int skipped{0};   // 幂等命中
        int failed{0};    // 失败并进入 DLQ
        int dlq{0};       // 实际发出的 DLQ 条数
        bool commit{true};  // false 表示不允许提交位点（等待重投）
    };

    /** 处理一批消息（不涉及 Kafka 网络，便于单测/验收工具直接调用） */
    BatchOutcome processBatch(const std::vector<cm::kafka::ConsumedRecord>& records);

    /** 处理单条：返回 false 表示失败（调用方负责重试/DLQ）。
     *  skipped 非空时回传"幂等命中、直接跳过"（Java 里同样返回 true）。 */
    bool processSingle(const cm::kafka::ConsumedRecord& record, std::vector<Json>& toSave,
                       std::vector<Json>& esDocs, std::string& processedId,
                       bool* skipped = nullptr);

    /** 发送死信（对应 sendToDLQ） */
    bool sendToDlq(const cm::kafka::ConsumedRecord& record, const std::string& reason);

    /** 幂等（对应 IdempotentUtil.checkAndSet / remove） */
    bool checkAndSetIdempotent(const std::string& key);
    void removeIdempotent(const std::string& key);

    long long successCount() const { return success_.load(); }
    long long failCount() const { return fail_.load(); }
    long long retryCount() const { return retry_.load(); }

private:
    SnapshotFlowKafkaConsumer() = default;
    void runLoop(int index);
    bool saveBatch(const std::vector<Json>& toSave, const std::vector<Json>& esDocs, std::string& err);

    cm::kafka::KafkaConfig cfg_;
    std::atomic<bool> running_{false};
    std::vector<std::thread> threads_;
    std::mutex dlqMu_;
    std::unique_ptr<cm::kafka::KafkaProducer> dlqProducer_;
    std::atomic<long long> success_{0};
    std::atomic<long long> fail_{0};
    std::atomic<long long> retry_{0};
};

/** 构造 ES 文档（对应 BeanUtils.copyProperties(data, SnapshotFlowDocument) + fastjson2 序列化） */
Json snapshotFlowEsDocument(const Json& row);

} // namespace cm::base::kafka
