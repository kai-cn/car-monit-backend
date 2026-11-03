// 对应 Java: com.ruoyi.web.controller.system.SysUserController
#include "cm/web/controller/system/SysAuthControllers.hpp"

#include <string>
#include <utility>
#include <vector>

#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/core/domain/entity/SysRole.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysPostService.hpp"
#include "cm/system/service/SysRoleService.hpp"
#include "cm/system/service/SysUserService.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/util/CommonUtil.hpp"

namespace cm::web {
namespace {

using cm::constant::UserConstants;
using cm::core::domain::AjaxResult;
using cm::system::service::SysPostService;
using cm::system::service::SysRoleService;
using cm::system::service::SysUserService;
using cm::utils::StringUtils;

constexpr const char* PASSWORD_POLICY_MSG =
    "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号";

std::optional<long long> asLong(const std::optional<std::string>& v) {
    if (!v || v->empty()) return std::nullopt;  // Spring 把空串绑成 null
    try {
        return std::stoll(*v);
    } catch (...) {
        throw cm::exception::MethodArgumentTypeMismatchException("userId", "java.lang.Long", *v);
    }
}

/** 对应 Spring 把 query 参数绑定到 SysUser（只绑 XML 里真正参与过滤的列） */
cm::domain::SysUser bindUserQuery(RequestContext& ctx) {
    cm::domain::SysUser u;
    u.userId = asLong(ctx.optParam("userId"));
    u.deptId = asLong(ctx.optParam("deptId"));
    u.tenantId = asLong(ctx.optParam("tenantId"));
    u.excludeId = asLong(ctx.optParam("excludeId"));
    for (auto& pair : std::vector<std::pair<const char*, std::optional<std::string>*>>{
             {"userName", &u.userName},           {"nickName", &u.nickName},
             {"queryNickName", &u.queryNickName}, {"phonenumber", &u.phonenumber},
             {"status", &u.status},               {"userType", &u.userType},
             {"deptName", &u.deptName},            {"roleCode", &u.roleCode},
             {"certId", &u.certId},                {"certEntityId", &u.certEntityId},
             {"dataId", &u.dataId},                {"flag", &u.flag},
             {"bussId", &u.bussId},                {"userName", &u.userName},
         }) {
        if (auto v = ctx.optParam(pair.first)) *pair.second = *v;
    }
    if (auto es = ctx.optParam("excludeSelf")) u.excludeSelf = (*es == "true" || *es == "1");
    return u;
}

Json userArray(const std::vector<cm::domain::SysUser>& users) {
    Json arr = Json::array();
    for (const auto& u : users) arr.push_back(u.toJson());
    return arr;
}

Json idJsonArray(const std::vector<long long>& ids) {
    Json arr = Json::array();
    for (long long v : ids) arr.push_back(v);
    return arr;
}

std::vector<long long> parseIds(const std::string& text) {
    std::vector<long long> ids;
    for (const auto& p : StringUtils::split(text, ',')) {
        if (!p.empty()) ids.push_back(std::stoll(p));
    }
    return ids;
}


} // namespace

void registerSysUserController(Router& r) {
    using cm::security::SecurityUtils;

    // 这 6 个列表接口在 Java 侧都没有 @PreAuthorize，靠全局 authenticated 兜底
    struct ListPreset {
        const char* path;
        std::function<void(cm::domain::SysUser&)> tweak;
    };
    const std::vector<ListPreset> presets = {
        // GET /system/user/list —— Java: user.setUserType("1")
        {"/list", [](cm::domain::SysUser& u) { u.userType = "1"; }},
        // GET /system/user/listAll —— Java: 强制本租户
        {"/listAll", [](cm::domain::SysUser& u) { u.tenantId = SecurityUtils::getTenantId(); }},
        // GET /system/user/listTenantIdAll —— 未传 tenantId 时故意查不到（tenantId = -1）
        {"/listTenantIdAll", [](cm::domain::SysUser& u) {
             if (!u.tenantId) u.tenantId = -1LL;
         }},
        // GET /system/user/listutil —— 按 flag 切换数据范围（本 fork 特有）
        {"/listutil", [](cm::domain::SysUser& u) {
             const std::string flag = u.flag ? StringUtils::trim(*u.flag) : std::string();
             if (flag == "myDept" || flag == "myDeptCg") {
                 u.status = "0";
                 u.userType = "1";
                 u.tenantId = SecurityUtils::getTenantId();
             } else if (flag == "sjzbDept" || flag == "sjzbDeptCg") {
                 u.dataId = std::to_string(SecurityUtils::getTenantId());
             } else if (flag == "allDept") {
                 // 不加条件
             } else {
                 u.userId = -1LL;
             }
         }},
        // GET /system/user/listSameUtil —— 本租户本部门的启用用户
        {"/listSameUtil", [](cm::domain::SysUser& u) {
             u.status = "0";
             u.userType = "1";
             u.tenantId = SecurityUtils::getTenantId();
             u.deptId = SecurityUtils::getEpsId();
         }},
        // GET /system/user/listMy
        {"/listMy", [](cm::domain::SysUser& u) { u.userId = SecurityUtils::getUserId(); }},
    };
    for (const auto& preset : presets) {
        const auto tweak = preset.tweak;
        r.get(std::string("/system/user") + preset.path,
              [tweak](RequestContext& ctx) -> cm::http::ApiResponse {
                  cm::domain::SysUser query = bindUserQuery(ctx);
                  tweak(query);
                  auto [users, total] =
                      SysUserService::selectUserEntityPage(query, ctx.pageRequest());
                  return BaseController::ok(BaseController::dataTable(userArray(users), total));
              });
    }

    // GET /system/user/list/dept —— 本部门用户，并把部门名回填到 deptName
    r.get("/system/user/list/dept", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user = bindUserQuery(ctx);
        const long long epsId = SecurityUtils::getEpsId();
        user.deptId = epsId;  // Java: if (epsId != null) —— 基本类型永远非 null
        if (user.excludeSelf.value_or(false)) user.excludeId = SecurityUtils::getUserId();
        user.userType = "1";
        auto [users, total] = SysUserService::selectUserEntityPage(user, ctx.pageRequest());
        for (auto& u : users) {
            if (u.dept && !StringUtils::isBlank(u.dept->deptName)) u.deptName = u.dept->deptName;
        }
        return BaseController::ok(BaseController::dataTable(userArray(users), total));
    });

