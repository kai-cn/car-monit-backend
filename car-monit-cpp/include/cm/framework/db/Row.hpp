#pragma once
// 对应 Java: MyBatis-Plus / JDBC ResultSet 的一行
#include <cctype>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace cm::db {

class Row {
public:
    Row() = default;
    Row(std::vector<std::string> cols, std::vector<std::optional<std::string>> vals)
        : cols_(std::move(cols)), vals_(std::move(vals)) {
        for (size_t i = 0; i < cols_.size(); ++i) {
            idx_[cols_[i]] = i;
            // MyBatis / JDBC 的列名匹配不区分大小写：information_schema 的列标签是全大写
            // （TABLE_NAME），而 resultMap 里写的是 table_name。同名冲突时保留第一个。
            std::string lower;
            lower.reserve(cols_[i].size());
            for (char c : cols_[i]) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
            lowerIdx_.emplace(lower, i);
        }
    }

    bool has(const std::string& name) const { return lookup(name) != static_cast<size_t>(-1); }
    bool isNull(const std::string& name) const {
        const size_t i = lookup(name);
        return i == static_cast<size_t>(-1) || !vals_[i].has_value();
    }

    std::optional<std::string> get(const std::string& name) const {
        const size_t i = lookup(name);
        if (i == static_cast<size_t>(-1)) return std::nullopt;
        return vals_[i];
    }

    std::string str(const std::string& name, const std::string& def = "") const {
        auto v = get(name);
        return v ? *v : def;
    }

    long long i64(const std::string& name, long long def = 0) const {
        auto v = get(name);
        if (!v || v->empty()) return def;
        try { return std::stoll(*v); } catch (...) {
            try { return static_cast<long long>(std::stod(*v)); } catch (...) { return def; }
        }
    }
    std::optional<long long> optI64(const std::string& name) const {
        auto v = get(name);
        if (!v || v->empty()) return std::nullopt;
        try { return std::stoll(*v); } catch (...) { return std::nullopt; }
    }
    double dbl(const std::string& name, double def = 0.0) const {
        auto v = get(name);
        if (!v || v->empty()) return def;
        try { return std::stod(*v); } catch (...) { return def; }
    }
    std::optional<bool> optBool(const std::string& name) const {
        auto v = get(name);
        if (!v) return std::nullopt;
        if (*v == "1" || *v == "true") return true;
        if (*v == "0" || *v == "false") return false;
        return std::nullopt;
    }

    const std::vector<std::string>& columns() const { return cols_; }
    const std::vector<std::optional<std::string>>& values() const { return vals_; }

private:
    /** 先精确匹配，再按小写匹配（大小写不敏感），都没有则返回 (size_t)-1 */
    size_t lookup(const std::string& name) const {
        auto it = idx_.find(name);
        if (it != idx_.end()) return it->second;
        std::string lower;
        lower.reserve(name.size());
        for (char c : name) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
        auto lit = lowerIdx_.find(lower);
        return lit == lowerIdx_.end() ? static_cast<size_t>(-1) : lit->second;
    }

    std::vector<std::string> cols_;
    std::vector<std::optional<std::string>> vals_;
    std::unordered_map<std::string, size_t> idx_;
    std::unordered_map<std::string, size_t> lowerIdx_;
};

struct Result {
    std::vector<Row> rows;
    long long affectedRows{0};
    long long insertId{0};
    std::string info;
};

} // namespace cm::db
