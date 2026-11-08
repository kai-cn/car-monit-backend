#include "cm/framework/kafka/KafkaClient.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstring>
#include <map>

#include <librdkafka/rdkafka.h>

#include "cm/common/utils/Logger.hpp"

namespace cm::kafka {
namespace {

int64_t nowMillis() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

std::string errText(const std::string& what, rd_kafka_resp_err_t err) {
    return what + ": " + rd_kafka_err2str(err);
}

/** 设置一个配置项；失败时回填 err 并返回 false（不销毁 conf） */
bool setConf(rd_kafka_conf_t* conf, const char* name, const std::string& value, std::string& err) {
    char errbuf[512];
    if (rd_kafka_conf_set(conf, name, value.c_str(), errbuf, sizeof(errbuf)) != RD_KAFKA_CONF_OK) {
        err = std::string("kafka 配置 ") + name + "=" + value + " 失败: " + errbuf;
        return false;
    }
    return true;
}

bool setConf(rd_kafka_conf_t* conf, const char* name, int value, std::string& err) {
    return setConf(conf, name, std::to_string(value), err);
}

} // namespace

std::vector<BrokerAddr> parseBootstrapServers(const std::string& text) {
    std::vector<BrokerAddr> out;
    size_t pos = 0;
    while (pos <= text.size()) {
        const size_t comma = text.find(',', pos);
        const std::string item =
            text.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
        if (!item.empty()) {
            BrokerAddr a;
            const size_t colon = item.rfind(':');
            if (colon == std::string::npos) {
                a.host = item;
                a.port = 9092;
            } else {
                a.host = item.substr(0, colon);
                try {
                    a.port = std::stoi(item.substr(colon + 1));
                } catch (...) {
                    a.port = 9092;
                }
            }
            if (!a.host.empty() && a.port > 0) out.push_back(a);
        }
        if (comma == std::string::npos) break;
        pos = comma + 1;
    }
    return out;
}

// ---------------------------------------------------------------------------
// KafkaConsumer
// ---------------------------------------------------------------------------
struct KafkaConsumer::Impl {
    rd_kafka_t* rk{nullptr};
    /** open() 等待首次分配期间提前拉到的消息，由首次 poll() 交还业务层 */
    std::vector<ConsumedRecord> pending;
    /** 最近一次 poll 的各分区“下一条待消费位点”（commit 时写入 librdkafka） */
    std::map<int32_t, int64_t> nextOffsets;
};

KafkaConsumer::KafkaConsumer(KafkaConfig cfg) : cfg_(std::move(cfg)) {}
KafkaConsumer::~KafkaConsumer() { close(); }

bool KafkaConsumer::open(std::string& err) {
    close();
    err.clear();
    impl_ = std::make_unique<Impl>();

    rd_kafka_conf_t* conf = rd_kafka_conf_new();
    const bool configured =
        setConf(conf, "bootstrap.servers", cfg_.bootstrapServers, err) &&
        setConf(conf, "client.id", cfg_.clientId.empty() ? "car-monit-cpp" : cfg_.clientId, err) &&
        setConf(conf, "group.id", cfg_.groupId, err) &&
        // Java：enable.auto.commit=false + MANUAL_IMMEDIATE ⇒ 手动提交、手动存位点
        setConf(conf, "enable.auto.commit", std::string("false"), err) &&
        setConf(conf, "enable.auto.offset.store", std::string("false"), err) &&
        setConf(conf, "auto.offset.reset", cfg_.fromBeginning ? "earliest" : "latest", err) &&
        setConf(conf, "session.timeout.ms", cfg_.sessionTimeoutMs, err) &&
        setConf(conf, "max.poll.interval.ms", cfg_.maxPollIntervalMs, err) &&
        setConf(conf, "fetch.max.bytes", cfg_.fetchMaxBytes, err) &&
        setConf(conf, "socket.timeout.ms", cfg_.socketTimeoutMs, err) &&
        setConf(conf, "socket.connection.setup.timeout.ms", cfg_.connectTimeoutMs, err) &&
        // Java 默认 RangeAssignor / read_uncommitted，保持逐项对齐
        setConf(conf, "partition.assignment.strategy", std::string("range"), err) &&
        setConf(conf, "isolation.level", std::string("read_uncommitted"), err);
    if (!configured) {
        rd_kafka_conf_destroy(conf);
        return false;
    }

    char errbuf[512];
    rd_kafka_t* rk = rd_kafka_new(RD_KAFKA_CONSUMER, conf, errbuf, sizeof(errbuf));
    if (!rk) {
        err = std::string("创建 Kafka 消费者失败: ") + errbuf;
        return false;
    }
    // 把主队列事件转交给 consumer 队列，保证 consumer_poll 能驱动再平衡
    rd_kafka_poll_set_consumer(rk);

    rd_kafka_topic_partition_list_t* topics = rd_kafka_topic_partition_list_new(1);
    rd_kafka_topic_partition_list_add(topics, cfg_.topic.c_str(), RD_KAFKA_PARTITION_UA);
    const rd_kafka_resp_err_t sub = rd_kafka_subscribe(rk, topics);
    rd_kafka_topic_partition_list_destroy(topics);
    if (sub) {
        err = errText("订阅 topic=" + cfg_.topic + " 失败", sub);
        rd_kafka_destroy(rk);
        return false;
    }
    impl_->rk = rk;

    // 等待首次分区分配：分配完成后 open() 才算成功（与自研版 joinGroup 成功语义一致）。
    // 等待期间若已拉到消息，先缓存，避免丢弃。
    const int64_t deadline = nowMillis() + std::max(5000, cfg_.connectTimeoutMs);
    while (nowMillis() < deadline) {
        rd_kafka_message_t* msg = rd_kafka_consumer_poll(rk, 200);
        if (msg) {
            if (!msg->err) {
                ConsumedRecord rec;
                if (msg->key) {
                    rec.key.assign(static_cast<const char*>(msg->key), msg->key_len);
                    rec.hasKey = true;
                }
                if (msg->payload) {
                    rec.value.assign(static_cast<const char*>(msg->payload), msg->len);
                }
                rec.partition = msg->partition;
                rec.offset = msg->offset;
                rd_kafka_timestamp_type_t tstype = RD_KAFKA_TIMESTAMP_NOT_AVAILABLE;
                const int64_t ts = rd_kafka_message_timestamp(msg, &tstype);
                rec.timestamp = (tstype == RD_KAFKA_TIMESTAMP_NOT_AVAILABLE) ? 0 : ts;
                impl_->pending.push_back(std::move(rec));
                impl_->nextOffsets[msg->partition] = msg->offset + 1;
            }
            rd_kafka_message_destroy(msg);
        }
        rd_kafka_topic_partition_list_t* assigned = nullptr;
        if (rd_kafka_assignment(rk, &assigned) == RD_KAFKA_RESP_ERR_NO_ERROR && assigned) {
            const bool hasAssignment = assigned->cnt > 0;
            rd_kafka_topic_partition_list_destroy(assigned);
            if (hasAssignment) return true;
        }
    }

    err = "等待消费组分配超时（group=" + cfg_.groupId + " topic=" + cfg_.topic +
          " servers=" + cfg_.bootstrapServers + "）";
    close();
    return false;
}

bool KafkaConsumer::poll(std::vector<ConsumedRecord>& out, int maxWaitMs, std::string& err) {
    out.clear();
    err.clear();
    if (!impl_ || !impl_->rk) {
        err = "Kafka 消费者未打开";
        return false;
    }
    rd_kafka_t* rk = impl_->rk;
    const size_t limit = static_cast<size_t>(std::max(1, cfg_.maxPollRecords));

    while (out.size() < limit && !impl_->pending.empty()) {
        out.push_back(std::move(impl_->pending.front()));
        impl_->pending.erase(impl_->pending.begin());
    }

    const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(maxWaitMs);
    while (out.size() < limit) {
        const auto remain = std::chrono::duration_cast<std::chrono::milliseconds>(
                                deadline - std::chrono::steady_clock::now())
                                .count();
        const int waitMs = static_cast<int>(std::max<long long>(0, remain));
        rd_kafka_message_t* msg = rd_kafka_consumer_poll(rk, waitMs);
        if (!msg) break;  // 超时/本批已空
        if (msg->err) {
            const rd_kafka_resp_err_t e = msg->err;
            rd_kafka_message_destroy(msg);
            if (e == RD_KAFKA_RESP_ERR__PARTITION_EOF) continue;
            err = errText("拉取消息失败", e);
            return false;
        }
        ConsumedRecord rec;
        if (msg->key) {
            rec.key.assign(static_cast<const char*>(msg->key), msg->key_len);
            rec.hasKey = true;
        }
        if (msg->payload) {
            rec.value.assign(static_cast<const char*>(msg->payload), msg->len);
        }
        rec.partition = msg->partition;
        rec.offset = msg->offset;
        rd_kafka_timestamp_type_t tstype = RD_KAFKA_TIMESTAMP_NOT_AVAILABLE;
        const int64_t ts = rd_kafka_message_timestamp(msg, &tstype);
        rec.timestamp = (tstype == RD_KAFKA_TIMESTAMP_NOT_AVAILABLE) ? 0 : ts;
        rd_kafka_message_destroy(msg);

        impl_->nextOffsets[rec.partition] = rec.offset + 1;
        out.push_back(std::move(rec));
        if (waitMs == 0 && out.size() >= limit) break;
    }
    return true;
}

bool KafkaConsumer::commit(std::string& err) {
    err.clear();
    if (!impl_ || !impl_->rk) {
        err = "Kafka 消费者未打开";
        return false;
    }
    if (impl_->nextOffsets.empty()) return true;

    rd_kafka_topic_partition_list_t* offsets =
        rd_kafka_topic_partition_list_new(static_cast<int>(impl_->nextOffsets.size()));
    for (const auto& kv : impl_->nextOffsets) {
        rd_kafka_topic_partition_t* p =
            rd_kafka_topic_partition_list_add(offsets, cfg_.topic.c_str(), kv.first);
        p->offset = kv.second;
    }
    rd_kafka_resp_err_t e = rd_kafka_offsets_store(impl_->rk, offsets);
    rd_kafka_topic_partition_list_destroy(offsets);
    if (e) {
        err = errText("保存消费位点失败", e);
        return false;
    }
    // 同步提交（MANUAL_IMMEDIATE：处理成功立即提交）
    e = rd_kafka_commit(impl_->rk, nullptr, 0);
    if (e) {
        err = errText("提交消费位点失败", e);
        return false;
    }
    impl_->nextOffsets.clear();
    return true;
}

bool KafkaConsumer::committedOffsets(std::map<int32_t, int64_t>& out, std::string& err) {
    out.clear();
    err.clear();
    if (!impl_ || !impl_->rk) {
        err = "Kafka 消费者未打开";
        return false;
    }
    rd_kafka_topic_partition_list_t* assigned = nullptr;
    if (rd_kafka_assignment(impl_->rk, &assigned) != RD_KAFKA_RESP_ERR_NO_ERROR || !assigned) {
        err = "获取分区分配失败";
        return false;
    }
    const rd_kafka_resp_err_t e = rd_kafka_committed(impl_->rk, assigned, 5000);
    if (e) {
        rd_kafka_topic_partition_list_destroy(assigned);
        err = errText("查询已提交位点失败", e);
        return false;
    }
    for (int i = 0; i < assigned->cnt; ++i) {
        const rd_kafka_topic_partition_t& p = assigned->elems[i];
        if (p.err == RD_KAFKA_RESP_ERR__NO_OFFSET || p.offset < 0) continue;
        out[p.partition] = p.offset;
    }
    rd_kafka_topic_partition_list_destroy(assigned);
    return true;
}

void KafkaConsumer::rewind(const std::vector<ConsumedRecord>& records) {
    if (!impl_ || !impl_->rk || records.empty()) return;
    std::map<int32_t, int64_t> firstOffsets;
    for (const auto& r : records) {
        auto it = firstOffsets.find(r.partition);
        if (it == firstOffsets.end() || r.offset < it->second) firstOffsets[r.partition] = r.offset;
    }
    rd_kafka_topic_partition_list_t* targets =
        rd_kafka_topic_partition_list_new(static_cast<int>(firstOffsets.size()));
    for (const auto& kv : firstOffsets) {
        rd_kafka_topic_partition_t* p =
            rd_kafka_topic_partition_list_add(targets, cfg_.topic.c_str(), kv.first);
        p->offset = kv.second;
    }
    rd_kafka_error_t* seekErr = rd_kafka_seek_partitions(impl_->rk, targets, 3000);
    rd_kafka_topic_partition_list_destroy(targets);
    if (seekErr) {
        LOG_WARN("KafkaClient", std::string("位点回退失败 err=") +
                                    rd_kafka_error_string(seekErr));
        rd_kafka_error_destroy(seekErr);
    }
    impl_->nextOffsets.clear();
}

void KafkaConsumer::close() {
    if (!impl_ || !impl_->rk) {
        impl_.reset();
        return;
    }
    rd_kafka_consumer_close(impl_->rk);
    rd_kafka_destroy(impl_->rk);
    impl_->rk = nullptr;
    impl_.reset();
}

bool KafkaConsumer::joined() const {
    if (!impl_ || !impl_->rk) return false;
    rd_kafka_topic_partition_list_t* assigned = nullptr;
    if (rd_kafka_assignment(impl_->rk, &assigned) != RD_KAFKA_RESP_ERR_NO_ERROR || !assigned) {
        return false;
    }
    const bool has = assigned->cnt > 0;
    rd_kafka_topic_partition_list_destroy(assigned);
    return has;
}

// ---------------------------------------------------------------------------
// KafkaProducer（仅 DLQ）
// ---------------------------------------------------------------------------
struct KafkaProducer::Impl {
    rd_kafka_t* rk{nullptr};
    std::atomic<int> failures{0};
    std::string lastError;
};

namespace {

void deliveryReport(rd_kafka_t*, const rd_kafka_message_t* msg, void* opaque) {
    auto* impl = static_cast<KafkaProducer::Impl*>(opaque);
    if (!impl) return;
    if (msg->err) {
        impl->lastError = rd_kafka_err2str(msg->err);
        impl->failures.fetch_add(1);
    }
}

} // namespace

KafkaProducer::KafkaProducer(KafkaConfig cfg) : cfg_(std::move(cfg)) {}
KafkaProducer::~KafkaProducer() { close(); }

void KafkaProducer::close() {
    if (!impl_ || !impl_->rk) {
        impl_.reset();
        return;
    }
    rd_kafka_flush(impl_->rk, cfg_.socketTimeoutMs);
    rd_kafka_destroy(impl_->rk);
    impl_->rk = nullptr;
    impl_.reset();
}

bool KafkaProducer::send(const std::string& topic, const std::string& value, std::string& err) {
    err.clear();
    if (!impl_) impl_ = std::make_unique<Impl>();
    if (!impl_->rk) {
        rd_kafka_conf_t* conf = rd_kafka_conf_new();
        const bool configured =
            setConf(conf, "bootstrap.servers", cfg_.bootstrapServers, err) &&
            setConf(conf, "client.id",
                    (cfg_.clientId.empty() ? "car-monit-cpp" : cfg_.clientId) + "-dlq", err) &&
            // 对齐 Java KafkaConfig.producerFactory：acks=all、retries=3、幂等
            setConf(conf, "acks", std::string("all"), err) &&
            setConf(conf, "message.send.max.retries", 3, err) &&
            setConf(conf, "enable.idempotence", std::string("true"), err) &&
            setConf(conf, "socket.timeout.ms", cfg_.socketTimeoutMs, err);
        if (!configured) {
            rd_kafka_conf_destroy(conf);
            return false;
        }
        rd_kafka_conf_set_dr_msg_cb(conf, deliveryReport);
        rd_kafka_conf_set_opaque(conf, impl_.get());

        char errbuf[512];
        rd_kafka_t* rk = rd_kafka_new(RD_KAFKA_PRODUCER, conf, errbuf, sizeof(errbuf));
        if (!rk) {
            err = std::string("创建 Kafka 生产者失败: ") + errbuf;
            return false;
        }
        impl_->rk = rk;
    }

    impl_->failures.store(0);
    impl_->lastError.clear();
    const rd_kafka_resp_err_t e = rd_kafka_producev(
        impl_->rk, RD_KAFKA_V_TOPIC(topic.c_str()),
        RD_KAFKA_V_VALUE(const_cast<char*>(value.data()), value.size()),
        RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY), RD_KAFKA_V_END);
    if (e) {
        err = errText("投递消息失败 topic=" + topic, e);
        return false;
    }
    const rd_kafka_resp_err_t f = rd_kafka_flush(impl_->rk, cfg_.socketTimeoutMs);
    if (f) {
        err = errText("等待消息投递完成超时 topic=" + topic, f);
        return false;
    }
    if (impl_->failures.load() > 0) {
        err = "消息投递失败 topic=" + topic + ": " + impl_->lastError;
        return false;
    }
    return true;
}

} // namespace cm::kafka
