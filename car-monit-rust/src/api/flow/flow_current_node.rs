// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowCurrentNodeController.java
//       ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowCurrentNodeServiceImpl.java
// 职责: 流程当前节点与审批引擎（提交/审核/撤销/委托）。
// 对应关系: saveFlowAuit/submitReturn/submitEntrustFlow -> 同名 async 函数。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Map, Value};
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::api::flow::shared;
use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.ID as id, t.FLOW_OID as flowOid, t.CURRENT_OID as currentOid, \
             t.NODE_ORDER as nodeOrder, t.NODE_KEY as nodeKey, t.NODE_NAME as nodeName, \
             t.CONFIG_TYPE as configType, t.CONFIG_ID as configId, t.CONFIG_NAME as configName, \
             t.BILL_OID as billOid, t.AUIT_EMP_OID as auitEmpOid, \
             t.AUIT_EMP_NAME as auitEmpName, t.BACK_COL1 as backCol1, \
             t.BACK_COL2 as backCol2, t.BACK_COL3 as backCol3, t.sort, t.eps_id, \
             t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, \
             null as remark, null as tenantId, null as deptSubCode, null as flag, \
             null as searchValue, null as params, null as roleId, null as tableName, \
             null as projectId, null as flowKey, null as flowRuid, null as flowApplyOid, \
             null as flowStatus, null as shValue, null as shContext, null as entrustUserId, \
             null as entrustUserName, null as roleKey, null as deptId",
    from: "from flow_current_node t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("flowOid", "t.FLOW_OID"),
        Filter::eq("currentOid", "t.CURRENT_OID"),
        Filter::eq("nodeOrder", "t.NODE_ORDER"),
        Filter::eq("nodeKey", "t.NODE_KEY"),
        Filter::like("nodeName", "t.NODE_NAME"),
        Filter::eq("configType", "t.CONFIG_TYPE"),
        Filter::eq("configId", "t.CONFIG_ID"),
        Filter::like("configName", "t.CONFIG_NAME"),
        Filter::eq("billOid", "t.BILL_OID"),
        Filter::eq("auitEmpOid", "t.AUIT_EMP_OID"),
        Filter::like("auitEmpName", "t.AUIT_EMP_NAME"),
        Filter::eq("backCol1", "t.BACK_COL1"),
        Filter::eq("backCol2", "t.BACK_COL2"),
        Filter::eq("backCol3", "t.BACK_COL3"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.ID",
};

const TEMPLATE_COLUMNS: &str = "ID, FLOW_OID, FLOW_TYPE, NODE_ORDER, NODE_KEY, NODE_NAME, \
     NEXT_NODE_OID, PREVIOUS_NODE_OID, RETURN_NUM, RETURN_NODE_OID, CONFIG_CONDTION, \
     CONFIG_TYPE, CONFIG_ID, CONFIG_NAME";

const FLOW_LIST_COLUMNS: &str = "ID, BILL_OID, BUSS_TYPE, TASK_ID, flow_ruid, CURRENT_OID, \
     SH_USER, SH_KEY, SH_VALUE, SH_CONTEXT, BACK_COL1, BACK_COL2, BACK_COL3, sort, eps_id, \
     del_flag, create_by, create_time, update_by, update_time";

