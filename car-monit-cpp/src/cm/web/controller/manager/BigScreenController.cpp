// 对应 Java: com.ruoyi.web.controller.manager.bigscreen.BigScreenController
//            的 sectionList / tollGantryFwqList / exceptionCar / orgList
//
// 这4个接口都是“查库 + 投影成小 VO”，VO 的 JSON 键序 = VO 字段声明序。
#include "cm/web/controller/manager/BigScreenController.hpp"

#include <stdexcept>
#include <string>
#include <vector>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"

namespace cm::web {
namespace {

using cm::constant::Constants;
using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::StringUtils;

cm::db::Result run(const std::string& sql) {
    cm::db::Result res;
    Db::instance().query(sql, res);
    return res;
}

/** 把逗号分隔的 sectionCode 展开成 in (...)；含 "all" 时不加条件（Java 直接清空列表） */
std::string sectionIn(const std::string& raw, const char* column) {
    std::vector<std::string> items;
    size_t pos = 0;
    while (pos <= raw.size()) {
        size_t comma = raw.find(',', pos);
        std::string item = raw.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
        if (!StringUtils::isBlank(item)) items.push_back(StringUtils::trim(item));
        if (comma == std::string::npos) break;
        pos = comma + 1;
    }
    if (items.empty()) return std::string();
    std::string in;
    for (const auto& v : items) {
        if (!in.empty()) in += ", ";
        in += Db::lit(v);
    }
    return std::string(" and ") + column + " in (" + in + ")";
}

Json vo2(const std::string& k1, const std::string& v1, const std::string& k2, const std::string& v2) {
    Json j = Json::object();
    j[k1] = v1;
    j[k2] = v2;
    return j;
}

/** 走 spec 取整表行（Java 的 selectXxxList(new Xxx()) 形态） */
std::vector<Json> specRows(const cm::web::crud::Spec& sp) {
    auto res = run("SELECT " + sp.selectColumns() + " FROM " + sp.table + " " + sp.alias + " " +
                   "WHERE 1=1" + sp.extraWhere +
                   (sp.orderBy.empty() ? std::string() : (" ORDER BY " + sp.orderBy)));
    std::vector<Json> out;
    for (const auto& row : res.rows) out.push_back(cm::web::crud::rowToJson(sp, row));
    return out;
}

/** Java: new BigDecimal(lonStr) —— 非法数字抛 NumberFormatException，冒泡成 500。
 *  ⚠️ BigDecimal 会保留原始 scale（"116.10" 输出 116.10），C++ 侧按 double 输出最简形式，
 *     精确值同时由 lonStr/latStr 原样给出（见 COMPATIBILITY.md §2.7）。 */
Json toDecimal(const std::string& text) {
    try {
        size_t used = 0;
        const double v = std::stod(text, &used);
        if (used != text.size()) throw std::invalid_argument("trailing");
        return Json(v);
    } catch (const std::exception&) {
        throw std::runtime_error("java.lang.NumberFormatException: " + text);
    }
}

/** CarLocationParam 里空值不参与过滤；isExitsStr 的"空参放行"语义在 CommonUtil 里 */
std::string param(const RequestContext& ctx, const char* name) {
    return StringUtils::trim(ctx.optParam(name).value_or(""));
}

} // namespace

void registerBigScreenController(Router& r) {
    // GET /manager/bigScreen/sectionList —— 路段列表，第一项固定是“全部”
    r.get("/manager/bigScreen/sectionList", [](RequestContext&) -> cm::http::ApiResponse {
        // Java: selectOdsSzdnSectionListNew(new OdsSzdnSection()) —— 不带任何条件
        auto res = run("SELECT distinct t.section_code, concat(t.road_code, '', t.section_name) section_name"
                       " FROM ods_szdn_section t WHERE 1=1");
        Json arr = Json::array();
        arr.push_back(vo2("sectionCode", "all", "sectionName", "全部"));  // Constants.section_all
        for (const auto& row : res.rows)
            arr.push_back(vo2("sectionCode", row.str("section_code"), "sectionName", row.str("section_name")));
        return BaseController::ok(AjaxResult::success(arr));
    });

    // GET /manager/bigScreen/tollGantryFwqList?type=1|2|3
    // ⚠️ Java 的 type 是 required 参数，缺失时 Spring 直接 400；这里按空串处理成“无匹配分支”→ 空数组
    r.get("/manager/bigScreen/tollGantryFwqList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string sectionCode = ctx.optParam("sectionCode").value_or("");
        if (StringUtils::isBlank(sectionCode))
            return BaseController::ok(AjaxResult::success(Json::array()));
        // CommonUtil.deleteEnd：去掉结尾的分隔符/空白
        sectionCode = StringUtils::trim(sectionCode);
        while (!sectionCode.empty() && sectionCode.back() == ',') sectionCode.pop_back();
        const std::string type = ctx.param("type");
        // 含 all 时不加路段条件
        const std::string in = sectionCode.find("all") != std::string::npos
                                   ? std::string()
                                   : sectionIn(sectionCode, "t.section_code");

        struct Branch {
            const char* type;
            const char* table;
            const char* codeCol;
            const char* nameCol;
            const char* order;
        };
        // 三个分支的 distinct 投影与排序逐条对照各自的 XxxListNew
        const Branch branches[] = {
            {"1", "ods_szdn_toll", "toll_code", "toll_name", "t.toll_name"},
            {"2", "ods_szdn_gantry", "gantry_code", "gantry_name", "t.gantry_name"},
        };
        Json arr = Json::array();
        for (const auto& b : branches) {
            if (type != b.type) continue;
            std::string sql = std::string("SELECT distinct t.") + b.codeCol + ", t." + b.nameCol +
                              " FROM " + b.table + " t WHERE 1=1";
            // 收费站的 ListNew 里路段列叫 section_code，门架也是 section_code
            sql += in;
            sql += std::string(" order by ") + b.order;
            for (const auto& row : run(sql).rows) {
                Json j = Json::object();
                j["type"] = b.type;
                j["code"] = Json(row.get(b.codeCol).value_or(std::string()));
                j["name"] = Json(row.get(b.nameCol).value_or(std::string()));
                arr.push_back(std::move(j));
            }
            return BaseController::ok(AjaxResult::success(arr));
        }
        if (type == "3") {
            // dwd_lczt_fwqjcxx union all base_config_service_area
            const std::string inFwq = sectionCode.find("all") != std::string::npos
                                          ? std::string()
                                          : sectionIn(sectionCode, "t.ssldbh");
            std::string sql =
                "SELECT distinct t.fwqbm,t.fwqmc FROM dwd_lczt_fwqjcxx t WHERE 1=1" + inFwq +
                " union all SELECT distinct t.fwqbm,t.fwqmc FROM base_config_service_area t WHERE 1=1" +
                (sectionCode.find("all") != std::string::npos ? std::string()
                                                              : sectionIn(sectionCode, "t.section_code"));
            for (const auto& row : run(sql).rows) {
                Json j = Json::object();
                j["type"] = "3";
                j["code"] = Json(row.get("fwqbm").value_or(std::string()));
                j["name"] = Json(row.get("fwqmc").value_or(std::string()));
                arr.push_back(std::move(j));
            }
        }
        return BaseController::ok(AjaxResult::success(arr));
    });

