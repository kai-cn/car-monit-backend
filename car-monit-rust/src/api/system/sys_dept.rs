// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDeptController.java
//       ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDeptServiceImpl.java
// 职责: 部门管理：列表/树/角色部门树/CRUD（含 sub_code 与 tenant_id 维护）。
// 对应关系: @DataScope -> support::data_scope_sql；buildDeptTreeSelect -> JSON 树。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support;
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

const DEPT_COLUMNS: &str = "d.dept_id, d.parent_id, d.ancestors, d.dept_name, d.order_num, \
     d.leader_id, d.leader, d.fgld_id, d.fgld_name, d.bank_name, d.account, d.social_code, \
     d.postal_code, d.address, d.phone, d.email, d.status, d.del_flag, d.create_by, \
     d.create_time, d.is_zbzg, d.is_uint, d.tree_leavel, d.sub_code, d.dept_jc, d.tenant_id, \n     null as updateBy, null as updateTime, null as remark, null as parentName, \n     null as flag, null as dataId, null as deptSubCode";

static LOG_ADD: LogSpec = LogSpec::new(
    "部门管理",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysDeptController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "部门管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysDeptController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "部门管理",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysDeptController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/dept/list",
            meta::get_route("/system/dept/list", Some("system:dept:list"), None, list),
        )
        .route(
            "/system/dept/getList",
            meta::get_route("/system/dept/getList", None, None, list),
        )
        .route(
            "/system/dept/list/exclude/{deptId}",
            meta::get_route(
                "/system/dept/list/exclude/{deptId}",
                Some("system:dept:list"),
                None,
                exclude_child,
            ),
        )
        .route(
            "/system/dept/treeselect",
            meta::get_route("/system/dept/treeselect", None, None, treeselect),
        )
        .route(
            "/system/dept/treeselectNew",
            meta::get_route("/system/dept/treeselectNew", None, None, treeselect_new),
        )
        .route(
            "/system/dept/roleDeptTreeselect/{roleId}",
            meta::get_route(
                "/system/dept/roleDeptTreeselect/{roleId}",
                None,
                None,
                role_dept_treeselect,
            ),
        )
        .route(
            "/system/dept/getCompanyList",
            meta::get_route("/system/dept/getCompanyList", None, None, company_list),
        )
        .route(
            "/system/dept/{deptId}",
            meta::get_route(
                "/system/dept/{deptId}",
                Some("system:dept:query"),
                None,
                get_info,
            )
            .merge(meta::delete_route(
                "/system/dept/{deptId}",
                Some("system:dept:remove"),
                Some(&LOG_REMOVE),
                remove,
            )),
        )
        .route(
            "/system/dept",
            meta::post_route("/system/dept", Some("system:dept:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/system/dept",
                    Some("system:dept:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
}

/// Java: selectDeptList —— del_flag='0' + 动态条件 + @DataScope。
/// Java SysDept：orderNum 是 String，children 初始化为空集合。
fn shape_dept_rows(rows: &mut [Value]) {
    support::apply_formats(rows, &[("orderNum", support::FieldFormat::String)]);
    for row in rows {
        if let Some(object) = row.as_object_mut() {
            object.entry("children").or_insert_with(|| json!([]));
        }
    }
}

async fn select_dept_list(
    state: &AppState,
    user: &LoginUser,
    params: &HashMap<String, String>,
) -> Result<Vec<Value>, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {DEPT_COLUMNS} from sys_dept d where d.del_flag = '0'"
    ));
    push_dept_filters(&mut builder, params);
    if let Some(scope) = support::data_scope_sql(user, "d", None) {
        builder.push(scope);
    }
    builder.push(" order by d.parent_id, d.order_num");
    let rows = builder.build().fetch_all(&state.db).await?;
    let mut rows = rows_to_json(&rows);
    shape_dept_rows(&mut rows);
    Ok(rows)
}

