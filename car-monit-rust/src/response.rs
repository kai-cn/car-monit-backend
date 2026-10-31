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
use serde_json::{json, Value};

/// Java: `public class AjaxResult extends HashMap<String,Object>`。
/// 注意：Java 的实际字段顺序来自 HashMap 桶序，不是插入序。实测顺序：
/// 错误 `msg,code`；登录 `msg,code,token`；getInfo `msg,code,pjFlag,overdue,permissions,roles,user`。
/// 这里用 IndexMap 固定插入顺序，构造器按实测顺序插入。
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

    /// Java: AjaxResult.success(Object data)
    pub fn success_data(data: impl DeriveSerialize) -> Self {
        let mut result = Self::base("操作成功", 200);
        result.0.insert(
            "data".to_string(),
            serde_json::to_value(data).unwrap_or(Value::Null),
        );
        result
    }

    /// Java: AjaxResult.success(String msg, Object data)
    pub fn success_msg_data(msg: impl Into<String>, data: impl DeriveSerialize) -> Self {
        let mut result = Self::base(msg, 200);
        result.0.insert(
            "data".to_string(),
            serde_json::to_value(data).unwrap_or(Value::Null),
        );
        result
    }

    /// Java: AjaxResult.error(String msg)
    pub fn error(msg: impl Into<String>) -> Self {
        Self::base(msg, 500)
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
        Value::Object(self.0.clone().into_iter().collect())
    }
}

impl Serialize for AjaxResult {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        self.0.serialize(serializer)
    }
}

impl IntoResponse for AjaxResult {
    fn into_response(self) -> Response {
        let body = serde_json::to_vec(&self).unwrap_or_else(|_| b"{}".to_vec());
        (
            StatusCode::OK,
            [(header::CONTENT_TYPE, "application/json;charset=UTF-8")],
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
            [(header::CONTENT_TYPE, "application/json;charset=UTF-8")],
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
            [(header::CONTENT_TYPE, "application/json;charset=UTF-8")],
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
