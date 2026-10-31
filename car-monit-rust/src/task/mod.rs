// 来源: Spring `@EnableScheduling` + 6 个 `@Scheduled` 方法（Java 侧因缺少注解从未触发）。
// 职责: 按 cron 触发用户要求“必须生效”的 6 个定时任务。
// 对应关系: TaskScheduler -> 每个任务一个 tokio 循环；@Scheduled(cron) -> CronExpression。

pub mod cron;
pub mod manager_sync;
pub mod partition_maintenance;
pub mod remote;
pub mod sharding_table;
pub mod snapshot_flow_sync;
pub mod view_maintenance;

use std::sync::Arc;

use tracing::{error, info, warn};

use crate::state::AppState;
use cron::CronExpression;

/// Java 4 个任务类中的 6 个 `@Scheduled` 方法。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JobKind {
    /// PartitionMaintenanceTask.createFuturePartitions
    PartitionCreate,
    /// PartitionMaintenanceTask.checkPartitionHealth
    PartitionHealth,
    /// SnapshotFlowSyncTask.syncIncrementalData
    IncrementalSync,
    /// SnapshotFlowSyncTask.manualFullSync
    FullSync,
    /// ShardingTableTask.createShardingTables
    ShardingTables,
    /// ViewMaintenanceTask.scheduledViewMaintenance
    ViewMaintenance,
}

impl JobKind {
    pub const ALL: [JobKind; 6] = [
        JobKind::PartitionCreate,
        JobKind::PartitionHealth,
        JobKind::IncrementalSync,
        JobKind::FullSync,
        JobKind::ShardingTables,
        JobKind::ViewMaintenance,
    ];

    pub fn name(self) -> &'static str {
        match self {
            JobKind::PartitionCreate => "partitionMaintenanceTask.createFuturePartitions",
            JobKind::PartitionHealth => "partitionMaintenanceTask.checkPartitionHealth",
            JobKind::IncrementalSync => "snapshotFlowSyncTask.syncIncrementalData",
            JobKind::FullSync => "snapshotFlowSyncTask.manualFullSync",
            JobKind::ShardingTables => "shardingTableTask.createShardingTables",
            JobKind::ViewMaintenance => "viewMaintenanceTask.scheduledViewMaintenance",
        }
    }

    /// 与 Java 注解逐字一致。
    pub fn cron(self) -> &'static str {
        match self {
            JobKind::PartitionCreate => "0 0 1 1 * ?",
            JobKind::PartitionHealth => "0 0 2 * * MON",
            JobKind::IncrementalSync => "0 0 * * * ?",
            JobKind::FullSync => "0 0/5 * * * *",
            JobKind::ShardingTables => "0 0 1 1 * ?",
            JobKind::ViewMaintenance => "0 0 2 1 * ?",
        }
    }

    async fn run(self, state: Arc<AppState>) {
        // 任务函数接收所有权（AppState 内部全是 Arc/连接池，克隆很轻），
        // 避免 `&AppState` 跨 await 触发 rustc 的 “Send is not general enough”。
        let state = (*state).clone();
        match self {
            JobKind::PartitionCreate => {
                partition_maintenance::create_future_partitions(state).await
            }
            JobKind::PartitionHealth => {
                partition_maintenance::check_partition_health(state).await
            }
            JobKind::IncrementalSync => {
                snapshot_flow_sync::sync_incremental_data(state).await
            }
            JobKind::FullSync => {
                snapshot_flow_sync::manual_full_sync(state).await;
            }
            JobKind::ShardingTables => sharding_table::create_sharding_tables(state).await,
            JobKind::ViewMaintenance => {
                view_maintenance::scheduled_view_maintenance(state).await;
            }
        }
    }
}

/// sys_job 调度器调用入口（与 JobKind 共享同一套任务实现）。
pub async fn run_partition_create(state: &AppState) {
    partition_maintenance::create_future_partitions(state.clone()).await;
}

pub async fn run_partition_health(state: &AppState) {
    partition_maintenance::check_partition_health(state.clone()).await;
}

pub async fn run_incremental_sync(state: &AppState) {
    snapshot_flow_sync::sync_incremental_data(state.clone()).await;
}

pub async fn run_full_sync(state: &AppState) {
    snapshot_flow_sync::manual_full_sync(state.clone()).await;
}

pub async fn run_sharding_tables(state: &AppState) {
    sharding_table::create_sharding_tables(state.clone()).await;
}

pub async fn run_view_maintenance(state: &AppState) {
    view_maintenance::scheduled_view_maintenance(state.clone()).await;
}

/// 启动全部 `@Scheduled` 任务。
pub fn start_scheduler(state: &AppState) {
    if !state.settings.app.scheduled_annotations_enabled {
        warn!("[定时任务] app.scheduled_annotations_enabled=false，@Scheduled 任务不会执行");
        return;
    }

    let state = Arc::new(state.clone());
    let mut registered = 0;
    for kind in JobKind::ALL {
        match CronExpression::parse(kind.cron()) {
            Ok(cron) => {
                // 显式装箱成 `Send` future，规避 rustc 对 async fn 生命周期的
                // “Send is not general enough”误判。
                let future: std::pin::Pin<Box<dyn std::future::Future<Output = ()> + Send>> =
                    Box::pin(run_loop(state.clone(), kind, cron));
                tokio::spawn(future);
                registered += 1;
            }
            Err(err) => error!("[定时任务] {} 的 cron 非法: {}", kind.name(), err),
        }
    }
    info!("[定时任务] 已注册 {registered} 个 @Scheduled 任务");
}

async fn run_loop(state: Arc<AppState>, kind: JobKind, cron: CronExpression) {
    let mut after = chrono::Local::now().naive_local();
    loop {
        let Some(next) = cron.next_after(after) else {
            error!("[定时任务] {} 无法计算下一次触发时间，循环结束", kind.name());
            return;
        };
        let now = chrono::Local::now().naive_local();
        let delay = (next - now).to_std().unwrap_or_default();
        tokio::time::sleep(delay).await;

        info!("[定时任务] 触发 {}，cron={}", kind.name(), kind.cron());
        kind.run(state.clone()).await;
        after = chrono::Local::now().naive_local();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_java_cron_expressions_parse() {
        for kind in JobKind::ALL {
            CronExpression::parse(kind.cron()).unwrap_or_else(|err| panic!("{}: {err}", kind.name()));
        }
    }

    #[test]
    fn six_scheduled_methods_are_registered() {
        assert_eq!(JobKind::ALL.len(), 6);
    }

    #[test]
    fn app_state_is_send_sync() {
        fn assert_send_sync<T: Send + Sync>() {}
        assert_send_sync::<AppState>();
    }
}
