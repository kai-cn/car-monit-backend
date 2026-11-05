// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/redis/RedisCache.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/config/FastJson2JsonRedisSerializer.java
// 职责: Redis 读写封装，保持 Java 的 JSON 值编码（FastJson2 WriteClassName）。
// 对应关系: RedisCache.getCacheObject/setCacheObject -> get_object/set_object；
//           FastJson2 的 @type 由 domain 结构体的 serde 字段携带。

use std::time::Duration;

use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use serde::de::DeserializeOwned;
use serde::Serialize;

use crate::error::AppError;

#[derive(Clone)]
pub struct RedisCache {
    conn: ConnectionManager,
}

impl RedisCache {
    pub async fn connect(url: &str) -> anyhow::Result<Self> {
        let client = redis::Client::open(url)?;
        let conn = client.get_connection_manager().await?;
        Ok(Self { conn })
    }

    /// Java: `getCacheObject(String key)`
    /// 值是 JSON 文本：String 会带引号，对象带 `@type`。serde 直接解析即可。
    pub async fn get_object<T: DeserializeOwned>(&self, key: &str) -> Result<Option<T>, AppError> {
        let mut conn = self.conn.clone();
        let raw: Option<String> = conn.get(key).await?;
        match raw {
            None => Ok(None),
            Some(text) => match serde_json::from_str::<T>(&sanitize_fastjson2(&text)) {
                Ok(value) => Ok(Some(value)),
                Err(err) => {
                    // Java FastJson2 遇到损坏缓存通常抛错；这里显式暴露原因便于排查。
                    Err(AppError::Cache(format!("反序列化缓存 {key} 失败: {err}")))
                }
            },
        }
    }

    /// Java: `setCacheObject(key, value)`（无 TTL）
    pub async fn set_object<T: Serialize>(&self, key: &str, value: &T) -> Result<(), AppError> {
        self.set_object_ttl(key, value, None).await
    }

    /// Java: `setCacheObject(key, value, timeout, unit)`
    pub async fn set_object_ttl<T: Serialize>(
        &self,
        key: &str,
        value: &T,
        ttl: Option<Duration>,
    ) -> Result<(), AppError> {
        let text = serde_json::to_string(value)?;
        let mut conn = self.conn.clone();
        match ttl {
            Some(ttl) => {
                let seconds = ttl.as_secs().max(1);
                let _: () = conn.set_ex(key, text, seconds).await?;
            }
            None => {
                let _: () = conn.set(key, text).await?;
            }
        }
        Ok(())
    }

    /// Java: `deleteObject(String key)`
    pub async fn delete_object(&self, key: &str) -> Result<(), AppError> {
        let mut conn = self.conn.clone();
        let _: i64 = conn.del(key).await?;
        Ok(())
    }

    /// Java: `hasKey(String key)`
    pub async fn has_key(&self, key: &str) -> Result<bool, AppError> {
        let mut conn = self.conn.clone();
        let count: i64 = conn.exists(key).await?;
        Ok(count > 0)
    }

    /// Java: `getCacheList(String key)` —— Redis list，元素为 FastJson 文本。
    pub async fn get_list<T: DeserializeOwned>(&self, key: &str) -> Result<Vec<T>, AppError> {
        let mut conn = self.conn.clone();
        let items: Vec<String> = conn.lrange(key, 0, -1).await?;
        let mut values = Vec::with_capacity(items.len());
        for item in items {
            values.push(
                serde_json::from_str::<T>(&sanitize_fastjson2(&item)).map_err(|err| {
                    AppError::Cache(format!("反序列化缓存列表 {key} 失败: {err}"))
                })?,
            );
        }
        Ok(values)
    }

    /// Java: `setCacheList(String key, List<T>)` —— 先删除再整体右推。
    pub async fn set_list<T: Serialize>(&self, key: &str, values: &[T]) -> Result<(), AppError> {
        let mut conn = self.conn.clone();
        let _: () = conn.del(key).await?;
        for value in values {
            let text = serde_json::to_string(value)?;
            let _: () = conn.rpush(key, text).await?;
        }
        Ok(())
    }

    /// Redis 原生命令，用于后续切片的计数器/限流。
    pub async fn incr(&self, key: &str) -> Result<i64, AppError> {
        let mut conn = self.conn.clone();
        let value: i64 = conn.incr(key, 1).await?;
        Ok(value)
    }

    /// Java: `RedisTemplate<String,String>.opsForValue().get(key)` —— 原始字符串。
    pub async fn get_string(&self, key: &str) -> Result<Option<String>, AppError> {
        let mut conn = self.conn.clone();
        Ok(conn.get(key).await?)
    }

    /// Java: `opsForValue().set(key, value, Duration)` —— StringRedisSerializer 原样写入。
    pub async fn set_string_ex(
        &self,
        key: &str,
        value: &str,
        seconds: u64,
    ) -> Result<(), AppError> {
        let mut conn = self.conn.clone();
        let _: () = conn.set_ex(key, value, seconds.max(1)).await?;
        Ok(())
    }

