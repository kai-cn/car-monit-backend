// 对应 Java: com.ruoyi.web.controller.system.SysProfileController
//            以及 com.ruoyi.web.controller.system.SysPostController#optionselect
//
// 两个控制器放在一个文件里，是因为 SysPost 的 6 个标准动作已由 CrudSpec 引擎生成，
// 这里只剩 optionselect 一个补充路由；独立成文件反而更难找。
#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/security/TokenService.hpp"
#include "cm/framework/web/FileUpload.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysPostService.hpp"
#include "cm/system/service/SysUserService.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/controller/system/SysAuthControllers.hpp"
#include "cm/web/util/CommonUtil.hpp"

namespace cm::web {
namespace {

using cm::constant::UserConstants;
using cm::core::domain::AjaxResult;
using cm::security::SecurityUtils;
using cm::security::TokenService;
using cm::system::service::SysPostService;
using cm::system::service::SysUserService;
using cm::utils::StringUtils;

Json postArray() {
    Json arr = Json::array();
    for (const auto& p : SysPostService::selectPostAll()) arr.push_back(p.toJson());
    return arr;
}

} // namespace

void registerSysProfileController(Router& r) {
    // GET /system/user/profile
    r.get("/system/user/profile", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto loginUser = TokenService::instance().getLoginUser(ctx.req);
        if (!loginUser) return BaseController::ok(AjaxResult::error("登录状态已过期"));
        AjaxResult ajax = AjaxResult::success(loginUser->user.toJson());
        ajax.put("roleGroup", SysUserService::selectUserRoleGroup(loginUser->user.userName.value_or("")));
        ajax.put("postGroup", SysUserService::selectUserPostGroup(loginUser->user.userName.value_or("")));
        return BaseController::ok(ajax);
    });

    // PUT /system/user/profile
    r.put("/system/user/profile", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysUser user;
        user.fromJson(ctx.body());
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
        if (SysUserService::updateUserProfile(user) <= 0) {
            return BaseController::ok(AjaxResult::error("修改个人信息异常，请联系管理员"));
        }
        auto loginUser = TokenService::instance().getLoginUser(ctx.req);
        if (loginUser) {
            loginUser->user.nickName = user.nickName;
            loginUser->user.phonenumber = user.phonenumber;
            loginUser->user.email = user.email;
            loginUser->user.sex = user.sex;
            TokenService::instance().setLoginUser(*loginUser);
        }
        return BaseController::ok(AjaxResult::success());
    });

    // PUT /system/user/profile/updatePwd —— Java 用 @RequestParam，即 query/form 参数
    r.put("/system/user/profile/updatePwd", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto loginUser = TokenService::instance().getLoginUser(ctx.req);
        if (!loginUser) return BaseController::ok(AjaxResult::error("登录状态已过期"));
        const std::string userName = loginUser->user.userName.value_or("");
        const std::string hashed = loginUser->user.password.value_or("");
        const std::string oldPassword = ctx.param("oldPassword");
        const std::string newPassword = ctx.param("newPassword");
        if (!SecurityUtils::matchesPassword(oldPassword, hashed)) {
            return BaseController::ok(AjaxResult::error("修改密码失败，旧密码错误"));
        }
        if (SecurityUtils::matchesPassword(newPassword, hashed)) {
            return BaseController::ok(AjaxResult::error("新密码不能与旧密码相同"));
        }
        if (cm::web::util::CommonUtil::checkPassword(newPassword)) {
            return BaseController::ok(AjaxResult::error(
                "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！"));
        }
        const std::string encrypted = SecurityUtils::encryptPassword(newPassword);
        if (SysUserService::resetUserPwd(userName, encrypted) > 0) {
            loginUser->user.password = encrypted;
            TokenService::instance().setLoginUser(*loginUser);
            return BaseController::ok(AjaxResult::success());
        }
        return BaseController::ok(AjaxResult::error("修改密码异常，请联系管理员"));
    });

    // POST /system/user/profile/avatar
    r.post("/system/user/profile/avatar", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto loginUser = TokenService::instance().getLoginUser(ctx.req);
        const cm::http::MultipartPart* file = nullptr;
        for (const auto& part : ctx.req.parts) {
            if (part.name == "avatarfile" && part.isFile()) {
                file = &part;
                break;
            }
        }
        if (file == nullptr || file->data.empty()) {
            return BaseController::ok(AjaxResult::error("上传图片异常，请联系管理员"));
        }
        auto& cfg = cm::config::AppConfig::instance();
        const std::string avatarDir = cfg.profile + "/avatar";
        const std::string avatar = cm::framework::web::FileUpload::upload(
            avatarDir, file->filename, file->content_type, file->data);
        if (avatar.empty() || !loginUser) {
            return BaseController::ok(AjaxResult::error("上传图片异常，请联系管理员"));
        }
        if (!SysUserService::updateUserAvatar(loginUser->user.userName.value_or(""), avatar)) {
            return BaseController::ok(AjaxResult::error("上传图片异常，请联系管理员"));
        }
        AjaxResult ajax = AjaxResult::success();
        ajax.put("imgUrl", avatar);
        loginUser->user.avatar = avatar;
        TokenService::instance().setLoginUser(*loginUser);
        return BaseController::ok(ajax);
    });
}

void registerSysPostExtraController(Router& r) {
    // GET /system/post/optionselect —— Java 侧没有 @PreAuthorize
    r.get("/system/post/optionselect", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(postArray()));
    });
}

} // namespace cm::web
