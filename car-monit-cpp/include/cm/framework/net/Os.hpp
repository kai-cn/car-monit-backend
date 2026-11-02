#pragma once
// 跨平台 TCP socket 封装。
//
// 为什么需要这一层：Server / RedisClient / MySqlConnection 原本直接调用 POSIX
// (socket/connect/read/write/writev/accept/bind/listen)。在 Linux 容器里没问题，
// 但 Java 开发同学多数在 Windows 上开发，Winsock2 与 POSIX 有三点不兼容：
//   1. 句柄类型是 SOCKET（64 位），不能当 int 用；
//   2. fd 不能用 CRT 的 read/write/close，必须 recv/send/closesocket；
//   3. 没有 writev，setsockopt 的超时参数是 DWORD 而不是 timeval。
// 这里把差异收敛在一个头文件里，业务代码只见 cm::net::*。
//
// 对应 Java: java.net.Socket / SocketChannel（JDK 屏蔽了 OS 差异）
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include "cm/framework/net/Fd.hpp"

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <arpa/inet.h>
#include <cerrno>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <unistd.h>
#endif

namespace cm::net {

inline bool isValid(Fd fd) { return fd != kInvalid; }

#ifdef _WIN32
inline SOCKET asSocket(Fd fd) { return static_cast<SOCKET>(fd); }
inline Fd fromSocket(SOCKET s) { return s == INVALID_SOCKET ? kInvalid : static_cast<Fd>(s); }

/** Winsock 需要显式 WSAStartup；用一次性泄漏的 holder 规避静态析构顺序问题 */
inline void ensureWs2() {
    static WSADATA* data = [] {
        auto* d = new WSADATA();
        WSAStartup(MAKEWORD(2, 2), d);
        return d;
    }();
    (void)data;
}
#else
inline int asSocket(Fd fd) { return fd; }
inline Fd fromSocket(int s) { return s < 0 ? kInvalid : static_cast<Fd>(s); }
inline void ensureWs2() {}
#endif

/** 最近一次 socket 错误的人类可读信息（对应 Java 的 SocketException message） */
inline std::string lastError() {
#ifdef _WIN32
    const int e = WSAGetLastError();
    char* msg = nullptr;
    std::string out;
    if (FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
                           FORMAT_MESSAGE_IGNORE_INSERTS,
                       nullptr, e, 0, reinterpret_cast<char*>(&msg), 0, nullptr) != 0 &&
        msg != nullptr) {
        out = msg;
        LocalFree(msg);
        while (!out.empty() && (out.back() == '\r' || out.back() == '\n' || out.back() == ' ')) {
            out.pop_back();
        }
    }
    return out.empty() ? ("WSAError " + std::to_string(e)) : out;
#else
    return std::strerror(errno);
#endif
}

inline void setTimeout(Fd fd, int timeout_ms) {
#ifdef _WIN32
    const DWORD ms = static_cast<DWORD>(timeout_ms < 0 ? 0 : timeout_ms);
    setsockopt(asSocket(fd), SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&ms), sizeof(ms));
    setsockopt(asSocket(fd), SOL_SOCKET, SO_SNDTIMEO, reinterpret_cast<const char*>(&ms), sizeof(ms));
#else
    timeval tv{};
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
#endif
}

inline void setNoDelay(Fd fd) {
    int one = 1;
#ifdef _WIN32
    setsockopt(asSocket(fd), IPPROTO_TCP, TCP_NODELAY, reinterpret_cast<const char*>(&one), sizeof(one));
#else
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
#endif
}

inline int closeTcp(Fd fd) {
    if (!isValid(fd)) return 0;
#ifdef _WIN32
    return closesocket(asSocket(fd)) == 0 ? 0 : -1;
#else
    return ::close(fd);
#endif
}

inline void shutdownTcp(Fd fd) {
    if (!isValid(fd)) return;
#ifdef _WIN32
    ::shutdown(asSocket(fd), SD_BOTH);
#else
    ::shutdown(fd, SHUT_RDWR);
#endif
}

/**
 * 读可用字节。
 *   > 0  实际读到的字节数
 *     0  连接被关闭 / 超时（SO_RCVTIMEO 到期）
 *    -1  出错
 * 与 POSIX read 的差别：Windows 超时返回 WSAETIMEDOUT，这里统一归为 0，
 * 让调用方按“对端无数据/已关闭”处理（原来的错误分支行为不变）。
 */
inline long readSome(Fd fd, void* buf, size_t len) {
    const int n = ::recv(asSocket(fd), static_cast<char*>(buf), static_cast<int>(len), 0);
    if (n > 0) return n;
    if (n == 0) return 0;
#ifdef _WIN32
    const int e = WSAGetLastError();
    if (e == WSAEWOULDBLOCK || e == WSAETIMEDOUT) return 0;
#else
    if (errno == EAGAIN || errno == EWOULDBLOCK) return 0;
#endif
    return -1;
}

