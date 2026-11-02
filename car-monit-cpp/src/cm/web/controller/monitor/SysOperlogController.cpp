// 对应 Java: com.ruoyi.web.controller.monitor.SysOperlogController
#include "cm/web/controller/monitor/SysOperlogController.hpp"

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/Convert.hpp"
#include "cm/common/utils/Excel.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/domain/SysOperLog.hpp"
#include "cm/system/service/SysOperLogService.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {

namespace {

cm::domain::SysOperLog bindOperLog(RequestContext& ctx) {
    cm::domain::SysOperLog log;
    if (auto v = ctx.optParam("title")) log.title = *v;
    if (auto v = ctx.optParam("businessType")) log.businessType = cm::utils::Convert::toLong(*v);
    if (auto v = ctx.optParam("status")) log.status = cm::utils::Convert::toLong(*v);
    if (auto v = ctx.optParam("operName")) log.operName = *v;
    // params.beginTime / params.endTime
    if (auto v = ctx.optParam("params[beginTime]")) log.params["beginTime"] = *v;
    if (auto v = ctx.optParam("params[endTime]")) log.params["endTime"] = *v;
    return log;
}

std::vector<cm::common::utils::ExcelColumn> operlogColumns() {
    return {
        {"操作序号", "operId", true, 10},
        {"操作模块", "title", false, 20},
        {"业务类型", "businessType", true, 10},
        {"请求方法", "method", false, 30},
        {"请求方式", "requestMethod", false, 10},
        {"操作类别", "operatorType", true, 10},
        {"操作人员", "operName", false, 15},
        {"部门名称", "deptName", false, 15},
        {"请求地址", "operUrl", false, 30},
        {"操作地址", "operIp", false, 20},
        {"操作地点", "operLocation", false, 20},
        {"请求参数", "operParam", false, 40},
        {"返回参数", "jsonResult", false, 40},
        {"状态", "status", true, 10},
        {"错误消息", "errorMsg", false, 30},
        {"操作时间", "operTime", false, 25},
    };
}

} // namespace

void registerSysOperlogController(Router& r) {
    // GET /monitor/operlog/list
    r.get("/monitor/operlog/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto operLog = bindOperLog(ctx);
        auto page = ctx.pageRequest();

        // 构造 count/data SQL
        std::string baseSql = "SELECT oper_id, title, business_type, method, request_method, operator_type, "
                              "oper_name, dept_name, oper_url, oper_ip, oper_location, oper_param, json_result, "
                              "status, error_msg, oper_time FROM sys_oper_log";
        std::string where;
        if (operLog.title && !operLog.title->empty()) {
            where += " AND title LIKE " + cm::db::Db::lit("%" + *operLog.title + "%");
        }
        if (operLog.businessType) {
            where += " AND business_type = " + cm::db::Db::lit(*operLog.businessType);
        }
        if (!operLog.businessTypes.empty()) {
            where += " AND business_type IN " + cm::db::Db::inList(operLog.businessTypes);
        }
        if (operLog.status) {
            where += " AND status = " + cm::db::Db::lit(*operLog.status);
        }
        if (operLog.operName && !operLog.operName->empty()) {
            where += " AND oper_name LIKE " + cm::db::Db::lit("%" + *operLog.operName + "%");
        }
        if (operLog.params.contains("beginTime") && operLog.params["beginTime"].is_string()) {
            std::string bt = operLog.params["beginTime"].get<std::string>();
            if (!bt.empty()) {
                where += " AND date_format(oper_time,'%y%m%d') >= date_format(" + cm::db::Db::lit(bt) + ",'%y%m%d')";
            }
        }
        if (operLog.params.contains("endTime") && operLog.params["endTime"].is_string()) {
            std::string et = operLog.params["endTime"].get<std::string>();
            if (!et.empty()) {
                where += " AND date_format(oper_time,'%y%m%d') <= date_format(" + cm::db::Db::lit(et) + ",'%y%m%d')";
            }
        }
        std::string countSql = "SELECT COUNT(*) FROM sys_oper_log";
        if (!where.empty()) countSql += " WHERE" + where.substr(4);
        std::string dataSql = baseSql;
        if (!where.empty()) dataSql += " WHERE" + where.substr(4);
        dataSql += " ORDER BY oper_id DESC";

        auto pr = cm::db::queryPage(countSql, dataSql, page);
        Json rows = Json::array();
        for (const auto& row : pr.rows.rows) {
            rows.push_back(cm::domain::SysOperLog::fromRow(row).toJson());
        }
        return BaseController::ok(BaseController::dataTable(rows, pr.total));
    }).permi("monitor:operlog:list");

    // GET /monitor/operlog/export
    r.get("/monitor/operlog/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto operLog = bindOperLog(ctx);
        auto list = cm::system::service::SysOperLogService::selectOperLogList(operLog);

        auto columns = operlogColumns();
        std::vector<Json> jsonRows;
        for (const auto& item : list) jsonRows.push_back(item.toJson());
        std::string csv = cm::common::utils::Excel::exportCsv(columns, jsonRows, "操作日志");

        cm::http::ApiResponse resp;
        resp.status = 200;
        resp.content_type = "text/csv;charset=UTF-8";
        resp.body = std::move(csv);
        resp.headers["Content-Disposition"] = "attachment; filename=operlog.csv";
        return resp;
    }).permi("monitor:operlog:export");

    // DELETE /monitor/operlog/{operIds}
    r.del("/monitor/operlog/{operIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string operIdsStr = ctx.pathVar("operIds");
        auto ids = cm::utils::Convert::toLongArray(operIdsStr, ",");
        int rows = cm::system::service::SysOperLogService::deleteOperLogByIds(ids);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("monitor:operlog:remove");

    // DELETE /monitor/operlog/clean
    r.del("/monitor/operlog/clean", [](RequestContext&) -> cm::http::ApiResponse {
        cm::system::service::SysOperLogService::cleanOperLog();
        return BaseController::ok(BaseController::success());
    }).permi("monitor:operlog:remove");
}

} // namespace cm::web
