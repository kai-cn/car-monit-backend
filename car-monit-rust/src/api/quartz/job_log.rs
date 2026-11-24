// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobLogController.java
//       ruoyi-quartz/src/main/resources/mapper/quartz/SysJobLogMapper.xml
// 职责: 调度日志列表/导出/删除/清空。
// 对应关系: selectJobLogList -> SPEC；cleanJobLog -> truncate。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "job_log_id, job_name, job_group, invoke_target, job_message, status, \
             exception_info, create_time, null as createBy, null as remark, null as startTime, null as stopTime, null as updateBy, null as updateTime",
    from: "from sys_job_log",
    filters: &[
        Filter::like("jobName", "job_name"),
        Filter::eq("jobGroup", "job_group"),
        Filter::eq("status", "status"),
        Filter::like("invokeTarget", "invoke_target"),
        Filter::raw(
            "params[beginTime]",
            " and date_format(create_time,'%y%m%d') >= date_format(?, '%y%m%d')",
        ),
        Filter::raw(
            "params[endTime]",
            " and date_format(create_time,'%y%m%d') <= date_format(?, '%y%m%d')",
        ),
    ],
    extra_where: "",
    order_by: "create_time desc",
    id_column: "job_log_id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "任务调度日志",
    BusinessType::Export,
    "com.ruoyi.quartz.controller.SysJobLogController.export()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "定时任务调度日志",
    BusinessType::Delete,
    "com.ruoyi.quartz.controller.SysJobLogController.remove()",
);
static LOG_CLEAN: LogSpec = LogSpec::new(
    "调度日志",
    BusinessType::Clean,
    "com.ruoyi.quartz.controller.SysJobLogController.clean()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/monitor/jobLog/list",
            meta::get_route("/monitor/jobLog/list", Some("monitor:job:list"), None, list),
        )
        .route(
            "/monitor/jobLog/export",
            meta::get_route(
                "/monitor/jobLog/export",
                Some("monitor:job:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/monitor/jobLog/clean",
            meta::delete_route(
                "/monitor/jobLog/clean",
                Some("monitor:job:remove"),
                Some(&LOG_CLEAN),
                clean,
            ),
        )
        .route(
            "/monitor/jobLog/{jobLogIds}",
            meta::get_route(
                "/monitor/jobLog/{jobLogIds}",
                Some("monitor:job:query"),
                None,
                get_info,
            )
            .merge(meta::delete_route(
                "/monitor/jobLog/{jobLogIds}",
                Some("monitor:job:remove"),
                Some(&LOG_REMOVE),
                remove,
            )),
        )
}

/// Java Jackson 的 SysJobLog 键序。
const JOB_LOG_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "jobLogId",
    "jobName",
    "jobGroup",
    "invokeTarget",
    "jobMessage",
    "status",
    "exceptionInfo",
    "startTime",
    "stopTime",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, JOB_LOG_KEYS),
    ))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "日志序号",
        "任务名称",
        "任务组名",
        "调用目标字符串",
        "日志信息",
        "执行状态",
        "异常信息",
    ]
    .map(str::to_string);
    let fields = [
        "jobLogId",
        "jobName",
        "jobGroup",
        "invokeTarget",
        "jobMessage",
        "status",
        "exceptionInfo",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            if let Some(Value::String(text)) = values.get(5).cloned() {
                values[5] = Value::String(match text.as_str() {
                    "0" => "正常".to_string(),
                    "1" => "失败".to_string(),
                    _ => text,
                });
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "调度日志", &headers, &data)
}

async fn get_info(
    State(_state): State<AppState>,
    Path(_job_log_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // 当前 Java 基准已把占位 ID 改为成功空结构。
    Ok(AjaxResult::success_data(serde_json::json!({"jobLogId": 1})))
}

async fn remove(
    State(state): State<AppState>,
    Path(job_log_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] jobLogIds` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("jobLogIds", &job_log_ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    let rows = support::delete_by_ids(&state.db, "sys_job_log", "job_log_id", &ids).await?;
    Ok(support::to_ajax(rows))
}

async fn clean(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    sqlx::query("truncate table sys_job_log")
        .execute(&state.db)
        .await?;
    Ok(AjaxResult::success())
}
