// 来源: ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssTemplate.java
//       （AWS SDK for Java v1 的 AmazonS3Client 调用，SigV4、path-style）
// 职责: S3/MinIO 的最小客户端 —— 桶与对象的增删查、以及**离线**的预签名 URL。
// 对应关系: listBuckets/doesBucketExistV2/createBucket/removeBucket/
//           putObject/getObject/deleteObject/listObjects(V2)/generatePresignedUrl。
//
// 出参形态是**实测**出来的（本机 MinIO 不可达，用 tools/endpoint_parity/fake_s3_full.py 顶上游）：
//   Bucket            -> {"name","owner":{"displayName","id"},"creationDate"}
//   S3ObjectSummary   -> {"bucketName","key","size","lastModified","storageClass","owner","etag"}
//   Date 的 Jackson 写法 -> ISO8601 带毫秒与本机偏移（2021-05-06T08:36:40.000+08:00）
//   预签名 URL 的参数顺序  -> Algorithm, Date, SignedHeaders, Expires, Credential, Signature

use chrono::{DateTime, Local, SecondsFormat, TimeZone, Utc};
use hmac::{Hmac, Mac};
use serde_json::Value;
use sha2::{Digest, Sha256};

use crate::error::AppError;
use crate::state::AppState;

const ALGORITHM: &str = "AWS4-HMAC-SHA256";
const EMPTY_PAYLOAD_SHA: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
/// Java: AWS SDK 的 presign 上限（7 天）。
const MAX_PRESIGN_SECONDS: i64 = 604800;
/// Java: generatePresignedUrl 里 ServiceUtils.formatS3PresignDate 的格式。
const PRESIGN_DATE_FORMAT: &str = "%Y%m%dT%H%M%SZ";

pub struct OssClient {
    endpoint: String,
    access_key: String,
    secret_key: String,
    region: String,
}

impl OssClient {
    pub fn new(state: &AppState) -> Self {
        let oss = &state.settings.oss;
        Self {
            // Java: OssProperties.endpoint（yml 里带 scheme，SDK 会自己补 host 头）。
            endpoint: oss.endpoint.trim_end_matches('/').to_string(),
            access_key: oss.access_key.clone(),
            secret_key: oss.secret_key.clone(),
            region: oss.region.clone(),
        }
    }

    fn host(&self) -> String {
        self.endpoint
            .split("://")
            .nth(1)
            .unwrap_or(&self.endpoint)
            .to_string()
    }

