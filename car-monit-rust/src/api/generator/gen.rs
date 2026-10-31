// 来源: ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java
//       ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java
//       ruoyi-generator/src/main/resources/mapper/generator/*.xml
// 职责: 代码生成器元数据（gen_table/gen_table_column）管理。
// 说明: preview/download/genCode/batchGenCode 依赖 Apache Velocity 模板引擎；
//       Rust 版本暂未内置模板渲染，返回明确错误（见 README-MIGRATION.md）。

use std::collections::HashMap;

use axum::extract::{Path, Query, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Map, Value};
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const TABLE_COLUMNS: &str = "table_id, table_name, table_comment, sub_table_name, \
     sub_table_fk_name, class_name, tpl_category, package_name, module_name, business_name, \
     function_name, function_author, gen_type, gen_path, options, create_by, create_time, \
     update_by, update_time, remark";

const COLUMN_COLUMNS: &str = "column_id, table_id, column_name, column_comment, column_type, \
     java_type, java_field, is_pk, is_increment, is_required, is_insert, is_edit, is_list, \
     is_query, query_type, html_type, dict_type, sort, create_by, create_time, update_by, \
     update_time, link_table_id, single_selection, multiple_selections, \
     dialog_search_column_ids, dialog_list_column_ids, field_map_string";

const GEN_AUTHOR: &str = "ruoyi";
const GEN_PACKAGE: &str = "com.ruoyi.manager";

