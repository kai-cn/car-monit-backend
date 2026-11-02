#pragma once
// 对应 Java: com.ruoyi.system.domain.SysConfig
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysConfig : BaseEntity {
    std::optional<long long> configId;
    std::optional<std::string> configName;
    std::optional<std::string> configKey;
    std::optional<std::string> configValue;
    std::optional<std::string> configType;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "configId", configId);
        putStr(j, "configName", configName);
        putStr(j, "configKey", configKey);
        putStr(j, "configValue", configValue);
        putStr(j, "configType", configType);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        configId = getI64(j, "configId");
        configName = getStr(j, "configName");
        configKey = getStr(j, "configKey");
        configValue = getStr(j, "configValue");
        configType = getStr(j, "configType");
    }
};

} // namespace cm::domain
