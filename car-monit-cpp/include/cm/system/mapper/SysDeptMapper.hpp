#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysDeptMapper
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysDept.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysDeptMapper {
public:
    static std::vector<cm::domain::SysDept> selectDeptList(const cm::domain::SysDept& dept);
    static std::optional<cm::domain::SysDept> selectDeptById(long long deptId);
    static std::vector<long long> selectDeptListByRoleId(long long roleId, bool deptCheckStrictly);
    static std::optional<cm::domain::SysDept> checkDeptNameUnique(const std::string& deptName, long long parentId);
    static int hasChildByDeptId(long long deptId);
    static int checkDeptExistUser(long long deptId);
    static int selectNormalChildrenDeptById(long long deptId);
    static bool insertDept(cm::domain::SysDept& dept);
    static bool updateDept(const cm::domain::SysDept& dept);
    static bool deleteDeptById(long long deptId);
    static std::optional<cm::domain::SysDept> selectTenantId(const cm::domain::SysDept& dept);

    static cm::domain::SysDept mapDept(const cm::db::Row& row);
};

} // namespace cm::system::mapper
