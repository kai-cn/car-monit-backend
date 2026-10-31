// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/TestController.java
// 职责: Swagger 示例接口（内存用户表）。
// 对应关系: LinkedHashMap<Integer, UserEntity> -> parking_lot::Mutex<IndexMap<i64, Value>>。

use std::sync::LazyLock;

use axum::extract::{Path, Query};
use axum::{Json, Router};
use indexmap::IndexMap;
use parking_lot::Mutex;
use serde_json::{json, Value};

use crate::api::meta;
use crate::response::R;
use crate::state::AppState;

static USERS: LazyLock<Mutex<IndexMap<i64, Value>>> = LazyLock::new(|| {
    let mut users = IndexMap::new();
    users.insert(1, user(1, "admin", "admin123", "15888888888"));
    users.insert(2, user(2, "ry", "admin123", "15666666666"));
    Mutex::new(users)
});

fn user(user_id: i64, username: &str, password: &str, mobile: &str) -> Value {
    json!({
        "userId": user_id,
        "username": username,
        "password": password,
        "mobile": mobile,
    })
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/test/user/list",
            meta::get_route("/test/user/list", None, None, list),
        )
        .route(
            "/test/user/save",
            meta::post_route("/test/user/save", None, None, save),
        )
        .route(
            "/test/user/update",
            meta::put_route("/test/user/update", None, None, update),
        )
        .route(
            "/test/user/{userId}",
            meta::get_route("/test/user/{userId}", None, None, get_user)
                .merge(meta::delete_route(
                    "/test/user/{userId}",
                    None,
                    None,
                    delete_user,
                )),
        )
}

async fn list() -> R<Vec<Value>> {
    R::ok(Some(USERS.lock().values().cloned().collect()))
}

async fn get_user(Path(user_id): Path<i64>) -> R<Value> {
    match USERS.lock().get(&user_id).cloned() {
        Some(user) => R::ok(Some(user)),
        None => R::fail(500, "用户不存在"),
    }
}

async fn save(Query(params): Query<std::collections::HashMap<String, String>>) -> R<Value> {
    let Some(user_id) = params.get("userId").and_then(|value| value.parse::<i64>().ok()) else {
        return R::fail(500, "用户ID不能为空");
    };
    let entity = json!({
        "userId": user_id,
        "username": params.get("username").cloned().unwrap_or_default(),
        "password": params.get("password").cloned().unwrap_or_default(),
        "mobile": params.get("mobile").cloned().unwrap_or_default(),
    });
    USERS.lock().insert(user_id, entity);
    R::ok(None)
}

async fn update(Json(body): Json<Value>) -> R<Value> {
    let Some(user_id) = body.get("userId").and_then(Value::as_i64) else {
        return R::fail(500, "用户ID不能为空");
    };
    let mut users = USERS.lock();
    if !users.contains_key(&user_id) {
        return R::fail(500, "用户不存在");
    }
    users.shift_remove(&user_id);
    users.insert(user_id, body);
    R::ok(None)
}

async fn delete_user(Path(user_id): Path<i64>) -> R<Value> {
    let mut users = USERS.lock();
    if users.shift_remove(&user_id).is_some() {
        R::ok(None)
    } else {
        R::fail(500, "用户不存在")
    }
}
