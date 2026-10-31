// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java
//       ruoyi-system/src/main/resources/mapper/flow/FlowMessageInfoMapper.xml
// 职责: 系统内部消息（待办/已办/已结/消息）与审核日志导出。
// 对应关系: selectFlowMessageInfoList 的动态列/flag 过滤 -> 自定义 QueryBuilder。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Router};
use serde_json::Value;
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::flow::shared;
use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support;
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const BASE_COLUMNS: &str = "t.ID, t.message_no, t.BILL_OID, t.BUSS_TYPE, t.FLOW_RUID, \
     t.MSG_TITLE, t.MSG_CONTEXT, t.MSG_TYPE, t.MSG_URL, t.PC_OID, t.APPLY_NAME, t.BACK_COL1, \
     t.BACK_COL2, t.BACK_COL3, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, \
     t.update_by, t.update_time, app.FLOW_STATUS flowStatus, app.BACK_COL1 curEmpNames";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "系统内部消息",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowMessageInfoController.export()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "系统内部消息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.flow.FlowMessageInfoController.remove()",
);
static LOG_SHRZ: LogSpec = LogSpec::new(
    "导出审核日志",
    BusinessType::Export,
    "com.ruoyi.web.controller.flow.FlowMessageInfoController.exportShrz()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/flow/messageinfo/list",
            meta::get_route("/flow/messageinfo/list", None, None, list_todo),
        )
        .route(
            "/flow/messageinfo/listyb",
            meta::get_route("/flow/messageinfo/listyb", None, None, list_done),
        )
        .route(
            "/flow/messageinfo/listyj",
            meta::get_route("/flow/messageinfo/listyj", None, None, list_closed),
        )
        .route(
            "/flow/messageinfo/listxx",
            meta::get_route("/flow/messageinfo/listxx", None, None, list_message),
        )
        .route(
            "/flow/messageinfo/export",
            meta::get_route("/flow/messageinfo/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/flow/messageinfo/exportShrz",
            meta::get_route(
                "/flow/messageinfo/exportShrz",
                None,
                Some(&LOG_SHRZ),
                export_shrz,
            ),
        )
        .route(
            "/flow/messageinfo/{ids}",
            meta::get_route("/flow/messageinfo/{ids}", None, None, get_info),
        )
        .route(
            "/flow/messageinfo/{ids}",
            meta::delete_route("/flow/messageinfo/{ids}", None, Some(&LOG_REMOVE), remove),
        )
}

fn build_query(
    params: &HashMap<String, String>,
    with_order: bool,
    count: bool,
) -> QueryBuilder<'static, MySql> {
    let flag = params.get("flag").cloned().unwrap_or_default();
    let mut builder = QueryBuilder::<MySql>::new("");
    if count {
        builder.push("select count(0)");
    } else {
        builder.push(format!("select {BASE_COLUMNS}"));
    }
    if flag == "myxx" && !count {
        builder.push(
            ", (select t2.MSG_STATUS from flow_message_dispose t2 where t2.del_flag = '0' \
             and t2.mid = t.id and t2.BUSS_ID = ",
        );
        builder.push_bind(params.get("userId").cloned().unwrap_or_default());
        builder.push(") msgStatus");
    }
    builder.push(
        " from flow_message_info t left join FLOW_APPLY_INFO app \
         on app.del_flag = '0' and app.BILL_OID = t.BILL_OID where t.del_flag = '0'",
    );
    let like = |builder: &mut QueryBuilder<'_, MySql>, column: &str, key: &str| {
        if let Some(value) = params.get(key).filter(|value| !value.trim().is_empty()) {
            builder.push(format!(" and {column} like concat('%', "));
            builder.push_bind(value.clone());
            builder.push(", '%')");
        }
    };
    let eq = |builder: &mut QueryBuilder<'_, MySql>, column: &str, key: &str| {
        if let Some(value) = params.get(key).filter(|value| !value.trim().is_empty()) {
            builder.push(format!(" and {column} = "));
            builder.push_bind(value.clone());
        }
    };
    eq(&mut builder, "t.id", "id");
    eq(&mut builder, "t.message_no", "messageNo");
    eq(&mut builder, "t.BILL_OID", "billOid");
    eq(&mut builder, "t.BUSS_TYPE", "bussType");
    eq(&mut builder, "t.FLOW_RUID", "flowRuid");
    like(&mut builder, "t.MSG_TITLE", "msgTitle");
    like(&mut builder, "t.MSG_CONTEXT", "msgContext");
    eq(&mut builder, "t.MSG_TYPE", "msgType");
    eq(&mut builder, "t.MSG_URL", "msgUrl");
    eq(&mut builder, "t.PC_OID", "pcOid");
    like(&mut builder, "t.APPLY_NAME", "applyName");
    eq(&mut builder, "t.BACK_COL1", "backCol1");
    eq(&mut builder, "t.BACK_COL2", "backCol2");
    eq(&mut builder, "t.BACK_COL3", "backCol3");
    eq(&mut builder, "t.sort", "sort");
    eq(&mut builder, "t.eps_id", "epsId");
    eq(&mut builder, "t.create_by", "createBy");

    let user_id = params.get("userId").cloned().unwrap_or_default();
    match flag.as_str() {
        "mydb" => {
            builder.push(
                " and t.MSG_TYPE = '2' and exists (select 1 from flow_message_dispose t1 \
                 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ",
            );
            builder.push_bind(user_id.clone());
            builder.push(" and t1.MSG_STATUS = '2')");
        }
        "myyb" => {
            builder.push(
                " and t.MSG_TYPE = '2' and exists (select 1 from flow_message_dispose t1 \
                 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ",
            );
            builder.push_bind(user_id.clone());
            builder.push(" and t1.MSG_STATUS = '1')");
        }
        "myyj" => {
            builder.push(
                " and t.MSG_TYPE = '2' and exists (select 1 from flow_message_dispose t1 \
                 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ",
            );
            builder.push_bind(user_id.clone());
            builder.push(" and t1.MSG_STATUS = '1') and app.FLOW_STATUS = '3'");
        }
        "myxx" => {
            builder.push(
                " and t.MSG_TYPE = '1' and exists (select 1 from flow_message_dispose t1 \
                 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ",
            );
            builder.push_bind(user_id);
            builder.push(")");
        }
        _ => {}
    }
    if with_order && !count {
        builder.push(" order by t.create_time desc, t.id");
    }
    builder
}

