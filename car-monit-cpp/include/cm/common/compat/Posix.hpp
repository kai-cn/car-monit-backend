#pragma once
// POSIX 运行时函数的 Windows 替身。
//
// Java 侧不需要关心这一层（JDK 屏蔽了 OS 差异）；C++ 侧 DateUtils/ServerController
// 直接用到了 libc 的 POSIX 扩展，MinGW/MSVC 没有提供，因此在这里补齐。
// Linux/macOS 分支只做必要的 include，语义完全交给系统 libc。
//
// 对应 Java: java.util.Date / SimpleDateFormat / java.io.File.totalSpace 等
#include <chrono>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <string>

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <windows.h>

#ifndef CM_NO_WINDOWS_SOCKET_COMPAT
using ssize_t = SSIZE_T;
#endif

namespace cm::compat {

/** POSIX localtime_r / gmtime_r 的 Windows 版本（线程安全） */
inline std::tm* localtime_r(const std::time_t* timep, std::tm* result) {
    return localtime_s(result, timep) == 0 ? result : nullptr;
}

inline std::tm* gmtime_r(const std::time_t* timep, std::tm* result) {
    return gmtime_s(result, timep) == 0 ? result : nullptr;
}

/** POSIX timegm：按 UTC 解释 tm 得到 time_t（Windows 的 _mkgmtime 同义） */
inline std::time_t timegm(std::tm* tm) { return _mkgmtime(tm); }

/**
 * POSIX strptime 的最小实现，只支持本项目用到的转换符：
 *   %Y %m %d %H %M %S %j %% 以及字面空格/标点（宽松匹配任意空白）
 * 返回输入串中下一个待解析位置；解析失败返回 nullptr（与 glibc 一致）。
 */
inline const char* strptime(const char* buf, const char* format, std::tm* tm) {
    const char* p = buf;
    const char* f = format;
    auto skipSpace = [](const char*& s) {
        while (*s == ' ' || *s == '\t') ++s;
    };
    auto digits = [](const char*& s, int max_len, int& out) {
        int v = 0;
        int n = 0;
        while (n < max_len && *s >= '0' && *s <= '9') {
            v = v * 10 + (*s - '0');
            ++s;
            ++n;
        }
        if (n == 0) return false;
        out = v;
        return true;
    };
    while (*f != '\0') {
        if (*f != '%') {
            if (*f == ' ' || *f == '\t') {
                skipSpace(p);
                ++f;
                continue;
            }
            if (*p != *f) return nullptr;
            ++p;
            ++f;
            continue;
        }
        ++f;  // 跳过 '%'
        int v = 0;
        switch (*f) {
            case 'Y':
                skipSpace(p);
                if (!digits(p, 4, v)) return nullptr;
                tm->tm_year = v - 1900;
                break;
            case 'm':
                skipSpace(p);
                if (!digits(p, 2, v) || v < 1 || v > 12) return nullptr;
                tm->tm_mon = v - 1;
                break;
            case 'd':
                skipSpace(p);
                if (!digits(p, 2, v) || v < 1 || v > 31) return nullptr;
                tm->tm_mday = v;
                break;
            case 'H':
                skipSpace(p);
                if (!digits(p, 2, v) || v > 23) return nullptr;
                tm->tm_hour = v;
                break;
            case 'M':
                skipSpace(p);
                if (!digits(p, 2, v) || v > 59) return nullptr;
                tm->tm_min = v;
                break;
            case 'S':
                skipSpace(p);
                if (!digits(p, 2, v) || v > 60) return nullptr;
                tm->tm_sec = v;
                break;
            case 'j':
                skipSpace(p);
                if (!digits(p, 3, v)) return nullptr;
                tm->tm_yday = v - 1;
                break;
            case '%':
                if (*p != '%') return nullptr;
                ++p;
                break;
            default:
                return nullptr;  // 未实现的转换符
        }
        ++f;
    }
    return p;
}

/** 兼容 mktime 语义下 UTC 解释的 time_point -> time_t（Linux 用 timegm） */
inline std::time_t toTimeT(std::tm* tm, bool as_utc) {
    return as_utc ? timegm(tm) : std::mktime(tm);
}

inline void sleepUs(long micro_seconds) {
    Sleep(static_cast<DWORD>(micro_seconds / 1000));
}

/** 对应 Java File.getTotalSpace()/getUsableSpace()：Windows 用 GetDiskFreeSpaceExA */
struct Statvfs {
    unsigned long long f_blocks;
    unsigned long long f_bfree;
    unsigned long long f_bavail;
    unsigned long long f_frsize;
};

inline int statvfs(const char* path, Statvfs* out) {
    ULARGE_INTEGER free_bytes_available{};
    ULARGE_INTEGER total_bytes{};
    ULARGE_INTEGER total_free_bytes{};
    if (!GetDiskFreeSpaceExA(path, &free_bytes_available, &total_bytes, &total_free_bytes)) {
        return -1;
    }
    out->f_frsize = 4096;
    out->f_blocks = total_bytes.QuadPart / out->f_frsize;
    out->f_bfree = total_free_bytes.QuadPart / out->f_frsize;
    out->f_bavail = free_bytes_available.QuadPart / out->f_frsize;
    return 0;
}

}  // namespace cm::compat

#else  // ---------------------------------------------------------------- POSIX

#include <strings.h>
#include <sys/statvfs.h>
#include <unistd.h>

namespace cm::compat {
using ::gmtime_r;
using ::localtime_r;
using ::strptime;
using ::timegm;

inline std::time_t toTimeT(std::tm* tm, bool as_utc) { return as_utc ? timegm(tm) : mktime(tm); }
inline void sleepUs(long micro_seconds) { ::usleep(static_cast<useconds_t>(micro_seconds)); }
}  // namespace cm::compat

#endif
