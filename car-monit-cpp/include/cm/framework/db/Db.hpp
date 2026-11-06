#pragma once
// 对应 Java: DataSource(Druid) + MyBatis SqlSession
//
// 提供全局连接池与 SQL 辅助（转义、IN 列表、分页）。
// ⚠️ 与 Java 的差异：MyBatis 使用 PreparedStatement；C++ 侧为文本协议 + 手工转义。
//    所有外部输入都必须经过 escape()/lit()，见 MIGRATION_GUIDE.md 的安全章节。
#include <optional>
#include <string>
#include <vector>

#include "cm/framework/db/MySqlClient.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::db {

class Db {
public:
    static Db& instance();

    void init(const DbConfig& cfg, int initial, int minIdle, int maxActive, int maxWaitMs);
    ConnectionPool& pool() { return *pool_; }
    bool ready() const { return pool_ != nullptr; }

    bool query(const std::string& sql, Result& out);
    bool execute(const std::string& sql, long long* affected = nullptr, long long* insertId = nullptr);
    /** 单值查询（第一行第一列） */
    std::optional<std::string> scalar(const std::string& sql);
    long long count(const std::string& sql);

    /** 当前线程绑定的事务连接；为空表示不在事务中。
     *  Db::query/execute 有它就直接用，不再从池里另借一条。 */
    static std::shared_ptr<MySqlConnection>& txConn();

    /** MySQL 字符串字面量转义（含引号） */
    static std::string lit(const std::string& value);
    /** ⚠️ 必须有这一条：没有它的话 `Db::lit("0")` 会选中 lit(bool) ——
     *  const char* → bool 是**标准转换**，比 → const std::string& 的用户定义转换优先级高，
     *  于是 del_flag 这类字面量悄悄变成 1。加了它之后字符串字面量走精确匹配。 */
    static std::string lit(const char* value) { return lit(std::string(value)); }
    static std::string lit(const std::optional<std::string>& value);
    static std::string lit(long long value);
    static std::string lit(std::optional<long long> value);
    static std::string lit(double value);
    static std::string lit(bool value);
    static std::string litNull();
    /** 转义为可嵌入 LIKE 的字符串（不含引号） */
    static std::string escapeLike(const std::string& value);
    /** 值数组 -> ('a','b')；空数组返回 (NULL) */
    static std::string inList(const std::vector<std::string>& values);
    static std::string inList(const std::vector<long long>& values);

private:
    Db() = default;
    std::unique_ptr<ConnectionPool> pool_;
};

/** 对应 Spring 的 @Transactional(rollbackFor = Exception.class)。
 *  作用域内 Db::query/execute 复用同一条连接；没走到 commit() 就离开作用域
 *  （包括异常向上抛出）一律 ROLLBACK —— 与 Java 的回滚语义一致。
 *  嵌套时按 PROPAGATION_REQUIRED 并入外层事务：内层既不 BEGIN 也不 ROLLBACK。 */
class Transaction {
public:
    Transaction() {
        outer_ = Db::instance().ready() ? Db::txConn() : nullptr;
        if (outer_) {  // 已在事务里，直接并入
            joined_ = true;
            return;
        }
        conn_ = Db::instance().pool().borrow();
        if (!conn_ || !conn_->begin()) {
            if (conn_) Db::instance().pool().release(conn_);
            conn_.reset();
            return;
        }
        Db::txConn() = conn_;
    }
    ~Transaction() {
        if (joined_) return;  // 外层决定提交还是回滚
        if (conn_) {
            if (!committed_) conn_->rollback();
            Db::txConn().reset();
            Db::instance().pool().release(conn_);
        }
    }
    Transaction(const Transaction&) = delete;
    Transaction& operator=(const Transaction&) = delete;

    /** 拿不到连接或 BEGIN 失败时为 false；调用方据此决定降级行为 */
    bool ok() const { return joined_ || conn_ != nullptr; }
    void commit() {
        if (joined_ || !conn_ || committed_) return;
        conn_->commit();
        committed_ = true;
    }

private:
    std::shared_ptr<MySqlConnection> outer_;
    std::shared_ptr<MySqlConnection> conn_;
    bool joined_{false};
    bool committed_{false};
};

/** 分页上下文（对应 PageHelper 的 ThreadLocal） */
struct PageRequest {
    int pageNum{1};
    int pageSize{10};
    bool reasonable{false};
    std::string orderBy;
    bool enabled{false};
};

/** 一次分页查询的结果 */
struct PageResult {
    Result rows;
    long long total{0};
};

/**
 * 执行分页查询：
 *   countSql 与 dataSql 的 WHERE 部分必须一致；dataSql 不需要写 LIMIT。
 */
PageResult queryPage(const std::string& countSql, const std::string& dataSql, const PageRequest& page);

} // namespace cm::db