async fn query(
    state: &AppState,
    params: &HashMap<String, String>,
    page: Option<&crate::common::page::PageDomain>,
) -> Result<(i64, Vec<Value>), AppError> {
    let mut count_builder = build_query(params, false, true);
    let total: i64 = count_builder.build_query_scalar().fetch_one(&state.db).await?;

    let mut builder = build_query(params, true, false);
    if let Some(page) = page {
        let (offset, limit) = page.resolve(total);
        builder.push(" limit ");
        builder.push_bind(limit);
        builder.push(" offset ");
        builder.push_bind(offset);
    }
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok((total, rows_to_json(&rows)))
}

async fn list_with_flag(
    state: &AppState,
    raw: Option<String>,
    flag: &str,
    user_id: Option<i64>,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    params.insert("flag".to_string(), flag.to_string());
    params.insert("userId".to_string(), user_id.unwrap_or_default().to_string());
    let (total, rows) = query(state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_todo(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    list_with_flag(&state, raw, "mydb", user.user.user_id).await
}

async fn list_done(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    list_with_flag(&state, raw, "myyb", user.user.user_id).await
}

async fn list_closed(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    list_with_flag(&state, raw, "myyj", user.user.user_id).await
}

async fn list_message(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    list_with_flag(&state, raw, "myxx", user.user.user_id).await
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let (_, rows) = query(&state, &params, None).await?;
    let headers = [
        "单据OID", "业务类型-字典", "流程实例ID", "标题", "内容", "消息类型(1:通知业务，2:办理业务)",
        "处理的URL", "批次OID", "申请人", "备用字段1", "备用字段2", "备用字段3",
    ]
    .map(str::to_string);
    let fields = [
        "billOid", "bussType", "flowRuid", "msgTitle", "msgContext", "msgType", "msgUrl",
        "pcOid", "applyName", "backCol1", "backCol2", "backCol3",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "系统内部消息数据", &headers, &data)
}

async fn export_shrz(
    State(_state): State<AppState>,
    RawQuery(_raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    // Java 模板 templates/export/exportShrz.xlsx 不存在，导出体被 catch 吞掉后 return null。
    Ok(AjaxResult::success())
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let row = sqlx::query(&format!(
        "select {BASE_COLUMNS} from flow_message_info t \
         left join FLOW_APPLY_INFO app on app.del_flag = '0' and app.BILL_OID = t.BILL_OID \
         where t.ID = ?"
    ))
    .bind(&id)
    .fetch_optional(&state.db)
    .await?;
    Ok(AjaxResult::success_data(
        row.map(|row| crate::db::rows::row_to_json(&row)),
    ))
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    shared::delete_flow_ids(&state, "flow_message_info", &ids).await
}
