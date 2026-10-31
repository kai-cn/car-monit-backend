// 来源: Spring `@Scheduled(cron = "...")` 的 6 段表达式（秒 分 时 日 月 周）。
// 职责: 仅实现本工程 6 个任务用到的语法：* ? 数字 列表 范围 步长 月份/星期名。
// 对应关系: org.springframework.scheduling.support.CronExpression -> CronExpression。

use chrono::{Datelike, Days, Duration, Months, NaiveDateTime, Timelike};

#[derive(Debug, Clone)]
pub struct CronExpression {
    seconds: Field,
    minutes: Field,
    hours: Field,
    days_of_month: Field,
    months: Field,
    days_of_week: Field,
}

#[derive(Debug, Clone)]
struct Field {
    values: Vec<bool>,
}

const MONTH_NAMES: &[(&str, u32)] = &[
    ("JAN", 1),
    ("FEB", 2),
    ("MAR", 3),
    ("APR", 4),
    ("MAY", 5),
    ("JUN", 6),
    ("JUL", 7),
    ("AUG", 8),
    ("SEP", 9),
    ("OCT", 10),
    ("NOV", 11),
    ("DEC", 12),
];

/// 0/7=周日、1=周一 … 6=周六（Spring 5.3 的 0-7 约定）。
const DAY_NAMES: &[(&str, u32)] = &[
    ("SUN", 0),
    ("MON", 1),
    ("TUE", 2),
    ("WED", 3),
    ("THU", 4),
    ("FRI", 5),
    ("SAT", 6),
];

impl CronExpression {
    pub fn parse(expression: &str) -> Result<Self, String> {
        let parts: Vec<&str> = expression.split_whitespace().collect();
        if parts.len() != 6 {
            return Err(format!(
                "cron 表达式必须是 6 段（秒 分 时 日 月 周）: {expression}"
            ));
        }
        Ok(Self {
            seconds: Field::parse(parts[0], 0, 59, &[])?,
            minutes: Field::parse(parts[1], 0, 59, &[])?,
            hours: Field::parse(parts[2], 0, 23, &[])?,
            days_of_month: Field::parse(parts[3], 1, 31, &[])?,
            months: Field::parse(parts[4], 1, 12, MONTH_NAMES)?,
            days_of_week: Field::parse(parts[5], 0, 7, DAY_NAMES)?,
        })
    }

    /// 返回 `after` 之后（不含）最近一次触发时间。
    pub fn next_after(&self, after: NaiveDateTime) -> Option<NaiveDateTime> {
        let mut cursor = (after + Duration::seconds(1))
            .with_nanosecond(0)
            .unwrap_or(after + Duration::seconds(1));

        // 每次不匹配都会跳到下一个时间边界，正常几十步内命中；上限防止死循环。
        for _ in 0..1_000_000 {
            if !self.months.matches(cursor.month()) {
                cursor = first_of_next_month(cursor)?;
                continue;
            }
            let dow = cursor.weekday().num_days_from_sunday();
            if !self.days_of_month.matches(cursor.day()) || !self.days_of_week.matches(dow) {
                cursor = next_day(cursor)?;
                continue;
            }
            if !self.hours.matches(cursor.hour()) {
                cursor = next_hour(cursor)?;
                continue;
            }
            if !self.minutes.matches(cursor.minute()) {
                cursor = next_minute(cursor)?;
                continue;
            }
            if !self.seconds.matches(cursor.second()) {
                cursor += Duration::seconds(1);
                continue;
            }
            return Some(cursor);
        }
        None
    }
}

