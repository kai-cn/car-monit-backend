// 出站 HTTP 客户端的单测：URL 解析、query 编码、状态/首部解析、chunked 成帧、上限与 TLS。
#include <atomic>
#include <string>
#include <thread>
#include <vector>

#include "cm/framework/net/HttpClient.hpp"
#include "cm/framework/net/Os.hpp"

extern int g_fails;
#define fails g_fails
#define CK(x)                                                             \
    do {                                                                  \
        if (!(x)) {                                                       \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);       \
            ++fails;                                                      \
        }                                                                 \
    } while (0)
#define CK_EQ(a, b)                                                         \
    do {                                                                    \
        auto _va = (a);                                                     \
        auto _vb = (b);                                                     \
        if (!(_va == _vb)) {                                                \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                                        \
        }                                                                   \
    } while (0)

using cm::net::HttpResponse;
using cm::net::Url;

static void testParseUrl() {
    Url u = cm::net::parseUrl("http://127.0.0.1:9901/base/sysutil/getByTrailBo?carNo=A%201");
    CK(u.ok);
    CK_EQ(u.scheme, std::string("http"));
    CK_EQ(u.host, std::string("127.0.0.1"));
    CK_EQ(u.port, 9901);
    CK_EQ(u.path, std::string("/base/sysutil/getByTrailBo"));
    CK_EQ(u.query, std::string("carNo=A%201"));

    Url d = cm::net::parseUrl("http://36.200.20.14/geoserver/rest");
    CK(d.ok && d.port == 80);
    CK_EQ(d.host, std::string("36.200.20.14"));

    Url noPath = cm::net::parseUrl("http://a.b");
    CK(noPath.ok);
    CK_EQ(noPath.path, std::string("/"));

    Url bad = cm::net::parseUrl("127.0.0.1:9901/x");
    CK(!bad.ok);
    CK(!bad.error.empty());
    Url badPort = cm::net::parseUrl("http://h:0x");
    CK(!badPort.ok || badPort.port <= 0);  // 端口非数字要落到默认或报错，不能静默变负数
}

static void testTlsTransport() {
#ifdef CM_HAVE_TLS
    // 有 TLS 实现：用仓库内的 CA 包做负向验证（不可达地址 → 传输层错误，不崩、不当作明文发出去）
    cm::net::HttpOptions opt;
    opt.caBundle = std::string(CM_TEST_SOURCE_DIR) + "/third_party/cacert.pem";
    opt.connectTimeoutMs = 700;
    opt.readTimeoutMs = 700;
    CK(!cm::net::HttpClient::defaultCaBundle().empty() || !opt.caBundle.empty());
    HttpResponse refused = cm::net::HttpClient::get("https://127.0.0.1:1/x", {}, opt);
    CK(!refused.ok());
    CK(!refused.error.empty());
    // CA 路径不存在时必须明确报错，而不是悄悄跳过校验
    cm::net::HttpOptions noCa = opt;
    noCa.caBundle = std::string(CM_TEST_SOURCE_DIR) + "/third_party/does-not-exist.pem";
    HttpResponse noCaResp = cm::net::HttpClient::get("https://127.0.0.1:1/x", {}, noCa);
    CK(!noCaResp.ok());
    CK(noCaResp.error.find("CA") != std::string::npos);
#else
    // 无 TLS 构建：必须是明确的传输层错误，而不是崩或当作 http 发出去
    HttpResponse r = cm::net::HttpClient::get("https://apis.map.qq.com/ws/direction/v1/driving");
    CK(!r.ok());
    CK(r.error.find("TLS") != std::string::npos);
#endif
}

