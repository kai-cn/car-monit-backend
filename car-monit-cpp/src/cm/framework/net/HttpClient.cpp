// 出站 HTTP/1.1 客户端实现。见头文件里对差异（不跟随重定向、不重试）的说明。
#include "cm/framework/net/HttpClient.hpp"

#include <cctype>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <map>
#include <memory>
#include <mutex>
#include <sstream>

#include "cm/framework/net/Os.hpp"

#ifdef CM_HAVE_TLS
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/entropy.h"
#include "mbedtls/error.h"
#include "mbedtls/net_sockets.h"
#include "mbedtls/ssl.h"
#include "mbedtls/x509_crt.h"
#endif

namespace cm::net {
namespace {

std::string lower(std::string s) {
    for (char& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

std::string trim(const std::string& s) {
    size_t b = 0, e = s.size();
    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
    return s.substr(b, e - b);
}

bool hexValue(char c, int& out) {
    if (c >= '0' && c <= '9') { out = c - '0'; return true; }
    if (c >= 'a' && c <= 'f') { out = c - 'a' + 10; return true; }
    if (c >= 'A' && c <= 'F') { out = c - 'A' + 10; return true; }
    return false;
}

struct Frame {
    bool chunked{false};
    long long length{-1};   // -1 = 未知（读到连接关闭为止）
};

Frame frameOf(const std::string& raw, size_t headEnd) {
    Frame f;
    const std::string head = raw.substr(0, headEnd);
    size_t pos = head.find('\n') + 1;  // 跳过状态行
    while (pos != std::string::npos && pos < head.size()) {
        size_t nl = head.find('\n', pos);
        const std::string line = head.substr(pos, nl == std::string::npos ? std::string::npos : nl - pos);
        size_t colon = line.find(':');
        if (colon != std::string::npos) {
            const std::string k = lower(trim(line.substr(0, colon)));
            const std::string v = lower(trim(line.substr(colon + 1)));
            if (k == "transfer-encoding" && v.find("chunked") != std::string::npos) f.chunked = true;
            else if (k == "content-length") f.length = std::atoll(v.c_str());
        }
        if (nl == std::string::npos) break;
        pos = nl + 1;
    }
    // Transfer-Encoding: chunked 优先于 Content-Length（RFC 7230 §3.3.3）
    if (f.chunked) f.length = -1;
    return f;
}

} // namespace

std::string HttpResponse::header(const std::string& lowerName) const {
    for (const auto& kv : headers) {
        if (kv.first == lowerName) return kv.second;
    }
    return std::string();
}

Url parseUrl(const std::string& url) {
    Url u;
    const size_t sep = url.find("://");
    if (sep == std::string::npos) {
        u.error = "非法 URL（缺少协议）: " + url;
        return u;
    }
    u.scheme = lower(url.substr(0, sep));
    if (u.scheme != "http" && u.scheme != "https") {
        u.error = "不支持的协议: " + u.scheme;
        return u;
    }
    std::string rest = url.substr(sep + 3);
    const size_t slash = rest.find('/');
    std::string authority = slash == std::string::npos ? rest : rest.substr(0, slash);
    std::string pathAndQuery = slash == std::string::npos ? std::string() : rest.substr(slash);
    const size_t q = pathAndQuery.find('?');
    if (q != std::string::npos) {
        u.path = pathAndQuery.substr(0, q);
        u.query = pathAndQuery.substr(q + 1);
    } else {
        u.path = pathAndQuery;
    }
    if (u.path.empty()) u.path = "/";
    const size_t colon = authority.rfind(':');
    if (colon != std::string::npos && authority.find(']') == std::string::npos) {
        u.host = authority.substr(0, colon);
        const std::string portText = authority.substr(colon + 1);
        // 端口必须全是数字：否则 atoi("0x") 会静默变成 0 再被兜成 80，把坏 URL 当好的用
        if (portText.empty() ||
            portText.find_first_not_of("0123456789") != std::string::npos) {
            u.error = "非法端口: " + authority;
            return u;
        }
        u.port = std::atoi(portText.c_str());
    } else {
        u.host = authority;
        u.port = u.scheme == "https" ? 443 : 80;
    }
    if (u.host.empty()) {
        u.error = "缺少主机名: " + url;
        return u;
    }
    if (u.port <= 0) u.port = u.scheme == "https" ? 443 : 80;
    u.ok = true;
    return u;
}

std::string urlEncodeQuery(const std::string& s) {
    // 与 Apache httpclient 的 URLEncodedUtils.format 一致：空格编成 '+'
    std::string out;
    char buf[4];
    for (unsigned char c : s) {
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
            c == '-' || c == '_' || c == '.' || c == '~') {
            out.push_back(static_cast<char>(c));
        } else if (c == ' ') {
            out.push_back('+');
        } else {
            std::snprintf(buf, sizeof(buf), "%%%02X", c);
            out += buf;
        }
    }
    return out;
}

std::string buildQuery(const std::vector<std::pair<std::string, std::string>>& params) {
    std::string out;
    for (const auto& kv : params) {
        if (!out.empty()) out += "&";
        out += urlEncodeQuery(kv.first) + "=" + urlEncodeQuery(kv.second);
    }
    return out;
}

bool decodeChunked(const std::string& src, size_t from, std::string& out, std::string* err) {
    out.clear();
    size_t pos = from;
    for (;;) {
        const size_t nl = src.find("\r\n", pos);
        if (nl == std::string::npos) {
            if (err) *err = "chunk 长度行不完整";
            return false;
        }
        // 扩展行（;ext=val）忽略；长度按 16 进制
        std::string sizeLine = src.substr(pos, nl - pos);
        const size_t semi = sizeLine.find(';');
        if (semi != std::string::npos) sizeLine = sizeLine.substr(0, semi);
        long long size = 0;
        int d = 0;
        for (char c : sizeLine) {
            if (!hexValue(c, d)) {
                if (err) *err = "chunk 长度非法: " + sizeLine;
                return false;
            }
            size = size * 16 + d;
        }
        pos = nl + 2;
        if (size == 0) {  // 终止块：后面是可选 trailer 与空行
            out.shrink_to_fit();
            return true;
        }
        if (pos + static_cast<size_t>(size) + 2 > src.size()) {
            if (err) *err = "chunk 数据未收全";
            return false;
        }
        out.append(src, pos, static_cast<size_t>(size));
        pos += static_cast<size_t>(size) + 2;  // 跳过块尾的 \r\n
    }
}

HttpResponse parseResponse(const std::string& raw) {
    HttpResponse r;
    const size_t headEnd = raw.find("\r\n\r\n");
    if (headEnd == std::string::npos) {
        r.error = "响应首部不完整";
        return r;
    }
    size_t pos = 0;
    const size_t firstNl = raw.find("\r\n");
    const std::string statusLine = raw.substr(0, firstNl == std::string::npos ? headEnd : firstNl);
    {
        std::istringstream ss(statusLine);
        std::string version, reason;
        int code = 0;
        if (!(ss >> version >> code)) {
            r.error = "状态行非法: " + statusLine;
            return r;
        }
        r.status = code;
        std::getline(ss, reason);
    }
    pos = (firstNl == std::string::npos ? headEnd : firstNl + 2);
    while (pos < headEnd) {
        size_t nl = raw.find("\r\n", pos);
        if (nl == std::string::npos || nl > headEnd) nl = headEnd;
        const std::string line = raw.substr(pos, nl - pos);
        const size_t colon = line.find(':');
        if (colon != std::string::npos) {
            r.headers.emplace_back(lower(trim(line.substr(0, colon))), trim(line.substr(colon + 1)));
        }
        pos = nl + 2;
    }
    const Frame f = frameOf(raw, headEnd);
    const std::string bodyRaw = raw.substr(headEnd + 4);
    if (f.chunked) {
        std::string err;
        if (!decodeChunked(bodyRaw, 0, r.body, &err)) {
            r.error = "chunked 解码失败: " + err;
            return r;
        }
    } else if (f.length >= 0) {
        r.body = bodyRaw.substr(0, static_cast<size_t>(f.length));
    } else {
        r.body = bodyRaw;  // 无成帧信息：以连接关闭为界
    }
    return r;
}

namespace {

bool bodyComplete(const std::string& buf, size_t headEnd, const Frame& f, long long max) {
    const size_t start = headEnd + 4;
    if (f.length >= 0) {
        if (f.length > max) return true;  // 超限：交给外层判错，不必再收
        return buf.size() - start >= static_cast<size_t>(f.length);
    }
    if (f.chunked) {
        std::string out, err;
        return decodeChunked(buf, start, out, &err);
    }
    return false;  // 无 Content-Length：只能读到来流关闭
}

} // namespace

// ---------------------------------------------------------------------------
// 传输层：明文与 TLS 共用请求构造/响应解析，只有字节收发不同
// ---------------------------------------------------------------------------
namespace {

class Transport {
public:
    virtual ~Transport() = default;
    virtual bool writeAll(const char* data, size_t len, std::string& err) = 0;
    /** >0 读到的字节数；0 对端关闭；-1 出错/超时（原因写入 err） */
    virtual long readSome(char* buf, size_t len, std::string& err) = 0;
};

class PlainTransport : public Transport {
public:
    explicit PlainTransport(Fd fd) : fd_(fd) {}
    ~PlainTransport() override { cm::net::closeTcp(fd_); }
    bool writeAll(const char* data, size_t len, std::string& err) override {
        return cm::net::writeAll(fd_, data, len, &err);
    }
    long readSome(char* buf, size_t len, std::string& err) override {
        const long n = cm::net::readSome(fd_, buf, len);
        if (n < 0) {
            err = cm::net::lastError();
            return -1;
        }
        return n;
    }

private:
    Fd fd_;
};

#ifdef CM_HAVE_TLS

/** 解析后的 CA 证书链。按路径缓存，进程内只解析一次（200KB / 118 个根证书）。 */
struct CaStore {
    mbedtls_x509_crt crt;
    CaStore() { mbedtls_x509_crt_init(&crt); }
    ~CaStore() { mbedtls_x509_crt_free(&crt); }
    CaStore(const CaStore&) = delete;
    CaStore& operator=(const CaStore&) = delete;
};

std::mutex g_ca_mu;
std::map<std::string, std::shared_ptr<CaStore>> g_ca_cache;

std::mutex g_default_ca_mu;
std::string g_default_ca;

bool fileReadable(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    return f.good();
}

/** 默认 CA 查找顺序：显式设置 → CM_CA_BUNDLE → 仓库内 cacert.pem → 系统 CA */
std::string resolveDefaultCaPath() {
    {
        std::lock_guard<std::mutex> lk(g_default_ca_mu);
        if (!g_default_ca.empty()) return g_default_ca;
    }
    if (const char* env = std::getenv("CM_CA_BUNDLE"); env != nullptr && *env != '\0') return env;
    for (const char* p : {"third_party/cacert.pem", "cacert.pem", "../third_party/cacert.pem"}) {
        if (fileReadable(p)) return p;
    }
#ifndef _WIN32
    for (const char* p : {"/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt",
                          "/etc/ssl/cert.pem"}) {
        if (fileReadable(p)) return p;
    }
#endif
    return std::string();
}

std::shared_ptr<CaStore> loadCaStore(const std::string& path, std::string& err) {
    if (path.empty()) {
        err = "未找到 CA 证书包（设置 CM_CA_BUNDLE 或 cm.http.ca-bundle）";
        return nullptr;
    }
    std::lock_guard<std::mutex> lk(g_ca_mu);
    if (auto it = g_ca_cache.find(path); it != g_ca_cache.end()) return it->second;
    auto store = std::make_shared<CaStore>();
    const int rc = mbedtls_x509_crt_parse_file(&store->crt, path.c_str());
    if (rc != 0) {
        char msg[256] = {0};
        mbedtls_strerror(rc, msg, sizeof(msg));
        err = "加载 CA 失败 " + path + ": " + msg;
        return nullptr;
    }
    g_ca_cache[path] = store;
    return store;
}

int tlsSendCb(void* ctx, const unsigned char* buf, size_t len) {
    auto* fd = static_cast<Fd*>(ctx);
    const long n = cm::net::writeSome(*fd, buf, len);
    return n <= 0 ? MBEDTLS_ERR_NET_SEND_FAILED : static_cast<int>(n);
}

int tlsRecvCb(void* ctx, unsigned char* buf, size_t len) {
    auto* fd = static_cast<Fd*>(ctx);
    // 不用 cm::net::readSome：它把"对端关闭(0)"与"超时(0)"混在一起，
    // 而 TLS 需要把 EOF 交给 mbedtls 走 close_notify 分支，所以这里直接 recv 区分。
    const int n = ::recv(cm::net::asSocket(*fd), reinterpret_cast<char*>(buf), static_cast<int>(len), 0);
    if (n > 0) return n;
    if (n == 0) return 0;
#ifdef _WIN32
    const int e = WSAGetLastError();
    if (e == WSAEWOULDBLOCK || e == WSAETIMEDOUT) return MBEDTLS_ERR_SSL_TIMEOUT;
#else
    if (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR) return MBEDTLS_ERR_SSL_TIMEOUT;
#endif
    return MBEDTLS_ERR_NET_RECV_FAILED;
}

std::string tlsErrorText(int rc) {
    char msg[256] = {0};
    mbedtls_strerror(rc, msg, sizeof(msg));
    return msg;
}

class TlsTransport : public Transport {
public:
    TlsTransport() {
        mbedtls_ssl_init(&ssl_);
        mbedtls_ssl_config_init(&conf_);
        mbedtls_ctr_drbg_init(&drbg_);
        mbedtls_entropy_init(&entropy_);
    }
    ~TlsTransport() override {
        // 不发 close_notify：明文路径也是读完直接 close，且对端已经关闭时
        // ssl_close_notify 会卡在 SO_SNDTIMEO 上（最长 readTimeoutMs），得不偿失
        mbedtls_ssl_free(&ssl_);
        mbedtls_ssl_config_free(&conf_);
        mbedtls_ctr_drbg_free(&drbg_);
        mbedtls_entropy_free(&entropy_);
        cm::net::closeTcp(fd_);
    }
    TlsTransport(const TlsTransport&) = delete;
    TlsTransport& operator=(const TlsTransport&) = delete;

