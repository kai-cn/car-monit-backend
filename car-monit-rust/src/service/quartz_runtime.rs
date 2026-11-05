// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/ScheduleUtils.java
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/AbstractQuartzJob.java
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/QuartzJobExecution.java
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobServiceImpl.java
// 职责: sys_job 的运行时调度（Quartz RAMJobStore -> tokio 循环）与执行日志。
// 对应关系: Scheduler.scheduleJob/pauseJob/resumeJob/deleteJob/triggerJob -> registry + 循环。
//
// 与 Java 的两处实现差异（行为等价，只有边界不同）：
// 1. `concurrent = "0"`（允许并发）时 Java 会让同一任务的两次触发重叠，Rust 侧串行；
//    本库现有 job 全是 `concurrent = '1'`，取不到差异。
// 2. `exceptionInfo` Java 写完整栈（截断 2000 字符），Rust 只有异常首行。

use std::collections::{HashMap, HashSet};
use std::sync::{LazyLock, Mutex};

use serde_json::json;

use crate::api::support;
use crate::service::{job_invoke, quartz_cron};
use crate::state::AppState;

type JobHandle = tokio::task::JoinHandle<()>;

/// Java: `ScheduleConstants.TASK_CLASS_NAME`，JobKey/TriggerKey 的名字前缀。
pub const TASK_CLASS_NAME: &str = "TASK_CLASS_NAME";

/// 已注册的 JobKey（RAMJobStore 里的 JobDetail），决定 `/monitor/job/run` 能否触发。
static REGISTERED: LazyLock<Mutex<HashSet<(i64, String)>>> =
    LazyLock::new(|| Mutex::new(HashSet::new()));

/// 正在跑的触发循环；暂停 = 移除句柄但保留注册。
static LOOPS: LazyLock<Mutex<HashMap<(i64, String), JobHandle>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

/// Java: `KeyImpl` 的组缺省值——`group == null` 时保持字段初值 "DEFAULT"。
pub fn normalize_group(group: &str) -> String {
    if group.trim().is_empty() {
        "DEFAULT".to_string()
    } else {
        group.to_string()
    }
}

/// Java: `ScheduleUtils.getJobKey(jobId, jobGroup)`。
pub fn key(job_id: i64, group: &str) -> (i64, String) {
    (job_id, normalize_group(group))
}

/// Java: `scheduler.checkExists(jobKey)`。
pub fn exists(job_id: i64, group: &str) -> bool {
    REGISTERED.lock().unwrap().contains(&key(job_id, group))
}

/// Java: SysJob 实体（调度器真正用到的字段）。
#[derive(Debug, Clone)]
pub struct JobRow {
    pub job_id: i64,
    pub job_name: String,
    pub job_group: String,
    pub invoke_target: String,
    pub cron_expression: String,
    /// Java 实体初值是 "0"，但显式 null（请求体或库里）会覆盖成 null -> `switch` 抛 NPE。
    pub misfire_policy: Option<String>,
    pub concurrent: String,
    /// Java: `SysJob.status` 可为 null；`createScheduleJob` 末尾 `getStatus().equals(PAUSE)`
    /// 会因此抛 NPE，所以这里必须区分「没给」与「给了空串」。
    pub status: Option<String>,
}

const ROW_SELECT: &str = "select job_id, job_name, job_group, invoke_target, cron_expression, \
                          misfire_policy, concurrent, status from sys_job";

/// `ROW_SELECT` 的解码元组；除主键与调用串外都允许 NULL。
type JobTuple = (
    i64,
    Option<String>,
    Option<String>,
    String,
    Option<String>,
    Option<String>,
    Option<String>,
    Option<String>,
);

fn owned(value: Option<String>) -> String {
    value.unwrap_or_default()
}

impl JobRow {
    fn from_tuple(row: JobTuple) -> JobRow {
        let (
            job_id,
            job_name,
            job_group,
            invoke_target,
            cron_expression,
            misfire_policy,
            concurrent,
            status,
        ) = row;
        JobRow {
            job_id,
            job_name: owned(job_name),
            job_group: owned(job_group),
            invoke_target,
            cron_expression: owned(cron_expression),
            // Java: MyBatis 会用列值调用 setter，库里是 NULL 就覆盖掉实体的 "0" 初值。
            misfire_policy,
            concurrent: owned(concurrent),
            status,
        }
    }

