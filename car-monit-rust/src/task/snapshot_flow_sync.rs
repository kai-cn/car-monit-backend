// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java
// 职责: 从 GaussDB（Forest 接口）按 snapshottime 月份同步到 MySQL 分表。
// 对应关系: @Scheduled / 线程池 / 分页拉取 / 批量插入 -> tokio + sqlx。
//
// 与 Java 的差异（用户决策「6 个定时任务必须生效」）：
// 1. Java 的 Rows 是 LinkedHashMap，`instanceof OdsRtSzdnSnapshotFlowAddcode` 永远为 false，
//    整趟同步搬 0 条；这里按 JSON 反序列化成实体，真正搬运数据。
// 2. Java 的 insert 引用了实体中不存在的 19 列，会报 Unknown column；这里只写真实存在的列。
// 3. Java 按月推进时保留原日号（月末会被夹到 28 号），可能漏掉最后一个月份分区；
//    这里按每月 1 日推进，保证区间内每个月都被同步。

use std::sync::atomic::{AtomicI64, AtomicUsize, Ordering};
use std::sync::Arc;

use chrono::{Datelike, Days, Local, Months, NaiveDate, NaiveDateTime};
use indexmap::IndexMap;
use tokio::sync::Semaphore;
use tracing::{debug, error, info, warn};

use crate::db::sharding::{physical_table_name, ShardingStrategy};
use crate::domain::{OdsRtSzdnSnapshotFlowAddcode, SnapshotFlowQuery};
use crate::error::AppError;
use crate::repository::snapshot_flow_repo::{
    check_table_exists, get_max_snapshottime, insert_batch_to_table,
};
use crate::response::AjaxResult;
use crate::state::AppState;
use crate::task::remote;
use crate::task::sharding_table::ensure_table_exists;

/// Java: `syncSnapshotFlowByDateRange` 的固定分页大小。
const PAGE_SIZE: i32 = 1000;

/// Java: `ThreadPoolExecutor(4, 8, ...)` —— 取核心线程数作为并发上限。
const SYNC_CONCURRENCY: usize = 4;

const TIME_FORMAT: &str = "%Y-%m-%d %H:%M:%S";

// ==================== 全量同步 ====================

/// Java: `syncFullData()`。
pub async fn sync_full_data(state: AppState) -> AjaxResult {
    info!("【全量同步任务】开始执行全量同步");
    let start = std::time::Instant::now();

    let Some(earliest) = query_earliest_snapshottime(&state).await else {
        warn!("【全量同步任务】未查询到最早的snapshottime，可能GaussDB中无数据");
        return AjaxResult::success_msg("GaussDB中暂无数据");
    };

    let now = Local::now().naive_local();
    let partitions = get_month_partitions(earliest, now);
    info!(
        "【全量同步任务】时间范围: {} 至 {}, 月份分区数: {}, 分区列表: {:?}",
        earliest.format("%Y-%m-%d"),
        now.format("%Y-%m-%d"),
        partitions.len(),
        partitions
    );

    let total = sync_by_month_partitions(&state, &partitions).await;
    info!(
        "【全量同步任务】完成全量同步，同步记录数: {}, 耗时: {} ms",
        total,
        start.elapsed().as_millis()
    );
    AjaxResult::success_msg(format!("全量同步完成，共同步 {total} 条数据"))
}

async fn query_earliest_snapshottime(state: &AppState) -> Option<NaiveDateTime> {
    match remote::get_earliest_snapshottime(state).await {
        Ok(value) => value,
        Err(err) => {
            error!("【全量同步任务】查询最早snapshottime失败: {}", err);
            None
        }
    }
}

