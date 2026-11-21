// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysProfileController.java
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserServiceImpl.java
// 职责: 个人信息、修改密码、头像上传（均刷新 Redis 登录态）。
// 对应关系: profile/updateProfile/updatePwd/avatar -> 本地 SQL + profile 目录。

use std::collections::HashMap;

use axum::extract::{Multipart, Query, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support;
use crate::auth::password;
use crate::common::utils::password_invalid;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

/// Java 登录态 user 由 FastJson2 反序列化，params 字段里会残留 `@type` 键。
fn shape_profile_user(value: &mut Value, admin: bool) {
    {
        let Some(object) = value.as_object_mut() else {
            return;
        };
        object.remove("password");
        object.insert("admin".to_string(), Value::Bool(admin));
        let params = json!({ "@type": "java.util.HashMap" });
        object.insert("params".to_string(), params.clone());
        if let Some(dept) = object.get_mut("dept").and_then(Value::as_object_mut) {
            dept.insert("params".to_string(), params.clone());
        }
        if let Some(roles) = object.get_mut("roles").and_then(Value::as_array_mut) {
            for role in roles.iter_mut() {
                let Some(role) = role.as_object_mut() else {
                    continue;
                };
                role.insert("params".to_string(), params.clone());
                let role_admin = role.get("roleId").and_then(Value::as_i64) == Some(1);
                role.insert("admin".to_string(), Value::Bool(role_admin));
            }
        }
    }
    // Jackson 顺序：先把嵌套对象内部排好，再排外层（外层重排会把它们放到各自的位置上）。
    if let Some(object) = value.as_object_mut() {
        if let Some(dept) = object.get_mut("dept") {
            *dept = support::reorder_keys(dept.take(), super::sys_dept::DEPT_KEYS);
        }
        if let Some(roles) = object.get_mut("roles").and_then(Value::as_array_mut) {
            for role in roles.iter_mut() {
                *role = support::reorder_keys(role.take(), super::sys_role::ROLE_KEYS);
            }
        }
    }
    *value = support::reorder_keys(value.take(), super::sys_user::USER_KEYS);
}

static LOG_UPDATE: LogSpec = LogSpec::new(
    "个人信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysProfileController.updateProfile()",
);
static LOG_PWD: LogSpec = LogSpec::new(
    "个人信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysProfileController.updatePwd()",
);
static LOG_AVATAR: LogSpec = LogSpec::new(
    "用户头像",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysProfileController.avatar()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/user/profile",
            meta::get_route("/system/user/profile", None, None, profile).merge(meta::put_route(
                "/system/user/profile",
                None,
                Some(&LOG_UPDATE),
                update_profile,
            )),
        )
        .route(
            "/system/user/profile/updatePwd",
            meta::put_route(
                "/system/user/profile/updatePwd",
                None,
                Some(&LOG_PWD),
                update_pwd,
            ),
        )
        .route(
            "/system/user/profile/avatar",
            meta::post_route(
                "/system/user/profile/avatar",
                None,
                Some(&LOG_AVATAR),
                avatar,
            ),
        )
}

async fn profile(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
) -> Result<AjaxResult, AppError> {
    let user_name = user.user.user_name.clone().unwrap_or_default();
    let role_group: Option<String> = sqlx::query_scalar(
        "select group_concat(distinct r.role_name) from sys_role r \
         left join sys_user_role ur on ur.role_id = r.role_id \
         left join sys_user u on u.user_id = ur.user_id where u.user_name = ?",
    )
    .bind(&user_name)
    .fetch_optional(&state.db)
    .await?
    .flatten();
    let post_group: Option<String> = sqlx::query_scalar(
        "select group_concat(p.post_name) from sys_post p \
         left join sys_user_post up on up.post_id = p.post_id \
         left join sys_user u on u.user_id = up.user_id where u.user_name = ?",
    )
    .bind(&user_name)
    .fetch_optional(&state.db)
    .await?
    .flatten();

    let mut data = serde_json::to_value(user.user.for_http())?;
    shape_profile_user(&mut data, user.user.is_admin());
    let mut ajax = AjaxResult::success();
    ajax.insert_value("data", data);
    ajax.insert_value("roleGroup", json!(role_group.unwrap_or_default()));
    ajax.insert_value("postGroup", json!(post_group.unwrap_or_default()));
    Ok(ajax)
}

