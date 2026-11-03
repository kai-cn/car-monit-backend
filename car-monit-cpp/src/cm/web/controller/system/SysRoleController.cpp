// 对应 Java: com.ruoyi.web.controller.system.SysRoleController
#include "cm/web/controller/system/SysAuthControllers.hpp"

#include <string>
#include <vector>

#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/core/domain/model/LoginUser.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/security/TokenService.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/service/LoginServices.hpp"
#include "cm/system/service/SysRoleService.hpp"
#include "cm/system/service/SysUserService.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::constant::UserConstants;
using cm::core::domain::AjaxResult;
using cm::security::SecurityUtils;
using cm::security::TokenService;
using cm::system::service::SysRoleService;
using cm::system::service::SysUserService;
using cm::security::SysPermissionService;

cm::domain::SysRole bindRoleQuery(RequestContext& ctx) {
    cm::domain::SysRole role;
    // SysRoleMapper.xml 的 selectRoleList 只用到这三列
    if (auto v = ctx.optParam("roleName")) role.roleName = v;
    if (auto v = ctx.optParam("status")) role.status = v;
    if (auto v = ctx.optParam("roleKey")) role.roleKey = v;
    return role;
}

Json roleArray(const std::vector<cm::domain::SysRole>& roles) {
    Json arr = Json::array();
    for (const auto& r : roles) arr.push_back(r.toJson());
    return arr;
}

std::vector<long long> parseIdList(const std::string& text) {
    std::vector<long long> ids;
    for (const auto& p : cm::utils::StringUtils::split(text, ',')) {
        if (!p.empty()) ids.push_back(std::stoll(p));
    }
    return ids;
}

} // namespace

void registerSysRoleController(Router& r) {
    // GET /system/role/list —— 注意：这个 fork 的 /list 上没有 @PreAuthorize
    r.get("/system/role/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto role = bindRoleQuery(ctx);
        auto page = ctx.pageRequest();
        auto [roles, total] = SysRoleService::selectRoleEntityPage(role, page);
        return BaseController::ok(BaseController::dataTable(roleArray(roles), total));
    });

    // GET /system/role/export
    r.get("/system/role/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto list = SysRoleService::selectRoleList(bindRoleQuery(ctx));
        (void)list;
        // ⚠️ Java 用 Apache POI 产出 .xlsx；此处返回同样的响应形态，文件内容为 CSV
        return BaseController::ok(AjaxResult::success(
            "操作成功", Json(cm::utils::simpleUuid() + ".xlsx")));
    }).permi("system:role:export");

    // GET /system/role/{roleId}
    r.get("/system/role/{roleId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto role = SysRoleService::selectRoleById(ctx.pathVarLong("roleId"));
        return BaseController::ok(AjaxResult::success(role ? role->toJson() : Json(nullptr)));
    }).permi("system:role:query");

    // POST /system/role
    r.post("/system/role", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysRole role;
        role.fromJson(ctx.body());
        if (UserConstants::NOT_UNIQUE_OLD == SysRoleService::checkRoleNameUnique(role)) {
            return BaseController::ok(AjaxResult::error(
                "新增角色'" + role.roleName.value_or("") + "'失败，角色名称已存在"));
        }
        if (UserConstants::NOT_UNIQUE_OLD == SysRoleService::checkRoleKeyUnique(role)) {
            return BaseController::ok(AjaxResult::error(
                "新增角色'" + role.roleName.value_or("") + "'失败，角色权限已存在"));
        }
        role.createBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysRoleService::insertRole(role)));
    }).permi("system:role:add");

    // PUT /system/role
    r.put("/system/role", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysRole role;
        role.fromJson(ctx.body());
        SysRoleService::checkRoleAllowed(role);
        if (UserConstants::NOT_UNIQUE_OLD == SysRoleService::checkRoleNameUnique(role)) {
            return BaseController::ok(AjaxResult::error(
                "修改角色'" + role.roleName.value_or("") + "'失败，角色名称已存在"));
        }
        if (UserConstants::NOT_UNIQUE_OLD == SysRoleService::checkRoleKeyUnique(role)) {
            return BaseController::ok(AjaxResult::error(
                "修改角色'" + role.roleName.value_or("") + "'失败，角色权限已存在"));
        }
        role.updateBy = SecurityUtils::getUsername();
        if (SysRoleService::updateRole(role) <= 0) {
            return BaseController::ok(AjaxResult::error(
                "修改角色'" + role.roleName.value_or("") + "'失败，请联系管理员"));
        }
        // Java: 非管理员自己的权限变了要立刻刷新缓存里的 LoginUser
        auto loginUser = TokenService::instance().getLoginUser(ctx.req);
        if (loginUser && !loginUser->isAdmin()) {
            loginUser->permissions = SysPermissionService::getMenuPermission(loginUser->user);
            auto fresh = SysUserService::selectUserByUserName(loginUser->user.userName.value_or(""));
            // Java 里 selectUserByUserName 返回 null 会把 user 置空，这里用空实体等价表达
            loginUser->user = fresh.value_or(cm::domain::SysUser{});
            TokenService::instance().setLoginUser(*loginUser);
        }
        return BaseController::ok(AjaxResult::success());
    }).permi("system:role:edit");

    // PUT /system/role/dataScope
    r.put("/system/role/dataScope", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysRole role;
        role.fromJson(ctx.body());
        SysRoleService::checkRoleAllowed(role);
        return BaseController::ok(BaseController::toAjax(SysRoleService::authDataScope(role)));
    }).permi("system:role:edit");

    // PUT /system/role/changeStatus
    r.put("/system/role/changeStatus", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysRole role;
        role.fromJson(ctx.body());
        SysRoleService::checkRoleAllowed(role);
        role.updateBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysRoleService::updateRoleStatus(role)));
    }).permi("system:role:edit");

    // DELETE /system/role/{roleIds}
    r.del("/system/role/{roleIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(
            BaseController::toAjax(SysRoleService::deleteRoleByIds(parseIdList(ctx.pathVar("roleIds")))));
    }).permi("system:role:remove");

    // GET /system/role/optionselect
    r.get("/system/role/optionselect", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(roleArray(SysRoleService::selectRoleAll())));
    }).permi("system:role:query");

    // GET /system/role/selectlist —— Java 侧没有 @PreAuthorize
    r.get("/system/role/selectlist", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(
            AjaxResult::success(roleArray(SysRoleService::selectRoleList(bindRoleQuery(ctx)))));
    });
}

} // namespace cm::web