/// Java: `getMonthPartitions(startDate, endDate)` —— 含首尾，格式 `yyyyMM`。
fn get_month_partitions(start: NaiveDateTime, end: NaiveDateTime) -> Vec<String> {
    // 有意偏差：Java 用 `Calendar.add(MONTH, 1)` 逐月推进，月末日期被夹到 28/30 号
    // （1-31 -> 2-28 -> 3-28 ...），当 end 落在月首时最后一个分区会被漏掉。
    // 这里把游标钉在每月 1 日，保证 [start, end] 覆盖的每个月份都参与同步。
    let mut partitions = Vec::new();
    let Some(mut cursor) = NaiveDate::from_ymd_opt(start.year(), start.month(), 1) else {
        return partitions;
    };
    let end_date = end.date();
    while cursor <= end_date {
        partitions.push(cursor.format("%Y%m").to_string());
        let Some(next) = cursor.checked_add_months(Months::new(1)) else {
            break;
        };
        cursor = next;
    }
    partitions
}

/// Java: `syncByMonthPartitions` —— 各月份并发执行，单月失败只记日志。
async fn sync_by_month_partitions(state: &AppState, partitions: &[String]) -> i64 {
    let total = Arc::new(AtomicI64::new(0));
    let failures = Arc::new(AtomicUsize::new(0));
    let limit = Arc::new(Semaphore::new(SYNC_CONCURRENCY));
    let mut handles = Vec::with_capacity(partitions.len());

    // 用 Semaphore + tokio::spawn 复刻固定并发度；每个任务持有 AppState 的所有权克隆，
    // 避免借用型 future 触发 rustc 的 “Send is not general enough”。
    for month in partitions {
        let Ok(permit) = limit.clone().acquire_owned().await else {
            break;
        };
        let state = state.clone();
        let month = month.clone();
        let total = Arc::clone(&total);
        let failures = Arc::clone(&failures);
        handles.push(tokio::spawn(async move {
            let _permit = permit;
            if let Err(err) = sync_single_month(&state, &month, &total).await {
                error!("【全量同步任务】月份 {} 同步失败: {}", month, err);
                failures.fetch_add(1, Ordering::Relaxed);
            }
        }));
    }

    for handle in handles {
        if let Err(err) = handle.await {
            error!("【全量同步任务】等待任务完成时发生异常: {}", err);
            failures.fetch_add(1, Ordering::Relaxed);
        }
    }

    let failed = failures.load(Ordering::Relaxed);
    if failed > 0 {
        warn!("【全量同步任务】有 {} 个月份同步失败", failed);
    }
    total.load(Ordering::Relaxed)
}

/// Java: `syncSingleMonth(month, totalCount)`。
async fn sync_single_month(
    state: &AppState,
    month: &str,
    total: &AtomicI64,
) -> Result<i64, AppError> {
    info!("【全量同步任务】开始同步月份: {}", month);
    let start = std::time::Instant::now();

    let year: i32 = month[0..4]
        .parse()
        .map_err(|_| AppError::Service(format!("非法月份: {month}")))?;
    let month_number: u32 = month[4..6]
        .parse()
        .map_err(|_| AppError::Service(format!("非法月份: {month}")))?;

    let start_date = format!("{year}-{month_number:02}-01 00:00:00");
    let last_day = last_day_of_month(year, month_number);
    let end_date = format!("{year}-{month_number:02}-{last_day:02} 23:59:59");

    let count = sync_snapshot_flow_by_date_range(&state, &start_date, &end_date).await?;
    total.fetch_add(count, Ordering::Relaxed);

    info!(
        "【全量同步任务】月份 {} 同步完成，记录数: {}, 耗时: {} ms",
        month,
        count,
        start.elapsed().as_millis()
    );
    Ok(count)
}

fn last_day_of_month(year: i32, month: u32) -> u32 {
    let first = NaiveDate::from_ymd_opt(year, month, 1).expect("month[0..6] 已校验");
    let first_of_next = first
        .checked_add_months(Months::new(1))
        .unwrap_or(first + Days::new(31));
    (first_of_next - Days::new(1)).day()
}