fn push_dept_filters(builder: &mut QueryBuilder<'_, MySql>, params: &HashMap<String, String>) {
    let eq = |builder: &mut QueryBuilder<'_, MySql>, column: &str, key: &str, allow_empty: bool| {
        if let Some(value) = params.get(key).filter(|value| allow_empty || !value.is_empty()) {
            builder.push(format!(" and {column} = "));
            builder.push_bind(value.clone());
        }
    };
    eq(builder, "d.parent_id", "parentId", true);
    eq(builder, "d.status", "status", false);
    eq(builder, "d.dept_id", "deptId", true);
    eq(builder, "d.is_zbzg", "isZbzg", false);
    eq(builder, "d.is_uint", "isUint", false);
    eq(builder, "d.tree_leavel", "treeLeavel", true);
    eq(builder, "d.sub_code", "subCode", false);
    eq(builder, "d.dept_jc", "deptJc", false);
    eq(builder, "d.tenant_id", "tenantId", true);
    eq(builder, "d.leader_id", "leaderId", true);
    eq(builder, "d.leader", "leader", false);
    eq(builder, "d.fgld_id", "fgldId", true);

    for (key, column, prefix) in [
        ("deptName", "d.dept_name", false),
        ("fgldName", "d.fgld_name", false),
        ("deptSubCode", "d.sub_code", true),
    ] {
        if let Some(value) = params.get(key).filter(|value| !value.is_empty()) {
            if prefix {
                builder.push(format!(" and {column} like concat("));
                builder.push_bind(value.clone());
                builder.push(", '%')");
            } else {
                builder.push(format!(" and {column} like concat('%', "));
                builder.push_bind(value.clone());
                builder.push(", '%')");
            }
        }
    }

    // Java: flag == 'sjzbDept' 的特殊过滤。
    if params.get("flag").map(String::as_str) == Some("sjzbDept") {
        builder.push(
            " and exists (select 1 from sys_dept tb, sys_dept tb1 \
             where tb.del_flag = '0' and tb.del_flag = '0' and tb1.dept_id = tb.parent_id \
             and tb.dept_id = ",
        );
        builder.push_bind(params.get("dataId").cloned().unwrap_or_default());
        builder.push(" and tb1.dept_id = d.tenant_id)");
    }
}

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let depts = select_dept_list(&state, &user, &params).await?;
    Ok(AjaxResult::success_data(depts))
}

