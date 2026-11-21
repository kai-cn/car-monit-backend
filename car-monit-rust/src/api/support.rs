// 来源: ruoyi-common/.../core/controller/BaseController.java
//       ruoyi-common/.../core/page/TableSupport.java
//       ruoyi-common/.../utils/poi/ExcelUtil.java
// 职责: 各切片共用的控制器层工具：分页、AjaxResult 约定、路径数组、导出。
// 对应关系: startPage()/getDataTable()/toAjax()/exportExcel() -> 这里的自由函数。

use std::collections::HashMap;

use axum::body::Body;
use axum::http::header::{CONTENT_DISPOSITION, CONTENT_TYPE};
use axum::response::Response;

use serde::de::DeserializeOwned;
use serde_json::Value;
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::common::excel;
use crate::common::page::{to_under_score_case, PageDomain};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

/// Java: TableSupport.buildPageRequest —— 从原始 query string 解析分页参数。
pub fn page_domain(raw: &Option<String>) -> PageDomain {
    PageDomain::from_query(raw.as_deref())
}

/// 把 query string 反序列化成实体/查询对象。
/// Java 的 `@ModelAttribute`/参数绑定：缺省字段为 null，未知字段忽略。
pub fn query_struct<T: DeserializeOwned>(raw: &Option<String>) -> Result<T, AppError> {
    match raw {
        Some(raw) if !raw.is_empty() => serde_urlencoded::from_str::<T>(raw)
            .map_err(|err| AppError::BadRequest(err.to_string())),
        _ => {
            serde_urlencoded::from_str::<T>("").map_err(|err| AppError::BadRequest(err.to_string()))
        }
    }
}

/// Java: `ServletUtils.getParameterMap` 的等价物（取每个键的第一个值）。
pub fn query_map(raw: &Option<String>) -> HashMap<String, String> {
    let mut map = HashMap::new();
    if let Some(raw) = raw {
        for (key, value) in url::form_urlencoded::parse(raw.as_bytes()) {
            map.entry(key.into_owned())
                .or_insert_with(|| value.into_owned());
        }
    }
    map
}

/// Java: `@PathVariable String[] ids` —— 逗号分隔。
pub fn ids_param(value: &str) -> Vec<String> {
    value.split(',').map(str::to_string).collect()
}

/// Java: `spring.servlet.multipart.max-file-size: 40MB`。
pub const MAX_UPLOAD_FILE_BYTES: usize = 40 * 1024 * 1024;

/// 一个 multipart 文件字段（保留 Java `MultipartFile` 用到的三要素）。
pub struct MultipartUpload {
    pub file_name: String,
    pub content_type: Option<String>,
    pub bytes: Vec<u8>,
}

/// 按 40MB 上限读取 multipart 文件字段；超限时返回 Java
/// `MaxUploadSizeExceededException` 的文案（HTTP 200 + code 500）。
pub async fn read_multipart_field(
    mut field: axum::extract::multipart::Field<'_>,
) -> Result<MultipartUpload, AppError> {
    let file_name = field.file_name().unwrap_or_default().to_string();
    let content_type = field.content_type().map(str::to_string);
    let mut bytes = Vec::new();
    while let Some(chunk) = field
        .chunk()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        if bytes.len().saturating_add(chunk.len()) > MAX_UPLOAD_FILE_BYTES {
            return Err(AppError::Service(
                "Maximum upload size exceeded".to_string(),
            ));
        }
        bytes.extend_from_slice(&chunk);
    }
    Ok(MultipartUpload {
        file_name,
        content_type,
        bytes,
    })
}

/// Java: `toAjax(int rows)` —— rows > 0 返回成功，否则返回错误。
pub fn to_ajax(rows: u64) -> AjaxResult {
    if rows > 0 {
        AjaxResult::success()
    } else {
        AjaxResult::error("操作失败")
    }
}

/// Java: `AjaxResult.success(count)` —— data 为影响行数。
pub fn success_count(rows: u64) -> AjaxResult {
    AjaxResult::success_data(rows)
}

/// Java: `getDataTable(list)`。
pub fn data_table(total: i64, rows: Vec<Value>) -> TableDataInfo<Value> {
    TableDataInfo::new(total, rows)
}

/// Java: `SecurityUtils.hasPermi` 守卫（handler 内显式调用时使用）。
pub fn require_permission(user: &LoginUser, permission: &str) -> Result<(), AppError> {
    crate::auth::security::require_permission(user, permission)
}

/// Java: `ExcelUtil.exportExcel(list, sheetName)` —— 写文件并返回文件名。
pub fn export_excel(
    state: &AppState,
    sheet_name: &str,
    headers: &[String],
    rows: &[Vec<Value>],
) -> Result<AjaxResult, AppError> {
    // Excel 生成与落盘是 CPU/IO 重活，移出 tokio worker（Java 在 Servlet 线程里做同样的事）。
    let filename = tokio::task::block_in_place(|| {
        excel::export_workbook(&state.settings.ruoyi.profile, sheet_name, headers, rows)
    })?;
    // Java ExcelUtil.exportExcel：文件落盘，响应里只有 msg=文件名。
    Ok(AjaxResult::success_msg(filename))
}

/// Java: 模板导出（EasyPOI）—— 直接把工作簿写入 HTTP 响应流。
pub fn export_download(
    sheet_name: &str,
    headers: &[String],
    rows: &[Vec<Value>],
) -> Result<Response, AppError> {
    let bytes = tokio::task::block_in_place(|| excel::export_bytes(sheet_name, headers, rows))?;
    Ok(Response::builder()
        .header(CONTENT_TYPE, "application/octet-stream;charset=UTF-8")
        .header(CONTENT_DISPOSITION, "attachment")
        .body(Body::from(bytes))
        .map_err(|err| AppError::Service(err.to_string()))?)
}

/// 按字段名从 JSON 行里取证（@Excel 列的取值）。
pub fn pick_fields(row: &Value, fields: &[&str]) -> Vec<Value> {
    fields
        .iter()
        .map(|field| row.get(*field).cloned().unwrap_or(Value::Null))
        .collect()
}

/// Java: `ISysDictDataService.selectDictDataMap(dictType)` —— dictValue -> dictLabel。
pub async fn dict_map(
    pool: &MySqlPool,
    dict_type: &str,
) -> Result<HashMap<String, String>, AppError> {
    let rows: Vec<(Option<String>, Option<String>)> = sqlx::query_as(
        "select dict_value, dict_label from sys_dict_data where dict_type = ? order by dict_sort asc",
    )
    .bind(dict_type)
    .fetch_all(pool)
    .await?;
    Ok(rows
        .into_iter()
        .map(|(value, label)| (value.unwrap_or_default(), label.unwrap_or_default()))
        .collect())
}

