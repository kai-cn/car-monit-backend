// 对应 Java: com.ruoyi.system.mapper.SysUserMapper（登录/权限所需部分）
// SQL 与 ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml 保持一致。
#include "cm/system/mapper/SysUserMapper.hpp"

#include <algorithm>

#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

namespace {

// 与 XML <sql id="selectUserVo"> 完全一致
constexpr const char* kSelectUserVo =
    "select u.user_id,"
    " u.user_no,"
    " u.dept_id,"
    " u.user_name,"
    " u.nick_name,"
    " u.email,"
    " u.avatar,"
    " u.phonenumber,"
    " u.password,"
    " u.sex,"
    " u.status,"
    " u.del_flag,"
    " u.login_ip,"
    " u.login_date,"
    " u.create_by,"
    " u.create_time,"
    " u.remark,"
    " u.user_type,"
    " u.cert_entity_id,"
    " u.cert_id,"
    " ifnull(u.buss_id, u.user_name) buss_id,"
    " u.buss_name,"
    " u.eps_name,"
    " ifnull(d.tenant_id, -1) tenant_id,"
    " d.sub_code,"
    " d.dept_id,"
    " d.parent_id,"
    " d.dept_name,"
    " d.order_num,"
    " d.leader,"
    " d.status as dept_status,"
    " r.role_id,"
    " r.role_name,"
    " r.role_key,"
    " r.role_sort,"
    " r.data_scope,"
    " r.status as role_status,"
    " u.image_id"
    " from sys_user u"
    " left join sys_dept d on u.dept_id = d.dept_id"
    " left join sys_user_role ur on u.user_id = ur.user_id"
    " left join sys_role r on r.role_id = ur.role_id";

/** MySQL DATETIME 文本 -> epoch 毫秒（无值/无法解析时为 nullopt） */
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}

std::optional<cm::domain::SysRole> mapRole(const cm::db::Row& row) {    if (!row.has("role_id") || row.isNull("role_id")) return std::nullopt;
    cm::domain::SysRole r;
    r.roleId = row.optI64("role_id");
    r.roleName = row.get("role_name");
    r.roleKey = row.get("role_key");
    r.roleSort = row.get("role_sort");
    r.dataScope = row.get("data_scope");
    r.status = row.get("role_status");
    return r;
}

/**
 * 拉取 selectUserVo 的结果并聚合成单个 SysUser（对应 MyBatis resultMap 的
 * association/collection 合并语义：一个用户多条 role 行合并为一个对象）。
 * 返回第一条 user_id 相同的连续行的聚合结果。
 */
std::optional<cm::domain::SysUser> loadFirstUser(const std::string& sql) {
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;

    const cm::db::Row& head = res.rows.front();
    cm::domain::SysUser user = cm::system::mapper::SysUserMapper::mapUser(head);
    std::vector<cm::domain::SysRole> roles;
    if (user.deptId) {
        cm::domain::SysDept dept;
        dept.deptId = head.optI64("dept_id");
        dept.parentId = head.optI64("parent_id");
        dept.deptName = head.get("dept_name");
        dept.orderNum = head.get("order_num");
        dept.leader = head.get("leader");
        dept.status = head.get("dept_status");
        dept.subCode = head.get("sub_code");
        dept.tenantId = head.optI64("tenant_id");
        user.dept = dept;
    }
    for (const auto& row : res.rows) {
        // MyBatis 以 <id property="userId"> 判定行是否属于同一对象
        if (row.optI64("user_id") != user.userId) continue;
        if (auto r = mapRole(row)) roles.push_back(*r);
    }
    user.roles = roles;
    return user;
}

} // namespace

