// 来源: ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java
//       ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java
//       ruoyi-generator/src/main/resources/mapper/generator/*.xml
// 职责: 代码生成器元数据（gen_table/gen_table_column）管理 + preview/download/genCode。

use std::collections::{HashMap, HashSet};

use axum::body::Body;
use axum::extract::{Path, Query, RawQuery, State};
use axum::http::header;
use axum::response::Response;
use axum::{Extension, Json, Router};
use serde_json::{json, Map, Value};
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::api::generator::{gen_render, gen_zip};
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

/// Java: selectGenTableById 的列（不含审计字段）。
pub(crate) const INFO_COLUMNS: &str = "table_id, table_name, table_comment, sub_table_name,      sub_table_fk_name, class_name, tpl_category, package_name, module_name, business_name,      function_name, function_author, gen_type, gen_path, options, remark";

const ALL_SPEC: ListSpec = ListSpec {
    select: TABLE_COLUMNS,
    from: "from gen_table",
    filters: &[],
    extra_where: "",
    order_by: "create_time DESC",
    id_column: "table_id",
};

const GEN_AUTHOR: &str = "ruoyi";
const GEN_PACKAGE: &str = "com.ruoyi.manager";

const SPEC: ListSpec = ListSpec {
    select: TABLE_COLUMNS,
    from: "from gen_table",
    filters: &[
        Filter::raw(
            "tableName",
            " and lower(table_name) like lower(concat('%', ?, '%'))",
        ),
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
            meta::get_route(
                "/tool/gen/column/{tableId}",
                Some("tool:gen:list"),
                None,
                column_list,
            ),
        )
        .route(
            "/tool/gen/getColumnList",
            meta::post_route("/tool/gen/getColumnList", None, None, get_column_list),
        )
        .route(
            "/tool/gen/getAllColumnList",
            meta::post_route(
                "/tool/gen/getAllColumnList",
                None,
                None,
                get_all_column_list,
            ),
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
            meta::get_route(
                "/tool/gen/preview/{tableId}",
                Some("tool:gen:preview"),
                None,
                preview,
            ),
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
            meta::get_route(
                "/tool/gen/{tableIds}",
                Some("tool:gen:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/tool/gen",
            meta::put_route(
                "/tool/gen",
                Some("tool:gen:edit"),
                Some(&LOG_EDIT),
                edit_save,
            ),
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
    table_name
        .rsplit('_')
        .next()
        .unwrap_or(table_name)
        .to_string()
}

fn module_name() -> String {
    GEN_PACKAGE
        .rsplit('.')
        .next()
        .unwrap_or_default()
        .to_string()
}

fn function_name(comment: &str) -> String {
    comment.replace('表', "").replace("若依", "")
}

/// Java: GenTable 实体的 Jackson 键顺序（BaseEntity 在前，派生 getter 在后）。
const GEN_TABLE_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "tableId",
    "tableName",
    "tableComment",
    "subTableName",
    "subTableFkName",
    "className",
    "tplCategory",
    "packageName",
    "moduleName",
    "businessName",
    "functionName",
    "functionAuthor",
    "genType",
    "genPath",
    "pkColumn",
    "subTable",
    "columns",
    "dictionaryInfoList",
    "dictionaryInfoString",
    "options",
    "treeCode",
    "treeParentCode",
    "treeName",
    "parentMenuId",
    "parentMenuName",
    "dictionaryListKeySuffix",
    "uploadInfo",
    "richTextInfo",
    "columnDialogInfo",
    "filterColumnList",
    "sub",
    "crud",
    "tree",
];

/// Java: GenTableColumn 实体的 Jackson 键顺序。
const GEN_COLUMN_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "columnId",
    "tableId",
    "columnName",
    "columnComment",
    "columnType",
    "javaType",
    "javaField",
    "isPk",
    "isIncrement",
    "isRequired",
    "isInsert",
    "isEdit",
    "isList",
    "isQuery",
    "queryType",
    "htmlType",
    "dictType",
    "dictTypeCamelCase",
    "sort",
    "generateLinkTableFlag",
    "linkTableId",
    "linkTable",
    "singleSelection",
    "multipleSelections",
    "dialogSearchColumnIds",
    "dialogListColumnIds",
    "dialogSearchColumnList",
    "dialogShowColumnList",
    "dialogSearchColumnNames",
    "dialogListColumnNames",
    "fieldMapString",
    "tableFieldList",
    "customFieldList",
    "majorLinkFieldInfo",
    "required",
    "list",
    "pk",
    "query",
    "insert",
    "edit",
    "capJavaField",
    "superColumn",
    "increment",
    "usableColumn",
];

/// Java: GenTableColumnMapper.xml 的 `selectGenTableColumnVo` —— 6 个关联列排在最前。
pub(crate) const DIALOG_COLUMN_COLUMNS: &str = "field_map_string, link_table_id, single_selection,      multiple_selections, dialog_search_column_ids, dialog_list_column_ids, column_id, table_id,      column_name, column_comment, column_type, java_type, java_field, is_pk, is_increment,      is_required, is_insert, is_edit, is_list, is_query, query_type, html_type, dict_type, sort,      create_by, create_time, update_by, update_time";

/// GenTableColumnResult 映射的属性（其余属性由 Jackson 输出为 null）。
const COLUMN_MAPPED_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "columnId",
    "tableId",
    "columnName",
    "columnComment",
    "columnType",
    "javaType",
    "javaField",
    "isPk",
    "isIncrement",
    "isRequired",
    "isInsert",
    "isEdit",
    "isList",
    "isQuery",
    "queryType",
    "htmlType",
    "dictType",
    "sort",
    "linkTableId",
    "singleSelection",
    "multipleSelections",
    "dialogSearchColumnIds",
    "dialogListColumnIds",
    "fieldMapString",
];

