#include "cm/common/utils/Logger.hpp"

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

void Logger::init(const std::string& dir, const std::string& level) {
    std::lock_guard<std::mutex> lock(mu_);
    dir_ = dir.empty() ? "logs" : dir;
    std::error_code ec;
    std::filesystem::create_directories(dir_, ec);
    file_ = dir_ + "/carmonit.log";
    size_ = 0;
    if (std::filesystem::exists(file_)) size_ = static_cast<long long>(std::filesystem::file_size(file_));
    setLevel(level);
}

void Logger::setLevel(const std::string& level) {
    std::string l = utils::StringUtils::toLower(level);
    if (l == "trace") level_ = Level::Trace;
    else if (l == "debug") level_ = Level::Debug;
    else if (l == "info") level_ = Level::Info;
    else if (l == "warn" || l == "warning") level_ = Level::Warn;
    else if (l == "error") level_ = Level::Error;
    else if (l == "off") level_ = Level::Off;
    else level_ = Level::Debug;
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
    std::lock_guard<std::mutex> lock(mu_);
    std::string ts = utils::DateUtils::formatInZone(utils::DateUtils::nowMillis(), 8 * 3600, "%Y-%m-%d %H:%M:%S");
    auto now = utils::DateUtils::nowMillis();
    int millis = static_cast<int>(((now + 8LL * 3600 * 1000) % 1000 + 1000) % 1000);
    char msbuf[8];
    std::snprintf(msbuf, sizeof(msbuf), ".%03d", millis);

    std::ostringstream line;
    line << ts << msbuf << " [" << levelName(level) << "] " << logger << " - " << msg << "\n";
    std::string s = line.str();

    std::cout << s;
    std::cout.flush();

    if (!file_.empty()) {
        rotateIfNeeded();
        std::ofstream out(file_, std::ios::app | std::ios::binary);
        if (out) {
            out << s;
            out.flush();
            size_ += static_cast<long long>(s.size());
        }
    }
}

} // namespace cm::log