    // GET /manager/bigScreen/exceptionCar —— 已确认异常且已审核的前 10 条
    r.get("/manager/bigScreen/exceptionCar", [](RequestContext&) -> cm::http::ApiResponse {
        auto res = run("SELECT t.car_no,t.car_type, t.escaped_type, t.section_name FROM car_suspicious t"
                       " WHERE t.del_flag = '0' and is_except = '1' and check_status = '1'"
                       " order by t.create_time desc,t.id limit 10");
        // 只投影 4 列，其余属性在 Java 里也是 null
        const auto& spec = cm::web::crud::specCarSuspicious();
        Json arr = Json::array();
        for (const auto& row : res.rows) arr.push_back(cm::web::crud::rowToJson(spec, row));
        return BaseController::ok(AjaxResult::success(arr));
    });

    // GET /manager/bigScreen/orgList —— MP lambdaQuery().select(orgCode, orgName).list()
    r.get("/manager/bigScreen/orgList", [](RequestContext&) -> cm::http::ApiResponse {
        auto res = run("SELECT org_code, org_name FROM ods_yhgl_v_base_org");
        Json arr = Json::array();
        for (const auto& row : res.rows)
            arr.push_back(vo2("orgCode", row.str("org_code"), "orgName", row.str("org_name")));
        return BaseController::ok(AjaxResult::success(arr));
    });

