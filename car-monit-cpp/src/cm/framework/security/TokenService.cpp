#include "cm/framework/security/TokenService.hpp"

#include <chrono>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/redis/RedisClient.hpp"

namespace cm::security {
namespace {

long long nowMillis() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

std::string browserName(const std::string& ua) {
    // 对齐 eu.bitwalker.useragentutils 的常见输出
    std::string l = cm::utils::StringUtils::toLower(ua);
    if (l.find("edg/") != std::string::npos) return "Edge";
    if (l.find("chrome/") != std::string::npos) return "Chrome";
    if (l.find("firefox/") != std::string::npos) return "Firefox";
    if (l.find("safari/") != std::string::npos && l.find("chrome") == std::string::npos) return "Safari";
    if (l.find("msie") != std::string::npos || l.find("trident") != std::string::npos) return "Internet Explorer";
    return "Unknown";
}

std::string osName(const std::string& ua) {
    std::string l = cm::utils::StringUtils::toLower(ua);
    if (l.find("windows") != std::string::npos) return "Windows";
    if (l.find("android") != std::string::npos) return "Android";
    if (l.find("iphone") != std::string::npos || l.find("ipad") != std::string::npos) return "iOS";
    if (l.find("mac os") != std::string::npos) return "Mac OS X";
    if (l.find("linux") != std::string::npos) return "Linux";
    return "Unknown";
}

} // namespace

TokenService& TokenService::instance() {
    static TokenService svc;
    return svc;
}

void TokenService::configure(const std::string& header, const std::string& secret, int expireMinutes) {
    header_ = header;
    secret_ = secret;
    expire_minutes_ = expireMinutes;
    jwt_.emplace(secret);
}

std::string TokenService::getTokenKey(const std::string& uuid) const {
    return std::string(cm::constant::Constants::LOGIN_TOKEN_KEY) + uuid;
}

std::string TokenService::getToken(const cm::http::HttpRequest& request) const {
    std::string token = request.getHeader(header_);
    const std::string prefix = cm::constant::Constants::TOKEN_PREFIX;
    if (!token.empty() && cm::utils::StringUtils::startsWith(token, prefix)) {
        // Java: token.replace("Bearer ", "") —— 替换所有出现，不是只替换前缀
        size_t pos = 0;
        while ((pos = token.find(prefix, pos)) != std::string::npos) {
            token.erase(pos, prefix.size());
        }
    }
    return token;
}

std::optional<cm::domain::LoginUser> TokenService::getLoginUserByToken(const std::string& token) {
    if (token.empty() || !jwt_) return std::nullopt;
    auto uuid = jwt_->parseLoginUserKey(token);
    if (!uuid) return std::nullopt;
    auto cached = cm::redis::RedisCache::instance().get(getTokenKey(*uuid));
    if (!cached) return std::nullopt;
    try {
        // Java 写入的会话值带 fastjson2 类型标注（Set[...] / 25367L），必须先降级
        Json j = cm::utils::parse_cached_json(*cached);
        return cm::domain::LoginUser::fromJson(j);
    } catch (const std::exception& e) {
        LOG_ERROR("TokenService", std::string("解析 LoginUser 缓存失败: ") + e.what());
        return std::nullopt;
    }
}

std::optional<cm::domain::LoginUser> TokenService::getLoginUser(const cm::http::HttpRequest& request) {
    std::string token = getToken(request);
    if (token.empty()) return std::nullopt;
    return getLoginUserByToken(token);
}

void TokenService::refreshToken(cm::domain::LoginUser& loginUser) {
    loginUser.loginTime = nowMillis();
    loginUser.expireTime = *loginUser.loginTime + static_cast<long long>(expire_minutes_) * 60 * 1000;
    std::string key = getTokenKey(loginUser.token.value_or(""));
    cm::redis::RedisCache::instance().set(key, loginUser.toJson().dump(),
                                          static_cast<long long>(expire_minutes_) * 60);
}

void TokenService::setLoginUser(cm::domain::LoginUser& loginUser) {
    if (loginUser.token && !loginUser.token->empty()) refreshToken(loginUser);
}

void TokenService::delLoginUser(const std::string& token) {
    if (!token.empty()) {
        cm::redis::RedisCache::instance().del(getTokenKey(token));
    }
}

std::string TokenService::createToken(cm::domain::LoginUser& loginUser) {
    if (!jwt_) jwt_.emplace(secret_);
    std::string token = cm::utils::uuid();
    loginUser.token = token;
    refreshToken(loginUser);
    return jwt_->createToken(token);
}

std::string TokenService::createToken(cm::domain::LoginUser& loginUser,
                                      const cm::http::HttpRequest& request) {
    if (!jwt_) jwt_.emplace(secret_);
    std::string token = cm::utils::uuid();
    loginUser.token = token;
    setUserAgent(loginUser, request);
    refreshToken(loginUser);
    return jwt_->createToken(token);
}

void TokenService::verifyToken(cm::domain::LoginUser& loginUser) {
    long long expire = loginUser.expireTime.value_or(0);
    long long current = nowMillis();
    // 相差不足 20 分钟，自动刷新缓存
    if (expire - current <= 20LL * 60 * 1000) {
        refreshToken(loginUser);
    }
}

void TokenService::setUserAgent(cm::domain::LoginUser& loginUser, const cm::http::HttpRequest& request) {
    std::string ua = request.getHeader("User-Agent");
    std::string ip = ipOf(request);
    std::string sid = request.getCookie("JSESSIONID").value_or("");
    loginUser.sessionId = sid.empty() ? cm::utils::sessionId() : sid;
    loginUser.ipaddr = ip;
    loginUser.loginLocation = addressByIp(ip);
    loginUser.browser = browserOf(ua);
    loginUser.os = osOf(ua);
}

std::string TokenService::ipOf(const cm::http::HttpRequest& request) {
    return cm::utils::ipAddr(request.remote_addr, request.getHeader("x-forwarded-for"),
                             request.getHeader("Proxy-Client-IP"),
                             request.getHeader("WL-Proxy-Client-IP"),
                             request.getHeader("X-Real-IP"));
}

std::string TokenService::browserOf(const std::string& userAgent) { return browserName(userAgent); }

std::string TokenService::osOf(const std::string& userAgent) { return osName(userAgent); }

bool TokenService::isValidTokenFormat(const std::string& token) {
    if (!jwt_) jwt_.emplace(secret_);
    return jwt_->parseLoginUserKey(token).has_value();
}

std::optional<std::string> TokenService::getUsernameFromToken(const std::string& token) {
    if (!jwt_) jwt_.emplace(secret_);
    return jwt_->parseSubject(token);
}

std::string TokenService::addressByIp(const std::string& ip) {
    if (cm::utils::internalIp(ip)) return "内网IP";
    // Java: addressEnabled=false 时返回 UNKNOWN
    return "XX XX";
}

} // namespace cm::security
