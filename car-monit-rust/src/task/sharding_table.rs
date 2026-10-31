// 来源: ruoyi-system/src/main/java/com/ruoyi/base/task/ShardingTableTask.java
// 职责: 每月 1 日提前创建未来 4 个月的分表。
// 对应关系: @Scheduled(cron = "0 0 1 1 * ?") -> task::JobKind::ShardingTables。

use tracing::{error, info};

use crate::db::sharding::{future_table_names, ShardingStrategy};
use crate::repository::snapshot_flow_repo::{check_table_exists, create_sharding_table};
use crate::state::AppState;

/// Java: `ShardingTableUtil.DEFAULT_TABLE_PREFIX`。
pub const DEFAULT_TABLE_PREFIX: &str = "ods_rt_szdn_snapshot_flow";

/// Java: `@Scheduled(cron = "0 0 1 1 * ?") createShardingTables()`
pub async fn create_sharding_tables(state: AppState) {
    info!("【分表定时任务】开始执行提前创建分表任务");

    let table_names = future_table_names(
        DEFAULT_TABLE_PREFIX,
        4,
        ShardingStrategy::Monthly,
        chrono::Local::now().naive_local(),
    );
    info!(
        "【分表定时任务】需要创建的分表数量: {}, 表名列表: {:?}",
        table_names.len(),
        table_names
    );

    let mut created = 0;
    let mut existed = 0;
    for table_name in &table_names {
        match check_table_exists(&state.db, table_name).await {
            Ok(count) if count > 0 => {
                info!("【分表定时任务】表 {} 已存在，跳过创建", table_name);
                existed += 1;
            }
            Ok(_) => match create_sharding_table(&state.db, table_name).await {
                Ok(()) => {
                    info!("【分表定时任务】成功创建分表: {}", table_name);
                    created += 1;
                }
                Err(err) => error!("【分表定时任务】创建分表失败: {} - {}", table_name, err),
            },
            Err(err) => error!("【分表定时任务】检查分表失败: {} - {}", table_name, err),
        }
    }

    info!(
        "【分表定时任务】执行完成，已存在表: {}, 新创建表: {}",
        existed, created
    );
}

/// Java: `manualCreateTables(int months)`。
pub async fn manual_create_tables(state: AppState, months: usize) -> String {
    info!("【分表手动任务】手动触发创建未来 {} 个月的分表", months);

    let table_names = future_table_names(
        DEFAULT_TABLE_PREFIX,
        months,
        ShardingStrategy::Monthly,
        chrono::Local::now().naive_local(),
    );
    let mut created = 0;
    let mut existed = 0;

    for table_name in &table_names {
        match check_table_exists(&state.db, table_name).await {
            Ok(count) if count > 0 => existed += 1,
            Ok(_) => match create_sharding_table(&state.db, table_name).await {
                Ok(()) => created += 1,
                Err(err) => {
                    error!("【分表手动任务】创建分表失败: {} - {}", table_name, err);
                    return format!("创建失败: {err}");
                }
            },
            Err(err) => return format!("创建失败: {err}"),
        }
    }

    format!("创建完成，已存在表: {existed}, 新创建表: {created}")
}

/// Java: `SnapshotFlowSyncTask.ensureTableExists` —— 不存在就建，异常只记日志。
pub async fn ensure_table_exists(state: &AppState, table_name: &str) {
    match check_table_exists(&state.db, table_name).await {
        Ok(0) => match create_sharding_table(&state.db, table_name).await {
            Ok(()) => info!("【分表同步任务】创建分表: {}", table_name),
            Err(err) => error!("【分表同步任务】创建分表失败: {}", err),
        },
        Ok(_) => {}
        Err(err) => error!("【分表同步任务】创建分表失败: {}", err),
    }
}