const SPEC: ListSpec = ListSpec {
    select: TABLE_COLUMNS,
    from: "from gen_table",
    filters: &[
        Filter::raw("tableName", " and lower(table_name) like lower(concat('%', ?, '%'))"),
        Filter::raw(
            "tableComment",
            " and lower(table_comment) like lower(concat('%', ?, '%'))",
        ),
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
    order_by: "create_time DESC",
    id_column: "table_id",
};

static LOG_IMPORT: LogSpec = LogSpec::new(
    "代码生成",
    BusinessType::Import,
    "com.ruoyi.generator.controller.GenController.importTableSave()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "代码生成",
    BusinessType::Update,
    "com.ruoyi.generator.controller.GenController.editSave()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "代码生成",
    BusinessType::Delete,
    "com.ruoyi.generator.controller.GenController.remove()",
);
static LOG_GEN: LogSpec = LogSpec::new(
    "代码生成",
    BusinessType::Gencode,
    "com.ruoyi.generator.controller.GenController.genCode()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/tool/gen/list",
            meta::get_route("/tool/gen/list", Some("tool:gen:list"), None, list),
        )
        .route(
            "/tool/gen/all/list",
            meta::get_route("/tool/gen/all/list", None, None, all_list),
        )
        .route(
            "/tool/gen/db/list",
            meta::get_route("/tool/gen/db/list", Some("tool:gen:list"), None, db_list),
        )
        .route(
            "/tool/gen/column/{tableId}",
            meta::get_route("/tool/gen/column/{tableId}", Some("tool:gen:list"), None, column_list),
        )
        .route(
            "/tool/gen/getColumnList",
            meta::post_route("/tool/gen/getColumnList", None, None, get_column_list),
        )
        .route(
            "/tool/gen/getAllColumnList",
            meta::post_route("/tool/gen/getAllColumnList", None, None, get_all_column_list),
        )
        .route(
            "/tool/gen/importTable",
            meta::post_route(
                "/tool/gen/importTable",
                Some("tool:gen:list"),
                Some(&LOG_IMPORT),
                import_table,
            ),
        )
        .route(
            "/tool/gen/preview/{tableId}",
            meta::get_route("/tool/gen/preview/{tableId}", Some("tool:gen:preview"), None, preview),
        )
        .route(
            "/tool/gen/download/{tableName}",
            meta::get_route(
                "/tool/gen/download/{tableName}",
                Some("tool:gen:code"),
                Some(&LOG_GEN),
                download,
            ),
        )
        .route(
            "/tool/gen/genCode/{tableName}",
            meta::get_route(
                "/tool/gen/genCode/{tableName}",
                Some("tool:gen:code"),
                Some(&LOG_GEN),
                gen_code,
            ),
        )
        .route(
            "/tool/gen/batchGenCode",
            meta::get_route(
                "/tool/gen/batchGenCode",
                Some("tool:gen:code"),
                Some(&LOG_GEN),
                batch_gen_code,
            ),
        )
        .route(
            "/tool/gen/synchDb/{tableName}",
            meta::get_route(
                "/tool/gen/synchDb/{tableName}",
                Some("tool:gen:edit"),
                None,
                synch_db,
            ),
        )
        .route(
            "/tool/gen/{tableIds}",
            meta::get_route("/tool/gen/{tableIds}", Some("tool:gen:query"), None, get_info),
        )
        .route(
            "/tool/gen",
            meta::put_route("/tool/gen", Some("tool:gen:edit"), Some(&LOG_EDIT), edit_save),
        )
        .route(
            "/tool/gen/{tableIds}",
            meta::delete_route(
                "/tool/gen/{tableIds}",
                Some("tool:gen:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

fn camel_case(value: &str, capitalize_first: bool) -> String {
    let mut out = String::new();
    let mut upper = capitalize_first;
    for ch in value.chars() {
        if ch == '_' {
            upper = true;
            continue;
        }
        if upper {
            out.extend(ch.to_uppercase());
            upper = false;
        } else {
            out.push(ch);
        }
    }
    out
}

fn business_name(table_name: &str) -> String {
    table_name.rsplit('_').next().unwrap_or(table_name).to_string()
}

fn module_name() -> String {
    GEN_PACKAGE.rsplit('.').next().unwrap_or_default().to_string()
}

fn function_name(comment: &str) -> String {
    comment.replace('表', "").replace("若依", "")
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

async fn all_list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    Ok(AjaxResult::success_data(
        support::query_all(&state.db, &params, &SPEC).await?,
    ))
}

fn push_db_table_filters(builder: &mut QueryBuilder<'_, MySql>, params: &HashMap<String, String>) {
    if let Some(value) = params.get("tableName").filter(|value| !value.is_empty()) {
        builder.push(" and lower(table_name) like lower(concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%'))");
    }
    if let Some(value) = params.get("tableComment").filter(|value| !value.is_empty()) {
        builder.push(" and lower(table_comment) like lower(concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%'))");
    }
    if let Some(value) = params.get("params[beginTime]").filter(|value| !value.is_empty()) {
        builder.push(" and date_format(create_time,'%y%m%d') >= date_format(");
        builder.push_bind(value.clone());
        builder.push(", '%y%m%d')");
    }
    if let Some(value) = params.get("params[endTime]").filter(|value| !value.is_empty()) {
        builder.push(" and date_format(create_time,'%y%m%d') <= date_format(");
        builder.push_bind(value.clone());
        builder.push(", '%y%m%d')");
    }
}

async fn db_list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let mut builder = QueryBuilder::<MySql>::new(
        "select table_name, table_comment, create_time, update_time from information_schema.tables \
         where table_schema = (select database()) and table_name not like 'qrtz_%' \
         and table_name not like 'gen_%' and table_name not in (select table_name from gen_table)",
    );
    push_db_table_filters(&mut builder, &params);
    let mut count_builder = QueryBuilder::<MySql>::new(
        "select count(0) from information_schema.tables          where table_schema = (select database()) and table_name not like 'qrtz_%'          and table_name not like 'gen_%' and table_name not in (select table_name from gen_table)",
    );
    push_db_table_filters(&mut count_builder, &params);
    let total: i64 = count_builder.build_query_scalar().fetch_one(&state.db).await?;
    let (offset, limit) = page.resolve(total);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(TableDataInfo::new(total, crate::db::rows::rows_to_json(&rows)))
}

async fn column_list(
    State(state): State<AppState>,
    Path(_table_id): Path<String>,
    Query(query): Query<HashMap<String, String>>,
) -> Result<TableDataInfo<Value>, AppError> {
    // Java: 路径变量拼写为 {talbleId}，真正取值来自 query 的 tableId。
    let table_id = query.get("tableId").cloned().unwrap_or_default();
    let rows = select_columns(&state.db, &table_id).await?;
    Ok(TableDataInfo::new(rows.len() as i64, rows))
}

async fn select_columns(pool: &MySqlPool, table_id: &str) -> Result<Vec<Value>, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {COLUMN_COLUMNS} from gen_table_column where table_id = "
    ));
    builder.push_bind(table_id.to_string());
    builder.push(" order by sort");
    let rows = builder.build().fetch_all(pool).await?;
    Ok(crate::db::rows::rows_to_json(&rows))
}

