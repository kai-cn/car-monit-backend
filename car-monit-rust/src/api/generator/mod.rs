// Java 切片: generator —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod gen;
pub mod gen_link;
pub mod gen_render;
pub mod gen_zip;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(gen::routes());
    router
}
