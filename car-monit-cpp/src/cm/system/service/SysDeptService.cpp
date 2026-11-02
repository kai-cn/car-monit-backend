// 对应 Java: com.ruoyi.system.service.impl.SysDeptServiceImpl
#include "cm/system/service/SysDeptService.hpp"
#include "cm/system/mapper/SysDeptMapper.hpp"
#include "cm/system/mapper/SysRoleMapper.hpp"
#include "cm/common/exception/Exceptions.hpp"

namespace cm::system::service {

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
    if (info && info->deptId && info->deptId.value() != deptId) return "1";
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
    if (!dept.parentId) { dept.parentId = 0; dept.isUint = "1"; }
    if (dept.parentId.value() == 0) { dept.treeLeavel = 1; }
    else {
        auto parent = cm::system::mapper::SysDeptMapper::selectDeptById(*dept.parentId);
        if (parent) dept.treeLeavel = (parent->treeLeavel.value_or(1)) + 1;
    }
    return cm::system::mapper::SysDeptMapper::insertDept(dept) ? 1 : 0;
}

int SysDeptService::updateDept(cm::domain::SysDept& dept) {
    return cm::system::mapper::SysDeptMapper::updateDept(dept) ? 1 : 0;
}

int SysDeptService::deleteDeptById(long long deptId) {
    return cm::system::mapper::SysDeptMapper::deleteDeptById(deptId) ? 1 : 0;
}

namespace {
void recursionFn(std::vector<cm::domain::SysDept>& list, cm::domain::SysDept& t) {
    std::vector<cm::domain::SysDept> childList;
    for (auto& n : list) {
        if (n.parentId && t.deptId && *n.parentId == *t.deptId) childList.push_back(n);
    }
    t.children = childList;
    for (auto& child : t.children) recursionFn(list, child);
}
} // namespace

std::vector<cm::domain::SysDept> SysDeptService::buildDeptTree(std::vector<cm::domain::SysDept> depts) {
    std::vector<cm::domain::SysDept> returnList;
    std::vector<long long> tempList;
    for (const auto& dept : depts) { if (dept.deptId) tempList.push_back(*dept.deptId); }
    for (auto it = depts.begin(); it != depts.end(); ) {
        if (std::find(tempList.begin(), tempList.end(), it->parentId.value_or(0)) == tempList.end()) {
            cm::domain::SysDept d = *it;
            recursionFn(depts, d);
            returnList.push_back(d);
            it = depts.erase(it);
        } else { ++it; }
    }
    if (returnList.empty()) returnList = depts;
    return returnList;
}

Json SysDeptService::buildDeptTreeSelect(const std::vector<cm::domain::SysDept>& depts) {
    auto trees = buildDeptTree(depts);
    Json arr = Json::array();
    for (const auto& d : trees) arr.push_back(d.toJson());
    return arr;
}

std::set<cm::domain::SysDept> SysDeptService::selectHeadOffice() {
    cm::domain::SysDept query;
    auto list = selectDeptList(query);
    std::set<cm::domain::SysDept> filterSet;
    std::set<long long> filterDeptIds;
    for (const auto& dept : list) {
        if (dept.treeLeavel && (*dept.treeLeavel == 1 || *dept.treeLeavel == 2)) {
            filterSet.insert(dept);
            if (dept.deptId) filterDeptIds.insert(*dept.deptId);
        }
    }
    for (const auto& dept : list) {
        if (dept.tenantId && filterDeptIds.count(*dept.tenantId)) filterSet.insert(dept);
    }
    return filterSet;
}

} // namespace cm::system::service
