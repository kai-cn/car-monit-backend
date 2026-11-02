// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexMenuController.java
//       ruoyi-system/src/main/resources/mapper/system/SysIndexMenuMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysIndexMenuServiceImpl.java
// 职责: 用户常用菜单（sys_index_menu）查询与维护。
// 对应关系: list/mylist/export/getInfo/add/edit/remove。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill, ListSpec};
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.ID as id, t.USER_ID as userId, t.MENU_ID as menuId, t.SORT as sort, \
             t.EPS_ID as epsId, t.DEL_FLAG as delFlag, t.CREATE_BY as createBy, \
             t.CREATE_TIME as createTime, t.UPDATE_BY as updateBy, \
             t.UPDATE_TIME as updateTime, t.TENANT_ID as tenantId, \
             null as menuName, null as menuName1, null as menuName2, null as menuName3, \
             null as menuIds, null as menuUrl, null as remark, null as deptSubCode, \
             null as flag, null as searchValue, null as params",
    from: "from sys_index_menu t",
    filters: &[],
    extra_where: "",
    order_by: "",
    id_column: "t.ID",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "用户常用菜单",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysIndexMenuController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "用户常用菜单",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysIndexMenuController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "用户常用菜单",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysIndexMenuController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "用户常用菜单",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysIndexMenuController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/indexmenu/list",
            meta::get_route("/system/indexmenu/list", None, None, list),
        )
        .route(
            "/system/indexmenu/mylist",
            meta::get_route("/system/indexmenu/mylist", None, None, my_list),
        )
        .route(
            "/system/indexmenu/export",
            meta::get_route(
                "/system/indexmenu/export",
                Some("system:indexmenu:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/indexmenu/{ids}",
            meta::get_route(
                "/system/indexmenu/{ids}",
                Some("system:indexmenu:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/system/indexmenu",
            meta::post_route("/system/indexmenu", None, Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/system/indexmenu",
                    Some("system:indexmenu:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/system/indexmenu/{ids}",
            meta::delete_route("/system/indexmenu/{ids}", None, Some(&LOG_REMOVE), remove),
        )
}

/// Java: selectSysIndexMenuList —— 可添加的常用菜单。
fn candidate_sql(
    builder: &mut QueryBuilder<'_, MySql>,
    params: &std::collections::HashMap<String, String>,
    count: bool,
) {
    builder.push(if count {
        "select count(0) from sys_menu t1, sys_menu t2 \
         where t1.menu_type='C' and t1.visible = '0' and t2.menu_id = t1.parent_id"
    } else {
        "select t2.menu_name as menu_name2, t1.menu_id, t1.menu_name, \
         null as id, null as epsId, null as delFlag, null as createBy, null as createTime, \
         null as updateBy, null as updateTime, null as sort, null as remark, null as tenantId, \
         null as deptSubCode, null as flag, null as searchValue, null as params, null as userId, \
         null as menuName1, null as menuName3, null as menuIds, null as menuUrl \
         from sys_menu t1, sys_menu t2 \
         where t1.menu_type='C' and t1.visible = '0' and t2.menu_id = t1.parent_id"
    });
    let user_id = params.get("userId").cloned().unwrap_or_default();
    if user_id != "1" {
        builder.push(
            " and exists (select 1 from sys_role_menu rm, sys_user_role ur \
             where rm.role_id = ur.role_id and rm.menu_id = t1.menu_id and ur.user_id = ",
        );
        builder.push_bind(user_id);
        builder.push(")");
    }
    builder.push(
        " and not exists (select 1 from sys_index_menu tim where tim.del_flag = '0' \
         and tim.menu_id = t1.menu_id and tim.user_id = ",
    );
    builder.push_bind(params.get("userId").cloned().unwrap_or_default());
    builder.push(")");
    builder.push(
        " and not exists (select 1 from sys_menu t3 where t3.menu_type = 'C' \
         and t3.parent_id = t1.menu_id)",
    );
    if let Some(value) = params.get("menuName").filter(|value| !value.is_empty()) {
        builder.push(" and t1.menu_name like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    if let Some(value) = params.get("menuName2").filter(|value| !value.is_empty()) {
        builder.push(" and t2.menu_name like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    if !count {
        builder.push(" order by t2.parent_id, t2.order_num, t1.order_num, t1.menu_id");
    }
}

/// Java Jackson 的 SysIndexMenu 键序：BaseEntity（本类自己声明的 id/epsId/delFlag/审计列/sort…）
/// 在前，再按声明顺序，业务列（userId/menuId/menuName…）最后。
const INDEX_MENU_KEYS: &[&str] = &[
    "id",
    "epsId",
    "delFlag",
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "sort",
    "remark",
    "tenantId",
    "deptSubCode",
    "flag",
    "searchValue",
    "params",
    "userId",
    "menuId",
    "menuName",
    "menuName1",
    "menuName2",
    "menuName3",
    "menuIds",
    "menuUrl",
];

fn shape_index_menu_rows(rows: Vec<Value>) -> Vec<Value> {
    support::reorder_rows(rows, INDEX_MENU_KEYS)
}

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    params.insert(
        "userId".to_string(),
        user.user.user_id.unwrap_or_default().to_string(),
    );

    let mut count_builder = QueryBuilder::<MySql>::new("");
    candidate_sql(&mut count_builder, &params, true);
    let total: i64 = count_builder.build_query_scalar().fetch_one(&state.db).await?;

    let (offset, limit) = page.resolve(total);
    let mut builder = QueryBuilder::<MySql>::new("");
    candidate_sql(&mut builder, &params, false);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(TableDataInfo::new(total, shape_index_menu_rows(rows_to_json(&rows))))
}

async fn my_list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
) -> Result<AjaxResult, AppError> {
    let rows = sqlx::query(
        "select t.ID as id, t.USER_ID as userId, t.MENU_ID as menuId, t.SORT as sort, \
         t.EPS_ID as epsId, t.DEL_FLAG as delFlag, t.CREATE_BY as createBy, \
         t.CREATE_TIME as createTime, t.UPDATE_BY as updateBy, t.UPDATE_TIME as updateTime, \
         t.TENANT_ID as tenantId, t1.menu_name as menuName, \
         concat(t2.path, '/', t1.path) as menuUrl, null as menuName1, null as menuName2, \
         null as menuName3, null as menuIds, null as remark, null as deptSubCode, \
         null as flag, null as searchValue, null as params \
         from SYS_INDEX_MENU t \
         left join sys_menu t1 on t.MENU_ID = t1.menu_id \
         left join sys_menu t2 on t1.parent_id = t2.menu_id \
         where t.del_flag='0' and t.USER_ID = ? \
         order by t.CREATE_TIME desc limit 9",
    )
    .bind(user.user.user_id)
    .fetch_all(&state.db)
    .await?;
    let mut data = rows_to_json(&rows);
    for row in &mut data {
        if let Some(object) = row.as_object_mut() {
            let id = object.remove("id").unwrap_or(Value::Null);
            object.insert(
                "id".to_string(),
                match id {
                    Value::Number(number) => Value::String(number.to_string()),
                    other => other,
                },
            );
            for key in [
                "userId", "menuId", "sort", "epsId", "delFlag", "createBy", "createTime",
                "updateBy", "updateTime", "tenantId", "menuName1", "menuName2", "menuName3",
                "menuIds", "remark", "deptSubCode", "flag", "searchValue", "params",
            ] {
                object.insert(key.to_string(), Value::Null);
            }
        }
    }
    Ok(AjaxResult::success_data(shape_index_menu_rows(data)))
}

async fn export(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let mut builder = QueryBuilder::<MySql>::new("");
    let mut params = params;
    params.insert(
        "userId".to_string(),
        user.user.user_id.unwrap_or_default().to_string(),
    );
    candidate_sql(&mut builder, &params, false);
    let rows = builder.build().fetch_all(&state.db).await?;
    let data = rows_to_json(&rows);
    let headers = ["用户ID", "菜单ID"].map(str::to_string);
    let fields = ["userId", "menuId"];
    let data = data.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "用户常用菜单数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mut row = support::query_by_id(&state.db, &SPEC, &id).await?;
    if let Some(Value::Object(object)) = row.as_mut() {
        if let Some(number) = object.get("id").and_then(Value::as_i64) {
            object.insert("id".to_string(), Value::String(number.to_string()));
        }
    }
    Ok(AjaxResult::success_data(
        row.map(|value| shape_index_menu_rows(vec![value]).pop().unwrap_or(Value::Null)),
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let menu_ids = body
        .get("menuIds")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim_end_matches(',')
        .to_string();
    let user_id = user.user.user_id;
    let now = support::now_string();
    for part in menu_ids.split(',') {
        if part.is_empty() {
            continue;
        }
        let menu_id: i64 = part
            .parse()
            .map_err(|_| AppError::BadRequest(format!("非法的菜单ID: {part}")))?;
        sqlx::query("delete from sys_index_menu where menu_id = ? and user_id = ?")
            .bind(menu_id)
            .bind(user_id)
            .execute(&state.db)
            .await?;
        let entity = json!({
            "id": uuid::Uuid::new_v4().simple().to_string(),
            "userId": user_id,
            "menuId": menu_id,
            "delFlag": "0",
            "epsId": user.user.dept_id,
            "createTime": now,
            "updateTime": now,
        });
        support::insert_entity(&state.db, "sys_index_menu", &entity, AutoFill::from_user(&user))
            .await?;
    }
    Ok(AjaxResult::success())
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let id = body
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    if id.is_empty() {
        let generated = uuid::Uuid::new_v4().simple().to_string();
        let mut entity = body;
        if let Some(object) = entity.as_object_mut() {
            object.insert("id".to_string(), Value::String(generated.clone()));
            object.insert("delFlag".to_string(), json!("0"));
        }
        support::insert_entity(&state.db, "sys_index_menu", &entity, AutoFill::from_user(&user))
            .await?;
        Ok(AjaxResult::success_msg_data("操作成功！", generated))
    } else {
        let mut entity = body;
        if let Some(object) = entity.as_object_mut() {
            object.insert("updateBy".to_string(), json!(user.user.user_id));
            object.insert("updateTime".to_string(), json!(support::now_string()));
        }
        support::update_entity_by_id(&state.db, "sys_index_menu", "id", &entity, AutoFill::NONE)
            .await?;
        Ok(AjaxResult::success_msg_data("操作成功！", id))
    }
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "sys_index_menu", "ID", &ids).await?;
    Ok(support::success_count(count))
}
