// 对应 Java: SysIndexMenuServiceImpl + SysIndexMenuMapper.xml + SysIndexMenuController
#include "cm/system/service/SysIndexMenuService.hpp"

#include <ctime>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::system::service {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::StringUtils;

std::string nowDb() {
    return cm::utils::DateUtils::formatMillis(cm::utils::DateUtils::nowMillis());
}

/** 行 -> JSON：这些 SQL 的列名不全是实体属性，MyBatis 按标签自动映射 */
Json rowsToJson(const cm::db::Result& res) {
    Json arr = Json::array();
    for (const auto& row : res.rows) {
        Json j = Json::object();
        for (const auto& col : row.columns()) {
            auto v = row.get(col);
            if (col == "menuId" || col == "MENU_ID" || col == "ID" || col == "id" ||
                col == "USER_ID" || col == "userId" || col == "menu_id") {
                j[col] = row.optI64(col) ? Json(*row.optI64(col)) : Json(nullptr);
            } else {
                j[col] = v ? Json(*v) : Json(nullptr);
            }
        }
        arr.push_back(std::move(j));
    }
    return arr;
}

/** Json 标量 -> SQL 字面量（Db::lit 的重载对 Json 有歧义，这里显式分流） */
std::string litJson(const Json& v) {
    if (v.is_null()) return "NULL";
    if (v.is_boolean()) return cm::db::bind(v.get<bool>());
    if (v.is_number_integer()) return cm::db::bind(static_cast<long long>(v.get<long long>()));
    if (v.is_number_float()) return cm::db::bind(v.get<double>());
    if (v.is_string()) return cm::db::bind(v.get<std::string>());
    return cm::db::bind(v.dump());
}

int execute(const std::string& sql) {
    long long affected = 0;
    if (!Db::instance().execute(sql, &affected)) return -1;
    return static_cast<int>(affected);
}

} // namespace

namespace {

Json rowsOf(const std::string& sql) {
    cm::db::Result res;
    if (!Db::instance().query(sql, res)) return Json::array();
    return rowsToJson(res);
}

std::string listSql(const IndexMenuQuery& q) {
    // 逐条对应 SysIndexMenuMapper.xml 的 selectSysIndexMenuList
    std::string sql =
        "select t2.menu_name as menuName2, t1.menu_id, t1.menu_name"
        " from sys_menu t1, sys_menu t2"
        " where t1.menu_type='C' and t1.visible = '0' and t2.menu_id = t1.parent_id";
    // <if test="userId != 1">：userId 为 null 时该条件同样成立（OGNL 语义）
    if (!q.userId || *q.userId != 1) {
        sql += " and exists ( select 1 from sys_role_menu rm,sys_user_role ur"
               " where rm.role_id = ur.role_id and rm.menu_id = t1.menu_id and ur.user_id = " +
               cm::db::bind(q.userId) + ")";
    }
    sql += " and not exists ( select 1 from sys_index_menu tim where tim.del_flag = '0'"
           " and tim.menu_id = t1.menu_id and tim.user_id = " + cm::db::bind(q.userId) + ")";
    sql += " and not exists ( select 1 from sys_menu t3 where t3.menu_type = 'C'"
           " and t3.parent_id = t1.menu_id)";
    if (q.menuName && !q.menuName->empty()) {
        sql += " and t1.menu_name like concat('%', " + cm::db::bind(*q.menuName) + ", '%')";
    }
    if (q.menuName2 && !q.menuName2->empty()) {
        sql += " and t2.menu_name like concat('%', " + cm::db::bind(*q.menuName2) + ", '%')";
    }
    sql += " order by t2.parent_id, t2.order_num, t1.order_num, t1.menu_id";
    return sql;
}

} // namespace

Json SysIndexMenuService::selectSysIndexMenuListJson(const IndexMenuQuery& q) {
    return rowsOf(listSql(q));
}


std::pair<Json, long long> SysIndexMenuService::selectSysIndexMenuListPage(
    const IndexMenuQuery& q, const cm::db::PageRequest& page) {
    // 与 selectSysIndexMenuListJson 同一条 SQL，只多套一层 PageHelper 的 count + LIMIT
    std::string sql = listSql(q);
    auto pr = cm::db::queryPage("select count(1) from (" + sql + ") page_count", sql, page);
    return {rowsToJson(pr.rows), pr.total};
}

