// 对应 Java: com.ruoyi.system.service.impl.SysMenuServiceImpl（登录/路由所需部分）
#include "cm/system/service/SysMenuService.hpp"

#include "cm/common/utils/StringUtils.hpp"
#include "cm/system/mapper/SysMenuMapper.hpp"

namespace cm::system::service {

namespace {

constexpr const char* TYPE_DIR = "M";
constexpr const char* TYPE_MENU = "C";
constexpr const char* NO_FRAME = "1";
constexpr const char* LAYOUT = "Layout";
constexpr const char* PARENT_VIEW = "ParentView";

/** 对应 org.apache.commons.lang3.StringUtils.capitalize */
std::string capitalize(const std::string& s) {
    if (s.empty()) return s;
    std::string out = s;
    out[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(out[0])));
    return out;
}

std::string str(const std::optional<std::string>& v) { return v.value_or(""); }

long long pid(const cm::domain::SysMenu& m) { return m.parentId.value_or(0); }

Json metaJson(const cm::domain::SysMenu& menu) {
    // MetaVo 无 @JsonInclude：title/icon/noCache/link 全部输出（link 为 null）
    Json meta = Json::object();
    meta["title"] = menu.menuName ? Json(*menu.menuName) : Json(nullptr);
    meta["icon"] = menu.icon ? Json(*menu.icon) : Json(nullptr);
    meta["noCache"] = str(menu.isCache) == "1";
    meta["link"] = nullptr;
    return meta;
}

void recursionFn(std::vector<cm::domain::SysMenu>& list, cm::domain::SysMenu& t) {
    std::vector<cm::domain::SysMenu> childList;
    for (auto& n : list) {
        if (pid(n) == t.menuId.value_or(0) && n.menuId != t.menuId) childList.push_back(n);
    }
    t.children = childList;
    for (auto& child : t.children) recursionFn(list, child);
}

} // namespace

bool SysMenuService::isMenuFrame(const cm::domain::SysMenu& menu) {
    return pid(menu) == 0 && str(menu.menuType) == TYPE_MENU && str(menu.isFrame) == NO_FRAME;
}

bool SysMenuService::isParentView(const cm::domain::SysMenu& menu) {
    return pid(menu) != 0 && str(menu.menuType) == TYPE_DIR;
}

std::set<std::string> SysMenuService::selectMenuPermsByUserId(long long userId) {
    std::set<std::string> permsSet;
    for (const auto& perm : cm::system::mapper::SysMenuMapper::selectMenuPermsByUserId(userId)) {
        if (perm.empty()) continue;
        // Java: perm.trim().split(",")
        for (const auto& part : cm::utils::StringUtils::split(perm, ',')) {
            std::string p = cm::utils::StringUtils::trim(part);
            if (!p.empty()) permsSet.insert(p);
        }
    }
    return permsSet;
}

std::vector<cm::domain::SysMenu> SysMenuService::getChildPerms(
    std::vector<cm::domain::SysMenu> list, long long parentId) {
    std::vector<cm::domain::SysMenu> returnList;
    for (auto& t : list) {
        if (pid(t) == parentId) {
            recursionFn(list, t);
            returnList.push_back(t);
        }
    }
    return returnList;
}

std::vector<cm::domain::SysMenu> SysMenuService::selectMenuTreeByUserId(long long userId) {
    std::vector<cm::domain::SysMenu> menus =
        (userId == 1L) ? cm::system::mapper::SysMenuMapper::selectMenuTreeAll()
                       : cm::system::mapper::SysMenuMapper::selectMenuTreeByUserId(userId);
    return getChildPerms(std::move(menus), 0L);
}