const APPLY_COLUMNS: &str = "ID, entrust_info, BILL_OID, BUSS_TYPE, FLOW_RUID, MSG_TITLE, \
     MSG_CONTEXT, MSG_TYPE, MSG_URL, APPLY_NAME, CURRENT_OID, PC_OID, BACK_COL1, BACK_COL2, \
     BACK_COL3, FLOW_STATUS, sort, eps_id, del_flag, create_by, create_time, update_by, update_time";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "流程_当前节点",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowCurrentNodeController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "流程_当前节点",
    BusinessType::Insert,
    "com.ruoyi.web.controller.flow.FlowCurrentNodeController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "流程_当前节点",
    BusinessType::Update,
    "com.ruoyi.web.controller.flow.FlowCurrentNodeController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "流程_当前节点",
    BusinessType::Delete,
    "com.ruoyi.web.controller.flow.FlowCurrentNodeController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/flow/currentnode/list",
            meta::get_route("/flow/currentnode/list", None, None, list),
        )
        .route(
            "/flow/currentnode/export",
            meta::get_route("/flow/currentnode/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/flow/currentnode/getInfoByBillId/{billOid}",
            meta::get_route(
                "/flow/currentnode/getInfoByBillId/{billOid}",
                None,
                None,
                get_info_by_bill,
            ),
        )
        .route(
            "/flow/currentnode/saveFlowAuit",
            meta::put_route("/flow/currentnode/saveFlowAuit", None, None, save_flow_auit),
        )
        .route(
            "/flow/currentnode/submitReturn",
            meta::post_route("/flow/currentnode/submitReturn", None, None, submit_return),
        )
        .route(
            "/flow/currentnode/submitEntrustFlow",
            meta::post_route(
                "/flow/currentnode/submitEntrustFlow",
                None,
                None,
                submit_entrust_flow,
            ),
        )
        .route(
            "/flow/currentnode/{ids}",
            meta::get_route("/flow/currentnode/{ids}", None, None, get_info),
        )
        .route(
            "/flow/currentnode",
            meta::post_route("/flow/currentnode", None, Some(&LOG_ADD), add).merge(meta::put_route(
                "/flow/currentnode",
                None,
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/flow/currentnode/{ids}",
            meta::delete_route("/flow/currentnode/{ids}", None, Some(&LOG_REMOVE), remove),
        )
}

// ==================== 基础查询 ====================

async fn select_nodes(
    pool: &MySqlPool,
    params: &HashMap<String, String>,
) -> Result<Vec<Value>, AppError> {
    Ok(support::query_all(pool, params, &SPEC).await?)
}

async fn select_node_row(
    pool: &MySqlPool,
    id: &str,
) -> Result<Option<Value>, AppError> {
    support::query_by_id(pool, &SPEC, id).await
}

async fn select_template(
    pool: &MySqlPool,
    id: &str,
) -> Result<Option<Value>, AppError> {
    let row = sqlx::query(&format!("select {TEMPLATE_COLUMNS} from flow_template where ID = ?"))
        .bind(id)
        .fetch_optional(pool)
        .await?;
    Ok(row.map(|row| crate::db::rows::row_to_json(&row)))
}

async fn select_flow_name(
    pool: &MySqlPool,
    id: &str,
) -> Result<Option<Value>, AppError> {
    let row = sqlx::query(
        "select ID, FLOW_KEY, FLOW_TITLE, FLOW_CONTEXT, BUSS_NAME, tenant_id, flow_business_type \
         from flow_name where ID = ?",
    )
    .bind(id)
    .fetch_optional(pool)
    .await?;
    Ok(row.map(|row| crate::db::rows::row_to_json(&row)))
}

async fn select_apply_by_bill(
    pool: &MySqlPool,
    bill_oid: &str,
) -> Result<Option<Value>, AppError> {
    let row = sqlx::query(&format!(
        "select {APPLY_COLUMNS} from flow_apply_info where del_flag = 0 and bill_oid = ? limit 1"
    ))
    .bind(bill_oid)
    .fetch_optional(pool)
    .await?;
    Ok(row.map(|row| crate::db::rows::row_to_json(&row)))
}

fn field_str<'a>(row: &'a Value, key: &str) -> &'a str {
    row.get(key).and_then(Value::as_str).unwrap_or_default()
}

// ==================== 审核人解析 ====================

/// Java: getEmpInfoList —— 节点配置转审核人列表（人员/角色，含部门领导特例）。
async fn emp_info_list(
    state: &AppState,
    flow_name: &Value,
    template: &Value,
    bill_oid: &str,
    user_id: i64,
) -> Result<Vec<Value>, AppError> {
    let config_type = field_str(template, "configType").trim().to_string();
    let config_id = field_str(template, "configId").trim().to_string();
    if config_id.is_empty() {
        return Ok(Vec::new());
    }
    if config_type == "1" {
        return Ok(vec![json!({
            "auitEmpOid": config_id,
            "auitEmpName": field_str(template, "configName"),
        })]);
    }
    let role_key: Option<String> = sqlx::query_scalar(
        "select role_key from sys_role where role_id = ?",
    )
    .bind(config_id.parse::<i64>().unwrap_or_default())
    .fetch_optional(&state.db)
    .await?
    .flatten();
    let Some(role_key) = role_key else { return Ok(Vec::new()) };

    let mut params = HashMap::new();
    params.insert("billOid".to_string(), bill_oid.to_string());
    match role_key.as_str() {
        "dept_manager" => {
            params.insert("flag".to_string(), "bmjlAudit".to_string());
            params.insert("backCol1".to_string(), user_id.to_string());
        }
        "fg_manager" => {
            params.insert("flag".to_string(), "fgldAudit".to_string());
            params.insert("backCol1".to_string(), user_id.to_string());
        }
        "dept_duty_emp" => {
            params.insert("flag".to_string(), "dutyAudit".to_string());
            params.insert(
                "backCol1".to_string(),
                field_str(flow_name, "bussName").to_string(),
            );
        }
        _ => {
            params.insert("roleId".to_string(), config_id);
        }
    }
    select_emp_info_rows(&state.db, &params).await
}

