// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/JobInvokeUtil.java
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/AbstractQuartzJob.java
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobServiceImpl.java
// 职责: sys_job 的运行时调度（Quartz RAM -> tokio 循环）与执行日志。
// 对应关系: Scheduler.scheduleJob/pauseJob/resumeJob/triggerJob -> registry + tokio::spawn。

use std::collections::HashMap;
use std::sync::{LazyLock, Mutex};

use serde_json::{json, Value};

use crate::api::support;
use crate::error::AppError;
use crate::state::AppState;
use crate::task;

type JobHandle = tokio::task::JoinHandle<()>;

static JOBS: LazyLock<Mutex<HashMap<i64, JobHandle>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

/// Java: JobInvokeUtil 的 bean 白名单。
pub const ALLOWED_BEANS: &[&str] = &[
    "ryTask",
    "vehicleMonitoringTask",
    "orgTask",
    "trackTask",
    "partitionMaintenanceTask",
    "snapshotFlowSyncTask",
    "shardingTableTask",
    "viewMaintenanceTask",
];

pub fn valid_target(target: &str) -> bool {
    let bean = target
        .split_once('.')
        .map(|(bean, _)| bean)
        .unwrap_or_default();
    ALLOWED_BEANS.contains(&bean)
}

/// Java: SysJobServiceImpl.init —— 启动时把 status=0 的任务装入调度器。
pub fn start_jobs(state: &AppState) {
    let state = state.clone();
    tokio::spawn(async move {
        let rows = sqlx::query_as::<_, (i64, String, Option<String>, Option<String>)>(
            "select job_id, invoke_target, cron_expression, job_name from sys_job where status = '0'",
        )
        .fetch_all(&state.db)
        .await;
        match rows {
            Ok(rows) => {
                for (job_id, invoke_target, cron, job_name) in rows {
                    if let Some(cron) = cron {
                        schedule(
                            &state,
                            job_id,
                            &cron,
                            &invoke_target,
                            job_name.as_deref().unwrap_or_default(),
                        );
                    }
                }
            }
            Err(err) => tracing::warn!("[定时任务] 加载 sys_job 失败: {err}"),
        }
    });
}

/// 注册/替换某个 sys_job。
pub fn schedule(
    state: &AppState,
    job_id: i64,
    cron: &str,
    invoke_target: &str,
    job_name: &str,
) {
    unschedule(job_id);
    let Ok(expression) = crate::task::cron::CronExpression::parse(cron) else {
        tracing::warn!("[定时任务] job {job_id} 的 cron 非法: {cron}");
        return;
    };
    let state = state.clone();
    let invoke_target = invoke_target.to_string();
    let job_name = job_name.to_string();
    let handle = tokio::spawn(async move {
        let mut after = chrono::Local::now().naive_local();
        loop {
            let Some(next) = expression.next_after(after) else { break };
            let wait = (next - chrono::Local::now().naive_local()).num_milliseconds();
            if wait > 0 {
                tokio::time::sleep(std::time::Duration::from_millis(wait as u64)).await;
            }
            run_job(&state, job_id, &job_name, &invoke_target).await;
            after = next;
        }
    });
    JOBS.lock().unwrap().insert(job_id, handle);
}

pub fn unschedule(job_id: i64) {
    if let Some(handle) = JOBS.lock().unwrap().remove(&job_id) {
        handle.abort();
    }
}

/// Java: Scheduler.triggerJob —— 立即执行一次。
pub fn run_once(state: &AppState, job_id: i64, job_name: &str, invoke_target: &str) {
    let state = state.clone();
    let job_name = job_name.to_string();
    let invoke_target = invoke_target.to_string();
    tokio::spawn(async move {
        run_job(&state, job_id, &job_name, &invoke_target).await;
    });
}

async fn run_job(state: &AppState, job_id: i64, job_name: &str, invoke_target: &str) {
    let started = chrono::Local::now().naive_local();
    let outcome = dispatch_job(state, invoke_target).await;
    let stopped = chrono::Local::now().naive_local();
    let (status, message, exception) = match &outcome {
        Ok(()) => ("0", "任务执行成功", String::new()),
        Err(err) => ("1", "任务执行失败", err.clone()),
    };
    if let Err(err) = outcome {
        tracing::error!("[定时任务] job {job_id} ({job_name}) 执行失败: {err}");
    }
    let elapsed = (stopped - started).num_milliseconds();
    let body = json!({
        "jobName": job_name,
        "jobGroup": "DEFAULT",
        "invokeTarget": invoke_target,
        "jobMessage": format!("{message}  共耗时：{elapsed} 毫秒"),
        "status": status,
        "exceptionInfo": if exception.is_empty() { Value::Null } else { json!(truncate(&exception, 2000)) },
    });
    if let Err(err) = support::insert_entity(&state.db, "sys_job_log", &body, support::AutoFill::NONE).await {
        tracing::warn!("[定时任务] 写入 sys_job_log 失败: {err}");
    }
}

