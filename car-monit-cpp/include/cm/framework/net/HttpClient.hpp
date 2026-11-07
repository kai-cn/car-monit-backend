#pragma once
// 极简出站 HTTP/1.1 客户端（零第三方 HTTP 依赖，建在 cm::net 的传输原语之上）。
//
// 对应 Java：Forest（`@Get`/`@Post` 声明式客户端）+ Apache httpclient，
// 配置见 application.yml 的 `vehicleMonitor.baseUrl` / `forest.variables.hendaUrl` /
// `roadPathUrl` / `oss.endpoint`，超时 60s、`BackOffRetryer` 重试 2 次
// （异常边界逐条分析见 COMPATIBILITY.md §5.1）。
//
// 传输层：http 走明文 socket；https 走 vendored mbedTLS（third_party/mbedtls）。
// 两条路径共用同一套请求构造与响应解析，只有字节收发不同。
// TLS 强制校验证书链与主机名，CA 来自 third_party/cacert.pem（可用配置覆盖）。
//
// ⚠️ 与 Java 的差异：
//   * 不自动跟随重定向（Forest/httpclient 对 GET 默认跟随）：原样返回 3xx 与 Location。
//   * 重试对齐 Forest 的 BackOffRetryer（retry-count=2、间隔 min(2^n×1000, 1s)、
//     传输异常或非 2xx 都重试），但**非幂等方法默认不重试**（Forest 是全局配置）；
//     查询型 POST 需调用方显式置 `retryNonIdempotent=true`。
//     注意最坏耗时：3 次尝试 × 单次超时 + 2×1s（默认 60s 读超时下约 182s）。
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
    /** CA 证书包路径（PEM）。空 = 用默认：CM_CA_BUNDLE 环境变量 →
     *  third_party/cacert.pem → 系统 CA 路径。仅 https 使用。 */
    std::string caBundle;
    /** 失败重试次数（对应 Java Forest 全局 `retry-count: 2`）。
     *  触发条件与 Java 一致：传输层异常或非 2xx；间隔取 min(2^n × 1000, retryIntervalMs)。 */
    int maxRetryCount{2};
    /** 单次重试间隔上限（Forest `max-retry-interval: 1000`） */
    int retryIntervalMs{1000};
    /** 非幂等方法（POST/PUT/DELETE/PATCH）是否也重试。
     *  Java 的 Forest 配置是全局的、POST 也会重试；这里默认关闭，避免把"写"操作重放。
     *  查询型 POST（如 roadPath `/api/routes/query`）由调用方显式打开。 */
    bool retryNonIdempotent{false};
};

class HttpClient {
public:
    /** 进程级默认 CA 包（由 main 从 AppConfig 注入，对应 `cm.http.ca-bundle`） */
    static void setDefaultCaBundle(const std::string& path);
    static std::string defaultCaBundle();

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
