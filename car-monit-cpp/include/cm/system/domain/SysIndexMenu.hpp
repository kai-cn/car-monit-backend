#pragma once
// 对应 Java: com.ruoyi.system.domain.SysIndexMenu
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysIndexMenu : BaseEntity {
    std::optional<long long> id;
    std::optional<long long> userId;
    std::optional<long long> menuId;
    std::optional<std::string> sort;
    std::optional<long long> epsId;
    std::optional<std::string> delFlag;
    std::optional<long long> tenantId;
    std::optional<std::string> menuName;
    std::optional<std::string> menuName1;
    std::optional<std::string> menuName2;
    std::optional<std::string> menuName3;
    std::optional<std::string> menuIds;
    std::optional<std::string> menuUrl;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "id", id);
        putI64(j, "userId", userId);
        putI64(j, "menuId", menuId);
        putStr(j, "sort", sort);
        putI64(j, "epsId", epsId);
        putStr(j, "delFlag", delFlag);
        putI64(j, "tenantId", tenantId);
        putStr(j, "menuName", menuName);
        putStr(j, "menuName1", menuName1);
        putStr(j, "menuName2", menuName2);
        putStr(j, "menuName3", menuName3);
        putStr(j, "menuIds", menuIds);
        putStr(j, "menuUrl", menuUrl);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        id = getI64(j, "id");
        userId = getI64(j, "userId");
        menuId = getI64(j, "menuId");
        sort = getStr(j, "sort");
        epsId = getI64(j, "epsId");
        delFlag = getStr(j, "delFlag");
        tenantId = getI64(j, "tenantId");
        menuName = getStr(j, "menuName");
        menuName1 = getStr(j, "menuName1");
        menuName2 = getStr(j, "menuName2");
        menuName3 = getStr(j, "menuName3");
        menuIds = getStr(j, "menuIds");
        menuUrl = getStr(j, "menuUrl");
    }
};

} // namespace cm::domain
