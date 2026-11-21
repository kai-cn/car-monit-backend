// 对应 Java: com.ruoyi.web.controller.system.SysDeptController
#include "cm/web/controller/system/SysAuthControllers.hpp"

#include <string>
#include <vector>

#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysDeptService.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::constant::UserConstants;
using cm::core::domain::AjaxResult;
using cm::security::SecurityUtils;
using cm::system::service::SysDeptService;
using cm::utils::StringUtils;

// 本 fork 的常量：SysDeptController.UNIT_FLAG = "1"
constexpr const char* UNIT_FLAG = "1";

std::optional<long long> paramAsLong(RequestContext& ctx, const char* name) {
    auto v = ctx.optParam(name);
    if (!v || v->empty()) return std::nullopt;  // Spring 把空串绑定成 null
    try {
        return std::stoll(*v);
    } catch (...) {
        // Java 侧类型绑定失败抛 MethodArgumentTypeMismatchException，消息形态保持一致
        throw cm::exception::MethodArgumentTypeMismatchException(name, "java.lang.Long", *v);
    }
}

/** 对应 Spring 把 query 参数绑定到 SysDept */
cm::domain::SysDept bindDeptQuery(RequestContext& ctx) {
    cm::domain::SysDept d;
    d.parentId = paramAsLong(ctx, "parentId");
    d.deptId = paramAsLong(ctx, "deptId");
    d.treeLeavel = paramAsLong(ctx, "treeLeavel");
    d.tenantId = paramAsLong(ctx, "tenantId");
    d.leaderId = paramAsLong(ctx, "leaderId");
    d.fgldId = paramAsLong(ctx, "fgldId");
    for (auto& pair : std::vector<std::pair<const char*, std::optional<std::string>*>>{
             {"deptName", &d.deptName},     {"status", &d.status},
             {"isZbzg", &d.isZbzg},         {"isUint", &d.isUint},
             {"subCode", &d.subCode},       {"deptJc", &d.deptJc},
             {"leader", &d.leader},         {"fgldName", &d.fgldName},
             {"deptSubCode", &d.deptSubCode}, {"flag", &d.flag},
             {"dataId", &d.dataId},         {"ancestors", &d.ancestors},
         }) {
        if (auto v = ctx.optParam(pair.first)) *pair.second = *v;
    }
    return d;
}

Json deptArray(const std::vector<cm::domain::SysDept>& depts) {
    Json arr = Json::array();
    for (const auto& d : depts) arr.push_back(d.toJson());
    return arr;
}

Json idArray(const std::vector<long long>& ids) {
    Json arr = Json::array();
    for (long long v : ids) arr.push_back(v);
    return arr;
}

/** CommonUtil.isNull(obj)：null -> ""，否则 toString().trim() */
std::string commonUtilIsNull(const std::optional<std::string>& v) {
    if (!v) return "";
    return StringUtils::trim(*v);
}

} // namespace

