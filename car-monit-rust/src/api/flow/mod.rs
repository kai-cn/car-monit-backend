// Java 切片: flow —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod flow_apply_info;
pub mod shared;
pub mod flow_current_node;
pub mod flow_list;
pub mod flow_message_dispose;
pub mod flow_message_info;
pub mod flow_name;
pub mod flow_template;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(flow_apply_info::routes());
    router = router.merge(flow_current_node::routes());
    router = router.merge(flow_list::routes());
    router = router.merge(flow_message_dispose::routes());
    router = router.merge(flow_message_info::routes());
    router = router.merge(flow_name::routes());
    router = router.merge(flow_template::routes());
    router
}
