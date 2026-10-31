// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailTracksController.java
//       ruoyi-system/src/main/resources/mapper/base/ZdataTrailTracksMapper.xml
// 职责: 轨迹数据只读查询。
// 对应关系: selectZdataTrailTracksList/ById -> SPEC（日期过滤沿用 STR_TO_DATE）。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.uuid, t.type, t.point_count, t.plate_key, t.enter_time, t.exit_time, \
             t.trail_points, t.create_time, t.enter_locationcode, t.exit_locationcode, \
             t.track_josn, t.enaxlecount, t.entolllaneid, t.entollstationid, \
             t.entollstationname, t.envehicleclass, t.envehicleid, t.envehicletype, t.enweight, \
             t.extolllaneid, t.extollstationid, t.extollstationname, t.exvehicleclass, \
             t.exvehicleid, t.exvehicletype, t.exweight, t.start_lon, t.strat_lat, t.end_lon, \
             t.end_lat",
    from: "from zdata_trail_tracks t",
    filters: &[
        Filter::eq("uuid", "t.uuid"),
        Filter::eq("type", "t.type"),
        Filter::eq("pointCount", "t.point_count"),
        Filter::eq("plateKey", "t.plate_key"),
        Filter::eq("enterTime", "t.enter_time"),
        Filter::eq("exitTime", "t.exit_time"),
        Filter::eq("trailPoints", "t.trail_points"),
        Filter::eq("carNo", "t.plate_key"),
        Filter::raw("applyTime1", " and t.enter_time >= STR_TO_DATE(?, '%Y-%m-%d')"),
        Filter::raw(
            "applyTime2",
            " and t.enter_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)",
        ),
    ],
    extra_where: "",
    order_by: "t.enter_time desc",
    id_column: "t.uuid",
};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/trailtracks/list",
            meta::get_route("/base/trailtracks/list", None, None, list),
        )
        .route(
            "/base/trailtracks/{uuid}",
            meta::get_route("/base/trailtracks/{uuid}", None, None, get_info),
        )
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn get_info(
    State(state): State<AppState>,
    Path(uuid_value): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &uuid_value).await?,
    ))
}