    /// Java: AmazonS3Client 的 SigV4 头部签名（SignedHeaders=host;x-amz-content-sha256;x-amz-date）。
    async fn request(
        &self,
        method: &str,
        path: &str,
        query: &[(&str, String)],
        body: Option<Vec<u8>>,
        content_type: Option<&str>,
    ) -> Result<(u16, Vec<u8>), AppError> {
        let payload = body.clone().unwrap_or_default();
        let payload_hash = if payload.is_empty() {
            EMPTY_PAYLOAD_SHA.to_string()
        } else {
            hex_sha256(&payload)
        };
        let amz_date = Utc::now().format("%Y%m%dT%H%M%SZ").to_string();
        let date_stamp = amz_date[..8].to_string();
        let canonical_query = canonical_query(query);
        // Java: path-style，且 key 里的 '/' 保留为层级（SDK 只按段编码）。
        let canonical_uri = encode_path(path);
        let mut extra_headers: Vec<(String, String)> = Vec::new();
        if let Some(value) = content_type {
            extra_headers.push(("content-type".to_string(), value.to_string()));
        }
        let mut signed_names = vec!["host", "x-amz-content-sha256", "x-amz-date"];
        for (name, _) in &extra_headers {
            signed_names.push(name.as_str());
        }
        signed_names.sort();
        let mut canonical_headers = format!(
            "host:{}\nx-amz-content-sha256:{}\nx-amz-date:{}\n",
            self.host(),
            payload_hash,
            amz_date
        );
        for (name, value) in &extra_headers {
            canonical_headers.push_str(&format!("{}:{}\n", name, value.trim()));
        }
        let canonical_request = format!(
            "{}\n{}\n{}\n{}\n{}\n{}",
            method,
            canonical_uri,
            canonical_query,
            canonical_headers,
            signed_names.join(";"),
            payload_hash
        );
        let scope = format!("{}/{}/s3/aws4_request", date_stamp, self.region);
        let string_to_sign = format!(
            "{}\n{}\n{}\n{}",
            ALGORITHM,
            amz_date,
            scope,
            hex_sha256(canonical_request.as_bytes())
        );
        let signature = hex::encode(sign(
            &self.secret_key,
            &date_stamp,
            &self.region,
            &string_to_sign,
        ));
        let authorization = format!(
            "{} Credential={}/{}, SignedHeaders={}, Signature={}",
            ALGORITHM,
            self.access_key,
            scope,
            signed_names.join(";"),
            signature
        );

        let client = reqwest::Client::new();
        let url = self.url(path, &canonical_query);
        let request = match method {
            "GET" => client.get(&url),
            "PUT" => client.put(&url),
            "DELETE" => client.delete(&url),
            other => {
                return Err(AppError::Service(format!("不支持的方法: {other}")));
            }
        };
        let mut builder = request
            .header("x-amz-date", &amz_date)
            .header("x-amz-content-sha256", &payload_hash)
            .header("authorization", &authorization);
        if let Some(value) = content_type {
            builder = builder.header("content-type", value);
        }
        if !payload.is_empty() {
            builder = builder.body(payload.clone());
        }
        let response = builder
            .send()
            .await
            .map_err(|err| AppError::Service(sdk_message(&err.to_string())))?;
        let status = response.status().as_u16();
        let bytes = response
            .bytes()
            .await
            .map_err(|err| AppError::Service(err.to_string()))?;
        Ok((status, bytes.to_vec()))
    }

    fn url(&self, path: &str, canonical_query: &str) -> String {
        if canonical_query.is_empty() {
            format!("{}{}", self.endpoint, path)
        } else {
            format!("{}{}?{}", self.endpoint, path, canonical_query)
        }
    }

    /// Java: `amazonS3.listBuckets()` —— GET / 的 ListAllMyBucketsResult。
    pub async fn list_buckets(&self) -> Result<Vec<serde_json::Value>, AppError> {
        let (status, body) = self.request("GET", "/", &[], None, None).await?;
        expect_ok(status, &body)?;
        let text = String::from_utf8_lossy(&body).to_string();
        Ok(xml_buckets(&text))
    }

    /// Java: `doesBucketExistV2` —— 实测发出的是 `GET /{bucket}/?acl`。
    pub async fn bucket_exists(&self, bucket: &str) -> Result<bool, AppError> {
        let path = format!("/{bucket}/");
        let (status, body) = self
            .request("GET", &path, &[("acl", String::new())], None, None)
            .await?;
        Ok(status == 200 && !body.is_empty())
    }

    pub async fn create_bucket(&self, bucket: &str) -> Result<(), AppError> {
        let (status, body) = self
            .request("PUT", &format!("/{bucket}/"), &[], Some(Vec::new()), None)
            .await?;
        expect_ok(status, &body)
    }

    pub async fn delete_bucket(&self, bucket: &str) -> Result<(), AppError> {
        let (status, body) = self
            .request("DELETE", &format!("/{bucket}/"), &[], None, None)
            .await?;
        // Java: removeBucket 接受 204（空体）。
        if status == 204 {
            return Ok(());
        }
        expect_ok(status, &body)
    }

    /// Java: `getAllObjectsByPrefix(bucket, prefix, ...)` —— `GET /{bucket}/?prefix=&encoding-type=url`。
    pub async fn list_objects(
        &self,
        bucket: &str,
        prefix: &str,
    ) -> Result<Vec<serde_json::Value>, AppError> {
        let path = format!("/{bucket}/");
        let query = [
            ("prefix", prefix.to_string()),
            ("encoding-type", "url".to_string()),
        ];
        let (status, body) = self.request("GET", &path, &query, None, None).await?;
        expect_ok(status, &body)?;
        let text = String::from_utf8_lossy(&body).to_string();
        Ok(xml_objects(&text))
    }

