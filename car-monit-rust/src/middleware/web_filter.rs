// 来源: ruoyi-system/src/main/java/com/ruoyi/common/core/filter/TraceIdFilter.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java（headers 段）
//       ruoyi-framework/src/main/java/com/ruoyi/framework/config/CorsConfig.java
// 职责: 响应头层面的对等 —— 链路 TraceId、Spring Security 默认安全头、Spring Cors 的头写法。
// 对应关系: Filter(order=1) + CorsFilter -> 最外层 middleware（401/404/405 也要带上这些头，Java 就是在业务之前 setHeader 的）。

use std::net::SocketAddr;
use std::time::Instant;

use axum::extract::{ConnectInfo, Request, State};
use axum::http::header::{
    HeaderName, HeaderValue, ACCESS_CONTROL_ALLOW_CREDENTIALS, ACCESS_CONTROL_ALLOW_ORIGIN, ALLOW,
    VARY,
};
use axum::middleware::Next;
use axum::response::Response;
use futures::FutureExt;

use crate::common::utils::client_ip;
use crate::logging;

/// Java: `TraceIdFilter.TRACE_ID_HEADER`（配置项 `monitor.trace-id-header` 的默认值）。
const TRACE_ID: &str = "x-trace-id";
/// `useTrailingSlashMatch` 削掉尾斜杠之前的原始 URI（Java 日志里的 `getRequestURI()`）。
#[derive(Clone)]
pub struct OriginalPath(pub String);
/// Java: `CorsConfig` 回显的请求头名。
const ALLOW_HEADERS: &str = "access-control-allow-headers";
/// Java: `TraceIdFilter` 的 logger 名（决定 sys-slow appender）。
const TRACE_FILTER_TARGET: &str = "com.ruoyi.common.core.monitor.TraceIdFilter";
/// Java: `TraceIdFilter.doFilter` 里的慢请求阈值（硬编码 3000ms）。
const SLOW_REQUEST_MILLIS: u128 = 3000;

/// Java: `TRACE_ID_PREFIX` 为空串，所以生成的 id 不带任何前缀。
fn generate_trace_id() -> String {
    uuid::Uuid::new_v4().simple().to_string()
}

