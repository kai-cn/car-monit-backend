#pragma once
// 对应 Java: com.ruoyi.common.core.domain.entity.SysUser
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysDept.hpp"
#include "cm/common/core/domain/entity/SysRole.hpp"

namespace cm::domain {

struct SysUser : BaseEntity {
    std::optional<long long> userId;
    std::optional<long long> userNo;
    std::optional<long long> deptId;
    std::optional<std::string> userName;
    std::optional<std::string> nickName;
    std::optional<std::string> userType;
    std::optional<std::string> email;
    std::optional<std::string> phonenumber;
    std::optional<std::string> sex;
    std::optional<std::string> avatar;
    /** @JsonIgnore + @JsonProperty on getter: 只写不读 */
    std::optional<std::string> password;
    std::optional<std::string> confirmPassword;
    std::optional<std::string> salt;
    std::optional<std::string> status;
    std::optional<std::string> delFlag;
    std::optional<std::string> loginIp;
    /** 无 @JsonFormat -> ISO 文本 */
    std::optional<long long> loginDate;
    std::optional<std::string> certId;
    std::optional<std::string> certEntityId;
    std::optional<std::string> bussId;
    std::optional<std::string> bussName;
    std::optional<std::string> epsName;
    std::optional<long long> tenantId;
    std::optional<std::string> tenantName;
    std::optional<std::string> roleCode;
    std::optional<SysDept> dept;
    std::optional<std::vector<SysRole>> roles;
    std::optional<std::vector<long long>> roleIds;
    std::optional<std::vector<long long>> postIds;
    std::optional<std::string> flag;
    std::optional<std::string> dataId;
    std::optional<std::string> subCode;
    std::optional<std::string> queryNickName;
    std::optional<bool> excludeSelf;
    std::optional<long long> excludeId;
    std::optional<bool> headOffice;
    std::optional<bool> procurementManager;
    std::optional<std::string> deptName;
    int pjFlag{0};
    std::optional<std::string> imageId;

    bool isAdmin() const { return userId && *userId == 1L; }
    static bool isAdmin(std::optional<long long> id) { return id && *id == 1L; }

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "userId", userId);
        putI64(j, "userNo", userNo);
        putI64(j, "deptId", deptId);
        putStr(j, "userName", userName);
        putStr(j, "nickName", nickName);
        putStr(j, "userType", userType);
        putStr(j, "email", email);
        putStr(j, "phonenumber", phonenumber);
        putStr(j, "sex", sex);
        putStr(j, "avatar", avatar);
        // password 不输出
        putStr(j, "confirmPassword", confirmPassword);
        putStr(j, "salt", salt);
        putStr(j, "status", status);
        putStr(j, "delFlag", delFlag);
        putStr(j, "loginIp", loginIp);
        putIsoDate(j, "loginDate", loginDate);
        putStr(j, "certId", certId);
        putStr(j, "certEntityId", certEntityId);
        putStr(j, "bussId", bussId);
        putStr(j, "bussName", bussName);
        putStr(j, "epsName", epsName);
        putI64(j, "tenantId", tenantId);
        putStr(j, "tenantName", tenantName);
        putStr(j, "roleCode", roleCode);
        j["dept"] = dept ? dept->toJson() : Json(nullptr);
        if (roles) {
            Json arr = Json::array();
            for (const auto& r : *roles) arr.push_back(r.toJson());
            j["roles"] = arr;
        } else {
            j["roles"] = Json(nullptr);
        }
        j["roleIds"] = roleIds ? Json(*roleIds) : Json(nullptr);
        j["postIds"] = postIds ? Json(*postIds) : Json(nullptr);
        putStr(j, "flag", flag);
        putStr(j, "dataId", dataId);
        putStr(j, "subCode", subCode);
        putStr(j, "queryNickName", queryNickName);
        j["excludeSelf"] = excludeSelf ? Json(*excludeSelf) : Json(nullptr);
        putI64(j, "excludeId", excludeId);
        j["headOffice"] = headOffice ? Json(*headOffice) : Json(nullptr);
        j["procurementManager"] = procurementManager ? Json(*procurementManager) : Json(nullptr);
        putStr(j, "deptName", deptName);
        j["pjFlag"] = pjFlag;
        putStr(j, "imageId", imageId);
        // public boolean isAdmin() -> 虚拟属性
        j["admin"] = isAdmin();
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        userId = getI64(j, "userId");
        userNo = getI64(j, "userNo");
        deptId = getI64(j, "deptId");
        userName = getStr(j, "userName");
        nickName = getStr(j, "nickName");
        userType = getStr(j, "userType");
        email = getStr(j, "email");
        phonenumber = getStr(j, "phonenumber");
        sex = getStr(j, "sex");
        avatar = getStr(j, "avatar");
        password = getStr(j, "password");
        confirmPassword = getStr(j, "confirmPassword");
        salt = getStr(j, "salt");
        status = getStr(j, "status");
        delFlag = getStr(j, "delFlag");
        loginIp = getStr(j, "loginIp");
        loginDate = getDate(j, "loginDate");
        certId = getStr(j, "certId");
        certEntityId = getStr(j, "certEntityId");
        bussId = getStr(j, "bussId");
        bussName = getStr(j, "bussName");
        epsName = getStr(j, "epsName");
        tenantId = getI64(j, "tenantId");
        tenantName = getStr(j, "tenantName");
        roleCode = getStr(j, "roleCode");
        if (j.contains("dept") && j["dept"].is_object()) {
            SysDept d;
            d.fromJson(j["dept"]);
            dept = d;
        }
        if (j.contains("roles") && j["roles"].is_array()) {
            std::vector<SysRole> rs;
            for (const auto& e : j["roles"]) {
                SysRole r;
                r.fromJson(e);
                rs.push_back(r);
            }
            roles = rs;
        }
        if (j.contains("roleIds") && j["roleIds"].is_array()) {
            std::vector<long long> v;
            for (const auto& e : j["roleIds"]) {
                if (e.is_number_integer()) v.push_back(e.get<long long>());
                else if (e.is_string() && !e.get<std::string>().empty()) v.push_back(std::stoll(e.get<std::string>()));
            }
            roleIds = v;
        }
        if (j.contains("postIds") && j["postIds"].is_array()) {
            std::vector<long long> v;
            for (const auto& e : j["postIds"]) {
                if (e.is_number_integer()) v.push_back(e.get<long long>());
                else if (e.is_string() && !e.get<std::string>().empty()) v.push_back(std::stoll(e.get<std::string>()));
            }
            postIds = v;
        }
        flag = getStr(j, "flag");
        dataId = getStr(j, "dataId");
        subCode = getStr(j, "subCode");
        queryNickName = getStr(j, "queryNickName");
        excludeSelf = getBool(j, "excludeSelf");
        excludeId = getI64(j, "excludeId");
        headOffice = getBool(j, "headOffice");
        procurementManager = getBool(j, "procurementManager");
        deptName = getStr(j, "deptName");
        pjFlag = static_cast<int>(getI64(j, "pjFlag").value_or(0));
        imageId = getStr(j, "imageId");
    }
};

} // namespace cm::domain