async fn select_emp_info_rows(
    pool: &MySqlPool,
    params: &HashMap<String, String>,
) -> Result<Vec<Value>, AppError> {
    let flag = params.get("flag").cloned().unwrap_or_default();
    let text = |key: &str| params.get(key).map(|value| value.trim()).filter(|value| !value.is_empty());
    let mut builder = QueryBuilder::<MySql>::new(
        "select t.user_id AUIT_EMP_OID, t.nick_name AUIT_EMP_NAME from sys_user t \
         where t.del_flag = '0' and t.status = '0'",
    );
    if let Some(role_id) = text("roleId") {
        builder.push(" and exists (select 1 from sys_user_role t1 where t1.user_id = t.user_id and t1.role_id = ");
        builder.push_bind(role_id.to_string());
        builder.push(")");
    }
    if let Some(tenant_id) = text("tenantId") {
        builder.push(
            " and exists (select 1 from sys_dept td where td.del_flag = '0' and td.dept_id = t.dept_id and td.tenant_id = ",
        );
        builder.push_bind(tenant_id.to_string());
        builder.push(")");
    }
    if let Some(dept_id) = text("deptId") {
        builder.push(" and t.dept_id = ");
        builder.push_bind(dept_id.to_string());
    }
    if flag == "dutyAudit" {
        let table_name = text("backCol1").unwrap_or_default();
        if valid_identifier(table_name) {
            builder.push(format!(
                " and t.dept_id in (select tp.borrow_dept_id from {table_name} tp where tp.id = "
            ));
            builder.push_bind(params.get("billOid").cloned().unwrap_or_default());
            builder.push(")");
        }
    } else if flag == "bmjlAudit" || flag == "fgldAudit" {
        let column = if flag == "bmjlAudit" { "leader_id" } else { "fgld_id" };
        builder.push(format!(
            " and exists (select 1 from sys_dept ds where ds.del_flag = '0' and ds.dept_id = \
             (select tt.dept_id from sys_user tt where tt.user_id = "
        ));
        builder.push_bind(text("backCol1").unwrap_or_default().to_string());
        builder.push(format!(") and ds.{column} = t.user_id)"));
    }
    let rows = builder.build().fetch_all(pool).await?;
    Ok(rows_to_json(&rows))
}

/// Java: getEmpInfoListReturn —— 退回时取上一条审核记录的审核人。
async fn emp_info_list_return(
    state: &AppState,
    template: &Value,
    bill_oid: &str,
) -> Result<Vec<Value>, AppError> {
    let row = sqlx::query(&format!(
        "select {FLOW_LIST_COLUMNS} from flow_list where del_flag = '0' and BILL_OID = ? \
         and CURRENT_OID = ? order by create_time desc, id limit 1"
    ))
    .bind(bill_oid)
    .bind(field_str(template, "id"))
    .fetch_optional(&state.db)
    .await?;
    match row {
        Some(row) => {
            let value = crate::db::rows::row_to_json(&row);
            let create_by = value.get("createBy").cloned().unwrap_or(Value::Null);
            let create_by = match &create_by {
                Value::Number(number) => number.to_string(),
                Value::String(text) => text.clone(),
                _ => String::new(),
            };
            Ok(vec![json!({
                "auitEmpOid": create_by,
                "auitEmpName": value.get("shUser").cloned().unwrap_or(Value::Null),
            })])
        }
        None => Ok(Vec::new()),
    }
}

fn valid_identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value.chars().all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
}

// ==================== 写入辅助 ====================

/// Java: saveFlowCurrentNode —— 新增/修改节点。
async fn save_current_node(
    state: &AppState,
    user: &LoginUser,
    body: &Value,
) -> Result<String, AppError> {
    let result = shared::save_flow_entity(state, user, body, "flow_current_node").await?;
    Ok(result
        .0
        .get("data")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string())
}

