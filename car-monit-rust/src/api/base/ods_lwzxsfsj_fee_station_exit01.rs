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

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    params.entry("pageNum".to_string()).or_insert_with(|| page.page_num.to_string());
    params.entry("pageSize".to_string()).or_insert_with(|| page.page_size.to_string());

    let value =
        remote::get_json_owned(&state, "/base/feestationexit/list", &remote::owned_params(&params))
            .await?;
    let code = value.get("code").and_then(Value::as_i64).unwrap_or_default();
    if code != 200 {
        tracing::error!("交易流水数据获取异常：{value}");
        return Err(AppError::Service("获取数据异常,请联系管理员".to_string()));
    }
    Ok(remote::page_from_value(&value))
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let path = format!("/base/feestationexit/{}", urlencoding(&big_id));
    let value = remote::get_json_owned(&state, &path, &[]).await?;
    Ok(AjaxResult::success_data(value))
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
