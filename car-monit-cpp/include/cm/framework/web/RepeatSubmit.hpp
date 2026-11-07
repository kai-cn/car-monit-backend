#pragma once
// 防重复提交（对应 Java：RepeatSubmitInterceptor + SameUrlDataInterceptor）
//
// Java 侧是对所有请求生效的拦截器，但只有打了 `@RepeatSubmit` 的方法才检查；
// 本项目目前只有 `POST /system/config` 一处使用（与 Java 一致）。
//
// 判定语义（逐条对齐 SameUrlDataInterceptor）：
//   * key = "repeat_submit:" + url + trimToEmpty(鉴权头原值，**不剥 "Bearer "**)
//   * 记录 {repeatParams = 请求体原文, repeatTime = 当前毫秒}
//   * 参数完全相同且时间差 < interval（`@RepeatSubmit.interval()` 默认 5000ms）⇒ 判定重复
//   * 命中返回 AjaxResult.error（HTTP 200 + code:500），与 Java 的 renderString 一致
//   * 未命中则写入本次记录，TTL = interval（毫秒级，对齐 setCacheObject(..., MILLISECONDS)）
#include <optional>
#include <string>

#include "cm/framework/http/HttpRequest.hpp"
#include "cm/framework/http/HttpResponse.hpp"

namespace cm::web {

/** 命中重复提交返回 error 响应；未命中写入记录并返回 nullopt。 */
std::optional<cm::http::ApiResponse> checkRepeatSubmit(const cm::http::HttpRequest& req,
                                                       const std::string& url,
                                                       int intervalMs = 5000);

/** 纯判定函数（可单测）：cached 是 Redis 里的原文（兼容 Java 的 fastjson2 形态）。 */
bool repeatSubmitHit(const std::string& cached, const std::string& url, const std::string& params,
                     long long nowMs, int intervalMs);

} // namespace cm::web
