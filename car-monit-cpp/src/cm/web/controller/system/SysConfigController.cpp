// 对应 Java: SysConfigController
#include "cm/web/BaseController.hpp"
#include "cm/common/constant/UserConstants.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysConfigService.hpp"
#include "cm/system/domain/SysConfig.hpp"

namespace cm::web {

void registerSysConfigController(cm::web::Router& r) {
    // GET /system/config/list
    r.get("/system/config/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysConfig config;
        config.configName = ctx.optParam("configName");
        config.configKey = ctx.optParam("configKey");
        config.configType = ctx.optParam("configType");
        auto [list, total] = cm::system::service::SysConfigService::selectConfigListEntityPage(config, page);
        Json rowsArr = Json::array();
        for (const auto& c : list) rowsArr.push_back(c.toJson());
        return BaseController::ok(BaseController::dataTable(rowsArr, total));
    }).permi("system:config:list");

    // GET /system/config/export
    r.get("/system/config/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysConfig config;
        config.configName = ctx.optParam("configName");
        config.configKey = ctx.optParam("configKey");
        config.configType = ctx.optParam("configType");
        auto list = cm::system::service::SysConfigService::selectConfigList(config);
        Json rowsArr = Json::array();
        for (const auto& c : list) rowsArr.push_back(c.toJson());
        // Excel export not implemented in C++
        return BaseController::ok(BaseController::success(std::string("Excel导出功能未实现")));
    }).permi("system:config:export");

    // GET /system/config/{configId}
    r.get("/system/config/{configId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        long long configId = ctx.pathVarLong("configId");
        auto config = cm::system::service::SysConfigService::selectConfigById(configId);
        if (config) {
            return BaseController::ok(BaseController::success(config->toJson()));
        }
        return BaseController::ok(BaseController::error("参数不存在"));
    }).permi("system:config:query");

    // GET /system/config/configKey/{configKey}
    r.get("/system/config/configKey/{configKey}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string configKey = ctx.pathVar("configKey");
        std::string value = cm::system::service::SysConfigService::selectConfigByKey(configKey);
        return BaseController::ok(BaseController::success(value));
    });

    // POST /system/config
    r.post("/system/config", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysConfig config;
        config.fromJson(body);
        if (cm::constant::UserConstants::NOT_UNIQUE_OLD ==
            cm::system::service::SysConfigService::checkConfigKeyUnique(config)) {
            return BaseController::ok(BaseController::error(
                "新增参数'" + config.configName.value_or("") + "'失败，参数键名已存在"));
        }
        config.createBy = cm::security::SecurityUtils::getUsername();
        long long rows = cm::system::service::SysConfigService::insertConfig(config);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:config:add");

    // PUT /system/config
    r.put("/system/config", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysConfig config;
        config.fromJson(body);
        if (cm::constant::UserConstants::NOT_UNIQUE_OLD ==
            cm::system::service::SysConfigService::checkConfigKeyUnique(config)) {
            return BaseController::ok(BaseController::error(
                "修改参数'" + config.configName.value_or("") + "'失败，参数键名已存在"));
        }
        config.updateBy = cm::security::SecurityUtils::getUsername();
        long long rows = cm::system::service::SysConfigService::updateConfig(config);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:config:edit");

    // DELETE /system/config/{configIds}
    r.del("/system/config/{configIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string configIdsStr = ctx.pathVar("configIds");
        std::vector<long long> configIds;
        std::string cur;
        for (char c : configIdsStr) {
            if (c == ',') {
                if (!cur.empty()) { configIds.push_back(std::stoll(cur)); cur.clear(); }
            } else cur += c;
        }
        if (!cur.empty()) configIds.push_back(std::stoll(cur));
        long long rows = cm::system::service::SysConfigService::deleteConfigByIds(configIds);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:config:remove");

    // DELETE /system/config/clearCache
    r.del("/system/config/clearCache", [](RequestContext&) -> cm::http::ApiResponse {
        cm::system::service::SysConfigService::clearCache();
        return BaseController::ok(BaseController::success());
    }).permi("system:config:remove");
}

} // namespace cm::web
