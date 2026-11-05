// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUpgradeInfoController.java
//       ruoyi-system/src/main/resources/mapper/system/SysUpgradeInfoMapper.xml
// 职责: 系统升级信息 CRUD（BaseUuidEntity，逻辑删除）。
// 对应关系: select/insert/update/delete -> SPEC + 自定义保存。

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
    select: "t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, t.create_by, t.create_time, \
             t.update_by, t.update_time, t.tenant_id",
    from: "from sys_upgrade_info t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("ver", "t.ver"),
        Filter::eq("info", "t.info"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.id",
};

const NEWEST_SQL: &str = "select t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, \
     t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id \
     from sys_upgrade_info t where t.del_flag = '0' and t.back_col1 = 1 \
     order by t.update_time desc limit 1";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "系统升级信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysUpgradeInfoController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "系统升级信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysUpgradeInfoController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "系统升级信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysUpgradeInfoController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "系统升级信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysUpgradeInfoController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/upgradeInfo/list",
            meta::get_route("/system/upgradeInfo/list", None, None, list),
        )
        .route(
            "/system/upgradeInfo/newest",
            meta::get_route("/system/upgradeInfo/newest", None, None, newest),
        )
        .route(
            "/system/upgradeInfo/export",
            meta::get_route(
                "/system/upgradeInfo/export",
                None,
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/upgradeInfo/{ids}",
            meta::get_route("/system/upgradeInfo/{ids}", None, None, get_info),
        )
        .route(
            "/system/upgradeInfo",
            meta::post_route("/system/upgradeInfo", None, Some(&LOG_ADD), add).merge(
                meta::put_route("/system/upgradeInfo", None, Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/system/upgradeInfo/{ids}",
            meta::delete_route("/system/upgradeInfo/{ids}", None, Some(&LOG_REMOVE), remove),
        )
}

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    // Java: sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId())
    if let Some(tenant_id) = user.user.tenant_id {
        params.insert("tenantId".to_string(), tenant_id.to_string());
    }
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn newest(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let row = sqlx::query(NEWEST_SQL).fetch_optional(&state.db).await?;
    Ok(AjaxResult::success_data(
        row.map(|row| crate::db::rows::row_to_json(&row)),
    ))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    // 实体没有 @Excel 注解，ExcelUtil 生成空表头。
    let headers: Vec<String> = Vec::new();
    let data = rows.iter().map(|_| Vec::new()).collect::<Vec<_>>();
    support::export_excel(&state, "系统升级信息数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id).await?,
    ))
}

async fn save(state: &AppState, user: &LoginUser, body: &Value) -> Result<AjaxResult, AppError> {
    let id = body
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    if id.is_empty() {
        let mut entity = body.clone();
        let generated = uuid::Uuid::new_v4().simple().to_string();
        if let Some(object) = entity.as_object_mut() {
            object.insert("id".to_string(), Value::String(generated.clone()));
            object.insert("delFlag".to_string(), json!("0"));
        }
        support::insert_entity(
            &state.db,
            "sys_upgrade_info",
            &entity,
            AutoFill::from_user(user),
        )
        .await?;
        Ok(AjaxResult::success_msg_data("操作成功！", generated))
    } else {
        let mut entity = body.clone();
        if let Some(object) = entity.as_object_mut() {
            object.insert("updateBy".to_string(), json!(user.user.user_id));
            object.insert("updateTime".to_string(), json!(support::now_string()));
        }
        support::update_entity_by_id(&state.db, "sys_upgrade_info", "id", &entity, AutoFill::NONE)
            .await?;
        Ok(AjaxResult::success_msg_data("操作成功！", id))
    }
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save(&state, &user, &body).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save(&state, &user, &body).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "sys_upgrade_info", "id", &ids).await?;
    Ok(support::success_count(count))
}
