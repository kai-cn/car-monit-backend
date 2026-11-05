// 来源: org.quartz.CronExpression（Quartz 2.3，ruoyi-admin.jar 内的实现）
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/CronUtils.java
// 职责: sys_job 的 cron 校验（CronUtils.isValid）与下次触发时间（CronUtils.getNextExecution）。
// 对应关系: CronExpression.isValidExpression -> is_valid；getNextValidTimeAfter -> next_after。
//
// 与 task::cron 的区别：那个是 Spring `@Scheduled` 的 6 段表达式，这里是 Quartz 表达式
// （`?`/`L`/`W`/`#`/第 7 段年份），语义按 Java 逐分支移植，含 Java 自身的三处怪癖：
// `?x` 因越界判断写成 `(i + 1) < len` 而被放过、第 8 段起被丢弃、年份字段不做范围校验。

use chrono::{Datelike, NaiveDate, NaiveDateTime, Timelike};

const SECOND: usize = 0;
const MINUTE: usize = 1;
const HOUR: usize = 2;
const DAY_OF_MONTH: usize = 3;
const MONTH: usize = 4;
const DAY_OF_WEEK: usize = 5;
const YEAR: usize = 6;

/// Java: `ALL_SPEC_INT = 99`（`*` 的哨兵）。
const ALL_SPEC: i32 = 99;
/// Java: `NO_SPEC_INT = 98`（`?` 的哨兵）。
const NO_SPEC: i32 = 98;

type Parsed<T> = Result<T, String>;

/// Java: `MAX_YEAR = Calendar.getInstance().get(Calendar.YEAR) + 100`，静态初始化一次。
fn max_year() -> i32 {
    use std::sync::OnceLock;
    static VALUE: OnceLock<i32> = OnceLock::new();
    *VALUE.get_or_init(|| {
        chrono::Local::now()
            .naive_local()
            .format("%Y")
            .to_string()
            .parse::<i32>()
            .unwrap_or(2026)
            + 100
    })
}

const MONTH_NAMES: &[(&str, i32)] = &[
    ("JAN", 0),
    ("FEB", 1),
    ("MAR", 2),
    ("APR", 3),
    ("MAY", 4),
    ("JUN", 5),
    ("JUL", 6),
    ("AUG", 7),
    ("SEP", 8),
    ("OCT", 9),
    ("NOV", 10),
    ("DEC", 11),
];

/// Java: `dayMap`，1=周日 … 7=周六。
const DAY_NAMES: &[(&str, i32)] = &[
    ("SUN", 1),
    ("MON", 2),
    ("TUE", 3),
    ("WED", 4),
    ("THU", 5),
    ("FRI", 6),
    ("SAT", 7),
];

#[derive(Debug, Clone, Default)]
pub struct QuartzCron {
    seconds: Vec<i32>,
    minutes: Vec<i32>,
    hours: Vec<i32>,
    days_of_month: Vec<i32>,
    months: Vec<i32>,
    days_of_week: Vec<i32>,
    years: Vec<i32>,
    last_day_of_week: bool,
    nth_day_of_week: i32,
    last_day_of_month: bool,
    nearest_weekday: bool,
    last_day_offset: i32,
}

/// Java: `CronExpression.isValidExpression`（ParseException 视为非法，其余异常也被
/// `buildExpression` 的 `catch (Exception e)` 收敛成 ParseException）。
pub fn is_valid(expression: &str) -> bool {
    QuartzCron::parse(expression).is_ok()
}

impl QuartzCron {
    /// Java: `new CronExpression(cronExpression)`；`Err` 里是 ParseException 文案。
    /// null 走的是 `IllegalArgumentException("cronExpression cannot be null")`，由调用方区分。
    pub fn parse(expression: &str) -> Parsed<QuartzCron> {
        let mut cron = QuartzCron::default();
        // Java: this.cronExpression = cronExpression.toUpperCase(Locale.US);
        let upper = expression.to_ascii_uppercase();
        cron.build_expression(&upper)?;
        for set in [
            &mut cron.seconds,
            &mut cron.minutes,
            &mut cron.hours,
            &mut cron.days_of_month,
            &mut cron.months,
            &mut cron.days_of_week,
            &mut cron.years,
        ] {
            // Java 用 TreeSet，天然有序去重。
            set.sort_unstable();
            set.dedup();
        }
        Ok(cron)
    }

