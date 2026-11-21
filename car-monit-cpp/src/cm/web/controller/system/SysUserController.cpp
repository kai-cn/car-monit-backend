// 对应 Java: com.ruoyi.web.controller.system.SysUserController
#include "cm/web/controller/system/SysAuthControllers.hpp"

#include <string>
#include <utility>
#include <vector>

#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/Excel.hpp"
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

/** SysUser 的 @Excel 元数据（列序 = 字段声明序，@Excel.sort 全部是默认值 1）
 *  type: "ALL" 两者都出；"IMPORT" 只进 importTemplate；"EXPORT" 只进导出 */
struct UserExcelField {
    const char* name;
    const char* field;
    const char* conv;   // readConverterExp，空串表示无
    int width;
    bool numeric;       // cellType = ColumnType.NUMERIC
    const char* type;
};

const std::vector<UserExcelField>& userExcelFields() {
    static const std::vector<UserExcelField> fields = {
        {"用户序号", "userId", "", 16, true, "ALL"},
        {"用户编码", "userNo", "", 16, true, "ALL"},
        {"部门编号", "deptId", "", 16, false, "IMPORT"},
        {"登录名称", "userName", "", 16, false, "ALL"},
        {"用户名称", "nickName", "", 16, false, "ALL"},
        {"用户类型", "userType", "1=机构用户2专家3供应商", 16, false, "ALL"},
        {"用户邮箱", "email", "", 16, false, "ALL"},
        {"手机号码", "phonenumber", "", 16, false, "ALL"},
        {"用户性别", "sex", "0=男,1=女,2=未知", 16, false, "ALL"},
        {"帐号状态", "status", "0=正常,1=停用", 16, false, "ALL"},
        {"最后登录IP", "loginIp", "", 16, false, "EXPORT"},
        {"最后登录时间", "loginDate", "", 30, false, "EXPORT"},
        {"证书Id", "certId", "", 16, false, "ALL"},
        {"证书实体Id", "certEntityId", "", 16, false, "ALL"},
        {"业务id", "bussId", "", 16, false, "ALL"},
        {"业务名称", "bussName", "", 16, false, "ALL"},
        {"单位名称", "epsName", "", 16, false, "ALL"},
        {"租户单位id", "tenantId", "", 16, false, "ALL"},
        {"租户单位名称", "tenantName", "", 16, false, "ALL"},
        {"角色编码", "roleCode", "", 16, false, "ALL"},
        {"部门名称", "dept.deptName", "", 16, false, "EXPORT"},
        {"部门负责人", "dept.leader", "", 16, false, "EXPORT"},
    };
    return fields;
}

/** 对应 ExcelUtil.convertByExp：先按 ',' 分段，段内按 '=' 取前两段；不命中返回原值。
 *  Java 的 split("=") 会丢掉尾部空串，所以 "a=" 这种会抛越界并被 catch 掉 -> 返回原值。 */
std::string convertByExp(const std::string& value, const std::string& exp) {
    size_t pos = 0;
    while (pos <= exp.size()) {
        const size_t comma = exp.find(',', pos);
        const std::string item = exp.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
        const size_t eq = item.find('=');
        if (eq != std::string::npos) {
            const size_t eq2 = item.find('=', eq + 1);
            const std::string mapped = item.substr(eq + 1, eq2 == std::string::npos ? std::string::npos : eq2 - eq - 1);
            if (item.substr(0, eq) == value && !mapped.empty()) return mapped;
        }
        if (comma == std::string::npos) break;
        pos = comma + 1;
    }
    return value;
}

bool userExcelTake(const UserExcelField& f, bool forExport) {
    const std::string t = f.type;
    if (t == "ALL") return true;
    return forExport ? t == "EXPORT" : t == "IMPORT";
}

/** 取实体值；null -> Json null（对应 Java "字段为 null 就留空格"） */
Json userExcelValue(const cm::domain::SysUser& u, const UserExcelField& f) {
    auto s = [](const std::optional<std::string>& v) { return v ? Json(*v) : Json(nullptr); };
    auto n = [](const std::optional<long long>& v) { return v ? Json(*v) : Json(nullptr); };
    // 非 NUMERIC 列 Java 走 cellType=STRING：Long 也写成文本
    auto t = [](const std::optional<long long>& v) {
        return v ? Json(std::to_string(*v)) : Json(nullptr);
    };
    const std::string k = f.field;
    if (k == "userId") return f.numeric ? n(u.userId) : t(u.userId);
    if (k == "userNo") return f.numeric ? n(u.userNo) : t(u.userNo);
    if (k == "deptId") return t(u.deptId);
    if (k == "tenantId") return t(u.tenantId);
    if (k == "userName") return s(u.userName);
    if (k == "nickName") return s(u.nickName);
    if (k == "userType") return s(u.userType);
    if (k == "email") return s(u.email);
    if (k == "phonenumber") return s(u.phonenumber);
    if (k == "sex") return s(u.sex);
    if (k == "status") return s(u.status);
    if (k == "loginIp") return s(u.loginIp);
    if (k == "loginDate")
        return u.loginDate ? Json(cm::utils::DateUtils::formatJsonDate(*u.loginDate)) : Json(nullptr);
    if (k == "certId") return s(u.certId);
    if (k == "certEntityId") return s(u.certEntityId);
    if (k == "bussId") return s(u.bussId);
    if (k == "bussName") return s(u.bussName);
    if (k == "epsName") return s(u.epsName);
    if (k == "tenantName") return s(u.tenantName);
    if (k == "roleCode") return s(u.roleCode);
    if (k == "dept.deptName") return u.dept ? s(u.dept->deptName) : Json(nullptr);
    if (k == "dept.leader") return u.dept ? s(u.dept->leader) : Json(nullptr);
    return Json(nullptr);
}

