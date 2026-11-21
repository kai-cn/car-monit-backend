#include "cm/common/core/domain/AjaxResult.hpp"

#include <algorithm>
#include <cstdint>
#include <stdexcept>

namespace cm::core::domain {

namespace {
// 把 UTF-8 字符串解码为 UTF-16 code unit 序列（Java String#hashCode 基于 char）
std::vector<uint16_t> toUtf16(const std::string& s) {
    std::vector<uint16_t> out;
    size_t i = 0;
    while (i < s.size()) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        uint32_t cp = 0;
        size_t n = 0;
        if (c < 0x80) { cp = c; n = 1; }
        else if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; n = 2; }
        else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; n = 3; }
        else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; n = 4; }
        else { out.push_back(0xFFFD); ++i; continue; }
        if (i + n > s.size()) { out.push_back(0xFFFD); break; }
        for (size_t k = 1; k < n; ++k) {
            cp = (cp << 6) | (static_cast<unsigned char>(s[i + k]) & 0x3F);
        }
        i += n;
        if (cp <= 0xFFFF) {
            out.push_back(static_cast<uint16_t>(cp));
        } else {
            cp -= 0x10000;
            out.push_back(static_cast<uint16_t>(0xD800 + (cp >> 10)));
            out.push_back(static_cast<uint16_t>(0xDC00 + (cp & 0x3FF)));
        }
    }
    return out;
}
} // namespace

AjaxResult::AjaxResult() = default;

AjaxResult::AjaxResult(int code, const std::string& msg) : code_(code) {
    obj_[CODE_TAG] = code;
    obj_[MSG_TAG] = msg;
}

AjaxResult::AjaxResult(int code, const std::string& msg, const Json& data) : code_(code) {
    obj_[CODE_TAG] = code;
    obj_[MSG_TAG] = msg;
    // Java: if (StringUtils.isNotNull(data)) — null 不写入
    if (!data.is_null()) obj_[DATA_TAG] = data;
}

AjaxResult AjaxResult::success() { return AjaxResult(constant::HttpStatus::SUCCESS, "操作成功"); }

AjaxResult AjaxResult::success(const std::string& msg) { return AjaxResult(constant::HttpStatus::SUCCESS, msg); }
AjaxResult AjaxResult::success(const char* msg) { return AjaxResult(constant::HttpStatus::SUCCESS, msg ? msg : ""); }

AjaxResult AjaxResult::success(const Json& data) {
    return AjaxResult(constant::HttpStatus::SUCCESS, "操作成功", data);
}

AjaxResult AjaxResult::success(const std::string& msg, const Json& data) {
    return AjaxResult(constant::HttpStatus::SUCCESS, msg, data);
}

AjaxResult AjaxResult::warn(const std::string& msg) {
    return AjaxResult(constant::HttpStatus::WARN, msg);
}

AjaxResult AjaxResult::warn(const std::string& msg, const Json& data) {
    return AjaxResult(constant::HttpStatus::WARN, msg, data);
}

AjaxResult AjaxResult::error() { return AjaxResult(constant::HttpStatus::ERROR, "操作失败"); }
AjaxResult AjaxResult::error(const std::string& msg) { return AjaxResult(constant::HttpStatus::ERROR, msg); }
AjaxResult AjaxResult::error(const char* msg) { return AjaxResult(constant::HttpStatus::ERROR, msg ? msg : ""); }

AjaxResult AjaxResult::error(const std::string& msg, const Json& data) {
    return AjaxResult(constant::HttpStatus::ERROR, msg, data);
}

AjaxResult AjaxResult::error(int code, const std::string& msg) { return AjaxResult(code, msg); }

bool AjaxResult::isSuccess() const { return code_ == constant::HttpStatus::SUCCESS; }
bool AjaxResult::isWarn() const { return code_ == constant::HttpStatus::WARN; }
bool AjaxResult::isError() const { return code_ == constant::HttpStatus::ERROR; }

AjaxResult& AjaxResult::put(const std::string& key, const Json& value) {
    obj_[key] = value;
    if (key == CODE_TAG && value.is_number_integer()) code_ = value.get<int>();
    return *this;
}
AjaxResult& AjaxResult::put(const std::string& key, const std::string& value) { return put(key, Json(value)); }
AjaxResult& AjaxResult::put(const std::string& key, const char* value) { return put(key, Json(value ? value : "")); }
AjaxResult& AjaxResult::put(const std::string& key, long long value) { return put(key, Json(value)); }
AjaxResult& AjaxResult::put(const std::string& key, int value) { return put(key, Json(value)); }
AjaxResult& AjaxResult::put(const std::string& key, bool value) { return put(key, Json(value)); }

Json AjaxResult::get(const std::string& key) const {
    auto it = obj_.find(key);
    return it == obj_.end() ? Json() : *it;
}

int AjaxResult::javaStringHash(const std::string& s) {
    uint32_t h = 0;
    for (uint16_t cu : toUtf16(s)) {
        h = h * 31u + cu;
    }
    return static_cast<int>(h);
}

int AjaxResult::bucketIndex(const std::string& key, int capacity) {
    uint32_t h = static_cast<uint32_t>(javaStringHash(key));
    uint32_t spread = h ^ (h >> 16);
    return static_cast<int>(spread & static_cast<uint32_t>(capacity - 1));
}

std::vector<std::string> AjaxResult::hashMapOrder(const std::vector<std::string>& keys) {
    // HashMap 默认容量 16、负载因子 0.75：第 13 个键触发扩容到 32，以此类推。
    int capacity = 16;
    while (static_cast<double>(keys.size()) > capacity * 0.75) capacity *= 2;
    std::vector<std::pair<int, size_t>> idx;
    idx.reserve(keys.size());
    for (size_t i = 0; i < keys.size(); ++i) {
        idx.emplace_back(bucketIndex(keys[i], capacity), i);
    }
    std::stable_sort(idx.begin(), idx.end(),
                     [](const auto& a, const auto& b) { return a.first < b.first; });
    std::vector<std::string> out;
    out.reserve(keys.size());
    for (const auto& p : idx) out.push_back(keys[p.second]);
    return out;
}

Json AjaxResult::toJson() const {
    std::vector<std::string> keys;
    keys.reserve(obj_.size());
    for (auto it = obj_.begin(); it != obj_.end(); ++it) keys.push_back(it.key());
    Json out = Json::object();
    for (const auto& k : hashMapOrder(keys)) out[k] = obj_[k];
    return out;
}

std::string AjaxResult::dump() const { return cm::dumpLenient(toJson()); }

} // namespace cm::core::domain
