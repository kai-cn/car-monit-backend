#pragma once
// 对应 Java: com.ruoyi.base.util.GpsUtil（WGS-84 ↔ GCJ-02 那部分）
//
// 为什么必须逐字照抄而不是引一个地理库：Geometry.paths 与腾讯路径规划的 waypoints 串
// 都由这里的输出决定，而 Java 用的就是这套经验公式（含 outOfChina 短路）。
// 更关键的是**返回值顺序**：gps84ToGcj02(lat, lon) 返回的是 {lat, lon}，
// getCarGeometryByPlan 拼 waypoints 时按 [0]+","+[1] 直接用，于是 waypoint 串是 "lat,lon"；
// 而 LonLatPathsUtils 最后又把输出交换成 [lon, lat]。两条分支的元素顺序相反 ——
// 这是本文件最容易抄错的地方。
//
// Java 里剩下的 BD-09 系列（gcj02_To_Bd09 / bd09_To_Gcj02 / gps84_To_bd09 / bd09_To_gps84）
// 只被一个注释掉的 main() 用到，移植不复制死代码。
#include <utility>

namespace cm::base {

class GpsUtil {
public:
    static double transformLat(double x, double y);
    static double transformLon(double x, double y);
    /** 超出中国范围直接原样返回，不做偏移 */
    static bool outOfChina(double lat, double lon);
    /** ⚠️ 返回 {lat, lon} */
    static std::pair<double, double> transform(double lat, double lon);
    /** ⚠️ 返回 {lat, lon} */
    static std::pair<double, double> gps84ToGcj02(double lat, double lon);
    /** ⚠️ 返回 {lat, lon} */
    static std::pair<double, double> gcj02ToGps84(double lat, double lon);
};

} // namespace cm::base
