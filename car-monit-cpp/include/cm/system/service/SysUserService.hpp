#pragma once
// 对应 Java: com.ruoyi.system.service.ISysUserService
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysUser.hpp"

namespace cm::system::service {

class SysUserService {
public:
    static std::vector<cm::domain::SysUser> selectUserList(const cm::domain::SysUser& user);
    static std::optional<cm::domain::SysUser> selectUserById(long long userId);
    static std::optional<cm::domain::SysUser> selectUserByUserName(const std::string& userName);
    static std::string checkUserNameUnique(const std::string& userName);
    static std::string checkPhoneUnique(const cm::domain::SysUser& user);
    static std::string checkEmailUnique(const cm::domain::SysUser& user);
    static void checkUserAllowed(const cm::domain::SysUser& user);
    static bool insertUser(cm::domain::SysUser& user);
    static int updateUser(cm::domain::SysUser& user);
    static int updateUserStatus(const cm::domain::SysUser& user);
    static int updateUserProfile(const cm::domain::SysUser& user);
    static int resetPwd(const cm::domain::SysUser& user);
    static int resetUserPwd(const std::string& userName, const std::string& password);
    static bool deleteUserById(long long userId);
    static int deleteUserByIds(const std::vector<long long>& userIds);
    static std::string selectUserRoleGroup(const std::string& userName);
    static std::string selectUserPostGroup(const std::string& userName);
    static cm::domain::SysUser selectCurrentUser();
};

} // namespace cm::system::service
