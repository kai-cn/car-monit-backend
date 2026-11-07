// 来源: ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssEndpoint.java
// 职责: `/oss/**` 的桶与对象端点（MinIO/S3 直连）。基线清单原本漏了这个控制器。
// 对应关系: 出参形态、错误信封与 HTTP 状态都按 Java 实测（tools/endpoint_parity/fake_s3_full.py 顶上游）：
//   GET  /oss/bucket                     -> Bucket[]
//   GET  /oss/bucket/{n}                 -> Bucket；找不到 -> msg="Bucket Name not found!"
//   POST /oss/bucket/{n}                 -> 先建再取，返回 Bucket
//   DELETE /oss/bucket/{n}               -> HTTP 202 空体（@ResponseStatus(ACCEPTED)）
//   POST /oss/object/{n}[/{name}]        -> 上传后 Jackson 序列化 S3Object 失败 -> {"msg":null,"code":500}
//   GET  /oss/object/{n}/{prefix}        -> S3ObjectSummary[]
//   GET  /oss/object/{n}/{name}/{expires}-> {"bucket","expires","url","object"}
//   DELETE /oss/object/{n}/{name}/       -> Java 的尾斜杠路径落回 GET 路由，等价于「方法不支持」

use axum::extract::{Multipart, Path, State};
use axum::http::StatusCode;
use axum::response::Response;
use axum::Json;
use axum::Router;
use serde_json::{json, Value};

use crate::api::meta;
use crate::api::support;
use crate::error::AppError;
use crate::service::oss_client::OssClient;
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/oss/bucket",
            meta::get_route("/oss/bucket", None, None, list_buckets),
        )
        .route(
            "/oss/bucket/{bucketName}",
            meta::get_route("/oss/bucket/{bucketName}", None, None, get_bucket)
                .merge(meta::post_route(
                    "/oss/bucket/{bucketName}",
                    None,
                    None,
                    create_bucket,
                ))
                .merge(meta::delete_route(
                    "/oss/bucket/{bucketName}",
                    None,
                    None,
                    delete_bucket,
                )),
        )
        .route(
            "/oss/object/{bucketName}",
            meta::post_route("/oss/object/{bucketName}", None, None, upload_named_by_path),
        )
        .route(
            "/oss/object/{bucketName}/{objectName}",
            meta::get_route(
                "/oss/object/{bucketName}/{objectName}",
                None,
                None,
                filter_object,
            )
            .merge(meta::post_route(
                "/oss/object/{bucketName}/{objectName}",
                None,
                None,
                upload_with_object_name,
            ))
            // Java: `@DeleteMapping("/object/{bucketName}/{objectName}/")` —— 模式带尾斜杠，
            // 只有 `/oss/object/b/o/` 才命中（不带斜杠的那次实测回「方法不支持」）。
            // Rust 的尾斜杠归一把两种写法收敛到同一条路由，这里按**语义**注册（删除 → 202）。
            .merge(meta::delete_route(
                "/oss/object/{bucketName}/{objectName}",
                None,
                None,
                delete_object,
            )),
        )
        .route(
            "/oss/object/{bucketName}/{objectName}/{expires}",
            meta::get_route(
                "/oss/object/{bucketName}/{objectName}/{expires}",
                None,
                None,
                presigned_url,
            ),
        )
}

fn client(state: &AppState) -> OssClient {
    OssClient::new(state)
}

/// Java: getAllBuckets()。
async fn list_buckets(State(state): State<AppState>) -> Result<Json<Vec<Value>>, AppError> {
    Ok(Json(client(&state).list_buckets().await?))
}

/// Java: getBucket(name).orElseThrow(() -> new IllegalArgumentException("Bucket Name not found!"))。
async fn get_bucket(
    State(state): State<AppState>,
    Path(bucket_name): Path<String>,
) -> Result<Json<Value>, AppError> {
    let buckets = client(&state).list_buckets().await?;
    find_bucket(&buckets, &bucket_name)
}

fn find_bucket(buckets: &[Value], name: &str) -> Result<Json<Value>, AppError> {
    buckets
        .iter()
        .find(|item| item.get("name").and_then(Value::as_str) == Some(name))
        .cloned()
        .map(Json)
        // Java: IllegalArgumentException 的 message 直接成为 msg。
        .ok_or_else(|| AppError::Service("Bucket Name not found!".to_string()))
}