async fn get_column_list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
    Json(body): Json<Value>,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {COLUMN_COLUMNS} from gen_table_column where 1=1"
    ));
    if let Some(table_id) = body.get("tableId").filter(|value| !value.is_null()) {
        builder.push(" and table_id = ");
        builder.push_bind(table_id.to_string().trim_matches('"').to_string());
    }
    if let Some(value) = body.get("columnName").and_then(Value::as_str).filter(|v| !v.is_empty()) {
        builder.push(" and column_name like concat('%', ");
        builder.push_bind(value.to_string());
        builder.push(", '%')");
    }
    if let Some(value) = body.get("javaField").and_then(Value::as_str).filter(|v| !v.is_empty()) {
        builder.push(" and java_field like concat('%', ");
        builder.push_bind(value.to_string());
        builder.push(", '%')");
    }
    let mut count_builder =
        QueryBuilder::<MySql>::new("select count(0) from gen_table_column where 1=1");
    if let Some(table_id) = body.get("tableId").filter(|value| !value.is_null()) {
        count_builder.push(" and table_id = ");
        count_builder.push_bind(table_id.to_string().trim_matches('"').to_string());
    }
    if let Some(value) = body.get("columnName").and_then(Value::as_str).filter(|v| !v.is_empty()) {
        count_builder.push(" and column_name like concat('%', ");
        count_builder.push_bind(value.to_string());
        count_builder.push(", '%')");
    }
    if let Some(value) = body.get("javaField").and_then(Value::as_str).filter(|v| !v.is_empty()) {
        count_builder.push(" and java_field like concat('%', ");
        count_builder.push_bind(value.to_string());
        count_builder.push(", '%')");
    }
    let total: i64 = count_builder.build_query_scalar().fetch_one(&state.db).await?;
    let (offset, limit) = page.resolve(total);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(TableDataInfo::new(total, crate::db::rows::rows_to_json(&rows)))
}

async fn get_all_column_list(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let ids = body
        .get("dialogSearchColumnIds")
        .and_then(Value::as_str)
        .or_else(|| body.get("dialogListColumnIds").and_then(Value::as_str))
        .unwrap_or_default()
        .to_string();
    if ids.is_empty() {
        return Ok(AjaxResult::success_data(Vec::<Value>::new()));
    }
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {COLUMN_COLUMNS} from gen_table_column where column_id in ("
    ));
    let mut separated = builder.separated(", ");
    for id in ids.split(',').filter(|item| !item.is_empty()) {
        separated.push_bind(id.to_string());
    }
    builder.push(") order by sort");
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(AjaxResult::success_data(crate::db::rows::rows_to_json(&rows)))
}

async fn get_info(
    State(state): State<AppState>,
    Path(table_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let table = support::query_by_id(&state.db, &SPEC, &table_id).await?;
    let rows = select_columns(&state.db, &table_id).await?;
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select t.table_name, t.table_comment from gen_table t order by t.create_time desc"
    ));
    let tables = builder.build().fetch_all(&state.db).await?;
    let mut map = Map::new();
    map.insert("info".to_string(), table.unwrap_or(Value::Null));
    map.insert("rows".to_string(), json!(rows));
    map.insert("tables".to_string(), json!(crate::db::rows::rows_to_json(&tables)));
    Ok(AjaxResult::success_data(map))
}

/// Java: GenUtils.initTable。
fn init_table_body(table_name: &str, table_comment: &str, oper_name: &str) -> Map<String, Value> {
    let mut map = Map::new();
    map.insert("tableName".to_string(), json!(table_name));
    map.insert("tableComment".to_string(), json!(table_comment));
    map.insert(
        "className".to_string(),
        json!(camel_case(table_name, true)),
    );
    map.insert("packageName".to_string(), json!(GEN_PACKAGE));
    map.insert("moduleName".to_string(), json!(module_name()));
    map.insert("businessName".to_string(), json!(business_name(table_name)));
    map.insert("functionName".to_string(), json!(function_name(table_comment)));
    map.insert("functionAuthor".to_string(), json!(GEN_AUTHOR));
    map.insert("createBy".to_string(), json!(oper_name));
    map
}

