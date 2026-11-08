// 来源: ruoyi-framework/.../aspectj/LogAspect.java
//       ruoyi-framework/.../security/SecurityConfig.java + @PreAuthorize
// 职责: 路由级元数据（权限点 / 操作日志）注册与统一执行。
// 对应关系: @PreAuthorize("@ss.hasPermi('x')") -> RouteMeta.permission；
//           @Log(title, businessType) -> RouteMeta.log + audit::record_oper。
//
// 为什么用中间件：501 条端点里 284 条有权限点、239 条有 @Log。把这两件事
// 放进统一中间件，handler 只写业务逻辑，且 sys_oper_log 的字段/截断规则只实现一次。

use std::panic::AssertUnwindSafe;
use std::sync::LazyLock;

use axum::body::Body;
use axum::extract::{MatchedPath, Request, State};
use axum::http::{header, Method};
use axum::middleware::Next;
use axum::response::{IntoResponse, Response};
use axum::routing::MethodRouter;
use dashmap::DashMap;
use futures::FutureExt;

use crate::auth::audit::{self, OperRecord};
use crate::auth::security;
use crate::common::utils::client_meta;
use crate::domain::LoginUser;
use crate::error::ErrorResponseMarker;
use crate::middleware::web_filter::OriginalPath;
use crate::response::AjaxResult;
use crate::state::AppState;

/// 请求体采样上限；超过则不再缓存（导出/列表响应仍照常返回）。
const REQUEST_CAPTURE_LIMIT: usize = 16 * 1024 * 1024;
/// 响应体采样上限。
const RESPONSE_CAPTURE_LIMIT: usize = 64 * 1024 * 1024;
/// Java: LogAspect 的 `StringUtils.substring(x, 0, 2000)`。
const LOG_TEXT_LIMIT: usize = 2000;

/// Java: `com.ruoyi.common.enums.BusinessType` 的 ordinal。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BusinessType {
    Other = 0,
    Insert = 1,
    Update = 2,
    Delete = 3,
    Grant = 4,
    Export = 5,
    Import = 6,
    Force = 7,
    Gencode = 8,
    Clean = 9,
}

/// Java: `@Log(title = "...", businessType = ...)`。
#[derive(Debug, Clone, Copy)]
pub struct LogSpec {
    pub title: &'static str,
    pub business_type: BusinessType,
    /// Java: `className + "." + methodName + "()"`，例如
    /// `com.ruoyi.web.controller.system.SysUserController.list()`。
    pub method: &'static str,
    /// Java @Log 默认 true。
    pub save_request_data: bool,
    /// Java @Log 默认 true。
    pub save_response_data: bool,
}

