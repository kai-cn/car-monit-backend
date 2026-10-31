// 来源: ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingTableUtil.java
//       ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingConfig.java
//       ruoyi-system/src/main/java/com/ruoyi/base/sharding/SnapshotFlowMonthShardingAlgorithm.java
//       ruoyi-system/src/main/java/com/ruoyi/base/sharding/FeeRecordsDayShardingAlgorithm.java
//       ruoyi-admin/src/main/java/com/ruoyi/admin/config/ShardingSphereConfig.java
// 职责: 分表策略、物理表名计算、时间范围分表枚举、精确/范围路由。
// 对应关系: ShardingTableUtil -> 同名函数；ShardingSphere 算法 -> ShardingRouter。

use chrono::{Datelike, Months, NaiveDateTime};
use sqlx::{MySqlPool, Row};

use crate::config::Settings;
use crate::error::AppError;

pub const SNAPSHOT_FLOW_LOGICAL: &str = "ods_rt_szdn_snapshot_flow";
pub const FEE_RECORDS_LOGICAL: &str = "ods_lwzxsfsj_fee_records";
/// Java: ShardingSphereConfig 的 dataNodes 固定从 2025 年建到 2099 年。
pub const FIRST_SHARD_YEAR: i32 = 2025;
pub const LAST_SHARD_YEAR: i32 = 2099;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ShardingStrategy {
    Monthly,
    Daily,
    Quarterly,
    Yearly,
}

impl ShardingStrategy {
    /// Java: ShardingConfig.ShardingStrategy 枚举名（YAML 中写成 month/monthly 均可）。
    pub fn parse(value: &str) -> Option<Self> {
        match value.trim().to_ascii_lowercase().as_str() {
            "month" | "monthly" => Some(Self::Monthly),
            "day" | "daily" => Some(Self::Daily),
            "quarter" | "quarterly" => Some(Self::Quarterly),
            "year" | "yearly" => Some(Self::Yearly),
            _ => None,
        }
    }

    /// Java: ShardingTableUtil.getTableSuffix
    pub fn suffix(&self, date: NaiveDateTime) -> String {
        let quarter = (date.month() - 1) / 3 + 1;
        match self {
            Self::Daily => format!("{:04}{:02}{:02}", date.year(), date.month(), date.day()),
            Self::Monthly => format!("{:04}{:02}", date.year(), date.month()),
            Self::Quarterly => format!("{:04}Q{}", date.year(), quarter),
            Self::Yearly => format!("{:04}", date.year()),
        }
    }

    /// Java: ShardingTableUtil.advanceCalendar
    fn advance(&self, date: NaiveDateTime) -> NaiveDateTime {
        match self {
            Self::Daily => date + chrono::Days::new(1),
            Self::Monthly => date + Months::new(1),
            Self::Quarterly => date + Months::new(3),
            Self::Yearly => date + Months::new(12),
        }
    }
}

/// Java: ShardingTableUtil.getTableNameByDate —— 前缀 + "_" + 后缀。
/// 配置中的 table-prefix 可能已带下划线，这里统一去掉再拼接。
pub fn physical_table_name(
    table_prefix: &str,
    date: NaiveDateTime,
    strategy: ShardingStrategy,
) -> String {
    format!(
        "{}_{}",
        table_prefix.trim_end_matches('_'),
        strategy.suffix(date)
    )
}

/// Java: ShardingTableUtil.getPeriodStart
pub fn period_start(date: NaiveDateTime, strategy: ShardingStrategy) -> NaiveDateTime {
    match strategy {
        ShardingStrategy::Daily => date.date().and_hms_opt(0, 0, 0).expect("midnight"),
        ShardingStrategy::Monthly => date
            .date()
            .with_day(1)
            .expect("valid day")
            .and_hms_opt(0, 0, 0)
            .expect("midnight"),
        ShardingStrategy::Quarterly => {
            let month = ((date.month() - 1) / 3) * 3 + 1;
            date.date()
                .with_day(1)
                .and_then(|d| d.with_month(month))
                .expect("valid quarter start")
                .and_hms_opt(0, 0, 0)
                .expect("midnight")
        }
        ShardingStrategy::Yearly => date
            .date()
            .with_month(1)
            .and_then(|d| d.with_day(1))
            .expect("valid year start")
            .and_hms_opt(0, 0, 0)
            .expect("midnight"),
    }
}

/// Java: ShardingTableUtil.getPeriodEnd —— 周期下一段起点减 1 毫秒。
pub fn period_end(date: NaiveDateTime, strategy: ShardingStrategy) -> NaiveDateTime {
    let start = period_start(date, strategy);
    let next = strategy.advance(start);
    next - chrono::Duration::milliseconds(1)
}

