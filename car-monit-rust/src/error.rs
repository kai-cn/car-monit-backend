// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/web/exception/GlobalExceptionHandler.java
// 职责: 复刻 GlobalExceptionHandler 的唯一生效模型（附录 E 实测）。
// 对应关系: @ExceptionHandler -> AppError 变体；handler 返回 Result<_, AppError>。
//
// 关键行为：除 404 外，所有业务/鉴权/校验/运行异常都返回 HTTP 200，
// 401/403 只是 body 内的 code。

use axum::http::{header, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};

use crate::response::AjaxResult;

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    /// AuthenticationEntryPointImpl
    #[error("{0}")]
    Unauthorized(String),
    /// AccessDeniedException
    #[error("{0}")]
    Forbidden(String),
    /// ServiceException
    #[error("{0}")]
    Service(String),
    /// ServiceException with custom code
    #[error("{1}")]
    ServiceCode(i32, String),
    /// BindException / MethodArgumentNotValidException（Java 仍返回 500）
    #[error("{0}")]
    Validation(String),
    /// HttpMessageNotReadableException / 参数类型不匹配等
    #[error("{0}")]
    BadRequest(String),
    /// HttpRequestMethodNotSupportedException
    #[error("{0}")]
    MethodNotSupported(String),
    /// RuntimeException / Exception；None 对应 NPE 的 msg=null
    #[error("{0:?}")]
    Internal(Option<String>),
    /// 数据库错误，最终映射为 500
    #[error("数据库异常: {0}")]
    Database(String),
    /// Redis 错误，最终映射为 500
    #[error("缓存异常: {0}")]
    Cache(String),
}

impl AppError {
    pub fn unauthorized(uri: &str) -> Self {
        Self::Unauthorized(format!("请求访问：{}，认证失败，无法访问系统资源", uri))
    }

    pub fn forbidden() -> Self {
        Self::Forbidden("没有权限，请联系管理员授权".to_string())
    }

    pub fn validation(msg: impl Into<String>) -> Self {
        Self::Validation(msg.into())
    }

    pub fn internal(msg: impl Into<String>) -> Self {
        Self::Internal(Some(msg.into()))
    }

    pub fn npe() -> Self {
        Self::Internal(None)
    }

    pub fn status_code(&self) -> i32 {
        match self {
            Self::Unauthorized(_) => 401,
            Self::Forbidden(_) => 403,
            Self::Service(_)
            | Self::Validation(_)
            | Self::BadRequest(_)
            | Self::MethodNotSupported(_)
            | Self::Internal(_)
            | Self::Database(_)
            | Self::Cache(_) => 500,
            Self::ServiceCode(code, _) => *code,
        }
    }

    pub fn user_message(&self) -> Option<String> {
        match self {
            Self::Unauthorized(m)
            | Self::Forbidden(m)
            | Self::Service(m)
            | Self::Validation(m)
            | Self::BadRequest(m)
            | Self::MethodNotSupported(m) => Some(m.clone()),
            Self::ServiceCode(_, m) => Some(m.clone()),
            Self::Internal(m) => m.clone(),
            Self::Database(m) | Self::Cache(m) => Some(m.clone()),
        }
    }
}

/// Java: 由 GlobalExceptionHandler 产生的响应（区别于控制器主动返回的 AjaxResult.error）。
/// @Log 切面据此把 sys_oper_log.status 置为失败。
#[derive(Debug, Clone, Copy)]
pub struct ErrorResponseMarker;

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let code = self.status_code();
        let body = match self.user_message() {
            Some(msg) => AjaxResult::error_code(code, msg),
            // Java NPE: {"msg":null,"code":500}
            None => AjaxResult::new()
                .put("msg", serde_json::Value::Null)
                .put("code", code),
        };
        let mut response = body.into_response();
        // Java: 认证/授权失败由 Spring Security 的 EntryPoint/AccessDeniedHandler 直接写响应，
        // Content-Type 是 `application/json;charset=utf-8`（小写），与 MVC 转换器的 `application/json` 不同。
        if matches!(self, Self::Unauthorized(_) | Self::Forbidden(_)) {
            response.headers_mut().insert(
                header::CONTENT_TYPE,
                HeaderValue::from_static("application/json;charset=utf-8"),
            );
        }
        response.extensions_mut().insert(ErrorResponseMarker);
        response
    }
}