async fn update_profile(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let user_name = body
        .get("userName")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let user_id = body.get("userId").and_then(Value::as_i64);
    let phone = body
        .get("phonenumber")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let email = body
        .get("email")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();

    if !phone.is_empty() {
        if let Some(found) = support::scalar_i64(
            &state.db,
            "select user_id from sys_user where phonenumber = ? and del_flag = '0' limit 1",
            &phone,
        )
        .await?
        {
            if Some(found) != user_id {
                return Ok(AjaxResult::error(format!(
                    "修改用户'{user_name}'失败，手机号码已存在"
                )));
            }
        }
    }
    if !email.is_empty() {
        if let Some(found) = support::scalar_i64(
            &state.db,
            "select user_id from sys_user where email = ? and del_flag = '0' limit 1",
            &email,
        )
        .await?
        {
            if Some(found) != user_id {
                return Ok(AjaxResult::error(format!(
                    "修改用户'{user_name}'失败，邮箱账号已存在"
                )));
            }
        }
    }

    let mut fields = serde_json::Map::new();
    for key in ["nickName", "phonenumber", "email", "sex"] {
        if let Some(value) = body.get(key) {
            if !value.is_null() {
                fields.insert(key.to_string(), value.clone());
            }
        }
    }
    if fields.is_empty() {
        return Ok(AjaxResult::error("修改个人信息异常，请联系管理员"));
    }
    let entity = Value::Object(fields);
    let current_id = user.user.user_id.unwrap_or_default();
    let mut tx = state.db.begin().await?;
    let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new("update sys_user set ");
    let mut first = true;
    for (key, value) in entity.as_object().unwrap() {
        if !first {
            builder.push(", ");
        }
        first = false;
        builder.push(format!("{} = ", support::column_name(key)));
        support::bind_value(&mut builder, value);
    }
    builder.push(" where user_id = ");
    builder.push_bind(current_id);
    let rows = builder.build().execute(&mut *tx).await?.rows_affected();
    tx.commit().await?;
    if rows == 0 {
        return Ok(AjaxResult::error("修改个人信息异常，请联系管理员"));
    }

    let mut login_user = user.clone();
    login_user.user.nick_name = body
        .get("nickName")
        .and_then(Value::as_str)
        .map(str::to_string)
        .or(login_user.user.nick_name);
    login_user.user.phonenumber = body
        .get("phonenumber")
        .and_then(Value::as_str)
        .map(str::to_string)
        .or(login_user.user.phonenumber);
    login_user.user.email = body
        .get("email")
        .and_then(Value::as_str)
        .map(str::to_string)
        .or(login_user.user.email);
    login_user.user.sex = body
        .get("sex")
        .and_then(Value::as_str)
        .map(str::to_string)
        .or(login_user.user.sex);
    save_login_user(&state, &login_user).await?;
    Ok(AjaxResult::success())
}

async fn update_pwd(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Query(params): Query<HashMap<String, String>>,
) -> Result<AjaxResult, AppError> {
    let old_password = params.get("oldPassword").cloned().unwrap_or_default();
    let new_password = params.get("newPassword").cloned().unwrap_or_default();
    let encoded = user.user.password.clone().unwrap_or_default();
    if !password::matches(&old_password, &encoded).await {
        return Ok(AjaxResult::error("修改密码失败，旧密码错误"));
    }
    if password::matches(&new_password, &encoded).await {
        return Ok(AjaxResult::error("新密码不能与旧密码相同"));
    }
    if password_invalid(&new_password) {
        return Ok(AjaxResult::error(
            "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！",
        ));
    }
    let new_encoded = password::encode(&new_password).await?;
    let rows =
        sqlx::query("update sys_user set password = ?, update_time = now() where user_name = ?")
            .bind(&new_encoded)
            .bind(&user.user.user_name)
            .execute(&state.db)
            .await?
            .rows_affected();
    if rows == 0 {
        return Ok(AjaxResult::error("修改密码异常，请联系管理员"));
    }
    let mut login_user = user.clone();
    login_user.user.password = Some(new_encoded);
    save_login_user(&state, &login_user).await?;
    Ok(AjaxResult::success())
}

async fn avatar(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    let mut uploaded: Option<Vec<u8>> = None;
    let mut original = String::new();
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        if field.name() == Some("avatarfile") {
            let upload = crate::api::support::read_multipart_field(field).await?;
            original = upload.file_name;
            uploaded = Some(upload.bytes);
        }
    }
    let Some(bytes) = uploaded else {
        return Ok(AjaxResult::error("上传图片异常，请联系管理员"));
    };

    // Java: FileUploadUtils.upload(profile + "/avatar", file) -> /profile/avatar/yyyy/MM/dd/{name}.
    let date_path = chrono::Local::now().format("%Y/%m/%d").to_string();
    let ext = original
        .rsplit_once('.')
        .map(|(_, ext)| ext)
        .unwrap_or("png");
    let base = original
        .rsplit_once('.')
        .map(|(base, _)| base)
        .unwrap_or("avatar");
    let stored = format!("{base}_{}.{ext}", uuid::Uuid::new_v4().simple());
    let dir = std::path::PathBuf::from(&state.settings.ruoyi.profile)
        .join("avatar")
        .join(&date_path);
    // 落盘是阻塞 IO，移出 tokio worker。
    tokio::task::block_in_place(|| {
        std::fs::create_dir_all(&dir)
            .map_err(|err| AppError::Service(format!("创建头像目录失败: {err}")))?;
        std::fs::write(dir.join(&stored), &bytes)
            .map_err(|err| AppError::Service(format!("保存头像失败: {err}")))
    })?;
    let avatar_path = format!("/profile/avatar/{date_path}/{stored}");

    let rows = sqlx::query("update sys_user set avatar = ? where user_name = ?")
        .bind(&avatar_path)
        .bind(&user.user.user_name)
        .execute(&state.db)
        .await?
        .rows_affected();
    if rows == 0 {
        return Ok(AjaxResult::error("上传图片异常，请联系管理员"));
    }
    let mut login_user = user.clone();
    login_user.user.avatar = Some(avatar_path.clone());
    save_login_user(&state, &login_user).await?;

    let mut ajax = AjaxResult::success();
    ajax.insert_value("imgUrl", json!(avatar_path));
    Ok(ajax)
}

async fn save_login_user(state: &AppState, login_user: &LoginUser) -> Result<(), AppError> {
    let ttl = login_user.expire_time - chrono::Utc::now().timestamp_millis();
    let seconds = (ttl / 1000).max(1) as u64;
    // FastJson2 WriteClassName：登录态写回 Redis 必须带 @type。
    let stored = login_user.clone().for_redis();
    state
        .redis
        .set_object_ttl(
            &format!("login_tokens:{}", login_user.token),
            &stored,
            Some(std::time::Duration::from_secs(seconds)),
        )
        .await?;
    Ok(())
}