/// Java: ShardingTableUtil.getTableNamesByDateRange —— 含起止周期的去重表名列表。
pub fn table_names_by_date_range(
    table_prefix: &str,
    start: NaiveDateTime,
    end: NaiveDateTime,
    strategy: ShardingStrategy,
) -> Vec<String> {
    let mut names = Vec::new();
    let mut cursor = period_start(start, strategy);
    while cursor <= end {
        let name = physical_table_name(table_prefix, cursor, strategy);
        if !names.contains(&name) {
            names.push(name);
        }
        cursor = strategy.advance(cursor);
    }
    names
}

/// Java: ShardingTableUtil.getFutureTableNames —— 从当前周期起 N 个周期。
pub fn future_table_names(
    table_prefix: &str,
    periods: usize,
    strategy: ShardingStrategy,
    now: NaiveDateTime,
) -> Vec<String> {
    let mut names = Vec::new();
    let mut cursor = period_start(now, strategy);
    for _ in 0..periods {
        let name = physical_table_name(table_prefix, cursor, strategy);
        if !names.contains(&name) {
            names.push(name);
        }
        cursor = strategy.advance(cursor);
    }
    names
}

/// Java: ShardingTableUtil.isOverMonths
pub fn is_over_months(start: NaiveDateTime, end: NaiveDateTime, months: u32) -> bool {
    match end.checked_sub_months(Months::new(months)) {
        Some(threshold) => start < threshold,
        None => false,
    }
}

/// Java: Spring 的 boolean 判断（sharding.enabled / snapshot.flow.sharding.enabled）。
#[derive(Debug, Clone)]
pub struct ShardingRule {
    pub logical: &'static str,
    pub table_prefix: String,
    pub sharding_field: String,
    pub strategy: ShardingStrategy,
}

#[derive(Debug, Clone, Default)]
pub struct ShardingRouter {
    snapshot: Option<ShardingRule>,
    fee_records: Option<ShardingRule>,
}

impl ShardingRouter {
    /// Java: ShardingSphereConfig 仅在 `sharding.enabled=true` 时创建数据源；
    /// 卡口流水前缀/字段来自 snapshot.flow.sharding，费用表按 Java 硬编码。
    pub fn from_settings(settings: &Settings) -> Self {
        let snapshot_cfg = &settings.snapshot.flow.sharding;
        let snapshot = (settings.sharding.enabled && snapshot_cfg.enabled).then(|| ShardingRule {
            logical: SNAPSHOT_FLOW_LOGICAL,
            table_prefix: snapshot_cfg.table_prefix.clone(),
            sharding_field: snapshot_cfg.sharding_field.clone(),
            strategy: ShardingStrategy::parse(&snapshot_cfg.sharding_type)
                .unwrap_or(ShardingStrategy::Monthly),
        });
        let fee_records = settings.sharding.enabled.then(|| ShardingRule {
            logical: FEE_RECORDS_LOGICAL,
            table_prefix: FEE_RECORDS_LOGICAL.to_string(),
            sharding_field: "record_time".to_string(),
            strategy: ShardingStrategy::Daily,
        });
        Self {
            snapshot,
            fee_records,
        }
    }

    pub fn rule(&self, logical: &str) -> Option<&ShardingRule> {
        if logical == SNAPSHOT_FLOW_LOGICAL {
            self.snapshot.as_ref()
        } else if logical == FEE_RECORDS_LOGICAL {
            self.fee_records.as_ref()
        } else {
            None
        }
    }

    /// Java: SnapshotFlowMonthShardingAlgorithm/FeeRecordsDayShardingAlgorithm.doSharding(precise)。
    /// 配置范围外的日期回退到第一张配置表（与算法实现一致）。
    pub fn route(&self, logical: &str, at: NaiveDateTime) -> String {
        let Some(rule) = self.rule(logical) else {
            return logical.to_string();
        };
        if at.year() < FIRST_SHARD_YEAR || at.year() > LAST_SHARD_YEAR {
            return self.first_shard(rule);
        }
        physical_table_name(&rule.table_prefix, at, rule.strategy)
    }

    /// Java: doSharding(range) —— 返回范围内涉及且配置存在的表。
    pub fn route_range(
        &self,
        logical: &str,
        start: NaiveDateTime,
        end: NaiveDateTime,
    ) -> Vec<String> {
        let Some(rule) = self.rule(logical) else {
            return vec![logical.to_string()];
        };
        let low = start.max(start_of_year(FIRST_SHARD_YEAR));
        let high = end.min(end_of_year(LAST_SHARD_YEAR));
        if low > high {
            return Vec::new();
        }
        table_names_by_date_range(&rule.table_prefix, low, high, rule.strategy)
    }

