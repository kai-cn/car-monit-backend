#include "cm/framework/redis/RedisClient.hpp"

#include "cm/framework/net/Os.hpp"

#include <cctype>
#include <cerrno>
#include <cstdlib>
#include <cstring>

namespace cm::redis {
namespace {

std::string toUpper(std::string s) {
    for (char& c : s) c = static_cast<char>(::toupper(static_cast<unsigned char>(c)));
    return s;
}

bool readLine(cm::net::Fd fd, std::string& line) {
    line.clear();
    char c;
    for (;;) {
        long n = cm::net::readSome(fd, &c, 1);
        if (n <= 0) return false;
        if (c == '\r') continue;
        if (c == '\n') return true;
        line.push_back(c);
    }
}

} // namespace

RedisClient::~RedisClient() { close(); }

void RedisClient::setError(const std::string& msg) { last_error_ = msg; }

bool RedisClient::connect(const RedisConfig& cfg) {
    close();
    cfg_ = cfg;
    std::string err;
    cm::net::Fd fd = cm::net::connectTcp(cfg.host, cfg.port, cfg.timeoutMs, &err);
    if (!cm::net::isValid(fd)) {
        setError(err);
        return false;
    }
    fd_ = cm::net::toStorage(fd);

    if (!cfg.password.empty()) {
        std::vector<std::string> args{"AUTH", cfg.password};
        if (!sendCommand(args)) {
            close();
            return false;
        }
        std::string reply;
        if (!readReply(reply)) {
            close();
            return false;
        }
        std::string head = reply.substr(0, 1);
        if (head == "-") {
            setError(reply);
            close();
            return false;
        }
    }
    if (cfg.database != 0) {
        std::vector<std::string> args{"SELECT", std::to_string(cfg.database)};
        if (!sendCommand(args)) {
            close();
            return false;
        }
        std::string reply;
        if (!readReply(reply) || (!reply.empty() && reply[0] == '-')) {
            close();
            return false;
        }
    }
    return true;
}

void RedisClient::close() {
    if (fd_ != cm::net::kInvalidStorage) {
        cm::net::closeTcp(handle());
        fd_ = cm::net::kInvalidStorage;
    }
}

bool RedisClient::reconnect() { return connect(cfg_); }

bool RedisClient::ensureConnected() {
    if (fd_ != cm::net::kInvalidStorage) return true;
    return connect(cfg_);
}

bool RedisClient::sendCommand(const std::vector<std::string>& args) {
    std::string buf;
    buf += '*';
    buf += std::to_string(args.size());
    buf += "\r\n";
    for (const auto& a : args) {
        buf += '$';
        buf += std::to_string(a.size());
        buf += "\r\n";
        buf += a;
        buf += "\r\n";
    }
    size_t sent = 0;
    while (sent < buf.size()) {
        long n = cm::net::writeSome(handle(), buf.data() + sent, buf.size() - sent);
        if (n <= 0) {
            setError("写入 Redis 失败: " + std::string(std::strerror(errno)));
            close();
            return false;
        }
        sent += static_cast<size_t>(n);
    }
    return true;
}

bool RedisClient::readBulk(std::string& out) {
    std::string line;
    if (!readLine(handle(), line)) return false;
    if (line.empty()) return false;
    if (line[0] == '-') {
        setError(line);
        return false;
    }
    if (line[0] == '$') {
        long long len = std::atoll(line.c_str() + 1);
        if (len < 0) return false; // nil
        out.resize(static_cast<size_t>(len));
        size_t got = 0;
        while (got < static_cast<size_t>(len)) {
            long n = cm::net::readSome(handle(), &out[got], static_cast<size_t>(len) - got);
            if (n <= 0) return false;
            got += static_cast<size_t>(n);
        }
        char crlf[2];
        size_t r = 0;
        while (r < 2) {
            long n = cm::net::readSome(handle(), crlf + r, 2 - r);
            if (n <= 0) return false;
            r += static_cast<size_t>(n);
        }
        return true;
    }
    out = line;
    return true;
}

bool RedisClient::readReply(std::string& out, bool* isNil) {
    if (isNil) *isNil = false;
    std::string line;
    if (!readLine(handle(), line)) return false;
    if (line.empty()) {
        setError("空的 Redis 回复");
        return false;
    }
    char t = line[0];
    if (t == '+' || t == ':') {
        out = line.substr(1);
        return true;
    }
    if (t == '-') {
        setError(line.substr(1));
        out = line;
        return false;
    }
    if (t == '$') {
        long long len = std::atoll(line.c_str() + 1);
        if (len < 0) {
            if (isNil) *isNil = true;
            out.clear();
            return true;
        }
        out.resize(static_cast<size_t>(len));
        size_t got = 0;
        while (got < static_cast<size_t>(len)) {
            long n = cm::net::readSome(handle(), &out[got], static_cast<size_t>(len) - got);
            if (n <= 0) return false;
            got += static_cast<size_t>(n);
        }
        char crlf[2];
        size_t r = 0;
        while (r < 2) {
            long n = cm::net::readSome(handle(), crlf + r, 2 - r);
            if (n <= 0) return false;
            r += static_cast<size_t>(n);
        }
        return true;
    }
    if (t == '*') {
        long long count = std::atoll(line.c_str() + 1);
        if (count < 0) {
            if (isNil) *isNil = true;
            out.clear();
            return true;
        }
        out.clear();
        for (long long i = 0; i < count; ++i) {
            std::string item;
            bool nil = false;
            if (!readReply(item, &nil)) return false;
            if (i) out.push_back('\n');
            if (!nil) out += item;
        }
        return true;
    }
    out = line;
    return true;
}

std::optional<std::string> RedisClient::command(const std::vector<std::string>& args) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!ensureConnected()) return std::nullopt;
    if (!sendCommand(args)) return std::nullopt;
    std::string reply;
    bool nil = false;
    if (!readReply(reply, &nil)) return std::nullopt;
    if (nil) return std::nullopt;
    return reply;
}

