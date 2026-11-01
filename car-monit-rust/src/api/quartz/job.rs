// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java
//       ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml
// 职责: 定时任务 CRUD + 调度（启动/暂停/立即执行）。
// 对应关系: Quartz Scheduler -> service::quartz_runtime。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::service::quartz_runtime;
use crate::state::AppState;
use crate::task::cron::CronExpression;

const SPEC: ListSpec = ListSpec {
    select: "job_id, job_name, job_group, invoke_target, cron_expression, misfire_policy, \
             concurrent, status, create_by, create_time, remark, null as updateBy, null as updateTime",
    from: "from sys_job",
    filters: &[
        Filter::like("jobName", "job_name"),
        Filter::eq("jobGroup", "job_group"),
        Filter::eq("status", "status"),
        Filter::like("invokeTarget", "invoke_target"),
    ],
    extra_where: "",
    order_by: "",
    id_column: "job_id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "定时任务",
    BusinessType::Export,
    "com.ruoyi.quartz.controller.SysJobController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "定时任务",
    BusinessType::Insert,
    "com.ruoyi.quartz.controller.SysJobController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "定时任务",
    BusinessType::Update,
    "com.ruoyi.quartz.controller.SysJobController.edit()",
);
static LOG_STATUS: LogSpec = LogSpec::new(
    "定时任务",
    BusinessType::Update,
    "com.ruoyi.quartz.controller.SysJobController.changeStatus()",
);
static LOG_RUN: LogSpec = LogSpec::new(
    "定时任务",
    BusinessType::Update,
    "com.ruoyi.quartz.controller.SysJobController.run()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "定时任务",
    BusinessType::Delete,
    "com.ruoyi.quartz.controller.SysJobController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/monitor/job/list",
            meta::get_route("/monitor/job/list", Some("monitor:job:list"), None, list),
        )
        .route(
            "/monitor/job/export",
            meta::get_route(
                "/monitor/job/export",
                Some("monitor:job:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/monitor/job/changeStatus",
            meta::put_route(
                "/monitor/job/changeStatus",
                Some("monitor:job:changeStatus"),
                Some(&LOG_STATUS),
                change_status,
            ),
        )
        .route(
            "/monitor/job/run",
            meta::put_route(
                "/monitor/job/run",
                Some("monitor:job:changeStatus"),
                Some(&LOG_RUN),
                run,
            ),
        )
        .route(
            "/monitor/job/{jobIds}",
            meta::get_route(
                "/monitor/job/{jobIds}",
                Some("monitor:job:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/monitor/job",
            meta::post_route("/monitor/job", Some("monitor:job:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/monitor/job",
                    Some("monitor:job:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/monitor/job/{jobIds}",
            meta::delete_route(
                "/monitor/job/{jobIds}",
                Some("monitor:job:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

fn text(body: &Value, key: &str) -> String {
    body.get(key).and_then(Value::as_str).unwrap_or_default().trim().to_string()
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, mut rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    fill_next_valid_time(&mut rows);
    Ok(TableDataInfo::new(total, rows))
}

/// Java: SysJob.getNextValidTime() —— 用 Quartz cron 计算下一次执行时间。
fn fill_next_valid_time(rows: &mut [Value]) {
    let now = chrono::Local::now().naive_local();
    for row in rows {
        let Some(object) = row.as_object_mut() else { continue };
        let expression = object
            .get("cronExpression")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let next = crate::task::cron::CronExpression::parse(&expression)
            .ok()
            .and_then(|cron| cron.next_after(now))
            .map(|time| time.format("%Y-%m-%d %H:%M:%S").to_string());
        object.insert("nextValidTime".to_string(), serde_json::json!(next));
    }
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "任务序号", "任务名称", "任务组名", "调用目标字符串", "执行表达式 ", "计划策略 ",
        "并发执行", "任务状态",
    ]
    .map(str::to_string);
    let fields = [
        "jobId", "jobName", "jobGroup", "invokeTarget", "cronExpression", "misfirePolicy",
        "concurrent", "status",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            if let Some(Value::String(text)) = values.get(5).cloned() {
                values[5] = Value::String(match text.as_str() {
                    "0" => "默认".to_string(),
                    "1" => "立即触发执行".to_string(),
                    "2" => "触发一次执行".to_string(),
                    "3" => "不触发立即执行".to_string(),
                    _ => text,
                });
            }
            if let Some(Value::String(text)) = values.get(6).cloned() {
                values[6] = Value::String(if text == "0" { "允许" } else { "禁止" }.to_string());
            }
            if let Some(Value::String(text)) = values.get(7).cloned() {
                values[7] = Value::String(if text == "0" { "正常" } else { "暂停" }.to_string());
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "定时任务", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(job_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mut row = support::query_by_id(&state.db, &SPEC, &job_id).await?;
    if let Some(value) = row.as_mut() {
        fill_next_valid_time(std::slice::from_mut(value));
    }
    Ok(AjaxResult::success_data(row))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let cron = text(&body, "cronExpression");
    if CronExpression::parse(&cron).is_err() {
        return Ok(AjaxResult::error("cron表达式不正确"));
    }
    if !quartz_runtime::valid_target(&text(&body, "invokeTarget")) {
        return Ok(AjaxResult::error("目标字符串不在白名单内"));
    }
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("createTime".to_string(), json!(support::now_string()));
    }
    let object = entity
        .as_object()
        .ok_or_else(|| AppError::BadRequest("请求体必须是 JSON 对象".to_string()))?;
    let mut tx = state.db.begin().await?;
    let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new("insert into sys_job (");
    let mut first = true;
    for (key, value) in object.iter() {
        if value.is_null() {
            continue;
        }
        if !first {
            builder.push(", ");
        }
        first = false;
        builder.push(support::column_name(key));
    }
    builder.push(") values (");
    let mut first = true;
    for value in object.values() {
        if value.is_null() {
            continue;
        }
        if !first {
            builder.push(", ");
        }
        first = false;
        support::bind_value(&mut builder, value);
    }
    builder.push(")");
    builder.build().execute(&mut *tx).await?;
    let job_id: i64 = sqlx::query_scalar("select last_insert_id()")
        .fetch_one(&mut *tx)
        .await?;
    tx.commit().await?;

    if text(&entity, "status") == "0" {
        quartz_runtime::schedule(
            &state,
            job_id,
            &text(&entity, "cronExpression"),
            &text(&entity, "invokeTarget"),
            &text(&entity, "jobName"),
        );
    }
    Ok(support::to_ajax(1))
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let cron = text(&body, "cronExpression");
    if CronExpression::parse(&cron).is_err() {
        return Ok(AjaxResult::error("cron表达式不正确"));
    }
    if !quartz_runtime::valid_target(&text(&body, "invokeTarget")) {
        return Ok(AjaxResult::error("目标字符串不在白名单内"));
    }
    let job_id = body
        .get("jobId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("jobId不能为空".to_string()))?;
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("updateTime".to_string(), json!(support::now_string()));
    }
    let rows = support::update_entity_by_id(&state.db, "sys_job", "job_id", &entity, AutoFill::NONE)
        .await?;

    if text(&entity, "status") == "0" {
        quartz_runtime::schedule(
            &state,
            job_id,
            &text(&entity, "cronExpression"),
            &text(&entity, "invokeTarget"),
            &text(&entity, "jobName"),
        );
    } else {
        quartz_runtime::unschedule(job_id);
    }
    Ok(support::to_ajax(rows))
}

async fn change_status(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let job_id = body
        .get("jobId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("jobId不能为空".to_string()))?;
    let status = text(&body, "status");
    let rows = sqlx::query("update sys_job set status = ? where job_id = ?")
        .bind(&status)
        .bind(job_id)
        .execute(&state.db)
        .await?
        .rows_affected();

    let job = sqlx::query_as::<_, (Option<String>, Option<String>, Option<String>)>(
        "select job_name, invoke_target, cron_expression from sys_job where job_id = ?",
    )
    .bind(job_id)
    .fetch_optional(&state.db)
    .await?;
    if let Some((job_name, invoke_target, cron)) = job {
        match (status.as_str(), cron) {
            ("0", Some(cron)) => quartz_runtime::schedule(
                &state,
                job_id,
                &cron,
                invoke_target.as_deref().unwrap_or_default(),
                job_name.as_deref().unwrap_or_default(),
            ),
            _ => quartz_runtime::unschedule(job_id),
        }
    }
    Ok(support::to_ajax(rows))
}

async fn run(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let job_id = body
        .get("jobId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("jobId不能为空".to_string()))?;
    let job = sqlx::query_as::<_, (Option<String>, Option<String>)>(
        "select job_name, invoke_target from sys_job where job_id = ?",
    )
    .bind(job_id)
    .fetch_optional(&state.db)
    .await?;
    if let Some((job_name, invoke_target)) = job {
        quartz_runtime::run_once(
            &state,
            job_id,
            job_name.as_deref().unwrap_or_default(),
            invoke_target.as_deref().unwrap_or_default(),
        );
    }
    Ok(AjaxResult::success())
}

async fn remove(
    State(state): State<AppState>,
    Path(job_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&job_ids);
    for id in &ids {
        if let Ok(job_id) = id.parse::<i64>() {
            quartz_runtime::unschedule(job_id);
        }
    }
    support::delete_by_ids(&state.db, "sys_job", "job_id", &ids).await?;
    Ok(AjaxResult::success())
}
