// 对应 Java: com.ruoyi.system.mapper.SysDeptMapper
#include "cm/system/mapper/SysDeptMapper.hpp"
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

cm::domain::SysDept SysDeptMapper::mapDept(const cm::db::Row& row) {
    cm::domain::SysDept d;
    d.deptId = row.optI64("dept_id");
    d.parentId = row.optI64("parent_id");
    d.ancestors = row.get("ancestors");
    d.deptName = row.get("dept_name");
    d.orderNum = row.get("order_num");
    d.leaderId = row.optI64("leader_id");
    d.leader = row.get("leader");
    d.fgldId = row.optI64("fgld_id");
    d.fgldName = row.get("fgld_name");
    d.bankName = row.get("bank_name");
    d.account = row.get("account");
    d.socialCode = row.get("social_code");
    d.postalCode = row.get("postal_code");
    d.address = row.get("address");
    d.phone = row.get("phone");
    d.email = row.get("email");
    d.status = row.get("status");
    d.delFlag = row.get("del_flag");
    d.createBy = row.get("create_by");
    d.createTime = parseDbDate(row.get("create_time"));
    d.updateBy = row.get("update_by");
    d.updateTime = parseDbDate(row.get("update_time"));
    d.isZbzg = row.get("is_zbzg");
    d.isUint = row.get("is_uint");
    d.treeLeavel = row.optI64("tree_leavel");
    d.subCode = row.get("sub_code");
    d.deptJc = row.get("dept_jc");
    d.tenantId = row.optI64("tenant_id");
    return d;
}

std::vector<cm::domain::SysDept> SysDeptMapper::selectDeptList(const cm::domain::SysDept& dept) {
    std::string sql = "select d.dept_id, d.parent_id, d.ancestors, d.dept_name, d.order_num, d.leader_id, d.leader, d.fgld_id, d.fgld_name,"
                      " d.bank_name, d.account, d.social_code, d.postal_code, d.address, d.phone, d.email, d.status, d.del_flag,"
                      " d.create_by, d.create_time, d.is_zbzg, d.is_uint, d.tree_leavel, d.sub_code, d.dept_jc, d.tenant_id"
                      " from sys_dept d where d.del_flag = '0'";
    if (dept.parentId) sql += " AND d.parent_id = " + cm::db::Db::lit(*dept.parentId);
    if (dept.deptName && !dept.deptName->empty()) sql += " AND d.dept_name like " + cm::db::Db::lit("%" + *dept.deptName + "%");
    if (dept.status && !dept.status->empty()) sql += " AND d.status = " + cm::db::Db::lit(*dept.status);
    if (dept.deptId) sql += " AND d.dept_id = " + cm::db::Db::lit(*dept.deptId);
    if (dept.isZbzg && !dept.isZbzg->empty()) sql += " and d.is_zbzg = " + cm::db::Db::lit(*dept.isZbzg);
    if (dept.isUint && !dept.isUint->empty()) sql += " and d.is_uint = " + cm::db::Db::lit(*dept.isUint);
    if (dept.treeLeavel) sql += " and d.tree_leavel = " + cm::db::Db::lit(*dept.treeLeavel);
    if (dept.subCode && !dept.subCode->empty()) sql += " and d.sub_code = " + cm::db::Db::lit(*dept.subCode);
    if (dept.deptJc && !dept.deptJc->empty()) sql += " and d.dept_jc = " + cm::db::Db::lit(*dept.deptJc);
    if (dept.tenantId) sql += " and d.tenant_id = " + cm::db::Db::lit(*dept.tenantId);
    if (dept.leaderId) sql += " and d.leader_id = " + cm::db::Db::lit(*dept.leaderId);
    if (dept.leader && !dept.leader->empty()) sql += " and d.leader = " + cm::db::Db::lit(*dept.leader);
    if (dept.fgldId) sql += " and d.fgld_id = " + cm::db::Db::lit(*dept.fgldId);
    if (dept.fgldName && !dept.fgldName->empty()) sql += " and d.fgld_name like " + cm::db::Db::lit("%" + *dept.fgldName + "%");
    if (dept.deptSubCode && !dept.deptSubCode->empty()) sql += " and d.sub_code like " + cm::db::Db::lit(*dept.deptSubCode + "%");
    sql += " order by d.parent_id, d.order_num";
    cm::db::Result res;
    std::vector<cm::domain::SysDept> depts;
    if (!cm::db::Db::instance().query(sql, res)) return depts;
    for (const auto& row : res.rows) depts.push_back(mapDept(row));
    return depts;
}