impl Field {
    fn parse(spec: &str, min: u32, max: u32, names: &[(&str, u32)]) -> Result<Self, String> {
        let spec = spec.trim();
        if spec.is_empty() {
            return Err("cron 字段为空".to_string());
        }
        let mut values = vec![false; (max + 1) as usize];

        for part in spec.split(',') {
            let part = part.trim();
            if part.is_empty() {
                return Err(format!("cron 字段非法: {spec}"));
            }
            let (base, step) = match part.split_once('/') {
                Some((base, step)) => {
                    let step = step
                        .parse::<u32>()
                        .map_err(|_| format!("cron 步长非法: {part}"))?;
                    if step == 0 {
                        return Err(format!("cron 步长不能为 0: {part}"));
                    }
                    (base, step)
                }
                None => (part, 1),
            };
            let (start, end) = if base == "*" || base == "?" {
                (min, max)
            } else if let Some((start, end)) = base.split_once('-') {
                (resolve(start, names)?, resolve(end, names)?)
            } else {
                let value = resolve(base, names)?;
                // `5/10` = 从 5 开始到字段上限，每 10 个取一个。
                if part.contains('/') {
                    (value, max)
                } else {
                    (value, value)
                }
            };
            if start < min || end > max || start > end {
                return Err(format!("cron 字段越界: {part}"));
            }
            let mut value = start;
            while value <= end {
                let slot = if value == 7 { 0 } else { value };
                values[slot as usize] = true;
                value += step;
            }
        }

        Ok(Self { values })
    }

    fn matches(&self, value: u32) -> bool {
        self.values.get(value as usize).copied().unwrap_or(false)
    }
}

fn resolve(token: &str, names: &[(&str, u32)]) -> Result<u32, String> {
    if let Ok(value) = token.parse::<u32>() {
        return Ok(value);
    }
    let upper = token.trim().to_ascii_uppercase();
    names
        .iter()
        .find(|(name, _)| *name == upper)
        .map(|(_, value)| *value)
        .ok_or_else(|| format!("无法识别的 cron 值: {token}"))
}

fn first_of_next_month(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    cursor
        .date()
        .with_day(1)?
        .checked_add_months(Months::new(1))?
        .and_hms_opt(0, 0, 0)
}

fn next_day(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    (cursor.date() + Days::new(1)).and_hms_opt(0, 0, 0)
}

fn next_hour(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    if cursor.hour() < 23 {
        cursor.date().and_hms_opt(cursor.hour() + 1, 0, 0)
    } else {
        next_day(cursor)
    }
}

fn next_minute(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    if cursor.minute() < 59 {
        cursor
            .date()
            .and_hms_opt(cursor.hour(), cursor.minute() + 1, 0)
    } else {
        next_hour(cursor)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    fn at(y: i32, m: u32, d: u32, h: u32, mi: u32, s: u32) -> NaiveDateTime {
        NaiveDate::from_ymd_opt(y, m, d)
            .expect("date")
            .and_hms_opt(h, mi, s)
            .expect("time")
    }

    #[test]
    fn parses_the_six_java_expressions() {
        for expression in [
            "0 0 1 1 * ?",
            "0 0 2 * * MON",
            "0 0 * * * ?",
            "0 0/5 * * * *",
            "0 0 2 1 * ?",
        ] {
            CronExpression::parse(expression).expect(expression);
        }
    }

    #[test]
    fn monthly_first_day_at_one() {
        let cron = CronExpression::parse("0 0 1 1 * ?").expect("cron");
        let next = cron.next_after(at(2026, 10, 31, 12, 0, 0)).expect("next");
        assert_eq!(next, at(2026, 11, 1, 1, 0, 0));
    }

    #[test]
    fn weekly_monday_at_two() {
        let cron = CronExpression::parse("0 0 2 * * MON").expect("cron");
        // 2026-10-30 是周五。
        let next = cron.next_after(at(2026, 10, 30, 12, 0, 0)).expect("next");
        assert_eq!(next, at(2026, 11, 2, 2, 0, 0));
    }

    #[test]
    fn hourly_and_every_five_minutes() {
        let hourly = CronExpression::parse("0 0 * * * ?").expect("cron");
        assert_eq!(
            hourly.next_after(at(2026, 10, 31, 12, 34, 56)).expect("next"),
            at(2026, 10, 31, 13, 0, 0)
        );

        let five = CronExpression::parse("0 0/5 * * * *").expect("cron");
        assert_eq!(
            five.next_after(at(2026, 10, 31, 12, 2, 0)).expect("next"),
            at(2026, 10, 31, 12, 5, 0)
        );
    }

    #[test]
    fn year_rollover() {
        let cron = CronExpression::parse("0 0 2 1 * ?").expect("cron");
        let next = cron.next_after(at(2026, 12, 31, 23, 0, 0)).expect("next");
        assert_eq!(next, at(2027, 1, 1, 2, 0, 0));
    }
}
