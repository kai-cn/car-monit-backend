// 对应 Java: com.ruoyi.system.mapper.SysMenuMapper
#include "cm/system/mapper/SysMenuMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

cm::domain::SysMenu SysMenuMapper::mapMenu(const cm::db::Row& row) {
    cm::domain::SysMenu m;
    m.menuId = row.optI64("menu_id");
    m.parentId = row.optI64("parent_id");
    m.menuName = row.get("menu_name");
    m.path = row.get("path");
    m.component = row.get("component");
    m.visible = row.get("visible");
    m.status = row.get("status");
    m.perms = row.get("perms");
    m.isFrame = row.get("is_frame");
    m.isCache = row.get("is_cache");
    m.menuType = row.get("menu_type");
    m.icon = row.get("icon");
    m.orderNum = row.get("order_num");
    return m;
}

std::vector<cm::domain::SysMenu> SysMenuMapper::selectMenuTreeAll() {
    const std::string sql =
        "select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component, m.visible,"
        " m.status, ifnull(m.perms,'') as perms, m.is_frame, m.is_cache, m.menu_type, m.icon,"
        " m.order_num, m.create_time"
        " from sys_menu m where m.menu_type in ('M', 'C') and m.status = 0"
        " order by m.parent_id, m.order_num";
    cm::db::Result res;
    std::vector<cm::domain::SysMenu> menus;
    if (!cm::db::Db::instance().query(sql, res)) return menus;
    for (const auto& row : res.rows) menus.push_back(mapMenu(row));
    return menus;
}

std::vector<cm::domain::SysMenu> SysMenuMapper::selectMenuTreeByUserId(long long userId) {
    const std::string sql =
        "select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component, m.visible,"
        " m.status, ifnull(m.perms,'') as perms, m.is_frame, m.is_cache, m.menu_type, m.icon,"
        " m.order_num, m.create_time"
        " from sys_menu m"
        " left join sys_role_menu rm on m.menu_id = rm.menu_id"
        " left join sys_user_role ur on rm.role_id = ur.role_id"
        " left join sys_role ro on ur.role_id = ro.role_id"
        " left join sys_user u on ur.user_id = u.user_id"
        " where u.user_id = " + cm::db::bind(userId) +
        " and m.menu_type in ('M', 'C') and m.status = 0 AND ro.status = 0"
        " order by m.parent_id, m.order_num";
    cm::db::Result res;
    std::vector<cm::domain::SysMenu> menus;
    if (!cm::db::Db::instance().query(sql, res)) return menus;
    for (const auto& row : res.rows) menus.push_back(mapMenu(row));
    return menus;
}

std::vector<std::string> SysMenuMapper::selectMenuPermsByUserId(long long userId) {
    const std::string sql =
        "select distinct m.perms"
        " from sys_menu m"
        " left join sys_role_menu rm on m.menu_id = rm.menu_id"
        " left join sys_user_role ur on rm.role_id = ur.role_id"
        " left join sys_role r on r.role_id = ur.role_id"
        " where m.status = '0' and r.status = '0' and ur.user_id = " + cm::db::bind(userId);
    cm::db::Result res;
    std::vector<std::string> perms;
    if (!cm::db::Db::instance().query(sql, res)) return perms;
    for (const auto& row : res.rows) {
        if (auto p = row.get("perms")) perms.push_back(*p);
    }
    return perms;
}

// --- CRUD additions ---

std::vector<cm::domain::SysMenu> SysMenuMapper::selectMenuList(const cm::domain::SysMenu& menu) {
    std::string sql = "select menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, ifnull(perms,'') as perms, icon, create_time from sys_menu";
    bool hasWhere = false;
    if (menu.menuName && !menu.menuName->empty()) {
        sql += " where menu_name like " + cm::db::bind("%" + *menu.menuName + "%");
        hasWhere = true;
    }
    if (menu.visible && !menu.visible->empty()) {
        sql += (hasWhere ? " and " : " where ") + std::string("visible = ") + cm::db::bind(*menu.visible);
        hasWhere = true;
    }
    if (menu.status && !menu.status->empty()) {
        sql += (hasWhere ? " and " : " where ") + std::string("status = ") + cm::db::bind(*menu.status);
    }
    sql += " order by parent_id, order_num";
    cm::db::Result res;
    std::vector<cm::domain::SysMenu> menus;
    if (!cm::db::Db::instance().query(sql, res)) return menus;
    for (const auto& row : res.rows) menus.push_back(mapMenu(row));
    return menus;
}

