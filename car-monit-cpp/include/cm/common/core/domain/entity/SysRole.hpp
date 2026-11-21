#pragma once
// 对应 Java: com.ruoyi.common.core.domain.entity.SysRole
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysRole : BaseEntity {
    std::optional<long long> roleId;
    std::optional<std::string> roleName;
    std::optional<std::string> roleKey;
    std::optional<std::string> roleSort;
    std::optional<std::string> dataScope;
    bool menuCheckStrictly{false};
    bool deptCheckStrictly{false};
    std::optional<std::string> status;
    std::optional<std::string> delFlag;
    bool flag{false};
    std::optional<std::vector<long long>> menuIds;
    std::optional<std::vector<long long>> deptIds;

    bool isAdmin() const { return roleId && *roleId == 1L; }
    static bool isAdmin(std::optional<long long> id) { return id && *id == 1L; }

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "roleId", roleId);
        putStr(j, "roleName", roleName);
        putStr(j, "roleKey", roleKey);
        putStr(j, "roleSort", roleSort);
        putStr(j, "dataScope", dataScope);
        j["menuCheckStrictly"] = menuCheckStrictly;
        j["deptCheckStrictly"] = deptCheckStrictly;
        putStr(j, "status", status);
        putStr(j, "delFlag", delFlag);
        j["flag"] = flag;
        j["menuIds"] = menuIds ? Json(*menuIds) : Json(nullptr);
        j["deptIds"] = deptIds ? Json(*deptIds) : Json(nullptr);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        roleId = getI64(j, "roleId");
        roleName = getStr(j, "roleName");
        roleKey = getStr(j, "roleKey");
        roleSort = getStr(j, "roleSort");
        dataScope = getStr(j, "dataScope");
        menuCheckStrictly = getBool(j, "menuCheckStrictly").value_or(false);
        deptCheckStrictly = getBool(j, "deptCheckStrictly").value_or(false);
        status = getStr(j, "status");
        delFlag = getStr(j, "delFlag");
        flag = getBool(j, "flag").value_or(false);
        auto parse_ids = [](const Json& v) -> std::optional<std::vector<long long>> {
            if (!v.is_array()) return std::nullopt;
            std::vector<long long> out;
            for (const auto& e : v) {
                if (e.is_number_integer()) out.push_back(e.get<long long>());
                else if (e.is_string()) out.push_back(std::stoll(e.get<std::string>()));
            }
            return out;
        };
        if (j.contains("menuIds")) menuIds = parse_ids(j["menuIds"]);
        if (j.contains("deptIds")) deptIds = parse_ids(j["deptIds"]);
    }
};

} // namespace cm::domain