/// Java: `ICarQueryLogService.queryLog(condition, modelType, menuPoint)` —— car_query_log 落库。
pub async fn query_log(
    pool: &MySqlPool,
    user: &LoginUser,
    condition: &str,
    model_type: &str,
    menu_point: &str,
) -> Result<(), AppError> {
    let body = serde_json::json!({
        "userId": user.user.user_id.map(|value| value.to_string()),
        "userName": user.user.nick_name,
        "userIp": user.user.login_ip,
        "modelType": model_type,
        "menuPoint": menu_point,
        "queryCondition": condition,
    });
    insert_entity(pool, "car_query_log", &body, AutoFill::from_user(user)).await?;
    Ok(())
}

/// Java: `JSON.toJSONString(query)` —— 查询日志里的 queryCondition。
pub fn query_json(params: &HashMap<String, String>) -> String {
    serde_json::to_string(params).unwrap_or_default()
}

/// Java: `DataScopeAspect.dataScopeFilter` —— 把角色数据范围拼成 `and (...)`。
/// 管理员或任一角色为“全部数据权限”时返回 None（不过滤）。
/// 角色/部门 ID 来自登录态（可信），与 Java 一样直接内联。
pub fn data_scope_sql(
    user: &LoginUser,
    dept_alias: &str,
    user_alias: Option<&str>,
) -> Option<String> {
    if user.user.is_admin() {
        return None;
    }
    let dept_id = user.user.dept_id.unwrap_or_default();
    let user_id = user.user.user_id.unwrap_or_default();
    let mut conditions: Vec<String> = Vec::new();
    for role in &user.user.roles {
        match role.data_scope.as_deref() {
            Some("1") => return None,
            Some("2") => {
                let role_id = role.role_id.unwrap_or_default();
                conditions.push(format!(
                    "{dept_alias}.dept_id in (select dept_id from sys_role_dept where role_id = {role_id})"
                ));
            }
            Some("3") | Some("5") => {
                if role.data_scope.as_deref() == Some("5") {
                    match user_alias {
                        Some(alias) => {
                            conditions.push(format!("{alias}.user_id = {user_id}"));
                            continue;
                        }
                        None => {
                            conditions.push("1=0".to_string());
                            continue;
                        }
                    }
                }
                conditions.push(format!("{dept_alias}.dept_id = {dept_id}"));
            }
            Some("4") => {
                conditions.push(format!(
                    "{dept_alias}.dept_id in (select dept_id from sys_dept \
                     where dept_id = {dept_id} or find_in_set({dept_id}, ancestors))"
                ));
            }
            _ => {}
        }
    }
    if conditions.is_empty() {
        None
    } else {
        Some(format!(" and ({})", conditions.join(" or ")))
    }
}

/// 分页窗口：Java PageHelper 的 reasonable 语义。
pub fn page_window(page: &PageDomain, total: i64) -> (i64, i64) {
    page.resolve(total)
}

/// 追加 `order by`（已通过 escapeOrderBySql 校验）。
pub fn with_order_by(mut sql: String, page: &PageDomain) -> Result<String, AppError> {
    let order_by = page.escape_order_by_sql()?;
    if !order_by.is_empty() {
        sql.push_str(" order by ");
        sql.push_str(&order_by);
    }
    Ok(sql)
}

// ==================== MyBatis 动态 SQL（XML <where>/<if>）等价物 ====================

/// mapper XML `<if test="x != null and x != ''">` 的过滤条件。
#[derive(Clone, Copy)]
pub enum FilterKind {
    Eq,
    /// `like concat('%', #{x}, '%')`
    Like,
    /// `like concat(#{x}, '%')`
    LikeRight,
    Gt,
    Ge,
    Lt,
    Le,
    /// 自定义条件 SQL，只允许一个 `?` 占位（如 in 子查询）。
    Raw(&'static str),
}

pub struct Filter {
    /// 查询参数名（camelCase，来自实体 setter）。
    pub param: &'static str,
    /// 列表达式，如 `t.road_code`。
    pub column: &'static str,
    pub kind: FilterKind,
    /// Java `test="x != null"`（无 `x != ''`）时，空串也要参与过滤。
    pub empty_ok: bool,
}

impl Filter {
    pub const fn eq(param: &'static str, column: &'static str) -> Self {
        Self {
            param,
            column,
            kind: FilterKind::Eq,
            empty_ok: false,
        }
    }

    pub const fn like(param: &'static str, column: &'static str) -> Self {
        Self {
            param,
            column,
            kind: FilterKind::Like,
            empty_ok: false,
        }
    }

    pub const fn like_right(param: &'static str, column: &'static str) -> Self {
        Self {
            param,
            column,
            kind: FilterKind::LikeRight,
            empty_ok: false,
        }
    }

    pub const fn raw(param: &'static str, sql: &'static str) -> Self {
        Self {
            param,
            column: "",
            kind: FilterKind::Raw(sql),
            empty_ok: false,
        }
    }

    pub const fn eq_allow_empty(param: &'static str, column: &'static str) -> Self {
        Self {
            param,
            column,
            kind: FilterKind::Eq,
            empty_ok: true,
        }
    }
}

/// 一个 mapper XML 的 list 查询：`select <select> <from> where 1=1 <filters> <extra> <order>`。
pub struct ListSpec {
    pub select: &'static str,
    pub from: &'static str,
    pub filters: &'static [Filter],
    pub extra_where: &'static str,
    pub order_by: &'static str,
    /// 按 id 查询时使用的列（`selectById`）。
    pub id_column: &'static str,
}

fn param_value<'a>(params: &'a HashMap<String, String>, filter: &Filter) -> Option<&'a str> {
    let value = params.get(filter.param)?.as_str();
    if value.is_empty() && !filter.empty_ok {
        return None;
    }
    Some(value)
}

