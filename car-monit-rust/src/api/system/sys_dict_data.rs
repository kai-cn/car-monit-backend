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

/// Java: SysDictData 的 Jackson 键顺序（BaseEntity 在前）。
const DICT_DATA_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "dictCode",
    "dictSort",
    "dictLabel",
    "dictValue",
    "dictType",
    "cssClass",
    "listClass",
    "isDefault",
    "status",
    "default",
];

/// 缓存里的元素带 FastJson2 的根 `@type`（Jackson 会消费掉，实测 Java 也不输出）。
/// `params` 按 Java 的 `@JsonInclude(NON_EMPTY)` 处理：Map 为空才省略；
/// 实测 Java 读回 Rust 写的缓存后**照样输出** `"params":{"@type":"java.util.HashMap"}`
/// （FastJson2 对 java.util.HashMap 不消费内层 @type），所以这里不能把纯标记当空 Map 丢掉。
fn project_dict_rows(rows: Vec<Value>) -> Vec<Value> {
    rows.into_iter()
        .map(|row| {
            let mut source = row.as_object().cloned().unwrap_or_default();
            source.remove("@type");
            // 实测（6/6 稳定）：命中缓存时 Java 把缓存元素**原样**出参，
            // `params` 里 FastJson2 写的 `{"@type":"java.util.HashMap"}` 也照旧出现在响应里；
            // 走 DB 的那条路径压根没有 params 列，于是 naturally 缺席。
            // 所以这里只按「是不是非空对象」决定带不带，**不剥内部的 @type**。
            let params = source.remove("params").filter(|value| {
                value
                    .as_object()
                    .map(|map| !map.is_empty())
                    .unwrap_or(false)
            });
            let mut out = Map::new();
            for key in DICT_DATA_KEYS {
                if *key == "params" {
                    if let Some(value) = &params {
                        out.insert("params".to_string(), value.clone());
                    }
                    continue;
                }
                out.insert(
                    key.to_string(),
                    source.get(*key).cloned().unwrap_or(Value::Null),
                );
            }
            for (key, value) in source {
                out.entry(key).or_insert(value);
            }
            Value::Object(out)
        })
        .collect()
}

/// 按 dictType 分组（Java 用 Collectors.groupingBy，HashMap 无序；这里保持首次出现顺序）。
fn group_by_dict_type(rows: Vec<Value>) -> Map<String, Value> {
    let mut grouped: Map<String, Value> = Map::new();
    for row in rows {
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
    grouped
}

/// Java: 缓存写入时 FastJson2 会把 params 空 Map 序列化成类型标记。
fn cached_dict_rows(rows: &[Value]) -> Vec<Value> {
    let mut cached = rows.to_vec();
    add_dict_params(&mut cached);
    // 形状照抄 Java 的 FastJson2 输出，否则 Java 读不到实体、会把 @type 透传给前端。
    let cached = support::fastjson_rows(cached);
    crate::db::redis_cache::stamp_types(cached, "com.ruoyi.common.core.domain.entity.SysDictData")
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
            meta::get_route(
                "/system/dict/data/list",
                Some("system:dict:list"),
                None,
                list,
            ),
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
            meta::get_route(
                "/system/dict/data/typemore/{dictType}",
                None,
                None,
                by_type_more,
            ),
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
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, DICT_DATA_KEYS),
    ))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all_fmt(&state.db, &params, &SPEC, FORMATS).await?;
    let headers = [
        "字典编码",
        "字典排序",
        "字典标签",
        "字典键值",
        "字典类型",
        "是否默认",
        "状态",
    ]
    .map(str::to_string);
    let fields = [
        "dictCode",
        "dictSort",
        "dictLabel",
        "dictValue",
        "dictType",
        "isDefault",
        "status",
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
    // Java: `@PathVariable Long dictCode`。
    let dict_code = support::path_long("dictCode", &dict_code)?.to_string();
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &dict_code, FORMATS)
            .await?
            .map(|row| support::reorder_keys(row, DICT_DATA_KEYS)),
    ))
}

async fn by_type(
    State(state): State<AppState>,
    Path(dict_type): Path<String>,
) -> Result<AjaxResult, AppError> {
    let cache_key = format!("sys_dict:{dict_type}");
    if let Some(cached) = state.redis.get_object::<Value>(&cache_key).await? {
        if cached
            .as_array()
            .map(|items| !items.is_empty())
            .unwrap_or(false)
        {
            return Ok(AjaxResult::success_data(project_dict_rows(
                cached.as_array().cloned().unwrap_or_default(),
            )));
        }
    }
    let rows = sqlx::query(BY_TYPE_SQL)
        .bind(&dict_type)
        .fetch_all(&state.db)
        .await?;
    let mut data = crate::db::rows::rows_to_json(&rows);
    support::apply_formats(&mut data, FORMATS);
    let data = project_dict_rows(data);
    if !data.is_empty() {
        // Java: DictTypeServiceImpl 通过 setCacheObject(List<SysDictData>) 写缓存，
        // FastJson2 WriteClassName 为每个元素写 @type；缺少会使 Java 反序列化失败。
        let cached = cached_dict_rows(&data);
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
    // Java: deleteEnd 等价于原样返回（substring(0, length) 不做任何删除），
    // 并且 DictUtils.getDictCache 用的是整个逗号串作 key。
    let cache_key = format!("sys_dict:{types}");
    if let Some(cached) = state.redis.get_object::<Value>(&cache_key).await? {
        if cached
            .as_array()
            .map(|items| !items.is_empty())
            .unwrap_or(false)
        {
            let rows = project_dict_rows(cached.as_array().cloned().unwrap_or_default());
            return Ok(AjaxResult::success_data(group_by_dict_type(rows)));
        }
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
    let data = project_dict_rows(data);
    if !data.is_empty() {
        let cached = cached_dict_rows(&data);
        state.redis.set_object(&cache_key, &cached).await?;
    }
    Ok(AjaxResult::success_data(group_by_dict_type(data)))
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
    // Java: `@PathVariable Long[] dictCodes` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("dictCodes", &dict_codes)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    let rows = support::delete_by_ids(&state.db, "sys_dict_data", "dict_code", &ids).await?;
    if rows > 0 {
        clear_dict_cache(&state).await?;
    }
    Ok(support::to_ajax(rows))
}