/// Java: GenUtils.initColumnField。
fn init_column(row: &Value, table_id: i64, create_by: &str) -> Map<String, Value> {
    let column_name = row.get("columnName").and_then(Value::as_str).unwrap_or_default();
    let column_type = row.get("columnType").and_then(Value::as_str).unwrap_or_default();
    let data_type = column_type
        .split('(')
        .next()
        .unwrap_or_default()
        .trim()
        .to_lowercase();
    let mut map = Map::new();
    map.insert("tableId".to_string(), json!(table_id));
    map.insert("columnName".to_string(), json!(column_name));
    map.insert(
        "columnComment".to_string(),
        row.get("columnComment").cloned().unwrap_or(Value::Null),
    );
    map.insert("columnType".to_string(), json!(column_type));
    map.insert("sort".to_string(), row.get("sort").cloned().unwrap_or(Value::Null));
    map.insert("isPk".to_string(), row.get("isPk").cloned().unwrap_or(Value::Null));
    map.insert(
        "isIncrement".to_string(),
        row.get("isIncrement").cloned().unwrap_or(Value::Null),
    );
    map.insert(
        "isRequired".to_string(),
        row.get("isRequired").cloned().unwrap_or(Value::Null),
    );
    map.insert("createBy".to_string(), json!(create_by));
    map.insert(
        "javaField".to_string(),
        json!(camel_case(column_name, false)),
    );
    map.insert("javaType".to_string(), json!("String"));
    map.insert("isInsert".to_string(), json!("1"));

    let str_types = ["char", "varchar", "nvarchar", "varchar2"];
    let text_types = ["tinytext", "text", "mediumtext", "longtext"];
    let time_types = ["datetime", "time", "date", "timestamp"];
    let number_types = [
        "tinyint", "smallint", "mediumint", "int", "number", "integer", "bit", "bigint", "float",
        "double", "decimal",
    ];
    if str_types.contains(&data_type.as_str()) || text_types.contains(&data_type.as_str()) {
        let length = column_type
            .split('(')
            .nth(1)
            .and_then(|rest| rest.split(')').next())
            .and_then(|value| value.split(',').next())
            .and_then(|value| value.trim().parse::<i32>().ok())
            .unwrap_or(0);
        let html = if length >= 500 || text_types.contains(&data_type.as_str()) {
            "textarea"
        } else {
            "input"
        };
        map.insert("htmlType".to_string(), json!(html));
    } else if time_types.contains(&data_type.as_str()) {
        map.insert("javaType".to_string(), json!("Date"));
        map.insert("htmlType".to_string(), json!("datetime"));
    } else if number_types.contains(&data_type.as_str()) {
        map.insert("htmlType".to_string(), json!("input"));
        let spec = column_type
            .split('(')
            .nth(1)
            .and_then(|rest| rest.split(')').next())
            .unwrap_or_default();
        let parts = spec.split(',').collect::<Vec<_>>();
        if parts.len() == 2 && parts[1].trim().parse::<i32>().unwrap_or(0) > 0 {
            map.insert("javaType".to_string(), json!("BigDecimal"));
        } else if parts.len() == 1 && parts[0].trim().parse::<i32>().unwrap_or(999) <= 10 {
            map.insert("javaType".to_string(), json!("Integer"));
        } else {
            map.insert("javaType".to_string(), json!("Long"));
        }
    }

    let is_pk = row.get("isPk").and_then(Value::as_str) == Some("1");
    let not_edit = ["id", "create_by", "create_time", "del_flag"];
    let not_list = ["id", "create_by", "create_time", "del_flag", "update_by", "update_time"];
    let not_query = [
        "id",
        "create_by",
        "create_time",
        "del_flag",
        "update_by",
        "update_time",
        "remark",
    ];
    if !not_edit.contains(&column_name) && !is_pk {
        map.insert("isEdit".to_string(), json!("1"));
    }
    if !not_list.contains(&column_name) && !is_pk {
        map.insert("isList".to_string(), json!("1"));
    }
    if !not_query.contains(&column_name) && !is_pk {
        map.insert("isQuery".to_string(), json!("1"));
    }
    let lower = column_name.to_lowercase();
    if lower.ends_with("name") {
        map.insert("queryType".to_string(), json!("LIKE"));
    }
    if lower.ends_with("status") {
        map.insert("htmlType".to_string(), json!("radio"));
    } else if lower.ends_with("type") || lower.ends_with("sex") {
        map.insert("htmlType".to_string(), json!("select"));
    } else if lower.ends_with("image") {
        map.insert("htmlType".to_string(), json!("imageUpload"));
    } else if lower.ends_with("file") {
        map.insert("htmlType".to_string(), json!("fileUpload"));
    } else if lower.ends_with("content") {
        map.insert("htmlType".to_string(), json!("editor"));
    }
    map
}