/// Axum 的 Json 提取失败默认返回 400；Java 实测为 HTTP 200 + AjaxResult(code=500)。
impl From<axum::extract::rejection::JsonRejection> for AppError {
    fn from(rejection: axum::extract::rejection::JsonRejection) -> Self {
        Self::BadRequest(rejection.body_text())
    }
}

/// Axum 路径参数类型不匹配，Java 文案为中文格式化。
impl From<axum::extract::rejection::PathRejection> for AppError {
    fn from(rejection: axum::extract::rejection::PathRejection) -> Self {
        Self::BadRequest(rejection.body_text())
    }
}

impl From<sqlx::Error> for AppError {
    fn from(err: sqlx::Error) -> Self {
        // Java SqlLogInterceptor.intercept 的 finally 里：
        // log.error("[SQL异常] {}, 耗时: {}ms, 异常: {}", sqlId, cost, throwable.getMessage())
        // 并写 SqlLogInterceptor logger（logback additivity=false -> sys-slow.log）。
        // Rust 侧没有 Mapper id，单次耗时尚需在 SQLx 事件里可见（成功执行时），
        // 异常转 AppError 时只能拿到异常文本。
        tracing::error!(
            target: crate::logging::SQL_LOG_TARGET,
            "[SQL异常] sqlx::query, 异常: {}",
            err
        );
        Self::Database(err.to_string())
    }
}

impl From<redis::RedisError> for AppError {
    fn from(err: redis::RedisError) -> Self {
        Self::Cache(err.to_string())
    }
}

impl From<serde_json::Error> for AppError {
    fn from(err: serde_json::Error) -> Self {
        Self::Internal(Some(err.to_string()))
    }
}

impl From<anyhow::Error> for AppError {
    fn from(err: anyhow::Error) -> Self {
        Self::Internal(Some(err.to_string()))
    }
}

/// Java: Spring Boot 默认 `/error` 响应体 —— `{"timestamp","status","error","path"}`。
/// 实测 charset 与请求方法有关：POST/PUT/PATCH 时是 `application/json;charset=UTF-8`，
/// GET/DELETE 时是 `application/json`；授权失败（403）无论什么方法都不带 charset。
fn spring_error_page(status: u16, error: &str, path: &str, charset: bool) -> Response {
    let now = chrono::Local::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true);
    let body = serde_json::json!({
        "timestamp": now,
        "status": status,
        "error": error,
        "path": path,
    });
    let content_type = if charset {
        "application/json;charset=UTF-8"
    } else {
        "application/json"
    };
    (
        StatusCode::from_u16(status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
        [(header::CONTENT_TYPE, content_type)],
        serde_json::to_vec(&body).unwrap_or_default(),
    )
        .into_response()
}

/// Java: 路径没有处理器 -> DefaultHandlerExceptionResolver/无匹配 -> sendError(404) -> /error。
pub fn not_found_response(method: &axum::http::Method, path: &str) -> Response {
    let charset = matches!(
        *method,
        axum::http::Method::POST | axum::http::Method::PUT | axum::http::Method::PATCH
    );
    spring_error_page(404, "Not Found", path, charset)
}

/// Java: Spring Security 只定制了 authenticationEntryPoint（401 走 RuoYi 的 JSON），
/// 授权失败仍用默认的 AccessDeniedHandlerImpl -> response.sendError(403) -> /error 的 JSON 错误页。
/// 命中 `anonymous()` / `denyAll()` 这类 URL 规则时就是这一种，而不是 AjaxResult。
pub fn forbidden_error_page(path: &str) -> Response {
    spring_error_page(403, "Forbidden", path, false)
}