bool RedisClient::ping() {
    auto r = command({"PING"});
    return r && *r == "PONG";
}

std::optional<std::string> RedisClient::get(const std::string& key) {
    std::lock_guard<std::mutex> lk(mu_);
    if (!ensureConnected()) return std::nullopt;
    if (!sendCommand({"GET", key})) return std::nullopt;
    std::string reply;
    bool nil = false;
    if (!readReply(reply, &nil) || nil) return std::nullopt;
    return reply;
}

bool RedisClient::set(const std::string& key, const std::string& value) {
    return command({"SET", key, value}).has_value();
}
bool RedisClient::setex(const std::string& key, const std::string& value, long long seconds) {
    return command({"SETEX", key, std::to_string(seconds), value}).has_value();
}
bool RedisClient::psetex(const std::string& key, const std::string& value, long long ms) {
    return command({"PSETEX", key, std::to_string(ms), value}).has_value();
}
bool RedisClient::setnx(const std::string& key, const std::string& value) {
    auto r = command({"SETNX", key, value});
    return r && *r == "1";
}
long long RedisClient::del(const std::vector<std::string>& keys) {
    if (keys.empty()) return 0;
    std::vector<std::string> args{"DEL"};
    args.insert(args.end(), keys.begin(), keys.end());
    auto r = command(args);
    return r ? std::atoll(r->c_str()) : 0;
}
bool RedisClient::exists(const std::string& key) {
    auto r = command({"EXISTS", key});
    return r && *r == "1";
}
bool RedisClient::expire(const std::string& key, long long seconds) {
    auto r = command({"EXPIRE", key, std::to_string(seconds)});
    return r && *r == "1";
}
long long RedisClient::pttl(const std::string& key) {
    auto r = command({"PTTL", key});
    return r ? std::atoll(r->c_str()) : -2;
}
long long RedisClient::incr(const std::string& key, long long delta) {
    if (delta == 1) {
        auto r = command({"INCR", key});
        return r ? std::atoll(r->c_str()) : 0;
    }
    auto r = command({"INCRBY", key, std::to_string(delta)});
    return r ? std::atoll(r->c_str()) : 0;
}
std::vector<std::string> RedisClient::keys(const std::string& pattern) {
    std::vector<std::string> out;
    auto r = command({"KEYS", pattern});
    if (!r || r->empty()) return out;
    size_t start = 0;
    for (;;) {
        size_t p = r->find('\n', start);
        if (p == std::string::npos) {
            out.push_back(r->substr(start));
            break;
        }
        out.push_back(r->substr(start, p - start));
        start = p + 1;
    }
    return out;
}

