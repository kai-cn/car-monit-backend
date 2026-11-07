#pragma once
// 内嵌 HTTP 服务器（对应 Spring Boot 内嵌 Tomcat + Filter 链）
//
// ⚠️ 限制（见 COMPATIBILITY.md）：
//   * 不支持 HTTP/2、TLS、WebSocket；chunked 请求体自 2026-11-07 起支持（与内嵌 Tomcat 一致）
//   * 工作线程数固定（默认 32，可用 CM_WORKERS 覆盖），Tomcat 默认 maxThreads=800
//   * 过载保护：待处理连接队列上限 max(100, workers×2)；请求行+头 60s 整体截止（防 slowloris）
//   * 请求体定界支持 Content-Length 与 Transfer-Encoding: chunked，上限 200MB（对齐 spring.servlet.multipart）
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <queue>

#include "cm/framework/net/Fd.hpp"
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

    /** 解析 chunked 的 chunk-size 行（可单测）：
     *  - 允许 `1A3` 十六进制与 `;name=value` 形式的 chunk-ext（ext 被忽略）
     *  - 超过 maxBytes 或含非法字符返回 false；`0` 是合法的结束块
     */
    static bool parseChunkSizeLine(const std::string& line, unsigned long long maxBytes,
                                   unsigned long long& outSize);

    /** 在一个已连接的 socket 上解析一次请求（可单测）。
     *  buffer 既是入参也是出参：keep-alive 下同一连接的下一个请求可能已经在里面，
     *  解析完当前请求后剩余字节会留在 buffer 中。
     *  deadline 是"请求行 + 请求头"的整体截止时间（slowloris 防护）；默认 max() 表示不限。
     */
    static bool readRequest(cm::net::Fd fd, std::string& buffer, cm::http::HttpRequest& req,
                            bool& closeAfter,
                            std::chrono::steady_clock::time_point deadline =
                                std::chrono::steady_clock::time_point::max());

private:
    void acceptLoop();
    void workerLoop();
    void handleConnection(cm::net::Fd fd, const std::string& peer);
    static void writeResponse(cm::net::Fd fd, const cm::http::ApiResponse& resp, bool keepAlive);

    std::string host_;
    int port_;
    int workers_;
    int backlog_;
    /** 待处理连接队列上限：对齐 Tomcat acceptCount=100，且不少于 workers×2 */
    size_t queue_cap_{100};
    std::atomic<unsigned long long> queue_overflow_{0};
    cm::net::Fd listen_fd_{cm::net::kInvalid};
    std::atomic<bool> running_{false};
    std::vector<std::thread> threads_;
    std::mutex queue_mu_;
    std::condition_variable queue_cv_;
    std::queue<std::pair<cm::net::Fd, std::string>> queue_;
};

} // namespace cm::web