    /// Java: `RedisTemplate.keys(pattern)`（生产环境大 key 空间慎用，与 Java 行为一致）。
    pub async fn keys(&self, pattern: &str) -> Result<Vec<String>, AppError> {
        let mut conn = self.conn.clone();
        Ok(conn.keys(pattern).await?)
    }

    /// Java: `connection.info()` / `connection.info(section)` —— 原始 INFO 文本。
    pub async fn info(&self, section: Option<&str>) -> Result<String, AppError> {
        let mut conn = self.conn.clone();
        let mut command = redis::cmd("INFO");
        if let Some(section) = section {
            command.arg(section);
        }
        Ok(command.query_async(&mut conn).await?)
    }

    /// Java: `connection.dbSize()`。
    pub async fn db_size(&self) -> Result<i64, AppError> {
        let mut conn = self.conn.clone();
        let command = redis::cmd("DBSIZE");
        Ok(command.query_async(&mut conn).await?)
    }
}

/// FastJson2 `WriteClassName`：给缓存对象补 `@type`，Java 端 `getCacheObject`
/// / `getCacheList` 依赖它才能反序列化成具体类（否则得到 JSONObject 抛 ClassCastException）。
pub fn stamp_type(mut value: serde_json::Value, type_name: &str) -> serde_json::Value {
    if let serde_json::Value::Object(map) = &mut value {
        let mut stamped = serde_json::Map::with_capacity(map.len() + 1);
        stamped.insert(
            "@type".to_string(),
            serde_json::Value::String(type_name.to_string()),
        );
        for (key, item) in std::mem::take(map) {
            stamped.insert(key, item);
        }
        *map = stamped;
    }
    value
}

/// 批量补 `@type`（FastJson2 集合元素同样带类名）。
pub fn stamp_types(values: Vec<serde_json::Value>, type_name: &str) -> Vec<serde_json::Value> {
    values
        .into_iter()
        .map(|value| stamp_type(value, type_name))
        .collect()
}

/// 从缓存对象中剥离 FastJson2 的 `@type`：Java 反序列化后返回的 HTTP 实体
/// 不含该字段，Rust 直接把缓存 JSON 返回给前端时需要先去掉。
pub fn strip_type(value: &mut serde_json::Value) {
    match value {
        serde_json::Value::Object(map) => {
            map.remove("@type");
            for item in map.values_mut() {
                strip_type(item);
            }
        }
        serde_json::Value::Array(items) => {
            for item in items {
                strip_type(item);
            }
        }
        _ => {}
    }
}

/// FastJson2 的 `WriteClassName` 会给 Long 输出 `123L`（非法 JSON）。
/// Redis 与 Java 共存时需要先剥掉整数字面量后缀再交给 serde。
fn sanitize_fastjson2(text: &str) -> std::borrow::Cow<'_, str> {
    let bytes = text.as_bytes();
    let mut needs = false;
    for (index, byte) in bytes.iter().enumerate() {
        if matches!(byte, b'L' | b'l') {
            let prev_digit = index > 0 && bytes[index - 1].is_ascii_digit();
            let next = bytes.get(index + 1).copied();
            if prev_digit && matches!(next, Some(b',') | Some(b'}') | Some(b']')) {
                needs = true;
                break;
            }
        }
        // FastJson2 WriteClassName 的容器字面量：Set[...] / List[...] / JSONArray[...]。
        if *byte == b'[' {
            for prefix in [
                b"Set[".as_slice(),
                b"List[".as_slice(),
                b"JSONArray[".as_slice(),
            ] {
                let start = index + 1;
                if start >= prefix.len() && &bytes[start - prefix.len()..start] == prefix {
                    needs = true;
                    break;
                }
            }
        }
    }
    if !needs {
        return std::borrow::Cow::Borrowed(text);
    }
    let mut out = String::with_capacity(text.len());
    let mut previous_digit = false;
    let mut in_string = false;
    let mut escaped = false;
    let mut index = 0;
    while index < text.len() {
        let ch = text[index..].chars().next().unwrap();
        if in_string {
            out.push(ch);
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_string = false;
            }
            previous_digit = false;
            index += ch.len_utf8();
            continue;
        }
        if ch == '"' {
            in_string = true;
            out.push(ch);
            previous_digit = false;
            index += 1;
            continue;
        }
        let mut typed_prefix = 0;
        for prefix in ["Set[", "List[", "JSONArray["] {
            if text[index..].starts_with(prefix) {
                typed_prefix = prefix.len();
                break;
            }
        }
        if typed_prefix > 0 {
            out.push('[');
            previous_digit = false;
            index += typed_prefix;
            continue;
        }
        if matches!(ch, 'L' | 'l') && previous_digit {
            let next = text[index + 1..].chars().next();
            if matches!(next, Some(',') | Some('}') | Some(']')) {
                previous_digit = false;
                index += 1;
                continue;
            }
        }
        previous_digit = ch.is_ascii_digit();
        out.push(ch);
        index += ch.len_utf8();
    }
    std::borrow::Cow::Owned(out)
}