/** 明文链路端到端：请求行、Host 头（非默认端口要带端口）、响应解析 */
static void testPlainRequest() {
    using namespace cm::net;
    Fd lfd = listenTcp("127.0.0.1", 0, 8);
    CK(isValid(lfd));
    if (!isValid(lfd)) return;
    sockaddr_in sa{};
    socklen_t sl = sizeof(sa);
    ::getsockname(asSocket(lfd), reinterpret_cast<sockaddr*>(&sa), &sl);
    const int port = ntohs(sa.sin_port);

    std::string seen;
    std::thread server([&] {
        std::string peer;
        Fd sfd = acceptTcp(lfd, peer);
        if (!isValid(sfd)) return;
        char buf[4096];
        while (seen.find("\r\n\r\n") == std::string::npos) {
            const long n = readSome(sfd, buf, sizeof(buf));
            if (n <= 0) break;
            seen.append(buf, static_cast<size_t>(n));
        }
        const std::string resp =
            "HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok";
        writeAll(sfd, resp.data(), resp.size());
        closeTcp(sfd);
    });

    cm::net::HttpOptions opt;
    opt.connectTimeoutMs = 2000;
    opt.readTimeoutMs = 2000;
    HttpResponse r = cm::net::HttpClient::get("http://127.0.0.1:" + std::to_string(port) + "/x?a=1", {}, opt);
    server.join();
    closeTcp(lfd);

    CK_EQ(r.status, 200);
    CK_EQ(r.body, std::string("ok"));
    CK(r.error.empty());
    CK(seen.rfind("GET /x?a=1 HTTP/1.1\r\n", 0) == 0);
    // 非默认端口必须出现在 Host 里（默认 80/443 会被省略）
    CK(seen.find("Host: 127.0.0.1:" + std::to_string(port) + "\r\n") != std::string::npos);
}

/** Forest BackOffRetryer 语义：GET 失败重试 2 次；POST 默认不重试，显式开启才重试 */
static void testRetry() {
    using namespace cm::net;
    // 服务端：前 failures 次返回 500，之后返回 200；记录收到的请求数
    auto runServer = [](int failures, int expectMaxAccepts, std::atomic<int>& served) {
        Fd lfd = listenTcp("127.0.0.1", 0, 16);
        if (!isValid(lfd)) return std::pair<Fd, int>(kInvalid, 0);
        sockaddr_in sa{};
        socklen_t sl = sizeof(sa);
        ::getsockname(asSocket(lfd), reinterpret_cast<sockaddr*>(&sa), &sl);
        const int port = ntohs(sa.sin_port);
        std::thread th([&served, lfd, failures, expectMaxAccepts] {
            for (int i = 0; i < expectMaxAccepts; ++i) {
                std::string peer;
                Fd sfd = acceptTcp(lfd, peer);
                if (!isValid(sfd)) break;
                ++served;
                char buf[8192];
                while (true) {
                    const long n = readSome(sfd, buf, sizeof(buf));
                    if (n <= 0) break;
                    if (std::string(buf, static_cast<size_t>(n)).find("\r\n\r\n") != std::string::npos) break;
                }
                const bool ok = served > failures;
                const std::string resp = ok
                    ? "HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"
                    : "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 3\r\nConnection: close\r\n\r\nbad";
                writeAll(sfd, resp.data(), resp.size());
                closeTcp(sfd);
            }
        });
        th.detach();
        return std::pair<Fd, int>(lfd, port);
    };

    cm::net::HttpOptions opt;
    opt.connectTimeoutMs = 2000;
    opt.readTimeoutMs = 2000;
    opt.retryIntervalMs = 10;  // 测试不睡满 1s

    // GET：第 1 次 500，第 2 次 200 ⇒ 重试生效
    {
        std::atomic<int> served{0};
        auto [lfd, port] = runServer(1, 4, served);
        CK(isValid(lfd));
        if (isValid(lfd)) {
            const auto r = cm::net::HttpClient::get("http://127.0.0.1:" + std::to_string(port) + "/x", {}, opt);
            CK_EQ(r.status, 200);
            CK_EQ(served.load(), 2);
            closeTcp(lfd);
        }
    }
    // POST 默认不重试：两次都 500，服务端只应收到 1 次
    {
        std::atomic<int> served{0};
        auto [lfd, port] = runServer(2, 4, served);
        CK(isValid(lfd));
        if (isValid(lfd)) {
            const auto r = cm::net::HttpClient::post("http://127.0.0.1:" + std::to_string(port) + "/x", "b",
                                                     "text/plain", {}, opt);
            CK_EQ(r.status, 500);
            CK_EQ(served.load(), 1);
            closeTcp(lfd);
        }
    }
    // POST + retryNonIdempotent=true：重试一次后成功
    {
        std::atomic<int> served{0};
        auto [lfd, port] = runServer(1, 4, served);
        CK(isValid(lfd));
        if (isValid(lfd)) {
            cm::net::HttpOptions o2 = opt;
            o2.retryNonIdempotent = true;
            const auto r = cm::net::HttpClient::post("http://127.0.0.1:" + std::to_string(port) + "/x", "b",
                                                     "text/plain", {}, o2);
            CK_EQ(r.status, 200);
            CK_EQ(served.load(), 2);
            closeTcp(lfd);
        }
    }
}