    /// Java: `putObject(bucket, name, stream, size, contentType)`。
    pub async fn put_object(
        &self,
        bucket: &str,
        key: &str,
        body: Vec<u8>,
        content_type: &str,
    ) -> Result<(), AppError> {
        let path = format!("/{bucket}/{key}");
        let (status, response) = self
            .request("PUT", &path, &[], Some(body), Some(content_type))
            .await?;
        expect_ok(status, &response)
    }

    /// Java: `deleteObject(bucket, name)`。
    pub async fn delete_object(&self, bucket: &str, key: &str) -> Result<(), AppError> {
        let path = format!("/{bucket}/{key}");
        let (status, body) = self.request("DELETE", &path, &[], None, None).await?;
        if status == 204 {
            return Ok(());
        }
        expect_ok(status, &body)
    }

    /// Java: `OssTemplate.getObjectURL(bucket, name, expires)` —— 先 `calendar.add(DAY_OF_MONTH, expires)`，
    /// 再 `generatePresignedUrl`；超过 7 天时 SDK 在**发请求之前**就抛异常。
    pub fn presigned_url(
        &self,
        bucket: &str,
        key: &str,
        expires_days: i32,
    ) -> Result<String, AppError> {
        // Java: `new Date()` -> calendar 加天数 -> 与签名时刻的差值（秒）作为 X-Amz-Expires。
        let start = Utc::now();
        let expiration = start + chrono::Duration::days(i64::from(expires_days));
        let amz_date = start.format("%Y%m%dT%H%M%SZ").to_string();
        let date_stamp = amz_date[..8].to_string();
        // SDK 用发起时刻与到期时刻的毫秒差取整秒，签名前的这点延迟会让 1 天偶尔算成 86399。
        let seconds = (expiration - Utc::now()).num_seconds();
        if seconds > MAX_PRESIGN_SECONDS {
            let text = expiration.format(PRESIGN_DATE_FORMAT).to_string();
            return Err(AppError::Service(format!(
                "Requests that are pre-signed by SigV4 algorithm are valid for at most 7 days. \
                 The expiration date set on the current request [{text}] has exceeded this limit."
            )));
        }
        let credential = format!(
            "{}/{}/{}/s3/aws4_request",
            self.access_key, date_stamp, self.region
        );
        let mut params: Vec<(String, String)> = vec![
            ("X-Amz-Algorithm".to_string(), ALGORITHM.to_string()),
            ("X-Amz-Credential".to_string(), credential.clone()),
            ("X-Amz-Date".to_string(), amz_date.clone()),
            ("X-Amz-Expires".to_string(), seconds.to_string()),
            ("X-Amz-SignedHeaders".to_string(), "host".to_string()),
        ];
        params.sort_by(|left, right| left.0.cmp(&right.0));
        let canonical_query = params
            .iter()
            .map(|(key, value)| format!("{}={}", uri_encode(key, true), uri_encode(value, true)))
            .collect::<Vec<_>>()
            .join("&");
        let canonical_uri = encode_path(&format!("/{bucket}/{key}"));
        let canonical_request = format!(
            "GET\n{}\n{}\nhost:{}\n\nhost\nUNSIGNED-PAYLOAD",
            canonical_uri,
            canonical_query,
            self.host()
        );
        let scope = format!("{}/{}/s3/aws4_request", date_stamp, self.region);
        let string_to_sign = format!(
            "{}\n{}\n{}\n{}",
            ALGORITHM,
            amz_date,
            scope,
            hex_sha256(canonical_request.as_bytes())
        );
        let signature = hex::encode(sign(
            &self.secret_key,
            &date_stamp,
            &self.region,
            &string_to_sign,
        ));
        // Java: 实测 URL 里的参数顺序就是下面这串（SDK 的追加顺序，非字典序）。
        Ok(format!(
            "{}{}?X-Amz-Algorithm={}&X-Amz-Date={}&X-Amz-SignedHeaders=host&X-Amz-Expires={}&X-Amz-Credential={}&X-Amz-Signature={}",
            self.endpoint,
            canonical_uri,
            ALGORITHM,
            amz_date,
            seconds,
            uri_encode(&credential, true),
            signature
        ))
    }
}

