// 可疑车辆写侧接口。对应 Java:
//   CarSuspiciousController#check → CarSuspiciousServiceImpl.cherkCarSuspicious（第 218-378 行）
// 外加 CarInfoServiceImpl.updateRedisCarList / CarSuspiciousCheckServiceImpl.saveBatch /
//     CarExceptRecordServiceImpl.saveBatch。
//
// @Transactional(rollbackFor = Exception.class) 覆盖整个方法，所以"先物理删除、后面才失败"
// 的组合在 Java 里是回滚的 —— C++ 必须在每个正常返回路径显式 commit，异常路径靠析构回滚。
//
// 需要照抄的行为：
//   * 两条删除是**物理 delete**（不是 del_flag='1'），而且发生在后续校验之前；
//     所以 isExcept!="1" 且 checkList 为 null 时会先删空、再在 for-each 上 NPE ⇒ 500 回滚。
//   * 判重用的是 `escapedType.indexOf(addCheckType) > -1` —— 子串判断，不是集合判断，
//     于是码 "1" 会因为已积累的 "10," 里含 "1" 而被跳过；addCheckType 为空串时
//     indexOf("")==0 也永远跳过。算出来的 escapedType 其实**没人用**（updatebo 用的是请求里的值）。
//   * isExcept=="1" 才走"补建重点车辆 + 批量落库"那一整段；isExcept 是别的值（含 "0"/null）
//     时 checkList 照样被遍历算 escapedAmount，但一条核实/异常流水都不写。
//   * isExcept=="0" 时 exceptFileIds 被强制写成空串。
//   * car_info 是否存在走的是 selectCarInfoList(carNo) ⇒ 那条 not exists 过滤同样生效，
//     已缴清的车会被当成"没有车"再插一行。
#include "cm/web/controller/manager/ManagerSuspiciousWriteControllers.hpp"

#include <algorithm>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/JsonUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/utils/crypto/Digest.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/system/mapper/SysDictDataMapper.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"
#include "cm/web/util/SuspiciousShared.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::constant::Constants;
using cm::utils::CommonUtil;
using cm::utils::DateUtils;
using cm::utils::StringUtils;

/** ISysDictDataServiceImpl.selectDictDataLaleMap：label → value。
 *  ⚠️ Collectors.toMap 遇重复 label 抛 IllegalStateException ⇒ 整个请求 500。 */
std::map<std::string, std::string> dictLabelToValue(const std::string& dictType) {
    cm::domain::SysDictData q;
    q.dictType = dictType;
    std::map<std::string, std::string> out;
    for (const auto& d : cm::system::mapper::SysDictDataMapper::selectDictDataList(q)) {
        const std::string label = d.dictLabel ? *d.dictLabel : std::string();
        const std::string value = d.dictValue ? *d.dictValue : std::string();
        auto it = out.find(label);
        if (it != out.end()) {
            throw cm::exception::ServiceException("Duplicate key " + label +
                                                  " (attempted merging values " + it->second +
                                                  " and " + value + ")");
        }
        out.emplace(label, value);
    }
    return out;
}

/** syncSuspiciousCar 里那串 envehicletype → car_vehicle 的 else-if 链。
 *  与 exceptrecord 导入那份**不一样**：这里落到 else 时留空串（不写车种），
 *  而导入那边兜成 "99"。 */
std::string vehicleOfEnVehicleType(const std::string& t) {
    if (t == "1" || t == "2" || t == "3" || t == "4") return "1";
    if (t == "11" || t == "12" || t == "13" || t == "14" || t == "15" || t == "16") return "2";
    if (t == "21" || t == "22" || t == "23" || t == "24" || t == "25" || t == "26") return "3";
    return "";
}

std::string optText(const Json& o, const char* key) {
    if (!o.is_object() || !o.contains(key) || o[key].is_null()) return "";
    const Json& v = o[key];
    return v.is_string() ? v.get<std::string>() : v.dump();
}

bool hasVal(const Json& o, const char* key) {
    return o.is_object() && o.contains(key) && !o[key].is_null();
}

/** MyBatis-Plus 的 insert：只写非 null 属性。
 *  pairs 里 value 为空串表示"这一列不参与 SQL"（调用方用 hasVal 判过）。 */
std::string mpInsert(const std::string& table,
                     const std::vector<std::pair<std::string, std::string>>& pairs) {
    std::string names, vals;
    for (const auto& c : pairs) {
        if (c.second.empty()) continue;
        if (!names.empty()) { names += ", "; vals += ", "; }
        names += c.first;
        vals += c.second;
    }
    return "INSERT INTO " + table + " (" + names + ") VALUES (" + vals + ")";
}

