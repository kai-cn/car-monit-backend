#pragma once
// 摘要 / HMAC 实现（纯 C++，无外部依赖）。
//
// 对应 Java:
//   MessageDigest.getInstance("MD5"/"SHA-1"/"SHA-256")  -> md5()/sha1()/sha256()
//   HmacUtils / jjwt 的 Mac.sign()                      -> hmacSha512() 等
//
// 为什么不用 OpenSSL：见 COMPATIBILITY.md「依赖」一节 —— 本工程要求 clone 后
// 无需包管理器即可构建（Windows 上装 OpenSSL 开发包对 Java 同学是第一个坑）。
// 算法按 RFC 1321 / FIPS 180-4 公开规范实现，tests/ 里有标准测试向量对拍。
#include <cstdint>
#include <string>
#include <string_view>

namespace cm::crypto {

/** 返回 16 字节原始摘要（对应 Java MD5 的 byte[]） */
std::string md5(std::string_view data);
// const char* / std::string 都能隐式转成 std::string_view，因此不提供 (const std::string&)
// 重载 —— 两个重载会让 md5("abc") 变成歧义调用。
/** 返回 20 字节原始摘要 */
std::string sha1(std::string_view data);
/** 返回 32 字节原始摘要 */
std::string sha256(std::string_view data);
/** 返回 64 字节原始摘要 */
std::string sha512(std::string_view data);


/** RFC 2104 HMAC，hash 取 "md5"|"sha1"|"sha256"|"sha512"，未知算法按 sha256 处理 */
std::string hmac(const std::string& hash, std::string_view key, std::string_view data);

inline std::string hmacMd5(std::string_view k, std::string_view d) { return hmac("md5", k, d); }
inline std::string hmacSha1(std::string_view k, std::string_view d) { return hmac("sha1", k, d); }
inline std::string hmacSha256(std::string_view k, std::string_view d) { return hmac("sha256", k, d); }
inline std::string hmacSha512(std::string_view k, std::string_view d) { return hmac("sha512", k, d); }

/** 小写十六进制（对应 Java DigestUtils.md5Hex / sha1Hex） */
std::string hex(std::string_view bytes);
/** 可打印 ASCII 的十六进制解码；非法输入返回空串 */
std::string unhex(std::string_view hex_text);

} // namespace cm::crypto
