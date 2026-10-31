// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysLoginController.java
// 职责: /login、/getInfo 与 /getRouters。
// 对应关系: login(LoginBody) -> login；getInfo() -> get_info；getRouters() -> get_routers。

use std::net::SocketAddr;

use axum::extract::rejection::JsonRejection;
use axum::extract::{ConnectInfo, State};
use axum::http::HeaderMap;
use axum::Extension;
use axum::Json;
use serde_json::json;

use crate::auth::login_service;
use crate::common::constants::{ALL_PERMISSION, SUPER_ADMIN};
use crate::common::utils::{client_meta, password_invalid};
use crate::domain::{LoginBody, LoginUser};
use crate::error::AppError;
use crate::repository::user_repo;
use crate::response::AjaxResult;
use crate::service::menu_service;
use crate::state::AppState;

/// i18n 之外的控制器常量（SysLoginController.login）
pub const MSG_PASSWORD_RULE: &str =
    "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！";

/// Java: POST /login
pub async fn login(
    State(state): State<AppState>,
    ConnectInfo(addr): ConnectInfo<SocketAddr>,
    headers: HeaderMap,
    payload: Result<Json<LoginBody>, JsonRejection>,
) -> Result<AjaxResult, AppError> {
    let Json(body) = payload?;

    // Java: String curPassword = CommonUtil.isNull(loginBody.getPassword());
    //       if (CommonUtil.checkPassword(curPassword)) return error(...)
    let cur_password = body.password().trim().to_string();
    if password_invalid(&cur_password) {
        return Ok(AjaxResult::error(MSG_PASSWORD_RULE));
    }

    let meta = client_meta(&headers, Some(addr), state.settings.ruoyi.address_enabled);
    let token = login_service::login(&state, &body, &meta).await?;
    Ok(AjaxResult::login(&token))
}

/// Java: GET /getInfo
pub async fn get_info(
    State(state): State<AppState>,
    Extension(login_user): Extension<LoginUser>,
) -> Result<AjaxResult, AppError> {
    let user = login_user.user.clone();

    // SysPermissionService.getRolePermission
    let roles = if user.is_admin() {
        vec![SUPER_ADMIN.to_string()]
    } else {
        match user.user_id {
            Some(user_id) => user_repo::select_role_keys_for_user(&state.db, user_id).await?,
            None => Vec::new(),
        }
    };

    // SysPermissionService.getMenuPermission
    let permissions = if user.is_admin() {
        vec![ALL_PERMISSION.to_string()]
    } else {
        match user.user_id {
            Some(user_id) => user_repo::select_menu_perms_for_user(&state.db, user_id).await?,
            None => Vec::new(),
        }
    };

    // 实测 Java 响应顺序：msg,code,pjFlag,overdue,permissions,roles,user
    let mut result = AjaxResult::success();
    result.insert_value("pjFlag", json!(0));
    result.insert_value("overdue", json!(false));
    result.insert_value("permissions", json!(permissions));
    result.insert_value("roles", json!(roles));
    result.insert_value("user", serde_json::to_value(user.for_http())?);
    Ok(result)
}

/// Java: GET /getRouters
pub async fn get_routers(
    State(state): State<AppState>,
    Extension(login_user): Extension<LoginUser>,
) -> Result<AjaxResult, AppError> {
    // Java: userId == null ? -9999L : userId
    let user_id = login_user.user.user_id.unwrap_or(-9999);
    let menus = menu_service::select_menu_tree_by_user_id(&state.db, user_id).await?;
    let routers = menu_service::build_menus(&menus);
    Ok(AjaxResult::success_data(routers))
}
