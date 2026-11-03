// 对应 Java: com.ruoyi.web.controller.manager.{CarSuspicious,CarExceptRecord,CarConfimFree,CarAduitFree}Controller
//            的非同构 CRUD 接口
//
// 这批端点的共同套路是“先给查询对象塞一个默认值（查不到而不是查全表），再走原本的分页查询”，
// 所以直接复用生成器暴露的 Spec（include/cm/web/specs/ManagerCrudSpecs.hpp），
// 只在其上叠加 Java 里的前置条件；统计类接口则是 XML 里独立的 group by 语句。
#include "cm/web/controller/manager/ManagerExtraControllers.hpp"

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
using namespace cm::web::crud;

/** 对应 CommonUtil.isBlank(getX()) -> setX("-1")：不传或全空白都算空 */
void presetBlank(Json& query, const char* key) {
    std::string v;
    if (query.contains(key) && !query[key].is_null()) {
        if (query[key].is_string()) v = query[key].get<std::string>();
    }
    if (!StringUtils::isBlank(v)) return;
    query[key] = "-1";
}

/** 把统计别名接进 spec：那些属性在实体上不是表列，只有这类 group by 查询才给值 */
Spec aliasSpec(const Spec& base, std::vector<std::pair<const char*, const char*>> aliases) {
    Spec s = base;
    for (const auto& [json, col] : aliases) {
        for (auto& f : s.fields) {
            if (std::string(f.json) == json) f.column = col;
        }
    }
    return s;
}

cm::db::Result select(const std::string& sql) {
    cm::db::Result res;
    Db::instance().query(sql, res);
    return res;
}

} // namespace

