// 来源: ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/SnapshotFlowEnhancedService.java
//       ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingTableUtil.java
// 职责: 门架抓拍流水跨月分表查询（本地 MySQL 优先）。
// 对应关系: queryPage -> query_page；queryListForExport -> query_list_for_export。
//
// 注意：Java 成功路径返回的是 `new TableDataInfo()`（code=0、msg=null），
// 时间校验失败/异常路径才回 200/"查询成功" —— 照抄。

use std::collections::HashMap;

use chrono::{NaiveDateTime, Timelike};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;
use tracing::{info, warn};

use crate::db::rows::rows_to_json;
use crate::db::sharding::{physical_table_name, table_names_by_date_range, ShardingStrategy};
use crate::response::TableDataInfo;
use crate::state::AppState;
use serde_json::Value;

/// Java: `ShardingTableUtil.DEFAULT_TABLE_PREFIX`（增强查询固定用默认前缀）。
pub const TABLE_PREFIX: &str = "ods_rt_szdn_snapshot_flow";

const COLUMNS: &str = "t.big_id, t.datasource, t.cameratype, t.deviceid, t.gantrycode, \
     t.gantryname, t.roadcode, t.roadname, t.sectioncode, t.sectionname, t.tollcode, \
     t.tollname, t.orgcode, t.orgname, t.direction, t.hexcode, t.pileno, t.lon, t.lat, \
     t.deviceip, t.siteid, t.laneid, t.snapshottimeunix, t.snapshottime, t.receivedtimeunix, \
     t.receivedtime, t.platenumber, t.platecolor, t.platecolorcode, t.platetype, \
     t.platetypecode, t.plateconfidence, t.carbrand, t.carcolor, t.carcolorcode, t.cartype, \
     t.cartypecode, t.cardirection, t.snappicturepath, t.loadtime, t.gradelevel, t.datauuid, \
     t.reserve3";

/// Java: `queryPage(queryParam)`。
pub async fn query_page(
    state: &AppState,
    params: &HashMap<String, String>,
) -> TableDataInfo<Value> {
    let mut result = TableDataInfo::new(0, Vec::new());

    if !validate_time_range(params) {
        warn!("【时间校验】查询时间范围无效或超过当前时间，返回空数据");
        return result;
    }

    let range = match time_range(params) {
        Some(range) => range,
        None => return result,
    };
    let tables =
        table_names_by_date_range(TABLE_PREFIX, range.0, range.1, ShardingStrategy::Monthly);
    match query_from_sharding_tables(state, params, &tables).await {
        Ok(page) => page,
        Err(err) => {
            warn!("【分表查询】查询失败: {err}");
            result.total = 0;
            result.rows.clear();
            result
        }
    }
}

/// Java: `queryListForExport(queryParam)` —— 不分页，跨表合并后按时间倒序。
pub async fn query_list_for_export(
    state: &AppState,
    params: &HashMap<String, String>,
) -> Result<Vec<Value>, String> {
    let range = time_range(params).ok_or_else(|| "时间范围缺失".to_string())?;
    let tables =
        table_names_by_date_range(TABLE_PREFIX, range.0, range.1, ShardingStrategy::Monthly);
    let mut all = Vec::new();
    for table in &tables {
        match select_list(state, table, params, 0, params_page_size(params)).await {
            Ok(mut rows) => all.append(&mut rows),
            Err(err) => warn!("【导出查询】表 {} 查询失败: {}", table, err),
        }
    }
    sort_desc(&mut all);
    Ok(all)
}

