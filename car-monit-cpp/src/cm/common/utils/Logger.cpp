#include "cm/common/utils/Logger.hpp"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>

#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"

namespace cm::log {

namespace {
const char* levelName(Level l) {
    switch (l) {
        case Level::Trace: return "TRACE";
        case Level::Debug: return "DEBUG";
        case Level::Info: return "INFO";
        case Level::Warn: return "WARN";
        case Level::Error: return "ERROR";
        default: return "OFF";
    }
}
} // namespace

Logger& Logger::instance() {
    static Logger l;
    return l;
}

Logger::~Logger() { shutdown(); }

void Logger::init(const std::string& dir, const std::string& level) {
    std::lock_guard<std::mutex> lock(mu_);
    dir_ = dir.empty() ? "logs" : dir;
    std::error_code ec;
    std::filesystem::create_directories(dir_, ec);
    file_ = dir_ + "/carmonit.log";
    size_ = 0;
    if (std::filesystem::exists(file_)) size_ = static_cast<long long>(std::filesystem::file_size(file_));
    // setLevel 内部不取锁时会与这里重复加锁，直接内联
    std::string l = utils::StringUtils::toLower(level);
    if (l == "trace") level_.store(Level::Trace);
    else if (l == "debug") level_.store(Level::Debug);
    else if (l == "info") level_.store(Level::Info);
    else if (l == "warn" || l == "warning") level_.store(Level::Warn);
    else if (l == "error") level_.store(Level::Error);
    else if (l == "off") level_.store(Level::Off);
    else level_.store(Level::Debug);

    if (!running_) {
        running_ = true;
        worker_ = std::thread([this] { workerLoop(); });
    }
}

void Logger::setLevel(const std::string& level) {
    std::string l = utils::StringUtils::toLower(level);
    if (l == "trace") level_.store(Level::Trace);
    else if (l == "debug") level_.store(Level::Debug);
    else if (l == "info") level_.store(Level::Info);
    else if (l == "warn" || l == "warning") level_.store(Level::Warn);
    else if (l == "error") level_.store(Level::Error);
    else if (l == "off") level_.store(Level::Off);
    else level_.store(Level::Debug);
}

void Logger::rotateIfNeeded() {
    if (size_ < max_size_) return;
    std::error_code ec;
    std::filesystem::remove(dir_ + "/carmonit." + std::to_string(max_files_) + ".log", ec);
    for (int i = max_files_ - 1; i >= 1; --i) {
        std::string from = dir_ + "/carmonit." + std::to_string(i) + ".log";
        std::string to = dir_ + "/carmonit." + std::to_string(i + 1) + ".log";
        if (std::filesystem::exists(from)) std::filesystem::rename(from, to, ec);
    }
    if (std::filesystem::exists(file_)) std::filesystem::rename(file_, dir_ + "/carmonit.1.log", ec);
    size_ = 0;
}

void Logger::write(Level level, const std::string& logger, const std::string& msg) {
    const long long now = utils::DateUtils::nowMillis();
    const std::string ts = utils::DateUtils::formatInZone(now, 8 * 3600, "%Y-%m-%d %H:%M:%S");
    const int millis = static_cast<int>(((now + 8LL * 3600 * 1000) % 1000 + 1000) % 1000);
    char msbuf[8];
    std::snprintf(msbuf, sizeof(msbuf), ".%03d", millis);

    std::ostringstream line;
    line << ts << msbuf << " [" << levelName(level) << "] " << logger << " - " << msg << "\n";
    std::string s = line.str();

    {
        std::lock_guard<std::mutex> lock(mu_);
        if (!running_) {
            // 未 init（例如静态初始化阶段）或已 shutdown：同步写，不能丢
            writeLine(s);
            return;
        }
        const size_t sz = queue_.size();
        if (sz >= queue_cap_) {
            dropped_.fetch_add(1, std::memory_order_relaxed);
            return;
        }
        // Logback AsyncAppender 的 discardingThreshold：空间紧张时先丢低级别
        if (sz + discarding_threshold_ >= queue_cap_ && level < Level::Warn) {
            dropped_.fetch_add(1, std::memory_order_relaxed);
            return;
        }
        queue_.push_back(std::move(s));
    }
    cv_.notify_one();
}

void Logger::workerLoop() {
    for (;;) {
        std::string s;
        unsigned long long dropped = 0;
        {
            std::unique_lock<std::mutex> lk(mu_);
            cv_.wait(lk, [this] { return !queue_.empty() || !running_; });
            if (queue_.empty() && !running_) break;
            dropped = dropped_.exchange(0, std::memory_order_relaxed);
            s = std::move(queue_.front());
            queue_.pop_front();
        }
        // 文件/控制台 I/O 必须在锁外做，否则 write() 会被磁盘拖住
        if (dropped > 0) {
            char buf[112];
            std::snprintf(buf, sizeof(buf), "logger: dropped %llu messages (queue full)\n",
                          static_cast<unsigned long long>(dropped));
            writeLine(buf);
        }
        writeLine(s);
    }
}

void Logger::writeLine(const std::string& line) {
    std::cout << line;
    std::cout.flush();

    if (file_.empty()) return;
    rotateIfNeeded();
    std::ofstream out(file_, std::ios::app | std::ios::binary);
    if (out) {
        out << line;
        out.flush();
        size_ += static_cast<long long>(line.size());
    }
}

void Logger::shutdown() {
    {
        std::lock_guard<std::mutex> lock(mu_);
        if (!running_) return;
        running_ = false;
    }
    cv_.notify_all();
    if (worker_.joinable()) worker_.join();
}

} // namespace cm::log