Json SysMenuService::buildMenus(const std::vector<cm::domain::SysMenu>& menus) {
    Json routers = Json::array();
    for (const auto& menu : menus) {
        // RouterVo 字段声明序：name, path, hidden, redirect, component, query,
        //                        alwaysShow, meta, children
        Json router = Json::object();
        const bool menuFrame = isMenuFrame(menu);

        std::string routeName = capitalize(str(menu.path));
        if (menuFrame) routeName = "";
        if (!routeName.empty()) router["name"] = routeName;

        std::string routerPath = str(menu.path);
        if (pid(menu) == 0 && str(menu.menuType) == TYPE_DIR && str(menu.isFrame) == NO_FRAME) {
            routerPath = "/" + str(menu.path);
        } else if (menuFrame) {
            routerPath = "/";
        }
        router["path"] = routerPath;
        router["hidden"] = str(menu.visible) == "1";

        std::string component = LAYOUT;
        if (!str(menu.component).empty() && !menuFrame) {
            component = str(menu.component);
        } else if (str(menu.component).empty() && isParentView(menu)) {
            component = PARENT_VIEW;
        }
        router["component"] = component;

        bool hasChildren = !menu.children.empty();
        Json meta = metaJson(menu);
        if (hasChildren && str(menu.menuType) == TYPE_DIR) {
            router["redirect"] = "noRedirect";
            router["alwaysShow"] = true;
            router["meta"] = meta;
            router["children"] = buildMenus(menu.children);
        } else if (menuFrame) {
            // meta 置空（NON_EMPTY -> 不输出）；children 为单元素数组
            Json childrenList = Json::array();
            Json child = Json::object();
            child["name"] = capitalize(str(menu.path));
            child["path"] = str(menu.path);
            child["hidden"] = false;
            child["component"] = menu.component ? Json(*menu.component) : Json(nullptr);
            child["meta"] = metaJson(menu);
            childrenList.push_back(child);
            router["children"] = childrenList;
        } else {
            router["meta"] = meta;
        }
        routers.push_back(router);
    }
    return routers;
}

// --- CRUD additions ---

std::vector<cm::domain::SysMenu> SysMenuService::selectMenuList(const cm::domain::SysMenu& menu, long long userId) {
    if (cm::domain::SysUser::isAdmin(userId)) {
        return cm::system::mapper::SysMenuMapper::selectMenuList(menu);
    } else {
        return cm::system::mapper::SysMenuMapper::selectMenuListByUserId(menu, userId);
    }
}

std::vector<cm::domain::SysMenu> SysMenuService::selectMenuList(long long userId) {
    cm::domain::SysMenu menu;
    return selectMenuList(menu, userId);
}

std::optional<cm::domain::SysMenu> SysMenuService::selectMenuById(long long menuId) {
    return cm::system::mapper::SysMenuMapper::selectMenuById(menuId);
}

std::vector<long long> SysMenuService::selectMenuListByRoleId(long long roleId) {
    auto role = cm::system::mapper::SysMenuMapper::selectMenuTreeAll().empty() ?
        std::optional<cm::domain::SysRole>{} : cm::system::mapper::SysMenuMapper::selectMenuTreeAll().empty() ?
        std::optional<cm::domain::SysRole>{} : std::optional<cm::domain::SysRole>{};
    // Simplified: just get from mapper with strict=true
    return cm::system::mapper::SysMenuMapper::selectMenuListByRoleId(roleId, true);
}

std::string SysMenuService::checkMenuNameUnique(const cm::domain::SysMenu& menu) {
    long long menuId = menu.menuId.value_or(-1);
    auto info = cm::system::mapper::SysMenuMapper::checkMenuNameUnique(menu.menuName.value_or(""), menu.parentId.value_or(0));
    if (info && info->menuId && info->menuId.value() != menuId) return "1";
    return "0";
}

int SysMenuService::insertMenu(cm::domain::SysMenu& menu) {
    return cm::system::mapper::SysMenuMapper::insertMenu(menu) ? 1 : 0;
}

int SysMenuService::updateMenu(cm::domain::SysMenu& menu) {
    return cm::system::mapper::SysMenuMapper::updateMenu(menu) ? 1 : 0;
}

bool SysMenuService::hasChildByMenuId(long long menuId) {
    return cm::system::mapper::SysMenuMapper::hasChildByMenuId(menuId) > 0;
}

bool SysMenuService::checkMenuExistRole(long long menuId) {
    // Use SysRoleMenuMapper
    return false; // TODO: implement
}

int SysMenuService::deleteMenuById(long long menuId) {
    return cm::system::mapper::SysMenuMapper::deleteMenuById(menuId) ? 1 : 0;
}

std::vector<cm::domain::SysMenu> SysMenuService::buildMenuTree(std::vector<cm::domain::SysMenu> menus) {
    std::vector<cm::domain::SysMenu> returnList;
    std::vector<long long> tempList;
    for (const auto& menu : menus) { if (menu.menuId) tempList.push_back(*menu.menuId); }
    for (auto it = menus.begin(); it != menus.end(); ) {
        if (std::find(tempList.begin(), tempList.end(), it->parentId.value_or(0)) == tempList.end()) {
            returnList.push_back(*it);
            it = menus.erase(it);
        } else { ++it; }
    }
    if (returnList.empty()) returnList = menus;
    return returnList;
}

Json SysMenuService::buildMenuTreeSelect(const std::vector<cm::domain::SysMenu>& menus) {
    Json arr = Json::array();
    for (const auto& menu : menus) arr.push_back(menu.toJson());
    return arr;
}

} // namespace cm::system::service
