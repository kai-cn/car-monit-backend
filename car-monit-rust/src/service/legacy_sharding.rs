// 来源: ruoyi-system/src/main/java/com/ruoyi/base/service/cache/PartitionMappingCache.java
//       .../query/PartitionParallelQueryService.java
//       .../sharding/ShardingQueryService.java
//       .../sharding/ShardingSyncService.java
//       .../consistency/DataConsistencyService.java
//       .../enhanced/ViewMaintenanceOptimizationService.java
//       ruoyi-common/src/main/java/com/ruoyi/common/utils/SnowflakeIdUtil.java
// 职责: 6 个「死代码」类的内部能力（无路由引用，用户决策：照样迁移）。
// 对应关系: 同名类 -> 同名结构/函数；Quartz/缓存/分表算法复用现有模块。

use chrono::{Datelike, Months, NaiveDateTime};
use serde_json::Value;

use crate::api::support;
use crate::db::rows::{row_to_json, rows_to_json};
use crate::db::sharding::{physical_table_name, ShardingStrategy};
use crate::error::AppError;
use crate::repository::snapshot_flow_repo;
use crate::state::AppState;

pub const CACHE_KEY_PREFIX: &str = "partition:mapping:";
pub const CACHE_EXPIRE_DAYS: u64 = 30;
const TIMESTAMP_OFFSET_MS: i64 = 1_609_459_200_000; // 2021-01-01
const TIMESTAMP_SHIFT: u32 = 22;

// ==================== SnowflakeIdUtil ====================

fn parse_date_from_id(id: &str) -> Option<NaiveDateTime> {
    let value: i64 = id.parse().ok()?;
    let millis = (value >> TIMESTAMP_SHIFT) + TIMESTAMP_OFFSET_MS;
    if millis < TIMESTAMP_OFFSET_MS {
        return None;
    }
    chrono::DateTime::from_timestamp_millis(millis).map(|dt| dt.naive_local())
}

/// Java: SnowflakeIdUtil.parsePartitionFromId —— `p` + yyyyMM。
pub fn parse_partition_from_id(id: &str) -> Option<String> {
    let date = parse_date_from_id(id)?;
    Some(format!("p{:04}{:02}", date.year(), date.month()))
}

/// Java: SnowflakeIdUtil.estimateTimeRange —— 前后各 1 天。
pub fn estimate_time_range(id: &str) -> Option<(NaiveDateTime, NaiveDateTime)> {
    let date = parse_date_from_id(id)?;
    Some((date - chrono::Duration::days(1), date + chrono::Duration::days(1)))
}

// ==================== PartitionMappingCache ====================

pub struct PartitionMappingCache;

impl PartitionMappingCache {
    fn key(big_id: &str) -> String {
        format!("{CACHE_KEY_PREFIX}{big_id}")
    }

    /// Java: getPartitionByBigId —— 缓存 -> 雪花解析 -> 回写缓存。
    pub async fn get_partition_by_big_id(
        state: &AppState,
        big_id: &str,
    ) -> Result<Option<String>, AppError> {
        if big_id.is_empty() {
            return Ok(None);
        }
        if let Some(value) = state.redis.get_string(&Self::key(big_id)).await? {
            return Ok(Some(value));
        }
        if let Some(partition) = parse_partition_from_id(big_id) {
            Self::cache_partition(state, big_id, &partition).await?;
            return Ok(Some(partition));
        }
        Ok(None)
    }

    pub async fn cache_partition_with_time(
        state: &AppState,
        big_id: &str,
        snapshottime: NaiveDateTime,
    ) -> Result<(), AppError> {
        let partition = format!("p{:04}{:02}", snapshottime.year(), snapshottime.month());
        Self::cache_partition(state, big_id, &partition).await
    }

