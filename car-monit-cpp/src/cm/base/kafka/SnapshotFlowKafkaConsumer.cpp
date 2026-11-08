#include "cm/base/kafka/SnapshotFlowKafkaConsumer.hpp"

#include <chrono>
#include <thread>

#include "cm/base/repository/SnapshotFlowRepository.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/framework/es/EsClient.hpp"
#include "cm/framework/redis/RedisClient.hpp"

namespace cm::base::kafka {
namespace {

constexpr int kMaxRetryTimes = 3;          // Java MAX_RETRY_TIMES
constexpr int kRetryIntervalMs = 1000;     // Java Thread.sleep(1000)

long long nowMillis() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

/** ISO/日期串 -> epoch 毫秒；失败原样返回文本 */
Json normalizeDateField(const Json& v) {
    if (v.is_number_integer()) return v;
    if (v.is_string()) {
        auto tp = cm::utils::DateUtils::parseDate(v.get<std::string>());
        if (tp) return cm::utils::DateUtils::toMillis(*tp);
    }
    return v;
}

} // namespace

SnapshotFlowKafkaConsumer& SnapshotFlowKafkaConsumer::instance() {
    static SnapshotFlowKafkaConsumer c;
    return c;
}

void SnapshotFlowKafkaConsumer::configure(const cm::kafka::KafkaConfig& cfg) { cfg_ = cfg; }

Json snapshotFlowEsDocument(const Json& row) {
    // SnapshotFlowDocument 的字段集（按 Java 声明序；null 省略，日期输出 epoch 毫秒）
    static const char* kFields[] = {
        "bigId",          "datasource",     "cameratype",      "deviceid",
        "gantrycode",     "gantryname",     "roadcode",        "roadname",
        "sectioncode",    "sectionname",    "tollcode",        "tollname",
        "orgcode",        "orgname",        "direction",       "hexcode",
        "pileno",         "lon",            "lat",             "deviceip",
        "siteid",         "laneid",         "snapshottimeunix", "snapshottime",
        "receivedtimeunix", "receivedtime", "platenumber",     "platecolor",
        "platecolorcode", "platetype",      "platetypecode",   "plateconfidence",
        "carbrand",       "carcolor",       "carcolorcode",    "cartype",
        "cartypecode",    "cardirection",   "snappicturepath", "loadtime",
        "gradelevel",     "datauuid",       "reserve3"};
    Json doc = Json::object();
    if (!row.is_object()) return doc;
    for (const char* f : kFields) {
        if (!row.contains(f) || row[f].is_null()) continue;
        if (std::string(f) == "snapshottime" || std::string(f) == "receivedtime" ||
            std::string(f) == "loadtime") {
            doc[f] = normalizeDateField(row[f]);
        } else {
            doc[f] = row[f];
        }
    }
    return doc;
}

bool SnapshotFlowKafkaConsumer::checkAndSetIdempotent(const std::string& key) {
    const std::string rk = cfg_.idempotentPrefix + key;
    // 对应 RedisCache.setCacheObjectIfAbsent(key, "1", 86400, SECONDS)：SET NX EX 原子
    const auto reply = cm::redis::RedisCache::instance().client().command(
        {"SET", rk, "1", "NX", "EX", std::to_string(cfg_.idempotentTtlSeconds)});
    return reply.has_value() && !reply->empty() && (*reply)[0] != '-';
}

void SnapshotFlowKafkaConsumer::removeIdempotent(const std::string& key) {
    const std::string rk = cfg_.idempotentPrefix + key;
    cm::redis::RedisCache::instance().client().del({rk});
}

bool SnapshotFlowKafkaConsumer::sendToDlq(const cm::kafka::ConsumedRecord& record,
                                          const std::string& reason) {
    std::lock_guard<std::mutex> lk(dlqMu_);
    if (!dlqProducer_) {
        dlqProducer_ = std::make_unique<cm::kafka::KafkaProducer>(cfg_);
    }
    Json msg = Json::object();
    msg["originalTopic"] = cfg_.topic;
    msg["partition"] = record.partition;
    msg["offset"] = record.offset;
    msg["timestamp"] = record.timestamp;
    msg["reason"] = reason;
    msg["value"] = record.value;
    std::string err;
    if (!dlqProducer_->send(cfg_.dlqTopic, msg.dump(), err)) {
        LOG_ERROR("SnapshotFlowKafka", "死信队列发送失败 offset=" + std::to_string(record.offset) +
                                           " err=" + err);
        return false;
    }
    LOG_WARN("SnapshotFlowKafka", "发送死信队列 offset=" + std::to_string(record.offset) +
                                      " reason=" + reason);
    return true;
}

bool SnapshotFlowKafkaConsumer::processSingle(const cm::kafka::ConsumedRecord& record,
                                              std::vector<Json>& toSave,
                                              std::vector<Json>& esDocs,
                                              std::string& processedId, bool* skipped) {
    Json data;
    bool hasData = false;
    try {
        if (!Json::accept(record.value)) {
            throw std::runtime_error("invalid json");
        }
        const Json msg = Json::parse(record.value);
        std::string operationType;
        if (msg.is_object()) {
            if (msg.contains("operationType") && msg["operationType"].is_string()) {
                operationType = msg["operationType"].get<std::string>();
            }
            if (msg.contains("data") && msg["data"].is_object()) {
                data = msg["data"];
                hasData = true;
            }
        }
        const std::optional<std::string> bigId =
            hasData && data.contains("bigId") && data["bigId"].is_string()
                ? std::optional<std::string>(data["bigId"].get<std::string>())
                : std::nullopt;
        if (!hasData || !bigId || bigId->empty()) {
            LOG_WARN("SnapshotFlowKafka", "数据校验失败：消息为空或缺少bigId offset=" +
                                              std::to_string(record.offset));
            sendToDlq(record, "数据为空或缺少bigId");
            return false;
        }
        const std::string idempotentKey = *bigId;
        if (!checkAndSetIdempotent(idempotentKey)) {
            LOG_INFO("SnapshotFlowKafka", "幂等检查通过：消息已处理 bigId=" + idempotentKey +
                                              " offset=" + std::to_string(record.offset));
            if (skipped) *skipped = true;
            return true;
        }
        processedId = idempotentKey;

        if (operationType == "INSERT" || operationType == "UPDATE") {
            toSave.push_back(data);
            esDocs.push_back(snapshotFlowEsDocument(data));
        } else if (operationType == "DELETE") {
            cm::base::repository::SnapshotFlowRepository::instance().deleteById(idempotentKey);
        }
        ++success_;
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("SnapshotFlowKafka", "单条处理失败 offset=" + std::to_string(record.offset) +
                                           " err=" + e.what());
        removeIdempotent(hasData && data.contains("bigId") && data["bigId"].is_string()
                             ? data["bigId"].get<std::string>()
                             : "unknown-" + std::to_string(record.offset));
        return false;
    }
}

bool SnapshotFlowKafkaConsumer::saveBatch(const std::vector<Json>& toSave,
                                          const std::vector<Json>& esDocs, std::string& err) {
    if (toSave.empty() && esDocs.empty()) return true;

    bool ok = true;
    if (!toSave.empty()) {
        int inserted = 0;
        std::string dbErr;
        if (!cm::base::repository::SnapshotFlowRepository::instance().insertGroupedByMonth(
                toSave, &inserted, dbErr)) {
            // 与 Java 不同：写库失败不吞掉（Java 会照常 ack ⇒ 静默丢消息）
            LOG_ERROR("SnapshotFlowKafka", "MySQL 分表保存失败: " + dbErr);
            err = dbErr;
            ok = false;
        } else {
            LOG_INFO("SnapshotFlowKafka", "MySQL 分表保存成功 数量=" + std::to_string(inserted));
        }
    }
    if (ok && !esDocs.empty() && cm::es::EsClient::instance().enabled()) {
        std::vector<std::pair<std::string, std::string>> docs;
        docs.reserve(esDocs.size());
        for (const auto& d : esDocs) {
            const std::string id = d.contains("bigId") && d["bigId"].is_string()
                                       ? d["bigId"].get<std::string>()
                                       : std::string();
            if (id.empty()) continue;
            docs.emplace_back(id, d.dump());
        }
        std::string esErr;
        if (!cm::es::EsClient::instance().bulkIndex(docs, esErr)) {
            // ES 是旁路索引：Java 侧也是记日志后继续
            LOG_WARN("SnapshotFlowKafka", "ES 批量保存失败（不影响位点提交）: " + esErr);
        } else {
            LOG_INFO("SnapshotFlowKafka", "ES 保存成功 数量=" + std::to_string(docs.size()));
        }
    }
    return ok;
}

SnapshotFlowKafkaConsumer::BatchOutcome SnapshotFlowKafkaConsumer::processBatch(
    const std::vector<cm::kafka::ConsumedRecord>& records) {
    BatchOutcome out;
    out.parsed = static_cast<int>(records.size());
    std::vector<Json> toSave;
    std::vector<Json> esDocs;
    std::vector<std::string> processedIds;
    std::vector<cm::kafka::ConsumedRecord> failed;

    for (const auto& rec : records) {
        std::string processedId;
        bool processed = false;
        bool skipped = false;
        try {
            processed = processSingle(rec, toSave, esDocs, processedId, &skipped);
        } catch (const std::exception& e) {
            LOG_ERROR("SnapshotFlowKafka", "单条处理异常 offset=" + std::to_string(rec.offset) +
                                               " err=" + e.what());
            processed = false;
        }
        if (!processedId.empty()) processedIds.push_back(processedId);
        if (processed) {
            ++out.success;
            if (skipped) ++out.skipped;
        } else {
            failed.push_back(rec);
            ++out.failed;
        }
    }

    if (!toSave.empty() || !esDocs.empty()) {
        std::string err;
        if (!saveBatch(toSave, esDocs, err)) {
            // 回滚幂等标记并拒绝提交位点，让 Kafka 重投（不丢消息）
            for (const auto& id : processedIds) removeIdempotent(id);
            ++fail_;
            out.commit = false;
            return out;
        }
    }

    // handleFailedRecords：本地重试 3 次（间隔 1s）→ 仍失败发 DLQ
    for (const auto& rec : failed) {
        bool retryOk = false;
        for (int i = 1; i <= kMaxRetryTimes && !retryOk; ++i) {
            ++retry_;
            LOG_WARN("SnapshotFlowKafka", "重试处理 第" + std::to_string(i) + "次 offset=" +
                                              std::to_string(rec.offset));
            std::this_thread::sleep_for(std::chrono::milliseconds(kRetryIntervalMs));
            std::vector<Json> tempToSave;
            std::vector<Json> tempEsDocs;
            std::string tempId;
            try {
                if (processSingle(rec, tempToSave, tempEsDocs, tempId)) {
                    std::string err;
                    if (tempToSave.empty() || saveBatch(tempToSave, tempEsDocs, err)) {
                        retryOk = true;
                    }
                }
            } catch (const std::exception& e) {
                LOG_ERROR("SnapshotFlowKafka", "重试异常 第" + std::to_string(i) +
                                                   "次 offset=" + std::to_string(rec.offset) +
                                                   " err=" + e.what());
            }
        }
        if (!retryOk) {
            if (sendToDlq(rec, "重试失败")) ++out.dlq;
            ++fail_;
        } else {
            --out.failed;
            ++out.success;
        }
    }
    return out;
}

void SnapshotFlowKafkaConsumer::start() {
    if (running_.exchange(true)) return;
    LOG_INFO("SnapshotFlowKafka", "启动消费线程 数量=" + std::to_string(cfg_.concurrency) +
                                      " topic=" + cfg_.topic + " group=" + cfg_.groupId);
    for (int i = 0; i < std::max(1, cfg_.concurrency); ++i) {
        threads_.emplace_back([this, i] { runLoop(i); });
    }
}

void SnapshotFlowKafkaConsumer::stop() {
    if (!running_.exchange(false)) return;
    for (auto& t : threads_) {
        if (t.joinable()) t.join();
    }
    threads_.clear();
    std::lock_guard<std::mutex> lk(dlqMu_);
    if (dlqProducer_) {
        dlqProducer_->close();
        dlqProducer_.reset();
    }
    LOG_INFO("SnapshotFlowKafka", "消费线程已停止");
}

void SnapshotFlowKafkaConsumer::runLoop(int index) {
    while (running_.load()) {
        cm::kafka::KafkaConsumer consumer(cfg_);
        std::string err;
        if (!consumer.open(err)) {
            LOG_WARN("SnapshotFlowKafka", "消费者[" + std::to_string(index) +
                                              "] 连接失败: " + err);
            std::this_thread::sleep_for(std::chrono::seconds(2));
            continue;
        }
        while (running_.load()) {
            std::vector<cm::kafka::ConsumedRecord> batch;
            if (!consumer.poll(batch, 500, err)) {
                LOG_WARN("SnapshotFlowKafka", "消费者[" + std::to_string(index) +
                                                  "] 拉取失败: " + err);
                break;
            }
            if (batch.empty()) continue;
            BatchOutcome outcome = processBatch(batch);
            if (!outcome.commit) {
                // 位点不提交：关掉连接重新入组，OffsetFetch 会回到上次提交的位置重投
                LOG_WARN("SnapshotFlowKafka", "批次处理失败，不提交位点，等待重投");
                std::this_thread::sleep_for(std::chrono::seconds(1));
                break;
            }
            if (!consumer.commit(err)) {
                LOG_WARN("SnapshotFlowKafka", "提交位点失败: " + err);
                break;
            }
            LOG_INFO("SnapshotFlowKafka", "批次完成 线程=" + std::to_string(index) +
                                              " 批次=" + std::to_string(outcome.parsed) +
                                              " 成功=" + std::to_string(outcome.success) +
                                              " 跳过=" + std::to_string(outcome.skipped) +
                                              " 失败=" + std::to_string(outcome.failed));
        }
        consumer.close();
        if (running_.load()) std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

} // namespace cm::base::kafka
