// 对应 Java: com.ruoyi.system.service.impl.SysUserOnlineServiceImpl
#include "cm/system/service/SysUserOnlineService.hpp"

#include <algorithm>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/redis/RedisClient.hpp"

namespace cm::system::service {

cm::domain::SysUserOnline SysUserOnlineService::loginUserToUserOnline(const cm::domain::LoginUser& user) {
    cm::domain::SysUserOnline online;
    online.tokenId = user.token;
    online.sessionId = user.sessionId;
    online.userName = user.user.userName;
    online.ipaddr = user.ipaddr;
    online.loginLocation = user.loginLocation;
    online.browser = user.browser;
    online.os = user.os;
    online.loginTime = user.loginTime;
    if (user.user.dept && user.user.dept->deptName) {
        online.deptName = user.user.dept->deptName;
    }
    return online;
}

std::vector<cm::domain::SysUserOnline> SysUserOnlineService::selectOnlineByInfo(const std::string& ipaddr, const std::string& userName) {
    std::vector<cm::domain::SysUserOnline> result;
    auto& cache = cm::redis::RedisCache::instance();
    std::string pattern = std::string(cm::constant::Constants::LOGIN_TOKEN_KEY) + "*";
    auto keys = cache.keys(pattern);

    for (const auto& key : keys) {
        auto jsonStr = cache.get(key);
        if (!jsonStr) continue;
        try {
            auto j = cm::utils::parse_cached_json(*jsonStr);
            cm::domain::LoginUser user = cm::domain::LoginUser::fromJson(j);
            if (!user.user.userId) continue;

            bool matchIp = ipaddr.empty() || (user.ipaddr && *user.ipaddr == ipaddr);
            bool matchUser = userName.empty() || (user.user.userName && *user.user.userName == userName);

            if (!ipaddr.empty() && !userName.empty()) {
                if (!matchIp || !matchUser) continue;
            } else if (!ipaddr.empty()) {
                if (!matchIp) continue;
            } else if (!userName.empty()) {
                if (!matchUser) continue;
            }

            result.push_back(loginUserToUserOnline(user));
        } catch (...) {
            continue;
        }
    }

    std::reverse(result.begin(), result.end());
    return result;
}

} // namespace cm::system::service
