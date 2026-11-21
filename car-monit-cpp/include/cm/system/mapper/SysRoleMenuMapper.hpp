#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysRoleMenuMapper
#include <string>
#include <vector>

namespace cm::system::mapper {

class SysRoleMenuMapper {
public:
    static bool deleteRoleMenuByRoleId(long long roleId);
    static bool deleteRoleMenu(const std::vector<long long>& roleIds);
    static bool batchRoleMenu(const std::vector<std::pair<long long, long long>>& roleMenus);
    static int checkMenuExistRole(long long menuId);
};

} // namespace cm::system::mapper
