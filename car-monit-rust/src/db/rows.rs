// 来源: RuoYi 实体类（BaseEntity 子类）+ MyBatis resultMap 的列到属性映射。
// 职责: 把 MySQL 行按列顺序转成 camelCase 的 JSON 对象。
// 对应关系: MyBatis resultMap（column -> property）+ Jackson 序列化 -> row_to_json。
//
// 为什么用动态映射：base/manager 切片有 60+ 张表、每张 20-60 列，逐列手写实体
// 既冗长又容易漏字段。MyBatis 的 resultMap 本身就是「列名 -> 属性名」的机械映射，
// 这里按同一规则做（下划线转驼峰），并保持 SELECT 的列顺序（Jackson 按 getter 顺序，
// MyBatis 按 alias 顺序，两者在本项目里等价）。

use base64::Engine;
use serde_json::{Map, Value};
use sqlx::mysql::MySqlRow;
use sqlx::{Column, Row, TypeInfo, ValueRef};

/// Java: MyBatis 自动映射 `user_name -> userName`。
pub fn column_to_property(column: &str) -> String {
    let mut out = String::with_capacity(column.len());
    let mut upper_next = false;
    for ch in column.chars() {
        if ch == '_' {
            upper_next = true;
            continue;
        }
        if upper_next {
            out.extend(ch.to_uppercase());
            upper_next = false;
        } else {
            out.push(ch);
        }
    }
    out
}

/// 把一行按列顺序转成 JSON；NULL 输出 null。
pub fn row_to_json(row: &MySqlRow) -> Value {
    let mut map = Map::with_capacity(row.columns().len());
    for (index, column) in row.columns().iter().enumerate() {
        let key = column_to_property(column.name());
        map.insert(key, cell_to_json(row, index, column.type_info().name()));
    }
    Value::Object(map)
}

fn cell_to_json(row: &MySqlRow, index: usize, type_name: &str) -> Value {
    // 先判 NULL：MySql 的 ValueRef 提供 is_null。
    match row.try_get_raw(index) {
        Ok(raw) if raw.is_null() => return Value::Null,
        Ok(_) => {}
        Err(_) => return Value::Null,
    }

    match type_name {
        "TINYINT" | "SMALLINT" | "MEDIUMINT" | "INT" | "INTEGER" | "BIGINT" | "YEAR" => {
            // sqlx 对不同位宽的整数类型解码是严格的：TINYINT 只能按 i8 取。
            macro_rules! try_num {
                ($($ty:ty),*) => {$(
                    if let Ok(value) = row.try_get::<$ty, _>(index) {
                        return Value::from(value);
                    }
                )*};
            }
            try_num!(i64, u64, i32, u32, i16, u16, i8, u8);
        }
        // sqlx 把 tinyint(1) 映射成 BOOLEAN。
        "BOOLEAN" | "BOOL" => {
            if let Ok(value) = row.try_get::<bool, _>(index) {
                return Value::Bool(value);
            }
            if let Ok(value) = row.try_get::<i8, _>(index) {
                return Value::Bool(value != 0);
            }
        }
        "TINYINT UNSIGNED" | "SMALLINT UNSIGNED" | "MEDIUMINT UNSIGNED"
        | "INT UNSIGNED" | "BIGINT UNSIGNED" => {
            macro_rules! try_unum {
                ($($ty:ty),*) => {$(
                    if let Ok(value) = row.try_get::<$ty, _>(index) {
                        return Value::from(value);
                    }
                )*};
            }
            try_unum!(u64, i64, u32, i32, u16, i16, u8, i8);
        }
        "FLOAT" | "DOUBLE" => {
            if let Ok(value) = row.try_get::<f64, _>(index) {
                return serde_json::Number::from_f64(value)
                    .map(Value::Number)
                    .unwrap_or(Value::Null);
            }
        }
        "DECIMAL" | "NUMERIC" => {
            if let Ok(value) = row.try_get::<rust_decimal::Decimal, _>(index) {
                // Jackson 默认把 BigDecimal 写成数字；保持精度用字符串再解析。
                if let Ok(number) = value.to_string().parse::<serde_json::Number>() {
                    return Value::Number(number);
                }
                return Value::String(value.to_string());
            }
        }
        "DATE" => {
            if let Ok(value) = row.try_get::<chrono::NaiveDate, _>(index) {
                return Value::String(value.format("%Y-%m-%d").to_string());
            }
        }
        "DATETIME" | "TIMESTAMP" => {
            if let Ok(value) = row.try_get::<chrono::NaiveDateTime, _>(index) {
                return Value::String(value.format("%Y-%m-%d %H:%M:%S").to_string());
            }
        }
        "TIME" => {
            if let Ok(value) = row.try_get::<chrono::NaiveTime, _>(index) {
                return Value::String(value.format("%H:%M:%S").to_string());
            }
        }
        "BLOB" | "TINYBLOB" | "MEDIUMBLOB" | "LONGBLOB" | "BINARY" | "VARBINARY" => {
            if let Ok(value) = row.try_get::<Vec<u8>, _>(index) {
                // MyBatis 对 String 属性使用 StringTypeHandler，BLOB 会按文本读出；
                // 只有真正的二进制字段（Java 属性为 byte[]）才走 Jackson 的 base64。
                if let Ok(text) = String::from_utf8(value.clone()) {
                    return Value::String(text);
                }
                return Value::String(base64::engine::general_purpose::STANDARD.encode(value));
            }
        }
        _ => {}
    }

    // 兜底：VARCHAR/CHAR/TEXT/JSON/ENUM/SET 都按字符串输出。
    match row.try_get::<String, _>(index) {
        Ok(value) => Value::String(value),
        Err(_) => Value::Null,
    }
}

/// 多行转换。
pub fn rows_to_json(rows: &[MySqlRow]) -> Vec<Value> {
    rows.iter().map(row_to_json).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn camel_case_conversion_matches_mybatis() {
        assert_eq!(column_to_property("user_name"), "userName");
        assert_eq!(column_to_property("gantry_code_in"), "gantryCodeIn");
        assert_eq!(column_to_property("id"), "id");
        assert_eq!(column_to_property("created_at_time"), "createdAtTime");
    }
}
