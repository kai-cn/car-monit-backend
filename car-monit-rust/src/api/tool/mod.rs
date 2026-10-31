// Java 切片: tool —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod test;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(test::routes());
    router
}
