// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysMenuController.java
//       ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysMenuServiceImpl.java
// 职责: 菜单管理（列表/树/角色菜单树/CRUD）。
// 对应关系: selectMenuList/buildMenuTreeSelect/selectMenuListByRoleId -> 本地 SQL + JSON 树。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill};
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

/// Java: `selectMenuVo` 的列（与 resultMap 对齐）。
const MENU_COLUMNS: &str = "m.menu_id, m.menu_name, m.parent_id, m.order_num, m.path, \
     m.component, m.is_frame, m.is_cache, m.menu_type, m.visible, m.status, \
     ifnull(m.perms, '') as perms, m.icon, m.create_time, \n     null as createBy, null as updateBy, null as updateTime, null as remark, null as parentName";

static LOG_ADD: LogSpec = LogSpec::new(
    "菜单管理",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysMenuController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "菜单管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysMenuController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "菜单管理",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysMenuController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/menu/list",
            meta::get_route("/system/menu/list", Some("system:menu:list"), None, list),
        )
        .route(
            "/system/menu/treeselect",
            meta::get_route("/system/menu/treeselect", None, None, treeselect),
        )
        .route(
            "/system/menu/roleMenuTreeselect/{roleId}",
            meta::get_route(
                "/system/menu/roleMenuTreeselect/{roleId}",
                None,
                None,
                role_menu_treeselect,
            ),
        )
        .route(
            "/system/menu/{menuId}",
            meta::get_route(
                "/system/menu/{menuId}",
                Some("system:menu:query"),
                None,
                get_info,
            )
            .merge(meta::delete_route(
                "/system/menu/{menuId}",
                Some("system:menu:remove"),
                Some(&LOG_REMOVE),
                remove,
            )),
        )
        .route(
            "/system/menu",
            meta::post_route("/system/menu", Some("system:menu:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/system/menu",
                    Some("system:menu:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
}

/// Java Jackson 的 SysMenu 键序：BaseEntity 在前（含 params），`children` 是派生 getter 所以最后。
const MENU_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "menuId",
    "menuName",
    "parentName",
    "parentId",
    "orderNum",
    "path",
    "component",
    "isFrame",
    "isCache",
    "menuType",
    "visible",
    "status",
    "perms",
    "icon",
    "children",
];

/// Java: selectMenuList(menu, userId) —— 管理员查全部，普通用户按角色过滤。
/// Java SysMenu：orderNum/isFrame/isCache 为 String，children 初始化为空集合。
fn shape_menu_rows(rows: &mut [Value]) {
    support::apply_formats(
        rows,
        &[
            ("orderNum", support::FieldFormat::String),
            ("isFrame", support::FieldFormat::String),
            ("isCache", support::FieldFormat::String),
        ],
    );
    for row in rows.iter_mut() {
        if let Some(object) = row.as_object_mut() {
            object.entry("children").or_insert_with(|| json!([]));
        }
    }
    for row in rows.iter_mut() {
        *row = support::reorder_keys(row.take(), MENU_KEYS);
    }
}

async fn select_menu_list(
    state: &AppState,
    params: &HashMap<String, String>,
    user_id: i64,
) -> Result<Vec<Value>, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(format!("select {MENU_COLUMNS} from sys_menu m"));
    if user_id != 1 {
        builder.push(
            " left join sys_role_menu rm on m.menu_id = rm.menu_id \
             left join sys_user_role ur on rm.role_id = ur.role_id \
             left join sys_role ro on ur.role_id = ro.role_id",
        );
    }
    builder.push(" where 1=1");
    if user_id != 1 {
        builder.push(" and ur.user_id = ");
        builder.push_bind(user_id);
        builder.push(" and ro.status = '0'");
    }
    if let Some(value) = params.get("menuName").filter(|value| !value.is_empty()) {
        builder.push(" and m.menu_name like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    if let Some(value) = params.get("visible").filter(|value| !value.is_empty()) {
        builder.push(" and m.visible = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params.get("status").filter(|value| !value.is_empty()) {
        builder.push(" and m.status = ");
        builder.push_bind(value.clone());
    }
    builder.push(" order by m.parent_id, m.order_num");
    let rows = builder.build().fetch_all(&state.db).await?;
    let mut rows = rows_to_json(&rows);
    shape_menu_rows(&mut rows);
    Ok(rows)
}

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let user_id = user.user.user_id.unwrap_or_default();
    let menus = select_menu_list(&state, &params, user_id).await?;
    Ok(AjaxResult::success_data(menus))
}

async fn treeselect(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let user_id = user.user.user_id.unwrap_or_default();
    let menus = select_menu_list(&state, &params, user_id).await?;
    Ok(AjaxResult::success_data(tree_select(&menus, 0)))
}

async fn role_menu_treeselect(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Path(role_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let user_id = user.user.user_id.unwrap_or_default();
    let menus = select_menu_list(&state, &HashMap::new(), user_id).await?;
    let checked = select_menu_ids_by_role(&state, &role_id).await?;
    let mut result = AjaxResult::success();
    result.insert_value("checkedKeys", json!(checked));
    result.insert_value("menus", json!(tree_select(&menus, 0)));
    Ok(result)
}

/// Java: selectMenuListByRoleId(roleId) —— 依赖角色的 menuCheckStrictly。
async fn select_menu_ids_by_role(
    state: &AppState,
    role_id: &str,
) -> Result<Vec<i64>, AppError> {
    let strict: Option<bool> = sqlx::query_scalar(
        "select menu_check_strictly from sys_role where role_id = ?",
    )
    .bind(role_id)
    .fetch_optional(&state.db)
    .await?;
    let mut sql = String::from(
        "select m.menu_id from sys_menu m left join sys_role_menu rm on m.menu_id = rm.menu_id \
         where rm.role_id = ?",
    );
    if strict.unwrap_or(false) {
        sql.push_str(
            " and m.menu_id not in (select m.parent_id from sys_menu m \
             inner join sys_role_menu rm on m.menu_id = rm.menu_id and rm.role_id = ?)",
        );
    }
    sql.push_str(" order by m.parent_id, m.order_num");
    let mut query = sqlx::query_scalar::<_, i64>(&sql).bind(role_id);
    if strict.unwrap_or(false) {
        query = query.bind(role_id);
    }
    Ok(query.fetch_all(&state.db).await?)
}

/// Java: TreeSelect —— 空 children 不输出。
fn tree_select(menus: &[Value], parent_id: i64) -> Vec<Value> {
    let mut nodes = Vec::new();
    for menu in menus {
        let current_parent = menu.get("parentId").and_then(Value::as_i64).unwrap_or(0);
        if current_parent != parent_id {
            continue;
        }
        let id = menu.get("menuId").and_then(Value::as_i64).unwrap_or_default();
        let mut node = json!({
            "id": id,
            "label": menu.get("menuName").cloned().unwrap_or(Value::Null),
        });
        let children = tree_select(menus, id);
        if !children.is_empty() {
            node["children"] = json!(children);
        }
        nodes.push(node);
    }
    nodes
}

async fn get_info(
    State(state): State<AppState>,
    Path(menu_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let row = sqlx::query(&format!("select {MENU_COLUMNS} from sys_menu m where m.menu_id = ?"))
        .bind(&menu_id)
        .fetch_optional(&state.db)
        .await?;
    Ok(AjaxResult::success_data(row.map(|row| {
        let mut rows = vec![crate::db::rows::row_to_json(&row)];
        shape_menu_rows(&mut rows);
        rows.pop().unwrap_or(serde_json::Value::Null)
    })))
}

fn text(body: &Value, key: &str) -> String {
    body.get(key).and_then(Value::as_str).unwrap_or_default().trim().to_string()
}

async fn validate_and_save(
    state: &AppState,
    user: &LoginUser,
    body: Value,
    is_add: bool,
) -> Result<AjaxResult, AppError> {
    let menu_name = text(&body, "menuName");
    if menu_name.is_empty() {
        return Ok(AjaxResult::error("菜单名称不能为空"));
    }
    let parent_id = body.get("parentId").and_then(Value::as_i64).unwrap_or(0);
    let found: Option<i64> = sqlx::query_scalar(
        "select menu_id from sys_menu where menu_name = ? and parent_id = ? limit 1",
    )
    .bind(&menu_name)
    .bind(parent_id)
    .fetch_optional(&state.db)
    .await?;
    let current = body.get("menuId").and_then(Value::as_i64).unwrap_or(-1);
    if let Some(found) = found {
        if found != current {
            let verb = if is_add { "新增" } else { "修改" };
            return Ok(AjaxResult::error(format!(
                "{verb}菜单'{menu_name}'失败，菜单名称已存在"
            )));
        }
    }
    if text(&body, "isFrame") == "0" {
        let path = text(&body, "path");
        if !(path.starts_with("http://") || path.starts_with("https://")) {
            let verb = if is_add { "新增" } else { "修改" };
            return Ok(AjaxResult::error(format!(
                "{verb}菜单'{menu_name}'失败，地址必须以http(s)://开头"
            )));
        }
    }
    if !is_add {
        let menu_id = body.get("menuId").and_then(Value::as_i64);
        if menu_id == Some(parent_id) {
            return Ok(AjaxResult::error(format!(
                "修改菜单'{menu_name}'失败，上级菜单不能选择自己"
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
        support::insert_entity(&state.db, "sys_menu", &entity, AutoFill::NONE).await?
    } else {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
        support::update_entity_by_id(&state.db, "sys_menu", "menu_id", &entity, AutoFill::NONE)
            .await?
    };
    Ok(support::to_ajax(rows))
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
    Path(menu_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let children: i64 = sqlx::query_scalar("select count(1) from sys_menu where parent_id = ?")
        .bind(&menu_id)
        .fetch_one(&state.db)
        .await?;
    if children > 0 {
        return Ok(AjaxResult::error("存在子菜单,不允许删除"));
    }
    let assigned: i64 =
        sqlx::query_scalar("select count(1) from sys_role_menu where menu_id = ?")
            .bind(&menu_id)
            .fetch_one(&state.db)
            .await?;
    if assigned > 0 {
        return Ok(AjaxResult::error("菜单已分配,不允许删除"));
    }
    let rows = support::delete_by_ids(&state.db, "sys_menu", "menu_id", &[menu_id]).await?;
    Ok(support::to_ajax(rows))
}
