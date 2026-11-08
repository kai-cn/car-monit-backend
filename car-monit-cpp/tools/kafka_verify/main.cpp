// Kafka 消费链路验收工具（对应 tools/db_verify、tools/redis_verify 的定位）。
//
// 用法：
//   set CM_VERIFY_KAFKA_BOOTSTRAP=127.0.0.1:9092
//   set CM_VERIFY_KAFKA_GROUP=cm-verify-group
//   set CM_VERIFY_KAFKA_TOPIC=cm-verify-snapshot-flow
//   set CM_VERIFY_KAFKA_DLQ=cm-verify-snapshot-flow-dlq
//   carmonit_kafka_verify [秒数]        # 默认 30 秒
//
// 判据：
//   1. 加入消费组并拉到消息（至少 1 条）
//   2. 处理后的 MySQL 行数 == 拉到的 INSERT/UPDATE 数（幂等去重后）
//   3. 发一条坏消息 → DLQ 中有对应记录
//   4. 重复投递同一批 → 幂等命中（不重复入库）
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <cstdio>
#include <map>
#include <string>
#include <thread>
#include <vector>

#include "cm/base/kafka/SnapshotFlowKafkaConsumer.hpp"
#include "cm/base/repository/SnapshotFlowRepository.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/kafka/KafkaClient.hpp"
#include "cm/framework/redis/RedisClient.hpp"

namespace {

std::string env(const char* k, const char* def) {
    const char* v = std::getenv(k);
    return (v && *v) ? std::string(v) : std::string(def);
}

int reportFailures = 0;
void report(bool ok, const std::string& name, const std::string& detail = "") {
    std::printf("[%s] %s%s%s\n", ok ? "PASS" : "FAIL", name.c_str(),
                detail.empty() ? "" : "  ", detail.c_str());
    if (!ok) ++reportFailures;
}

} // namespace