void registerSysDeptController(Router& r) {
    // GET /system/dept/list
    r.get("/system/dept/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto depts = SysDeptService::selectDeptList(bindDeptQuery(ctx));
        return BaseController::ok(AjaxResult::success(deptArray(depts)));
    }).permi("system:dept:list");

    // GET /system/dept/getList —— Java 侧没有 @PreAuthorize
    r.get("/system/dept/getList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto depts = SysDeptService::selectDeptList(bindDeptQuery(ctx));
        return BaseController::ok(AjaxResult::success(deptArray(depts)));
    });

    // GET /system/dept/list/exclude/{deptId}
    // Java 用 Iterator 就地剔除：本部门 + 祖级列表里包含该部门的节点
    r.get("/system/dept/list/exclude/{deptId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const long long deptId = ctx.pathVarLong("deptId");
        auto depts = SysDeptService::selectDeptList(cm::domain::SysDept{});
        std::vector<cm::domain::SysDept> kept;
        for (const auto& d : depts) {
            const bool self = d.deptId && *d.deptId == deptId;
            // StringUtils.split(ancestors, ",") 里是否含 deptId 的字符串形式
            bool inAncestors = false;
            if (d.ancestors) {
                for (const auto& token : StringUtils::split(*d.ancestors, ',')) {
                    if (token == std::to_string(deptId)) {
                        inAncestors = true;
                        break;
                    }
                }
            }
            if (!self && !inAncestors) kept.push_back(d);
        }
        return BaseController::ok(AjaxResult::success(deptArray(kept)));
    }).permi("system:dept:list");

    // GET /system/dept/{deptId}
    r.get("/system/dept/{deptId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto dept = SysDeptService::selectDeptById(ctx.pathVarLong("deptId"));
        return BaseController::ok(AjaxResult::success(dept ? dept->toJson() : Json(nullptr)));
    }).permi("system:dept:query");

    // GET /system/dept/treeselect
    r.get("/system/dept/treeselect", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto depts = SysDeptService::selectDeptList(bindDeptQuery(ctx));
        return BaseController::ok(AjaxResult::success(SysDeptService::buildDeptTreeSelect(depts)));
    });

    // GET /system/dept/treeselectNew —— 本 fork 特有的按 flag 切换数据范围
    r.get("/system/dept/treeselectNew", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysDept dept = bindDeptQuery(ctx);
        const std::string flag = commonUtilIsNull(dept.flag);
        if (flag == "myDept" || flag == "myDeptCg") {
            dept.tenantId = SecurityUtils::getTenantId();
        } else if (flag == "sjzbDept" || flag == "sjzbDeptCg") {
            dept.dataId = std::to_string(SecurityUtils::getTenantId());
        } else if (flag == "isUint") {
            dept.isUint = UNIT_FLAG;
        } else if (flag == "allDept") {
            // 不加条件
        } else if (flag == "onlyMyDept") {
            dept.deptId = SecurityUtils::getEpsId();
        } else {
            dept.deptId = -1LL;  // Java: dept.setDeptId(-1l) —— 兜底查不到任何部门
        }
        auto depts = SysDeptService::selectDeptList(dept);
        return BaseController::ok(AjaxResult::success(SysDeptService::buildDeptTreeSelect(depts)));
    });

    // GET /system/dept/roleDeptTreeselect/{roleId}
    r.get("/system/dept/roleDeptTreeselect/{roleId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const long long roleId = ctx.pathVarLong("roleId");
        auto depts = SysDeptService::selectDeptList(cm::domain::SysDept{});
        AjaxResult ajax = AjaxResult::success();
        ajax.put("checkedKeys", idArray(SysDeptService::selectDeptListByRoleId(roleId)));
        ajax.put("depts", SysDeptService::buildDeptTreeSelect(depts));
        return BaseController::ok(ajax);
    });

    // POST /system/dept
    r.post("/system/dept", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysDept dept;
        dept.fromJson(ctx.body());
        if (UserConstants::NOT_UNIQUE_OLD == SysDeptService::checkDeptNameUnique(dept)) {
            return BaseController::ok(
                AjaxResult::error("新增部门'" + dept.deptName.value_or("") + "'失败，部门名称已存在"));
        }
        dept.createBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysDeptService::insertDept(dept)));
    }).permi("system:dept:add");

    // PUT /system/dept
    r.put("/system/dept", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysDept dept;
        dept.fromJson(ctx.body());
        if (UserConstants::NOT_UNIQUE_OLD == SysDeptService::checkDeptNameUnique(dept)) {
            return BaseController::ok(
                AjaxResult::error("修改部门'" + dept.deptName.value_or("") + "'失败，部门名称已存在"));
        }
        // Java: dept.getParentId().equals(dept.getDeptId()) —— parentId 为 null 时 NPE
        if (!dept.parentId) throw cm::exception::NullPointerException();
        if (dept.parentId == dept.deptId) {
            return BaseController::ok(
                AjaxResult::error("修改部门'" + dept.deptName.value_or("") + "'失败，上级部门不能是自己"));
        }
        if (StringUtils::equals(UserConstants::DEPT_DISABLE, dept.status.value_or("")) &&
            SysDeptService::selectNormalChildrenDeptById(dept.deptId.value_or(-1)) > 0) {
            return BaseController::ok(AjaxResult::error("该部门包含未停用的子部门！"));
        }
        dept.updateBy = SecurityUtils::getUsername();
        return BaseController::ok(BaseController::toAjax(SysDeptService::updateDept(dept)));
    }).permi("system:dept:edit");

    // DELETE /system/dept/{deptId}
    r.del("/system/dept/{deptId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const long long deptId = ctx.pathVarLong("deptId");
        if (SysDeptService::hasChildByDeptId(deptId)) {
            return BaseController::ok(AjaxResult::error("存在下级部门,不允许删除"));
        }
        if (SysDeptService::checkDeptExistUser(deptId)) {
            return BaseController::ok(AjaxResult::error("部门存在用户,不允许删除"));
        }
        return BaseController::ok(BaseController::toAjax(SysDeptService::deleteDeptById(deptId)));
    }).permi("system:dept:remove");

    // GET /system/dept/getCompanyList —— 只取单位节点（is_uint = '1'）
    r.get("/system/dept/getCompanyList", [](RequestContext&) -> cm::http::ApiResponse {
        cm::domain::SysDept query;
        query.isUint = UNIT_FLAG;
        auto list = SysDeptService::selectDeptList(query);
        return BaseController::ok(AjaxResult::success(deptArray(list)));
    });
}

} // namespace cm::web
