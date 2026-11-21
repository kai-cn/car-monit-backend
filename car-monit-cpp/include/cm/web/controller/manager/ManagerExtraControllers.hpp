#pragma once
// manager 域里“同构 CRUD + 一点前置条件”的那批端点
//
// 这些接口不需要另写 SQL：Java 侧只是在调用原本的分页查询前先给查询对象塞默认值
// （查不到而不是查全表），或者用一条独立的 group by 统计。
// 列定义复用 scripts/gen_crud_spec.py 暴露的 specCarXxx()。
#include <string>
#include <utility>
#include <vector>

#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web {

void registerManagerExtraControllers(Router& r);

/** 可疑车辆“备份表”查询的 spec 变体：Java 的 selectCarSuspiciousListHistroy 与
 *  selectCarSuspiciousList 的 <if> 条件逐条相同，只有 FROM（car_suspicious_back）
 *  和 order by（t.id）不同，所以不另写一份列定义。
 *  listHistory 与 exportHistory 共用（后者是模板导出，走另一个控制器文件）。 */
const cm::web::crud::Spec& suspiciousHistorySpec();

/** TrailBo（com.ruoyi.base.domain.TrailBo）32 个字段的 JSON 投影：
 *  fastjson2 反序列化成实体再交给 Jackson 输出 ⇒ 多出来的键丢掉、缺的键补 null、顺序按声明序。
 *  changeTrailInfo / listFileCarNo / history/{id} 与 listByCarByTime 共用同一份。 */
Json projectTrailBoJson(const Json& src);

/** ZdataTrailTracksServiceImpl.carTrackQuery（本地 SQL）+ 控制器里 track_josn 展开的那一段。
 *  listByCarByTime 与 listByCarId 走的是同一段 Java 代码，所以共用这一份实现 ——
 *  两处各抄一遍正是这批端点里最容易走形的坑。
 *  query 得是已经绑好的 ZdataTrailTracks 形态：listByCarId 会先把 carNo 兜成 "-1"，
 *  这一个差别不值得再多抄一遍 SQL。
 *  hasRows 判的是 DB 行数而不是 rtnList 非空：Java 判的是 carlist.size() > 0 ⇒
 *  track_josn 为空的行虽然进不了 rtnList，照样算“有数据”，于是远程回退不会触发。 */
struct CarTrackLocal {
    Json rtnList;         // TrailInfo 数组
    long long total{0};   // new PageInfo(carlist).getTotal()
    bool hasRows{false};
};

CarTrackLocal carTrackQueryLocal(RequestContext& ctx, const Json& query);

/** Spring 对 `carSnapShot(TrailBo trailBo)` 的查询参数绑定：只有请求里出现过的键才写入，
 *  数字/布尔属性收到空串时按转换器行为落回 null（String 属性的 "" 则照样是值）。 */
Json bindTrailBoQuery(RequestContext& ctx);

/** Forest `@Query TrailBo` 的拍平（实测抓包）：按声明序、null 省略、BigDecimal 保标度、
 *  布尔是小写文本、嵌套对象转成 JSON 文本、空串渲染成**没有等号**的裸键名。 */
std::vector<std::pair<std::string, std::string>> flattenTrailBoQuery(const Json& bo);

} // namespace cm::web
