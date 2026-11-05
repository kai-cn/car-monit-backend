// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/AjaxResult.java
//       ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableDataInfo.java
//       ruoyi-common/src/main/java/com/ruoyi/common/core/domain/R.java
// 职责: 复刻三种响应封套及其字段顺序。
// 对应关系: AjaxResult.success/error -> AjaxResult；TableDataInfo -> TableDataInfo；R.ok/fail -> R。

use axum::http::{header, StatusCode};
use axum::response::{IntoResponse, Response};
use indexmap::IndexMap;
use serde::ser::{Serialize, Serializer};
use serde::Serialize as DeriveSerialize;
use serde_json::{json, Map, Value};

/// Java: `public class AjaxResult extends HashMap<String,Object>`。
/// 键序不取决于插入序，而是 HashMap 桶序，序列化时由 `java_hashmap_ordered` 统一还原
/// （见 `src/api/system/sys_*` 里按实体声明顺序的 reorder_keys，是 Jackson 对实体的另一套规则）。
#[derive(Debug, Clone, Default)]
pub struct AjaxResult(pub IndexMap<String, Value>);

impl AjaxResult {
    pub fn new() -> Self {
        Self(IndexMap::new())
    }

    fn base(msg: impl Into<String>, code: i32) -> Self {
        let mut map = IndexMap::new();
        map.insert("msg".to_string(), Value::String(msg.into()));
        map.insert("code".to_string(), json!(code));
        Self(map)
    }

    /// Java: AjaxResult.success()
    pub fn success() -> Self {
        Self::base("操作成功", 200)
    }

    /// Java: AjaxResult.success(String msg)
    pub fn success_msg(msg: impl Into<String>) -> Self {
        Self::base(msg, 200)
    }

    /// Java: AjaxResult.success(Object data) —— data 为 null 时不写该键。
    pub fn success_data(data: impl DeriveSerialize) -> Self {
        let mut result = Self::base("操作成功", 200);
        let value = serde_json::to_value(data).unwrap_or(Value::Null);
        if !value.is_null() {
            result.0.insert("data".to_string(), value);
        }
        result
    }

    /// Java: AjaxResult.success(String msg, Object data) —— data 为 null 时不写该键。
    pub fn success_msg_data(msg: impl Into<String>, data: impl DeriveSerialize) -> Self {
        let mut result = Self::base(msg, 200);
        let value = serde_json::to_value(data).unwrap_or(Value::Null);
        if !value.is_null() {
            result.0.insert("data".to_string(), value);
        }
        result
    }

    /// Java: AjaxResult.error(String msg)
    pub fn error(msg: impl Into<String>) -> Self {
        Self::base(msg, 500)
    }

    /// Java: `AjaxResult.error(500, e.getMessage())` 且异常 message 为 null ——
    /// HashMap 里 msg 键存在但值为 null，响应是 `{"msg":null,"code":500}`。
    pub fn error_null_msg() -> Self {
        let mut map = IndexMap::new();
        map.insert("msg".to_string(), Value::Null);
        map.insert("code".to_string(), json!(500));
        Self(map)
    }

    /// Java: AjaxResult.error(int code, String msg)
    pub fn error_code(code: i32, msg: impl Into<String>) -> Self {
        Self::base(msg, code)
    }

    /// Java: SysLoginController.login -> AjaxResult.success().put("token", token)
    pub fn login(token: &str) -> Self {
        let mut result = Self::success();
        result
            .0
            .insert("token".to_string(), Value::String(token.to_string()));
        result
    }

    /// Java: AjaxResult.put(key, value)
    pub fn put(mut self, key: &str, value: impl DeriveSerialize) -> Self {
        self.0.insert(
            key.to_string(),
            serde_json::to_value(value).unwrap_or(Value::Null),
        );
        self
    }

    pub fn insert_value(&mut self, key: &str, value: Value) {
        self.0.insert(key.to_string(), value);
    }

    pub fn to_value(&self) -> Value {
        Value::Object(java_hashmap_ordered(&self.0).into_iter().collect())
    }
}