/** (列名, 字面量) —— 属性为 null 时返回空串，让 mpInsert 跳过这一列 */
std::pair<std::string, std::string> colText(const char* column, const Json& o, const char* key) {
    if (!hasVal(o, key)) return {column, std::string()};
    const Json& v = o[key];
    if (v.is_number_integer()) return {column, v.dump()};
    if (v.is_number()) return {column, v.dump()};
    return {column, cm::db::bind(v.is_string() ? v.get<std::string>() : v.dump())};
}

/** car_suspicious_check 的一行（实体属性名 → 列名） */
std::string buildCheckInsert(const Json& e) {
    std::vector<std::pair<std::string, std::string>> pairs = {
        colText("id", e, "id"),
        colText("car_id", e, "carId"),
        colText("car_no", e, "carNo"),
        colText("suspicous_flag", e, "suspicousFlag"),
        colText("escaped_type", e, "escapedType"),
        colText("charge_amount", e, "chargeAmount"),
        colText("total_amount", e, "totalAmount"),
        colText("dif_amount", e, "difAmount"),
        colText("attachments", e, "attachments"),
        colText("status", e, "status"),
        colText("remark", e, "remark"),
        colText("back_col1", e, "backCol1"),
        colText("back_col2", e, "backCol2"),
        colText("create_by", e, "createBy"),
        colText("create_time", e, "createTime"),
        colText("eps_id", e, "epsId"),
        colText("tenant_id", e, "tenantId"),
    };
    return mpInsert("car_suspicious_check", pairs);
}

/** car_except_record 的一行 */
std::string buildExceptInsert(const Json& e) {
    std::vector<std::pair<std::string, std::string>> pairs = {
        colText("id", e, "id"),
        colText("car_id", e, "carId"),
        colText("car_no", e, "carNo"),
        colText("car_type", e, "carType"),
        colText("car_vehicle", e, "carVehicle"),
        colText("car_num", e, "carNum"),
        colText("pass_type", e, "passType"),
        colText("in_station_id", e, "inStationId"),
        colText("in_station", e, "inStation"),
        colText("in_time", e, "inTime"),
        colText("out_station_id", e, "outStationId"),
        colText("out_station", e, "outStation"),
        colText("out_time", e, "outTime"),
        colText("total_amount", e, "totalAmount"),
        colText("charge_amount", e, "chargeAmount"),
        colText("dif_amount", e, "difAmount"),
        colText("escaped_type", e, "escapedType"),
        colText("status", e, "status"),
        colText("create_by", e, "createBy"),
        colText("create_time", e, "createTime"),
        colText("eps_id", e, "epsId"),
        colText("tenant_id", e, "tenantId"),
    };
    return mpInsert("car_except_record", pairs);
}

// ---------------------------------------------------------------- PUT /manager/suspicious/check

