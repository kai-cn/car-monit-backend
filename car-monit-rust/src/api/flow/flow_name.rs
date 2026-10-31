// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowNameController.java
//       ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowNameServiceImpl.java
// 职责: 流程名称 CRUD 与「同步其他单位工作流」。
// 对应关系: saveFlowName/tbFlow -> 本地 SQL + flow_template 复制。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::flow::shared;
use crate::api::flow::flow_template::save_flow_order;
use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.ID, t.FLOW_KEY, t.FLOW_TITLE, t.FLOW_CONTEXT, t.BUSS_NAME, t.sort, t.eps_id, \
             t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id, \
             t.flow_business_type, IFNULL(sd.dept_name, '系统默认') tenantName",
    from: "from flow_name t left join sys_dept sd on sd.dept_id = t.tenant_id",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("flowBusinessType", "t.flow_business_type"),
        Filter::eq("flowKey", "t.FLOW_KEY"),
        Filter::like("flowTitle", "t.FLOW_TITLE"),
        Filter::raw(
            "tenantName",
            " and IFNULL(sd.dept_name, '系统默认') like concat('%', ?, '%')",
        ),
        Filter::like("flowContext", "t.FLOW_CONTEXT"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("createBy", "t.create_by"),
        Filter::eq("tenantId", "t.tenant_id"),
    ],
    extra_where: "",
    order_by: "t.tenant_id, t.flow_key, t.id",
    id_column: "t.ID",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "流程名称",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowNameController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "流程名称",
    BusinessType::Insert,
    "com.ruoyi.web.controller.flow.FlowNameController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "流程名称",
    BusinessType::Update,
    "com.ruoyi.web.controller.flow.FlowNameController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "流程名称",
    BusinessType::Delete,
    "com.ruoyi.web.controller.flow.FlowNameController.remove()",
);
static LOG_TB: LogSpec = LogSpec::new(
    "同步其他单位的工作流",
    BusinessType::Update,
    "com.ruoyi.web.controller.flow.FlowNameController.tbFlow()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/flow/flowname/list",
            meta::get_route("/flow/flowname/list", Some("flow:flowname:list"), None, list),
        )
        .route(
            "/flow/flowname/listQuery",
            meta::get_route("/flow/flowname/listQuery", None, None, list_query),
        )
        .route(
            "/flow/flowname/export",
            meta::get_route(
                "/flow/flowname/export",
                Some("flow:flowname:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/flow/flowname/tbFlow",
            meta::post_route(
                "/flow/flowname/tbFlow",
                Some("flow:flowname:edit"),
                Some(&LOG_TB),
                tb_flow,
            ),
        )
        .route(
            "/flow/flowname/{ids}",
            meta::get_route(
                "/flow/flowname/{ids}",
                Some("flow:flowname:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/flow/flowname",
            meta::post_route(
                "/flow/flowname",
                Some("flow:flowname:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/flow/flowname",
                Some("flow:flowname:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/flow/flowname/{ids}",
            meta::delete_route(
                "/flow/flowname/{ids}",
                Some("flow:flowname:remove"),
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
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_query(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    // Java: flowName.setTenantId(SecurityUtils.getTenantId())
    if let Some(tenant_id) = user.user.tenant_id {
        params.insert("tenantId".to_string(), tenant_id.to_string());
    }
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = ["流程KEY", "流程名称", "内容", "业务名称", "单位名称"].map(str::to_string);
    let fields = ["flowKey", "flowTitle", "flowContext", "bussName", "tenantName"];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "流程名称数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id).await?,
    ))
}

async fn save_flow_name(
    state: &AppState,
    user: &LoginUser,
    body: &Value,
) -> Result<AjaxResult, AppError> {
    let flow_key = body.get("flowKey").and_then(Value::as_str).unwrap_or_default().to_string();
    let id = body.get("id").and_then(Value::as_str).unwrap_or_default().to_string();
    let mut sql = String::from(
        "select count(1) from flow_name t where t.del_flag = '0' and t.FLOW_KEY = ? and t.create_by = -1",
    );
    if body.get("tenantId").map(|value| !value.is_null()).unwrap_or(false) {
        sql.push_str(" and t.tenant_id = ?");
    }
    if !id.is_empty() {
        sql.push_str(" and t.id != ?");
    }
    let mut query = sqlx::query_scalar::<_, i64>(&sql).bind(&flow_key);
    if let Some(tenant_id) = body.get("tenantId").and_then(Value::as_i64) {
        query = query.bind(tenant_id);
    }
    if !id.is_empty() {
        query = query.bind(&id);
    }
    if query.fetch_one(&state.db).await? > 0 {
        return Ok(AjaxResult::error("节点key存在重复"));
    }

    let mut entity = body.clone();
    if id.is_empty() {
        // Java: 新增时 createBy 固定为 -1（系统模板）。
        if let Some(object) = entity.as_object_mut() {
            object.insert("createBy".to_string(), json!(-1));
        }
    }
    shared::save_flow_entity(state, user, &entity, "flow_name").await
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save_flow_name(&state, &user, &body).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save_flow_name(&state, &user, &body).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    shared::delete_flow_ids(&state, "flow_name", &ids).await
}

/// Java: `tbFlow` —— 把 create_by=-1 的系统流程复制给每个单位。
async fn tb_flow(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(_body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let templates = sqlx::query_scalar::<_, String>(
        "select ID from flow_name where del_flag = '0' and create_by = -1",
    )
    .fetch_all(&state.db)
    .await?;
    let units = sqlx::query_scalar::<_, i64>(
        "select dept_id from sys_dept where del_flag = '0' and is_uint = '1'",
    )
    .fetch_all(&state.db)
    .await?;

    for flow_oid in templates {
        let mut params = std::collections::HashMap::new();
        params.insert("id".to_string(), flow_oid.clone());
        let Some(source) = support::query_all(&state.db, &params, &SPEC).await?.into_iter().next()
        else {
            continue;
        };
        let mut template_params = std::collections::HashMap::new();
        template_params.insert("flowOid".to_string(), flow_oid.clone());
        let node_rows = support::query_all(&state.db, &template_params, &crate::api::flow::flow_template::SPEC)
            .await?;

        let flow_key = source.get("flowKey").cloned().unwrap_or(Value::Null);
        for unit in &units {
            let count: i64 = sqlx::query_scalar(
                "select count(1) from flow_name where del_flag = '0' and tenant_id = ? and FLOW_KEY = ?",
            )
            .bind(unit)
            .bind(flow_key.as_str().unwrap_or_default())
            .fetch_one(&state.db)
            .await?;
            if count > 0 {
                continue;
            }
            let mut entity = source.clone();
            if let Some(object) = entity.as_object_mut() {
                object.insert("id".to_string(), Value::Null);
                object.insert("tenantId".to_string(), json!(unit));
                object.insert("flowBusinessType".to_string(), json!("1"));
                object.insert("createBy".to_string(), json!(user.user.user_id));
                object.insert("epsId".to_string(), json!(user.user.dept_id));
                object.remove("tenantName");
            }
            let inserted = shared::save_flow_entity(&state, &user, &entity, "flow_name").await?;
            let new_flow_id = inserted
                .0
                .get("data")
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            for node in &node_rows {
                let mut copy = node.clone();
                if let Some(object) = copy.as_object_mut() {
                    object.insert("id".to_string(), Value::Null);
                    object.insert("flowOid".to_string(), json!(new_flow_id));
                    object.insert("nextNodeOid".to_string(), json!(""));
                    object.insert("previousNodeOid".to_string(), json!(""));
                }
                shared::save_flow_entity(&state, &user, &copy, "flow_template").await?;
            }
            save_flow_order(&state, &new_flow_id).await?;
        }
    }
    Ok(AjaxResult::success_msg("同步成功！"))
}
