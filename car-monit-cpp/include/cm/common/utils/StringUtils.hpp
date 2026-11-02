#pragma once
// 对应 Java: com.ruoyi.common.utils.StringUtils
#include <algorithm>
#include <cctype>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace cm::utils {

class StringUtils {
public:
    static bool isEmpty(const std::string& s) { return s.empty(); }
    static bool isNotEmpty(const std::string& s) { return !s.empty(); }
    static bool isNotEmpty(const char* s) { return s != nullptr && *s != '\0'; }

    static bool isBlank(const std::string& s) {
        for (unsigned char c : s) {
            if (!std::isspace(c)) return false;
        }
        return true;
    }
    static bool isBlank(const std::optional<std::string>& s) { return !s || isBlank(*s); }
    static bool isNotBlank(const std::string& s) { return !isBlank(s); }
    static bool isNotBlank(const std::optional<std::string>& s) { return s && !isBlank(*s); }

    /** Java: StringUtils.isNull(Object) —— null 引用判断 */
    template <typename T>
    static bool isNull(const std::optional<T>& v) { return !v.has_value(); }
    template <typename T>
    static bool isNotNull(const std::optional<T>& v) { return v.has_value(); }

    static std::string trim(const std::string& s) {
        size_t b = 0, e = s.size();
        while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
        while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
        return s.substr(b, e - b);
    }

    static std::string toLower(const std::string& s) {
        std::string r = s;
        std::transform(r.begin(), r.end(), r.begin(),
                       [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        return r;
    }
    static std::string toUpper(const std::string& s) {
        std::string r = s;
        std::transform(r.begin(), r.end(), r.begin(),
                       [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
        return r;
    }

    static bool equals(const std::string& a, const std::string& b) { return a == b; }
    static bool equalsIgnoreCase(const std::string& a, const std::string& b) {
        return toLower(a) == toLower(b);
    }

    static bool startsWith(const std::string& s, const std::string& prefix) {
        return s.size() >= prefix.size() && s.compare(0, prefix.size(), prefix) == 0;
    }
    static bool endsWith(const std::string& s, const std::string& suffix) {
        return s.size() >= suffix.size() &&
               s.compare(s.size() - suffix.size(), suffix.size(), suffix) == 0;
    }
    static bool contains(const std::string& s, const std::string& sub) {
        return s.find(sub) != std::string::npos;
    }
    static bool containsIgnoreCase(const std::string& s, const std::string& sub) {
        return toLower(s).find(toLower(sub)) != std::string::npos;
    }

    static std::vector<std::string> split(const std::string& s, char sep) {
        std::vector<std::string> out;
        std::string cur;
        for (char c : s) {
            if (c == sep) { out.push_back(cur); cur.clear(); }
            else cur.push_back(c);
        }
        out.push_back(cur);
        return out;
    }

    static std::string join(const std::vector<std::string>& parts, const std::string& sep) {
        std::string out;
        for (size_t i = 0; i < parts.size(); ++i) {
            if (i) out += sep;
            out += parts[i];
        }
        return out;
    }

    static std::string nvl(const std::string& v, const std::string& def) {
        return v.empty() ? def : v;
    }

    /** Java: StringUtils.format("{}", a) —— 依次替换 {} */
    template <typename... Args>
    static std::string format(std::string tpl, Args&&... args) {
        std::vector<std::string> vals{toStr(std::forward<Args>(args))...};
        for (const auto& v : vals) {
            auto pos = tpl.find("{}");
            if (pos == std::string::npos) break;
            tpl.replace(pos, 2, v);
        }
        return tpl;
    }

    /** Java: StringUtils.toUnderScoreCase("createTime") -> "create_time" */
    static std::string toUnderScoreCase(const std::string& s) {
        std::string out;
        for (size_t i = 0; i < s.size(); ++i) {
            char c = s[i];
            if (std::isupper(static_cast<unsigned char>(c))) {
                if (i > 0 && s[i - 1] != '_') out.push_back('_');
                out.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
            } else {
                out.push_back(c);
            }
        }
        return out;
    }

    /** Java: StringUtils.substringAfter("a.b", ".") */
    static std::string substringAfter(const std::string& s, const std::string& sep) {
        auto p = s.find(sep);
        if (p == std::string::npos) return "";
        return s.substr(p + sep.size());
    }
    static std::string substringBefore(const std::string& s, const std::string& sep) {
        auto p = s.find(sep);
        if (p == std::string::npos) return s;
        return s.substr(0, p);
    }
    static std::string substringAfterLast(const std::string& s, const std::string& sep) {
        auto p = s.rfind(sep);
        if (p == std::string::npos) return "";
        return s.substr(p + sep.size());
    }

    static std::string capitalize(const std::string& s) {
        if (s.empty()) return s;
        std::string r = s;
        r[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(r[0])));
        return r;
    }

    static bool isHttp(const std::string& link) {
        std::string l = toLower(link);
        return startsWith(l, "http:") || startsWith(l, "https:");
    }

    template <typename T>
    static std::string toStr(const T& v) {
        std::ostringstream os;
        os << v;
        return os.str();
    }
    static std::string toStr(const std::string& v) { return v; }
    static std::string toStr(const char* v) { return v ? v : ""; }
    static std::string toStr(bool v) { return v ? "true" : "false"; }
    static std::string toStr(const std::optional<std::string>& v) { return v.value_or(""); }

    /** 常见校验：仅数字 */
    static bool isNumeric(const std::string& s) {
        if (s.empty()) return false;
        return std::all_of(s.begin(), s.end(),
                           [](unsigned char c) { return std::isdigit(c); });
    }
};

} // namespace cm::utils
