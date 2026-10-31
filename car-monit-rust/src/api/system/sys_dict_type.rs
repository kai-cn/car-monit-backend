// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictTypeController.java
//       ruoyi-system/src/main/resources/mapper/system/SysDictTypeMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictTypeServiceImpl.java
// 职责: 字典类型 CRUD + sys_dict:* 缓存清理。
// 对应关系: list/export/get/optionselect/add/edit/remove/clearCache。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "dict_id, dict_name, dict_type, status, create_by, create_time, remark",
    from: "from sys_dict_type",
    filters: &[
        Filter::like("dictName", "dict_name"),
        Filter::eq("status", "status"),
        Filter::like("dictType", "dict_type"),
        Filter::raw(
            "params[beginTime]",
            " and date_format(create_time,'%y%m%d') >= date_format(?, '%y%m%d')",
        ),
        Filter::raw(
            "params[endTime]",
            " and date_format(create_time,'%y%m%d') <= date_format(?, '%y%m%d')",
        ),
    ],
    extra_where: "",
    order_by: "create_time desc",
    id_column: "dict_id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "字典类型",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysDictTypeController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "字典类型",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysDictTypeController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "字典类型",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysDictTypeController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "字典类型",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysDictTypeController.remove()",
);
static LOG_CLEAR: LogSpec = LogSpec::new(
    "字典类型",
    BusinessType::Clean,
    "com.ruoyi.web.controller.system.SysDictTypeController.clearCache()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/dict/type/list",
            meta::get_route("/system/dict/type/list", Some("system:dict:list"), None, list),
        )
        .route(
            "/system/dict/type/export",
            meta::get_route(
                "/system/dict/type/export",
                Some("system:dict:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/dict/type/optionselect",
            meta::get_route("/system/dict/type/optionselect", None, None, optionselect),
        )
        .route(
            "/system/dict/type/clearCache",
            meta::delete_route(
                "/system/dict/type/clearCache",
                Some("system:dict:remove"),
                Some(&LOG_CLEAR),
                clear_cache,
            ),
        )
        .route(
            "/system/dict/type/{dictIds}",
            meta::get_route(
                "/system/dict/type/{dictIds}",
                Some("system:dict:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/system/dict/type",
            meta::post_route(
                "/system/dict/type",
                Some("system:dict:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/system/dict/type",
                Some("system:dict:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/system/dict/type/{dictIds}",
            meta::delete_route(
                "/system/dict/type/{dictIds}",
                Some("system:dict:remove"),
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
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = ["字典主键", "字典名称", "字典类型", "状态"].map(str::to_string);
    let fields = ["dictId", "dictName", "dictType", "status"];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            if let Some(Value::String(text)) = values.get(3).cloned() {
                values[3] = Value::String(convert_status(&text));
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "字典类型", &headers, &data)
}

fn convert_status(text: &str) -> String {
    match text {
        "0" => "正常".to_string(),
        "1" => "停用".to_string(),
        other => other.to_string(),
    }
}

async fn optionselect(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows = support::query_all(&state.db, &std::collections::HashMap::new(), &SPEC).await?;
    Ok(AjaxResult::success_data(rows))
}

async fn get_info(
    State(state): State<AppState>,
    Path(dict_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &dict_id).await?,
    ))
}

async fn save(
    state: &AppState,
    user: &LoginUser,
    body: Value,
    is_add: bool,
) -> Result<AjaxResult, AppError> {
    for (key, message) in [("dictName", "字典名称不能为空"), ("dictType", "字典类型不能为空")] {
        let value = body.get(key).and_then(Value::as_str).unwrap_or_default();
        if value.trim().is_empty() {
            return Ok(AjaxResult::error(message));
        }
    }
    let dict_type = body
        .get("dictType")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let found: Option<i64> =
        sqlx::query_scalar("select dict_id from sys_dict_type where dict_type = ? limit 1")
            .bind(&dict_type)
            .fetch_optional(&state.db)
            .await?;
    let current = body.get("dictId").and_then(Value::as_i64).unwrap_or(-1);
    if let Some(found) = found {
        if found != current {
            let name = body.get("dictName").and_then(Value::as_str).unwrap_or_default();
            let verb = if is_add { "新增" } else { "修改" };
            return Ok(AjaxResult::error(format!(
                "{verb}字典'{name}'失败，字典类型已存在"
            )));
        }
    }

    let mut entity = body;
    let object = entity
        .as_object_mut()
        .ok_or_else(|| AppError::BadRequest("请求体必须是 JSON 对象".to_string()))?;
    let rows = if is_add {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("createTime".to_string(), json!(support::now_string()));
        support::insert_entity(&state.db, "sys_dict_type", &entity, AutoFill::NONE).await?
    } else {
        // Java: 先同步 sys_dict_data.dict_type，再更新字典类型。
        let old_type: Option<String> =
            sqlx::query_scalar("select dict_type from sys_dict_type where dict_id = ?")
                .bind(object.get("dictId").cloned().unwrap_or(Value::Null))
                .fetch_optional(&state.db)
                .await?;
        if let Some(old_type) = old_type {
            sqlx::query("update sys_dict_data set dict_type = ? where dict_type = ?")
                .bind(dict_type)
                .bind(old_type)
                .execute(&state.db)
                .await?;
        }
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
        support::update_entity_by_id(
            &state.db,
            "sys_dict_type",
            "dict_id",
            &entity,
            AutoFill::NONE,
        )
        .await?
    };

    if rows > 0 {
        clear_dict_cache(state).await?;
    }
    Ok(support::to_ajax(rows))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save(&state, &user, body, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save(&state, &user, body, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(dict_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&dict_ids);
    for id in &ids {
        let dict_type: Option<String> =
            sqlx::query_scalar("select dict_type from sys_dict_type where dict_id = ?")
                .bind(id)
                .fetch_optional(&state.db)
                .await?;
        if let Some(dict_type) = dict_type {
            let count: i64 =
                sqlx::query_scalar("select count(1) from sys_dict_data where dict_type = ?")
                    .bind(&dict_type)
                    .fetch_one(&state.db)
                    .await?;
            if count > 0 {
                let name: Option<String> =
                    sqlx::query_scalar("select dict_name from sys_dict_type where dict_id = ?")
                        .bind(id)
                        .fetch_optional(&state.db)
                        .await?;
                return Err(AppError::Service(format!(
                    "{}已分配,不能删除",
                    name.unwrap_or_default()
                )));
            }
        }
    }
    let rows = support::delete_by_ids(&state.db, "sys_dict_type", "dict_id", &ids).await?;
    if rows > 0 {
        clear_dict_cache(&state).await?;
    }
    Ok(support::to_ajax(rows))
}

async fn clear_cache(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    clear_dict_cache(&state).await?;
    Ok(AjaxResult::success())
}

pub(crate) async fn clear_dict_cache(state: &AppState) -> Result<(), AppError> {
    for key in state.redis.keys("sys_dict:*").await? {
        state.redis.delete_object(&key).await?;
    }
    Ok(())
}