fn push_filters(
    builder: &mut QueryBuilder<MySql>,
    params: &HashMap<String, String>,
    filters: &[Filter],
) {
    for filter in filters {
        let Some(value) = param_value(params, filter) else {
            continue;
        };
        match filter.kind {
            FilterKind::Eq => {
                builder.push(" and ");
                builder.push(filter.column);
                builder.push(" = ");
                builder.push_bind(value.to_string());
            }
            FilterKind::Like => {
                builder.push(" and ");
                builder.push(filter.column);
                builder.push(" like concat('%', ");
                builder.push_bind(value.to_string());
                builder.push(", '%')");
            }
            FilterKind::LikeRight => {
                builder.push(" and ");
                builder.push(filter.column);
                builder.push(" like concat(");
                builder.push_bind(value.to_string());
                builder.push(", '%')");
            }
            FilterKind::Gt => push_cmp(builder, filter.column, " > ", value),
            FilterKind::Ge => push_cmp(builder, filter.column, " >= ", value),
            FilterKind::Lt => push_cmp(builder, filter.column, " < ", value),
            FilterKind::Le => push_cmp(builder, filter.column, " <= ", value),
            FilterKind::Raw(sql) => {
                // Raw 片段可能内含多个词，按片段拼接后绑定唯一参数。
                for (index, part) in sql.split('?').enumerate() {
                    if index > 0 {
                        builder.push_bind(value.to_string());
                    }
                    builder.push(part);
                }
            }
        }
    }
}

fn push_cmp(builder: &mut QueryBuilder<MySql>, column: &str, op: &str, value: &str) {
    builder.push(" and ");
    builder.push(column);
    builder.push(op);
    builder.push_bind(value.to_string());
}

fn build_list_sql<'a>(
    spec: &'a ListSpec,
    params: &'a HashMap<String, String>,
    with_order: bool,
) -> QueryBuilder<'a, MySql> {
    let mut builder = QueryBuilder::new("select ");
    builder.push(spec.select);
    builder.push(" ");
    builder.push(spec.from);
    builder.push(" where 1=1");
    push_filters(&mut builder, params, spec.filters);
    if !spec.extra_where.is_empty() {
        builder.push(spec.extra_where);
    }
    if with_order && !spec.order_by.is_empty() {
        builder.push(" order by ");
        builder.push(spec.order_by);
    }
    builder
}

/// Java: PageHelper.startPage + mapper.selectXxxList —— 先 count 再分页。
/// PageHelper 的 count 为 `select count(0) from (<原 SQL>) tmp_count`，这里保持一致。
pub async fn query_list(
    pool: &MySqlPool,
    params: &HashMap<String, String>,
    spec: &ListSpec,
    page: &PageDomain,
) -> Result<(i64, Vec<Value>), AppError> {
    // PageHelper 的 count 为 `select count(0) from (<原 SQL>) tmp_count`。
    // 这里用同一个 QueryBuilder 一次性渲染并绑定参数；不能先 `.sql()` 再重新绑定，
    // 因为 sqlx 的 `.sql()` 会为已 push 的参数写出占位符，导致参数数量翻倍。
    let mut count_builder = QueryBuilder::<MySql>::new("select count(0) from (select ");
    count_builder.push(spec.select);
    count_builder.push(" ");
    count_builder.push(spec.from);
    count_builder.push(" where 1=1");
    push_filters(&mut count_builder, params, spec.filters);
    if !spec.extra_where.is_empty() {
        count_builder.push(spec.extra_where);
    }
    count_builder.push(") tmp_count");
    let count_sql = count_builder.sql().to_string();
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(pool)
        .await
        .map_err(|err| {
            tracing::warn!("[分页计数失败] {err}\nSQL: {count_sql}");
            err
        })?;

    let (offset, limit) = page.resolve(total);
    let mut builder = build_list_sql(spec, params, true);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let data_sql = builder.sql().to_string();
    let rows = builder.build().fetch_all(pool).await.map_err(|err| {
        tracing::warn!("[分页查询失败] {err}\nSQL: {data_sql}");
        err
    })?;
    Ok((total, crate::db::rows::rows_to_json(&rows)))
}

/// 导出等场景：不分页，取全部匹配行。
pub async fn query_all(
    pool: &MySqlPool,
    params: &HashMap<String, String>,
    spec: &ListSpec,
) -> Result<Vec<Value>, AppError> {
    let rows = build_list_sql(spec, params, true)
        .build()
        .fetch_all(pool)
        .await?;
    Ok(crate::db::rows::rows_to_json(&rows))
}

/// Java 实体字段类型与 MySQL 列类型不一致时的序列化覆盖。
/// 例如 DB 是 DATE 但实体是 `java.util.Date`（ISO+时区），
/// 或 DB 是 DOUBLE 但实体是 `Integer`。
#[derive(Clone, Copy)]
pub enum FieldFormat {
    /// `java.time.LocalDate` -> `yyyy-MM-dd`
    DateOnly,
    /// `java.util.Date`（Jackson 默认）-> `yyyy-MM-dd'T'HH:mm:ss.SSS+08:00`
    IsoOffset,
    /// `java.time.LocalDateTime` / `@JsonFormat` -> `yyyy-MM-dd HH:mm:ss`
    DateTimeSpace,
    /// 数值列按整数输出（Java Integer/Long）
    Int,
    /// 数值列按字符串输出（Java String）
    String,
    /// 0/1、Y/N 转 JSON 布尔（Java boolean）
    Bool,
}

/// 按 Java 实体的声明顺序补齐并排序键：未查询的属性输出 null，
/// 多出的键保持原相对顺序追加在后面。
pub fn shape_entity_row(row: Value, keys: &[&str]) -> Value {
    let source = match row {
        Value::Object(object) => object,
        _ => serde_json::Map::new(),
    };
    let mut out = serde_json::Map::with_capacity(keys.len());
    for key in keys {
        out.insert(
            (*key).to_string(),
            source.get(*key).cloned().unwrap_or(Value::Null),
        );
    }
    for (key, value) in source {
        out.entry(key).or_insert(value);
    }
    Value::Object(out)
}

// ==================== Java 常用工具语义 ====================

/// Java: CommonUtil.isNull —— null 转空串，其余 toString + trim。
pub fn java_text(value: Option<&Value>) -> String {
    match value {
        Some(Value::String(text)) => text.trim().to_string(),
        Some(Value::Null) | None => String::new(),
        Some(other) => other.to_string().trim().to_string(),
    }
}

/// Java: GlobalExceptionHandler.handleMethodArgumentTypeMismatchException 的固定文案。
/// `%s` 依次是参数名、`getRequiredType().getName()`（数组是 `[Ljava.lang.Long;`）、原始输入值。
pub fn type_mismatch(name: &str, required: &str, raw: &str) -> AppError {
    AppError::BadRequest(format!(
        "请求参数类型不匹配，参数[{name}]要求类型为：'{required}'，但输入值为：'{raw}'"
    ))
}

