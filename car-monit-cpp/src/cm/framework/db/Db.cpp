#include "cm/framework/db/Db.hpp"

#include <cctype>
#include <cstdio>
#include <memory>

#include "cm/common/utils/Logger.hpp"

namespace cm::db {

Db& Db::instance() {
    static Db db;
    return db;
}

void Db::init(const DbConfig& cfg, int initial, int minIdle, int maxActive, int maxWaitMs,
              int preparedCacheMax) {
    pool_ = std::make_unique<ConnectionPool>(cfg, initial, minIdle, maxActive, maxWaitMs);
    pool_->setPreparedCacheCapacity(preparedCacheMax);
    if (pool_->idleCount() == 0) {
        LOG_WARN("Db", "MySQL 连接池初始化后无可用连接（" + cfg.host + ":" + std::to_string(cfg.port) + "/" +
                           cfg.database + "）");
    }
}

bool Db::query(const std::string& sql, Result& out) {
    auto resolved = resolveBindings(sql);
    if (!resolved.ok) {
        LOG_WARN("Db", "绑定解析失败: " + resolved.error);
        out = Result{};
        return false;
    }
    if (!resolved.params.empty()) return query(resolved.sql, resolved.params, out);
    const std::string& plain = resolved.sql;
    if (!pool_) {
        out = Result{};
        return false;
    }
    // 事务作用域内：必须用同一条连接，否则 BEGIN/ROLLBACK 看到的是别的会话
    if (auto& tx = txConn(); tx) {
        if (tx->query(plain, out)) return true;
        LOG_WARN("Db", "查询失败: " + plain);
        return false;
    }
    bool ok = pool_->query(plain, out);
    if (!ok) LOG_WARN("Db", "查询失败: " + plain);
    return ok;
}

bool Db::execute(const std::string& sql, long long* affected, long long* insertId) {
    auto resolved = resolveBindings(sql);
    if (!resolved.ok) {
        LOG_WARN("Db", "绑定解析失败: " + resolved.error);
        return false;
    }
    if (!resolved.params.empty()) return execute(resolved.sql, resolved.params, affected, insertId);
    const std::string& plain = resolved.sql;
    if (!pool_) return false;
    if (auto& tx = txConn(); tx) {
        if (tx->execute(plain, affected, insertId)) return true;
        LOG_WARN("Db", "执行失败: " + plain);
        return false;
    }
    bool ok = pool_->execute(plain, affected, insertId);
    if (!ok) LOG_WARN("Db", "执行失败: " + plain);
    return ok;
}

bool Db::query(const std::string& sql, const Params& params, Result& out) {
    if (hasBindTokens(sql)) {
        LOG_WARN("Db", "显式 Params 与延迟绑定令牌不能混用: " + sql);
        out = Result{};
        return false;
    }
    if (!pool_) {
        out = Result{};
        return false;
    }
    if (params.empty()) return query(sql, out);
    if (auto& tx = txConn(); tx) {
        if (tx->queryPrepared(sql, params, out)) return true;
        LOG_WARN("Db", "绑定查询失败: " + sql + " (" + tx->lastError() + ")");
        return false;
    }
    bool ok = pool_->queryPrepared(sql, params, out);
    if (!ok) LOG_WARN("Db", "绑定查询失败: " + sql);
    return ok;
}

bool Db::execute(const std::string& sql, const Params& params, long long* affected, long long* insertId) {
    if (hasBindTokens(sql)) {
        LOG_WARN("Db", "显式 Params 与延迟绑定令牌不能混用: " + sql);
        return false;
    }
    if (!pool_) return false;
    if (params.empty()) return execute(sql, affected, insertId);
    if (auto& tx = txConn(); tx) {
        if (tx->executePrepared(sql, params, affected, insertId)) return true;
        LOG_WARN("Db", "绑定执行失败: " + sql + " (" + tx->lastError() + ")");
        return false;
    }
    bool ok = pool_->executePrepared(sql, params, affected, insertId);
    if (!ok) LOG_WARN("Db", "绑定执行失败: " + sql);
    return ok;
}

std::shared_ptr<MySqlConnection>& Db::txConn() {
    // 每个工作线程一条事务连接（对应 Spring 的 TransactionSynchronizationManager）
    static thread_local std::shared_ptr<MySqlConnection> current;
    return current;
}

std::optional<std::string> Db::scalar(const std::string& sql) {
    Result r;
    if (!query(sql, r) || r.rows.empty()) return std::nullopt;
    const auto& vals = r.rows.front().values();
    if (vals.empty()) return std::nullopt;
    return vals.front();
}

std::optional<std::string> Db::scalar(const std::string& sql, const Params& params) {
    Result r;
    if (!query(sql, params, r) || r.rows.empty()) return std::nullopt;
    const auto& vals = r.rows.front().values();
    if (vals.empty()) return std::nullopt;
    return vals.front();
}

long long Db::count(const std::string& sql) {
    auto v = scalar(sql);
    if (!v || v->empty()) return 0;
    try {
        return std::stoll(*v);
    } catch (...) {
        return 0;
    }
}

long long Db::count(const std::string& sql, const Params& params) {
    auto v = scalar(sql, params);
    if (!v || v->empty()) return 0;
    try {
        return std::stoll(*v);
    } catch (...) {
        return 0;
    }
}

std::string Db::lit(const std::string& value) {
    std::string out = "'";
    for (char c : value) {
        switch (c) {
            case '\0': out += "\\0"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\\': out += "\\\\"; break;
            case '\'': out += "\\'"; break;
            case '"': out += "\\\""; break;
            case '\032': out += "\\Z"; break;
            default: out.push_back(c);
        }
    }
    out.push_back('\'');
    return out;
}

std::string Db::lit(const std::optional<std::string>& value) {
    return value ? lit(*value) : "NULL";
}
std::string Db::lit(long long value) { return std::to_string(value); }
std::string Db::lit(std::optional<long long> value) { return value ? std::to_string(*value) : "NULL"; }
std::string Db::lit(double value) {
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%.15g", value);
    return buf;
}
std::string Db::lit(bool value) { return value ? "1" : "0"; }
std::string Db::litNull() { return "NULL"; }

std::string Db::escapeLike(const std::string& value) {
    std::string out;
    for (char c : value) {
        if (c == '%' || c == '_' || c == '\\') out.push_back('\\');
        out.push_back(c);
    }
    return out;
}

std::string Db::inList(const std::vector<std::string>& values) {
    if (values.empty()) return "(NULL)";
    std::string out = "(";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out += ",";
        out += lit(values[i]);
    }
    out += ")";
    return out;
}