/// join 后只属于子表的标签，父行需要剔除。
const COLUMN_ONLY_KEYS: &[&str] = &[
    "columnId",
    "columnName",
    "columnComment",
    "columnType",
    "javaType",
    "javaField",
    "isPk",
    "isIncrement",
    "isRequired",
    "isInsert",
    "isEdit",
    "isList",
    "isQuery",
    "queryType",
    "htmlType",
    "dictType",
    "fieldMapString",
    "linkTableId",
    "singleSelection",
    "multipleSelections",
    "dialogSearchColumnIds",
    "dialogListColumnIds",
    "sort",
];

/// 按 Java 实体声明顺序重排；缺失的键补 null，多出的键保持原顺序追加。
fn reorder(row: &mut Value, order: &[&str]) {
    let Some(object) = row.as_object().cloned() else {
        return;
    };
    let mut out = Map::with_capacity(object.len().max(order.len()));
    for key in order {
        out.insert(
            (*key).to_string(),
            object.get(*key).cloned().unwrap_or(Value::Null),
        );
    }
    for (key, value) in object {
        out.entry(key).or_insert(value);
    }
    *row = Value::Object(out);
}

/// Java: StringUtils.capitalize。
fn capitalize(text: &str) -> String {
    let mut chars = text.chars();
    match chars.next() {
        Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
        None => String::new(),
    }
}

fn is_one(src: &Map<String, Value>, key: &str) -> bool {
    src.get(key).and_then(Value::as_str) == Some("1")
}

