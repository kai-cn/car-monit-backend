// 来源: 多个 domain 上的 Jackson 注解（@JsonFormat / @JsonInclude）
// 职责: 日期/空值序列化规则，供 serde 逐字段复用。

use chrono::{DateTime, Local, NaiveDate, NaiveDateTime, TimeZone};
use serde::{Deserialize, Deserializer, Serializer};

pub const DATE_TIME_FORMAT: &str = "%Y-%m-%d %H:%M:%S";
pub const DATE_FORMAT: &str = "%Y-%m-%d";

/// Jackson 默认：未标注 @JsonFormat 的 java.util.Date 输出 epoch 毫秒。
pub fn serialize_millis<S: Serializer>(
    value: &Option<NaiveDateTime>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    match value {
        Some(dt) => serializer.serialize_i64(dt.and_utc().timestamp_millis()),
        None => serializer.serialize_none(),
    }
}

/// 同时接受 epoch 毫秒、`yyyy-MM-dd HH:mm:ss`、`yyyy-MM-dd` 与 RFC3339。
pub fn deserialize_millis<'de, D: Deserializer<'de>>(
    deserializer: D,
) -> Result<Option<NaiveDateTime>, D::Error> {
    use serde::de::Error as _;
    let value = serde_json::Value::deserialize(deserializer)?;
    match value {
        serde_json::Value::Null => Ok(None),
        other => parse_json_datetime(&other)
            .map(Some)
            .ok_or_else(|| D::Error::custom(format!("invalid date: {other}"))),
    }
}

/// 宽容解析上游 JSON 时间：epoch 毫秒/秒、`yyyy-MM-dd HH:mm:ss`、`yyyy-MM-dd`、RFC3339。
/// 用于 Forest 接口返回的 `Date`（上游格式在 Java 侧并不固定）。
pub fn parse_json_datetime(value: &serde_json::Value) -> Option<NaiveDateTime> {
    match value {
        serde_json::Value::Null => None,
        serde_json::Value::Number(n) => {
            let raw = n.as_i64()?;
            // Java Date 的 JSON 值是毫秒；上游偶尔给秒，这里按量级区分。
            let millis = if raw.abs() < 100_000_000_000 { raw * 1000 } else { raw };
            Local
                .timestamp_millis_opt(millis)
                .single()
                .map(|dt| dt.naive_local())
        }
        serde_json::Value::String(s) => parse_datetime(s),
        _ => None,
    }
}

/// @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
pub fn serialize_datetime<S: Serializer>(
    value: &Option<NaiveDateTime>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    match value {
        Some(dt) => serializer.serialize_str(&dt.format(DATE_TIME_FORMAT).to_string()),
        None => serializer.serialize_none(),
    }
}

pub fn deserialize_datetime<'de, D: Deserializer<'de>>(
    deserializer: D,
) -> Result<Option<NaiveDateTime>, D::Error> {
    deserialize_millis(deserializer)
}

/// @JsonFormat(pattern = "yyyy-MM-dd")
pub fn serialize_date<S: Serializer>(
    value: &Option<NaiveDateTime>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    match value {
        Some(dt) => serializer.serialize_str(&dt.format(DATE_FORMAT).to_string()),
        None => serializer.serialize_none(),
    }
}

pub fn deserialize_date<'de, D: Deserializer<'de>>(
    deserializer: D,
) -> Result<Option<NaiveDateTime>, D::Error> {
    use serde::de::Error as _;
    let value = serde_json::Value::deserialize(deserializer)?;
    match value {
        serde_json::Value::Null => Ok(None),
        serde_json::Value::String(s) => {
            if let Ok(d) = NaiveDate::parse_from_str(&s, DATE_FORMAT) {
                return Ok(Some(d.and_hms_opt(0, 0, 0).expect("midnight")));
            }
            parse_datetime(&s)
                .map(Some)
                .ok_or_else(|| D::Error::custom(format!("invalid date: {s}")))
        }
        serde_json::Value::Number(n) => {
            let millis = n
                .as_i64()
                .ok_or_else(|| D::Error::custom("invalid date millis"))?;
            Ok(Local
                .timestamp_millis_opt(millis)
                .single()
                .map(|dt| dt.naive_local()))
        }
        _ => Err(D::Error::custom("invalid date value")),
    }
}

fn parse_datetime(s: &str) -> Option<NaiveDateTime> {
    let s = s.trim();
    NaiveDateTime::parse_from_str(s, DATE_TIME_FORMAT)
        .ok()
        .or_else(|| NaiveDateTime::parse_from_str(s, "%Y-%m-%d %H:%M:%S%.f").ok())
        .or_else(|| NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f").ok())
        .or_else(|| {
            DateTime::parse_from_rfc3339(s)
                .ok()
                .map(|dt| dt.naive_local())
        })
        .or_else(|| {
            NaiveDate::parse_from_str(s, DATE_FORMAT)
                .ok()
                .and_then(|d| d.and_hms_opt(0, 0, 0))
        })
}

/// `@JsonInclude(JsonInclude.Include.NON_EMPTY)` 对 Option<Map> 的近似。
pub fn is_none_or_empty_map(value: &Option<serde_json::Map<String, serde_json::Value>>) -> bool {
    value.as_ref().is_none_or(|m| m.is_empty())
}

/// `@JsonInclude(JsonInclude.Include.NON_EMPTY)` 对 Option<Vec> 的近似。
pub fn is_none_or_empty_vec<T>(value: &Option<Vec<T>>) -> bool {
    value.as_ref().is_none_or(|v| v.is_empty())
}
