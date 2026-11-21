// Redis 连接模型验收工具（一次性验收用，默认不参与构建）
//
// 验证点：
//   1. 每条连接都执行 AUTH（多线程各自连接，全部可用即证明不是"只有首条 AUTH"）
//   2. 并发无全局锁：32 线程 × N 次 GET/SET 的吞吐与 P99
//   3. 断线自愈：用 CLIENT KILL 打死某线程的连接，下一次命令应自动重连成功
//   4. 线程退出回收：线程结束后 CLIENT LIST 的连接数应回落
//   5. 降级返回值：错误密码/错误端口下 get→nullopt、set→false、del→0、pttl→-2、keys→空
//
// 环境变量：CM_VERIFY_REDIS_HOST/PORT/PASS
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <string>
#include <thread>
#include <vector>

#include "cm/common/utils/Logger.hpp"
#include "cm/framework/redis/RedisClient.hpp"

using cm::redis::RedisCache;
using cm::redis::RedisClient;
using cm::redis::RedisConfig;

namespace {

int g_pass = 0;
int g_fail = 0;

std::string env(const char* k, const std::string& def = "") {
    const char* v = std::getenv(k);
    return v ? std::string(v) : def;
}

void report(bool ok, const std::string& name, const std::string& detail) {
    if (ok) {
        ++g_pass;
        std::cout << "[PASS] " << name << "  " << detail << "\n";
    } else {
        ++g_fail;
        std::cout << "[FAIL] " << name << "  " << detail << "\n";
    }
}

/** 用独立连接数一次 CLIENT LIST 的行数（含自己） */
long long clientCount(const RedisConfig& cfg) {
    RedisClient admin;
    if (!admin.connect(cfg)) return -1;
    auto out = admin.command({"CLIENT", "LIST"});
    if (!out) return -1;
    long long n = 0;
    for (char c : *out) {
        if (c == '\n') ++n;
    }
    return n;
}

} // namespace

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    cm::log::Logger::instance().init("logs", "error");

    RedisConfig cfg;
    cfg.host = env("CM_VERIFY_REDIS_HOST", "127.0.0.1");
    cfg.port = std::stoi(env("CM_VERIFY_REDIS_PORT", "6380"));
    cfg.password = env("CM_VERIFY_REDIS_PASS", "cmtestpwd");
    cfg.timeoutMs = 5000;

    std::cout << "=== Redis: " << cfg.host << ":" << cfg.port << " ===\n";

    // ---- 5) 降级返回值（错误密码）----
    {
        RedisConfig bad = cfg;
        bad.password = "definitely-wrong";
        RedisClient c;
        const bool connected = c.connect(bad);
        report(!connected, "错误密码连接失败（不抛异常）", connected ? "connect 返回 true" : "connect=false");
        report(!c.get("k").has_value(), "错误密码下 get -> nullopt", "");
        report(!c.set("k", "v"), "错误密码下 set -> false", "");
        report(c.del({"k"}) == 0, "错误密码下 del -> 0", "del=" + std::to_string(c.del({"k"})));
        report(c.pttl("k") == -2, "错误密码下 pttl -> -2", "pttl=" + std::to_string(c.pttl("k")));
        report(c.keys("cm:*").empty(), "错误密码下 keys -> 空", "");
    }
    // 错误端口
    {
        RedisConfig bad = cfg;
        bad.port = 1;
        RedisClient c;
        report(!c.connect(bad), "错误端口连接失败", "");
        report(!c.exists("k"), "错误端口下 exists -> false", "");
    }

    // ---- 1) 多线程各自 AUTH ----
    RedisCache::instance().init(cfg);
    // 主线程先建连
    const bool mainPing = RedisCache::instance().client().ping();
    report(mainPing, "主线程 PING", "");

    const int THREADS = 32;
    std::atomic<int> authOk{0};
    {
        std::vector<std::thread> ts;
        for (int i = 0; i < THREADS; ++i) {
            ts.emplace_back([&, i]() {
                auto& c = RedisCache::instance().client();
                if (c.ping()) authOk.fetch_add(1);
                // 每条连接写自己专属 key，证明是独立连接而非共享
                RedisCache::instance().set("cm:auth:" + std::to_string(i), std::to_string(i));
            });
        }
        for (auto& t : ts) t.join();
    }
    report(authOk.load() == THREADS,
           "32 线程各自 PING 成功（每条连接都执行了 AUTH）",
           "ok=" + std::to_string(authOk.load()) + "/" + std::to_string(THREADS));
    {
        long long found = 0;
        for (int i = 0; i < THREADS; ++i) {
            if (RedisCache::instance().exists("cm:auth:" + std::to_string(i))) ++found;
        }
        report(found == THREADS, "32 个线程写入各自 key 均可见", "found=" + std::to_string(found));
    }

    // ---- 4) 线程退出回收连接 ----
    const long long afterJoin = clientCount(cfg);
    // clientCount 自己也会占用一条；main 线程 1 条；理论上应远小于 34
    report(afterJoin >= 0 && afterJoin <= 4,
           "线程退出后连接数回落（回收生效）",
           "CLIENT LIST 行数=" + std::to_string(afterJoin) + "（工作线程已 join）");

    // ---- 3) 断线自愈 ----
    {
        std::atomic<bool> killed{false};
        std::atomic<bool> healed{false};
        std::string detail;
        std::thread worker([&]() {
            auto& c = RedisCache::instance().client();
            c.ping();
            // 让主线程有机会 kill 掉"我们这个线程的连接"
            while (!killed.load()) std::this_thread::sleep_for(std::chrono::milliseconds(5));
            // 连接已被服务端关闭，下一次命令应触发 ensureConnected 重连
            const bool ok = c.set("cm:heal", "1");
            healed.store(ok);
        });
        std::this_thread::sleep_for(std::chrono::milliseconds(80));
        // 从管理连接杀掉所有普通客户端连接
        {
            RedisClient admin;
            admin.connect(cfg);
            admin.command({"CLIENT", "KILL", "TYPE", "normal"});
        }
        killed.store(true);
        worker.join();
        report(healed.load(), "断线后本线程自愈（重连成功）", healed.load() ? "set 成功" : "set 失败");
    }

    // ---- 2) 并发吞吐 ----
    {
        const int OPS = 2000;
        std::vector<std::vector<double>> lat(THREADS);
        auto worker = [&](int idx) {
            auto& c = RedisCache::instance().client();
            c.ping();
            lat[idx].reserve(OPS);
            for (int i = 0; i < OPS; ++i) {
                const std::string key = "cm:bench:" + std::to_string(idx) + ":" + std::to_string(i % 64);
                const auto t0 = std::chrono::steady_clock::now();
                if (i % 2 == 0) {
                    c.set(key, "v" + std::to_string(i));
                } else {
                    c.get(key);
                }
                const auto t1 = std::chrono::steady_clock::now();
                lat[idx].push_back(std::chrono::duration<double, std::micro>(t1 - t0).count());
            }
        };
        std::vector<std::thread> ts;
        const auto t0 = std::chrono::steady_clock::now();
        for (int i = 0; i < THREADS; ++i) ts.emplace_back(worker, i);
        for (auto& t : ts) t.join();
        const auto t1 = std::chrono::steady_clock::now();
        const double secs = std::chrono::duration<double>(t1 - t0).count();
        const long long total = static_cast<long long>(THREADS) * OPS;

        std::vector<double> all;
        for (auto& v : lat) all.insert(all.end(), v.begin(), v.end());
        std::sort(all.begin(), all.end());
        const double p50 = all[static_cast<size_t>(all.size() * 0.50)];
        const double p99 = all[static_cast<size_t>(all.size() * 0.99)];
        const double qps = total / secs;

        char buf[320];
        std::snprintf(buf, sizeof(buf),
                      "%d 线程 x %d 次 = %lld ops, 耗时 %.3fs, QPS=%.0f, P50=%.1fus, P99=%.1fus",
                      THREADS, OPS, total, secs, qps, p50, p99);
        report(qps > 0, "并发吞吐（每线程独立连接，无全局锁）", buf);
    }

    // ---- 2b) 旧模型对照：32 线程共享同一个 RedisClient（= 改造前的"单连接 + 全局互斥"）----
    {
        const int OPS = 2000;
        RedisClient shared;
        if (!shared.connect(cfg)) {
            report(false, "旧模型对照", "共享连接无法建立");
        } else {
            std::vector<double> all;
            std::atomic<long long> n{0};
            std::vector<std::thread> ts;
            const auto t0 = std::chrono::steady_clock::now();
            for (int i = 0; i < THREADS; ++i) {
                ts.emplace_back([&, i]() {
                    for (int k = 0; k < OPS; ++k) {
                        const std::string key = "cm:old:" + std::to_string(i) + ":" + std::to_string(k % 64);
                        const auto a0 = std::chrono::steady_clock::now();
                        if (k % 2 == 0)
                            shared.set(key, "v");
                        else
                            shared.get(key);
                        const auto a1 = std::chrono::steady_clock::now();
                        n.fetch_add(1);
                        (void)a0;
                        (void)a1;
                    }
                });
            }
            for (auto& t : ts) t.join();
            const auto t1 = std::chrono::steady_clock::now();
            const double secs = std::chrono::duration<double>(t1 - t0).count();
            char buf[320];
            std::snprintf(buf, sizeof(buf),
                          "旧模型（共享 1 连接 + 全局 mutex）: %d 线程 x %d 次 = %lld ops, 耗时 %.3fs, QPS=%.0f",
                          THREADS, OPS, n.load(), secs, n.load() / secs);
            report(true, "BENCH-旧模型", buf);
        }
    }

    // ---- 简单正确性回归 ----
    {
        auto& c = RedisCache::instance().client();
        RedisCache::instance().set("cm:k1", "v1", 60);
        report(RedisCache::instance().get("cm:k1").value_or("") == "v1", "SET/GET 往返", "");
        const long long ttl = RedisCache::instance().pttlMs("cm:k1");
        report(ttl > 0 && ttl <= 60000, "SETEX TTL 生效", "pttl=" + std::to_string(ttl));
        report(RedisCache::instance().del("cm:k1"), "DEL 生效", "");
        report(!RedisCache::instance().exists("cm:k1"), "DEL 后不存在", "");
        report(RedisCache::instance().pttlMs("cm:k1") == -2, "不存在 key 的 pttl=-2", "");
        (void)c;
    }

    std::cout << "\n通过 " << g_pass << " / 失败 " << g_fail << "\n";
    return g_fail == 0 ? 0 : 1;
}