    pub async fn cache_partition(
        state: &AppState,
        big_id: &str,
        partition: &str,
    ) -> Result<(), AppError> {
        if big_id.is_empty() || partition.is_empty() {
            return Ok(());
        }
        state
            .redis
            .set_string_ex(
                &Self::key(big_id),
                partition,
                CACHE_EXPIRE_DAYS * 24 * 3600,
            )
            .await
    }

    pub async fn remove_partition_mapping(
        state: &AppState,
        big_id: &str,
    ) -> Result<(), AppError> {
        if big_id.is_empty() {
            return Ok(());
        }
        state.redis.delete_object(&Self::key(big_id)).await
    }

    pub fn get_time_range_for_fallback(
        big_id: &str,
    ) -> Option<(NaiveDateTime, NaiveDateTime)> {
        estimate_time_range(big_id)
    }

    pub async fn has_cached_partition(
        state: &AppState,
        big_id: &str,
    ) -> Result<bool, AppError> {
        if big_id.is_empty() {
            return Ok(false);
        }
        state.redis.has_key(&Self::key(big_id)).await
    }
}

// ==================== ShardingQueryService ====================

pub const ACTIVE_TABLE: &str = "ods_rt_szdn_snapshot_flow_addcode";

fn valid_partition(partition: &str) -> bool {
    !partition.is_empty()
        && partition.len() <= 16
        && partition.chars().all(|ch| ch.is_ascii_alphanumeric())
}

/// Java: selectByIdOptimized —— 先用分区映射定位，失败再按主键全表查。
pub async fn select_by_id_optimized(
    state: &AppState,
    big_id: &str,
) -> Result<Option<Value>, AppError> {
    if let Some(partition) = PartitionMappingCache::get_partition_by_big_id(state, big_id).await? {
        if valid_partition(&partition) {
            let sql = format!(
                "select * from {ACTIVE_TABLE} partition ({partition}) where big_id = ?"
            );
            if let Ok(row) = sqlx::query(&sql).bind(big_id).fetch_optional(&state.db).await {
                return Ok(row.map(|row| row_to_json(&row)));
            }
        }
    }
    let row = sqlx::query(&format!("select * from {ACTIVE_TABLE} where big_id = ?"))
        .bind(big_id)
        .fetch_optional(&state.db)
        .await?;
    Ok(row.map(|row| row_to_json(&row)))
}

/// Java: selectByIdByTimeRange —— 用雪花时间 ±1 天缩小扫描范围。
pub async fn select_by_id_by_time_range(
    state: &AppState,
    big_id: &str,
) -> Result<Option<Value>, AppError> {
    let Some((start, end)) = estimate_time_range(big_id) else {
        return Ok(None);
    };
    let row = sqlx::query(&format!(
        "select * from {ACTIVE_TABLE} where big_id = ? and snapshottime between ? and ?"
    ))
    .bind(big_id)
    .bind(start)
    .bind(end)
    .fetch_optional(&state.db)
    .await?;
    Ok(row.map(|row| row_to_json(&row)))
}

/// Java: insertWithCache —— 插入后缓存 bigId -> 分区。
pub async fn insert_with_cache(state: &AppState, record: &Value) -> Result<u64, AppError> {
    let rows = support::insert_entity(&state.db, ACTIVE_TABLE, record, support::AutoFill::NONE)
        .await?;
    if let (Some(big_id), Some(snapshottime)) = (
        record.get("bigId").and_then(Value::as_str),
        record.get("snapshottime").and_then(Value::as_str),
    ) {
        if let Ok(date) = NaiveDateTime::parse_from_str(snapshottime, "%Y-%m-%d %H:%M:%S") {
            PartitionMappingCache::cache_partition_with_time(state, big_id, date).await?;
        }
    }
    Ok(rows)
}

pub async fn batch_insert_with_cache(
    state: &AppState,
    records: &[Value],
) -> Result<u64, AppError> {
    let mut total = 0;
    for record in records {
        total += insert_with_cache(state, record).await?;
    }
    Ok(total)
}

// ==================== ShardingSyncService<T> ====================