cm::http::ApiResponse checkSuspicious(RequestContext& ctx) {
    Json body = cm::parse_json(ctx.req.body);
    cm::db::Transaction tx;   // @Transactional(rollbackFor = Exception.class)

    const std::string carId = CommonUtil::isNull(optText(body, "id"));
    if (StringUtils::isBlank(carId)) {
        return BaseController::ok(AjaxResult::error("可疑车俩不存在！"));
    }

    const cm::web::crud::Spec& spec = cm::web::crud::specCarSuspicious();
    const Json rtnVo = suspiciousByIdRow(spec, "car_suspicious", carId);
    if (rtnVo.is_null() || StringUtils::isBlank(optText(rtnVo, "id"))) {
        return BaseController::ok(AjaxResult::error("可疑车俩不存在！"));
    }
    if (CommonUtil::isNull(optText(rtnVo, "status")) == "1") {
        return BaseController::ok(AjaxResult::error("可疑车俩异常流水已追缴！"));
    }

    const std::string carNo = CommonUtil::isNull(optText(body, "carNo"));
    const Json checkList = hasVal(body, "checkList") ? body["checkList"] : Json(nullptr);
    const std::string isExcept = CommonUtil::isNull(optText(body, "isExcept"));
    if (isExcept == "1" && (!checkList.is_array() || checkList.empty())) {
        return BaseController::ok(AjaxResult::error("车辆逃费类型列表不能为空！"));
    }

    // ⚠️ 物理删除，且发生在后面那个可能 NPE 的循环之前 —— 靠事务回滚保住一致性
    mustRunSql("delete from car_suspicious_check where car_id = " + cm::db::bind(carId));
    mustRunSql("delete from car_except_record where car_id = " + cm::db::bind(carId));

    const long long userId = cm::security::SecurityUtils::getUserId();
    const long long epsId = cm::security::SecurityUtils::getEpsId();

    std::string escapedType;
    double escapedAmount = 0.0;   // BigDecimal.ZERO 起步，只用于写 car_info.decimal(19,2)
    if (checkList.is_null()) {
        // Java: for (CarSuspiciousCheck check : checkList) 对 null 直接 NPE ⇒ 500
        throw cm::exception::NullPointerException();
    }
    for (const auto& check : checkList) {
        const std::string addCheckType = CommonUtil::isNull(optText(check, "escapedType"));
        // 子串判重："1" 会因为已积累的 "10," 含 '1' 而被当成重复
        if (escapedType.find(addCheckType) == std::string::npos) {
            escapedType += addCheckType + ",";
        }
        if (hasVal(check, "difAmount")) escapedAmount += cm::jdouble(check, "difAmount");
    }
    escapedType = CommonUtil::deleteEnd(escapedType);
    (void)escapedType;   // 算完不用 —— Java 里 updatebo 取的是请求上的 escapedType

    if (isExcept == "1") {
        cm::db::Result cars = selectCarInfoListByNo(carNo);
        if (cars.rows.empty()) {
            // 与 saveCarInfo 的新增分支同一套列；这里 Java 是直接 new 一个 CarInfo 插
            std::vector<std::pair<std::string, std::string>> col = {
                {"id", cm::db::bind(cm::utils::simpleUuid())},
                {"del_flag", Db::lit("0")},
                {"eps_id", std::to_string(epsId)},
                {"create_by", std::to_string(userId)},
                {"create_time", cm::db::bind(DateUtils::getTime())},
                {"update_by", std::to_string(userId)},
                {"update_time", cm::db::bind(DateUtils::getTime())},
                {"car_no", cm::db::bind(carNo)},
                {"car_type", hasVal(body, "carType") ? cm::db::bind(optText(body, "carType")) : std::string()},
                {"car_num", hasVal(body, "carNum") ? std::to_string(cm::jlong(body, "carNum")) : std::string()},
                {"car_vehicle", hasVal(body, "carVehicle") ? cm::db::bind(optText(body, "carVehicle")) : std::string()},
                {"plate_color", hasVal(body, "plateColor") ? cm::db::bind(optText(body, "plateColor")) : std::string()},
                {"escaped_type", hasVal(body, "escapedType") ? cm::db::bind(optText(body, "escapedType")) : std::string()},
                {"escaped_amount", cm::db::bind(escapedAmount)},
            };
            std::string names, vals;
            for (const auto& c : col) {
                if (c.second.empty()) continue;
                if (!names.empty()) { names += ", "; vals += ", "; }
                names += c.first;
                vals += c.second;
            }
            mustRunSql("INSERT INTO car_info (" + names + ") VALUES (" + vals + ")");
        }

        std::vector<std::string> checkInserts, exceptInserts;
        for (const auto& check : checkList) {
            Json one = check;
            one["carId"] = Json(carId);
            one["carNo"] = Json(carNo);
            one["suspicousFlag"] = Json(optText(body, "isExcept"));
            if (!hasVal(one, "id")) one["id"] = Json(cm::utils::simpleUuid());
            // BasePlusEntity 的 insertFill
            if (!hasVal(one, "createTime")) one["createTime"] = Json(DateUtils::getTime());
            if (!hasVal(one, "createBy")) one["createBy"] = Json(userId);
            if (!hasVal(one, "epsId")) one["epsId"] = Json(epsId);
            checkInserts.push_back(buildCheckInsert(one));

            Json rec = Json::object();
            rec["id"] = Json(cm::utils::simpleUuid());
            rec["carId"] = Json(carId);
            rec["carNo"] = Json(carNo);
            for (const char* k : {"carType", "carVehicle", "carNum"}) {
                if (hasVal(body, k)) rec[k] = body[k];
            }
            for (const char* k : {"passType", "inStationId", "inStation", "inTime",
                                  "gantryStationId", "gantrytStation", "gantryTime"}) {
                if (hasVal(rtnVo, k)) rec[k] = rtnVo[k];
            }
            // ⚠️ 出口那一侧取的是**门架**三列，列名也跟着换成 out_station_id/out_station/out_time
            if (hasVal(rtnVo, "gantryStationId")) rec["outStationId"] = rtnVo["gantryStationId"];
            if (hasVal(rtnVo, "gantrytStation")) rec["outStation"] = rtnVo["gantrytStation"];
            if (hasVal(rtnVo, "gantryTime")) rec["outTime"] = rtnVo["gantryTime"];
            rec["status"] = Json("0");
            for (const char* k : {"totalAmount", "chargeAmount", "difAmount", "escapedType"}) {
                if (hasVal(check, k)) rec[k] = check[k];
            }
            rec["createTime"] = Json(DateUtils::getTime());
            rec["createBy"] = Json(userId);
            rec["epsId"] = Json(epsId);
            exceptInserts.push_back(buildExceptInsert(rec));
        }
        for (const auto& s : checkInserts) mustRunSql(s);
        for (const auto& s : exceptInserts) mustRunSql(s);
    }

    // 修改状态已核实：updateById 只写非 null 属性
    std::vector<std::pair<std::string, std::string>> set = {
        {"check_status", Db::lit("1")},
        {"is_except", hasVal(body, "isExcept") ? cm::db::bind(optText(body, "isExcept")) : std::string()},
        {"except_remark", hasVal(body, "exceptRemark") ? cm::db::bind(optText(body, "exceptRemark")) : std::string()},
        {"except_file_ids", hasVal(body, "exceptFileIds") ? cm::db::bind(optText(body, "exceptFileIds")) : std::string()},
        {"pass_type", hasVal(body, "passType") ? cm::db::bind(optText(body, "passType")) : std::string()},
        {"plate_color", hasVal(body, "plateColor") ? cm::db::bind(optText(body, "plateColor")) : std::string()},
        {"car_no", cm::db::bind(carNo)},
        {"car_type", hasVal(body, "carType") ? cm::db::bind(optText(body, "carType")) : std::string()},
        {"car_vehicle", hasVal(body, "carVehicle") ? cm::db::bind(optText(body, "carVehicle")) : std::string()},
        {"car_num", hasVal(body, "carNum") ? std::to_string(cm::jlong(body, "carNum")) : std::string()},
        {"escaped_type", hasVal(body, "escapedType") ? cm::db::bind(optText(body, "escapedType")) : std::string()},
        {"remark", hasVal(body, "remark") ? cm::db::bind(optText(body, "remark")) : std::string()},
    };
    if (isExcept == "0") {
        // setExceptFileIds("") —— 空串不是 null，照样进 SET
        for (auto& p : set) {
            if (p.first == "except_file_ids") p.second = cm::db::bind(std::string());
        }
    }
    std::string sets;
    for (const auto& p : set) {
        if (p.second.empty()) continue;
        if (!sets.empty()) sets += ", ";
        sets += p.first + " = " + p.second;
    }
    if (!sets.empty()) {
        mustRunSql("UPDATE car_suspicious SET " + sets + " WHERE id = " + cm::db::bind(carId) +
                   " AND del_flag = '0'");
    }

    updateRedisCarList();
    tx.commit();
    return BaseController::ok(AjaxResult::success("操作成功！", Json(optText(body, "id"))));
}

