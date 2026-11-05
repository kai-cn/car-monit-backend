// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java
//       ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml
// 职责: 定时任务 CRUD + 调度（启动/暂停/立即执行）。
// 对应关系: Quartz Scheduler -> service::quartz_runtime。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::service::quartz_cron;
use crate::service::quartz_runtime;
use crate::state::AppState;

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
    body.get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim()
        .to_string()
}

/// Java Jackson 的 SysJob 键序：BaseEntity 在前，派生 `nextValidTime` 最后。
const JOB_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "jobId",
    "jobName",
    "jobGroup",
    "invokeTarget",
    "cronExpression",
    "misfirePolicy",
    "concurrent",
    "status",
    "nextValidTime",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, mut rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    fill_next_valid_time(&mut rows)?;
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, JOB_KEYS),
    ))
}

/// Java: `CronUtils.isValid` —— `null` 走 `IllegalArgumentException("cronExpression cannot be null")`
/// 由全局异常处理器回文案，与空串/非法串的「cron表达式不正确」是两条路径。
fn validate_cron(body: &Value) -> Result<(), AjaxResult> {
    let Some(value) = body.get("cronExpression").filter(|value| !value.is_null()) else {
        return Err(AjaxResult::error("cronExpression cannot be null"));
    };
    if quartz_cron::is_valid(value.as_str().unwrap_or_default()) {
        Ok(())
    } else {
        Err(AjaxResult::error("cron表达式不正确"))
    }
}

/// Java: SysJob.getNextValidTime() —— `CronUtils.getNextExecution`。
/// 表达式非法时 Java 抛 `IllegalArgumentException(ParseException 文案)`，整个接口 500；
/// `cronExpression` 为空则直接给 `null`（`StringUtils.isNotEmpty` 短路）。
fn fill_next_valid_time(rows: &mut [Value]) -> Result<(), AppError> {
    let now = chrono::Local::now().naive_local();
    for row in rows {
        let Some(object) = row.as_object_mut() else {
            continue;
        };
        let expression = object
            .get("cronExpression")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let next = if expression.is_empty() {
            None
        } else {
            crate::service::quartz_cron::next_execution(&expression, now)
                .map_err(AppError::Service)?
        };
        object.insert(
            "nextValidTime".to_string(),
            json!(next.map(|time| time.format("%Y-%m-%d %H:%M:%S").to_string())),
        );
    }
    Ok(())
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "任务序号",
        "任务名称",
        "任务组名",
        "调用目标字符串",
        "执行表达式 ",
        "计划策略 ",
        "并发执行",
        "任务状态",
    ]
    .map(str::to_string);
    let fields = [
        "jobId",
        "jobName",
        "jobGroup",
        "invokeTarget",
        "cronExpression",
        "misfirePolicy",
        "concurrent",
        "status",
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
    // Java: `@PathVariable Long jobId`。
    let job_id = support::path_long("jobId", &job_id)?.to_string();
    let mut row = support::query_by_id(&state.db, &SPEC, &job_id).await?;
    if let Some(value) = row.as_mut() {
        fill_next_valid_time(std::slice::from_mut(value))?;
    }
    Ok(AjaxResult::success_data(
        row.map(|value| support::reorder_keys(value, JOB_KEYS)),
    ))
}

/// Java: `SysJobMapper.insertJob` 的 `<if>` 链——只认这些列，且 null 与空串都不写。
const INSERT_FIELDS: &[(&str, &str)] = &[
    ("jobId", "job_id"),
    ("jobName", "job_name"),
    ("jobGroup", "job_group"),
    ("invokeTarget", "invoke_target"),
    ("cronExpression", "cron_expression"),
    ("misfirePolicy", "misfire_policy"),
    ("concurrent", "concurrent"),
    ("status", "status"),
    ("remark", "remark"),
    ("createBy", "create_by"),
];