/// Java: GenTableColumn 实体（含 isPk()/isSuperColumn()/getCapJavaField() 等派生属性）。
pub(crate) fn shape_column(src: &Map<String, Value>) -> Value {
    let java_field = src
        .get("javaField")
        .and_then(Value::as_str)
        .map(str::to_string);
    let lower = java_field.as_deref().map(|value| value.to_lowercase());
    // Java: isSuperColumn 的忽略名单（BaseEntity + TreeEntity 字段）。
    let super_column = matches!(
        lower.as_deref(),
        Some("createby")
            | Some("createtime")
            | Some("updateby")
            | Some("updatetime")
            | Some("remark")
            | Some("parentname")
            | Some("parentid")
            | Some("ordernum")
            | Some("ancestors")
    );
    let usable_column = matches!(
        lower.as_deref(),
        Some("parentid") | Some("ordernum") | Some("remark")
    );
    let mut map = Map::new();
    for key in COLUMN_MAPPED_KEYS {
        if let Some(value) = src.get(*key) {
            map.insert(key.to_string(), value.clone());
        }
    }
    // gen_table_column.table_id 是 varchar，而 Java 属性是 Long（MyBatis 取 getLong），
    // 因此数字串要输出成 JSON 数字。
    for key in ["columnId", "tableId", "linkTableId"] {
        if let Some(Value::String(text)) = map.get(key) {
            if let Ok(number) = text.parse::<i64>() {
                map.insert(key.to_string(), json!(number));
            }
        }
    }
    map.insert("generateLinkTableFlag".to_string(), json!("0"));
    map.insert(
        "capJavaField".to_string(),
        match &java_field {
            Some(value) => Value::String(capitalize(value)),
            None => Value::Null,
        },
    );
    for (key, value) in [
        ("required", is_one(src, "isRequired")),
        ("list", is_one(src, "isList")),
        ("pk", is_one(src, "isPk")),
        ("query", is_one(src, "isQuery")),
        ("usableColumn", usable_column),
        ("edit", is_one(src, "isEdit")),
        ("superColumn", super_column),
        ("insert", is_one(src, "isInsert")),
        ("increment", is_one(src, "isIncrement")),
    ] {
        map.insert(key.to_string(), Value::Bool(value));
    }
    let mut row = Value::Object(map);
    reorder(&mut row, GEN_COLUMN_KEYS);
    row
}

/// Java: GenTable.isCrud()/isSub()/isTree()（Jackson 会输出这三个派生属性）。
fn add_tpl_flags(row: &mut Value) {
    let category = row
        .get("tplCategory")
        .and_then(Value::as_str)
        .map(str::to_string);
    let flag = |expect: &str| Value::Bool(category.as_deref() == Some(expect));
    if let Some(object) = row.as_object_mut() {
        object.insert("crud".to_string(), flag("crud"));
        object.insert("sub".to_string(), flag("sub"));
        object.insert("tree".to_string(), flag("tree"));
    }
}

/// MyBatis 的嵌套 `<collection>` 即使没有子表列也会产出一个子对象，
/// 其同名标签（create_by/create_time/table_id…）取自父行。
fn inherited_column(parent: Option<&Map<String, Value>>) -> Value {
    let mut src = Map::new();
    if let Some(parent) = parent {
        for key in [
            "createBy",
            "createTime",
            "updateBy",
            "updateTime",
            "tableId",
        ] {
            if let Some(value) = parent.get(key) {
                src.insert(key.to_string(), value.clone());
            }
        }
    }
    Value::Array(vec![shape_column(&src)])
}

/// 给 gen_table 行补齐派生键（columns / 未映射字段 / crud|sub|tree）。
pub(crate) fn finish_gen_table_row(row: &mut Value, columns: Option<Vec<Value>>) {
    let parent = row.as_object().cloned();
    if let Some(object) = row.as_object_mut() {
        let columns_value = match columns {
            Some(items) if !items.is_empty() => Value::Array(items),
            _ => inherited_column(parent.as_ref()),
        };
        object.insert("columns".to_string(), columns_value);
    }
    add_tpl_flags(row);
    reorder(row, GEN_TABLE_KEYS);
}

/// Java: `selectDbTableList` 的 resultMap 只有 4 列有标签，其余实体字段为 null。
fn shape_db_table_row(row: Value) -> Value {
    let mut map = Map::new();
    for key in ["createTime", "tableName", "tableComment", "updateTime"] {
        if let Some(value) = row.get(key) {
            map.insert(key.to_string(), value.clone());
        }
    }
    let mut value = Value::Object(map);
    finish_gen_table_row(&mut value, None);
    value
}

