#include "cm/framework/kafka/KafkaCodec.hpp"

#include <cstring>

#include "cm/common/utils/Inflate.hpp"

namespace cm::kafka {
namespace {

uint32_t crc32cTable[256];
bool crc32cReady = false;

void initCrc32c() {
    if (crc32cReady) return;
    for (uint32_t i = 0; i < 256; ++i) {
        uint32_t c = i;
        for (int k = 0; k < 8; ++k) c = (c & 1) ? (0x82f63b78u ^ (c >> 1)) : (c >> 1);
        crc32cTable[i] = c;
    }
    crc32cReady = true;
}

inline void putBE16(std::string& b, uint16_t v) {
    b.push_back(static_cast<char>((v >> 8) & 0xFF));
    b.push_back(static_cast<char>(v & 0xFF));
}
inline void putBE32(std::string& b, uint32_t v) {
    b.push_back(static_cast<char>((v >> 24) & 0xFF));
    b.push_back(static_cast<char>((v >> 16) & 0xFF));
    b.push_back(static_cast<char>((v >> 8) & 0xFF));
    b.push_back(static_cast<char>(v & 0xFF));
}
inline void putBE64(std::string& b, uint64_t v) {
    putBE32(b, static_cast<uint32_t>(v >> 32));
    putBE32(b, static_cast<uint32_t>(v & 0xFFFFFFFFu));
}

/** 读一条记录（RecordBatch 内的 record 结构），pos 前进到记录末尾 */
bool parseRecord(Reader& r, int64_t baseOffset, int64_t firstTimestamp, ConsumedRecord& out,
                 std::string& err) {
    const int64_t len = r.varint();
    if (len < 0) {
        err = "record 长度为负";
        return false;
    }
    const size_t end = r.pos() + static_cast<size_t>(len);
    out.partition = out.partition;  // 由调用方填
    r.i8();                          // attributes（含 header 的压缩/控制位，这里不用）
    const int64_t tsDelta = r.varint();
    const int64_t offsetDelta = r.varint();

    const int64_t keyLen = r.varint();
    if (keyLen >= 0) {
        std::string_view k = r.view(static_cast<size_t>(keyLen));
        out.key.assign(k.data(), k.size());
        out.hasKey = true;
    } else {
        out.hasKey = false;
        out.key.clear();
    }
    const int64_t valLen = r.varint();
    if (valLen >= 0) {
        std::string_view v = r.view(static_cast<size_t>(valLen));
        out.value.assign(v.data(), v.size());
    } else {
        out.value.clear();  // Kafka 的 tombstone：null value
    }
    const int64_t headerCount = r.varint();
    for (int64_t i = 0; i < headerCount; ++i) {
        const int64_t hkLen = r.varint();
        if (hkLen > 0) r.skip(static_cast<size_t>(hkLen));
        const int64_t hvLen = r.varint();
        if (hvLen > 0) r.skip(static_cast<size_t>(hvLen));
    }
    if (!r.ok()) {
        err = r.error() ? *r.error() : "record 解析越界";
        return false;
    }
    // 跳过记录尾部的对齐字节
    if (r.pos() < end) r.skip(end - r.pos());
    out.offset = baseOffset + offsetDelta;
    out.timestamp = firstTimestamp + tsDelta;
    return true;
}

/** legacy（magic=0/1）消息集合 */
bool parseLegacyMessageSet(Reader& r, std::vector<ConsumedRecord>& out, std::string& err) {
    while (r.remaining() >= 12) {
        const int64_t offset = r.i64();
        const int32_t msgSize = r.i32();
        if (msgSize < 0) {
            err = "legacy message 长度为负";
            return false;
        }
        if (static_cast<size_t>(msgSize) > r.remaining()) {
            err = "legacy message 长度越界";
            return false;
        }
        const size_t msgStart = r.pos();
        r.i32();  // crc
        const int8_t magic = r.i8();
        const int8_t attrs = r.i8();
        int64_t ts = 0;
        if (magic == 1) ts = r.i64();
        std::string key, value;
        const int32_t keyLen = r.i32();
        bool hasKey = false;
        if (keyLen >= 0) {
            std::string_view k = r.view(static_cast<size_t>(keyLen));
            key.assign(k.data(), k.size());
            hasKey = true;
        }
        const int32_t valLen = r.i32();
        if (valLen >= 0) {
            std::string_view v = r.view(static_cast<size_t>(valLen));
            value.assign(v.data(), v.size());
        }
        if (!r.ok()) {
            err = r.error() ? *r.error() : "legacy message 解析越界";
            return false;
        }
        r.skip(msgStart + static_cast<size_t>(msgSize) - r.pos());  // 对齐到 msg 末尾
        if ((attrs & 0x07) != 0) {
            err = "legacy message 使用了不支持的压缩编码";
            return false;
        }
        ConsumedRecord rec;
        rec.offset = offset;
        rec.timestamp = ts;
        rec.key = std::move(key);
        rec.hasKey = hasKey;
        rec.value = std::move(value);
        out.push_back(std::move(rec));
    }
    return true;
}

} // namespace

void Writer::i16(int16_t v) { putBE16(buf, static_cast<uint16_t>(v)); }
void Writer::i32(int32_t v) { putBE32(buf, static_cast<uint32_t>(v)); }
void Writer::i64(int64_t v) { putBE64(buf, static_cast<uint64_t>(v)); }

void Writer::str(const std::string& v) {
    if (v.size() > 0x7FFF) {  // Kafka 的 STRING 上限就是 INT16
        i16(-1);
        return;
    }
    i16(static_cast<int16_t>(v.size()));
    buf.append(v);
}

void Writer::nullableStr(bool present, const std::string& v) {
    if (!present) {
        i16(-1);
        return;
    }
    str(v);
}

void Writer::bytes(const std::string& v) {
    i32(static_cast<int32_t>(v.size()));
    buf.append(v);
}

void Writer::nullableBytes(bool present, const std::string& v) {
    if (!present) {
        i32(-1);
        return;
    }
    bytes(v);
}

void Writer::varint(int64_t v) {
    uint64_t u = (static_cast<uint64_t>(v) << 1) ^ static_cast<uint64_t>(v >> 63);
    while (u >= 0x80) {
        buf.push_back(static_cast<char>((u & 0x7F) | 0x80));
        u >>= 7;
    }
    buf.push_back(static_cast<char>(u));
}

void Reader::fail(const std::string& msg) {
    if (ok_) {
        ok_ = false;
        err_ = msg;
    }
}

bool Reader::skip(size_t n) {
    if (!ok_) return false;
    if (pos_ + n > n_) {
        fail("读取越界（skip）");
        return false;
    }
    pos_ += n;
    return true;
}

int8_t Reader::i8() {
    if (!ok_) return 0;
    if (pos_ + 1 > n_) {
        fail("读取越界（i8）");
        return 0;
    }
    return static_cast<int8_t>(p_[pos_++]);
}

int16_t Reader::i16() {
    if (!ok_) return 0;
    if (pos_ + 2 > n_) {
        fail("读取越界（i16）");
        return 0;
    }
    const auto v = static_cast<uint16_t>((static_cast<uint8_t>(p_[pos_]) << 8) |
                                         static_cast<uint8_t>(p_[pos_ + 1]));
    pos_ += 2;
    return static_cast<int16_t>(v);
}

int32_t Reader::i32() {
    if (!ok_) return 0;
    if (pos_ + 4 > n_) {
        fail("读取越界（i32）");
        return 0;
    }
    const auto v = (static_cast<uint32_t>(static_cast<uint8_t>(p_[pos_])) << 24) |
                   (static_cast<uint32_t>(static_cast<uint8_t>(p_[pos_ + 1])) << 16) |
                   (static_cast<uint32_t>(static_cast<uint8_t>(p_[pos_ + 2])) << 8) |
                   static_cast<uint32_t>(static_cast<uint8_t>(p_[pos_ + 3]));
    pos_ += 4;
    return static_cast<int32_t>(v);
}

int64_t Reader::i64() {
    const uint64_t hi = static_cast<uint32_t>(i32());
    const uint64_t lo = static_cast<uint32_t>(i32());
    return static_cast<int64_t>((hi << 32) | lo);
}

std::string Reader::str() {
    const int16_t len = i16();
    if (len < 0) return {};
    return std::string(view(static_cast<size_t>(len)));
}

bool Reader::nullableStr(std::string& out) {
    const int16_t len = i16();
    if (len < 0) {
        out.clear();
        return false;
    }
    out.assign(view(static_cast<size_t>(len)));
    return true;
}

std::string Reader::bytes() {
    const int32_t len = i32();
    if (len < 0) return {};
    return std::string(view(static_cast<size_t>(len)));
}

bool Reader::nullableBytes(std::string& out) {
    const int32_t len = i32();
    if (len < 0) {
        out.clear();
        return false;
    }
    out.assign(view(static_cast<size_t>(len)));
    return true;
}

int32_t Reader::arrayLen() { return i32(); }

int64_t Reader::varint() {
    uint64_t u = 0;
    int shift = 0;
    for (;;) {
        if (!ok_) return 0;
        const uint8_t b = static_cast<uint8_t>(i8());
        u |= static_cast<uint64_t>(b & 0x7F) << shift;
        if ((b & 0x80) == 0) break;
        shift += 7;
        if (shift > 63) {
            fail("varint 过长");
            return 0;
        }
    }
    return static_cast<int64_t>((u >> 1) ^ (~(u & 1) + 1));
}

std::string_view Reader::view(size_t n) {
    if (!ok_) return {};
    if (pos_ + n > n_) {
        fail("读取越界（bytes）");
        return {};
    }
    std::string_view v(p_ + pos_, n);
    pos_ += n;
    return v;
}

uint32_t crc32c(const char* data, size_t n) {
    initCrc32c();
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < n; ++i) {
        crc = crc32cTable[(crc ^ static_cast<uint8_t>(data[i])) & 0xFF] ^ (crc >> 8);
    }
    return crc ^ 0xFFFFFFFFu;
}