cm::domain::SysUser SysUserMapper::mapUser(const cm::db::Row& row) {
    cm::domain::SysUser u;
    u.userId = row.optI64("user_id");
    u.userNo = row.optI64("user_no");
    u.deptId = row.optI64("dept_id");
    u.userName = row.get("user_name");
    u.nickName = row.get("nick_name");
    u.userType = row.get("user_type");
    u.email = row.get("email");
    u.phonenumber = row.get("phonenumber");
    u.sex = row.get("sex");
    u.avatar = row.get("avatar");
    u.password = row.get("password");
    u.status = row.get("status");
    u.delFlag = row.get("del_flag");
    u.loginIp = row.get("login_ip");
    u.loginDate = parseDbDate(row.get("login_date"));
    u.createBy = row.get("create_by");
    u.createTime = parseDbDate(row.get("create_time"));
    u.remark = row.get("remark");
    u.certEntityId = row.get("cert_entity_id");
    u.certId = row.get("cert_id");
    u.bussId = row.get("buss_id");
    u.bussName = row.get("buss_name");
    u.epsName = row.get("eps_name");
    u.tenantId = row.optI64("tenant_id");
    u.imageId = row.get("image_id");
    return u;
}

std::optional<cm::domain::SysUser> SysUserMapper::selectUserByUserName(const std::string& userName) {
    return loadFirstUser(std::string(kSelectUserVo) + " where u.user_name = " +
                         cm::db::Db::lit(userName));
}

std::optional<cm::domain::SysUser> SysUserMapper::selectUserById(long long userId) {
    return loadFirstUser(std::string(kSelectUserVo) + " where u.user_id = " +
                         cm::db::Db::lit(userId));
}

std::optional<cm::domain::SysUser> SysUserMapper::selectUserByCertEntityId(const std::string& certEntityId) {
    return loadFirstUser(std::string(kSelectUserVo) + " where u.cert_entity_id = " +
                         cm::db::Db::lit(certEntityId));
}

std::vector<cm::domain::SysRole> SysUserMapper::selectRolesByUserId(long long userId) {
    // SysRoleMapper.selectRoleVo + join，语义等价
    const std::string sql =
        "select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,"
        " r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark"
        " from sys_role r"
        " left join sys_user_role ur on ur.role_id = r.role_id"
        " left join sys_user u on u.user_id = ur.user_id"
        " left join sys_dept d on u.dept_id = d.dept_id"
        " where r.del_flag = '0' and ur.user_id = " + cm::db::Db::lit(userId) +
        " and r.status = '0'";
    cm::db::Result res;
    std::vector<cm::domain::SysRole> roles;
    if (!cm::db::Db::instance().query(sql, res)) return roles;
    for (const auto& row : res.rows) {
        cm::domain::SysRole r;
        r.roleId = row.optI64("role_id");
        r.roleName = row.get("role_name");
        r.roleKey = row.get("role_key");
        r.roleSort = row.get("role_sort");
        r.dataScope = row.get("data_scope");
        r.status = row.get("status");
        r.delFlag = row.get("del_flag");
        roles.push_back(r);
    }
    return roles;
}

std::vector<std::string> SysUserMapper::selectRolePermissionByUserId(long long userId) {
    const std::string sql =
        "select distinct r.role_key"
        " from sys_role r"
        " left join sys_user_role ur on ur.role_id = r.role_id"
        " left join sys_user u on u.user_id = ur.user_id"
        " left join sys_dept d on u.dept_id = d.dept_id"
        " WHERE r.del_flag = '0' and ur.user_id = " + cm::db::Db::lit(userId);
    cm::db::Result res;
    std::vector<std::string> keys;
    if (!cm::db::Db::instance().query(sql, res)) return keys;
    for (const auto& row : res.rows) {
        if (auto k = row.get("role_key")) keys.push_back(*k);
    }
    return keys;
}

