// Consolidated service implementations for system auth CRUD
#include "cm/system/service/SysMenuService.hpp"
#include "cm/system/service/SysRoleService.hpp"
#include "cm/system/service/SysDeptService.hpp"
#include "cm/system/service/SysUserService.hpp"
#include "cm/system/mapper/SysMenuMapper.hpp"
#include "cm/system/mapper/SysRoleMapper.hpp"
#include "cm/system/mapper/SysDeptMapper.hpp"
#include "cm/system/mapper/SysUserMapper.hpp"
#include "cm/system/mapper/SysUserRoleMapper.hpp"
#include "cm/system/mapper/SysUserPostMapper.hpp"
#include "cm/system/mapper/SysRoleMenuMapper.hpp"
#include "cm/system/mapper/SysRoleDeptMapper.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"

namespace cm::system::service {

// ========== SysMenuService additions ==========
std::vector<cm::domain::SysMenu> SysMenuService::selectMenuList(const cm::domain::SysMenu& menu, long long userId) {
    if (cm::domain::SysUser::isAdmin(userId)) {
        return cm::system::mapper::SysMenuMapper::selectMenuList(menu);
    } else {
        return cm::system::mapper::SysMenuMapper::selectMenuListByUserId(menu, userId);
    }
}

std::vector<cm::domain::SysMenu> SysMenuService::selectMenuList(long long userId) {
    cm::domain::SysMenu menu;
    return selectMenuList(menu, userId);
}

std::optional<cm::domain::SysMenu> SysMenuService::selectMenuById(long long menuId) {
    return cm::system::mapper::SysMenuMapper::selectMenuById(menuId);
}

std::vector<long long> SysMenuService::selectMenuListByRoleId(long long roleId) {
    auto role = cm::system::mapper::SysRoleMapper::selectRoleById(roleId);
    bool strictly = role ? role->menuCheckStrictly : false;
    return cm::system::mapper::SysMenuMapper::selectMenuListByRoleId(roleId, strictly);
}

std::string SysMenuService::checkMenuNameUnique(const cm::domain::SysMenu& menu) {
    long long menuId = menu.menuId.value_or(-1);
    auto info = cm::system::mapper::SysMenuMapper::checkMenuNameUnique(menu.menuName.value_or(""), menu.parentId.value_or(0));
    if (info && info->menuId && info->menuId.value() != menuId) {
        return "1";
    }
    return "0";
}

int SysMenuService::insertMenu(cm::domain::SysMenu& menu) {
    return cm::system::mapper::SysMenuMapper::insertMenu(menu) ? 1 : 0;
}

int SysMenuService::updateMenu(cm::domain::SysMenu& menu) {
    return cm::system::mapper::SysMenuMapper::updateMenu(menu) ? 1 : 0;
}

bool SysMenuService::hasChildByMenuId(long long menuId) {
    return cm::system::mapper::SysMenuMapper::hasChildByMenuId(menuId) > 0;
}

bool SysMenuService::checkMenuExistRole(long long menuId) {
    return cm::system::mapper::SysRoleMenuMapper::checkMenuExistRole(menuId) > 0;
}

int SysMenuService::deleteMenuById(long long menuId) {
    return cm::system::mapper::SysMenuMapper::deleteMenuById(menuId) ? 1 : 0;
}

std::vector<cm::domain::SysMenu> SysMenuService::buildMenuTree(std::vector<cm::domain::SysMenu> menus) {
    std::vector<cm::domain::SysMenu> returnList;
    std::vector<long long> tempList;
    for (const auto& menu : menus) {
        if (menu.menuId) tempList.push_back(*menu.menuId);
    }
    for (auto it = menus.begin(); it != menus.end(); ) {
        if (std::find(tempList.begin(), tempList.end(), it->parentId.value_or(0)) == tempList.end()) {
            returnList.push_back(*it);
            it = menus.erase(it);
        } else {
            ++it;
        }
    }
    if (returnList.empty()) returnList = menus;
    return returnList;
}

Json SysMenuService::buildMenuTreeSelect(const std::vector<cm::domain::SysMenu>& menus) {
    // Simplified: return array of menu objects
    Json arr = Json::array();
    for (const auto& menu : menus) {
        arr.push_back(menu.toJson());
    }
    return arr;
}

// ========== SysRoleService ==========
std::vector<cm::domain::SysRole> SysRoleService::selectRoleList(const cm::domain::SysRole& role) {
    return cm::system::mapper::SysRoleMapper::selectRoleList(role);
}

std::vector<cm::domain::SysRole> SysRoleService::selectRoleAll() {
    cm::domain::SysRole role;
    return selectRoleList(role);
}

std::optional<cm::domain::SysRole> SysRoleService::selectRoleById(long long roleId) {
    return cm::system::mapper::SysRoleMapper::selectRoleById(roleId);
}

std::vector<long long> SysRoleService::selectRoleListByUserId(long long userId) {
    return cm::system::mapper::SysRoleMapper::selectRoleListByUserId(userId);
}

std::string SysRoleService::checkRoleNameUnique(const cm::domain::SysRole& role) {
    long long roleId = role.roleId.value_or(-1);
    auto info = cm::system::mapper::SysRoleMapper::checkRoleNameUnique(role.roleName.value_or(""));
    if (info && info->roleId && info->roleId.value() != roleId) {
        return "1";
    }
    return "0";
}

std::string SysRoleService::checkRoleKeyUnique(const cm::domain::SysRole& role) {
    long long roleId = role.roleId.value_or(-1);
    auto info = cm::system::mapper::SysRoleMapper::checkRoleKeyUnique(role.roleKey.value_or(""));
    if (info && info->roleId && info->roleId.value() != roleId) {
        return "1";
    }
    return "0";
}

void SysRoleService::checkRoleAllowed(const cm::domain::SysRole& role) {
    if (role.roleId && role.isAdmin()) {
        throw cm::exception::CustomException("不允许操作超级管理员角色");
    }
}

int SysRoleService::insertRole(cm::domain::SysRole& role) {
    if (!cm::system::mapper::SysRoleMapper::insertRole(role)) return 0;
    // Insert role-menu relations
    if (role.menuIds) {
        std::vector<std::pair<long long, long long>> rms;
        for (long long menuId : *role.menuIds) {
            rms.push_back(*role.roleId, menuId);
        }
        cm::system::mapper::SysRoleMenuMapper::batchRoleMenu(rms);
    }
    return 1;
}

int SysRoleService::updateRole(cm::domain::SysRole& role) {
    if (!cm::system::mapper::SysRoleMapper::updateRole(role)) return 0;
    if (role.roleId) {
        cm::system::mapper::SysRoleMenuMapper::deleteRoleMenuByRoleId(*role.roleId);
        if (role.menuIds) {
            std::vector<std::pair<long long, long long>> rms;
            for (long long menuId : *role.menuIds) {
                rms.push_back(*role.roleId, menuId);
            }
            cm::system::mapper::SysRoleMenuMapper::batchRoleMenu(rms);
        }
    }
    return 1;
}

int SysRoleService::updateRoleStatus(const cm::domain::SysRole& role) {
    return cm::system::mapper::SysRoleMapper::updateRole(role) ? 1 : 0;
}

int SysRoleService::authDataScope(cm::domain::SysRole& role) {
    if (!cm::system::mapper::SysRoleMapper::updateRole(role)) return 0;
    if (role.roleId) {
        cm::system::mapper::SysRoleDeptMapper::deleteRoleDeptByRoleId(*role.roleId);
        if (role.deptIds) {
            std::vector<std::pair<long long, long long>> rds;
            for (long long deptId : *role.deptIds) {
                rds.push_back(*role.roleId, deptId);
            }
            cm::system::mapper::SysRoleDeptMapper::batchRoleDept(rds);
        }
    }
    return 1;
}

int SysRoleService::deleteRoleById(long long roleId) {
    cm::system::mapper::SysRoleMenuMapper::deleteRoleMenuByRoleId(roleId);
    cm::system::mapper::SysRoleDeptMapper::deleteRoleDeptByRoleId(roleId);
    return cm::system::mapper::SysRoleMapper::deleteRoleById(roleId) ? 1 : 0;
}

int SysRoleService::deleteRoleByIds(const std::vector<long long>& roleIds) {
    for (long long roleId : roleIds) {
        cm::domain::SysRole role;
        role.roleId = roleId;
        checkRoleAllowed(role);
        auto r = selectRoleById(roleId);
        if (cm::system::mapper::SysUserRoleMapper::countUserRoleByRoleId(roleId) > 0) {
            throw cm::exception::CustomException(r->roleName.value_or("") + "已分配,不能删除");
        }
    }
    cm::system::mapper::SysRoleMenuMapper::deleteRoleMenu(roleIds);
    cm::system::mapper::SysRoleDeptMapper::deleteRoleDept(roleIds);
    return cm::system::mapper::SysRoleMapper::deleteRoleByIds(roleIds) ? static_cast<int>(roleIds.size()) : 0;
}

// ========== SysDeptService ==========
std::vector<cm::domain::SysDept> SysDeptService::selectDeptList(const cm::domain::SysDept& dept) {
    return cm::system::mapper::SysDeptMapper::selectDeptList(dept);
}

std::optional<cm::domain::SysDept> SysDeptService::selectDeptById(long long deptId) {
    return cm::system::mapper::SysDeptMapper::selectDeptById(deptId);
}

std::vector<long long> SysDeptService::selectDeptListByRoleId(long long roleId) {
    auto role = cm::system::mapper::SysRoleMapper::selectRoleById(roleId);
    bool strictly = role ? role->deptCheckStrictly : false;
    return cm::system::mapper::SysDeptMapper::selectDeptListByRoleId(roleId, strictly);
}

std::string SysDeptService::checkDeptNameUnique(const cm::domain::SysDept& dept) {
    long long deptId = dept.deptId.value_or(-1);
    auto info = cm::system::mapper::SysDeptMapper::checkDeptNameUnique(dept.deptName.value_or(""), dept.parentId.value_or(0));
    if (info && info->deptId && info->deptId.value() != deptId) {
        return "1";
    }
    return "0";
}

bool SysDeptService::hasChildByDeptId(long long deptId) {
    return cm::system::mapper::SysDeptMapper::hasChildByDeptId(deptId) > 0;
}

bool SysDeptService::checkDeptExistUser(long long deptId) {
    return cm::system::mapper::SysDeptMapper::checkDeptExistUser(deptId) > 0;
}

int SysDeptService::selectNormalChildrenDeptById(long long deptId) {
    return cm::system::mapper::SysDeptMapper::selectNormalChildrenDeptById(deptId);
}

int SysDeptService::insertDept(cm::domain::SysDept& dept) {
    // Simplified: just insert
    return cm::system::mapper::SysDeptMapper::insertDept(dept) ? 1 : 0;
}

int SysDeptService::updateDept(cm::domain::SysDept& dept) {
    return cm::system::mapper::SysDeptMapper::updateDept(dept) ? 1 : 0;
}

int SysDeptService::deleteDeptById(long long deptId) {
    return cm::system::mapper::SysDeptMapper::deleteDeptById(deptId) ? 1 : 0;
}

std::vector<cm::domain::SysDept> SysDeptService::buildDeptTree(std::vector<cm::domain::SysDept> depts) {
    // Simplified: return as-is
    return depts;
}

Json SysDeptService::buildDeptTreeSelect(const std::vector<cm::domain::SysDept>& depts) {
    Json arr = Json::array();
    for (const auto& dept : depts) {
        arr.push_back(dept.toJson());
    }
    return arr;
}

std::set<cm::domain::SysDept> SysDeptService::selectHeadOffice() {
    cm::domain::SysDept query;
    auto list = selectDeptList(query);
    std::set<cm::domain::SysDept> result;
    for (const auto& dept : list) {
        if (dept.treeLeavel && (*dept.treeLeavel == 1 || *dept.treeLeavel == 2)) {
            result.insert(dept);
        }
    }
    return result;
}

// ========== SysUserService ==========
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
    if (info && info->userId && info->userId.value() != userId) {
        return "1";
    }
    return "0";
}

