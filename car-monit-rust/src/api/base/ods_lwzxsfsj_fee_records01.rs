// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java
//       ruoyi-system/.../base/service/forest/HttpOdsLwzxsfsjFeeRecords01Service.java
// 职责: 基础-收费流水（远端查询 + 字典/路段缓存补全 + 导出）。
// 对应关系: Forest TableDataInfo -> page_from_value；导出模板列 -> 标准工作簿。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;
use crate::task::remote;

use axum::Extension;

/// Java: `CommonUtil.isNull` —— null 变空串并 trim。
fn is_null(value: Option<&Value>) -> String {
    match value {
        None | Some(Value::Null) => String::new(),
        Some(Value::String(text)) => text.trim().to_string(),
        Some(other) => other.to_string().trim().to_string(),
    }
}

fn is_blank(text: &str) -> bool {
    text.trim().is_empty()
}

/// 收集远端查询参数（Java 会先补 pageNum/pageSize；sectionCodeStr 含 all 时清空）。
fn remote_query(params: &HashMap<String, String>) -> Vec<(String, String)> {
    let mut forwarded = params.clone();
    forwarded.entry("pageNum".to_string()).or_insert_with(|| "1".to_string());
    forwarded.entry("pageSize".to_string()).or_insert_with(|| "10".to_string());

    // Java: deleteEnd(sectionCodeStr).indexOf("all") > -1 -> sectionCodeStr = ""。
    let section_code = params
        .get("sectionCodeStr")
        .map(|value| value.trim().trim_end_matches(',').to_string())
        .unwrap_or_default();
    let forwarded = if section_code.contains("all") {
        forwarded
            .into_iter()
            .map(|(key, value)| {
                if key == "sectionCodeStr" {
                    (key, String::new())
                } else {
                    (key, value)
                }
            })
            .collect()
    } else {
        forwarded
    };
    remote::owned_params(&forwarded)
}

/// Java: `sectionMap` 来自 `section_list` 缓存。
async fn section_display(state: &AppState) -> HashMap<String, (String, String)> {
    let mut map = HashMap::new();
    if let Ok(list) = state.redis.get_list::<Value>("section_list").await {
        for item in list {
            let code = is_null(item.get("sectionCode"));
            let name = is_null(item.get("sectionName"));
            let road = is_null(item.get("roadName"));
            map.entry(code).or_insert((name, road));
        }
    }
    map
}

