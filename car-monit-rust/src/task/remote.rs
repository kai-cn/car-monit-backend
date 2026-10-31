// 来源: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsRtSzdnSnapshotFlowAddcodeService.java
// 职责: 远端门架流水接口的 HTTP 客户端（Forest -> reqwest）。
// 对应关系: @BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}") -> AppState.http + base_url。

use chrono::NaiveDateTime;
use serde::Deserialize;
use tracing::warn;

use crate::common::serde_helpers::parse_json_datetime;
use crate::domain::{OdsRtSzdnSnapshotFlowAddcode, SnapshotFlowQuery};
use crate::error::AppError;
use crate::state::AppState;

pub const LIST_PATH: &str = "/base/snapshotflow/list";
pub const LIST_TO_EXPORT_PATH: &str = "/base/snapshotflow/listToExport";
pub const EARLIEST_PATH: &str = "/base/snapshotflow/earliest-time";

/// Java: `TableDataInfo`（只取同步用到的字段）。
#[derive(Debug, Clone, Default, Deserialize)]
pub struct RemotePage {
    #[serde(default)]
    pub total: i64,
    #[serde(default)]
    pub rows: Vec<OdsRtSzdnSnapshotFlowAddcode>,
}

/// Java: `getOdsRtSzdnSnapshotFlowAddcodePage(@Query q)`。
pub async fn get_snapshot_flow_page(
    state: &AppState,
    query: &SnapshotFlowQuery,
) -> Result<RemotePage, AppError> {
    let mut params: Vec<(&'static str, String)> = Vec::new();
    if let Some(value) = &query.apply_time1 {
        params.push(("applyTime1", value.clone()));
    }
    if let Some(value) = &query.apply_time2 {
        params.push(("applyTime2", value.clone()));
    }
    if let Some(value) = query.page_num {
        params.push(("pageNum", value.to_string()));
    }
    if let Some(value) = query.page_size {
        params.push(("pageSize", value.to_string()));
    }

    let value = get_json(state, LIST_PATH, &params).await?;
    serde_json::from_value(value).map_err(|err| {
        AppError::Internal(Some(format!("解析 /base/snapshotflow/list 响应失败: {err}")))
    })
}

/// Java: `getEarliestSnapshottime()` —— 返回值可能为 null / 字符串 / 毫秒数。
pub async fn get_earliest_snapshottime(
    state: &AppState,
) -> Result<Option<NaiveDateTime>, AppError> {
    let mut value = get_json(state, EARLIEST_PATH, &[]).await?;
    // RuoYi 控制器可能包一层 AjaxResult；Forest 的 Date 通常拿到裸值。
    if let Some(data) = value.get("data") {
        value = data.clone();
    }
    if value.is_null() {
        return Ok(None);
    }
    parse_json_datetime(&value).map(Some).ok_or_else(|| {
        AppError::Internal(Some(format!(
            "无法把最早 snapshottime 解析为日期: {value}"
        )))
    })
}

/// Java: `selectOdsRtSzdnSnapshotFlowAddcodeById(@Var bigId)`。
pub async fn select_snapshot_flow_by_id(
    state: &AppState,
    big_id: &str,
) -> Result<Option<OdsRtSzdnSnapshotFlowAddcode>, AppError> {
    let path = format!("/base/snapshotflow/{}", urlencoding(big_id));
    let value = get_json(state, &path, &[]).await?;
    if value.is_null() {
        return Ok(None);
    }
    serde_json::from_value(value)
        .map(Some)
        .map_err(|err| AppError::Internal(Some(format!("解析抓拍流水失败: {err}"))))
}

/// 把远端 `TableDataInfo` JSON 还原成本地结构。
pub fn page_from_value(value: &serde_json::Value) -> crate::response::TableDataInfo<serde_json::Value> {
    let total = value
        .get("total")
        .and_then(|total| total.as_i64().or_else(|| total.as_str().and_then(|text| text.parse().ok())))
        .unwrap_or(0);
    let rows = value
        .get("rows")
        .and_then(|rows| rows.as_array())
        .cloned()
        .unwrap_or_default();
    let mut page = crate::response::TableDataInfo::new(total, rows);
    if let Some(code) = value.get("code").and_then(serde_json::Value::as_i64) {
        page.code = code as i32;
    }
    if let Some(msg) = value.get("msg").and_then(serde_json::Value::as_str) {
        page.msg = Some(msg.to_string());
    }
    page
}

/// 请求 query 原样转发给远端（Forest `@Query` 绑定实体）。
pub fn owned_params(params: &std::collections::HashMap<String, String>) -> Vec<(String, String)> {
    params
        .iter()
        .map(|(key, value)| (key.clone(), value.clone()))
        .collect()
}

async fn get_json(
    state: &AppState,
    path: &str,
    params: &[(&'static str, String)],
) -> Result<serde_json::Value, AppError> {
    let owned = params
        .iter()
        .map(|(key, value)| ((*key).to_string(), value.clone()))
        .collect::<Vec<_>>();
    get_json_owned(state, path, &owned).await
}

/// 通用 GET：参数来自请求 query（`@Query` 绑定实体的等价物）。
pub async fn get_json_owned(
    state: &AppState,
    path: &str,
    params: &[(String, String)],
) -> Result<serde_json::Value, AppError> {
    let base = state.settings.vehicle_monitor.base_url.trim_end_matches('/');
    let url = format!("{base}{path}");
    let attempts = state.settings.forest.retry_count + 1;
    let mut last_error = String::new();

    for attempt in 1..=attempts {
        let response = state.http.get(&url).query(params).send().await;
        match response {
            Ok(response) => {
                let status = response.status();
                let body = response.text().await.unwrap_or_default();
                if status.is_success() {
                    return Ok(serde_json::from_str(&body)
                        .unwrap_or_else(|_| serde_json::Value::String(body.trim().to_string())));
                }
                last_error = format!("{path} 返回 HTTP {status}: {body}");
            }
            Err(err) => last_error = format!("{path} 请求失败: {err}"),
        }
        if attempt < attempts {
            warn!("【Forest】{} 第 {} 次失败，准备重试: {}", path, attempt, last_error);
        }
    }

    Err(AppError::Internal(Some(last_error)))
}

fn urlencoding(value: &str) -> String {
    url::form_urlencoded::byte_serialize(value.as_bytes()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn parses_remote_rows_with_mixed_date_formats() {
        let page: RemotePage = serde_json::from_value(json!({
            "total": 1,
            "rows": [{
                "bigId": "123",
                "snapshottime": "2025-08-29 10:15:30",
                "receivedtime": "2025-08-29",
                "lon": 113.123456,
                "direction": 1,
                "platenumber": "粤A12345"
            }]
        }))
        .expect("rows");
        assert_eq!(page.total, 1);
        let row = &page.rows[0];
        assert_eq!(row.big_id.as_deref(), Some("123"));
        assert_eq!(
            row.snapshottime,
            NaiveDateTime::parse_from_str("2025-08-29 10:15:30", "%Y-%m-%d %H:%M:%S").ok()
        );
        assert_eq!(row.receivedtime.unwrap().date().to_string(), "2025-08-29");
        assert_eq!(row.direction, Some(1));
    }
}