std::string SysUserService::checkEmailUnique(const cm::domain::SysUser& user) {
    long long userId = user.userId.value_or(-1);
    auto info = cm::system::mapper::SysUserMapper::checkEmailUnique(user.email.value_or(""));
    if (info && info->userId && info->userId.value() != userId) {
        return "1";
    }
    return "0";
}

void SysUserService::checkUserAllowed(const cm::domain::SysUser& user) {
    if (user.userId && user.isAdmin()) {
        throw cm::exception::CustomException("不允许操作超级管理员用户");
    }
}

bool SysUserService::insertUser(cm::domain::SysUser& user) {
    // Set tenant info from dept
    if (user.deptId) {
        auto dept = cm::system::mapper::SysDeptMapper::selectDeptById(*user.deptId);
        if (dept) {
            user.bussName = dept->deptName;
            user.tenantId = dept->tenantId;
        }
    }
    if (!cm::system::mapper::SysUserMapper::insertUser(user)) return false;
    // Insert user-role and user-post relations
    if (user.userId) {
        if (user.roleIds) {
            std::vector<std::pair<long long, long long>> urs;
            for (long long roleId : *user.roleIds) {
                urs.push_back(*user.userId, roleId);
            }
            cm::system::mapper::SysUserRoleMapper::batchUserRole(urs);
        }
        if (user.postIds) {
            std::vector<std::pair<long long, long long>> ups;
            for (long long postId : *user.postIds) {
                ups.push_back(*user.userId, postId);
            }
            cm::system::mapper::SysUserPostMapper::batchUserPost(ups);
        }
    }
    return true;
}

