#pragma once
// 密码学安全随机数。
//
// 对应 Java: java.security.SecureRandom（JDK 默认 NativePRNG）
// Linux 走 getrandom()/​/dev/urandom，Windows 走 BCryptGenRandom，
// 都失败时退回 std::random_device —— 与 Java 一样，绝不使用 rand() 生成密钥类数据。
#include <cstdint>
#include <string>
#include <string_view>

namespace cm::crypto {

/** 填充 len 字节随机数据；失败返回 false（调用方必须中止，不能带着弱随机继续跑） */
bool secureRandom(void* out, size_t len);

inline std::string secureRandomString(size_t len) {
    std::string s(len, '\0');
    if (!secureRandom(s.data(), len)) return {};
    return s;
}

} // namespace cm::crypto