/// Java: `syncSnapshotFlowByDateRange(startDate, endDate)` —— 每页 1000 条。
async fn sync_snapshot_flow_by_date_range(
    state: &AppState,
    start_date: &str,
    end_date: &str,
) -> Result<i64, AppError> {
    let mut total = 0i64;
    let mut page_num = 1;

    loop {
        let Some(page) =
            fetch_from_gauss_db(state, start_date, end_date, page_num, PAGE_SIZE).await
        else {
            break;
        };
        if page.rows.is_empty() {
            break;
        }

        let rows = page.rows;
        let row_count = rows.len();
        let grouped = group_by_month(&table_prefix(state), &rows);

        for (table_name, list) in grouped {
            ensure_table_exists(state, &table_name).await;
            insert_batch_to_table(&state.db, &table_name, &list).await?;
            total += list.len() as i64;
            debug!(
                "【全量同步任务】表 {} 插入 {} 条数据",
                table_name,
                list.len()
            );
        }

        if row_count < PAGE_SIZE as usize {
            break;
        }
        page_num += 1;
    }

    Ok(total)
}

// ==================== 增量同步 ====================

/// Java: `@Scheduled(cron = "0 0 * * * ?") syncIncrementalData()`。
pub async fn sync_incremental_data(state: AppState) {
    info!("【增量同步任务】开始执行增量同步");
    let start = std::time::Instant::now();

    let current_month_table = current_table_name(&state);
    let last_sync_time = query_last_sync_time(&state, &current_month_table).await;

    let start_date = match last_sync_time {
        Some(value) => value.format(TIME_FORMAT).to_string(),
        None => {
            let now = Local::now().naive_local();
            now.date()
                .with_day(1)
                .and_then(|date| date.and_hms_opt(0, 0, 0))
                .unwrap_or(now)
                .format(TIME_FORMAT)
                .to_string()
        }
    };
    let end_date = Local::now().naive_local().format(TIME_FORMAT).to_string();
    info!(
        "【增量同步任务】同步时间范围: {} 至 {}",
        start_date, end_date
    );

    match sync_snapshot_flow_by_date_range(&state, &start_date, &end_date).await {
        Ok(count) => info!(
            "【增量同步任务】完成增量同步，同步记录数: {}, 耗时: {} ms",
            count,
            start.elapsed().as_millis()
        ),
        Err(err) => error!("【增量同步任务】增量同步失败: {}", err),
    }
}

async fn query_last_sync_time(state: &AppState, table_name: &str) -> Option<NaiveDateTime> {
    match check_table_exists(&state.db, table_name).await {
        Ok(0) => {
            warn!(
                "【增量同步任务】表 {} 不存在，将从本月初开始同步",
                table_name
            );
            None
        }
        Ok(_) => match get_max_snapshottime(&state.db, table_name).await {
            Ok(value) => value,
            Err(err) => {
                error!("【增量同步任务】查询最新snapshottime失败: {}", err);
                None
            }
        },
        Err(err) => {
            error!("【增量同步任务】查询最新snapshottime失败: {}", err);
            None
        }
    }
}

// ==================== 辅助方法 ====================

async fn fetch_from_gauss_db(
    state: &AppState,
    start_date: &str,
    end_date: &str,
    page_num: i32,
    page_size: i32,
) -> Option<remote::RemotePage> {
    let query = SnapshotFlowQuery {
        apply_time1: Some(start_date.to_string()),
        apply_time2: Some(end_date.to_string()),
        page_num: Some(page_num),
        page_size: Some(page_size),
    };
    match remote::get_snapshot_flow_page(state, &query).await {
        Ok(page) => Some(page),
        Err(err) => {
            error!("【分表同步任务】从GaussDB拉取数据失败: {}", err);
            None
        }
    }
}

/// Java: `groupByMonth` —— `LinkedHashMap` 保序。
fn group_by_month(
    table_prefix: &str,
    data_list: &[OdsRtSzdnSnapshotFlowAddcode],
) -> IndexMap<String, Vec<OdsRtSzdnSnapshotFlowAddcode>> {
    let mut grouped: IndexMap<String, Vec<OdsRtSzdnSnapshotFlowAddcode>> = IndexMap::new();
    for data in data_list {
        if let Some(snapshottime) = data.snapshottime {
            let table_name =
                physical_table_name(table_prefix, snapshottime, ShardingStrategy::Monthly);
            grouped.entry(table_name).or_default().push(data.clone());
        }
    }
    grouped
}