/// Java: Jackson 对 `java.util.Date` 的写法（Spring Boot 关掉时间戳、用 JVM 默认时区）。
pub fn java_date(value: DateTime<Utc>) -> String {
    value
        .with_timezone(&Local)
        .to_rfc3339_opts(SecondsFormat::Millis, false)
}

fn hex_sha256(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hex::encode(hasher.finalize())
}

fn sign(secret: &str, date_stamp: &str, region: &str, string_to_sign: &str) -> Vec<u8> {
    let mac = |key: &[u8], data: &str| -> Vec<u8> {
        let mut mac = Hmac::<Sha256>::new_from_slice(key).expect("hmac key");
        mac.update(data.as_bytes());
        mac.finalize().into_bytes().to_vec()
    };
    let mut key = mac(&format!("AWS4{secret}").into_bytes(), date_stamp);
    key = mac(&key, region);
    key = mac(&key, "s3");
    key = mac(&key, "aws4_request");
    let mut mac = Hmac::<Sha256>::new_from_slice(&key).expect("hmac key");
    mac.update(string_to_sign.as_bytes());
    mac.finalize().into_bytes().to_vec()
}

fn canonical_query(query: &[(&str, String)]) -> String {
    let mut pairs: Vec<(String, String)> = query
        .iter()
        .map(|(key, value)| (uri_encode(key, true), uri_encode(value, true)))
        .collect();
    pairs.sort();
    pairs
        .iter()
        .map(|(key, value)| format!("{key}={value}"))
        .collect::<Vec<_>>()
        .join("&")
}

/// Java: S3 的路径按段编码，`/` 保留。
fn encode_path(path: &str) -> String {
    path.split('/')
        .map(|segment| uri_encode(segment, false))
        .collect::<Vec<_>>()
        .join("/")
}

pub fn uri_encode(value: &str, encode_slash: bool) -> String {
    let mut out = String::new();
    for byte in value.as_bytes() {
        let ch = *byte as char;
        let unreserved = ch.is_ascii_alphanumeric()
            || matches!(ch, '-' | '_' | '.' | '~')
            || (ch == '/' && !encode_slash);
        if unreserved {
            out.push(ch);
        } else {
            out.push_str(&format!("%{byte:02X}", byte = *byte));
        }
    }
    out
}

fn expect_ok(status: u16, body: &[u8]) -> Result<(), AppError> {
    if (200..300).contains(&status) {
        return Ok(());
    }
    // Java: AmazonServiceException.getMessage() 形如 status + 上游文本，这里给同类的 500 信封。
    let text = String::from_utf8_lossy(body).to_string();
    let code = xml_tag(&text, "Code").unwrap_or_default();
    Err(AppError::Service(format!(
        "Status Code: {status}; Error Code: {code}"
    )))
}

/// 上游异常文本可能带栈，Java 出的是 message 首行。
fn sdk_message(text: &str) -> String {
    text.lines().next().unwrap_or(text).to_string()
}

fn xml_tag(content: &str, tag: &str) -> Option<String> {
    let open = format!("<{tag}>");
    let close = format!("</{tag}>");
    let start = content.find(&open)? + open.len();
    let end = content[start..].find(&close)? + start;
    Some(content[start..end].to_string())
}