impl LogSpec {
    pub const fn new(
        title: &'static str,
        business_type: BusinessType,
        method: &'static str,
    ) -> Self {
        Self {
            title,
            business_type,
            method,
            save_request_data: true,
            save_response_data: true,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct RouteMeta {
    pub permission: Option<&'static str>,
    pub log: Option<&'static LogSpec>,
}

static REGISTRY: LazyLock<DashMap<(String, String), RouteMeta>> = LazyLock::new(DashMap::new);

fn static_method(method: &Method) -> &'static str {
    match *method {
        Method::GET => "GET",
        Method::POST => "POST",
        Method::PUT => "PUT",
        Method::DELETE => "DELETE",
        Method::PATCH => "PATCH",
        Method::HEAD => "HEAD",
        Method::OPTIONS => "OPTIONS",
        _ => "OTHER",
    }
}

/// 在构造路由时登记元数据；重复登记（测试多次 build_router）保持幂等。
pub fn register(
    method: &Method,
    pattern: &'static str,
    permission: Option<&'static str>,
    log: Option<&'static LogSpec>,
) {
    REGISTRY.insert(
        (static_method(method).to_string(), pattern.to_string()),
        RouteMeta { permission, log },
    );
}

/// 已登记路由快照（顺序不保证；供自检/对拍使用）。
pub fn registered() -> Vec<(String, String)> {
    REGISTRY
        .iter()
        .map(|entry| (entry.key().0.clone(), entry.key().1.clone()))
        .collect()
}

pub fn lookup(method: &Method, pattern: &str) -> Option<RouteMeta> {
    REGISTRY
        .get(&(static_method(method).to_string(), pattern.to_string()))
        .map(|entry| *entry.value())
}

macro_rules! route_helper {
    ($name:ident, $method:expr, $router:path) => {
        pub fn $name<H, T>(
            pattern: &'static str,
            permission: Option<&'static str>,
            log: Option<&'static LogSpec>,
            handler: H,
        ) -> MethodRouter<AppState>
        where
            H: axum::handler::Handler<T, AppState>,
            T: 'static,
        {
            register(&$method, pattern, permission, log);
            $router(handler)
        }
    };
}

route_helper!(get_route, Method::GET, axum::routing::get);
route_helper!(post_route, Method::POST, axum::routing::post);
route_helper!(put_route, Method::PUT, axum::routing::put);
route_helper!(delete_route, Method::DELETE, axum::routing::delete);
route_helper!(patch_route, Method::PATCH, axum::routing::patch);

/// 执行 @PreAuthorize + @Log。必须位于认证中间件内侧。
pub async fn meta_middleware(
    State(state): State<AppState>,
    request: Request,
    next: Next,
) -> Response {
    let Some(pattern) = request
        .extensions()
        .get::<MatchedPath>()
        .map(|path| path.as_str().to_string())
    else {
        return next.run(request).await;
    };
    let Some(meta) = lookup(request.method(), &pattern) else {
        return next.run(request).await;
    };

    // ---- @PreAuthorize ----
    if let Some(permission) = meta.permission {
        let allowed = request
            .extensions()
            .get::<LoginUser>()
            .map(|user| security::require_permission(user, permission).is_ok())
            .unwrap_or(false);
        if !allowed {
            // Java: AccessDeniedException -> {"code":403,"msg":"没有权限，请联系管理员授权"}
            return AjaxResult::error_code(403, "没有权限，请联系管理员授权").into_response();
        }
    }

    let Some(log_spec) = meta.log else {
        return next.run(request).await;
    };

    // ---- 拆请求：权限检查已完成，这里缓存请求体用于 oper_param ----
    let (parts, body) = request.into_parts();
    let method = parts.method.clone();
    // Java LogAspect 的 operUrl 取 getRequestURI()：尾斜杠归一路径后仍要记原始 URI。
    let uri_path = parts
        .extensions
        .get::<OriginalPath>()
        .map(|path| path.0.clone())
        .unwrap_or_else(|| parts.uri.path().to_string());
    let login_user = parts.extensions.get::<LoginUser>().cloned();
    let query = parts.uri.query().unwrap_or_default().to_string();
    let content_type = parts
        .headers
        .get(header::CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default()
        .to_string();

    let mut captured_text: Option<String> = None;
    let body = if log_spec.save_request_data && should_capture_body(&method, &content_type) {
        match axum::body::to_bytes(body, REQUEST_CAPTURE_LIMIT).await {
            Ok(bytes) => {
                captured_text = Some(String::from_utf8_lossy(&bytes).to_string());
                // 审计需要请求体；处理后必须原样回填，否则 Json 提取器会读到空 body。
                Body::from(bytes)
            }
            Err(_) => Body::empty(),
        }
    } else {
        body
    };

    let oper_param = if !log_spec.save_request_data {
        None
    } else if let Some(text) = captured_text {
        Some(truncate(&text, LOG_TEXT_LIMIT))
    } else if query.is_empty() {
        None
    } else {
        Some(truncate(&query_to_json(&query), LOG_TEXT_LIMIT))
    };

    let request = Request::from_parts(parts, body);
    let oper_name = login_user
        .as_ref()
        .map(|user| user.username())
        .unwrap_or_default();
    let dept_name = login_user
        .as_ref()
        .and_then(|user| user.user.dept.as_ref())
        .and_then(|dept| dept.dept_name.clone())
        .unwrap_or_default();
    let oper_ip = client_meta(
        request.headers(),
        request
            .extensions()
            .get::<axum::extract::ConnectInfo<std::net::SocketAddr>>()
            .map(|info| info.0),
        state.settings.ruoyi.address_enabled,
    )
    .ip;

    // Java: LogAspect 对抛出的异常同样落库（status=1 + errorMsg）；
    // 这里先捕获 panic 记审计，再把 panic 原样抛回给 web_filter 转 500。
    let response = match AssertUnwindSafe(next.run(request)).catch_unwind().await {
        Ok(response) => response,
        Err(payload) => {
            let message = crate::logging::panic_payload_text(&*payload);
            audit::record_oper(
                &state.db,
                OperRecord {
                    title: log_spec.title,
                    business_type: log_spec.business_type as i32,
                    method: log_spec.method,
                    request_method: method.as_str().to_string(),
                    oper_name,
                    dept_name,
                    oper_url: truncate(&uri_path, 255),
                    oper_ip,
                    oper_param,
                    json_result: None,
                    status: 1,
                    error_msg: Some(truncate(&format!("panic: {message}"), LOG_TEXT_LIMIT)),
                },
            );
            std::panic::resume_unwind(payload);
        }
    };

    // ---- 结果体：LogAspect 的 jsonResult / status / errorMsg ----
    let is_error = response.extensions().get::<ErrorResponseMarker>().is_some();
    let (parts, body) = response.into_parts();

    // Java: 导出类端点直接写 HttpServletResponse 流，LogAspect 拿不到 JSON 结果；
    // 这里不缓冲二进制 body，避免 64MB 上限与二次拷贝。
    if is_binary_response(&parts.headers) {
        audit::record_oper(
            &state.db,
            OperRecord {
                title: log_spec.title,
                business_type: log_spec.business_type as i32,
                method: log_spec.method,
                request_method: method.as_str().to_string(),
                oper_name,
                dept_name,
                oper_url: truncate(&uri_path, 255),
                oper_ip,
                oper_param,
                json_result: None,
                status: if is_error { 1 } else { 0 },
                error_msg: None,
            },
        );
        return Response::from_parts(parts, body);
    }

    let body_bytes = match axum::body::to_bytes(body, RESPONSE_CAPTURE_LIMIT).await {
        Ok(bytes) => bytes,
        Err(_) => return Response::from_parts(parts, Body::empty()),
    };
    let body_text = String::from_utf8_lossy(&body_bytes).to_string();
    let json_result = if log_spec.save_response_data && !is_error {
        Some(truncate(&body_text, LOG_TEXT_LIMIT))
    } else {
        None
    };
    let error_msg = if is_error {
        serde_json::from_str::<serde_json::Value>(&body_text)
            .ok()
            .and_then(|value| {
                value
                    .get("msg")
                    .and_then(|msg| msg.as_str())
                    .map(str::to_string)
            })
            .map(|msg| truncate(&msg, LOG_TEXT_LIMIT))
    } else {
        None
    };

    audit::record_oper(
        &state.db,
        OperRecord {
            title: log_spec.title,
            business_type: log_spec.business_type as i32,
            method: log_spec.method,
            request_method: method.as_str().to_string(),
            oper_name,
            dept_name,
            oper_url: truncate(&uri_path, 255),
            oper_ip,
            oper_param,
            json_result,
            status: if is_error { 1 } else { 0 },
            error_msg,
        },
    );

    Response::from_parts(parts, Body::from(body_bytes))
}

fn is_binary_response(headers: &axum::http::HeaderMap) -> bool {
    let content_type = headers
        .get(header::CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default()
        .to_ascii_lowercase();
    let attachment = headers
        .get(header::CONTENT_DISPOSITION)
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default()
        .to_ascii_lowercase();
    content_type.contains("application/octet-stream") || attachment.contains("attachment")
}

fn should_capture_body(method: &Method, content_type: &str) -> bool {
    if matches!(
        *method,
        Method::GET | Method::DELETE | Method::HEAD | Method::OPTIONS
    ) {
        return false;
    }
    // 文件上传的 body 不能缓存后重放（体积大且后续 extractor 需要流）。
    !content_type.to_ascii_lowercase().contains("multipart/")
}

/// query string -> JSON 对象（ServletUtils.getParamMap 的等价物）。
fn query_to_json(query: &str) -> String {
    let mut map = serde_json::Map::new();
    for (key, value) in url::form_urlencoded::parse(query.as_bytes()) {
        map.entry(key.into_owned())
            .or_insert_with(|| serde_json::Value::String(value.into_owned()));
    }
    serde_json::Value::Object(map).to_string()
}

fn truncate(value: &str, limit: usize) -> String {
    value.chars().take(limit).collect()
}
