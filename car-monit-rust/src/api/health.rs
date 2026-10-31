// Rust-only: 容器编排探活端点（Java 无对应实现）。
// 默认由 app.health-endpoint-enabled 控制，启用时 GET /health。

use axum::extract::State;
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use serde_json::json;

use crate::state::AppState;

pub async fn health(State(state): State<AppState>) -> Response {
    match state.check_health().await {
        Ok(()) => (StatusCode::OK, Json(json!({"status": "UP"}))).into_response(),
        Err(err) => (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({"status": "DOWN", "error": err.to_string()})),
        )
            .into_response(),
    }
}
