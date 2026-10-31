// Java 切片: quartz —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod job;
pub mod job_log;
pub mod registry;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(job::routes());
    router = router.merge(job_log::routes());
    router
}
