// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java
//       ruoyi-system/.../base/service/enhanced/SnapshotFlowEnhancedService.java
//       ruoyi-system/.../base/service/forest/HttpOdsRtSzdnSnapshotFlowAddcodeService.java
// 职责: 门架抓拍流水：本地 MySQL 跨月分表优先，远端 Forest 代理兜底。
// 对应关系: list/export/getInfo/earliest-time -> enhanced + task::remote。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Router};
use serde_json::Value;

use crate::api::meta;
use crate::api::support;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::service::snapshot_flow_enhanced;
use crate::state::AppState;
use crate::task::remote;

/// `list` / `export` 共用的三步预处理（缺省分页 + 路段串归一）。
fn normalize(params: &mut HashMap<String, String>) {
    params.entry("pageNum".to_string()).or_insert_with(|| "1".to_string());
    params.entry("pageSize".to_string()).or_insert_with(|| "10".to_string());

    // Java: deleteEnd(sectionCodeStr).indexOf("all") > -1 -> sectionCodeStr = ""
    let section_code = params
        .get("sectionCodeStr")
        .map(|value| value.trim().trim_end_matches(',').to_string())
        .unwrap_or_default();
    if section_code.contains("all") {
        params.insert("sectionCodeStr".to_string(), String::new());
    }
}

fn require_time_range(params: &HashMap<String, String>) -> bool {
    let present = |key: &str| {
        params
            .get(key)
            .map(|value| !value.trim().is_empty())
            .unwrap_or(false)
    };
    present("applyTime1") && present("applyTime2")
}

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    support::query_log(&state.db, &user, &support::query_json(&params), "2", "1").await?;
    normalize(&mut params);

    if !require_time_range(&params) {
        return Ok(TableDataInfo::new(0, Vec::new()));
    }
    Ok(snapshot_flow_enhanced::query_page(&state, &params).await)
}

async fn export(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let mut params = support::query_map(&raw);
    support::query_log(&state.db, &user, &support::query_json(&params), "2", "2").await?;
    normalize(&mut params);

    let mut rows = if require_time_range(&params) {
        snapshot_flow_enhanced::query_list_for_export(&state, &params)
            .await
            .unwrap_or_default()
    } else {
        Vec::new()
    };

    // Java: directionMap.get(direction.toString()) —— 方向为空时 Java 会 NPE，
    // 这里按最佳实践跳过，导出仍可完成。
    let direction_map = support::dict_map(&state.db, "direction").await?;
    for row in &mut rows {
        let Some(object) = row.as_object_mut() else { continue };
        let Some(direction) = object.get("direction") else { continue };
        let key = match direction {
            Value::String(text) => text.clone(),
            other => other.to_string(),
        };
        let label = direction_map.get(&key).cloned().unwrap_or_default();
        object.insert("directionStr".to_string(), Value::String(label));
    }

    let headers =
        ["路线名称", "路段名称", "车牌颜色", "车牌号", "车辆类型", "门架", "方向", "抓拍时间"]
            .map(str::to_string);
    let fields = [
        "roadname",
        "sectionname",
        "platecolor",
        "platenumber",
        "cartype",
        "gantryname",
        "directionStr",
        "snapshottimeStr",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_download("门架抓拍流水数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        remote::select_snapshot_flow_by_id(&state, &big_id).await?,
    ))
}

async fn earliest_time(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    match remote::get_earliest_snapshottime(&state).await? {
        Some(time) => {
            // Java: AjaxResult.success(Date) —— Jackson 默认输出毫秒时间戳。
            let millis = time
                .and_local_timezone(chrono::Local)
                .single()
                .map(|local| local.timestamp_millis())
                .unwrap_or_default();
            Ok(AjaxResult::success_data(millis))
        }
        None => Ok(AjaxResult::success_data("暂无数据")),
    }
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/snapshotflow/list",
            meta::get_route(
                "/base/snapshotflow/list",
                Some("base:snapshotflow:list"),
                None,
                list,
            ),
        )
        .route(
            "/base/snapshotflow/export",
            meta::get_route(
                "/base/snapshotflow/export",
                Some("base:snapshotflow:list"),
                None,
                export,
            ),
        )
        .route(
            "/base/snapshotflow/earliest-time",
            meta::get_route("/base/snapshotflow/earliest-time", None, None, earliest_time),
        )
        .route(
            "/base/snapshotflow/{bigId}",
            meta::get_route("/base/snapshotflow/{bigId}", None, None, get_info),
        )
}
