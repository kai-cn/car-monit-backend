// 对应 Java: com.ruoyi.system.mapper.SysRoleMapper
#include "cm/system/mapper/SysRoleMapper.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/common/utils/DateUtils.hpp"

namespace cm::system::mapper {

namespace {
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}
} // namespace

cm::domain::SysRole SysRoleMapper::mapRole(const cm::db::Row& row) {
    cm::domain::SysRole r;
    r.roleId = row.optI64("role_id");
    r.roleName = row.get("role_name");
    r.roleKey = row.get("role_key");
    r.roleSort = row.get("role_sort");
    r.dataScope = row.get("data_scope");
    r.menuCheckStrictly = row.optBool("menu_check_strictly").value_or(false);
    r.deptCheckStrictly = row.optBool("dept_check_strictly").value_or(false);
    r.status = row.get("status");
    r.delFlag = row.get("del_flag");
    r.createBy = row.get("create_by");
    r.createTime = parseDbDate(row.get("create_time"));
    r.updateBy = row.get("update_by");
    r.updateTime = parseDbDate(row.get("update_time"));
    r.remark = row.get("remark");
    return r;
}

std::string SysRoleMapper::selectRoleListSql(const cm::domain::SysRole& role) {
    std::string sql = "select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,"
                      " r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark"
                      " from sys_role r"
                      " left join sys_user_role ur on ur.role_id = r.role_id"
                      " left join sys_user u on u.user_id = ur.user_id"
                      " left join sys_dept d on u.dept_id = d.dept_id"
                      " where r.del_flag = '0'";
    if (role.roleName && !role.roleName->empty()) {
        sql += " AND r.role_name like " + cm::db::Db::lit("%" + *role.roleName + "%");
    }
    if (role.status && !role.status->empty()) {
        sql += " AND r.status = " + cm::db::Db::lit(*role.status);
    }
    if (role.roleKey && !role.roleKey->empty()) {
        sql += " AND r.role_key = " + cm::db::Db::lit(*role.roleKey);
    }
    sql += " order by r.role_sort";
    return sql;
}

std::pair<std::vector<cm::domain::SysRole>, long long>
SysRoleMapper::selectRoleEntityPage(const cm::domain::SysRole& role,
                                    const cm::db::PageRequest& page) {
    const std::string dataSql = selectRoleListSql(role);
    // PageHelper 的 count 语义：把原 SQL 整体包一层，distinct / join 都不会算错
    auto pr = cm::db::queryPage("select count(1) from (" + dataSql + ") page_count", dataSql, page);
    std::vector<cm::domain::SysRole> roles;
    for (const auto& row : pr.rows.rows) roles.push_back(mapRole(row));
    return {std::move(roles), pr.total};
}

std::vector<cm::domain::SysRole> SysRoleMapper::selectRoleList(const cm::domain::SysRole& role) {
    cm::db::Result res;
    std::vector<cm::domain::SysRole> roles;
    if (!cm::db::Db::instance().query(selectRoleListSql(role), res)) return roles;
    for (const auto& row : res.rows) roles.push_back(mapRole(row));
    return roles;
}

std::vector<cm::domain::SysRole> SysRoleMapper::selectRoleAll() {
    std::string sql = "select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,"
                      " r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark"
                      " from sys_role r"
                      " left join sys_user_role ur on ur.role_id = r.role_id"
                      " left join sys_user u on u.user_id = ur.user_id"
                      " left join sys_dept d on u.dept_id = d.dept_id";
    cm::db::Result res;
    std::vector<cm::domain::SysRole> roles;
    if (!cm::db::Db::instance().query(sql, res)) return roles;
    for (const auto& row : res.rows) roles.push_back(mapRole(row));
    return roles;
}

std::optional<cm::domain::SysRole> SysRoleMapper::selectRoleById(long long roleId) {
    std::string sql = "select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,"
                      " r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark"
                      " from sys_role r"
                      " left join sys_user_role ur on ur.role_id = r.role_id"
                      " left join sys_user u on u.user_id = ur.user_id"
                      " left join sys_dept d on u.dept_id = d.dept_id"
                      " where r.role_id = " + cm::db::Db::lit(roleId);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapRole(res.rows[0]);
}

std::vector<cm::domain::SysRole> SysRoleMapper::selectRolesByUserName(const std::string& userName) {
    std::string sql = "select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,"
                      " r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark"
                      " from sys_role r"
                      " left join sys_user_role ur on ur.role_id = r.role_id"
                      " left join sys_user u on u.user_id = ur.user_id"
                      " left join sys_dept d on u.dept_id = d.dept_id"
                      " WHERE r.del_flag = '0' and u.user_name = " + cm::db::Db::lit(userName);
    cm::db::Result res;
    std::vector<cm::domain::SysRole> roles;
    if (!cm::db::Db::instance().query(sql, res)) return roles;
    for (const auto& row : res.rows) roles.push_back(mapRole(row));
    return roles;
}

