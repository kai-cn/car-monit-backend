// Java 切片: common —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod common;
pub mod down_template;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(common::routes());
    router = router.merge(down_template::routes());
    router
}
