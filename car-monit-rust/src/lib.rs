// 职责: 库入口 —— 模块声明与路由装配。
// 对应关系: Spring MVC 的 DispatcherServlet 注册 + Filter 链 -> axum Router + middleware。

pub mod api;
pub mod auth;
pub mod common;
pub mod config;
pub mod db;
pub mod domain;
pub mod error;
pub mod middleware;
pub mod repository;
pub mod response;
pub mod service;
pub mod state;
pub mod task;

use std::time::Duration;

use axum::response::IntoResponse;
use axum::routing::{any, get};
use axum::Router;
use tower_http::cors::{AllowHeaders, AllowMethods, AllowOrigin, CorsLayer};
use tower_http::services::ServeDir;

use crate::error::not_found_response;
use crate::state::AppState;

/// Java: `spring.servlet.multipart.max-request-size: 200MB`。
const MAX_REQUEST_BYTES: usize = 200 * 1024 * 1024;

/// Java: ResourcesConfig.corsFilter —— allowCredentials + allowedOriginPattern("*")
fn cors_layer() -> CorsLayer {
    CorsLayer::new()
        .allow_origin(AllowOrigin::mirror_request())
        .allow_credentials(true)
        .allow_methods(AllowMethods::mirror_request())
        // tower-http 不允许 allow_credentials=true 与 allow_headers=* 组合；
        // Java 的 allowedOriginPattern("*") 语义是反射请求头，这里用 mirror_request 等价实现。
        .allow_headers(AllowHeaders::mirror_request())
        .max_age(Duration::from_secs(1800))
}

/// Java: Spring Boot 默认 /error（未匹配路由）
async fn fallback(request: axum::extract::Request) -> axum::response::Response {
    let path = request.uri().path().to_string();
    not_found_response(request.method(), &path)
}

/// Java: 路径存在但方法不匹配时，Spring MVC 抛 HttpRequestMethodNotSupportedException，
/// 由 GlobalExceptionHandler 转成 HTTP 200 + `{"msg":"Request method 'POST' not supported","code":500}`；
/// axum 默认直接回 405 空响应体（还带 `Allow` 头），这里翻译成 Java 的形状。
/// 放在最内层：鉴权（外层）先失败的场景仍按 Java 返回 401/403。
async fn method_not_allowed_mapper(
    request: axum::extract::Request,
    next: axum::middleware::Next,
) -> axum::response::Response {
    let method = request.method().clone();
    let response = next.run(request).await;
    if response.status() == axum::http::StatusCode::METHOD_NOT_ALLOWED {
        // Java: 该响应由异常解析器写出，Content-Type 带 `;charset=UTF-8`，也没有 `Allow` 头。
        let mut response =
            crate::response::AjaxResult::error(format!("Request method '{method}' not supported"))
                .into_response();
        response.headers_mut().remove("allow");
        response.headers_mut().insert(
            axum::http::header::CONTENT_TYPE,
            axum::http::HeaderValue::from_static("application/json;charset=UTF-8"),
        );
        return response;
    }
    response
}

/// 附录 B 的 501 条控制器端点 + 认证入口（不含 state/中间件，便于自检与复用）。
/// 不包含 `/oss/**`：Java 的 `OssEndpoint` 只在 `oss.info=true` 时创建（见 `build_router`）。
fn api_routes_without_oss() -> Router<AppState> {
    use api::meta;
    let router = Router::new()
        .route(
            "/login",
            meta::post_route("/login", None, None, api::auth::login),
        )
        .route(
            "/captchaImage",
            meta::get_route("/captchaImage", None, None, api::captcha::get_code),
        )
        .route(
            "/getInfo",
            meta::get_route("/getInfo", None, None, api::auth::get_info),
        )
        .route(
            "/getRouters",
            meta::get_route("/getRouters", None, None, api::auth::get_routers),
        )
        // /logout 由 auth 中间件在鉴权前处理（LogoutFilter 语义）
        .route(
            "/logout",
            any(|| async { response::AjaxResult::success_msg("退出成功") }),
        )
        // Java 各切片控制器（附录 B 的 501 条端点）
        .merge(api::system::routes())
        .merge(api::monitor::routes())
        .merge(api::quartz::routes())
        .merge(api::tool::routes())
        .merge(api::common::routes())
        .merge(api::base::routes())
        .merge(api::manager::routes())
        .merge(api::flow::routes())
        .merge(api::generator::routes());
    router
}

/// 附录 B 的基线路由（含 `/oss/**`），供 `route_parity` 逐条对拍使用。
pub fn build_api_routes() -> Router<AppState> {
    api_routes_without_oss().merge(api::oss::routes())
}

