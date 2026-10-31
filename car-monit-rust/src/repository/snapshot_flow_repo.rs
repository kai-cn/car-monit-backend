// 来源: ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml
// 职责: 分表同步所需的 mapper 子集（存在性/建表/水位线/批量插入/分表枚举）。
// 对应关系: OdsRtSzdnSnapshotFlowAddcodeMapper -> 同名 async 函数。

use chrono::NaiveDateTime;
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::domain::OdsRtSzdnSnapshotFlowAddcode;
use crate::error::AppError;

/// 主表（`CREATE TABLE ... LIKE` 的模板）。
pub const BASE_TABLE: &str = "ods_rt_szdn_snapshot_flow_addcode";

/// Java: `insertBatchToTable` 的列顺序。Java 版本还列了 19 个实体中不存在的字段
/// （smallpicturepath/gpsinfo/...），而实际建表 DDL 只有这 43 列，照抄会在 insert 时
/// 直接报 Unknown column。这里按真实表结构收敛到实体字段。
const INSERT_COLUMNS: &str = "big_id, datasource, cameratype, deviceid, gantrycode, gantryname, \
     roadcode, roadname, sectioncode, sectionname, tollcode, tollname, orgcode, orgname, direction, \
     hexcode, pileno, lon, lat, deviceip, siteid, laneid, snapshottimeunix, snapshottime, \
     receivedtimeunix, receivedtime, platenumber, platecolor, platecolorcode, platetype, \
     platetypecode, plateconfidence, carbrand, carcolor, carcolorcode, cartype, cartypecode, \
     cardirection, snappicturepath, loadtime, gradelevel, datauuid, reserve3";

/// 每批行数（43 列 × 500 行 ≈ 21500 个占位符，低于 MySQL 65535 上限）。
const INSERT_CHUNK_SIZE: usize = 500;

/// Java: `checkTableExists` —— 返回 1/0。
pub async fn check_table_exists(pool: &MySqlPool, table_name: &str) -> Result<i64, AppError> {
    let count: i64 = sqlx::query_scalar(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES \
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?",
    )
    .bind(table_name)
    .fetch_one(pool)
    .await?;
    Ok(count)
}

/// Java: `createShardingTable` —— `CREATE TABLE IF NOT EXISTS ${tableName} LIKE ...`。
pub async fn create_sharding_table(pool: &MySqlPool, table_name: &str) -> Result<(), AppError> {
    validate_table_name(table_name)?;
    let sql = format!("CREATE TABLE IF NOT EXISTS `{table_name}` LIKE {BASE_TABLE}");
    sqlx::query(&sql).execute(pool).await?;
    Ok(())
}

/// Java: `getMaxSnapshottime` —— 表内最大抓拍时间；空表返回 NULL。
pub async fn get_max_snapshottime(
    pool: &MySqlPool,
    table_name: &str,
) -> Result<Option<NaiveDateTime>, AppError> {
    validate_table_name(table_name)?;
    let sql = format!("SELECT MAX(t.snapshottime) FROM `{table_name}` t");
    let value = sqlx::query_scalar::<_, Option<NaiveDateTime>>(&sql)
        .fetch_one(pool)
        .await?;
    Ok(value)
}

/// Java: `listShardingTables` —— `LIKE CONCAT(#{tablePrefix}, '%') ORDER BY TABLE_NAME DESC`。
pub async fn list_sharding_tables(
    pool: &MySqlPool,
    table_prefix: &str,
) -> Result<Vec<String>, AppError> {
    let pattern = format!("{table_prefix}%");
    let names = sqlx::query_scalar::<_, String>(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES \
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME LIKE ? ORDER BY TABLE_NAME DESC",
    )
    .bind(pattern)
    .fetch_all(pool)
    .await?;
    Ok(names)
}

/// Java: `insertBatchToTable`。
///
/// 两处刻意差异（见 README-MIGRATION.md）：
/// 1. 只写真实存在的 43 列（Java 的 SQL 引用了不存在的列）；
/// 2. 使用 `INSERT IGNORE` —— `manualFullSync` 每 5 分钟跑一次全量，重复主键不应中断任务。
pub async fn insert_batch_to_table(
    pool: &MySqlPool,
    table_name: &str,
    rows: &[OdsRtSzdnSnapshotFlowAddcode],
) -> Result<(), AppError> {
    if rows.is_empty() {
        return Ok(());
    }
    validate_table_name(table_name)?;

    let mut tx = pool.begin().await?;
    for chunk in rows.chunks(INSERT_CHUNK_SIZE) {
        let mut builder = QueryBuilder::<MySql>::new(format!(
            "INSERT IGNORE INTO `{table_name}` ({INSERT_COLUMNS}) "
        ));
        builder.push_values(chunk, |mut bind, row| {
            bind.push_bind(row.big_id.as_deref())
                .push_bind(row.datasource.as_deref())
                .push_bind(row.cameratype.as_deref())
                .push_bind(row.deviceid.as_deref())
                .push_bind(row.gantrycode.as_deref())
                .push_bind(row.gantryname.as_deref())
                .push_bind(row.roadcode.as_deref())
                .push_bind(row.roadname.as_deref())
                .push_bind(row.sectioncode.as_deref())
                .push_bind(row.sectionname.as_deref())
                .push_bind(row.tollcode.as_deref())
                .push_bind(row.tollname.as_deref())
                .push_bind(row.orgcode.as_deref())
                .push_bind(row.orgname.as_deref())
                .push_bind(row.direction)
                .push_bind(row.hexcode.as_deref())
                .push_bind(row.pileno.as_deref())
                .push_bind(row.lon)
                .push_bind(row.lat)
                .push_bind(row.deviceip.as_deref())
                .push_bind(row.siteid)
                .push_bind(row.laneid)
                .push_bind(row.snapshottimeunix)
                .push_bind(row.snapshottime)
                .push_bind(row.receivedtimeunix)
                .push_bind(row.receivedtime)
                .push_bind(row.platenumber.as_deref())
                .push_bind(row.platecolor.as_deref())
                .push_bind(row.platecolorcode)
                .push_bind(row.platetype.as_deref())
                .push_bind(row.platetypecode)
                .push_bind(row.plateconfidence)
                .push_bind(row.carbrand.as_deref())
                .push_bind(row.carcolor.as_deref())
                .push_bind(row.carcolorcode)
                .push_bind(row.cartype.as_deref())
                .push_bind(row.cartypecode)
                .push_bind(row.cardirection.as_deref())
                .push_bind(row.snappicturepath.as_deref())
                .push_bind(row.loadtime)
                .push_bind(row.gradelevel)
                .push_bind(row.datauuid.as_deref())
                .push_bind(row.reserve3.as_deref());
        });
        builder.build().execute(&mut *tx).await?;
    }
    tx.commit().await?;
    Ok(())
}

/// 表名来自配置/分表算法，仍做白名单校验，避免 DDL 字符串拼接被注入。
fn validate_table_name(table_name: &str) -> Result<(), AppError> {
    let valid = !table_name.is_empty()
        && table_name.len() <= 64
        && table_name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_');
    if valid {
        Ok(())
    } else {
        Err(AppError::Service(format!("非法的分表名: {table_name}")))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn table_names_are_whitelisted() {
        assert!(validate_table_name("ods_rt_szdn_snapshot_flow_202508").is_ok());
        assert!(validate_table_name("ods_rt_szdn_snapshot_flow_202508; drop table x").is_err());
        assert!(validate_table_name("").is_err());
    }
}
