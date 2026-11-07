#pragma once
// 对应 Java: SLF4J + Logback（LogAspect / BaseController.logger）
//
// 行为：
//   * 控制台 + 文件双写
//   * 文件按大小滚动（默认 50MB，保留 10 个），命名 carmonit.log / carmonit.1.log
//   * 级别过滤：trace/debug/info/warn/error
//   * **异步**：调用线程只做格式化与入队，文件/控制台 I/O 由单个后台线程完成
//     （对应 Logback AsyncAppender；避免 32 个 worker 在日志写盘上互相排队）
//     队列有界：接近上限时先丢 TRACE/DEBUG/INFO，满了丢弃并计数，绝不阻塞请求线程。
#include <atomic>
#include <condition_variable>
#include <deque>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>

namespace cm::log {

enum class Level { Trace = 0, Debug, Info, Warn, Error, Off };

class Logger {
public:
    static Logger& instance();

    void init(const std::string& dir, const std::string& level);
    void setLevel(const std::string& level);

    /** 入队（异步）；未 init 或已 shutdown 时退化为同步写 */
    void write(Level level, const std::string& logger, const std::string& msg);
    bool enabled(Level level) const {
        return level >= level_.load(std::memory_order_relaxed);
    }

    /** 停后台线程并把队列写空。main 退出前调用，保证最后几条日志落盘。 */
    void shutdown();

private:
    Logger() = default;
    ~Logger();
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    void workerLoop();
    /** 后台线程里真正写控制台/文件（只有 worker 调用，无需加锁） */
    void writeLine(const std::string& line);
    void rotateIfNeeded();

    mutable std::mutex mu_;
    std::condition_variable cv_;
    std::deque<std::string> queue_;
    std::thread worker_;
    bool running_{false};
    size_t queue_cap_{8192};
    size_t discarding_threshold_{1638};  // 20%：剩余空间不足时先丢低级别
    std::atomic<unsigned long long> dropped_{0};

    std::atomic<Level> level_{Level::Debug};
    std::string dir_{"logs"};
    std::string file_;
    long long size_{0};
    long long max_size_{50LL * 1024 * 1024};
    int max_files_{10};
};

} // namespace cm::log

#define CM_LOG(level, logger, msg)                                                    \
    do {                                                                              \
        if (::cm::log::Logger::instance().enabled(level)) {                           \
            std::ostringstream _os;                                                   \
            _os << msg;                                                               \
            ::cm::log::Logger::instance().write(level, logger, _os.str());            \
        }                                                                             \
    } while (0)

#define LOG_TRACE(logger, msg) CM_LOG(::cm::log::Level::Trace, logger, msg)
#define LOG_DEBUG(logger, msg) CM_LOG(::cm::log::Level::Debug, logger, msg)
#define LOG_INFO(logger, msg) CM_LOG(::cm::log::Level::Info, logger, msg)
#define LOG_WARN(logger, msg) CM_LOG(::cm::log::Level::Warn, logger, msg)
#define LOG_ERROR(logger, msg) CM_LOG(::cm::log::Level::Error, logger, msg)
