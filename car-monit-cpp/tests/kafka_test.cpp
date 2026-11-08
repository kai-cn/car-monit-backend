// Kafka 协议层 + 快照流分表/ES 文档映射的单测（不依赖真实 broker）。
#include <string>
#include <vector>

#include "cm/base/kafka/SnapshotFlowKafkaConsumer.hpp"
#include "cm/base/repository/SnapshotFlowRepository.hpp"
#include "cm/framework/kafka/KafkaCodec.hpp"

using cm::Json;

extern int g_fails;
#define fails g_fails
#define CK(x)                                                             \
    do {                                                                  \
        if (!(x)) {                                                       \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);       \
            ++fails;                                                      \
        }                                                                 \
    } while (0)
#define CK_EQ(a, b)                                                         \
    do {                                                                    \
        auto _va = (a);                                                     \
        auto _vb = (b);                                                     \
        if (!(_va == _vb)) {                                                \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                                        \
        }                                                                   \
    } while (0)

static void testCrc32c() {
    // RFC 3720 标准向量
    CK_EQ(cm::kafka::crc32c("123456789", 9), 0xE3069283u);
    CK_EQ(cm::kafka::crc32c("", 0), 0u);
}

static void testBatchRoundTripSingle() {
    const std::string value = "{\"operationType\":\"INSERT\",\"data\":{\"bigId\":\"9001\",\"platenumber\":\"云A12345\"}}";
    const std::string batch = cm::kafka::buildRecordBatch("", value, 1762500000000LL);
    std::vector<cm::kafka::ConsumedRecord> out;
    std::string err;
    CK(cm::kafka::parseRecordSet(batch, out, err));
    CK(err.empty());
    CK_EQ(out.size(), static_cast<size_t>(1));
    if (out.size() == 1) {
        CK_EQ(out[0].value, value);
        CK(!out[0].hasKey);  // 空 key == null key
        CK_EQ(out[0].offset, 0LL);
        CK_EQ(out[0].timestamp, 1762500000000LL);
    }
}

static void testBatchRoundTripMulti() {
    std::vector<std::pair<std::string, std::string>> records;
    records.emplace_back("k1", "v1");
    records.emplace_back("", "中文值-2");
    records.emplace_back("k3", std::string(1000, 'x'));
    const std::string batch = cm::kafka::buildRecordBatch(records, 1762500001000LL);
    std::vector<cm::kafka::ConsumedRecord> out;
    std::string err;
    CK(cm::kafka::parseRecordSet(batch, out, err));
    CK_EQ(out.size(), static_cast<size_t>(3));
    if (out.size() == 3) {
        CK_EQ(out[0].key, std::string("k1"));
        CK_EQ(out[0].value, std::string("v1"));
        CK(out[0].hasKey);
        CK_EQ(out[1].value, std::string("中文值-2"));
        CK(!out[1].hasKey);
        CK_EQ(out[2].value.size(), static_cast<size_t>(1000));
        CK_EQ(out[2].offset, 2LL);
    }
}

static void testBatchTrailingTruncation() {
    const std::string batch =
        cm::kafka::buildRecordBatch("k", "v", 1762500000000LL);
    // 模拟抓取窗口在批次中间截断：解析器应保留已解析内容而不是报错
    std::string truncated = batch.substr(0, batch.size() - 3);
    std::vector<cm::kafka::ConsumedRecord> out;
    std::string err;
    CK(cm::kafka::parseRecordSet(truncated, out, err));
    CK_EQ(out.size(), static_cast<size_t>(0));
}

