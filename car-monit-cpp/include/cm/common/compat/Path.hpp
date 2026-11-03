#pragma once
// UTF-8 字符串 -> std::filesystem::path
//
// ⚠️ 平台坑：MinGW 的 std::filesystem 把窄字符串按**本地 ANSI 码页**(GBK)解释，
// 而本项目的路径（profile 目录、上传文件名、导出文件名）都是 UTF-8。
// 结果就是任何含中文的路径在 Windows 上都"文件不存在" —— 而这套系统的导出文件名
// 恰好都是中文（"<uuid>_登录日志.xlsx"），所以必须先过这一层。
// Java/JDK 没有这个问题（NIO 内部是 UTF-16），POSIX 下路径本来就是字节串。
#include <filesystem>
#include <string>

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <windows.h>
#endif

namespace cm::compat {

#ifdef _WIN32
/** CP_UTF8 -> UTF-16，再交给 filesystem；空串安全 */
inline std::filesystem::path fsPath(const std::string& utf8) {
    if (utf8.empty()) return std::filesystem::path();
    const int n = ::MultiByteToWideChar(CP_UTF8, 0, utf8.data(), static_cast<int>(utf8.size()),
                                        nullptr, 0);
    if (n <= 0) return std::filesystem::path(utf8.begin(), utf8.end());  // 退化为按字节
    std::wstring w(static_cast<size_t>(n), L'\0');
    ::MultiByteToWideChar(CP_UTF8, 0, utf8.data(), static_cast<int>(utf8.size()), &w[0], n);
    return std::filesystem::path(w);
}
#else
inline std::filesystem::path fsPath(const std::string& utf8) { return std::filesystem::path(utf8); }
#endif

/** 反方向：path -> UTF-8 字符串。不要用 path::string()，MinGW 会按 ANSI 码页转，
 *  中文路径会被毁掉（前缀校验和错误消息都依赖它）。 */
#ifdef _WIN32
inline std::string fsUtf8(const std::filesystem::path& p) {
    const std::wstring& w = p.native();
    if (w.empty()) return std::string();
    const int n = ::WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), nullptr, 0,
                                        nullptr, nullptr);
    if (n <= 0) return p.string();  // 仅在 API 失败时退化（Windows 上几乎不可能）
    std::string s(static_cast<size_t>(n), '\0');
    ::WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), &s[0], n, nullptr, nullptr);
    return s;
}
#else
inline std::string fsUtf8(const std::filesystem::path& p) { return p.native(); }
#endif

} // namespace cm::compat
