#include "cm/common/utils/IdUtils.hpp"

#include <cstdlib>
#include <random>
#include <sstream>
#include <string_view>

#include "cm/common/utils/StringUtils.hpp"

namespace cm::utils {
namespace {

std::string randomHex(size_t n) {
    static const char* hex = "0123456789abcdef";
    thread_local std::mt19937_64 gen{std::random_device{}()};
    std::string out;
    out.reserve(n);
    for (size_t i = 0; i < n; ++i) out.push_back(hex[gen() & 0xf]);
    return out;
}

} // namespace

std::string simpleUuid() { return randomHex(32); }

std::string uuid() {
    std::string s = randomHex(32);
    // 版本 4 / variant 8 (RFC 4122)，与 java.util.UUID 一致
    s[12] = '4';
    static const char variant[] = "89ab";
    s[16] = variant[std::stoi(s.substr(16, 1), nullptr, 16) & 0x3];
    return s.substr(0, 8) + "-" + s.substr(8, 4) + "-" + s.substr(12, 4) + "-" + s.substr(16, 4) +
           "-" + s.substr(20, 12);
}

std::string sessionId() { return randomHex(32); }

bool internalIp(const std::string& ip) {
    if (ip == "127.0.0.1" || ip == "localhost" || ip.empty()) return true;
    auto parts = cm::utils::StringUtils::split(ip, '.');
    if (parts.size() < 2) return true;
    int b0 = std::atoi(parts[0].c_str());
    int b1 = std::atoi(parts[1].c_str());
    if (b0 == 10) return true;
    if (b0 == 172 && b1 >= 16 && b1 <= 31) return true;
    if (b0 == 192 && b1 == 168) return true;
    return false;
}

std::string ipAddr(const std::string& remoteAddr,
                   const std::string& xForwardedFor,
                   const std::string& proxyClientIp,
                   const std::string& wlProxyClientIp,
                   const std::string& xRealIp) {
    auto unknown = [](const std::string& s) {
        return s.empty() || cm::utils::StringUtils::equalsIgnoreCase(s, "unknown");
    };
    std::string ip;
    if (!unknown(xForwardedFor)) ip = xForwardedFor;
    else if (!unknown(proxyClientIp)) ip = proxyClientIp;
    else if (!unknown(xForwardedFor)) ip = xForwardedFor;
    else if (!unknown(wlProxyClientIp)) ip = wlProxyClientIp;
    else if (!unknown(xRealIp)) ip = xRealIp;
    else ip = remoteAddr;
    if (ip == "0:0:0:0:0:0:0:1") return "127.0.0.1";
    // 多级反向代理：取第一个非法 IP 之前的部分
    auto parts = cm::utils::StringUtils::split(ip, ',');
    if (parts.size() > 1) return cm::utils::StringUtils::trim(parts[0]);
    return cm::utils::StringUtils::trim(ip);
}

} // namespace cm::utils
