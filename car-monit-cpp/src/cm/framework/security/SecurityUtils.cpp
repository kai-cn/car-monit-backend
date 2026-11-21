#include "cm/framework/security/SecurityUtils.hpp"

#include <bcrypt/bcrypt.h>

#include <stdexcept>

#include "cm/common/exception/Exceptions.hpp"

namespace cm::security {
namespace {

thread_local std::optional<cm::domain::LoginUser> g_loginUser;

} // namespace

void SecurityUtils::setLoginUser(const cm::domain::LoginUser& user) { g_loginUser = user; }
void SecurityUtils::clear() { g_loginUser.reset(); }
bool SecurityUtils::isAuthenticated() { return g_loginUser.has_value(); }
std::optional<cm::domain::LoginUser> SecurityUtils::current() { return g_loginUser; }

cm::domain::LoginUser SecurityUtils::getLoginUser() {
    if (!g_loginUser) {
        throw cm::exception::CustomException("获取用户信息异常", 401);
    }
    return *g_loginUser;
}

std::string SecurityUtils::getUsername() {
    try {
        auto lu = g_loginUser;
        if (!lu) throw std::runtime_error("no auth");
        return lu->user.userName.value_or("");
    } catch (...) {
        throw cm::exception::CustomException("获取用户账户异常", 401);
    }
}

long long SecurityUtils::getUserId() {
    try {
        if (!g_loginUser) throw std::runtime_error("no auth");
        const auto& u = g_loginUser->user;
        if (!u.userId) return -1L;
        return *u.userId;
    } catch (...) {
        throw cm::exception::CustomException("获取用户账户异常", 401);
    }
}

std::string SecurityUtils::getUserRealName() {
    try {
        if (!g_loginUser) throw std::runtime_error("no auth");
        return g_loginUser->user.nickName.value_or("");
    } catch (...) {
        throw cm::exception::CustomException("获取用户账户异常", 401);
    }
}

long long SecurityUtils::getEpsId() {
    try {
        if (!g_loginUser) throw std::runtime_error("no auth");
        return g_loginUser->user.deptId.value_or(-1L);
    } catch (...) {
        throw cm::exception::CustomException("获取用户账户异常", 401);
    }
}

std::string SecurityUtils::getEps() {
    try {
        if (!g_loginUser) throw std::runtime_error("no auth");
        return g_loginUser->user.epsName.value_or("");
    } catch (...) {
        throw cm::exception::CustomException("获取用户账户异常", 401);
    }
}

long long SecurityUtils::getTenantId() {
    try {
        if (!g_loginUser) throw std::runtime_error("no auth");
        return g_loginUser->user.tenantId.value_or(-1L);
    } catch (...) {
        throw cm::exception::CustomException("获取用户账户异常", 401);
    }
}

std::string SecurityUtils::getDeptSubCode() {
    try {
        if (!g_loginUser) throw std::runtime_error("no auth");
        return g_loginUser->user.subCode.value_or("-1");
    } catch (...) {
        throw cm::exception::CustomException("获取用户账户异常", 401);
    }
}

std::string SecurityUtils::encryptPassword(const std::string& password) {
    char salt[BCRYPT_HASHSIZE] = {0};
    char hash[BCRYPT_HASHSIZE] = {0};
    // Spring BCryptPasswordEncoder 默认 strength = 10
    if (bcrypt_gensalt(10, salt) != 0) return "";
    if (bcrypt_hashpw(password.c_str(), salt, hash) != 0) return "";
    return std::string(hash);
}

bool SecurityUtils::matchesPassword(const std::string& rawPassword, const std::string& encodedPassword) {
    if (encodedPassword.empty()) return false;
    return bcrypt_checkpw(rawPassword.c_str(), encodedPassword.c_str()) == 0;
}

bool SecurityUtils::isAdmin(std::optional<long long> userId) { return userId && *userId == 1L; }

bool SecurityUtils::simpleMatch(const std::string& pattern, const std::string& str) {
    if (pattern.empty() || str.empty()) return false;
    if (pattern == "*") return true;
    size_t pi = 0, si = 0, star = std::string::npos, mark = 0;
    while (si < str.size()) {
        if (pi < pattern.size() && (pattern[pi] == '?' || pattern[pi] == str[si])) {
            ++pi;
            ++si;
        } else if (pi < pattern.size() && pattern[pi] == '*') {
            star = pi++;
            mark = si;
        } else if (star != std::string::npos) {
            pi = star + 1;
            si = ++mark;
        } else {
            return false;
        }
    }
    while (pi < pattern.size() && pattern[pi] == '*') ++pi;
    return pi == pattern.size();
}

bool SecurityUtils::hasPermi(const std::string& permission) {
    if (permission.empty()) return false;
    auto lu = g_loginUser;
    if (!lu || lu->permissions.empty()) return false;
    for (const auto& p : lu->permissions) {
        if (p.empty()) continue;
        if (p == "*:*:*" || simpleMatch(p, permission)) return true;
    }
    return false;
}

bool SecurityUtils::hasRole(const std::string& role) {
    if (role.empty()) return false;
    auto lu = g_loginUser;
    if (!lu || !lu->user.roles) return false;
    for (const auto& r : *lu->user.roles) {
        const std::string& key = r.roleKey.value_or("");
        if (key == "admin" || simpleMatch(key, role)) return true;
    }
    return false;
}

} // namespace cm::security
