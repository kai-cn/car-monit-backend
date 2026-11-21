#pragma once
// 预编译语句的参数值（对应 JDBC PreparedStatement 的绑定参数）
//
// 设计约束：
//   * 值只以 Param 结构交给驱动，绝不拼接进 SQL 文本；
//   * Text 保留原始 UTF-8 字节，由驱动用 `_utf8mb4 0x...` 形式传给 MySQL，
//     因此单双引号、反斜杠、% _ 等字符都不需要再做转义；
//   * Int / Double 保留调用方已有的规范十进制文本，语义等价于原先未加引号的字面量；
//   * Null 与空串严格区分（对应 MyBatis 的 null 与 ''）。
#include <cstdio>
#include <cstdlib>
#include <optional>
#include <string>
#include <vector>

namespace cm::db {

enum class ParamKind { Null, Text, Int, Double };

struct Param {
    ParamKind kind{ParamKind::Null};
    std::string text;
};

using Params = std::vector<Param>;

// ---- 显式 Params 版（调用方按顺序自己 bind；适合循环/逐段拼装） ----
std::string bind(Params& p, const std::string& v);
std::string bind(Params& p, const char* v);
std::string bind(Params& p, const std::optional<std::string>& v);
/** 绑定整数（长整型），返回占位符 "?" */
std::string bind(Params& p, long long v);
std::string bind(Params& p, int v);
std::string bind(Params& p, unsigned long long v);
std::string bind(Params& p, bool v);
/** 绑定浮点；text 由调用方传入的十进制文本决定，避免 %.15g 之外的额外舍入 */
std::string bind(Params& p, double v);
std::string bind(Params& p, const std::optional<long long>& v);
std::string bind(Params& p, const std::optional<double>& v);
/** 显式 NULL */
std::string bindNull(Params& p);
/** 字符串数组 -> (?,?,?)；空数组返回 (NULL)，与 Db::inList 现有输出一致 */
std::string bindIn(Params& p, const std::vector<std::string>& values);
std::string bindIn(Params& p, const std::vector<long long>& values);
/** 强制按文本绑定（金额/标度字段透传原始文本时用） */
std::string bindText(Params& p, const std::string& v);

// ---- 延迟绑定版（无需 Params 参数） ----
//
// 为什么需要这一套：C++ 对重载 operator+ 的**操作数求值顺序不作保证**，
// `"a" + bind(p, x) + "b" + bind(p, y)` 可能先算 y 再算 x，参数顺序就会错。
// 因此这里把值登记到线程内注册表，返回一个带 id 的占位令牌（`/*cmpN*/?`）；
// 执行时按 SQL 文本中出现的位置解析成 `?` 并把参数按文本顺序排好，
// 与调用表达式的求值顺序无关。令牌只由本函数生成，用户值永远不进入 SQL 文本。
struct ResolvedSql {
    std::string sql;
    Params params;
    bool ok{true};
    std::string error;
};

std::string bind(const std::string& v);
std::string bind(const char* v);
std::string bind(const std::optional<std::string>& v);
std::string bind(long long v);
std::string bind(int v);
std::string bind(unsigned long long v);
std::string bind(bool v);
std::string bind(double v);
std::string bind(const std::optional<long long>& v);
std::string bind(const std::optional<double>& v);
std::string bindNull();
std::string bindIn(const std::vector<std::string>& values);
std::string bindIn(const std::vector<long long>& values);

/** 执行前解析：把令牌替换为 `?`，并按文本顺序产出参数。 */
ResolvedSql resolveBindings(const std::string& sql);
/** 是否含有未解析的绑定令牌 */
bool hasBindTokens(const std::string& sql);
/** 请求/后台任务边界清空线程内注册表，避免跨请求泄漏。 */
void resetBindings();

/** Param -> 会话变量赋值右侧的 SQL 文本（驱动内部使用，单测也直接钉住）：
 *  Null -> NULL；Int/Double -> 规范十进制；Text -> `_utf8mb4 0x<hex>`（空串 -> `_utf8mb4''`）。 */
std::string paramWireLiteral(const Param& p);

inline std::string bind(Params& p, const std::string& v) {
    Param x;
    x.kind = ParamKind::Text;
    x.text = v;
    p.push_back(std::move(x));
    return "?";
}

inline std::string bind(Params& p, const char* v) { return cm::db::bind(p, std::string(v ? v : "")); }

inline std::string bind(Params& p, const std::optional<std::string>& v) {
    if (!v) return bindNull(p);
    return cm::db::bind(p, *v);
}

inline std::string bind(Params& p, long long v) {
    Param x;
    x.kind = ParamKind::Int;
    x.text = std::to_string(v);
    p.push_back(std::move(x));
    return "?";
}

inline std::string bind(Params& p, int v) { return cm::db::bind(p, static_cast<long long>(v)); }

inline std::string bind(Params& p, unsigned long long v) {
    return cm::db::bind(p, static_cast<long long>(v));
}

inline std::string bind(Params& p, bool v) { return cm::db::bind(p, static_cast<long long>(v ? 1 : 0)); }

inline std::string bind(Params& p, double v) {
    Param x;
    x.kind = ParamKind::Double;
    char buf[64];
    // double 需要 17 位有效数字才能无损往返；固定 "%.15g" 会把第 16/17 位抹掉。
    // 这里按"最短且可 strtod 往返"输出：常见值仍是 116.5 / 0.1，高精度值不再被无条件截断。
    int prec = 15;
    for (;; ++prec) {
        std::snprintf(buf, sizeof(buf), "%.*g", prec, v);
        if (prec >= 17 || std::strtod(buf, nullptr) == v) break;
    }
    x.text = buf;
    p.push_back(std::move(x));
    return "?";
}

inline std::string bind(Params& p, const std::optional<long long>& v) {
    if (!v) return bindNull(p);
    return cm::db::bind(p, *v);
}

inline std::string bind(Params& p, const std::optional<double>& v) {
    if (!v) return bindNull(p);
    return cm::db::bind(p, *v);
}

inline std::string bindNull(Params& p) {
    Param x;
    x.kind = ParamKind::Null;
    p.push_back(std::move(x));
    return "?";
}

inline std::string bindText(Params& p, const std::string& v) { return cm::db::bind(p, v); }

inline std::string bindIn(Params& p, const std::vector<std::string>& values) {
    if (values.empty()) return "(NULL)";
    std::string out = "(";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out += ",";
        out += cm::db::bind(p, values[i]);
    }
    out += ")";
    return out;
}

inline std::string bindIn(Params& p, const std::vector<long long>& values) {
    if (values.empty()) return "(NULL)";
    std::string out = "(";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out += ",";
        out += cm::db::bind(p, values[i]);
    }
    out += ")";
    return out;
}

} // namespace cm::db
