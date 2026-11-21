#pragma once
// 对应 Java: com.ruoyi.system.domain.SysIndexMenu + ISysIndexMenuService + SysIndexMenuMapper
//
// 这里把 mapper 与 service 放在同一个头文件里，是因为该模块两个类都只有几行、
// 且 ServiceImpl 只是转发 + 补审计字段；拆开只会让 Java 同学多跳一次文件。
//
// 与 Java 对齐的三个坑（都刻意保留，不做“顺手修正”）：
//   1. SysIndexMenu 继承 BaseUuidEntity，**id 在 Java 里是 String**，
//      而库里 sys_index_menu.ID 是 bigint、createBy/updateBy 是 bigint。
//      Java 的 saveSysIndexMenu 用 StringUtils.getUUID() 生成 32 位十六进制串写入
//      bigint 列，在 STRICT_TRANS_TABLES 下必然报 1366 —— 也就是说 Java 的
//      PUT /system/indexmenu 本来就是 500。C++ 侧发同一条 SQL，得到同样的错误。
//   2. selectSysIndexMenuList 的 SQL 根本不是 sys_index_menu 表的投影，而是
//      sys_menu 自连接的“可选菜单”查询（返回 menuName2/menu_id/menu_name）；
//      所以这个模块不能走通用 CRUD 引擎，必须手写。
//   3. <if test="userId != 1"> 在 userId 为 null 时成立（OGNL 语义），
//      与 Java 一样按字符串比较处理。
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"

namespace cm::system::service {

struct IndexMenuQuery {
    std::optional<long long> userId;
    std::optional<std::string> menuName;
    std::optional<std::string> menuName2;
};

class SysIndexMenuService {
public:
    /** 对应 SysIndexMenuMapper.selectSysIndexMenuList（sys_menu 自连接，非本表投影） */
    static Json selectSysIndexMenuListJson(const IndexMenuQuery& q);
    /** 同上 + PageHelper 分页：对应 Java 的 startPage() + getDataTable(list) */
    static std::pair<Json, long long> selectSysIndexMenuListPage(const IndexMenuQuery& q,
                                                                 const cm::db::PageRequest& page);
    /** 对应 getList：我常用菜单，limit 9 */
    static Json getListJson(long long userId);
    /** 对应 selectSysIndexMenuById */
    static Json selectSysIndexMenuByIdJson(long long id);

    /** 对应 saveSysIndexMenu：有 id 则 update，否则用 UUID 插入；返回 Java 的 AjaxResult */
    static cm::core::domain::AjaxResult saveSysIndexMenu(const Json& body);
    /** 对应 insertSysIndexMenu(menuIds)：先按 (menuId,userId) 删再插 */
    static cm::core::domain::AjaxResult insertSysIndexMenu(const std::string& menuIds);
    /** 对应 deleteSysIndexMenuByIds：软删除，返回 AjaxResult.success(count) */
    static cm::core::domain::AjaxResult deleteSysIndexMenuByIds(const std::vector<long long>& ids);
};

} // namespace cm::system::service

namespace cm::web {
void registerSysIndexMenuController(cm::web::Router& r);
} // namespace cm::web