// ------------------------------------------------ POST /manager/suspicious/syncSuspiciousCarTask

/** fastjson2 `JSON.toJSON(x)+""` 的形态：对象键**按名字排序**、null 整个省略。
 *  这个值要写进 car_suspicious.track_josn 列，所以排序差一个字就算数据不一致。
 *  ⚠️ 近似之处：嵌套的 Ods* BO 这里按"原样透传"处理，Java 是先反序列化成那个类型再写，
 *     未声明的键会被丢掉；实测真实数据里这些键从未出现。 */
Json sortedNoNulls(const Json& v) {
    if (v.is_array()) {
        Json out = Json::array();
        for (const auto& e : v) out.push_back(sortedNoNulls(e));
        return out;
    }
    if (!v.is_object()) return v;
    std::vector<std::string> keys;
    for (auto it = v.begin(); it != v.end(); ++it) {
        if (it.value().is_null()) continue;
        keys.push_back(it.key());
    }
    std::sort(keys.begin(), keys.end());
    Json out = Json::object();
    for (const auto& k : keys) out[k] = sortedNoNulls(v[k]);
    return out;
}

/** 白名单缓存：对应 CarWhiteInfoServiceImpl.getRedisCarWhiteList() */
std::set<std::string> whiteCarNos() {
    std::vector<cm::db::Row> rows;
    if (auto cached = cm::redis::RedisCache::instance().get("white_car_list");
        cached && !cached->empty()) {
        // 缓存里是 fastjson2 形态，直接读 car_no 这一列名（CarWhiteInfo 的 JSON 键是 carNo）
        Json j = cm::utils::parse_cached_json(*cached);
        std::set<std::string> out;
        if (j.is_array()) {
            for (const auto& e : j) {
                if (e.is_object() && e.contains("carNo") && !e["carNo"].is_null()) {
                    out.insert(CommonUtil::isNull(e["carNo"].is_string()
                                                      ? e["carNo"].get<std::string>()
                                                      : e["carNo"].dump()));
                }
            }
        }
        return out;
    }
    const cm::web::crud::Spec& spec = cm::web::crud::specCarWhiteInfo();
    for (const auto& row : mustRunSql(cm::web::crud::selectSqlOf(
             spec, cm::web::crud::buildWhere(spec, Json::object()),
             spec.orderBy.empty() ? std::string() : " ORDER BY " + spec.orderBy)).rows) {
        rows.push_back(row);
    }
    std::string cacheJson = "[";
    std::set<std::string> out;
    for (size_t i = 0; i < rows.size(); ++i) {
        if (i) cacheJson += ",";
        cacheJson += "{\"@type\":\"com.ruoyi.manager.domain.CarWhiteInfo\"";
        for (const char* k : {"carNo", "remark", "status"}) {
            (void)k;
        }
        const std::string no = CommonUtil::isNull(rows[i].str("car_no"));
        out.insert(no);
        cacheJson += ",\"carNo\":" + Json(rows[i].str("car_no")).dump() + "}";
    }
    cacheJson += "]";
    cm::redis::RedisCache::instance().set("white_car_list", cacheJson);
    return out;
}

