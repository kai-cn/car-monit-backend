#pragma once
// 对应 Java: com.ruoyi.system.domain.SysUpgradeInfo
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysUpgradeInfo : BaseEntity {
    std::optional<std::string> id;
    std::optional<std::string> ver;
    std::optional<std::string> info;
    std::optional<std::string> backCol1;
    std::optional<std::string> epsId;
    std::optional<std::string> delFlag;
    std::optional<long long> tenantId;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putStr(j, "id", id);
        putStr(j, "ver", ver);
        putStr(j, "info", info);
        putStr(j, "backCol1", backCol1);
        putStr(j, "epsId", epsId);
        putStr(j, "delFlag", delFlag);
        putI64(j, "tenantId", tenantId);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        id = getStr(j, "id");
        ver = getStr(j, "ver");
        info = getStr(j, "info");
        backCol1 = getStr(j, "backCol1");
        epsId = getStr(j, "epsId");
        delFlag = getStr(j, "delFlag");
        tenantId = getI64(j, "tenantId");
    }
};

} // namespace cm::domain