std::vector<std::string> RedisClient::scanAll(const std::string& pattern, int count) {
    std::vector<std::string> out;
    std::string cursor = "0";
    for (;;) {
        auto r = command({"SCAN", cursor, "MATCH", pattern, "COUNT", std::to_string(count)});
        if (!r) break;
        // 回复被 readReply 拼成 "cursor\nk1\nk2..."
        size_t p = r->find('\n');
        if (p == std::string::npos) {
            cursor = *r;
        } else {
            cursor = r->substr(0, p);
            size_t start = p + 1;
            while (start < r->size()) {
                size_t q = r->find('\n', start);
                if (q == std::string::npos) {
                    out.push_back(r->substr(start));
                    break;
                }
                out.push_back(r->substr(start, q - start));
                start = q + 1;
            }
        }
        if (cursor == "0") break;
    }
    return out;
}

std::vector<std::string> RedisClient::hkeys(const std::string& key) {
    std::vector<std::string> out;
    auto r = command({"HKEYS", key});
    if (!r || r->empty()) return out;
    size_t start = 0;
    for (;;) {
        size_t p = r->find('\n', start);
        if (p == std::string::npos) {
            out.push_back(r->substr(start));
            break;
        }
        out.push_back(r->substr(start, p - start));
        start = p + 1;
    }
    return out;
}
std::optional<std::string> RedisClient::hget(const std::string& key, const std::string& field) {
    return command({"HGET", key, field});
}
bool RedisClient::hset(const std::string& key, const std::string& field, const std::string& value) {
    return command({"HSET", key, field, value}).has_value();
}
long long RedisClient::hdel(const std::string& key, const std::vector<std::string>& fields) {
    if (fields.empty()) return 0;
    std::vector<std::string> args{"HDEL", key};
    args.insert(args.end(), fields.begin(), fields.end());
    auto r = command(args);
    return r ? std::atoll(r->c_str()) : 0;
}
long long RedisClient::dbsize() {
    auto r = command({"DBSIZE"});
    return r ? std::atoll(r->c_str()) : 0;
}
std::vector<std::string> RedisClient::info(const std::string& section) {
    std::vector<std::string> lines;
    std::vector<std::string> args{"INFO"};
    if (!section.empty()) args.push_back(section);
    auto r = command(args);
    if (!r) return lines;
    size_t start = 0;
    for (;;) {
        size_t p = r->find('\n', start);
        std::string line = p == std::string::npos ? r->substr(start) : r->substr(start, p - start);
        if (!line.empty() && line.back() == '\r') line.pop_back();
        lines.push_back(line);
        if (p == std::string::npos) break;
        start = p + 1;
    }
    return lines;
}
bool RedisClient::flushdb() {
    return command({"FLUSHDB"}).has_value();
}

// ---------------------------------------------------------------------------

RedisCache& RedisCache::instance() {
    static RedisCache cache;
    return cache;
}

void RedisCache::init(const RedisConfig& cfg) { client_.connect(cfg); }

std::optional<std::string> RedisCache::get(const std::string& key) { return client_.get(key); }
bool RedisCache::set(const std::string& key, const std::string& value) { return client_.set(key, value); }
bool RedisCache::set(const std::string& key, const std::string& value, long long ttlSeconds) {
    return client_.setex(key, value, ttlSeconds);
}
bool RedisCache::del(const std::string& key) { return client_.del({key}) > 0; }
bool RedisCache::expire(const std::string& key, long long seconds) { return client_.expire(key, seconds); }
bool RedisCache::exists(const std::string& key) { return client_.exists(key); }
long long RedisCache::pttlMs(const std::string& key) { return client_.pttl(key); }
std::vector<std::string> RedisCache::keys(const std::string& pattern) { return client_.keys(pattern); }

} // namespace cm::redis