std::vector<long long> SysRoleMapper::selectRoleListByUserId(long long userId) {
    std::string sql = "select r.role_id from sys_role r"
                      " left join sys_user_role ur on ur.role_id = r.role_id"
                      " left join sys_user u on u.user_id = ur.user_id"
                      " where u.user_id = " + cm::db::Db::lit(userId);
    cm::db::Result res;
    std::vector<long long> ids;
    if (!cm::db::Db::instance().query(sql, res)) return ids;
    for (const auto& row : res.rows) {
        auto id = row.optI64("role_id");
        if (id) ids.push_back(*id);
    }
    return ids;
}

std::optional<cm::domain::SysRole> SysRoleMapper::checkRoleNameUnique(const std::string& roleName) {
    std::string sql = "select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,"
                      " r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark"
                      " from sys_role r"
                      " left join sys_user_role ur on ur.role_id = r.role_id"
                      " left join sys_user u on u.user_id = ur.user_id"
                      " left join sys_dept d on u.dept_id = d.dept_id"
                      " where r.role_name = " + cm::db::Db::lit(roleName) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapRole(res.rows[0]);
}

std::optional<cm::domain::SysRole> SysRoleMapper::checkRoleKeyUnique(const std::string& roleKey) {
    std::string sql = "select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,"
                      " r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark"
                      " from sys_role r"
                      " left join sys_user_role ur on ur.role_id = r.role_id"
                      " left join sys_user u on u.user_id = ur.user_id"
                      " left join sys_dept d on u.dept_id = d.dept_id"
                      " where r.role_key = " + cm::db::Db::lit(roleKey) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapRole(res.rows[0]);
}

bool SysRoleMapper::insertRole(cm::domain::SysRole& role) {
    std::string sql = "insert into sys_role(";
    std::string vals;
    if (role.roleId && *role.roleId != 0) { sql += "role_id,"; vals += cm::db::Db::lit(*role.roleId) + ","; }
    if (role.roleName && !role.roleName->empty()) { sql += "role_name,"; vals += cm::db::Db::lit(*role.roleName) + ","; }
    if (role.roleKey && !role.roleKey->empty()) { sql += "role_key,"; vals += cm::db::Db::lit(*role.roleKey) + ","; }
    if (role.roleSort && !role.roleSort->empty()) { sql += "role_sort,"; vals += cm::db::Db::lit(*role.roleSort) + ","; }
    if (role.dataScope && !role.dataScope->empty()) { sql += "data_scope,"; vals += cm::db::Db::lit(*role.dataScope) + ","; }
    sql += "menu_check_strictly,"; vals += cm::db::Db::lit(role.menuCheckStrictly) + ",";
    sql += "dept_check_strictly,"; vals += cm::db::Db::lit(role.deptCheckStrictly) + ",";
    if (role.status && !role.status->empty()) { sql += "status,"; vals += cm::db::Db::lit(*role.status) + ","; }
    if (role.remark && !role.remark->empty()) { sql += "remark,"; vals += cm::db::Db::lit(*role.remark) + ","; }
    if (role.createBy && !role.createBy->empty()) { sql += "create_by,"; vals += cm::db::Db::lit(*role.createBy) + ","; }
    sql += "create_time) values (" + vals + "sysdate())";
    long long insertId = 0;
    bool ok = cm::db::Db::instance().execute(sql, nullptr, &insertId);
    if (ok && insertId > 0) role.roleId = insertId;
    return ok;
}

bool SysRoleMapper::updateRole(const cm::domain::SysRole& role) {
    std::string sql = "update sys_role set ";
    if (role.roleName && !role.roleName->empty()) sql += "role_name = " + cm::db::Db::lit(*role.roleName) + ",";
    if (role.roleKey && !role.roleKey->empty()) sql += "role_key = " + cm::db::Db::lit(*role.roleKey) + ",";
    if (role.roleSort && !role.roleSort->empty()) sql += "role_sort = " + cm::db::Db::lit(*role.roleSort) + ",";
    if (role.dataScope && !role.dataScope->empty()) sql += "data_scope = " + cm::db::Db::lit(*role.dataScope) + ",";
    sql += "menu_check_strictly = " + cm::db::Db::lit(role.menuCheckStrictly) + ",";
    sql += "dept_check_strictly = " + cm::db::Db::lit(role.deptCheckStrictly) + ",";
    if (role.status && !role.status->empty()) sql += "status = " + cm::db::Db::lit(*role.status) + ",";
    if (role.remark) sql += "remark = " + cm::db::Db::lit(*role.remark) + ",";
    if (role.updateBy && !role.updateBy->empty()) sql += "update_by = " + cm::db::Db::lit(*role.updateBy) + ",";
    sql += "update_time = sysdate() where role_id = " + cm::db::Db::lit(role.roleId.value_or(0));
    return cm::db::Db::instance().execute(sql);
}

bool SysRoleMapper::deleteRoleById(long long roleId) {
    std::string sql = "update sys_role set del_flag = '2' where role_id = " + cm::db::Db::lit(roleId);
    return cm::db::Db::instance().execute(sql);
}

bool SysRoleMapper::deleteRoleByIds(const std::vector<long long>& roleIds) {
    if (roleIds.empty()) return true;
    std::string sql = "update sys_role set del_flag = '2' where role_id in " + cm::db::Db::inList(roleIds);
    return cm::db::Db::instance().execute(sql);
}

} // namespace cm::system::mapper