    /// Java: ShardingSphereConfig 的 dataNodes —— 2025-01 至 2099-12 的全量物理表。
    pub fn configured_shards(&self, logical: &str) -> Vec<String> {
        let Some(rule) = self.rule(logical) else {
            return vec![logical.to_string()];
        };
        let mut names = Vec::new();
        let mut cursor = start_of_year(FIRST_SHARD_YEAR);
        let end = end_of_year(LAST_SHARD_YEAR);
        while cursor <= end {
            let name = physical_table_name(&rule.table_prefix, cursor, rule.strategy);
            if !names.contains(&name) {
                names.push(name);
            }
            cursor = rule.strategy.advance(cursor);
        }
        names
    }

    /// 无分片条件时广播：只查询数据库中真实存在的物理表。
    pub async fn existing_shards(
        &self,
        pool: &MySqlPool,
        logical: &str,
    ) -> Result<Vec<String>, AppError> {
        let Some(rule) = self.rule(logical) else {
            return Ok(vec![logical.to_string()]);
        };
        let pattern = format!("{}\\_%", rule.table_prefix.trim_end_matches('_'));
        let rows = sqlx::query(
            "select table_name from information_schema.tables \
             where table_schema = database() and table_name like ? order by table_name",
        )
        .bind(pattern)
        .fetch_all(pool)
        .await?;
        Ok(rows
            .into_iter()
            .filter_map(|row| row.try_get::<String, _>("table_name").ok())
            .collect())
    }

    fn first_shard(&self, rule: &ShardingRule) -> String {
        physical_table_name(
            &rule.table_prefix,
            start_of_year(FIRST_SHARD_YEAR),
            rule.strategy,
        )
    }
}

fn start_of_year(year: i32) -> NaiveDateTime {
    chrono::NaiveDate::from_ymd_opt(year, 1, 1)
        .expect("valid year")
        .and_hms_opt(0, 0, 0)
        .expect("midnight")
}

fn end_of_year(year: i32) -> NaiveDateTime {
    chrono::NaiveDate::from_ymd_opt(year, 12, 31)
        .expect("valid year")
        .and_hms_opt(23, 59, 59)
        .expect("end of day")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn dt(y: i32, m: u32, d: u32) -> NaiveDateTime {
        chrono::NaiveDate::from_ymd_opt(y, m, d)
            .expect("date")
            .and_hms_opt(0, 0, 0)
            .expect("time")
    }

    #[test]
    fn suffixes_match_java_formats() {
        let date = dt(2025, 8, 15);
        assert_eq!(ShardingStrategy::Monthly.suffix(date), "202508");
        assert_eq!(ShardingStrategy::Daily.suffix(date), "20250815");
        assert_eq!(ShardingStrategy::Quarterly.suffix(date), "2025Q3");
        assert_eq!(ShardingStrategy::Yearly.suffix(date), "2025");
    }

    #[test]
    fn physical_names_strip_duplicate_underscore() {
        assert_eq!(
            physical_table_name(
                "ods_rt_szdn_snapshot_flow_",
                dt(2025, 8, 15),
                ShardingStrategy::Monthly
            ),
            "ods_rt_szdn_snapshot_flow_202508"
        );
        assert_eq!(
            physical_table_name(
                "ods_lwzxsfsj_fee_records",
                dt(2025, 8, 15),
                ShardingStrategy::Daily
            ),
            "ods_lwzxsfsj_fee_records_20250815"
        );
    }

    #[test]
    fn range_covers_each_month() {
        let names = table_names_by_date_range(
            "ods_rt_szdn_snapshot_flow",
            dt(2025, 1, 31),
            dt(2025, 3, 1),
            ShardingStrategy::Monthly,
        );
        assert_eq!(
            names,
            vec![
                "ods_rt_szdn_snapshot_flow_202501",
                "ods_rt_szdn_snapshot_flow_202502",
                "ods_rt_szdn_snapshot_flow_202503"
            ]
        );
    }

    #[test]
    fn period_bounds_are_inclusive() {
        let start = period_start(dt(2025, 8, 15), ShardingStrategy::Monthly);
        let end = period_end(dt(2025, 8, 15), ShardingStrategy::Monthly);
        assert_eq!(start, dt(2025, 8, 1));
        assert_eq!(
            end,
            chrono::NaiveDate::from_ymd_opt(2025, 9, 1)
                .expect("date")
                .and_hms_opt(0, 0, 0)
                .expect("time")
                - chrono::Duration::milliseconds(1)
        );
    }

    #[test]
    fn over_months_matches_java_comparison() {
        assert!(is_over_months(dt(2025, 1, 1), dt(2025, 4, 1), 2));
        assert!(!is_over_months(dt(2025, 2, 1), dt(2025, 4, 1), 2));
    }
}
