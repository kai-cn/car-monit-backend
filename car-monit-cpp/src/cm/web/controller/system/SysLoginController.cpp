// 对应 Java: com.ruoyi.web.controller.system.SysLoginController
#include <string>
#include <set>
#include <vector>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/core/domain/model/LoginBody.hpp"
#include "cm/common/utils/JavaCollections.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/service/LoginServices.hpp"
#include "cm/system/service/SysMenuService.hpp"
#include "cm/web/controller/Controllers.hpp"
#include "cm/web/util/CommonUtil.hpp"

namespace cm::web {

namespace {

Json toJsonArray(const std::vector<std::string>& ordered) {
    Json arr = Json::array();
    for (const auto& s : ordered) arr.push_back(s);
    return arr;
}

Json setToJson(const std::set<std::string>& values) {
    std::vector<std::string> keys(values.begin(), values.end());
    // Java HashSet 迭代顺序
    return toJsonArray(cm::utils::javaSetOrder(keys));
}

} // namespace

void registerLoginController(Router& r) {
    // POST /login —— @RequestBody LoginBody
    r.post("/login", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::LoginBody loginBody;
        loginBody.fromJson(body);

        const std::string curPassword = loginBody.password.value_or("");
        if (cm::web::util::CommonUtil::checkPassword(curPassword)) {
            auto a = cm::core::domain::AjaxResult::error(
                "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！");
            return cm::http::ApiResponse::json(a.toJson());
        }

        std::string token = cm::security::SysLoginService::login(
            loginBody.username.value_or(""), curPassword, loginBody.code.value_or(""),
            loginBody.uuid, ctx.req);

        auto ajax = cm::core::domain::AjaxResult::success();
        ajax.put(cm::constant::Constants::TOKEN, token);
        return cm::http::ApiResponse::json(ajax.toJson());
    }).permitAll();

    // GET /getInfo
    r.get("/getInfo", [](RequestContext&) -> cm::http::ApiResponse {
        auto loginUser = cm::security::SecurityUtils::getLoginUser();
        const cm::domain::SysUser& user = loginUser.user;

        auto roles = cm::security::SysPermissionService::getRolePermission(user);
        auto permissions = cm::security::SysPermissionService::getMenuPermission(user);

        auto ajax = cm::core::domain::AjaxResult::success();
        ajax.put("user", user.toJson());
        ajax.put("roles", setToJson(roles));
        ajax.put("permissions", setToJson(permissions));
        ajax.put("pjFlag", 0);
        ajax.put("overdue", false);
        return cm::http::ApiResponse::json(ajax.toJson());
    });

    // GET /getRouters
    r.get("/getRouters", [](RequestContext&) -> cm::http::ApiResponse {
        long long userId = cm::security::SecurityUtils::getUserId();
        if (userId < 0) userId = -9999L; // Java: null -> -9999L
        auto menus = cm::system::service::SysMenuService::selectMenuTreeByUserId(userId);
        auto routers = cm::system::service::SysMenuService::buildMenus(menus);
        auto a = cm::core::domain::AjaxResult::success(routers);
        return cm::http::ApiResponse::json(a.toJson());
    });
}

} // namespace cm::web
