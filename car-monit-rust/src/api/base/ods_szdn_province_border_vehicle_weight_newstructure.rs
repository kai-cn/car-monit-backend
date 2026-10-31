// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnProvinceBorderVehicleWeightNewstructureController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.xml
// 职责: 省界称重只读查询。
// 对应关系: selectOdsSzdnProvinceBorderVehicleWeightNewstructureList/ById -> SPEC。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.dataSource, t.dataType, t.plateNo, t.siteId, t.location, t.driveNo, t.plateColor, \
             t.plateColorCode, t.plateType, t.plateTypeCode, t.vehicleColor, t.vehicleColorCode, \
             t.vehicleType, t.vehicleTypeCode, t.vehicleSpeed, t.isOverweight, t.axleNum, \
             t.overWeight, t.vehicleWeight, t.limitWeight, t.checkTimeUnix, t.checkTime, \
             t.axleModel, t.loadRate, t.axleArray, t.weighingImagesArry, t.load_time, \
             t.grade_level, t.datauuid, t.reserve1, t.reserve2, t.reserve3",
    from: "from ods_szdn_province_border_vehicle_weight_newstructure t",
    filters: &[
        Filter::eq("dataSource", "t.dataSource"),
        Filter::eq("dataType", "t.dataType"),
        Filter::eq("plateNo", "t.plateNo"),
        Filter::eq("siteId", "t.siteId"),
        Filter::eq("location", "t.location"),
        Filter::eq("driveNo", "t.driveNo"),
        Filter::eq("plateColor", "t.plateColor"),
        Filter::eq("plateColorCode", "t.plateColorCode"),
        Filter::eq("plateType", "t.plateType"),
        Filter::eq("plateTypeCode", "t.plateTypeCode"),
        Filter::eq("vehicleColor", "t.vehicleColor"),
        Filter::eq("vehicleColorCode", "t.vehicleColorCode"),
        Filter::eq("vehicleType", "t.vehicleType"),
        Filter::eq("vehicleTypeCode", "t.vehicleTypeCode"),
        Filter::eq("vehicleSpeed", "t.vehicleSpeed"),
        Filter::eq("isOverweight", "t.isOverweight"),
        Filter::eq("axleNum", "t.axleNum"),
        Filter::eq("overWeight", "t.overWeight"),
        Filter::eq("vehicleWeight", "t.vehicleWeight"),
        Filter::eq("limitWeight", "t.limitWeight"),
        Filter::eq("checkTimeUnix", "t.checkTimeUnix"),
        Filter::eq("checkTime", "t.checkTime"),
        Filter::eq("axleModel", "t.axleModel"),
        Filter::eq("loadRate", "t.loadRate"),
        Filter::eq("axleArray", "t.axleArray"),
        Filter::eq("weighingImagesArry", "t.weighingImagesArry"),
        Filter::eq("loadTime", "t.load_time"),
        Filter::eq("gradeLevel", "t.grade_level"),
        Filter::eq("datauuid", "t.datauuid"),
        Filter::eq("reserve1", "t.reserve1"),
        Filter::eq("reserve2", "t.reserve2"),
        Filter::eq("reserve3", "t.reserve3"),
    ],
    extra_where: "",
    order_by: "",
    id_column: "t.dataSource",
};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/vehicleweight/list",
            meta::get_route("/base/vehicleweight/list", None, None, list),
        )
        .route(
            "/base/vehicleweight/{dataSource}",
            meta::get_route("/base/vehicleweight/{dataSource}", None, None, get_info),
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
    Path(data_source): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &data_source).await?,
    ))
}