/// Java: `SysJobMapper.updateJob` 的 `<set>` 链；`status` 只判 null，其余还判空串。
const UPDATE_FIELDS: &[(&str, &str)] = &[
    ("jobName", "job_name"),
    ("jobGroup", "job_group"),
    ("invokeTarget", "invoke_target"),
    ("cronExpression", "cron_expression"),
    ("misfirePolicy", "misfire_policy"),
    ("concurrent", "concurrent"),
    ("status", "status"),
    ("remark", "remark"),
    ("updateBy", "update_by"),
];

/// Java: 实体里 null 或空串都不进 mapper（`jobId` 另外排除 0）。
fn mappable<'a>(body: &'a Value, key: &str, allow_empty: bool) -> Option<&'a Value> {
    let value = body.get(key).filter(|value| !value.is_null())?;
    if !allow_empty && matches!(value, Value::String(text) if text.is_empty()) {
        return None;
    }
    if key == "jobId" && value.as_i64() == Some(0) {
        return None;
    }
    Some(value)
}

/// Java: `jobMapper.insertJob(job)`，create_time 恒为最后一列 sysdate()。
async fn insert_job(
    tx: &mut sqlx::Transaction<'_, sqlx::MySql>,
    entity: &Value,
) -> Result<u64, AppError> {
    let mut columns: Vec<&str> = Vec::new();
    let mut values: Vec<&Value> = Vec::new();
    for (key, column) in INSERT_FIELDS {
        if let Some(value) = mappable(entity, key, false) {
            columns.push(column);
            values.push(value);
        }
    }

    let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new("insert into sys_job (");
    for (index, column) in columns.iter().enumerate() {
        if index > 0 {
            builder.push(", ");
        }
        builder.push(support::column_name(column));
    }
    builder.push(", create_time) values (");
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            builder.push(", ");
        }
        support::bind_value(&mut builder, value);
    }
    builder.push(", sysdate())");
    let rows = builder.build().execute(&mut **tx).await?.rows_affected();
    Ok(rows)
}

/// Java: `jobMapper.updateJob(job)`，update_time 恒为 sysdate()。
async fn update_job(
    tx: &mut sqlx::Transaction<'_, sqlx::MySql>,
    entity: &Value,
    job_id: i64,
) -> Result<u64, AppError> {
    let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new("update sys_job set ");
    let mut first = true;
    for (key, column) in UPDATE_FIELDS {
        // Java 的 `<if test="status !=null">` 只判 null，空串也会写进去。
        let allow_empty = *key == "status";
        if let Some(value) = mappable(entity, key, allow_empty) {
            if !first {
                builder.push(", ");
            }
            first = false;
            builder.push(format!("{} = ", support::column_name(column)));
            support::bind_value(&mut builder, value);
        }
    }
    if !first {
        builder.push(", ");
    }
    builder.push("update_time = sysdate() where job_id = ");
    builder.push_bind(job_id);
    let rows = builder.build().execute(&mut **tx).await?.rows_affected();
    Ok(rows)
}

/// 请求体 -> JobRow（Java 传给 createScheduleJob 的是实体本身，不是重查的库行）。
fn entity_row(entity: &Value, job_id: i64) -> quartz_runtime::JobRow {
    // 缺席 -> 实体初值 "0"；显式 null -> null（Java 的 switch(null) 抛 NPE）。
    let misfire_policy = match entity.get("misfirePolicy") {
        None => Some("0".to_string()),
        Some(value) => value.as_str().map(str::to_string),
    };
    quartz_runtime::JobRow {
        job_id,
        job_name: text(entity, "jobName"),
        job_group: text(entity, "jobGroup"),
        invoke_target: text(entity, "invokeTarget"),
        cron_expression: text(entity, "cronExpression"),
        misfire_policy,
        concurrent: text(entity, "concurrent"),
        status: entity
            .get("status")
            .and_then(Value::as_str)
            .map(str::to_string),
    }
}