fn xml_sections(content: &str, tag: &str) -> Vec<String> {
    let open = format!("<{tag}>");
    let close = format!("</{tag}>");
    let mut out = Vec::new();
    let mut cursor = 0usize;
    while let Some(found) = content[cursor..].find(&open) {
        let start = cursor + found + open.len();
        let Some(relative) = content[start..].find(&close) else {
            break;
        };
        out.push(content[start..start + relative].to_string());
        cursor = start + relative + close.len();
    }
    out
}

fn xml_owner(content: &str) -> serde_json::Value {
    let Some(section) = xml_sections(content, "Owner").pop() else {
        return serde_json::Value::Null;
    };
    serde_json::json!({
        // Java: Owner 的 Jackson 键序实测是 displayName 在前。
        "displayName": xml_tag(&section, "DisplayName").unwrap_or_default(),
        "id": xml_tag(&section, "ID").unwrap_or_default(),
    })
}

/// Java: ListAllMyBucketsResult -> Bucket{name, owner, creationDate}。
/// 注意 `<Owner>` 在根元素上（不在每个 `<Bucket>` 里），SDK 把它填进每个 Bucket。
pub fn xml_buckets(content: &str) -> Vec<serde_json::Value> {
    let root_owner = xml_sections(content, "Owner")
        .first()
        .map(|section| {
            serde_json::json!({
                "displayName": xml_tag(section, "DisplayName").unwrap_or_default(),
                "id": xml_tag(section, "ID").unwrap_or_default(),
            })
        })
        .unwrap_or(Value::Null);
    xml_sections(content, "Bucket")
        .into_iter()
        .map(|section| {
            let created = xml_utc_time(&xml_tag(&section, "CreationDate").unwrap_or_default());
            serde_json::json!({
                "name": xml_tag(&section, "Name").unwrap_or_default(),
                "owner": root_owner.clone(),
                "creationDate": created.map(java_date),
            })
        })
        .collect()
}

/// Java: ListBucketResult -> S3ObjectSummary{bucketName,key,size,lastModified,storageClass,owner,etag}。
pub fn xml_objects(content: &str) -> Vec<serde_json::Value> {
    xml_sections(content, "Contents")
        .into_iter()
        .map(|section| {
            let modified = xml_utc_time(&xml_tag(&section, "LastModified").unwrap_or_default());
            let etag = xml_tag(&section, "ETag")
                .unwrap_or_default()
                .trim_matches('"')
                .to_string();
            serde_json::json!({
                "bucketName": xml_tag(content, "Name").unwrap_or_default(),
                "key": xml_tag(&section, "Key").unwrap_or_default(),
                "size": xml_tag(&section, "Size").unwrap_or_default().parse::<i64>().unwrap_or(0),
                "lastModified": modified.map(java_date),
                "storageClass": xml_tag(&section, "StorageClass").unwrap_or_default(),
                "owner": xml_owner(&section),
                "etag": etag,
            })
        })
        .collect()
}