/// Java: saveFlowNode —— 按审核人批量插入当前节点。
async fn save_flow_node(
    state: &AppState,
    user: &LoginUser,
    template: &Value,
    emp_list: &[Value],
    bill_oid: &str,
    project_id: &str,
) -> Result<(), AppError> {
    for emp in emp_list {
        let body = json!({
            "billOid": bill_oid,
            "flowOid": template.get("flowOid").cloned().unwrap_or(Value::Null),
            "currentOid": template.get("id").cloned().unwrap_or(Value::Null),
            "nodeOrder": template.get("nodeOrder").cloned().unwrap_or(Value::Null),
            "nodeKey": template.get("nodeKey").cloned().unwrap_or(Value::Null),
            "nodeName": template.get("nodeName").cloned().unwrap_or(Value::Null),
            "configType": template.get("configType").cloned().unwrap_or(Value::Null),
            "configId": template.get("configId").cloned().unwrap_or(Value::Null),
            "configName": template.get("configName").cloned().unwrap_or(Value::Null),
            "auitEmpOid": emp.get("auitEmpOid").cloned().unwrap_or(Value::Null),
            "auitEmpName": emp.get("auitEmpName").cloned().unwrap_or(Value::Null),
            "backCol1": project_id,
        });
        save_current_node(state, user, &body).await?;
    }
    Ok(())
}

/// Java: saveFlowList —— 写审核历史。
async fn save_history(
    state: &AppState,
    user: &LoginUser,
    template: &Value,
    bill_oid: &str,
    flow_key: &str,
    auit_result: &str,
    context: &str,
) -> Result<(), AppError> {
    let sh_value = match auit_result {
        "S" => "提交",
        "T" => "同意",
        "F" => "拒绝",
        "R" => "退回",
        "entrust" => "委托",
        _ => "",
    };
    let body = json!({
        "billOid": bill_oid,
        "bussType": flow_key,
        "flowRuid": template.get("flowOid").cloned().unwrap_or(Value::Null),
        "currentOid": template.get("id").cloned().unwrap_or(Value::Null),
        "shUser": user.user.nick_name.clone().unwrap_or_default(),
        "shKey": auit_result,
        "shValue": sh_value,
        "shContext": context,
    });
    shared::save_flow_entity(state, user, &body, "flow_list").await?;
    Ok(())
}

/// Java: saveFlowMessageInfo —— 同一 billOid+msgType(+bussType) 复用一条消息主体。
async fn save_message_info(
    state: &AppState,
    user: &LoginUser,
    bill_oid: &str,
    msg_type: &str,
    buss_type: Option<&str>,
    flow_ruid: Option<&str>,
    apply_name: Option<&str>,
    msg_title: Option<&str>,
) -> Result<String, AppError> {
    let mut sql = String::from(
        "select ID from flow_message_info where del_flag = '0' and BILL_OID = ? and MSG_TYPE = ?",
    );
    if buss_type.is_some() {
        sql.push_str(" and BUSS_TYPE = ?");
    }
    sql.push_str(" order by create_time desc, id limit 1");
    let mut query = sqlx::query_scalar::<_, String>(&sql).bind(bill_oid).bind(msg_type);
    if let Some(buss_type) = buss_type {
        query = query.bind(buss_type);
    }
    let existing = query.fetch_optional(&state.db).await?;

    let mut body = Map::new();
    body.insert("billOid".to_string(), json!(bill_oid));
    body.insert("msgType".to_string(), json!(msg_type));
    if let Some(buss_type) = buss_type {
        body.insert("bussType".to_string(), json!(buss_type));
    }
    if let Some(flow_ruid) = flow_ruid {
        body.insert("flowRuid".to_string(), json!(flow_ruid));
    }
    if let Some(apply_name) = apply_name {
        body.insert("applyName".to_string(), json!(apply_name));
    }
    if let Some(msg_title) = msg_title {
        body.insert("msgTitle".to_string(), json!(msg_title));
    }
    if let Some(id) = existing {
        body.insert("id".to_string(), json!(id.clone()));
        shared::save_flow_entity(state, user, &Value::Object(body), "flow_message_info").await?;
        Ok(id)
    } else {
        let result =
            shared::save_flow_entity(state, user, &Value::Object(body), "flow_message_info").await?;
        Ok(result
            .0
            .get("data")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string())
    }
}

/// Java: flowMessageDisposeService.saveFlowList(mid, userIds) —— 先删后插。
async fn save_dispose_list(
    state: &AppState,
    user: &LoginUser,
    mid: &str,
    user_ids: &[String],
) -> Result<(), AppError> {
    for user_id in user_ids {
        sqlx::query("delete from flow_message_dispose where MID = ? and BUSS_ID = ?")
            .bind(mid)
            .bind(user_id)
            .execute(&state.db)
            .await?;
        let body = json!({
            "mid": mid,
            "msgStatus": "2",
            "bussId": user_id,
        });
        shared::save_flow_entity(state, user, &body, "flow_message_dispose").await?;
    }
    Ok(())
}

