// 对应 Java: CarExceptRecordController / CarConfimFreeController / CarAduitFreeController 里的模板导出
//            + /manager/exceptrecord/listCarOrgId
//
// Java 侧这些导出走的是 easypoi 的 TemplateExportParams：
//   Workbook wb = ExcelExportUtil.exportExcel(params, map);
//   response.setContentType("application/octet-stream;charset=UTF-8");
//   response.setHeader("Content-Disposition", "attachment");
//   wb.write(response.getOutputStream()); ... return null;
// 也就是**响应体只有 xlsx 字节**，不会再包一层 AjaxResult。
//
// ⚠️ 与 Java 的差异（有意为之，见 COMPATIBILITY.md §2.3）：
//   模板里的标题行、两级表头、合并单元格与单元格样式不复刻；C++ 用自研 OOXML 写出
//   「一行表头 + 数据行」，列集合与列顺序取模板 {{$fe:entitylist ...}} 标记行的实际取值列，
//   表头文案取模板第一行表头。值集合一致，版式不同。
#include "cm/web/controller/manager/ManagerTemplateExportControllers.hpp"

#include <map>
#include <string>
#include <utility>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/Excel.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/controller/manager/ManagerExtraControllers.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::StringUtils;

struct TplCol {
    const char* header;
    const char* field;
    bool numeric{false};
};

/** easypoi 模板导出的响应形态：只有字节，Content-Type / Disposition 照抄 */
cm::http::ApiResponse streamTemplate(const std::vector<TplCol>& cols, const std::vector<Json>& rows) {
    std::vector<cm::common::utils::ExcelColumn> ec;
    for (const auto& c : cols) ec.push_back({c.header, c.field, c.numeric, 16});
    cm::http::ApiResponse resp;
    resp.status = 200;
    resp.content_type = "application/octet-stream;charset=UTF-8";
    resp.headers["Content-Disposition"] = "attachment";
    resp.body = cm::common::utils::Excel::exportXlsx(ec, rows, "Sheet1");
    return resp;
}

/** 这里的查询失败必须抛出去：Java 侧 MyBatis 抛 BadSqlGrammarException → 全局异常处理 → code 500。
 *  ⚠️ CRUD 引擎与部分手写控制器目前把"查询失败"降级成空结果，是已知偏离（见 COMPATIBILITY.md §2.10）。 */
cm::db::Result run(const std::string& sql) {
    cm::db::Result res;
    if (!Db::instance().query(sql, res)) {
        throw cm::exception::ServiceException(
            "数据访问异常，SQL 执行失败: " + sql.substr(0, 200));
    }
    return res;
}

/** 对应 SysDictDataServiceImpl.selectDictDataMap：value -> label。
 *  Java 用 Collectors.toMap，同一个 dict_value 出现两次会抛 IllegalStateException（→ 500），照抄。 */
std::map<std::string, std::string> dictDataMap(const std::string& dictType) {
    std::map<std::string, std::string> out;
    for (const auto& row : run("select d.dict_value dict_value, d.dict_label dict_label"
                               " from sys_dict_data d left join sys_dict_type t on d.dict_type = t.dict_type"
                               " where d.dict_type = " + cm::db::bind(dictType) + " order by d.dict_sort").rows) {
        const std::string k = row.str("dict_value");
        if (out.count(k)) {
            throw cm::exception::ServiceException(
                "Duplicate key " + k + " (attempted merging values " + out[k] + " and " + row.str("dict_label") + ")");
        }
        out[k] = row.str("dict_label");
    }
    return out;
}

std::string str(const Json& j, const char* key) { return cm::jstr(j, key, std::string()); }

/** listCarOrgId / exportOrgId 共用的查询（selectCarExceptRecordListNew）
 *  条件与 specCarExceptRecord 一致，只是 order by 不同；
 *  createInfo 与两个 join 现在由 spec 的 selectTail/fromSql 提供，这里不再手写。 */
