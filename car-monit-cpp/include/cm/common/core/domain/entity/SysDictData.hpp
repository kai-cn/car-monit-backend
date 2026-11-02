#pragma once
// 对应 Java: com.ruoyi.common.core.domain.entity.SysDictData
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct SysDictData : BaseEntity {
    std::optional<long long> dictCode;
    std::optional<long long> dictSort;
    std::optional<std::string> dictLabel;
    std::optional<std::string> dictValue;
    std::optional<std::string> dictType;
    std::optional<std::string> cssClass;
    std::optional<std::string> listClass;
    std::optional<std::string> isDefault;
    std::optional<std::string> status;

    bool getDefault() const {
        return isDefault && *isDefault == "Y";
    }

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "dictCode", dictCode);
        putI64(j, "dictSort", dictSort);
        putStr(j, "dictLabel", dictLabel);
        putStr(j, "dictValue", dictValue);
        putStr(j, "dictType", dictType);
        putStr(j, "cssClass", cssClass);
        putStr(j, "listClass", listClass);
        putStr(j, "isDefault", isDefault);
        putStr(j, "status", status);
        j["default"] = getDefault();
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        dictCode = getI64(j, "dictCode");
        dictSort = getI64(j, "dictSort");
        dictLabel = getStr(j, "dictLabel");
        dictValue = getStr(j, "dictValue");
        dictType = getStr(j, "dictType");
        cssClass = getStr(j, "cssClass");
        listClass = getStr(j, "listClass");
        isDefault = getStr(j, "isDefault");
        status = getStr(j, "status");
    }
};

} // namespace cm::domain
