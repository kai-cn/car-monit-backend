// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/security/filter/JwtAuthenticationTokenFilter.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/security/handle/LogoutSuccessHandlerImpl.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/security/handle/AuthenticationEntryPointImpl.java
// 职责: 令牌解析 -> 续期 -> 路由放行/拒绝；/logout 在鉴权前处理。
// 对应关系: OncePerRequestFilter + FilterSecurityInterceptor + LogoutFilter。

use std::net::SocketAddr;

use axum::extract::{ConnectInfo, Request};
use axum::middleware::Next;
use axum::response::{IntoResponse, Response};

use crate::auth::audit::record_logininfor;
use crate::auth::security::{self, Access};
use crate::auth::token_service::TokenService;
use crate::common::constants::LOGOUT;
use crate::common::utils::client_meta;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

pub async fn auth_middleware(state: AppState, mut request: Request, next: Next) -> Response {
    let path = request.uri().path().to_string();
    // Request<Body> 不是 Sync，跨 await 只能持有克隆后的 headers。
    let headers = request.headers().clone();
    let addr = request
        .extensions()
        .get::<ConnectInfo<SocketAddr>>()
        .map(|info| info.0);

    // Java: LogoutFilter 位于授权之前，/logout 无论是否认证都返回成功。
    if path == "/logout" {
        return logout(&state, &headers, addr).await;
    }

    let method = request.method().clone();
    let login_user = TokenService::get_login_user(&state, &headers).await;
    let access = security::access(&method, &path);

    match access {
        Access::DenyAll => {
            if login_user.is_some() {
                // Java: denyAll 命中已认证用户 -> AccessDeniedHandlerImpl -> 403 错误页。
                return crate::error::forbidden_error_page(&path);
            }
            return AppError::unauthorized(&path).into_response();
        }
        Access::Anonymous if login_user.is_some() => {
            // Java: `anonymous()` 的规则只放行匿名请求，带 token 反而 403 错误页。
            return crate::error::forbidden_error_page(&path);
        }
        Access::Authenticated if login_user.is_none() => {
            return AppError::unauthorized(&path).into_response();
        }
        _ => {}
    }

    if let Some(mut user) = login_user {
        // Java: tokenService.verifyToken(loginUser) —— 剩余不足 20 分钟自动续期。
        if let Err(err) = TokenService::verify_token(&state, &mut user).await {
            return err.into_response();
        }
        request.extensions_mut().insert(user);
    }

    next.run(request).await
}

/// Java: LogoutSuccessHandlerImpl.onLogoutSuccess
async fn logout(
    state: &AppState,
    headers: &axum::http::HeaderMap,
    addr: Option<SocketAddr>,
) -> Response {
    let login_user = TokenService::get_login_user(state, headers).await;
    if let Some(login_user) = login_user {
        let username = login_user.username();
        let _ = TokenService::del_login_user(state, &login_user.token).await;

        let meta = client_meta(headers, addr, state.settings.ruoyi.address_enabled);
        record_logininfor(&state.db, &username, LOGOUT, "退出成功", &meta);
    }
    // i18n: user.logout.success
    AjaxResult::success_msg("退出成功").into_response()
}