/// Java: createBucket（已存在则跳过）+ getBucket(name).get()。
async fn create_bucket(
    State(state): State<AppState>,
    Path(bucket_name): Path<String>,
) -> Result<Json<Value>, AppError> {
    let oss = client(&state);
    // Java: `if (!doesBucketExistV2(name)) createBucket(name)`。
    if !oss.bucket_exists(&bucket_name).await? {
        oss.create_bucket(&bucket_name).await?;
    }
    let buckets = oss.list_buckets().await?;
    // Java: Optional.get() 在空值上抛 NoSuchElementException("No value present")。
    let found = buckets
        .iter()
        .any(|item| item.get("name").and_then(Value::as_str) == Some(bucket_name.as_str()));
    if !found {
        return Err(AppError::Service("No value present".to_string()));
    }
    find_bucket(&buckets, &bucket_name)
}

/// Java: removeBucket + `@ResponseStatus(HttpStatus.ACCEPTED)` —— 202 空体。
async fn delete_bucket(
    State(state): State<AppState>,
    Path(bucket_name): Path<String>,
) -> Result<Response, AppError> {
    client(&state).delete_bucket(&bucket_name).await?;
    // Java: 返回 void + `@ResponseStatus(ACCEPTED)` —— 202、空体、没有 Content-Type。
    Response::builder()
        .status(StatusCode::ACCEPTED)
        .body(axum::body::Body::empty())
        .map_err(|err| AppError::Service(err.to_string()))
}

/// Java: createObject(object, bucketName) —— 对象名取上传文件的原始文件名。
async fn upload_named_by_path(
    State(state): State<AppState>,
    Path(bucket_name): Path<String>,
    multipart: Multipart,
) -> Result<Response, AppError> {
    upload(state, bucket_name, None, multipart).await
}

/// Java: createObject(object, bucketName, objectName)。
async fn upload_with_object_name(
    State(state): State<AppState>,
    Path((bucket_name, object_name)): Path<(String, String)>,
    multipart: Multipart,
) -> Result<Response, AppError> {
    upload(state, bucket_name, Some(object_name), multipart).await
}

/// Java: putObject(...) 之后 getObjectInfo(...) 返回 S3Object；
/// 实测 Jackson 序列化这个对象必然失败（`{"msg":null,"code":500}`，与对象是否存在无关）。
async fn upload(
    state: AppState,
    bucket_name: String,
    object_name: Option<String>,
    mut multipart: Multipart,
) -> Result<Response, AppError> {
    let mut stored: Option<(String, Vec<u8>, String)> = None;
    while let Some(field) = multipart.next_field().await.ok().flatten() {
        let upload = support::read_multipart_field(field).await?;
        let content_type = upload
            .content_type
            .unwrap_or_else(|| "application/octet-stream".to_string());
        stored = Some((upload.file_name, upload.bytes, content_type));
    }
    let (fallback_name, body, content_type) = stored.unwrap_or_default();
    let object_name = object_name.unwrap_or(fallback_name);
    if object_name.is_empty() {
        // Java: object.getOriginalFilename() 为 null 时 putObject 直接抛 NPE（msg=null）。
        return Err(AppError::Internal(None));
    }
    client(&state)
        .put_object(&bucket_name, &object_name, body, &content_type)
        .await?;
    Err(AppError::Internal(None))
}

/// Java: filterObject —— objectName 当 prefix 用。
async fn filter_object(
    State(state): State<AppState>,
    Path((bucket_name, object_name)): Path<(String, String)>,
) -> Result<Json<Vec<Value>>, AppError> {
    Ok(Json(
        client(&state)
            .list_objects(&bucket_name, &object_name)
            .await?,
    ))
}

/// Java: deleteObject + `@ResponseStatus(HttpStatus.ACCEPTED)` —— 202 空体。
async fn delete_object(
    State(state): State<AppState>,
    Path((bucket_name, object_name)): Path<(String, String)>,
) -> Result<Response, AppError> {
    client(&state)
        .delete_object(&bucket_name, &object_name)
        .await?;
    Response::builder()
        .status(StatusCode::ACCEPTED)
        .body(axum::body::Body::empty())
        .map_err(|err| AppError::Service(err.to_string()))
}

/// Java: getObject —— 返回 HashMap（实测键序 bucket、expires、url、object）。
async fn presigned_url(
    State(state): State<AppState>,
    Path((bucket_name, object_name, expires)): Path<(String, String, String)>,
) -> Result<Json<Value>, AppError> {
    let expires = support::path_int("expires", &expires)?;
    let url = client(&state).presigned_url(&bucket_name, &object_name, expires)?;
    Ok(Json(json!({
        "bucket": bucket_name,
        "expires": expires,
        "url": url,
        "object": object_name,
    })))
}
