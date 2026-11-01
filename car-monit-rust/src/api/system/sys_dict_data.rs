// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictDataController.java
//       ruoyi-system/src/main/resources/mapper/system/SysDictDataMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictDataServiceImpl.java
// 职责: 字典数据 CRUD、按类型查询（sys_dict:{type} 缓存）。
// 对应关系: list/export/get/type/typemore/add/edit/remove。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Map, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill, FieldFormat, Filter, ListSpec};
use crate::api::system::sys_dict_type::clear_dict_cache;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, \
             is_default, status, create_by, create_time, remark, \
             null as updateBy, null as updateTime, \
             case when is_default = 'Y' then 1 else 0 end as `default`",
    from: "from sys_dict_data",
    filters: &[
        Filter::eq("dictType", "dict_type"),
        Filter::like("dictLabel", "dict_label"),
        Filter::eq("status", "status"),
    ],
    extra_where: "",
    order_by: "dict_sort asc",
    id_column: "dict_code",
};

// Java: `default` 是 boolean getter。
const FORMATS: &[(&str, FieldFormat)] = &[("default", FieldFormat::Bool)];

fn add_dict_params(rows: &mut [Value]) {
    for row in rows {
        if let Some(object) = row.as_object_mut() {
            object.insert(
                "params".to_string(),
                serde_json::json!({ "@type": "java.util.HashMap" }),
            );
        }
    }
}

const BY_TYPE_SQL: &str = "select dict_code, dict_sort, dict_label, dict_value, dict_type, \
     css_class, list_class, is_default, status, create_by, create_time, remark, \
     null as updateBy, null as updateTime, \
     case when is_default = 'Y' then 1 else 0 end as `default` \
     from sys_dict_data where status = '0' and dict_type = ? order by dict_sort asc";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "字典数据",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysDictDataController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "字典数据",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysDictDataController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "字典数据",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysDictDataController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "字典数据",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysDictDataController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/dict/data/list",
            meta::get_route("/system/dict/data/list", Some("system:dict:list"), None, list),
        )
        .route(
            "/system/dict/data/export",
            meta::get_route(
                "/system/dict/data/export",
                Some("system:dict:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/dict/data/type/{dictType}",
            meta::get_route("/system/dict/data/type/{dictType}", None, None, by_type),
        )
        .route(
            "/system/dict/data/typemore/{dictType}",
            meta::get_route("/system/dict/data/typemore/{dictType}", None, None, by_type_more),
        )
        .route(
            "/system/dict/data/{dictCodes}",
            meta::get_route(
                "/system/dict/data/{dictCodes}",
                Some("system:dict:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/system/dict/data",
            meta::post_route(
                "/system/dict/data",
                Some("system:dict:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/system/dict/data",
                Some("system:dict:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/system/dict/data/{dictCodes}",
            meta::delete_route(
                "/system/dict/data/{dictCodes}",
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
    let (total, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all_fmt(&state.db, &params, &SPEC, FORMATS).await?;
    let headers = [
        "字典编码", "字典排序", "字典标签", "字典键值", "字典类型", "是否默认", "状态",
    ]
    .map(str::to_string);
    let fields = [
        "dictCode", "dictSort", "dictLabel", "dictValue", "dictType", "isDefault", "status",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            for index in [5usize, 6] {
                if let Some(Value::String(text)) = values.get(index).cloned() {
                    values[index] = Value::String(match text.as_str() {
                        "Y" if index == 5 => "是".to_string(),
                        "N" if index == 5 => "否".to_string(),
                        "0" if index == 6 => "正常".to_string(),
                        "1" if index == 6 => "停用".to_string(),
                        _ => text,
                    });
                }
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "字典数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(dict_code): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &dict_code, FORMATS).await?,
    ))
}

async fn by_type(
    State(state): State<AppState>,
    Path(dict_type): Path<String>,
) -> Result<AjaxResult, AppError> {
    let cache_key = format!("sys_dict:{dict_type}");
    if let Some(mut cached) = state.redis.get_object::<Value>(&cache_key).await? {
        if cached.as_array().map(|items| !items.is_empty()).unwrap_or(false) {
            crate::db::redis_cache::strip_type(&mut cached);
            return Ok(AjaxResult::success_data(cached));
        }
    }
    let rows = sqlx::query(BY_TYPE_SQL)
        .bind(&dict_type)
        .fetch_all(&state.db)
        .await?;
    let mut data = crate::db::rows::rows_to_json(&rows);
    support::apply_formats(&mut data, FORMATS);
    add_dict_params(&mut data);
    if !data.is_empty() {
        // Java: DictTypeServiceImpl 通过 setCacheObject(List<SysDictData>) 写缓存，
        // FastJson2 WriteClassName 为每个元素写 @type；缺少会使 Java 反序列化失败。
        let cached = crate::db::redis_cache::stamp_types(
            data.clone(),
            "com.ruoyi.common.core.domain.entity.SysDictData",
        );
        state.redis.set_object(&cache_key, &cached).await?;
        return Ok(AjaxResult::success_data(data));
    }
    Ok(AjaxResult::success_data(Vec::<Value>::new()))
}

async fn by_type_more(
    State(state): State<AppState>,
    Path(dict_type): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java 的 deleteEnd 等价于原样返回（substring(0, length) 不做任何删除）。
    let mut types = dict_type.trim().to_string();
    if types.is_empty() {
        types = "-dadadadas".to_string();
    }
    let names: Vec<&str> = types.split(',').collect();
    let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new(
        "select dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, \
         is_default, status, create_by, create_time, remark, null as updateBy, \
         null as updateTime, case when is_default = 'Y' then 1 else 0 end as `default` \
         from sys_dict_data where status = '0' and dict_type in (",
    );
    let mut separated = builder.separated(", ");
    for name in &names {
        separated.push_bind(name.to_string());
    }
    builder.push(") order by dict_type, dict_sort asc");
    let rows = builder.build().fetch_all(&state.db).await?;
    let mut data = crate::db::rows::rows_to_json(&rows);
    support::apply_formats(&mut data, FORMATS);

    let mut grouped: Map<String, Value> = Map::new();
    for row in data {
        let key = row
            .get("dictType")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let entry = grouped
            .entry(key)
            .or_insert_with(|| Value::Array(Vec::new()));
        if let Some(items) = entry.as_array_mut() {
            items.push(row);
        }
    }
    Ok(AjaxResult::success_data(grouped))
}

async fn save(
    state: &AppState,
    user: &LoginUser,
    body: Value,
    is_add: bool,
) -> Result<AjaxResult, AppError> {
    for (key, message) in [
        ("dictType", "字典类型不能为空"),
        ("dictLabel", "字典标签不能为空"),
        ("dictValue", "字典键值不能为空"),
    ] {
        let value = body.get(key).and_then(Value::as_str).unwrap_or_default();
        if value.trim().is_empty() {
            return Ok(AjaxResult::error(message));
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
        support::insert_entity(&state.db, "sys_dict_data", &entity, AutoFill::NONE).await?
    } else {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
        support::update_entity_by_id(
            &state.db,
            "sys_dict_data",
            "dict_code",
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
    Path(dict_codes): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&dict_codes);
    let rows = support::delete_by_ids(&state.db, "sys_dict_data", "dict_code", &ids).await?;
    if rows > 0 {
        clear_dict_cache(&state).await?;
    }
    Ok(support::to_ajax(rows))
}