/// Java: `AjaxResult extends HashMap<String,Object>`，Jackson 输出的键序是 HashMap 的桶序：
/// 桶下标 = `(h ^ (h >>> 16)) & (容量 - 1)`，`h` 为 String.hashCode（UTF-16 码元 31 进制），
/// 容量从 16 起、元素数超过 0.75×容量时翻倍；同桶按插入序。
/// 实测校验：`/captchaImage` -> msg,img,code,uuid；`/getInfo` -> msg,code,pjFlag,overdue,
/// permissions,roles,user；`/system/user/1` -> msg,code,roleIds,data,postIds,roles,posts。
pub(crate) fn java_hashmap_ordered(map: &IndexMap<String, Value>) -> IndexMap<String, Value> {
    let mut capacity = 16usize;
    while map.len() > capacity * 3 / 4 {
        capacity *= 2;
    }
    let mut keyed = map
        .iter()
        .enumerate()
        .map(|(index, (key, value))| (bucket(key, capacity), index, key.clone(), value.clone()))
        .collect::<Vec<_>>();
    // sort_by 稳定：同桶保留插入序。
    keyed.sort_by(|left, right| left.0.cmp(&right.0).then(left.1.cmp(&right.1)));
    keyed
        .into_iter()
        .map(|(_, _, key, value)| (key, value))
        .collect()
}

fn bucket(key: &str, capacity: usize) -> usize {
    let mut hash: u32 = 0;
    for unit in key.encode_utf16() {
        hash = hash.wrapping_mul(31).wrapping_add(unit as u32);
    }
    ((hash ^ (hash >> 16)) as usize) & (capacity - 1)
}

/// 把任意 JSON 对象按 Java HashMap 桶序重排——Java 侧用 `HashMap` 承载的响应片段
/// （如 `/monitor/cache` 的 info 与外壳）走这套规则，而非实体声明顺序。
pub(crate) fn java_ordered(value: &Value) -> Value {
    let Some(object) = value.as_object() else {
        return value.clone();
    };
    let indexed = object
        .clone()
        .into_iter()
        .collect::<IndexMap<String, Value>>();
    Value::Object(java_hashmap_ordered(&indexed).into_iter().collect())
}

/// Java: `Properties`（Hashtable 子类）的迭代顺序——容量从 11 起按 `2n+1` 扩容，
/// 桶下标 = `(hash & 0x7FFFFFFF) % 容量`（不做 `h ^ (h>>>16)` 扩散），
/// 从最后一个桶往前遍历。`/monitor/cache` 的 `data.info` 就是 Jackson 直接序列化
/// Properties 的结果：这样排完与 Java 大部分一致，但同桶内的链表顺序随 JDK 的
/// 头插/尾插实现有关，仍有出入（该端点因此保留 ORDER-DIFF 级 WARN，值完全一致）。
pub(crate) fn java_hashtable_ordered(value: &Value) -> Value {
    let Some(object) = value.as_object() else {
        return value.clone();
    };
    let mut capacity = 11usize;
    while object.len() > capacity * 3 / 4 {
        capacity = capacity * 2 + 1;
    }
    let mut buckets = vec![Vec::new(); capacity];
    for (index, (key, value)) in object.iter().enumerate() {
        let mut hash: u32 = 0;
        for unit in key.encode_utf16() {
            hash = hash.wrapping_mul(31).wrapping_add(unit as u32);
        }
        buckets[(hash & 0x7FFF_FFFF) as usize % capacity].push((index, key.clone(), value.clone()));
    }
    let mut out = Map::with_capacity(object.len());
    for bucket in buckets.iter().rev() {
        for (_, key, value) in bucket {
            out.insert(key.clone(), value.clone());
        }
    }
    Value::Object(out)
}

impl Serialize for AjaxResult {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        java_hashmap_ordered(&self.0).serialize(serializer)
    }
}

impl IntoResponse for AjaxResult {
    fn into_response(self) -> Response {
        let body = serde_json::to_vec(&self).unwrap_or_else(|_| b"{}".to_vec());
        (
            StatusCode::OK,
            [(header::CONTENT_TYPE, "application/json")],
            body,
        )
            .into_response()
    }
}

