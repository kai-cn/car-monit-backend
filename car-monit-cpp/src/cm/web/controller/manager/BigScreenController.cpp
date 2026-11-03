// 对应 Java: com.ruoyi.web.controller.manager.bigscreen.BigScreenController
//            的 sectionList / tollGantryFwqList / exceptionCar / orgList
//
// 这4个接口都是“查库 + 投影成小 VO”，VO 的 JSON 键序 = VO 字段声明序。
#include "cm/web/controller/manager/BigScreenController.hpp"

#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"

namespace cm::web {
namespace {

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
}

} // namespace cm::web