/// Java: `ShardingTableUtil.DEFAULT_TABLE_PREFIX` 是可配置项的等价物。
fn table_prefix(state: &AppState) -> String {
    state
        .settings
        .snapshot
        .flow
        .sharding
        .table_prefix
        .trim_end_matches('_')
        .to_string()
}

fn current_table_name(state: &AppState) -> String {
    physical_table_name(
        &table_prefix(&state),
        Local::now().naive_local(),
        ShardingStrategy::Monthly,
    )
}

// ==================== 手工入口 ====================

/// Java: `@Scheduled(cron = "0 0/5 * * * *") manualFullSync()`。
pub async fn manual_full_sync(state: AppState) -> AjaxResult {
    sync_full_data(state).await
}

/// Java: `manualIncrementalSync()` —— 文案固定，不反映真实结果。
pub async fn manual_incremental_sync(state: AppState) -> AjaxResult {
    sync_incremental_data(state).await;
    AjaxResult::success_msg("增量同步任务已触发")
}

/// Java: `preCreateTables(months)`。
pub async fn pre_create_tables(state: AppState, months: usize) {
    let table_names = crate::db::sharding::future_table_names(
        &table_prefix(&state),
        months,
        ShardingStrategy::Monthly,
        Local::now().naive_local(),
    );
    for table_name in &table_names {
        ensure_table_exists(&state, table_name).await;
    }
    info!(
        "【分表同步任务】已提前创建 {} 个未来分表",
        table_names.len()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    fn dt(y: i32, m: u32, d: u32) -> NaiveDateTime {
        NaiveDate::from_ymd_opt(y, m, d)
            .expect("date")
            .and_hms_opt(0, 0, 0)
            .expect("time")
    }

    #[test]
    fn month_partitions_include_both_ends() {
        // 起点是月末也不影响：游标钉在每月 1 日（见 get_month_partitions 的有意偏差说明）。
        let partitions = get_month_partitions(dt(2025, 1, 31), dt(2025, 4, 1));
        assert_eq!(partitions, vec!["202501", "202502", "202503", "202504"]);

        let rollover = get_month_partitions(dt(2025, 11, 30), dt(2026, 2, 1));
        assert_eq!(rollover, vec!["202511", "202512", "202601", "202602"]);
    }

    #[test]
    fn last_day_handles_leap_years() {
        assert_eq!(last_day_of_month(2024, 2), 29);
        assert_eq!(last_day_of_month(2025, 2), 28);
        assert_eq!(last_day_of_month(2025, 12), 31);
    }

    #[test]
    fn monthly_grouping_uses_snapshottime() {
        let rows = vec![
            OdsRtSzdnSnapshotFlowAddcode {
                big_id: Some("1".to_string()),
                snapshottime: Some(dt(2025, 8, 1)),
                ..Default::default()
            },
            OdsRtSzdnSnapshotFlowAddcode {
                big_id: Some("2".to_string()),
                snapshottime: Some(dt(2025, 8, 31)),
                ..Default::default()
            },
            OdsRtSzdnSnapshotFlowAddcode {
                big_id: Some("3".to_string()),
                snapshottime: Some(dt(2025, 9, 1)),
                ..Default::default()
            },
            // 没有抓拍时间的行会被丢弃（Java: if (data.getSnapshottime() != null)）。
            OdsRtSzdnSnapshotFlowAddcode {
                big_id: Some("4".to_string()),
                ..Default::default()
            },
        ];
        let grouped = group_by_month("ods_rt_szdn_snapshot_flow", &rows);
        assert_eq!(grouped.len(), 2);
        assert_eq!(grouped["ods_rt_szdn_snapshot_flow_202508"].len(), 2);
        assert_eq!(grouped["ods_rt_szdn_snapshot_flow_202509"].len(), 1);
        assert!(grouped["ods_rt_szdn_snapshot_flow_202508"][0]
            .snapshottime
            .is_some());
    }
}