pub fn build_router(state: AppState) -> Router {
    let mut router = api_routes_without_oss();
    // Java: `OssAutoConfiguration.ossEndpoint` 仅 `oss.info=true` 时创建 Bean；默认不注册。
    if state.settings.oss.info {
        router = router.merge(api::oss::routes());
    }

    if state.settings.app.health_endpoint_enabled {
        router = router.route("/health", get(api::health::health));
    }

    // Java: ResourcesConfig.addResourceHandlers —— /profile/** -> file:{profile}/
    router = router.nest_service(
        "/profile",
        ServeDir::new(state.settings.ruoyi.profile.clone()),
    );

    let router = router
        .fallback(any(fallback))
        .with_state(state.clone())
        // Java: spring.servlet.multipart.max-request-size: 200MB（单文件 40MB 在 handler 内校验）。
        .layer(axum::extract::DefaultBodyLimit::max(MAX_REQUEST_BYTES))
        // 方法不匹配先由路由层产出 405，这里立刻换成 Java 的响应体，再交给 @Log/鉴权之外层。
        .layer(axum::middleware::from_fn(method_not_allowed_mapper))
        // @PreAuthorize + @Log 元数据中间件（必须位于认证内侧）。
        .layer(axum::middleware::from_fn_with_state(
            state.clone(),
            api::meta::meta_middleware,
        ))
        .layer(axum::middleware::from_fn({
            let state = state.clone();
            move |request, next| {
                let state = state.clone();
                async move { middleware::auth::auth_middleware(state, request, next).await }
            }
        }))
        // CORS 必须在最外层：预检请求在鉴权之前响应。
        .layer(cors_layer())
        // TraceId / 安全头 / CORS 头写法：Java 的 Filter 在业务之前就写好了，401/404/405 也带。
        .layer(axum::middleware::from_fn(
            middleware::web_filter::web_filter,
        ));

    // Java: Spring Boot 2.x 默认 useTrailingSlashMatch —— `/x/` 也命中注册为 `/x` 的映射。
    // axum 的 `.layer()` 只包住各路由的 handler，改 URI 影响不到路由本身，
    // 所以只能在「按原样路由不到」之后削掉一个尾斜杠再路由一次。
    let retrier = router.clone();
    router.fallback(move |request: axum::extract::Request| {
        let retrier = retrier.clone();
        async move { retry_with_trimmed_trailing_slash(request, retrier).await }
    })
}

/// 尾斜杠重路由；削不动就直接给 Java 的 404 错误页。
async fn retry_with_trimmed_trailing_slash(
    mut request: axum::extract::Request,
    retrier: Router,
) -> axum::response::Response {
    use tower::ServiceExt;

    let path = request.uri().path().to_string();
    let Some(trimmed) = path.strip_suffix('/') else {
        return not_found_response(request.method(), &path);
    };
    if trimmed.is_empty() {
        return not_found_response(request.method(), &path);
    }
    let rebuilt = match request.uri().query() {
        Some(query) => format!("{trimmed}?{query}"),
        None => trimmed.to_string(),
    };
    let Ok(uri) = rebuilt.parse::<axum::http::Uri>() else {
        return not_found_response(request.method(), &path);
    };
    *request.uri_mut() = uri;
    match retrier.oneshot(request).await {
        Ok(response) => response,
        // Router 的 Error 是 Infallible。
        Err(err) => match err {},
    }
}

#[cfg(test)]
mod route_parity {
    use std::collections::HashSet;

    /// 附录 B（501 条）与 Rust 路由注册表按「method + 路径形状」对拍。
    /// 允许的额外路由：/logout（Spring Security 过滤器，不是控制器端点）。
    #[test]
    fn baseline_endpoints_are_registered() {
        // 构造路由 = 同时完成 meta 注册；若存在重叠路由会在此 panic。
        let _ = crate::build_api_routes();

        let baseline_text = include_str!("../docs/01-baseline/02-endpoints.md");
        let mut expected = HashSet::new();
        for line in baseline_text.lines() {
            let line = line.trim();
            if !line.starts_with('|') {
                continue;
            }
            let cells: Vec<&str> = line.trim_matches('|').split('|').map(str::trim).collect();
            if cells.len() < 3 {
                continue;
            }
            let method = cells[1];
            if !matches!(method, "GET" | "POST" | "PUT" | "DELETE" | "PATCH") {
                continue;
            }
            let path = cells[2].trim_matches('`').trim();
            if !path.starts_with('/') {
                continue;
            }
            expected.insert((method.to_string(), shape(path)));
        }

        let registered: HashSet<(String, String)> = crate::api::meta::registered()
            .into_iter()
            .map(|(method, path)| (method, shape(&path)))
            .collect();

        let mut missing: Vec<_> = expected.difference(&registered).cloned().collect();
        missing.sort();
        let mut extra: Vec<_> = registered
            .difference(&expected)
            .filter(|(_, path)| path != "/logout" && path != "/health")
            .cloned()
            .collect();
        extra.sort();

        assert!(
            missing.is_empty(),
            "以下基线端点未注册（{} 条）: {:?}",
            missing.len(),
            missing
        );
        assert!(
            extra.is_empty(),
            "以下路由不在基线中（{} 条）: {:?}",
            extra.len(),
            extra
        );
        assert_eq!(expected.len(), 510, "基线端点数量应为 510");
    }

    /// 形状归一：`{var}` 收成 `{}`，并按 Spring 的 `useTrailingSlashMatch` 削掉一个结尾斜杠
    /// （Java 的 `/oss/object/{b}/{o}/` 与 `/oss/object/{b}/{o}` 命中同一个映射）。
    fn shape(path: &str) -> String {
        let path = match path.strip_suffix('/') {
            Some(trimmed) if trimmed.len() > 1 => trimmed,
            _ => path,
        };
        let mut out = String::with_capacity(path.len());
        let mut in_param = false;
        for ch in path.chars() {
            match ch {
                '{' => {
                    in_param = true;
                    out.push('{');
                }
                '}' => {
                    in_param = false;
                    out.push('}');
                }
                _ if in_param => {}
                _ => out.push(ch),
            }
        }
        out
    }
}
