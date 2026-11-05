// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java
//       ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysConfigServiceImpl.java
// 职责: 参数配置 CRUD + sys_config:{key} 缓存。
// 对应关系: select/insert/update/delete/clearCache -> SPEC + 自定义保存。

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
    select: "config_id, config_name, config_key, config_value, config_type, create_by, \
             create_time, update_by, update_time, remark",
    from: "from sys_config",
    filters: &[
        Filter::like("configName", "config_name"),
        Filter::eq("configType", "config_type"),
        Filter::like("configKey", "config_key"),
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
    order_by: "",
    id_column: "config_id",
};

const CACHE_PREFIX: &str = "sys_config:";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "参数管理",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysConfigController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "参数管理",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysConfigController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "参数管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysConfigController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "参数管理",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysConfigController.remove()",
);
static LOG_CLEAR: LogSpec = LogSpec::new(
    "参数管理",
    BusinessType::Clean,
    "com.ruoyi.web.controller.system.SysConfigController.clearCache()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/config/list",
            meta::get_route(
                "/system/config/list",
                Some("system:config:list"),
                None,
                list,
            ),
        )
        .route(
            "/system/config/export",
            meta::get_route(
                "/system/config/export",
                Some("system:config:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/config/configKey/{configKey}",
            meta::get_route(
                "/system/config/configKey/{configKey}",
                None,
                None,
                get_config_key,
            ),
        )
        .route(
            "/system/config/clearCache",
            meta::delete_route(
                "/system/config/clearCache",
                Some("system:config:remove"),
                Some(&LOG_CLEAR),
                clear_cache,
            ),
        )
        .route(
            "/system/config/{configIds}",
            meta::get_route(
                "/system/config/{configIds}",
                Some("system:config:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/system/config",
            meta::post_route(
                "/system/config",
                Some("system:config:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/system/config",
                Some("system:config:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/system/config/{configIds}",
            meta::delete_route(
                "/system/config/{configIds}",
                Some("system:config:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java Jackson 的 SysConfig 键序：BaseEntity 在前（含 params），再按声明顺序。
const CONFIG_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "configId",
    "configName",
    "configKey",
    "configValue",
    "configType",
];

fn shape_config_rows(rows: Vec<Value>) -> Vec<Value> {
    support::reorder_rows(rows, CONFIG_KEYS)
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, shape_config_rows(rows)))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = ["参数主键", "参数名称", "参数键名", "参数键值", "系统内置"].map(str::to_string);
    let fields = [
        "configId",
        "configName",
        "configKey",
        "configValue",
        "configType",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            // @Excel(readConverterExp = "Y=是,N=否")
            if let Some(Value::String(text)) = values.get(4).cloned() {
                values[4] = Value::String(match text.as_str() {
                    "Y" => "是".to_string(),
                    "N" => "否".to_string(),
                    _ => text,
                });
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "参数数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(config_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long configId` —— 非数字在进控制器前就被 Spring 拦下。
    let config_id = support::path_long("configId", &config_id)?.to_string();
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &config_id)
            .await?
            .map(|row| shape_config_rows(vec![row]).pop().unwrap_or(Value::Null)),
    ))
}

async fn get_config_key(
    State(state): State<AppState>,
    Path(config_key): Path<String>,
) -> Result<AjaxResult, AppError> {
    let cache_key = format!("{CACHE_PREFIX}{config_key}");
    if let Some(cached) = state.redis.get_object::<Value>(&cache_key).await? {
        let text = match cached {
            Value::String(text) => text,
            other => other.to_string(),
        };
        if !text.is_empty() {
            return Ok(AjaxResult::success_msg(text));
        }
    }
    let value: Option<String> =
        sqlx::query_scalar("select config_value from sys_config where config_key = ?")
            .bind(&config_key)
            .fetch_optional(&state.db)
            .await?;
    match value {
        Some(value) => {
            state.redis.set_object(&cache_key, &value).await?;
            // Java 重载解析命中 success(String msg)：值放在 msg 上，没有 data。
            Ok(AjaxResult::success_msg(value))
        }
        None => Ok(AjaxResult::success_msg("")),
    }
}

async fn unique_error(
    state: &AppState,
    body: &Value,
    verb: &str,
) -> Result<Option<AjaxResult>, AppError> {
    let key = body
        .get("configKey")
        .and_then(Value::as_str)
        .unwrap_or_default();
    if key.is_empty() {
        return Ok(None);
    }
    let found: Option<i64> =
        sqlx::query_scalar("select config_id from sys_config where config_key = ? limit 1")
            .bind(key)
            .fetch_optional(&state.db)
            .await?;
    let current = body.get("configId").and_then(Value::as_i64).unwrap_or(-1);
    if let Some(found) = found {
        if found != current {
            let name = body
                .get("configName")
                .and_then(Value::as_str)
                .unwrap_or_default();
            return Ok(Some(AjaxResult::error(format!(
                "{verb}参数'{name}'失败，参数键名已存在"
            ))));
        }
    }
    Ok(None)
}

async fn save(
    state: &AppState,
    user: &LoginUser,
    body: Value,
    is_add: bool,
) -> Result<AjaxResult, AppError> {
    for (key, message) in [
        ("configName", "参数名称不能为空"),
        ("configKey", "参数键名不能为空"),
    ] {
        let value = body.get(key).and_then(Value::as_str).unwrap_or_default();
        if value.trim().is_empty() {
            return Ok(AjaxResult::error(message));
        }
    }
    let verb = if is_add { "新增" } else { "修改" };
    if let Some(error) = unique_error(state, &body, verb).await? {
        return Ok(error);
    }

    let mut entity = body;
    let config_key = entity
        .get("configKey")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let config_value = entity
        .get("configValue")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let object = entity
        .as_object_mut()
        .ok_or_else(|| AppError::BadRequest("请求体必须是 JSON 对象".to_string()))?;
    let rows = if is_add {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("createTime".to_string(), json!(support::now_string()));
        support::insert_entity(&state.db, "sys_config", &entity, AutoFill::NONE).await?
    } else {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
        support::update_entity_by_id(
            &state.db,
            "sys_config",
            "config_id",
            &entity,
            AutoFill::NONE,
        )
        .await?
    };

    if rows > 0 && !config_key.is_empty() {
        state
            .redis
            .set_object(&format!("{CACHE_PREFIX}{config_key}"), &config_value)
            .await?;
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
    Path(config_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] configIds` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("configIds", &config_ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    for id in &ids {
        let config_type: Option<String> =
            sqlx::query_scalar("select config_type from sys_config where config_id = ?")
                .bind(id)
                .fetch_optional(&state.db)
                .await?;
        if config_type.as_deref() == Some("Y") {
            let key: Option<String> =
                sqlx::query_scalar("select config_key from sys_config where config_id = ?")
                    .bind(id)
                    .fetch_optional(&state.db)
                    .await?;
            return Err(AppError::Service(format!(
                "内置参数【{}】不能删除 ",
                key.unwrap_or_default()
            )));
        }
    }
    let rows = support::delete_by_ids(&state.db, "sys_config", "config_id", &ids).await?;
    if rows > 0 {
        clear_cache_keys(&state).await?;
    }
    Ok(support::to_ajax(rows))
}

async fn clear_cache(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    clear_cache_keys(&state).await?;
    Ok(AjaxResult::success())
}

async fn clear_cache_keys(state: &AppState) -> Result<(), AppError> {
    for key in state.redis.keys(&format!("{CACHE_PREFIX}*")).await? {
        state.redis.delete_object(&key).await?;
    }
    Ok(())
}
