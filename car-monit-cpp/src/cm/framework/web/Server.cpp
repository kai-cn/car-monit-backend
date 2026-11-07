#include "cm/framework/web/Server.hpp"

#include <cerrno>

#include "cm/framework/net/Os.hpp"
#include <chrono>
#include <condition_variable>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <queue>
#include <sstream>

#include "cm/framework/aspect/OperLogAspect.hpp"
#include "cm/common/compat/Path.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/security/TokenService.hpp"
#include "cm/framework/web/Errors.hpp"
#include "cm/framework/web/ExceptionMapper.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/service/LoginServices.hpp"

namespace cm::web {
namespace {

std::string lower(std::string s) {
    for (char& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

/** 对应 Java 的 e.getMessage()：可能真的是 null（如 NullPointerException），
 *  用 optional 区分 "没有消息" 与 "消息是空串"，LogAspect 的 error_msg 要写 NULL。 */
std::optional<std::string> exceptionMessage(std::exception_ptr ep) {
    try {
        std::rethrow_exception(ep);
    } catch (const cm::exception::NullPointerException&) {
        return std::nullopt;
    } catch (const std::exception& e) {
        return std::string(e.what());
    } catch (...) {
        return std::nullopt;
    }
}

std::string trimCr(std::string s) {
    while (!s.empty() && (s.back() == '\r' || s.back() == '\n')) s.pop_back();
    return s;
}

/** 从缓冲区读出一行（含 \r\n），返回是否成功 */
bool readLine(cm::net::Fd fd, std::string& buf, std::string& line) {
    for (;;) {
        size_t p = buf.find("\r\n");
        if (p != std::string::npos) {
            line = buf.substr(0, p);
            buf.erase(0, p + 2);
            return true;
        }
        char tmp[4096];
        const long n = cm::net::readSome(fd, tmp, sizeof(tmp));
        if (n <= 0) return false;
        buf.append(tmp, static_cast<size_t>(n));
        if (buf.size() > 64 * 1024) return false; // 头部过大
    }
}

bool readExact(cm::net::Fd fd, std::string& buf, size_t n, std::string& out) {
    while (buf.size() < n) {
        char tmp[65536];
        size_t want = std::min(sizeof(tmp), n - buf.size());
        const long r = cm::net::readSome(fd, tmp, want);
        if (r <= 0) return false;
        buf.append(tmp, static_cast<size_t>(r));
    }
    out = buf.substr(0, n);
    buf.erase(0, n);
    return true;
}

bool isCorsPreflight(const cm::http::HttpRequest& req) {
    return req.method == "OPTIONS" && req.getHeader("Origin") != "" ;
}

void applyCors(cm::http::HttpRequest& req, cm::http::ApiResponse& resp) {
    std::string origin = req.getHeader("Origin");
    if (origin.empty()) return;
    resp.headers["Access-Control-Allow-Origin"] = origin;
    resp.headers["Access-Control-Allow-Credentials"] = "true";
    std::string reqHeaders = req.getHeader("Access-Control-Request-Headers");
    if (!reqHeaders.empty()) resp.headers["Access-Control-Allow-Headers"] = reqHeaders;
    std::string reqMethods = req.getHeader("Access-Control-Request-Method");
    if (!reqMethods.empty()) resp.headers["Access-Control-Allow-Methods"] = reqMethods;
    resp.headers["Access-Control-Max-Age"] = "1800";
    resp.headers["Vary"] = "Origin, Access-Control-Request-Method, Access-Control-Request-Headers";
}

/** 对应 LogoutSuccessHandlerImpl */
cm::http::ApiResponse handleLogout(cm::http::HttpRequest& req) {
    auto loginUser = cm::security::TokenService::instance().getLoginUser(req);
    if (loginUser) {
        cm::security::TokenService::instance().delLoginUser(loginUser->token.value_or(""));
        cm::security::SysLoginService::recordLogininfor(
            loginUser->user.userName.value_or(""), cm::constant::Constants::LOGOUT, "退出成功", req);
    }
    cm::core::domain::AjaxResult a = cm::core::domain::AjaxResult::success("退出成功");
    return json(a);
}

std::string contentTypeFor(const std::string& path) {
    auto ends = [&](const char* ext) {
        size_t n = std::strlen(ext);
        return path.size() >= n && path.compare(path.size() - n, n, ext) == 0;
    };
    if (ends(".html")) return "text/html;charset=UTF-8";
    if (ends(".css")) return "text/css;charset=UTF-8";
    if (ends(".js")) return "application/javascript;charset=UTF-8";
    if (ends(".json")) return "application/json;charset=UTF-8";
    if (ends(".png")) return "image/png";
    if (ends(".jpg") || ends(".jpeg")) return "image/jpeg";
    if (ends(".gif")) return "image/gif";
    if (ends(".svg")) return "image/svg+xml";
    if (ends(".ico")) return "image/x-icon";
    if (ends(".txt")) return "text/plain;charset=UTF-8";
    return "application/octet-stream";
}

bool safePath(const std::string& rel) {
    return rel.find("..") == std::string::npos;
}

/** 静态资源：classpath:/static（这里映射到 config/static）与 /profile/**（uploadPath） */
bool serveStatic(const std::string& method, const std::string& path, cm::http::ApiResponse& out) {
    if (method != "GET") return false;
    auto& cfg = cm::config::AppConfig::instance();
    std::filesystem::path file;
    if (path.rfind("/profile/", 0) == 0) {
        std::string rel = path.substr(std::strlen("/profile/"));
        if (!safePath(rel)) return false;
        file = cm::compat::fsPath(cfg.profile) / cm::compat::fsPath(rel);
        // RuoYi 的 uploadPath 已经是 /profile 的根
        if (!std::filesystem::exists(file)) {
            file = cm::compat::fsPath(cfg.profile) / "profile" / cm::compat::fsPath(rel);
        }
    } else {
        std::string rel = path == "/" ? "index.html" : path.substr(1);
        if (!safePath(rel)) return false;
        file = cm::compat::fsPath("config/static") / cm::compat::fsPath(rel);
    }
    if (!std::filesystem::is_regular_file(file)) return false;
    std::ifstream in(file, std::ios::binary);
    if (!in) return false;
    std::ostringstream ss;
    ss << in.rdbuf();
    out.status = 200;
    out.content_type = contentTypeFor(path);
    out.body = ss.str();
    return true;
}

} // namespace

Server::Server(std::string host, int port, int workers, int backlog)
    : host_(std::move(host)), port_(port), workers_(workers <= 0 ? 32 : workers), backlog_(backlog) {}

Server::~Server() { stop(); }

bool Server::start() {
    std::string err;
    listen_fd_ = cm::net::listenTcp(host_, port_, backlog_, &err);
    if (!cm::net::isValid(listen_fd_)) {
        LOG_ERROR("Server", err);
        return false;
    }
    running_.store(true);
    threads_.emplace_back([this] { acceptLoop(); });
    for (int i = 0; i < workers_; ++i) {
        threads_.emplace_back([this] { workerLoop(); });
    }
    LOG_INFO("Server", "HTTP 服务已启动: http://" + host_ + ":" + std::to_string(port_) +
                           " （工作线程 " + std::to_string(workers_) + "）");
    return true;
}

void Server::stop() {
    if (!running_.exchange(false)) return;
    if (cm::net::isValid(listen_fd_)) {
        // 先 shutdown 唤醒阻塞在 accept() 上的线程，再关闭句柄
        cm::net::shutdownTcp(listen_fd_);
        cm::net::closeTcp(listen_fd_);
        listen_fd_ = cm::net::kInvalid;
    }
    queue_cv_.notify_all();
    // 关闭尚未处理的连接
    {
        std::lock_guard<std::mutex> lk(queue_mu_);
        while (!queue_.empty()) {
            cm::net::closeTcp(queue_.front().first);
            queue_.pop();
        }
    }
    for (auto& t : threads_) {
        if (t.joinable()) t.join();
    }
    threads_.clear();
}

void Server::acceptLoop() {
    while (running_.load()) {
        std::string ip;
        cm::net::Fd fd = cm::net::acceptTcp(listen_fd_, ip);
        if (!cm::net::isValid(fd)) {
            if (!running_.load()) break;
            continue;
        }
        {
            std::lock_guard<std::mutex> lk(queue_mu_);
            queue_.emplace(fd, ip);
        }
        queue_cv_.notify_one();
    }
}

void Server::workerLoop() {
    for (;;) {
        std::pair<int, std::string> item;
        {
            std::unique_lock<std::mutex> lk(queue_mu_);
            queue_cv_.wait(lk, [this] { return !queue_.empty() || !running_.load(); });
            if (!running_.load() && queue_.empty()) return;
            if (queue_.empty()) continue;
            item = std::move(queue_.front());
            queue_.pop();
        }
        handleConnection(item.first, item.second);
    }
}

bool Server::readRequest(cm::net::Fd fd, std::string& buf, cm::http::HttpRequest& req, bool& closeAfter) {
    closeAfter = false;
    std::string line;
    if (!readLine(fd, buf, line)) return false;
    if (line.empty()) return false;
    {
        std::istringstream ss(line);
        std::string target;
        if (!(ss >> req.method >> target >> req.http_version)) return false;
        req.target = target;
        size_t q = target.find('?');
        const std::string rawPath = q == std::string::npos ? target : target.substr(0, q);
        // Tomcat/Spring 会按 URIEncoding(UTF-8) 解码 request URI，路径变量与 /profile/** 的
        // 文件名都是解码后交给处理器的；查询参数在 parseUrlEncoded 里已解码，路径此前漏了，
        // 导致 %20 / %E4%BA%91 之类的路径变量与 Java 行为不一致。
        req.path = cm::http::HttpRequest::percentDecode(rawPath, false);
        if (q != std::string::npos) {
            cm::http::HttpRequest::parseUrlEncoded(target.substr(q + 1), req.query_params);
        }
    }
    // 规范化路径：去掉末尾多余 '/'（Spring 默认 useTrailingSlashMatch=true）
    while (req.path.size() > 1 && req.path.back() == '/') req.path.pop_back();

    std::string contentLength;
    bool chunked = false;
    for (;;) {
        if (!readLine(fd, buf, line)) return false;
        if (line.empty()) break;
        size_t colon = line.find(':');
        if (colon == std::string::npos) continue;
        std::string name = lower(cm::utils::StringUtils::trim(line.substr(0, colon)));
        std::string value = cm::utils::StringUtils::trim(line.substr(colon + 1));
        if (name == "content-length") contentLength = value;
        if (name == "transfer-encoding" && lower(value).find("chunked") != std::string::npos) chunked = true;
        if (name == "connection" && lower(value).find("close") != std::string::npos) closeAfter = true;
        req.headers[name] = value;
        if (name == "cookie") cm::http::HttpRequest::parseCookies(value, req.cookies);
    }
    // 请求体上限：与 application.yaml 的 max-request-size(200MB) 对齐
    constexpr unsigned long long kMaxBodyBytes = 200ULL * 1024 * 1024;
    if (chunked) {
        // HTTP/1.1 chunked 请求体（Transfer-Encoding: chunked）。
        // Java 侧内嵌 Tomcat 原生支持，这里补齐以保持行为一致（此前是直接断开连接）。
        std::string body;
        for (;;) {
            std::string sizeLine;
            if (!readLine(fd, buf, sizeLine)) return false;
            unsigned long long chunkLen = 0;
            if (!parseChunkSizeLine(sizeLine, kMaxBodyBytes, chunkLen)) return false;
            if (chunkLen == 0) {
                // 末尾可选 trailer：读到空行为止
                for (;;) {
                    std::string trailer;
                    if (!readLine(fd, buf, trailer)) return false;
                    if (trailer.empty()) break;
                }
                break;
            }
            if (body.size() + chunkLen > kMaxBodyBytes) return false;
            // readExact 是覆盖写（不是追加），必须经临时串再拼到 body，否则多块之间会互相覆盖
            std::string chunk;
            if (!readExact(fd, buf, static_cast<size_t>(chunkLen), chunk)) return false;
            body += chunk;
            std::string crlf;
            if (!readLine(fd, buf, crlf)) return false;  // 每块数据后的 CRLF
        }
        req.body = std::move(body);
    } else {
        size_t len = 0;
        if (!contentLength.empty()) {
            try {
                len = static_cast<size_t>(std::stoull(contentLength));
            } catch (...) {
                len = 0;
            }
        }
        if (len > 0) {
            if (len > kMaxBodyBytes) return false;
            if (!readExact(fd, buf, len, req.body)) return false;
        }
    }
    std::string ct = lower(req.getHeader("content-type"));
    if (ct.find("application/x-www-form-urlencoded") != std::string::npos) {
        cm::http::HttpRequest::parseUrlEncoded(req.body, req.form_params);
    } else if (ct.find("multipart/form-data") != std::string::npos) {
        req.parts = cm::http::HttpRequest::parseMultipart(req.body, req.getHeader("content-type"));
    }
    if (req.http_version == "HTTP/1.0" && req.getHeader("connection").empty()) closeAfter = true;
    return true;
}

cm::http::ApiResponse Server::dispatch(cm::http::HttpRequest& req) {
    // 每个请求开始清空线程内的延迟绑定注册表：上一个请求若有"构建了 SQL 但没执行"的
    // 分支，令牌会残留；这里保证参数不会跨请求串用。
    cm::db::resetBindings();
    auto& ts = cm::security::TokenService::instance();
    cm::security::SecurityUtils::clear();

    // CORS 预检：CorsFilter 在最外层直接应答
    if (isCorsPreflight(req)) {
        cm::http::ApiResponse r;
        r.status = 200;
        applyCors(req, r);
        return r;
    }

    // LogoutFilter 在 JWT 过滤器之前：/logout 不需要有效登录态
    if (req.path == "/logout") {
        cm::http::ApiResponse r = handleLogout(req);
        applyCors(req, r);
        return r;
    }

    // JwtAuthenticationTokenFilter
    std::string rawToken = ts.getToken(req);
    if (!rawToken.empty()) {
        if (!ts.isValidTokenFormat(rawToken)) {
            // 过滤器抛出的异常到不了 @ControllerAdvice -> 真实 500
            cm::http::ApiResponse r = containerError(500, req.path);
            applyCors(req, r);
            return r;
        }
        auto loginUser = ts.getLoginUserByToken(rawToken);
        if (loginUser) {
            ts.verifyToken(*loginUser);
            cm::security::SecurityUtils::setLoginUser(*loginUser);
        }
    }
    bool authenticated = cm::security::SecurityUtils::isAuthenticated();

    RouteMatch m = router().match(req.method, req.path);
    // Spring 的顺序：URL 层 antMatchers 规则先裁决，命中即生效；未命中才轮到路由级标记
    //（@PreAuthorize 是之后的方法层，另说）。
    AuthType rule = Router::urlRule(req.method, req.path).value_or(
        m.matched ? m.route->auth : AuthType::Authenticated);

    if (rule == AuthType::Authenticated && !authenticated) {
        cm::http::ApiResponse r = unauthorized(req.path);
        applyCors(req, r);
        return r;
    }
    if (rule == AuthType::DenyAll) {
        cm::http::ApiResponse r = authenticated ? containerError(403, req.path) : unauthorized(req.path);
        applyCors(req, r);
        return r;
    }
    if (rule == AuthType::Anonymous && authenticated) {
        cm::http::ApiResponse r = containerError(403, req.path);
        applyCors(req, r);
        return r;
    }

    if (!m.matched) {
        cm::http::ApiResponse r;
        if (m.method_not_allowed) {
            cm::core::domain::AjaxResult a =
                cm::core::domain::AjaxResult::error("Request method '" + req.method + "' not supported");
            r = json(a);
        } else if (!serveStatic(req.method, req.path, r)) {
            r = containerError(404, req.path);
        }
        applyCors(req, r);
        return r;
    }

    // @PreAuthorize 在方法参数绑定之前执行
    for (const auto& p : m.route->required_perms) {
        if (!cm::security::SecurityUtils::hasPermi(p)) {
            cm::http::ApiResponse r = ExceptionMapper::map(std::make_exception_ptr(
                cm::exception::AccessDeniedException("没有权限，请联系管理员授权")));
            applyCors(req, r);
            return r;
        }
    }
    if (!m.route->any_perms.empty()) {
        bool ok = false;
        for (const auto& p : m.route->any_perms) {
            if (cm::security::SecurityUtils::hasPermi(p)) {
                ok = true;
                break;
            }
        }
        if (!ok) {
            cm::http::ApiResponse r = ExceptionMapper::map(std::make_exception_ptr(
                cm::exception::AccessDeniedException("没有权限，请联系管理员授权")));
            applyCors(req, r);
            return r;
        }
    }
    if (!m.route->required_role.empty() && !cm::security::SecurityUtils::hasRole(m.route->required_role)) {
        cm::http::ApiResponse r = ExceptionMapper::map(std::make_exception_ptr(
            cm::exception::AccessDeniedException("没有权限，请联系管理员授权")));
        applyCors(req, r);
        return r;
    }

    RequestContext ctx;
    ctx.req = std::move(req);
    ctx.path_vars = m.path_vars;
    try {
        cm::http::ApiResponse r = m.route->handler(ctx);
        // LogAspect 的 @AfterReturning：只对真正进入控制器的请求生效
        cm::aspect::OperLogAspect::instance().record(ctx, r, nullptr);
        // handler 可能改写过 req
        req = std::move(ctx.req);
        applyCors(req, r);
        return r;
    } catch (...) {
        // LogAspect 的 @AfterThrowing：status=1，异常消息进 error_msg（NPE 时为 NULL）
        const std::exception_ptr ep = std::current_exception();
        cm::aspect::Failure failure{exceptionMessage(ep)};
        cm::http::ApiResponse r = ExceptionMapper::map(ep);
        cm::aspect::OperLogAspect::instance().record(ctx, r, &failure);
        req = std::move(ctx.req);
        applyCors(req, r);
        return r;
    }
}

void Server::handleConnection(cm::net::Fd fd, const std::string& peer) {
    cm::net::setNoDelay(fd);
    cm::net::setTimeout(fd, 60000);  // 对应 Tomcat keepAliveTimeout

    std::string buf;
    while (running_.load()) {
        cm::http::HttpRequest req;
        req.remote_addr = peer;
        bool closeAfter = false;
        if (!readRequest(fd, buf, req, closeAfter)) break;
        cm::http::ApiResponse resp = dispatch(req);
        writeResponse(fd, resp, !closeAfter);
        if (closeAfter) break;
    }
    cm::net::closeTcp(fd);
}

// 标准 reason phrase（与 Tomcat 内置表一致）。HttpServletResponse 允许为空，
// 但 Tomcat 会写出标准文案，客户端日志/抓包常依赖它，因此这里完整覆盖而不是只列常用几个。
static const char* reasonPhrase(int status) {
    switch (status) {
        case 100: return "Continue";
        case 101: return "Switching Protocols";
        case 200: return "OK";
        case 201: return "Created";
        case 202: return "Accepted";
        case 203: return "Non-Authoritative Information";
        case 204: return "No Content";
        case 205: return "Reset Content";
        case 206: return "Partial Content";
        case 300: return "Multiple Choices";
        case 301: return "Moved Permanently";
        case 302: return "Found";
        case 303: return "See Other";
        case 304: return "Not Modified";
        case 307: return "Temporary Redirect";
        case 308: return "Permanent Redirect";
        case 400: return "Bad Request";
        case 401: return "Unauthorized";
        case 402: return "Payment Required";
        case 403: return "Forbidden";
        case 404: return "Not Found";
        case 405: return "Method Not Allowed";
        case 406: return "Not Acceptable";
        case 407: return "Proxy Authentication Required";
        case 408: return "Request Timeout";
        case 409: return "Conflict";
        case 410: return "Gone";
        case 411: return "Length Required";
        case 412: return "Precondition Failed";
        case 413: return "Payload Too Large";
        case 414: return "URI Too Long";
        case 415: return "Unsupported Media Type";
        case 416: return "Range Not Satisfiable";
        case 417: return "Expectation Failed";
        case 422: return "Unprocessable Entity";
        case 425: return "Too Early";
        case 429: return "Too Many Requests";
        case 431: return "Request Header Fields Too Large";
        case 451: return "Unavailable For Legal Reasons";
        case 500: return "Internal Server Error";
        case 501: return "Not Implemented";
        case 502: return "Bad Gateway";
        case 503: return "Service Unavailable";
        case 504: return "Gateway Timeout";
        case 505: return "HTTP Version Not Supported";
        default: return "";
    }
}

bool Server::parseChunkSizeLine(const std::string& line, unsigned long long maxBytes,
                                unsigned long long& outSize) {
    outSize = 0;
    // chunk-size 后面可能跟 chunk-ext（;name=value），只取分号前的十六进制
    const size_t semi = line.find(';');
    const std::string hexPart =
        cm::utils::StringUtils::trim(semi == std::string::npos ? line : line.substr(0, semi));
    if (hexPart.empty()) return false;
    unsigned long long v = 0;
    for (char c : hexPart) {
        unsigned long long digit;
        if (c >= '0' && c <= '9')
            digit = static_cast<unsigned long long>(c - '0');
        else if (c >= 'a' && c <= 'f')
            digit = static_cast<unsigned long long>(c - 'a' + 10);
        else if (c >= 'A' && c <= 'F')
            digit = static_cast<unsigned long long>(c - 'A' + 10);
        else
            return false;  // 非法十六进制
        if (v > (maxBytes - digit) / 16) return false;  // 溢出或超上限
        v = v * 16 + digit;
        if (v > maxBytes) return false;
    }
    outSize = v;
    return true;
}

void Server::writeResponse(cm::net::Fd fd, const cm::http::ApiResponse& resp, bool keepAlive) {
    std::ostringstream head;
    head << "HTTP/1.1 " << resp.status << " " << reasonPhrase(resp.status) << "\r\n";
    head << "Content-Type: " << resp.content_type << "\r\n";
    head << "Content-Length: " << resp.body.size() << "\r\n";
    for (const auto& [k, v] : resp.headers) head << k << ": " << v << "\r\n";
    head << "Connection: " << (keepAlive ? "keep-alive" : "close") << "\r\n\r\n";
    std::string data = head.str() + resp.body;
    size_t sent = 0;
    while (sent < data.size()) {
        const long n = cm::net::writeSome(fd, data.data() + sent, data.size() - sent);
        if (n <= 0) break;
        sent += static_cast<size_t>(n);
    }
}

} // namespace cm::web
