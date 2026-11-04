// S3/MinIO SigV4 客户端实现，见 include/cm/framework/net/S3Client.hpp 顶部说明。
#include "cm/framework/net/S3Client.hpp"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <ctime>
#include <map>
#include <sstream>

#include "cm/common/utils/crypto/Digest.hpp"

namespace cm::net::s3 {
namespace {

bool isUnreserved(unsigned char c) {
    return std::isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~';
}

std::string encode(const std::string& raw, bool keepSlash) {
    std::string out;
    for (unsigned char c : raw) {
        if (isUnreserved(c) || (keepSlash && c == '/')) {
            out.push_back(static_cast<char>(c));
        } else {
            char buf[4];
            std::snprintf(buf, sizeof buf, "%%%02X", c);
            out += buf;
        }
    }
    return out;
}

/** SigV4 要求首部值去掉首尾空白、相邻空白压成一个空格 */
std::string trimAll(const std::string& v) {
    size_t a = v.find_first_not_of(" \t");
    if (a == std::string::npos) return "";
    size_t b = v.find_last_not_of(" \t");
    std::string out;
    bool space = false;
    for (size_t i = a; i <= b; ++i) {
        const char c = v[i];
        const bool ws = (c == ' ' || c == '\t');
        if (ws) {
            space = true;
            continue;
        }
        if (space) {
            out.push_back(' ');
            space = false;
        }
        out.push_back(c);
    }
    return out;
}

std::string lower(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

} // namespace

std::string uriEncodePath(const std::string& raw) { return encode(raw, true); }
std::string uriEncodeQuery(const std::string& raw) { return encode(raw, false); }

std::pair<std::string, std::string> amzTimestamp(long long epochSeconds) {
    const std::time_t t = static_cast<std::time_t>(epochSeconds);
    std::tm gm{};
#if defined(_WIN32)
    gmtime_s(&gm, &t);
#else
    gmtime_r(&t, &gm);
#endif
    char a[24], b[16];
    std::strftime(a, sizeof a, "%Y%m%dT%H%M%SZ", &gm);
    std::strftime(b, sizeof b, "%Y%m%d", &gm);
    return {a, b};
}

std::string canonicalRequestOf(const SignInput& in) {
    // 首部按小写名排序，重复同名首部合并成逗号分隔（AWS 规范）
    std::map<std::string, std::string> merged;
    for (const auto& [name, value] : in.headers) {
        const std::string k = lower(name);
        merged[k] = merged.count(k) ? merged[k] + "," + trimAll(value) : trimAll(value);
    }
    std::string headersBlock;
    std::string signedHeaders;
    for (const auto& [k, v] : merged) {
        headersBlock += k + ":" + v + "\n";
        if (!signedHeaders.empty()) signedHeaders += ";";
        signedHeaders += k;
    }
    return in.method + "\n" + in.canonicalUri + "\n" + in.canonicalQuery + "\n" + headersBlock +
           "\n" + signedHeaders + "\n" + in.payloadHash;
}

std::string stringToSignOf(const SignInput& in, const std::string& canonicalRequest) {
    const std::string scope = in.dateStamp + "/" + in.region + "/s3/aws4_request";
    return "AWS4-HMAC-SHA256\n" + in.amzDate + "\n" + scope + "\n" +
           cm::crypto::hex(cm::crypto::sha256(canonicalRequest));
}

std::string signingKey(const std::string& secret, const std::string& dateStamp,
                       const std::string& region) {
    // 链式 HMAC 用的是原始字节，不是十六进制：中间量编码一次都会让签名对不上
    const std::string kDate = cm::crypto::hmacSha256("AWS4" + secret, dateStamp);
    const std::string kRegion = cm::crypto::hmacSha256(kDate, region);
    const std::string kService = cm::crypto::hmacSha256(kRegion, "s3");
    return cm::crypto::hmacSha256(kService, "aws4_request");
}

std::string authorization(const SignInput& in) {
    const std::string cr = canonicalRequestOf(in);
    const std::string sts = stringToSignOf(in, cr);
    const std::string kSigning = signingKey(in.secretKey, in.dateStamp, in.region);
    const std::string signature = cm::crypto::hex(cm::crypto::hmac("sha256", kSigning, sts));
    std::map<std::string, std::string> names;
    for (const auto& [name, value] : in.headers) names[lower(name)] = value;
    std::string signedHeaders;
    for (const auto& [k, _v] : names) {
        if (!signedHeaders.empty()) signedHeaders += ";";
        signedHeaders += k;
    }
    return "AWS4-HMAC-SHA256 Credential=" + in.accessKey + "/" + in.dateStamp + "/" + in.region +
           "/s3/aws4_request, SignedHeaders=" + signedHeaders + ", Signature=" + signature;
}

namespace {

std::string hostOf(const std::string& endpoint, const std::string& host, int port) {
    // AWS SDK 的 Host 首部：http 默认端口 80 不写出来
    if (endpoint.find("https://") == 0) return host;
    return port == 80 ? host : (host + ":" + std::to_string(port));
}

struct Prepared {
    std::string url;
    std::vector<std::pair<std::string, std::string>> headers;
};

Prepared prepare(const Config& cfg, const std::string& method, const std::string& bucket,
                 const std::string& key, const std::string& body, const std::string& contentType,
                 long long timeoutMs) {
    Url u = parseUrl(cfg.endpoint);
    const std::string scheme = u.scheme.empty() ? "http" : u.scheme;
    const int port = u.port ? u.port : (scheme == "https" ? 443 : 80);
    std::string base = u.path;   // endpoint 里可能带前缀路径
    while (!base.empty() && base.back() == '/') base.pop_back();
    const std::string path = base + "/" + uriEncodePath(bucket) + "/" + uriEncodePath(key);
    Prepared p;
    p.url = scheme + "://" + u.host + (port == 80 ? "" : ":" + std::to_string(port)) + path;
    (void)method;

    const auto [amzDate, dateStamp] = amzTimestamp(static_cast<long long>(std::time(nullptr)));
    const std::string payloadHash = cm::crypto::hex(cm::crypto::sha256(body));
    const std::string host = hostOf(cfg.endpoint, u.host, port);

    SignInput si;
    si.method = (method == "PUT" ? "PUT" : (method == "DELETE" ? "DELETE" : "GET"));
    si.canonicalUri = path;
    si.canonicalQuery = "";
    si.payloadHash = payloadHash;
    si.amzDate = amzDate;
    si.dateStamp = dateStamp;
    si.region = cfg.region.empty() ? kDefaultRegion : cfg.region;
    si.accessKey = cfg.accessKey;
    si.secretKey = cfg.secretKey;
    si.headers = {{"host", host},
                  {"x-amz-content-sha256", payloadHash},
                  {"x-amz-date", amzDate},
                  {"content-length", std::to_string(body.size())}};
    if (!contentType.empty()) si.headers.emplace_back("content-type", contentType);
    const std::string auth = authorization(si);

    p.headers = {{"Host", host},
                 {"x-amz-content-sha256", payloadHash},
                 {"x-amz-date", amzDate},
                 {"Content-Length", std::to_string(body.size())},
                 {"Authorization", auth},
                 {"Connection", "close"}};
    if (!contentType.empty()) p.headers.emplace_back("Content-Type", contentType);
    (void)timeoutMs;
    return p;
}

Result call(const Config& cfg, const std::string& method, const std::string& bucket,
            const std::string& key, const std::string& body, const std::string& contentType,
            long long timeoutMs) {
    Result r;
    if (cfg.endpoint.empty()) {
        r.error = "oss.endpoint 未配置";
        return r;
    }
    Url probe = parseUrl(cfg.endpoint);
    if (!probe.ok) {
        r.error = "A problem was encountered while attempting to connect to " + cfg.endpoint +
                  " (service: Amazon S3): " + probe.error;
        return r;
    }
    if (probe.scheme == "https") {
        // 没有 TLS：与 Java 的 https 直连能力不同，如实报传输层失败
        r.error = "A problem was encountered while attempting to connect to " + cfg.endpoint +
                  " (service: Amazon S3): 未实现 TLS，无法访问 https 主机: " + probe.host;
        return r;
    }
    Prepared p = prepare(cfg, method, bucket, key, body, contentType, timeoutMs);
    HttpOptions opt;
    opt.connectTimeoutMs = static_cast<int>(timeoutMs > 0 ? std::min<long long>(timeoutMs, 60000)
                                                          : 10000);
    opt.readTimeoutMs = static_cast<int>(timeoutMs > 0 ? timeoutMs : 60000);
    opt.maxBodyBytes = 64LL * 1024 * 1024;   // 对齐 spring.servlet.multipart.max-file-size 40MB
    HttpResponse resp = HttpClient::send(method, p.url, body, p.headers, opt);
    r.status = resp.status;
    if (!resp.error.empty()) {
        r.error = "A problem was encountered while attempting to connect to " + cfg.endpoint +
                  " (service: Amazon S3): " + resp.error;
        return r;
    }
    r.ok = resp.is2xx();
    r.body = resp.body;
    r.contentType = resp.header("content-type");
    if (!r.ok) {
        // SDK 把 4xx/5xx 转成 AmazonServiceException，消息里带状态码与 <Message>
        std::string msg;
        const auto p1 = resp.body.find("<Message>");
        const auto p2 = resp.body.find("</Message>");
        if (p1 != std::string::npos && p2 != std::string::npos && p2 > p1)
            msg = resp.body.substr(p1 + 9, p2 - p1 - 9);
        r.error = "Amazon Service error. Http Status Code: " + std::to_string(resp.status) +
                  ", Error Code: S3, Message: " + (msg.empty() ? resp.body.substr(0, 200) : msg) +
                  ".";
    }
    return r;
}

} // namespace

Result putObject(const Config& cfg, const std::string& bucket, const std::string& key,
                 const std::string& body, long long timeoutMs) {
    return call(cfg, "PUT", bucket, key, body, "application/octet-stream", timeoutMs);
}

Result getObject(const Config& cfg, const std::string& bucket, const std::string& key,
                 long long timeoutMs) {
    return call(cfg, "GET", bucket, key, std::string(), std::string(), timeoutMs);
}

Result deleteObject(const Config& cfg, const std::string& bucket, const std::string& key,
                   long long timeoutMs) {
    return call(cfg, "DELETE", bucket, key, std::string(), std::string(), timeoutMs);
}

} // namespace cm::net::s3