std::string listNewSql(const std::string& where) {
    const auto& sp = cm::web::crud::specCarExceptRecord();
    return "SELECT " + sp.selectColumns() + " " + cm::web::crud::fromClauseOf(sp) + " " + where +
           " order by t.dif_amount desc,t.id";
}

std::vector<Json> listNewRows(RequestContext& ctx) {
    const auto& sp = cm::web::crud::specCarExceptRecord();
    Json query = cm::web::crud::bindQuery(sp, ctx);
    // Java: epsId 为空时兜成 -1（于是默认查不到任何行，除非 eps_id 真是 -1）
    if (!query.contains("epsId") || query["epsId"].is_null()) query["epsId"] = -1;
    std::vector<Json> out;
    for (const auto& row : run(listNewSql(cm::web::crud::buildWhere(sp, query))).rows) {
        out.push_back(cm::web::crud::rowToJson(sp, row));
    }
    return out;
}

} // namespace

void registerManagerTemplateExportControllers(Router& r) {
    // GET /manager/exceptrecord/listCarOrgId —— 按单位维度的异常流水（分页）
    r.get("/manager/exceptrecord/listCarOrgId", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto& sp = cm::web::crud::specCarExceptRecord();
        Json query = cm::web::crud::bindQuery(sp, ctx);
        if (!query.contains("epsId") || query["epsId"].is_null()) query["epsId"] = -1;
        const std::string where = cm::web::crud::buildWhere(sp, query);
        const auto page = ctx.pageRequest();
        const std::string dataSql = listNewSql(where);
        if (page.enabled) {
            auto pr = cm::db::queryPage(
                "SELECT count(1) FROM car_except_record t"
                " left join sys_user su on su.user_id = t.create_by"
                " left join sys_dept sd on t.eps_id = sd.dept_id " + where,
                dataSql, page);
            Json rows = Json::array();
            for (const auto& row : pr.rows.rows) rows.push_back(cm::web::crud::rowToJson(sp, row));
            return BaseController::ok(BaseController::dataTable(rows, pr.total));
        }
        Json rows = Json::array();
        for (const auto& row : run(dataSql).rows) rows.push_back(cm::web::crud::rowToJson(sp, row));
        return BaseController::ok(BaseController::dataTable(rows, static_cast<long long>(rows.size())));
    });

    // GET /manager/exceptrecord/exportOrgId —— 同一份数据导出（模板 exportCarExcept.xlsx）
    r.get("/manager/exceptrecord/exportOrgId", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto list = listNewRows(ctx);
        const auto carTypeMap = dictDataMap("car_type");
        const auto carVehicleMap = dictDataMap("car_vehicle");
        const auto escapedTypeMap = dictDataMap("escaped_type");
        const auto statusMap = dictDataMap("supplementary_status");

        for (size_t i = 0; i < list.size(); ++i) {
            Json& dp = list[i];
            // 三个 XxxStr 由 Date 字段格式化而来（spec 里已是同格式文本）
            for (auto& kv : std::vector<std::pair<const char*, const char*>>{
                     {"createTime", "createTimeStr"}, {"inTime", "inTimeStr"}, {"outTime", "outTimeStr"}}) {
                const std::string v = str(dp, kv.first);
                if (!v.empty()) dp[kv.second] = Json(v);
            }
            // 注意：这里三个字段是「字典里有才替换」，与 exportConcernedList 的无条件替换不同
            auto replaceIfPresent = [&](const char* key, const std::map<std::string, std::string>& m) {
                const std::string v = str(dp, key);
                auto it = m.find(v);
                if (it != m.end()) dp[key] = Json(it->second);
            };
            replaceIfPresent("carType", carTypeMap);
            replaceIfPresent("carVehicle", carVehicleMap);
            replaceIfPresent("escapedType", escapedTypeMap);
            // status 是无条件的：字典里没有就变成空串
            auto sit = statusMap.find(str(dp, "status"));
            dp["status"] = Json(sit == statusMap.end() ? std::string() : sit->second);
            dp["sort"] = Json(static_cast<long long>(i + 1));  // Java: dp.setSort(i + 1)
            dp["carNoQuery"] = Json("");
        }

        // 模板标记行里 t.carNoQuery 的那些单元格是"空位"，实际取值的列只有下面 14 个
        static const std::vector<TplCol> cols = {
            {"序号", "sort"},                       {"出口收费站", "outStation"},
            {"出口时间", "outTimeStr"},             {"通行PASSID", "passType"},
            {"车牌", "carNo"},                      {"交易车型", "carType"},
            {"车种", "carVehicle"},                 {"入口站", "inStation"},
            {"入口时间", "inTimeStr"},               {"漏交通行费类型", "escapedType"},
            {"交易金额", "chargeAmount", true},      {"应交金额", "totalAmount", true},
            {"实际追交金额", "difAmount", true},     {"备注", "remark"},
        };
        return streamTemplate(cols, list);
    });

    // GET /manager/confimfree/exportConcernedList —— 待关注车辆（模板 concernedList.xlsx）
    r.get("/manager/confimfree/exportConcernedList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        // CarConfimFreeMapper.selectConcernedList：car_info 聚合 join 异常流水
        const auto& sp = cm::web::crud::specCarConfimFree();
        Json query = cm::web::crud::bindQuery(sp, ctx);
        std::string where = " WHERE t.del_flag = '0'";
        auto p = [&](const char* k) { return cm::jstr(query, k, std::string()); };
        if (!p("carNo").empty()) where += " and t.car_no = " + cm::db::bind(p("carNo"));
        if (!p("carType").empty()) where += " and t.car_type = " + cm::db::bind(p("carType"));
        if (!p("carVehicle").empty()) where += " and t.car_vehicle = " + cm::db::bind(p("carVehicle"));
        if (!p("escapedType").empty()) where += " and t.escaped_type = " + cm::db::bind(p("escapedType"));
        if (!p("orgName").empty()) where += " and sd.dept_name like concat('%', " + cm::db::bind(p("orgName")) + ", '%')";
        if (!p("backCol1").empty()) where += " and t.back_col1 = " + cm::db::bind(p("backCol1"));
        if (!p("backCol2").empty()) where += " and t.back_col2 = " + cm::db::bind(p("backCol2"));
        if (!p("status").empty()) where += " and t.status = " + cm::db::bind(p("status"));
        if (!p("carNoQuery").empty()) where += " and t.car_no like concat('%', " + cm::db::bind(p("carNoQuery")) + ", '%')";
        const std::string apply1 = p("applyTime1");
        const std::string apply2 = p("applyTime2");
        if (!apply1.empty()) where += " and t.create_time >= STR_TO_DATE(" + cm::db::bind(apply1) + ", '%Y-%m-%d %H:%i:%s')";
        if (!apply2.empty()) where += " and t.create_time <= STR_TO_DATE(" + cm::db::bind(apply2) + ", '%Y-%m-%d %H:%i:%s')";
        // ⚠️ 其余 <if> 条件（id/carId/amount/escapedTypes/userIds…）在本页前端不传，未逐条移植；
        //     传了也不会生效，与 Java 不同的地方仅此一处，且只在异常路径上。
        const std::string sql =
            "select t.id, t.car_no, t.car_type, t.car_vehicle, t.escaped_type, t.org_id,"
            " sd.dept_name org_name, k.total_amount totalAmount, k.charge_amount chargeAmount,"
            " k.dif_amount difAmount, k.except_ids"
            " from car_info t"
            " JOIN (select t1.car_no, sum(t1.total_amount) total_amount, sum(t1.charge_amount) charge_amount,"
            " sum(t1.dif_amount) dif_amount,"
            " sum(case when t1.status = '0' then 1 else 0 end) except_num, count(1) count_num,"
            " GROUP_CONCAT(t1.id SEPARATOR ',') except_ids"
            " from car_except_record t1 where t1.del_flag = '0' group by t1.car_no) k"
            " on k.count_num > 0 and k.except_num = 0 and t.car_no = k.car_no"
            " left join sys_dept sd on sd.dept_id = t.eps_id and sd.del_flag = '0'"
            + where;

        std::vector<Json> list;
        for (const auto& row : run(sql).rows) {
            Json j = Json::object();
            j["carNo"] = row.get("car_no") ? Json(*row.get("car_no")) : Json(nullptr);
            j["carType"] = row.get("car_type") ? Json(*row.get("car_type")) : Json(nullptr);
            j["carVehicle"] = row.get("car_vehicle") ? Json(*row.get("car_vehicle")) : Json(nullptr);
            j["escapedType"] = row.get("escaped_type") ? Json(*row.get("escaped_type")) : Json(nullptr);
            j["orgName"] = row.get("org_name") ? Json(*row.get("org_name")) : Json(nullptr);
            j["totalAmount"] = row.get("total_amount") ? Json(row.dbl("total_amount")) : Json(nullptr);
            j["chargeAmount"] = row.get("charge_amount") ? Json(row.dbl("charge_amount")) : Json(nullptr);
            j["difAmount"] = row.get("dif_amount") ? Json(row.dbl("dif_amount")) : Json(nullptr);
            j["remark"] = Json(nullptr);
            list.push_back(std::move(j));
        }

        const auto carTypeMap = dictDataMap("car_type");
        const auto carVehicleMap = dictDataMap("car_vehicle");
        const auto escapedTypeMap = dictDataMap("escaped_type");
        for (auto& dp : list) {
            // 这里是**无条件**替换：字典里没有就变空串（与 exportOrgId 不同）
            auto pick = [&](const std::map<std::string, std::string>& m, const char* key) {
                auto it = m.find(str(dp, key));
                dp[key] = Json(it == m.end() ? std::string() : it->second);
            };
            pick(carTypeMap, "carType");
            pick(carVehicleMap, "carVehicle");
            // 逃费类型是逗号串，逐个翻译再拼回去
            std::string bussName;
            const std::string bussType = utils::CommonUtil::deleteEnd(str(dp, "escapedType"));
            if (!StringUtils::isBlank(bussType)) {
                for (const auto& code : StringUtils::split(bussType, ',')) {
                    auto it = escapedTypeMap.find(code);
                    if (it != escapedTypeMap.end()) bussName += it->second + ",";
                }
            }
            dp["escapedType"] = Json(utils::CommonUtil::deleteEnd(bussName));
        }

        static const std::vector<TplCol> cols = {
            {"车牌号", "carNo"},          {"车型", "carType"},
            {"车种", "carVehicle"},       {"逃费类型", "escapedType"},
            {"录入单位", "orgName"},      {"应缴金额（元）", "totalAmount", true},
            {"收费金额（元）", "chargeAmount", true}, {"差额（元）", "difAmount", true},
            {"备注", "remark"},
        };
        return streamTemplate(cols, list);
    });

    // GET /manager/confimfree/exportCarStatics —— PC 统计导出（模板 carStatistics.xlsx）
    r.get("/manager/confimfree/exportCarStatics", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string sql =
            "select d.dept_id eps_id, d.dept_name org_name, a.escaped_type escapedType,"
            " sum(ifnull(a.dif_amount, 0)) escapedAmount, count(distinct a.car_no) number"
            " from car_except_record a"
            " inner join sys_dept d on a.eps_id = d.dept_id and d.del_flag = '0'"
            " where a.del_flag = '0'";
        const std::string apply1 = ctx.optParam("applyTime1").value_or("");
        const std::string apply2 = ctx.optParam("applyTime2").value_or("");
        const std::string escapedType = ctx.optParam("escapedType").value_or("");
        const std::string orgId = ctx.optParam("orgId").value_or("");
        if (!apply1.empty()) sql += " and a.create_time >= STR_TO_DATE(" + cm::db::bind(apply1) + ", '%Y-%m-%d')";
        if (!apply2.empty())
            sql += " and a.create_time < date_add(STR_TO_DATE(" + cm::db::bind(apply2) + ", '%Y-%m-%d'), interval 1 day)";
        if (!escapedType.empty()) sql += " and a.escaped_type = " + cm::db::bind(escapedType);
        if (!orgId.empty()) sql += " and a.eps_id = " + cm::db::bind(orgId);
        sql += " group by d.dept_id, d.dept_name, a.escaped_type";

        std::vector<Json> list;
        for (const auto& row : run(sql).rows) {
            Json j = Json::object();
            j["orgName"] = row.get("org_name") ? Json(*row.get("org_name")) : Json(nullptr);
            // 模板引用的是 escapedTypeXXNum / XXAmount 这些"按类型展开"的列，
            // 而 Java 的 SQL 只按 (单位, 类型) 出行、也没有透视 —— 那些列在 Java 输出里同样是空的。
            for (const char* code : {"10", "20", "30", "40", "50", "60"}) {
                j[std::string("escapedType") + code + "Num"] = Json(nullptr);
                j[std::string("escapedType") + code + "Amount"] = Json(nullptr);
            }
            j["totalNum"] = Json(nullptr);
            j["totalAmount"] = Json(nullptr);
            list.push_back(std::move(j));
        }
        static const std::vector<TplCol> cols = {
            {"录入单位", "orgName"},           {"入口少轴车辆数", "escapedType10Num"},
            {"入口少轴金额（元）", "escapedType10Amount"}, {"屏蔽车辆数", "escapedType20Num"},
            {"屏蔽金额（元）", "escapedType20Amount"},   {"货车客标车辆数", "escapedType30Num"},
            {"货车客标金额（元）", "escapedType30Amount"}, {"有入无出车辆数", "escapedType40Num"},
            {"有入无出金额（元）", "escapedType40Amount"}, {"大车小标车辆数", "escapedType50Num"},
            {"大车小标金额（元）", "escapedType50Amount"}, {"假冒其他优免车车辆数", "escapedType60Num"},
            {"假冒其他优免车金额（元）", "escapedType60Amount"}, {"合计数量", "totalNum"},
            {"合计金额（元）", "totalAmount"},
        };
        return streamTemplate(cols, list);
    });

    // GET /manager/aduitfree/exportIncomeStatics —— 堵漏增收统计（模板 incomeStatics.xlsx）
    r.get("/manager/aduitfree/exportIncomeStatics", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const std::string orgId = ctx.optParam("orgId").value_or("");
        const std::string apply1 = ctx.optParam("applyTime1").value_or("");
        const std::string apply2 = ctx.optParam("applyTime2").value_or("");
        const std::string carNo = ctx.optParam("carNo").value_or("");
        auto half = [&](const char* table, bool aduit) {
            std::string s = std::string("select ifnull(a.amount, 0) amount, a.car_no, a.org_id,") +
                            " d.dept_name orgName from " + table +
                            " a left join sys_dept d on d.dept_id = a.org_id where a.del_flag = '0'";
            if (aduit) s += " and a.status = '0'";
            if (!orgId.empty()) s += " and a.org_id = " + cm::db::bind(orgId);
            if (!apply1.empty()) s += " and a.create_time >= STR_TO_DATE(" + cm::db::bind(apply1) + ", '%Y-%m-%d')";
            if (!apply2.empty())
                s += " and a.create_time < date_add(STR_TO_DATE(" + cm::db::bind(apply2) + ", '%Y-%m-%d'), interval 1 day)";
            if (!carNo.empty()) s += " and a.car_no like concat('%', " + cm::db::bind(carNo) + ", '%')";
            return s;
        };
        const std::string sql =
            "select sum(t.amount) amount, count(distinct t.car_no) carNum, t.org_id, t.orgName from ("
            + half("car_aduit_free", true) + " UNION all " + half("car_confim_free", false) +
            ") t group by t.org_id, t.orgName order by amount desc";

        std::vector<Json> list;
        for (const auto& row : run(sql).rows) {
            Json j = Json::object();
            j["orgName"] = row.get("orgName") ? Json(*row.get("orgName")) : Json(nullptr);
            j["carNum"] = row.get("carNum") ? Json(row.i64("carNum")) : Json(nullptr);
            j["amount"] = row.get("amount") ? Json(row.dbl("amount")) : Json(nullptr);
            list.push_back(std::move(j));
        }
        static const std::vector<TplCol> cols = {
            {"录入单位", "orgName"}, {"车辆数量", "carNum", true}, {"逃费金额（元）", "amount", true},
        };
        return streamTemplate(cols, list);
    });

    // GET /manager/aduitfree/exportIncomeDetailList —— 明细导出（模板 exportIncomeDetailList.xlsx）
    r.get("/manager/aduitfree/exportIncomeDetailList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string orgId = ctx.optParam("orgId").value_or("");
        if (StringUtils::isBlank(orgId)) orgId = "-1";  // Java: CommonUtil.isBlank 时兜成 "-1"
        const std::string apply1 = ctx.optParam("applyTime1").value_or("");
        const std::string apply2 = ctx.optParam("applyTime2").value_or("");
        const std::string carNo = ctx.optParam("carNo").value_or("");
        auto half = [&](const char* table, bool aduit) {
            std::string s = std::string("select ifnull(a.amount, 0) amount, a.car_no, a.org_id,") +
                            " d.dept_name orgName, a.create_time from " + table +
                            " a left join sys_dept d on d.dept_id = a.org_id where a.del_flag = '0'";
            if (aduit) s += " and a.status = '0'";
            s += " and a.org_id = " + cm::db::bind(orgId);
            if (!apply1.empty()) s += " and a.create_time >= STR_TO_DATE(" + cm::db::bind(apply1) + ", '%Y-%m-%d')";
            if (!apply2.empty())
                s += " and a.create_time < date_add(STR_TO_DATE(" + cm::db::bind(apply2) + ", '%Y-%m-%d'), interval 1 day)";
            if (!carNo.empty()) s += " and a.car_no like concat('%', " + cm::db::bind(carNo) + ", '%')";
            return s;
        };
        const std::string sql = "select * from (" + half("car_aduit_free", true) + " UNION all " +
                                half("car_confim_free", false) +
                                ") t order by t.create_time desc";

        std::vector<Json> list;
        for (const auto& row : run(sql).rows) {
            Json j = Json::object();
            j["carNo"] = row.get("car_no") ? Json(*row.get("car_no")) : Json(nullptr);
            j["amount"] = row.get("amount") ? Json(row.dbl("amount")) : Json(nullptr);
            j["orgName"] = row.get("orgName") ? Json(*row.get("orgName")) : Json(nullptr);
            j["createTime"] = row.get("create_time") ? Json(*row.get("create_time")) : Json(nullptr);
            list.push_back(std::move(j));
        }
        static const std::vector<TplCol> cols = {
            {"车牌号", "carNo"}, {"追缴金额（元）", "amount", true},
            {"录入单位", "orgName"}, {"录入时间", "createTime"},
        };
        return streamTemplate(cols, list);
    });

    // GET /manager/suspicious/exportHistory —— 历史可疑车辆（模板 carSuspicious.xlsx）
    // 与 listHistory 同一份查询（selectCarSuspiciousListHistroy），只是导出的是"当前页"：
    // Java 在导出前也调了 startPage()。
    r.get("/manager/suspicious/exportHistory", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto& sp = cm::web::suspiciousHistorySpec();
        Json query = cm::web::crud::bindQuery(sp, ctx);
        if (sp.hooks.beforeQuery) sp.hooks.beforeQuery(ctx, query);
        const std::string where = cm::web::crud::buildWhere(sp, query);
        const auto page = ctx.pageRequest();
        std::string order = " ORDER BY " + (!page.orderBy.empty() ? page.orderBy : sp.orderBy);
        const std::string dataSql = "SELECT " + sp.selectColumns() + " FROM " + sp.table + " " +
                                    sp.alias + " " + where + order;
        std::vector<Json> list;
        if (page.enabled) {
            auto pr = cm::db::queryPage(
                "SELECT COUNT(1) FROM " + std::string(sp.table) + " " + sp.alias + " " + where,
                dataSql, page);
            for (const auto& row : pr.rows.rows) list.push_back(cm::web::crud::rowToJson(sp, row));
        } else {
            for (const auto& row : run(dataSql).rows)
                list.push_back(cm::web::crud::rowToJson(sp, row));
        }

        // Java 导出前把 7 个字典全查一遍：selectDictDataMap 走 Collectors.toMap，
        // 同一个 dict_value 出现两次会抛 IllegalStateException -> 整个导出 500。
        // 少查一个就变成“Java 500、C++ 成功”，所以这里连没用到的 run_type 也照查。
        const auto plateColorMap = dictDataMap("plate_color");
        const auto carTypeMap = dictDataMap("car_type");
        const auto carVehicleMap = dictDataMap("car_vehicle");
        const auto escapedTypeMap = dictDataMap("escaped_type");
        const auto isExceptMap = dictDataMap("is_except");
        const auto checkStatusMap = dictDataMap("check_status");
        const auto passTypeMap = dictDataMap("run_type");  // 取而不用：Java 里那行被注释掉了
        (void)passTypeMap;

        // 字典标签是**无条件**覆盖（与 exportOrgId 的"有才覆盖"不同）：
        // 码值不在字典里时 CommonUtil.isNull(null) 给出空串，单元格就是空的。
        auto label = [](const std::map<std::string, std::string>& m, const std::string& code) {
            auto it = m.find(code);
            return it == m.end() ? std::string() : it->second;
        };
        for (Json& dp : list) {
            const std::string createTime = cm::jstr(dp, "createTime");
            if (!createTime.empty()) dp["createTimeStr"] = Json(createTime);
            dp["plateColor"] = Json(label(plateColorMap, cm::jstr(dp, "plateColor")));
            dp["carType"] = Json(label(carTypeMap, cm::jstr(dp, "carType")));
            dp["carVehicle"] = Json(label(carVehicleMap, cm::jstr(dp, "carVehicle")));
            dp["escapedType"] = Json(label(escapedTypeMap, cm::jstr(dp, "escapedType")));
            dp["isExcept"] = Json(label(isExceptMap, cm::jstr(dp, "isExcept")));
            dp["checkStatus"] = Json(label(checkStatusMap, cm::jstr(dp, "checkStatus")));

            // 通行/门架的时间与地点各是"入口 + 至 + 出口"的两段拼接，缺一段就不出现"至"
            auto joinRange = [&](const char* head, const char* tail) {
                std::string out = cm::jstr(dp, head);
                const std::string rhs = cm::jstr(dp, tail);
                if (!rhs.empty()) out += "至" + rhs;
                return out;
            };
            dp["txTime"] = Json(joinRange("inTime", "outTime"));
            dp["mjTime"] = Json(joinRange("gantryTime", "outGantryTime"));
            dp["txAddress"] = Json(joinRange("inStation", "outStation"));
            dp["mjAddress"] = Json(joinRange("gantrytStation", "outGantrytStation"));
        }

        // 列集合与顺序由模板第二行的 {{$fe:entitylist t.plateColor | t.carNo | …}} 决定
        static const std::vector<TplCol> cols = {
            {"车牌颜色", "plateColor"},   {"车牌号", "carNo"},
            {"车种", "carVehicle"},       {"通行时间", "txTime"},
            {"入口站及出口站", "txAddress"}, {"经过门架时间", "mjTime"},
            {"起始门架及终止门架", "mjAddress"}, {"轴数", "carNum", true},
            {"通行标识", "passType"},     {"逃费类型", "escapedType"},
            {"是否为可疑车辆", "isExcept"}, {"稽查状态", "checkStatus"},
            {"备注", "remark"},           {"录入时间", "createTimeStr"},
        };
        return streamTemplate(cols, list);
    }).permi("manager:suspicious:export");
}

} // namespace cm::web