pub async fn web_filter(State(port): State<u16>, request: Request, next: Next) -> Response {
    // 借读请求头要先结束借用，后面才能把 request 移动去改 URI。
    let (trace_id, has_origin) = {
        let headers = request.headers();
        // Java: `traceId != null && !traceId.trim().isEmpty()` 才沿用，否则新生成。
        let incoming = headers
            .get(TRACE_ID)
            .and_then(|value| value.to_str().ok())
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .map(str::to_string);
        let trace_id = incoming.unwrap_or_else(generate_trace_id);
        // Spring 的 CorsFilter 只在请求带 Origin 时才回显来源相关头。
        (trace_id, headers.contains_key("origin"))
    };

    let method = request.method().as_str().to_string();
    let method_value = request.method().clone();
    // Java 记的是容器收到的原始 URI —— 尾斜杠重写前的路径。
    let path = request
        .extensions()
        .get::<OriginalPath>()
        .map(|path| path.0.clone())
        .unwrap_or_else(|| request.uri().path().to_string());
    let ip = client_ip(
        request.headers(),
        request
            .extensions()
            .get::<ConnectInfo<SocketAddr>>()
            .map(|info| info.0),
    );
    let trace_for_log = trace_id.clone();
    let started = Instant::now();

    // Java: TraceIdFilter 在 MDC 里放 traceId，所有业务日志都带它；
    // 同时绑定本请求的 Servlet 逻辑线程名（http-nio-<port>-exec-<n>）。
    let response = logging::with_request_context(trace_id.clone(), port, async move {
        // Java: TraceIdFilter 的 `catch (RuntimeException)` 分支 —— 未捕获异常也要落日志。
        // Rust 的 panic 等价于逃出业务层的 RuntimeException；在这里 catch 住，
        // web_filter 才拿得到响应并继续写 [请求完成]/[服务器错误响应]。
        let outcome = std::panic::AssertUnwindSafe(next.run(request))
            .catch_unwind()
            .await;
        let (response, panic) = match outcome {
            Ok(response) => (response, None),
            Err(payload) => {
                let captured = logging::take_panic().unwrap_or_else(|| {
                    (logging::panic_payload_text(&*payload), None)
                });
                let page = crate::error::internal_error_page(&method_value, &path);
                (page, Some(captured))
            }
        };
        let cost = started.elapsed().as_millis();
        let status = response.status().as_u16();
        if let Some((message, backtrace)) = panic.as_ref() {
            let throwable = logging::PanicThrowable {
                message: message.as_str(),
                backtrace: backtrace.as_ref(),
            };
            tracing::error!(
                target: TRACE_FILTER_TARGET,
                exception = %throwable,
                "[未捕获异常] TraceId={}, Path={}, 异常信息: {}",
                trace_for_log,
                path,
                message
            );
        }
        log_trace_filter(&method, &path, &ip, status, cost, &trace_for_log);
        response
    })
    .await;

    let mut response = response;
    let out = response.headers_mut();

    let value = HeaderValue::from_str(&trace_id).unwrap_or_else(|_| HeaderValue::from_static("0"));
    out.insert(HeaderName::from_static(TRACE_ID), value);
    // Java: SecurityConfig 只禁用了 cacheControl 与 frameOptions，这两个默认头仍在。
    out.insert(
        HeaderName::from_static("x-content-type-options"),
        HeaderValue::from_static("nosniff"),
    );
    out.insert(
        HeaderName::from_static("x-xss-protection"),
        HeaderValue::from_static("1; mode=block"),
    );

    // Java: CorsFilter 写 `Vary: Origin`；tower-http 写的是三个候选头，这里照抄 Java。
    out.insert(VARY, HeaderValue::from_static("Origin"));
    if !has_origin {
        out.remove(ACCESS_CONTROL_ALLOW_CREDENTIALS);
        out.remove(ACCESS_CONTROL_ALLOW_ORIGIN);
    }
    // axum 的路由层会在所有层之外补 `Allow`（方法不匹配/预检时），Java 从不发这个头。
    out.remove(ALLOW);
    // Java 把请求头列表按 ", " 拼接回显，tower-http 是原样透传。
    if let Some(text) = out.get(ALLOW_HEADERS).and_then(|value| value.to_str().ok()) {
        let joined = text
            .split(',')
            .map(str::trim)
            .filter(|item| !item.is_empty())
            .collect::<Vec<_>>()
            .join(", ");
        if let Ok(value) = HeaderValue::from_str(&joined) {
            out.insert(HeaderName::from_static(ALLOW_HEADERS), value);
        }
    }
    response
}

