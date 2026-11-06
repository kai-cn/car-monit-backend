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

#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/JsonUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"
#include "cm/web/util/SuspiciousShared.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::CommonUtil;
using cm::utils::DateUtils;
using cm::utils::StringUtils;

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
    return {column, Db::lit(v.is_string() ? v.get<std::string>() : v.dump())};
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
    mustRunSql("delete from car_suspicious_check where car_id = " + Db::lit(carId));
    mustRunSql("delete from car_except_record where car_id = " + Db::lit(carId));

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
                {"id", Db::lit(cm::utils::simpleUuid())},
                {"del_flag", Db::lit("0")},
                {"eps_id", std::to_string(epsId)},
                {"create_by", std::to_string(userId)},
                {"create_time", Db::lit(DateUtils::getTime())},
                {"update_by", std::to_string(userId)},
                {"update_time", Db::lit(DateUtils::getTime())},
                {"car_no", Db::lit(carNo)},
                {"car_type", hasVal(body, "carType") ? Db::lit(optText(body, "carType")) : std::string()},
                {"car_num", hasVal(body, "carNum") ? std::to_string(cm::jlong(body, "carNum")) : std::string()},
                {"car_vehicle", hasVal(body, "carVehicle") ? Db::lit(optText(body, "carVehicle")) : std::string()},
                {"plate_color", hasVal(body, "plateColor") ? Db::lit(optText(body, "plateColor")) : std::string()},
                {"escaped_type", hasVal(body, "escapedType") ? Db::lit(optText(body, "escapedType")) : std::string()},
                {"escaped_amount", Db::lit(escapedAmount)},
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
        {"is_except", hasVal(body, "isExcept") ? Db::lit(optText(body, "isExcept")) : std::string()},
        {"except_remark", hasVal(body, "exceptRemark") ? Db::lit(optText(body, "exceptRemark")) : std::string()},
        {"except_file_ids", hasVal(body, "exceptFileIds") ? Db::lit(optText(body, "exceptFileIds")) : std::string()},
        {"pass_type", hasVal(body, "passType") ? Db::lit(optText(body, "passType")) : std::string()},
        {"plate_color", hasVal(body, "plateColor") ? Db::lit(optText(body, "plateColor")) : std::string()},
        {"car_no", Db::lit(carNo)},
        {"car_type", hasVal(body, "carType") ? Db::lit(optText(body, "carType")) : std::string()},
        {"car_vehicle", hasVal(body, "carVehicle") ? Db::lit(optText(body, "carVehicle")) : std::string()},
        {"car_num", hasVal(body, "carNum") ? std::to_string(cm::jlong(body, "carNum")) : std::string()},
        {"escaped_type", hasVal(body, "escapedType") ? Db::lit(optText(body, "escapedType")) : std::string()},
        {"remark", hasVal(body, "remark") ? Db::lit(optText(body, "remark")) : std::string()},
    };
    if (isExcept == "0") {
        // setExceptFileIds("") —— 空串不是 null，照样进 SET
        for (auto& p : set) {
            if (p.first == "except_file_ids") p.second = Db::lit(std::string());
        }
    }
    std::string sets;
    for (const auto& p : set) {
        if (p.second.empty()) continue;
        if (!sets.empty()) sets += ", ";
        sets += p.first + " = " + p.second;
    }
    if (!sets.empty()) {
        mustRunSql("UPDATE car_suspicious SET " + sets + " WHERE id = " + Db::lit(carId) +
                   " AND del_flag = '0'");
    }

    updateRedisCarList();
    tx.commit();
    return BaseController::ok(AjaxResult::success("操作成功！", Json(optText(body, "id"))));
}

}  // namespace

void registerManagerSuspiciousWriteControllers(Router& r) {
    // ⚠️ Java 里 check 的 @PreAuthorize 是**注释掉的**，不要顺手补上权限
    r.put("/manager/suspicious/check", [](RequestContext& ctx) { return checkSuspicious(ctx); });
}

}  // namespace cm::web