async fn exclude_child(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Path(dept_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let depts = select_dept_list(&state, &user, &HashMap::new()).await?;
    if let Ok(dept_id_num) = dept_id.parse::<i64>() {
        let filtered = depts
            .into_iter()
            .filter(|dept| {
                let id = dept.get("deptId").and_then(Value::as_i64).unwrap_or_default();
                if id == dept_id_num {
                    return false;
                }
                let ancestors = dept.get("ancestors").and_then(Value::as_str).unwrap_or_default();
                !ancestors.split(',').any(|item| item == dept_id.to_string())
            })
            .collect::<Vec<_>>();
        return Ok(AjaxResult::success_data(filtered));
    }
    Ok(AjaxResult::success_data(depts))
}

async fn treeselect(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let depts = select_dept_list(&state, &user, &params).await?;
    Ok(AjaxResult::success_data(build_tree_select(&depts)))
}

async fn treeselect_new(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let mut params = support::query_map(&raw);
    let flag = params.get("flag").cloned().unwrap_or_default();
    let tenant_id = user.user.tenant_id.unwrap_or_default();
    match flag.as_str() {
        "myDept" | "myDeptCg" => {
            params.insert("tenantId".to_string(), tenant_id.to_string());
        }
        "sjzbDept" | "sjzbDeptCg" => {
            params.insert("dataId".to_string(), tenant_id.to_string());
        }
        "isUint" => {
            params.insert("isUint".to_string(), "1".to_string());
        }
        "allDept" => {}
        "onlyMyDept" => {
            params.insert(
                "deptId".to_string(),
                user.user.dept_id.unwrap_or_default().to_string(),
            );
        }
        _ => {
            params.insert("deptId".to_string(), "-1".to_string());
        }
    }
    let depts = select_dept_list(&state, &user, &params).await?;
    Ok(AjaxResult::success_data(build_tree_select(&depts)))
}

async fn role_dept_treeselect(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Path(role_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let depts = select_dept_list(&state, &user, &HashMap::new()).await?;
    let checked = select_dept_ids_by_role(&state, &role_id).await?;
    let mut result = AjaxResult::success();
    result.insert_value("checkedKeys", json!(checked));
    result.insert_value("depts", json!(build_tree_select(&depts)));
    Ok(result)
}

async fn company_list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
) -> Result<AjaxResult, AppError> {
    let mut params = HashMap::new();
    params.insert("isUint".to_string(), "1".to_string());
    Ok(AjaxResult::success_data(
        select_dept_list(&state, &user, &params).await?,
    ))
}

async fn get_info(
    State(state): State<AppState>,
    Path(dept_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let row = sqlx::query(&format!(
        "select {DEPT_COLUMNS} from sys_dept d where d.dept_id = ?"
    ))
    .bind(&dept_id)
    .fetch_optional(&state.db)
    .await?;
    Ok(AjaxResult::success_data(row.map(|row| {
        let mut rows = vec![crate::db::rows::row_to_json(&row)];
        shape_dept_rows(&mut rows);
        rows.pop().unwrap_or(Value::Null)
    })))
}

async fn select_dept_ids_by_role(
    state: &AppState,
    role_id: &str,
) -> Result<Vec<i64>, AppError> {
    let strict: Option<bool> =
        sqlx::query_scalar("select dept_check_strictly from sys_role where role_id = ?")
            .bind(role_id)
            .fetch_optional(&state.db)
            .await?;
    let mut sql = String::from(
        "select d.dept_id from sys_dept d left join sys_role_dept rd on d.dept_id = rd.dept_id \
         where rd.role_id = ?",
    );
    if strict.unwrap_or(false) {
        sql.push_str(
            " and d.dept_id not in (select d.parent_id from sys_dept d \
             inner join sys_role_dept rd on d.dept_id = rd.dept_id and rd.role_id = ?)",
        );
    }
    sql.push_str(" order by d.parent_id, d.order_num");
    let mut query = sqlx::query_scalar::<_, i64>(&sql).bind(role_id);
    if strict.unwrap_or(false) {
        query = query.bind(role_id);
    }
    Ok(query.fetch_all(&state.db).await?)
}

/// Java: buildDeptTree + TreeSelect。
fn build_tree_select(depts: &[Value]) -> Vec<Value> {
    let ids = depts
        .iter()
        .filter_map(|dept| dept.get("deptId").and_then(Value::as_i64))
        .collect::<Vec<_>>();
    let roots = depts
        .iter()
        .filter(|dept| {
            let parent = dept.get("parentId").and_then(Value::as_i64).unwrap_or(0);
            !ids.contains(&parent)
        })
        .collect::<Vec<_>>();
    let roots = if roots.is_empty() {
        depts.iter().collect::<Vec<_>>()
    } else {
        roots
    };
    roots.iter().map(|dept| dept_node(depts, dept)).collect()
}

fn dept_node(depts: &[Value], dept: &Value) -> Value {
    let id = dept.get("deptId").and_then(Value::as_i64).unwrap_or_default();
    let mut node = json!({
        "id": id,
        "label": dept.get("deptName").cloned().unwrap_or(Value::Null),
    });
    let children = depts
        .iter()
        .filter(|child| child.get("parentId").and_then(Value::as_i64) == Some(id))
        .map(|child| dept_node(depts, child))
        .collect::<Vec<_>>();
    if !children.is_empty() {
        node["children"] = json!(children);
    }
    node
}

fn text(body: &Value, key: &str) -> String {
    body.get(key).and_then(Value::as_str).unwrap_or_default().trim().to_string()
}

/// Java: 新增/修改共用 sub_code、tree_leavel 计算。
async fn compute_sub_code(
    pool: &MySqlPool,
    parent_id: i64,
    dept_id: Option<i64>,
) -> Result<(i32, String), AppError> {
    let (tree_level, parent_sub_code) = if parent_id == 0 {
        (1, "001".to_string())
    } else {
        let parent: Option<(Option<i32>, Option<String>)> = sqlx::query_as(
            "select tree_leavel, sub_code from sys_dept where dept_id = ?",
        )
        .bind(parent_id)
        .fetch_optional(pool)
        .await?;
        let (level, sub) = parent.unwrap_or((None, None));
        (level.unwrap_or(0) + 1, sub.unwrap_or_default())
    };

    let mut recompute = true;
    if let Some(dept_id) = dept_id {
        let current_parent: Option<i64> =
            sqlx::query_scalar("select parent_id from sys_dept where dept_id = ?")
                .bind(dept_id)
                .fetch_optional(pool)
                .await?;
        if current_parent == Some(parent_id) {
            recompute = false;
        }
    }
    if !recompute {
        return Ok((tree_level, String::new()));
    }

    let counts: i64 = sqlx::query_scalar(
        "select count(1) from sys_dept where del_flag = '0' and parent_id = ?",
    )
    .bind(parent_id)
    .fetch_one(pool)
    .await?;
    let sub_code = if parent_id == 0 {
        format!("00{}", counts + 1)
    } else if counts < 9 {
        format!("{parent_sub_code}-00{}", counts + 1)
    } else if counts < 99 {
        format!("{parent_sub_code}-0{}", counts + 1)
    } else {
        format!("{parent_sub_code}-{}", counts + 1)
    };
    Ok((tree_level, sub_code))
}

async fn save(
    state: &AppState,
    user: &LoginUser,
    body: Value,
    is_add: bool,
) -> Result<AjaxResult, AppError> {
    let dept_name = text(&body, "deptName");
    if dept_name.is_empty() {
        return Ok(AjaxResult::error("部门名称不能为空"));
    }
    let parent_id = body
        .get("parentId")
        .and_then(Value::as_i64)
        .filter(|value| *value != 0)
        .unwrap_or(0);
    let dept_id = body.get("deptId").and_then(Value::as_i64);

    let found: Option<i64> = sqlx::query_scalar(
        "select dept_id from sys_dept where dept_name = ? and parent_id = ? limit 1",
    )
    .bind(&dept_name)
    .bind(parent_id)
    .fetch_optional(&state.db)
    .await?;
    if let Some(found) = found {
        if Some(found) != dept_id {
            let verb = if is_add { "新增" } else { "修改" };
            return Ok(AjaxResult::error(format!(
                "{verb}部门'{dept_name}'失败，部门名称已存在"
            )));
        }
    }
    if !is_add {
        if dept_id == Some(parent_id) && parent_id != 0 {
            return Ok(AjaxResult::error(format!(
                "修改部门'{dept_name}'失败，上级部门不能是自己"
            )));
        }
        if text(&body, "status") == "1" {
            let dept_id_value = dept_id.unwrap_or_default();
            let normal_children: i64 = sqlx::query_scalar(
                "select count(*) from sys_dept where status = 0 and del_flag = '0' \
                 and find_in_set(?, ancestors)",
            )
            .bind(dept_id_value)
            .fetch_one(&state.db)
            .await?;
            if normal_children > 0 {
                return Ok(AjaxResult::error("该部门包含未停用的子部门！"));
            }
        }
    }

    let (tree_level, sub_code) = compute_sub_code(&state.db, parent_id, dept_id).await?;
    let is_unit = text(&body, "isUint");

    let mut entity = body;
    let object = entity
        .as_object_mut()
        .ok_or_else(|| AppError::BadRequest("请求体必须是 JSON 对象".to_string()))?;
    object.insert("parentId".to_string(), json!(parent_id));
    object.insert("treeLeavel".to_string(), json!(tree_level));
    if !sub_code.is_empty() {
        object.insert("subCode".to_string(), json!(sub_code));
    }
    if is_unit == "0" {
        object.insert("isZbzg".to_string(), json!("0"));
    }

    let mut tx = state.db.begin().await?;
    let dept_id = if is_add {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("createTime".to_string(), json!(support::now_string()));
        let mut builder = QueryBuilder::<MySql>::new("insert into sys_dept (");
        let mut columns = Vec::new();
        let mut values = Vec::new();
        for (key, value) in object.iter() {
            if value.is_null() {
                continue;
            }
            columns.push(support::column_name(key));
            values.push(value.clone());
        }
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
        let inserted: i64 = sqlx::query_scalar("select last_insert_id()")
            .fetch_one(&mut *tx)
            .await?;
        inserted
    } else {
        let current = dept_id.ok_or_else(|| AppError::Service("deptId不能为空".to_string()))?;
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
        let mut builder = QueryBuilder::<MySql>::new("update sys_dept set ");
        let mut first = true;
        for (key, value) in object.iter() {
            if value.is_null() || key == "deptId" {
                continue;
            }
            if !first {
                builder.push(", ");
            }
            first = false;
            builder.push(format!("{} = ", support::column_name(key)));
            support::bind_value(&mut builder, value);
        }
        builder.push(" where dept_id = ");
        builder.push_bind(current);
        builder.build().execute(&mut *tx).await?;
        current
    };

    // Java: 新增后按 is_uint 设置 tenant_id；修改后按 sub_code 批量刷新租户。
    if is_add {
        if is_unit == "0" {
            let sub_code = object.get("subCode").and_then(Value::as_str).unwrap_or_default();
            if let Some(tenant) = select_tenant(&mut tx, sub_code).await? {
                sqlx::query("update sys_dept set tenant_id = ? where dept_id = ?")
                    .bind(tenant)
                    .bind(dept_id)
                    .execute(&mut *tx)
                    .await?;
            }
        } else {
            sqlx::query("update sys_dept set tenant_id = ? where dept_id = ?")
                .bind(dept_id)
                .bind(dept_id)
                .execute(&mut *tx)
                .await?;
        }
    } else {
        let sub_code = object
            .get("subCode")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        // Java: updateTenantId(dept.getSubCode()) —— subCode 为空时刷新全部部门。
        refresh_tenants(&mut tx, &sub_code).await?;
    }
    tx.commit().await?;

    Ok(support::to_ajax(1))
}

/// Java: `selectTenantId` —— sub_code 前缀匹配的最近一个单位。
async fn select_tenant(
    tx: &mut sqlx::Transaction<'_, MySql>,
    sub_code: &str,
) -> Result<Option<i64>, AppError> {
    let tenant: Option<i64> = sqlx::query_scalar(
        "select d.dept_id from sys_dept d where d.del_flag = '0' \
         and ? like concat(d.sub_code, '%') and d.is_uint = '1' \
         order by d.tree_leavel desc limit 1",
    )
    .bind(sub_code)
    .fetch_optional(&mut **tx)
    .await?;
    Ok(tenant)
}

/// Java: `updateTenantId(deptSubCode)` —— 子部门刷新 tenant_id。
async fn refresh_tenants(
    tx: &mut sqlx::Transaction<'_, MySql>,
    sub_code: &str,
) -> Result<(), AppError> {
    let mut builder = sqlx::QueryBuilder::<MySql>::new(
        "select dept_id, sub_code, is_uint from sys_dept where del_flag = '0'",
    );
    if !sub_code.is_empty() {
        builder.push(" and sub_code like concat(");
        builder.push_bind(sub_code.to_string());
        builder.push(", '%')");
    }
    let rows: Vec<(i64, Option<String>, Option<String>)> =
        builder.build_query_as().fetch_all(&mut **tx).await?;
    for (dept_id, child_sub_code, is_unit) in rows {
        if is_unit.as_deref() == Some("0") {
            if let Some(tenant) = select_tenant(tx, child_sub_code.as_deref().unwrap_or_default()).await? {
                sqlx::query("update sys_dept set tenant_id = ? where dept_id = ?")
                    .bind(tenant)
                    .bind(dept_id)
                    .execute(&mut **tx)
                    .await?;
            }
        } else {
            sqlx::query("update sys_dept set tenant_id = ? where dept_id = ?")
                .bind(dept_id)
                .bind(dept_id)
                .execute(&mut **tx)
                .await?;
        }
    }
    Ok(())
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
    Path(dept_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let children: i64 = sqlx::query_scalar(
        "select count(1) from sys_dept where del_flag = '0' and parent_id = ? limit 1",
    )
    .bind(&dept_id)
    .fetch_one(&state.db)
    .await?;
    if children > 0 {
        return Ok(AjaxResult::error("存在下级部门,不允许删除"));
    }
    let users: i64 =
        sqlx::query_scalar("select count(1) from sys_user where dept_id = ? and del_flag = '0'")
            .bind(&dept_id)
            .fetch_one(&state.db)
            .await?;
    if users > 0 {
        return Ok(AjaxResult::error("部门存在用户,不允许删除"));
    }
    let rows = sqlx::query("update sys_dept set del_flag = '2' where dept_id = ?")
        .bind(&dept_id)
        .execute(&state.db)
        .await?
        .rows_affected();
    Ok(support::to_ajax(rows))
}