void registerManagerExtraControllers(Router& r) {
    // ---- 车牌维度：Java 一律先把 carNo 兜成 "-1"，避免全表扫 ----

    // GET /manager/suspicious/listCarNo
    {
        Spec s = specCarSuspicious();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "carNo"); };
        registerListVariant(r, "/manager/suspicious/listCarNo", s, ListKind::Paged);
    }
    // GET /manager/exceptrecord/listCarNo
    {
        Spec s = specCarExceptRecord();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "carNo"); };
        registerListVariant(r, "/manager/exceptrecord/listCarNo", s, ListKind::Paged);
    }
    // GET /manager/exceptrecord/listExceptId —— 同样兜底，条件是 find_in_set(t.id, #{exceptIds})
    {
        Spec s = specCarExceptRecord();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "exceptIds"); };
        registerListVariant(r, "/manager/exceptrecord/listExceptId", s, ListKind::Paged);
    }
    // GET /manager/confimfree/listCarNo
    {
        Spec s = specCarConfimFree();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "carNo"); };
        registerListVariant(r, "/manager/confimfree/listCarNo", s, ListKind::Paged);
    }

    // GET /manager/exceptrecord/exceptRecordCount
    // 对应 CarExceptRecordMapper.exceptRecordCount：按车牌聚合，返回单个实体（查不到为 null）
    r.get("/manager/exceptrecord/exceptRecordCount", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string carNo = ctx.optParam("carNo").value_or("");
        if (StringUtils::isBlank(carNo)) carNo = "-1";
        std::string sql =
            "select t.car_no,count(1) exceptNum,round(sum(t.dif_amount),2) exceptAmount,"
            "round(sum(t.total_amount),2) total_amount,round(sum(t.charge_amount),2) charge_amount "
            "from car_except_record t where t.del_flag = '0' and t.car_no = " +
            Db::lit(carNo);
        if (auto v = ctx.optParam("status"); v && !StringUtils::isBlank(*v))
            sql += " and t.status = " + Db::lit(*v);
        sql += " group by t.car_no";

        static const Spec cs = aliasSpec(specCarExceptRecord(),
                                         {{"exceptNum", "exceptNum"},
                                          {"exceptAmount", "exceptAmount"},
                                          {"totalAmount", "total_amount"},
                                          {"chargeAmount", "charge_amount"},
                                          {"carNo", "car_no"}});
        auto res = select(sql);
        // Java 的 resultMap 只认列名，未投影的属性保持 null
        Json data = res.rows.empty() ? Json(nullptr) : rowToJson(cs, res.rows[0]);
        return BaseController::ok(AjaxResult::success(data));
    });

    // GET /manager/confimfree/listCount —— 同上，free 记录的聚合
    r.get("/manager/confimfree/listCount", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string carNo = ctx.optParam("carNo").value_or("");
        if (StringUtils::isBlank(carNo)) carNo = "-1";
        std::string sql =
            "select t.car_no,count(1) confimFreeNum,"
            "round(ifnull(sum(t.aduit_amount),0) + ifnull(sum(t.amount),0),2) confimFreeAmount "
            "from car_confim_free t where t.del_flag = '0' and t.car_no = " +
            Db::lit(carNo);
        if (auto v = ctx.optParam("status"); v && !StringUtils::isBlank(*v))
            sql += " and t.status = " + Db::lit(*v);
        sql += " group by t.car_no";

        static const Spec cs = aliasSpec(specCarConfimFree(),
                                         {{"confimFreeNum", "confimFreeNum"},
                                          {"confimFreeAmount", "confimFreeAmount"},
                                          {"carNo", "car_no"}});
        auto res = select(sql);
        Json data = res.rows.empty() ? Json(nullptr) : rowToJson(cs, res.rows[0]);
        return BaseController::ok(AjaxResult::success(data));
    });

    // GET /manager/exceptrecord/getConfirmId/{id}
    // Java: selectCarConfimFreeByExceptIds([id]) 取第一条的 id，没有则 "-1"
    r.get("/manager/exceptrecord/getConfirmId/{id}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const std::string id = ctx.pathVar("id");
        const std::string sql =
            "SELECT t.ID FROM car_confim_free t WHERE t.del_flag = '0' and (find_in_set(" +
            Db::lit(id) + ", t.except_ids) > 0)";
        auto res = select(sql);
        const std::string confirmId = res.rows.empty() ? std::string("-1") : res.rows[0].str("ID");
        AjaxResult success = AjaxResult::success();
        success.put("data", confirmId);
        return BaseController::ok(success);
    });

    // GET /manager/aduitfree/incomeDetailList
    // 对应 CarAduitFreeMapper.incomeDetailList：两张表的 union all，再按创建时间倒序分页
    r.get("/manager/aduitfree/incomeDetailList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string orgId = ctx.optParam("orgId").value_or("");
        if (StringUtils::isBlank(orgId)) orgId = "-1";  // Java: getOrgId() 为空时兜成 "-1"
        const std::string applyTime1 = ctx.optParam("applyTime1").value_or("");
        const std::string applyTime2 = ctx.optParam("applyTime2").value_or("");
        const std::string carNo = ctx.optParam("carNo").value_or("");

        auto half = [&](const char* table, bool aduit) {
            std::string s = std::string("select ifnull(a.amount, 0) amount, a.car_no, a.org_id, ") +
                            "d.dept_name orgName,a.create_time from " + table +
                            " a left join sys_dept d on d.dept_id = a.org_id where a.del_flag = '0'";
            if (aduit) s += " and a.status = '0'";
            s += " and a.org_id = " + Db::lit(orgId);
            if (!StringUtils::isBlank(applyTime1))
                s += " and a.create_time >= STR_TO_DATE(" + Db::lit(applyTime1) + ",'%Y-%m-%d')";
            if (!StringUtils::isBlank(applyTime2))
                s += " and a.create_time < date_add(STR_TO_DATE(" + Db::lit(applyTime2) +
                     ", '%Y-%m-%d'), interval 1 day)";
            if (!StringUtils::isBlank(carNo))
                s += " and a.car_no like concat('%', " + Db::lit(carNo) + ", '%')";
            return s;
        };
        const std::string inner = half("car_aduit_free", true) + " UNION all " + half("car_confim_free", false);
        const std::string data = "select t.* from (" + inner + ") t order by t.create_time desc";
        const auto page = ctx.pageRequest();
        auto pr = cm::db::queryPage("select count(1) from (" + inner + ") page_count", data, page);

        // resultType=CarConfimFree：按列名自动映射，只有这 5 个属性会有值
        static const Spec cs = aliasSpec(specCarConfimFree(), {{"orgName", "orgName"}});
        Json rows = Json::array();
        for (const auto& row : pr.rows.rows) rows.push_back(rowToJson(cs, row));
        return BaseController::ok(BaseController::dataTable(rows, pr.total));
    });
}

} // namespace cm::web