async fn query_from_sharding_tables(
    state: &AppState,
    params: &HashMap<String, String>,
    tables: &[String],
) -> Result<TableDataInfo<Value>, String> {
    let current_table = physical_table_name(
        TABLE_PREFIX,
        chrono::Local::now().naive_local(),
        ShardingStrategy::Monthly,
    );

    let mut total = 0i64;
    for table in tables {
        let count = if table == &current_table {
            select_count(state, table, params).await
        } else {
            approximate_count(state, table, params).await
        };
        match count {
            Ok(count) => total += count,
            Err(err) => warn!("【分表统计】表 {} 不存在或查询失败: {}", table, err),
        }
    }

    let page_num = params
        .get("pageNum")
        .and_then(|value| value.parse::<i64>().ok())
        .unwrap_or(1);
    let page_size = params_page_size(params);
    let offset = (page_num - 1) * page_size;

    if total <= offset {
        return Ok(TableDataInfo {
            total,
            rows: Vec::new(),
            code: 0,
            msg: None,
        });
    }

    let mut all = Vec::new();
    let mut remaining = page_size;
    let mut current_offset = offset;
    for table in tables {
        if remaining <= 0 {
            break;
        }
        let table_count = match select_count(state, table, params).await {
            Ok(count) => count,
            Err(err) => {
                warn!("【分页查询】表 {} 查询失败: {}", table, err);
                continue;
            }
        };
        if current_offset >= table_count {
            current_offset -= table_count;
            continue;
        }
        match select_list(state, table, params, current_offset, page_size).await {
            Ok(rows) => {
                let take = rows.len().min(remaining as usize);
                all.extend(rows.into_iter().take(take));
                remaining -= take as i64;
                current_offset = 0;
            }
            Err(err) => warn!("【分页查询】表 {} 查询失败: {}", table, err),
        }
    }

    sort_desc(&mut all);
    info!(
        "【分表查询完成】总记录数: {}, 当前页数据量: {}",
        total,
        all.len()
    );
    Ok(TableDataInfo {
        total,
        rows: all,
        code: 0,
        msg: None,
    })
}

async fn approximate_count(
    state: &AppState,
    table: &str,
    params: &HashMap<String, String>,
) -> Result<i64, String> {
    if has_extra_filters(params) {
        return select_count(state, table, params).await;
    }
    let approx = sqlx::query_scalar::<_, Option<u64>>(
        "SELECT TABLE_ROWS FROM INFORMATION_SCHEMA.TABLES \
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?",
    )
    .bind(table)
    .fetch_one(&state.db)
    .await;
    match approx {
        Ok(Some(count)) if count > 0 => return Ok(count as i64),
        Ok(_) => {}
        Err(err) => warn!("【近似计数】获取表 {} 近似行数失败: {}", table, err),
    }
    select_count(state, table, params).await
}

async fn select_count(
    state: &AppState,
    table: &str,
    params: &HashMap<String, String>,
) -> Result<i64, String> {
    if !valid_table(table) {
        return Err(format!("非法的分表名: {table}"));
    }
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "SELECT CAST(COUNT(1) AS CHAR) FROM {table} t WHERE 1=1"
    ));
    push_filters(&mut builder, params);
    let text: Option<String> = builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await
        .map_err(|err| err.to_string())?;
    Ok(text
        .and_then(|value| value.parse::<i64>().ok())
        .unwrap_or(0))
}

async fn select_list(
    state: &AppState,
    table: &str,
    params: &HashMap<String, String>,
    offset: i64,
    page_size: i64,
) -> Result<Vec<Value>, String> {
    if !valid_table(table) {
        return Err(format!("非法的分表名: {table}"));
    }
    let mut builder =
        QueryBuilder::<MySql>::new(format!("SELECT {COLUMNS} FROM {table} t WHERE 1=1"));
    push_filters(&mut builder, params);
    builder.push(" ORDER BY t.snapshottime DESC LIMIT ");
    builder.push_bind(offset);
    builder.push(", ");
    builder.push_bind(page_size);
    let rows = builder
        .build()
        .fetch_all(&state.db)
        .await
        .map_err(|err| err.to_string())?;
    Ok(rows_to_json(&rows))
}

