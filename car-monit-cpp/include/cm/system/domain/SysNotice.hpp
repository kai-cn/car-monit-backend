#pragma once
// 对应 Java: com.ruoyi.system.domain.SysNotice
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysNotice : BaseEntity {
    std::optional<long long> noticeId;
    std::optional<std::string> noticeTitle;
    std::optional<std::string> noticeType;
    std::optional<std::string> noticeContent;
    std::optional<std::string> status;
    std::optional<std::string> bussId;
    std::optional<std::string> bussName;
    std::optional<long long> tenantId;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "noticeId", noticeId);
        putStr(j, "noticeTitle", noticeTitle);
        putStr(j, "noticeType", noticeType);
        putStr(j, "noticeContent", noticeContent);
        putStr(j, "status", status);
        putStr(j, "bussId", bussId);
        putStr(j, "bussName", bussName);
        putI64(j, "tenantId", tenantId);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        noticeId = getI64(j, "noticeId");
        noticeTitle = getStr(j, "noticeTitle");
        noticeType = getStr(j, "noticeType");
        noticeContent = getStr(j, "noticeContent");
        status = getStr(j, "status");
        bussId = getStr(j, "bussId");
        bussName = getStr(j, "bussName");
        tenantId = getI64(j, "tenantId");
    }
};

} // namespace cm::domain
