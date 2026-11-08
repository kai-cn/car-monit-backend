#include "cm/framework/kafka/KafkaClient.hpp"

#include <algorithm>
#include <cstdio>
#include <thread>

#include "cm/common/utils/Logger.hpp"
#include "cm/framework/net/Os.hpp"

namespace cm::kafka {
namespace {

constexpr int16_t API_PRODUCE = 0;
constexpr int16_t API_FETCH = 1;
constexpr int16_t API_LIST_OFFSETS = 2;
constexpr int16_t API_METADATA = 3;
constexpr int16_t API_OFFSET_COMMIT = 8;
constexpr int16_t API_OFFSET_FETCH = 9;
constexpr int16_t API_FIND_COORDINATOR = 10;
constexpr int16_t API_JOIN_GROUP = 11;
constexpr int16_t API_HEARTBEAT = 12;
constexpr int16_t API_LEAVE_GROUP = 13;
constexpr int16_t API_SYNC_GROUP = 14;

// Kafka 错误码（只列会改变控制流的）
constexpr int16_t ERR_NONE = 0;
constexpr int16_t ERR_UNKNOWN_TOPIC_OR_PARTITION = 3;
constexpr int16_t ERR_NOT_LEADER = 6;
constexpr int16_t ERR_COORDINATOR_NOT_AVAILABLE = 15;
constexpr int16_t ERR_NOT_COORDINATOR = 16;
constexpr int16_t ERR_ILLEGAL_GENERATION = 22;
constexpr int16_t ERR_UNKNOWN_MEMBER_ID = 25;
constexpr int16_t ERR_REBALANCE_IN_PROGRESS = 27;
constexpr int16_t ERR_FENCED_LEADER_EPOCH = 70;
constexpr int16_t ERR_MEMBER_ID_REQUIRED = 79;

bool readExact(cm::net::Fd fd, char* buf, size_t n) {
    size_t got = 0;
    while (got < n) {
        const long r = cm::net::readSome(fd, buf + got, n - got);
        if (r <= 0) return false;
        got += static_cast<size_t>(r);
    }
    return true;
}

bool isSessionError(int16_t code) {
    return code == ERR_ILLEGAL_GENERATION || code == ERR_UNKNOWN_MEMBER_ID ||
           code == ERR_REBALANCE_IN_PROGRESS || code == ERR_MEMBER_ID_REQUIRED;
}

std::string errText(const std::string& what, int16_t code) {
    return what + " (kafka error=" + std::to_string(code) + ")";
}

int64_t nowMillis() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
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
// KafkaConnection
// ---------------------------------------------------------------------------
KafkaConnection::~KafkaConnection() { close(); }

bool KafkaConnection::connect(const std::string& clientId, const BrokerAddr& addr,
                              int connectTimeoutMs, int socketTimeoutMs, std::string& err) {
    close();
    clientId_ = clientId.empty() ? std::string("car-monit-cpp") : clientId;
    cm::net::Fd fd = cm::net::connectTcp(addr.host, addr.port, connectTimeoutMs, &err);
    if (!cm::net::isValid(fd)) return false;
    cm::net::setTimeout(fd, socketTimeoutMs);
    cm::net::setNoDelay(fd);
    fd_ = cm::net::toStorage(fd);
    addr_ = addr;
    correlation_ = 0;
    return true;
}

void KafkaConnection::close() {
    if (cm::net::validStorage(fd_)) {
        cm::net::closeTcp(cm::net::fromStorage(fd_));
        fd_ = cm::net::kInvalidStorage;
    }
}

bool KafkaConnection::request(int16_t apiKey, int16_t apiVersion, const std::string& body,
                              std::string& payload, std::string& err) {
    if (!isOpen()) {
        err = "Kafka 连接未建立";
        return false;
    }
    Writer w;
    w.i16(apiKey);
    w.i16(apiVersion);
    ++correlation_;
    w.i32(correlation_);
    // ⚠️ client_id 不能为 null：Kafka 把它写进 GroupMetadataValue，
    // 为 null 时 broker 在 SyncGroup 落盘阶段 NPE（实测 error=-1 UNKNOWN_SERVER_ERROR）。
    w.str(clientId_);
    w.raw(body);

    std::string frame;
    {
        Writer h;
        h.i32(static_cast<int32_t>(w.buf.size()));
        frame = h.buf + w.buf;
    }
    const auto fd = cm::net::fromStorage(fd_);
    if (!cm::net::writeAll(fd, frame.data(), frame.size(), &err)) {
        close();
        return false;
    }
    char lenBuf[4];
    if (!readExact(fd, lenBuf, 4)) {
        err = "读取 Kafka 响应长度失败（连接关闭/超时）";
        close();
        return false;
    }
    Reader lr(lenBuf, 4);
    const int32_t len = lr.i32();
    if (len < 0) {
        err = "Kafka 响应长度为负";
        close();
        return false;
    }
    payload.assign(static_cast<size_t>(len), '\0');
    if (len > 0 && !readExact(fd, payload.data(), static_cast<size_t>(len))) {
        err = "读取 Kafka 响应体失败";
        close();
        return false;
    }
    // 响应头 v0（所有非 flexible 版本）：correlation_id(INT32)，其后才是响应体。
    // ⚠️ 必须在这里剥掉：漏读会让每个响应整体偏移 4 字节（实测表现为字段长度离谱）。
    if (payload.size() < 4) {
        err = "Kafka 响应过短";
        close();
        return false;
    }
    Reader hr(payload);
    const int32_t corr = hr.i32();
    if (corr != correlation_) {
        err = "Kafka correlation id 不匹配";
        close();
        return false;
    }
    payload.erase(0, 4);
    return true;
}

// ---------------------------------------------------------------------------
// KafkaConsumer
// ---------------------------------------------------------------------------
KafkaConsumer::KafkaConsumer(KafkaConfig cfg) : cfg_(std::move(cfg)) {}

KafkaConsumer::~KafkaConsumer() { close(); }

BrokerAddr KafkaConsumer::firstBootstrap() const {
    const auto list = parseBootstrapServers(cfg_.bootstrapServers);
    if (!list.empty()) return list.front();
    return BrokerAddr{"127.0.0.1", 9092};
}

void KafkaConsumer::resetSession() {
    joined_ = false;
    generation_ = -1;
    memberId_.clear();
    leaderId_.clear();
    partitions_.clear();
    nextOffset_.clear();
    pendingCommit_.clear();
    pending_.clear();
}

void KafkaConsumer::close() {
    if (joined_ && coord_ && coord_->isOpen()) {
        Writer w;
        w.str(cfg_.groupId);
        w.str(memberId_);
        std::string payload, err;
        coord_->request(API_LEAVE_GROUP, 1, w.buf, payload, err);
    }
    joined_ = false;
    if (fetchConn_) fetchConn_->close();
    if (coord_) coord_->close();
    fetchConn_.reset();
    coord_.reset();
}

bool KafkaConsumer::ensureCoordinator(std::string& err) {
    if (coord_ && coord_->isOpen() && !coordAddr_.host.empty()) return true;
    const auto boot = firstBootstrap();
    KafkaConnection tmp;
    std::string localErr;
    if (!tmp.connect(cfg_.clientId, boot, cfg_.connectTimeoutMs, cfg_.socketTimeoutMs, localErr)) {
        err = "连接 bootstrap " + boot.toString() + " 失败: " + localErr;
        return false;
    }
    Writer w;
    // FindCoordinator v1 的字段顺序是 key(STRING) 然后 key_type(INT8)；
    // 顺序颠倒会让 broker 读到错误长度（实测 BufferUnderflow）。
    w.str(cfg_.groupId);
    w.i8(0);  // key_type = 0（消费组）
    std::string payload;
    if (!tmp.request(API_FIND_COORDINATOR, 1, w.buf, payload, localErr)) {
        err = "FindCoordinator 失败: " + localErr;
        return false;
    }
    Reader r(payload);
    r.i32();  // throttle
    const int16_t code = r.i16();
    std::string msg;
    r.nullableStr(msg);
    const int32_t node = r.i32();
    (void)node;
    const std::string host = r.str();
    const int32_t port = r.i32();
    if (!r.ok()) {
        err = "FindCoordinator 响应解析失败";
        return false;
    }
    if (code != ERR_NONE) {
        err = errText("FindCoordinator", code) + (msg.empty() ? "" : " " + msg);
        return false;
    }
    coordAddr_ = BrokerAddr{host, port};
    coord_ = std::make_unique<KafkaConnection>();
    if (!coord_->connect(cfg_.clientId, coordAddr_, cfg_.connectTimeoutMs, cfg_.socketTimeoutMs,
                         localErr)) {
        err = "连接 coordinator " + coordAddr_.toString() + " 失败: " + localErr;
        coord_.reset();
        return false;
    }
    return true;
}

bool KafkaConsumer::refreshMetadata(std::string& err) {
    const auto boot = firstBootstrap();
    KafkaConnection tmp;
    std::string localErr;
    if (!tmp.connect(cfg_.clientId, boot, cfg_.connectTimeoutMs, cfg_.socketTimeoutMs, localErr)) {
        err = "连接 bootstrap 失败: " + localErr;
        return false;
    }
    Writer w;
    w.i32(1);
    w.str(cfg_.topic);
    std::string payload;
    if (!tmp.request(API_METADATA, 1, w.buf, payload, localErr)) {
        err = "Metadata 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    const int32_t brokerCount = r.arrayLen();
    std::map<int32_t, BrokerAddr> brokers;
    for (int32_t i = 0; i < brokerCount && r.ok(); ++i) {
        const int32_t node = r.i32();
        const std::string host = r.str();
        const int32_t port = r.i32();
        std::string rack;
        r.nullableStr(rack);
        brokers[node] = BrokerAddr{host, port};
    }
    r.i32();  // controller_id
    const int32_t topicCount = r.arrayLen();
    bool found = false;
    int16_t topicError = 0;
    for (int32_t i = 0; i < topicCount && r.ok(); ++i) {
        topicError = r.i16();
        const std::string name = r.str();
        r.i8();  // is_internal
        const int32_t partCount = r.arrayLen();
        std::vector<int32_t> parts;
        int32_t leader = -1;
        for (int32_t p = 0; p < partCount && r.ok(); ++p) {
            r.i16();  // partition error
            const int32_t index = r.i32();
            const int32_t leaderId = r.i32();
            const int32_t replicas = r.arrayLen();
            for (int32_t k = 0; k < replicas; ++k) r.i32();
            const int32_t isr = r.arrayLen();
            for (int32_t k = 0; k < isr; ++k) r.i32();
            parts.push_back(index);
            if (leader < 0) leader = leaderId;
        }
        if (name == cfg_.topic) {
            found = true;
            std::sort(parts.begin(), parts.end());
            partitions_ = parts;
            const auto it = brokers.find(leader);
            if (it != brokers.end()) {
                leaderAddr_ = it->second;
            }
        }
    }
    if (!r.ok()) {
        err = "Metadata 响应解析失败";
        return false;
    }
    if (!found || partitions_.empty()) {
        err = "topic " + cfg_.topic + " 不存在或无分区（error=" + std::to_string(topicError) + "）";
        return false;
    }
    if (leaderAddr_.host.empty()) {
        err = "topic " + cfg_.topic + " 的分区 leader 不在 broker 列表中";
        return false;
    }
    return true;
}

bool KafkaConsumer::joinGroup(std::string& err) {
    if (!ensureCoordinator(err)) return false;
    std::string localErr;
    if (!refreshMetadata(localErr)) {
        err = localErr;
        return false;
    }
    // 订阅元数据（consumer protocol v0）：version + topics + userData
    Writer meta;
    meta.i16(0);
    meta.i32(1);
    meta.str(cfg_.topic);
    meta.nullableBytes(false, "");

    Writer w;
    w.str(cfg_.groupId);
    w.i32(cfg_.sessionTimeoutMs);
    w.i32(cfg_.maxPollIntervalMs);
    w.str(memberId_);
    w.str("consumer");
    w.i32(1);
    w.str("range");
    w.bytes(meta.buf);

    std::string payload;
    if (!coord_->request(API_JOIN_GROUP, 2, w.buf, payload, localErr)) {
        err = "JoinGroup 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    r.i32();  // throttle
    const int16_t code = r.i16();
    if (code != ERR_NONE) {
        err = errText("JoinGroup", code);
        return false;
    }
    generation_ = r.i32();
    const std::string protocol = r.str();
    (void)protocol;
    leaderId_ = r.str();
    const std::string assignedId = r.str();
    if (!assignedId.empty()) memberId_ = assignedId;
    const int32_t memberCount = r.arrayLen();
    for (int32_t i = 0; i < memberCount && r.ok(); ++i) {
        r.str();       // member_id
        r.bytes();     // metadata
    }
    if (!r.ok()) {
        err = "JoinGroup 响应解析失败";
        return false;
    }
    return true;
}

bool KafkaConsumer::syncGroup(std::string& err) {
    // leader 需要下发分配方案；单成员时就是把所有分区给自己
    Writer assign;
    assign.i16(0);
    assign.i32(1);
    assign.str(cfg_.topic);
    assign.i32(static_cast<int32_t>(partitions_.size()));
    for (int32_t p : partitions_) assign.i32(p);
    assign.nullableBytes(false, "");

    Writer w;
    w.str(cfg_.groupId);
    w.i32(generation_);
    w.str(memberId_);
    const bool isLeader = (memberId_ == leaderId_);
    w.i32(isLeader ? 1 : 0);
    if (isLeader) {
        w.str(memberId_);
        w.bytes(assign.buf);
    }

    std::string payload, localErr;
    if (!coord_->request(API_SYNC_GROUP, 1, w.buf, payload, localErr)) {
        err = "SyncGroup 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    r.i32();  // throttle
    const int16_t code = r.i16();
    if (code != ERR_NONE) {
        err = errText("SyncGroup", code);
        return false;
    }
    std::string assignment;
    assignment = r.bytes();
    if (!r.ok()) {
        err = "SyncGroup 响应解析失败";
        return false;
    }
    Reader ar(assignment);
    if (assignment.size() >= 2) {
        ar.i16();  // version
        const int32_t topicCount = ar.arrayLen();
        std::vector<int32_t> parts;
        for (int32_t t = 0; t < topicCount && ar.ok(); ++t) {
            const std::string name = ar.str();
            const int32_t cnt = ar.arrayLen();
            for (int32_t i = 0; i < cnt; ++i) {
                const int32_t p = ar.i32();
                if (name == cfg_.topic) parts.push_back(p);
            }
        }
        if (ar.ok() && !parts.empty()) {
            std::sort(parts.begin(), parts.end());
            partitions_ = parts;
        }
    }
    if (partitions_.empty()) {
        err = "SyncGroup 返回空分配";
        return false;
    }
    return true;
}

bool KafkaConsumer::heartbeat(std::string& err) {
    Writer w;
    w.str(cfg_.groupId);
    w.i32(generation_);
    w.str(memberId_);
    std::string payload, localErr;
    if (!coord_->request(API_HEARTBEAT, 1, w.buf, payload, localErr)) {
        err = "Heartbeat 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    r.i32();
    const int16_t code = r.i16();
    if (code != ERR_NONE) {
        if (isSessionError(code)) resetSession();
        err = errText("Heartbeat", code);
        return false;
    }
    lastHeartbeat_ = std::chrono::steady_clock::now();
    return true;
}

bool KafkaConsumer::listOffsets(std::string& err) {
    Writer w;
    w.i32(-1);  // replica_id
    w.i32(1);   // 一个 topic
    w.str(cfg_.topic);
    w.i32(static_cast<int32_t>(partitions_.size()));
    for (int32_t p : partitions_) {
        w.i32(p);
        w.i64(cfg_.fromBeginning ? -2 : -1);  // earliest / latest
    }
    std::string payload, localErr;
    if (!coord_->request(API_LIST_OFFSETS, 1, w.buf, payload, localErr)) {
        err = "ListOffsets 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    const int32_t topicCount = r.arrayLen();
    for (int32_t t = 0; t < topicCount && r.ok(); ++t) {
        r.str();
        const int32_t partCount = r.arrayLen();
        for (int32_t i = 0; i < partCount && r.ok(); ++i) {
            const int32_t partition = r.i32();
            const int16_t code = r.i16();
            r.i64();  // timestamp
            const int64_t offset = r.i64();
            if (code == ERR_NONE) nextOffset_[partition] = offset;
        }
    }
    if (!r.ok()) {
        err = "ListOffsets 响应解析失败";
        return false;
    }
    return true;
}

bool KafkaConsumer::fetchOffsets(std::string& err) {
    Writer w;
    w.str(cfg_.groupId);
    w.i32(1);
    w.str(cfg_.topic);
    w.i32(static_cast<int32_t>(partitions_.size()));
    for (int32_t p : partitions_) w.i32(p);

    std::string payload, localErr;
    if (!coord_->request(API_OFFSET_FETCH, 3, w.buf, payload, localErr)) {
        err = "OffsetFetch 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    r.i32();  // throttle
    const int32_t topicCount = r.arrayLen();
    std::map<int32_t, int64_t> committed;
    for (int32_t t = 0; t < topicCount && r.ok(); ++t) {
        r.str();
        const int32_t partCount = r.arrayLen();
        for (int32_t i = 0; i < partCount && r.ok(); ++i) {
            const int32_t partition = r.i32();
            const int64_t offset = r.i64();
            r.str();  // metadata
            r.i16();  // error
            if (offset >= 0) committed[partition] = offset;
        }
    }
    const int16_t topError = r.i16();
    if (!r.ok()) {
        err = "OffsetFetch 响应解析失败";
        return false;
    }
    if (topError != ERR_NONE) {
        err = errText("OffsetFetch", topError);
        return false;
    }
    nextOffset_.clear();
    bool needListOffsets = false;
    for (int32_t p : partitions_) {
        const auto it = committed.find(p);
        if (it != committed.end()) {
            nextOffset_[p] = it->second;
        } else {
            needListOffsets = true;
        }
    }
    if (needListOffsets) {
        if (!listOffsets(err)) return false;
    }
    return true;
}

bool KafkaConsumer::open(std::string& err) {
    resetSession();
    if (!ensureCoordinator(err)) return false;
    // 先用 coordinator 拿 metadata（同时校验 topic 存在）
    if (!refreshMetadata(err)) return false;
    if (fetchConn_) fetchConn_->close();
    fetchConn_ = std::make_unique<KafkaConnection>();
    std::string localErr;
    if (!fetchConn_->connect(cfg_.clientId, leaderAddr_, cfg_.connectTimeoutMs,
                             cfg_.socketTimeoutMs, localErr)) {
        err = "连接分区 leader " + leaderAddr_.toString() + " 失败: " + localErr;
        fetchConn_.reset();
        return false;
    }
    if (!joinGroup(err)) return false;
    if (!syncGroup(err)) return false;
    if (!fetchOffsets(err)) return false;
    if (!heartbeat(err)) return false;
    joined_ = true;
    LOG_INFO("kafka", "已加入消费组 group=" + cfg_.groupId + " topic=" + cfg_.topic +
                          " generation=" + std::to_string(generation_) +
                          " partitions=" + std::to_string(partitions_.size()));
    return true;
}

bool KafkaConsumer::runFetch(int maxWaitMs, std::string& err) {
    if (!fetchConn_ || !fetchConn_->isOpen()) {
        err = "fetch 连接未建立";
        return false;
    }
    Writer w;
    w.i32(-1);          // replica_id
    w.i32(maxWaitMs);   // max_wait_ms
    w.i32(1);           // min_bytes
    w.i32(cfg_.fetchMaxBytes);
    w.i8(0);            // isolation_level = read_uncommitted
    w.i32(1);
    w.str(cfg_.topic);
    w.i32(static_cast<int32_t>(partitions_.size()));
    for (int32_t p : partitions_) {
        w.i32(p);
        w.i64(nextOffset_.count(p) ? nextOffset_[p] : (cfg_.fromBeginning ? 0 : -1));
        w.i32(cfg_.fetchMaxBytes);
    }
    std::string payload, localErr;
    if (!fetchConn_->request(API_FETCH, 4, w.buf, payload, localErr)) {
        err = "Fetch 请求失败: " + localErr;
        if (fetchConn_) fetchConn_->close();
        return false;
    }
    Reader r(payload);
    r.i32();  // throttle
    const int32_t topicCount = r.arrayLen();
    bool gotAny = false;
    int16_t firstError = ERR_NONE;
    for (int32_t t = 0; t < topicCount && r.ok(); ++t) {
        r.str();
        const int32_t partCount = r.arrayLen();
        for (int32_t i = 0; i < partCount && r.ok(); ++i) {
            const int32_t partition = r.i32();
            const int16_t code = r.i16();
            r.i64();  // high watermark
            r.i64();  // last stable offset
            const int32_t aborted = r.arrayLen();
            for (int32_t a = 0; a < aborted; ++a) {
                r.i64();
                r.i64();
            }
            std::string records;
            const bool hasRecords = r.nullableBytes(records);
            if (code != ERR_NONE) {
                if (firstError == ERR_NONE) firstError = code;
                continue;
            }
            if (!hasRecords || records.empty()) continue;
            std::vector<ConsumedRecord> parsed;
            std::string parseErr;
            if (!parseRecordSet(records, parsed, parseErr)) {
                err = "RecordBatch 解析失败: " + parseErr;
                return false;
            }
            const int64_t base = nextOffset_.count(partition) ? nextOffset_[partition] : 0;
            for (auto& rec : parsed) {
                rec.partition = partition;
                if (rec.offset < base) continue;  // 位点之前的旧数据（重复抓取）丢弃
                pending_.push_back(std::move(rec));
                gotAny = true;
            }
            if (!parsed.empty()) {
                nextOffset_[partition] = parsed.back().offset + 1;
            }
        }
    }
    if (!r.ok()) {
        err = "Fetch 响应解析失败";
        return false;
    }
    if (firstError == ERR_NOT_LEADER || firstError == ERR_UNKNOWN_TOPIC_OR_PARTITION ||
        firstError == ERR_FENCED_LEADER_EPOCH) {
        err = "分区 leader 已变更（error=" + std::to_string(firstError) + "）";
        resetSession();
        return false;
    }
    if (firstError != ERR_NONE) {
        err = "Fetch 分区错误 error=" + std::to_string(firstError);
        return false;
    }
    return gotAny || pending_.empty();
}

bool KafkaConsumer::poll(std::vector<ConsumedRecord>& out, int maxWaitMs, std::string& err) {
    out.clear();
    if (!joined_) {
        if (!open(err)) return false;
    }
    if (pending_.empty()) {
        const auto now = std::chrono::steady_clock::now();
        if (now - lastHeartbeat_ >= std::chrono::milliseconds(cfg_.heartbeatIntervalMs)) {
            if (!heartbeat(err)) {
                joined_ = false;
                return false;
            }
        }
        if (!runFetch(maxWaitMs, err)) {
            joined_ = false;
            return false;
        }
    }
    if (pending_.empty()) return true;  // 本次没有新消息（不是错误）

    const size_t n = std::min<size_t>(pending_.size(), static_cast<size_t>(std::max(1, cfg_.maxPollRecords)));
    out.assign(std::make_move_iterator(pending_.begin()),
               std::make_move_iterator(pending_.begin() + static_cast<std::ptrdiff_t>(n)));
    pending_.erase(pending_.begin(), pending_.begin() + static_cast<std::ptrdiff_t>(n));
    for (const auto& rec : out) pendingCommit_[rec.partition] = rec.offset + 1;
    return true;
}

bool KafkaConsumer::commit(std::string& err) {
    if (pendingCommit_.empty()) return true;
    if (!coord_ || !coord_->isOpen()) {
        err = "coordinator 连接未建立，无法提交位点";
        return false;
    }
    Writer w;
    w.str(cfg_.groupId);
    w.i32(generation_);
    w.str(memberId_);
    w.i64(-1);  // retention_time
    w.i32(1);
    w.str(cfg_.topic);
    w.i32(static_cast<int32_t>(pendingCommit_.size()));
    for (const auto& kv : pendingCommit_) {
        w.i32(kv.first);
        w.i64(kv.second);
        w.str("");
    }
    std::string payload, localErr;
    if (!coord_->request(API_OFFSET_COMMIT, 2, w.buf, payload, localErr)) {
        err = "OffsetCommit 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    const int32_t topicCount = r.arrayLen();
    int16_t bad = ERR_NONE;
    for (int32_t t = 0; t < topicCount && r.ok(); ++t) {
        r.str();
        const int32_t partCount = r.arrayLen();
        for (int32_t i = 0; i < partCount && r.ok(); ++i) {
            r.i32();
            const int16_t code = r.i16();
            if (code != ERR_NONE && bad == ERR_NONE) bad = code;
        }
    }
    if (!r.ok()) {
        err = "OffsetCommit 响应解析失败";
        return false;
    }
    if (bad != ERR_NONE) {
        if (isSessionError(bad)) resetSession();
        err = errText("OffsetCommit", bad);
        return false;
    }
    pendingCommit_.clear();
    return true;
}

// ---------------------------------------------------------------------------
// KafkaProducer
// ---------------------------------------------------------------------------
KafkaProducer::KafkaProducer(KafkaConfig cfg) : cfg_(std::move(cfg)) {}

KafkaProducer::~KafkaProducer() { close(); }

void KafkaProducer::close() {
    if (conn_) conn_->close();
    conn_.reset();
}

bool KafkaProducer::ensureLeader(const std::string& topic, std::string& err) {
    if (conn_ && conn_->isOpen() && topic_ == topic && !leader_.host.empty()) return true;
    const auto boot = parseBootstrapServers(cfg_.bootstrapServers);
    KafkaConnection tmp;
    std::string localErr;
    const BrokerAddr first = boot.empty() ? BrokerAddr{"127.0.0.1", 9092} : boot.front();
    if (!tmp.connect(cfg_.clientId, first, cfg_.connectTimeoutMs, cfg_.socketTimeoutMs, localErr)) {
        err = "连接 bootstrap 失败: " + localErr;
        return false;
    }
    Writer w;
    w.i32(1);
    w.str(topic);
    std::string payload;
    if (!tmp.request(API_METADATA, 1, w.buf, payload, localErr)) {
        err = "Metadata 请求失败: " + localErr;
        return false;
    }
    Reader r(payload);
    const int32_t brokerCount = r.arrayLen();
    std::map<int32_t, BrokerAddr> brokers;
    for (int32_t i = 0; i < brokerCount && r.ok(); ++i) {
        const int32_t node = r.i32();
        const std::string host = r.str();
        const int32_t port = r.i32();
        std::string rack;
        r.nullableStr(rack);
        brokers[node] = BrokerAddr{host, port};
    }
    r.i32();  // controller
    const int32_t topicCount = r.arrayLen();
    int32_t leader = -1;
    for (int32_t t = 0; t < topicCount && r.ok(); ++t) {
        r.i16();
        const std::string name = r.str();
        r.i8();
        const int32_t partCount = r.arrayLen();
        for (int32_t p = 0; p < partCount && r.ok(); ++p) {
            r.i16();
            const int32_t index = r.i32();
            const int32_t leaderId = r.i32();
            const int32_t replicas = r.arrayLen();
            for (int32_t k = 0; k < replicas; ++k) r.i32();
            const int32_t isr = r.arrayLen();
            for (int32_t k = 0; k < isr; ++k) r.i32();
            if (name == topic && index == 0) leader = leaderId;
        }
    }
    if (!r.ok()) {
        err = "Metadata 响应解析失败";
        return false;
    }
    const auto it = brokers.find(leader);
    if (it == brokers.end()) {
        err = "未找到 topic " + topic + " 的分区 0 leader";
        return false;
    }
    leader_ = it->second;
    topic_ = topic;
    conn_ = std::make_unique<KafkaConnection>();
    if (!conn_->connect(cfg_.clientId, leader_, cfg_.connectTimeoutMs, cfg_.socketTimeoutMs,
                        localErr)) {
        err = "连接 leader " + leader_.toString() + " 失败: " + localErr;
        conn_.reset();
        return false;
    }
    return true;
}

bool KafkaProducer::send(const std::string& topic, const std::string& value, std::string& err) {
    // Java 侧 `retries=3` 是"可重试错误"的语义；topic 首次自动创建属于 metadata
    // 等待（max.block.ms=60s），所以这里用更长的窗口覆盖 auto-create，而不是只重试 3 次。
    const int maxAttempts = 12;  // ≈ 12 × 400ms = 4.8s
    for (int attempt = 0; attempt < maxAttempts; ++attempt) {
        std::string localErr;
        if (!ensureLeader(topic, localErr)) {
            err = localErr;
            std::this_thread::sleep_for(std::chrono::milliseconds(400));
            continue;
        }
        Writer w;
        w.nullableStr(false, "");  // transactional_id
        w.i16(-1);                 // acks = all
        w.i32(30000);
        w.i32(1);
        w.str(topic);
        w.i32(1);
        w.i32(0);  // partition
        w.bytes(buildRecordBatch("", value, nowMillis()));
        std::string payload;
        if (!conn_->request(API_PRODUCE, 3, w.buf, payload, localErr)) {
            err = localErr;
            if (conn_) conn_->close();
            continue;
        }
        Reader r(payload);
        const int32_t topicCount = r.arrayLen();
        int16_t code = ERR_NONE;
        for (int32_t t = 0; t < topicCount && r.ok(); ++t) {
            r.str();
            const int32_t partCount = r.arrayLen();
            for (int32_t i = 0; i < partCount && r.ok(); ++i) {
                r.i32();
                const int16_t c = r.i16();
                r.i64();
                r.i64();
                if (c != ERR_NONE && code == ERR_NONE) code = c;
            }
        }
        if (!r.ok()) {
            err = "Produce 响应解析失败";
            return false;
        }
        if (code == ERR_NONE) return true;
        err = errText("Produce", code);
        if (code == ERR_NOT_LEADER || code == ERR_UNKNOWN_TOPIC_OR_PARTITION) {
            leader_ = BrokerAddr{};
            if (conn_) conn_->close();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(400));
    }
    return false;
}

} // namespace cm::kafka