/// Java: `ShardingSyncService<T>` 接口 —— 死代码接口，保留同等约束。
#[async_trait::async_trait]
pub trait ShardingSyncService<T>: Send + Sync {
    async fn sync(&self, items: &[T]) -> Result<usize, AppError>;
}

// ==================== PartitionParallelQueryService ====================

/// Java: getPartitionsInRange —— p + yyyyMM（按月）。
pub fn get_partitions_in_range(start: NaiveDateTime, end: NaiveDateTime) -> Vec<String> {
    let mut values = Vec::new();
    if start > end {
        return values;
    }
    let mut cursor = start.date().with_day(1).expect("valid day").and_hms_opt(0, 0, 0).expect("midnight");
    while cursor <= end {
        let partition = format!("p{:04}{:02}", cursor.year(), cursor.month());
        if !values.contains(&partition) {
            values.push(partition);
        }
        cursor = cursor + Months::new(1);
    }
    values
}

/// Java: queryMultiPartitionParallel —— 逐分区并发查询后按 snapshottime 升序合并。
pub async fn query_multi_partition_parallel(
    state: &AppState,
    start: NaiveDateTime,
    end: NaiveDateTime,
) -> Result<Vec<Value>, AppError> {
    let partitions = get_partitions_in_range(start, end);
    if partitions.is_empty() {
        return Ok(Vec::new());
    }
    let mut futures = Vec::new();
    for partition in partitions {
        let state = state.clone();
        futures.push(async move {
            query_partition(&state, &partition, start, end).await.unwrap_or_default()
        });
    }
    let results = futures::future::join_all(futures).await;
    let mut rows: Vec<Value> = results.into_iter().flatten().collect();
    rows.sort_by(|left, right| {
        left.get("snapshottime")
            .and_then(Value::as_str)
            .cmp(&right.get("snapshottime").and_then(Value::as_str))
    });
    Ok(rows)
}

async fn query_partition(
    state: &AppState,
    partition: &str,
    start: NaiveDateTime,
    end: NaiveDateTime,
) -> Result<Vec<Value>, AppError> {
    if !valid_partition(partition) {
        return Ok(Vec::new());
    }
    let sql = format!(
        "select * from {ACTIVE_TABLE} partition ({partition}) \
         where snapshottime between ? and ? order by snapshottime asc"
    );
    let rows = sqlx::query(&sql)
        .bind(start)
        .bind(end)
        .fetch_all(&state.db)
        .await?;
    Ok(rows_to_json(&rows))
}

/// Java: queryWithPageOptimized —— 先统计各分区行数，再按 offset 跨分区取数。
pub async fn query_with_page_optimized(
    state: &AppState,
    start: NaiveDateTime,
    end: NaiveDateTime,
    offset: i64,
    limit: i64,
) -> Result<(Vec<Value>, i64), AppError> {
    let partitions = get_partitions_in_range(start, end);
    let mut counts = Vec::new();
    let mut total = 0i64;
    for partition in &partitions {
        let count = count_partition(state, partition, start, end).await.unwrap_or(0);
        total += count;
        counts.push(count);
    }
    let mut remaining_offset = offset;
    let mut remaining_limit = limit;
    let mut rows = Vec::new();
    for (index, partition) in partitions.iter().enumerate() {
        if remaining_limit <= 0 {
            break;
        }
        let count = counts[index];
        if remaining_offset >= count {
            remaining_offset -= count;
            continue;
        }
        if !valid_partition(partition) {
            continue;
        }
        let sql = format!(
            "select * from {ACTIVE_TABLE} partition ({partition}) \
             where snapshottime between ? and ? order by snapshottime asc limit ? offset ?"
        );
        let page = sqlx::query(&sql)
            .bind(start)
            .bind(end)
            .bind(remaining_limit)
            .bind(remaining_offset)
            .fetch_all(&state.db)
            .await
            .unwrap_or_default();
        let take = page.len() as i64;
        rows.extend(rows_to_json(&page));
        remaining_limit -= take;
        remaining_offset = 0;
    }
    Ok((rows, total))
}

