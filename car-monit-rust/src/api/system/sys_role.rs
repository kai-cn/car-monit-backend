// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysRoleController.java
//       ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysRoleServiceImpl.java
// 职责: 角色管理（含数据权限、角色菜单/部门关联、登录态权限刷新）。
// 对应关系: selectRoleList(@DataScope) -> data_scope_sql；insert/update -> 事务。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill};
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const ROLE_COLUMNS: &str = "r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope, \
     r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark, \
     null as createBy, null as updateBy, null as updateTime, 0 as flag, \
     null as menuIds, null as deptIds";

const ROLE_FORMATS: &[(&str, support::FieldFormat)] = &[
    ("roleSort", support::FieldFormat::String),
    ("menuCheckStrictly", support::FieldFormat::Bool),
    ("deptCheckStrictly", support::FieldFormat::Bool),
    ("flag", support::FieldFormat::Bool),
];

/// Java: SysRole.isAdmin() 影响 JSON 的 `admin` 字段；menuIds/deptIds 为 null。
/// Java Jackson 的 SysRole 键序：BaseEntity 在前（含 params），派生 getter（flag/menuIds/deptIds/admin）在最后。
pub(crate) const ROLE_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "roleId",
    "roleName",
    "roleKey",
    "roleSort",
    "dataScope",
    "menuCheckStrictly",
    "deptCheckStrictly",
    "status",
    "delFlag",
    "flag",
    "menuIds",
    "deptIds",
    "admin",
];

pub(crate) fn role_rows(mut rows: Vec<Value>) -> Vec<Value> {
    support::apply_formats(&mut rows, ROLE_FORMATS);
    for row in &mut rows {
        if let Some(object) = row.as_object_mut() {
            let admin = object
                .get("roleId")
                .and_then(Value::as_i64)
                .map(|id| id == 1)
                .unwrap_or(false);
            object.insert("admin".to_string(), Value::Bool(admin));
            object.entry("menuIds").or_insert(Value::Null);
            object.entry("deptIds").or_insert(Value::Null);
        }
    }
    for row in rows.iter_mut() {
        *row = support::reorder_keys(row.take(), ROLE_KEYS);
    }
    rows
}

