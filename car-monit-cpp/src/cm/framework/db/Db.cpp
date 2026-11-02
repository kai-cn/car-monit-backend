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

void Db::init(const DbConfig& cfg, int initial, int minIdle, int maxActive, int maxWaitMs) {
    pool_ = std::make_unique<ConnectionPool>(cfg, initial, minIdle, maxActive, maxWaitMs);
    if (pool_->idleCount() == 0) {
        LOG_WARN("Db", "MySQL 连接池初始化后无可用连接（" + cfg.host + ":" + std::to_string(cfg.port) + "/" +
                           cfg.database + "）");
    }
}

bool Db::query(const std::string& sql, Result& out) {
    if (!pool_) {
        out = Result{};
        return false;
    }
    bool ok = pool_->query(sql, out);
    if (!ok) LOG_WARN("Db", "查询失败: " + sql);
    return ok;
}

bool Db::execute(const std::string& sql, long long* affected, long long* insertId) {
    if (!pool_) return false;
    bool ok = pool_->execute(sql, affected, insertId);
    if (!ok) LOG_WARN("Db", "执行失败: " + sql);
    return ok;
}

std::optional<std::string> Db::scalar(const std::string& sql) {
    Result r;
    if (!query(sql, r) || r.rows.empty()) return std::nullopt;
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

PageResult queryPage(const std::string& countSql, const std::string& dataSql, const PageRequest& page) {
    PageResult pr;
    if (!page.enabled) {
        Db::instance().query(dataSql, pr.rows);
        return pr;
    }
    pr.total = Db::instance().count(countSql);
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
    Db::instance().query(sql, pr.rows);
    return pr;
}

} // namespace cm::db
