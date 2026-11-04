#pragma once
// 极简出站 HTTP/1.1 客户端（零第三方依赖，建在 cm::net 的传输原语之上）。
//
// 对应 Java：Forest（`@Get`/`@Post` 声明式客户端）+ Apache httpclient，
// 配置见 application.yml 的 `vehicleMonitor.baseUrl` / `forest.variables.hendaUrl` /
// `roadPathUrl` / `oss.endpoint`，超时 60s、`BackOffRetryer` 重试 2 次
// （异常边界逐条分析见 COMPATIBILITY.md §5.1）。
//
// ⚠️ 与 Java 的差异：
//   * 不支持 https（没有 TLS 实现）。遇到 https:// 直接返回传输层错误，
//     调用方按 Java 的 catch 分支处理（多数上游本来就是 http，只有腾讯地图是 https）。
//   * 不自动跟随重定向（Forest/httpclient 对 GET 默认跟随）：原样返回 3xx 与 Location。
//   * 不做重试：Java 的重试会让一次失败的外部调用最长占 3×60s，
//     这里把重试交给调用方，避免悄悄放大超时。
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "cm/framework/net/Fd.hpp"

namespace cm::net {

struct Url {
    bool ok{false};
    std::string scheme;
    std::string host;
    int port{80};
    std::string path{"/"};   // 不含 query
    std::string query;       // 不含 '?'
    std::string error;
};

Url parseUrl(const std::string& url);

/** 键值对 -> a=1&b=2（值做百分号编码，对应 Forest 的 @Query 拍平语义） */
std::string buildQuery(const std::vector<std::pair<std::string, std::string>>& params);
std::string urlEncodeQuery(const std::string& s);

struct HttpResponse {
    int status{0};
    std::vector<std::pair<std::string, std::string>> headers;  // 键已小写，保留原顺序
    std::string body;
    std::string error;      // 非空即传输层失败（对应 Java 的 IOException/超时）

    bool ok() const { return error.empty() && status > 0; }
    bool is2xx() const { return status >= 200 && status < 300; }
    std::string header(const std::string& lowerName) const;
};

struct HttpOptions {
    int connectTimeoutMs{10000};
    int readTimeoutMs{60000};
    long long maxBodyBytes{8LL * 1024 * 1024};
};

class HttpClient {
public:
    static HttpResponse get(const std::string& url,
                            const std::vector<std::pair<std::string, std::string>>& headers = {},
                            const HttpOptions& opt = {});
    /** 对应 Forest 的 `@Get(url)` + `@Query`：把参数拍平进 query */
    static HttpResponse getWithQuery(
        const std::string& url,
        const std::vector<std::pair<std::string, std::string>>& params,
        const std::vector<std::pair<std::string, std::string>>& headers = {},
        const HttpOptions& opt = {});
    static HttpResponse post(const std::string& url, const std::string& body,
                             const std::string& contentType,
                             const std::vector<std::pair<std::string, std::string>>& headers = {},
                             const HttpOptions& opt = {});
    static HttpResponse postForm(
        const std::string& url,
        const std::vector<std::pair<std::string, std::string>>& form,
        const std::vector<std::pair<std::string, std::string>>& headers = {},
        const HttpOptions& opt = {});
    /** DELETE + 可选响应体，S3 DeleteObject 用 */
    static HttpResponse send(const std::string& method, const std::string& url,
                             const std::string& body,
                             const std::vector<std::pair<std::string, std::string>>& headers,
                             const HttpOptions& opt = {});
};

/** 纯解析函数（单测直接覆盖：状态行、首部、Content-Length 与 chunked 两种成帧） */
HttpResponse parseResponse(const std::string& raw);
bool decodeChunked(const std::string& src, size_t from, std::string& out, std::string* err);

} // namespace cm::net
