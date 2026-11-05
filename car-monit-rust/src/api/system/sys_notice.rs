// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysNoticeController.java
//       ruoyi-system/src/main/resources/mapper/system/SysNoticeMapper.xml
// 职责: 通知公告 CRUD。
// 对应关系: list/listquery/getInfo/view/add/edit/remove -> SPEC + 自定义保存。

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
    select: "t.notice_id, t.notice_title, t.notice_type, \
             cast(t.notice_content as char) as notice_content, t.status, t.create_by, \
             t.create_time, t.update_by, t.update_time, t.remark, t.buss_id, t.buss_name, \
             t.tenant_id",
    from: "from sys_notice t",
    filters: &[
        Filter::like("noticeTitle", "t.notice_title"),
        Filter::eq("noticeType", "t.notice_type"),
        Filter::eq("createBy", "t.create_by"),
        Filter::eq("status", "t.status"),
        Filter::eq("bussId", "t.buss_id"),
        Filter::like("bussName", "t.buss_name"),
        Filter::raw("tenantId", " and (t.TENANT_ID = ? or t.TENANT_ID = 100 )"),
        Filter::eq("noticeContent", "t.notice_content"),
    ],
    extra_where: "",
    order_by: "t.create_time desc",
    id_column: "t.notice_id",
};

static LOG_ADD: LogSpec = LogSpec::new(
    "通知公告",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysNoticeController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "通知公告",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysNoticeController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "通知公告",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysNoticeController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/notice/list",
            meta::get_route("/system/notice/list", None, None, list),
        )
        .route(
            "/system/notice/listquery",
            meta::get_route("/system/notice/listquery", None, None, list_query),
        )
        .route(
            "/system/notice/view/{noticeId}",
            meta::get_route("/system/notice/view/{noticeId}", None, None, get_info),
        )
        .route(
            "/system/notice/{noticeIds}",
            meta::get_route("/system/notice/{noticeIds}", None, None, get_info),
        )
        .route(
            "/system/notice",
            meta::post_route(
                "/system/notice",
                Some("system:notice:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/system/notice",
                Some("system:notice:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/system/notice/{noticeIds}",
            meta::delete_route(
                "/system/notice/{noticeIds}",
                Some("system:notice:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java Jackson 的 SysNotice 键序：BaseEntity 在前（含 params），再按声明顺序。
const NOTICE_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "noticeId",
    "noticeTitle",
    "noticeType",
    "noticeContent",
    "status",
    "bussId",
    "bussName",
    "tenantId",
];

fn shape_notice_rows(rows: Vec<Value>) -> Vec<Value> {
    support::reorder_rows(rows, NOTICE_KEYS)
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    query(&state, raw, false).await
}

async fn list_query(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    query(&state, raw, true).await
}

async fn query(
    state: &AppState,
    raw: Option<String>,
    only_normal: bool,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    if only_normal {
        params.insert("status".to_string(), "0".to_string());
    }
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, shape_notice_rows(rows)))
}

async fn get_info(
    State(state): State<AppState>,
    Path(notice_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long noticeId`（/{noticeId} 与 /view/{noticeId} 共用）。
    let notice_id = support::path_long("noticeId", &notice_id)?.to_string();
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &notice_id)
            .await?
            .map(|row| shape_notice_rows(vec![row]).pop().unwrap_or(Value::Null)),
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("createTime".to_string(), json!(support::now_string()));
    }
    let rows = support::insert_entity(&state.db, "sys_notice", &entity, AutoFill::NONE).await?;
    Ok(support::to_ajax(rows))
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
    }
    let rows = support::update_entity_by_id(
        &state.db,
        "sys_notice",
        "notice_id",
        &entity,
        AutoFill::NONE,
    )
    .await?;
    Ok(support::to_ajax(rows))
}

async fn remove(
    State(state): State<AppState>,
    Path(notice_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] noticeIds` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("noticeIds", &notice_ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    let rows = support::delete_by_ids(&state.db, "sys_notice", "notice_id", &ids).await?;
    Ok(support::to_ajax(rows))
}