/** 对应 CarInfoServiceImpl.getRedisCarList()：命中就用缓存，否则回源并写回（不设 TTL）。 */
std::map<std::string, cm::db::Row> carInfoByPlate() {
    cm::db::Result res;
    if (auto cached = cm::redis::RedisCache::instance().get("car_list");
        cached && !cached->empty()) {
        Json j = cm::utils::parse_cached_json(*cached);
        // 缓存形态是 JSON，转回"按列名取值"太绕，这里直接用 Json 行集
        std::map<std::string, cm::db::Row> out;
        if (j.is_array()) {
            for (const auto& e : j) {
                std::vector<std::string> cols;
                std::vector<std::optional<std::string>> vals;
                for (auto it = e.begin(); it != e.end(); ++it) {
                    cols.push_back(it.key());
                    vals.push_back(it.value().is_null()
                                       ? std::nullopt
                                       : std::optional<std::string>(
                                             it.value().is_string()
                                                 ? it.value().get<std::string>()
                                                 : it.value().dump()));
                }
                cm::db::Row row(std::move(cols), std::move(vals));
                out[CommonUtil::isNull(row.str("carNo"))] = std::move(row);
            }
        }
        return out;
    }
    res = selectCarInfoListByNo(std::string());
    cm::redis::RedisCache::instance().set(
        "car_list", cm::web::crud::fastJson2CachedArray(cm::web::crud::specCarInfo(), res.rows,
                                                        "com.ruoyi.manager.domain.CarInfo"));
    std::map<std::string, cm::db::Row> out;
    for (const auto& row : res.rows) out[CommonUtil::isNull(row.str("car_no"))] = row;
    return out;
}

/** 从 car_list 缓存/库里取某个属性的文本（缓存那一路键名是驼峰，回源那一路是列名） */
std::string carAttr(const cm::db::Row& row, const char* jsonKey, const char* column) {
    auto v = row.get(jsonKey);
    if (!v) v = row.get(column);
    return v ? CommonUtil::isNull(*v) : std::string();
}

std::string tsText(const Json& o, const char* key) {
    if (!o.is_object() || !o.contains(key) || o[key].is_null()) return "";
    const Json& v = o[key];
    if (v.is_number()) {
        return DateUtils::formatMillis(static_cast<long long>(v.get<double>()),
                                       DateUtils::YYYY_MM_DD_HH_MM_SS);
    }
    return CommonUtil::isNull(v.is_string() ? v.get<std::string>() : v.dump());
}

/** CarSuspiciousServiceImpl.syncSuspiciousCar("task", list)。
 *  addFlag 参数照常实现：控制器传 "task"，Java 里那个 redis 分支因此不生效，
 *  但 **redisCache.keys(car_uspicious+yyyyMMdd+"*") 仍然会真的执行一次**（在判分支之前），
 *  所以这条 KEYS 扫描不是死代码，去掉它就是不一致。 */
