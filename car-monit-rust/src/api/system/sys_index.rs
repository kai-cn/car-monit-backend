// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexController.java
// 职责: 首页提示语。
// 对应关系: @RequestMapping("/") -> 纯文本响应（StringHttpMessageConverter）。

use axum::http::header;
use axum::response::{IntoResponse, Response};
use axum::Router;

use crate::api::meta;
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    // Java: @RequestMapping("/") —— 不限 method（附录 B 列 5 个方法）。
    Router::new().route(
        "/",
        meta::get_route("/", None, None, index)
            .merge(meta::post_route("/", None, None, index))
            .merge(meta::put_route("/", None, None, index))
            .merge(meta::delete_route("/", None, None, index))
            .merge(meta::patch_route("/", None, None, index)),
    )
}

async fn index(state: axum::extract::State<AppState>) -> Response {
    // Java: StringUtils.format("欢迎使用{}后台管理框架，请通过前端地址访问。", ruoyiConfig.getName())
    let body = format!(
        "欢迎使用{}后台管理框架，请通过前端地址访问。",
        state.settings.ruoyi.name
    );
    (
        [(header::CONTENT_TYPE, "text/plain;charset=UTF-8")],
        body,
    )
        .into_response()
}
