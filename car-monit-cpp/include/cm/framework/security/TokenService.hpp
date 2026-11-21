#pragma once
// 对应 Java: com.ruoyi.framework.web.service.TokenService
#include <optional>
#include <string>

#include "cm/common/core/domain/model/LoginUser.hpp"
#include "cm/framework/http/HttpRequest.hpp"
#include "cm/framework/security/Jwt.hpp"

namespace cm::security {

class TokenService {
public:
    static TokenService& instance();

    void configure(const std::string& header, const std::string& secret, int expireMinutes);

    /** 对应 getLoginUser(request)：解析 token 并从 Redis 取 LoginUser */
    std::optional<cm::domain::LoginUser> getLoginUser(const cm::http::HttpRequest& request);
    std::optional<cm::domain::LoginUser> getLoginUserByToken(const std::string& token);

    void setLoginUser(cm::domain::LoginUser& loginUser);
    void delLoginUser(const std::string& token);

    /** 对应 createToken(LoginUser)：生成 UUID -> JWT */
    std::string createToken(cm::domain::LoginUser& loginUser);
    /** Java createToken 内部调用 setUserAgent()（依赖 RequestContextHolder），此处显式传入请求 */
    std::string createToken(cm::domain::LoginUser& loginUser, const cm::http::HttpRequest& request);
    /** 剩余不足 20 分钟自动续期 */
    void verifyToken(cm::domain::LoginUser& loginUser);
    void refreshToken(cm::domain::LoginUser& loginUser);
    /** 解析 UA / IP / sessionId */
    void setUserAgent(cm::domain::LoginUser& loginUser, const cm::http::HttpRequest& request);

    std::optional<std::string> getUsernameFromToken(const std::string& token);
    /** 令牌格式/签名是否可解析（用于区分「无 token」与「非法 token」） */
    bool isValidTokenFormat(const std::string& token);
    /** 对应 getToken(request)：去 "Bearer " 前缀（replace 全部出现） */
    std::string getToken(const cm::http::HttpRequest& request) const;
    std::string getTokenKey(const std::string& uuid) const;

    /** 对应 addressEnabled=false 时的 AddressUtils */
    static std::string addressByIp(const std::string& ip);
    /** 对应 IpUtils.getIpAddr(request) */
    static std::string ipOf(const cm::http::HttpRequest& request);
    /** 对应 UserAgent.getBrowser().getName() */
    static std::string browserOf(const std::string& userAgent);
    /** 对应 UserAgent.getOperatingSystem().getName() */
    static std::string osOf(const std::string& userAgent);
    /** 对应 IpUtils.getIpAddr()（AsyncFactory 的取 IP 口径） */
    static std::string currentIp(const cm::http::HttpRequest& request) { return ipOf(request); }

    const std::string& header() const { return header_; }
    int expireMinutes() const { return expire_minutes_; }

private:
    TokenService() = default;

    std::string header_{"Authorization"};
    std::string secret_{"abcdefghijklmnopqrstuvwxyz"};
    int expire_minutes_{120};
    std::optional<Jwt> jwt_;
};

} // namespace cm::security
