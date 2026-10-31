// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysLoginService.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/UserDetailsServiceImpl.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysPermissionService.java
// 职责: 登录主流程（验证码 -> 用户状态 -> BCrypt -> 权限 -> 令牌）。
// 对应关系: login(...) -> login(...)；UserDetailsServiceImpl -> load_user。

use crate::auth::audit::record_logininfor;
use crate::auth::password;
use crate::auth::token_service::TokenService;
use crate::common::constants::{ALL_PERMISSION, CAPTCHA_CODE_KEY, LOGIN_FAIL, LOGIN_SUCCESS};
use crate::common::utils::{is_not_blank, ClientMeta};
use crate::domain::{LoginBody, LoginUser};
use crate::error::AppError;
use crate::repository::user_repo;
use crate::state::AppState;

/// i18n: user.jcaptcha.expire
pub const MSG_CAPTCHA_EXPIRE: &str = "验证码已失效";
/// i18n: user.jcaptcha.error
pub const MSG_CAPTCHA_ERROR: &str = "验证码错误";
/// i18n: user.password.not.match（DaoAuthenticationProvider 会隐藏“用户不存在”）
pub const MSG_PASSWORD_NOT_MATCH: &str = "用户不存在/密码错误";
/// i18n: user.login.success
pub const MSG_LOGIN_SUCCESS: &str = "登录成功";

/// Java: SysLoginService.login(username, password, code, uuid)
pub async fn login(
    state: &AppState,
    body: &LoginBody,
    meta: &ClientMeta,
) -> Result<String, AppError> {
    let username = body.username();
    let code = body.code();

    // if (CommonUtil.isNotBlank(code)) { 校验验证码 }
    if is_not_blank(&code) {
        let verify_key = format!("{CAPTCHA_CODE_KEY}{}", body.uuid);
        let captcha: Option<String> = state.redis.get_object(&verify_key).await?;
        state.redis.delete_object(&verify_key).await?;

        match captcha {
            None => {
                record_logininfor(&state.db, &username, LOGIN_FAIL, MSG_CAPTCHA_EXPIRE, meta);
                return Err(AppError::Service(MSG_CAPTCHA_EXPIRE.to_string()));
            }
            Some(expected) if !code.eq_ignore_ascii_case(&expected) => {
                record_logininfor(&state.db, &username, LOGIN_FAIL, MSG_CAPTCHA_ERROR, meta);
                return Err(AppError::Service(MSG_CAPTCHA_ERROR.to_string()));
            }
            Some(_) => {}
        }
    }

    // UserDetailsServiceImpl.loadUserByUsername
    let user = user_repo::select_user_by_user_name(&state.db, &username).await?;
    let Some(user) = user else {
        // DaoAuthenticationProvider.hideUserNotFoundExceptions = true
        record_logininfor(
            &state.db,
            &username,
            LOGIN_FAIL,
            MSG_PASSWORD_NOT_MATCH,
            meta,
        );
        return Err(AppError::Service(MSG_PASSWORD_NOT_MATCH.to_string()));
    };

    if user.del_flag.as_deref() == Some("2") {
        let msg = format!("对不起，您的账号：{username} 已被删除");
        record_logininfor(&state.db, &username, LOGIN_FAIL, &msg, meta);
        return Err(AppError::Service(msg));
    }
    if user.status.as_deref() == Some("1") {
        let msg = format!("对不起，您的账号：{username} 已停用");
        record_logininfor(&state.db, &username, LOGIN_FAIL, &msg, meta);
        return Err(AppError::Service(msg));
    }

    let encoded = user.password.clone().unwrap_or_default();
    if !password::matches(&body.password(), &encoded) {
        record_logininfor(
            &state.db,
            &username,
            LOGIN_FAIL,
            MSG_PASSWORD_NOT_MATCH,
            meta,
        );
        return Err(AppError::Service(MSG_PASSWORD_NOT_MATCH.to_string()));
    }

    // SysPermissionService.getMenuPermission
    let permissions = if user.is_admin() {
        vec![ALL_PERMISSION.to_string()]
    } else {
        match user.user_id {
            Some(user_id) => user_repo::select_menu_perms_for_user(&state.db, user_id).await?,
            None => Vec::new(),
        }
    };

    let login_user = LoginUser::new(user, permissions);
    let token = TokenService::create_token(state, login_user, meta).await?;
    record_logininfor(&state.db, &username, LOGIN_SUCCESS, MSG_LOGIN_SUCCESS, meta);
    Ok(token)
}