/// Spring: `StringUtils.trimAllWhitespace` —— 去掉**所有**空白（含中间的），不是首尾 trim。
fn strip_all_whitespace(raw: &str) -> String {
    raw.chars().filter(|ch| !ch.is_whitespace()).collect()
}

/// Java: `@PathVariable Long x`（Spring 的 StringToNumber + Long.valueOf）。
/// 路径变量不会是空串，所以不处理 `source.isEmpty() -> null` 那一支。
pub fn path_long(name: &str, raw: &str) -> Result<i64, AppError> {
    strip_all_whitespace(raw)
        .parse::<i64>()
        .map_err(|_| type_mismatch(name, "java.lang.Long", raw))
}

/// Java: `@PathVariable Integer x` / `int x`。
pub fn path_int(name: &str, raw: &str) -> Result<i32, AppError> {
    strip_all_whitespace(raw)
        .parse::<i32>()
        .map_err(|_| type_mismatch(name, "java.lang.Integer", raw))
}

/// Java: `@PathVariable Long[] ids` —— 逗号分隔，空段被丢弃；
/// 任一段转不动就整体失败，报错里的值是**整段路径变量原文**（不是出错的那一段）。
pub fn path_long_list(name: &str, raw: &str) -> Result<Vec<i64>, AppError> {
    let mut out = Vec::new();
    for token in raw.split(',') {
        let text = strip_all_whitespace(token);
        if text.is_empty() {
            continue;
        }
        out.push(
            text.parse::<i64>()
                .map_err(|_| type_mismatch(name, "[Ljava.lang.Long;", raw))?,
        );
    }
    Ok(out)
}

/// Java: `@PathVariable Integer[] ids`。
pub fn path_int_list(name: &str, raw: &str) -> Result<Vec<i32>, AppError> {
    let mut out = Vec::new();
    for token in raw.split(',') {
        let text = strip_all_whitespace(token);
        if text.is_empty() {
            continue;
        }
        out.push(
            text.parse::<i32>()
                .map_err(|_| type_mismatch(name, "[Ljava.lang.Integer;", raw))?,
        );
    }
    Ok(out)
}

/// Java: BigDecimal 字段的值（列可能是 DECIMAL/字符串）。
pub fn json_decimal(value: Option<&Value>) -> Option<rust_decimal::Decimal> {
    match value {
        Some(Value::Number(number)) => number.to_string().parse::<rust_decimal::Decimal>().ok(),
        Some(Value::String(text)) => text.trim().parse::<rust_decimal::Decimal>().ok(),
        _ => None,
    }
}

/// BigDecimal -> JSON 数字（保持 Jackson 的写法）。
pub fn decimal_json(value: rust_decimal::Decimal) -> Value {
    value
        .to_string()
        .parse::<serde_json::Number>()
        .map(Value::Number)
        .unwrap_or_else(|_| Value::String(value.to_string()))
}

/// Java: Integer/int 字段。
pub fn java_int(value: Option<&Value>) -> i64 {
    match value {
        Some(Value::Number(number)) => number
            .as_i64()
            // DECIMAL 列经 rows.rs 变成 JSON 浮点（`1119.0`），`as_i64()` 会 None；
            // Java 的 BigDecimal.intValue() 是向零截断，这里同样截断而不是当 0。
            .or_else(|| number.as_f64().map(|float| float as i64))
            .unwrap_or(0),
        Some(Value::String(text)) => text
            .trim()
            .parse::<f64>()
            .map(|float| float as i64)
            .unwrap_or(0),
        _ => 0,
    }
}

/// 只保留实体声明的键（Java 的 fastjson2/Jackson 会丢弃 DTO 之外的字段）。
pub fn project_entity_row(row: Value, keys: &[&str]) -> Value {
    let source = match row {
        Value::Object(object) => object,
        _ => serde_json::Map::new(),
    };
    let mut out = serde_json::Map::with_capacity(keys.len());
    for key in keys {
        out.insert(
            (*key).to_string(),
            source.get(*key).cloned().unwrap_or(Value::Null),
        );
    }
    Value::Object(out)
}

/// Java 实体里的集合字段：null 时 Jackson 输出 null，空集合输出 []。
pub fn shape_rows(rows: Vec<Value>, keys: &[&str]) -> Vec<Value> {
    rows.into_iter()
        .map(|row| shape_entity_row(row, keys))
        .collect()
}

/// 纯键序重排：只按 `keys` 调整已有键的先后，不补 null、不删键。
/// 用于「值一致、只有 Jackson 顺序不同」的端点（BaseEntity 字段在前 + 声明顺序 + 派生 getter）。
pub fn reorder_keys(row: Value, keys: &[&str]) -> Value {
    let Value::Object(mut source) = row else {
        return row;
    };
    let mut out = serde_json::Map::with_capacity(source.len());
    for key in keys {
        if let Some((name, value)) = source.remove_entry(*key) {
            out.insert(name, value);
        }
    }
    out.extend(source);
    Value::Object(out)
}

pub fn reorder_rows(rows: Vec<Value>, keys: &[&str]) -> Vec<Value> {
    rows.into_iter()
        .map(|row| reorder_keys(row, keys))
        .collect()
}

/// Java: Forest 把上游 JSON 反序列化成实体、再由 Jackson 序列化出去 ——
/// 实体字段**全部**出现（上游没给的补 null），上游多给的字段被丢弃
/// （Jackson `FAIL_ON_UNKNOWN_PROPERTIES=false`）。远端透传类端点要用它，
/// 光 `reorder_keys` 只会少键。
pub fn entity_shape(value: Value, keys: &[&str]) -> Value {
    let Value::Object(mut source) = value else {
        return value;
    };
    let mut out = serde_json::Map::with_capacity(keys.len());
    for key in keys {
        out.insert(
            (*key).to_string(),
            source.remove(*key).unwrap_or(Value::Null),
        );
    }
    Value::Object(out)
}

pub fn entity_shapes(rows: Vec<Value>, keys: &[&str]) -> Vec<Value> {
    rows.into_iter()
        .map(|row| entity_shape(row, keys))
        .collect()
}

