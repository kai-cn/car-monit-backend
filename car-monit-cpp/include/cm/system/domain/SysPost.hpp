#pragma once
// 对应 Java: com.ruoyi.system.domain.SysPost
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysPost : BaseEntity {
    std::optional<long long> postId;
    std::optional<std::string> postCode;
    std::optional<std::string> postName;
    std::optional<std::string> postSort;
    std::optional<std::string> status;
    bool flag{false};

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "postId", postId);
        putStr(j, "postCode", postCode);
        putStr(j, "postName", postName);
        putStr(j, "postSort", postSort);
        putStr(j, "status", status);
        j["flag"] = flag;
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        postId = getI64(j, "postId");
        postCode = getStr(j, "postCode");
        postName = getStr(j, "postName");
        postSort = getStr(j, "postSort");
        status = getStr(j, "status");
        flag = getBool(j, "flag").value_or(false);
    }
};

} // namespace cm::domain
