#pragma once
// 对应 Java: application.yml / application-druid.yml + @ConfigurationProperties
//
// 配置优先级（与 Spring Boot 对齐）：
//   1. 环境变量  CM_<UPPER_DOT_PATH>（例如 CM_SERVER_PORT=8080），
//      同时兼容 Spring 风格 SERVER_PORT / TOKEN_SECRET / SPRING_DATASOURCE_DRUID_MASTER_URL
//   2. config/application.yaml
//   3. 内置默认值（与 Java application.yml 完全一致）
#include <string>
#include <vector>

#include "cm/framework/config/Yaml.hpp"

namespace cm::config {

class AppConfig {
public:
    static AppConfig& instance();

    /** 加载配置目录（默认 ./config 或环境变量 CM_CONFIG_DIR） */
    void load(const std::string& dir = "");

    // ---- server ----
    int port{9989};
    std::string contextPath{"/"};
    int maxThreads{800};
    int acceptCount{1000};

    // ---- ruoyi ----
    std::string name{"系统"};
    std::string version{"3.8.7"};
    std::string profile{"D:/ruoyi/uploadPath"};
    bool addressEnabled{false};
    std::string captchaType{"math"};
    int copyrightYear{2024};

    // ---- token ----
    std::string tokenHeader{"Authorization"};
    std::string tokenSecret{"abcdefghijklmnopqrstuvwxyz"};
    int tokenExpireTime{120}; // 分钟

    // ---- redis ----
    std::string redisHost{"127.0.0.1"};
    int redisPort{6379};
    int redisDatabase{0};
    std::string redisPassword;
    int redisTimeoutMs{10000};
    int redisMaxIdle{8};
    int redisMaxActive{8};

    // ---- datasource (master) ----
    std::string dbHost{"127.0.0.1"};
    int dbPort{3307};
    std::string dbName{"carmonitdb"};
    std::string dbUser{"root"};
    std::string dbPassword{"root"};
    std::string dbCharset{"utf8"};
    std::string dbTimezone{"+08:00"};
    int dbInitialSize{5};
    int dbMinIdle{10};
    int dbMaxActive{200};
    int dbMaxWaitMs{60000};
    int dbConnectTimeoutMs{30000};
    int dbSocketTimeoutMs{60000};
    bool dbSlaveEnabled{false};
    /** 每条 MySQL 连接的预备语句缓存上限（LRU）；默认 64。 */
    int dbPreparedCacheMax{64};

    // ---- user.password ----
    int pwdMaxRetryCount{5};
    int pwdLockTime{10};

    // ---- multipart ----
    long long maxFileSize{40LL * 1024 * 1024};
    long long maxRequestSize{200LL * 1024 * 1024};

    // ---- xss ----
    bool xssEnabled{true};
    std::string xssExcludes{"/system/notice"};
    std::string xssUrlPatterns{"/system/*,/monitor/*,/tool/*"};

    // ---- monitor ----
    bool monitorEnabled{true};
    int slowRequestThreshold{3000};
    int slowMethodThreshold{500};
    int slowSqlThreshold{1000};
    std::string traceIdHeader{"X-Trace-Id"};
    int alertWindowMs{60000};
    int alertMaxCount{5};

    // ---- captcha ----
    std::string captchaBorder{"yes"};
    std::string captchaNoise{"yes"};
    std::string captchaPath{"/"};

    // ---- kafka / es / oss（迁移状态见 COMPATIBILITY.md） ----
    bool kafkaEnabled{false};
    std::string kafkaBootstrapServers{"127.0.0.1:9092"};
    std::string kafkaGroupId{"snapshot-flow-consumer-group"};
    std::string kafkaTopicSnapshotFlow{"ods-rt-szdn-snapshot-flow"};
    std::string kafkaTopicSnapshotFlowDlq{"ods-rt-szdn-snapshot-flow-dlq"};
    int kafkaSessionTimeoutMs{60000};
    int kafkaFetchMaxBytes{52428800};
    int kafkaMaxPollRecords{500};
    int kafkaMaxPollIntervalMs{300000};
    int kafkaConcurrency{3};
    std::string idempotentPrefix{"snapshot:flow:idempotent_"};
    int idempotentExpireSeconds{86400};
    bool esEnabled{false};
    std::string esHost{"127.0.0.1"};
    int esPort{9200};
    std::string esIndex{"snapshot-flow"};
    std::string ossEndpoint;
    std::string ossAccessKey;
    std::string ossSecretKey;
    std::string ossBucketName;

    // ---- 外部服务 ----
    std::string vehicleMonitorBaseUrl{"http://127.0.0.1:9901"};
    std::string hengdaUrl{"http://36.200.20.14:7890/8809/geoserver-pg/rest"};   // forest.variables.hendaUrl
    std::string hengdaAppid{"YHZS"};
    std::string hengdaSecret{"b48381c4b98311ea90b100155d14fa3b"};
    std::string txServiceUrl{"https://apis.map.qq.com"};
    std::string roadPathUrl{"http://36.200.30.117:8080"};
    bool isLocalhost{true};

    // ---- 出站 HTTPS（vendored mbedTLS）----
    /** CA 证书包路径；空 = CM_CA_BUNDLE → third_party/cacert.pem → 系统 CA */
    std::string httpCaBundle;

    // ---- 分表 ----
    bool shardingEnabled{true};
    std::string shardingTablePrefix{"ods_rt_szdn_snapshot_flow_"};
    std::string shardingField{"snapshottime"};

    // ---- 日志 ----
    std::string logDir{"logs"};
    std::string logLevel{"debug"};

    /** 原始 YAML（只读） */
    const yaml::Node& raw() const { return root_; }

    std::string getString(const std::string& path, const std::string& def = "") const;
    long long getInt(const std::string& path, long long def = 0) const;
    bool getBool(const std::string& path, bool def = false) const;

    static std::string envKey(const std::string& path);
    static std::string readEnv(const std::string& path);

private:
    AppConfig() = default;
    void apply();

    yaml::Node root_;
    yaml::Node druidRoot_;
    std::string dir_;
};

} // namespace cm::config
