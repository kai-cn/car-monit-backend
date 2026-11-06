// GpsUtil 的移植，公式与常数逐字照抄 Java（见 hpp 顶部关于返回顺序的说明）。
#include "cm/base/util/GpsUtil.hpp"

#include <cmath>

namespace cm::base {

namespace {
// Java: pi = 3.1415926535897932384626 / a = 6378245.0 / ee = 0.00669342162296594323
// 这几个字面量在 double 上的取整结果与 Java 完全一致（同为 IEEE-754 binary64）。
constexpr double PI = 3.1415926535897932384626;
constexpr double A = 6378245.0;
constexpr double EE = 0.00669342162296594323;
} // namespace

double GpsUtil::transformLat(double x, double y) {
    double ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y +
                 0.2 * std::sqrt(std::abs(x));
    ret += (20.0 * std::sin(6.0 * x * PI) + 20.0 * std::sin(2.0 * x * PI)) * 2.0 / 3.0;
    ret += (20.0 * std::sin(y * PI) + 40.0 * std::sin(y / 3.0 * PI)) * 2.0 / 3.0;
    ret += (160.0 * std::sin(y / 12.0 * PI) + 320 * std::sin(y * PI / 30.0)) * 2.0 / 3.0;
    return ret;
}

double GpsUtil::transformLon(double x, double y) {
    double ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * std::sqrt(std::abs(x));
    ret += (20.0 * std::sin(6.0 * x * PI) + 20.0 * std::sin(2.0 * x * PI)) * 2.0 / 3.0;
    ret += (20.0 * std::sin(x * PI) + 40.0 * std::sin(x / 3.0 * PI)) * 2.0 / 3.0;
    ret += (150.0 * std::sin(x / 12.0 * PI) + 300.0 * std::sin(x / 30.0 * PI)) * 2.0 / 3.0;
    return ret;
}

bool GpsUtil::outOfChina(double lat, double lon) {
    if (lon < 72.004 || lon > 137.8347) return true;
    if (lat < 0.8293 || lat > 55.8271) return true;
    return false;
}

std::pair<double, double> GpsUtil::transform(double lat, double lon) {
    if (outOfChina(lat, lon)) return {lat, lon};
    double dLat = transformLat(lon - 105.0, lat - 35.0);
    double dLon = transformLon(lon - 105.0, lat - 35.0);
    const double radLat = lat / 180.0 * PI;
    double magic = std::sin(radLat);
    magic = 1 - EE * magic * magic;
    const double sqrtMagic = std::sqrt(magic);
    dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI);
    dLon = (dLon * 180.0) / (A / sqrtMagic * std::cos(radLat) * PI);
    return {lat + dLat, lon + dLon};
}

std::pair<double, double> GpsUtil::gps84ToGcj02(double lat, double lon) {
    // 与 transform 是同一套公式（Java 里就是复制粘贴的两份），照抄两份而不是合并：
    // 一旦哪天 Java 只改其中一个，这里不会跟着漂移。
    if (outOfChina(lat, lon)) return {lat, lon};
    double dLat = transformLat(lon - 105.0, lat - 35.0);
    double dLon = transformLon(lon - 105.0, lat - 35.0);
    const double radLat = lat / 180.0 * PI;
    double magic = std::sin(radLat);
    magic = 1 - EE * magic * magic;
    const double sqrtMagic = std::sqrt(magic);
    dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI);
    dLon = (dLon * 180.0) / (A / sqrtMagic * std::cos(radLat) * PI);
    return {lat + dLat, lon + dLon};
}

std::pair<double, double> GpsUtil::gcj02ToGps84(double lat, double lon) {
    const auto gps = transform(lat, lon);
    return {lat * 2 - gps.first, lon * 2 - gps.second};
}

} // namespace cm::base
