// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysFileController.java
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysFileServiceImpl.java
//       ruoyi-system/src/main/resources/mapper/system/SysFileMapper.xml
// 职责: 文件管理（列表/上传/下载/删除/CA 更新）。
// 对应关系: OssTemplate.putObject/getObject/removeObject -> 本地 profile/upload 目录。
// 说明: Java 的上传对象存 S3（OssProperties/OssTemplate）；Rust 侧未配置对象存储，
//       按现有 profile 目录落盘，响应形状（bucketName/fileName/url/id）保持不变。

use axum::extract::{Multipart, Path, RawQuery, State};
use axum::http::header;
use axum::response::{IntoResponse, Response};
use axum::{Extension, Json, Router};
use base64::Engine;
use serde_json::{json, Map, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, FieldFormat, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.file_name, t.bucket_name, t.original, t.type, t.file_size, t.buss_type, \
             t.buss_name, t.create_user, t.create_time, t.update_user, t.update_time, \
             t.del_flag, t.tenant_id, null as files, null as createUserName",
    from: "from sys_file t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::like("fileName", "t.file_name"),
        Filter::like("bucketName", "t.bucket_name"),
        Filter::eq("original", "t.original"),
        Filter::eq("type", "t.type"),
        Filter::eq("fileSize", "t.file_size"),
        Filter::eq("bussType", "t.buss_type"),
        Filter::like("bussName", "t.buss_name"),
        Filter::eq("createUser", "t.create_user"),
        Filter::eq("updateUser", "t.update_user"),
        Filter::eq("tenantId", "t.tenant_id"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.id",
};

// Java: SysFile.id 是 String（雪花 ID），files/createUserName 为 transient 字段。
const FORMATS: &[(&str, FieldFormat)] = &[("id", FieldFormat::String)];

/// Java: fileLog/fileLogId 的扩展名白名单。
const ALLOWED_EXT: &[&str] = &[
    "doc", "docx", "pdf", "xls", "xlsx", "ppt", "pptx", "txt", "zip", "rar", "jpg", "jpeg", "png",
    "gif", "mp3", "mp4", "flv", "3gp",
];

static LOG_UPLOAD: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysFileController.upload()",
);
static LOG_UPLOAD_URL: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysFileController.uploadByUrl()",
);
static LOG_UPLOAD_SUPPLIER: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysFileController.uploadSupplier()",
);
static LOG_UPLOAD_PDF: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysFileController.uploadPdf()",
);
static LOG_UPLOAD_ID: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysFileController.uploadFileId()",
);
static LOG_UPLOAD_ENC: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysFileController.uploadFileEnc()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "文件管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysFileController.edit()",
);
static LOG_CA: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysFileController.updateCAFile()",
);
static LOG_DELETE: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysFileController.remove()",
);
static LOG_DELETE_ONE: LogSpec = LogSpec::new(
    "文件",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysFileController.removeById()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/file/list",
            meta::get_route("/system/file/list", Some("base:sysflie:list"), None, list),
        )
        .route(
            "/system/file/getInfoById/{id}",
            meta::get_route("/system/file/getInfoById/{id}", None, None, get_info_by_id),
        )
        .route(
            "/system/file/getNewCa",
            meta::get_route("/system/file/getNewCa", None, None, get_new_ca),
        )
        .route(
            "/system/file/upload",
            meta::post_route("/system/file/upload", None, Some(&LOG_UPLOAD), upload),
        )
        .route(
            "/system/file/uploadByUrl",
            meta::post_route(
                "/system/file/uploadByUrl",
                None,
                Some(&LOG_UPLOAD_URL),
                upload_by_url,
            ),
        )
        .route(
            "/system/file/uploadSupplier",
            meta::post_route(
                "/system/file/uploadSupplier",
                None,
                Some(&LOG_UPLOAD_SUPPLIER),
                upload_supplier,
            ),
        )
        .route(
            "/system/file/uploadPdf",
            meta::post_route(
                "/system/file/uploadPdf",
                None,
                Some(&LOG_UPLOAD_PDF),
                upload_pdf,
            ),
        )
        .route(
            "/system/file/uploadFileId",
            meta::post_route(
                "/system/file/uploadFileId",
                None,
                Some(&LOG_UPLOAD_ID),
                upload_file_id,
            ),
        )
        .route(
            "/system/file/uploadFileEnc",
            meta::post_route(
                "/system/file/uploadFileEnc",
                None,
                Some(&LOG_UPLOAD_ENC),
                upload_file_enc,
            ),
        )
        .route(
            "/system/file/uploadFile",
            meta::post_route("/system/file/uploadFile", None, None, upload_file),
        )
        .route(
            "/system/file/updateCAFile",
            meta::post_route(
                "/system/file/updateCAFile",
                None,
                Some(&LOG_CA),
                update_ca_file,
            ),
        )
        .route(
            "/system/file",
            meta::put_route("/system/file", None, Some(&LOG_EDIT), edit),
        )
        .route(
            "/system/file/del/{id}",
            meta::delete_route(
                "/system/file/del/{id}",
                None,
                Some(&LOG_DELETE_ONE),
                remove_by_id,
            ),
        )
        .route(
            "/system/file/view/{bucket}/{fileName}",
            meta::get_route(
                "/system/file/view/{bucket}/{fileName}",
                None,
                None,
                view_file,
            ),
        )
        .route(
            "/system/file/{bucket}/{fileName}",
            meta::get_route("/system/file/{bucket}/{fileName}", None, None, view_file),
        )
        .route(
            "/system/file/{ids}",
            meta::get_route("/system/file/{ids}", None, None, get_info).merge(meta::delete_route(
                "/system/file/{ids}",
                Some("base:supplier:remove"),
                Some(&LOG_DELETE),
                remove,
            )),
        )
}

