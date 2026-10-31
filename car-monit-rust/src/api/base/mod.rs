// Java 切片: base —— 各控制器模块的路由汇总。

use axum::Router;

use crate::state::AppState;

pub mod base_config_service_area;
pub mod car_warning_config;
pub mod cdc;
pub mod dwd_lczt_fwqjcxx;
pub mod dwd_lczt_sfsjcxx;
pub mod dwd_lczt_sfzjcxx;
pub mod geometry;
pub mod ods_cxzt_fwqclls;
pub mod ods_lwzxsfsj_fee_gantry_fusion01;
pub mod ods_lwzxsfsj_fee_records01;
pub mod ods_lwzxsfsj_fee_station_enter01;
pub mod ods_lwzxsfsj_fee_station_exit01;
pub mod ods_rt_szdn_snapshot_flow_addcode;
pub mod ods_rt_szdn_snapshot_flow_provcapture_addcode;
pub mod ods_rt_szdn_snapshot_flow_stationcapture_addcode;
pub mod ods_szdn_gantry;
pub mod ods_szdn_gantry_ip;
pub mod ods_szdn_province_border_vehicle_weight_newstructure;
pub mod ods_szdn_section;
pub mod ods_szdn_toll;
pub mod ods_szdn_toll_station_ip;
pub mod ods_yhgl_vbase_org;
pub mod zdata_location_dict;
pub mod zdata_trail_fitting;
pub mod zdata_trail_tracks;

pub fn routes() -> Router<AppState> {
    let mut router = Router::new();
    router = router.merge(base_config_service_area::routes());
    router = router.merge(car_warning_config::routes());
    router = router.merge(cdc::routes());
    router = router.merge(dwd_lczt_fwqjcxx::routes());
    router = router.merge(dwd_lczt_sfsjcxx::routes());
    router = router.merge(dwd_lczt_sfzjcxx::routes());
    router = router.merge(geometry::routes());
    router = router.merge(ods_cxzt_fwqclls::routes());
    router = router.merge(ods_lwzxsfsj_fee_gantry_fusion01::routes());
    router = router.merge(ods_lwzxsfsj_fee_records01::routes());
    router = router.merge(ods_lwzxsfsj_fee_station_enter01::routes());
    router = router.merge(ods_lwzxsfsj_fee_station_exit01::routes());
    router = router.merge(ods_rt_szdn_snapshot_flow_addcode::routes());
    router = router.merge(ods_rt_szdn_snapshot_flow_provcapture_addcode::routes());
    router = router.merge(ods_rt_szdn_snapshot_flow_stationcapture_addcode::routes());
    router = router.merge(ods_szdn_gantry::routes());
    router = router.merge(ods_szdn_gantry_ip::routes());
    router = router.merge(ods_szdn_province_border_vehicle_weight_newstructure::routes());
    router = router.merge(ods_szdn_section::routes());
    router = router.merge(ods_szdn_toll::routes());
    router = router.merge(ods_szdn_toll_station_ip::routes());
    router = router.merge(ods_yhgl_vbase_org::routes());
    router = router.merge(zdata_location_dict::routes());
    router = router.merge(zdata_trail_fitting::routes());
    router = router.merge(zdata_trail_tracks::routes());
    router
}