/// Java: selectGenTableAll —— 与列 join，`<collection>` 按 table_id 归并（首次出现顺序）。
const ALL_JOIN_SELECT: &str = "t.table_id, t.table_name, t.table_comment, t.sub_table_name,      \
     t.sub_table_fk_name, t.class_name, t.tpl_category, t.package_name, t.module_name,      \
     t.business_name, t.function_name, t.function_author, t.options, t.remark,      \
     c.column_id, c.column_name, c.column_comment, c.column_type, c.java_type, c.java_field,      \
     c.is_pk, c.is_increment, c.is_required, c.is_insert, c.is_edit, c.is_list, c.is_query,      \
     c.query_type, c.html_type, c.dict_type, c.field_map_string, c.link_table_id,      \
     c.single_selection, c.multiple_selections, c.dialog_search_column_ids,      \
     c.dialog_list_column_ids, c.sort";

async fn gen_tables_all(pool: &MySqlPool) -> Result<Vec<Value>, AppError> {
    let sql = format!(
        "select {ALL_JOIN_SELECT} from gen_table t \
         left join gen_table_column c on t.table_id = c.table_id order by c.sort"
    );
    let rows = sqlx::query(&sql).fetch_all(pool).await?;
    let mut order: Vec<String> = Vec::new();
    let mut groups: HashMap<String, Vec<Value>> = HashMap::new();
    for row in crate::db::rows::rows_to_json(&rows) {
        let key = match row.get("tableId") {
            Some(value) if !value.is_null() => value.to_string(),
            _ => String::new(),
        };
        if !groups.contains_key(&key) {
            order.push(key.clone());
        }
        groups.entry(key).or_default().push(row);
    }
    let mut tables = Vec::with_capacity(order.len());
    for key in order {
        let Some(items) = groups.remove(&key) else {
            continue;
        };
        let Some(first) = items.first() else {
            continue;
        };
        let mut table = first.clone();
        if let Some(object) = table.as_object_mut() {
            for column_key in COLUMN_ONLY_KEYS {
                object.remove(*column_key);
            }
        }
        let columns = items
            .iter()
            .filter_map(Value::as_object)
            .map(shape_column)
            .collect();
        finish_gen_table_row(&mut table, Some(columns));
        tables.push(table);
    }
    Ok(tables)
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, mut rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    for row in &mut rows {
        finish_gen_table_row(row, None);
    }
    Ok(TableDataInfo::new(total, rows))
}

async fn all_list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    // Java: getAllGenerateTableList 复用 selectGenTableList（不含列 join）。
    let mut rows = support::query_all(&state.db, &params, &ALL_SPEC).await?;
    for row in &mut rows {
        finish_gen_table_row(row, None);
    }
    Ok(AjaxResult::success_data(rows))
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
    if let Some(value) = params
        .get("params[beginTime]")
        .filter(|value| !value.is_empty())
    {
        builder.push(" and date_format(create_time,'%y%m%d') >= date_format(");
        builder.push_bind(value.clone());
        builder.push(", '%y%m%d')");
    }
    if let Some(value) = params
        .get("params[endTime]")
        .filter(|value| !value.is_empty())
    {
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
        "select table_name as tableName, table_comment as tableComment, \
         create_time as createTime, update_time as updateTime from information_schema.tables \
         where table_schema = (select database()) and table_name not like 'qrtz_%' \
         and table_name not like 'gen_%' and table_name not in (select table_name from gen_table)",
    );
    push_db_table_filters(&mut builder, &params);
    let mut count_builder = QueryBuilder::<MySql>::new(
        "select count(0) from information_schema.tables          where table_schema = (select database()) and table_name not like 'qrtz_%'          and table_name not like 'gen_%' and table_name not in (select table_name from gen_table)",
    );
    push_db_table_filters(&mut count_builder, &params);
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;
    let (offset, limit) = page.resolve(total);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows)
        .into_iter()
        .map(shape_db_table_row)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
}

async fn column_list(
    State(state): State<AppState>,
    Path(_table_id): Path<String>,
    Query(query): Query<HashMap<String, String>>,
) -> Result<TableDataInfo<Value>, AppError> {
    // Java: 路径变量拼写为 {talbleId}，真正取值来自 query 的 tableId。
    let table_id = query.get("tableId").cloned().unwrap_or_default();
    let rows = select_columns(&state.db, &table_id).await?;
    // Java GenController.columnList：new TableDataInfo() 形态（code=0, msg=null）。
    Ok(TableDataInfo {
        total: rows.len() as i64,
        rows,
        code: 200,
        msg: None,
    })
}