async fn count_partition(
    state: &AppState,
    partition: &str,
    start: NaiveDateTime,
    end: NaiveDateTime,
) -> Result<i64, AppError> {
    if !valid_partition(partition) {
        return Ok(0);
    }
    let sql = format!(
        "select count(1) from {ACTIVE_TABLE} partition ({partition}) \
         where snapshottime between ? and ?"
    );
    Ok(sqlx::query_scalar(&sql)
        .bind(start)
        .bind(end)
        .fetch_one(&state.db)
        .await?)
}

// ==================== DataConsistencyService ====================

#[derive(Debug, Clone, Default)]
pub struct ConsistencyResult {
    pub consistent: bool,
    pub month: String,
    pub source_count: i64,
    pub target_count: i64,
}

/// Java: checkConsistency —— 源表（分区表）与目标月表行数对比。
pub async fn check_consistency(
    state: &AppState,
    month: &str,
) -> Result<ConsistencyResult, AppError> {
    let (start, end) = month_range(month)?;
    let table = physical_table_name("ods_rt_szdn_snapshot_flow", start, ShardingStrategy::Monthly);
    let target_count: i64 = sqlx::query_scalar(&format!(
        "select count(1) from {table} where snapshottime between ? and ?"
    ))
    .bind(start)
    .bind(end)
    .fetch_one(&state.db)
    .await
    .unwrap_or(0);
    let source_count: i64 = sqlx::query_scalar(&format!(
        "select count(1) from {ACTIVE_TABLE} where snapshottime between ? and ?"
    ))
    .bind(start)
    .bind(end)
    .fetch_one(&state.db)
    .await
    .unwrap_or(0);
    Ok(ConsistencyResult {
        consistent: source_count == target_count,
        month: month.to_string(),
        source_count,
        target_count,
    })
}

/// Java: syncWithConsistency —— 按月从远端分页补齐到本地分表。
pub async fn sync_with_consistency(state: &AppState) -> Result<String, AppError> {
    let Some(earliest) = crate::task::remote::get_earliest_snapshottime(state).await? else {
        return Ok("GaussDB中暂无数据".to_string());
    };
    let now = chrono::Local::now().naive_local();
    let mut synced = 0usize;
    let mut corrected = 0;
    for month in months_between(earliest, now) {
        let (start, end) = month_range(&month)?;
        let table = physical_table_name("ods_rt_szdn_snapshot_flow", start, ShardingStrategy::Monthly);
        if snapshot_flow_repo::check_table_exists(&state.db, &table).await? == 0 {
            snapshot_flow_repo::create_sharding_table(&state.db, &table).await?;
        }
        synced += sync_month(state, &table, start, end).await?;
        let result = check_consistency(state, &month).await?;
        if !result.consistent {
            corrected += sync_month(state, &table, start, end).await?;
        }
    }
    Ok(format!("全量同步完成，同步数: {synced}, 补偿数: {corrected}"))
}

async fn sync_month(
    state: &AppState,
    table: &str,
    start: NaiveDateTime,
    end: NaiveDateTime,
) -> Result<usize, AppError> {
    let mut page_num = 1;
    let mut total = 0usize;
    loop {
        let query = crate::domain::SnapshotFlowQuery {
            apply_time1: Some(start.format("%Y-%m-%d %H:%M:%S").to_string()),
            apply_time2: Some(end.format("%Y-%m-%d %H:%M:%S").to_string()),
            page_num: Some(page_num),
            page_size: Some(1000),
        };
        let page = crate::task::remote::get_snapshot_flow_page(state, &query).await?;
        if page.rows.is_empty() {
            break;
        }
        total += page.rows.len();
        snapshot_flow_repo::insert_batch_to_table(&state.db, table, &page.rows).await?;
        page_num += 1;
    }
    Ok(total)
}