    /// Java: `CronUtils.getNextExecution` -> `getNextValidTimeAfter`；永不触发返回 None。
    pub fn next_after(&self, after: NaiveDateTime) -> Option<NaiveDateTime> {
        let limit = max_year();
        // Java: `cl.set(MILLISECOND, 0); cl.add(SECOND, 1);`——严格晚于 after。
        let mut cursor = after
            .with_nanosecond(0)?
            .checked_add_signed(chrono::Duration::seconds(1))?;
        loop {
            if cursor.year() > 2999 || cursor.year() > limit {
                return None;
            }
            if !contains(&self.years, cursor.year()) {
                cursor = start_of_year(cursor.year() + 1)?;
                continue;
            }
            if !contains(&self.months, cursor.month() as i32) {
                cursor = start_of_next_month(cursor)?;
                continue;
            }
            if !self.matches_day(cursor.date()) {
                cursor = start_of_next_day(cursor)?;
                continue;
            }
            if !contains(&self.hours, cursor.hour() as i32) {
                cursor = start_of_next_hour(cursor)?;
                continue;
            }
            if !contains(&self.minutes, cursor.minute() as i32) {
                cursor = start_of_next_minute(cursor)?;
                continue;
            }
            if !contains(&self.seconds, cursor.second() as i32) {
                cursor = cursor
                    .with_nanosecond(0)?
                    .checked_add_signed(chrono::Duration::seconds(1))?;
                continue;
            }
            return Some(cursor);
        }
    }

    /// Java: `buildExpression`。
    fn build_expression(&mut self, expression: &str) -> Parsed<()> {
        let mut expr_on = SECOND;
        for token in tokenize(expression, " \t") {
            if expr_on > YEAR {
                break;
            }
            let expr = java_trim(&token);
            // Java: 'L'/'LW' 不许与别的日/周值并列。
            if expr_on == DAY_OF_MONTH
                && expr.contains('L')
                && expr.chars().count() > 1
                && expr.contains(',')
            {
                return Err(
                    "Support for specifying 'L' and 'LW' with other days of the month is not implemented"
                        .to_string(),
                );
            }
            if expr_on == DAY_OF_WEEK
                && expr.contains('L')
                && expr.chars().count() > 1
                && expr.contains(',')
            {
                return Err(
                    "Support for specifying 'L' with other days of the week is not implemented"
                        .to_string(),
                );
            }
            if expr_on == DAY_OF_WEEK && expr.matches('#').count() > 1 {
                return Err(
                    "Support for specifying multiple \"nth\" days is not implemented.".to_string(),
                );
            }
            for value in tokenize(&expr, ",") {
                let value = java_trim(&value);
                self.store_expression_vals(&own_chars(&value), expr_on)?;
            }
            expr_on += 1;
        }
        if expr_on <= DAY_OF_WEEK {
            return Err("Unexpected end of expression.".to_string());
        }
        if expr_on <= YEAR {
            self.store_expression_vals(&own_chars("*"), YEAR)?;
        }
        // Java: DOM 与 DOW 必须恰好有一个是 '?'。
        let day_of_m_spec = !self.days_of_month.contains(&NO_SPEC);
        let day_of_w_spec = !self.days_of_week.contains(&NO_SPEC);
        if (!day_of_m_spec || day_of_w_spec) && (!day_of_w_spec || day_of_m_spec) {
            return Err("Support for specifying both a day-of-week AND a day-of-month parameter is not implemented.".to_string());
        }
        Ok(())
    }

