#pragma once
// 对应 Java: com.ruoyi.common.core.domain.BaseEntity
#include <optional>
#include <string>

#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/JsonUtils.hpp"

namespace cm::domain {

/** 序列化辅助：Jackson 默认 ALWAYS，null 也要输出 */
inline void putStr(Json& j, const char* key, const std::optional<std::string>& v) {
    j[key] = v ? Json(*v) : Json(nullptr);
}
inline void putI64(Json& j, const char* key, const std::optional<long long>& v) {
    j[key] = v ? Json(*v) : Json(nullptr);
}
inline void putJsonDate(Json& j, const char* key, const std::optional<long long>& v) {
    j[key] = v ? Json(utils::DateUtils::formatJsonDate(v)) : Json(nullptr);
}
inline void putIsoDate(Json& j, const char* key, const std::optional<long long>& v) {
    j[key] = v ? Json(utils::DateUtils::formatIsoDate(v)) : Json(nullptr);
}

inline std::optional<std::string> getStr(const Json& j, const char* key) {
    if (!j.is_object()) return std::nullopt;
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return std::nullopt;
    if (it->is_string()) return it->get<std::string>();
    return it->dump();
}
inline std::optional<long long> getI64(const Json& j, const char* key) {
    if (!j.is_object()) return std::nullopt;
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return std::nullopt;
    if (it->is_number_integer()) return it->get<long long>();
    if (it->is_number_float()) return static_cast<long long>(it->get<double>());
    if (it->is_string()) {
        const std::string& s = it->get_ref<const std::string&>();
        if (s.empty()) return std::nullopt;
        try { return std::stoll(s); } catch (...) { return std::nullopt; }
    }
    return std::nullopt;
}
inline std::optional<long long> getDate(const Json& j, const char* key) {
    auto it = j.is_object() ? j.find(key) : j.end();
    if (it == j.end() || it->is_null()) return std::nullopt;
    if (it->is_number()) return it->get<long long>();
    if (it->is_string()) {
        auto v = utils::DateUtils::parseDate(it->get<std::string>());
        if (v) return utils::DateUtils::toMillis(*v);
    }
    return std::nullopt;
}
inline std::optional<bool> getBool(const Json& j, const char* key) {
    if (!j.is_object()) return std::nullopt;
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return std::nullopt;
    if (it->is_boolean()) return it->get<bool>();
    if (it->is_number()) return it->get<double>() != 0;
    if (it->is_string()) {
        std::string s = it->get<std::string>();
        return s == "true" || s == "1" || s == "Y";
    }
    return std::nullopt;
}

/** 请求参数绑定：支持 JSON body / query / form */
std::optional<std::string> bindStr(const Json& j, const char* key);
std::optional<long long> bindI64(const Json& j, const char* key);
std::optional<long long> bindDate(const Json& j, const char* key);
std::optional<bool> bindBool(const Json& j, const char* key);

struct BaseEntity {
    /** Java: @JsonIgnore private String searchValue */
    std::optional<std::string> searchValue;
    std::optional<std::string> createBy;
    std::optional<long long> createTime; // epoch millis
    std::optional<std::string> updateBy;
    std::optional<long long> updateTime; // epoch millis
    std::optional<std::string> remark;
    Json params = Json::object();

    void baseToJson(Json& j) const {
        putStr(j, "createBy", createBy);
        putJsonDate(j, "createTime", createTime);
        putStr(j, "updateBy", updateBy);
        putJsonDate(j, "updateTime", updateTime);
        putStr(j, "remark", remark);
        // @JsonInclude(NON_EMPTY)
        if (!params.empty()) j["params"] = params;
    }

    void baseFromJson(const Json& j) {
        createBy = getStr(j, "createBy");
        createTime = getDate(j, "createTime");
        updateBy = getStr(j, "updateBy");
        updateTime = getDate(j, "updateTime");
        remark = getStr(j, "remark");
        auto it = j.is_object() ? j.find("params") : j.end();
        if (it != j.end() && it->is_object()) params = *it;
    }
};

} // namespace cm::domain
