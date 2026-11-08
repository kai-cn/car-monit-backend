// 对应 Java: com.ruoyi.RuoYiApplication（Spring Boot 启动类）
//
// 启动顺序：
//   1. 加载 config/application.yaml + application-druid.yaml
//   2. 初始化日志
//   3. 初始化 MySQL 连接池 / Redis
//   4. 配置 TokenService（token.header / secret / expireTime）
//   5. 注册路由（对应 @RestController 扫描）
//   6. 启动内嵌 HTTP 服务
#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <string>
#include <thread>

#include "cm/common/utils/Logger.hpp"
#include "cm/base/kafka/SnapshotFlowKafkaConsumer.hpp"
#include "cm/framework/aspect/OperLogAspect.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/es/EsClient.hpp"
#include "cm/framework/kafka/KafkaClient.hpp"
#include "cm/framework/http/HttpResponse.hpp"
#include "cm/framework/net/HttpClient.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/security/TokenService.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/Server.hpp"
#include "cm/web/controller/Controllers.hpp"

namespace {

std::atomic<bool> g_running{true};

void onSignal(int sig) {
    (void)sig;
    g_running.store(false);
}

int envInt(const char* name, int def) {
    const char* v = std::getenv(name);
    if (!v || !*v) return def;
    try {
        return std::stoi(v);
    } catch (...) {
        return def;
    }
}

} // namespace