/// Java: `public class TableDataInfo implements Serializable`
/// 字段顺序必须是 `total -> rows -> code -> msg`（实测）。
#[derive(Debug, Clone, DeriveSerialize)]
pub struct TableDataInfo<T> {
    pub total: i64,
    pub rows: Vec<T>,
    pub code: i32,
    /// Java `new TableDataInfo()` 的 msg 为 null（分表查询成功路径即如此）。
    pub msg: Option<String>,
}

impl<T> TableDataInfo<T> {
    /// Java: getDataTable(list) -> new TableDataInfo(list, new PageInfo(list).getTotal())
    pub fn new(total: i64, rows: Vec<T>) -> Self {
        Self {
            total,
            rows,
            code: 200,
            msg: Some("查询成功".to_string()),
        }
    }

    /// Java: `new TableDataInfo()` —— code=0、msg=null。
    pub fn empty() -> Self {
        Self {
            total: 0,
            rows: Vec::new(),
            code: 0,
            msg: None,
        }
    }
}

impl<T: DeriveSerialize> IntoResponse for TableDataInfo<T> {
    fn into_response(self) -> Response {
        let body = serde_json::to_vec(&self).unwrap_or_else(|_| b"{}".to_vec());
        (
            StatusCode::OK,
            [(header::CONTENT_TYPE, "application/json")],
            body,
        )
            .into_response()
    }
}

/// Java: `public class R<T>`（仅 /test/** 使用）
#[derive(Debug, Clone, DeriveSerialize)]
pub struct R<T> {
    pub code: i32,
    pub msg: String,
    pub data: Option<T>,
}

impl<T> R<T> {
    pub fn ok(data: Option<T>) -> Self {
        Self {
            code: 200,
            msg: "操作成功".to_string(),
            data,
        }
    }

    pub fn fail(code: i32, msg: impl Into<String>) -> Self {
        Self {
            code,
            msg: msg.into(),
            data: None,
        }
    }
}

impl<T: DeriveSerialize> IntoResponse for R<T> {
    fn into_response(self) -> Response {
        let body = serde_json::to_vec(&self).unwrap_or_else(|_| b"{}".to_vec());
        (
            StatusCode::OK,
            [(header::CONTENT_TYPE, "application/json")],
            body,
        )
            .into_response()
    }
}

/// Java: Spring Boot 默认 `/error` 响应体。
/// 实测：`{"timestamp":"...","status":404,"error":"Not Found","path":"/x"}`。
#[derive(Debug, Clone, DeriveSerialize)]
pub struct DefaultErrorBody {
    pub timestamp: String,
    pub status: i32,
    pub error: String,
    pub path: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn keys(inserted: &[&str]) -> Vec<String> {
        let mut map = IndexMap::new();
        for key in inserted {
            map.insert((*key).to_string(), Value::Null);
        }
        java_hashmap_ordered(&map).keys().cloned().collect()
    }

    /// 与 Java 实测响应顺序逐条对齐（均为 HashMap<String,Object> 子类）。
    #[test]
    fn ajax_result_uses_java_hash_bucket_order() {
        assert_eq!(
            keys(&["msg", "code", "uuid", "img"]),
            vec!["msg", "img", "code", "uuid"]
        );
        assert_eq!(
            keys(&[
                "msg",
                "code",
                "pjFlag",
                "overdue",
                "permissions",
                "roles",
                "user"
            ]),
            vec![
                "msg",
                "code",
                "pjFlag",
                "overdue",
                "permissions",
                "roles",
                "user"
            ]
        );
        assert_eq!(
            keys(&["msg", "code", "roles", "posts", "postIds", "roleIds", "data"]),
            vec!["msg", "code", "roleIds", "data", "postIds", "roles", "posts"]
        );
        assert_eq!(
            keys(&["msg", "code", "data", "roleGroup", "postGroup"]),
            vec!["msg", "postGroup", "code", "data", "roleGroup"]
        );
        assert_eq!(
            keys(&["msg", "code", "menus", "checkedKeys"]),
            vec!["msg", "code", "menus", "checkedKeys"]
        );
    }

    /// 与插入顺序无关：同输入集合必得同输出。
    #[test]
    fn order_is_independent_of_insertion() {
        let a = keys(&["msg", "code", "data", "token"]);
        let b = keys(&["data", "token", "msg", "code"]);
        assert_eq!(a, b);
    }
}
