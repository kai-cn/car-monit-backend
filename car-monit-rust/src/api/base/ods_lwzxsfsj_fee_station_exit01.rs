// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java
//       ruoyi-system/.../base/service/forest/HttpOdsLwzxsfsjFeeStationExit01Service.java
// 职责: 收费站出口流水（转发 `<baseUrl>/base/feestationexit`）。
// 对应关系: Forest JSONObject -> get_json_owned；code != 200 抛 ServiceException。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;
use crate::task::remote;

/// Java Jackson 的 BaseLwzxsfsjFeeStationExit01 键序（远端透传后仍按实体声明顺序输出）。
const STATION_EXIT_KEYS: &[&str] = &[
    "axlecount",
    "transfee",
    "fee",
    "shift",
    "entolllanehex",
    "obutotaldiscountamount",
    "signstatus",
    "exvehicleid",
    "lanetype",
    "provincecount",
    "gradeLevel",
    "identification",
    "tac",
    "receivetime",
    "feeboardplay",
    "shortfee",
    "splitprovince",
    "discountfee",
    "provtranscount",
    "shortfeemileage",
    "transtype",
    "extime",
    "operid",
    "params",
    "bigId",
    "entolllaneid",
    "envehicletype",
    "spcrateversion",
    "mediano",
    "actualfeeclass",
    "envehicleid",
    "mediatype",
    "feerate",
    "entollstationid",
    "terminalno",
    "extolllaneid",
    "passid",
    "vehiclesignid",
    "vehiclesign",
    "exvehicletype",
    "entollstationname",
    "loadTime",
    "extollstationname",
    "exvehicleclass",
    "electricalpercentage",
    "transpaytype",
    "nocardcount",
    "identifyvehicleid",
    "feemileage",
    "entime",
    "payfee",
    "envehicleclass",
    "extollstationid",
    "obutotalamount",
    "exweight",
    "terminaltransno",
    "paytype",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    params
        .entry("pageNum".to_string())
        .or_insert_with(|| page.page_num.to_string());
    params
        .entry("pageSize".to_string())
        .or_insert_with(|| page.page_size.to_string());

    let value = remote::strip_nulls_owned(
        remote::get_json_owned(
            &state,
            "/base/feestationexit/list",
            &remote::owned_params(&params),
        )
        .await?,
    );
    let code = value
        .get("code")
        .and_then(Value::as_i64)
        .unwrap_or_default();
    if code != 200 {
        tracing::error!("交易流水数据获取异常：{value}");
        return Err(AppError::Service("获取数据异常,请联系管理员".to_string()));
    }
    let mut page = remote::page_from_value(&value);
    page.rows = support::reorder_rows(page.rows, STATION_EXIT_KEYS);
    Ok(page)
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let path = format!("/base/feestationexit/{}", urlencoding(&big_id));
    let value = remote::strip_nulls_owned(remote::get_json_owned(&state, &path, &[]).await?);
    Ok(AjaxResult::success_data(crate::response::java_ordered(
        &value,
    )))
}

fn urlencoding(value: &str) -> String {
    url::form_urlencoded::byte_serialize(value.as_bytes()).collect()
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/feestationexit/list",
            meta::get_route(
                "/base/feestationexit/list",
                Some("base:feestationexit:list"),
                None,
                list,
            ),
        )
        .route(
            "/base/feestationexit/{bigId}",
            meta::get_route("/base/feestationexit/{bigId}", None, None, get_info),
        )
}
