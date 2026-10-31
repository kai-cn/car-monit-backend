// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysUserOnlineController.java
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserOnlineServiceImpl.java
// 职责: 在线用户列表与强退。
// 对应关系: login_tokens:* 扫描 -> keys + get_object<LoginUser>。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::{json, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const TOKEN_PREFIX: &str = "login_tokens:";

static LOG_FORCE: LogSpec = LogSpec::new(
    "在线用户",
    BusinessType::Force,
    "com.ruoyi.web.controller.monitor.SysUserOnlineController.forceLogout()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/monitor/online/list",
            meta::get_route("/monitor/online/list", Some("monitor:online:list"), None, list),
        )
        .route(
            "/monitor/online/{tokenId}",
            meta::delete_route(
                "/monitor/online/{tokenId}",
                Some("monitor:online:forceLogout"),
                Some(&LOG_FORCE),
                force_logout,
            ),
        )
}

fn online_of(login_user: &LoginUser) -> Value {
    json!({
        "tokenId": login_user.token,
        "sessionId": login_user.session_id,
        "deptName": login_user.user.dept_id.map(|_| Value::Null).unwrap_or(Value::Null),
        "userName": login_user.username.clone().or_else(|| login_user.user.user_name.clone()),
        "ipaddr": login_user.ipaddr,
        "loginLocation": login_user.login_location,
        "browser": login_user.browser,
        "os": login_user.os,
        "loginTime": login_user.login_time,
    })
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let params = support::query_map(&raw);
    let ipaddr = params.get("ipaddr").cloned().unwrap_or_default();
    let user_name = params.get("userName").cloned().unwrap_or_default();

    let mut rows = Vec::new();
    for key in state.redis.keys(&format!("{TOKEN_PREFIX}*")).await? {
        let Some(login_user) = state.redis.get_object::<LoginUser>(&key).await? else {
            continue;
        };
        let username = login_user
            .username
            .clone()
            .or_else(|| login_user.user.user_name.clone())
            .unwrap_or_default();
        let matched = if !ipaddr.is_empty() && !user_name.is_empty() {
            login_user.ipaddr.as_deref() == Some(ipaddr.as_str()) && username == user_name
        } else if !ipaddr.is_empty() {
            login_user.ipaddr.as_deref() == Some(ipaddr.as_str())
        } else if !user_name.is_empty() {
            username == user_name
        } else {
            true
        };
        if matched {
            rows.push(online_of(&login_user));
        }
    }
    rows.reverse();
    Ok(TableDataInfo::new(rows.len() as i64, rows))
}

async fn force_logout(
    State(state): State<AppState>,
    Path(token_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    state
        .redis
        .delete_object(&format!("{TOKEN_PREFIX}{token_id}"))
        .await?;
    Ok(AjaxResult::success())
}
