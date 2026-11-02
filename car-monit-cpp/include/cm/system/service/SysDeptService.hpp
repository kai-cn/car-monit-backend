#pragma once
// 对应 Java: com.ruoyi.system.service.ISysDeptService
#include <optional>
#include <string>
#include <vector>
#include <set>

#include "cm/common/core/domain/entity/SysDept.hpp"

namespace cm::system::service {

class SysDeptService {
public:
    static std::vector<cm::domain::SysDept> selectDeptList(const cm::domain::SysDept& dept);
    static std::optional<cm::domain::SysDept> selectDeptById(long long deptId);
    static std::vector<long long> selectDeptListByRoleId(long long roleId);
    static std::string checkDeptNameUnique(const cm::domain::SysDept& dept);
    static bool hasChildByDeptId(long long deptId);
    static bool checkDeptExistUser(long long deptId);
    static int selectNormalChildrenDeptById(long long deptId);
    static int insertDept(cm::domain::SysDept& dept);
    static int updateDept(cm::domain::SysDept& dept);
    static int deleteDeptById(long long deptId);
    static std::vector<cm::domain::SysDept> buildDeptTree(std::vector<cm::domain::SysDept> depts);
    static Json buildDeptTreeSelect(const std::vector<cm::domain::SysDept>& depts);
    static std::set<cm::domain::SysDept> selectHeadOffice();
};

} // namespace cm::system::service