std::vector<cm::domain::SysMenu> SysMenuMapper::selectMenuListByUserId(const cm::domain::SysMenu& menu, long long userId) {
    std::string sql = "select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component, m.visible, m.status, ifnull(m.perms,'') as perms, m.is_frame, m.is_cache, m.menu_type, m.icon, m.order_num, m.create_time"
                      " from sys_menu m"
                      " left join sys_role_menu rm on m.menu_id = rm.menu_id"
                      " left join sys_user_role ur on rm.role_id = ur.role_id"
                      " left join sys_role ro on ur.role_id = ro.role_id"
                      " where ur.user_id = " + cm::db::bind(userId);
    if (menu.menuName && !menu.menuName->empty()) sql += " AND m.menu_name like " + cm::db::bind("%" + *menu.menuName + "%");
    if (menu.visible && !menu.visible->empty()) sql += " AND m.visible = " + cm::db::bind(*menu.visible);
    if (menu.status && !menu.status->empty()) sql += " AND m.status = " + cm::db::bind(*menu.status);
    sql += " order by m.parent_id, m.order_num";
    cm::db::Result res;
    std::vector<cm::domain::SysMenu> menus;
    if (!cm::db::Db::instance().query(sql, res)) return menus;
    for (const auto& row : res.rows) menus.push_back(mapMenu(row));
    return menus;
}

std::optional<cm::domain::SysMenu> SysMenuMapper::selectMenuById(long long menuId) {
    std::string sql = "select menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, ifnull(perms,'') as perms, icon, create_time from sys_menu where menu_id = " + cm::db::bind(menuId);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapMenu(res.rows[0]);
}

