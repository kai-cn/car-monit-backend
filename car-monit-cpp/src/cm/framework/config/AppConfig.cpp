#include "cm/framework/config/AppConfig.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <vector>

#include "cm/common/utils/Logger.hpp"

namespace cm::config {

namespace {

std::string upper(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

std::string trim(const std::string& s) {
    size_t b = 0, e = s.size();
    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
    return s.substr(b, e - b);
}

// 从 jdbc URL 提取 host / port / database
void parseJdbcUrl(const std::string& url, std::string& host, int& port, std::string& db) {
    auto pos = url.find("mysql://");
    if (pos == std::string::npos) return;
    std::string rest = url.substr(pos + 8);
    auto slash = rest.find('/');
    std::string authority = rest.substr(0, slash);
    auto colon = authority.find(':');
    host = colon == std::string::npos ? authority : authority.substr(0, colon);
    if (colon != std::string::npos) {
        try { port = std::stoi(authority.substr(colon + 1)); } catch (...) {}
    }
    if (slash != std::string::npos) {
        std::string tail = rest.substr(slash + 1);
        auto q = tail.find('?');
        db = q == std::string::npos ? tail : tail.substr(0, q);
    }
}

} // namespace

AppConfig& AppConfig::instance() {
    static AppConfig cfg;
    return cfg;
}

std::string AppConfig::envKey(const std::string& path) {
    std::string k = "CM_";
    for (char c : path) {
        if (c == '.' || c == '-' || c == '/') k.push_back('_');
        else k.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
    }
    return k;
}

std::string AppConfig::readEnv(const std::string& path) {
    const char* v = std::getenv(envKey(path).c_str());
    if (v != nullptr) return v;
    // Spring 风格：server.port -> SERVER_PORT
    std::string spring;
    for (char c : path) {
        if (c == '.' || c == '-') spring.push_back('_');
        else spring.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
    }
    const char* v2 = std::getenv(spring.c_str());
    if (v2 != nullptr) return v2;
    return std::string();
}

std::string AppConfig::getString(const std::string& path, const std::string& def) const {
    std::string env = readEnv(path);
    if (!env.empty()) return env;
    std::string v = root_.getString(path, "");
    return v.empty() ? def : v;
}

long long AppConfig::getInt(const std::string& path, long long def) const {
    std::string env = readEnv(path);
    if (!env.empty()) {
        try { return std::stoll(env); } catch (...) {}
    }
    return root_.getInt(path, def);
}

bool AppConfig::getBool(const std::string& path, bool def) const {
    std::string env = readEnv(path);
    if (!env.empty()) {
        yaml::Node n;
        n.type = yaml::Node::Type::Scalar;
        n.scalar = env;
        return n.asBool(def);
    }
    return root_.getBool(path, def);
}

void AppConfig::load(const std::string& dir) {
    const char* env_dir = std::getenv("CM_CONFIG_DIR");
    if (!dir.empty()) dir_ = dir;
    else if (env_dir) dir_ = env_dir;
    else if (std::filesystem::exists("config/application.yaml")) dir_ = "config";
    else if (std::filesystem::exists("../config/application.yaml")) dir_ = "../config";
    else dir_ = "config";

    std::string app = dir_ + "/application.yaml";
    std::vector<std::string> warnings;
    root_ = yaml::parseFile(app, &warnings);
    if (std::filesystem::exists(dir_ + "/application.yml")) {
        root_ = yaml::parseFile(dir_ + "/application.yml", &warnings);
    }
    druidRoot_ = yaml::parseFile(dir_ + "/application-druid.yaml", &warnings);
    if (druidRoot_.isNull()) druidRoot_ = yaml::parseFile(dir_ + "/application-druid.yml", &warnings);

    // 不支持的 YAML 语法不能静默：否则配置"看起来改了"实际读到缺省值
    for (const auto& w : warnings) {
        LOG_WARN("config", app + " " + w);
    }

    apply();
}

void AppConfig::apply() {
    port = static_cast<int>(getInt("server.port", port));
    contextPath = getString("server.servlet.context-path", contextPath);
    maxThreads = static_cast<int>(getInt("server.tomcat.threads.max", maxThreads));
    acceptCount = static_cast<int>(getInt("server.tomcat.accept-count", acceptCount));

    name = getString("ruoyi.name", name);
    version = getString("ruoyi.version", version);
    profile = getString("ruoyi.profile", profile);
    addressEnabled = getBool("ruoyi.addressEnabled", addressEnabled);
    captchaType = getString("ruoyi.captchaType", captchaType);
    copyrightYear = static_cast<int>(getInt("ruoyi.copyrightYear", copyrightYear));

    tokenHeader = getString("token.header", tokenHeader);
    if (const char* envSecret = std::getenv("TOKEN__SECRET")) {
        tokenSecret = envSecret;
    } else {
        tokenSecret = getString("token.secret", tokenSecret);
    }
    tokenExpireTime = static_cast<int>(getInt("token.expireTime", tokenExpireTime));

    redisHost = getString("spring.redis.host", redisHost);
    redisPort = static_cast<int>(getInt("spring.redis.port", redisPort));
    redisDatabase = static_cast<int>(getInt("spring.redis.database", redisDatabase));
    redisPassword = getString("spring.redis.password", redisPassword);
    redisMaxIdle = static_cast<int>(getInt("spring.redis.lettuce.pool.max-idle", redisMaxIdle));
    redisMaxActive = static_cast<int>(getInt("spring.redis.lettuce.pool.max-active", redisMaxActive));
    {
        std::string timeout = getString("spring.redis.timeout", "10s");
        int ms = 10000;
        try {
            if (!timeout.empty() && timeout.back() == 's') ms = std::stoi(timeout.substr(0, timeout.size() - 1)) * 1000;
            else if (!timeout.empty() && timeout.back() == 'm') ms = std::stoi(timeout.substr(0, timeout.size() - 1)) * 60000;
        } catch (...) {}
        redisTimeoutMs = ms;
    }

    // datasource：优先 application-druid.yml 的 master
    std::string url = druidRoot_.getString("spring.datasource.druid.master.url", "");
    std::string user = druidRoot_.getString("spring.datasource.druid.master.username", "");
    std::string pass = druidRoot_.getString("spring.datasource.druid.master.password", "");
    // 环境变量覆盖
    std::string env_url = readEnv("spring.datasource.druid.master.url");
    if (!env_url.empty()) url = env_url;
    std::string env_user = readEnv("spring.datasource.druid.master.username");
    if (!env_user.empty()) user = env_user;
    std::string env_pass = readEnv("spring.datasource.druid.master.password");
    if (!env_pass.empty()) pass = env_pass;

    if (!url.empty()) {
        parseJdbcUrl(url, dbHost, dbPort, dbName);
    }
    if (!user.empty()) dbUser = user;
    if (!pass.empty()) dbPassword = pass;

    dbMaxActive = static_cast<int>(druidRoot_.getInt("spring.datasource.druid.maxActive", dbMaxActive));
    dbMinIdle = static_cast<int>(druidRoot_.getInt("spring.datasource.druid.minIdle", dbMinIdle));
    dbInitialSize = static_cast<int>(druidRoot_.getInt("spring.datasource.druid.initialSize", dbInitialSize));
    dbMaxWaitMs = static_cast<int>(druidRoot_.getInt("spring.datasource.druid.maxWait", dbMaxWaitMs));
    dbConnectTimeoutMs = static_cast<int>(druidRoot_.getInt("spring.datasource.druid.connectTimeout", dbConnectTimeoutMs));
    dbSocketTimeoutMs = static_cast<int>(druidRoot_.getInt("spring.datasource.druid.socketTimeout", dbSocketTimeoutMs));
    dbSlaveEnabled = druidRoot_.getBool("spring.datasource.druid.slave.enabled", dbSlaveEnabled);
    // C++ 扩展配置：每条连接的预备语句缓存上限（LRU）。默认 64，避免 33 条连接
    // 在筛选组合很多时把会话级 prepared statement 数推到 max_prepared_stmt_count 附近。
    dbPreparedCacheMax = static_cast<int>(getInt("cm.db.prepared-cache-max", dbPreparedCacheMax));

    pwdMaxRetryCount = static_cast<int>(getInt("user.password.maxRetryCount", pwdMaxRetryCount));
    pwdLockTime = static_cast<int>(getInt("user.password.lockTime", pwdLockTime));

    std::string max_file = getString("spring.servlet.multipart.max-file-size", "40MB");
    std::string max_req = getString("spring.servlet.multipart.max-request-size", "200MB");
    auto to_bytes = [](const std::string& s) -> long long {
        try {
            if (s.size() > 2 && (s.substr(s.size() - 2) == "MB")) return std::stoll(s.substr(0, s.size() - 2)) * 1024 * 1024;
            if (s.size() > 2 && (s.substr(s.size() - 2) == "KB")) return std::stoll(s.substr(0, s.size() - 2)) * 1024;
            if (!s.empty() && s.back() == 'B') return std::stoll(s.substr(0, s.size() - 1));
            return std::stoll(s);
        } catch (...) { return 0; }
    };
    if (to_bytes(max_file) > 0) maxFileSize = to_bytes(max_file);
    if (to_bytes(max_req) > 0) maxRequestSize = to_bytes(max_req);

    xssEnabled = getBool("xss.enabled", xssEnabled);
    xssExcludes = getString("xss.excludes", xssExcludes);
    xssUrlPatterns = getString("xss.urlPatterns", xssUrlPatterns);

    monitorEnabled = getBool("monitor.enabled", monitorEnabled);
    slowRequestThreshold = static_cast<int>(getInt("monitor.slow-request-threshold", slowRequestThreshold));
    slowMethodThreshold = static_cast<int>(getInt("monitor.slow-method-threshold", slowMethodThreshold));
    slowSqlThreshold = static_cast<int>(getInt("monitor.slow-sql-threshold", slowSqlThreshold));
    traceIdHeader = getString("monitor.trace-id-header", traceIdHeader);
    alertWindowMs = static_cast<int>(getInt("monitor.alert-window-ms", alertWindowMs));
    alertMaxCount = static_cast<int>(getInt("monitor.alert-max-count", alertMaxCount));

    kafkaEnabled = getBool("kafka.enabled", kafkaEnabled);
    kafkaBootstrapServers = getString("kafka.bootstrap-servers", kafkaBootstrapServers);
    kafkaGroupId = getString("kafka.consumer.group-id", kafkaGroupId);
    kafkaTopicSnapshotFlow = getString("kafka.topic.snapshot-flow", kafkaTopicSnapshotFlow);
    kafkaTopicSnapshotFlowDlq =
        getString("kafka.topic.snapshot-flow-dlq", kafkaTopicSnapshotFlowDlq);
    kafkaSessionTimeoutMs =
        static_cast<int>(getInt("kafka.consumer.session-timeout-ms", kafkaSessionTimeoutMs));
    kafkaFetchMaxBytes =
        static_cast<int>(getInt("kafka.consumer.fetch-max-bytes", kafkaFetchMaxBytes));
    kafkaMaxPollRecords =
        static_cast<int>(getInt("kafka.consumer.max-poll-records", kafkaMaxPollRecords));
    kafkaMaxPollIntervalMs =
        static_cast<int>(getInt("kafka.consumer.max-poll-interval-ms", kafkaMaxPollIntervalMs));
    kafkaConcurrency = static_cast<int>(getInt("kafka.listener.concurrency", kafkaConcurrency));
    idempotentPrefix = getString("idempotent.redis.prefix", idempotentPrefix);
    idempotentExpireSeconds =
        static_cast<int>(getInt("idempotent.redis.expire-time", idempotentExpireSeconds));
    esEnabled = getBool("elasticsearch.enabled", esEnabled);
    esHost = getString("elasticsearch.host", esHost);
    esPort = static_cast<int>(getInt("elasticsearch.port", esPort));
    esIndex = getString("elasticsearch.index.snapshot-flow", esIndex);
    ossEndpoint = getString("oss.endpoint", ossEndpoint);
    ossAccessKey = getString("oss.accessKey", ossAccessKey);
    ossSecretKey = getString("oss.secretKey", ossSecretKey);
    ossBucketName = getString("oss.bucketName", ossBucketName);

    vehicleMonitorBaseUrl = getString("vehicleMonitor.baseUrl", vehicleMonitorBaseUrl);
    hengdaUrl = getString("forest.variables.hendaUrl", hengdaUrl);
    hengdaAppid = getString("hengda.appid", hengdaAppid);
    hengdaSecret = getString("hengda.secret", hengdaSecret);
    txServiceUrl = getString("tx-service-url", txServiceUrl);
    roadPathUrl = getString("roadPathUrl", roadPathUrl);
    isLocalhost = getString("isLocalhost", "local") == "local";
    httpCaBundle = getString("cm.http.ca-bundle", httpCaBundle);

    shardingEnabled = getBool("snapshot.flow.sharding.enabled", shardingEnabled);
    shardingTablePrefix = getString("snapshot.flow.sharding.table-prefix", shardingTablePrefix);
    shardingField = getString("snapshot.flow.sharding.sharding-field", shardingField);

    logLevel = getString("logging.level.com.ruoyi", logLevel);
    logDir = getString("cm.log.dir", logDir);
    logLevel = getString("cm.log.level", logLevel);
}

} // namespace cm::config
