// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportSysUtil.java
//       ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportUtil.java
//       ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportEntity.java
//       ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportErrorEntity.java
// 职责: 导入用的 xlsx 读取（Java 的单元格取值规则）+ 按 ImportEntity 列表做校验并转成实体 JSON。
// 对应关系: getXSSFSheet/colVdaExcel07/08/dataRtnExcel07/08 -> read_sheet/header_at/data_rows；
//           ImportUtil.importExcel -> apply_rules。

use regex::Regex;
use serde_json::{json, Map, Value};

use crate::error::AppError;

/// Java: `ImportEntity`（列名、属性名、校验规则码，多个规则以逗号分隔）。
pub struct ImportField {
    pub col_name: &'static str,
    pub prop: &'static str,
    pub rules: &'static str,
}

/// 常量里构造 `ImportField` 用的简写。
pub const fn field(col_name: &'static str, prop: &'static str, rules: &'static str) -> ImportField {
    ImportField {
        col_name,
        prop,
        rules,
    }
}

/// Java: `ImportErrorEntity` —— Jackson 出来的键序就是 rowNo/colName/message。
pub fn error_item(row_no: i64, col_name: &str, message: String) -> Value {
    json!({ "rowNo": row_no, "colName": col_name, "message": message })
}

/// Java: `ImportSysUtil.getCellFormatValue08` —— 日期取 `yyyy-MM-dd HH:mm:ss`，
/// 其余数值一律 `DecimalFormat("#.##")`，最后 trim。
#[cfg(feature = "excel")]
fn cell_text(cell: &calamine::Data) -> String {
    use calamine::Data;
    let text = match cell {
        Data::Empty => String::new(),
        Data::String(text) => text.clone(),
        Data::Bool(flag) => flag.to_string(),
        Data::Float(value) => decimal_hash_dot_2(*value),
        Data::Int(value) => decimal_hash_dot_2(*value as f64),
        // calamine 的 chrono 特性没开，这里自己按 Excel 序列号折算（与 POI 的 1900 历元一致）。
        Data::DateTime(value) => excel_serial_to_text(value.as_f64()),
        Data::DateTimeIso(text) | Data::DurationIso(text) => text.clone(),
        // Java: case ERROR 只打印，不赋值 -> 空串
        Data::Error(_) => String::new(),
    };
    text.trim().to_string()
}

/// Java: `DecimalFormat("#.##")` —— 无分组、最多两位小数、不留尾随 0，
/// 且绝对值小于 1 时不写整数位的 0（0.5 -> ".5"）。
pub fn decimal_hash_dot_2(value: f64) -> String {
    if !value.is_finite() {
        return value.to_string();
    }
    let rounded = (value * 100.0).round_ties_even() / 100.0;
    let negative = rounded < 0.0 || (rounded == 0.0 && rounded.is_sign_negative());
    let absolute = rounded.abs();
    let mut text = if absolute.fract() == 0.0 {
        format!("{}", absolute as i128)
    } else {
        let mut text = format!("{absolute:.2}");
        while text.ends_with('0') {
            text.pop();
        }
        if text.ends_with('.') {
            text.pop();
        }
        text
    };
    if negative {
        text.insert(0, '-');
    }
    if let Some(rest) = text.strip_prefix("0.") {
        text = format!(".{rest}");
    } else if text.starts_with("-0.") {
        text = format!("-{}", &text[2..]);
    }
    text
}

/// Excel 序列号（1900 历元，1900-01-01=1）转 `yyyy-MM-dd HH:mm:ss`。
/// 60 以下受 POI 的 1900 闰年 bug 影响，现实日期不会走到那里。
pub fn excel_serial_to_text(serial: f64) -> String {
    let base = chrono::NaiveDate::from_ymd_opt(1899, 12, 30)
        .and_then(|date| date.and_hms_opt(0, 0, 0))
        .unwrap();
    let seconds = (serial * 86_400.0).round() as i64;
    match base.checked_add_signed(chrono::Duration::seconds(seconds)) {
        Some(moment) => moment.format("%Y-%m-%d %H:%M:%S").to_string(),
        None => decimal_hash_dot_2(serial),
    }
}