fn month_range(month: &str) -> Result<(NaiveDateTime, NaiveDateTime), AppError> {
    let year: i32 = month
        .get(0..4)
        .and_then(|value| value.parse().ok())
        .ok_or_else(|| AppError::BadRequest(format!("非法月份: {month}")))?;
    let month_num: u32 = month
        .get(4..6)
        .and_then(|value| value.parse().ok())
        .ok_or_else(|| AppError::BadRequest(format!("非法月份: {month}")))?;
    let start = chrono::NaiveDate::from_ymd_opt(year, month_num, 1)
        .ok_or_else(|| AppError::BadRequest(format!("非法月份: {month}")))?
        .and_hms_opt(0, 0, 0)
        .expect("midnight");
    let next = start + Months::new(1);
    Ok((start, next - chrono::Duration::seconds(1)))
}

fn months_between(start: NaiveDateTime, end: NaiveDateTime) -> Vec<String> {
    let mut values = Vec::new();
    let mut cursor = start.date().with_day(1).expect("valid day").and_hms_opt(0, 0, 0).expect("midnight");
    while cursor <= end {
        values.push(format!("{:04}{:02}", cursor.year(), cursor.month()));
        cursor = cursor + Months::new(1);
    }
    values
}

// ==================== ViewMaintenanceOptimizationService ====================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OptimizationStrategy {
    Fast,
    Balanced,
    Thorough,
}

/// Java: selectOptimalStrategy —— 依据分表数量选择策略。
pub async fn select_optimal_strategy(
    state: &AppState,
) -> Result<OptimizationStrategy, AppError> {
    let tables = snapshot_flow_repo::list_sharding_tables(&state.db, "ods_rt_szdn_snapshot_flow_").await?;
    Ok(match tables.len() {
        0..=3 => OptimizationStrategy::Fast,
        4..=12 => OptimizationStrategy::Balanced,
        _ => OptimizationStrategy::Thorough,
    })
}

/// Java: executeOptimizedMaintenance —— 按策略重建视图。
pub async fn execute_optimized_maintenance(state: &AppState) -> Result<String, AppError> {
    let strategy = select_optimal_strategy(state).await?;
    crate::task::view_maintenance::scheduled_view_maintenance(state.clone()).await;
    Ok(format!("视图维护完成（策略: {strategy:?}）"))
}

/// Java: getStrategyInfo —— 策略与分表信息。
pub async fn get_strategy_info(state: &AppState) -> Result<Value, AppError> {
    let strategy = select_optimal_strategy(state).await?;
    let tables = snapshot_flow_repo::list_sharding_tables(&state.db, "ods_rt_szdn_snapshot_flow_").await?;
    Ok(serde_json::json!({
        "strategy": format!("{strategy:?}"),
        "tableCount": tables.len(),
        "tables": tables,
        "cacheTtlMs": 3_600_000,
    }))
}

/// 便于外部按月份聚合（与原 Java 私有方法等价）。
pub fn month_partition(date: NaiveDateTime) -> String {
    format!("p{:04}{:02}", date.year(), date.month())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn snowflake_partition_roundtrip() {
        // 由 (timestamp - offset) << 22 构造一个雪花 ID。
        let millis = 1_750_000_000_000i64;
        let id = (millis - TIMESTAMP_OFFSET_MS) << TIMESTAMP_SHIFT;
        let partition = parse_partition_from_id(&id.to_string()).expect("partition");
        assert_eq!(partition.len(), 7);
        assert!(partition.starts_with('p'));
    }

    #[test]
    fn partitions_cover_month_range() {
        let start = NaiveDateTime::parse_from_str("2025-08-15 00:00:00", "%Y-%m-%d %H:%M:%S").unwrap();
        let end = NaiveDateTime::parse_from_str("2025-10-01 00:00:00", "%Y-%m-%d %H:%M:%S").unwrap();
        assert_eq!(
            get_partitions_in_range(start, end),
            vec!["p202508".to_string(), "p202509".to_string(), "p202510".to_string()]
        );
    }
}
