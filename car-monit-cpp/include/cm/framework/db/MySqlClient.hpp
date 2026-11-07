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
#include <list>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "cm/framework/db/Param.hpp"
#include "cm/framework/db/Row.hpp"
#include "cm/framework/net/Fd.hpp"

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
    bool isOpen() const { return cm::net::validStorage(fd_); }

    /** 执行一条或多条语句；返回最后一个结果集 */
    bool query(const std::string& sql, Result& out);
    /** 执行写语句（返回受影响行数与自增 ID） */
    bool execute(const std::string& sql, long long* affected = nullptr, long long* insertId = nullptr);

    /** 参数绑定查询：SQL 模板含 `?`，值经 SET @v / EXECUTE ... USING 绑定，不拼接进 SQL。
     *  模板无占位符时等价于 query()；占位符与参数数量不一致直接失败（不猜）。 */
    bool queryPrepared(const std::string& sql, const Params& params, Result& out);
    bool executePrepared(const std::string& sql, const Params& params, long long* affected = nullptr,
                         long long* insertId = nullptr);

    /** 会话级预备语句缓存容量（默认 64；LRU 淘汰，淘汰时发送 DEALLOCATE PREPARE）。
     *  33 条连接 × 64 ≈ 2.1k，远低于 MySQL 默认 max_prepared_stmt_count=16382。 */
    void setPreparedCacheCapacity(int maxEntries) { prepared_max_ = maxEntries < 8 ? 8 : maxEntries; }
    int preparedCacheSize() const { return static_cast<int>(prepared_.size()); }
    unsigned long long preparedCacheHits() const { return prepared_hits_; }
    unsigned long long preparedCacheEvictions() const { return prepared_evictions_; }
    unsigned long long preparedQueries() const { return prepared_queries_; }
    /** 首次预编译时读到的服务端 max_prepared_stmt_count；未知为 -1 */
    long long serverPreparedStmtLimit() const { return server_stmt_limit_; }

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

    /** COM_QUERY 的原始执行（不再进入预编译分支，避免 PREPARE/SET/EXECUTE 递归） */
    bool queryRaw(const std::string& sql, Result& out);
    /** 取（或首次 PREPARE）模板对应的语句名；失败返回空串 */
    bool ensurePrepared(const std::string& sql, std::string& stmtName);
    /** 把所有参数写成一条 SET @cm_p1=..., @cm_p2=... */
    bool setPreparedParams(const Params& params);
    /** 淘汰最久未使用的预备语句（发送 DEALLOCATE PREPARE，失败只记录不抛出） */
    void evictPreparedOne();
    /** 首次预编译时探测服务端 max_prepared_stmt_count */
    void probeServerStmtLimit();
    static size_t countPlaceholders(const std::string& sql);
    static std::string normalizeTemplate(const std::string& sql);
    static std::string quoteTextLiteral(const std::string& s);

    /** socket 句柄以 long long 存放（Windows 的 SOCKET 是 64 位），避免头文件引入 winsock2.h */
    long long fd_{cm::net::kInvalidStorage};
    cm::net::Fd handle() const {
        return cm::net::fromStorage(fd_);
    }
    uint8_t seq_{0};
    unsigned long thread_id_{0};
    std::string last_error_;
    int last_errno_{0};
    bool in_tx_{false};
    std::string scramble_;

    // ---- 会话级预备语句缓存（LRU） ----
    struct PreparedEntry {
        std::string name;
        std::list<std::string>::iterator lru_it;
    };
    std::unordered_map<std::string, PreparedEntry> prepared_; // key: 归一化后的 SQL 模板
    std::list<std::string> prepared_lru_;                     // front = 最近使用
    int prepared_max_{64};
    unsigned long long next_stmt_id_{0};
    unsigned long long prepared_hits_{0};
    unsigned long long prepared_evictions_{0};
    unsigned long long prepared_queries_{0};
    long long server_stmt_limit_{-1};
    bool stmt_limit_probed_{false};
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
    /** 参数绑定执行（借出连接 → queryPrepared/executePrepared → 归还） */
    bool queryPrepared(const std::string& sql, const Params& params, Result& out);
    bool executePrepared(const std::string& sql, const Params& params, long long* affected = nullptr,
                         long long* insertId = nullptr);
    bool pingAll();

    /** 新建连接时应用该容量（默认 64） */
    void setPreparedCacheCapacity(int maxEntries) { prepared_cache_max_ = maxEntries < 8 ? 8 : maxEntries; }

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
    int prepared_cache_max_{64};
};

} // namespace cm::db
