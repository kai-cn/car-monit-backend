#pragma once
// MySQL 客户端（手写 wire protocol，零第三方依赖）
//
// ⚠️ 与 Java JDBC 的差异：
//   * 未启用 TLS（Java 的 useSSL=true 在本地 MySQL 上等价于明文，见 COMPATIBILITY.md）
//   * 使用文本协议而非 prepared statement：值统一转义后内联，语义等价，
//     但 `?` 预编译的性能收益不存在
//   * 时间列按字符串返回，由上层用 DateUtils::parseDbDateTime 转 epoch millis
#include <atomic>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"

namespace cm::db {

struct DbConfig {
    std::string host{"127.0.0.1"};
    int port{3306};
    std::string user{"root"};
    std::string password;
    std::string database;
    std::string charset{"utf8mb4"};
    int connectTimeoutMs{30000};
    int socketTimeoutMs{60000};
};

class MySqlConnection {
public:
    MySqlConnection() = default;
    ~MySqlConnection();
    MySqlConnection(const MySqlConnection&) = delete;
    MySqlConnection& operator=(const MySqlConnection&) = delete;

    bool connect(const DbConfig& cfg);
    void close();
    bool isOpen() const { return fd_ >= 0; }

    /** 执行一条或多条语句；返回最后一个结果集 */
    bool query(const std::string& sql, Result& out);
    /** 执行写语句（返回受影响行数与自增 ID） */
    bool execute(const std::string& sql, long long* affected = nullptr, long long* insertId = nullptr);

    bool begin();
    bool commit();
    bool rollback();
    bool ping();
    unsigned long threadId() const { return thread_id_; }
    const std::string& lastError() const { return last_error_; }
    int lastErrno() const { return last_errno_; }
    /** 是否处于事务中（手动 begin） */
    bool inTransaction() const { return in_tx_; }

private:
    bool sendPacket(const std::string& payload);
    bool recvPacket(std::string& payload);
    bool handshake(const DbConfig& cfg);
    bool authenticate(const DbConfig& cfg, uint8_t plugin, const std::string& scramble);
    bool handleAuthResponse(const DbConfig& cfg, const std::string& scramble);
    bool readResult(Result& out, bool& more_results);
    bool readOkOrErr(std::string& payload, Result& out);
    void setError(const std::string& msg, int err = -1);

    int fd_{-1};
    uint8_t seq_{0};
    unsigned long thread_id_{0};
    std::string last_error_;
    int last_errno_{0};
    bool in_tx_{false};
    std::string scramble_;
};

/** 连接池（对应 Druid：initialSize/minIdle/maxActive/maxWait） */
class ConnectionPool {
public:
    ConnectionPool(DbConfig cfg, int initial, int minIdle, int maxActive, int maxWaitMs);
    ~ConnectionPool();

    /** 借出连接；超时返回 nullptr */
    std::shared_ptr<MySqlConnection> borrow(int timeoutMs = -1);
    void release(std::shared_ptr<MySqlConnection> conn);

    /** 便捷执行 */
    bool query(const std::string& sql, Result& out);
    bool execute(const std::string& sql, long long* affected = nullptr, long long* insertId = nullptr);
    bool pingAll();

    int idleCount() const;
    int activeCount() const { return active_.load(); }
    int maxActive() const { return max_active_; }
    const DbConfig& config() const { return cfg_; }

private:
    std::shared_ptr<MySqlConnection> create();
    void destroy(std::shared_ptr<MySqlConnection> conn);

    DbConfig cfg_;
    int min_idle_{0};
    int max_active_{8};
    int max_wait_ms_{60000};
    mutable std::mutex mu_;
    std::condition_variable cv_;
    std::vector<std::shared_ptr<MySqlConnection>> idle_;
    std::atomic<int> total_{0};
    std::atomic<int> active_{0};
    std::atomic<bool> closed_{false};
};

} // namespace cm::db
