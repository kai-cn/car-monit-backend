#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysRoleDeptMapper
#include <string>
#include <vector>

namespace cm::system::mapper {

class SysRoleDeptMapper {
public:
    static bool deleteRoleDeptByRoleId(long long roleId);
    static bool deleteRoleDept(const std::vector<long long>& roleIds);
    static bool batchRoleDept(const std::vector<std::pair<long long, long long>>& roleDepts);
};

} // namespace cm::system::mapper
