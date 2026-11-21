// Kafka 客户端配置 + 快照流分表/ES 文档映射的单测（不依赖真实 broker）。
#include <string>
#include <vector>

#include "cm/base/kafka/SnapshotFlowKafkaConsumer.hpp"
#include "cm/base/repository/SnapshotFlowRepository.hpp"
#include "cm/framework/kafka/KafkaClient.hpp"

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

/** KafkaConfig 的默认值必须与 Java KafkaConfig/application.yml 一致 */
static void testKafkaConfigDefaults() {
    cm::kafka::KafkaConfig cfg;
    CK_EQ(cfg.groupId, std::string("snapshot-flow-consumer-group"));
    CK_EQ(cfg.maxPollRecords, 500);
    CK_EQ(cfg.maxPollIntervalMs, 300000);
    CK_EQ(cfg.fetchMaxBytes, 52428800);
    CK_EQ(cfg.sessionTimeoutMs, 60000);
    CK_EQ(cfg.concurrency, 3);
    CK(cfg.fromBeginning);  // auto-offset-reset=earliest
}

static void testBootstrapParse() {
    auto one = cm::kafka::parseBootstrapServers("127.0.0.1:9092");
    CK_EQ(one.size(), static_cast<size_t>(1));
    if (one.size() == 1) {
        CK_EQ(one[0].host, std::string("127.0.0.1"));
        CK_EQ(one[0].port, 9092);
    }

    auto two = cm::kafka::parseBootstrapServers("10.0.0.1:9092, 10.0.0.2:9093");
    CK_EQ(two.size(), static_cast<size_t>(2));
    if (two.size() == 2) {
        CK_EQ(two[1].host, std::string(" 10.0.0.2"));
        CK_EQ(two[1].port, 9093);
    }

    auto noPort = cm::kafka::parseBootstrapServers("broker.local");
    CK_EQ(noPort.size(), static_cast<size_t>(1));
    if (noPort.size() == 1) CK_EQ(noPort[0].port, 9092);

    CK_EQ(cm::kafka::parseBootstrapServers("").size(), static_cast<size_t>(0));
    CK_EQ(cm::kafka::parseBootstrapServers(",,").size(), static_cast<size_t>(0));
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
    testKafkaConfigDefaults();
    testBootstrapParse();
    testShardingRoute();
    testEsDocument();
}
