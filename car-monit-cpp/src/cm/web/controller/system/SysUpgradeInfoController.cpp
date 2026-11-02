// 对应 Java: SysUpgradeInfoController
#include "cm/web/BaseController.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysUpgradeInfoService.hpp"

namespace cm::web {

void registerSysUpgradeInfoController(cm::web::Router& r) {
    r.get("/system/upgradeInfo/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysUpgradeInfo info;
        info.id = ctx.optParam("id");
        info.ver = ctx.optParam("ver");
        info.tenantId = cm::security::SecurityUtils::getTenantId();
        auto list = cm::system::service::SysUpgradeInfoService::selectSysUpgradeInfoList(info);
        Json rowsArr = Json::array();
        for (const auto& i : list) rowsArr.push_back(i.toJson());
        auto countSql = "select count(1) from sys_upgrade_info where del_flag='0'";
        auto dataSql = "select * from sys_upgrade_info where del_flag='0'";
        auto result = cm::db::queryPage(countSql, dataSql, page);
        return BaseController::ok(BaseController::dataTable(rowsArr, result.total));
    });

    r.get("/system/upgradeInfo/newest", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUpgradeInfo info;
        auto newest = cm::system::service::SysUpgradeInfoService::selectSysUpgradeInfoNewest(info);
        if (newest) {
            return BaseController::ok(BaseController::success(newest->toJson()));
        }
        return BaseController::ok(BaseController::success());
    });

    r.get("/system/upgradeInfo/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUpgradeInfo info;
        info.id = ctx.optParam("id");
        info.ver = ctx.optParam("ver");
        auto list = cm::system::service::SysUpgradeInfoService::selectSysUpgradeInfoList(info);
        return BaseController::ok(BaseController::success(std::string("Excel导出功能未实现")));
    });

    r.get("/system/upgradeInfo/{id}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string id = ctx.pathVar("id");
        auto info = cm::system::service::SysUpgradeInfoService::selectSysUpgradeInfoById(id);
        if (info) {
            return BaseController::ok(BaseController::success(info->toJson()));
        }
        return BaseController::ok(BaseController::error("升级信息不存在"));
    });

    r.post("/system/upgradeInfo", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysUpgradeInfo info;
        info.fromJson(body);
        auto result = cm::system::service::SysUpgradeInfoService::saveSysUpgradeInfo(info);
        return BaseController::ok(result);
    });

    r.put("/system/upgradeInfo", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysUpgradeInfo info;
        info.fromJson(body);
        auto result = cm::system::service::SysUpgradeInfoService::saveSysUpgradeInfo(info);
        return BaseController::ok(result);
    });

    r.del("/system/upgradeInfo/{ids}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string idsStr = ctx.pathVar("ids");
        std::vector<std::string> ids;
        std::string cur;
        for (char c : idsStr) {
            if (c == ',') {
                if (!cur.empty()) { ids.push_back(cur); cur.clear(); }
            } else cur += c;
        }
        if (!cur.empty()) ids.push_back(cur);
        auto result = cm::system::service::SysUpgradeInfoService::deleteSysUpgradeInfoByIds(ids);
        return BaseController::ok(result);
    });
}

} // namespace cm::web
