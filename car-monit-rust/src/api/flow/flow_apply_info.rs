// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowApplyInfoController.java
//       ruoyi-system/src/main/resources/mapper/flow/FlowApplyInfoMapper.xml
// 职责: 我的申请 CRUD 与导出。
// 对应关系: selectFlowApplyInfoList/ById -> SPEC；save -> shared::save_flow_entity。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::flow::shared;
use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

pub(crate) const APPLY_SPEC: ListSpec = ListSpec {
    select: "t.ID as id, t.entrust_info as entrustInfo, t.BILL_OID as billOid, \
             t.BUSS_TYPE as bussType, t.FLOW_RUID as flowRuid, t.MSG_TITLE as msgTitle, \
             t.MSG_CONTEXT as msgContext, t.MSG_TYPE as msgType, t.MSG_URL as msgUrl, \
             t.APPLY_NAME as applyName, t.CURRENT_OID as currentOid, t.PC_OID as pcOid, \
             t.BACK_COL1 as backCol1, t.BACK_COL2 as backCol2, t.BACK_COL3 as backCol3, \
             t.FLOW_STATUS as flowStatus, t.sort, t.eps_id, t.del_flag, t.create_by, \
             t.create_time, t.update_by, t.update_time, \
             t.BACK_COL1 as auitEmpName, null as remark, null as tenantId, \
             null as deptSubCode, null as flag, null as searchValue, null as params",
    from: "from flow_apply_info t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("billOid", "t.BILL_OID"),
        Filter::eq("bussType", "t.BUSS_TYPE"),
        Filter::eq("flowRuid", "t.FLOW_RUID"),
        Filter::like("msgTitle", "t.MSG_TITLE"),
        Filter::like("msgContext", "t.MSG_CONTEXT"),
        Filter::eq("msgType", "t.MSG_TYPE"),
        Filter::eq("msgUrl", "t.MSG_URL"),
        Filter::like("applyName", "t.APPLY_NAME"),
        Filter::eq("currentOid", "t.CURRENT_OID"),
        Filter::eq("pcOid", "t.PC_OID"),
        Filter::eq("backCol1", "t.BACK_COL1"),
        Filter::eq("backCol2", "t.BACK_COL2"),
        Filter::eq("backCol3", "t.BACK_COL3"),
        Filter::eq("flowStatus", "t.FLOW_STATUS"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.ID",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "我的申请",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowApplyInfoController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "我的申请",
    BusinessType::Insert,
    "com.ruoyi.web.controller.flow.FlowApplyInfoController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "我的申请",
    BusinessType::Update,
    "com.ruoyi.web.controller.flow.FlowApplyInfoController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "我的申请",
    BusinessType::Delete,
    "com.ruoyi.web.controller.flow.FlowApplyInfoController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/flow/applyinfo/list",
            meta::get_route("/flow/applyinfo/list", None, None, list),
        )
        .route(
            "/flow/applyinfo/listAll",
            meta::get_route(
                "/flow/applyinfo/listAll",
                Some("flow:applyinfo:list"),
                None,
                list_all,
            ),
        )
        .route(
            "/flow/applyinfo/export",
            meta::get_route("/flow/applyinfo/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/flow/applyinfo/{ids}",
            meta::get_route("/flow/applyinfo/{ids}", None, None, get_info),
        )
        .route(
            "/flow/applyinfo",
            meta::post_route("/flow/applyinfo", None, Some(&LOG_ADD), add).merge(meta::put_route(
                "/flow/applyinfo",
                None,
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/flow/applyinfo/{ids}",
            meta::delete_route("/flow/applyinfo/{ids}", None, Some(&LOG_REMOVE), remove),
        )
}

/// Java Jackson 的 FlowApplyInfo 键序（BaseEntity 组 + 业务列 + 派生 entrustInfo）。
const APPLY_INFO_KEYS: &[&str] = &[
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
    "billOid",
    "bussType",
    "flowRuid",
    "msgTitle",
    "msgContext",
    "msgType",
    "msgUrl",
    "applyName",
    "currentOid",
    "pcOid",
    "backCol1",
    "backCol2",
    "backCol3",
    "flowStatus",
    "auitEmpName",
    "entrustInfo",
];

async fn list(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    params.insert(
        "createBy".to_string(),
        user.user.user_id.unwrap_or_default().to_string(),
    );
    let (total, rows) = support::query_list(&state.db, &params, &APPLY_SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_all(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &APPLY_SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &APPLY_SPEC).await?;
    let headers = [
        "单据OID",
        "业务类型-字典",
        "流程实例ID",
        "标题",
        "内容",
        "消息类型(1:通知业务，2:办理业务)",
        "处理的URL",
        "申请人",
        "当前节点OID(流程节点OID)",
        "批次OID",
        "备用字段1",
        "备用字段2",
        "备用字段3",
        "流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)",
    ]
    .map(str::to_string);
    let fields = [
        "billOid",
        "bussType",
        "flowRuid",
        "msgTitle",
        "msgContext",
        "msgType",
        "msgUrl",
        "applyName",
        "currentOid",
        "pcOid",
        "backCol1",
        "backCol2",
        "backCol3",
        "flowStatus",
    ];
    let data = rows
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_excel(&state, "我的申请数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mut row = support::query_by_id(&state.db, &APPLY_SPEC, &id).await?;
    if let Some(Value::Object(object)) = row.as_mut() {
        object.insert("auitEmpName".to_string(), Value::Null);
    }
    Ok(AjaxResult::success_data(row.map(|value| {
        support::reorder_keys(value, APPLY_INFO_KEYS)
    })))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    shared::save_flow_entity(&state, &user, &body, "flow_apply_info").await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    shared::save_flow_entity(&state, &user, &body, "flow_apply_info").await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    shared::delete_flow_ids(&state, "flow_apply_info", &ids).await
}
