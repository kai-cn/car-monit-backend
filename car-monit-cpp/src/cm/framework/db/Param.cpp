#include "cm/framework/db/Param.hpp"

#include <cstring>
#include <unordered_map>

#include "cm/common/utils/Logger.hpp"

namespace cm::db {
namespace {

constexpr const char* kTokenPrefix = "/*cmp";
constexpr size_t kMaxPendingBindings = 8192;

/** 线程内待解析绑定：key = 令牌 id（十进制字符串） */
std::unordered_map<std::string, Param>& registry() {
    static thread_local std::unordered_map<std::string, Param> reg;
    return reg;
}

unsigned long long& sequence() {
    static thread_local unsigned long long seq = 0;
    return seq;
}

std::string hexEncode(const std::string& s) {
    static const char* digits = "0123456789abcdef";
    std::string out;
    out.reserve(s.size() * 2);
    for (unsigned char c : s) {
        out.push_back(digits[c >> 4]);
        out.push_back(digits[c & 0x0f]);
    }
    return out;
}

std::string makeToken(Param p) {
    auto& reg = registry();
    if (reg.size() >= kMaxPendingBindings) {
        // 正常情况下每个请求/每个后台任务都会 resetBindings()；这里只是兜底，
        // 避免异常路径把内存无限增长。清空后旧令牌会解析失败并报错，不会静默执行。
        LOG_WARN("Db", "绑定注册表超过上限，已清空；请检查是否有 SQL 构建后未执行的路径");
        reg.clear();
    }
    const std::string id = std::to_string(++sequence());
    reg[id] = std::move(p);
    return std::string(kTokenPrefix) + id + "*/?";
}

Param textParam(const std::string& v) {
    Param p;
    p.kind = ParamKind::Text;
    p.text = v;
    return p;
}

Param intParam(long long v) {
    Param p;
    p.kind = ParamKind::Int;
    p.text = std::to_string(v);
    return p;
}

Param doubleParam(double v) {
    Param p;
    p.kind = ParamKind::Double;
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%.15g", v);
    p.text = buf;
    return p;
}

} // namespace

std::string bind(const std::string& v) { return makeToken(textParam(v)); }
std::string bind(const char* v) { return bind(std::string(v ? v : "")); }
std::string bind(const std::optional<std::string>& v) {
    if (!v) return bindNull();
    return bind(*v);
}
std::string bind(long long v) { return makeToken(intParam(v)); }
std::string bind(int v) { return bind(static_cast<long long>(v)); }
std::string bind(unsigned long long v) { return bind(static_cast<long long>(v)); }
std::string bind(bool v) { return bind(static_cast<long long>(v ? 1 : 0)); }
std::string bind(double v) { return makeToken(doubleParam(v)); }
std::string bind(const std::optional<long long>& v) {
    if (!v) return bindNull();
    return bind(*v);
}
std::string bind(const std::optional<double>& v) {
    if (!v) return bindNull();
    return bind(*v);
}

std::string bindNull() {
    Param p;
    p.kind = ParamKind::Null;
    return makeToken(std::move(p));
}

std::string bindIn(const std::vector<std::string>& values) {
    if (values.empty()) return "(NULL)";
    std::string out = "(";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out += ",";
        out += bind(values[i]);
    }
    out += ")";
    return out;
}

std::string bindIn(const std::vector<long long>& values) {
    if (values.empty()) return "(NULL)";
    std::string out = "(";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out += ",";
        out += bind(values[i]);
    }
    out += ")";
    return out;
}

bool hasBindTokens(const std::string& sql) { return sql.find(kTokenPrefix) != std::string::npos; }

std::string paramWireLiteral(const Param& p) {
    switch (p.kind) {
        case ParamKind::Null:
            return "NULL";
        case ParamKind::Int:
        case ParamKind::Double: {
            // 数值由 Param.hpp 生成，已是规范十进制；这里再做一次白名单校验，
            // 防止有人手工构造 Param 把 SQL 片段塞进数值位置。
            bool ok = !p.text.empty();
            for (char c : p.text) {
                if (!((c >= '0' && c <= '9') || c == '-' || c == '+' || c == '.' || c == 'e' ||
                      c == 'E'))
                    ok = false;
            }
            if (ok) return p.text;
            return p.text.empty() ? "_utf8mb4''" : ("_utf8mb4 0x" + hexEncode(p.text));
        }
        case ParamKind::Text:
        default:
            return p.text.empty() ? "_utf8mb4''" : ("_utf8mb4 0x" + hexEncode(p.text));
    }
}

ResolvedSql resolveBindings(const std::string& sql) {
    ResolvedSql r;
    auto& reg = registry();
    size_t pos = 0;
    while (pos < sql.size()) {
        const size_t start = sql.find(kTokenPrefix, pos);
        if (start == std::string::npos) {
            r.sql.append(sql, pos, sql.size() - pos);
            break;
        }
        r.sql.append(sql, pos, start - pos);
        size_t d = start + std::strlen(kTokenPrefix);
        size_t e = d;
        while (e < sql.size() && sql[e] >= '0' && sql[e] <= '9') ++e;
        if (e == d || e + 2 >= sql.size() || sql[e] != '*' || sql[e + 1] != '/' ||
            sql[e + 2] != '?') {
            r.ok = false;
            r.error = "非法的绑定令牌: " + sql.substr(start, 24);
            return r;
        }
        const std::string id = sql.substr(d, e - d);
        auto it = reg.find(id);
        if (it == reg.end()) {
            r.ok = false;
            r.error = "绑定令牌已失效（可能跨请求/跨线程使用）: " + id;
            return r;
        }
        r.params.push_back(it->second);
        r.sql.push_back('?');
        pos = e + 3;
    }
    return r;
}

void resetBindings() { registry().clear(); }

} // namespace cm::db
