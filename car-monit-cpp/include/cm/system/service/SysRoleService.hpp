#pragma once
// 对应 Java: com.ruoyi.system.service.ISysRoleService
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysRole.hpp"

namespace cm::system::service {

class SysRoleService {
public:
    static std::vector<cm::domain::SysRole> selectRoleList(const cm::domain::SysRole& role);
    static std::vector<cm::domain::SysRole> selectRoleAll();
    static std::optional<cm::domain::SysRole> selectRoleById(long long roleId);
    static std::vector<long long> selectRoleListByUserId(long long userId);
    static std::string checkRoleNameUnique(const cm::domain::SysRole& role);
    static std::string checkRoleKeyUnique(const cm::domain::SysRole& role);
    static void checkRoleAllowed(const cm::domain::SysRole& role);
    static int insertRole(cm::domain::SysRole& role);
    static int updateRole(cm::domain::SysRole& role);
    static int updateRoleStatus(const cm::domain::SysRole& role);
    static int authDataScope(cm::domain::SysRole& role);
    static int deleteRoleById(long long roleId);
    static int deleteRoleByIds(const std::vector<long long>& roleIds);
};

} // namespace cm::system::service
