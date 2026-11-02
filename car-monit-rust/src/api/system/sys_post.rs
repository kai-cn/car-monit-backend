// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysPostController.java
//       ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml
// 职责: 岗位管理 CRUD、导出与下拉列表。
// 对应关系: list/export/getInfo/add/edit/remove/optionselect -> SPEC + 自定义保存。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill, FieldFormat, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "post_id, post_code, post_name, post_sort, status, create_by, create_time, remark, \n             null as updateBy, null as updateTime, 0 as flag",
    from: "from sys_post",
    filters: &[
        Filter::like("postCode", "post_code"),
        Filter::eq("status", "status"),
        Filter::like("postName", "post_name"),
    ],
    extra_where: "",
    order_by: "",
    id_column: "post_id",
};

// Java: postSort 是 String；flag 是 boolean。
const FORMATS: &[(&str, FieldFormat)] = &[
    ("postSort", FieldFormat::String),
    ("flag", FieldFormat::Bool),
];

static LOG_EXPORT: LogSpec = LogSpec::new(
    "岗位管理",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysPostController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "岗位管理",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysPostController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "岗位管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysPostController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "岗位管理",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysPostController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/post/list",
            meta::get_route("/system/post/list", Some("system:post:list"), None, list),
        )
        .route(
            "/system/post/export",
            meta::get_route(
                "/system/post/export",
                Some("system:post:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/post/optionselect",
            meta::get_route("/system/post/optionselect", None, None, optionselect),
        )
        .route(
            "/system/post/{postIds}",
            meta::get_route("/system/post/{postIds}", Some("system:post:query"), None, get_info),
        )
        .route(
            "/system/post",
            meta::post_route("/system/post", Some("system:post:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/system/post",
                    Some("system:post:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/system/post/{postIds}",
            meta::delete_route(
                "/system/post/{postIds}",
                Some("system:post:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    Ok(TableDataInfo::new(total, shape_post_rows(rows)))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all_fmt(&state.db, &params, &SPEC, FORMATS).await?;
    let headers =
        ["岗位序号", "岗位编码", "岗位名称", "岗位排序", "状态"].map(str::to_string);
    let fields = ["postId", "postCode", "postName", "postSort", "status"];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            // @Excel(readConverterExp = "0=正常,1=停用")
            if let Some(Value::String(text)) = values.get(4).cloned() {
                values[4] = Value::String(match text.as_str() {
                    "0" => "正常".to_string(),
                    "1" => "停用".to_string(),
                    _ => text,
                });
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "岗位数据", &headers, &data)
}

/// Java Jackson 的 SysPost 键序（BaseEntity 在前，派生 getter `flag` 最后）。
pub(crate) const POST_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "postId",
    "postCode",
    "postName",
    "postSort",
    "status",
    "flag",
];

fn shape_post_rows(mut rows: Vec<Value>) -> Vec<Value> {
    support::apply_formats(&mut rows, FORMATS);
    for row in &mut rows {
        if let Some(object) = row.as_object_mut() {
            object.entry("updateBy").or_insert(Value::Null);
            object.entry("updateTime").or_insert(Value::Null);
            object.entry("flag").or_insert(Value::Bool(false));
        }
    }
    for row in rows.iter_mut() {
        *row = support::reorder_keys(row.take(), POST_KEYS);
    }
    rows
}

async fn optionselect(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows =
        support::query_all_fmt(&state.db, &std::collections::HashMap::new(), &SPEC, FORMATS).await?;
    Ok(AjaxResult::success_data(shape_post_rows(rows)))
}

async fn get_info(
    State(state): State<AppState>,
    Path(post_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &post_id, FORMATS)
            .await?
            .map(|row| shape_post_rows(vec![row]).pop().unwrap_or(Value::Null)),
    ))
}

fn text(body: &Value, key: &str) -> String {
    body.get(key).and_then(Value::as_str).unwrap_or_default().trim().to_string()
}

async fn ensure_unique(
    state: &AppState,
    body: &Value,
    column: &str,
    key: &str,
    label: &str,
) -> Result<Option<AjaxResult>, AppError> {
    let value = text(body, key);
    if value.is_empty() {
        return Ok(None);
    }
    let sql = format!("select post_id from sys_post where {column} = ? limit 1");
    let found: Option<i64> = sqlx::query_scalar(&sql).bind(&value).fetch_optional(&state.db).await?;
    let current = body.get("postId").and_then(Value::as_i64).unwrap_or(-1);
    if let Some(found) = found {
        if found != current {
            let verb = if body.get("postId").is_some() { "修改" } else { "新增" };
            return Ok(Some(AjaxResult::error(format!(
                "{verb}岗位'{}'失败，{label}已存在",
                text(body, "postName")
            ))));
        }
    }
    Ok(None)
}

async fn validate_and_save(
    state: &AppState,
    user: &LoginUser,
    body: Value,
    is_add: bool,
) -> Result<AjaxResult, AppError> {
    if text(&body, "postCode").is_empty() {
        return Ok(AjaxResult::error("岗位编码不能为空"));
    }
    if text(&body, "postName").is_empty() {
        return Ok(AjaxResult::error("岗位名称不能为空"));
    }
    if let Some(error) = ensure_unique(state, &body, "post_name", "postName", "岗位名称").await? {
        return Ok(error);
    }
    if let Some(error) = ensure_unique(state, &body, "post_code", "postCode", "岗位编码").await? {
        return Ok(error);
    }

    let mut entity = body;
    let object = entity
        .as_object_mut()
        .ok_or_else(|| AppError::BadRequest("请求体必须是 JSON 对象".to_string()))?;
    if is_add {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("createTime".to_string(), json!(support::now_string()));
        let rows = support::insert_entity(&state.db, "sys_post", &entity, AutoFill::NONE).await?;
        Ok(support::to_ajax(rows))
    } else {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
        let rows = support::update_entity_by_id(
            &state.db,
            "sys_post",
            "post_id",
            &entity,
            AutoFill::NONE,
        )
        .await?;
        Ok(support::to_ajax(rows))
    }
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    validate_and_save(&state, &user, body, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    validate_and_save(&state, &user, body, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(post_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&post_ids);
    for id in &ids {
        let count: i64 =
            sqlx::query_scalar("select count(1) from sys_user_post where post_id = ?")
                .bind(id)
                .fetch_one(&state.db)
                .await?;
        if count > 0 {
            let name: Option<String> =
                sqlx::query_scalar("select post_name from sys_post where post_id = ?")
                    .bind(id)
                    .fetch_optional(&state.db)
                    .await?;
            return Err(AppError::Service(format!(
                "{}已分配,不能删除",
                name.unwrap_or_default()
            )));
        }
    }
    let rows = support::delete_by_ids(&state.db, "sys_post", "post_id", &ids).await?;
    Ok(support::to_ajax(rows))
}