/// Java: saveSzzdFlowMessageAll —— 全部待办归属当前用户并置为已办。
async fn mark_all_read(state: &AppState, mid: &str, user_id: i64) -> Result<(), AppError> {
    sqlx::query(
        "update flow_message_dispose set MSG_STATUS = '1', BUSS_ID = ? \
         where del_flag = '0' and MID = ? and MSG_STATUS = '2'",
    )
    .bind(user_id.to_string())
    .bind(mid)
    .execute(&state.db)
    .await?;
    Ok(())
}

/// Java: saveFlowApplyInfoNew —— 按 billOid 复用申请记录。
async fn save_apply_by_bill(
    state: &AppState,
    user: &LoginUser,
    fields: Map<String, Value>,
) -> Result<String, AppError> {
    let bill_oid = fields
        .get("billOid")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let existing = select_apply_by_bill(&state.db, &bill_oid).await?;
    let mut body = fields;
    if let Some(existing) = existing {
        if let Some(id) = existing.get("id").cloned() {
            body.insert("id".to_string(), id);
        }
    }
    let result = shared::save_flow_entity(state, user, &Value::Object(body), "flow_apply_info").await?;
    Ok(result
        .0
        .get("data")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string())
}

/// Java: updateFlowTable —— 业务表流程字段回写。
async fn update_flow_table(
    state: &AppState,
    table_name: &str,
    bill_oid: &str,
    flow_key: Option<&str>,
    flow_ruid: Option<&str>,
    flow_apply_oid: Option<&str>,
    flow_status: &str,
) -> Result<(), AppError> {
    if !valid_identifier(table_name) {
        return Ok(());
    }
    let mut builder = QueryBuilder::<MySql>::new(format!("update {table_name} set "));
    let mut first = true;
    let mut push = |builder: &mut QueryBuilder<'_, MySql>, column: &str, value: String| {
        if !first {
            builder.push(", ");
        }
        first = false;
        builder.push(format!("{column} = "));
        builder.push_bind(value);
    };
    if let Some(flow_key) = flow_key {
        push(&mut builder, "flow_key", flow_key.to_string());
    }
    if let Some(flow_ruid) = flow_ruid {
        push(&mut builder, "flow_ruid", flow_ruid.to_string());
    }
    if let Some(flow_apply_oid) = flow_apply_oid {
        push(&mut builder, "flow_apply_oid", flow_apply_oid.to_string());
    }
    push(&mut builder, "flow_status", flow_status.to_string());
    if flow_status == "3" {
        if !first {
            builder.push(", ");
        }
        builder.push("sh_time = now()");
    }
    builder.push(", update_time = now() where id = ");
    builder.push_bind(bill_oid.to_string());
    builder.build().execute(&state.db).await?;
    Ok(())
}

// ==================== 控制器端点 ====================

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "流程OID", "当前节点OID(流程节点OID)", "节点顺序", "节点KEY", "节点名称",
        "当前流程类型(字典：1人员2角色3其他)", "节点配置id", "节点配置名称", "单据OID", "处理人ID",
        "处理人名称", "备用字段1", "备用字段2", "备用字段3", "流程key", "流程实例ID", "流程申请ID",
        "流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)",
    ]
    .map(str::to_string);
    let fields = [
        "flowOid", "currentOid", "nodeOrder", "nodeKey", "nodeName", "configType", "configId",
        "configName", "billOid", "auitEmpOid", "auitEmpName", "backCol1", "backCol2", "backCol3",
        "flowKey", "flowRuid", "flowApplyOid", "flowStatus",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "流程_当前节点数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        select_node_row(&state.db, &id).await?,
    ))
}

async fn get_info_by_bill(
    State(state): State<AppState>,
    Path(bill_oid): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mut params = HashMap::new();
    params.insert("billOid".to_string(), bill_oid);
    let bill_oid_value = params.get("billOid").cloned().unwrap_or_default();
    let rows = select_nodes(&state.db, &params).await?;
    // Java: 查不到时返回 new FlowCurrentNode()（实体字段全 null）。
    let node = rows.into_iter().next().unwrap_or_else(|| {
        let mut object = Map::new();
        for key in [
            "id", "epsId", "delFlag", "createBy", "createTime", "updateBy", "updateTime",
            "sort", "remark", "tenantId", "deptSubCode", "flag", "searchValue", "params",
            "flowOid", "currentOid", "nodeOrder", "nodeKey", "nodeName", "configType",
            "configId", "configName", "billOid", "auitEmpOid", "auitEmpName", "backCol1",
            "backCol2", "backCol3", "roleId", "tableName", "projectId", "flowKey", "flowRuid",
            "flowApplyOid", "flowStatus", "shValue", "shContext", "entrustUserId",
            "entrustUserName", "roleKey", "deptId",
        ] {
            object.insert(key.to_string(), Value::Null);
        }
        object.insert("billOid".to_string(), Value::String(bill_oid_value));
        Value::Object(object)
    });
    Ok(AjaxResult::success_data(node))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    shared::save_flow_entity(&state, &user, &body, "flow_current_node").await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    shared::save_flow_entity(&state, &user, &body, "flow_current_node").await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    shared::delete_flow_ids(&state, "flow_current_node", &ids).await
}

