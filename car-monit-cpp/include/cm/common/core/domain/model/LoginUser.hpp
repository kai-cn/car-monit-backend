#pragma once
// 对应 Java: com.ruoyi.common.core.domain.model.LoginUser
#include <optional>
#include <set>
#include <string>

#include "cm/common/core/domain/entity/SysUser.hpp"

namespace cm::domain {

struct LoginUser {
    std::optional<std::string> token;
    std::optional<std::string> sessionId;
    std::optional<long long> loginTime;
    std::optional<long long> expireTime;
    std::optional<std::string> ipaddr;
    std::optional<std::string> loginLocation;
    std::optional<std::string> browser;
    std::optional<std::string> os;
    std::set<std::string> permissions;
    SysUser user;

    bool isAdmin() const { return user.isAdmin(); }

    Json toJson() const {
        Json j = Json::object();
        putStr(j, "token", token);
        putStr(j, "sessionId", sessionId);
        putI64(j, "loginTime", loginTime);
        putI64(j, "expireTime", expireTime);
        putStr(j, "ipaddr", ipaddr);
        putStr(j, "loginLocation", loginLocation);
        putStr(j, "browser", browser);
        putStr(j, "os", os);
        Json perms = Json::array();
        for (const auto& p : permissions) perms.push_back(p);
        j["permissions"] = perms;
        j["user"] = user.toJson();
        return j;
    }

    static LoginUser fromJson(const Json& j) {
        LoginUser u;
        u.token = getStr(j, "token");
        u.sessionId = getStr(j, "sessionId");
        u.loginTime = getI64(j, "loginTime");
        u.expireTime = getI64(j, "expireTime");
        u.ipaddr = getStr(j, "ipaddr");
        u.loginLocation = getStr(j, "loginLocation");
        u.browser = getStr(j, "browser");
        u.os = getStr(j, "os");
        if (j.contains("permissions") && j["permissions"].is_array()) {
            for (const auto& p : j["permissions"]) {
                if (p.is_string()) u.permissions.insert(p.get<std::string>());
            }
        }
        if (j.contains("user") && j["user"].is_object()) u.user.fromJson(j["user"]);
        return u;
    }
};

} // namespace cm::domain
