#include "cm/framework/web/RepeatSubmit.hpp"

#include <chrono>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/security/TokenService.hpp"

namespace cm::web {
namespace {

long long nowMillis() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

} // namespace

bool repeatSubmitHit(const std::string& cached, const std::string& url, const std::string& params,
                     long long nowMs, int intervalMs) {
    // 空值直接判定"没有记录"：不要进解析器（见 parse_json 对空输入的说明）
    if (cached.empty()) return false;
    try {
        const Json m = cm::utils::parse_cached_json(cached);
        const Json* prev = m.is_object() && m.contains(url) && m[url].is_object() ? &m[url] : nullptr;
        if (prev == nullptr) return false;
        const std::string prevParams = cm::jstr(*prev, "repeatParams", "");
        long long prevTime = 0;
        const Json* t = prev->contains("repeatTime") ? &(*prev)["repeatTime"] : nullptr;
        if (t != nullptr && t->is_number()) prevTime = t->get<long long>();
        return prevParams == params && (nowMs - prevTime) < intervalMs;
    } catch (...) {
        return false;  // 缓存内容不可解析：当作没有记录
    }
}

std::optional<cm::http::ApiResponse> checkRepeatSubmit(const cm::http::HttpRequest& req,
                                                       const std::string& url, int intervalMs) {
    // Java: StringUtils.trimToEmpty(request.getHeader(header)) —— 原样取头，不剥 "Bearer "
    const std::string submitKey = cm::utils::StringUtils::trim(
        req.getHeader(cm::security::TokenService::instance().header()));
    const std::string key = std::string(cm::constant::Constants::REPEAT_SUBMIT_KEY) + url + submitKey;

    // Java: RepeatedlyRequestWrapper 读 body；body 为空时退化为 parameterMap 的 JSON。
    // 这里的调用面是 @RequestBody，body 一定存在；为空时用 "{}" 对齐空 Map 的序列化。
    const std::string params = req.body.empty() ? std::string("{}") : req.body;
    const long long now = nowMillis();

    auto cached = cm::redis::RedisCache::instance().get(key);
    if (cached && repeatSubmitHit(*cached, url, params, now, intervalMs)) {
        // Java 走 ServletUtils.renderString ⇒ Content-Type 是**小写 utf-8**、HTTP 200
        return cm::http::ApiResponse::json(
            cm::core::domain::AjaxResult::error("不允许重复提交，请稍候再试").toJson(),
            "application/json;charset=utf-8");
    }

    // 写入 fastjson2 形态：Java 侧用 Object 反序列化后按 Map 读，
    // 嵌套的 repeatTime 是 Long，fastjson2 会写成带 L 的形式。
    std::string value = "{\"@type\":\"java.util.HashMap\",";
    value += Json(url).dump() + ":{\"repeatParams\":" + Json(params).dump() +
             ",\"repeatTime\":" + std::to_string(now) + "L}}";
    cm::redis::RedisCache::instance().client().psetex(key, value, intervalMs);
    return std::nullopt;
}

} // namespace cm::web
