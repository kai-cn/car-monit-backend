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

use crate::common::utils::client_ip;
use crate::logging;
use crate::state::AppState;

/// Java: `TraceIdFilter.TRACE_ID_HEADER`（配置项 `monitor.trace-id-header` 的默认值）。
const TRACE_ID: &str = "x-trace-id";
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

pub async fn web_filter(State(state): State<AppState>, request: Request, next: Next) -> Response {
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
    let path = request.uri().path().to_string();
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
    let port = state.settings.server.port;
    let response = logging::with_request_context(trace_id.clone(), port, async move {
        let response = next.run(request).await;
        let cost = started.elapsed().as_millis();
        let status = response.status().as_u16();
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
}
