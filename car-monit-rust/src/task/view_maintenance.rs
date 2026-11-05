// 来源: ruoyi-system/src/main/java/com/ruoyi/base/task/ViewMaintenanceTask.java
// 职责: 每月维护「主表 + 按月分表」的联合视图。
// 对应关系: @Scheduled(cron = "0 0 2 1 * ?") -> task::JobKind::ViewMaintenance。
//
// 与 Java 的差异：Java 的 executeDDL() 是空实现（视图从未真正重建）；用户要求
// 定时任务必须生效，这里真正执行 CREATE OR REPLACE VIEW，并只合并 yyyyMM 形式的
// 月份分表（避免把 provcapture/stationcapture 等异构表拼进 UNION）。

use std::sync::atomic::{AtomicI32, AtomicI64, Ordering};
use std::sync::LazyLock;

use chrono::{Datelike, Months, TimeZone};
use serde_json::json;
use tracing::{debug, error, info};

use crate::repository::snapshot_flow_repo::list_sharding_tables;
use crate::state::AppState;

const TABLE_PREFIX: &str = "ods_rt_szdn_snapshot_flow_";
const VIEW_NAME: &str = "ods_rt_szdn_snapshot_flow_view";
const ACTIVE_TABLE_NAME: &str = "ods_rt_szdn_snapshot_flow_addcode";

#[derive(Default)]
struct Metrics {
    last_execute_time: AtomicI64,
    last_duration_ms: AtomicI64,
    last_updated_table_count: AtomicI32,
}

static METRICS: LazyLock<Metrics> = LazyLock::new(Metrics::default);

/// Java: `@Scheduled(cron = "0 0 2 1 * ?") scheduledViewMaintenance()`
pub async fn scheduled_view_maintenance(state: AppState) -> String {
    info!("[视图维护任务] 定时任务开始执行");
    execute_view_maintenance(&state, false).await
}

/// Java: `manualTrigger()`
pub async fn manual_trigger(state: AppState) -> String {
    info!("[视图维护任务] 手动触发执行");
    execute_view_maintenance(&state, true).await
}

async fn execute_view_maintenance(state: &AppState, is_manual: bool) -> String {
    let start = std::time::Instant::now();
    let trigger_type = if is_manual { "手动" } else { "定时" };

    let existing_tables = match list_sharding_tables(&state.db, TABLE_PREFIX).await {
        Ok(tables) => tables,
        Err(err) => {
            let duration = start.elapsed().as_millis() as i64;
            error!(
                "[视图维护任务] {}执行异常，耗时={}ms: {}",
                trigger_type, duration, err
            );
            return format!("执行异常: {err}");
        }
    };

    let view_sql = build_view_sql(&existing_tables);
    let success = rebuild_view(state, &view_sql).await;

    let duration = start.elapsed().as_millis() as i64;
    update_metrics(duration, existing_tables.len() as i32);
    log_performance_metrics(trigger_type, duration, existing_tables.len(), success);

    if success {
        let message = format!(
            "[视图维护任务] {}执行成功，耗时={}ms，表数量={}",
            trigger_type,
            duration,
            existing_tables.len()
        );
        info!("{}", message);
        message
    } else {
        let message = format!(
            "[视图维护任务] {}执行失败，耗时={}ms",
            trigger_type, duration
        );
        error!("{}", message);
        message
    }
}

/// Java: `buildViewSql(existingTables)` —— 主表在前，历史分表按名称升序。
fn build_view_sql(existing_tables: &[String]) -> String {
    let mut sql =
        format!("CREATE OR REPLACE VIEW {VIEW_NAME} AS\nSELECT * FROM {ACTIVE_TABLE_NAME}");

    let mut shards: Vec<&str> = existing_tables
        .iter()
        .map(String::as_str)
        .filter(|name| is_monthly_shard(name))
        .collect();
    shards.sort_unstable();

    for table in shards {
        if table != ACTIVE_TABLE_NAME {
            sql.push_str("\nUNION ALL\nSELECT * FROM ");
            sql.push_str(table);
        }
    }
    sql
}

fn is_monthly_shard(table_name: &str) -> bool {
    table_name
        .strip_prefix(TABLE_PREFIX)
        .map(|suffix| suffix.len() == 6 && suffix.chars().all(|c| c.is_ascii_digit()))
        .unwrap_or(false)
}