async fn import_table(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
    body: String,
) -> Result<AjaxResult, AppError> {
    // Spring 的 String 形参可以来自 query，也可以来自 form 表单。
    let mut params = support::query_map(&raw);
    if !params.contains_key("tables") {
        for (key, value) in url::form_urlencoded::parse(body.as_bytes()) {
            params.insert(key.into_owned(), value.into_owned());
        }
    }
    let tables = params.get("tables").cloned().unwrap_or_default();
    let oper_name = user.user.user_name.clone().unwrap_or_default();
    for name in tables.split(',').filter(|name| !name.is_empty()) {
        let db_table = sqlx::query(
            "select table_name, table_comment from information_schema.tables \
             where table_schema = (select database()) and table_name = ?",
        )
        .bind(name)
        .fetch_optional(&state.db)
        .await?;
        let Some(db_table) = db_table else { continue };
        let table_name: String = sqlx::Row::try_get(&db_table, "table_name").unwrap_or_default();
        let table_comment: Option<String> =
            sqlx::Row::try_get(&db_table, "table_comment").unwrap_or_default();
        let comment = table_comment.unwrap_or_default();

        let mut entity = init_table_body(&table_name, &comment, &oper_name);
        entity.insert("createTime".to_string(), json!(support::now_string()));

        let mut tx = state.db.begin().await?;
        let mut builder = QueryBuilder::<MySql>::new("insert into gen_table (");
        let mut first = true;
        for key in entity.keys() {
            if !first {
                builder.push(", ");
            }
            first = false;
            builder.push(support::column_name(key));
        }
        builder.push(") values (");
        let mut first = true;
        for value in entity.values() {
            if !first {
                builder.push(", ");
            }
            first = false;
            support::bind_value(&mut builder, value);
        }
        builder.push(")");
        builder.build().execute(&mut *tx).await?;
        let table_id: i64 = sqlx::query_scalar("select last_insert_id()")
            .fetch_one(&mut *tx)
            .await?;

        let columns = sqlx::query(
            "select column_name, column_comment, column_type, \
             (case when (is_nullable = 'no' && column_key != 'PRI') then '1' else null end) as is_required, \
             (case when column_key = 'PRI' then '1' else '0' end) as is_pk, \
             ordinal_position as sort, \
             (case when extra = 'auto_increment' then '1' else '0' end) as is_increment \
             from information_schema.columns \
             where table_schema = (select database()) and table_name = ? order by ordinal_position",
        )
        .bind(&table_name)
        .fetch_all(&mut *tx)
        .await?;
        for row in columns.iter() {
            let value = crate::db::rows::row_to_json(row);
            let column = init_column(&value, table_id, &oper_name);
            let mut builder = QueryBuilder::<MySql>::new("insert into gen_table_column (");
            let mut first = true;
            for key in column.keys() {
                if !first {
                    builder.push(", ");
                }
                first = false;
                builder.push(support::column_name(key));
            }
            builder.push(") values (");
            let mut first = true;
            for value in column.values() {
                if !first {
                    builder.push(", ");
                }
                first = false;
                support::bind_value(&mut builder, value);
            }
            builder.push(")");
            builder.build().execute(&mut *tx).await?;
        }
        tx.commit().await?;
    }
    Ok(AjaxResult::success())
}