    /// Java: `jobMapper.selectJobById(jobId)`。
    pub async fn load(pool: &sqlx::MySqlPool, job_id: i64) -> Option<JobRow> {
        let row = sqlx::query_as::<_, JobTuple>(&format!("{ROW_SELECT} where job_id = ?"))
            .bind(job_id)
            .fetch_optional(pool)
            .await
            .ok()?;
        row.map(JobRow::from_tuple)
    }
}

/// Java: `SysJobServiceImpl.init()` —— `selectJobAll` 后逐条 createScheduleJob。
/// 注意装载的是**全部**行（暂停的也在调度器里，所以「立即执行」照样能跑）。
pub fn start_jobs(state: &AppState) {
    let state = state.clone();
    tokio::spawn(async move {
        let rows = sqlx::query_as::<_, JobTuple>(ROW_SELECT)
            .fetch_all(&state.db)
            .await;
        let rows = match rows {
            Ok(rows) => rows,
            Err(err) => {
                tracing::warn!("[定时任务] 加载 sys_job 失败: {err}");
                return;
            }
        };
        for row in rows {
            let job = JobRow::from_tuple(row);
            if let Err(err) = create_schedule_job(&state, &job).await {
                // Java: @PostConstruct 抛出去就直接启动失败；Rust 侧记录后跳过，
                // 否则一条脏数据会让整个服务起不来。
                tracing::error!("[定时任务] 装载 job {} 失败: {}", job.job_id, err.message());
            }
        }
    });
}

/// Java: `SysJob` 实体的 misfirePolicy 初值是 `MISFIRE_DEFAULT("0")`，
/// 但请求体显式发 null（或库里就是 NULL）会被覆盖成 null —— Java 的
/// `switch (job.getMisfirePolicy())` 于是抛 NPE（RuntimeException，事务回滚）。
pub enum ScheduleFailure {
    /// TaskException / SchedulerException 都是 checked 异常，`@Transactional` 默认**不回滚**，
    /// 行留在库里（实测 `misfire_policy = '9'` 与年份越界两种情况都留下了行）。
    Checked(String),
    /// NullPointerException 是 RuntimeException，事务回滚；文案无 message。
    Rollback,
}

impl ScheduleFailure {
    /// 日志用的一行描述。
    pub fn message(&self) -> String {
        match self {
            ScheduleFailure::Checked(text) => text.clone(),
            ScheduleFailure::Rollback => "java.lang.NullPointerException".to_string(),
        }
    }
}

/// Java: `ScheduleUtils.createScheduleJob`，按 Java 的先后顺序做三件校验：
/// misfire 策略 -> trigger 首个触发时间 -> 暂停态。前两步失败不回滚，NPE 会。
pub async fn create_schedule_job(state: &AppState, job: &JobRow) -> Result<(), ScheduleFailure> {
    // Java: handleCronScheduleMisfirePolicy
    match job.misfire_policy.as_deref() {
        None => return Err(ScheduleFailure::Rollback),
        Some("0") | Some("1") | Some("2") | Some("3") => {}
        Some(policy) => {
            return Err(ScheduleFailure::Checked(format!(
                "The task misfire policy '{policy}' cannot be used in cron schedule tasks"
            )));
        }
    }
    // Java: CronTriggerImpl.validate() -> computeFirstFireTime
    let expression = quartz_cron::QuartzCron::parse(&job.cron_expression)
        .map_err(|_| ScheduleFailure::Checked(cron_trigger_message(&job.job_group, job.job_id)))?;
    if expression
        .next_after(chrono::Local::now().naive_local())
        .is_none()
    {
        return Err(ScheduleFailure::Checked(cron_trigger_message(
            &job.job_group,
            job.job_id,
        )));
    }
    register(state, job, expression);
    // Java: `if (job.getStatus().equals(ScheduleConstants.Status.PAUSE.getValue()))`——
    // 只有 "1" 会 pauseJob；status 为 null 时这一句本身就是 NPE（trigger 已经装进去了）。
    match job.status.as_deref() {
        Some("1") => pause(job.job_id, &job.job_group),
        Some(_) => {}
        None => return Err(ScheduleFailure::Rollback),
    }
    Ok(())
}

fn cron_trigger_message(group: &str, job_id: i64) -> String {
    format!(
        "Based on configured schedule, the given trigger '{}.{TASK_CLASS_NAME}{job_id}' will never fire.",
        normalize_group(group)
    )
}

