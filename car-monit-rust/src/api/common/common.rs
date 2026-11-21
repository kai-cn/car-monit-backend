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
use crate::api::support;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

/// Java: MimeTypeUtils.DEFAULT_ALLOWED_EXTENSION。
const ALLOWED_EXT: &[&str] = &[
    "bmp", "gif", "jpg", "jpeg", "png", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm",
    "txt", "rar", "zip", "gz", "bz2", "mp4", "avi", "rmvb", "pdf",
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

/// Java: `FilenameUtils.getBaseName` —— 只保留最后一段，丢掉客户端路径。
fn base_name(original: &str) -> &str {
    original.rsplit(['/', '\\']).next().unwrap_or(original)
}

/// Java: `FilenameUtils.getExtension`（大小写保留，比较时忽略大小写）。
fn extension_of(name: &str) -> String {
    name.rsplit_once('.')
        .map(|(_, ext)| ext.to_string())
        .unwrap_or_default()
}

/// Java: `MimeTypeUtils.getExtension(contentType)` —— 原文件名无后缀时的回退。
fn mime_extension(content_type: Option<&str>) -> &'static str {
    match content_type
        .unwrap_or_default()
        .to_ascii_lowercase()
        .as_str()
    {
        "image/png" => "png",
        "image/jpg" => "jpg",
        "image/jpeg" => "jpeg",
        "image/bmp" => "bmp",
        "image/gif" => "gif",
        _ => "",
    }
}

fn allowed_extension_text() -> String {
    format!("[{}]", ALLOWED_EXT.join(", "))
}

/// Java: `FileUploadUtils.upload` —— 文件名长度 -> 后缀白名单 -> `datePath/base_seq.ext`。
fn prepare_upload(
    state: &AppState,
    original: &str,
    content_type: Option<&str>,
) -> Result<(String, std::path::PathBuf), AppError> {
    // Java: `DEFAULT_FILE_NAME_LENGTH = 100`，按 UTF-16 code unit 计。
    if original.encode_utf16().count() > 100 {
        return Err(AppError::Service("上传的文件名最长100个字符".to_string()));
    }
    let base_name = base_name(original);
    let mut ext = extension_of(base_name);
    if ext.is_empty() {
        ext = mime_extension(content_type).to_string();
    }
    // Java: `isAllowedExtension` 使用 equalsIgnoreCase。
    if !ALLOWED_EXT
        .iter()
        .any(|item| item.eq_ignore_ascii_case(&ext))
    {
        return Err(AppError::Service(format!(
            "文件[{original}]后缀[{ext}]不正确，请上传{}格式",
            allowed_extension_text()
        )));
    }
    let base = base_name
        .rsplit_once('.')
        .map(|(base, _)| base)
        .unwrap_or(base_name);
    let base = if base.is_empty() { "file" } else { base };
    let date_path = chrono::Local::now().format("%Y/%m/%d").to_string();
    // Java: `Seq.getId(Seq.uploadSeqType)`；这里用进程内雪花 ID 保证并发唯一。
    let seq = state.snowflake.next_id()?;
    let file_name = format!("{date_path}/{base}_{seq}.{ext}");
    let relative = format!("/profile/upload/{file_name}");
    let path = std::path::PathBuf::from(&state.settings.ruoyi.profile)
        .join("upload")
        .join(&file_name);
    Ok((relative, path))
}

async fn store_upload(
    state: &AppState,
    original: &str,
    content_type: Option<&str>,
    bytes: &[u8],
) -> Result<String, AppError> {
    let (relative, path) = prepare_upload(state, original, content_type)?;
    let bytes = bytes.to_vec();
    // 落盘是阻塞 IO，移出 tokio worker。
    tokio::task::spawn_blocking(move || {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|err| AppError::Service(format!("创建上传目录失败: {err}")))?;
        }
        std::fs::write(&path, &bytes)
            .map_err(|err| AppError::Service(format!("写入文件失败: {err}")))
    })
    .await
    .map_err(|err| AppError::Service(format!("写入任务失败: {err}")))??;
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
            let upload = support::read_multipart_field(field).await?;
            let file_name = store_upload(
                &state,
                &upload.file_name,
                upload.content_type.as_deref(),
                &upload.bytes,
            )
            .await?;
            let url = format!("{}{}", server_url(&headers), file_name);
            let new_file_name = file_name.rsplit('/').next().unwrap_or_default();
            let mut ajax = AjaxResult::success();
            ajax.insert_value("url", json!(url));
            ajax.insert_value("fileName", json!(file_name));
            ajax.insert_value("newFileName", json!(new_file_name));
            ajax.insert_value("originalFilename", json!(upload.file_name));
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
        let upload = support::read_multipart_field(field).await?;
        let file_name = store_upload(
            &state,
            &upload.file_name,
            upload.content_type.as_deref(),
            &upload.bytes,
        )
        .await?;
        urls.push(format!("{}{}", server_url(&headers), file_name));
        new_file_names.push(file_name.rsplit('/').next().unwrap_or_default().to_string());
        file_names.push(file_name);
        original_names.push(upload.file_name);
    }
    let mut ajax = AjaxResult::success();
    ajax.insert_value("urls", json!(urls.join(",")));
    ajax.insert_value("fileNames", json!(file_names.join(",")));
    ajax.insert_value("newFileNames", json!(new_file_names.join(",")));
    ajax.insert_value("originalFilenames", json!(original_names.join(",")));
    Ok(ajax)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn client_paths_are_reduced_to_basename() {
        assert_eq!(base_name(r"C:\fakepath\a.png"), "a.png");
        assert_eq!(base_name("../../evil.png"), "evil.png");
        assert_eq!(base_name("plain.txt"), "plain.txt");
    }

    #[test]
    fn extension_rules_match_java() {
        assert_eq!(extension_of("a.PNG"), "PNG");
        assert_eq!(extension_of("noext"), "");
        assert_eq!(mime_extension(Some("image/png")), "png");
        assert_eq!(mime_extension(Some("image/jpeg")), "jpeg");
        assert_eq!(mime_extension(Some("application/octet-stream")), "");
        assert!(allowed_extension_text().contains("pdf"));
    }
}