int main(int argc, char** argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    const int seconds = argc > 1 ? std::atoi(argv[1]) : 30;

    cm::config::AppConfig::instance().load("");
    auto& cfg = cm::config::AppConfig::instance();
    cm::log::Logger::instance().init("logs", "info");

    // MySQL / Redis 用与其它 verify 工具一致的环境变量
    cm::db::DbConfig dbc;
    dbc.host = env("CM_VERIFY_DB_HOST", "127.0.0.1");
    dbc.port = std::stoi(env("CM_VERIFY_DB_PORT", "3307"));
    dbc.user = env("CM_VERIFY_DB_USER", "root");
    dbc.password = env("CM_VERIFY_DB_PASS", "");
    dbc.database = env("CM_VERIFY_DB_NAME", "cm_verify_kafka");
    cm::db::Db::instance().init(dbc, 1, 1, 4, 3000, 64);
    report(cm::db::Db::instance().ready(), "MySQL 初始化");
    if (!cm::db::Db::instance().ready()) return 2;

    cm::redis::RedisConfig rc;
    rc.host = env("CM_VERIFY_REDIS_HOST", "127.0.0.1");
    rc.port = std::stoi(env("CM_VERIFY_REDIS_PORT", "6379"));
    rc.password = env("CM_VERIFY_REDIS_PASS", "");
    rc.timeoutMs = 5000;
    cm::redis::RedisCache::instance().init(rc);
    report(cm::redis::RedisCache::instance().client().ping(), "Redis PING");

    cm::kafka::KafkaConfig kc;
    kc.bootstrapServers = env("CM_VERIFY_KAFKA_BOOTSTRAP", "127.0.0.1:9092");
    kc.groupId = env("CM_VERIFY_KAFKA_GROUP", "cm-verify-group");
    kc.topic = env("CM_VERIFY_KAFKA_TOPIC", "cm-verify-snapshot-flow");
    kc.dlqTopic = env("CM_VERIFY_KAFKA_DLQ", "cm-verify-snapshot-flow-dlq");
    kc.concurrency = 1;
    kc.maxPollRecords = 500;
    kc.idempotentPrefix = "cm:verify:idempotent_";
    kc.idempotentTtlSeconds = 600;

    std::printf("=== Kafka: %s topic=%s group=%s ===\n", kc.bootstrapServers.c_str(),
                kc.topic.c_str(), kc.groupId.c_str());

    // 目标表：清空历史分表 + 活跃表（保证多次运行可复现），活跃表同时充当建表模板
    {
        auto old = cm::base::repository::SnapshotFlowRepository::instance().listShardingTables();
        for (const auto& t : old) {
            if (cm::base::repository::SnapshotFlowRepository::isKnownTableName(t)) {
                cm::db::Db::instance().execute("DROP TABLE IF EXISTS " + t);
            }
        }
        // 清掉本工具的幂等键，避免上一轮运行把本轮消息全部判成重复
        auto keys = cm::redis::RedisCache::instance().client().scanAll("cm:verify:idempotent_*");
        if (!keys.empty()) cm::redis::RedisCache::instance().client().del(keys);
    }
    cm::db::Db::instance().execute("DROP TABLE IF EXISTS ods_rt_szdn_snapshot_flow_addcode");
    cm::db::Db::instance().execute(
        "CREATE TABLE ods_rt_szdn_snapshot_flow_addcode ("
        "big_id VARCHAR(64) NOT NULL PRIMARY KEY, lon DOUBLE, lat DOUBLE, deviceip VARCHAR(64),"
        "siteid BIGINT, laneid INT, snapshottimeunix BIGINT, snapshottime DATETIME,"
        "receivedtimeunix BIGINT, receivedtime DATETIME, platenumber VARCHAR(32),"
        "platecolor VARCHAR(32), platecolorcode INT, platetype VARCHAR(32), platetypecode INT,"
        "plateconfidence INT, carbrand VARCHAR(64), carcolor VARCHAR(32), carcolorcode INT,"
        "cartype VARCHAR(32), cartypecode INT, cardirection VARCHAR(32),"
        "snappicturepath VARCHAR(512), smallpicturepath VARCHAR(512), plategnssstatus VARCHAR(32),"
        "gpsinfo VARCHAR(128), deviceid VARCHAR(64), devicename VARCHAR(128),"
        "devicetype VARCHAR(32), gantrycode VARCHAR(64), gantryname VARCHAR(128),"
        "roadcode VARCHAR(64), roadname VARCHAR(128), sectioncode VARCHAR(64),"
        "sectionname VARCHAR(128), tollcode VARCHAR(64), tollname VARCHAR(128),"
        "orgcode VARCHAR(64), orgname VARCHAR(128), direction INT, datasource VARCHAR(32),"
        "carclass VARCHAR(32), gantryid VARCHAR(64), smallsideimage VARCHAR(512),"
        "headimageheight INT, sidescenetypecode INT, sidescenetype VARCHAR(32),"
        "tailimagewidth INT, envstate VARCHAR(32), headscenetypecode INT,"
        "headscenetype VARCHAR(32), sidedrivingdirectioncode INT,"
        "sidedrivingdirection VARCHAR(32), sideimageheight INT, speed DOUBLE,"
        "tailplateimage VARCHAR(512), headdrivingdirectioncode INT,"
        "headdrivingdirection VARCHAR(32), laneidcode INT, carlength DOUBLE,"
        "imagelevel INT, cameratype VARCHAR(32)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");

    cm::base::kafka::SnapshotFlowKafkaConsumer::instance().configure(kc);
    cm::base::kafka::SnapshotFlowKafkaConsumer::instance().start();
    report(true, "消费线程已启动");
    const auto consumeStart = std::chrono::steady_clock::now();
    std::this_thread::sleep_for(std::chrono::seconds(seconds));
    cm::base::kafka::SnapshotFlowKafkaConsumer::instance().stop();
    const double elapsedSec =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - consumeStart).count();

    // 统计结果：消费按月份路由到分表（不一定是活跃表），逐表求和
    long long rows = 0;
    std::vector<std::string> tables{"ods_rt_szdn_snapshot_flow_addcode"};
    for (const auto& t : cm::base::repository::SnapshotFlowRepository::instance().listShardingTables()) {
        if (t != "ods_rt_szdn_snapshot_flow_addcode") tables.push_back(t);
    }
    for (const auto& t : tables) {
        if (!cm::base::repository::SnapshotFlowRepository::isKnownTableName(t)) continue;
        cm::db::Result r;
        if (cm::db::Db::instance().query("SELECT COUNT(*) AS c FROM " + t, r) && !r.rows.empty()) {
            rows += r.rows[0].i64("c");
        }
    }
    std::printf("--- 表: ");
    for (const auto& t : tables) std::printf("%s ", t.c_str());
    std::printf("---\n");
    const long long ok = cm::base::kafka::SnapshotFlowKafkaConsumer::instance().successCount();
    const long long failed = cm::base::kafka::SnapshotFlowKafkaConsumer::instance().failCount();
    const long long parsed = cm::base::kafka::SnapshotFlowKafkaConsumer::instance().parsedCount();
    const long long latCount = cm::base::kafka::SnapshotFlowKafkaConsumer::instance().latencyCount();
    const long long latTotal = cm::base::kafka::SnapshotFlowKafkaConsumer::instance().latencyTotalMs();
    const long long latMax = cm::base::kafka::SnapshotFlowKafkaConsumer::instance().latencyMaxMs();
    std::printf("--- 结果: 入库行数=%lld 成功计数=%lld 失败计数=%lld 消费条数=%lld ---\n", rows, ok,
                failed, parsed);
    // 吞吐与端到端延迟（CreateTime → 处理完成）
    const double throughput = elapsedSec > 0 ? static_cast<double>(parsed) / elapsedSec : 0.0;
    const double avgLatency = latCount > 0 ? static_cast<double>(latTotal) / latCount : 0.0;
    std::printf("--- 吞吐: %.1f 条/秒 (窗口 %.1fs) | 延迟: 平均 %.1fms 最大 %lldms (样本 %lld) ---\n",
                throughput, elapsedSec, avgLatency, latMax, latCount);
    report(ok > 0, "拉取并处理了消息", "success=" + std::to_string(ok));
    report(rows > 0, "MySQL 有落库数据", "rows=" + std::to_string(rows));

    // 期望值由灌消息脚本传入（不假设具体条数，保持工具通用）
    const char* expectRows = std::getenv("CM_VERIFY_EXPECT_ROWS");
    if (expectRows && *expectRows) {
        report(rows == std::atoll(expectRows), "落库行数符合预期",
               "rows=" + std::to_string(rows) + " expect=" + expectRows);
    }
    const char* expectOk = std::getenv("CM_VERIFY_EXPECT_SUCCESS");
    if (expectOk && *expectOk) {
        report(ok == std::atoll(expectOk), "成功计数符合预期",
               "success=" + std::to_string(ok) + " expect=" + expectOk);
    }
    const char* expectFail = std::getenv("CM_VERIFY_EXPECT_FAIL_MIN");
    if (expectFail && *expectFail) {
        report(failed >= std::atoll(expectFail), "失败计数符合预期",
               "failed=" + std::to_string(failed) + " expect>=" + expectFail);
    }

    // ---- DLQ 条数：独立消费组从最早开始读死信 topic（topic 应每轮重建，否则会累计历史） ----
    long long dlqCount = 0;
    {
        cm::kafka::KafkaConfig dlqCfg = kc;
        dlqCfg.topic = kc.dlqTopic;
        dlqCfg.groupId = kc.groupId + "-dlq-counter";
        dlqCfg.fromBeginning = true;
        cm::kafka::KafkaConsumer counter(dlqCfg);
        std::string err;
        if (!counter.open(err)) {
            report(false, "DLQ 查询消费者启动", err);
        } else {
            while (true) {
                std::vector<cm::kafka::ConsumedRecord> batch;
                if (!counter.poll(batch, 1500, err)) {
                    report(false, "DLQ 读取失败", err);
                    break;
                }
                if (batch.empty()) break;
                dlqCount += static_cast<long long>(batch.size());
            }
            counter.close();
        }
    }
    std::printf("--- DLQ 条数=%lld topic=%s ---\n", dlqCount, kc.dlqTopic.c_str());
    const char* expectDlq = std::getenv("CM_VERIFY_EXPECT_DLQ");
    if (expectDlq && *expectDlq) {
        report(dlqCount == std::atoll(expectDlq), "DLQ 条数符合预期",
               "dlq=" + std::to_string(dlqCount) + " expect=" + expectDlq);
    }

    // ---- 位点提交：主消费线程停止后，用同一消费组查询已提交位点 ----
    {
        cm::kafka::KafkaConsumer probe(kc);
        std::string err;
        std::map<int32_t, int64_t> committed;
        if (!probe.open(err)) {
            report(false, "查询位点提交", err);
        } else if (!probe.committedOffsets(committed, err)) {
            report(false, "查询位点提交", err);
        } else {
            for (const auto& kv : committed) {
                std::printf("--- 提交位点: partition=%d nextOffset=%lld ---\n", kv.first, kv.second);
            }
            report(!committed.empty(), "存在已提交位点",
                   "partitions=" + std::to_string(committed.size()));
        }
        probe.close();
    }

    std::printf("%d passed, %d failed\n", reportFailures == 0 ? 1 : 0, reportFailures);
    return reportFailures == 0 ? 0 : 1;
}
