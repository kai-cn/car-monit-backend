#include "cm/framework/web/Errors.hpp"

#include "cm/common/utils/DateUtils.hpp"

namespace cm::web {

cm::http::ApiResponse unauthorized(const std::string& uri) {
    cm::core::domain::AjaxResult a(401, "请求访问：" + uri + "，认证失败，无法访问系统资源");
    cm::http::ApiResponse r;
    r.status = 200;
    r.content_type = "application/json;charset=utf-8";
    r.body = a.dump();   // AjaxResult::dump 走 dumpLenient：URI 里的非法字节不能把进程带下去
    return r;
}

cm::http::ApiResponse containerError(int status, const std::string& path) {
    Json j = Json::object();
    j["timestamp"] = cm::utils::DateUtils::formatIsoDate(cm::utils::DateUtils::nowMillis());
    j["status"] = status;
    j["error"] = status == 404 ? "Not Found"
                 : status == 403 ? "Forbidden"
                 : status == 400 ? "Bad Request"
                 : status == 405 ? "Method Not Allowed"
                                 : "Internal Server Error";
    j["path"] = path;
    cm::http::ApiResponse r;
    r.status = status;
    r.content_type = "application/json";
    r.body = cm::dumpLenient(j);
    return r;
}

} // namespace cm::web
