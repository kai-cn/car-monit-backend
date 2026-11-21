#pragma once
// 对应 Java: com.ruoyi.system.domain.SysFile
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysFile : BaseEntity {
    std::optional<long long> id;
    std::optional<std::string> fileName;
    std::optional<std::string> bucketName;
    std::optional<std::string> original;
    std::optional<std::string> type;
    std::optional<long long> fileSize;
    std::optional<std::string> bussType;
    std::optional<std::string> bussName;
    std::optional<std::string> createUser;
    std::optional<std::string> updateUser;
    std::optional<std::string> delFlag;
    std::optional<long long> tenantId;
    std::optional<std::string> files;
    std::optional<std::string> createUserName;

    Json toJson() const {
        Json j = Json::object();
        // SysFile does not extend BaseEntity in Java, but has create/update fields
        putI64(j, "id", id);
        putStr(j, "fileName", fileName);
        putStr(j, "bucketName", bucketName);
        putStr(j, "original", original);
        putStr(j, "type", type);
        putI64(j, "fileSize", fileSize);
        putStr(j, "bussType", bussType);
        putStr(j, "bussName", bussName);
        putJsonDate(j, "createTime", createTime);
        putStr(j, "createUser", createUser);
        putJsonDate(j, "updateTime", updateTime);
        putStr(j, "updateUser", updateUser);
        putStr(j, "delFlag", delFlag);
        putI64(j, "tenantId", tenantId);
        putStr(j, "files", files);
        putStr(j, "createUserName", createUserName);
        return j;
    }

    void fromJson(const Json& j) {
        id = getI64(j, "id");
        fileName = getStr(j, "fileName");
        bucketName = getStr(j, "bucketName");
        original = getStr(j, "original");
        type = getStr(j, "type");
        fileSize = getI64(j, "fileSize");
        bussType = getStr(j, "bussType");
        bussName = getStr(j, "bussName");
        createTime = getDate(j, "createTime");
        createUser = getStr(j, "createUser");
        updateTime = getDate(j, "updateTime");
        updateUser = getStr(j, "updateUser");
        delFlag = getStr(j, "delFlag");
        tenantId = getI64(j, "tenantId");
        files = getStr(j, "files");
        createUserName = getStr(j, "createUserName");
    }
};

} // namespace cm::domain
