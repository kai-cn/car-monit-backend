// 对应 Java: com.ruoyi.web.controller.monitor.ServerController
// 以及 com.ruoyi.framework.web.domain.Server 及其子组件（Cpu, Mem, Jvm, Sys, SysFileInfo）
#include "cm/web/controller/monitor/ServerController.hpp"

#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#ifdef __linux__
#include <sys/statvfs.h>
#include <unistd.h>
#endif

#include "cm/common/compat/Path.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {

namespace {

/** 对应 Java Arith.round(Arith.mul(value, 100), 2) */
double roundPercent(double value, double total) {
    if (total <= 0) return 0.0;
    double pct = (value / total) * 100.0;
    return std::round(pct * 100.0) / 100.0;
}

/** 对应 Java Arith.div(a, b, scale) */
double div(double a, double b, int scale) {
    if (b == 0) return 0;
    double factor = std::pow(10.0, scale);
    return std::round((a / b) * factor) / factor;
}

/** 对应 Java Arith.mul(a, b) */
double mul(double a, double b) {
    return a * b;
}

/** 对应 Java convertFileSize(long size) */
std::string convertFileSize(long long size) {
    long long kb = 1024;
    long long mb = kb * 1024;
    long long gb = mb * 1024;
    char buf[64];
    if (size >= gb) {
        std::snprintf(buf, sizeof(buf), "%.1f GB", static_cast<double>(size) / gb);
    } else if (size >= mb) {
        double f = static_cast<double>(size) / mb;
        if (f > 100) std::snprintf(buf, sizeof(buf), "%.0f MB", f);
        else std::snprintf(buf, sizeof(buf), "%.1f MB", f);
    } else if (size >= kb) {
        double f = static_cast<double>(size) / kb;
        if (f > 100) std::snprintf(buf, sizeof(buf), "%.0f KB", f);
        else std::snprintf(buf, sizeof(buf), "%.1f KB", f);
    } else {
        std::snprintf(buf, sizeof(buf), "%lld B", size);
    }
    return buf;
}

/** 读取 /proc/stat 获取 CPU 信息（Linux） */
Json getCpuInfo() {
    Json cpu = Json::object();
#ifdef __linux__
    // 读取两次 /proc/stat，间隔 100ms（对应 Java OSHI_WAIT_SECOND = 1000）
    auto readTicks = []() -> std::vector<long long> {
        std::ifstream in("/proc/stat");
        std::string line;
        std::getline(in, line);
        std::istringstream ss(line);
        std::string label;
        ss >> label;
        std::vector<long long> ticks(8, 0);
        for (int i = 0; i < 8 && ss; ++i) ss >> ticks[i];
        return ticks;
    };

    auto prev = readTicks();
    usleep(100000); // 100ms
    auto cur = readTicks();

    long long user = cur[0] - prev[0];
    long long nice = cur[1] - prev[1];
    long long cSys = cur[2] - prev[2];
    long long idle = cur[3] - prev[3];
    long long iowait = cur[4] - prev[4];
    long long irq = cur[5] - prev[5];
    long long softirq = cur[6] - prev[6];
    long long steal = cur[7] - prev[7];
    long long totalCpu = user + nice + cSys + idle + iowait + irq + softirq + steal;

    // 获取 CPU 核心数
    int cpuNum = sysconf(_SC_NPROCESSORS_ONLN);
    if (cpuNum <= 0) cpuNum = 1;

    cpu["cpuNum"] = cpuNum;
    cpu["total"] = roundPercent(totalCpu, totalCpu);
    cpu["sys"] = roundPercent(cSys, totalCpu);
    cpu["used"] = roundPercent(user, totalCpu);
    cpu["wait"] = roundPercent(iowait, totalCpu);
    cpu["free"] = roundPercent(idle, totalCpu);
#else
    cpu["cpuNum"] = 1;
    cpu["total"] = 0;
    cpu["sys"] = 0;
    cpu["used"] = 0;
    cpu["wait"] = 0;
    cpu["free"] = 0;
#endif
    return cpu;
}

/** 读取 /proc/meminfo 获取内存信息（Linux） */
Json getMemInfo() {
    Json mem = Json::object();
#ifdef __linux__
    std::ifstream in("/proc/meminfo");
    std::string line;
    long long total = 0, freeMem = 0, available = 0, buffers = 0, cached = 0;
    while (std::getline(in, line)) {
        if (line.find("MemTotal:") == 0) {
            std::sscanf(line.c_str(), "MemTotal: %lld", &total);
            total *= 1024; // kB -> bytes
        } else if (line.find("MemFree:") == 0) {
            std::sscanf(line.c_str(), "MemFree: %lld", &freeMem);
            freeMem *= 1024;
        } else if (line.find("MemAvailable:") == 0) {
            std::sscanf(line.c_str(), "MemAvailable: %lld", &available);
            available *= 1024;
        } else if (line.find("Buffers:") == 0) {
            std::sscanf(line.c_str(), "Buffers: %lld", &buffers);
            buffers *= 1024;
        } else if (line.find("Cached:") == 0) {
            std::sscanf(line.c_str(), "Cached: %lld", &cached);
            cached *= 1024;
        }
    }
    long long used = total - available;

    double totalGb = div(total, 1024LL * 1024 * 1024, 2);
    double usedGb = div(used, 1024LL * 1024 * 1024, 2);
    double freeGb = div(available, 1024LL * 1024 * 1024, 2);
    double usage = mul(div(used, total, 4), 100);

    mem["total"] = totalGb;
    mem["used"] = usedGb;
    mem["free"] = freeGb;
    mem["usage"] = usage;
#else
    mem["total"] = 0;
    mem["used"] = 0;
    mem["free"] = 0;
    mem["usage"] = 0;
#endif
    return mem;
}

/** 获取 JVM（进程）信息 */
Json getJvmInfo() {
    Json jvm = Json::object();
    // Java: Runtime.getRuntime().totalMemory() / maxMemory() / freeMemory()
    // C++: 读取 /proc/self/status 获取进程内存信息
    long long vmRSS = 0, vmSize = 0;
#ifdef __linux__
    std::ifstream in("/proc/self/status");
    std::string line;
    while (std::getline(in, line)) {
        if (line.find("VmRSS:") == 0) {
            std::sscanf(line.c_str(), "VmRSS: %lld", &vmRSS);
            vmRSS *= 1024; // kB -> bytes
        } else if (line.find("VmSize:") == 0) {
            std::sscanf(line.c_str(), "VmSize: %lld", &vmSize);
            vmSize *= 1024;
        }
    }
#endif

    double totalMb = div(vmRSS, 1024LL * 1024, 2);
    double maxMb = div(vmSize, 1024LL * 1024, 2);
    double freeMb = div(vmSize - vmRSS, 1024LL * 1024, 2);
    double usedMb = div(vmRSS, 1024LL * 1024, 2);
    double usage = mul(div(vmRSS, vmSize, 4), 100);

    jvm["total"] = totalMb;
    jvm["max"] = maxMb;
    jvm["free"] = freeMb;
    jvm["used"] = usedMb;
    jvm["usage"] = usage;
    jvm["name"] = "C++ Runtime"; // Java: ManagementFactory.getRuntimeMXBean().getVmName()
    jvm["version"] = "C++20";    // Java: System.getProperty("java.version")
    jvm["home"] = "/usr/bin";    // Java: System.getProperty("java.home")
    jvm["startTime"] = cm::utils::DateUtils::dateTimeNow();
    jvm["runTime"] = "0天0小时0分钟";
    jvm["inputArgs"] = "[]";

    return jvm;
}

/** 获取系统信息 */
Json getSysInfo() {
    Json sys = Json::object();
#ifdef __linux__
    char hostname[256] = {0};
    gethostname(hostname, sizeof(hostname));
    sys["computerName"] = hostname;

    // 获取 IP（简化：读取 /etc/hostname 或使用 localhost）
    sys["computerIp"] = "127.0.0.1";

    // 获取 OS 信息
    std::string osName, osArch;
    std::ifstream osRelease("/etc/os-release");
    if (osRelease) {
        std::string line;
        while (std::getline(osRelease, line)) {
            if (line.find("PRETTY_NAME=") == 0) {
                osName = line.substr(13);
                // 去掉引号
                if (!osName.empty() && osName.front() == '"') osName = osName.substr(1);
                if (!osName.empty() && osName.back() == '"') osName.pop_back();
                break;
            }
        }
    }
    if (osName.empty()) osName = "Linux";

    // 获取架构
    struct utsname {
        char sysname[65];
        char nodename[65];
        char release[65];
        char version[65];
        char machine[65];
    };
    // 简化：直接使用 uname -m
    FILE* fp = popen("uname -m", "r");
    if (fp) {
        char buf[64] = {0};
        if (fgets(buf, sizeof(buf), fp)) {
            osArch = buf;
            if (!osArch.empty() && osArch.back() == '\n') osArch.pop_back();
        }
        pclose(fp);
    }
    if (osArch.empty()) osArch = "x86_64";

    sys["osName"] = osName;
    sys["osArch"] = osArch;
    sys["userDir"] = cm::compat::fsUtf8(std::filesystem::current_path());
#else
    sys["computerName"] = "localhost";
    sys["computerIp"] = "127.0.0.1";
    sys["osName"] = "Unknown";
    sys["osArch"] = "unknown";
    sys["userDir"] = ".";
#endif
    return sys;
}

/** 获取磁盘信息 */
Json getSysFilesInfo() {
    Json sysFiles = Json::array();
#ifdef __linux__
    // 读取 /proc/mounts 获取挂载点
    std::ifstream in("/proc/mounts");
    std::string line;
    std::vector<std::string> seen;
    while (std::getline(in, line)) {
        std::istringstream ss(line);
        std::string device, mountPoint, fsType;
        ss >> device >> mountPoint >> fsType;

        // 只关注真实文件系统
        if (device.empty() || device[0] != '/') continue;
        if (mountPoint.find("/snap/") == 0) continue;
        if (mountPoint.find("/sys/") == 0) continue;
        if (mountPoint.find("/proc/") == 0) continue;
        if (mountPoint.find("/dev/") == 0) continue;
        if (mountPoint.find("/run/") == 0) continue;

        // 去重
        if (std::find(seen.begin(), seen.end(), mountPoint) != seen.end()) continue;
        seen.push_back(mountPoint);

        struct statvfs stat;
        if (statvfs(mountPoint.c_str(), &stat) != 0) continue;

        long long total = static_cast<long long>(stat.f_blocks) * stat.f_frsize;
        long long freeSpace = static_cast<long long>(stat.f_bavail) * stat.f_frsize;
        long long used = total - freeSpace;
        double usage = mul(div(used, total, 4), 100);

        Json file = Json::object();
        file["dirName"] = mountPoint;
        file["sysTypeName"] = fsType;
        file["typeName"] = device;
        file["total"] = convertFileSize(total);
        file["free"] = convertFileSize(freeSpace);
        file["used"] = convertFileSize(used);
        file["usage"] = usage;
        sysFiles.push_back(file);
    }
#endif
    return sysFiles;
}

} // namespace

void registerServerController(Router& r) {
    // GET /monitor/server
    r.get("/monitor/server", [](RequestContext&) -> cm::http::ApiResponse {
        Json server = Json::object();
        server["cpu"] = getCpuInfo();
        server["mem"] = getMemInfo();
        server["jvm"] = getJvmInfo();
        server["sys"] = getSysInfo();
        server["sysFiles"] = getSysFilesInfo();

        auto a = BaseController::success(server);
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:server:list");
}

} // namespace cm::web