std::optional<cm::domain::SysDept> SysDeptMapper::selectDeptById(long long deptId) {
    std::string sql = "select d.dept_id, d.parent_id, d.ancestors, d.dept_name, d.order_num, d.leader_id, d.leader, d.fgld_id, d.fgld_name,"
                      " d.bank_name, d.account, d.social_code, d.postal_code, d.address, d.phone, d.email, d.status, d.del_flag,"
                      " d.create_by, d.create_time, d.is_zbzg, d.is_uint, d.tree_leavel, d.sub_code, d.dept_jc, d.tenant_id"
                      " from sys_dept d where dept_id = " + cm::db::Db::lit(deptId);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapDept(res.rows[0]);
}

std::vector<long long> SysDeptMapper::selectDeptListByRoleId(long long roleId, bool deptCheckStrictly) {
    std::string sql = "select d.dept_id from sys_dept d left join sys_role_dept rd on d.dept_id = rd.dept_id where rd.role_id = " + cm::db::Db::lit(roleId);
    if (deptCheckStrictly) {
        sql += " and d.dept_id not in (select d.parent_id from sys_dept d inner join sys_role_dept rd on d.dept_id = rd.dept_id and rd.role_id = " + cm::db::Db::lit(roleId) + ")";
    }
    sql += " order by d.parent_id, d.order_num";
    cm::db::Result res;
    std::vector<long long> ids;
    if (!cm::db::Db::instance().query(sql, res)) return ids;
    for (const auto& row : res.rows) {
        auto id = row.optI64("dept_id");
        if (id) ids.push_back(*id);
    }
    return ids;
}

std::optional<cm::domain::SysDept> SysDeptMapper::checkDeptNameUnique(const std::string& deptName, long long parentId) {
    std::string sql = "select d.dept_id, d.parent_id, d.ancestors, d.dept_name, d.order_num, d.leader_id, d.leader, d.fgld_id, d.fgld_name,"
                      " d.bank_name, d.account, d.social_code, d.postal_code, d.address, d.phone, d.email, d.status, d.del_flag,"
                      " d.create_by, d.create_time, d.is_zbzg, d.is_uint, d.tree_leavel, d.sub_code, d.dept_jc, d.tenant_id"
                      " from sys_dept d where dept_name = " + cm::db::Db::lit(deptName) + " and parent_id = " + cm::db::Db::lit(parentId) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapDept(res.rows[0]);
}

