#pragma once
// 内嵌 HTTP 服务器（对应 Spring Boot 内嵌 Tomcat + Filter 链）
//
// ⚠️ 限制（见 COMPATIBILITY.md）：
//   * 不支持 HTTP/2、TLS、chunked 请求体（返回 411）、WebSocket
//   * 工作线程数固定（默认 32，可用 CM_WORKERS 覆盖），Tomcat 默认 maxThreads=800
//   * 仅支持 Content-Length 定界请求体，最大 200MB（对齐 spring.servlet.multipart）
#include <atomic>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include "cm/framework/http/HttpRequest.hpp"
#include "cm/framework/http/HttpResponse.hpp"

namespace cm::web {

class Server {
public:
    Server(std::string host, int port, int workers, int backlog);
    ~Server();

    bool start();
    void stop();
    bool running() const { return running_.load(); }
    int port() const { return port_; }

    /** 单次请求处理（可脱离 socket 单测） */
    static cm::http::ApiResponse dispatch(cm::http::HttpRequest& req);

private:
    void acceptLoop();
    void workerLoop();
    void handleConnection(int fd, const std::string& peer);
    bool readRequest(int fd, std::string& buffer, cm::http::HttpRequest& req, bool& closeAfter);
    static void writeResponse(int fd, const cm::http::ApiResponse& resp, bool keepAlive);

    std::string host_;
    int port_;
    int workers_;
    int backlog_;
    int listen_fd_{-1};
    std::atomic<bool> running_{false};
    std::vector<std::thread> threads_;
    std::mutex queue_mu_;
    std::condition_variable queue_cv_;
    std::queue<std::pair<int, std::string>> queue_;
};

} // namespace cm::web
