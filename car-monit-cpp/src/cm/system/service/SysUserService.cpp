// 对应 Java: com.ruoyi.system.service.impl.SysUserServiceImpl
#include "cm/system/service/SysUserService.hpp"
#include "cm/system/mapper/SysUserMapper.hpp"
#include "cm/system/mapper/SysRoleMapper.hpp"
#include "cm/system/mapper/SysPostMapper.hpp"
#include "cm/system/mapper/SysDeptMapper.hpp"
#include "cm/system/mapper/SysUserRoleMapper.hpp"
#include "cm/system/mapper/SysUserPostMapper.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/framework/security/SecurityUtils.hpp"

namespace cm::system::service {

std::pair<std::vector<cm::domain::SysUser>, long long> SysUserService::selectUserEntityPage(
        const cm::domain::SysUser& user, const cm::db::PageRequest& page) {
    return cm::system::mapper::SysUserMapper::selectUserEntityPage(user, page);
}

std::vector<cm::domain::SysUser> SysUserService::selectUserList(const cm::domain::SysUser& user) {
    return cm::system::mapper::SysUserMapper::selectUserList(user);
}

std::optional<cm::domain::SysUser> SysUserService::selectUserById(long long userId) {
    return cm::system::mapper::SysUserMapper::selectUserById(userId);
}

std::optional<cm::domain::SysUser> SysUserService::selectUserByUserName(const std::string& userName) {
    return cm::system::mapper::SysUserMapper::selectUserByUserName(userName);
}

std::string SysUserService::checkUserNameUnique(const std::string& userName) {
    int count = cm::system::mapper::SysUserMapper::checkUserNameUnique(userName);
    return count > 0 ? "1" : "0";
}

std::string SysUserService::checkPhoneUnique(const cm::domain::SysUser& user) {
    long long userId = user.userId.value_or(-1);
    auto info = cm::system::mapper::SysUserMapper::checkPhoneUnique(user.phonenumber.value_or(""));
    if (info && info->userId && info->userId.value() != userId) return "1";
    return "0";
}

std::string SysUserService::checkEmailUnique(const cm::domain::SysUser& user) {
    long long userId = user.userId.value_or(-1);
    auto info = cm::system::mapper::SysUserMapper::checkEmailUnique(user.email.value_or(""));
    if (info && info->userId && info->userId.value() != userId) return "1";
    return "0";
}

void SysUserService::checkUserAllowed(const cm::domain::SysUser& user) {
    if (user.userId && user.isAdmin()) {
        throw cm::exception::CustomException("不允许操作超级管理员用户");
    }
}

bool SysUserService::insertUser(cm::domain::SysUser& user) {
    if (user.deptId) {
        auto dept = cm::system::mapper::SysDeptMapper::selectDeptById(*user.deptId);
        if (dept) { user.bussName = dept->deptName; user.tenantId = dept->tenantId; }
    }
    if (!cm::system::mapper::SysUserMapper::insertUser(user)) return false;
    if (user.userId) {
        if (user.roleIds) {
            std::vector<std::pair<long long, long long>> urs;
            for (long long rid : *user.roleIds) urs.push_back({*user.userId, rid});
            cm::system::mapper::SysUserRoleMapper::batchUserRole(urs);
        }
        if (user.postIds) {
            std::vector<std::pair<long long, long long>> ups;
            for (long long pid : *user.postIds) ups.push_back({*user.userId, pid});
            cm::system::mapper::SysUserPostMapper::batchUserPost(ups);
        }
    }
    return true;
}

int SysUserService::updateUser(cm::domain::SysUser& user) {
    if (!user.userId) return 0;
    cm::system::mapper::SysUserRoleMapper::deleteUserRoleByUserId(*user.userId);
    cm::system::mapper::SysUserPostMapper::deleteUserPostByUserId(*user.userId);
    if (user.deptId) {
        auto dept = cm::system::mapper::SysDeptMapper::selectDeptById(*user.deptId);
        if (dept) { user.bussName = dept->deptName; user.tenantId = dept->tenantId; }
    }
    int rows = cm::system::mapper::SysUserMapper::updateUser(user);
    if (user.roleIds) {
        std::vector<std::pair<long long, long long>> urs;
        for (long long rid : *user.roleIds) urs.push_back({*user.userId, rid});
        cm::system::mapper::SysUserRoleMapper::batchUserRole(urs);
    }
    if (user.postIds) {
        std::vector<std::pair<long long, long long>> ups;
        for (long long pid : *user.postIds) ups.push_back({*user.userId, pid});
        cm::system::mapper::SysUserPostMapper::batchUserPost(ups);
    }
    return rows;
}

int SysUserService::updateUserStatus(const cm::domain::SysUser& user) {
    return cm::system::mapper::SysUserMapper::updateUser(user);
}

int SysUserService::updateUserProfile(const cm::domain::SysUser& user) {
    return cm::system::mapper::SysUserMapper::updateUser(user);
}

int SysUserService::resetPwd(const cm::domain::SysUser& user) {
    return cm::system::mapper::SysUserMapper::updateUser(user);
}

bool SysUserService::updateUserAvatar(const std::string& userName, const std::string& avatar) {
    return cm::system::mapper::SysUserMapper::updateUserAvatar(userName, avatar);
}

int SysUserService::resetUserPwd(const std::string& userName, const std::string& password) {
    return cm::system::mapper::SysUserMapper::resetUserPwd(userName, password);
}

bool SysUserService::deleteUserById(long long userId) {
    cm::system::mapper::SysUserRoleMapper::deleteUserRoleByUserId(userId);
    cm::system::mapper::SysUserPostMapper::deleteUserPostByUserId(userId);
    return cm::system::mapper::SysUserMapper::deleteUserById(userId);
}

int SysUserService::deleteUserByIds(const std::vector<long long>& userIds) {
    for (long long uid : userIds) {
        cm::domain::SysUser u; u.userId = uid;
        checkUserAllowed(u);
    }
    cm::system::mapper::SysUserRoleMapper::deleteUserRole(userIds);
    cm::system::mapper::SysUserPostMapper::deleteUserPost(userIds);
    return cm::system::mapper::SysUserMapper::deleteUserByIds(userIds);
}

std::string SysUserService::selectUserRoleGroup(const std::string& userName) {
    auto roles = cm::system::mapper::SysRoleMapper::selectRolesByUserName(userName);
    std::string result;
    for (const auto& r : roles) { if (!result.empty()) result += ","; result += r.roleName.value_or(""); }
    return result;
}

std::string SysUserService::selectUserPostGroup(const std::string& userName) {
    auto posts = cm::system::mapper::SysPostMapper::selectPostsByUserName(userName);
    std::string result;
    for (const auto& p : posts) { if (!result.empty()) result += ","; result += p.postName.value_or(""); }
    return result;
}

cm::domain::SysUser SysUserService::selectCurrentUser() {
    auto loginUser = cm::security::SecurityUtils::getLoginUser();
    cm::domain::SysUser user = loginUser.user;
    user.headOffice = false;
    user.procurementManager = false;
    return user;
}

} // namespace cm::system::service
