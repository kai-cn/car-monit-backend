// 对应 Java: com.ruoyi.system.mapper.SysRoleMenuMapper
#include "cm/system/mapper/SysRoleMenuMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

bool SysRoleMenuMapper::deleteRoleMenuByRoleId(long long roleId) {
    std::string sql = "delete from sys_role_menu where role_id = " + cm::db::Db::lit(roleId);
    return cm::db::Db::instance().execute(sql);
}

bool SysRoleMenuMapper::deleteRoleMenu(const std::vector<long long>& roleIds) {
    if (roleIds.empty()) return true;
    std::string sql = "delete from sys_role_menu where role_id in " + cm::db::Db::inList(roleIds);
    return cm::db::Db::instance().execute(sql);
}

bool SysRoleMenuMapper::batchRoleMenu(const std::vector<std::pair<long long, long long>>& roleMenus) {
    if (roleMenus.empty()) return true;
    std::string sql = "insert into sys_role_menu(role_id, menu_id) values ";
    for (size_t i = 0; i < roleMenus.size(); ++i) {
        if (i > 0) sql += ",";
        sql += "(" + cm::db::Db::lit(roleMenus[i].first) + "," + cm::db::Db::lit(roleMenus[i].second) + ")";
    }
    return cm::db::Db::instance().execute(sql);
}

int SysRoleMenuMapper::checkMenuExistRole(long long menuId) {
    std::string sql = "select count(1) from sys_role_menu where menu_id = " + cm::db::Db::lit(menuId);
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

} // namespace cm::system::mapper
