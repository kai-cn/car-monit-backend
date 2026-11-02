// 对应 Java: com.ruoyi.system.mapper.SysRoleDeptMapper
#include "cm/system/mapper/SysRoleDeptMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

bool SysRoleDeptMapper::deleteRoleDeptByRoleId(long long roleId) {
    std::string sql = "delete from sys_role_dept where role_id = " + cm::db::Db::lit(roleId);
    return cm::db::Db::instance().execute(sql);
}

bool SysRoleDeptMapper::deleteRoleDept(const std::vector<long long>& roleIds) {
    if (roleIds.empty()) return true;
    std::string sql = "delete from sys_role_dept where role_id in " + cm::db::Db::inList(roleIds);
    return cm::db::Db::instance().execute(sql);
}

bool SysRoleDeptMapper::batchRoleDept(const std::vector<std::pair<long long, long long>>& roleDepts) {
    if (roleDepts.empty()) return true;
    std::string sql = "insert into sys_role_dept(role_id, dept_id) values ";
    for (size_t i = 0; i < roleDepts.size(); ++i) {
        if (i > 0) sql += ",";
        sql += "(" + cm::db::Db::lit(roleDepts[i].first) + "," + cm::db::Db::lit(roleDepts[i].second) + ")";
    }
    return cm::db::Db::instance().execute(sql);
}

} // namespace cm::system::mapper