std::vector<std::string> SysUserMapper::selectMenuPermsByUserId(long long userId) {
    const std::string sql =
        "select distinct m.perms"
        " from sys_menu m"
        " left join sys_role_menu rm on m.menu_id = rm.menu_id"
        " left join sys_user_role ur on rm.role_id = ur.role_id"
        " left join sys_role r on r.role_id = ur.role_id"
        " where m.status = '0' and r.status = '0' and ur.user_id = " + cm::db::Db::lit(userId);
    cm::db::Result res;
    std::vector<std::string> perms;
    if (!cm::db::Db::instance().query(sql, res)) return perms;
    for (const auto& row : res.rows) {
        if (auto p = row.get("perms")) perms.push_back(*p);
    }
    return perms;
}

bool SysUserMapper::updateLoginInfo(long long userId, const std::string& loginIp, long long loginDate) {
    // updateUser 中登录相关字段；时间用 FROM_UNIXTIME 保持服务器时区口径
    const std::string sql =
        "update sys_user set login_ip = " + cm::db::Db::lit(loginIp) +
        ", login_date = from_unixtime(" + std::to_string(loginDate / 1000) + ")"
        " where user_id = " + cm::db::Db::lit(userId);
    return cm::db::Db::instance().execute(sql);
}

void SysUserMapper::insertLogininfor(const std::string& userName, const std::string& status,
                                     const std::string& ipaddr, const std::string& loginLocation,
                                     const std::string& browser, const std::string& os,
                                     const std::string& msg, long long loginTime) {
    const std::string sql =
        "insert into sys_logininfor (user_name, status, ipaddr, login_location, browser, os, msg, login_time)"
        " values (" + cm::db::Db::lit(userName) + ", " + cm::db::Db::lit(status) + ", " +
        cm::db::Db::lit(ipaddr) + ", " + cm::db::Db::lit(loginLocation) + ", " +
        cm::db::Db::lit(browser) + ", " + cm::db::Db::lit(os) + ", " + cm::db::Db::lit(msg) +
        ", from_unixtime(" + std::to_string(loginTime / 1000) + "))";
    cm::db::Db::instance().execute(sql);
}

// --- CRUD additions ---

std::vector<cm::domain::SysUser> SysUserMapper::selectUserList(const cm::domain::SysUser& user) {
    std::string sql = "select u.user_id, u.user_no, u.dept_id, u.nick_name, u.user_name, u.email, u.avatar, u.phonenumber, u.password,"
                      " u.sex, u.status, u.del_flag, u.login_ip, u.login_date, u.create_by, u.create_time, u.remark,"
                      " u.user_type, u.cert_entity_id, u.cert_id, u.buss_id, u.buss_name, u.eps_name, ifnull(d.tenant_id, -1) tenant_id,"
                      " d2.dept_name tenant_name, d.dept_name, d.leader, u.image_id"
                      " from sys_user u"
                      " left join sys_dept d on u.dept_id = d.dept_id"
                      " left join sys_dept d2 on d.tenant_id = d2.dept_id"
                      " where u.del_flag = '0'";
    if (user.userId && *user.userId != 0) sql += " AND u.user_id = " + cm::db::Db::lit(*user.userId);
    if (user.userNo) sql += " AND u.user_no = " + cm::db::Db::lit(*user.userNo);
    if (user.userName && !user.userName->empty()) sql += " AND u.user_name like " + cm::db::Db::lit("%" + *user.userName + "%");
    if (user.status && !user.status->empty()) sql += " AND u.status = " + cm::db::Db::lit(*user.status);
    if (user.phonenumber && !user.phonenumber->empty()) sql += " AND u.phonenumber like " + cm::db::Db::lit("%" + *user.phonenumber + "%");
    if (user.deptId && *user.deptId != 0) sql += " AND (u.dept_id = " + cm::db::Db::lit(*user.deptId) + " OR u.dept_id IN (SELECT t.dept_id FROM sys_dept t WHERE find_in_set(" + cm::db::Db::lit(*user.deptId) + ", ancestors)))";
    if (user.userType && !user.userType->empty()) sql += " and u.user_type = " + cm::db::Db::lit(*user.userType);
    if (user.certEntityId && !user.certEntityId->empty()) sql += " and u.cert_entity_id = " + cm::db::Db::lit(*user.certEntityId);
    if (user.certId && !user.certId->empty()) sql += " and u.cert_id = " + cm::db::Db::lit(*user.certId);
    if (user.bussId && !user.bussId->empty()) sql += " and u.buss_id = " + cm::db::Db::lit(*user.bussId);
    if (user.bussName && !user.bussName->empty()) sql += " and u.buss_name like " + cm::db::Db::lit("%" + *user.bussName + "%");
    if (user.epsName && !user.epsName->empty()) sql += " and u.eps_name like " + cm::db::Db::lit("%" + *user.epsName + "%");
    if (user.tenantId) sql += " and d.tenant_id = " + cm::db::Db::lit(*user.tenantId);
    if (user.roleCode && !user.roleCode->empty()) {
        sql += " and EXISTS (select 1 from sys_user_role t1, sys_role t2 where t2.del_flag = '0' and t2.role_id = t1.role_id and t1.user_id = u.user_id and t2.role_key = " + cm::db::Db::lit(*user.roleCode) + ")";
    }
    if (user.queryNickName && !user.queryNickName->empty()) sql += " AND u.nick_name LIKE " + cm::db::Db::lit("%" + *user.queryNickName + "%");
    if (user.excludeId) sql += " AND u.user_id != " + cm::db::Db::lit(*user.excludeId);
    cm::db::Result res;
    std::vector<cm::domain::SysUser> users;
    if (!cm::db::Db::instance().query(sql, res)) return users;
    for (const auto& row : res.rows) users.push_back(mapUser(row));
    return users;
}

