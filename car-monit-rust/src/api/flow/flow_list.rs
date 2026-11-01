// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowListController.java
//       ruoyi-system/src/main/resources/mapper/flow/FlowListMapper.xml
// 职责: 审核历史记录 CRUD；listnew 按申请状态补「待审批/流程结束」行。
// 对应关系: selectFlowListList -> SPEC。

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

const SPEC: ListSpec = ListSpec {
    select: "t.ID as id, t.BILL_OID as billOid, t.BUSS_TYPE as bussType, \
             t.TASK_ID as taskId, t.flow_ruid as flowRuid, t.CURRENT_OID as currentOid, \
             t.SH_USER as shUser, t.SH_KEY as shKey, t.SH_VALUE as shValue, \
             t.SH_CONTEXT as shContext, t.BACK_COL1 as backCol1, t.BACK_COL2 as backCol2, \
             t.BACK_COL3 as backCol3, t.sort, t.eps_id, t.del_flag, t.create_by, \
             t.create_time, t.update_by, t.update_time, null as remark, null as tenantId, \
             null as deptSubCode, null as flag, null as searchValue, null as params",
    from: "from flow_list t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("billOid", "t.BILL_OID"),
        Filter::eq("bussType", "t.BUSS_TYPE"),
        Filter::eq("taskId", "t.TASK_ID"),
        Filter::eq("flowRuid", "t.flow_ruid"),
        Filter::eq("currentOid", "t.CURRENT_OID"),
        Filter::eq("shUser", "t.SH_USER"),
        Filter::eq("shKey", "t.SH_KEY"),
        Filter::eq("shValue", "t.SH_VALUE"),
        Filter::eq("shContext", "t.SH_CONTEXT"),
        Filter::eq("backCol1", "t.BACK_COL1"),
        Filter::eq("backCol2", "t.BACK_COL2"),
        Filter::eq("backCol3", "t.BACK_COL3"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time ASC, t.id",
    id_column: "t.ID",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "审核历史记录",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowListController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "审核历史记录",
    BusinessType::Insert,
    "com.ruoyi.web.controller.flow.FlowListController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "审核历史记录",
    BusinessType::Update,
    "com.ruoyi.web.controller.flow.FlowListController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "审核历史记录",
    BusinessType::Delete,
    "com.ruoyi.web.controller.flow.FlowListController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/flow/flowlist/list",
            meta::get_route("/flow/flowlist/list", None, None, list),
        )
        .route(
            "/flow/flowlist/listnew",
            meta::get_route("/flow/flowlist/listnew", None, None, list_new),
        )
        .route(
            "/flow/flowlist/export",
            meta::get_route("/flow/flowlist/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/flow/flowlist/{ids}",
            meta::get_route("/flow/flowlist/{ids}", None, None, get_info),
        )
        .route(
            "/flow/flowlist",
            meta::post_route("/flow/flowlist", None, Some(&LOG_ADD), add).merge(meta::put_route(
                "/flow/flowlist",
                None,
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/flow/flowlist/{ids}",
            meta::delete_route("/flow/flowlist/{ids}", None, Some(&LOG_REMOVE), remove),
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

async fn list_new(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let mut params = support::query_map(&raw);
    let bill_oid = params.get("billOid").cloned().unwrap_or_default();
    let bill_oid = if bill_oid.is_empty() { "-1".to_string() } else { bill_oid };
    params.insert("billOid".to_string(), bill_oid.clone());
    let mut rows = support::query_all(&state.db, &params, &SPEC).await?;

    // 查询我的申请记录，补「待审批 / 流程结束」。
    let mut apply_params = std::collections::HashMap::new();
    apply_params.insert("billOid".to_string(), bill_oid);
    let applies = support::query_all(
        &state.db,
        &apply_params,
        &crate::api::flow::flow_apply_info::APPLY_SPEC,
    )
    .await?;
    if let Some(apply) = applies.into_iter().next() {
        let status = apply
            .get("flowStatus")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let auit_emp = apply
            .get("backCol1")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        if status == "2" {
            if !auit_emp.is_empty() {
                rows.push(json!({ "shUser": auit_emp, "shValue": "待审批" }));
            }
        } else if status == "3" {
            rows.push(json!({ "shValue": "流程结束" }));
        }
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
        "单据OID", "流程类型", "任务ID", "流程实例ID", "当前节点OID(流程节点OID)", "审核人",
        "审核结论KEY", "审核结论", "内容", "备用字段1", "备用字段2", "备用字段3",
    ]
    .map(str::to_string);
    let fields = [
        "billOid", "bussType", "taskId", "flowRuid", "currentOid", "shUser", "shKey", "shValue",
        "shContext", "backCol1", "backCol2", "backCol3",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            for index in [6usize, 7] {
                if let Some(Value::String(text)) = values.get(index).cloned() {
                    values[index] = Value::String(match text.as_str() {
                        "T" => "同意".to_string(),
                        "F" => "拒绝".to_string(),
                        "R" => "退回".to_string(),
                        "S" => "提交".to_string(),
                        _ => text,
                    });
                }
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "审核历史记录数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id).await?,
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    shared::save_flow_entity(&state, &user, &body, "flow_list").await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    shared::save_flow_entity(&state, &user, &body, "flow_list").await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    shared::delete_flow_ids(&state, "flow_list", &ids).await
}