std::vector<cm::common::utils::ExcelColumn> userExcelColumns(bool forExport) {
    std::vector<cm::common::utils::ExcelColumn> cols;
    for (const auto& f : userExcelFields()) {
        if (!userExcelTake(f, forExport)) continue;
        cols.push_back({f.name, f.field, f.numeric, f.width});
    }
    return cols;
}

std::vector<Json> userExcelRows(const std::vector<cm::domain::SysUser>& list, bool forExport) {
    std::vector<Json> rows;
    for (const auto& u : list) {
        Json row = Json::object();
        for (const auto& f : userExcelFields()) {
            if (!userExcelTake(f, forExport)) continue;
            Json v = userExcelValue(u, f);
            if (*f.conv && v.is_string()) v = Json(convertByExp(v.get<std::string>(), f.conv));
            row[f.field] = std::move(v);
        }
        rows.push_back(std::move(row));
    }
    return rows;
}

/** 对应 ExcelUtil.exportExcel：落盘 + 返回 AjaxResult.success(filename)（msg 重载，没有 data） */
cm::http::ApiResponse exportUserExcel(const std::vector<cm::domain::SysUser>& list) {
    const std::string filename = cm::common::utils::Excel::encodingFilename("用户数据");
    cm::common::utils::Excel::writeDownloadFile(
        filename,
        cm::common::utils::Excel::exportXlsx(userExcelColumns(true), userExcelRows(list, true), "用户数据"));
    return cm::http::ApiResponse::json(AjaxResult::success(filename).toJson());
}

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

    // 这 6 个列表接口在 Java 侧都没有 @PreAuthorize，靠全局 authenticated 兜底，
    // 差异只在进入分页前的查询条件，所以共用一个 handler 工厂、逐个显式注册路径。
    auto userListHandler = [](std::function<void(cm::domain::SysUser&)> tweak) {
        return [tweak](RequestContext& ctx) -> cm::http::ApiResponse {
            cm::domain::SysUser query = bindUserQuery(ctx);
            tweak(query);
            auto [users, total] = SysUserService::selectUserEntityPage(query, ctx.pageRequest());
            return BaseController::ok(BaseController::dataTable(userArray(users), total));
        };
    };
    // GET /system/user/list —— Java: user.setUserType("1")
    r.get("/system/user/list", userListHandler([](cm::domain::SysUser& u) { u.userType = "1"; }));
    // GET /system/user/listAll —— Java: 强制本租户
    r.get("/system/user/listAll", userListHandler([](cm::domain::SysUser& u) {
        u.tenantId = SecurityUtils::getTenantId();
    }));
    // GET /system/user/listTenantIdAll —— 未传 tenantId 时故意查不到（tenantId = -1）
    r.get("/system/user/listTenantIdAll", userListHandler([](cm::domain::SysUser& u) {
        if (!u.tenantId) u.tenantId = -1LL;
    }));
    // GET /system/user/listutil —— 按 flag 切换数据范围（本 fork 特有）
    r.get("/system/user/listutil", userListHandler([](cm::domain::SysUser& u) {
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
    }));
    // GET /system/user/listSameUtil —— 本租户本部门的启用用户
    r.get("/system/user/listSameUtil", userListHandler([](cm::domain::SysUser& u) {
        u.status = "0";
        u.userType = "1";
        u.tenantId = SecurityUtils::getTenantId();
        u.deptId = SecurityUtils::getEpsId();
    }));
    // GET /system/user/listMy
    r.get("/system/user/listMy", userListHandler([](cm::domain::SysUser& u) {
        u.userId = SecurityUtils::getUserId();
    }));

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
        return exportUserExcel(SysUserService::selectUserList(bindUserQuery(ctx)));
    }).permi("system:user:export");

    // POST /system/user/importData
    // ❌ 需要读 xlsx（POI XSSF：sharedStrings + 表头反查 @Excel 名称），C++ 侧未实现。
    //     按“未完成的接口不会静默返回假数据”的原则显式报错，不伪装成功。
    r.post("/system/user/importData", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(
            AjaxResult::error("导入功能依赖 Excel 解析（Java: ExcelUtil.importExcel），C++ 侧尚未实现"));
    }).permi("system:user:import");
    r.get("/system/user/importTemplate", [](RequestContext&) -> cm::http::ApiResponse {
        // 对应 ExcelUtil.importTemplateExcel("用户数据")：Type.IMPORT 的列，只有表头那一行
        const std::string filename = cm::common::utils::Excel::encodingFilename("用户数据");
        cm::common::utils::Excel::writeDownloadFile(
            filename, cm::common::utils::Excel::exportXlsx(userExcelColumns(false), {}, "用户数据"));
        return cm::http::ApiResponse::json(AjaxResult::success(filename).toJson());
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
