#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysRoleMapper
#include <optional>
#include <utility>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysRole.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysRoleMapper {
public:
    /** 与 XML 的 selectRoleList 等价的 SQL（不含 LIMIT），供分页复用 */
    static std::string selectRoleListSql(const cm::domain::SysRole& role);
    /** PageHelper 语义的分页查询：count 包住同一条 dataSql；返回映射后的实体 + total */
    static std::pair<std::vector<cm::domain::SysRole>, long long>
    selectRoleEntityPage(const cm::domain::SysRole& role, const cm::db::PageRequest& page);
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