bool syncSuspiciousCar(const std::string& addFlag, const Json& paraTrailInfoList,
                       std::string& errMsg) {
    const long long userId = 1L;   // Java 里写死 userId = 1L，不是当前登录人
    std::set<std::string> white = whiteCarNos();

    const std::string today = DateUtils::formatMillis(DateUtils::nowMillis(), "yyyyMMdd");
    const auto keys = cm::redis::RedisCache::instance().keys(
        std::string(Constants::car_uspicious) + today + "*");
    Json trailInfoList = paraTrailInfoList;
    if (CommonUtil::isNull(addFlag) == "redis") {
        trailInfoList = Json::array();
        for (const auto& k : keys) {
            if (auto cached = cm::redis::RedisCache::instance().get(k); cached) {
                trailInfoList.push_back(cm::utils::parse_cached_json(*cached));
            }
        }
    }
    // ⚠️ Java 紧接着就 trailInfoList = paraTrailInfoList; —— 上面一整段的结果被丢掉。
    //    也就是说 redis 分支只会多跑一次 KEYS + 若干次 GET，对输出没有任何影响。
    trailInfoList = paraTrailInfoList;

    auto carMap = carInfoByPlate();
    const auto plateColorMap = dictLabelToValue("plate_color");

    // 列名 ← CarSuspicious 的属性；MP saveBatch/updateById 都只写非 null。
    // 这份顺序决定 SQL 里的列序，漏一个就等于那一列根本不写（id 漏过一次：
    // MySQL 直接报 "Field 'id' doesn't have a default value"）。
    const std::vector<std::pair<const char*, const char*>> orderedCols = {
        {"id", "id"},                  {"track_id", "track_id"},
        {"track_josn", "track_josn"},  {"back_col1", "back_col1"},
        {"car_no", "car_no"},          {"plate_color", "plate_color"},
        {"car_type", "car_type"},      {"car_vehicle", "car_vehicle"},
        {"car_num", "car_num"},        {"pass_type", "pass_type"},
        {"in_station_id", "in_station_id"}, {"in_station", "in_station"},
        {"in_time", "in_time"},        {"out_station_id", "out_station_id"},
        {"out_station", "out_station"}, {"out_time", "out_time"},
        {"gantry_station_id", "gantry_station_id"}, {"gantryt_station", "gantryt_station"},
        {"gantry_time", "gantry_time"}, {"out_gantry_station_id", "out_gantry_station_id"},
        {"out_gantryt_station", "out_gantryt_station"}, {"out_gantry_time", "out_gantry_time"},
        {"escaped_type", "escaped_type"}, {"remark", "remark"},
        {"track_names", "track_names"}, {"is_except", "is_except"},
        {"status", "status"},           {"create_by", "create_by"},
        {"create_time", "create_time"}, {"update_by", "update_by"},
        {"update_time", "update_time"},
    };
    struct Row {
        std::string id;
        std::map<std::string, std::string> col;
    };
    std::vector<Row> addList, updList;

    if (!trailInfoList.is_array()) return true;
    for (const auto& trailInfo : trailInfoList) {
        const Json tracks = trailInfo.contains("tracks") ? trailInfo["tracks"] : Json(nullptr);
        if (!tracks.is_object()) continue;
        const std::string carNo = CommonUtil::isNull(jstr(tracks, "plateKey"));
        const std::string trailUUid = CommonUtil::isNull(jstr(tracks, "uuid"));
        if (StringUtils::isBlank(carNo) || StringUtils::isBlank(trailUUid)) continue;
        if (white.count(carNo)) continue;             // 白名单不生成
        const Json josnList = trailInfo.contains("trailList") ? trailInfo["trailList"] : Json(nullptr);
        if (!josnList.is_array() || josnList.empty()) continue;

        Row row;
        std::string devCodes;
        Json queryQ = Json::object();
        queryQ["carNo"] = Json(carNo);
        queryQ["trackId"] = Json(trailUUid);
        const cm::web::crud::Spec& susSpec = cm::web::crud::specCarSuspicious();
        const auto queryList = mustRunSql(cm::web::crud::selectSqlOf(
            susSpec, cm::web::crud::buildWhere(susSpec, queryQ),
            " ORDER BY " + susSpec.orderBy)).rows;
        std::string checkStatus = "0";
        if (!queryList.empty()) {
            row.id = queryList[0].str("id");
            checkStatus = CommonUtil::isNull(queryList[0].str("check_status"));
        }
        row.col["track_id"] = cm::db::bind(trailUUid);
        row.col["track_josn"] = cm::db::bind(sortedNoNulls(trailInfo).dump());
        if (!tsText(tracks, "escapedTfcj").empty()) row.col["back_col1"] = cm::db::bind(jstr(tracks, "escapedTfcj"));

        if (checkStatus == "1") {
            // 已核实的什么都不改（Java 那里是一个空的 if 块）
            continue;
        }

        row.col["car_no"] = cm::db::bind(carNo);
        // plateColor 先按**中文 label** 翻成码；翻不到就得到 null（Map.get 不是空串）
        {
            const std::string raw = jstr(tracks, "plateColor");
            auto it = plateColorMap.find(CommonUtil::isNull(raw));
            row.col["plate_color"] = it != plateColorMap.end() ? cm::db::bind(it->second) : std::string();
        }
        // 有重点车辆信息就以它为准（覆盖上面那次字典翻译的结果）
        auto cit = carMap.find(carNo);
        if (cit != carMap.end()) {
            row.col["plate_color"] = cm::db::bind(carAttr(cit->second, "plateColor", "plate_color"));
            row.col["car_type"] = cm::db::bind(carAttr(cit->second, "carType", "car_type"));
            row.col["car_vehicle"] = cm::db::bind(carAttr(cit->second, "carVehicle", "car_vehicle"));
        } else {
            const std::string envehicletype = jstr(tracks, "envehicletype");
            if (StringUtils::isNotBlank(envehicletype)) {
                const std::string carVehicle = vehicleOfEnVehicleType(envehicletype);
                if (!carVehicle.empty()) {
                    row.col["car_type"] = cm::db::bind(envehicletype);
                    row.col["car_vehicle"] = cm::db::bind(carVehicle);
                }
            }
        }
        // 入口车轴数：tracks.enaxlecount 优先，为 null 才用 tracks.carNum
        if (tracks.contains("enaxlecount") && !tracks["enaxlecount"].is_null()) {
            row.col["car_num"] = std::to_string(cm::jlong(tracks, "enaxlecount"));
        } else if (tracks.contains("carNum") && !tracks["carNum"].is_null()) {
            row.col["car_num"] = std::to_string(cm::jlong(tracks, "carNum"));
        }
        row.col["pass_type"] = cm::db::bind(jstr(tracks, "passType"));

        // 门架 / 收费站两个子表，按 stateType 分进去
        std::vector<Json> gantryList, stationList;
        for (const auto& bo : josnList) {
            const std::string stateType = CommonUtil::isNull(jstr(bo, "stateType"));
            // ⚠️ 设备编码那一段**没有**判重（下面 roadCode/sectionCode 却有）——照抄
            if (StringUtils::isNotBlank(jstr(bo, "devCode"))) {
                devCodes += stateType + ":" + jstr(bo, "devCode") + ",";
            }
            const std::string roadCode = jstr(bo, "roadCode");
            if (StringUtils::isNotBlank(roadCode)) {
                const std::string roadKey = "roadCode:" + roadCode;
                if (devCodes.find(roadKey) == std::string::npos) devCodes += roadKey + ",";
            }
            const std::string sectionCode = jstr(bo, "sectionCode");
            if (StringUtils::isNotBlank(sectionCode)) {
                const std::string sectionKey = "sectionCode:" + sectionCode;
                if (devCodes.find(sectionKey) == std::string::npos) devCodes += sectionKey + ",";
            }
            if (stateType == Constants::GANTRY_CAPTURE) gantryList.push_back(bo);
            else if (stateType == Constants::STATION_CAPTURE) stationList.push_back(bo);
        }

        for (size_t i = 0; i < stationList.size(); ++i) {
            if (i != 0 && i + 1 != stationList.size()) continue;
            const Json& bo = stationList[i];
            if (i == 0) {
                row.col["in_station_id"] = cm::db::bind(jstr(bo, "devCode"));
                row.col["in_station"] = cm::db::bind(jstr(bo, "devName"));
            } else {
                row.col["out_station_id"] = cm::db::bind(jstr(bo, "devCode"));
                row.col["out_station"] = cm::db::bind(jstr(bo, "devName"));
            }
            const std::string t = tsText(bo, "captureTime");
            if (!t.empty()) {
                if (i == 0) row.col["in_time"] = cm::db::bind(t); else row.col["out_time"] = cm::db::bind(t);
            }
        }
        // tracks 上的进出口站编号优先覆盖上面收费站的结果
        if (StringUtils::isNotBlank(jstr(tracks, "entollstationid"))) {
            row.col["in_station_id"] = cm::db::bind(jstr(tracks, "entollstationid"));
            row.col["in_station"] = cm::db::bind(jstr(tracks, "entollstationname"));
            const std::string t = tsText(tracks, "enterTime");
            if (!t.empty()) row.col["in_time"] = cm::db::bind(t);
        }
        if (StringUtils::isNotBlank(jstr(tracks, "extollstationid"))) {
            row.col["out_station_id"] = cm::db::bind(jstr(tracks, "extollstationid"));
            row.col["out_station"] = cm::db::bind(jstr(tracks, "extollstationname"));
            const std::string t = tsText(tracks, "exitTime");
            if (!t.empty()) row.col["out_time"] = cm::db::bind(t);
        }
        for (size_t i = 0; i < gantryList.size(); ++i) {
            if (i != 0 && i + 1 != gantryList.size()) continue;
            const Json& bo = gantryList[i];
            const std::string t = tsText(bo, "captureTime");
            if (i == 0) {
                row.col["gantry_station_id"] = cm::db::bind(jstr(bo, "devCode"));
                row.col["gantryt_station"] = cm::db::bind(jstr(bo, "devName"));
                if (!t.empty()) row.col["gantry_time"] = cm::db::bind(t);
            } else {
                row.col["out_gantry_station_id"] = cm::db::bind(jstr(bo, "devCode"));
                row.col["out_gantryt_station"] = cm::db::bind(jstr(bo, "devName"));
                if (!t.empty()) row.col["out_gantry_time"] = cm::db::bind(t);
            }
        }

        // ⚠️ getTimestampNew2() 不是"当前时间"，是**当前时间减 2 天**（方法名看不出来）
        const std::string twoDaysAgo = DateUtils::formatMillis(
            DateUtils::nowMillis() - 2LL * 24 * 3600 * 1000, DateUtils::YYYY_MM_DD_HH_MM_SS);
        row.col["create_by"] = std::to_string(userId);
        row.col["create_time"] = cm::db::bind(twoDaysAgo);
        row.col["update_by"] = std::to_string(userId);
        row.col["update_time"] = cm::db::bind(twoDaysAgo);
        row.col["is_except"] = Db::lit("1");
        row.col["status"] = Db::lit("0");
        row.col["track_names"] = cm::db::bind(CommonUtil::deleteEnd(devCodes));
        row.col["remark"] = cm::db::bind(jstr(tracks, "escapedTypeRemark"));
        if (row.id.empty()) {
            row.col["escaped_type"] = cm::db::bind(jstr(tracks, "escapedType"));
            addList.push_back(std::move(row));
        } else {
            updList.push_back(std::move(row));
        }
    }

    for (auto& r : addList) {
        r.col["id"] = cm::db::bind(cm::utils::simpleUuid());
        std::string names, vals;
        for (const auto& c : orderedCols) {
            const auto it = r.col.find(c.first);
            if (it == r.col.end() || it->second.empty()) continue;
            if (!names.empty()) { names += ", "; vals += ", "; }
            names += c.second;
            vals += it->second;
        }
        if (names.empty()) continue;
        mustRunSql("INSERT INTO car_suspicious (" + names + ") VALUES (" + vals + ")");
    }
    for (auto& r : updList) {
        std::string sets;
        for (const auto& c : orderedCols) {
            if (std::string(c.first) == "id") continue;
            const auto it = r.col.find(c.first);
            if (it == r.col.end() || it->second.empty()) continue;
            if (!sets.empty()) sets += ", ";
            sets += std::string(c.second) + " = " + it->second;
        }
        if (sets.empty()) continue;
        // CarSuspicious 的父类 BasePlusEntityLong 没有 fill，create_by/create_time 不在
        // updateById 的 SET 里（Java 手动设过 create_by，但 MP 只写非 null 属性 —— 一样会写）。
        mustRunSql("UPDATE car_suspicious SET " + sets + " WHERE id = " + cm::db::bind(r.id) +
                   " AND del_flag = '0'");
    }
    (void)errMsg;
    return true;
}

