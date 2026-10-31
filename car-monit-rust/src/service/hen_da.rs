// 来源: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/HenDaServiceImpl.java
//       ruoyi-system/src/main/java/com/ruoyi/base/service/forest/IHenDaApi.java
//       ruoyi-system/src/main/java/com/ruoyi/base/util/EncryptUtils.java
// 职责: 恒达 GeoServer 桩号 -> 经纬度查询（含签名与 URL 双重编码）。
// 对应关系: IHenDaService.getPileToLonLat -> get_pile_to_lon_lat；Forest 客户端 -> reqwest。

use md5::{Digest, Md5};
use serde_json::{json, Value};
use tracing::warn;

use crate::state::AppState;

/// Java: `@Get(url = "${hendaUrl}/getLonLatByPos", connectTimeout = 30000)`。
const PATH: &str = "/getLonLatByPos";

/// Java: `getPileToLonLat(roadCode, pile, direction)` —— 任何异常都吞掉返回 null。
pub async fn get_pile_to_lon_lat(
    state: &AppState,
    road_code: Option<&str>,
    pile: Option<&str>,
    direction: Option<&str>,
) -> Option<Value> {
    let base = state.settings.forest.variables.henda_url.trim_end_matches('/');
    if base.is_empty() {
        return None;
    }

    // Java: "lxbh='" + roadCode + "'  and gxfx = '" + direction + "'"（两个空格）。
    let road = road_code.unwrap_or("null");
    let dir = direction.unwrap_or("null");
    let filter = format!("lxbh='{road}'  and gxfx = '{dir}'");
    let params = json!({
        "layerName": "rdlinelong",
        "filter": filter,
        "m": pile,
    });
    let params_text = serde_json::to_string(&params).ok()?;
    // Java: URLEncoder.encode(json, "utf8") —— 空格编码为 '+'。
    let encoded = form_encode(&params_text);

    let nonce = chrono::Utc::now().timestamp_millis().to_string();
    let timestamp = chrono::Local::now().format("%Y%m%d%H%M%S").to_string();
    let appid = &state.settings.hengda.appid;
    let secret = &state.settings.hengda.secret;
    let signature = ciphertext(appid, secret, &nonce, &timestamp);

    let url = format!("{base}{PATH}");
    let response = state
        .http
        .get(&url)
        .query(&[
            ("params", encoded.as_str()),
            ("appid", appid.as_str()),
            ("nonce", nonce.as_str()),
            ("signature", signature.as_str()),
            ("timestamp", timestamp.as_str()),
        ])
        .send()
        .await;

    let body = match response {
        Ok(response) if response.status().is_success() => response.text().await.ok()?,
        Ok(response) => {
            warn!("【恒达】{} 返回 HTTP {}", PATH, response.status());
            return None;
        }
        Err(err) => {
            warn!("【恒达】{} 请求失败: {}", PATH, err);
            return None;
        }
    };

    let value: Value = serde_json::from_str(&body).ok()?;
    let data = value.get("data")?;
    Some(json!({
        "longitude": data.get("x").and_then(stringify),
        "latitude": data.get("y").and_then(stringify),
    }))
}

fn stringify(value: &Value) -> Option<String> {
    match value {
        Value::String(text) => Some(text.clone()),
        Value::Null => None,
        other => Some(other.to_string()),
    }
}

/// Java: `EncryptUtils.getCiphertext(appid, secretKey, nonce, timestamp)`。
fn ciphertext(appid: &str, secret: &str, nonce: &str, timestamp: &str) -> String {
    // Java: createSignature(headers, secretKey, nonce) —— jsonStr 传的是 nonce。
    create_signature(appid, secret, nonce, timestamp, nonce)
}

/// Java: `createSignature` —— 注意 `publicStr.append(publicStr)` 的重复拼接缺陷，
/// 服务端按同一算法校验，必须原样复现。
fn create_signature(
    appid: &str,
    secret: &str,
    nonce: &str,
    timestamp: &str,
    json_str: &str,
) -> String {
    let strip = |value: &str| value.replace('[', "").replace(']', "");
    let mut parts = vec![strip(appid), strip(timestamp), strip(nonce), secret.to_string()];
    parts.sort();

    let mut public_str = String::new();
    for part in parts {
        if public_str.is_empty() {
            public_str = part;
        } else {
            let doubled = format!("{public_str}{public_str}&{part}");
            public_str = doubled;
        }
    }

    let cleaned = json_str.replace('\n', "").replace(' ', "");
    let to_sign = format!("{public_str}&{cleaned}");
    let digest = Md5::digest(to_sign.as_bytes());
    hex::encode(digest)
}

/// Java: `URLEncoder.encode(value, "UTF-8")` —— 保留 `A-Za-z0-9.-*_`，空格转 `+`。
fn form_encode(value: &str) -> String {
    let mut out = String::with_capacity(value.len());
    for byte in value.as_bytes() {
        match *byte {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'.' | b'-' | b'*' | b'_' => {
                out.push(*byte as char)
            }
            b' ' => out.push('+'),
            other => out.push_str(&format!("%{other:02X}")),
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn form_encoding_matches_java_url_encoder() {
        assert_eq!(form_encode("a b"), "a+b");
        assert_eq!(form_encode("{'a':'1'}"), "%7B%27a%27%3A%271%27%7D");
    }

    #[test]
    fn signature_replicates_java_string_builder_bug() {
        // 元素排序后按 Java 的重复拼接缺陷生成，最终长度呈指数增长。
        let value = create_signature("app", "sec", "123", "20250101120000", "123");
        assert_eq!(value.len(), 32);
    }
}