    /// Java: `storeExpressionVals(int pos, String s, int type)`，`pos` 恒为 0。
    fn store_expression_vals(&mut self, s: &[char], type_: usize) -> Parsed<()> {
        let mut incr = 0;
        let mut i = skip_white_space(0, s);
        if i >= s.len() {
            return Ok(());
        }
        let c = s[i];
        if c.is_ascii_alphabetic()
            && c.is_uppercase()
            && !is_eq(s, "L")
            && !is_eq(s, "LW")
            && !is_l_minus(s)
        {
            let mut sub = substring(s, i, Some(i + 3))?;
            let sval;
            let mut eval = -1;
            if type_ == MONTH {
                sval = name_number(&sub, MONTH_NAMES) + 1;
                if sval <= 0 {
                    return Err(format!("Invalid Month value: '{sub}'"));
                }
                if s.len() > i + 3 && s[i + 3] == '-' {
                    i += 4;
                    sub = substring(s, i, Some(i + 3))?;
                    eval = name_number(&sub, MONTH_NAMES) + 1;
                    if eval <= 0 {
                        return Err(format!("Invalid Month value: '{sub}'"));
                    }
                }
            } else if type_ == DAY_OF_WEEK {
                sval = name_number(&sub, DAY_NAMES);
                if sval < 0 {
                    return Err(format!("Invalid Day-of-Week value: '{sub}'"));
                }
                if s.len() > i + 3 {
                    match s[i + 3] {
                        '-' => {
                            i += 4;
                            sub = substring(s, i, Some(i + 3))?;
                            eval = name_number(&sub, DAY_NAMES);
                            if eval < 0 {
                                return Err(format!("Invalid Day-of-Week value: '{sub}'"));
                            }
                        }
                        '#' => {
                            i += 4;
                            self.nth_day_of_week = parse_int(&substring(s, i, None)?)?;
                            if !(1..=5).contains(&self.nth_day_of_week) {
                                return Err(
                                    "A numeric value between 1 and 5 must follow the '#' option"
                                        .to_string(),
                                );
                            }
                        }
                        'L' => {
                            self.last_day_of_week = true;
                        }
                        _ => {}
                    }
                }
            } else {
                return Err(format!("Illegal characters for this position: '{sub}'"));
            }
            if eval != -1 {
                incr = 1;
            }
            self.add_to_set(sval, eval, incr, type_)?;
            return Ok(());
        }

        if c == '?' {
            i += 1;
            // Java 的越界判断写成 (i + 1) < length，于是 "?x" 逃过检查——照抄。
            if (i + 1) < s.len() && s[i] != ' ' && s[i + 1] != '\t' {
                return Err(format!("Illegal character after '?': {}", s[i]));
            }
            if type_ != DAY_OF_WEEK && type_ != DAY_OF_MONTH {
                return Err(
                    "'?' can only be specified for Day-of-Month or Day-of-Week.".to_string()
                );
            }
            if type_ == DAY_OF_WEEK && !self.last_day_of_month {
                // Java: daysOfMonth.last()，空集合时 NoSuchElementException -> 非法。
                let val = self
                    .days_of_month
                    .last()
                    .copied()
                    .ok_or_else(|| "Illegal cron expression format".to_string())?;
                if val == NO_SPEC {
                    return Err(
                        "'?' can only be specified for Day-of-Month -OR- Day-of-Week.".to_string(),
                    );
                }
            }
            self.add_to_set(NO_SPEC, -1, 0, type_)?;
            return Ok(());
        }

        if c == '*' || c == '/' {
            if c == '*' && (i + 1) >= s.len() {
                self.add_to_set(ALL_SPEC, -1, incr, type_)?;
                return Ok(());
            }
            if c == '/' && ((i + 1) >= s.len() || s[i + 1] == ' ' || s[i + 1] == '\t') {
                return Err("'/' must be followed by an integer.".to_string());
            }
            if c == '*' {
                i += 1;
            }
            let next = *s
                .get(i)
                .ok_or_else(|| "String index out of range".to_string())?;
            if next == '/' {
                i += 1;
                if i >= s.len() {
                    return Err("Unexpected end of string.".to_string());
                }
                incr = get_numeric_value(s, i)?;
                // Java 还会 `i++`（`incr > 10` 时再来一次）只为给异常标位置，这里用不上。
                check_increment_range(incr, type_)?;
            } else {
                incr = 1;
            }
            self.add_to_set(ALL_SPEC, -1, incr, type_)?;
            return Ok(());
        }

        if c == 'L' {
            i += 1;
            if type_ == DAY_OF_MONTH {
                self.last_day_of_month = true;
            }
            if type_ == DAY_OF_WEEK {
                // Java: 裸 L 等价周六的最后一个。
                self.add_to_set(7, 7, 0, type_)?;
            }
            if type_ == DAY_OF_MONTH && i < s.len() {
                if s[i] == '-' {
                    let (value, next) = get_value(0, s, i + 1)?;
                    self.last_day_offset = value;
                    if self.last_day_offset > 30 {
                        return Err("Offset from last day must be <= 30".to_string());
                    }
                    i = next;
                }
                if i < s.len() && s[i] == 'W' {
                    self.nearest_weekday = true;
                    i += 1;
                }
            }
            let _ = i;
            return Ok(());
        }

        if c.is_ascii_digit() {
            let mut val = c as i32 - '0' as i32;
            i += 1;
            if i >= s.len() {
                self.add_to_set(val, -1, -1, type_)?;
                return Ok(());
            }
            if s[i].is_ascii_digit() {
                let (next_val, next_i) = get_value(val, s, i)?;
                val = next_val;
                i = next_i;
            }
            self.check_next(i, s, val, type_)?;
            return Ok(());
        }

        Err(format!("Unexpected character: {c}"))
    }