    bool connect(const Url& u, const HttpOptions& opt, std::string& err) {
        std::string caErr;
        const auto ca = loadCaStore(opt.caBundle.empty() ? resolveDefaultCaPath() : opt.caBundle, caErr);
        if (!ca) {
            err = caErr;
            return false;
        }
        fd_ = cm::net::connectTcp(u.host, u.port, opt.connectTimeoutMs, &err);
        if (!cm::net::isValid(fd_)) return false;
        cm::net::setTimeout(fd_, opt.readTimeoutMs);

        int rc = mbedtls_ctr_drbg_seed(&drbg_, mbedtls_entropy_func, &entropy_, nullptr, 0);
        if (rc != 0) {
            err = "TLS 随机源初始化失败: " + tlsErrorText(rc);
            return false;
        }
        rc = mbedtls_ssl_config_defaults(&conf_, MBEDTLS_SSL_IS_CLIENT, MBEDTLS_SSL_TRANSPORT_STREAM,
                                         MBEDTLS_SSL_PRESET_DEFAULT);
        if (rc != 0) {
            err = "TLS 配置初始化失败: " + tlsErrorText(rc);
            return false;
        }
        // 强制校验证书链与主机名。不做"校验失败仍继续"的降级，避免悄悄失去中间人防护。
        mbedtls_ssl_conf_authmode(&conf_, MBEDTLS_SSL_VERIFY_REQUIRED);
        mbedtls_ssl_conf_ca_chain(&conf_, &ca->crt, nullptr);
        mbedtls_ssl_conf_rng(&conf_, mbedtls_ctr_drbg_random, &drbg_);

        rc = mbedtls_ssl_setup(&ssl_, &conf_);
        if (rc != 0) {
            err = "TLS 上下文初始化失败: " + tlsErrorText(rc);
            return false;
        }
        rc = mbedtls_ssl_set_hostname(&ssl_, u.host.c_str());
        if (rc != 0) {
            err = "TLS 设置主机名失败: " + tlsErrorText(rc);
            return false;
        }
        mbedtls_ssl_set_bio(&ssl_, &fd_, tlsSendCb, tlsRecvCb, nullptr);

        for (;;) {
            rc = mbedtls_ssl_handshake(&ssl_);
            if (rc == 0) break;
            if (rc == MBEDTLS_ERR_SSL_WANT_READ || rc == MBEDTLS_ERR_SSL_WANT_WRITE) continue;
            err = "TLS 握手失败 " + u.host + ": " + tlsErrorText(rc);
            // 证书问题单独给出可读原因，否则只会看到笼统的 X509 错误
            const uint32_t flags = mbedtls_ssl_get_verify_result(&ssl_);
            if (flags != 0) {
                char info[512] = {0};
                mbedtls_x509_crt_verify_info(info, sizeof(info), "", flags);
                err = "TLS 证书校验失败 " + u.host + ": " + info;
            }
            return false;
        }
        const uint32_t flags = mbedtls_ssl_get_verify_result(&ssl_);
        if (flags != 0) {
            char info[512] = {0};
            mbedtls_x509_crt_verify_info(info, sizeof(info), "", flags);
            err = "TLS 证书校验失败 " + u.host + ": " + info;
            return false;
        }
        return true;
    }

