// Java 切片: monitor —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod cache;
pub mod server;
pub mod sys_logininfor;
pub mod sys_operlog;
pub mod sys_user_online;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(cache::routes());
    router = router.merge(server::routes());
    router = router.merge(sys_logininfor::routes());
    router = router.merge(sys_operlog::routes());
    router = router.merge(sys_user_online::routes());
    router
}