Json SysIndexMenuService::getListJson(long long userId) {
    // 对应 getList（“查询我常用的菜单”），注意表名在 XML 里写成大写 SYS_INDEX_MENU
    const std::string sql =
        "select t.id, t1.menu_name, concat(t2.path,'/',t1.path) as menuUrl"
        " from SYS_INDEX_MENU t"
        " left join sys_menu t1 on t.MENU_ID = t1.menu_id"
        " left join sys_menu t2 on t1.parent_id = t2.menu_id"
        " where t.del_flag='0' and t.USER_ID = " + cm::db::bind(userId) +
        " order by t.CREATE_TIME desc limit 9";
    cm::db::Result res;
    if (!Db::instance().query(sql, res)) return Json::array();
    return rowsToJson(res);
}

Json SysIndexMenuService::selectSysIndexMenuByIdJson(long long id) {
    const std::string sql =
        "select t.ID, t.USER_ID, t.MENU_ID, t.SORT, t.EPS_ID, t.DEL_FLAG, t.CREATE_BY,"
        " t.CREATE_TIME, t.UPDATE_BY, t.UPDATE_TIME, t.TENANT_ID"
        " from sys_index_menu t where t.ID = " + cm::db::bind(id);
    cm::db::Result res;
    if (!Db::instance().query(sql, res) || res.rows.empty()) return Json(nullptr);
    Json j = Json::object();
    for (const auto& col : res.rows.front().columns()) {
        auto v = res.rows.front().get(col);
        j[col] = v ? Json(*v) : Json(nullptr);
    }
    return j;
}

cm::core::domain::AjaxResult SysIndexMenuService::saveSysIndexMenu(const Json& body) {
    const long long userId = cm::security::SecurityUtils::getUserId();
    const std::string ts = nowDb();
    auto getStr = [&](const char* k) -> std::string {
        if (body.is_object() && body.contains(k) && !body[k].is_null()) {
            return body[k].is_string() ? body[k].get<std::string>() : body[k].dump();
        }
        return "";
    };
    const std::string id = getStr("id");
    if (!id.empty()) {
        std::string sets = "UPDATE_BY = " + cm::db::bind(userId) + ", UPDATE_TIME = " + cm::db::bind(ts);
        if (auto v = body.find("menuId"); v != body.end() && !v->is_null())
            sets += ", MENU_ID = " + litJson(*v);
        if (auto v = body.find("sort"); v != body.end() && !v->is_null())
            sets += ", SORT = " + litJson(*v);
        if (auto v = body.find("epsId"); v != body.end() && !v->is_null())
            sets += ", EPS_ID = " + litJson(*v);
        // Java 的 <if test="id != null"> 不含 ID 列（WHERE 用），此处一致
        if (execute("update sys_index_menu SET " + sets + " where ID = " + cm::db::bind(id)) < 0) {
            return AjaxResult::error("操作失败");
        }
        return AjaxResult::success("操作成功！", Json(id));
    }
    // ⚠️ Java: sysIndexMenu.setId(StringUtils.getUUID()) —— 把 32 位十六进制串写进
    //    bigint 的 ID 列。库里开着 STRICT_TRANS_TABLES，这条语句在 Java 侧同样报
    //    1366，即 PUT /system/indexmenu 本来就是 500；这里刻意照抄，不做修正。
    const std::string newId = cm::utils::simpleUuid();
    std::string cols = "ID, ", vals = cm::db::bind(newId);
    cols += ", USER_ID"; vals += ", " + cm::db::bind(userId);
    if (auto v = body.find("menuId"); v != body.end() && !v->is_null()) {
        cols += ", MENU_ID"; vals += ", " + litJson(*v);
    }
    if (auto v = body.find("sort"); v != body.end() && !v->is_null()) {
        cols += ", SORT"; vals += ", " + litJson(*v);
    }
    cols += ", DEL_FLAG, CREATE_BY, CREATE_TIME, UPDATE_BY, UPDATE_TIME";
    vals += ", " + Db::lit("0") + ", " + cm::db::bind(userId) + ", " + cm::db::bind(ts) + ", " +
            cm::db::bind(userId) + ", " + cm::db::bind(ts);
    if (auto v = body.find("epsId"); v != body.end() && !v->is_null()) {
        cols += ", EPS_ID";
        vals += ", " + litJson(*v);
    } else {
        cols += ", EPS_ID";
        vals += ", " + cm::db::bind(cm::security::SecurityUtils::getEpsId());
    }
    // Java 的 <trim suffixOverrides=","> 会留下 “ID, ,  USER_ID” 之类的双逗号吗？
    // 不会：每个 <if> 自带尾逗号。上面拼法与之等价。
    if (execute("insert into sys_index_menu (" + cols + ") values (" + vals + ")") < 0) {
        return AjaxResult::error("操作失败");
    }
    return AjaxResult::success("操作成功！", Json(newId));
}

