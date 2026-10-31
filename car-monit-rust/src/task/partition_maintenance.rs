// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/PartitionMaintenanceTask.java
// 职责: GaussDB 分区维护（预创建未来 6 个月分区 / 每周检查分区）。
// 对应关系: JdbcTemplate.execute/query -> sqlx。SQL 为 PostgreSQL/GaussDB 语法，
//           在 MySQL 上执行必然失败并记录 warn/error —— 与 Java 的 catch 行为一致。

use chrono::{Datelike, Months};
use tracing::{error, info, warn};

use crate::state::AppState;

const PRE_CREATE_MONTHS: i32 = 6;

/// Java: `PARTITION_TABLES` —— 表名 + 分区键（分区键当前未参与 SQL）。
const PARTITION_TABLES: &[(&str, &str)] = &[
    ("ods_rt_szdn_snapshot_flow_addcode", "snapshottime"),
    ("ods_lwzxsfsj_fee_records_01", "transtime"),
    ("zdata_trail_fitting", "extime"),
];

/// Java: `@Scheduled(cron = "0 0 1 1 * ?") createFuturePartitions()`
pub async fn create_future_partitions(state: AppState) {
    info!("[分区维护] 开始创建未来{}个月的分区", PRE_CREATE_MONTHS);

    let Some(current) = chrono::Local::now().date_naive().with_day(1) else {
        error!("[分区维护] 无法计算当前月份");
        return;
    };

    for offset in 1..=PRE_CREATE_MONTHS {
        let Some(start_month) = current.checked_add_months(Months::new(offset as u32)) else {
            continue;
        };
        let Some(end_month) = start_month.checked_add_months(Months::new(1)) else {
            continue;
        };
        let start_date = start_month.format("%Y-%m-%d").to_string();
        let end_date = end_month.format("%Y-%m-%d").to_string();
        let month_suffix = start_month.format("%Y%m").to_string();

        for (table_name, _field) in PARTITION_TABLES {
            let partition_name = format!("{table_name}_p{month_suffix}");
            let sql = format!(
                "CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF {table_name} \
                 FOR VALUES FROM ('{start_date}') TO ('{end_date}')"
            );
            match sqlx::query(&sql).execute(&state.db).await {
                Ok(_) => info!(
                    "[分区维护] 创建分区成功: {} (范围: {} ~ {})",
                    partition_name, start_date, end_date
                ),
                // Java: 分区已存在（或库不支持该语法）时只记 warn。
                Err(err) => warn!("[分区维护] 分区可能已存在: {} - {}", partition_name, err),
            }
        }
    }

    info!("[分区维护] 分区创建任务完成");
}

/// Java: `@Scheduled(cron = "0 0 2 * * MON") checkPartitionHealth()`
pub async fn check_partition_health(state: AppState) {
    info!("[分区维护] 开始检查分区健康状态");

    for (table_name, _field) in PARTITION_TABLES {
        let sql = format!(
            "SELECT inhrelid::regclass AS partition_name \
             FROM pg_inherits WHERE inhparent = '{table_name}'::regclass \
             ORDER BY partition_name"
        );
        match sqlx::query_scalar::<_, String>(&sql).fetch_all(&state.db).await {
            Ok(partitions) => {
                for partition in partitions {
                    info!("[分区维护] {} 分区: {}", table_name, partition);
                }
            }
            Err(err) => error!("[分区维护] 检查表分区失败: {} - {}", table_name, err),
        }
    }

    info!("[分区维护] 分区健康检查完成");
}