int SysMenuMapper::hasChildByMenuId(long long menuId) {
    std::string sql = "select count(1) from sys_menu where parent_id = " + cm::db::bind(menuId);
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

std::optional<cm::domain::SysMenu> SysMenuMapper::checkMenuNameUnique(const std::string& menuName, long long parentId) {
    std::string sql = "select menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, ifnull(perms,'') as perms, icon, create_time from sys_menu where menu_name = " + cm::db::bind(menuName) + " and parent_id = " + cm::db::bind(parentId) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapMenu(res.rows[0]);
}

bool SysMenuMapper::insertMenu(cm::domain::SysMenu& menu) {
    std::string sql = "insert into sys_menu(";
    std::string vals;
    if (menu.menuId && *menu.menuId != 0) { sql += "menu_id,"; vals += cm::db::bind(*menu.menuId) + ","; }
    if (menu.parentId && *menu.parentId != 0) { sql += "parent_id,"; vals += cm::db::bind(*menu.parentId) + ","; }
    if (menu.menuName && !menu.menuName->empty()) { sql += "menu_name,"; vals += cm::db::bind(*menu.menuName) + ","; }
    if (menu.orderNum && !menu.orderNum->empty()) { sql += "order_num,"; vals += cm::db::bind(*menu.orderNum) + ","; }
    if (menu.path && !menu.path->empty()) { sql += "path,"; vals += cm::db::bind(*menu.path) + ","; }
    if (menu.component && !menu.component->empty()) { sql += "component,"; vals += cm::db::bind(*menu.component) + ","; }
    if (menu.isFrame && !menu.isFrame->empty()) { sql += "is_frame,"; vals += cm::db::bind(*menu.isFrame) + ","; }
    if (menu.isCache && !menu.isCache->empty()) { sql += "is_cache,"; vals += cm::db::bind(*menu.isCache) + ","; }
    if (menu.menuType && !menu.menuType->empty()) { sql += "menu_type,"; vals += cm::db::bind(*menu.menuType) + ","; }
    if (menu.visible) { sql += "visible,"; vals += cm::db::bind(*menu.visible) + ","; }
    if (menu.status) { sql += "status,"; vals += cm::db::bind(*menu.status) + ","; }
    if (menu.perms && !menu.perms->empty()) { sql += "perms,"; vals += cm::db::bind(*menu.perms) + ","; }
    if (menu.icon && !menu.icon->empty()) { sql += "icon,"; vals += cm::db::bind(*menu.icon) + ","; }
    if (menu.remark && !menu.remark->empty()) { sql += "remark,"; vals += cm::db::bind(*menu.remark) + ","; }
    if (menu.createBy && !menu.createBy->empty()) { sql += "create_by,"; vals += cm::db::bind(*menu.createBy) + ","; }
    sql += "create_time) values (" + vals + "sysdate())";
    long long insertId = 0;
    bool ok = cm::db::Db::instance().execute(sql, nullptr, &insertId);
    if (ok && insertId > 0) menu.menuId = insertId;
    return ok;
}

bool SysMenuMapper::updateMenu(const cm::domain::SysMenu& menu) {
    std::string sql = "update sys_menu set ";
    if (menu.menuName && !menu.menuName->empty()) sql += "menu_name = " + cm::db::bind(*menu.menuName) + ",";
    if (menu.parentId) sql += "parent_id = " + cm::db::bind(*menu.parentId) + ",";
    if (menu.orderNum && !menu.orderNum->empty()) sql += "order_num = " + cm::db::bind(*menu.orderNum) + ",";
    if (menu.path && !menu.path->empty()) sql += "path = " + cm::db::bind(*menu.path) + ",";
    if (menu.component) sql += "component = " + cm::db::bind(*menu.component) + ",";
    if (menu.isFrame && !menu.isFrame->empty()) sql += "is_frame = " + cm::db::bind(*menu.isFrame) + ",";
    if (menu.isCache && !menu.isCache->empty()) sql += "is_cache = " + cm::db::bind(*menu.isCache) + ",";
    if (menu.menuType && !menu.menuType->empty()) sql += "menu_type = " + cm::db::bind(*menu.menuType) + ",";
    if (menu.visible) sql += "visible = " + cm::db::bind(*menu.visible) + ",";
    if (menu.status) sql += "status = " + cm::db::bind(*menu.status) + ",";
    if (menu.perms) sql += "perms = " + cm::db::bind(*menu.perms) + ",";
    if (menu.icon && !menu.icon->empty()) sql += "icon = " + cm::db::bind(*menu.icon) + ",";
    if (menu.remark) sql += "remark = " + cm::db::bind(*menu.remark) + ",";
    if (menu.updateBy && !menu.updateBy->empty()) sql += "update_by = " + cm::db::bind(*menu.updateBy) + ",";
    sql += "update_time = sysdate() where menu_id = " + cm::db::bind(menu.menuId.value_or(0));
    return cm::db::Db::instance().execute(sql);
}

bool SysMenuMapper::deleteMenuById(long long menuId) {
    std::string sql = "delete from sys_menu where menu_id = " + cm::db::bind(menuId);
    return cm::db::Db::instance().execute(sql);
}

std::vector<long long> SysMenuMapper::selectMenuListByRoleId(long long roleId, bool menuCheckStrictly) {
    std::string sql = "select m.menu_id from sys_menu m left join sys_role_menu rm on m.menu_id = rm.menu_id where rm.role_id = " + cm::db::bind(roleId);
    if (menuCheckStrictly) {
        sql += " and m.menu_id not in (select m.parent_id from sys_menu m inner join sys_role_menu rm on m.menu_id = rm.menu_id and rm.role_id = " + cm::db::bind(roleId) + ")";
    }
    sql += " order by m.parent_id, m.order_num";
    cm::db::Result res;
    std::vector<long long> ids;
    if (!cm::db::Db::instance().query(sql, res)) return ids;
    for (const auto& row : res.rows) {
        auto id = row.optI64("menu_id");
        if (id) ids.push_back(*id);
    }
    return ids;
}

} // namespace cm::system::mapper
