// 对应 Java: com.ruoyi.web.controller.monitor.SysUserOnlineController
#include "cm/web/controller/monitor/SysUserOnlineController.hpp"

#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/domain/SysUserOnline.hpp"
#include "cm/system/service/SysUserOnlineService.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {

void registerSysUserOnlineController(Router& r) {
    // GET /monitor/online/list
    r.get("/monitor/online/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string ipaddr = ctx.param("ipaddr");
        std::string userName = ctx.param("userName");

        auto list = cm::system::service::SysUserOnlineService::selectOnlineByInfo(ipaddr, userName);

        Json rows = Json::array();
        for (const auto& item : list) {
            rows.push_back(item.toJson());
        }
        // Java: getDataTable(userOnlineService.selectOnlineByInfo(ipaddr, userName))
        // 注意：Java 版本没有分页，直接返回所有结果
        return BaseController::ok(BaseController::dataTable(rows, static_cast<long long>(list.size())));
    }).permi("monitor:online:list");

    // DELETE /monitor/online/{tokenId}
    r.del("/monitor/online/{tokenId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string tokenId = ctx.pathVar("tokenId");

        // Java: redisCache.deleteObject(Constants.LOGIN_TOKEN_KEY + tokenId)
        auto& cache = cm::redis::RedisCache::instance();
        std::string key = std::string(cm::constant::Constants::LOGIN_TOKEN_KEY) + tokenId;
        cache.del(key);

        return BaseController::ok(BaseController::success());
    }).permi("monitor:online:forceLogout");
}

} // namespace cm::web