/// Java: saveFlowAuit —— 业务审核。
async fn save_flow_auit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let mut sh_value = body
        .get("shValue")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let bill_oid = body
        .get("billOid")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let mut flow_status = "2".to_string();
    match sh_value.as_str() {
        "1" => sh_value = "T".to_string(),
        "2" => {
            sh_value = "F".to_string();
            flow_status = "5".to_string();
        }
        "3" => sh_value = "R".to_string(),
        _ => {}
    }
    if sh_value.is_empty() {
        return Ok(AjaxResult::error("请填写审核结论！"));
    }
    if bill_oid.is_empty() {
        return Ok(AjaxResult::error("业务不存在！"));
    }

    let mut query = HashMap::new();
    query.insert("billOid".to_string(), bill_oid.clone());
    query.insert(
        "auitEmpOid".to_string(),
        user.user.user_id.unwrap_or_default().to_string(),
    );
    let current = match select_nodes(&state.db, &query).await?.into_iter().next() {
        Some(node) => node,
        None => return Ok(AjaxResult::error("对不起，该单据已审核，请确定！")),
    };
    let project_id = field_str(&current, "backCol1").to_string();

    let current_oid = field_str(&current, "currentOid").to_string();
    let cur_template = select_template(&state.db, &current_oid)
        .await?
        .ok_or_else(|| AppError::Service("当前节点不存在".to_string()))?;
    let next_node_oid = field_str(&cur_template, "nextNodeOid").to_string();
    let return_node_oid = field_str(&cur_template, "previousNodeOid").to_string();
    let flow_name = select_flow_name(&state.db, field_str(&cur_template, "flowOid"))
        .await?
        .ok_or_else(|| AppError::Service("流程不存在".to_string()))?;

    let mut emp_list: Vec<Value> = Vec::new();
    let mut next_template = Value::Object(Map::new());
    if next_node_oid != "-1" && sh_value == "T" {
        next_template = select_template(&state.db, &next_node_oid)
            .await?
            .ok_or_else(|| AppError::Service("下一个节点不存在，请与管理员联系！".to_string()))?;
        if next_template.get("id").and_then(Value::as_str).unwrap_or_default().is_empty() {
            return Ok(AjaxResult::error("下一个节点不存在，请与管理员联系！"));
        }
        emp_list = emp_info_list(
            &state,
            &flow_name,
            &next_template,
            &bill_oid,
            user.user.user_id.unwrap_or_default(),
        )
        .await?;
        if emp_list.is_empty() {
            return Ok(AjaxResult::error("该业务找不到下一审批人，请与管理员联系！"));
        }
    } else if return_node_oid != "0" && sh_value == "R" {
        next_template = select_template(&state.db, &return_node_oid)
            .await?
            .ok_or_else(|| AppError::Service("退回节点不存在，请与管理员联系！".to_string()))?;
        emp_list = emp_info_list_return(&state, &next_template, &bill_oid).await?;
        if emp_list.is_empty() {
            return Ok(AjaxResult::error("该业务找不到下一审批人，请与管理员联系！"));
        }
    }

    let auit_names = emp_list
        .iter()
        .map(|emp| field_str(emp, "auitEmpName").to_string())
        .collect::<Vec<_>>()
        .join(",");
    let use_ids = emp_list
        .iter()
        .map(|emp| field_str(emp, "auitEmpOid").to_string())
        .collect::<Vec<_>>();

    if next_node_oid == "-1" && sh_value == "T" {
        flow_status = "3".to_string();
    }
    if return_node_oid == "0" && sh_value == "R" {
        flow_status = "4".to_string();
    }

    let flow_key = field_str(&flow_name, "flowKey").to_string();
    let flow_ruid = field_str(&flow_name, "id").to_string();
    let table_name = field_str(&flow_name, "bussName").to_string();

    // 先删除当前节点
    sqlx::query("delete from flow_current_node where BILL_OID = ?")
        .bind(&bill_oid)
        .execute(&state.db)
        .await?;

    let mid = save_message_info(&state, &user, &bill_oid, "2", None, None, None, None).await?;
    mark_all_read(&state, &mid, user.user.user_id.unwrap_or_default()).await?;

    let mut apply_fields = Map::new();
    apply_fields.insert("billOid".to_string(), json!(bill_oid));
    apply_fields.insert("flowStatus".to_string(), json!(flow_status));
    apply_fields.insert("backCol1".to_string(), json!(auit_names));
    let flow_apply_oid = save_apply_by_bill(&state, &user, apply_fields).await?;

    let apply_row = sqlx::query("select create_by from flow_apply_info where ID = ?")
        .bind(&flow_apply_oid)
        .fetch_optional(&state.db)
        .await?;
    let applicant_id: Option<i64> = match apply_row {
        Some(row) => sqlx::Row::try_get(&row, "create_by").ok(),
        None => None,
    };

    update_flow_table(
        &state,
        &table_name,
        &bill_oid,
        None,
        None,
        None,
        &flow_status,
    )
    .await?;

    save_history(
        &state,
        &user,
        &cur_template,
        &bill_oid,
        &flow_key,
        &sh_value,
        body.get("shContext").and_then(Value::as_str).unwrap_or_default(),
    )
    .await?;

    if !next_template.as_object().map(|map| map.is_empty()).unwrap_or(true) {
        save_flow_node(&state, &user, &next_template, &emp_list, &bill_oid, &project_id).await?;
    }
    save_dispose_list(&state, &user, &mid, &use_ids).await?;

    let buss_type_name = field_str(&flow_name, "flowTitle").to_string();
    let msg_title = if flow_status == "3" {
        format!("你提交的{buss_type_name}业务已通过，请查看！")
    } else if flow_status == "5" {
        format!("你提交的{buss_type_name}业务已拒绝，请查看！")
    } else if flow_status == "4" {
        format!("你提交的{buss_type_name}业务已退回，请查看！")
    } else {
        String::new()
    };
    if !msg_title.is_empty() {
        let applicant_mid = save_message_info(
            &state,
            &user,
            &bill_oid,
            "1",
            Some(&flow_key),
            Some(&flow_ruid),
            None,
            Some(&msg_title),
        )
        .await?;
        if let Some(applicant_id) = applicant_id {
            save_dispose_list(&state, &user, &applicant_mid, &[applicant_id.to_string()]).await?;
        }
    }

    Ok(AjaxResult::success_msg("审核成功！"))
}

