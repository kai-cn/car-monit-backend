#pragma once
// 对应 Java: com.ruoyi.system.domain.SysUserOnline
#include <optional>
#include <string>

/* putStr/putI64 等序列化辅助函数定义在 BaseEntity.hpp 的 cm::domain 里 */
#include "cm/common/core/domain/BaseEntity.hpp"
#include "cm/common/utils/JsonUtils.hpp"

namespace cm::domain {

struct SysUserOnline {
    std::optional<std::string> tokenId;
    std::optional<std::string> sessionId;
    std::optional<std::string> deptName;
    std::optional<std::string> userName;
    std::optional<std::string> ipaddr;
    std::optional<std::string> loginLocation;
    std::optional<std::string> browser;
    std::optional<std::string> os;
    std::optional<long long> loginTime;

    Json toJson() const {
        Json j = Json::object();
        putStr(j, "tokenId", tokenId);
        putStr(j, "sessionId", sessionId);
        putStr(j, "deptName", deptName);
        putStr(j, "userName", userName);
        putStr(j, "ipaddr", ipaddr);
        putStr(j, "loginLocation", loginLocation);
        putStr(j, "browser", browser);
        putStr(j, "os", os);
        putI64(j, "loginTime", loginTime);
        return j;
    }
};

} // namespace cm::domain