/// Java: `getXSSFSheet(is, 0)` 后的整张表，按行给出文本单元格。
#[cfg(feature = "excel")]
pub fn read_sheet(bytes: &[u8]) -> Result<Vec<Vec<String>>, AppError> {
    use calamine::{open_workbook_auto_from_rs, Reader};
    use std::io::Cursor;

    let cursor = Cursor::new(bytes.to_vec());
    let mut workbook = open_workbook_auto_from_rs(cursor)
        .map_err(|err| AppError::Service(format!("读取Excel失败: {err}")))?;
    let Some(Ok(range)) = workbook.worksheet_range_at(0) else {
        return Ok(Vec::new());
    };
    Ok(range
        .rows()
        .map(|row| row.iter().map(cell_text).collect())
        .collect())
}

#[cfg(not(feature = "excel"))]
pub fn read_sheet(_bytes: &[u8]) -> Result<Vec<Vec<String>>, AppError> {
    Err(AppError::Service("编译时未启用 excel feature".to_string()))
}

/// Java: `colVdaExcel07/08` —— 比对第 `header_row` 行（0 基）前 cols.len() 个单元格。
pub fn header_at(rows: &[Vec<String>], header_row: usize, cols: &[&str]) -> bool {
    let Some(row) = rows.get(header_row) else {
        return false;
    };
    cols.iter()
        .enumerate()
        .all(|(index, want)| row.get(index).map(String::as_str) == Some(*want))
}

/// Java: `dataRtnExcel08(sheet, colsName, rowNume, num)` —— 从 `start` 行起，
/// 跳过 `skip` 里的列下标；整行为空或首列是 `break`/`结束` 就停止读取。
pub fn data_rows(
    rows: &[Vec<String>],
    start: usize,
    width: usize,
    skip: &[usize],
) -> Vec<Vec<String>> {
    let mut out = Vec::new();
    for index in start..rows.len() {
        let Some(row) = rows.get(index) else { break };
        if row.iter().all(|cell| cell.is_empty()) {
            break;
        }
        let first = row.first().cloned().unwrap_or_default();
        if first == "break" || first == "结束" {
            break;
        }
        out.push(
            (0..width)
                .map(|column| {
                    if skip.contains(&column) {
                        String::new()
                    } else {
                        row.get(column).cloned().unwrap_or_default()
                    }
                })
                .collect(),
        );
    }
    out
}

fn matches(value: &str, pattern: &str) -> bool {
    Regex::new(pattern)
        .map(|regex| regex.is_match(value))
        .unwrap_or(false)
}

