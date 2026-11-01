// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowTemplateController.java
//       ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowTemplateServiceImpl.java
// 职责: 流程节点 CRUD，并在保存/删除后重排 next/previous/return 节点。
// 对应关系: saveFlowTemplate + saveFlow -> save_flow_order。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::flow::shared;
use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

pub(crate) const SPEC: ListSpec = ListSpec {
    select: "t.ID as id, t.FLOW_OID as flowOid, t.FLOW_TYPE as flowType, \
             t.NODE_ORDER as nodeOrder, t.NODE_KEY as nodeKey, t.NODE_NAME as nodeName, \
             t.NEXT_NODE_OID as nextNodeOid, t.PREVIOUS_NODE_OID as previousNodeOid, \
             t.RETURN_NUM as returnNum, t.RETURN_NODE_OID as returnNodeOid, \
             t.CONFIG_CONDTION as configCondtion, t.CONFIG_TYPE as configType, \
             t.CONFIG_ID as configId, t.CONFIG_NAME as configName, t.sort, t.eps_id, \
             t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, \
             null as remark, null as tenantId, null as deptSubCode, null as flag, \
             null as searchValue, null as params",
    from: "from flow_template t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("flowOid", "t.FLOW_OID"),
        Filter::eq("flowType", "t.FLOW_TYPE"),
        Filter::eq("nodeOrder", "t.NODE_ORDER"),
        Filter::eq("nodeKey", "t.NODE_KEY"),
        Filter::like("nodeName", "t.NODE_NAME"),
        Filter::eq("nextNodeOid", "t.NEXT_NODE_OID"),
        Filter::eq("previousNodeOid", "t.PREVIOUS_NODE_OID"),
        Filter::eq("returnNum", "t.RETURN_NUM"),
        Filter::eq("returnNodeOid", "t.RETURN_NODE_OID"),
        Filter::eq("configCondtion", "t.CONFIG_CONDTION"),
        Filter::eq("configType", "t.CONFIG_TYPE"),
        Filter::eq("configId", "t.CONFIG_ID"),
        Filter::like("configName", "t.CONFIG_NAME"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.NODE_ORDER, t.id",
    id_column: "t.ID",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "流程节点",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowTemplateController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "流程节点",
    BusinessType::Insert,
    "com.ruoyi.web.controller.flow.FlowTemplateController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "流程节点",
    BusinessType::Update,
    "com.ruoyi.web.controller.flow.FlowTemplateController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "流程节点",
    BusinessType::Delete,
    "com.ruoyi.web.controller.flow.FlowTemplateController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/flow/flowtemplate/list",
            meta::get_route("/flow/flowtemplate/list", None, None, list),
        )
        .route(
            "/flow/flowtemplate/flowlist",
            meta::get_route("/flow/flowtemplate/flowlist", None, None, flowlist),
        )
        .route(
            "/flow/flowtemplate/export",
            meta::get_route("/flow/flowtemplate/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/flow/flowtemplate/{ids}",
            meta::get_route("/flow/flowtemplate/{ids}", None, None, get_info),
        )
        .route(
            "/flow/flowtemplate",
            meta::post_route("/flow/flowtemplate", None, Some(&LOG_ADD), add).merge(
                meta::put_route("/flow/flowtemplate", None, Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/flow/flowtemplate/{ids}",
            meta::delete_route("/flow/flowtemplate/{ids}", None, Some(&LOG_REMOVE), remove),
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

async fn flowlist(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let mut rows = Vec::new();
    if params
        .get("flowOid")
        .map(|value| !value.trim().is_empty())
        .unwrap_or(false)
    {
        // Java: 在真实节点前插入「申请人提交」占位节点。
        rows.push(json!({
            "id": "-1",
            "nodeOrder": -1,
            "nodeKey": "tj",
            "nodeName": "申请人提交",
        }));
        rows.extend(support::query_all(&state.db, &params, &SPEC).await?);
    }
    Ok(AjaxResult::success_data(rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "流程OID", "当前流程类型(字典：1正常流程2会签流程)", "节点顺序", "节点KEY", "节点名称",
        "下一节点OID(-1为当前为最后一个节点)", "上一节点OID(0为开始节点)", "驳回到第几步 0 是发起人",
        "驳回节点OID", "节点配置条件", "当前流程类型(字典：1人员2角色3其他)", "节点配置id",
        "节点配置名称",
    ]
    .map(str::to_string);
    let fields = [
        "flowOid", "flowType", "nodeOrder", "nodeKey", "nodeName", "nextNodeOid",
        "previousNodeOid", "returnNum", "returnNodeOid", "configCondtion", "configType",
        "configId", "configName",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "流程节点数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id).await?,
    ))
}

async fn unique_count(state: &AppState, flow_oid: &str, column: &str, value: &str, id: &str) -> Result<i64, AppError> {
    let mut sql = format!(
        "select count(1) from flow_template t where t.del_flag = '0' and t.FLOW_OID = ? and t.{column} = ?"
    );
    if !id.is_empty() {
        sql.push_str(" and t.id != ?");
    }
    let mut query = sqlx::query_scalar::<_, i64>(&sql).bind(flow_oid).bind(value);
    if !id.is_empty() {
        query = query.bind(id);
    }
    Ok(query.fetch_one(&state.db).await?)
}

async fn save_template(
    state: &AppState,
    user: &LoginUser,
    body: Value,
) -> Result<AjaxResult, AppError> {
    let flow_oid = body.get("flowOid").and_then(Value::as_str).unwrap_or_default().to_string();
    let id = body.get("id").and_then(Value::as_str).unwrap_or_default().to_string();
    let node_key = body.get("nodeKey").and_then(Value::as_str).unwrap_or_default().to_string();
    let node_order = body
        .get("nodeOrder")
        .map(|value| value.to_string())
        .unwrap_or_default();
    if unique_count(state, &flow_oid, "NODE_KEY", &node_key, &id).await? > 0 {
        return Ok(AjaxResult::error("节点key存在重复"));
    }
    if unique_count(state, &flow_oid, "NODE_ORDER", &node_order, &id).await? > 0 {
        return Ok(AjaxResult::error("节点顺序存在重复"));
    }

    let result = shared::save_flow_entity(state, user, &body, "flow_template").await?;
    save_flow_order(state, &flow_oid).await?;
    Ok(result)
}

/// Java: `saveFlow(flowOid)` —— 按 NODE_ORDER 重排 next/previous/return。
pub async fn save_flow_order(state: &AppState, flow_oid: &str) -> Result<(), AppError> {
    if flow_oid.is_empty() {
        return Ok(());
    }
    let mut params = std::collections::HashMap::new();
    params.insert("flowOid".to_string(), flow_oid.to_string());
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let mut first_id = "-1".to_string();
    for index in 0..rows.len() {
        let current = &rows[index];
        let previous = if index == 0 {
            "0".to_string()
        } else {
            rows[index - 1]
                .get("id")
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string()
        };
        let next = if index + 1 == rows.len() {
            "-1".to_string()
        } else {
            rows[index + 1]
                .get("id")
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string()
        };
        let return_node = if index == 0 {
            first_id = current
                .get("id")
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            "0".to_string()
        } else {
            let return_num = current
                .get("returnNum")
                .map(|value| value.to_string())
                .unwrap_or_default();
            let found = rows.iter().find(|row| {
                row.get("nodeOrder").map(|value| value.to_string()) == Some(return_num.clone())
            });
            found
                .and_then(|row| row.get("id"))
                .and_then(Value::as_str)
                .map(str::to_string)
                .unwrap_or_else(|| first_id.clone())
        };
        let Some(id) = current.get("id").and_then(Value::as_str) else { continue };
        sqlx::query(
            "update flow_template set PREVIOUS_NODE_OID = ?, NEXT_NODE_OID = ?, \
             RETURN_NODE_OID = ? where ID = ?",
        )
        .bind(previous)
        .bind(next)
        .bind(return_node)
        .bind(id)
        .execute(&state.db)
        .await?;
    }
    Ok(())
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save_template(&state, &user, body).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save_template(&state, &user, body).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let first = support::ids_param(&ids).into_iter().next().unwrap_or_default();
    let flow_oid: Option<String> =
        sqlx::query_scalar("select FLOW_OID from flow_template where ID = ?")
            .bind(&first)
            .fetch_optional(&state.db)
            .await?;
    let result = shared::delete_flow_ids(&state, "flow_template", &ids).await?;
    if let Some(flow_oid) = flow_oid {
        save_flow_order(&state, &flow_oid).await?;
    }
    Ok(result)
}