/// Java: submitReturn —— 撤销流程（仅第一节点）。
async fn submit_return(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let bill_oid = body
        .get("billOid")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    if bill_oid.is_empty() {
        return Ok(AjaxResult::error("业务不存在！"));
    }
    let mut query = HashMap::new();
    query.insert("billOid".to_string(), bill_oid.clone());
    let current = match select_nodes(&state.db, &query).await?.into_iter().next() {
        Some(node) => node,
        None => return Ok(AjaxResult::error("撤销失败，该单据已撤销，请确定！")),
    };
    let current_oid = field_str(&current, "currentOid").to_string();
    let cur_template = select_template(&state.db, &current_oid)
        .await?
        .ok_or_else(|| AppError::Service("当前节点不存在".to_string()))?;
    if field_str(&cur_template, "previousNodeOid") != "0" {
        return Ok(AjaxResult::error("撤销失败，该单据已审核，请确定！"));
    }
    let flow_name = select_flow_name(&state.db, field_str(&cur_template, "flowOid"))
        .await?
        .ok_or_else(|| AppError::Service("流程不存在".to_string()))?;
    let table_name = field_str(&flow_name, "bussName").to_string();

    sqlx::query("delete from flow_current_node where BILL_OID = ?")
        .bind(&bill_oid)
        .execute(&state.db)
        .await?;

    let msg_row = sqlx::query(
        "select ID from flow_message_info where del_flag = '0' and BILL_OID = ? \
         and MSG_TYPE = '2' order by create_time desc, id limit 1",
    )
    .bind(&bill_oid)
    .fetch_optional(&state.db)
    .await?;
    if let Some(row) = msg_row {
        let mid: String = sqlx::Row::try_get(&row, "ID").unwrap_or_default();
        sqlx::query("update flow_message_info set del_flag = '1' where ID = ?")
            .bind(&mid)
            .execute(&state.db)
            .await?;
        sqlx::query("delete from flow_message_dispose where MID = ?")
            .bind(&mid)
            .execute(&state.db)
            .await?;
    }

    // Java: deleteFlowApplyInfoById(flowCurrentNode.getId()) —— 用请求体里的 id。
    let apply_id = body
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    sqlx::query("update flow_apply_info set del_flag = '1' where ID = ?")
        .bind(&apply_id)
        .execute(&state.db)
        .await?;

    update_flow_table(&state, &table_name, &bill_oid, None, None, None, "1").await?;
    let _ = user;
    Ok(AjaxResult::success_msg("撤销成功！"))
}