/// Java: `SysJobController.add` + `SysJobServiceImpl.insertJob`。
async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    if let Err(result) = validate_cron(&body) {
        return Ok(result);
    }
    // Java: 控制器 setCreateBy，随后 insertJob 先 setStatus(PAUSE)——请求体的 status 被覆盖。
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert("status".to_string(), json!("1"));
    }

    let mut tx = state.db.begin().await?;
    let rows = insert_job(&mut tx, &entity).await?;
    // LAST_INSERT_ID() 的列元信息是 BIGINT UNSIGNED，只能按 u64 取回。
    let job_id: u64 = sqlx::query_scalar("select last_insert_id()")
        .fetch_one(&mut *tx)
        .await?;
    let job = entity_row(&entity, job_id as i64);
    let failure = if rows > 0 {
        quartz_runtime::create_schedule_job(&state, &job)
            .await
            .err()
        // Java: insertJob 只在 rows > 0 时才 createScheduleJob，没有任务时 rows 恒为 1
        // （useGeneratedKeys + 单行插入），所以这条分支就是「库里真有行」的分支。
    } else {
        None
    };
    // Java: `@Transactional` 只对 RuntimeException 回滚——TaskException/SchedulerException
    // 都是 checked，行留在库里；只有 misfirePolicy 为 null 的 NPE 会把刚插入的行撤掉。
    match failure {
        Some(quartz_runtime::ScheduleFailure::Rollback) => {
            tx.rollback().await?;
            return Ok(AjaxResult::error_null_msg());
        }
        Some(quartz_runtime::ScheduleFailure::Checked(message)) => {
            tx.commit().await?;
            return Ok(AjaxResult::error(message));
        }
        None => {}
    }
    tx.commit().await?;
    Ok(support::to_ajax(rows))
}

/// Java: `SysJobController.edit` + `SysJobServiceImpl.updateJob`。
async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    if let Err(result) = validate_cron(&body) {
        return Ok(result);
    }
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
    }
    let job_id = entity.get("jobId").and_then(Value::as_i64);
    // Java: properties = selectJobById(jobId)，用于拿**旧的**任务组名。
    let properties = match job_id {
        Some(job_id) => quartz_runtime::JobRow::load(&state.db, job_id).await,
        None => None,
    };

    let mut tx = state.db.begin().await?;
    // Java: `where job_id = #{jobId}`，jobId 为 null 时命中 0 行。
    let rows = match job_id {
        Some(job_id) => update_job(&mut tx, &entity, job_id).await?,
        None => 0,
    };

    let mut failure = None;
    if rows > 0 {
        if let (Some(job_id), Some(properties)) = (job_id, properties.clone()) {
            // Java: updateSchedulerJob —— 先按旧组名删掉已有 JobKey，再按实体（新组名）重建。
            quartz_runtime::delete(job_id, &properties.job_group);
            let mut job = entity_row(&entity, job_id);
            // mapper 跳过 null/空串，库里没改的字段要沿用旧值（实体那侧也是旧值）。
            if job.cron_expression.is_empty() {
                job.cron_expression = properties.cron_expression.clone();
            }
            if job.job_name.is_empty() {
                job.job_name = properties.job_name.clone();
            }
            if job.invoke_target.is_empty() {
                job.invoke_target = properties.invoke_target.clone();
            }
            if job.misfire_policy.is_none() && properties.misfire_policy.is_some() {
                job.misfire_policy = properties.misfire_policy.clone();
            }
            failure = quartz_runtime::create_schedule_job(&state, &job)
                .await
                .err();
        }
    }
    // Java: 同 insertJob——checked 异常照旧提交，NPE 才把这次 UPDATE 撤掉。
    match failure {
        Some(quartz_runtime::ScheduleFailure::Rollback) => {
            tx.rollback().await?;
            return Ok(AjaxResult::error_null_msg());
        }
        Some(quartz_runtime::ScheduleFailure::Checked(message)) => {
            tx.commit().await?;
            return Ok(AjaxResult::error(message));
        }
        None => {}
    }
    tx.commit().await?;
    Ok(support::to_ajax(rows))
}

