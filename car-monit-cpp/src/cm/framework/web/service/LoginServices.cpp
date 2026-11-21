// 对应 Java:
//   SysLoginService / SysPermissionService / SysPasswordService / UserDetailsServiceImpl
#include "cm/framework/web/service/LoginServices.hpp"

#include <chrono>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/security/TokenService.hpp"
#include "cm/system/mapper/SysUserMapper.hpp"
#include "cm/system/service/SysMenuService.hpp"

namespace cm::security {

namespace {
constexpr const char* kMsgCaptchaError = "验证码错误";
constexpr const char* kMsgCaptchaExpire = "验证码已失效";
constexpr const char* kMsgPwdNotMatch = "用户不存在/密码错误";
constexpr const char* kMsgLoginSuccess = "登录成功";

long long nowMillis() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

std::string trimCode(const std::string& s) {
    size_t b = s.find_first_not_of(" \t\r\n");
    if (b == std::string::npos) return "";
    size_t e = s.find_last_not_of(" \t\r\n");
    return s.substr(b, e - b + 1);
}
} // namespace

// ---------------------------------------------------------------------------
// SysPermissionService
// ---------------------------------------------------------------------------
std::set<std::string> SysPermissionService::getRolePermission(const cm::domain::SysUser& user) {
    std::set<std::string> roles;
    if (user.isAdmin()) {
        roles.insert("admin");
    } else {
        auto ids = cm::system::mapper::SysUserMapper::selectRolePermissionByUserId(
            user.userId.value_or(0));
        roles.insert(ids.begin(), ids.end());
    }
    return roles;
}

std::set<std::string> SysPermissionService::getMenuPermission(const cm::domain::SysUser& user) {
    std::set<std::string> perms;
    if (user.isAdmin()) {
        perms.insert("*:*:*");
    } else {
        // 对应 menuService.selectMenuPermsByUserId（会按逗号拆分）
        perms = cm::system::service::SysMenuService::selectMenuPermsByUserId(
            user.userId.value_or(0));
    }
    return perms;
}

// ---------------------------------------------------------------------------
// SysPasswordService
// ---------------------------------------------------------------------------
std::string SysPasswordService::getCacheKey(const std::string& username) {
    return std::string(cm::constant::Constants::PWD_ERR_CNT_KEY) + username;
}

bool SysPasswordService::matches(const cm::domain::SysUser& user, const std::string& rawPassword) {
    return SecurityUtils::matchesPassword(rawPassword, user.password.value_or(""));
}

void SysPasswordService::clearLoginRecordCache(const std::string& loginName) {
    auto& cache = cm::redis::RedisCache::instance();
    if (cache.exists(getCacheKey(loginName))) cache.del(getCacheKey(loginName));
}

void SysPasswordService::validate(const cm::domain::SysUser& user, const std::string& username,
                                  const std::string& password) {
    // ⚠️ 与 Java 对齐：RuoYi 3.8.7 实际通过 DaoAuthenticationProvider 校验密码，
    //    SysPasswordService.validate() 未被调用（无失败计数）。这里保留同样的行为，
    //    仅提供匹配判断；如启用计数需显式调用。
    if (!matches(user, password)) throw cm::exception::UserPasswordNotMatchException();
    clearLoginRecordCache(username);
}

// ---------------------------------------------------------------------------
// UserDetailsService
// ---------------------------------------------------------------------------
cm::domain::LoginUser UserDetailsService::createLoginUser(const cm::domain::SysUser& user) {
    cm::domain::LoginUser loginUser;
    loginUser.user = user;
    loginUser.permissions = SysPermissionService::getMenuPermission(user);
    return loginUser;
}

cm::domain::LoginUser UserDetailsService::loadUserByUsername(const std::string& username) {
    auto user = cm::system::mapper::SysUserMapper::selectUserByUserName(username);
    if (!user) {
        LOG_INFO("UserDetailsService", "登录用户：" + username + " 不存在.");
        // Java: UsernameNotFoundException -> DaoAuthenticationProvider 隐藏为 BadCredentials
        throw cm::exception::UserPasswordNotMatchException();
    }
    if (user->delFlag && *user->delFlag == "2") {
        LOG_INFO("UserDetailsService", "登录用户：" + username + " 已被删除.");
        throw cm::exception::BaseException("对不起，您的账号：" + username + " 已被删除");
    }
    if (user->status && *user->status == "1") {
        LOG_INFO("UserDetailsService", "登录用户：" + username + " 已被停用.");
        throw cm::exception::BaseException("对不起，您的账号：" + username + " 已停用");
    }
    return createLoginUser(*user);
}

// ---------------------------------------------------------------------------
// SysLoginService
// ---------------------------------------------------------------------------
void SysLoginService::recordLogininfor(const std::string& username, const std::string& status,
                                       const std::string& message,
                                       const cm::http::HttpRequest& request) {
    const std::string ip = TokenService::ipOf(request);
    const std::string address = TokenService::addressByIp(ip);
    const std::string browser = TokenService::browserOf(request.getHeader("User-Agent"));
    const std::string os = TokenService::osOf(request.getHeader("User-Agent"));

    // Constants.LOGIN_SUCCESS/LOGOUT/REGISTER -> "0"；LOGIN_FAIL -> "1"
    std::string dbStatus;
    if (status == cm::constant::Constants::LOGIN_FAIL) {
        dbStatus = "1";
    } else if (status == cm::constant::Constants::LOGIN_SUCCESS ||
               status == cm::constant::Constants::LOGOUT ||
               status == cm::constant::Constants::REGISTER) {
        dbStatus = "0";
    }
    LOG_INFO("sys-user", ip + " " + address + " " + username + " " + status + " " + message);
    cm::system::mapper::SysUserMapper::insertLogininfor(username, dbStatus, ip, address, browser, os,
                                                        message, nowMillis());
}

std::string SysLoginService::login(const std::string& username, const std::string& password,
                                   const std::string& code, const std::string& uuid,
                                   const cm::http::HttpRequest& request) {
    // 验证码校验（Java: CommonUtil.isNotBlank(code) 才校验）
    if (!trimCode(code).empty()) {
        const std::string verifyKey =
            std::string(cm::constant::Constants::CAPTCHA_CODE_KEY) + uuid;
        auto& cache = cm::redis::RedisCache::instance();
        auto captcha = cache.get(verifyKey);
        cache.del(verifyKey);
        if (!captcha) {
            recordLogininfor(username, cm::constant::Constants::LOGIN_FAIL, kMsgCaptchaExpire,
                             request);
            throw cm::exception::CaptchaExpireException();
        }
        if (!cm::utils::StringUtils::equalsIgnoreCase(code, *captcha)) {
            recordLogininfor(username, cm::constant::Constants::LOGIN_FAIL, kMsgCaptchaError,
                             request);
            throw cm::exception::CaptchaException();
        }
    }

    // 用户验证（对应 authenticationManager.authenticate）
    cm::domain::LoginUser loginUser;
    try {
        loginUser = UserDetailsService::loadUserByUsername(username);
        // DaoAuthenticationProvider 的密码校验
        if (!SysPasswordService::matches(loginUser.user, password)) {
            throw cm::exception::UserPasswordNotMatchException();
        }
    } catch (const cm::exception::UserPasswordNotMatchException&) {
        recordLogininfor(username, cm::constant::Constants::LOGIN_FAIL, kMsgPwdNotMatch, request);
        throw;
    } catch (const cm::exception::BaseException& e) {
        recordLogininfor(username, cm::constant::Constants::LOGIN_FAIL, e.getMessage(), request);
        throw cm::exception::CustomException(e.getMessage());
    } catch (const std::exception& e) {
        recordLogininfor(username, cm::constant::Constants::LOGIN_FAIL, e.what(), request);
        throw cm::exception::CustomException(e.what());
    }

    recordLogininfor(username, cm::constant::Constants::LOGIN_SUCCESS, kMsgLoginSuccess, request);
    return TokenService::instance().createToken(loginUser, request);
}

} // namespace cm::security
