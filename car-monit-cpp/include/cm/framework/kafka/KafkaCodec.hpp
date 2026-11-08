#pragma once
// Kafka 二进制协议编解码（最小子集）+ RecordBatch v2 解析/构造。
//
// 为什么自研：工程承诺"clone 即可构建"，本机没有任何 Kafka C/C++ 客户端库可 vendor
// （librdkafka 未安装且体积大）。我们只需要一个消费者 + DLQ 生产者，
// 协议子集足以覆盖：ApiVersions / Metadata / FindCoordinator / JoinGroup / SyncGroup /
// Heartbeat / OffsetFetch / OffsetCommit / ListOffsets / Fetch / LeaveGroup / Produce。
//
// 报文版本一律用**非 flexible 版本**（Kafka 0.10~2.x 全支持）：没有 tagged fields，
// 结构简单、易核对。RecordBatch 支持 magic=2（0.11+）与 legacy magic=0/1，
// 压缩只支持 none / gzip（gzip 复用 cm::utils::inflateGzip，与 xlsx 同一套实现）。
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace cm::kafka {

// ---------------------------------------------------------------------------
// 写
// ---------------------------------------------------------------------------
class Writer {
public:
    std::string buf;

    void i8(int8_t v) { buf.push_back(static_cast<char>(v)); }
    void i16(int16_t v);
    void i32(int32_t v);
    void i64(int64_t v);
    /** INT16 长度前缀的字符串（不可为 null） */
    void str(const std::string& v);
    /** INT16 长度前缀；absent=true 时写 -1 */
    void nullableStr(bool present, const std::string& v);
    /** INT32 长度前缀的字节串（不可为 null） */
    void bytes(const std::string& v);
    /** INT32 长度前缀；absent=true 时写 -1 */
    void nullableBytes(bool present, const std::string& v);
    void raw(const char* p, size_t n) { buf.append(p, n); }
    void raw(const std::string& s) { buf.append(s); }

    /** Kafka 的 varint/varlong 都是 zig-zag 编码 */
    void varint(int64_t v);
};

// ---------------------------------------------------------------------------
// 读
// ---------------------------------------------------------------------------
class Reader {
public:
    Reader(const char* p, size_t n) : p_(p), n_(n) {}
    explicit Reader(const std::string& s) : p_(s.data()), n_(s.size()) {}
    explicit Reader(std::string_view s) : p_(s.data()), n_(s.size()) {}

    bool ok() const { return ok_; }
    size_t pos() const { return pos_; }
    size_t remaining() const { return ok_ ? n_ - pos_ : 0; }
    bool skip(size_t n);

    int8_t i8();
    int16_t i16();
    int32_t i32();
    int64_t i64();
    std::string str();
    /** 返回 false 表示 null（长度 -1） */
    bool nullableStr(std::string& out);
    std::string bytes();
    bool nullableBytes(std::string& out);
    /** 读 array 长度；-1（null）也返回 -1，由调用方决定是否当 0 处理 */
    int32_t arrayLen();
    int64_t varint();
    /** 读取 [pos, pos+n) 的视图（不拷贝） */
    std::string_view view(size_t n);

    const std::string* error() const { return ok_ ? nullptr : &err_; }
    void fail(const std::string& msg);

private:
    const char* p_;
    size_t n_;
    size_t pos_{0};
    bool ok_{true};
    std::string err_;
};

// ---------------------------------------------------------------------------
// CRC32C（Castagnoli，Kafka RecordBatch 用）
// ---------------------------------------------------------------------------
uint32_t crc32c(const char* data, size_t n);
inline uint32_t crc32c(const std::string& s) { return crc32c(s.data(), s.size()); }

// ---------------------------------------------------------------------------
// 消息
// ---------------------------------------------------------------------------
struct ConsumedRecord {
    std::string key;
    bool hasKey{false};
    std::string value;
    int32_t partition{0};
    int64_t offset{0};
    int64_t timestamp{0};
};

/**
 * 解析 Fetch 响应里的 records 字节串（可能是多个 RecordBatch 拼接）。
 * 支持 magic=2（含 gzip 压缩）与 legacy magic=0/1（不压缩）。
 * 失败返回 false 并写 err（例如遇到 snappy/lz4/zstd 压缩）。
 */
bool parseRecordSet(std::string_view data, std::vector<ConsumedRecord>& out, std::string& err);

/** 构造单条消息的 RecordBatch（magic=2，不压缩，CreateTime）。key 为空表示 null key。 */
std::string buildRecordBatch(const std::string& key, const std::string& value, int64_t timestampMs);

/** 构造包含多条消息的 RecordBatch（producer 用；offsetDelta 从 0 递增）。 */
std::string buildRecordBatch(const std::vector<std::pair<std::string, std::string>>& records,
                             int64_t timestampMs);

} // namespace cm::kafka
