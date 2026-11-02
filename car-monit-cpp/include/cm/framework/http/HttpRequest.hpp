#pragma once
// 对应 Java: javax.servlet.http.HttpServletRequest（仅迁移项目实际用到的能力）
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::http {

struct MultipartPart {
    std::string name;
    std::string filename;
    std::string content_type;
    std::string data;
    std::map<std::string, std::string> headers;

    bool isFile() const { return !filename.empty(); }
};

class HttpRequest {
public:
    std::string method;
    /** 原始请求目标，例如 /system/user/list?pageNum=1 */
    std::string target;
    /** 去掉 query 的路径 */
    std::string path;
    std::string http_version;
    std::string remote_addr;
    int remote_port{0};
    std::string body;

    /** 按出现顺序保存 query 参数（对应 getParameterValues 的顺序语义） */
    std::vector<std::pair<std::string, std::string>> query_params;
    std::vector<std::pair<std::string, std::string>> form_params;
    std::vector<std::pair<std::string, std::string>> cookies;
    std::map<std::string, std::string> headers; // key 已转小写
    std::vector<MultipartPart> parts;

    std::string getHeader(const std::string& name) const;
    std::string getHeaderIgnoreCase(const std::string& name) const { return getHeader(name); }

    std::optional<std::string> getParameter(const std::string& name) const;
    std::vector<std::string> getParameterValues(const std::string& name) const;
    bool hasParameter(const std::string& name) const;
    std::string getParameterOr(const std::string& name, const std::string& def) const;

    std::optional<std::string> getCookie(const std::string& name) const;

    bool isMultipart() const;
    std::optional<MultipartPart> getPart(const std::string& name) const;

    std::string contentType() const { return getHeader("content-type"); }
    std::string userAgent() const { return getHeader("user-agent"); }
    std::string getRequestURI() const { return path; }
    std::string getMethod() const { return method; }
    std::string getRemoteAddr() const { return remote_addr; }
    std::string getSessionId() const;

    /** 解析 body 为 JSON；非法 JSON 抛 JsonParseException（对应 Jackson） */
    Json json() const;

    static std::string urlDecode(const std::string& s);
    static std::string urlEncode(const std::string& s);
    static void parseUrlEncoded(const std::string& text,
                                std::vector<std::pair<std::string, std::string>>& out);
    static void parseCookies(const std::string& header,
                             std::vector<std::pair<std::string, std::string>>& out);
    static std::vector<MultipartPart> parseMultipart(const std::string& body,
                                                     const std::string& content_type);
};

} // namespace cm::http
