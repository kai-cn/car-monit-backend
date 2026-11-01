// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationEnter01Controller.java
//       ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationEnter01Mapper.xml
// 职责: 收费站入口数据只读查询。
// 对应关系: selectOdsLwzxsfsjFeeStationEnter01List/ById -> SPEC。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, FieldFormat, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.big_id, t.cardid, t.electricalpercentage, t.enaxlecount, t.entime, \
             t.entolllanehex, t.entolllaneid, t.entollstationid, t.enweight, \
             t.identifyvehicleid, t.lanetype, t.mediatype, t.operid, t.operationmedia, t.params, \
             t.passid, t.receivetime, t.shift, t.signstatus, t.specialtype, t.tac, t.terminalno, \
             t.terminaltransno, t.transfee, t.transtype, t.vcount, t.vehicleclass, t.vehicleid, \
             t.vehiclesign, t.vehiclesignid, t.vehicletype, t.load_time, t.grade_level, t.cid",
    from: "from ods_lwzxsfsj_fee_station_enter_01 t",
    filters: &[
        Filter::eq("bigId", "t.big_id"),
        Filter::eq("cardid", "t.cardid"),
        Filter::eq("electricalpercentage", "t.electricalpercentage"),
        Filter::eq("enaxlecount", "t.enaxlecount"),
        Filter::eq("entime", "t.entime"),
        Filter::eq("entolllanehex", "t.entolllanehex"),
        Filter::eq("entolllaneid", "t.entolllaneid"),
        Filter::eq("entollstationid", "t.entollstationid"),
        Filter::eq("enweight", "t.enweight"),
        Filter::eq("identifyvehicleid", "t.identifyvehicleid"),
        Filter::eq("lanetype", "t.lanetype"),
        Filter::eq("mediatype", "t.mediatype"),
        Filter::eq("operid", "t.operid"),
        Filter::eq("operationmedia", "t.operationmedia"),
        Filter::eq("params", "t.params"),
        Filter::eq("passid", "t.passid"),
        Filter::eq("receivetime", "t.receivetime"),
        Filter::eq("shift", "t.shift"),
        Filter::eq("signstatus", "t.signstatus"),
        Filter::eq("specialtype", "t.specialtype"),
        Filter::eq("tac", "t.tac"),
        Filter::eq("terminalno", "t.terminalno"),
        Filter::eq("terminaltransno", "t.terminaltransno"),
        Filter::eq("transfee", "t.transfee"),
        Filter::eq("transtype", "t.transtype"),
        Filter::eq("vcount", "t.vcount"),
        Filter::eq("vehicleclass", "t.vehicleclass"),
        Filter::eq("vehicleid", "t.vehicleid"),
        Filter::eq("vehiclesign", "t.vehiclesign"),
        Filter::eq("vehiclesignid", "t.vehiclesignid"),
        Filter::eq("vehicletype", "t.vehicletype"),
        Filter::eq("loadTime", "t.load_time"),
        Filter::eq("gradeLevel", "t.grade_level"),
    ],
    extra_where: "",
    order_by: "t.big_id",
    id_column: "t.big_id",
};

// Java 实体这些字段是 LocalDate（只输出 yyyy-MM-dd），DB 是 datetime。
const FORMATS: &[(&str, FieldFormat)] = &[
    ("entime", FieldFormat::DateOnly),
    ("receivetime", FieldFormat::DateOnly),
    ("loadTime", FieldFormat::DateOnly),
];

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/feeStationEnter/list",
            meta::get_route("/base/feeStationEnter/list", None, None, list),
        )
        .route(
            "/base/feeStationEnter/{bigId}",
            meta::get_route("/base/feeStationEnter/{bigId}", None, None, get_info),
        )
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &big_id, FORMATS).await?,
    ))
}