int main(int argc, char** argv) {
    std::string config_dir;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if ((a == "--config" || a == "-c") && i + 1 < argc) config_dir = argv[++i];
        else if (a.rfind("--config=", 0) == 0) config_dir = a.substr(9);
    }

    auto& cfg = cm::config::AppConfig::instance();
    cfg.load(config_dir);

    cm::log::Logger::instance().init(cfg.logDir, cfg.logLevel);
    LOG_INFO("main", "car-monit-cpp 启动，配置目录=" + (config_dir.empty() ? "config" : config_dir));

    // ---- 出站 HTTPS：注入 CA 证书包（留空则走 CM_CA_BUNDLE / third_party/cacert.pem）----
    cm::net::HttpClient::setDefaultCaBundle(cfg.httpCaBundle);
    LOG_INFO("main", "出站 HTTPS CA=" +
                         (cm::net::HttpClient::defaultCaBundle().empty()
                              ? std::string("(未找到，https 请求会失败)")
                              : cm::net::HttpClient::defaultCaBundle()));

    // ---- MySQL ----
    cm::db::DbConfig dbc;
    dbc.host = cfg.dbHost;
    dbc.port = cfg.dbPort;
    dbc.user = cfg.dbUser;
    dbc.password = cfg.dbPassword;
    dbc.database = cfg.dbName;
    dbc.charset = cfg.dbCharset;
    dbc.connectTimeoutMs = cfg.dbConnectTimeoutMs;
    dbc.socketTimeoutMs = cfg.dbSocketTimeoutMs;
    cm::db::Db::instance().init(dbc, cfg.dbInitialSize, cfg.dbMinIdle, cfg.dbMaxActive,
                                cfg.dbMaxWaitMs, cfg.dbPreparedCacheMax);
    if (!cm::db::Db::instance().pool().pingAll()) {
        LOG_WARN("main", "MySQL 不可用，服务继续启动（登录等需要数据库的接口会失败）");
    }

    // ---- Redis ----
    cm::redis::RedisConfig rc;
    rc.host = cfg.redisHost;
    rc.port = cfg.redisPort;
    rc.database = cfg.redisDatabase;
    rc.password = cfg.redisPassword;
    rc.timeoutMs = cfg.redisTimeoutMs;
    try {
        cm::redis::RedisCache::instance().init(rc);
        if (!cm::redis::RedisCache::instance().client().ping()) {
            LOG_WARN("main", "Redis PING 失败，服务继续启动（token/验证码相关接口会失败）");
        }
    } catch (const std::exception& e) {
        LOG_WARN("main", std::string("Redis 初始化失败: ") + e.what());
    }

    // ---- TokenService ----
    cm::security::TokenService::instance().configure(cfg.tokenHeader, cfg.tokenSecret,
                                                     cfg.tokenExpireTime);

    // ---- Elasticsearch（对应 RestHighLevelClient；默认关闭）----
    {
        cm::es::EsConfig esc;
        esc.enabled = cfg.esEnabled;
        esc.host = cfg.esHost;
        esc.port = cfg.esPort;
        esc.index = cfg.esIndex;
        cm::es::EsClient::instance().configure(esc);
        if (esc.enabled) {
            LOG_INFO("main", "Elasticsearch=" + esc.host + ":" + std::to_string(esc.port) +
                                 " index=" + esc.index +
                                 (cm::es::EsClient::instance().ping() ? " (PING OK)" : " (PING 失败)"));
        }
    }

    // ---- Kafka 快照流消费（对应 SnapshotFlowKafkaConsumerV2）----
    if (cfg.kafkaEnabled) {
        cm::kafka::KafkaConfig kc;
        kc.bootstrapServers = cfg.kafkaBootstrapServers;
        kc.groupId = cfg.kafkaGroupId;
        kc.topic = cfg.kafkaTopicSnapshotFlow;
        kc.dlqTopic = cfg.kafkaTopicSnapshotFlowDlq;
        kc.sessionTimeoutMs = cfg.kafkaSessionTimeoutMs;
        kc.fetchMaxBytes = cfg.kafkaFetchMaxBytes;
        kc.maxPollRecords = cfg.kafkaMaxPollRecords;
        kc.maxPollIntervalMs = cfg.kafkaMaxPollIntervalMs;
        kc.concurrency = cfg.kafkaConcurrency;
        kc.idempotentPrefix = cfg.idempotentPrefix;
        kc.idempotentTtlSeconds = cfg.idempotentExpireSeconds;
        cm::base::kafka::SnapshotFlowKafkaConsumer::instance().configure(kc);
        cm::base::kafka::SnapshotFlowKafkaConsumer::instance().start();
    }

    // ---- 路由 ----
    cm::web::registerControllers(cm::web::router());
    // C++ 扩展：健康检查（Java 侧无 actuator，见 COMPATIBILITY.md §扩展接口）
    cm::web::router()
        .get("/health",
             [](cm::web::RequestContext&) -> cm::http::ApiResponse {
                 cm::Json j = cm::Json::object();
                 j["status"] = "UP";
                 j["db"] = cm::db::Db::instance().pool().pingAll() ? "UP" : "DOWN";
                 bool redis_ok = false;
                 try {
                     redis_ok = cm::redis::RedisCache::instance().client().ping();
                 } catch (...) {
                 }
                 j["redis"] = redis_ok ? "UP" : "DOWN";
                 return cm::http::ApiResponse::json(j);
             })
        .permitAll();

    // ---- HTTP ----
    const int port = envInt("CM_SERVER_PORT", cfg.port);
    const int workers = envInt("CM_WORKERS", 32);
    cm::web::Server server("0.0.0.0", port, workers, cfg.acceptCount);
    // 对应 AsyncManager 的单线程定时器：@Log 命中的请求异步落 sys_oper_log
    cm::aspect::OperLogAspect::instance().start();
    if (!server.start()) {
        LOG_ERROR("main", "HTTP 服务启动失败，端口=" + std::to_string(port));
        cm::aspect::OperLogAspect::instance().stop();
        return 1;
    }
    std::signal(SIGINT, onSignal);
    std::signal(SIGTERM, onSignal);
    LOG_INFO("main", "HTTP 服务已启动: http://0.0.0.0:" + std::to_string(port));
    std::printf("car-monit-cpp listening on 0.0.0.0:%d\n", port);
    std::fflush(stdout);

    while (g_running.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }

    LOG_INFO("main", "收到退出信号，正在关闭...");
    // 先停 Kafka 消费（不再拉新消息），再停 HTTP 与落盘队列
    cm::base::kafka::SnapshotFlowKafkaConsumer::instance().stop();
    server.stop();
    // 先停接收再排空操作日志队列（对应 Java 的 ShutterManager 顺序）
    cm::aspect::OperLogAspect::instance().stop();
    // 排空异步日志队列（否则最后几条日志会随进程退出丢失）
    cm::log::Logger::instance().shutdown();
    return 0;
}