/// MyBatis 用 Long 绑定主键；若按字符串绑定，MySQL 会把结果集中同名列的
/// 元数据也报成字符串（sqlx 于是取到 "231" 而不是 231）。
fn bind_id(builder: &mut QueryBuilder<'_, MySql>, value: &str) {
    let text = value.trim_matches('"');
    match text.parse::<i64>() {
        Ok(number) => builder.push_bind(number),
        Err(_) => builder.push_bind(text.to_string()),
    };
}

pub(crate) async fn select_columns(
    pool: &MySqlPool,
    table_id: &str,
) -> Result<Vec<Value>, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {COLUMN_COLUMNS} from gen_table_column where table_id = "
    ));
    bind_id(&mut builder, table_id);
    builder.push(" order by sort");
    let rows = builder.build().fetch_all(pool).await?;
    Ok(crate::db::rows::rows_to_json(&rows)
        .iter()
        .filter_map(Value::as_object)
        .map(shape_column)
        .collect())
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
        bind_id(&mut builder, &table_id.to_string());
    }
    if let Some(value) = body
        .get("columnName")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
    {
        builder.push(" and column_name like concat('%', ");
        builder.push_bind(value.to_string());
        builder.push(", '%')");
    }
    if let Some(value) = body
        .get("javaField")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
    {
        builder.push(" and java_field like concat('%', ");
        builder.push_bind(value.to_string());
        builder.push(", '%')");
    }
    let mut count_builder =
        QueryBuilder::<MySql>::new("select count(0) from gen_table_column where 1=1");
    if let Some(table_id) = body.get("tableId").filter(|value| !value.is_null()) {
        count_builder.push(" and table_id = ");
        let table_id = table_id.to_string();
        let table_id = table_id.trim_matches('"').to_string();
        count_builder.push_bind(table_id);
    }
    if let Some(value) = body
        .get("columnName")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
    {
        count_builder.push(" and column_name like concat('%', ");
        count_builder.push_bind(value.to_string());
        count_builder.push(", '%')");
    }
    if let Some(value) = body
        .get("javaField")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
    {
        count_builder.push(" and java_field like concat('%', ");
        count_builder.push_bind(value.to_string());
        count_builder.push(", '%')");
    }
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;
    let (offset, limit) = page.resolve(total);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows)
        .iter()
        .filter_map(Value::as_object)
        .map(shape_column)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
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
    let items: Vec<&str> = ids
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .collect();
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {COLUMN_COLUMNS} from gen_table_column where column_id in ("
    ));
    // 与 bind_id 同理：column_id 按数字绑定，否则结果集列元数据会变成字符串。
    let numbers: Option<Vec<i64>> = items.iter().map(|item| item.parse::<i64>().ok()).collect();
    let mut separated = builder.separated(", ");
    match numbers {
        Some(values) => {
            for value in values {
                separated.push_bind(value);
            }
        }
        None => {
            for item in &items {
                separated.push_bind(item.to_string());
            }
        }
    }
    builder.push(") order by sort");
    let rows = builder.build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows)
        .iter()
        .filter_map(Value::as_object)
        .map(shape_column)
        .collect::<Vec<_>>();
    Ok(AjaxResult::success_data(data))
}

/// Java: GenTableServiceImpl.setTableFromOptions —— 仅 selectGenTableById 会调用。
fn apply_table_options(row: &mut Value) {
    let Some(Value::String(options)) = row.get("options").cloned() else {
        return;
    };
    let Ok(parsed) = serde_json::from_str::<Value>(&options) else {
        return;
    };
    let Some(object) = parsed.as_object() else {
        return;
    };
    let Some(target) = row.as_object_mut() else {
        return;
    };
    for key in [
        "treeCode",
        "treeParentCode",
        "treeName",
        "parentMenuId",
        "parentMenuName",
    ] {
        // Java: paramsObj.getString(key)，非字符串值也会转成字符串。
        let value = match object.get(key) {
            Some(Value::String(text)) => Value::String(text.clone()),
            Some(Value::Null) | None => Value::Null,
            Some(other) => Value::String(other.to_string()),
        };
        target.insert(key.to_string(), value);
    }
}