    // GET /system/user/export
    r.get("/system/user/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto list = SysUserService::selectUserList(bindUserQuery(ctx));
        (void)list;
        // ⚠️ Java 用 POI 产出 .xlsx；这里返回同样的响应形态（data = 文件名）
        return BaseController::ok(AjaxResult::success(
            "操作成功", Json(cm::utils::simpleUuid() + ".xlsx")));
    }).permi("system:user:export");

    // POST /system/user/importData、GET /system/user/importTemplate
    // ❌ 需要 Apache POI 的 xlsx 解析/模板生成，C++ 侧未实现。
    //     按“未完成的接口不会静默返回假数据”的原则显式报错，不伪装成功。
    r.post("/system/user/importData", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(
            AjaxResult::error("导入功能依赖 Excel 解析（Java: ExcelUtil.importExcel），C++ 侧尚未实现"));
    }).permi("system:user:import");
    r.get("/system/user/importTemplate", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(
            AjaxResult::error("导入模板生成依赖 Excel（Java: ExcelUtil.importTemplateExcel），C++ 侧尚未实现"));
    });

    // GET /system/user 与 GET /system/user/{userId}
    // Java 用 @GetMapping(value = {"/", "/{userId}"}) 一个方法映射两个路径
    auto getInfo = [](RequestContext& ctx) -> cm::http::ApiResponse {
        AjaxResult ajax = AjaxResult::success();
        auto roles = SysRoleService::selectRoleAll();
        const auto userId = asLong(ctx.optParam("userId"));
        Json roleArr = Json::array();
        // Java: 非管理员要过滤掉 admin 角色
        const bool admin = cm::domain::SysUser::isAdmin(userId);
        for (const auto& role : roles) {
            if (!admin && role.isAdmin()) continue;
            roleArr.push_back(role.toJson());
        }
        ajax.put("roles", roleArr);
        auto posts = SysPostService::selectPostAll();
        Json postArr = Json::array();
        for (const auto& p : posts) postArr.push_back(p.toJson());
        ajax.put("posts", postArr);
        if (userId) {
            auto user = SysUserService::selectUserById(*userId);
            ajax.put(AjaxResult::DATA_TAG, user ? user->toJson() : Json(nullptr));
            ajax.put("postIds", idJsonArray(SysPostService::selectPostListByUserId(*userId)));
            ajax.put("roleIds", idJsonArray(SysRoleService::selectRoleListByUserId(*userId)));
        }
        return BaseController::ok(ajax);
    };
    r.get("/system/user", getInfo).permi("system:user:query");
    r.get("/system/user/{userId}",
          [getInfo](RequestContext& ctx) -> cm::http::ApiResponse {
              // Spring 把路径变量也放进参数表，getInfo 统一按 userId 取
              return getInfo(ctx);
          })
        .permi("system:user:query");

    // POST /system/user
    r.post("/system/user", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user;
        user.fromJson(ctx.body());
        if (UserConstants::NOT_UNIQUE_OLD ==
            SysUserService::checkUserNameUnique(user.userName.value_or(""))) {
            return BaseController::ok(AjaxResult::error(
                "新增用户'" + user.userName.value_or("") + "'失败，登录账号已存在"));
        }
        if (StringUtils::isNotBlank(user.phonenumber) &&
            UserConstants::NOT_UNIQUE_OLD == SysUserService::checkPhoneUnique(user)) {
            return BaseController::ok(AjaxResult::error(
                "新增用户'" + user.userName.value_or("") + "'失败，手机号码已存在"));
        }
        if (StringUtils::isNotBlank(user.email) &&
            UserConstants::NOT_UNIQUE_OLD == SysUserService::checkEmailUnique(user)) {
            return BaseController::ok(AjaxResult::error(
                "新增用户'" + user.userName.value_or("") + "'失败，邮箱账号已存在"));
        }
        // Java: CommonUtil.checkPassword(null) 会在 matches 上抛 NPE
        if (!user.password) throw cm::exception::NullPointerException();
        if (cm::web::util::CommonUtil::checkPassword(*user.password)) {
            return BaseController::ok(AjaxResult::error(PASSWORD_POLICY_MSG));
        }
        user.createBy = SecurityUtils::getUsername();
        user.password = SecurityUtils::encryptPassword(*user.password);
        return BaseController::ok(BaseController::toAjax(SysUserService::insertUser(user) ? 1 : 0));
    }).permi("system:user:add");

    // PUT /system/user
    r.put("/system/user", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user;
        user.fromJson(ctx.body());
        SysUserService::checkUserAllowed(user);
        if (StringUtils::isNotBlank(user.phonenumber) &&
            UserConstants::NOT_UNIQUE_OLD == SysUserService::checkPhoneUnique(user)) {
            return BaseController::ok(AjaxResult::error(
                "修改用户'" + user.userName.value_or("") + "'失败，手机号码已存在"));
        }
        if (StringUtils::isNotBlank(user.email) &&
            UserConstants::NOT_UNIQUE_OLD == SysUserService::checkEmailUnique(user)) {
            return BaseController::ok(AjaxResult::error(
                "修改用户'" + user.userName.value_or("") + "'失败，邮箱账号已存在"));
        }
        user.updateBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysUserService::updateUser(user)));
    }).permi("system:user:edit");

    // DELETE /system/user/{userIds}
    r.del("/system/user/{userIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(
            BaseController::toAjax(SysUserService::deleteUserByIds(parseIds(ctx.pathVar("userIds")))));
    }).permi("system:user:remove");

    // PUT /system/user/resetPwd
    r.put("/system/user/resetPwd", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user;
        user.fromJson(ctx.body());
        const std::string password = user.password.value_or("");
        if (cm::web::util::CommonUtil::checkPassword(password)) {
            return BaseController::ok(AjaxResult::error(PASSWORD_POLICY_MSG));
        }
        SysUserService::checkUserAllowed(user);
        user.password = SecurityUtils::encryptPassword(password);
        user.updateBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysUserService::resetPwd(user)));
    }).permi("system:user:resetPwd");

    // PUT /system/user/changeStatus
    r.put("/system/user/changeStatus", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user;
        user.fromJson(ctx.body());
        SysUserService::checkUserAllowed(user);
        user.updateBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysUserService::updateUserStatus(user)));
    }).permi("system:user:edit");

    // PUT /system/user/bindUky —— 绑定 UKey（唯一实体标识 + 序列号）
    r.put("/system/user/bindUky", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user;
        user.fromJson(ctx.body());
        if (!user.userId) user.userId = SecurityUtils::getUserId();
        if (StringUtils::isBlank(user.certEntityId)) {
            return BaseController::ok(AjaxResult::error("唯一实体标识不能为空"));
        }
        if (StringUtils::isBlank(user.certId)) {
            return BaseController::ok(AjaxResult::error("密码卡/USD-Key序列号不能为空"));
        }
        // 已被别人绑定则拒绝（Java 用 userList.get(0).getUserId().equals(user.getUserId())）
        auto boundCheck = [&](const std::optional<std::string>& certEntityId,
                              const std::optional<std::string>& certId,
                              const char* msg) -> std::optional<cm::http::ApiResponse> {
            cm::domain::SysUser query;
            query.certEntityId = certEntityId;
            query.certId = certId;
            auto list = SysUserService::selectUserList(query);
            if (!list.empty() && list.front().userId != user.userId) {
                return BaseController::ok(AjaxResult::error(msg));
            }
            return std::nullopt;
        };
        if (auto bad = boundCheck(user.certEntityId, std::nullopt, "唯一实体标识已绑定，请确认！"))
            return *bad;
        if (auto bad = boundCheck(std::nullopt, user.certId, "密码卡/USD-Key序列号已绑定，请确认！"))
            return *bad;
        cm::domain::SysUser upd;
        upd.userId = user.userId;
        upd.certId = user.certId;
        upd.certEntityId = user.certEntityId;
        upd.updateBy = SecurityUtils::getUsername();
        // Java 复用 updateUserStatus 做局部更新（方法名有误导性，这里保持同名行为）
        return BaseController::ok(BaseController::toAjax(SysUserService::updateUserStatus(upd)));
    });

    // GET /system/user/getroleUser/{roleCode}
    r.get("/system/user/getroleUser/{roleCode}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user;
        user.roleCode = ctx.pathVar("roleCode");
        user.tenantId = SecurityUtils::getTenantId();
        return BaseController::ok(AjaxResult::success(userArray(SysUserService::selectUserList(user))));
    });

    // GET /system/user/currentUser
    r.get("/system/user/currentUser", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(SysUserService::selectCurrentUser().toJson()));
    });
}

} // namespace cm::web
