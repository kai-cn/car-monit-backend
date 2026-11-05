// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CommonController.java
// 职责: 通用下载/上传（单/多文件）。
// 对应关系: FileUtils/FileUploadUtils -> profile 目录；serverConfig.getUrl -> 请求 Host。

use axum::extract::{Multipart, Query, State};
use axum::http::header;
use axum::http::HeaderMap;
use axum::response::{IntoResponse, Response};
use axum::Router;
use serde_json::json;

use crate::api::meta;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

/// Java: MimeTypeUtils.DEFAULT_ALLOWED_EXTENSION。
const ALLOWED_EXT: &[&str] = &[
    "bmp", "gif", "jpg", "jpeg", "png", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm",
    "txt", "rar", "zip", "gz", "bz2", "mp4", "avi", "rmvb",
];

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/common/download",
            meta::get_route("/common/download", None, None, download),
        )
        .route(
            "/common/download/resource",
            meta::get_route("/common/download/resource", None, None, download_resource),
        )
        .route(
            "/common/upload",
            meta::post_route("/common/upload", None, None, upload),
        )
        .route(
            "/common/uploads",
            meta::post_route("/common/uploads", None, None, uploads),
        )
}

/// Java: FileUtils.checkAllowDownload —— 禁止 ".."，扩展名白名单。
fn allow_download(name: &str) -> bool {
    if name.contains("..") {
        return false;
    }
    let ext = name.rsplit_once('.').map(|(_, ext)| ext.to_lowercase());
    ext.map(|ext| ALLOWED_EXT.contains(&ext.as_str()))
        .unwrap_or(false)
}

/// Java: serverConfig.getUrl() —— scheme://host（无 contextPath）。
fn server_url(headers: &HeaderMap) -> String {
    let host = headers
        .get(header::HOST)
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default();
    format!("http://{host}")
}

async fn download(
    State(state): State<AppState>,
    Query(params): Query<std::collections::HashMap<String, String>>,
) -> Response {
    let file_name = params.get("fileName").cloned().unwrap_or_default();
    let delete = params
        .get("delete")
        .map(|value| value == "true")
        .unwrap_or(false);
    if !allow_download(&file_name) {
        tracing::error!("下载文件失败: 文件名称({file_name})非法，不允许下载。");
        return (
            [(header::CONTENT_TYPE, "application/octet-stream")],
            Vec::<u8>::new(),
        )
            .into_response();
    }
    let real_name = format!(
        "{}{}",
        chrono::Local::now().timestamp_millis(),
        file_name
            .split_once('_')
            .map(|(_, rest)| rest)
            .unwrap_or(&file_name)
    );
    let path = std::path::PathBuf::from(&state.settings.ruoyi.profile)
        .join("download")
        .join(&file_name);
    match std::fs::read(&path) {
        Ok(bytes) => {
            if delete {
                let _ = std::fs::remove_file(&path);
            }
            (
                [
                    (header::CONTENT_TYPE, "application/octet-stream".to_string()),
                    (
                        header::CONTENT_DISPOSITION,
                        format!("attachment; filename=\"{real_name}\""),
                    ),
                ],
                bytes,
            )
                .into_response()
        }
        Err(err) => {
            tracing::error!("下载文件失败: {err}");
            (
                [(header::CONTENT_TYPE, "application/octet-stream")],
                Vec::<u8>::new(),
            )
                .into_response()
        }
    }
}

/// Java: resourceDownload —— 方法体已全部注释，永远返回空响应。
async fn download_resource() -> Response {
    (
        [(header::CONTENT_TYPE, "application/octet-stream")],
        Vec::<u8>::new(),
    )
        .into_response()
}

fn upload_path(state: &AppState, original: &str) -> Result<(String, std::path::PathBuf), AppError> {
    let date_path = chrono::Local::now().format("%Y/%m/%d").to_string();
    let base = original
        .rsplit_once('.')
        .map(|(base, _)| base)
        .unwrap_or("file");
    let ext = original.rsplit_once('.').map(|(_, ext)| ext).unwrap_or("");
    let file_name = format!(
        "{date_path}/{base}_{}.{ext}",
        chrono::Local::now().timestamp_millis()
    );
    let relative = format!("/profile/upload/{file_name}");
    let path = std::path::PathBuf::from(&state.settings.ruoyi.profile)
        .join("upload")
        .join(&file_name);
    Ok((relative, path))
}

async fn store_upload(state: &AppState, original: &str, bytes: &[u8]) -> Result<String, AppError> {
    let (relative, path) = upload_path(state, original)?;
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|err| AppError::Service(format!("创建上传目录失败: {err}")))?;
    }
    std::fs::write(&path, bytes)
        .map_err(|err| AppError::Service(format!("写入文件失败: {err}")))?;
    Ok(relative)
}

async fn upload(
    State(state): State<AppState>,
    headers: HeaderMap,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        if field.file_name().is_some() {
            let original = field.file_name().unwrap_or_default().to_string();
            let bytes = field
                .bytes()
                .await
                .map_err(|err| AppError::BadRequest(err.to_string()))?;
            let file_name = store_upload(&state, &original, &bytes).await?;
            let url = format!("{}{}", server_url(&headers), file_name);
            let new_file_name = file_name.rsplit('/').next().unwrap_or_default();
            let mut ajax = AjaxResult::success();
            ajax.insert_value("url", json!(url));
            ajax.insert_value("fileName", json!(file_name));
            ajax.insert_value("newFileName", json!(new_file_name));
            ajax.insert_value("originalFilename", json!(original));
            return Ok(ajax);
        }
    }
    Ok(AjaxResult::error("上传失败"))
}

async fn uploads(
    State(state): State<AppState>,
    headers: HeaderMap,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    let mut urls = Vec::new();
    let mut file_names = Vec::new();
    let mut new_file_names = Vec::new();
    let mut original_names = Vec::new();
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        if field.file_name().is_none() {
            continue;
        }
        let original = field.file_name().unwrap_or_default().to_string();
        let bytes = field
            .bytes()
            .await
            .map_err(|err| AppError::BadRequest(err.to_string()))?;
        let file_name = store_upload(&state, &original, &bytes).await?;
        urls.push(format!("{}{}", server_url(&headers), file_name));
        new_file_names.push(file_name.rsplit('/').next().unwrap_or_default().to_string());
        file_names.push(file_name);
        original_names.push(original);
    }
    let mut ajax = AjaxResult::success();
    ajax.insert_value("urls", json!(urls.join(",")));
    ajax.insert_value("fileNames", json!(file_names.join(",")));
    ajax.insert_value("newFileNames", json!(new_file_names.join(",")));
    ajax.insert_value("originalFilenames", json!(original_names.join(",")));
    Ok(ajax)
}