/// 列表/导出共用的字段翻译。
async fn enrich(state: &AppState, rows: &mut [Value], with_passstate: bool) -> Result<(), AppError> {
    let plate_color = support::dict_map(&state.db, "plate_color").await?;
    let car_type = support::dict_map(&state.db, "car_type_old").await?;
    let car_vehicle = support::dict_map(&state.db, "car_vehicle_old").await?;
    let passstate = if with_passstate {
        support::dict_map(&state.db, "passstate").await?
    } else {
        HashMap::new()
    };
    let sections = section_display(state).await;

    for row in rows {
        let Some(object) = row.as_object_mut() else { continue };

        let plate = is_null(object.get("plateColor"));
        if !is_blank(&plate) {
            if let Some(label) = plate_color.get(&plate) {
                if !is_blank(label) {
                    let plate_no = is_null(object.get("vehicleplate"));
                    object.insert(
                        "vehicleplate".to_string(),
                        Value::String(format!("{plate_no}_{label}")),
                    );
                }
            }
        }

        let fee_type = is_null(object.get("feevehicletype"));
        if !is_blank(&fee_type) {
            let label = car_type.get(&fee_type).cloned().unwrap_or_default();
            object.insert("feevehicletype".to_string(), Value::String(label));
        }

        let vehicle_class = is_null(object.get("vehicleclass"));
        if !is_blank(&vehicle_class) {
            let label = car_vehicle.get(&vehicle_class).cloned().unwrap_or_default();
            object.insert("vehicleclass".to_string(), Value::String(label));
        }

        let success = object
            .get("fee")
            .and_then(|fee| match fee {
                Value::Number(number) => number.as_f64(),
                Value::String(text) => text.parse().ok(),
                _ => None,
            })
            .map(|fee| fee > 0.0)
            .unwrap_or(false);
        object.insert(
            "chargeStatus".to_string(),
            Value::String(if success { "成功" } else { "失败" }.to_string()),
        );
        object.insert("fee".to_string(), Value::Null);

        let section_code = is_null(object.get("sectionCodeStr"));
        if !is_blank(&section_code) {
            if let Some((name, road)) = sections.get(&section_code) {
                object.insert("sectionName".to_string(), Value::String(name.clone()));
                object.insert("roadname".to_string(), Value::String(road.clone()));
            }
        }

        if with_passstate {
            let value = is_null(object.get("passstate"));
            let label = passstate.get(&value).cloned().unwrap_or_default();
            object.insert("passstate".to_string(), Value::String(label));
        }
    }
    Ok(())
}

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let query = support::query_map(&raw);
    support::query_log(&state.db, &user, &support::query_json(&query), "3", "1").await?;

    let forwarded = remote_query(&query);

    let start = query.get("inApplyTime1").map(|value| !is_blank(value)).unwrap_or(false);
    let end = query.get("inApplyTime2").map(|value| !is_blank(value)).unwrap_or(false);
    if !(start && end) {
        // 时间段必填：缺失时返回空表。
        return Ok(TableDataInfo::new(0, Vec::new()));
    }

    let value = remote::get_json_owned(&state, "/base/feerecords/list", &forwarded).await?;
    let mut page = remote::page_from_value(&value);
    enrich(&state, &mut page.rows, false).await?;
    Ok(page)
}

async fn export(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let query = support::query_map(&raw);
    support::query_log(&state.db, &user, &support::query_json(&query), "3", "2").await?;

    let start = query.get("inApplyTime1").map(|value| !is_blank(value)).unwrap_or(false);
    let end = query.get("inApplyTime2").map(|value| !is_blank(value)).unwrap_or(false);
    if !(start && end) {
        // Java 模板导出即使没有数据也会写出表头工作簿。
        return support::export_download("基础-收费流水数据", &[], &[]);
    }

    let forwarded = remote_query(&query);
    let value = remote::get_json_owned(&state, "/base/feerecords/listToExport", &forwarded).await?;
    let mut rows = match value {
        Value::Array(items) => items,
        Value::Object(mut object) => object
            .remove("data")
            .and_then(|data| data.as_array().cloned())
            .unwrap_or_default(),
        _ => Vec::new(),
    };
    enrich(&state, &mut rows, true).await?;

    let headers = [
        "路线名称", "路段名称", "车牌号", "轴数", "门架", "计费交易时间", "通行状态", "交易结果",
        "车型", "车种", "通行ID", "驶入时间",
    ]
    .map(str::to_string);
    let fields = [
        "roadname", "sectionName", "vehicleplate", "axlecount", "gantryName", "transtimeStr",
        "passstate", "chargeStatus", "feevehicletype", "vehicleclass", "passid", "entimeStr",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_download("基础-收费流水数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let path = format!("/base/feerecords/{}", urlencoding(&big_id));
    let value = remote::get_json_owned(&state, &path, &[]).await?;
    Ok(AjaxResult::success_data(value))
}

fn urlencoding(value: &str) -> String {
    url::form_urlencoded::byte_serialize(value.as_bytes()).collect()
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/feerecords/list",
            meta::get_route("/base/feerecords/list", Some("base:feerecords:list"), None, list),
        )
        .route(
            "/base/feerecords/export",
            meta::get_route(
                "/base/feerecords/export",
                Some("base:feerecords:list"),
                None,
                export,
            ),
        )
        .route(
            "/base/feerecords/{bigId}",
            meta::get_route("/base/feerecords/{bigId}", None, None, get_info),
        )
}
