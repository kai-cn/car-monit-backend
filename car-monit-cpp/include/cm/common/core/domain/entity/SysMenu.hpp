#pragma once
// 对应 Java: com.ruoyi.common.core.domain.entity.SysMenu
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysMenu : BaseEntity {
    std::optional<long long> menuId;
    std::optional<std::string> menuName;
    std::optional<std::string> parentName;
    std::optional<long long> parentId;
    std::optional<std::string> orderNum;
    std::optional<std::string> path;
    std::optional<std::string> component;
    std::optional<std::string> isFrame;
    std::optional<std::string> isCache;
    std::optional<std::string> menuType;
    std::optional<std::string> visible;
    std::optional<std::string> status;
    std::optional<std::string> perms;
    std::optional<std::string> icon;
    std::vector<SysMenu> children;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "menuId", menuId);
        putStr(j, "menuName", menuName);
        putStr(j, "parentName", parentName);
        putI64(j, "parentId", parentId);
        putStr(j, "orderNum", orderNum);
        putStr(j, "path", path);
        putStr(j, "component", component);
        putStr(j, "isFrame", isFrame);
        putStr(j, "isCache", isCache);
        putStr(j, "menuType", menuType);
        putStr(j, "visible", visible);
        putStr(j, "status", status);
        putStr(j, "perms", perms);
        putStr(j, "icon", icon);
        Json kids = Json::array();
        for (const auto& c : children) kids.push_back(c.toJson());
        j["children"] = kids;
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        menuId = getI64(j, "menuId");
        menuName = getStr(j, "menuName");
        parentName = getStr(j, "parentName");
        parentId = getI64(j, "parentId");
        orderNum = getStr(j, "orderNum");
        path = getStr(j, "path");
        component = getStr(j, "component");
        isFrame = getStr(j, "isFrame");
        isCache = getStr(j, "isCache");
        menuType = getStr(j, "menuType");
        visible = getStr(j, "visible");
        status = getStr(j, "status");
        perms = getStr(j, "perms");
        icon = getStr(j, "icon");
    }
};

} // namespace cm::domain
