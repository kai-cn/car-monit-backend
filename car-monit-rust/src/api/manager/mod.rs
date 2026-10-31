// Java 切片: manager —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod bigscreen;
pub mod buss_test;
pub mod car_aduit_free;
pub mod car_confim_free;
pub mod car_except_record;
pub mod car_fee_record;
pub mod car_info;
pub mod car_query_log;
pub mod car_route_detail;
pub mod car_route_info;
pub mod car_split_record;
pub mod car_suspicious_back;
pub mod car_suspicious_check;
pub mod car_suspicious;
pub mod car_track_info;
pub mod car_warning_info;
pub mod car_warning_rule;
pub mod car_white_info;
pub mod gantry_car;
pub mod gantry_trade_info;
pub mod shared;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(bigscreen::routes());
    router = router.merge(buss_test::routes());
    router = router.merge(car_aduit_free::routes());
    router = router.merge(car_confim_free::routes());
    router = router.merge(car_except_record::routes());
    router = router.merge(car_fee_record::routes());
    router = router.merge(car_info::routes());
    router = router.merge(car_query_log::routes());
    router = router.merge(car_route_detail::routes());
    router = router.merge(car_route_info::routes());
    router = router.merge(car_split_record::routes());
    router = router.merge(car_suspicious_back::routes());
    router = router.merge(car_suspicious_check::routes());
    router = router.merge(car_suspicious::routes());
    router = router.merge(car_track_info::routes());
    router = router.merge(car_warning_info::routes());
    router = router.merge(car_warning_rule::routes());
    router = router.merge(car_white_info::routes());
    router = router.merge(gantry_car::routes());
    router = router.merge(gantry_trade_info::routes());
    router
}