int SysDeptMapper::hasChildByDeptId(long long deptId) {
    std::string sql = "select count(1) from sys_dept where del_flag = '0' and parent_id = " + cm::db::Db::lit(deptId) + " limit 1";
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

int SysDeptMapper::checkDeptExistUser(long long deptId) {
    std::string sql = "select count(1) from sys_user where dept_id = " + cm::db::Db::lit(deptId) + " and del_flag = '0'";
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

int SysDeptMapper::selectNormalChildrenDeptById(long long deptId) {
    std::string sql = "select count(*) from sys_dept where status = 0 and del_flag = '0' and find_in_set(" + cm::db::Db::lit(deptId) + ", ancestors)";
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

bool SysDeptMapper::insertDept(cm::domain::SysDept& dept) {
    std::string sql = "insert into sys_dept(";
    std::string vals;
    if (dept.deptId && *dept.deptId != 0) { sql += "dept_id,"; vals += cm::db::Db::lit(*dept.deptId) + ","; }
    if (dept.parentId && *dept.parentId != 0) { sql += "parent_id,"; vals += cm::db::Db::lit(*dept.parentId) + ","; }
    if (dept.deptName && !dept.deptName->empty()) { sql += "dept_name,"; vals += cm::db::Db::lit(*dept.deptName) + ","; }
    if (dept.ancestors && !dept.ancestors->empty()) { sql += "ancestors,"; vals += cm::db::Db::lit(*dept.ancestors) + ","; }
    if (dept.orderNum && !dept.orderNum->empty()) { sql += "order_num,"; vals += cm::db::Db::lit(*dept.orderNum) + ","; }
    if (dept.leaderId) { sql += "leader_id,"; vals += cm::db::Db::lit(*dept.leaderId) + ","; }
    if (dept.leader) { sql += "leader,"; vals += cm::db::Db::lit(*dept.leader) + ","; }
    if (dept.fgldId) { sql += "fgld_id,"; vals += cm::db::Db::lit(*dept.fgldId) + ","; }
    if (dept.fgldName) { sql += "fgld_name,"; vals += cm::db::Db::lit(*dept.fgldName) + ","; }
    if (dept.bankName) { sql += "bank_name,"; vals += cm::db::Db::lit(*dept.bankName) + ","; }
    if (dept.account) { sql += "account,"; vals += cm::db::Db::lit(*dept.account) + ","; }
    if (dept.socialCode) { sql += "social_code,"; vals += cm::db::Db::lit(*dept.socialCode) + ","; }
    if (dept.postalCode) { sql += "postal_code,"; vals += cm::db::Db::lit(*dept.postalCode) + ","; }
    if (dept.address) { sql += "address,"; vals += cm::db::Db::lit(*dept.address) + ","; }
    if (dept.phone && !dept.phone->empty()) { sql += "phone,"; vals += cm::db::Db::lit(*dept.phone) + ","; }
    if (dept.email && !dept.email->empty()) { sql += "email,"; vals += cm::db::Db::lit(*dept.email) + ","; }
    if (dept.status) { sql += "status,"; vals += cm::db::Db::lit(*dept.status) + ","; }
    if (dept.createBy && !dept.createBy->empty()) { sql += "create_by,"; vals += cm::db::Db::lit(*dept.createBy) + ","; }
    if (dept.isZbzg) { sql += "is_zbzg,"; vals += cm::db::Db::lit(*dept.isZbzg) + ","; }
    if (dept.isUint) { sql += "is_uint,"; vals += cm::db::Db::lit(*dept.isUint) + ","; }
    if (dept.treeLeavel) { sql += "tree_leavel,"; vals += cm::db::Db::lit(*dept.treeLeavel) + ","; }
    if (dept.subCode) { sql += "sub_code,"; vals += cm::db::Db::lit(*dept.subCode) + ","; }
    if (dept.deptJc) { sql += "dept_jc,"; vals += cm::db::Db::lit(*dept.deptJc) + ","; }
    if (dept.tenantId) { sql += "tenant_id,"; vals += cm::db::Db::lit(*dept.tenantId) + ","; }
    sql += "create_time) values (" + vals + "sysdate())";
    long long insertId = 0;
    bool ok = cm::db::Db::instance().execute(sql, nullptr, &insertId);
    if (ok && insertId > 0) dept.deptId = insertId;
    return ok;
}

bool SysDeptMapper::updateDept(const cm::domain::SysDept& dept) {
    std::string sql = "update sys_dept set ";
    if (dept.parentId && *dept.parentId != 0) sql += "parent_id = " + cm::db::Db::lit(*dept.parentId) + ",";
    if (dept.deptName && !dept.deptName->empty()) sql += "dept_name = " + cm::db::Db::lit(*dept.deptName) + ",";
    if (dept.ancestors && !dept.ancestors->empty()) sql += "ancestors = " + cm::db::Db::lit(*dept.ancestors) + ",";
    if (dept.orderNum && !dept.orderNum->empty()) sql += "order_num = " + cm::db::Db::lit(*dept.orderNum) + ",";
    if (dept.leaderId) sql += "leader_id = " + cm::db::Db::lit(*dept.leaderId) + ",";
    if (dept.leader) sql += "leader = " + cm::db::Db::lit(*dept.leader) + ",";
    if (dept.fgldId) sql += "fgld_id = " + cm::db::Db::lit(*dept.fgldId) + ",";
    if (dept.fgldName) sql += "fgld_name = " + cm::db::Db::lit(*dept.fgldName) + ",";
    if (dept.bankName) sql += "bank_name = " + cm::db::Db::lit(*dept.bankName) + ",";
    if (dept.account) sql += "account = " + cm::db::Db::lit(*dept.account) + ",";
    if (dept.socialCode) sql += "social_code = " + cm::db::Db::lit(*dept.socialCode) + ",";
    if (dept.postalCode) sql += "postal_code = " + cm::db::Db::lit(*dept.postalCode) + ",";
    if (dept.address) sql += "address = " + cm::db::Db::lit(*dept.address) + ",";
    if (dept.phone) sql += "phone = " + cm::db::Db::lit(*dept.phone) + ",";
    if (dept.email) sql += "email = " + cm::db::Db::lit(*dept.email) + ",";
    if (dept.status && !dept.status->empty()) sql += "status = " + cm::db::Db::lit(*dept.status) + ",";
    if (dept.updateBy && !dept.updateBy->empty()) sql += "update_by = " + cm::db::Db::lit(*dept.updateBy) + ",";
    if (dept.isZbzg) sql += "is_zbzg = " + cm::db::Db::lit(*dept.isZbzg) + ",";
    if (dept.isUint) sql += "is_uint = " + cm::db::Db::lit(*dept.isUint) + ",";
    if (dept.treeLeavel) sql += "tree_leavel = " + cm::db::Db::lit(*dept.treeLeavel) + ",";
    if (dept.subCode) sql += "sub_code = " + cm::db::Db::lit(*dept.subCode) + ",";
    if (dept.deptJc) sql += "dept_jc = " + cm::db::Db::lit(*dept.deptJc) + ",";
    if (dept.tenantId) sql += "tenant_id = " + cm::db::Db::lit(*dept.tenantId) + ",";
    sql += "update_time = sysdate() where dept_id = " + cm::db::Db::lit(dept.deptId.value_or(0));
    return cm::db::Db::instance().execute(sql);
}

bool SysDeptMapper::deleteDeptById(long long deptId) {
    std::string sql = "update sys_dept set del_flag = '2' where dept_id = " + cm::db::Db::lit(deptId);
    return cm::db::Db::instance().execute(sql);
}

std::optional<cm::domain::SysDept> SysDeptMapper::selectTenantId(const cm::domain::SysDept& dept) {
    std::string sql = "select d.dept_id, d.parent_id, d.ancestors, d.dept_name, d.order_num, d.leader_id, d.leader, d.fgld_id, d.fgld_name,"
                      " d.bank_name, d.account, d.social_code, d.postal_code, d.address, d.phone, d.email, d.status, d.del_flag,"
                      " d.create_by, d.create_time, d.is_zbzg, d.is_uint, d.tree_leavel, d.sub_code, d.dept_jc, d.tenant_id"
                      " from sys_dept d where d.del_flag = '0' and " + cm::db::Db::lit(dept.subCode.value_or("")) + " like concat(d.sub_code, '%')"
                      " and d.is_uint = '1' order by d.tree_leavel desc limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapDept(res.rows[0]);
}

} // namespace cm::system::mapper