    /// Java: `checkNext(int pos, String s, int val, int type)`。
    fn check_next(&mut self, pos: usize, s: &[char], val: i32, type_: usize) -> Parsed<usize> {
        let mut end = -1;
        let mut i = pos;

        if i >= s.len() {
            self.add_to_set(val, end, -1, type_)?;
            return Ok(i);
        }

        let c = s[i];

        if c == 'L' {
            if type_ == DAY_OF_WEEK {
                if !(1..=7).contains(&val) {
                    return Err("Day-of-Week values must be between 1 and 7".to_string());
                }
                self.last_day_of_week = true;
            } else {
                return Err(format!("'L' option is not valid here. (pos={i})"));
            }
            self.set_mut(type_).push(val);
            i += 1;
            return Ok(i);
        }

        if c == 'W' {
            if type_ == DAY_OF_MONTH {
                self.nearest_weekday = true;
            } else {
                return Err(format!("'W' option is not valid here. (pos={i})"));
            }
            if val > 31 {
                return Err("The 'W' option does not make sense with values larger than 31 (max number of days in a month)".to_string());
            }
            self.set_mut(type_).push(val);
            i += 1;
            return Ok(i);
        }

        if c == '#' {
            if type_ != DAY_OF_WEEK {
                return Err(format!("'#' option is not valid here. (pos={i})"));
            }
            i += 1;
            let nth = parse_int(&substring(s, i, None)?)?;
            if !(1..=5).contains(&nth) {
                return Err(
                    "A numeric value between 1 and 5 must follow the '#' option".to_string()
                );
            }
            self.nth_day_of_week = nth;
            self.set_mut(type_).push(val);
            i += 1;
            return Ok(i);
        }

        if c == '-' {
            i += 1;
            let next = *s
                .get(i)
                .ok_or_else(|| "Unexpected end of string.".to_string())?;
            if !next.is_ascii_digit() {
                return Err(format!("Unexpected character: {next}"));
            }
            let v = next as i32 - '0' as i32;
            end = v;
            i += 1;
            if i >= s.len() {
                self.add_to_set(val, end, 1, type_)?;
                return Ok(i);
            }
            if s[i].is_ascii_digit() {
                let (next_end, next_i) = get_value(v, s, i)?;
                end = next_end;
                i = next_i;
            }
            if i < s.len() && s[i] == '/' {
                i += 1;
                let c2 = *s
                    .get(i)
                    .ok_or_else(|| "Unexpected character: end of string".to_string())?;
                if !c2.is_ascii_digit() {
                    return Err(format!("Unexpected character: {c2}"));
                }
                let mut v2 = c2 as i32 - '0' as i32;
                i += 1;
                if i >= s.len() {
                    self.add_to_set(val, end, v2, type_)?;
                    return Ok(i);
                }
                if s[i].is_ascii_digit() {
                    let (v3, _) = get_value(v2, s, i)?;
                    v2 = v3;
                }
                self.add_to_set(val, end, v2, type_)?;
                return Ok(i);
            }
            self.add_to_set(val, end, 1, type_)?;
            return Ok(i);
        }

        if c == '/' {
            if (i + 1) >= s.len() || s[i + 1] == ' ' || s[i + 1] == '\t' {
                return Err("'/' must be followed by an integer.".to_string());
            }
            i += 1;
            let next = *s
                .get(i)
                .ok_or_else(|| "Unexpected character: end of string".to_string())?;
            if !next.is_ascii_digit() {
                return Err(format!("Unexpected character: {next}"));
            }
            let mut v2 = next as i32 - '0' as i32;
            i += 1;
            if i >= s.len() {
                check_increment_range(v2, type_)?;
                self.add_to_set(val, end, v2, type_)?;
                return Ok(i);
            }
            if s[i].is_ascii_digit() {
                let (v3, next_i) = get_value(v2, s, i)?;
                v2 = v3;
                i = next_i;
                check_increment_range(v2, type_)?;
                self.add_to_set(val, end, v2, type_)?;
                return Ok(i);
            }
            return Err(format!("Unexpected character '{}' after '/'", s[i]));
        }

        self.add_to_set(val, end, 0, type_)?;
        i += 1;
        Ok(i)
    }