async fn edit_save(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let mut table = body.clone();
    if let Some(object) = table.as_object_mut() {
        object.remove("columns");
        object.remove("params");
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
    }
    support::update_entity_by_id(&state.db, "gen_table", "table_id", &table, support::AutoFill::NONE)
        .await?;

    if let Some(columns) = body.get("columns").and_then(Value::as_array) {
        for column in columns {
            let Some(column_id) = column.get("columnId").and_then(Value::as_i64) else {
                continue;
            };
            let mut entity = column.clone();
            if let Some(object) = entity.as_object_mut() {
                object.insert(
                    "updateBy".to_string(),
                    Value::String(user.user.user_name.clone().unwrap_or_default()),
                );
                object.insert("updateTime".to_string(), json!(support::now_string()));
            }
            let _ = column_id;
            support::update_entity_by_id(
                &state.db,
                "gen_table_column",
                "column_id",
                &entity,
                support::AutoFill::NONE,
            )
            .await?;
        }
    }
    Ok(support::to_ajax(1))
}

async fn remove(
    State(state): State<AppState>,
    Path(table_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&table_ids);
    for id in &ids {
        sqlx::query("delete from gen_table_column where table_id = ?")
            .bind(id)
            .execute(&state.db)
            .await?;
    }
    let rows = support::delete_by_ids(&state.db, "gen_table", "table_id", &ids).await?;
    Ok(support::to_ajax(rows))
}

async fn synch_db(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Path(table_name): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: 同步数据库字段（保留已配置的列，新增缺失列）。
    let table_id: Option<i64> =
        sqlx::query_scalar("select table_id from gen_table where table_name = ?")
            .bind(&table_name)
            .fetch_optional(&state.db)
            .await?;
    let Some(table_id) = table_id else {
        return Ok(AjaxResult::error("同步数据失败，原表结构不存在"));
    };
    let existing: Vec<String> =
        sqlx::query_scalar("select column_name from gen_table_column where table_id = ?")
            .bind(table_id)
            .fetch_all(&state.db)
            .await?;
    let columns = sqlx::query(
        "select column_name, column_comment, column_type, \
         (case when (is_nullable = 'no' && column_key != 'PRI') then '1' else null end) as is_required, \
         (case when column_key = 'PRI' then '1' else '0' end) as is_pk, \
         ordinal_position as sort, \
         (case when extra = 'auto_increment' then '1' else '0' end) as is_increment \
         from information_schema.columns \
         where table_schema = (select database()) and table_name = ? order by ordinal_position",
    )
    .bind(&table_name)
    .fetch_all(&state.db)
    .await?;
    let oper_name = user.user.user_name.clone().unwrap_or_default();
    for row in columns.iter() {
        let value = crate::db::rows::row_to_json(row);
        let name = value
            .get("columnName")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        if existing.contains(&name) {
            continue;
        }
        let column = init_column(&value, table_id, &oper_name);
        support::insert_entity(
            &state.db,
            "gen_table_column",
            &Value::Object(column),
            support::AutoFill::NONE,
        )
        .await?;
    }
    Ok(AjaxResult::success())
}

async fn preview(
    State(_state): State<AppState>,
    Path(_table_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Err(AppError::Service(
        "代码预览依赖 Velocity 模板引擎，Rust 迁移版本暂未提供".to_string(),
    ))
}

async fn download(
    State(_state): State<AppState>,
    Path(_table_name): Path<String>,
) -> Result<AjaxResult, AppError> {
    Err(AppError::Service(
        "代码下载依赖 Velocity 模板引擎，Rust 迁移版本暂未提供".to_string(),
    ))
}

async fn gen_code(
    State(_state): State<AppState>,
    Path(_table_name): Path<String>,
) -> Result<AjaxResult, AppError> {
    Err(AppError::Service(
        "代码生成依赖 Velocity 模板引擎，Rust 迁移版本暂未提供".to_string(),
    ))
}

async fn batch_gen_code(
    State(_state): State<AppState>,
    Query(_params): Query<HashMap<String, String>>,
) -> Result<AjaxResult, AppError> {
    Err(AppError::Service(
        "代码生成依赖 Velocity 模板引擎，Rust 迁移版本暂未提供".to_string(),
    ))
}
