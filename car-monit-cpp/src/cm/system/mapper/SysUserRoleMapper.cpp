// 对应 Java: com.ruoyi.system.mapper.SysUserRoleMapper
#include "cm/system/mapper/SysUserRoleMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

bool SysUserRoleMapper::deleteUserRoleByUserId(long long userId) {
    std::string sql = "delete from sys_user_role where user_id = " + cm::db::bind(userId);
    return cm::db::Db::instance().execute(sql);
}

bool SysUserRoleMapper::deleteUserRole(const std::vector<long long>& userIds) {
    if (userIds.empty()) return true;
    std::string sql = "delete from sys_user_role where user_id in " + cm::db::bindIn(userIds);
    return cm::db::Db::instance().execute(sql);
}

bool SysUserRoleMapper::batchUserRole(const std::vector<std::pair<long long, long long>>& userRoles) {
    if (userRoles.empty()) return true;
    std::string sql = "insert into sys_user_role(user_id, role_id) values ";
    for (size_t i = 0; i < userRoles.size(); ++i) {
        if (i > 0) sql += ",";
        sql += "(" + cm::db::bind(userRoles[i].first) + "," + cm::db::bind(userRoles[i].second) + ")";
    }
    return cm::db::Db::instance().execute(sql);
}

int SysUserRoleMapper::countUserRoleByRoleId(long long roleId) {
    std::string sql = "select count(1) from sys_user_role where role_id = " + cm::db::bind(roleId);
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

int SysUserRoleMapper::countUserRoleByRoleIdUserId(long long roleId, long long userId) {
    std::string sql = "select count(1) from sys_user_role where role_id = " + cm::db::bind(roleId) +
                      " and user_id = " + cm::db::bind(userId);
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

} // namespace cm::system::mapper