/// 按字段名覆盖行值格式（key 为 JSON 驼峰名）。
pub fn apply_formats(rows: &mut [Value], formats: &[(&str, FieldFormat)]) {
    if formats.is_empty() {
        return;
    }
    for row in rows.iter_mut() {
        let Some(object) = row.as_object_mut() else {
            continue;
        };
        for (key, format) in formats {
            let Some(value) = object.get_mut(*key) else {
                continue;
            };
            if value.is_null() {
                continue;
            }
            *value = format_value(value, *format);
        }
    }
}

fn format_value(value: &Value, format: FieldFormat) -> Value {
    match format {
        FieldFormat::Int => match value {
            Value::Number(number) => {
                if let Some(text) = number.as_i64() {
                    Value::from(text)
                } else if let Some(float) = number.as_f64() {
                    Value::from(float.trunc() as i64)
                } else {
                    value.clone()
                }
            }
            Value::String(text) => match text.trim().parse::<i64>() {
                Ok(number) => Value::from(number),
                Err(_) => match text.trim().parse::<f64>() {
                    Ok(float) => Value::from(float.trunc() as i64),
                    Err(_) => value.clone(),
                },
            },
            _ => value.clone(),
        },
        FieldFormat::String => match value {
            Value::String(_) => value.clone(),
            Value::Null => value.clone(),
            other => Value::String(other.to_string()),
        },
        FieldFormat::Bool => match value {
            Value::Bool(_) => value.clone(),
            Value::Number(number) => Value::Bool(number.as_i64().unwrap_or(0) != 0),
            Value::String(text) => Value::Bool(matches!(text.as_str(), "1" | "Y" | "y" | "true")),
            _ => value.clone(),
        },
        FieldFormat::DateOnly => match value.as_str() {
            Some(text) if text.len() >= 10 => Value::String(text[..10].to_string()),
            _ => value.clone(),
        },
        FieldFormat::IsoOffset => match value.as_str() {
            Some(text) => match parse_naive(text) {
                Some(dt) => Value::String(dt.format("%Y-%m-%dT%H:%M:%S.000+08:00").to_string()),
                None => value.clone(),
            },
            _ => value.clone(),
        },
        FieldFormat::DateTimeSpace => match value.as_str() {
            Some(text) => match parse_naive(text) {
                Some(dt) => Value::String(dt.format("%Y-%m-%d %H:%M:%S").to_string()),
                None => value.clone(),
            },
            _ => value.clone(),
        },
    }
}

fn parse_naive(text: &str) -> Option<chrono::NaiveDateTime> {
    let trimmed = text.trim();
    if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(trimmed, "%Y-%m-%d %H:%M:%S") {
        return Some(dt);
    }
    if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(trimmed, "%Y-%m-%dT%H:%M:%S") {
        return Some(dt);
    }
    if let Ok(dt) = chrono::DateTime::parse_from_rfc3339(trimmed) {
        return Some(dt.naive_local());
    }
    if let Ok(date) =
        chrono::NaiveDate::parse_from_str(trimmed.get(..10).unwrap_or(trimmed), "%Y-%m-%d")
    {
        return date.and_hms_opt(0, 0, 0);
    }
    None
}

/// Java: startPage(); mapper.selectXxxList —— 分页查询后按实体字段类型覆盖格式。
pub async fn query_list_fmt(
    pool: &MySqlPool,
    params: &HashMap<String, String>,
    spec: &ListSpec,
    page: &PageDomain,
    formats: &[(&str, FieldFormat)],
) -> Result<(i64, Vec<Value>), AppError> {
    let (total, mut rows) = query_list(pool, params, spec, page).await?;
    apply_formats(&mut rows, formats);
    Ok((total, rows))
}

/// Java: mapper.selectXxxList（不分页）后按实体字段类型覆盖格式。
pub async fn query_all_fmt(
    pool: &MySqlPool,
    params: &HashMap<String, String>,
    spec: &ListSpec,
    formats: &[(&str, FieldFormat)],
) -> Result<Vec<Value>, AppError> {
    let mut rows = query_all(pool, params, spec).await?;
    apply_formats(&mut rows, formats);
    Ok(rows)
}

/// Java: mapper.selectXxxById 后按实体字段类型覆盖格式。
pub async fn query_by_id_fmt(
    pool: &MySqlPool,
    spec: &ListSpec,
    id: &str,
    formats: &[(&str, FieldFormat)],
) -> Result<Option<Value>, AppError> {
    let mut row = query_by_id(pool, spec, id).await?;
    if let Some(value) = row.as_mut() {
        apply_formats(std::slice::from_mut(value), formats);
    }
    Ok(row)
}

/// Java: mapper.selectXxxById。
pub async fn query_by_id(
    pool: &MySqlPool,
    spec: &ListSpec,
    id: &str,
) -> Result<Option<Value>, AppError> {
    let sql = format!(
        "select {} {} where {} = ?",
        spec.select, spec.from, spec.id_column
    );
    let row = sqlx::query(&sql).bind(id).fetch_optional(pool).await?;
    Ok(row.map(|row| crate::db::rows::row_to_json(&row)))
}

// ==================== MyBatis-Plus 等价 CRUD ====================

/// Java: MyBatis-Plus 的 insert/updateById 默认策略（NOT_NULL：空字段不参与 SQL）。
/// `enabled` 时等价 `MyBatisPlusHandlerConfig` 的 MetaObjectHandler：
/// insert 补 id(UUID)/create_time/create_by/eps_id/tenant_id，update 补 update_time/update_by。
pub struct AutoFill<'a> {
    pub enabled: bool,
    pub username: Option<&'a str>,
    pub user_id: Option<i64>,
    pub dept_id: Option<i64>,
    pub tenant_id: Option<i64>,
    /// Java: `@TableId(type)` —— `ASSIGN_UUID` 生成主键；`INPUT` 不生成，
    /// 但 MP 仍把 `id` 放进 INSERT 列清单，于是 MySQL 报 `Column 'id' cannot be null`。
    pub generate_id: bool,
}

/// Java: 主键为 `IdType.INPUT`（实体继承 `BasePlusEntityInput`）且 service 里没有显式
/// setUUID 的表。`car_info` 也继承该类，但 `CarInfoServiceImpl.saveCarInfo` 里
/// `carInfo.setId(StringUtils.getUUID())`，所以不在此列。
const ID_INPUT_TABLES: &[&str] = &["car_suspicious_back"];

impl AutoFill<'_> {
    pub const NONE: AutoFill<'static> = AutoFill {
        enabled: false,
        username: None,
        user_id: None,
        dept_id: None,
        tenant_id: None,
        generate_id: true,
    };
}

