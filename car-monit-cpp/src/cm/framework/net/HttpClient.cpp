// 出站 HTTP/1.1 客户端实现。见头文件里对差异（无 TLS、不跟随重定向、不重试）的说明。
#include "cm/framework/net/HttpClient.hpp"

#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <sstream>

#include "cm/framework/net/Os.hpp"

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
    if (u.scheme == "https") {
        // COMPATIBILITY §5.1：本实现不带 TLS。腾讯地图 direction 是 https，
        // 其余上游（GeoServer / 路网 / vehicle-monitor / MinIO）都是 http。
        r.error = "未实现 TLS，无法访问 https 主机: " + u.host;
        return r;
    }
    std::string err;
    Fd fd = connectTcp(u.host, u.port, opt.connectTimeoutMs, &err);
    if (!isValid(fd)) {
        r.error = err;
        return r;
    }
    setTimeout(fd, opt.readTimeoutMs);

    std::string target = u.path;
    if (!u.query.empty()) target += "?" + u.query;
    std::ostringstream req;
    req << method << " " << target << " HTTP/1.1\r\n"
        << "Host: " << u.host << ":" << u.port << "\r\n"
        << "User-Agent: car-monit-cpp\r\n"
        << "Accept: */*\r\n"
        << "Connection: close\r\n";
    for (const auto& kv : headers) req << kv.first << ": " << kv.second << "\r\n";
    req << "Content-Length: " << body.size() << "\r\n\r\n" << body;
    const std::string request = req.str();

    if (!writeAll(fd, request.data(), request.size(), &err)) {
        r.error = "发送请求失败: " + err;
        closeTcp(fd);
        return r;
    }

    std::string buf;
    size_t headEnd = std::string::npos;
    char chunkBuf[8192];
    for (;;) {
        const long n = readSome(fd, chunkBuf, sizeof(chunkBuf));
        if (n < 0) {
            r.error = "读取响应失败或超时: " + lastError();
            closeTcp(fd);
            return r;
        }
        if (n == 0) break;  // 服务端关闭连接
        buf.append(chunkBuf, static_cast<size_t>(n));
        if (headEnd == std::string::npos) {
            headEnd = buf.find("\r\n\r\n");
            if (headEnd == std::string::npos) {
                if (buf.size() > 256 * 1024) {
                    r.error = "响应首部过大";
                    closeTcp(fd);
                    return r;
                }
                continue;
            }
        }
        const Frame f = frameOf(buf, headEnd);
        if (bodyComplete(buf, headEnd, f, opt.maxBodyBytes)) {
            if (f.length > opt.maxBodyBytes) {
                r.error = "响应体超过上限 " + std::to_string(opt.maxBodyBytes) + " 字节";
                closeTcp(fd);
                return r;
            }
            break;
        }
        if (static_cast<long long>(buf.size()) > headEnd + 4 + opt.maxBodyBytes) {
            r.error = "响应体超过上限 " + std::to_string(opt.maxBodyBytes) + " 字节";
            closeTcp(fd);
            return r;
        }
    }
    closeTcp(fd);
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