    // GET /manager/bigScreen/carLocation —— 车辆定位
    // 数据源是 Redis car_list（Java 用 setCacheObject 不带过期时间），没有才按
    // selectCarInfoList(new CarInfo()) 回源并写回缓存；随后在内存里按设备编码串过滤。
    r.get("/manager/bigScreen/carLocation", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::vector<Json> cars;
        auto cached = cm::redis::RedisCache::instance().get("car_list");
        if (cached && !cached->empty()) {
            Json j = cm::utils::parse_cached_json(*cached);  // 解析失败 -> 500（Java 的强转同样会抛）
            if (j.is_array()) for (const auto& e : j) cars.push_back(e);
        } else {
            cars = specRows(cm::web::crud::specCarInfo());
            Json arr = Json::array();
            for (const auto& c : cars) arr.push_back(c);
            cm::redis::RedisCache::instance().set("car_list", arr.dump());  // 不设 TTL，与 Java 一致
        }

        // 参数预处理：sectionCode 含 all 视为不限；type 决定 code 落到哪个编码字段
        std::string sectionCode = param(ctx, "sectionCode");
        if (sectionCode.find(Constants::section_all) != std::string::npos) sectionCode.clear();
        std::string tollCode, gantryCode, fwqbm;
        const std::string type = param(ctx, "type");
        const std::string code = param(ctx, "code");
        if (!type.empty()) {
            const std::string fallback = !code.empty() ? code : std::string();
            if (type == "1") tollCode = !code.empty() ? code : Constants::STATION_CAPTURE;
            else if (type == "2") gantryCode = !code.empty() ? code : Constants::GANTRY_CAPTURE;
            else if (type == "3") fwqbm = !code.empty() ? code : Constants::SERVICE_AREA_CAPTURE;
            (void)fallback;
        }
        const std::string roadCode = param(ctx, "roadCode");
        const std::string escapedType = param(ctx, "escapedType");
        const std::string carNoQuery = param(ctx, "carNoQuery");

        Json out = Json::array();
        for (const auto& c : cars) {
            if (utils::CommonUtil::isNull(c, "status") != "1") continue;
            const std::string devCodes = utils::CommonUtil::isNull(c, "gantryCode");
            bool pass = utils::CommonUtil::isExitsStr(devCodes, roadCode) &&
                        utils::CommonUtil::isExitsStr(devCodes, sectionCode) &&
                        utils::CommonUtil::isExitsStr(devCodes, tollCode) &&
                        utils::CommonUtil::isExitsStr(devCodes, gantryCode) &&
                        utils::CommonUtil::isExitsStr(devCodes, fwqbm) &&
                        utils::CommonUtil::isExitsStr(utils::CommonUtil::isNull(c, "escapedType"), escapedType) &&
                        utils::CommonUtil::isExitsStr(utils::CommonUtil::isNull(c, "carNo"), carNoQuery);
            if (!pass) continue;

            const std::string lonStr = utils::CommonUtil::isNull(c, "lastPassLongitude");
            const std::string latStr = utils::CommonUtil::isNull(c, "lastPassLatitude");
            Json vo = Json::object();
            // CarLocationVO 字段声明序：id, carNo, carType, lon, lat, lonStr, latStr, status, lastPassType
            vo["id"] = cm::jstr(c, "id", std::string()).empty() ? Json(nullptr) : Json(cm::jstr(c, "id", std::string()));
            vo["carNo"] = cm::jstr(c, "carNo", std::string()).empty() ? Json(nullptr) : Json(cm::jstr(c, "carNo", std::string()));
            vo["carType"] = cm::jstr(c, "carType", std::string()).empty() ? Json(nullptr) : Json(cm::jstr(c, "carType", std::string()));
            vo["lon"] = StringUtils::isBlank(lonStr) ? Json(nullptr) : toDecimal(lonStr);
            vo["lat"] = StringUtils::isBlank(latStr) ? Json(nullptr) : toDecimal(latStr);
            vo["lonStr"] = StringUtils::isBlank(lonStr) ? Json(nullptr) : Json(lonStr);
            vo["latStr"] = StringUtils::isBlank(latStr) ? Json(nullptr) : Json(latStr);
            vo["status"] = cm::jstr(c, "status", std::string()).empty() ? Json(nullptr) : Json(cm::jstr(c, "status", std::string()));
            vo["lastPassType"] = cm::jstr(c, "lastPassType", std::string()).empty() ? Json(nullptr) : Json(cm::jstr(c, "lastPassType", std::string()));
            out.push_back(std::move(vo));
        }
        return BaseController::ok(AjaxResult::success(out));
    });

    // GET /manager/bigScreen/carVoList —— 重点车辆库统计前 10 条（CarInfoMapper.selectCarVoList）
    // VO 只有 4 个属性，SQL 里多投影的 id / escaped_type_name 无处映射 -> 不出现在响应里
    r.get("/manager/bigScreen/carVoList", [](RequestContext&) -> cm::http::ApiResponse {
        auto res = run("select t.id, t.car_no, t.car_type, t.escaped_type, t.escaped_type_name, t.escaped_amount"
                       " from car_info t WHERE t.del_flag = '0' order by t.create_time desc,t.id limit 10");
        Json arr = Json::array();
        for (const auto& row : res.rows) {
            Json vo = Json::object();
            vo["carNo"] = row.get("car_no") ? Json(*row.get("car_no")) : Json(nullptr);
            vo["carType"] = row.get("car_type") ? Json(*row.get("car_type")) : Json(nullptr);
            vo["escapedType"] = row.get("escaped_type") ? Json(*row.get("escaped_type")) : Json(nullptr);
            vo["escapedAmount"] = row.get("escaped_amount") ? Json(row.dbl("escaped_amount")) : Json(nullptr);
            arr.push_back(std::move(vo));
        }
        return BaseController::ok(AjaxResult::success(arr));
    });

    // GET /manager/bigScreen/topTen —— 重点车辆通行前 10（告警表按路段聚合）
    // rank / rate 在 Java 里也没被 SQL 投影 -> 恒为 null，但键必须在
    r.get("/manager/bigScreen/topTen", [](RequestContext&) -> cm::http::ApiResponse {
        auto res = run("select t1.road_code roadCode, t1.section_name sectionName, count(1) carNum"
                       " from car_warning_info t, ods_szdn_section t1"
                       " where t.del_flag = '0' and t.section_code = t1.section_code"
                       " group by t1.road_code, t1.section_name order by carNum desc limit 10");
        Json arr = Json::array();
        for (const auto& row : res.rows) {
            Json vo = Json::object();
            vo["roadCode"] = row.get("roadCode") ? Json(*row.get("roadCode")) : Json(nullptr);
            vo["sectionName"] = row.get("sectionName") ? Json(*row.get("sectionName")) : Json(nullptr);
            vo["carNum"] = row.get("carNum") ? Json(row.i64("carNum")) : Json(nullptr);
            vo["rank"] = nullptr;
            vo["rate"] = nullptr;
            arr.push_back(std::move(vo));
        }
        return BaseController::ok(AjaxResult::success(arr));
    });

    // GET /manager/bigScreen/incomeStatistic —— 堵漏增收统计（两张 free 表 union 后按单位聚合）
    r.get("/manager/bigScreen/incomeStatistic", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string queryDateType = param(ctx, "queryDateType");
        if (queryDateType.empty()) queryDateType = "suo";  // Java: 默认为所
        const std::string startDate = param(ctx, "startDate");
        const std::string applyTime1 = param(ctx, "applyTime1");
        const std::string applyTime2 = param(ctx, "applyTime2");

        std::string sql =
            "select sum(ifnull(amount, 0)) amount, count(distinct car_no) carNum, d.dept_name orgName, a.org_id"
            " from ("
            " select t.car_no,t.amount,t.org_id,t.create_time,t.del_flag,t.status from car_confim_free t"
            " where t.del_flag = '0' and t.status = '0'"
            " UNION all"
            " select t.car_no,t.amount,t.org_id,t.create_time,t.del_flag,t.status from car_aduit_free t"
            " where t.del_flag = '0') a"
            " left join sys_dept d on d.dept_id = a.org_id and d.del_flag = '0'"
            " where a.del_flag = '0'";
        if (queryDateType == "suo") sql += " and a.status = '0'";
        if (!startDate.empty())
            sql += " and a.create_time >= STR_TO_DATE(" + Db::lit(startDate) + ",'%Y-%m-%d')"
                   " and a.create_time < LAST_DAY(" + Db::lit(startDate) + ")";
        sql += queryDateType == "suo" ? " and d.tree_leavel = 2"
                                      : (queryDateType == "zhan" ? " and d.tree_leavel = 3" : "");
        if (!applyTime1.empty())
            sql += " and a.create_time >= STR_TO_DATE(" + Db::lit(applyTime1) + ",'%Y-%m-%d')";
        if (!applyTime2.empty())
            sql += " and a.create_time < date_add(STR_TO_DATE(" + Db::lit(applyTime2) +
                   ", '%Y-%m-%d'), interval 1 day)";
        sql += " group by a.org_id order by amount desc";

        auto res = run(sql);
        Json arr = Json::array();
        for (const auto& row : res.rows) {
            Json vo = Json::object();
            // incomeStatisticVO 声明序：orgName, amount, carNum
            vo["orgName"] = row.get("orgName") ? Json(*row.get("orgName")) : Json(nullptr);
            vo["amount"] = row.get("amount") ? Json(row.dbl("amount")) : Json(nullptr);
            vo["carNum"] = row.get("carNum") ? Json(row.i64("carNum")) : Json(nullptr);
            arr.push_back(std::move(vo));
        }
        return BaseController::ok(AjaxResult::success(arr));
    });
}

} // namespace cm::web
