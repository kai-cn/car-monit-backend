// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/CacheController.java
// 职责: Redis 监控（info / dbSize / commandStats）。
// 对应关系: RedisCallback info()/dbSize() -> RedisCache::info/db_size。

use axum::extract::State;
use axum::Router;
use serde_json::{json, Map, Value};

use crate::api::meta;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    Router::new().route(
        "/monitor/cache",
        meta::get_route("/monitor/cache", Some("monitor:cache:list"), None, get_info),
    )
}

async fn get_info(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let info = state.redis.info(None).await?;
    let command_stats = state.redis.info(Some("commandstats")).await?;
    let db_size = state.redis.db_size().await?;

    let info_map = parse_info(&info);
    let mut pie_list = Vec::new();
    for (key, value) in parse_info(&command_stats) {
        let Some(name) = key.strip_prefix("cmdstat_") else { continue };
        let text = value.as_str().unwrap_or_default();
        let calls = text
            .split_once("calls=")
            .and_then(|(_, rest)| rest.split_once(",usec"))
            .map(|(calls, _)| calls.to_string())
            .unwrap_or_default();
        pie_list.push(json!({ "name": name, "value": calls }));
    }

    // Java 侧这两层都是 HashMap，键序按桶序而非构造序。
    let info_map = crate::response::java_hashtable_ordered(&Value::Object(info_map));
    Ok(AjaxResult::success_data(crate::response::java_ordered(&json!({
        "info": info_map,
        "dbSize": db_size,
        "commandStats": pie_list,
    }))))
}

fn parse_info(text: &str) -> Map<String, Value> {
    let mut map = Map::new();
    for line in text.lines() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some((key, value)) = line.split_once(':') {
            map.insert(key.to_string(), Value::String(value.to_string()));
        }
    }
    map
}
