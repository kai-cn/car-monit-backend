#pragma once
// 对应 Java: javax.servlet.http.HttpServletResponse（仅迁移项目实际用到的能力）
#include <map>
#include <string>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::http {

class HttpResponse {
public:
    int status{200};
    std::map<std::string, std::string> headers;
    std::string body;

    void setHeader(const std::string& k, const std::string& v) { headers[k] = v; }
    void setContentType(const std::string& v) { headers["Content-Type"] = v; }
    void setStatus(int s) { status = s; }
};

struct ApiResponse {
    int status{200};
    std::string content_type{"application/json;charset=UTF-8"};
    std::string body;
    std::map<std::string, std::string> headers;

    static ApiResponse json(const Json& j,
                            const std::string& ct = "application/json;charset=UTF-8") {
        ApiResponse r;
        r.content_type = ct;
        r.body = j.dump();
        return r;
    }

    static ApiResponse text(const std::string& text, const std::string& ct = "text/plain;charset=UTF-8") {
        ApiResponse r;
        r.content_type = ct;
        r.body = text;
        return r;
    }

    static ApiResponse binary(std::string data, const std::string& ct) {
        ApiResponse r;
        r.content_type = ct;
        r.body = std::move(data);
        return r;
    }

    static ApiResponse notFound(const std::string& path);
};

} // namespace cm::http