    /// Java: `addToSet(int val, int end, int incr, int type)`。
    fn add_to_set(&mut self, val: i32, end: i32, mut incr: i32, type_: usize) -> Parsed<()> {
        let target = self.set_mut(type_);
        match type_ {
            SECOND | MINUTE => {
                if val != ALL_SPEC && (!(0..=59).contains(&val) || end > 59) {
                    return Err("Minute and Second values must be between 0 and 59".to_string());
                }
            }
            HOUR => {
                if val != ALL_SPEC && (!(0..=23).contains(&val) || end > 23) {
                    return Err("Hour values must be between 0 and 23".to_string());
                }
            }
            DAY_OF_MONTH => {
                if val != ALL_SPEC && val != NO_SPEC && (!(1..=31).contains(&val) || end > 31) {
                    return Err("Day of month values must be between 1 and 31".to_string());
                }
            }
            MONTH => {
                if val != ALL_SPEC && (!(1..=12).contains(&val) || end > 12) {
                    return Err("Month values must be between 1 and 12".to_string());
                }
            }
            DAY_OF_WEEK => {
                if (val == 0 || val > 7 || end > 7) && val != ALL_SPEC && val != NO_SPEC {
                    return Err("Day-of-Week values must be between 1 and 7".to_string());
                }
            }
            YEAR => {}
            _ => return Err("unexpected set type".to_string()),
        }

        if (incr == 0 || incr == -1) && val != ALL_SPEC {
            target.push(if val == -1 { NO_SPEC } else { val });
            return Ok(());
        }

        let mut start_at = val;
        let mut stop_at = end;

        if val == ALL_SPEC && incr <= 0 {
            incr = 1;
            // Java 既塞哨兵也填满取值，所以 `*/0` 等价 `*`。
            target.push(ALL_SPEC);
        }

        let (default_stop, default_start);
        match type_ {
            SECOND | MINUTE => {
                default_stop = 59;
                default_start = 0;
            }
            HOUR => {
                default_stop = 23;
                default_start = 0;
            }
            DAY_OF_MONTH => {
                default_stop = 31;
                default_start = 1;
            }
            MONTH => {
                default_stop = 12;
                default_start = 1;
            }
            DAY_OF_WEEK => {
                default_stop = 7;
                default_start = 1;
            }
            _ => {
                default_stop = max_year();
                default_start = 1970;
            }
        }
        if stop_at == -1 {
            stop_at = default_stop;
        }
        if start_at == -1 || start_at == ALL_SPEC {
            start_at = default_start;
        }

        // Java: 区间跨越上限时取模回卷，1 基字段不把 0 算进来。
        let mut maximum = -1;
        if stop_at < start_at {
            maximum = match type_ {
                SECOND | MINUTE => 60,
                HOUR => 24,
                MONTH => 12,
                DAY_OF_WEEK => 7,
                DAY_OF_MONTH => 31,
                YEAR => return Err("Start year must be less than stop year".to_string()),
                _ => return Err("Unexpected type encountered".to_string()),
            };
            stop_at += maximum;
        }

        let mut value = start_at;
        while value <= stop_at {
            if maximum == -1 {
                target.push(value);
            } else {
                let mut reduced = value.rem_euclid(maximum);
                if reduced == 0 && matches!(type_, MONTH | DAY_OF_WEEK | DAY_OF_MONTH) {
                    reduced = maximum;
                }
                target.push(reduced);
            }
            value += incr;
        }
        Ok(())
    }

    fn set_mut(&mut self, type_: usize) -> &mut Vec<i32> {
        match type_ {
            SECOND => &mut self.seconds,
            MINUTE => &mut self.minutes,
            HOUR => &mut self.hours,
            DAY_OF_MONTH => &mut self.days_of_month,
            MONTH => &mut self.months,
            DAY_OF_WEEK => &mut self.days_of_week,
            _ => &mut self.years,
        }
    }

    /// Quartz 的日判定：DOM 规则与 DOW 规则二选一（解析阶段已保证）。
    fn matches_day(&self, date: NaiveDate) -> bool {
        let day_of_m_spec = !self.days_of_month.contains(&NO_SPEC);
        if day_of_m_spec {
            return self.dom_matches(date);
        }
        self.dow_matches(date)
    }

    /// Java: `getTimeAfter` 的 DOM 分支——`L`/`LW`/`nW` 都只认一个目标日。
    fn dom_matches(&self, date: NaiveDate) -> bool {
        let last = last_day_of_month(date);
        if self.last_day_of_month {
            let mut day = last - self.last_day_offset;
            if self.nearest_weekday {
                day = nearest_weekday(date, day, last);
            }
            return date.day() as i32 == day;
        }
        if self.nearest_weekday {
            let first = *self.days_of_month.first().unwrap_or(&1);
            return date.day() as i32 == nearest_weekday(date, first, last);
        }
        contains(&self.days_of_month, date.day() as i32)
    }

    /// Java: `getTimeAfter` 的 DOW 分支——`L`/`#` 同样只认 `daysOfWeek.first()`。
    fn dow_matches(&self, date: NaiveDate) -> bool {
        let weekday = java_day_of_week(date);
        let last = last_day_of_month(date);
        if self.last_day_of_week {
            let target = *self.days_of_week.first().unwrap_or(&1);
            return weekday == target && date.day() as i32 + 7 > last;
        }
        if self.nth_day_of_week != 0 {
            let target = *self.days_of_week.first().unwrap_or(&1);
            let week_of_month = (date.day() as i32 - 1) / 7 + 1;
            return weekday == target && week_of_month == self.nth_day_of_week;
        }
        contains(&self.days_of_week, weekday)
    }
}

fn check_increment_range(incr: i32, type_: usize) -> Parsed<()> {
    let limit = match type_ {
        SECOND | MINUTE => 59,
        HOUR => 23,
        DAY_OF_MONTH => 31,
        DAY_OF_WEEK => 7,
        MONTH => 12,
        _ => return Ok(()),
    };
    let label = match type_ {
        SECOND | MINUTE => 60,
        HOUR => 24,
        DAY_OF_MONTH => 31,
        DAY_OF_WEEK => 7,
        MONTH => 12,
        _ => 0,
    };
    if incr > limit {
        return Err(format!("Increment > {label} : {incr}"));
    }
    Ok(())
}