fn upload_dir(profile: &str) -> std::path::PathBuf {
    std::path::PathBuf::from(profile).join("upload")
}

/// Java: `IdUtil.simpleUUID() + "." + extName(original)`。
fn stored_name(original: &str) -> String {
    let ext = original
        .rsplit_once('.')
        .map(|(_, ext)| ext)
        .unwrap_or_default();
    format!("{}.{}", uuid::Uuid::new_v4().simple(), ext)
}

fn ext_allowed(original: &str) -> Option<String> {
    let ext = original
        .rsplit_once('.')
        .map(|(_, ext)| ext.to_lowercase())?;
    if ext.is_empty() {
        return None;
    }
    ALLOWED_EXT.contains(&ext.as_str()).then_some(ext)
}

/// Java: `ossTemplate.putObject(bucket, fileName, stream)` -> 本地落盘。
fn store_file(state: &AppState, file_name: &str, bytes: &[u8]) -> Result<(), AppError> {
    let dir = upload_dir(&state.settings.ruoyi.profile);
    std::fs::create_dir_all(&dir)
        .map_err(|err| AppError::Service(format!("创建上传目录失败: {err}")))?;
    std::fs::write(dir.join(file_name), bytes)
        .map_err(|err| AppError::Service(format!("写入文件失败: {err}")))
}

/// Java: `fileLog` —— 记录允许的文件类型；不支持的返回 -1。
async fn file_log(
    state: &AppState,
    user: Option<&LoginUser>,
    original: &str,
    file_name: &str,
    size: i64,
    buss_name: Option<&str>,
) -> Result<(i64, Option<String>), AppError> {
    let Some(ext) = ext_allowed(original) else {
        return Ok((-1, None));
    };
    let id = state.snowflake.next_id()?;
    let user_id = user
        .and_then(|user| user.user.user_id)
        .map(|id| id.to_string());
    let now = support::now_string();
    let body = json!({
        "id": id,
        "fileName": file_name,
        "original": original,
        "fileSize": size,
        "type": ext,
        "bucketName": state.settings.oss.bucket_name,
        "bussName": buss_name,
        "createUser": user_id,
        "updateUser": user_id,
        "createTime": now,
        "updateTime": now,
        "delFlag": "0",
    });
    support::insert_entity(&state.db, "sys_file", &body, support::AutoFill::NONE).await?;
    Ok((id, Some(ext)))
}