int SysUserMapper::checkUserNameUnique(const std::string& userName) {
    std::string sql = "select count(1) from sys_user where user_name = " + cm::db::Db::lit(userName) + " and del_flag = '0' limit 1";
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

std::optional<cm::domain::SysUser> SysUserMapper::checkPhoneUnique(const std::string& phonenumber) {
    std::string sql = "select user_id, phonenumber from sys_user where phonenumber = " + cm::db::Db::lit(phonenumber) + " and del_flag = '0' limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    cm::domain::SysUser u;
    u.userId = res.rows[0].optI64("user_id");
    u.phonenumber = res.rows[0].get("phonenumber");
    return u;
}

std::optional<cm::domain::SysUser> SysUserMapper::checkEmailUnique(const std::string& email) {
    std::string sql = "select user_id, email from sys_user where email = " + cm::db::Db::lit(email) + " and del_flag = '0' limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    cm::domain::SysUser u;
    u.userId = res.rows[0].optI64("user_id");
    u.email = res.rows[0].get("email");
    return u;
}

bool SysUserMapper::insertUser(cm::domain::SysUser& user) {
    std::string sql = "insert into sys_user(";
    std::string vals;
    if (user.userNo) { sql += "user_no,"; vals += cm::db::Db::lit(*user.userNo) + ","; }
    if (user.deptId) { sql += "dept_id,"; vals += cm::db::Db::lit(*user.deptId) + ","; }
    if (user.userName && !user.userName->empty()) { sql += "user_name,"; vals += cm::db::Db::lit(*user.userName) + ","; }
    if (user.nickName && !user.nickName->empty()) { sql += "nick_name,"; vals += cm::db::Db::lit(*user.nickName) + ","; }
    if (user.userType && !user.userType->empty()) { sql += "user_type,"; vals += cm::db::Db::lit(*user.userType) + ","; }
    if (user.email && !user.email->empty()) { sql += "email,"; vals += cm::db::Db::lit(*user.email) + ","; }
    if (user.phonenumber && !user.phonenumber->empty()) { sql += "phonenumber,"; vals += cm::db::Db::lit(*user.phonenumber) + ","; }
    if (user.sex && !user.sex->empty()) { sql += "sex,"; vals += cm::db::Db::lit(*user.sex) + ","; }
    if (user.avatar && !user.avatar->empty()) { sql += "avatar,"; vals += cm::db::Db::lit(*user.avatar) + ","; }
    if (user.password && !user.password->empty()) { sql += "password,"; vals += cm::db::Db::lit(*user.password) + ","; }
    if (user.status && !user.status->empty()) { sql += "status,"; vals += cm::db::Db::lit(*user.status) + ","; }
    if (user.remark && !user.remark->empty()) { sql += "remark,"; vals += cm::db::Db::lit(*user.remark) + ","; }
    if (user.certEntityId && !user.certEntityId->empty()) { sql += "cert_entity_id,"; vals += cm::db::Db::lit(*user.certEntityId) + ","; }
    if (user.certId && !user.certId->empty()) { sql += "cert_id,"; vals += cm::db::Db::lit(*user.certId) + ","; }
    if (user.bussId && !user.bussId->empty()) { sql += "buss_id,"; vals += cm::db::Db::lit(*user.bussId) + ","; }
    if (user.bussName && !user.bussName->empty()) { sql += "buss_name,"; vals += cm::db::Db::lit(*user.bussName) + ","; }
    if (user.epsName && !user.epsName->empty()) { sql += "eps_name,"; vals += cm::db::Db::lit(*user.epsName) + ","; }
    if (user.loginIp && !user.loginIp->empty()) { sql += "login_ip,"; vals += cm::db::Db::lit(*user.loginIp) + ","; }
    if (user.loginDate) { sql += "login_date,"; vals += "from_unixtime(" + std::to_string(*user.loginDate / 1000) + "),"; }
    if (user.delFlag && !user.delFlag->empty()) { sql += "del_flag,"; vals += cm::db::Db::lit(*user.delFlag) + ","; }
    if (user.createBy && !user.createBy->empty()) { sql += "create_by,"; vals += cm::db::Db::lit(*user.createBy) + ","; }
    if (user.createTime) { sql += "create_time,"; vals += "from_unixtime(" + std::to_string(*user.createTime / 1000) + "),"; }
    if (user.updateBy && !user.updateBy->empty()) { sql += "update_by,"; vals += cm::db::Db::lit(*user.updateBy) + ","; }
    if (user.updateTime) { sql += "update_time,"; vals += "from_unixtime(" + std::to_string(*user.updateTime / 1000) + "),"; }
    if (user.tenantId) { sql += "tenant_id,"; vals += cm::db::Db::lit(*user.tenantId) + ","; }
    if (user.imageId && !user.imageId->empty()) { sql += "image_id,"; vals += cm::db::Db::lit(*user.imageId) + ","; }
    sql += ") values (" + vals + ")";
    long long insertId = 0;
    bool ok = cm::db::Db::instance().execute(sql, nullptr, &insertId);
    if (ok && insertId > 0) user.userId = insertId;
    return ok;
}

int SysUserMapper::updateUser(const cm::domain::SysUser& user) {
    std::string sql = "update sys_user set ";
    if (user.userNo) sql += "user_no = " + cm::db::Db::lit(*user.userNo) + ",";
    if (user.deptId) sql += "dept_id = " + cm::db::Db::lit(*user.deptId) + ",";
    if (user.userName && !user.userName->empty()) sql += "user_name = " + cm::db::Db::lit(*user.userName) + ",";
    if (user.nickName && !user.nickName->empty()) sql += "nick_name = " + cm::db::Db::lit(*user.nickName) + ",";
    if (user.password && !user.password->empty()) sql += "password = " + cm::db::Db::lit(*user.password) + ",";
    if (user.userType && !user.userType->empty()) sql += "user_type = " + cm::db::Db::lit(*user.userType) + ",";
    if (user.email && !user.email->empty()) sql += "email = " + cm::db::Db::lit(*user.email) + ",";
    if (user.phonenumber && !user.phonenumber->empty()) sql += "phonenumber = " + cm::db::Db::lit(*user.phonenumber) + ",";
    if (user.sex && !user.sex->empty()) sql += "sex = " + cm::db::Db::lit(*user.sex) + ",";
    if (user.avatar && !user.avatar->empty()) sql += "avatar = " + cm::db::Db::lit(*user.avatar) + ",";
    if (user.status && !user.status->empty()) sql += "status = " + cm::db::Db::lit(*user.status) + ",";
    if (user.remark) sql += "remark = " + cm::db::Db::lit(*user.remark) + ",";
    if (user.certEntityId && !user.certEntityId->empty()) sql += "cert_entity_id = " + cm::db::Db::lit(*user.certEntityId) + ",";
    if (user.certId && !user.certId->empty()) sql += "cert_id = " + cm::db::Db::lit(*user.certId) + ",";
    if (user.bussId && !user.bussId->empty()) sql += "buss_id = " + cm::db::Db::lit(*user.bussId) + ",";
    if (user.bussName && !user.bussName->empty()) sql += "buss_name = " + cm::db::Db::lit(*user.bussName) + ",";
    if (user.epsName && !user.epsName->empty()) sql += "eps_name = " + cm::db::Db::lit(*user.epsName) + ",";
    if (user.loginIp && !user.loginIp->empty()) sql += "login_ip = " + cm::db::Db::lit(*user.loginIp) + ",";
    if (user.loginDate) sql += "login_date = from_unixtime(" + std::to_string(*user.loginDate / 1000) + "),";
    if (user.delFlag && !user.delFlag->empty()) sql += "del_flag = " + cm::db::Db::lit(*user.delFlag) + ",";
    if (user.createBy && !user.createBy->empty()) sql += "create_by = " + cm::db::Db::lit(*user.createBy) + ",";
    if (user.createTime) sql += "create_time = from_unixtime(" + std::to_string(*user.createTime / 1000) + "),";
    if (user.updateBy && !user.updateBy->empty()) sql += "update_by = " + cm::db::Db::lit(*user.updateBy) + ",";
    if (user.updateTime) sql += "update_time = from_unixtime(" + std::to_string(*user.updateTime / 1000) + "),";
    if (user.tenantId) sql += "tenant_id = " + cm::db::Db::lit(*user.tenantId) + ",";
    if (user.imageId && !user.imageId->empty()) sql += "image_id = " + cm::db::Db::lit(*user.imageId) + ",";
    // Remove trailing comma
    if (!sql.empty() && sql.back() == ',') sql.pop_back();
    sql += " where user_id = " + cm::db::Db::lit(user.userId.value_or(0));
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return static_cast<int>(affected);
}

bool SysUserMapper::deleteUserById(long long userId) {
    std::string sql = "update sys_user set del_flag = '1' where user_id = " + cm::db::Db::lit(userId);
    return cm::db::Db::instance().execute(sql);
}

int SysUserMapper::deleteUserByIds(const std::vector<long long>& userIds) {
    if (userIds.empty()) return 0;
    std::string sql = "update sys_user set del_flag = '1' where user_id in " + cm::db::Db::inList(userIds);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return static_cast<int>(affected);
}

int SysUserMapper::resetUserPwd(const std::string& userName, const std::string& password) {
    std::string sql = "update sys_user set password = " + cm::db::Db::lit(password) + ", update_time = now() where user_name = " + cm::db::Db::lit(userName);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return static_cast<int>(affected);
}

int SysUserMapper::updateUserAvatar(const std::string& userName, const std::string& avatar) {
    std::string sql = "update sys_user set avatar = " + cm::db::Db::lit(avatar) + " where user_name = " + cm::db::Db::lit(userName);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return static_cast<int>(affected);
}

} // namespace cm::system::mapper
