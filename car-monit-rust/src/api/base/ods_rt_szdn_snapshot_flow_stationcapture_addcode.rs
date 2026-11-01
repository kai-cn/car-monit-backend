// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.xml
// 职责: 收费站抓拍只读查询。
// 对应关系: selectOdsRtSzdnSnapshotFlowStationcaptureAddcodeList/ById -> SPEC。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, FieldFormat, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.big_id, t.datasource, t.cameratype, t.deviceid, t.deviceip, t.tollcode, \
             t.tollname, t.orgcode, t.siteid, t.laneid, t.snapshottimeunix, t.snapshottime, \
             t.receivedtimeunix, t.receivedtime, t.platenumber, t.platecolorcode, t.platecolor, \
             t.platetypecode, t.platetype, t.plateconfidence, t.carbrand, t.carcolorcode, \
             t.carcolor, t.cartypecode, t.cartype, t.cardirectioncode, t.cardirection, \
             t.snappicturepath, t.loadtime, t.gradelevel, t.datauuid, t.maindirection, \
             t.maindirectionname, t.reserve3",
    from: "from ods_rt_szdn_snapshot_flow_stationcapture_addcode t",
    filters: &[
        Filter::eq("bigId", "t.big_id"),
        Filter::eq("datasource", "t.datasource"),
        Filter::eq("cameratype", "t.cameratype"),
        Filter::eq("deviceid", "t.deviceid"),
        Filter::eq("deviceip", "t.deviceip"),
        Filter::eq("tollcode", "t.tollcode"),
        Filter::like("tollname", "t.tollname"),
        Filter::eq("orgcode", "t.orgcode"),
        Filter::eq("siteid", "t.siteid"),
        Filter::eq("laneid", "t.laneid"),
        Filter::eq("snapshottimeunix", "t.snapshottimeunix"),
        Filter::eq("snapshottime", "t.snapshottime"),
        Filter::eq("receivedtimeunix", "t.receivedtimeunix"),
        Filter::eq("receivedtime", "t.receivedtime"),
        Filter::eq("platenumber", "t.platenumber"),
        Filter::eq("platecolorcode", "t.platecolorcode"),
        Filter::eq("platecolor", "t.platecolor"),
        Filter::eq("platetypecode", "t.platetypecode"),
        Filter::eq("platetype", "t.platetype"),
        Filter::eq("plateconfidence", "t.plateconfidence"),
        Filter::eq("carbrand", "t.carbrand"),
        Filter::eq("carcolorcode", "t.carcolorcode"),
        Filter::eq("carcolor", "t.carcolor"),
        Filter::eq("cartypecode", "t.cartypecode"),
        Filter::eq("cartype", "t.cartype"),
        Filter::eq("cardirectioncode", "t.cardirectioncode"),
        Filter::eq("cardirection", "t.cardirection"),
        Filter::eq("snappicturepath", "t.snappicturepath"),
        Filter::eq("loadtime", "t.loadtime"),
        Filter::eq("gradelevel", "t.gradelevel"),
        Filter::eq("datauuid", "t.datauuid"),
        Filter::eq("maindirection", "t.maindirection"),
        Filter::like("maindirectionname", "t.maindirectionname"),
        Filter::eq("reserve3", "t.reserve3"),
    ],
    extra_where: "",
    order_by: "t.big_id",
    id_column: "t.big_id",
};

// Java 实体这些字段为 LocalDate。
const FORMATS: &[(&str, FieldFormat)] = &[
    ("snapshottime", FieldFormat::DateOnly),
    ("receivedtime", FieldFormat::DateOnly),
    ("loadtime", FieldFormat::DateOnly),
];

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/stationcapture/list",
            meta::get_route("/base/stationcapture/list", None, None, list),
        )
        .route(
            "/base/stationcapture/{bigId}",
            meta::get_route("/base/stationcapture/{bigId}", None, None, get_info),
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