/// Java: `TraceIdFilter.logResponse` + `doFilter.finally` 的慢请求告警。
fn log_trace_filter(method: &str, path: &str, ip: &str, status: u16, cost: u128, trace_id: &str) {
    if status >= 500 {
        tracing::error!(
            target: TRACE_FILTER_TARGET,
            "[服务器错误响应] Path={}, Status={}, 耗时={}ms, TraceId={}, IP={}",
            path,
            status,
            cost,
            trace_id,
            ip
        );
    } else if status >= 400 {
        tracing::warn!(
            target: TRACE_FILTER_TARGET,
            "[客户端错误响应] Path={}, Status={}, 耗时={}ms, TraceId={}, IP={}",
            path,
            status,
            cost,
            trace_id,
            ip
        );
    } else {
        tracing::info!(
            target: TRACE_FILTER_TARGET,
            "[请求完成] Path={}, Status={}, 耗时={}ms, TraceId={}",
            path,
            status,
            cost,
            trace_id
        );
    }
    if cost >= SLOW_REQUEST_MILLIS {
        tracing::warn!(
            target: TRACE_FILTER_TARGET,
            "[慢请求告警] Path={}, 耗时={}ms, Method={}, IP={}, TraceId={}",
            path,
            cost,
            method,
            ip,
            trace_id
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn trace_id_is_32_lowercase_hex() {
        let id = generate_trace_id();
        assert_eq!(id.len(), 32, "{id}");
        assert!(id.chars().all(|c| c.is_ascii_hexdigit()));
        assert!(!id.contains('-'));
    }

    /// Java: `TRACE_ID_PREFIX` 是空串，所以生成的 id 不带任何前缀。
    #[test]
    fn blank_incoming_trace_id_falls_back_to_generated() {
        let blank = Some("   ".to_string()).map(|value| value.trim().to_string());
        let kept = blank.filter(|value| !value.is_empty());
        assert!(kept.is_none());
    }

    #[test]
    fn allow_headers_are_rejoined_like_spring() {
        let text = "authorization,content-type";
        let joined = text
            .split(',')
            .map(str::trim)
            .filter(|item| !item.is_empty())
            .collect::<Vec<_>>()
            .join(", ");
        assert_eq!(joined, "authorization, content-type");
    }

    async fn boom() -> &'static str {
        panic!("boom")
    }

    /// Java: `TraceIdFilter.logResponse` 覆盖所有响应。
    /// 404（容器 /error）、405（GlobalExceptionHandler 转 200）、panic（逃出业务层的 RuntimeException）
    /// 都必须落一条完成日志，不能像以前那样绕过 web_filter。
    #[tokio::test]
    async fn every_response_path_is_logged() {
        use axum::routing::get;
        use tower::ServiceExt;
        use tracing_subscriber::layer::SubscriberExt;

        static PANIC_HOOK: std::sync::Once = std::sync::Once::new();
        PANIC_HOOK.call_once(logging::install_panic_hook);

        let dir = tempfile::tempdir().expect("tempdir");
        // 用一个不会触发滚动的上限：panic 的 throwable 带栈帧，1024 字节会切文件。
        let handle = crate::logging::start_appender(dir.path(), "sys-info", true, u64::MAX, 60)
            .expect("start");
        let layer = tracing_subscriber::fmt::layer()
            .event_format(crate::logging::JavaLogFormat {
                console: false,
                logger_width: 36,
                slow_sql_threshold_ms: 1000,
            })
            .with_writer(handle.writer())
            .with_ansi(false);
        let subscriber = tracing_subscriber::registry().with(layer);
        let guard = tracing::subscriber::set_default(subscriber);

        const PORT: u16 = 9989;
        // 与 build_router 相同的装配顺序：fallback 先装好，再统一 layer。
        let router = axum::Router::new()
            .route("/only-get", get(|| async { "ok" }))
            .route("/boom", get(boom))
            .with_state(PORT)
            .fallback(|request: axum::extract::Request| async move {
                crate::error::not_found_response(request.method(), request.uri().path())
            })
            .layer(axum::middleware::from_fn(crate::method_not_allowed_mapper))
            .layer(axum::middleware::from_fn_with_state(PORT, web_filter));

        let request = |method: &str, uri: &str| {
            axum::http::Request::builder()
                .method(method)
                .uri(uri)
                .body(axum::body::Body::empty())
                .expect("request")
        };

        let not_found = router
            .clone()
            .oneshot(request("GET", "/nope"))
            .await
            .expect("404");
        assert_eq!(not_found.status(), axum::http::StatusCode::NOT_FOUND);

        let method_not_allowed = router
            .clone()
            .oneshot(request("POST", "/only-get"))
            .await
            .expect("405");
        assert_eq!(method_not_allowed.status(), axum::http::StatusCode::OK);

        let panicked = router
            .clone()
            .oneshot(request("GET", "/boom"))
            .await
            .expect("panic");
        assert_eq!(
            panicked.status(),
            axum::http::StatusCode::INTERNAL_SERVER_ERROR
        );

        drop(guard);
        drop(handle);
        let files: Vec<_> = std::fs::read_dir(dir.path())
            .expect("read dir")
            .flatten()
            .map(|entry| entry.path())
            .collect();
        let text = std::fs::read_to_string(&files[0]).expect("read log");
        // 404: Java 的 TraceIdFilter 走 4xx 分支。
        assert!(
            text.contains("[客户端错误响应] Path=/nope, Status=404"),
            "{text}"
        );
        // 405: GlobalExceptionHandler 把方法不支持转成 200，完成日志是 INFO。
        assert!(
            text.contains("[请求完成] Path=/only-get, Status=200"),
            "{text}"
        );
        // panic: 先按 TraceIdFilter 的 RuntimeException 分支记 [未捕获异常] + throwable，
        // 再补一条 500 的完成日志。
        assert!(text.contains("Path=/boom"), "{text}");
        assert!(text.contains("异常信息: boom"), "{text}");
        assert!(text.contains("\npanic: boom"), "{text}");
        assert!(text.contains("\n\tat "), "{text}");
        assert!(
            text.contains("[服务器错误响应] Path=/boom, Status=500"),
            "{text}"
        );
    }
}
