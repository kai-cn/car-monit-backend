#pragma once
// 对应 Java: com.ruoyi.manager.service.impl.CarTrackInfoServiceImpl 里那三条
// getCarGeometry* + getTrailDevBO，以及 com.ruoyi.base.service.impl.GeometryServiceImpl
// 的 lxbh_jdwd: 缓存与 com.ruoyi.base.util.LonLatPathsUtils / RoadPathImpl 两条出站调用。
//
// 三条轨迹类端点（PUT /manager/cartrackinfo/changeTrailInfo、
// GET /manager/suspicious/listFileCarNo、GET /manager/suspicious/history/{id}）
// 全部走这里，所以回退链必须一级不差：
//
//   getCarGeometryByPlanNew
//    ├─ Redis sys_config:api_map == "0" ────────────────► getCarGeometryByPlan   [腾讯]
//    ├─ 入/出口站编号任一为空 ───────────────────────────► getCarGeometryByPlan
//    ├─ Redis car_lxgh:<…> 命中 ────────────────────────► [{lxbh, paths}]
//    ├─ 未命中 → roadPathService.getShortestRoadPath(nodeIds)
//    │     ├─ 非 null ─► 写缓存(无 TTL) ─► [{lxbh, paths}]
//    │     └─ null ────► getCarGeometryByPlan      （失败不缓存、不返回空）
//    └─ （判 paths==null 是在缓存读之后做的 ⇒ 缓存里存了空串也不会回退）
//
//   getCarGeometryByPlan
//    ├─ tracks 的 startLonDec/stratLatDec/endLonDec/endLatDec 任一为 null ► getCarGeometry [纯本地桩号]
//    ├─ Redis 命中 ► [{lxbh, paths}]
//    └─ 未命中 → calcLonAndLatPaths(...) 非 null ⇒ 缓存并返回；null ⇒ getCarGeometry
//
// 出站调用一律"吞掉所有异常返回 null"（Java 就是 catch(Exception){return null;}），
// 所以外部服务不可达时表现是**降级到纯本地桩号计算**，不是空数组也不是 500。
// 本机没有 roadPath/腾讯服务，实测走的就是这条降级路径 —— 与 Java 在同环境下的行为一致。
#include <string>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::base {

/** josnList 用引用传进来：getCarGeometry 会往每个 TrailBo 上写 pilenoDec，
 *  而调用方（控制器）把**同一个 list** 交给响应里的 trailList / trailDevCountBO.trailList，
 *  所以这个副作用是响应的一部分，不能内部拷贝掉。 */
class TrailGeometry {
public:
    /** List<Geometry> 的 JSON 形态（每个元素 7 个键，按 Geometry 字段声明序） */
    static Json carGeometryByPlanNew(const Json& tracks, std::vector<Json>& josnList);
    static Json carGeometryByPlan(const Json& tracks, std::vector<Json>& josnList);
    static Json carGeometry(const Json& tracks, std::vector<Json>& josnList);

    /** TrailDevCountBO：{exceptNum, trailDevList, trailList, exceptMsg}
     *  ⚠️ 字段 Java 声明成 `private List<TrailDevBO> TrailDevList;`（首字母大写），
     *     但 Jackson 从 getter 推名字 ⇒ JSON 键是 trailDevList。 */
    static Json trailDevCountBo(const Json& tracks, std::vector<Json>& josnList);

    // ---- 纯函数，单测直接覆盖 ----
    /** pileno 归一化：先 '+'→'.'，再去 ZK / YK / K（顺序照抄）。返回文本给 BigDecimal 用；
     *  非法文本返回 false（Java 在那里抛 NumberFormatException ⇒ 500）。 */
    static bool normalizePileno(const std::string& pileno, std::string& out);
    /** BigDecimal.setScale(4, HALF_UP).intValue()：先四位半进位，再向零截断 */
    static long long scale4ThenTrunc(const std::string& decimalText);
    /** 腾讯 sig() 的拼串（含"值为空也照样留下 & 分隔符"这个 quirk） */
    static std::string txSignatureSource(const std::string& from, const std::string& to,
                                         const std::string& heading, const std::string& waypoints);
};

} // namespace cm::base