fn xml_utc_time(text: &str) -> Option<DateTime<Utc>> {
    DateTime::parse_from_rfc3339(text)
        .ok()
        .map(|value| value.with_timezone(&Utc))
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    const BUCKETS_XML: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner><ID>abc123</ID><DisplayName>parity</DisplayName></Owner><Buckets><Bucket><Name>developer</Name><CreationDate>2021-05-06T00:36:40.000Z</CreationDate></Bucket><Bucket><Name>parity-bucket</Name><CreationDate>2021-05-06T00:36:40.000Z</CreationDate></Bucket></Buckets></ListAllMyBucketsResult>"#;

    const LIST_XML: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>developer</Name><Prefix>a</Prefix><KeyCount>2</KeyCount><Contents><Key>a/b.txt</Key><LastModified>2024-03-01T08:00:00.000Z</LastModified><ETag>"5c1a8f0deadbeef"</ETag><Size>12</Size><StorageClass>STANDARD</StorageClass><Owner><ID>abc123</ID><DisplayName>parity</DisplayName></Owner></Contents></ListBucketResult>"#;

    /// Java 实测：Bucket 的键序是 name、owner、creationDate，且 Owner 来自根元素。
    #[test]
    fn bucket_rows_take_owner_from_root() {
        let rows = xml_buckets(BUCKETS_XML);
        assert_eq!(rows.len(), 2);
        let keys: Vec<&str> = rows[0]
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect();
        assert_eq!(keys, vec!["name", "owner", "creationDate"]);
        assert_eq!(rows[0]["name"], json!("developer"));
        assert_eq!(rows[0]["owner"]["displayName"], json!("parity"));
        assert_eq!(rows[0]["owner"]["id"], json!("abc123"));
        // Java 用 JVM 默认时区输出：格式固定为「毫秒 + 偏移」，但偏移随进程时区变化。
        // 这里断言同一个 UTC 瞬间与格式，不把 +08:00 这种运行环境细节写死。
        let text = rows[0]["creationDate"].as_str().unwrap().to_string();
        let instant = DateTime::parse_from_rfc3339(&text)
            .unwrap_or_else(|e| panic!("{text} 不是带偏移的 RFC3339: {e}"));
        assert_eq!(
            instant.with_timezone(&Utc),
            Utc.with_ymd_and_hms(2021, 5, 6, 0, 36, 40).unwrap()
        );
        assert!(text.contains(".000"), "{text}");
        // yyyy-mm-ddThh:mm:ss.mmm+hh:mm
        assert!(text.len() >= 25, "{text}");
    }

    /// Java 实测：S3ObjectSummary 的键序与 ETag 去引号。
    #[test]
    fn object_rows_match_measured_jackson_shape() {
        let rows = xml_objects(LIST_XML);
        assert_eq!(rows.len(), 1);
        let keys: Vec<&str> = rows[0]
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect();
        assert_eq!(
            keys,
            vec![
                "bucketName",
                "key",
                "size",
                "lastModified",
                "storageClass",
                "owner",
                "etag"
            ]
        );
        assert_eq!(rows[0]["etag"], json!("5c1a8f0deadbeef"));
        assert_eq!(rows[0]["size"], json!(12));
        assert_eq!(rows[0]["bucketName"], json!("developer"));
    }

    #[test]
    fn path_style_uri_keeps_slash_and_encodes_key_segments() {
        assert_eq!(encode_path("/developer/a/b.txt"), "/developer/a/b.txt");
        assert_eq!(encode_path("/developer/a b.txt"), "/developer/a%20b.txt");
        assert_eq!(uri_encode("a/b", true), "a%2Fb");
        assert_eq!(uri_encode("a/b", false), "a/b");
    }

    #[test]
    fn canonical_query_is_sorted_by_encoded_key() {
        let prefix = "a b".to_string();
        let query = vec![("encoding-type", "url".to_string()), ("prefix", prefix)];
        let text = canonical_query(&query);
        assert_eq!(text, "encoding-type=url&prefix=a%20b");
    }

    /// Java: SDK 的 7 天上限判定在发请求之前，文案里是 UTC 的到期时刻。
    #[test]
    fn presign_rejects_more_than_seven_days() {
        let client = OssClient {
            endpoint: "http://127.0.0.1:9124".to_string(),
            access_key: "ak".to_string(),
            secret_key: "sk".to_string(),
            region: "us-east-1".to_string(),
        };
        let error = client
            .presigned_url("developer", "b.txt", 60)
            .err()
            .expect("60 天必须报错");
        let text = error.to_string();
        assert!(
            text.contains("valid for at most 7 days"),
            "文案照抄 SDK: {text}"
        );
        // 1 天与 7 天要能通过，并且 URL 是 path-style。
        for days in [0, 1, 7] {
            let url = client.presigned_url("developer", "b.txt", days).unwrap();
            assert!(
                url.starts_with("http://127.0.0.1:9124/developer/b.txt?X-Amz-Algorithm="),
                "{url}"
            );
            assert!(url.contains("X-Amz-Credential=ak%2F"), "{url}");
            assert!(url.contains("&X-Amz-Signature="), "{url}");
        }
    }
}