cm::core::domain::AjaxResult SysIndexMenuService::insertSysIndexMenu(const std::string& menuIds) {
    const long long userId = cm::security::SecurityUtils::getUserId();
    const std::string ts = nowDb();
    std::string ids = menuIds;
    if (!ids.empty() && ids.back() == ',') ids.pop_back();
    if (StringUtils::isNotBlank(ids)) {
        for (const auto& token : StringUtils::split(ids, ',')) {
            if (token.empty()) continue;
            const std::string menuId = token;
            // deleteByMenuUserId：物理删除同 (menu_id,user_id) 的旧记录
            execute("delete from sys_index_menu where menu_id = " + cm::db::bind(menuId) +
                    " and user_id = " + cm::db::bind(userId));
            execute("insert into sys_index_menu (USER_ID, MENU_ID, DEL_FLAG, EPS_ID, CREATE_BY,"
                    " CREATE_TIME, UPDATE_BY, UPDATE_TIME) values (" + cm::db::bind(userId) + ", " +
                    cm::db::bind(menuId) + ", " + Db::lit("0") + ", " +
                    cm::db::bind(cm::security::SecurityUtils::getEpsId()) + ", " + cm::db::bind(userId) +
                    ", " + cm::db::bind(ts) + ", " + cm::db::bind(userId) + ", " + cm::db::bind(ts) + ")");
        }
    }
    return AjaxResult::success();
}

cm::core::domain::AjaxResult SysIndexMenuService::deleteSysIndexMenuByIds(
    const std::vector<long long>& ids) {
    if (ids.empty()) return AjaxResult::success(0);
    std::string in;
    for (long long id : ids) {
        if (!in.empty()) in += ", ";
        in += cm::db::bind(id);
    }
    const int count = execute("update sys_index_menu set del_flag = '1' where ID in (" + in + ")");
    return AjaxResult::success(count < 0 ? 0 : count);
}

} // namespace cm::system::service

// ------------------------------------------------------------------ 控制器

namespace cm::web {

using cm::core::domain::AjaxResult;
using cm::utils::StringUtils;
using cm::system::service::IndexMenuQuery;
using cm::system::service::SysIndexMenuService;

void registerSysIndexMenuController(Router& r) {
    // GET /system/indexmenu/list
    r.get("/system/indexmenu/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        IndexMenuQuery q;
        q.userId = cm::security::SecurityUtils::getUserId();
        if (auto v = ctx.optParam("menuName")) q.menuName = v;
        if (auto v = ctx.optParam("menuName2")) q.menuName2 = v;
        // Java: startPage() + selectSysIndexMenuList + getDataTable
        auto [rows, total] = SysIndexMenuService::selectSysIndexMenuListPage(q, ctx.pageRequest());
        return BaseController::ok(BaseController::dataTable(rows, total));
    });

    // GET /system/indexmenu/mylist
    r.get("/system/indexmenu/mylist", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(SysIndexMenuService::getListJson(
            cm::security::SecurityUtils::getUserId())));
    });

    // GET /system/indexmenu/export
    r.get("/system/indexmenu/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        IndexMenuQuery q;
        q.userId = cm::security::SecurityUtils::getUserId();
        if (auto v = ctx.optParam("menuName")) q.menuName = v;
        (void)SysIndexMenuService::selectSysIndexMenuListJson(q);
        return BaseController::ok(AjaxResult::success(
            "操作成功", Json(cm::utils::simpleUuid() + ".xlsx")));
    }).permi("system:indexmenu:export");

    // GET /system/indexmenu/{id}
    r.get("/system/indexmenu/{id}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(SysIndexMenuService::selectSysIndexMenuByIdJson(
            ctx.pathVarLong("id"))));
    }).permi("system:indexmenu:query");

    // POST /system/indexmenu —— 参数是逗号分隔的 menuIds
    r.post("/system/indexmenu", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string menuIds;
        if (auto v = ctx.optParam("menuIds")) menuIds = *v;
        else if (ctx.body().is_object() && ctx.body().contains("menuIds")) {
            menuIds = ctx.body()["menuIds"].is_string() ? ctx.body()["menuIds"].get<std::string>()
                                                        : ctx.body()["menuIds"].dump();
        }
        return BaseController::ok(SysIndexMenuService::insertSysIndexMenu(menuIds));
    });

    // PUT /system/indexmenu
    r.put("/system/indexmenu", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(SysIndexMenuService::saveSysIndexMenu(ctx.body()));
    }).permi("system:indexmenu:edit");

    // DELETE /system/indexmenu/{ids}
    r.del("/system/indexmenu/{ids}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::vector<long long> ids;
        for (const auto& p : StringUtils::split(ctx.pathVar("ids"), ',')) {
            if (!p.empty()) ids.push_back(std::stoll(p));
        }
        return BaseController::ok(SysIndexMenuService::deleteSysIndexMenuByIds(ids));
    });
}

} // namespace cm::web
