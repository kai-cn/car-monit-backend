#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysMenuMapper（登录/路由所需部分）
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysMenu.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysMenuMapper {
public:
    /** selectMenuTreeAll：管理员全量菜单（M/C） */
    static std::vector<cm::domain::SysMenu> selectMenuTreeAll();
    /** selectMenuTreeByUserId */
    static std::vector<cm::domain::SysMenu> selectMenuTreeByUserId(long long userId);
    /** selectMenuPermsByUserId：原始 perms 字符串（可能逗号分隔） */
    static std::vector<std::string> selectMenuPermsByUserId(long long userId);

    static cm::domain::SysMenu mapMenu(const cm::db::Row& row);

    // --- CRUD additions (SysMenuController / SysMenuServiceImpl) ---
    static std::vector<cm::domain::SysMenu> selectMenuList(const cm::domain::SysMenu& menu);
    static std::vector<cm::domain::SysMenu> selectMenuListByUserId(const cm::domain::SysMenu& menu, long long userId);
    static std::optional<cm::domain::SysMenu> selectMenuById(long long menuId);
    static int hasChildByMenuId(long long menuId);
    static std::optional<cm::domain::SysMenu> checkMenuNameUnique(const std::string& menuName, long long parentId);
    static bool insertMenu(cm::domain::SysMenu& menu);
    static bool updateMenu(const cm::domain::SysMenu& menu);
    static bool deleteMenuById(long long menuId);
    static std::vector<long long> selectMenuListByRoleId(long long roleId, bool menuCheckStrictly);
};

} // namespace cm::system::mapper
