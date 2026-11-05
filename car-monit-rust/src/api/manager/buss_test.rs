// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/BussTestController.java
//       ruoyi-system/src/main/resources/mapper/manager/BussTestMapper.xml
// 职责: 流程联调测试业务 CRUD；syncCurrentTrack 触发车辆轨迹同步（远端任务未接入）。
// 对应关系: selectBussTestList -> SPEC；saveBussTest/deleteBussTestByIds -> support 通用 CRUD。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, FieldFormat, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.bill_name, t.bill_type, t.amount, t.dept_id, t.user_id, t.apply_time, \
             t.apply_time2, t.file_ids, t.flow_key, t.flow_ruid, t.flow_apply_oid, \
             t.flow_status, t.sh_time, t.back_col1, t.back_col2, t.remark, t.status, t.sort, \
             t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, \
             t.tenant_id",
    from: "from buss_test t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::like("billName", "t.bill_name"),
        Filter::eq("billType", "t.bill_type"),
        Filter::eq("amount", "t.amount"),
        Filter::eq("deptId", "t.dept_id"),
        Filter::eq("userId", "t.user_id"),
        Filter::eq("applyTime", "t.apply_time"),
        Filter::eq("applyTime2", "t.apply_time2"),
        Filter::eq("fileIds", "t.file_ids"),
        Filter::eq("flowKey", "t.flow_key"),
        Filter::eq("flowRuid", "t.flow_ruid"),
        Filter::eq("flowApplyOid", "t.flow_apply_oid"),
        Filter::eq("flowStatus", "t.flow_status"),
        Filter::eq("shTime", "t.sh_time"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.id",
};

const FORMATS: &[(&str, FieldFormat)] = &[
    ("applyTime2", FieldFormat::DateOnly),
    ("shTime", FieldFormat::DateOnly),
];

static LOG_EXPORT: LogSpec = LogSpec::new(
    "业务测试",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.BussTestController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "业务测试",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.BussTestController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "业务测试",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.BussTestController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "业务测试",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.BussTestController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/busstest/list",
            meta::get_route(
                "/manager/busstest/list",
                Some("manager:busstest:list"),
                None,
                list,
            ),
        )
        .route(
            "/manager/busstest/export",
            meta::get_route(
                "/manager/busstest/export",
                Some("manager:busstest:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/manager/busstest/syncCurrentTrack",
            meta::post_route(
                "/manager/busstest/syncCurrentTrack",
                Some("manager:busstest:syncTest"),
                None,
                sync_current_track,
            ),
        )
        .route(
            "/manager/busstest/{ids}",
            meta::get_route("/manager/busstest/{ids}", None, None, get_info).merge(
                meta::delete_route(
                    "/manager/busstest/{ids}",
                    Some("manager:busstest:remove"),
                    Some(&LOG_REMOVE),
                    remove,
                ),
            ),
        )
        .route(
            "/manager/busstest",
            meta::post_route(
                "/manager/busstest",
                Some("manager:busstest:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/manager/busstest",
                Some("manager:busstest:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
}

/// Java Jackson 的 BussTest 键序（BaseEntity 组 + 业务列）。
const BUSS_TEST_KEYS: &[&str] = &[
    "id",
    "epsId",
    "delFlag",
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "sort",
    "tenantId",
    "billName",
    "billType",
    "amount",
    "deptId",
    "userId",
    "applyTime",
    "applyTime2",
    "fileIds",
    "flowKey",
    "flowRuid",
    "flowApplyOid",
    "flowStatus",
    "shTime",
    "backCol1",
    "backCol2",
    "status",
    "remark",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, BUSS_TEST_KEYS),
    ))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "业务名称",
        "业务名称(字典：1业务2其他)",
        "金额",
        "部门id",
        "人员id",
        "申请时间",
        "时间时分秒",
        "附件(逗号多个分割)",
        "流程key",
        "流程实例ID",
        "流程申请ID",
        "流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)",
        "审核时间",
        "备用字段1",
        "备用字段2",
        "状态",
        "备注",
    ]
    .map(str::to_string);
    let fields = [
        "billName",
        "billType",
        "amount",
        "deptId",
        "userId",
        "applyTime",
        "applyTime2",
        "fileIds",
        "flowKey",
        "flowRuid",
        "flowApplyOid",
        "flowStatus",
        "shTime",
        "backCol1",
        "backCol2",
        "status",
        "remark",
    ];
    let data = rows
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_excel(&state, "业务测试数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &id, FORMATS)
            .await?
            .map(|row| support::reorder_keys(row, BUSS_TEST_KEYS)),
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "buss_test", "id", true, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "buss_test", "id", true, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "buss_test", "id", &ids).await?;
    Ok(support::success_count(count))
}

/// Java: syncCurrentTrack —— 车俩实时轨迹同步（远端 GPS/门架数据），记录日志后返回空响应。
async fn sync_current_track() -> axum::response::Response {
    tracing::info!("车俩实时轨迹同步开始同步！（Rust 迁移版本：远端轨迹同步任务未接入）");
    axum::response::IntoResponse::into_response(())
}
