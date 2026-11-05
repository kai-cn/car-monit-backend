// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CdcController.java
//       ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/DeadLetterQueueService.java
//       ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcSyncService.java
// 职责: CDC 队列管理（重试队列/死信队列，Redis 存储）。
// 对应关系: RedisTemplate<String,String> -> RedisCache::get_string/set_string_ex/keys。

use axum::extract::{Path, State};
use axum::Router;
use serde_json::{json, Value};

use crate::api::meta;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

/// Java: `DLQ_RETRY_KEY_PREFIX`。
const RETRY_PREFIX: &str = "cdc:retry:";
/// Java: `DLQ_DLQ_KEY_PREFIX`。
const DEAD_PREFIX: &str = "cdc:dead:";

async fn queue_values(state: &AppState, prefix: &str) -> Result<Vec<Value>, AppError> {
    let pattern = format!("{prefix}*");
    let mut values = Vec::new();
    for key in state.redis.keys(&pattern).await? {
        if let Some(text) = state.redis.get_string(&key).await? {
            match serde_json::from_str::<Value>(&text) {
                Ok(value) => values.push(value),
                Err(err) => tracing::error!("【死信队列】解析消息失败: {err}"),
            }
        }
    }
    Ok(values)
}

async fn status(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let retry_keys = state.redis.keys(&format!("{RETRY_PREFIX}*")).await?;
    let dead_keys = state.redis.keys(&format!("{DEAD_PREFIX}*")).await?;
    let cdc = &state.settings.cdc;
    Ok(AjaxResult::success_data(crate::response::java_ordered(
        &json!({
            "retryQueueSize": retry_keys.len(),
            "deadLetterQueueSize": dead_keys.len(),
            "kafkaTopic": cdc.kafka.topic,
            "consumerGroupId": cdc.kafka.group_id,
            "maxRetryAttempts": cdc.retry.max_retries,
        }),
    )))
}

async fn dead_letters(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        queue_values(&state, DEAD_PREFIX).await?,
    ))
}

async fn retry_messages(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        queue_values(&state, RETRY_PREFIX).await?,
    ))
}

/// Java: `CdcSyncService.processCdcMessage` —— ES 写入在 Java 里被注释，始终返回 true。
fn process_message(_message: &Value) -> bool {
    true
}

async fn retry_one(
    State(state): State<AppState>,
    Path(message_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let pattern = format!("{DEAD_PREFIX}*");
    for key in state.redis.keys(&pattern).await? {
        let Some(text) = state.redis.get_string(&key).await? else {
            continue;
        };
        let Ok(value) = serde_json::from_str::<Value>(&text) else {
            continue;
        };
        if value.get("messageId").and_then(Value::as_str) == Some(message_id.as_str()) {
            if process_message(&value) {
                state.redis.delete_object(&key).await?;
                return Ok(AjaxResult::success_msg("重试成功"));
            }
            return Ok(AjaxResult::error("重试失败，消息不存在或处理失败"));
        }
    }
    Ok(AjaxResult::error("重试失败，消息不存在或处理失败"))
}

async fn retry_all(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let pattern = format!("{DEAD_PREFIX}*");
    let mut success_count = 0;
    for key in state.redis.keys(&pattern).await? {
        let Some(text) = state.redis.get_string(&key).await? else {
            continue;
        };
        let Ok(value) = serde_json::from_str::<Value>(&text) else {
            continue;
        };
        if process_message(&value) {
            state.redis.delete_object(&key).await?;
            success_count += 1;
        }
    }
    Ok(AjaxResult::success_msg(format!(
        "批量重试完成，成功 {success_count} 条"
    )))
}

async fn delete_dead(
    State(state): State<AppState>,
    Path(message_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    state
        .redis
        .delete_object(&format!("{DEAD_PREFIX}{message_id}"))
        .await?;
    Ok(AjaxResult::success_msg("删除成功"))
}

async fn clear_dead(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    for key in state.redis.keys(&format!("{DEAD_PREFIX}*")).await? {
        state.redis.delete_object(&key).await?;
    }
    Ok(AjaxResult::success_msg("已清空死信队列"))
}

/// Java: `AjaxResult.success(cdcConfig)` —— 返回配置项（缺省值照抄 CdcConfig）。
async fn config(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let cdc = &state.settings.cdc;
    Ok(AjaxResult::success_data(json!({
        "kafka": {
            "bootstrapServers": cdc.kafka.bootstrap_servers,
            "consumerGroupId": cdc.kafka.group_id,
            "topic": cdc.kafka.topic,
            "autoCommit": true,
            "autoCommitInterval": 1000,
            "sessionTimeout": 30000,
            "concurrency": cdc.kafka.concurrency,
        },
        "esSync": {
            "enabled": cdc.es_sync.enabled,
            "batchSize": 500,
            "batchInterval": 5000,
            "asyncThreads": 2,
        },
        "retry": {
            "maxAttempts": cdc.retry.max_retries,
            "interval": 1000,
            "multiplier": 2.0,
            "maxInterval": 30000,
        },
    })))
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/cdc/status",
            meta::get_route("/base/cdc/status", None, None, status),
        )
        .route(
            "/base/cdc/dead-letters",
            meta::get_route("/base/cdc/dead-letters", None, None, dead_letters),
        )
        .route(
            "/base/cdc/retry-messages",
            meta::get_route("/base/cdc/retry-messages", None, None, retry_messages),
        )
        .route(
            "/base/cdc/retry-all",
            meta::post_route("/base/cdc/retry-all", None, None, retry_all),
        )
        .route(
            "/base/cdc/retry/{messageId}",
            meta::post_route("/base/cdc/retry/{messageId}", None, None, retry_one),
        )
        .route(
            "/base/cdc/dead-letters/clear",
            meta::delete_route("/base/cdc/dead-letters/clear", None, None, clear_dead),
        )
        .route(
            "/base/cdc/dead-letters/{messageId}",
            meta::delete_route(
                "/base/cdc/dead-letters/{messageId}",
                None,
                None,
                delete_dead,
            ),
        )
        .route(
            "/base/cdc/config",
            meta::get_route("/base/cdc/config", None, None, config),
        )
}