static LOG_EXPORT: LogSpec = LogSpec::new(
    "角色管理",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysRoleController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "角色管理",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysRoleController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "角色管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysRoleController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "角色管理",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysRoleController.remove()",
);
static LOG_SCOPE: LogSpec = LogSpec::new(
    "角色管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysRoleController.dataScope()",
);
static LOG_STATUS: LogSpec = LogSpec::new(
    "角色管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysRoleController.changeStatus()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/role/list",
            meta::get_route("/system/role/list", None, None, list),
        )
        .route(
            "/system/role/export",
            meta::get_route(
                "/system/role/export",
                Some("system:role:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/role/optionselect",
            meta::get_route(
                "/system/role/optionselect",
                Some("system:role:query"),
                None,
                optionselect,
            ),
        )
        .route(
            "/system/role/selectlist",
            meta::get_route("/system/role/selectlist", None, None, selectlist),
        )
        .route(
            "/system/role/dataScope",
            meta::put_route(
                "/system/role/dataScope",
                Some("system:role:edit"),
                Some(&LOG_SCOPE),
                data_scope,
            ),
        )
        .route(
            "/system/role/changeStatus",
            meta::put_route(
                "/system/role/changeStatus",
                Some("system:role:edit"),
                Some(&LOG_STATUS),
                change_status,
            ),
        )
        .route(
            "/system/role/{roleIds}",
            meta::get_route(
                "/system/role/{roleIds}",
                Some("system:role:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/system/role",
            meta::post_route("/system/role", Some("system:role:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/system/role",
                    Some("system:role:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/system/role/{roleIds}",
            meta::delete_route(
                "/system/role/{roleIds}",
                Some("system:role:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

fn push_role_filters(builder: &mut QueryBuilder<'_, MySql>, params: &HashMap<String, String>) {
    if let Some(value) = params.get("roleName").filter(|value| !value.is_empty()) {
        builder.push(" and r.role_name like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    if let Some(value) = params.get("status").filter(|value| !value.is_empty()) {
        builder.push(" and r.status = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params.get("roleKey").filter(|value| !value.is_empty()) {
        builder.push(" and r.role_key = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params
        .get("params[beginTime]")
        .filter(|value| !value.is_empty())
    {
        builder.push(" and date_format(r.create_time,'%y%m%d') >= date_format(");
        builder.push_bind(value.clone());
        builder.push(", '%y%m%d')");
    }
    if let Some(value) = params
        .get("params[endTime]")
        .filter(|value| !value.is_empty())
    {
        builder.push(" and date_format(r.create_time,'%y%m%d') <= date_format(");
        builder.push_bind(value.clone());
        builder.push(", '%y%m%d')");
    }
}

/// Java: selectRoleVo + 动态条件 + @DataScope（不分页）。
pub(crate) async fn select_roles(
    state: &AppState,
    user: &LoginUser,
    params: &HashMap<String, String>,
) -> Result<Vec<Value>, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select distinct {ROLE_COLUMNS} from sys_role r \
         left join sys_user_role ur on ur.role_id = r.role_id \
         left join sys_user u on u.user_id = ur.user_id \
         left join sys_dept d on u.dept_id = d.dept_id where r.del_flag = '0'"
    ));
    push_role_filters(&mut builder, params);
    if let Some(scope) = support::data_scope_sql(user, "d", None) {
        builder.push(scope);
    }
    builder.push(" order by r.role_sort");
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(role_rows(rows_to_json(&rows)))
}

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let params = support::query_map(&raw);
    let page = support::page_domain(&raw);
    let from = "from sys_role r \
         left join sys_user_role ur on ur.role_id = r.role_id \
         left join sys_user u on u.user_id = ur.user_id \
         left join sys_dept d on u.dept_id = d.dept_id where r.del_flag = '0'";
    let mut count_builder =
        QueryBuilder::<MySql>::new(format!("select count(distinct r.role_id) {from}"));
    push_role_filters(&mut count_builder, &params);
    if let Some(scope) = support::data_scope_sql(&user, "d", None) {
        count_builder.push(scope);
    }
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;

    let mut builder = QueryBuilder::<MySql>::new(format!("select distinct {ROLE_COLUMNS} {from}"));
    push_role_filters(&mut builder, &params);
    if let Some(scope) = support::data_scope_sql(&user, "d", None) {
        builder.push(scope);
    }

    let (offset, limit) = page.resolve(total);
    let mut builder = builder;
    builder.push(" order by r.role_sort");
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(TableDataInfo::new(total, role_rows(rows_to_json(&rows))))
}

async fn export(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = select_roles(&state, &user, &params).await?;
    let headers = [
        "角色序号",
        "角色名称",
        "角色权限",
        "角色排序",
        "数据范围",
        "角色状态",
    ]
    .map(str::to_string);
    let fields = [
        "roleId",
        "roleName",
        "roleKey",
        "roleSort",
        "dataScope",
        "status",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            if let Some(Value::String(text)) = values.get(4).cloned() {
                values[4] = Value::String(match text.as_str() {
                    "1" => "所有数据权限".to_string(),
                    "2" => "自定义数据权限".to_string(),
                    "3" => "本部门数据权限".to_string(),
                    "4" => "本部门及以下数据权限".to_string(),
                    _ => text,
                });
            }
            if let Some(Value::String(text)) = values.get(5).cloned() {
                values[5] = Value::String(match text.as_str() {
                    "0" => "正常".to_string(),
                    "1" => "停用".to_string(),
                    _ => text,
                });
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "角色数据", &headers, &data)
}

async fn optionselect(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
) -> Result<AjaxResult, AppError> {
    let rows = select_roles(&state, &user, &HashMap::new()).await?;
    Ok(AjaxResult::success_data(rows))
}

async fn selectlist(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = select_roles(&state, &user, &params).await?;
    Ok(AjaxResult::success_data(rows))
}

async fn get_info(
    State(state): State<AppState>,
    Path(role_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long roleId`。
    let role_id = support::path_long("roleId", &role_id)?.to_string();
    let row = sqlx::query(&format!(
        "select distinct {ROLE_COLUMNS} from sys_role r \
         left join sys_user_role ur on ur.role_id = r.role_id \
         left join sys_user u on u.user_id = ur.user_id \
         left join sys_dept d on u.dept_id = d.dept_id \
         where r.role_id = ?"
    ))
    .bind(&role_id)
    .fetch_optional(&state.db)
    .await?;
    Ok(AjaxResult::success_data(row.map(|row| {
        role_rows(vec![crate::db::rows::row_to_json(&row)])
            .pop()
            .unwrap_or(Value::Null)
    })))
}

fn text(body: &Value, key: &str) -> String {
    body.get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn id_list(body: &Value, key: &str) -> Vec<i64> {
    body.get(key)
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(|item| {
                    item.as_i64()
                        .or_else(|| item.as_str().and_then(|text| text.parse().ok()))
                })
                .collect()
        })
        .unwrap_or_default()
}

async fn unique_error(
    pool: &MySqlPool,
    body: &Value,
    column: &str,
    key: &str,
    label: &str,
) -> Result<Option<AjaxResult>, AppError> {
    let value = text(body, key);
    if value.is_empty() {
        return Ok(None);
    }
    let sql = format!("select r.role_id from sys_role r where r.{column} = ? limit 1");
    let found: Option<i64> = sqlx::query_scalar(&sql)
        .bind(&value)
        .fetch_optional(pool)
        .await?;
    let current = body.get("roleId").and_then(Value::as_i64).unwrap_or(-1);
    if let Some(found) = found {
        if found != current {
            let verb = if current == -1 { "新增" } else { "修改" };
            return Ok(Some(AjaxResult::error(format!(
                "{verb}角色'{}'失败，{label}已存在",
                text(body, "roleName")
            ))));
        }
    }
    Ok(None)
}

fn check_role_allowed(body: &Value) -> Result<(), AppError> {
    if body.get("roleId").and_then(Value::as_i64) == Some(1) {
        return Err(AppError::Service("不允许操作超级管理员角色".to_string()));
    }
    Ok(())
}

async fn insert_role_menu(
    tx: &mut sqlx::Transaction<'_, MySql>,
    role_id: i64,
    menu_ids: &[i64],
) -> Result<(), AppError> {
    if menu_ids.is_empty() {
        return Ok(());
    }
    let mut builder = QueryBuilder::<MySql>::new("insert into sys_role_menu(role_id, menu_id) ");
    builder.push_values(menu_ids, |mut bind, menu_id| {
        bind.push_bind(role_id).push_bind(*menu_id);
    });
    builder.build().execute(&mut **tx).await?;
    Ok(())
}

async fn insert_role_dept(
    tx: &mut sqlx::Transaction<'_, MySql>,
    role_id: i64,
    dept_ids: &[i64],
) -> Result<(), AppError> {
    if dept_ids.is_empty() {
        return Ok(());
    }
    let mut builder = QueryBuilder::<MySql>::new("insert into sys_role_dept(role_id, dept_id) ");
    builder.push_values(dept_ids, |mut bind, dept_id| {
        bind.push_bind(role_id).push_bind(*dept_id);
    });
    builder.build().execute(&mut **tx).await?;
    Ok(())
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    if text(&body, "roleName").is_empty() {
        return Ok(AjaxResult::error("角色名称不能为空"));
    }
    if text(&body, "roleKey").is_empty() {
        return Ok(AjaxResult::error("权限字符不能为空"));
    }
    if let Some(error) = unique_error(&state.db, &body, "role_name", "roleName", "角色名称").await?
    {
        return Ok(error);
    }
    if let Some(error) = unique_error(&state.db, &body, "role_key", "roleKey", "角色权限").await?
    {
        return Ok(error);
    }

    // `menuIds` 不是 sys_role 的列，要在过滤前先取出来。
    let menu_ids = id_list(&body, "menuIds");
    // Java: Jackson 忽略非实体字段（`params`/`deptIds`/`flag` 等），自己拼 SQL 要先按表列过滤。
    let mut entity = support::entity_for_table(&state.db, "sys_role", &body).await?;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("createTime".to_string(), json!(support::now_string()));
    }

    let mut tx = state.db.begin().await?;
    // insert_entity 不支持外部事务，这里手工拼 SQL 以便同一事务写 sys_role_menu。
    let object = entity.as_object().cloned().unwrap_or_default();
    let mut columns = Vec::new();
    let mut values = Vec::new();
    for (key, value) in object.iter() {
        if value.is_null() || key == "menuIds" || key == "deptIds" || key == "flag" {
            continue;
        }
        columns.push(support::column_name(key));
        values.push(value.clone());
    }
    let mut builder = QueryBuilder::<MySql>::new("insert into sys_role (");
    for (index, column) in columns.iter().enumerate() {
        if index > 0 {
            builder.push(", ");
        }
        builder.push(column.clone());
    }
    builder.push(") values (");
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            builder.push(", ");
        }
        support::bind_value(&mut builder, value);
    }
    builder.push(")");
    builder.build().execute(&mut *tx).await?;
    // LAST_INSERT_ID() 的列元信息是 BIGINT UNSIGNED，只能按 u64 取回。
    let role_id: u64 = sqlx::query_scalar("select last_insert_id()")
        .fetch_one(&mut *tx)
        .await?;
    insert_role_menu(&mut tx, role_id as i64, &menu_ids).await?;
    tx.commit().await?;
    Ok(support::to_ajax(1))
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    check_role_allowed(&body)?;
    if let Some(error) = unique_error(&state.db, &body, "role_name", "roleName", "角色名称").await?
    {
        return Ok(error);
    }
    if let Some(error) = unique_error(&state.db, &body, "role_key", "roleKey", "角色权限").await?
    {
        return Ok(error);
    }
    let role_id = body
        .get("roleId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("roleId不能为空".to_string()))?;
    let menu_ids = id_list(&body, "menuIds");

    let mut entity = support::entity_for_table(&state.db, "sys_role", &body).await?;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
    }
    let mut tx = state.db.begin().await?;
    update_role_row(&mut tx, &entity, role_id).await?;
    sqlx::query("delete from sys_role_menu where role_id = ?")
        .bind(role_id)
        .execute(&mut *tx)
        .await?;
    insert_role_menu(&mut tx, role_id, &menu_ids).await?;
    tx.commit().await?;

    refresh_login_user(&state, &user).await?;
    Ok(AjaxResult::success())
}

async fn update_role_row(
    tx: &mut sqlx::Transaction<'_, MySql>,
    entity: &Value,
    role_id: i64,
) -> Result<(), AppError> {
    let Some(object) = entity.as_object() else {
        return Ok(());
    };
    let mut builder = QueryBuilder::<MySql>::new("update sys_role set ");
    let mut first = true;
    for (key, value) in object.iter() {
        if value.is_null() || matches!(key.as_str(), "roleId" | "menuIds" | "deptIds" | "flag") {
            continue;
        }
        if !first {
            builder.push(", ");
        }
        first = false;
        builder.push(format!("{} = ", support::column_name(key)));
        support::bind_value(&mut builder, value);
    }
    if first {
        return Ok(());
    }
    builder.push(", update_time = sysdate() where role_id = ");
    builder.push_bind(role_id);
    builder.build().execute(&mut **tx).await?;
    Ok(())
}

async fn data_scope(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    check_role_allowed(&body)?;
    let role_id = body
        .get("roleId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("roleId不能为空".to_string()))?;
    let dept_ids = id_list(&body, "deptIds");
    let mut tx = state.db.begin().await?;
    update_role_row(&mut tx, &body, role_id).await?;
    sqlx::query("delete from sys_role_dept where role_id = ?")
        .bind(role_id)
        .execute(&mut *tx)
        .await?;
    insert_role_dept(&mut tx, role_id, &dept_ids).await?;
    tx.commit().await?;
    Ok(support::to_ajax(1))
}

async fn change_status(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    check_role_allowed(&body)?;
    if body.get("roleId").and_then(Value::as_i64).is_none() {
        // Java: where role_id = null 命中 0 行 -> toAjax(0) -> "操作失败"。
        return Ok(AjaxResult::error("操作失败"));
    }
    let mut entity = support::entity_for_table(&state.db, "sys_role", &body).await?;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
    }
    let rows =
        support::update_entity_by_id(&state.db, "sys_role", "role_id", &entity, AutoFill::NONE)
            .await?;
    Ok(support::to_ajax(rows))
}

async fn remove(
    State(state): State<AppState>,
    Path(role_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] roleIds` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("roleIds", &role_ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    for id in &ids {
        if id == "1" {
            return Err(AppError::Service("不允许操作超级管理员角色".to_string()));
        }
        let count: i64 = sqlx::query_scalar("select count(1) from sys_user_role where role_id = ?")
            .bind(id)
            .fetch_one(&state.db)
            .await?;
        if count > 0 {
            let name: Option<String> =
                sqlx::query_scalar("select role_name from sys_role where role_id = ?")
                    .bind(id)
                    .fetch_optional(&state.db)
                    .await?;
            return Err(AppError::Service(format!(
                "{}已分配,不能删除",
                name.unwrap_or_default()
            )));
        }
    }
    let mut tx = state.db.begin().await?;
    let mut builder = QueryBuilder::<MySql>::new("delete from sys_role_menu where role_id in (");
    let mut separated = builder.separated(", ");
    for id in &ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    builder.build().execute(&mut *tx).await?;
    let mut builder = QueryBuilder::<MySql>::new("delete from sys_role_dept where role_id in (");
    let mut separated = builder.separated(", ");
    for id in &ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    builder.build().execute(&mut *tx).await?;
    let mut builder =
        QueryBuilder::<MySql>::new("update sys_role set del_flag = '2' where role_id in (");
    let mut separated = builder.separated(", ");
    for id in &ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    let rows = builder.build().execute(&mut *tx).await?.rows_affected();
    tx.commit().await?;
    Ok(support::to_ajax(rows))
}

/// Java: 角色修改后刷新当前登录用户的权限缓存（仅非管理员）。
async fn refresh_login_user(state: &AppState, user: &LoginUser) -> Result<(), AppError> {
    if user.user.is_admin() {
        return Ok(());
    }
    let Some(user_name) = user.user.user_name.clone() else {
        return Ok(());
    };
    let Some(refreshed) =
        crate::repository::user_repo::select_user_by_user_name(&state.db, &user_name).await?
    else {
        return Ok(());
    };
    let permissions = match refreshed.user_id {
        Some(user_id) => {
            crate::repository::user_repo::select_menu_perms_for_user(&state.db, user_id).await?
        }
        None => Vec::new(),
    };
    let mut login_user = user.clone();
    login_user.user = refreshed;
    login_user.permissions = permissions;
    let ttl = login_user.expire_time - chrono::Utc::now().timestamp_millis();
    let seconds = (ttl / 1000).max(1) as u64;
    // Java: TokenService.setLoginUser —— 以相同 key 覆盖缓存，保留原过期窗口。
    let stored = login_user.clone().for_redis();
    state
        .redis
        .set_object_ttl(
            &format!("login_tokens:{}", login_user.token),
            &stored,
            Some(std::time::Duration::from_secs(seconds)),
        )
        .await?;
    Ok(())
}