/// Java: `getValue(int v, String s, int i)`——`charAt(i)` 越界即整条表达式非法。
fn get_value(v: i32, s: &[char], start: usize) -> Parsed<(i32, usize)> {
    let mut i = start;
    let mut text = v.to_string();
    let mut c = *s
        .get(i)
        .ok_or_else(|| "String index out of range".to_string())?;
    while c.is_ascii_digit() {
        text.push(c);
        i += 1;
        if i == s.len() {
            break;
        }
        c = s[i];
    }
    let pos = if i < s.len() { i } else { i + 1 };
    Ok((text.parse::<i32>().map_err(|e| e.to_string())?, pos))
}

/// Java: `getNumericValue` —— `findNextWhiteSpace` 的判据恒为真，所以总是取到串尾，
/// 于是 `*/2L` 会去解析 "2L" 而抛异常（照抄）。
fn get_numeric_value(s: &[char], i: usize) -> Parsed<i32> {
    let text: String = s[i..].iter().collect();
    parse_int(&text)
}

fn parse_int(text: &str) -> Parsed<i32> {
    if text.is_empty() {
        return Err("For input string: \"\"".to_string());
    }
    text.parse::<i32>()
        .map_err(|_| format!("For input string: \"{text}\""))
}

fn name_number(text: &str, names: &[(&str, i32)]) -> i32 {
    names
        .iter()
        .find(|(name, _)| *name == text)
        .map(|(_, value)| *value)
        .unwrap_or(-1)
}

fn is_eq(s: &[char], text: &str) -> bool {
    s.iter().collect::<String>() == text
}

/// Java: `s.matches("^L-[0-9]*[W]?")`，`matches` 是整串匹配。
fn is_l_minus(s: &[char]) -> bool {
    let text: String = s.iter().collect();
    let Some(rest) = text.strip_prefix("L-") else {
        return false;
    };
    let digits = rest.strip_suffix('W').unwrap_or(rest);
    digits.chars().all(|c| c.is_ascii_digit())
}

fn skip_white_space(mut i: usize, s: &[char]) -> usize {
    while i < s.len() && (s[i] == ' ' || s[i] == '\t') {
        i += 1;
    }
    i
}

fn substring(s: &[char], begin: usize, end: Option<usize>) -> Parsed<String> {
    let end = end.unwrap_or(s.len());
    if begin > s.len() || end > s.len() || begin > end {
        return Err(format!(
            "String index out of range: begin {begin}, end {end}, length {}",
            s.len()
        ));
    }
    Ok(s[begin..end].iter().collect())
}

/// Java: `String.trim()` —— 去掉两端 `<= ' '` 的字符。
fn java_trim(text: &str) -> String {
    let chars: Vec<char> = text.chars().collect();
    let mut start = 0;
    let mut end = chars.len();
    while start < end && chars[start] <= ' ' {
        start += 1;
    }
    while end > start && chars[end - 1] <= ' ' {
        end -= 1;
    }
    chars[start..end].iter().collect()
}

