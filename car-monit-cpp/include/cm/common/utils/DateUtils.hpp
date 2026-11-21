#pragma once
// 对应 Java: com.ruoyi.common.utils.DateUtils
#include <chrono>
#include "cm/common/compat/Posix.hpp"
#include <cstdio>
#include <cstring>
#include <ctime>
#include <optional>
#include <string>

namespace cm::utils {

class DateUtils {
public:
    static constexpr const char* YYYY = "yyyy";
    static constexpr const char* YYYY_MM = "yyyy-MM";
    static constexpr const char* YYYY_MM_DD = "yyyy-MM-dd";
    static constexpr const char* YYYYMMDDHHMMSS = "yyyyMMddHHmmss";
    static constexpr const char* YYYY_MM_DD_HH_MM_SS = "yyyy-MM-dd HH:mm:ss";

    using TimePoint = std::chrono::system_clock::time_point;

    /** 当前毫秒时间戳（Java System.currentTimeMillis） */
    static long long nowMillis() {
        return std::chrono::duration_cast<std::chrono::milliseconds>(
                   std::chrono::system_clock::now().time_since_epoch())
            .count();
    }

    static long long toMillis(TimePoint tp) {
        return std::chrono::duration_cast<std::chrono::milliseconds>(tp.time_since_epoch()).count();
    }

    static TimePoint fromMillis(long long ms) {
        return TimePoint(std::chrono::milliseconds(ms));
    }

    /** Java 的 SimpleDateFormat 模式 -> strftime 模式（只覆盖项目用到的） */
    static std::string toStrftime(const std::string& pattern) {
        std::string out;
        for (size_t i = 0; i < pattern.size();) {
            if (pattern.compare(i, 4, "yyyy") == 0) { out += "%Y"; i += 4; }
            else if (pattern.compare(i, 2, "yy") == 0) { out += "%y"; i += 2; }
            else if (pattern.compare(i, 2, "MM") == 0) { out += "%m"; i += 2; }
            else if (pattern.compare(i, 2, "dd") == 0) { out += "%d"; i += 2; }
            else if (pattern.compare(i, 2, "HH") == 0) { out += "%H"; i += 2; }
            else if (pattern.compare(i, 2, "mm") == 0) { out += "%M"; i += 2; }
            else if (pattern.compare(i, 2, "ss") == 0) { out += "%S"; i += 2; }
            else { out.push_back(pattern[i]); ++i; }
        }
        return out;
    }

    static std::tm localTm(TimePoint tp) {
        std::time_t t = std::chrono::system_clock::to_time_t(tp);
        std::tm tm{};
        cm::compat::localtime_r(&t, &tm);
        return tm;
    }

    static std::string format(TimePoint tp, const std::string& pattern = YYYY_MM_DD_HH_MM_SS) {
        std::tm tm = localTm(tp);
        char buf[128];
        std::strftime(buf, sizeof(buf), toStrftime(pattern).c_str(), &tm);
        return buf;
    }

    static std::string formatMillis(long long ms, const std::string& pattern = YYYY_MM_DD_HH_MM_SS) {
        return format(fromMillis(ms), pattern);
    }

    /** Java: DateUtils.getTime() —— yyyy-MM-dd HH:mm:ss */
    static std::string getTime() { return format(std::chrono::system_clock::now()); }

    /** Java: DateUtils.dateTimeNow() */
    static std::string dateTimeNow() { return format(std::chrono::system_clock::now()); }

    /** Java: DateUtils.dateTimeNow("yyyyMMddHHmmss") */
    static std::string dateTimeNow(const std::string& pattern) {
        return format(std::chrono::system_clock::now(), pattern);
    }

    /** Java: DateUtils.getDate() —— yyyy-MM-dd */
    static std::string getDate() { return format(std::chrono::system_clock::now(), YYYY_MM_DD); }

    /** Java: DateUtils.dateTime() —— yyyy-MM-dd */
    static std::string dateTime() { return getDate(); }

    /** Java: DateUtils.parseDate(str) —— 支持多种常见格式；失败返回 nullopt（Java 返回 null） */
    static std::optional<TimePoint> parseDate(const std::string& text) {
        if (text.empty()) return std::nullopt;
        static const char* fmts[] = {
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S", "%Y/%m/%d", "%Y%m%d%H%M%S", "%Y%m%d",
        };
        for (const char* f : fmts) {
            std::tm tm{};
            if (cm::compat::strptime(text.c_str(), f, &tm) != nullptr) {
                tm.tm_isdst = -1;
                std::time_t t = std::mktime(&tm);
                if (t != static_cast<std::time_t>(-1)) return fromMillis(t * 1000LL);
            }
        }
        // 纯数字：按毫秒时间戳解析（对应 Jackson 反序列化 Date）
        try {
            size_t idx = 0;
            long long v = std::stoll(text, &idx);
            if (idx == text.size()) return fromMillis(v);
        } catch (...) {}
        return std::nullopt;
    }

    /** Java: DateUtils.parseDateToStr */
    static std::string parseDateToStr(const std::string& pattern, const std::string& text) {
        auto tp = parseDate(text);
        return tp ? format(*tp, pattern) : "";
    }

    // ---------------------------------------------------------------
    // Jackson 序列化口径（实测见 MIGRATION_GUIDE.md）
    // ---------------------------------------------------------------
    /** @JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")，固定 +08:00（Asia/Shanghai） */
    static std::string formatJsonDate(std::optional<long long> ms) {
        if (!ms) return "";
        return formatInZone(*ms, 8 * 3600, "%Y-%m-%d %H:%M:%S");
    }

    /** 无 @JsonFormat 的 Date：StdDateFormat -> 2024-05-17T14:15:52.000+08:00 */
    static std::string formatIsoDate(std::optional<long long> ms) {
        if (!ms) return "";
        long long local = *ms + 8LL * 3600 * 1000;
        std::time_t t = static_cast<std::time_t>(local / 1000);
        int millis = static_cast<int>(((local % 1000) + 1000) % 1000);
        std::tm tm{};
        cm::compat::gmtime_r(&t, &tm);
        char buf[64];
        std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &tm);
        char out[80];
        std::snprintf(out, sizeof(out), "%s.%03d+08:00", buf, millis);
        return out;
    }

    /** 在固定时区偏移下格式化（offsetSeconds 例如 8*3600） */
    static std::string formatInZone(long long ms, int offsetSeconds, const char* fmt) {
        std::time_t t = static_cast<std::time_t>((ms + offsetSeconds * 1000LL) / 1000);
        std::tm tm{};
        cm::compat::gmtime_r(&t, &tm);
        char buf[128];
        std::strftime(buf, sizeof(buf), fmt, &tm);
        return buf;
    }

    /** 解析数据库 datetime 字符串（wall clock, +08:00）为 epoch millis */
    static std::optional<long long> parseDbDateTime(const std::string& text) {
        if (text.empty()) return std::nullopt;
        std::tm tm{};
        const char* fmts[] = {"%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.", "%Y-%m-%d"};
        for (const char* f : fmts) {
            std::memset(&tm, 0, sizeof(tm));
            if (cm::compat::strptime(text.c_str(), f, &tm) != nullptr) {
                // wall clock in +08:00 -> epoch millis
                std::time_t utc = cm::compat::timegm(&tm);
                return static_cast<long long>(utc) * 1000LL - 8LL * 3600 * 1000;
            }
        }
        return std::nullopt;
    }
};

} // namespace cm::utils