/// Java: `SysJobController.changeStatus` + `SysJobServiceImpl.changeStatus`。
async fn change_status(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    // Java: 控制器先 selectJobById 再 newJob.setStatus(...)，查不到行就是 NPE -> msg 为 null。
    let Some(job_id) = body.get("jobId").and_then(Value::as_i64) else {
        return Ok(AjaxResult::error_null_msg());
    };
    let Some(mut new_job) = quartz_runtime::JobRow::load(&state.db, job_id).await else {
        return Ok(AjaxResult::error_null_msg());
    };
    let status = body
        .get("status")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    // Java: changeStatus 只认 "0"（resumeJob）与 "1"（pauseJob），其余 rows 恒 0 且不改库。
    if !matches!(status.as_str(), "0" | "1") {
        return Ok(support::to_ajax(0));
    }
    new_job.status = Some(status.clone());
    let entity = json!({
        "jobId": new_job.job_id,
        "jobName": new_job.job_name,
        "jobGroup": new_job.job_group,
        "invokeTarget": new_job.invoke_target,
        "cronExpression": new_job.cron_expression,
        "misfirePolicy": new_job.misfire_policy,
        "concurrent": new_job.concurrent,
        "status": new_job.status,
    });
    // Java: resumeJob/pauseJob 里都先 jobMapper.updateJob(job)，实体来自库里那一行。
    let mut tx = state.db.begin().await?;
    let rows = update_job(&mut tx, &entity, job_id).await?;
    let mut failure = None;
    if rows > 0 {
        if status == "0" {
            // Java: scheduler.resumeJob(getJobKey(jobId, **库里**的 jobGroup))
            failure = quartz_runtime::resume(&state, &new_job).await.err();
        } else {
            quartz_runtime::pause(job_id, &new_job.job_group);
        }
    }
    // Java: 调度器的注册不受事务管辖——回滚只撤数据库，trigger 仍然装进去了。
    match failure {
        Some(quartz_runtime::ScheduleFailure::Rollback) => {
            tx.rollback().await?;
            return Ok(AjaxResult::error_null_msg());
        }
        Some(quartz_runtime::ScheduleFailure::Checked(message)) => {
            tx.commit().await?;
            return Ok(AjaxResult::error(message));
        }
        None => {}
    }
    tx.commit().await?;
    Ok(support::to_ajax(rows))
}

/// Java: `SysJobServiceImpl.run` —— `scheduler.triggerJob(getJobKey(body.jobId, body.jobGroup), dataMap)`。
async fn run(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let group = text(&body, "jobGroup");
    // Java: jobId 为 null 时 JobKey 名字是 "TASK_CLASS_NAMEnull"，调度器里必然查不到。
    let Some(job_id) = body.get("jobId").and_then(Value::as_i64) else {
        return Ok(AjaxResult::error(format!(
            "The job ({}.TASK_CLASS_NAMEnull) referenced by the trigger does not exist.",
            quartz_runtime::normalize_group(&group)
        )));
    };
    let row = quartz_runtime::JobRow::load(&state.db, job_id).await;
    match quartz_runtime::trigger(&state, job_id, &group, row) {
        Ok(()) => Ok(AjaxResult::success()),
        Err(message) => Ok(AjaxResult::error(message)),
    }
}

/// Java: `SysJobServiceImpl.deleteJobByIds` —— 逐条 selectJobById 后 deleteJob，查不到即 NPE。
async fn remove(
    State(state): State<AppState>,
    Path(job_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] jobIds` —— 出错时文案里是整段路径变量原文，不是失败的那一段。
    let ids = support::path_long_list("jobIds", &job_ids)?;
    for job_id in ids {
        let Some(job) = quartz_runtime::JobRow::load(&state.db, job_id).await else {
            return Ok(AjaxResult::error_null_msg());
        };
        let rows =
            support::delete_by_ids(&state.db, "sys_job", "job_id", &[job_id.to_string()]).await?;
        if rows > 0 {
            quartz_runtime::delete(job_id, &job.job_group);
        }
    }
    Ok(AjaxResult::success())
}