    bool writeAll(const char* data, size_t len, std::string& err) override {
        size_t off = 0;
        while (off < len) {
            const int rc = mbedtls_ssl_write(&ssl_,
                                             reinterpret_cast<const unsigned char*>(data + off), len - off);
            if (rc > 0) {
                off += static_cast<size_t>(rc);
                continue;
            }
            if (rc == MBEDTLS_ERR_SSL_WANT_WRITE || rc == MBEDTLS_ERR_SSL_WANT_READ) continue;
            err = tlsErrorText(rc);
            return false;
        }
        return true;
    }

    long readSome(char* buf, size_t len, std::string& err) override {
        for (;;) {
            const int rc = mbedtls_ssl_read(&ssl_, reinterpret_cast<unsigned char*>(buf), len);
            if (rc > 0) return rc;
            // close_notify 与"未发 close_notify 就断开"都按对端关闭处理：
            // 响应字节可能已经完整，交给上层 parseResponse 判断
            if (rc == 0 || rc == MBEDTLS_ERR_SSL_PEER_CLOSE_NOTIFY || rc == MBEDTLS_ERR_SSL_CONN_EOF) {
                return 0;
            }
            if (rc == MBEDTLS_ERR_SSL_WANT_READ || rc == MBEDTLS_ERR_SSL_WANT_WRITE) continue;
            err = tlsErrorText(rc);
            return -1;
        }
    }

private:
    Fd fd_{kInvalid};
    mbedtls_ssl_context ssl_;
    mbedtls_ssl_config conf_;
    mbedtls_ctr_drbg_context drbg_;
    mbedtls_entropy_context entropy_;
};

#endif // CM_HAVE_TLS

} // namespace

void HttpClient::setDefaultCaBundle(const std::string& path) {
#ifdef CM_HAVE_TLS
    std::lock_guard<std::mutex> lk(g_default_ca_mu);
    g_default_ca = path;
#else
    (void)path;
#endif
}

std::string HttpClient::defaultCaBundle() {
#ifdef CM_HAVE_TLS
    return resolveDefaultCaPath();
#else
    return std::string();
#endif
}

HttpResponse HttpClient::send(const std::string& method, const std::string& url,
                              const std::string& body,
                              const std::vector<std::pair<std::string, std::string>>& headers,
                              const HttpOptions& opt) {
    HttpResponse r;
    Url u = parseUrl(url);
    if (!u.ok) {
        r.error = u.error;
        return r;
    }
    std::string err;
    std::unique_ptr<Transport> transport;
    if (u.scheme == "https") {
#ifdef CM_HAVE_TLS
        auto tls = std::make_unique<TlsTransport>();
        if (!tls->connect(u, opt, err)) {
            r.error = err;
            return r;
        }
        transport = std::move(tls);
#else
        r.error = "本次构建未启用 TLS，无法访问 https 主机: " + u.host;
        return r;
#endif
    } else {
        Fd fd = connectTcp(u.host, u.port, opt.connectTimeoutMs, &err);
        if (!isValid(fd)) {
            r.error = err;
            return r;
        }
        setTimeout(fd, opt.readTimeoutMs);
        transport = std::make_unique<PlainTransport>(fd);
    }

    std::string target = u.path;
    if (!u.query.empty()) target += "?" + u.query;
    // 默认端口不进 Host（Java/Apache httpclient 的行为，部分网关按 Host 精确匹配）
    const bool defaultPort = (u.scheme == "https" && u.port == 443) ||
                             (u.scheme == "http" && u.port == 80);
    std::ostringstream req;
    req << method << " " << target << " HTTP/1.1\r\n"
        << "Host: " << u.host << (defaultPort ? "" : ":" + std::to_string(u.port)) << "\r\n"
        << "User-Agent: car-monit-cpp\r\n"
        << "Accept: */*\r\n"
        << "Connection: close\r\n";
    for (const auto& kv : headers) req << kv.first << ": " << kv.second << "\r\n";
    req << "Content-Length: " << body.size() << "\r\n\r\n" << body;
    const std::string request = req.str();

    if (!transport->writeAll(request.data(), request.size(), err)) {
        r.error = "发送请求失败: " + err;
        return r;
    }

    std::string buf;
    size_t headEnd = std::string::npos;
    char chunkBuf[8192];
    for (;;) {
        const long n = transport->readSome(chunkBuf, sizeof(chunkBuf), err);
        if (n < 0) {
            r.error = "读取响应失败或超时: " + err;
            return r;
        }
        if (n == 0) break;  // 服务端关闭连接
        buf.append(chunkBuf, static_cast<size_t>(n));
        if (headEnd == std::string::npos) {
            headEnd = buf.find("\r\n\r\n");
            if (headEnd == std::string::npos) {
                if (buf.size() > 256 * 1024) {
                    r.error = "响应首部过大";
                    return r;
                }
                continue;
            }
        }
        const Frame f = frameOf(buf, headEnd);
        if (bodyComplete(buf, headEnd, f, opt.maxBodyBytes)) {
            if (f.length > opt.maxBodyBytes) {
                r.error = "响应体超过上限 " + std::to_string(opt.maxBodyBytes) + " 字节";
                return r;
            }
            break;
        }
        if (static_cast<long long>(buf.size()) > headEnd + 4 + opt.maxBodyBytes) {
            r.error = "响应体超过上限 " + std::to_string(opt.maxBodyBytes) + " 字节";
            return r;
        }
    }
    r = parseResponse(buf);
    if (r.error.empty() && static_cast<long long>(r.body.size()) > opt.maxBodyBytes) {
        HttpResponse over;
        over.error = "响应体超过上限 " + std::to_string(opt.maxBodyBytes) + " 字节";
        return over;
    }
    return r;
}

HttpResponse HttpClient::get(const std::string& url,
                            const std::vector<std::pair<std::string, std::string>>& headers,
                            const HttpOptions& opt) {
    return send("GET", url, std::string(), headers, opt);
}

HttpResponse HttpClient::getWithQuery(
    const std::string& url, const std::vector<std::pair<std::string, std::string>>& params,
    const std::vector<std::pair<std::string, std::string>>& headers, const HttpOptions& opt) {
    if (params.empty()) return get(url, headers, opt);
    std::string full = url;
    full += (url.find('?') == std::string::npos ? "?" : "&");
    full += buildQuery(params);
    return get(full, headers, opt);
}

HttpResponse HttpClient::post(const std::string& url, const std::string& body,
                              const std::string& contentType,
                              const std::vector<std::pair<std::string, std::string>>& headers,
                              const HttpOptions& opt) {
    std::vector<std::pair<std::string, std::string>> h = headers;
    h.emplace_back("Content-Type", contentType);
    return send("POST", url, body, h, opt);
}

HttpResponse HttpClient::postForm(
    const std::string& url, const std::vector<std::pair<std::string, std::string>>& form,
    const std::vector<std::pair<std::string, std::string>>& headers, const HttpOptions& opt) {
    return post(url, buildQuery(form), "application/x-www-form-urlencoded;charset=UTF-8", headers, opt);
}

} // namespace cm::net
