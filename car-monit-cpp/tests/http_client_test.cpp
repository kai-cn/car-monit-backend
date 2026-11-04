// 出站 HTTP 客户端的单测：URL 解析、query 编码、状态/首部解析、chunked 成帧、上限与 TLS 拒绝。
#include <string>
#include <vector>

#include "cm/framework/net/HttpClient.hpp"

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

static void testTlsRejected() {
    // 未实现 TLS：必须是明确的传输层错误，而不是崩或当作 http 发出去
    HttpResponse r = cm::net::HttpClient::get("https://apis.map.qq.com/ws/direction/v1/driving");
    CK(!r.ok());
    CK(r.error.find("TLS") != std::string::npos);
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
    testTlsRejected();
    testBuildQuery();
    testParseResponse();
    testChunked();
    testTimeoutAndUnreachable();
}