std::string Db::inList(const std::vector<long long>& values) {
    if (values.empty()) return "(NULL)";
    std::string out = "(";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out += ",";
        out += std::to_string(values[i]);
    }
    out += ")";
    return out;
}

namespace {

PageResult runPage(const std::string& countSql, const Params& countParams, const std::string& dataSql,
                   const Params& dataParams, const PageRequest& page, bool bound) {
    PageResult pr;
    if (!page.enabled) {
        if (bound)
            Db::instance().query(dataSql, dataParams, pr.rows);
        else
            Db::instance().query(dataSql, pr.rows);
        return pr;
    }
    pr.total = bound ? Db::instance().count(countSql, countParams) : Db::instance().count(countSql);
    // Java: PageHelper 在 count == 0 时 **不执行** data 语句，直接返回空 Page
    if (pr.total <= 0) return pr;

    int pageNum = page.pageNum;
    int pageSize = page.pageSize <= 0 ? 10 : page.pageSize;
    long long pages = (pr.total + pageSize - 1) / pageSize;
    if (page.reasonable) {
        if (pageNum < 1) pageNum = 1;
        if (pages > 0 && pageNum > pages) pageNum = static_cast<int>(pages);
    }
    long long offset = pageNum > 0 ? static_cast<long long>(pageNum - 1) * pageSize : 0;

    std::string sql = dataSql;
    if (!page.orderBy.empty()) {
        std::string lower = sql;
        for (char& c : lower) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        if (lower.find(" order by ") == std::string::npos) {
            sql += " ORDER BY " + page.orderBy;
        }
    }
    sql += " LIMIT " + std::to_string(offset) + "," + std::to_string(pageSize);
    if (bound)
        Db::instance().query(sql, dataParams, pr.rows);
    else
        Db::instance().query(sql, pr.rows);
    return pr;
}

} // namespace

PageResult queryPage(const std::string& countSql, const std::string& dataSql, const PageRequest& page) {
    return runPage(countSql, Params{}, dataSql, Params{}, page, false);
}

PageResult queryPage(const std::string& countSql, const Params& countParams, const std::string& dataSql,
                     const Params& dataParams, const PageRequest& page) {
    return runPage(countSql, countParams, dataSql, dataParams, page, true);
}

} // namespace cm::db