fn log_count(label: &str, result: Result<usize, AppError>) {
    match result {
        Ok(count) => tracing::info!("[定时任务] {label}同步完成，共 {count} 条"),
        Err(err) => tracing::error!("[定时任务] {label}同步失败: {err}"),
    }
}

fn truncate(text: &str, max: usize) -> String {
    text.chars().take(max).collect()
}

/// Java: AbstractQuartzJob.execute -> JobInvokeUtil.invokeMethod —— 仅迁移本仓库内的任务 Bean。
pub async fn dispatch_job(state: &AppState, target: &str) -> Result<(), String> {
    let state = state.clone();
    match target {
        "partitionMaintenanceTask.createFuturePartitions" => {
            task::run_partition_create(&state).await;
        }
        "partitionMaintenanceTask.checkPartitionHealth" => {
            task::run_partition_health(&state).await;
        }
        "snapshotFlowSyncTask.syncIncrementalData" => {
            task::run_incremental_sync(&state).await;
        }
        "snapshotFlowSyncTask.manualFullSync" => {
            task::run_full_sync(&state).await;
        }
        "shardingTableTask.createShardingTables" => {
            task::run_sharding_tables(&state).await;
        }
        "viewMaintenanceTask.scheduledViewMaintenance" => {
            task::run_view_maintenance(&state).await;
        }
        "vehicleMonitoringTask.syncOrgInfo" => {
            log_count("机构信息", crate::task::manager_sync::sync_org(&state).await);
        }
        "vehicleMonitoringTask.syncSectionInfo" => {
            log_count("路段信息", crate::task::manager_sync::sync_section(&state).await);
        }
        "vehicleMonitoringTask.syncGantryInfo" => {
            log_count("门架信息", crate::task::manager_sync::sync_gantry(&state).await);
        }
        "vehicleMonitoringTask.syncServiceAreaInfoInfo" => {
            log_count(
                "服务区信息",
                crate::task::manager_sync::sync_service_area(&state).await,
            );
        }
        "vehicleMonitoringTask.syncTollBoothInfoInfo" => {
            log_count(
                "收费所信息",
                crate::task::manager_sync::sync_toll_booth(&state).await,
            );
        }
        "vehicleMonitoringTask.syncSfzjcxxInfoInfo" => {
            log_count(
                "收费站基础信息位置",
                crate::task::manager_sync::sync_sfzjcxx(&state).await,
            );
        }
        "vehicleMonitoringTask.syncTollStationInfo" => {
            log_count(
                "收费站信息",
                crate::task::manager_sync::sync_toll_station(&state).await,
            );
        }
        // Java: OrgTask.syncOrgInfo 方法体全部注释，等价于空操作。
        "orgTask.syncOrgInfo" => {
            tracing::info!("[定时任务] orgTask.syncOrgInfo（Java 方法体已注释，跳过）");
        }
        "trackTask.syncCurrentTrack" => {
            if let Err(err) = crate::task::manager_sync::sync_current_track(&state).await {
                return Err(format!("实时轨迹同步失败: {err}"));
            }
        }
        "trackTask.syncSuspiciousCar" => {
            if let Err(err) = crate::task::manager_sync::sync_suspicious_car(&state, &[]).await {
                return Err(format!("可疑车辆同步失败: {err}"));
            }
        }
        "trackTask.syncHistoryTrack" => {
            log_count(
                "历史轨迹",
                crate::task::manager_sync::sync_history_track(&state).await,
            );
        }
        "trackTask.saveCarExcept" => {
            log_count(
                "逃费金额回写",
                crate::task::manager_sync::save_car_except(&state).await,
            );
        }
        // Java: TrackTask.syncHistoryTrackNoCar 方法体全部注释，等价于空操作。
        "trackTask.syncHistoryTrackNoCar" => {
            tracing::info!("[定时任务] trackTask.syncHistoryTrackNoCar（方法体已注释，跳过）");
        }
        "trackTask.changeCarSuspicious" => {
            match crate::task::manager_sync::change_car_suspicious(&state).await {
                Ok((moved, removed)) => {
                    tracing::info!("[定时任务] 可疑车辆迁移完成，迁移 {} 条，删除 {} 条", moved, removed);
                }
                Err(err) => return Err(format!("可疑车辆迁移失败: {err}")),
            }
        }
        other if other.starts_with("ryTask.") => {
            tracing::info!("[定时任务] 执行演示任务: {other}");
        }
        other => {
            return Err(format!(
                "任务 {other} 尚未迁移（依赖远端 HttpBaseInfoApiService / 轨迹同步），已跳过"
            ));
        }
    }
    Ok(())
}