impl<'a> AutoFill<'a> {
    /// Java: SecurityUtils.getUserId()/getEpsId()(=deptId)/getTenantId()。
    pub fn from_user(user: &'a LoginUser) -> Self {
        Self {
            enabled: true,
            username: Some(user.user.user_name.as_deref().unwrap_or_default()),
            user_id: user.user.user_id,
            dept_id: user.user.dept_id,
            tenant_id: user.user.tenant_id,
            generate_id: true,
        }
    }

    /// 关闭主键生成，等价实体的 `@TableId(type = IdType.INPUT)`。
    pub fn with_input_id(mut self) -> Self {
        self.generate_id = false;
        self
    }
}

/// 表名 -> 列名集合（`information_schema`，进程内缓存）。
static COLUMN_CACHE: std::sync::LazyLock<
    std::sync::Mutex<HashMap<String, std::sync::Arc<std::collections::HashSet<String>>>>,
> = std::sync::LazyLock::new(|| std::sync::Mutex::new(HashMap::new()));

/// 查一张表的真实列名（小写），带缓存。
pub async fn table_columns(
    pool: &MySqlPool,
    table: &str,
) -> Result<std::sync::Arc<std::collections::HashSet<String>>, AppError> {
    checked_table(table)?;
    if let Some(found) = COLUMN_CACHE
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .get(table)
    {
        return Ok(std::sync::Arc::clone(found));
    }
    let rows: Vec<(String,)> = sqlx::query_as(
        "select column_name from information_schema.columns \
         where table_schema = database() and table_name = ?",
    )
    .bind(table)
    .fetch_all(pool)
    .await?;
    if rows.is_empty() {
        return Err(AppError::Service(format!("表不存在: {table}")));
    }
    let columns = std::sync::Arc::new(
        rows.into_iter()
            .map(|(name,)| name.to_lowercase())
            .collect::<std::collections::HashSet<_>>(),
    );
    COLUMN_CACHE
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .insert(table.to_string(), std::sync::Arc::clone(&columns));
    Ok(columns)
}

/// Java: Jackson/FastJSON 忽略实体里没有对应列的属性（`params`、`applyTime1` 这类
/// `exist = false` 字段每个请求体都带），SQLx 侧不过滤就会 1054 —— 前端的
/// `add`/`edit` 请求整体打不进 Rust。
fn filter_entity_columns(entity: &Value, columns: &std::collections::HashSet<String>) -> Value {
    let Some(map) = entity.as_object() else {
        return entity.clone();
    };
    let mut kept = serde_json::Map::new();
    for (key, value) in map {
        if columns.contains(&to_under_score_case(key)) {
            kept.insert(key.clone(), value.clone());
        }
    }
    Value::Object(kept)
}

/// 自己拼 SQL（同一事务里还要写关联表）的端点用这个：先丢掉非列字段再拼。
pub async fn entity_for_table(
    pool: &MySqlPool,
    table: &str,
    entity: &Value,
) -> Result<Value, AppError> {
    let known = table_columns(pool, table).await?;
    Ok(filter_entity_columns(entity, &known))
}

/// Java: FastJson2 `WriteClassName` 写缓存的形状 —— `@type` 在最前、字段名**字典序**、
/// null 不写。只有按这个形状写，Java 侧才会把缓存反序列化成实体；
/// 否则 `redisCache.getCacheObject` 拿到的是原始 JSONObject，会把 `@type`/`params`
/// 一路透传进 HTTP 响应（`sys_dict:*` 就踩过这条）。
pub fn fastjson_rows(rows: Vec<Value>) -> Vec<Value> {
    rows.into_iter()
        .filter_map(|row| row.as_object().cloned())
        .map(|object| {
            let mut kept: Vec<(String, Value)> = object
                .into_iter()
                .filter(|(_, value)| !value.is_null())
                .collect();
            kept.sort_by(|left, right| left.0.cmp(&right.0));
            Value::Object(kept.into_iter().collect())
        })
        .collect()
}

/// Java: `mapper.insert(entity)` —— 只写入非 null 字段。
pub async fn insert_entity(
    pool: &MySqlPool,
    table: &str,
    entity: &Value,
    fill: AutoFill<'_>,
) -> Result<u64, AppError> {
    let mut columns = Vec::new();
    let mut values = Vec::new();
    let known = table_columns(pool, table).await?;
    collect_columns(
        &filter_entity_columns(entity, &known),
        None,
        &mut columns,
        &mut values,
    )?;

    if fill.enabled {
        // Java: @TableId(type = IdType.ASSIGN_UUID) —— 主键缺失时生成本地 UUID；
        // IdType.INPUT 不生成，但 MP 仍把 id 放进列清单（值 NULL），由 MySQL 拒绝。
        let id_value = if fill.generate_id {
            Value::String(uuid::Uuid::new_v4().simple().to_string())
        } else {
            Value::Null
        };
        push_if_absent(&mut columns, &mut values, "id", Some(id_value));
        push_if_absent(
            &mut columns,
            &mut values,
            "create_time",
            Some(Value::String(now_string())),
        );
        push_if_absent(
            &mut columns,
            &mut values,
            "create_by",
            fill.user_id.map(Value::from),
        );
        push_if_absent(
            &mut columns,
            &mut values,
            "eps_id",
            fill.dept_id.map(Value::from),
        );
        // Java 的 tenantId 判空写成了 `epsId == null`（局部变量，填充前取值），
        // 效果与“tenantId 为空则填充”一致。
        push_if_absent(
            &mut columns,
            &mut values,
            "tenant_id",
            fill.tenant_id.map(Value::from),
        );
    }

    if columns.is_empty() {
        return Err(AppError::Service("新增失败：没有可写入的字段".to_string()));
    }

    let mut builder: QueryBuilder<MySql> = QueryBuilder::new("insert into ");
    builder.push(checked_table(table)?);
    builder.push(" (");
    for (index, column) in columns.iter().enumerate() {
        if index > 0 {
            builder.push(", ");
        }
        builder.push(checked_identifier(column)?);
    }
    builder.push(") values (");
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            builder.push(", ");
        }
        bind_json(&mut builder, value)?;
    }
    builder.push(")");

    let result = builder.build().execute(pool).await?;
    Ok(result.rows_affected())
}