bool parseRecordSet(std::string_view data, std::vector<ConsumedRecord>& out, std::string& err) {
    Reader r(data);
    while (r.remaining() >= 12) {
        const size_t batchStart = r.pos();
        const int64_t baseOffset = r.i64();
        const int32_t batchLen = r.i32();
        if (batchLen < 0) {
            err = "RecordBatch 长度为负";
            return false;
        }
        if (static_cast<size_t>(batchLen) > r.remaining()) {
            // 抓取窗口在批次中间截断：保留已解析的消息，不视为错误
            break;
        }
        const size_t batchEnd = r.pos() + static_cast<size_t>(batchLen);
        const int32_t leaderEpoch = r.i32();
        (void)leaderEpoch;
        const int8_t magic = r.i8();

        if (magic == 2) {
            r.i32();  // crc
            const int16_t attributes = r.i16();
            r.i32();  // lastOffsetDelta
            const int64_t firstTs = r.i64();
            r.i64();  // maxTimestamp
            r.i64();  // producerId
            r.i16();  // producerEpoch
            r.i32();  // baseSequence
            const int32_t count = r.i32();
            const int codec = attributes & 0x07;
            if (count < 0) {
                err = "RecordBatch 记录数为负";
                return false;
            }
            std::string payload;
            if (codec == 0) {
                std::string_view sv = r.view(batchEnd - r.pos());
                if (!r.ok()) {
                    err = "RecordBatch 数据越界";
                    return false;
                }
                payload.assign(sv.data(), sv.size());
            } else if (codec == 1) {
                std::string_view rest = r.view(batchEnd - r.pos());
                if (!r.ok()) {
                    err = "RecordBatch 数据越界";
                    return false;
                }
                if (!cm::utils::inflateGzip(rest, payload, &err)) return false;
            } else {
                err = "不支持的 RecordBatch 压缩编码: " + std::to_string(codec) +
                      "（仅支持 none/gzip）";
                return false;
            }
            Reader rr(payload);
            for (int32_t i = 0; i < count; ++i) {
                ConsumedRecord rec;
                if (!parseRecord(rr, baseOffset, firstTs, rec, err)) return false;
                out.push_back(std::move(rec));
            }
            // 对齐到批次末尾（含可能的 padding）
            r.skip(batchEnd - r.pos());
        } else if (magic == 0 || magic == 1) {
            // legacy：回到批次起点按 message set 解析
            Reader lr(data.substr(batchStart));
            std::vector<ConsumedRecord> legacy;
            if (!parseLegacyMessageSet(lr, legacy, err)) return false;
            for (auto& rec : legacy) out.push_back(std::move(rec));
            // legacy 内部会把整段消费完；剩余不足 12 字节时结束
            r.skip(data.size() - r.pos());
            break;
        } else {
            err = "未知的 RecordBatch magic: " + std::to_string(static_cast<int>(magic));
            return false;
        }
    }
    return true;
}

