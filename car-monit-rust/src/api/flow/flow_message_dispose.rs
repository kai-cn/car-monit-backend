// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageDisposeController.java
//       ruoyi-system/src/main/resources/mapper/flow/FlowMessageDisposeMapper.xml
// 职责: 系统消息处理人 CRUD，以及「我删除/我知晓」。
// 对应关系: removeFlowMessage/saveSzzdFlowMessage -> 按 mid + bussId 更新。

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

const SPEC: ListSpec = ListSpec {
    select: "t.ID as id, t.MID as mid, t.BUSS_ID as bussId, t.BUSS_NAME as bussName, \
             t.MSG_STATUS as msgStatus, t.HANG_TIME as hangTime, \
             t.DISPOSE_OTHER as disposeOther, t.sort, t.eps_id, t.del_flag, t.create_by, \
             t.create_time, t.update_by, t.update_time, null as remark, null as tenantId, \
             null as deptSubCode, null as flag, null as searchValue, null as params",
    from: "from flow_message_dispose t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("mid", "t.MID"),
        Filter::eq("bussId", "t.BUSS_ID"),
        Filter::like("bussName", "t.BUSS_NAME"),
        Filter::eq("msgStatus", "t.MSG_STATUS"),
        Filter::eq("hangTime", "t.HANG_TIME"),
        Filter::eq("disposeOther", "t.DISPOSE_OTHER"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.ID",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "系统消息处理人",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowMessageDisposeController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "系统消息处理人",
    BusinessType::Insert,
    "com.ruoyi.web.controller.flow.FlowMessageDisposeController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "系统消息处理人",
    BusinessType::Update,
    "com.ruoyi.web.controller.flow.FlowMessageDisposeController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "系统消息处理人",
    BusinessType::Delete,
    "com.ruoyi.web.controller.flow.FlowMessageDisposeController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/flow/messagedispose/list",
            meta::get_route("/flow/messagedispose/list", None, None, list),
        )
        .route(
            "/flow/messagedispose/export",
            meta::get_route(
                "/flow/messagedispose/export",
                None,
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/flow/messagedispose/delmes/{mid}",
            meta::delete_route("/flow/messagedispose/delmes/{mid}", None, None, del_mes),
        )
        .route(
            "/flow/messagedispose/szzdmes/{mid}",
            meta::delete_route("/flow/messagedispose/szzdmes/{mid}", None, None, szzd_mes),
        )
        .route(
            "/flow/messagedispose/{ids}",
            meta::get_route("/flow/messagedispose/{ids}", None, None, get_info),
        )
        .route(
            "/flow/messagedispose",
            meta::post_route("/flow/messagedispose", None, Some(&LOG_ADD), add).merge(
                meta::put_route("/flow/messagedispose", None, Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/flow/messagedispose/{ids}",
            meta::delete_route(
                "/flow/messagedispose/{ids}",
                None,
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

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "消息外键",
        "处理对象ID",
        "处理对象名称",
        "消息状态",
        "处理时间",
        "其他",
    ]
    .map(str::to_string);
    let fields = [
        "mid",
        "bussId",
        "bussName",
        "msgStatus",
        "hangTime",
        "disposeOther",
    ];
    let data = rows
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_excel(&state, "系统消息处理人数据", &headers, &data)
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
    shared::save_flow_entity(&state, &user, &body, "flow_message_dispose").await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    shared::save_flow_entity(&state, &user, &body, "flow_message_dispose").await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    shared::delete_flow_ids(&state, "flow_message_dispose", &ids).await
}

/// Java: `removeFlowMessage(mid, userId)` —— 物理删除自己的消息明细。
async fn del_mes(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Path(mid): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mid = if mid.is_empty() {
        "-1".to_string()
    } else {
        mid
    };
    let rows = sqlx::query("delete from flow_message_dispose where MID = ? and BUSS_ID = ?")
        .bind(&mid)
        .bind(user.user.user_id.unwrap_or_default().to_string())
        .execute(&state.db)
        .await?
        .rows_affected();
    Ok(support::success_count(rows))
}

/// Java: `saveSzzdFlowMessage(mid, userId)` —— 设置自己的消息为已读。
async fn szzd_mes(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Path(mid): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mid = if mid.is_empty() {
        "-1".to_string()
    } else {
        mid
    };
    let rows = sqlx::query(
        "update flow_message_dispose set MSG_STATUS = '1' \
         where del_flag = '0' and MID = ? and BUSS_ID = ?",
    )
    .bind(&mid)
    .bind(user.user.user_id.unwrap_or_default().to_string())
    .execute(&state.db)
    .await?
    .rows_affected();
    Ok(support::success_count(rows))
}