/// Java: `ImportUtil.importExcel` 的校验部分。
/// 规则码：1 必填、2 小数、3 正整数、4 日期、5 身份证、6 年月、7 数值、8 年月日时分秒。
/// 返回属性->值的映射，**仅当整份导入到这里还没有任何错误**（Java 的 `errorList.size() == 0` 判据）。
pub fn apply_rules(
    fields: &[ImportField],
    strs: &[String],
    index: usize,
    errors: &mut Vec<Value>,
) -> Option<Value> {
    for (position, field) in fields.iter().enumerate() {
        let value = strs.get(position).cloned().unwrap_or_default();
        if field.rules.is_empty() {
            continue;
        }
        for code in field.rules.split(',') {
            if code == "1" && value.is_empty() {
                errors.push(error_item(
                    index as i64 + 1,
                    field.col_name,
                    "不能为空".to_string(),
                ));
            }
            if value.is_empty() {
                continue;
            }
            let (pattern, message) = match code {
                "2" => (r"^(-?\d+)(\.\d+)?$", "不是小数"),
                "3" => (r"^[0-9]*$", "不是正整数"),
                "4" => (
                    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                    "日期格式（年-月-日）不正确",
                ),
                "5" => (
                    r"^[1-9]\d{5}[1-9]\d{3}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}([0-9]|X|x)$",
                    "身份证号码不正确",
                ),
                "6" => (r"^\d{4}(\-|\/|\.)\d{1,2}$", "日期格式（年-月）不正确"),
                "7" => (r"^(\-|\+)?\d+(\.\d+)?$", "不是数值"),
                "8" => (
                    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
                    "日期格式（年月日时分秒）不正确",
                ),
                _ => continue,
            };
            if !matches(&value, pattern) {
                errors.push(error_item(
                    index as i64 + 1,
                    field.col_name,
                    message.to_string(),
                ));
            }
        }
    }

    if !errors.is_empty() {
        return None;
    }
    let mut object = Map::new();
    for (position, field) in fields.iter().enumerate() {
        if field.prop.is_empty() {
            continue;
        }
        object.insert(
            field.prop.to_string(),
            json!(strs.get(position).cloned().unwrap_or_default()),
        );
    }
    Some(Value::Object(object))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decimal_hash_dot_two_matches_java() {
        // Java: new DecimalFormat("#.##")
        assert_eq!(decimal_hash_dot_2(12.0), "12");
        assert_eq!(decimal_hash_dot_2(12.5), "12.5");
        assert_eq!(decimal_hash_dot_2(12.50), "12.5");
        assert_eq!(decimal_hash_dot_2(1234.5678), "1234.57");
        assert_eq!(decimal_hash_dot_2(-1234.5678), "-1234.57");
        assert_eq!(decimal_hash_dot_2(2026.0), "2026");
        assert_eq!(decimal_hash_dot_2(15800001234.0), "15800001234");
        // 绝对值小于 1 时 Java 不写整数位的 0
        assert_eq!(decimal_hash_dot_2(0.5), ".5");
        assert_eq!(decimal_hash_dot_2(-0.5), "-.5");
        assert_eq!(decimal_hash_dot_2(0.0), "0");
        // HALF_EVEN：0.125 -> 0.12
        assert_eq!(decimal_hash_dot_2(0.125), ".12");
    }

    #[test]
    fn excel_serial_maps_to_java_date_text() {
        // 2026-01-02 03:04:05：Excel 序列号 = 距 1899-12-30 的天数 + 一天中的比例
        let days = chrono::NaiveDate::from_ymd_opt(2026, 1, 2)
            .expect("date")
            .signed_duration_since(chrono::NaiveDate::from_ymd_opt(1899, 12, 30).expect("epoch"))
            .num_days();
        let serial = days as f64 + (3 * 3600 + 4 * 60 + 5) as f64 / 86_400.0;
        assert_eq!(excel_serial_to_text(serial), "2026-01-02 03:04:05");
    }

    #[test]
    fn header_and_data_row_rules() {
        let rows = vec![
            vec!["标题".to_string()],
            vec!["甲".to_string(), "乙".to_string()],
            vec!["A".to_string(), "B".to_string()],
            vec!["1".to_string(), "2".to_string()],
            vec!["3".to_string(), "".to_string()],
            vec!["结束".to_string(), "x".to_string()],
            vec!["9".to_string(), "9".to_string()],
        ];
        assert!(header_at(&rows, 1, &["甲", "乙"]));
        assert!(!header_at(&rows, 1, &["甲", "丙"]));
        assert!(!header_at(&rows, 9, &["甲"]));

        // 从行 3 起，跳过第 1 列；首列遇到「结束」就停。
        let data = data_rows(&rows, 3, 2, &[1]);
        assert_eq!(
            data,
            vec![
                vec!["1".to_string(), "".to_string()],
                vec!["3".to_string(), "".to_string()]
            ]
        );
    }

    #[test]
    fn apply_rules_messages_match_java() {
        let fields = [
            ImportField {
                col_name: "出口时间",
                prop: "outTime",
                rules: "1,8",
            },
            ImportField {
                col_name: "车牌",
                prop: "carNo",
                rules: "1",
            },
            ImportField {
                col_name: "小计",
                prop: "chargeAmount",
                rules: "1,2",
            },
        ];
        let mut errors = Vec::new();
        let strs = vec![
            "2026/01/02 03:04:05".to_string(),
            String::new(),
            "12.5".to_string(),
        ];
        assert!(apply_rules(&fields, &strs, 0, &mut errors).is_none());
        assert_eq!(errors.len(), 2);
        assert_eq!(errors[0]["colName"], "出口时间");
        assert_eq!(errors[0]["message"], "日期格式（年月日时分秒）不正确");
        assert_eq!(errors[1]["message"], "不能为空");
        assert_eq!(errors[0]["rowNo"], 1);

        let mut clean = Vec::new();
        let strs = vec![
            "2026-01-02 03:04:05".to_string(),
            "赣A12345".to_string(),
            "12.5".to_string(),
        ];
        let object = apply_rules(&fields, &strs, 2, &mut clean).expect("应当转换成功");
        assert!(clean.is_empty());
        assert_eq!(object["outTime"], "2026-01-02 03:04:05");
        assert_eq!(object["chargeAmount"], "12.5");
    }

    #[test]
    fn int_rule_accepts_only_unsigned_digits() {
        let fields = [ImportField {
            col_name: "轴数",
            prop: "carNum",
            rules: "3",
        }];
        for (value, ok) in [
            ("2", true),
            ("0", true),
            ("-2", false),
            ("2.5", false),
            ("", true),
        ] {
            let mut errors = Vec::new();
            apply_rules(&fields, &[value.to_string()], 0, &mut errors);
            assert_eq!(errors.is_empty(), ok, "{value:?}");
        }
    }
}
