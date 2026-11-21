#pragma once
// 对应 Java: com.ruoyi.system.service.impl.SysMenuServiceImpl（登录/路由所需部分）
#include <set>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysMenu.hpp"

namespace cm::system::service {

class SysMenuService {
public:
    /** 对应 selectMenuPermsByUserId：按逗号拆分并 trim，忽略空串 */
    static std::set<std::string> selectMenuPermsByUserId(long long userId);
    /** 对应 selectMenuTreeByUserId：管理员取全量，否则按角色过滤，最后转树 */
    static std::vector<cm::domain::SysMenu> selectMenuTreeByUserId(long long userId);
    /** 对应 buildMenus(List<SysMenu>) */
    static Json buildMenus(const std::vector<cm::domain::SysMenu>& menus);

    /** 对应 getChildPerms(list, parentId) */
    static std::vector<cm::domain::SysMenu> getChildPerms(std::vector<cm::domain::SysMenu> list,
                                                          long long parentId);
    static bool isMenuFrame(const cm::domain::SysMenu& menu);
    static bool isParentView(const cm::domain::SysMenu& menu);

    // --- CRUD additions (SysMenuController) ---
    static std::vector<cm::domain::SysMenu> selectMenuList(const cm::domain::SysMenu& menu, long long userId);
    static std::vector<cm::domain::SysMenu> selectMenuList(long long userId);
    static std::optional<cm::domain::SysMenu> selectMenuById(long long menuId);
    static std::vector<long long> selectMenuListByRoleId(long long roleId);
    static std::string checkMenuNameUnique(const cm::domain::SysMenu& menu);
    static int insertMenu(cm::domain::SysMenu& menu);
    static int updateMenu(cm::domain::SysMenu& menu);
    static bool hasChildByMenuId(long long menuId);
    static bool checkMenuExistRole(long long menuId);
    static int deleteMenuById(long long menuId);
    static std::vector<cm::domain::SysMenu> buildMenuTree(std::vector<cm::domain::SysMenu> menus);
    static Json buildMenuTreeSelect(const std::vector<cm::domain::SysMenu>& menus);
};

} // namespace cm::system::service
