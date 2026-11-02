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

    /** MySQL 字符串字面量转义（含引号） */
    static std::string lit(const std::string& value);
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
