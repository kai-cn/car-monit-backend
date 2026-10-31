// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/TokenService.java
// 职责: 登录令牌生命周期（创建/读取/续期/删除），Redis key 与 Java 完全一致。
// 对应关系: createToken/getLoginUser/verifyToken/refreshToken/delLoginUser。

use std::time::Duration;

use axum::http::HeaderMap;

use crate::common::constants::{LOGIN_TOKEN_KEY, TOKEN_PREFIX};
use crate::common::utils::ClientMeta;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::state::AppState;

/// Java: TokenService.MILLIS_MINUTE_TEN —— 剩余不足 20 分钟即续期。
const REFRESH_THRESHOLD_MILLIS: i64 = 20 * 60 * 1000;
const MILLIS_MINUTE: i64 = 60 * 1000;

pub struct TokenService;

impl TokenService {
    /// Java: TokenService.createToken(LoginUser)
    pub async fn create_token(
        state: &AppState,
        login_user: LoginUser,
        meta: &ClientMeta,
    ) -> Result<String, AppError> {
        let token = crate::common::utils::fast_uuid();
        let mut login_user = login_user;
        login_user.token = token.clone();
        // Java: request.getSession().getId()（无状态链仍会创建 session）
        login_user.session_id = Some(uuid::Uuid::new_v4().to_string());
        login_user.ipaddr = Some(meta.ip.clone());
        login_user.login_location = Some(meta.login_location.clone());
        login_user.browser = Some(meta.browser.clone());
        login_user.os = Some(meta.os.clone());
        login_user.username = Some(login_user.user.username());

        Self::refresh(state, &mut login_user).await?;
        state.jwt.create_token(&token)
    }

    /// Java: TokenService.refreshToken(LoginUser)
    pub async fn refresh(state: &AppState, login_user: &mut LoginUser) -> Result<(), AppError> {
        let now = chrono::Utc::now().timestamp_millis();
        login_user.login_time = now;
        login_user.expire_time = now + state.settings.token.expire_time * MILLIS_MINUTE;

        let key = token_key(&login_user.token);
        let ttl = Duration::from_secs((state.settings.token.expire_time * 60).max(1) as u64);
        // FastJson2 WriteClassName：写入前补 @type。
        let stored = login_user.clone().for_redis();
        state.redis.set_object_ttl(&key, &stored, Some(ttl)).await
    }

    /// Java: TokenService.verifyToken(LoginUser)
    pub async fn verify_token(
        state: &AppState,
        login_user: &mut LoginUser,
    ) -> Result<(), AppError> {
        let now = chrono::Utc::now().timestamp_millis();
        if login_user.expire_time - now <= REFRESH_THRESHOLD_MILLIS {
            Self::refresh(state, login_user).await?;
        }
        Ok(())
    }

    /// Java: TokenService.getLoginUser(HttpServletRequest)
    /// Java 解析异常会抛到过滤器；Rust 中间件按“未认证”处理以便返回 401。
    pub async fn get_login_user(state: &AppState, headers: &HeaderMap) -> Option<LoginUser> {
        let token = Self::token_from_headers(headers, &state.settings.token.header)?;
        let uuid = state.jwt.parse_token(&token).ok()?;
        let key = format!("{LOGIN_TOKEN_KEY}{uuid}");
        state.redis.get_object::<LoginUser>(&key).await.ok()?
    }

    /// Java: TokenService.delLoginUser(String token)
    pub async fn del_login_user(state: &AppState, token: &str) -> Result<(), AppError> {
        if token.is_empty() {
            return Ok(());
        }
        state.redis.delete_object(&token_key(token)).await
    }

    /// Java: getToken(HttpServletRequest) —— token.replace("Bearer ", "")
    pub fn token_from_headers(headers: &HeaderMap, header: &str) -> Option<String> {
        let raw = headers.get(header)?.to_str().ok()?;
        if raw.is_empty() {
            return None;
        }
        Some(raw.replace(TOKEN_PREFIX, ""))
    }
}

fn token_key(uuid: &str) -> String {
    format!("{LOGIN_TOKEN_KEY}{uuid}")
}