std::string buildRecordBatch(const std::string& key, const std::string& value,
                             int64_t timestampMs) {
    return buildRecordBatch(std::vector<std::pair<std::string, std::string>>{{key, value}},
                            timestampMs);
}

std::string buildRecordBatch(const std::vector<std::pair<std::string, std::string>>& records,
                             int64_t timestampMs) {
    Writer body;
    body.i32(-1);  // partitionLeaderEpoch
    body.i8(2);    // magic
    body.i32(0);   // crc 占位
    body.i16(0);   // attributes：无压缩、CreateTime
    body.i32(static_cast<int32_t>(records.size()) - 1);  // lastOffsetDelta
    body.i64(timestampMs);
    body.i64(timestampMs);
    body.i64(-1);  // producerId
    body.i16(-1);  // producerEpoch
    body.i32(-1);  // baseSequence
    body.i32(static_cast<int32_t>(records.size()));

    for (size_t i = 0; i < records.size(); ++i) {
        Writer rec;
        rec.i8(0);              // record attributes
        rec.varint(0);          // timestampDelta
        rec.varint(static_cast<int64_t>(i));  // offsetDelta
        if (records[i].first.empty()) {
            rec.varint(-1);     // null key（对应 Java kafkaTemplate.send(topic, value)）
        } else {
            rec.varint(static_cast<int64_t>(records[i].first.size()));
            rec.raw(records[i].first);
        }
        rec.varint(static_cast<int64_t>(records[i].second.size()));
        rec.raw(records[i].second);
        rec.varint(0);          // headers
        body.varint(static_cast<int64_t>(rec.buf.size()));
        body.raw(rec.buf);
    }

    // crc 覆盖 attributes 起到末尾（即偏移 4+1+4 = 9 之后）
    const uint32_t crc = crc32c(body.buf.data() + 9, body.buf.size() - 9);
    body.buf[5] = static_cast<char>((crc >> 24) & 0xFF);
    body.buf[6] = static_cast<char>((crc >> 16) & 0xFF);
    body.buf[7] = static_cast<char>((crc >> 8) & 0xFF);
    body.buf[8] = static_cast<char>(crc & 0xFF);

    Writer out;
    out.i64(0);  // baseOffset：producer 发送时由 broker 重写
    out.i32(static_cast<int32_t>(body.buf.size()));
    out.raw(body.buf);
    return out.buf;
}

} // namespace cm::kafka
