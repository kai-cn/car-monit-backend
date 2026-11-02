// 对应 Java: com.ruoyi.system.service.impl.SysRoleServiceImpl
#include "cm/system/service/SysRoleService.hpp"
#include "cm/system/mapper/SysRoleMapper.hpp"
#include "cm/system/mapper/SysUserRoleMapper.hpp"
#include "cm/system/mapper/SysRoleMenuMapper.hpp"
#include "cm/system/mapper/SysRoleDeptMapper.hpp"
#include "cm/common/exception/Exceptions.hpp"

namespace cm::system::service {

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
    if (info && info->roleId && info->roleId.value() != roleId) return "1";
    return "0";
}

std::string SysRoleService::checkRoleKeyUnique(const cm::domain::SysRole& role) {
    long long roleId = role.roleId.value_or(-1);
    auto info = cm::system::mapper::SysRoleMapper::checkRoleKeyUnique(role.roleKey.value_or(""));
    if (info && info->roleId && info->roleId.value() != roleId) return "1";
    return "0";
}

void SysRoleService::checkRoleAllowed(const cm::domain::SysRole& role) {
    if (role.roleId && role.isAdmin()) {
        throw cm::exception::CustomException("不允许操作超级管理员角色");
    }
}

int SysRoleService::insertRole(cm::domain::SysRole& role) {
    if (!cm::system::mapper::SysRoleMapper::insertRole(role)) return 0;
    if (role.menuIds && role.roleId) {
        std::vector<std::pair<long long, long long>> rms;
        for (long long menuId : *role.menuIds) rms.push_back({*role.roleId, menuId});
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
            for (long long menuId : *role.menuIds) rms.push_back({*role.roleId, menuId});
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
            for (long long deptId : *role.deptIds) rds.push_back({*role.roleId, deptId});
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
        cm::domain::SysRole r;
        r.roleId = roleId;
        checkRoleAllowed(r);
        auto role = selectRoleById(roleId);
        if (cm::system::mapper::SysUserRoleMapper::countUserRoleByRoleId(roleId) > 0) {
            throw cm::exception::CustomException(role->roleName.value_or("") + "已分配,不能删除");
        }
    }
    cm::system::mapper::SysRoleMenuMapper::deleteRoleMenu(roleIds);
    cm::system::mapper::SysRoleDeptMapper::deleteRoleDept(roleIds);
    return cm::system::mapper::SysRoleMapper::deleteRoleByIds(roleIds) ? static_cast<int>(roleIds.size()) : 0;
}

} // namespace cm::system::service