fn result_map(state: &AppState, file_name: &str, id: Option<i64>) -> Map<String, Value> {
    let bucket = &state.settings.oss.bucket_name;
    let mut map = Map::new();
    map.insert("bucketName".to_string(), json!(bucket));
    map.insert("fileName".to_string(), json!(file_name));
    map.insert(
        "url".to_string(),
        json!(format!("/system/file/{bucket}/{file_name}")),
    );
    if let Some(id) = id {
        map.insert("id".to_string(), json!(id.to_string()));
    }
    map
}

/// Java Jackson 的 SysFile 键序：实体声明顺序 + 派生 `files`/`createUserName`。
const FILE_KEYS: &[&str] = &[
    "id",
    "fileName",
    "bucketName",
    "original",
    "type",
    "fileSize",
    "bussType",
    "bussName",
    "createTime",
    "createUser",
    "updateTime",
    "updateUser",
    "delFlag",
    "tenantId",
    "files",
    "createUserName",
];

fn shape_file_rows(rows: Vec<Value>) -> Vec<Value> {
    support::reorder_rows(rows, FILE_KEYS)
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    Ok(TableDataInfo::new(total, shape_file_rows(rows)))
}

async fn get_info_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long id`。
    let id = support::path_long("id", &id)?.to_string();
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &id, FORMATS)
            .await?
            .map(|row| shape_file_rows(vec![row]).pop().unwrap_or(Value::Null)),
    ))
}

async fn get_info(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: deleteEnd(ids)；空串替换成 -111111。
    let ids = ids.trim().trim_end_matches(',');
    let ids = if ids.is_empty() { "-111111" } else { ids };
    let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new(&format!(
        "select {}, t2.nick_name createUserName from sys_file t \
         left join sys_user t2 on t.create_user = t2.user_id and t2.del_flag='0' where t.id in (",
        SPEC.select
    ));
    let parts = support::ids_param(ids);
    let mut separated = builder.separated(", ");
    for part in &parts {
        separated.push_bind(part.clone());
    }
    builder.push(") order by t.id");
    let rows = builder.build().fetch_all(&state.db).await?;
    let mut rows = crate::db::rows::rows_to_json(&rows);
    support::apply_formats(&mut rows, FORMATS);
    Ok(AjaxResult::success_data(shape_file_rows(rows)))
}

async fn get_new_ca(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (_, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    match shape_file_rows(rows).into_iter().next() {
        Some(row) => Ok(AjaxResult::success_data(row)),
        None => Ok(AjaxResult::error("未找到CA驱动程序")),
    }
}

async fn multipart_files(multipart: &mut Multipart) -> Result<Vec<(String, Vec<u8>)>, AppError> {
    let mut files = Vec::new();
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        let name = field.file_name().unwrap_or_default().to_string();
        let bytes = field
            .bytes()
            .await
            .map_err(|err| AppError::BadRequest(err.to_string()))?;
        files.push((name, bytes.to_vec()));
    }
    Ok(files)
}

/// Java: uploadFiles —— 逐个落盘并登记 sys_file。
async fn upload_documents(
    state: &AppState,
    user: Option<&LoginUser>,
    files: Vec<(String, Vec<u8>)>,
    buss_names: Option<Vec<String>>,
) -> Result<AjaxResult, AppError> {
    let mut results = Vec::new();
    for (index, (original, bytes)) in files.into_iter().enumerate() {
        let file_name = stored_name(&original);
        let buss_name = buss_names
            .as_ref()
            .and_then(|names| names.get(index))
            .map(String::as_str);
        let (id, ext) = file_log(
            state,
            user,
            &original,
            &file_name,
            bytes.len() as i64,
            buss_name,
        )
        .await?;
        if ext.is_some() {
            store_file(state, &file_name, &bytes)?;
        }
        results.push(Value::Object(result_map(state, &file_name, Some(id))));
    }
    Ok(AjaxResult::success_data(results))
}

async fn upload(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    let files = multipart_files(&mut multipart).await?;
    upload_documents(&state, Some(&user), files, None).await
}

async fn upload_file(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    let mut files = Vec::new();
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        let original = field.file_name().unwrap_or_default().to_string();
        let bytes = field
            .bytes()
            .await
            .map_err(|err| AppError::BadRequest(err.to_string()))?;
        let ext = original.rsplit_once('.').map(|(_, ext)| ext.to_lowercase());
        match ext.as_deref() {
            Some(ext)
                if ext.contains("jpg")
                    || ext.contains("jpeg")
                    || ext.contains("png")
                    || ext.contains("gif") => {}
            _ => return Ok(AjaxResult::error("上传失败,请上传照片格式的附件！")),
        }
        files.push((original, bytes.to_vec()));
    }
    upload_documents(&state, Some(&user), files, None).await
}

async fn upload_pdf(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    // Java 非 PDF 走格式转换（Java 库）；这里保留原文件上传。
    let files = multipart_files(&mut multipart).await?;
    upload_documents(&state, Some(&user), files, None).await
}

async fn upload_supplier(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    let mut files = Vec::new();
    let mut buss_names = Vec::new();
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
            files.push((original, bytes.to_vec()));
        } else if let Ok(text) = field.text().await {
            buss_names.push(text);
        }
    }
    upload_documents(&state, Some(&user), files, Some(buss_names)).await
}

async fn upload_by_url(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let mut results = Vec::new();
    let items = body
        .get("list")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    for item in items {
        let Some(url) = item.get("url").and_then(Value::as_str) else {
            continue;
        };
        let name = item
            .get("fileName")
            .and_then(Value::as_str)
            .unwrap_or_default();
        let original = format!("{name}.jpg");
        let bytes = match state.http.get(url).send().await {
            Ok(response) => response.bytes().await.map(|bytes| bytes.to_vec()),
            Err(err) => {
                tracing::error!("上传失败: {err}");
                continue;
            }
        };
        let Ok(bytes) = bytes else { continue };
        let file_name = stored_name(&original);
        let (id, ext) = file_log(
            &state,
            Some(&user),
            &original,
            &file_name,
            bytes.len() as i64,
            None,
        )
        .await?;
        if ext.is_some() {
            store_file(&state, &file_name, &bytes)?;
        }
        results.push(Value::Object(result_map(&state, &file_name, Some(id))));
    }
    Ok(AjaxResult::success_data(results))
}

async fn upload_file_id(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let id = body.get("id").and_then(Value::as_i64);
    let encoded = body
        .get("files")
        .and_then(Value::as_str)
        .unwrap_or_default();
    if encoded.is_empty() {
        return Ok(AjaxResult::error("主键不能为空"));
    }
    let raw = encoded
        .split_once(',')
        .map(|(_, rest)| rest)
        .unwrap_or(encoded);
    let bytes = base64::engine::general_purpose::STANDARD
        .decode(raw)
        .or_else(|_| base64::engine::general_purpose::STANDARD_NO_PAD.decode(raw))
        .map_err(|err| AppError::BadRequest(format!("base64 解析失败: {err}")))?;
    let original = body
        .get("original")
        .and_then(Value::as_str)
        .unwrap_or("upload.jpg")
        .to_string();
    let file_name = stored_name(&original);

    // Java: 先删除同 id 记录，再按指定 id 插入。
    if let Some(id) = id {
        sqlx::query("delete from sys_file where id = ?")
            .bind(id)
            .execute(&state.db)
            .await?;
    }
    let ext = ext_allowed(&original);
    if ext.is_none() {
        return Ok(AjaxResult::success_data(vec![Value::Object(result_map(
            &state, &file_name, id,
        ))]));
    }
    let user_id = user.user.user_id.map(|id| id.to_string());
    let now = support::now_string();
    let entity = json!({
        "id": id.unwrap_or(state.snowflake.next_id()?),
        "fileName": file_name,
        "original": original,
        "fileSize": bytes.len() as i64,
        "type": ext,
        "bucketName": state.settings.oss.bucket_name,
        "createUser": user_id,
        "updateUser": user_id,
        "createTime": now,
        "updateTime": now,
        "delFlag": "0",
    });
    support::insert_entity(&state.db, "sys_file", &entity, support::AutoFill::NONE).await?;
    store_file(&state, &file_name, &bytes)?;
    let result = result_map(&state, &file_name, id);
    Ok(AjaxResult::success_data(vec![Value::Object(result)]))
}

async fn upload_file_enc(
    State(_state): State<AppState>,
    Extension(_user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    // Java: 整个方法体被注释，永远返回空数组。
    let _ = multipart_files(&mut multipart).await?;
    Ok(AjaxResult::success_data(Vec::<Value>::new()))
}

async fn view_file(
    State(state): State<AppState>,
    Path((_bucket, file_name)): Path<(String, String)>,
) -> Response {
    let path = upload_dir(&state.settings.ruoyi.profile).join(&file_name);
    match std::fs::read(&path) {
        Ok(bytes) => {
            let mime = mime_guess::from_path(&path)
                .first_raw()
                .unwrap_or("application/octet-stream");
            ([(header::CONTENT_TYPE, mime.to_string())], bytes).into_response()
        }
        Err(_) => (
            [(header::CONTENT_TYPE, "application/octet-stream".to_string())],
            Vec::<u8>::new(),
        )
            .into_response(),
    }
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let mut entity = body;
    let user_id = user.user.user_id.map(|id| id.to_string());
    let now = support::now_string();
    if entity.get("id").is_none() || entity.get("id") == Some(&Value::Null) {
        if let Some(object) = entity.as_object_mut() {
            object.insert("delFlag".to_string(), json!("0"));
            object.insert("createUser".to_string(), json!(user_id));
            object.insert("updateUser".to_string(), json!(user_id));
            object.insert("createTime".to_string(), json!(now));
            object.insert("updateTime".to_string(), json!(now));
        }
        let id = state.snowflake.next_id()?;
        if let Some(object) = entity.as_object_mut() {
            object.insert("id".to_string(), json!(id));
        }
        support::insert_entity(&state.db, "sys_file", &entity, support::AutoFill::NONE).await?;
        return Ok(AjaxResult::success_msg_data("操作成功！", id));
    }
    let id = entity.get("id").cloned().unwrap_or(Value::Null);
    if let Some(object) = entity.as_object_mut() {
        object.insert("updateUser".to_string(), json!(user_id));
        object.insert("updateTime".to_string(), json!(now));
    }
    support::update_entity_by_id(
        &state.db,
        "sys_file",
        "id",
        &entity,
        support::AutoFill::NONE,
    )
    .await?;
    Ok(AjaxResult::success_msg_data("操作成功！", id))
}

async fn remove_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long id`（DELETE /system/file/del/{id}）。
    let id = support::path_long("id", &id)?.to_string();
    let file_name: Option<String> =
        sqlx::query_scalar("select file_name from sys_file where id = ?")
            .bind(&id)
            .fetch_optional(&state.db)
            .await?;
    if let Some(file_name) = file_name {
        let _ = std::fs::remove_file(upload_dir(&state.settings.ruoyi.profile).join(file_name));
    }
    let rows = sqlx::query("update sys_file set del_flag = '1' where id = ?")
        .bind(&id)
        .execute(&state.db)
        .await?
        .rows_affected();
    Ok(AjaxResult::success_data(rows))
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] ids` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("ids", &ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    for id in &ids {
        let file_name: Option<String> =
            sqlx::query_scalar("select file_name from sys_file where id = ?")
                .bind(id)
                .fetch_optional(&state.db)
                .await?;
        if let Some(file_name) = file_name {
            let _ = std::fs::remove_file(upload_dir(&state.settings.ruoyi.profile).join(file_name));
        }
    }
    let rows = support::soft_delete_by_ids(&state.db, "sys_file", "id", &ids).await?;
    Ok(AjaxResult::success_data(rows))
}

/// Java: updateCAFile —— 删除 id=3001 的旧记录并把当前文件改成 3001。
async fn update_ca_file(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let id = body.get("id").cloned().unwrap_or(Value::Null);
    sqlx::query("delete from sys_file where id = 3001")
        .execute(&state.db)
        .await?;
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "updateUser".to_string(),
            json!(user.user.user_id.map(|id| id.to_string())),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
    }
    support::update_entity_by_id(
        &state.db,
        "sys_file",
        "id",
        &entity,
        support::AutoFill::NONE,
    )
    .await?;
    sqlx::query("update sys_file set id = 3001 where id = ?")
        .bind(id.as_i64())
        .execute(&state.db)
        .await?;
    Ok(AjaxResult::success_msg_data("操作成功！", id))
}