/// Java: `StringTokenizer`（连续分隔符合并、不产生空串）。
fn tokenize(text: &str, delimiters: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    for c in text.chars() {
        if delimiters.contains(c) {
            if !current.is_empty() {
                tokens.push(std::mem::take(&mut current));
            }
        } else {
            current.push(c);
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

fn own_chars(text: &str) -> Vec<char> {
    text.chars().collect()
}

fn contains(set: &[i32], value: i32) -> bool {
    set.contains(&value) || set.contains(&ALL_SPEC)
}

fn java_day_of_week(date: NaiveDate) -> i32 {
    date.weekday().num_days_from_sunday() as i32 + 1
}

/// Java: `getLastDayOfMonth(int monthNum, int year)`。
fn last_day_of_month(date: NaiveDate) -> i32 {
    match date.month() {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        _ => {
            let year = date.year();
            if (year % 4 == 0 && year % 100 != 0) || year % 400 == 0 {
                29
            } else {
                28
            }
        }
    }
}

/// Java: `nW`/`LW` 的最近工作日折算。Java 用 `Calendar` 取星期，日子超出当月会进位，
/// 这里同样按「当月 1 号 + (day-1) 天」取星期，算出的目标日若越界则由调用方判不等。
fn nearest_weekday(date: NaiveDate, day: i32, last: i32) -> i32 {
    let mut day = day;
    let Some(target) = date
        .with_day(1)
        .and_then(|first| first.checked_add_signed(chrono::Duration::days(i64::from(day) - 1)))
    else {
        return day;
    };
    match java_day_of_week(target) {
        7 if day == 1 => day += 2,
        7 => day -= 1,
        1 if day == last => day -= 2,
        1 => day += 1,
        _ => {}
    }
    day
}

fn start_of_year(year: i32) -> Option<NaiveDateTime> {
    NaiveDate::from_ymd_opt(year, 1, 1)?.and_hms_opt(0, 0, 0)
}

fn start_of_next_month(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    let (year, month) = if cursor.month() == 12 {
        (cursor.year() + 1, 1)
    } else {
        (cursor.year(), cursor.month() + 1)
    };
    NaiveDate::from_ymd_opt(year, month, 1)?.and_hms_opt(0, 0, 0)
}

fn start_of_next_day(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    cursor
        .date()
        .succ_opt()
        .and_then(|next| next.and_hms_opt(0, 0, 0))
}

fn start_of_next_hour(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    if cursor.hour() < 23 {
        cursor.date().and_hms_opt(cursor.hour() + 1, 0, 0)
    } else {
        start_of_next_day(cursor)
    }
}

fn start_of_next_minute(cursor: NaiveDateTime) -> Option<NaiveDateTime> {
    if cursor.minute() < 59 {
        cursor
            .date()
            .and_hms_opt(cursor.hour(), cursor.minute() + 1, 0)
    } else {
        start_of_next_hour(cursor)
    }
}

/// Java: `CronUtils.getNextExecution` —— 非法表达式抛 `IllegalArgumentException(消息)`。
pub fn next_execution(
    expression: &str,
    after: NaiveDateTime,
) -> Result<Option<NaiveDateTime>, String> {
    let cron = QuartzCron::parse(expression)?;
    Ok(cron.next_after(after))
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    /// Java 侧采集基准时（`tools/endpoint_parity/cron_matrix.py`）的本地时刻。
    fn at(y: i32, m: u32, d: u32, h: u32, mi: u32, s: u32) -> NaiveDateTime {
        NaiveDate::from_ymd_opt(y, m, d)
            .expect("date")
            .and_hms_opt(h, mi, s)
            .expect("time")
    }

    fn java_valid() -> Vec<&'static str> {
        vec![
            "0 0 2 * * ?",
            "0 0/5 * * * ?",
            "0 0 2 ? * MON-FRI",
            "0 0 2 ? * 2#1",
            "0 0 2 ? * 6L",
            "0 0 2 L * ?",
            "0 0 2 LW * ?",
            "0 0 2 L-3 * ?",
            "0 0 2 15W * ?",
            "0 0 2 ? * L",
            "0 0 2 ? * SAT",
            "0 0 2 ? * sat",
            "0 0 2 ? * 7",
            "0 0 2 ? * 1",
            "0 0 2 ? * 1-5",
            "0 0 2 ? * 1,3,5",
            "0 0 2 ? * 1/2",
            "0 0 2 1/1 * ?",
            "0 0 2 1 1 ? 2099",
            "0 0 2 1 1 ? *",
            "0 0 2 1 1 ? 1969",
            "0 0 2 1 1 ? 2400",
            "0 0 2 * 1-12 ?",
            "*/0 * * * * ?",
            "0 0 2 ? * 2-6L",
            "0 0 2 ? * 1LW",
            "0 0 2 * * ? 2099 2100",
            "0 0 2 * * ?x",
            "0 0 2 1W,3 * ?",
            "0 0 2 ? * 5#2,6",
            "0 0 2 ? * 5,6#2",
            "0 0 2 ? * *",
            "0 0 2 * 1 ?",
            "0  0  2 * * ?",
            " 0 0 2 * * ? ",
            "0 0 2 1 FEB ?",
        ]
    }

    fn java_invalid() -> Vec<&'static str> {
        vec![
            "0 0 2 ? * 7W",
            "0 0 2 ? * 5#2,6#3",
            "0 0 2 ? * 3#0",
            "0 0 2 ? * 3#6",
            "0 0 2 0 * ?",
            "0 0 2 32 * ?",
            "0 0 2 L-31 * ?",
            "0 0 25 * * ?",
            "60 0 2 * * ?",
            "0 60 2 * * ?",
            "0 0 2 * 13 ?",
            "0 0 2 * * 8",
            "0 0 2 ? * 0",
            "? 0 2 * * ?",
            "0 0 2 * ? 1",
            "bogus",
            "",
            "   ",
            "0 0 2 * *",
            "0 0 2 LW,1 * ?",
            "0 0 2 ? * ?",
            "0 0 2 * * *",
            "0 0 2 ? JAN ?",
            "0 0 2 ? jan ?",
            "0 0 2 * * ?x y",
        ]
    }

    #[test]
    fn accepts_every_java_valid_expression() {
        for expression in java_valid() {
            assert!(
                is_valid(expression),
                "Java 接受但 Rust 判非法: {expression:?}"
            );
        }
    }

    #[test]
    fn rejects_every_java_invalid_expression() {
        for expression in java_invalid() {
            assert!(
                !is_valid(expression),
                "Java 拒绝但 Rust 判合法: {expression:?}"
            );
        }
    }

    /// 期望值全部取自 `cron_matrix.py` 在 Java 上读到的 `nextValidTime`。
    #[test]
    fn next_fire_times_match_java() {
        let after = at(2026, 11, 3, 11, 58, 40);
        let cases = [
            ("0 0 2 * * ?", "2026-11-04 02:00:00"),
            ("0 0 2 ? * MON-FRI", "2026-11-04 02:00:00"),
            ("0 0 2 ? * 2#1", "2026-12-07 02:00:00"),
            ("0 0 2 ? * 6L", "2026-11-27 02:00:00"),
            ("0 0 2 L * ?", "2026-11-30 02:00:00"),
            ("0 0 2 LW * ?", "2026-11-30 02:00:00"),
            ("0 0 2 L-3 * ?", "2026-11-27 02:00:00"),
            ("0 0 2 15W * ?", "2026-11-16 02:00:00"),
            ("0 0 2 ? * L", "2026-11-07 02:00:00"),
            ("0 0 2 ? * 7", "2026-11-07 02:00:00"),
            ("0 0 2 ? * 1", "2026-11-08 02:00:00"),
            ("0 0 2 ? * 1-5", "2026-11-04 02:00:00"),
            ("0 0 2 ? * 1,3,5", "2026-11-05 02:00:00"),
            ("0 0 2 ? * 1/2", "2026-11-05 02:00:00"),
            ("0 0 2 1/1 * ?", "2026-11-04 02:00:00"),
            ("0 0 2 * 1-12 ?", "2026-11-04 02:00:00"),
            ("0 0 2 ? * 2-6L", "2026-11-04 02:00:00"),
            ("0 0 2 ? * 1LW", "2026-11-29 02:00:00"),
            ("0 0 2 1W,3 * ?", "2026-12-01 02:00:00"),
            ("0 0 2 ? * 5#2,6", "2026-11-12 02:00:00"),
            ("0 0 2 ? * 5,6#2", "2026-11-12 02:00:00"),
            ("0 0 2 ? * *", "2026-11-04 02:00:00"),
            ("0 0 2 * 1 ?", "2027-01-01 02:00:00"),
            (" 0 0 2 * * ? ", "2026-11-04 02:00:00"),
            ("0 0 2 * * ?x", "2026-11-04 02:00:00"),
            ("0 0 2 1 1 ? 2099", "2099-01-01 02:00:00"),
            ("0 0 2 1 1 ? 2099 2100", "2099-01-01 02:00:00"),
            ("0 0 2 1 1 ? *", "2027-01-01 02:00:00"),
            ("0 0 2 1 FEB ?", "2027-02-01 02:00:00"),
            ("0 30 0 * * ?", "2026-11-04 00:30:00"),
            ("0 0/10 * * * ?", "2026-11-03 12:00:00"),
        ];
        for (expression, expected) in cases {
            let actual = QuartzCron::parse(expression)
                .unwrap_or_else(|err| panic!("{expression:?} 解析失败: {err}"))
                .next_after(after)
                .unwrap_or_else(|| panic!("{expression:?} 居然永不触发"));
            assert_eq!(
                actual.format("%Y-%m-%d %H:%M:%S").to_string(),
                expected,
                "{expression:?}"
            );
        }
    }

    #[test]
    fn never_fires_beyond_max_year() {
        // 年字段不做范围校验，但取不到触发时间（Java 建 trigger 时报 never fire）。
        for expression in ["0 0 2 1 1 ? 1969", "0 0 2 1 1 ? 2400"] {
            assert_eq!(
                QuartzCron::parse(expression)
                    .unwrap()
                    .next_after(at(2026, 11, 3, 12, 0, 0)),
                None,
                "{expression:?}"
            );
        }
    }

    #[test]
    fn java_bugs_are_replicated() {
        // `?` 的越界判断写成 (i + 1) < length：两字符的 "?x" 逃过检查。
        assert!(is_valid("0 0 2 * * ?x"));
        assert!(!is_valid("0 0 2 * * ?xy"));
        // 第 8 段起被丢弃。
        assert!(is_valid("0 0 2 * * ? 2099 junk"));
        // 区间分支 return 得早，尾部的 L 从未被解析。
        let cron = QuartzCron::parse("0 0 2 ? * 2-6L").expect("cron");
        assert!(!cron.last_day_of_week);
        assert_eq!(cron.days_of_week, vec![2, 3, 4, 5, 6]);
        // `*/0` 走 increment<=0 分支，等价 `*`。
        let cron = QuartzCron::parse("*/0 * * * * ?").expect("cron");
        assert!(cron.seconds.contains(&ALL_SPEC));
        assert_eq!(cron.seconds.first(), Some(&0));
    }
}
