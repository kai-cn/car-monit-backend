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
        file = std::filesystem::path(cfg.profile) / rel;
        // RuoYi 的 uploadPath 已经是 /profile 的根
        if (!std::filesystem::exists(file)) {
            file = std::filesystem::path(cfg.profile) / "profile" / rel;
        }
    } else {
        std::string rel = path == "/" ? "index.html" : path.substr(1);
        if (!safePath(rel)) return false;
        file = std::filesystem::path("config/static") / rel;
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
    if (chunked) {
        // ⚠️ 不支持 chunked
        return false;
    }
    size_t len = 0;
    if (!contentLength.empty()) {
        try {
            len = static_cast<size_t>(std::stoull(contentLength));
        } catch (...) {
            len = 0;
        }
    }
    if (len > 0) {
        if (len > 200ULL * 1024 * 1024) return false;
        if (!readExact(fd, buf, len, req.body)) return false;
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
    AuthType rule = m.matched ? m.route->auth : Router::securityRule(req.method, req.path);

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
        // handler 可能改写过 req
        req = std::move(ctx.req);
        applyCors(req, r);
        return r;
    } catch (...) {
        req = std::move(ctx.req);
        cm::http::ApiResponse r = ExceptionMapper::map(std::current_exception());
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

void Server::writeResponse(cm::net::Fd fd, const cm::http::ApiResponse& resp, bool keepAlive) {
    std::ostringstream head;
    head << "HTTP/1.1 " << resp.status << " " << (resp.status == 200 ? "OK"
                                            : resp.status == 201 ? "Created"
                                            : resp.status == 204 ? "No Content"
                                            : resp.status == 400 ? "Bad Request"
                                            : resp.status == 401 ? "Unauthorized"
                                            : resp.status == 403 ? "Forbidden"
                                            : resp.status == 404 ? "Not Found"
                                            : resp.status == 405 ? "Method Not Allowed"
                                            : resp.status == 500 ? "Internal Server Error"
                                                                 : "OK")
         << "\r\n";
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