cm::http::ApiResponse syncSuspiciousCarTask(RequestContext& ctx) {
    Json body = cm::parse_json(ctx.req.body);
    const std::string signatureKey = jstr(body, "signatureKey");
    const bool hasStamp = body.contains("timeStamp") && !body["timeStamp"].is_null();
    const std::string signature = jstr(body, "signature");
    if (StringUtils::isBlank(signatureKey) || StringUtils::isBlank(signature) || !hasStamp) {
        return BaseController::ok(AjaxResult::error("参数错误"));
    }
    // shaEncode(signatureKey + timeStamp)：Long 拼进字符串就是十进制，没有 L 后缀
    std::string stamp;
    const Json& ts = body["timeStamp"];
    if (ts.is_number_integer()) stamp = ts.dump();
    else if (ts.is_number()) stamp = std::to_string(static_cast<long long>(ts.get<double>()));
    else stamp = CommonUtil::isNull(ts.is_string() ? ts.get<std::string>() : ts.dump());
    const std::string expect = cm::crypto::hex(cm::crypto::sha1(signatureKey + stamp));
    if (expect != signature) {
        return BaseController::ok(AjaxResult::error("错误，签名验证失败！"));
    }
    const Json list = body.contains("trailInfoList") ? body["trailInfoList"] : Json::array();
    if (list.is_array() && !list.empty()) {
        std::string errMsg;
        syncSuspiciousCar("task", list, errMsg);
    }
    return BaseController::ok(AjaxResult::success());
}

}  // namespace

void registerManagerSuspiciousWriteControllers(Router& r) {
    // ⚠️ Java 里 check 的 @PreAuthorize 是**注释掉的**，不要顺手补上权限
    r.put("/manager/suspicious/check", [](RequestContext& ctx) { return checkSuspicious(ctx); });
    r.post("/manager/suspicious/syncSuspiciousCarTask",
           [](RequestContext& ctx) { return syncSuspiciousCarTask(ctx); });
}

}  // namespace cm::web