fn push_filters(builder: &mut QueryBuilder<MySql>, params: &HashMap<String, String>) {
    let value = |key: &str| {
        params
            .get(key)
            .map(|value| value.trim())
            .filter(|value| !value.is_empty())
    };
    for (param, column) in [
        ("bigId", "big_id"),
        ("datasource", "datasource"),
        ("cameratype", "cameratype"),
        ("deviceid", "deviceid"),
        ("gantrycode", "gantrycode"),
        ("roadcode", "roadcode"),
        ("sectioncode", "sectioncode"),
        ("tollcode", "tollcode"),
        ("orgcode", "orgcode"),
        ("platenumber", "platenumber"),
        ("platecolor", "platecolor"),
        ("cartype", "cartype"),
    ] {
        if let Some(value) = value(param) {
            builder.push(format!(" and t.{column} = "));
            builder.push_bind(value.to_string());
        }
    }
    for (param, column) in [
        ("gantryname", "gantryname"),
        ("roadname", "roadname"),
        ("sectionname", "sectionname"),
        ("tollname", "tollname"),
        ("orgname", "orgname"),
    ] {
        if let Some(value) = value(param) {
            builder.push(format!(" and t.{column} like concat('%', "));
            builder.push_bind(value.to_string());
            builder.push(", '%')");
        }
    }
    // Java: `direction != null` —— Integer 字段，0 也参与过滤。
    if let Some(value) = params.get("direction").filter(|value| !value.is_empty()) {
        builder.push(" and t.direction = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = value("applyTime1") {
        builder.push(" and t.snapshottime >= ");
        builder.push_bind(value.to_string());
    }
    if let Some(value) = value("applyTime2") {
        builder.push(" and t.snapshottime <= ");
        builder.push_bind(value.to_string());
    }
    if let Some(value) = value("sectionCodeStr") {
        builder.push(" and find_in_set(t.sectioncode, ");
        builder.push_bind(value.to_string());
        builder.push(")");
    }
}

fn has_extra_filters(params: &HashMap<String, String>) -> bool {
    let present = |key: &str| {
        params
            .get(key)
            .map(|value| !value.trim().is_empty())
            .unwrap_or(false)
    };
    present("platenumber")
        || present("deviceid")
        || present("gantrycode")
        || present("sectionCodeStr")
        || params
            .get("direction")
            .map(|value| !value.is_empty())
            .unwrap_or(false)
        || present("platecolor")
        || present("cartype")
        || present("datasource")
}

fn params_page_size(params: &HashMap<String, String>) -> i64 {
    params
        .get("pageSize")
        .and_then(|value| value.parse().ok())
        .unwrap_or(10)
}

fn valid_table(table: &str) -> bool {
    !table.is_empty()
        && table.len() <= 64
        && table
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
}

/// Java: `validateTimeRange` —— 空参数 true；格式非法/超过当前时间/起大于止 false。
fn validate_time_range(params: &HashMap<String, String>) -> bool {
    let start = params
        .get("applyTime1")
        .map(|value| value.trim())
        .unwrap_or("");
    let end = params
        .get("applyTime2")
        .map(|value| value.trim())
        .unwrap_or("");
    if start.is_empty() && end.is_empty() {
        return true;
    }
    let Some((start, end)) = parse_range(start, end) else {
        return false;
    };
    let now = chrono::Local::now().naive_local();
    if start > now || end > now || start > end {
        return false;
    }
    true
}

fn time_range(params: &HashMap<String, String>) -> Option<(NaiveDateTime, NaiveDateTime)> {
    let start = params
        .get("applyTime1")
        .map(|value| value.trim())
        .unwrap_or("");
    let end = params
        .get("applyTime2")
        .map(|value| value.trim())
        .unwrap_or("");
    parse_range(start, end)
}

fn parse_range(start: &str, end: &str) -> Option<(NaiveDateTime, NaiveDateTime)> {
    if start.is_empty() || end.is_empty() {
        return None;
    }
    let start = with_seconds(start, " 00:00:00");
    let end = with_seconds(end, " 23:59:59");
    let start = NaiveDateTime::parse_from_str(&start, "%Y-%m-%d %H:%M:%S").ok()?;
    let end = NaiveDateTime::parse_from_str(&end, "%Y-%m-%d %H:%M:%S").ok()?;
    if start.second() > 59 {
        return None;
    }
    Some((start, end))
}

fn with_seconds(value: &str, suffix: &str) -> String {
    if value.len() == 10 {
        format!("{value}{suffix}")
    } else {
        value.to_string()
    }
}

/// Java: `Comparator.comparing(snapshottime).reversed()` —— null 排在最后。
fn sort_desc(rows: &mut [Value]) {
    rows.sort_by(|left, right| {
        let left = left.get("snapshottime").and_then(Value::as_str);
        let right = right.get("snapshottime").and_then(Value::as_str);
        match (left, right) {
            (Some(left), Some(right)) => right.cmp(left),
            (Some(_), None) => std::cmp::Ordering::Less,
            (None, Some(_)) => std::cmp::Ordering::Greater,
            (None, None) => std::cmp::Ordering::Equal,
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn time_range_defaults_fill_seconds() {
        let (start, end) = parse_range("2025-08-01", "2025-08-31").expect("range");
        assert_eq!(start.to_string(), "2025-08-01 00:00:00");
        assert_eq!(end.to_string(), "2025-08-31 23:59:59");
    }

    #[test]
    fn future_range_fails_validation() {
        let mut params = HashMap::new();
        params.insert("applyTime1".to_string(), "2999-01-01".to_string());
        params.insert("applyTime2".to_string(), "2999-01-02".to_string());
        assert!(!validate_time_range(&params));
    }
}