async fn get_info(
    State(state): State<AppState>,
    Path(table_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long talbleId`（拼写就是这样，报错文案里也是它）。
    let table_id = support::path_long("talbleId", &table_id)?.to_string();
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {INFO_COLUMNS} from gen_table where table_id = "
    ));
    bind_id(&mut builder, &table_id);
    let info_row = builder.build().fetch_optional(&state.db).await?;
    let rows = select_columns(&state.db, &table_id).await?;
    let mut info = info_row
        .map(|row| crate::db::rows::row_to_json(&row))
        .unwrap_or(Value::Null);
    if info.is_object() {
        // Java: info.columns 来自 selectGenTableById 的 join，其中没有 c.create_by
        // 等审计标签，因此子对象的审计字段为 null（rows 才有值）。
        let mut join_columns = rows.clone();
        for column in &mut join_columns {
            if let Some(object) = column.as_object_mut() {
                for key in ["createBy", "createTime", "updateBy", "updateTime"] {
                    object.insert(key.to_string(), Value::Null);
                }
            }
        }
        finish_gen_table_row(&mut info, Some(join_columns));
        apply_table_options(&mut info);
    }
    let tables = gen_tables_all(&state.db).await?;
    // Java 端为 HashMap：实测键顺序 tables, rows, info。
    let mut map = Map::new();
    map.insert("tables".to_string(), json!(tables));
    map.insert("rows".to_string(), json!(rows));
    map.insert("info".to_string(), info);
    Ok(AjaxResult::success_data(map))
}

/// Java: GenUtils.initTable。
fn init_table_body(table_name: &str, table_comment: &str, oper_name: &str) -> Map<String, Value> {
    let mut map = Map::new();
    map.insert("tableName".to_string(), json!(table_name));
    map.insert("tableComment".to_string(), json!(table_comment));
    map.insert("className".to_string(), json!(camel_case(table_name, true)));
    map.insert("packageName".to_string(), json!(GEN_PACKAGE));
    map.insert("moduleName".to_string(), json!(module_name()));
    map.insert("businessName".to_string(), json!(business_name(table_name)));
    map.insert(
        "functionName".to_string(),
        json!(function_name(table_comment)),
    );
    map.insert("functionAuthor".to_string(), json!(GEN_AUTHOR));
    map.insert("createBy".to_string(), json!(oper_name));
    map
}

/// Java: GenUtils.initColumnField。
fn init_column(row: &Value, table_id: i64, create_by: &str) -> Map<String, Value> {
    let column_name = row
        .get("columnName")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let column_type = row
        .get("columnType")
        .and_then(Value::as_str)
        .unwrap_or_default();
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
    map.insert(
        "sort".to_string(),
        row.get("sort").cloned().unwrap_or(Value::Null),
    );
    map.insert(
        "isPk".to_string(),
        row.get("isPk").cloned().unwrap_or(Value::Null),
    );
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
        "tinyint",
        "smallint",
        "mediumint",
        "int",
        "number",
        "integer",
        "bit",
        "bigint",
        "float",
        "double",
        "decimal",
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
    let not_list = [
        "id",
        "create_by",
        "create_time",
        "del_flag",
        "update_by",
        "update_time",
    ];
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
        // information_schema 的列名在结果元信息里是大写（TABLE_NAME），必须像 Java 的
        // mapper 那样起别名，否则按名字取不到值（先前静默取成空串，登记出一行脏数据）。
        let db_table = sqlx::query(
            "select table_name as tableName, table_comment as tableComment \
             from information_schema.tables \
             where table_schema = (select database()) and table_name = ?",
        )
        .bind(name)
        .fetch_optional(&state.db)
        .await?;
        let Some(db_table) = db_table else { continue };
        let table_name: String = sqlx::Row::try_get(&db_table, "tableName").unwrap_or_default();
        let table_comment: Option<String> =
            sqlx::Row::try_get(&db_table, "tableComment").unwrap_or_default();
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
        // LAST_INSERT_ID() 的列元信息是 BIGINT UNSIGNED，只能按 u64 取回。
        let table_id: u64 = sqlx::query_scalar("select last_insert_id()")
            .fetch_one(&mut *tx)
            .await?;

        let columns = sqlx::query(
            "select column_name as columnName, column_comment as columnComment, \
             column_type as columnType, \
             (case when (is_nullable = 'no' && column_key != 'PRI') then '1' else null end) as isRequired, \
             (case when column_key = 'PRI' then '1' else '0' end) as isPk, \
             ordinal_position as sort, \
             (case when extra = 'auto_increment' then '1' else '0' end) as isIncrement \
             from information_schema.columns \
             where table_schema = (select database()) and table_name = ? order by ordinal_position",
        )
        .bind(&table_name)
        .fetch_all(&mut *tx)
        .await?;
        for row in columns.iter() {
            let value = crate::db::rows::row_to_json(row);
            let column = init_column(&value, table_id as i64, &oper_name);
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
    support::update_entity_by_id(
        &state.db,
        "gen_table",
        "table_id",
        &table,
        support::AutoFill::NONE,
    )
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
    // Java: `@PathVariable Long[] tableIds` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("tableIds", &table_ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
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
        // 当前 Java 基准对占位 table 返回成功。
        return Ok(AjaxResult::success());
    };
    let existing: Vec<String> =
        sqlx::query_scalar("select column_name from gen_table_column where table_id = ?")
            .bind(table_id)
            .fetch_all(&state.db)
            .await?;
    let columns = sqlx::query(
        "select column_name as columnName, column_comment as columnComment, \
         column_type as columnType, \
         (case when (is_nullable = 'no' && column_key != 'PRI') then '1' else null end) as isRequired, \
         (case when column_key = 'PRI' then '1' else '0' end) as isPk, \
         ordinal_position as sort, \
         (case when extra = 'auto_increment' then '1' else '0' end) as isIncrement \
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
    State(state): State<AppState>,
    Path(table_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: GenTableServiceImpl.previewCode —— selectGenTableById + 表信息加工 + 逐模板渲染。
    let table_id = support::path_long("tableId", &table_id)?.to_string();
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {INFO_COLUMNS} from gen_table where table_id = "
    ));
    bind_id(&mut builder, &table_id);
    let Some(info_row) = builder.build().fetch_optional(&state.db).await? else {
        // 当前 Java 基准对占位 tableId 返回成功空对象。
        return Ok(AjaxResult::success_data(serde_json::json!({})));
    };
    let mut info = crate::db::rows::row_to_json(&info_row);
    let columns = select_columns(&state.db, &table_id).await?;
    if info.is_object() {
        // Java: previewCode 拿到的是 selectGenTableById 的完整 GenTable
        // （含 crud/sub/tree 派生属性与 columns），模板用 `$table.crud` 走分支。
        finish_gen_table_row(&mut info, Some(columns.clone()));
        apply_table_options(&mut info);
    }
    let datetime = chrono::Local::now().format("%Y-%m-%d").to_string();
    let data = gen_render::render_preview(
        &state.db,
        &info,
        &columns,
        &datetime,
        state.settings.generator_code.mybatis_plus.enable,
    )
    .await
    .map_err(AppError::Service)?;
    Ok(AjaxResult::success_data(data))
}

async fn download(
    State(state): State<AppState>,
    Path(table_name): Path<String>,
) -> Result<Response, AppError> {
    // Java: GenTableServiceImpl.downloadCode(String tableName) -> genCode(response, data)
    let entries = zip_entries(&state, &[table_name]).await?;
    zip_response(gen_zip::build(&entries))
}

async fn gen_code(
    State(state): State<AppState>,
    Path(table_name): Path<String>,
) -> Result<AjaxResult, AppError> {
    let (table, columns) = match load_table_by_name(&state.db, &table_name).await? {
        Some(value) => value,
        None => return Ok(AjaxResult::success()),
    };
    let datetime = chrono::Local::now().format("%Y-%m-%d").to_string();
    let rendered = gen_render::render_templates(
        &state.db,
        &table,
        &columns,
        &datetime,
        state.settings.generator_code.mybatis_plus.enable,
    )
    .await
    .map_err(AppError::Service)?;
    for (template, text) in rendered {
        // Java: 自定义路径生成跳过 sql.vm / api.js.vm / index.vue.vm / index-tree.vue.vm
        if ["sql.vm", "api.js.vm", "index.vue.vm", "index-tree.vue.vm"]
            .iter()
            .any(|skip| template.contains(*skip))
        {
            continue;
        }
        let path = gen_render::gen_path(&table, &template).map_err(AppError::Service)?;
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).map_err(|err| {
                AppError::Service(format!("渲染模板失败，表名：{}: {err}", table_name))
            })?;
        }
        // Java: FileUtils.writeStringToFile(new File(path), sw.toString(), UTF_8)
        std::fs::write(&path, text).map_err(|err| {
            AppError::Service(format!("渲染模板失败，表名：{}: {err}", table_name))
        })?;
    }
    Ok(AjaxResult::success())
}

async fn batch_gen_code(
    State(state): State<AppState>,
    Query(params): Query<HashMap<String, String>>,
) -> Result<Response, AppError> {
    // Java: Convert.toStrArray(tables) —— 按逗号切分，空串得到空数组，仍然返回合法空 zip。
    let raw = params.get("tables").map(String::as_str).unwrap_or_default();
    let names: Vec<String> = raw
        .split(',')
        .filter(|name| !name.is_empty())
        .map(str::to_string)
        .collect();
    let entries = zip_entries(&state, &names).await?;
    zip_response(gen_zip::build(&entries))
}

/// Java: GenController.genCode(HttpServletResponse response, byte[] data)
fn zip_response(data: Vec<u8>) -> Result<Response, AppError> {
    Response::builder()
        .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
        .header(header::ACCESS_CONTROL_EXPOSE_HEADERS, "Content-Disposition")
        .header(
            header::CONTENT_DISPOSITION,
            "attachment; filename=\"ruoyi.zip\"",
        )
        .header(
            header::CONTENT_TYPE,
            "application/octet-stream;charset=UTF-8",
        )
        .body(Body::from(data))
        .map_err(|err| AppError::Service(err.to_string()))
}

/// Java: selectGenTableByName + `<collection>` 归并出的 GenTable（含 columns）。
async fn load_table_by_name(
    pool: &MySqlPool,
    table_name: &str,
) -> Result<Option<(Value, Vec<Value>)>, AppError> {
    let Some(row) = sqlx::query(&format!(
        "select {INFO_COLUMNS} from gen_table where table_name = ?"
    ))
    .bind(table_name)
    .fetch_optional(pool)
    .await?
    else {
        return Ok(None);
    };
    let mut table = crate::db::rows::row_to_json(&row);
    let table_id = table
        .get("tableId")
        .map(Value::to_string)
        .unwrap_or_default();
    let columns = select_columns(pool, &table_id).await?;
    finish_gen_table_row(&mut table, Some(columns.clone()));
    apply_table_options(&mut table);
    Ok(Some((table, columns)))
}

async fn zip_entries(
    state: &AppState,
    table_names: &[String],
) -> Result<Vec<(String, Vec<u8>)>, AppError> {
    let mut entries: Vec<(String, Vec<u8>)> = Vec::new();
    let mut names: HashSet<String> = HashSet::new();
    for table_name in table_names {
        let (table, columns) = match load_table_by_name(&state.db, table_name).await? {
            Some(value) => value,
            None => continue,
        };
        let datetime = chrono::Local::now().format("%Y-%m-%d").to_string();
        let rendered = gen_render::render_templates(
            &state.db,
            &table,
            &columns,
            &datetime,
            state.settings.generator_code.mybatis_plus.enable,
        )
        .await
        .map_err(AppError::Service)?;
        for (template, text) in rendered {
            let entry = gen_render::file_name(&template, &table).map_err(AppError::Service)?;
            // Java: 重名条目在 putNextEntry 抛 ZipException，被 catch 后该条目不写入。
            if names.insert(entry.clone()) {
                entries.push((entry, text.into_bytes()));
            }
        }
    }
    Ok(entries)
}
