#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysRoleMapper
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysRole.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysRoleMapper {
public:
    static std::vector<cm::domain::SysRole> selectRoleList(const cm::domain::SysRole& role);
    static std::vector<cm::domain::SysRole> selectRoleAll();
    static std::optional<cm::domain::SysRole> selectRoleById(long long roleId);
    static std::vector<cm::domain::SysRole> selectRolesByUserName(const std::string& userName);
    static std::vector<long long> selectRoleListByUserId(long long userId);
    static std::optional<cm::domain::SysRole> checkRoleNameUnique(const std::string& roleName);
    static std::optional<cm::domain::SysRole> checkRoleKeyUnique(const std::string& roleKey);
    static bool insertRole(cm::domain::SysRole& role);
    static bool updateRole(const cm::domain::SysRole& role);
    static bool deleteRoleById(long long roleId);
    static bool deleteRoleByIds(const std::vector<long long>& roleIds);

    static cm::domain::SysRole mapRole(const cm::db::Row& row);
};

} // namespace cm::system::mapper
