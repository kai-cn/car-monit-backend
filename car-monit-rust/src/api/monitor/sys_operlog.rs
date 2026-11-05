// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysOperlogController.java
//       ruoyi-system/src/main/resources/mapper/system/SysOperLogMapper.xml
// 职责: 操作日志列表/导出/删除/清空。
// 对应关系: selectOperLogList -> SPEC；cleanOperLog -> truncate。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "oper_id, title, business_type, method, request_method, operator_type, oper_name, \
             dept_name, oper_url, oper_ip, oper_location, oper_param, json_result, status, \
             error_msg, oper_time, null as businessTypes, null as createBy, null as createTime, null as updateBy, null as updateTime, null as remark",
    from: "from sys_oper_log",
    filters: &[
        Filter::like("title", "title"),
        Filter::eq("businessType", "business_type"),
        Filter::raw("businessTypes", " and find_in_set(business_type, ?)"),
        Filter::eq("status", "status"),
        Filter::like("operName", "oper_name"),
        Filter::raw(
            "params[beginTime]",
            " and date_format(oper_time,'%y%m%d') >= date_format(?, '%y%m%d')",
        ),
        Filter::raw(
            "params[endTime]",
            " and date_format(oper_time,'%y%m%d') <= date_format(?, '%y%m%d')",
        ),
    ],
    extra_where: "",
    order_by: "oper_id desc",
    id_column: "oper_id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "操作日志",
    BusinessType::Export,
    "com.ruoyi.web.controller.monitor.SysOperlogController.export()",
);
static LOG_CLEAN: LogSpec = LogSpec::new(
    "操作日志",
    BusinessType::Clean,
    "com.ruoyi.web.controller.monitor.SysOperlogController.clean()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/monitor/operlog/list",
            meta::get_route(
                "/monitor/operlog/list",
                Some("monitor:operlog:list"),
                None,
                list,
            ),
        )
        .route(
            "/monitor/operlog/export",
            meta::get_route(
                "/monitor/operlog/export",
                Some("monitor:operlog:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/monitor/operlog/clean",
            meta::delete_route(
                "/monitor/operlog/clean",
                Some("monitor:operlog:remove"),
                Some(&LOG_CLEAN),
                clean,
            ),
        )
        .route(
            "/monitor/operlog/{operIds}",
            meta::delete_route(
                "/monitor/operlog/{operIds}",
                Some("monitor:operlog:remove"),
                None,
                remove,
            ),
        )
}

/// Java Jackson 的 SysOperLog 键序。
const OPERLOG_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "operId",
    "title",
    "businessType",
    "businessTypes",
    "method",
    "requestMethod",
    "operatorType",
    "operName",
    "deptName",
    "operUrl",
    "operIp",
    "operLocation",
    "operParam",
    "jsonResult",
    "status",
    "errorMsg",
    "operTime",
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
        support::reorder_rows(rows, OPERLOG_KEYS),
    ))
}

fn convert_business_type(text: &str) -> String {
    match text {
        "0" => "其它",
        "1" => "新增",
        "2" => "修改",
        "3" => "删除",
        "4" => "授权",
        "5" => "导出",
        "6" => "导入",
        "7" => "强退",
        "8" => "生成代码",
        "9" => "清空数据",
        _ => text,
    }
    .to_string()
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "操作序号",
        "操作模块",
        "业务类型",
        "请求方法",
        "请求方式",
        "操作类别",
        "操作人员",
        "部门名称",
        "请求地址",
        "操作地址",
        "操作地点",
        "请求参数",
        "返回参数",
        "状态",
        "错误消息",
        "操作时间",
    ]
    .map(str::to_string);
    let fields = [
        "operId",
        "title",
        "businessType",
        "method",
        "requestMethod",
        "operatorType",
        "operName",
        "deptName",
        "operUrl",
        "operIp",
        "operLocation",
        "operParam",
        "jsonResult",
        "status",
        "errorMsg",
        "operTime",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            for (index, convert) in [
                (2usize, convert_business_type as fn(&str) -> String),
                (5, |text: &str| {
                    match text {
                        "0" => "其它",
                        "1" => "后台用户",
                        "2" => "手机端用户",
                        _ => text,
                    }
                    .to_string()
                }),
                (13, |text: &str| {
                    match text {
                        "0" => "正常",
                        "1" => "异常",
                        _ => text,
                    }
                    .to_string()
                }),
            ] {
                if let Some(Value::String(text)) = values.get(index).cloned() {
                    values[index] = Value::String(convert(&text));
                }
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "操作日志", &headers, &data)
}

async fn remove(
    State(state): State<AppState>,
    Path(oper_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] operIds` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("operIds", &oper_ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    let rows = support::delete_by_ids(&state.db, "sys_oper_log", "oper_id", &ids).await?;
    Ok(support::to_ajax(rows))
}

async fn clean(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    sqlx::query("truncate table sys_oper_log")
        .execute(&state.db)
        .await?;
    Ok(AjaxResult::success())
}
