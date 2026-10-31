// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java
//       ruoyi-system/.../base/service/forest/HttpOdsLwzxsfsjFeeGantryFusion01Service.java
// 职责: 门架交易流水（转发 vehicleMonitor.baseUrl 远端服务）。
// 对应关系: Forest @Get -> task::remote::get_json_owned；本地 mapper 仅保留列定义。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;
use crate::task::remote;

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    // Java: pageNum/pageSize 为空时补 1/10。
    params.entry("pageNum".to_string()).or_insert_with(|| page.page_num.to_string());
    params.entry("pageSize".to_string()).or_insert_with(|| page.page_size.to_string());
    let value = remote::get_json_owned(&state, "/base/feeGantry/list", &remote::owned_params(&params))
        .await?;
    Ok(remote::page_from_value(&value))
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let path = format!("/base/feeGantry/{}", urlencoding(&big_id));
    let value = remote::get_json_owned(&state, &path, &[]).await?;
    Ok(AjaxResult::success_data(value))
}

fn urlencoding(value: &str) -> String {
    url::form_urlencoded::byte_serialize(value.as_bytes()).collect()
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/feeGantry/list",
            meta::get_route("/base/feeGantry/list", Some("base:feeGantry:list"), None, list),
        )
        .route(
            "/base/feeGantry/{bigId}",
            meta::get_route("/base/feeGantry/{bigId}", None, None, get_info),
        )
}
