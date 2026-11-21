#pragma once
// 对应 Java: com.ruoyi.common.core.domain.entity.SysDept
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysDept;

struct SysDept : BaseEntity {
    std::optional<long long> deptId;
    std::optional<long long> parentId;
    std::optional<std::string> ancestors;
    std::optional<std::string> deptName;
    std::optional<std::string> orderNum;
    std::optional<long long> leaderId;
    std::optional<std::string> leader;
    std::optional<long long> fgldId;
    std::optional<std::string> fgldName;
    std::optional<std::string> bankName;
    std::optional<std::string> account;
    std::optional<std::string> socialCode;
    std::optional<std::string> postalCode;
    std::optional<std::string> address;
    std::optional<std::string> phone;
    std::optional<std::string> email;
    std::optional<std::string> status;
    std::optional<std::string> isZbzg;
    std::optional<std::string> isUint;
    std::optional<long long> treeLeavel;
    std::optional<std::string> subCode;
    std::optional<std::string> deptJc;
    std::optional<std::string> delFlag;
    std::optional<std::string> parentName;
    std::vector<SysDept> children;
    std::optional<long long> tenantId;
    std::optional<std::string> flag;
    std::optional<std::string> dataId;
    std::optional<std::string> deptSubCode;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "deptId", deptId);
        putI64(j, "parentId", parentId);
        putStr(j, "ancestors", ancestors);
        putStr(j, "deptName", deptName);
        putStr(j, "orderNum", orderNum);
        putI64(j, "leaderId", leaderId);
        putStr(j, "leader", leader);
        putI64(j, "fgldId", fgldId);
        putStr(j, "fgldName", fgldName);
        putStr(j, "bankName", bankName);
        putStr(j, "account", account);
        putStr(j, "socialCode", socialCode);
        putStr(j, "postalCode", postalCode);
        putStr(j, "address", address);
        putStr(j, "phone", phone);
        putStr(j, "email", email);
        putStr(j, "status", status);
        putStr(j, "isZbzg", isZbzg);
        putStr(j, "isUint", isUint);
        putI64(j, "treeLeavel", treeLeavel);
        putStr(j, "subCode", subCode);
        putStr(j, "deptJc", deptJc);
        putStr(j, "delFlag", delFlag);
        putStr(j, "parentName", parentName);
        Json kids = Json::array();
        for (const auto& c : children) kids.push_back(c.toJson());
        j["children"] = kids;
        putI64(j, "tenantId", tenantId);
        putStr(j, "flag", flag);
        putStr(j, "dataId", dataId);
        putStr(j, "deptSubCode", deptSubCode);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        deptId = getI64(j, "deptId");
        parentId = getI64(j, "parentId");
        ancestors = getStr(j, "ancestors");
        deptName = getStr(j, "deptName");
        orderNum = getStr(j, "orderNum");
        leaderId = getI64(j, "leaderId");
        leader = getStr(j, "leader");
        fgldId = getI64(j, "fgldId");
        fgldName = getStr(j, "fgldName");
        bankName = getStr(j, "bankName");
        account = getStr(j, "account");
        socialCode = getStr(j, "socialCode");
        postalCode = getStr(j, "postalCode");
        address = getStr(j, "address");
        phone = getStr(j, "phone");
        email = getStr(j, "email");
        status = getStr(j, "status");
        isZbzg = getStr(j, "isZbzg");
        isUint = getStr(j, "isUint");
        treeLeavel = getI64(j, "treeLeavel");
        subCode = getStr(j, "subCode");
        deptJc = getStr(j, "deptJc");
        delFlag = getStr(j, "delFlag");
        parentName = getStr(j, "parentName");
        tenantId = getI64(j, "tenantId");
        flag = getStr(j, "flag");
        dataId = getStr(j, "dataId");
        deptSubCode = getStr(j, "deptSubCode");
    }
};

} // namespace cm::domain