static void testBuildQuery() {
    auto q = cm::net::buildQuery({{"carNo", "赣AK7388"}, {"n", "1 2+3/"}});
    // 空格 -> '+'（Apache httpclient URLEncodedUtils.format 的行为），'+' 自身要转 %2B
    CK(q.find("carNo=") == 0);
    CK(q.find("n=1+2%2B3%2F") != std::string::npos);
    CK(q.find('&') != std::string::npos);
}

static void testParseResponse() {
    const std::string raw =
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json;charset=UTF-8\r\n"
        "Content-Length: 8\r\n"
        "\r\n"
        "{\"ok\":1}\r\nEXTRA-IGNORED";
    HttpResponse r = cm::net::parseResponse(raw);
    CK(r.ok());
    CK_EQ(r.status, 200);
    CK_EQ(r.body, std::string("{\"ok\":1}"));
    // 首部键小写化，但原顺序保留
    CK_EQ(r.headers.size(), static_cast<size_t>(2));
    CK_EQ(r.headers[0].first, std::string("content-type"));
    CK_EQ(r.header("content-length"), std::string("8"));
    CK_EQ(r.header("missing"), std::string());
    CK(r.is2xx());

    HttpResponse noHead = cm::net::parseResponse("garbage");
    CK(!noHead.ok());

    // Content-Length 比实际短：只取声明的长度
    HttpResponse shortBody = cm::net::parseResponse(
        "HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n");
    CK_EQ(shortBody.status, 204);
    CK(shortBody.body.empty());

    HttpResponse notFound = cm::net::parseResponse(
        "HTTP/1.1 404 Not Found\r\nContent-Length: 1\r\n\r\nx");
    CK(!notFound.is2xx());
    CK_EQ(notFound.status, 404);
}

static void testChunked() {
    const std::string raw =
        "HTTP/1.1 200 OK\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "5\r\nhello\r\n"
        "14\r\n0123456789abcdefghij\r\n"
        "0\r\n\r\n";
    HttpResponse r = cm::net::parseResponse(raw);
    CK(r.ok());
    CK_EQ(r.body, std::string("hello0123456789abcdefghij"));

    // chunk 扩展参数要忽略
    const std::string ext =
        "HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
        "3;name=value\r\nabc\r\n0\r\n\r\n";
    CK_EQ(cm::net::parseResponse(ext).body, std::string("abc"));

    // chunked 优先于 Content-Length（RFC 7230 §3.3.3）
    const std::string both =
        "HTTP/1.1 200 OK\r\nContent-Length: 99\r\nTransfer-Encoding: chunked\r\n\r\n"
        "2\r\nhi\r\n0\r\n\r\n";
    CK_EQ(cm::net::parseResponse(both).body, std::string("hi"));

    // 半截 chunk 不能当成完整响应
    std::string out;
    std::string err;
    CK(!cm::net::decodeChunked("5\r\nhel", 0, out, &err));
    CK(!err.empty());
    out.clear(); err.clear();
    CK(cm::net::decodeChunked("5\r\nhello\r\n0\r\n\r\n", 0, out, &err));
    CK_EQ(out, std::string("hello"));
    err.clear();
    CK(!cm::net::decodeChunked("zz\r\nx\r\n", 0, out, &err));  // 非法长度行
}

static void testTimeoutAndUnreachable() {
    cm::net::HttpOptions opt;
    opt.connectTimeoutMs = 700;
    opt.readTimeoutMs = 700;
    // 保留端口，连接应当被拒 —— 必须返回 error 而不是抛出或挂住
    HttpResponse r = cm::net::HttpClient::get("http://127.0.0.1:1/nothing", {}, opt);
    CK(!r.ok());
    CK(!r.error.empty());
    // 解析不出主机也要有 error
    HttpResponse bad = cm::net::HttpClient::get("http://nonexistent.invalid./x", {}, opt);
    CK(!bad.ok());
}

void run_http_client_tests() {
    testParseUrl();
    testTlsTransport();
    testPlainRequest();
    testRetry();
    testBuildQuery();
    testParseResponse();
    testChunked();
    testTimeoutAndUnreachable();
}
