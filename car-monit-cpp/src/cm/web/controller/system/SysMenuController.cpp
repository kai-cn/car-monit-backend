// 对应 Java: com.ruoyi.web.controller.system.SysMenuController
#include "cm/web/controller/system/SysAuthControllers.hpp"

#include <string>
#include <vector>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysMenuService.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::constant::Constants;
using cm::constant::UserConstants;
using cm::core::domain::AjaxResult;
using cm::security::SecurityUtils;
using cm::system::service::SysMenuService;

/** Spring 把 query 参数绑定到 SysMenu；这里只绑定 XML <if> 真正用到的三列 */
cm::domain::SysMenu bindMenuQuery(RequestContext& ctx) {
    cm::domain::SysMenu menu;
    if (auto v = ctx.optParam("menuName")) menu.menuName = v;
    if (auto v = ctx.optParam("visible")) menu.visible = v;
    if (auto v = ctx.optParam("status")) menu.status = v;
    return menu;
}

Json menuArray(const std::vector<cm::domain::SysMenu>& menus) {
    Json arr = Json::array();
    for (const auto& m : menus) arr.push_back(m.toJson());
    return arr;
}

Json idArray(const std::vector<long long>& ids) {
    Json arr = Json::array();
    for (long long v : ids) arr.push_back(v);
    return arr;
}

/** 对应 Java 的 isFrame == YES_FRAME && path 不是 http(s) 开头 */
bool badExternalPath(const cm::domain::SysMenu& menu) {
    if (menu.isFrame.value_or("") != UserConstants::YES_FRAME) return false;
    const std::string path = menu.path.value_or("");
    return !(utils::StringUtils::startsWith(path, Constants::HTTP) ||
             utils::StringUtils::startsWith(path, Constants::HTTPS));
}

} // namespace

void registerSysMenuController(Router& r) {
    // GET /system/menu/list
    r.get("/system/menu/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto menu = bindMenuQuery(ctx);
        auto menus = SysMenuService::selectMenuList(menu, SecurityUtils::getUserId());
        return BaseController::ok(AjaxResult::success(menuArray(menus)));
    }).permi("system:menu:list");

    // GET /system/menu/{menuId}
    r.get("/system/menu/{menuId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto menu = SysMenuService::selectMenuById(ctx.pathVarLong("menuId"));
        return BaseController::ok(AjaxResult::success(menu ? menu->toJson() : Json(nullptr)));
    }).permi("system:menu:query");

    // GET /system/menu/treeselect —— Java 侧没有 @PreAuthorize
    r.get("/system/menu/treeselect", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto menu = bindMenuQuery(ctx);
        auto menus = SysMenuService::selectMenuList(menu, SecurityUtils::getUserId());
        return BaseController::ok(AjaxResult::success(SysMenuService::buildMenuTreeSelect(menus)));
    });

    // GET /system/menu/roleMenuTreeselect/{roleId}
    // Java: AjaxResult.success() 后 put("checkedKeys"), put("menus")，
    // 输出顺序仍由 HashMap 桶序决定（AjaxResult extends HashMap）
    r.get("/system/menu/roleMenuTreeselect/{roleId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const long long roleId = ctx.pathVarLong("roleId");
        auto menus = SysMenuService::selectMenuList(SecurityUtils::getUserId());
        AjaxResult ajax = AjaxResult::success();
        ajax.put("checkedKeys", idArray(SysMenuService::selectMenuListByRoleId(roleId)));
        ajax.put("menus", SysMenuService::buildMenuTreeSelect(menus));
        return BaseController::ok(ajax);
    });

    // POST /system/menu
    r.post("/system/menu", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysMenu menu;
        menu.fromJson(ctx.body());
        if (UserConstants::NOT_UNIQUE_OLD == SysMenuService::checkMenuNameUnique(menu)) {
            return BaseController::ok(AjaxResult::error(
                "新增菜单'" + menu.menuName.value_or("") + "'失败，菜单名称已存在"));
        }
        if (badExternalPath(menu)) {
            return BaseController::ok(AjaxResult::error(
                "新增菜单'" + menu.menuName.value_or("") + "'失败，地址必须以http(s)://开头"));
        }
        menu.createBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysMenuService::insertMenu(menu)));
    }).permi("system:menu:add");

    // PUT /system/menu
    r.put("/system/menu", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysMenu menu;
        menu.fromJson(ctx.body());
        if (UserConstants::NOT_UNIQUE_OLD == SysMenuService::checkMenuNameUnique(menu)) {
            return BaseController::ok(AjaxResult::error(
                "修改菜单'" + menu.menuName.value_or("") + "'失败，菜单名称已存在"));
        }
        if (badExternalPath(menu)) {
            return BaseController::ok(AjaxResult::error(
                "修改菜单'" + menu.menuName.value_or("") + "'失败，地址必须以http(s)://开头"));
        }
        // Java: menu.getMenuId().equals(menu.getParentId()) —— menuId 为 null 时直接 NPE
        if (!menu.menuId) throw cm::exception::NullPointerException();
        if (menu.menuId == menu.parentId) {
            return BaseController::ok(AjaxResult::error(
                "修改菜单'" + menu.menuName.value_or("") + "'失败，上级菜单不能选择自己"));
        }
        menu.updateBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysMenuService::updateMenu(menu)));
    }).permi("system:menu:edit");

    // DELETE /system/menu/{menuId}
    r.del("/system/menu/{menuId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const long long menuId = ctx.pathVarLong("menuId");
        if (SysMenuService::hasChildByMenuId(menuId)) {
            return BaseController::ok(AjaxResult::error("存在子菜单,不允许删除"));
        }
        if (SysMenuService::checkMenuExistRole(menuId)) {
            return BaseController::ok(AjaxResult::error("菜单已分配,不允许删除"));
        }
        return BaseController::ok(BaseController::toAjax(SysMenuService::deleteMenuById(menuId)));
    }).permi("system:menu:remove");
}

} // namespace cm::web
