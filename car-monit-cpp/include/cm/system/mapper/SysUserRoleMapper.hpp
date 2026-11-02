#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysUserRoleMapper
#include <string>
#include <vector>

namespace cm::system::mapper {

class SysUserRoleMapper {
public:
    static bool deleteUserRoleByUserId(long long userId);
    static bool deleteUserRole(const std::vector<long long>& userIds);
    static bool batchUserRole(const std::vector<std::pair<long long, long long>>& userRoles);
    static int countUserRoleByRoleId(long long roleId);
    static int countUserRoleByRoleIdUserId(long long roleId, long long userId);
};

} // namespace cm::system::mapper