static void testLegacyMessageSet() {
    // 手工构造 magic=0 的 message set：offset + size + crc + magic + attrs + keyLen + key + valLen + value
    using cm::kafka::Writer;
    Writer msg;
    msg.i8(0);   // magic
    msg.i8(0);   // attributes
    msg.i32(-1); // key = null
    msg.i32(2);
    msg.raw("hi");
    Writer out;
    out.i64(7);                            // offset
    out.i32(static_cast<int32_t>(msg.buf.size()));  // size
    out.raw(msg.buf);                      // 注意：真实报文这里先有 4 字节 crc，但解析器会跳过前 4 字节
    // 上面的写法把 magic 放在了 crc 的位置；重新按真实布局构造：
    Writer real;
    real.i64(7);
    Writer body;
    body.i32(0);  // crc 占位
    body.i8(0);   // magic
    body.i8(0);   // attrs
    body.i32(-1); // key
    body.i32(2);
    body.raw("hi");
    real.i32(static_cast<int32_t>(body.buf.size()));
    real.raw(body.buf);

    std::vector<cm::kafka::ConsumedRecord> records;
    std::string err;
    CK(cm::kafka::parseRecordSet(real.buf, records, err));
    CK_EQ(records.size(), static_cast<size_t>(1));
    if (records.size() == 1) {
        CK_EQ(records[0].offset, 7LL);
        CK_EQ(records[0].value, std::string("hi"));
        CK(!records[0].hasKey);
    }
    (void)out;
}

static void testShardingRoute() {
    using cm::base::repository::SnapshotFlowRepository;
    Json row = Json::object();
    row["bigId"] = "1";
    row["snapshottime"] = 1735689600000LL;  // 2025-01-01 08:00 +08:00
    auto t = SnapshotFlowRepository::monthTableForRow(row);
    CK(t.has_value());
    if (t) CK_EQ(*t, std::string("ods_rt_szdn_snapshot_flow_202501"));

    Json row2 = Json::object();
    row2["bigId"] = "2";
    row2["snapshottime"] = "2024-12-31 23:59:59";
    auto t2 = SnapshotFlowRepository::monthTableForRow(row2);
    CK(t2.has_value());
    if (t2) CK_EQ(*t2, std::string("ods_rt_szdn_snapshot_flow_202412"));

    Json row3 = Json::object();
    row3["bigId"] = "3";
    CK(!SnapshotFlowRepository::monthTableForRow(row3).has_value());

    CK(SnapshotFlowRepository::isKnownTableName("ods_rt_szdn_snapshot_flow_addcode"));
    CK(SnapshotFlowRepository::isKnownTableName("ods_rt_szdn_snapshot_flow_202501"));
    CK(!SnapshotFlowRepository::isKnownTableName("ods_rt_szdn_snapshot_flow_20250"));
    CK(!SnapshotFlowRepository::isKnownTableName("ods_rt_szdn_snapshot_flow_202501; drop"));
    CK(!SnapshotFlowRepository::isKnownTableName("other_table"));
}

static void testEsDocument() {
    Json row = Json::object();
    row["bigId"] = "abc";
    row["platenumber"] = "云A123";
    row["platenumber"] = "云A123";
    row["snapshottime"] = 1762500000000LL;
    row["receivedtime"] = "2025-11-07 10:00:00";
    row["reserve3"] = nullptr;
    row["unknownField"] = "ignored";
    const Json doc = cm::base::kafka::snapshotFlowEsDocument(row);
    CK(doc.contains("bigId"));
    CK_EQ(doc["bigId"].get<std::string>(), std::string("abc"));
    CK(doc.contains("snapshottime"));
    CK(doc["snapshottime"].is_number_integer());
    CK(doc.contains("receivedtime"));
    CK(doc["receivedtime"].is_number_integer());  // 字符串日期 -> epoch 毫秒
    CK(!doc.contains("reserve3"));                // null 字段省略
    CK(!doc.contains("unknownField"));            // 不在 SnapshotFlowDocument 字段集里
}

void run_kafka_tests() {
    testCrc32c();
    testBatchRoundTripSingle();
    testBatchRoundTripMulti();
    testBatchTrailingTruncation();
    testLegacyMessageSet();
    testShardingRoute();
    testEsDocument();
}
