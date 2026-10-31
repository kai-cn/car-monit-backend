// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsCxztFwqcllsController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsCxztFwqcllsMapper.xml
// 职责: 服务区车辆流水只读查询。
// 对应关系: selectOdsCxztFwqcllsList/ById -> SPEC。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.big_id, t.datauuid, t.targetpicurl, t.vehiclebrand, t.platepicurl, \
             t.rollvehiclestype, t.plateno, t.directionname, t.platetype, t.dangmark, \
             t.crosstime, t.axles, t.devicename, t.ipaddress, t.servicename, t.vehicletype, \
             t.load_time, t.grade_level",
    from: "from ods_cxzt_fwqclls t",
    filters: &[
        Filter::eq("bigId", "t.big_id"),
        Filter::eq("datauuid", "t.datauuid"),
        Filter::eq("targetpicurl", "t.targetpicurl"),
        Filter::eq("vehiclebrand", "t.vehiclebrand"),
        Filter::eq("platepicurl", "t.platepicurl"),
        Filter::eq("rollvehiclestype", "t.rollvehiclestype"),
        Filter::eq("plateno", "t.plateno"),
        Filter::like("directionname", "t.directionname"),
        Filter::eq("platetype", "t.platetype"),
        Filter::eq("dangmark", "t.dangmark"),
        Filter::eq("crosstime", "t.crosstime"),
        Filter::eq("axles", "t.axles"),
        Filter::like("devicename", "t.devicename"),
        Filter::eq("ipaddress", "t.ipaddress"),
        Filter::like("servicename", "t.servicename"),
        Filter::eq("vehicletype", "t.vehicletype"),
        Filter::eq("loadTime", "t.load_time"),
        Filter::eq("gradeLevel", "t.grade_level"),
    ],
    extra_where: "",
    order_by: "",
    id_column: "t.big_id",
};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/fwqclls/list",
            meta::get_route("/manager/fwqclls/list", Some("manager:fwqclls:list"), None, list),
        )
        .route(
            "/manager/fwqclls/{bigId}",
            meta::get_route("/manager/fwqclls/{bigId}", None, None, get_info),
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
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &big_id).await?,
    ))
}
