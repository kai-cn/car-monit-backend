// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollStationIpController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml
// 职责: 收费站 IP 只读查询。
// 对应关系: selectOdsSzdnTollStationIpList/ById -> SPEC。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.toll_code, t.toll_name, t.org_code, t.ip, t.brand",
    from: "from ods_szdn_toll_station_ip t",
    filters: &[
        Filter::eq("tollCode", "t.toll_code"),
        Filter::like("tollName", "t.toll_name"),
        Filter::eq("orgCode", "t.org_code"),
        Filter::eq("ip", "t.ip"),
        Filter::eq("brand", "t.brand"),
    ],
    extra_where: "",
    order_by: "t.id",
    id_column: "t.id",
};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/tollStationIp/list",
            meta::get_route("/base/tollStationIp/list", None, None, list),
        )
        .route(
            "/base/tollStationIp/{id}",
            meta::get_route("/base/tollStationIp/{id}", None, None, get_info),
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
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id).await?,
    ))
}
