#pragma once
// manager 域几个控制器共用的"读 car_info / car_suspicious + 刷 Redis 车辆缓存"的小工具。
//
// 为什么单独立一个文件而不是各写一份：`updateRedisCarList()` 在 Java 里被
// saveCarInfo / doImport / deleteCarInfoById / cherkCarSuspicious 好几条路径调用，
// 而它的输出形态是有主的 —— Redis 里必须是 fastjson2 WriteClassName 那一套
// （见 FINAL_DIFFERENCES §2 契约 23）。各写一份迟早会有一份写成严格 JSON，
// 然后表现为"Java 读到 JSONObject 崩掉"这种只有混跑才会踩到的坑。
#include <string>

#include "cm/common/utils/JsonUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web {

/** 查询失败直接抛（Java 侧 MyBatis 抛 BadSqlGrammarException → 500，而不是"空结果"） */
cm::db::Result mustRunSql(const std::string& sql);

/** selectCarInfoList(CarInfo{carNo})：与 /manager/carinfo/list 同一条语句，
 *  所以"异常流水已全部补缴 ⇒ 这辆车查不到"的那个 not exists 照样生效。
 *  carNo 为空串时就是 selectCarInfoList(new CarInfo())。 */
cm::db::Result selectCarInfoListByNo(const std::string& carNo);

/** selectCarInfoList(new CarInfo()) 全量 */
inline cm::db::Result selectAllCarInfo() { return selectCarInfoListByNo(std::string()); }

/** 对应 CarInfoServiceImpl.updateRedisCarList()：两条缓存，都不设过期时间 */
void updateRedisCarList();

/** 对应 selectCarSuspiciousById / selectCarSuspiciousHistoryById：
 *  与列表那条语句的差别只有一列 —— by-id 多带 t.track_josn，且没有 del_flag 过滤。
 *  查不到返回 Json(nullptr)（Java 那边是返回 null，由调用方决定是 NPE 还是空响应）。 */
Json suspiciousByIdRow(const cm::web::crud::Spec& spec, const std::string& table,
                       const std::string& id);

} // namespace cm::web
