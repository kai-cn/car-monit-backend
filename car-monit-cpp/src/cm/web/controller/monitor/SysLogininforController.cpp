// 对应 Java: com.ruoyi.web.controller.monitor.SysLogininforController
#include "cm/web/controller/monitor/SysLogininforController.hpp"

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/Convert.hpp"
#include "cm/common/utils/Excel.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/domain/SysLogininfor.hpp"
#include "cm/system/service/SysLogininforService.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {

namespace {

cm::domain::SysLogininfor bindLogininfor(RequestContext& ctx) {
    cm::domain::SysLogininfor li;
    if (auto v = ctx.optParam("ipaddr")) li.ipaddr = *v;
    if (auto v = ctx.optParam("status")) li.status = *v;
    if (auto v = ctx.optParam("userName")) li.userName = *v;
    // params.beginTime / params.endTime
    if (auto v = ctx.optParam("params[beginTime]")) li.params["beginTime"] = *v;
    if (auto v = ctx.optParam("params[endTime]")) li.params["endTime"] = *v;
    return li;
}

std::vector<cm::common::utils::ExcelColumn> logininforColumns() {
    return {
        {"序号", "infoId", true, 10},
        {"用户账号", "userName", false, 20},
        {"登录状态", "status", false, 10},
        {"登录地址", "ipaddr", false, 20},
        {"登录地点", "loginLocation", false, 20},
        {"浏览器", "browser", false, 15},
        {"操作系统", "os", false, 15},
        {"提示消息", "msg", false, 30},
        {"访问时间", "loginTime", false, 25},
    };
}

} // namespace

void registerSysLogininforController(Router& r) {
    // GET /monitor/logininfor/list
    r.get("/monitor/logininfor/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto logininfor = bindLogininfor(ctx);
        auto page = ctx.pageRequest();

        // 构造 count/data SQL
        std::string baseSql = "SELECT info_id, user_name, ipaddr, login_location, browser, os, status, msg, login_time FROM sys_logininfor";
        std::string where;
        if (logininfor.ipaddr && !logininfor.ipaddr->empty()) {
            where += " AND ipaddr LIKE " + cm::db::Db::lit("%" + *logininfor.ipaddr + "%");
        }
        if (logininfor.status && !logininfor.status->empty()) {
            where += " AND status = " + cm::db::Db::lit(*logininfor.status);
        }
        if (logininfor.userName && !logininfor.userName->empty()) {
            where += " AND user_name LIKE " + cm::db::Db::lit("%" + *logininfor.userName + "%");
        }
        if (logininfor.params.contains("beginTime") && logininfor.params["beginTime"].is_string()) {
            std::string bt = logininfor.params["beginTime"].get<std::string>();
            if (!bt.empty()) {
                where += " AND date_format(login_time,'%y%m%d') >= date_format(" + cm::db::Db::lit(bt) + ",'%y%m%d')";
            }
        }
        if (logininfor.params.contains("endTime") && logininfor.params["endTime"].is_string()) {
            std::string et = logininfor.params["endTime"].get<std::string>();
            if (!et.empty()) {
                where += " AND date_format(login_time,'%y%m%d') <= date_format(" + cm::db::Db::lit(et) + ",'%y%m%d')";
            }
        }
        std::string countSql = "SELECT COUNT(*) FROM sys_logininfor";
        if (!where.empty()) countSql += " WHERE" + where.substr(4);
        std::string dataSql = baseSql;
        if (!where.empty()) dataSql += " WHERE" + where.substr(4);
        dataSql += " ORDER BY info_id DESC";

        auto pr = cm::db::queryPage(countSql, dataSql, page);
        Json rows = Json::array();
        for (const auto& row : pr.rows.rows) {
            rows.push_back(cm::domain::SysLogininfor::fromRow(row).toJson());
        }
        return BaseController::ok(BaseController::dataTable(rows, pr.total));
    }).permi("monitor:logininfor:list");

    // GET /monitor/logininfor/export
    r.get("/monitor/logininfor/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto logininfor = bindLogininfor(ctx);
        auto list = cm::system::service::SysLogininforService::selectLogininforList(logininfor);

        auto columns = logininforColumns();
        std::vector<Json> jsonRows;
        for (const auto& item : list) jsonRows.push_back(item.toJson());
        // 对应 ExcelUtil.exportExcel：落盘真 xlsx，响应是 success(filename) —— String 走 msg 重载
        const std::string filename = cm::common::utils::Excel::encodingFilename("登录日志");
        cm::common::utils::Excel::writeDownloadFile(
            filename, cm::common::utils::Excel::exportXlsx(columns, jsonRows, "登录日志"));
        return BaseController::ok(cm::core::domain::AjaxResult::success(filename));
    }).permi("monitor:logininfor:export");

    // DELETE /monitor/logininfor/{infoIds}
    r.del("/monitor/logininfor/{infoIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string infoIdsStr = ctx.pathVar("infoIds");
        auto ids = cm::utils::Convert::toLongArray(infoIdsStr, ",");
        int rows = cm::system::service::SysLogininforService::deleteLogininforByIds(ids);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("monitor:logininfor:remove");

    // DELETE /monitor/logininfor/clean
    r.del("/monitor/logininfor/clean", [](RequestContext&) -> cm::http::ApiResponse {
        cm::system::service::SysLogininforService::cleanLogininfor();
        return BaseController::ok(BaseController::success());
    }).permi("monitor:logininfor:remove");
}

} // namespace cm::web
