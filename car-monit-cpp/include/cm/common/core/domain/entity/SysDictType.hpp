#pragma once
// 对应 Java: com.ruoyi.common.core.domain.entity.SysDictType
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysDictType : BaseEntity {
    std::optional<long long> dictId;
    std::optional<std::string> dictName;
    std::optional<std::string> dictType;
    std::optional<std::string> status;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "dictId", dictId);
        putStr(j, "dictName", dictName);
        putStr(j, "dictType", dictType);
        putStr(j, "status", status);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        dictId = getI64(j, "dictId");
        dictName = getStr(j, "dictName");
        dictType = getStr(j, "dictType");
        status = getStr(j, "status");
    }
};

} // namespace cm::domain
