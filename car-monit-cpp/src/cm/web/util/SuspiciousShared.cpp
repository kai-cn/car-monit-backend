// 见 SuspiciousShared.hpp 顶部说明。实现是从 ManagerImportControllers.cpp /
// ManagerTrailInfoControllers.cpp 里搬过来的，两处改为调用这里，避免同一份缓存形态写两遍。
#include "cm/web/util/SuspiciousShared.hpp"

#include <string>
#include <vector>

#include "cm/common/exception/Exceptions.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"

namespace cm::web {

using cm::db::Db;

cm::db::Result mustRunSql(const std::string& sql) {
    cm::db::Result res;
    if (!Db::instance().query(sql, res)) {
        throw cm::exception::ServiceException("数据访问异常，SQL 执行失败: " + sql.substr(0, 200));
    }
    return res;
}

cm::db::Result selectCarInfoListByNo(const std::string& carNo) {
    const cm::web::crud::Spec& spec = cm::web::crud::specCarInfo();
    Json q = Json::object();
    if (!carNo.empty()) q["carNo"] = Json(carNo);
    return mustRunSql(cm::web::crud::selectSqlOf(
        spec, cm::web::crud::buildWhere(spec, q), " ORDER BY " + spec.orderBy));
}

void updateRedisCarList() {
    const cm::web::crud::Spec& spec = cm::web::crud::specCarInfo();
    const cm::db::Result res = selectCarInfoListByNo(std::string());
    cm::redis::RedisCache& cache = cm::redis::RedisCache::instance();
    cache.set("car_list", cm::web::crud::fastJson2CachedArray(
                              spec, res.rows, "com.ruoyi.manager.domain.CarInfo"));

    std::string jc = "[";
    for (size_t i = 0; i < res.rows.size(); ++i) {
        if (i) jc += ",";
        // CarVO 只赋了 carId/carNo，其余属性是 null ⇒ fastjson2 不写出来
        jc += "{\"@type\":\"com.ruoyi.base.domain.CarVO\",\"carId\":" +
              Json(res.rows[i].str("id")).dump() + ",\"carNo\":" +
              Json(res.rows[i].str("car_no")).dump() + "}";
    }
    cache.set("car_list_jc", jc + "]");
}

Json suspiciousByIdRow(const cm::web::crud::Spec& spec, const std::string& table,
                       const std::string& id) {
    const std::string sql =
        "SELECT " + spec.selectColumns() + ", t.track_josn FROM " + table + " t WHERE t.id = " +
        Db::lit(id);
    const cm::db::Result res = mustRunSql(sql);
    if (res.rows.empty()) return Json(nullptr);
    return cm::web::crud::rowToJson(spec, res.rows[0]);
}

} // namespace cm::web
