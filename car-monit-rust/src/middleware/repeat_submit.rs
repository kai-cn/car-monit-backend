// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/impl/SameUrlDataInterceptor.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/RepeatSubmitInterceptor.java
// 职责: 复刻 @RepeatSubmit 防重复提交（当前仅 /system/config 新增使用）。
// 对应关系: HandlerInterceptor.preHandle -> repeat_submit_middleware。

use std::time::Duration;

use axum::body::{Body, Bytes};
use axum::extract::{Request, State};
use axum::http::header::CONTENT_TYPE;
use axum::http::Method;
use axum::middleware::Next;
use axum::response::{IntoResponse, Response};
use serde_json::{json, Map, Value};

use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

/// Java: `SysConfigController.add` 上的 `@RepeatSubmit`。
const REPEAT_SUBMIT_PATH: &str = "/system/config";
/// Java: `@RepeatSubmit.message()` 默认值。
const REPEAT_SUBMIT_MESSAGE: &str = "不允许重复提交，请稍候再试";
/// Java: `@RepeatSubmit.interval()` 默认 5000 毫秒。
const REPEAT_SUBMIT_INTERVAL_MS: i64 = 5000;
/// Java: `CacheConstants.REPEAT_SUBMIT_KEY`。
const REPEAT_SUBMIT_KEY: &str = "repeat_submit:";
const MAX_BODY_BYTES: usize = 200 * 1024 * 1024;

pub async fn repeat_submit_middleware(
    State(state): State<AppState>,
    request: Request,
    next: Next,
) -> Response {
    if request.method() != Method::POST || request.uri().path() != REPEAT_SUBMIT_PATH {
        return next.run(request).await;
    }

    let token = request
        .headers()
        .get(state.settings.token.header.as_str())
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default()
        .trim()
        .to_string();
    let (parts, body) = request.into_parts();
    let bytes = axum::body::to_bytes(body, MAX_BODY_BYTES)
        .await
        .unwrap_or_else(|_| Bytes::new());
    let now_params = String::from_utf8_lossy(&bytes).to_string();

    match check_repeat(&state, &token, &now_params).await {
        Ok(true) => repeat_response(),
        Ok(false) => {
            next.run(Request::from_parts(parts, Body::from(bytes)))
                .await
        }
        // Java: Redis 异常会冒到 GlobalExceptionHandler -> HTTP 200 + code 500。
        Err(err) => err.into_response(),
    }
}

async fn check_repeat(state: &AppState, token: &str, now_params: &str) -> Result<bool, AppError> {
    let key = format!("{REPEAT_SUBMIT_KEY}{REPEAT_SUBMIT_PATH}{token}");
    let now = chrono::Utc::now().timestamp_millis();

    if let Some(Value::Object(map)) = state.redis.get_object::<Value>(&key).await? {
        if let Some(Value::Object(previous)) = map.get(REPEAT_SUBMIT_PATH) {
            let previous_params = previous
                .get("repeatParams")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let previous_time = previous
                .get("repeatTime")
                .and_then(Value::as_i64)
                .unwrap_or_default();
            if previous_params == now_params && now - previous_time < REPEAT_SUBMIT_INTERVAL_MS {
                return Ok(true);
            }
        }
    }

    // Java: FastJson2 写缓存时 HashMap 根对象带 @type。
    let mut inner = Map::new();
    inner.insert("repeatParams".to_string(), json!(now_params));
    inner.insert("repeatTime".to_string(), json!(now));
    let mut outer = Map::new();
    outer.insert("@type".to_string(), json!("java.util.HashMap"));
    outer.insert(REPEAT_SUBMIT_PATH.to_string(), Value::Object(inner));
    state
        .redis
        .set_object_ttl(
            &key,
            &Value::Object(outer),
            Some(Duration::from_millis(REPEAT_SUBMIT_INTERVAL_MS as u64)),
        )
        .await?;
    Ok(false)
}

/// Java: `ServletUtils.renderString` —— HTTP 200 + `application/json;charset=utf-8`。
fn repeat_response() -> Response {
    let body = serde_json::to_vec(&AjaxResult::error(REPEAT_SUBMIT_MESSAGE))
        .unwrap_or_else(|_| b"{}".to_vec());
    Response::builder()
        .status(200)
        .header(CONTENT_TYPE, "application/json;charset=utf-8")
        .body(Body::from(body))
        .unwrap_or_else(|_| AjaxResult::error(REPEAT_SUBMIT_MESSAGE).into_response())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn repeat_window_is_java_default() {
        assert_eq!(REPEAT_SUBMIT_INTERVAL_MS, 5000);
        assert_eq!(REPEAT_SUBMIT_MESSAGE, "不允许重复提交，请稍候再试");
    }
}