/// Java: `rebuildView(viewSql)` + `executeDDL`（Java 侧为空实现）。
async fn rebuild_view(state: &AppState, view_sql: &str) -> bool {
    debug!("[视图维护任务] 执行视图重建SQL: {}", view_sql);
    match sqlx::query(view_sql).execute(&state.db).await {
        Ok(_) => true,
        Err(err) => {
            error!("[视图维护任务] 视图重建失败: {}", err);
            false
        }
    }
}

fn update_metrics(duration_ms: i64, table_count: i32) {
    METRICS
        .last_execute_time
        .store(chrono::Local::now().timestamp_millis(), Ordering::Relaxed);
    METRICS
        .last_duration_ms
        .store(duration_ms, Ordering::Relaxed);
    METRICS
        .last_updated_table_count
        .store(table_count, Ordering::Relaxed);
}

fn log_performance_metrics(
    trigger_type: &str,
    duration_ms: i64,
    table_count: usize,
    success: bool,
) {
    info!(
        "[视图维护任务] 性能指标 - 触发类型={}, 耗时={}ms, 表数量={}, 成功={}",
        trigger_type, duration_ms, table_count, success
    );

    const WARNING_THRESHOLD: i64 = 30_000;
    const CRITICAL_THRESHOLD: i64 = 60_000;
    if duration_ms > CRITICAL_THRESHOLD {
        error!(
            "[视图维护任务] 性能告警 - 执行耗时超过临界阈值: {}ms > {}ms",
            duration_ms, CRITICAL_THRESHOLD
        );
    } else if duration_ms > WARNING_THRESHOLD {
        tracing::warn!(
            "[视图维护任务] 性能警告 - 执行耗时超过警告阈值: {}ms > {}ms",
            duration_ms,
            WARNING_THRESHOLD
        );
    }
}

/// Java: `getMetrics()`。
pub fn get_metrics() -> serde_json::Value {
    json!({
        "lastExecuteTime": METRICS.last_execute_time.load(Ordering::Relaxed),
        "lastDurationMs": METRICS.last_duration_ms.load(Ordering::Relaxed),
        "lastUpdatedTableCount": METRICS.last_updated_table_count.load(Ordering::Relaxed),
        "nextScheduleTime": next_schedule_time(),
    })
}

/// Java: `getNextScheduleTime()` —— 下个月 1 日 02:00 的时间戳（毫秒）。
fn next_schedule_time() -> i64 {
    let today = chrono::Local::now().date_naive();
    let Some(first_of_next_month) = today
        .with_day(1)
        .and_then(|date| date.checked_add_months(Months::new(1)))
    else {
        return 0;
    };
    let naive = first_of_next_month
        .and_hms_opt(2, 0, 0)
        .unwrap_or_else(|| first_of_next_month.and_hms_opt(0, 0, 0).expect("midnight"));
    chrono::Local
        .from_local_datetime(&naive)
        .single()
        .map(|dt| dt.timestamp_millis())
        .unwrap_or(0)
}

/// Java: `needsUpdate()` —— 当月分表尚未创建时需要维护。
pub async fn needs_update(state: &AppState) -> bool {
    // Java: TABLE_PREFIX + DateUtils.getYearMonth()，getYearMonth() 是 "yyyy-MM"。
    let current_month_table = format!("{}{}", TABLE_PREFIX, chrono::Local::now().format("%Y-%m"));
    match list_sharding_tables(&state.db, TABLE_PREFIX).await {
        Ok(tables) => !tables.contains(&current_month_table),
        Err(err) => {
            error!("[视图维护任务] 预检查失败: {}", err);
            true
        }
    }
}

/// Java: `getViewDefinition()`。
pub fn get_view_definition() -> &'static str {
    "视图定义查询需要根据数据库类型实现"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn view_sql_orders_shards_and_skips_active_table() {
        let tables = vec![
            "ods_rt_szdn_snapshot_flow_addcode".to_string(),
            "ods_rt_szdn_snapshot_flow_202510".to_string(),
            "ods_rt_szdn_snapshot_flow_202509".to_string(),
            "ods_rt_szdn_snapshot_flow_provcapture_addcode".to_string(),
        ];
        let sql = build_view_sql(&tables);
        assert_eq!(
            sql,
            "CREATE OR REPLACE VIEW ods_rt_szdn_snapshot_flow_view AS\n\
             SELECT * FROM ods_rt_szdn_snapshot_flow_addcode\n\
             UNION ALL\nSELECT * FROM ods_rt_szdn_snapshot_flow_202509\n\
             UNION ALL\nSELECT * FROM ods_rt_szdn_snapshot_flow_202510"
        );
    }
}
