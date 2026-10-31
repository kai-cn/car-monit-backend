// Java 切片: system —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod sys_config;
pub mod sys_dept;
pub mod sys_dict_data;
pub mod sys_dict_type;
pub mod sys_file;
pub mod sys_index;
pub mod sys_index_menu;
pub mod sys_menu;
pub mod sys_notice;
pub mod sys_post;
pub mod sys_profile;
pub mod sys_role;
pub mod sys_upgrade_info;
pub mod sys_user;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(sys_config::routes());
    router = router.merge(sys_dept::routes());
    router = router.merge(sys_dict_data::routes());
    router = router.merge(sys_dict_type::routes());
    router = router.merge(sys_file::routes());
    router = router.merge(sys_index::routes());
    router = router.merge(sys_index_menu::routes());
    router = router.merge(sys_menu::routes());
    router = router.merge(sys_notice::routes());
    router = router.merge(sys_post::routes());
    router = router.merge(sys_profile::routes());
    router = router.merge(sys_role::routes());
    router = router.merge(sys_upgrade_info::routes());
    router = router.merge(sys_user::routes());
    router
}
