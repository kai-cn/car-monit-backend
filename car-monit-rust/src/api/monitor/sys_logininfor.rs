// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysLogininforController.java
//       ruoyi-system/src/main/resources/mapper/system/SysLogininforMapper.xml
// 职责: 登录日志列表/导出/删除/清空。
// 对应关系: selectLogininforList -> SPEC；cleanLogininfor -> truncate。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "info_id, user_name, ipaddr, login_location, browser, os, status, msg, login_time",
    from: "from sys_logininfor",
    filters: &[
        Filter::like("ipaddr", "ipaddr"),
        Filter::eq("status", "status"),
        Filter::like("userName", "user_name"),
        Filter::raw(
            "params[beginTime]",
            " and date_format(login_time,'%y%m%d') >= date_format(?, '%y%m%d')",
        ),
        Filter::raw(
            "params[endTime]",
            " and date_format(login_time,'%y%m%d') <= date_format(?, '%y%m%d')",
        ),
    ],
    extra_where: "",
    order_by: "info_id desc",
    id_column: "info_id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "登录日志",
    BusinessType::Export,
    "com.ruoyi.web.controller.monitor.SysLogininforController.export()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "登录日志",
    BusinessType::Delete,
    "com.ruoyi.web.controller.monitor.SysLogininforController.remove()",
);
static LOG_CLEAN: LogSpec = LogSpec::new(
    "登录日志",
    BusinessType::Clean,
    "com.ruoyi.web.controller.monitor.SysLogininforController.clean()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/monitor/logininfor/list",
            meta::get_route(
                "/monitor/logininfor/list",
                Some("monitor:logininfor:list"),
                None,
                list,
            ),
        )
        .route(
            "/monitor/logininfor/export",
            meta::get_route(
                "/monitor/logininfor/export",
                Some("monitor:logininfor:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/monitor/logininfor/clean",
            meta::delete_route(
                "/monitor/logininfor/clean",
                Some("monitor:logininfor:remove"),
                Some(&LOG_CLEAN),
                clean,
            ),
        )
        .route(
            "/monitor/logininfor/{infoIds}",
            meta::delete_route(
                "/monitor/logininfor/{infoIds}",
                Some("monitor:logininfor:remove"),
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
        "序号", "用户账号", "登录状态", "登录地址", "登录地点", "浏览器", "操作系统", "提示消息",
        "访问时间",
    ]
    .map(str::to_string);
    let fields = [
        "infoId", "userName", "status", "ipaddr", "loginLocation", "browser", "os", "msg",
        "loginTime",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            if let Some(Value::String(text)) = values.get(2).cloned() {
                values[2] = Value::String(match text.as_str() {
                    "0" => "成功".to_string(),
                    "1" => "失败".to_string(),
                    _ => text,
                });
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "登录日志", &headers, &data)
}

async fn remove(
    State(state): State<AppState>,
    Path(info_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&info_ids);
    let rows = support::delete_by_ids(&state.db, "sys_logininfor", "info_id", &ids).await?;
    Ok(support::to_ajax(rows))
}

async fn clean(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    sqlx::query("truncate table sys_logininfor").execute(&state.db).await?;
    Ok(AjaxResult::success())
}
