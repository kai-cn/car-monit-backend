#pragma once
// 对应 Java: com.alibaba.fastjson2 / Jackson 的 JSON 能力封装。
//
// ⚠️ C++ 侧使用 nlohmann::ordered_json：
//    * 对象内部保持插入顺序（对应 Jackson 的 POJO 字段声明序）
//    * 统一 UTF-8 输出，不转义中文（对应 Jackson 默认 WRITE_CHAR_ARRAY_AS_JSON_ARRAY 行为）
//    * 数字按最短表示输出（整数原样，浮点与 Jackson 略有差异，见 COMPATIBILITY.md）
#include <nlohmann/json.hpp>
#include <optional>
#include <string>
#include <vector>

namespace cm {

using Json = nlohmann::ordered_json;

/** 便捷构造 / 读取函数 */
inline Json jnull() { return Json(nullptr); }
inline Json jarr() { return Json::array(); }
inline Json jobj() { return Json::object(); }

inline std::string jstr(const Json& j, const char* key, const std::string& def = "") {
    if (!j.is_object()) return def;
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    if (it->is_string()) return it->get<std::string>();
    return it->dump();
}

inline long long jlong(const Json& j, const char* key, long long def = 0) {
    if (!j.is_object()) return def;
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    if (it->is_number_integer()) return it->get<long long>();
    if (it->is_number_unsigned()) return static_cast<long long>(it->get<unsigned long long>());
    if (it->is_number_float()) return static_cast<long long>(it->get<double>());
    if (it->is_string()) {
        try { return std::stoll(it->get<std::string>()); } catch (...) { return def; }
    }
    return def;
}

inline bool jbool(const Json& j, const char* key, bool def = false) {
    if (!j.is_object()) return def;
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    if (it->is_boolean()) return it->get<bool>();
    if (it->is_number()) return it->get<double>() != 0;
    if (it->is_string()) {
        std::string s = it->get<std::string>();
        return s == "true" || s == "1" || s == "Y";
    }
    return def;
}

inline double jdouble(const Json& j, const char* key, double def = 0.0) {
    if (!j.is_object()) return def;
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    if (it->is_number()) return it->get<double>();
    if (it->is_string()) {
        try { return std::stod(it->get<std::string>()); } catch (...) { return def; }
    }
    return def;
}

/** 解析 JSON；失败抛 JsonParseException（对应 Jackson 的读取失败） */
Json parse_json(const std::string& text);

} // namespace cm