fn register(state: &AppState, job: &JobRow, expression: quartz_cron::QuartzCron) {
    let key = key(job.job_id, &job.job_group);
    REGISTERED.lock().unwrap().insert(key.clone());
    stop_loop(&key);
    let state = state.clone();
    let job = job.clone();
    let handle = tokio::spawn(async move {
        let mut after = chrono::Local::now().naive_local();
        loop {
            let Some(next) = expression.next_after(after) else {
                break;
            };
            let wait = (next - chrono::Local::now().naive_local()).num_milliseconds();
            if wait > 0 {
                tokio::time::sleep(std::time::Duration::from_millis(wait as u64)).await;
            }
            run_job(&state, &job).await;
            after = next;
        }
    });
    LOOPS.lock().unwrap().insert(key, handle);
}

/// Java: `scheduler.pauseJob(jobKey)`——保留 JobDetail，只停 trigger。
pub fn pause(job_id: i64, group: &str) {
    stop_loop(&key(job_id, group));
}

/// Java: `scheduler.resumeJob(jobKey)`——按当前行重新启动 trigger。
pub async fn resume(state: &AppState, job: &JobRow) -> Result<(), ScheduleFailure> {
    create_schedule_job(state, job).await
}

/// Java: `scheduler.deleteJob(jobKey)`。
pub fn delete(job_id: i64, group: &str) {
    let key = key(job_id, group);
    stop_loop(&key);
    REGISTERED.lock().unwrap().remove(&key);
}

fn stop_loop(key: &(i64, String)) {
    if let Some(handle) = LOOPS.lock().unwrap().remove(key) {
        handle.abort();
    }
}

/// Java: `scheduler.triggerJob(jobKey, dataMap)`；`dataMap` 放的是刚查出来的行。
/// 未注册时 Java 抛 `SchedulerException("The job (KEY) referenced by the trigger does not exist.")`。
pub fn trigger(
    state: &AppState,
    job_id: i64,
    group: &str,
    row: Option<JobRow>,
) -> Result<(), String> {
    if !exists(job_id, group) {
        return Err(format!(
            "The job ({}.{TASK_CLASS_NAME}{job_id}) referenced by the trigger does not exist.",
            normalize_group(group)
        ));
    }
    let state = state.clone();
    let job = row.unwrap_or_else(|| JobRow {
        job_id,
        job_name: String::new(),
        job_group: normalize_group(group),
        invoke_target: String::new(),
        cron_expression: String::new(),
        misfire_policy: Some("0".to_string()),
        concurrent: "1".to_string(),
        status: Some("1".to_string()),
    });
    tokio::spawn(async move {
        run_job(&state, &job).await;
    });
    Ok(())
}

/// Java: `AbstractQuartzJob.execute` -> `after(...)`，成功失败都写 sys_job_log。
async fn run_job(state: &AppState, job: &JobRow) {
    let started = chrono::Local::now().naive_local();
    let outcome = job_invoke::invoke(state, &job.invoke_target).await;
    let stopped = chrono::Local::now().naive_local();
    let (status, exception) = match &outcome {
        Ok(()) => ("0", String::new()),
        Err(err) => ("1", err.clone()),
    };
    if let Err(err) = &outcome {
        tracing::error!(
            "[定时任务] job {} ({}) 执行失败: {err}",
            job.job_id,
            job.job_name
        );
    }
    // Java: sysJobLog.getJobName() + " 总共耗时：" + runMs + "毫秒"
    let elapsed = (stopped - started).num_milliseconds();
    let mut body = json!({
        "jobName": job.job_name,
        "jobGroup": job.job_group,
        "invokeTarget": job.invoke_target,
        "jobMessage": format!("{} 总共耗时：{elapsed}毫秒", job.job_name),
        "status": status,
        "createTime": support::now_string(),
    });
    if !exception.is_empty() {
        // Java: StringUtils.substring(ExceptionUtil.getExceptionMessage(e), 0, 2000)
        body["exceptionInfo"] = json!(truncate(&exception, 2000));
    }
    if let Err(err) =
        support::insert_entity(&state.db, "sys_job_log", &body, support::AutoFill::NONE).await
    {
        tracing::warn!("[定时任务] 写入 sys_job_log 失败: {err}");
    }
}

fn truncate(text: &str, max: usize) -> String {
    text.chars().take(max).collect()
}

/// Java: `JobInvokeUtil.invokeMethod` —— 保留旧入口名，实现在 `service::job_invoke`。
pub async fn dispatch_job(state: &AppState, target: &str) -> Result<(), String> {
    job_invoke::invoke(state, target).await
}