/// Java: submitEntrustFlow —— 委托办理。
async fn submit_entrust_flow(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let entrust_user_id = body
        .get("entrustUserId")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let entrust_user_name = body
        .get("entrustUserName")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let bill_oid = body
        .get("billOid")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    if entrust_user_id.is_empty() || entrust_user_name.is_empty() || bill_oid.is_empty() {
        return Ok(AjaxResult::error("缺少参数!"));
    }
    let user_id = user.user.user_id.unwrap_or_default();

    let mut query = HashMap::new();
    query.insert("billOid".to_string(), bill_oid.clone());
    query.insert("auitEmpOid".to_string(), user_id.to_string());
    let current = match select_nodes(&state.db, &query).await?.into_iter().next() {
        Some(node) => node,
        None => return Ok(AjaxResult::error("当前流程节点不存在!")),
    };
    let current_oid = field_str(&current, "currentOid").to_string();
    let template = select_template(&state.db, &current_oid)
        .await?
        .ok_or_else(|| AppError::Service("找不到对应的流程节点模板信息!".to_string()))?;
    let flow_name = select_flow_name(&state.db, field_str(&template, "flowOid"))
        .await?
        .ok_or_else(|| AppError::Service("找不到对应的流程信息!".to_string()))?;
    let apply = select_apply_by_bill(&state.db, &bill_oid)
        .await?
        .ok_or_else(|| AppError::Service("找不到对应的流程申请信息!".to_string()))?;

    // 更新当前节点：委托给目标用户，记录原审核人。
    let mut node_update = current.clone();
    if let Some(object) = node_update.as_object_mut() {
        object.insert("auitEmpOid".to_string(), json!(entrust_user_id));
        object.insert("auitEmpName".to_string(), json!(entrust_user_name));
        object.insert("backCol2".to_string(), json!(user_id.to_string()));
        object.insert(
            "backCol3".to_string(),
            json!(user.user.nick_name.clone().unwrap_or_default()),
        );
    }
    save_current_node(&state, &user, &node_update).await?;

    // 保存委托记录。
    save_history(
        &state,
        &user,
        &template,
        &bill_oid,
        field_str(&flow_name, "flowKey"),
        "entrust",
        &format!("委托{entrust_user_name}办理"),
    )
    .await?;

    let mid = save_message_info(
        &state,
        &user,
        &bill_oid,
        "2",
        None,
        None,
        None,
        None,
    )
    .await?;
    mark_all_read(&state, &mid, user_id).await?;
    save_dispose_list(&state, &user, &mid, &[entrust_user_id.clone()]).await?;

    // 追加 entrust_info。
    let mut entrusts: Vec<Value> = apply
        .get("entrustInfo")
        .and_then(Value::as_str)
        .and_then(|text| serde_json::from_str::<Vec<Value>>(text).ok())
        .unwrap_or_default();
    entrusts.push(json!({
        "operatorUserId": user_id.to_string(),
        "operatorUserName": user.user.nick_name.clone().unwrap_or_default(),
        "entrustUserId": entrust_user_id,
        "entrustUserName": entrust_user_name,
        "operationTime": chrono::Local::now().format("%Y-%m-%dT%H:%M:%S").to_string(),
        "flowId": flow_name.get("id").cloned().unwrap_or(Value::Null),
        "flowKey": flow_name.get("flowKey").cloned().unwrap_or(Value::Null),
        "flowTemplateId": template.get("id").cloned().unwrap_or(Value::Null),
    }));
    let mut apply_update = Map::new();
    apply_update.insert(
        "id".to_string(),
        apply.get("id").cloned().unwrap_or(Value::Null),
    );
    apply_update.insert("backCol1".to_string(), json!(entrust_user_name));
    apply_update.insert(
        "entrustInfo".to_string(),
        json!(serde_json::to_string(&entrusts).unwrap_or_default()),
    );
    shared::save_flow_entity(&state, &user, &Value::Object(apply_update), "flow_apply_info").await?;

    Ok(AjaxResult::success())
}
