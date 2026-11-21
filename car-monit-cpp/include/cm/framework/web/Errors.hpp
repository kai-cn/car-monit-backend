#pragma once
// 响应/错误封装工具（对应 Spring Boot 的 /error + AuthenticationEntryPointImpl）
#include <string>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/core/page/TableDataInfo.hpp"
#include "cm/framework/http/HttpResponse.hpp"

namespace cm::web {

/** JSON 响应（Content-Type: application/json;charset=UTF-8） */
inline cm::http::ApiResponse json(const Json& j) {
    cm::http::ApiResponse r;
    r.content_type = "application/json;charset=UTF-8";
    r.body = j.dump();
    return r;
}
inline cm::http::ApiResponse json(const cm::core::domain::AjaxResult& a) { return json(a.toJson()); }
inline cm::http::ApiResponse json(const cm::core::page::TableDataInfo& t) { return json(t.toJson()); }

/**
 * 401：AuthenticationEntryPointImpl -> ServletUtils.renderString
 * 注意 Content-Type 是 **小写 utf-8**，HTTP 状态 **200**。
 */
cm::http::ApiResponse unauthorized(const std::string& uri);

/**
 * Spring Boot BasicErrorController（真实 HTTP 状态码，无 message 字段）
 * 用于 403/404/500 的容器级错误。
 */
cm::http::ApiResponse containerError(int status, const std::string& path);

} // namespace cm::web
