#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysUserMapper（登录/权限所需部分）
#include <optional>
#include <utility>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysUser.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysUserMapper {
public:
    /** selectUserByUserName（含 dept 关联，roles 由 selectRolesByUserId 补齐） */
    static std::optional<cm::domain::SysUser> selectUserByUserName(const std::string& userName);
    static std::optional<cm::domain::SysUser> selectUserById(long long userId);
    static std::optional<cm::domain::SysUser> selectUserByCertEntityId(const std::string& certEntityId);

    static std::vector<cm::domain::SysRole> selectRolesByUserId(long long userId);
    /** selectRolePermissionByUserId：返回 role_key 列表（不过滤 status，对应 Java） */
    static std::vector<std::string> selectRolePermissionByUserId(long long userId);
    /** selectMenuPermsByUserId：返回 perms 列表 */
    static std::vector<std::string> selectMenuPermsByUserId(long long userId);

    /** updateUser（登录 IP / 时间） */
    static bool updateLoginInfo(long long userId, const std::string& loginIp, long long loginDate);

    /** 插入 sys_logininfor（对应 AsyncFactory.recordLogininfor） */
    static void insertLogininfor(const std::string& userName, const std::string& status,
                                 const std::string& ipaddr, const std::string& loginLocation,
                                 const std::string& browser, const std::string& os,
                                 const std::string& msg, long long loginTime);

    /** Row -> SysUser（供其它切片复用） */
    static cm::domain::SysUser mapUser(const cm::db::Row& row);

    // --- CRUD additions (SysUserController / SysUserServiceImpl) ---
    /** 与 SysUserMapper.xml 的 selectUserList 等价的 SQL（不含 LIMIT），供分页复用 */
    static std::string selectUserListSql(const cm::domain::SysUser& user);
    /** PageHelper 语义：count 包住同一条 dataSql，返回映射后的实体 + total */
    static std::pair<std::vector<cm::domain::SysUser>, long long>
    selectUserEntityPage(const cm::domain::SysUser& user, const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysUser> selectUserList(const cm::domain::SysUser& user);
    static int checkUserNameUnique(const std::string& userName);
    static std::optional<cm::domain::SysUser> checkPhoneUnique(const std::string& phonenumber);
    static std::optional<cm::domain::SysUser> checkEmailUnique(const std::string& email);
    static bool insertUser(cm::domain::SysUser& user);
    static int updateUser(const cm::domain::SysUser& user);
    static bool deleteUserById(long long userId);
    static int deleteUserByIds(const std::vector<long long>& userIds);
    static int resetUserPwd(const std::string& userName, const std::string& password);
    static int updateUserAvatar(const std::string& userName, const std::string& avatar);
};

} // namespace cm::system::mapper
