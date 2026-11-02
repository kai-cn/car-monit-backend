#pragma once
// 对应 Java: SLF4J + Logback（LogAspect / BaseController.logger）
//
// 行为：
//   * 控制台 + 文件双写
//   * 文件按大小滚动（默认 50MB，保留 10 个），命名 carmonit.log / carmonit.1.log
//   * 级别过滤：trace/debug/info/warn/error
#include <mutex>
#include <sstream>
#include <string>

namespace cm::log {

enum class Level { Trace = 0, Debug, Info, Warn, Error, Off };

class Logger {
public:
    static Logger& instance();

    void init(const std::string& dir, const std::string& level);
    void setLevel(const std::string& level);

    void write(Level level, const std::string& logger, const std::string& msg);
    bool enabled(Level level) const { return level >= level_; }

private:
    Logger() = default;
    void rotateIfNeeded();

    std::mutex mu_;
    Level level_{Level::Debug};
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