/// 各 Service 统一的 `saveXxx`：主键非空则 updateById，否则 insert。
/// `audit` 为 Some 时等价 BasePlusEntity 的自动填充（UUID/审计列/del_flag 条件）；
/// Custom 实体（@TableId 为 INPUT/ASSIGN_UUID 之外的普通主键）应传 None。
pub async fn save_or_update(
    state: &AppState,
    user: &LoginUser,
    body: &Value,
    table: &str,
    pk_column: &str,
    audit: bool,
    generate_uuid: bool,
) -> Result<AjaxResult, AppError> {
    // Java: `@TableId(type = IdType.INPUT)` 的实体不生成主键，见 ID_INPUT_TABLES。
    let generate_uuid = generate_uuid && !ID_INPUT_TABLES.contains(&table);
    let mut fill = if audit {
        AutoFill::from_user(user)
    } else {
        AutoFill::NONE
    };
    fill.generate_id = generate_uuid;
    let pk_json = to_camel(pk_column);
    let current = body.get(&pk_json).cloned().unwrap_or(Value::Null);
    let blank = match &current {
        Value::Null => true,
        Value::String(text) => text.is_empty(),
        _ => false,
    };

    if blank {
        let mut entity = body.clone();
        let pk_value = if generate_uuid {
            let generated = uuid::Uuid::new_v4().simple().to_string();
            if let Some(map) = entity.as_object_mut() {
                map.insert(pk_json.clone(), Value::String(generated.clone()));
            }
            Value::String(generated)
        } else {
            Value::Null
        };
        insert_entity(&state.db, table, &entity, fill).await?;
        Ok(AjaxResult::success_msg_data("操作成功！", pk_value))
    } else {
        update_entity_by_id(&state.db, table, pk_column, body, fill).await?;
        Ok(AjaxResult::success_msg_data("操作成功！", current))
    }
}

/// Java: `mapper.updateById(entity)` —— 以 `id_column` 为条件，只更新非 null 字段。
pub async fn update_entity_by_id(
    pool: &MySqlPool,
    table: &str,
    id_column: &str,
    entity: &Value,
    fill: AutoFill<'_>,
) -> Result<u64, AppError> {
    let id_value = entity
        .get(&to_camel(id_column))
        .or_else(|| entity.get(id_column))
        .filter(|value| !value.is_null())
        .cloned()
        .ok_or_else(|| AppError::Service(format!("{}不能为空", to_camel(id_column))))?;

    let mut columns = Vec::new();
    let mut values = Vec::new();
    let known = table_columns(pool, table).await?;
    collect_columns(
        &filter_entity_columns(entity, &known),
        Some(id_column),
        &mut columns,
        &mut values,
    )?;

    if fill.enabled {
        upsert_column(
            &mut columns,
            &mut values,
            "update_by",
            fill.user_id.map(Value::from),
        );
        upsert_column(
            &mut columns,
            &mut values,
            "update_time",
            Some(Value::String(now_string())),
        );
    }

    if columns.is_empty() {
        return Ok(0);
    }

    let mut builder: QueryBuilder<MySql> = QueryBuilder::new("update ");
    builder.push(checked_table(table)?);
    builder.push(" set ");
    for (index, (column, value)) in columns.iter().zip(values.iter()).enumerate() {
        if index > 0 {
            builder.push(", ");
        }
        builder.push(checked_identifier(column)?);
        builder.push(" = ");
        bind_json(&mut builder, value)?;
    }
    builder.push(" where ");
    builder.push(checked_identifier(id_column)?);
    builder.push(" = ");
    bind_json(&mut builder, &id_value)?;
    if fill.enabled {
        // Java: @TableLogic —— updateById 自动追加 del_flag = '0'。
        builder.push(" and del_flag = '0'");
    }

    let result = builder.build().execute(pool).await?;
    Ok(result.rows_affected())
}

/// Java: `delete from t where col in (?, ?, ...)`。
pub async fn delete_by_ids(
    pool: &MySqlPool,
    table: &str,
    column: &str,
    ids: &[String],
) -> Result<u64, AppError> {
    if ids.is_empty() {
        return Ok(0);
    }
    let mut builder: QueryBuilder<MySql> = QueryBuilder::new("delete from ");
    builder.push(checked_table(table)?);
    builder.push(" where ");
    builder.push(checked_identifier(column)?);
    builder.push(" in (");
    let mut separated = builder.separated(", ");
    for id in ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    let result = builder.build().execute(pool).await?;
    Ok(result.rows_affected())
}

/// mapper XML 的软删除：`update t set del_flag='1' where col in (...)`。
pub async fn soft_delete_by_ids(
    pool: &MySqlPool,
    table: &str,
    column: &str,
    ids: &[String],
) -> Result<u64, AppError> {
    if ids.is_empty() {
        return Ok(0);
    }
    let mut builder: QueryBuilder<MySql> = QueryBuilder::new("update ");
    builder.push(checked_table(table)?);
    builder.push(" set del_flag = '1' where ");
    builder.push(checked_identifier(column)?);
    builder.push(" in (");
    let mut separated = builder.separated(", ");
    for id in ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    let result = builder.build().execute(pool).await?;
    Ok(result.rows_affected())
}

fn collect_columns(
    entity: &Value,
    skip_column: Option<&str>,
    columns: &mut Vec<String>,
    values: &mut Vec<Value>,
) -> Result<(), AppError> {
    let Some(map) = entity.as_object() else {
        return Err(AppError::BadRequest("请求体必须是 JSON 对象".to_string()));
    };
    for (key, value) in map {
        // Java FastJSON 反序列化的实体字段均为 camelCase；忽略 null。
        if value.is_null() {
            continue;
        }
        if key.starts_with('@') {
            continue;
        }
        let column = to_under_score_case(key);
        if Some(column.as_str()) == skip_column {
            continue;
        }
        columns.push(column);
        values.push(value.clone());
    }
    Ok(())
}

fn push_if_absent(
    columns: &mut Vec<String>,
    values: &mut Vec<Value>,
    column: &str,
    value: Option<Value>,
) {
    if columns.iter().any(|existing| existing == column) {
        return;
    }
    if let Some(value) = value {
        columns.push(column.to_string());
        values.push(value);
    }
}

fn upsert_column(
    columns: &mut Vec<String>,
    values: &mut Vec<Value>,
    column: &str,
    value: Option<Value>,
) {
    let Some(value) = value else { return };
    if let Some(index) = columns.iter().position(|existing| existing == column) {
        values[index] = value;
    } else {
        columns.push(column.to_string());
        values.push(value);
    }
}