int SysUserService::updateUser(cm::domain::SysUser& user) {
    if (!user.userId) return 0;
    // Delete and re-insert relations
    cm::system::mapper::SysUserRoleMapper::deleteUserRoleByUserId(*user.userId);
    cm::system::mapper::SysUserPostMapper::deleteUserPostByUserId(*user.userId);
    // Set tenant info
    if (user.deptId) {
        auto dept = cm::system::mapper::SysDeptMapper::selectDeptById(*user.deptId);
        if (dept) {
            user.bussName = dept->deptName;
            user.tenantId = dept->tenantId;
        }
    }
    int rows = cm::system::mapper::SysUserMapper::updateUser(user);
    // Re-insert relations
    if (user.roleIds) {
        std::vector<std::pair<long long, long long>> urs;
        for (long long roleId : *user.roleIds) {
            urs.push_back(*user.userId, roleId);
        }
        cm::system::mapper::SysUserRoleMapper::batchUserRole(urs);
    }
    if (user.postIds) {
        std::vector<std::pair<long long, long long>> ups;
        for (long long postId : *user.postIds) {
            ups.push_back(*user.userId, postId);
        }
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

int SysUserService::resetUserPwd(const std::string& userName, const std::string& password) {
    return cm::system::mapper::SysUserMapper::resetUserPwd(userName, password);
}

bool SysUserService::deleteUserById(long long userId) {
    cm::system::mapper::SysUserRoleMapper::deleteUserRoleByUserId(userId);
    cm::system::mapper::SysUserPostMapper::deleteUserPostByUserId(userId);
    return cm::system::mapper::SysUserMapper::deleteUserById(userId);
}

int SysUserService::deleteUserByIds(const std::vector<long long>& userIds) {
    for (long long userId : userIds) {
        cm::domain::SysUser user;
        user.userId = userId;
        checkUserAllowed(user);
    }
    cm::system::mapper::SysUserRoleMapper::deleteUserRole(userIds);
    cm::system::mapper::SysUserPostMapper::deleteUserPost(userIds);
    return cm::system::mapper::SysUserMapper::deleteUserByIds(userIds);
}

std::string SysUserService::selectUserRoleGroup(const std::string& userName) {
    auto roles = cm::system::mapper::SysRoleMapper::selectRolesByUserName(userName);
    std::string result;
    for (const auto& role : roles) {
        if (!result.empty()) result += ",";
        result += role.roleName.value_or("");
    }
    return result;
}

std::string SysUserService::selectUserPostGroup(const std::string& userName) {
    auto posts = cm::system::mapper::SysPostMapper::selectPostsByUserName(userName);
    std::string result;
    for (const auto& post : posts) {
        if (!result.empty()) result += ",";
        result += post.postName.value_or("");
    }
    return result;
}

cm::domain::SysUser SysUserService::selectCurrentUser() {
    auto loginUser = cm::security::SecurityUtils::getLoginUser();
    cm::domain::SysUser user = loginUser.user;
    user.headOffice = false;
    user.procurementManager = false;
    // Simplified: return user as-is
    return user;
}

} // namespace cm::system::service
