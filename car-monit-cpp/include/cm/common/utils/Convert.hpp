#pragma once
// 对应 Java: com.ruoyi.common.core.text.Convert
#include <optional>
#include <string>
#include <vector>

namespace cm::utils {

class Convert {
public:
    static int toInt(const std::string& s, int def = 0) {
        try { size_t i = 0; int v = std::stoi(s, &i); return i == s.size() ? v : def; }
        catch (...) { return def; }
    }
    static long long toLong(const std::string& s, long long def = 0) {
        try { size_t i = 0; long long v = std::stoll(s, &i); return i == s.size() ? v : def; }
        catch (...) { return def; }
    }
    static double toDouble(const std::string& s, double def = 0.0) {
        try { size_t i = 0; double v = std::stod(s, &i); return i == s.size() ? v : def; }
        catch (...) { return def; }
    }
    /** Java: Convert.toBool("true"/"1"/"Y") */
    static bool toBool(const std::string& s, bool def = false) {
        if (s.empty()) return def;
        std::string v;
        for (char c : s) v.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
        if (v == "true" || v == "1" || v == "y" || v == "yes" || v == "on") return true;
        if (v == "false" || v == "0" || v == "n" || v == "no" || v == "off") return false;
        return def;
    }
    static std::string toStr(const std::string& s) { return s; }

    static std::vector<std::string> toStrArray(const std::string& s, const std::string& sep = ",") {
        std::vector<std::string> out;
        if (s.empty()) return out;
        size_t start = 0;
        while (true) {
            size_t p = s.find(sep, start);
            if (p == std::string::npos) { out.push_back(s.substr(start)); break; }
            out.push_back(s.substr(start, p - start));
            start = p + sep.size();
        }
        return out;
    }

    static std::vector<long long> toLongArray(const std::string& s, const std::string& sep = ",") {
        std::vector<long long> out;
        for (const auto& p : toStrArray(s, sep)) {
            if (!p.empty()) out.push_back(toLong(p));
        }
        return out;
    }
};

} // namespace cm::utils
