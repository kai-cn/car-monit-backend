#pragma once
// 对应 Java: RedisTemplate + RedisCache（Spring Data Redis / Lettuce）
//
// ⚠️ 序列化差异（见 COMPATIBILITY.md）：
//   Java 侧 RedisConfig 使用 FastJson2JsonRedisSerializer，value 是带 "@type" 的 JSON；
//   C++ 侧写入纯 JSON（无 @type），读取时两种都兼容。若与 Java 版本共用同一个 Redis，
//   C++ 写入的 key 不能被 Java 读取（反之可以）。
#include <cstdint>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

#include "cm/framework/net/Fd.hpp"

namespace cm::redis {

struct RedisConfig {
    std::string host{"127.0.0.1"};
    int port{6379};
    int database{0};
    std::string password;
    int timeoutMs{10000};
};

class RedisClient {
public:
    RedisClient() = default;
    ~RedisClient();
    RedisClient(const RedisClient&) = delete;
    RedisClient& operator=(const RedisClient&) = delete;

    bool connect(const RedisConfig& cfg);
    void close();
    bool isOpen() const { return cm::net::validStorage(fd_); }
    bool reconnect();

    // ---- 基础命令 ----
    bool ping();
    std::optional<std::string> get(const std::string& key);
    bool set(const std::string& key, const std::string& value);
    /** SET key value EX seconds */
    bool setex(const std::string& key, const std::string& value, long long seconds);
    /** SET key value PX ms */
    bool psetex(const std::string& key, const std::string& value, long long ms);
    /** SETNX，返回是否设置成功 */
    bool setnx(const std::string& key, const std::string& value);
    long long del(const std::vector<std::string>& keys);
    bool exists(const std::string& key);
    bool expire(const std::string& key, long long seconds);
    /** 返回剩余毫秒数；-2 不存在，-1 无过期 */
    long long pttl(const std::string& key);
    long long incr(const std::string& key, long long delta = 1);
    std::vector<std::string> keys(const std::string& pattern);
    /** SCAN 游标遍历（用于 keys 的替代实现） */
    std::vector<std::string> scanAll(const std::string& pattern, int count = 1000);
    std::vector<std::string> hkeys(const std::string& key);
    std::optional<std::string> hget(const std::string& key, const std::string& field);
    bool hset(const std::string& key, const std::string& field, const std::string& value);
    long long hdel(const std::string& key, const std::vector<std::string>& fields);
    /** 所有库的 key 数量（对应 monitor/cache 的 dbSize） */
    long long dbsize();
    std::vector<std::string> info(const std::string& section = "");
    bool flushdb();

    /** 原始命令（调试/管理用），返回回复的文本表示 */
    std::optional<std::string> command(const std::vector<std::string>& args);

    const std::string& lastError() const { return last_error_; }

private:
    bool sendCommand(const std::vector<std::string>& args);
    /** 读取一个 RESP 回复，返回类型 + 文本值；数组按行拼接 */
    bool readReply(std::string& out, bool* isNil = nullptr);
    bool readBulk(std::string& out);
    bool ensureConnected();
    void setError(const std::string& msg);
    /** fd_ 以 long long 存放，避免头文件拖进 winsock2.h */
    cm::net::Fd handle() const {
        return cm::net::fromStorage(fd_);
    }

    /** 句柄数值以 long long 存放，避免头文件引入 winsock2.h */
    long long fd_{cm::net::kInvalidStorage};
    RedisConfig cfg_;
    std::string last_error_;
    std::mutex mu_;
};

/** 对应 Java RedisCache（带前缀/过期时间的便捷封装） */
class RedisCache {
public:
    static RedisCache& instance();
    void init(const RedisConfig& cfg);
    RedisClient& client() { return client_; }

    std::optional<std::string> get(const std::string& key);
    bool set(const std::string& key, const std::string& value);
    bool set(const std::string& key, const std::string& value, long long ttlSeconds);
    bool del(const std::string& key);
    bool expire(const std::string& key, long long seconds);
    bool exists(const std::string& key);
    long long pttlMs(const std::string& key);
    std::vector<std::string> keys(const std::string& pattern);

private:
    RedisCache() = default;
    RedisClient client_;
};

} // namespace cm::redis
