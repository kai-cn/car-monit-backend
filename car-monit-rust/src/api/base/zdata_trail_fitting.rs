// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailFittingController.java
//       ruoyi-system/src/main/resources/mapper/base/ZdataTrailFittingMapper.xml
// 职责: 车辆出入口拟合轨迹只读查询。
// 对应关系: selectZdataTrailFittingList/ById -> SPEC（列表固定 del_flag='0'）。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.cid, t.enaxlecount, t.entime, t.entolllaneid, t.entollstationid, \
             t.entollstationname, t.envehicleclass, t.envehicleid, t.envehicletype, t.enweight, \
             t.extime, t.extolllaneid, t.extollstationid, t.extollstationname, t.exvehicleclass, \
             t.exvehicleid, t.exvehicletype, t.exweight, t.trailpoints",
    from: "from zdata_trail_fitting t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("enaxlecount", "t.enaxlecount"),
        Filter::eq("entime", "t.entime"),
        Filter::eq("entolllaneid", "t.entolllaneid"),
        Filter::eq("entollstationid", "t.entollstationid"),
        Filter::like("entollstationname", "t.entollstationname"),
        Filter::eq("envehicleclass", "t.envehicleclass"),
        Filter::eq("envehicleid", "t.envehicleid"),
        Filter::eq("envehicletype", "t.envehicletype"),
        Filter::eq("enweight", "t.enweight"),
        Filter::eq("extime", "t.extime"),
        Filter::eq("extolllaneid", "t.extolllaneid"),
        Filter::eq("extollstationid", "t.extollstationid"),
        Filter::like("extollstationname", "t.extollstationname"),
        Filter::eq("exvehicleclass", "t.exvehicleclass"),
        Filter::eq("exvehicleid", "t.exvehicleid"),
        Filter::eq("exvehicletype", "t.exvehicletype"),
        Filter::eq("exweight", "t.exweight"),
        Filter::eq("trailpoints", "t.trailpoints"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "",
    id_column: "t.cid",
};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/fitting/list",
            meta::get_route("/base/fitting/list", None, None, list),
        )
        .route(
            "/base/fitting/{cid}",
            meta::get_route("/base/fitting/{cid}", None, None, get_info),
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
    Path(cid): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &cid).await?,
    ))
}
