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

use axum::http::Uri;
use axum::routing::{any, get};
use axum::Router;
use tower_http::cors::{AllowHeaders, AllowMethods, AllowOrigin, CorsLayer};
use tower_http::services::ServeDir;

use crate::error::not_found_response;
use crate::state::AppState;

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
async fn fallback(uri: Uri) -> axum::response::Response {
    not_found_response(uri.path())
}

/// 附录 B 的 501 条控制器端点 + 认证入口（不含 state/中间件，便于自检与复用）。
pub fn build_api_routes() -> Router<AppState> {
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

pub fn build_router(state: AppState) -> Router {
    let mut router = build_api_routes();

    if state.settings.app.health_endpoint_enabled {
        router = router.route("/health", get(api::health::health));
    }

    // Java: ResourcesConfig.addResourceHandlers —— /profile/** -> file:{profile}/
    router = router.nest_service(
        "/profile",
        ServeDir::new(state.settings.ruoyi.profile.clone()),
    );

    router
        .fallback(any(fallback))
        .with_state(state.clone())
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
        assert_eq!(expected.len(), 501, "基线端点数量应为 501");
    }

    fn shape(path: &str) -> String {
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