/** 写可用字节，语义同 readSome */
inline long writeSome(Fd fd, const void* buf, size_t len) {
    const int n = ::send(asSocket(fd), static_cast<const char*>(buf), static_cast<int>(len), 0);
    if (n > 0) return n;
#ifdef _WIN32
    const int e = WSAGetLastError();
    if (e == WSAEWOULDBLOCK) return 0;
#else
    if (errno == EAGAIN || errno == EWOULDBLOCK) return 0;
#endif
    return -1;
}

/** 全量写出（对应 Java OutputStream.write + flush） */
inline bool writeAll(Fd fd, const void* buf, size_t len, std::string* err = nullptr) {
    size_t sent = 0;
    const auto* p = static_cast<const char*>(buf);
    while (sent < len) {
        const long w = writeSome(fd, p + sent, len - sent);
        if (w <= 0) {
            if (err) *err = lastError();
            return false;
        }
        sent += static_cast<size_t>(w);
    }
    return true;
}

/** writev 的可移植替代：依次写出多个片段 */
struct Chunk {
    const void* data;
    size_t size;
};

inline bool writeChunks(Fd fd, const std::vector<Chunk>& chunks, std::string* err = nullptr) {
    for (const auto& c : chunks) {
        if (c.size == 0) continue;
        if (!writeAll(fd, c.data, c.size, err)) return false;
    }
    return true;
}

/**
 * 建一个 TCP 客户端连接（解析 host + socket + 连接超时 + connect）。
 * 失败返回 kInvalid 并把原因写入 *err。
 */
inline Fd connectTcp(const std::string& host, int port, int connect_timeout_ms,
                     std::string* err = nullptr) {
    ensureWs2();
    addrinfo hints{};
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo* res = nullptr;
    const std::string service = std::to_string(port);
    if (getaddrinfo(host.c_str(), service.c_str(), &hints, &res) != 0 || res == nullptr) {
        if (err) *err = "无法解析主机: " + host;
        return kInvalid;
    }
    Fd fd = fromSocket(::socket(AF_INET, SOCK_STREAM, 0));
    if (!isValid(fd)) {
        if (err) *err = "socket() 失败: " + lastError();
        freeaddrinfo(res);
        return kInvalid;
    }
    setTimeout(fd, connect_timeout_ms);
#ifdef _WIN32
    if (::connect(asSocket(fd), res->ai_addr, static_cast<int>(res->ai_addrlen)) != 0) {
#else
    if (::connect(fd, res->ai_addr, res->ai_addrlen) != 0) {
#endif
        if (err) *err = "连接 " + host + ":" + service + " 失败: " + lastError();
        freeaddrinfo(res);
        closeTcp(fd);
        return kInvalid;
    }
    freeaddrinfo(res);
    return fd;
}

/** 服务端监听（对应 Tomcat NioEndpoint 的 bind + listen） */
inline Fd listenTcp(const std::string& bind_addr, int port, int backlog,
                    std::string* err = nullptr) {
    ensureWs2();
    Fd fd = fromSocket(::socket(AF_INET, SOCK_STREAM, 0));
    if (!isValid(fd)) {
        if (err) *err = "socket() 失败: " + lastError();
        return kInvalid;
    }
    int one = 1;
#ifdef _WIN32
    setsockopt(asSocket(fd), SOL_SOCKET, SO_REUSEADDR, reinterpret_cast<const char*>(&one), sizeof(one));
#else
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
#endif
    sockaddr_in sa{};
    sa.sin_family = AF_INET;
    sa.sin_port = htons(static_cast<uint16_t>(port));
    if (bind_addr.empty() || bind_addr == "0.0.0.0" || bind_addr == "*") {
        sa.sin_addr.s_addr = htonl(INADDR_ANY);
    } else {
        inet_pton(AF_INET, bind_addr.c_str(), &sa.sin_addr);
    }
#ifdef _WIN32
    if (::bind(asSocket(fd), reinterpret_cast<const sockaddr*>(&sa), sizeof(sa)) != 0) {
#else
    if (::bind(fd, reinterpret_cast<const sockaddr*>(&sa), sizeof(sa)) != 0) {
#endif
        if (err) *err = "bind 失败: " + lastError();
        closeTcp(fd);
        return kInvalid;
    }
#ifdef _WIN32
    if (::listen(asSocket(fd), backlog) != 0) {
#else
    if (::listen(fd, backlog) != 0) {
#endif
        if (err) *err = "listen 失败: " + lastError();
        closeTcp(fd);
        return kInvalid;
    }
    return fd;
}

/** 接受一个连接；peer_ip 输出对端点分十进制地址（对应 Java Socket.getInetAddress()） */
inline Fd acceptTcp(Fd listen_fd, std::string& peer_ip) {
    sockaddr_in peer{};
    socklen_t len = sizeof(peer);
#ifdef _WIN32
    Fd fd = fromSocket(::accept(asSocket(listen_fd), reinterpret_cast<sockaddr*>(&peer), &len));
#else
    Fd fd = fromSocket(::accept(listen_fd, reinterpret_cast<sockaddr*>(&peer), &len));
#endif
    if (!isValid(fd)) return kInvalid;
    char ip[INET_ADDRSTRLEN] = {0};
    inet_ntop(AF_INET, &peer.sin_addr, ip, sizeof(ip));
    peer_ip = ip;
    return fd;
}

} // namespace cm::net