pub fn now_string() -> String {
    chrono::Local::now()
        .naive_local()
        .format("%Y-%m-%d %H:%M:%S")
        .to_string()
}

/// 单值查询（i64）。
pub async fn scalar_i64(pool: &MySqlPool, sql: &str, value: &str) -> Result<Option<i64>, AppError> {
    Ok(sqlx::query_scalar(sql)
        .bind(value)
        .fetch_optional(pool)
        .await?)
}

/// Java: `ISysConfigService.selectConfigByKey` —— 读 sys_config（不走缓存）。
pub async fn config_value(pool: &MySqlPool, key: &str) -> Result<String, AppError> {
    Ok(scalar_string(
        pool,
        "select config_value from sys_config where config_key = ?",
        key,
    )
    .await?
    .unwrap_or_default())
}

/// 单值查询（String）。
pub async fn scalar_string(
    pool: &MySqlPool,
    sql: &str,
    value: &str,
) -> Result<Option<String>, AppError> {
    Ok(sqlx::query_scalar(sql)
        .bind(value)
        .fetch_optional(pool)
        .await?)
}

/// camelCase JSON 字段 -> 下划线列名（MyBatis-Plus 列映射）。
pub fn column_name(key: &str) -> String {
    to_under_score_case(key)
}

/// 把 JSON 值绑定到 QueryBuilder（与 insert/update 内部策略一致）。
pub fn bind_value(builder: &mut QueryBuilder<'_, MySql>, value: &Value) {
    let _ = bind_json(builder, value);
}

fn to_camel(column: &str) -> String {
    crate::db::rows::column_to_property(column)
}

fn checked_table(table: &str) -> Result<&str, AppError> {
    if table
        .chars()
        .all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
        && !table.is_empty()
    {
        Ok(table)
    } else {
        Err(AppError::Service(format!("非法表名: {table}")))
    }
}

fn checked_identifier(identifier: &str) -> Result<&str, AppError> {
    if identifier
        .chars()
        .all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
        && !identifier.is_empty()
    {
        Ok(identifier)
    } else {
        Err(AppError::Service(format!("非法列名: {identifier}")))
    }
}

fn bind_json(builder: &mut QueryBuilder<MySql>, value: &Value) -> Result<(), AppError> {
    match value {
        Value::Null => builder.push_bind(Option::<String>::None),
        Value::Bool(flag) => builder.push_bind(i64::from(*flag)),
        Value::Number(number) => {
            if let Some(value) = number.as_i64() {
                builder.push_bind(value)
            } else if let Some(value) = number.as_u64() {
                builder.push_bind(value)
            } else {
                builder.push_bind(number.as_f64().unwrap_or_default())
            }
        }
        Value::String(text) => builder.push_bind(text.clone()),
        other => builder.push_bind(other.to_string()),
    };
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn columns() -> std::collections::HashSet<String> {
        ["car_no", "car_type", "remark"]
            .into_iter()
            .map(str::to_string)
            .collect()
    }

    /// Java: Jackson/FastJSON 丢掉非列属性，但 `exist=false` 字段在响应里仍是显式 null。
    #[test]
    fn non_column_keys_are_dropped_before_sql() {
        let body = json!({"carNo": "A", "params": {"beginTime": "x"}, "applyTime1": "y",
                          "unknownZz": 1, "carType": null});
        let kept = filter_entity_columns(&body, &columns());
        assert_eq!(
            kept.as_object().unwrap().keys().collect::<Vec<_>>(),
            vec!["carNo", "carType"],
            "camelCase 键要按同一规则换算成列名再判定"
        );
    }

    #[test]
    fn entity_shape_fills_missing_keys_and_drops_extras() {
        // 上游只给两个字段（桩上游就是这么不完整），实体键全部出现。
        let shaped = entity_shape(
            json!({"bigId": "1", "upstreamOnly": true}),
            &["bigId", "axlecount", "vehicleplate"],
        );
        assert_eq!(
            shaped,
            json!({"bigId": "1", "axlecount": null, "vehicleplate": null})
        );
        // 非对象（null/数组）原样返回：Java 的 data 也就跟着是 null。
        assert_eq!(entity_shape(Value::Null, &["bigId"]), Value::Null);
    }

    /// Java: FastJson2 写缓存是 `@type` 最前 + 字段名字典序 + null 不写；
    /// 形状不对时 Java 会把缓存当 JSONObject 原样透传（docs/03 §9.1）。
    #[test]
    fn cache_rows_match_fastjson2_write_shape() {
        let shaped = fastjson_rows(vec![json!({
            "carNo": "A",
            "updateBy": null,
            "createTime": "2026-11-04 09:02:17",
            "epsId": 25367,
        })]);
        assert_eq!(
            shaped[0].as_object().unwrap().keys().collect::<Vec<_>>(),
            vec!["carNo", "createTime", "epsId"],
            "字典序且不写 null"
        );
        let stamped =
            crate::db::redis_cache::stamp_types(shaped, "com.ruoyi.manager.domain.CarInfo");
        assert_eq!(
            stamped[0].as_object().unwrap().keys().next().unwrap(),
            "@type",
            "@type 必须在最前"
        );
    }

    /// Java: `IdType.INPUT` 的表不生成主键（见 ID_INPUT_TABLES）。
    #[test]
    fn id_input_tables_are_the_java_input_pk_entities() {
        assert!(ID_INPUT_TABLES.contains(&"car_suspicious_back"));
        assert!(
            !ID_INPUT_TABLES.contains(&"car_info"),
            "CarInfoServiceImpl.saveCarInfo 里显式 setUUID，不算 INPUT"
        );
    }

    /// Java: `BigDecimal.intValue()` 是向零截断；DECIMAL 列在 JSON 里是 `1119.0`，
    /// 早先 `as_i64()` 拿不到就返回 0，把 `geometry` 桩号区间比较全部判成不命中
    /// （`/manager/suspicious/{id}` 的 raodTrailList 因此为空）。
    #[test]
    fn java_int_truncates_like_bigdecimal() {
        assert_eq!(java_int(Some(&json!(1119))), 1119);
        assert_eq!(java_int(Some(&json!(1119.0))), 1119);
        assert_eq!(java_int(Some(&json!(1119.9))), 1119);
        assert_eq!(java_int(Some(&json!(-1119.9))), -1119);
        assert_eq!(java_int(Some(&json!("1121.0000"))), 1121);
        assert_eq!(java_int(Some(&json!(""))), 0);
        assert_eq!(java_int(None), 0);
    }
}
