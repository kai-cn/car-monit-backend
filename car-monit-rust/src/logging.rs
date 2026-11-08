// 来源: ruoyi-admin/src/main/resources/logback.xml
// 职责: 复刻 logback 的四个文件 appender + 日志格式 + 本地时区按天/按大小滚动。
// 对应关系:
//   sys-info/sys-error/sys-slow/sys-user appender -> start_appender("sys-*")
//   log.pattern -> JavaLogFormat
//   SizeAndTimeBasedFNATP -> RollingWriter(max_bytes)
//   maxHistory -> cleanup()

use backtrace::Backtrace;
use std::error::Error;
use std::fmt;
use std::fs::{File, OpenOptions};
use std::future::Future;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::mpsc::{sync_channel, Receiver, SyncSender, TrySendError};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;

use chrono::{Days, Local, NaiveDate, TimeZone};
use tracing::field::{Field, Visit};
use tracing::{Event, Subscriber};
use tracing_subscriber::fmt::format::Writer;
use tracing_subscriber::fmt::{FmtContext, FormatEvent, FormatFields, MakeWriter};
use tracing_subscriber::registry::LookupSpan;

const CHANNEL_CAPACITY: usize = 1024;
const DATE_LEN: usize = 10;
const TRACE_ID_TARGET: &str = "com.ruoyi.common.core.monitor.TraceIdFilter";
pub const SQL_LOG_TARGET: &str = "com.ruoyi.common.core.monitor.SqlLogInterceptor";
/// SQLx 内建 SQL 日志事件（LogSettings）的 target；对应 Java SqlLogInterceptor。
pub const SQLX_QUERY_TARGET: &str = "sqlx::query";
const USER_LOG_TARGET: &str = "sys-user";
/// Java SqlLogInterceptor.java 中 log.warn / log.debug / log.debug / log.error 的调用行号（%L）。
const SQL_WARN_LINE: u32 = 139;
const SQL_DEBUG_LINE: u32 = 156;
const SQL_DEBUG_TEXT_LINE: u32 = 159;
const SQL_ERROR_LINE: u32 = 165;
/// Rust 侧拿不到 MyBatis MappedStatement#getId（Mapper FQCN + 方法名）。
const SQL_MAPPER_PLACEHOLDER: &str = "sqlx::query";

tokio::task_local! {
    static TRACE_ID: String;
    /// Java Servlet 请求线程名（`http-nio-<port>-exec-<n>` 形态）。
    static LOG_THREAD: String;
}

static REQUEST_SEQUENCE: AtomicU64 = AtomicU64::new(0);

/// 让日志格式能读到当前请求的 traceId（Java 用 MDC）。
pub async fn with_trace_id<F>(trace_id: String, future: F) -> F::Output
where
    F: Future,
{
    TRACE_ID.scope(trace_id, future).await
}

/// 进入一次请求：绑定 traceId + 请求逻辑线程名。
/// Java 每个请求跑在 Tomcat 工作线程上（`http-nio-<port>-exec-<n>`）；
/// Rust 是异步任务模型，这里给每个请求分配稳定序号，输出同等形态的线程名。
pub async fn with_request_context<F>(trace_id: String, port: u16, future: F) -> F::Output
where
    F: Future,
{
    let sequence = REQUEST_SEQUENCE.fetch_add(1, Ordering::Relaxed) + 1;
    let thread = format!("http-nio-{port}-exec-{sequence}");
    TRACE_ID
        .scope(trace_id, LOG_THREAD.scope(thread, future))
        .await
}

/// 后台任务线程名（调度器/Quartz）；未标注时回退到操作系统线程名。
pub async fn with_log_thread<F>(thread: impl Into<String>, future: F) -> F::Output
where
    F: Future,
{
    LOG_THREAD.scope(thread.into(), future).await
}

pub fn current_trace_id() -> String {
    TRACE_ID.try_with(|value| value.clone()).unwrap_or_default()
}

/// 当前日志线程名：请求逻辑线程 > 显式后台线程名 > 真实线程名。
pub fn current_log_thread() -> String {
    LOG_THREAD
        .try_with(|value| value.clone())
        .unwrap_or_else(|_| {
            let actual = std::thread::current()
                .name()
                .unwrap_or_default()
                .to_string();
            // 不把 Rust 运行时实现细节（tokio-rt-worker / tokio-runtime-worker）透到日志里；
            // Java 后台任务跑在调度线程上，这里用 Spring 默认调度线程名做等价占位。
            if actual.starts_with("tokio-") {
                "scheduling-1".to_string()
            } else {
                actual
            }
        })
}

enum Command {
    Write(Vec<u8>),
    Flush,
    Shutdown,
}

/// 可克隆的 MakeWriter；每个日志事件写到一个有界通道，由后台线程落盘。
#[derive(Clone)]
pub struct LogWriter {
    tx: Arc<Mutex<SyncSender<Command>>>,
}

pub struct LogHandle {
    tx: Arc<Mutex<SyncSender<Command>>>,
    join: Option<JoinHandle<()>>,
}

impl LogHandle {
    pub fn writer(&self) -> LogWriter {
        LogWriter {
            tx: self.tx.clone(),
        }
    }
}

impl Drop for LogHandle {
    fn drop(&mut self) {
        if let Ok(sender) = self.tx.lock() {
            let _ = sender.send(Command::Shutdown);
        }
        if let Some(join) = self.join.take() {
            let _ = join.join();
        }
    }
}

impl<'a> MakeWriter<'a> for LogWriter {
    type Writer = LogGuard;

    fn make_writer(&'a self) -> Self::Writer {
        LogGuard {
            tx: self.tx.clone(),
        }
    }
}

pub struct LogGuard {
    tx: Arc<Mutex<SyncSender<Command>>>,
}

impl Write for LogGuard {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        if buf.is_empty() {
            return Ok(0);
        }
        let result = self
            .tx
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
            .try_send(Command::Write(buf.to_vec()));
        match result {
            Ok(()) | Err(TrySendError::Full(_)) | Err(TrySendError::Disconnected(_)) => {
                Ok(buf.len())
            }
        }
    }

    fn flush(&mut self) -> io::Result<()> {
        let _ = self
            .tx
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
            .try_send(Command::Flush);
        Ok(())
    }
}

/// 启动一个文件 appender。
/// `indexed` = Java fileNamePattern 是否含 `%i`（只有 sys-info/sys-error 含）。
pub fn start_appender(
    dir: impl AsRef<Path>,
    name: &str,
    indexed: bool,
    max_bytes: u64,
    max_history: u32,
) -> io::Result<LogHandle> {
    let dir = dir.as_ref().to_path_buf();
    std::fs::create_dir_all(&dir)?;
    let (tx, rx) = sync_channel(CHANNEL_CAPACITY);
    let writer = RollingWriter {
        dir,
        name: name.to_string(),
        indexed,
        max_bytes: if indexed { max_bytes.max(1) } else { u64::MAX },
        max_history: max_history.max(1),
        date: String::new(),
        index: 0,
        file: None,
        size: 0,
    };
    let join = std::thread::Builder::new()
        .name(format!("log-{name}"))
        .spawn(move || writer.run(rx))?;
    Ok(LogHandle {
        tx: Arc::new(Mutex::new(tx)),
        join: Some(join),
    })
}

/// Java logback 的 `100MB` / `512KB` / `1GB` 写法。
pub fn parse_size(text: &str) -> u64 {
    let text = text.trim().to_ascii_uppercase();
    for (suffix, unit) in [
        ("GB", 1024u64 * 1024 * 1024),
        ("MB", 1024 * 1024),
        ("KB", 1024),
    ] {
        if let Some(number) = text.strip_suffix(suffix) {
            if let Ok(value) = number.trim().parse::<u64>() {
                return value.saturating_mul(unit).max(1);
            }
        }
    }
    text.parse::<u64>()
        .map(|value| value.max(1))
        .unwrap_or(100 * 1024 * 1024)
}

struct RollingWriter {
    dir: PathBuf,
    name: String,
    indexed: bool,
    max_bytes: u64,
    max_history: u32,
    date: String,
    index: u32,
    file: Option<File>,
    size: u64,
}

impl RollingWriter {
    fn run(mut self, rx: Receiver<Command>) {
        if let Err(err) = self.ensure_active() {
            eprintln!("初始化日志文件 {} 失败: {err}", self.name);
        }
        self.cleanup();
        while let Ok(command) = rx.recv() {
            match command {
                Command::Write(bytes) => {
                    if let Err(err) = self.write_bytes(&bytes) {
                        eprintln!("写日志文件 {} 失败: {err}", self.name);
                    }
                }
                Command::Flush => {
                    if let Some(file) = self.file.as_mut() {
                        let _ = file.flush();
                    }
                }
                Command::Shutdown => {
                    let _ = self.flush();
                    break;
                }
            }
        }
    }

    fn write_bytes(&mut self, bytes: &[u8]) -> io::Result<()> {
        let today = local_date();
        if self.date != today {
            self.archive_active(&self.date.clone())?;
            self.date = today.clone();
            self.index = self.next_index(&today);
            self.open_active()?;
            self.cleanup();
        }
        if self.file.is_none() {
            self.open_active()?;
        }
        if self.indexed
            && self.size > 0
            && self.size.saturating_add(bytes.len() as u64) > self.max_bytes
        {
            let date = self.date.clone();
            self.archive_active(&date)?;
            self.index = self.next_index(&date);
            self.open_active()?;
        }
        let file = self.file.as_mut().expect("日志文件已打开");
        file.write_all(bytes)?;
        self.size = self.size.saturating_add(bytes.len() as u64);
        Ok(())
    }

    fn ensure_active(&mut self) -> io::Result<()> {
        let today = local_date();
        let active = self.active_path();
        let metadata = std::fs::metadata(&active).ok();
        if let Some(metadata) = metadata {
            let modified_date = metadata
                .modified()
                .ok()
                .and_then(|time| {
                    Local
                        .timestamp_opt(
                            time.duration_since(std::time::UNIX_EPOCH).ok()?.as_secs() as i64,
                            0,
                        )
                        .single()
                })
                .map(|time| time.format("%Y-%m-%d").to_string())
                .unwrap_or_else(|| today.clone());
            self.date = modified_date.clone();
            self.index = self.next_index(&modified_date);
            if metadata.len() > 0 {
                self.open_active()?;
                if modified_date != today {
                    self.archive_active(&modified_date)?;
                } else if self.indexed && self.size >= self.max_bytes {
                    self.archive_active(&self.date.clone())?;
                } else {
                    return Ok(());
                }
            }
        }
        self.date = today.clone();
        self.index = self.next_index(&today);
        self.file = None;
        self.size = 0;
        self.open_active()
    }

    fn open_active(&mut self) -> io::Result<()> {
        let path = self.active_path();
        let size = std::fs::metadata(&path).map(|meta| meta.len()).unwrap_or(0);
        let file = OpenOptions::new().create(true).append(true).open(&path)?;
        self.file = Some(file);
        self.size = size;
        Ok(())
    }

    fn archive_active(&mut self, date: &str) -> io::Result<()> {
        let Some(mut file) = self.file.take() else {
            return Ok(());
        };
        let _ = file.flush();
        drop(file);
        if self.size == 0 {
            self.size = 0;
            return Ok(());
        }
        let active = self.active_path();
        let archive = self.archive_path(date, self.index);
        if !self.indexed && archive.exists() {
            let mut source = File::open(&active)?;
            let mut target = OpenOptions::new()
                .create(true)
                .append(true)
                .open(&archive)?;
            io::copy(&mut source, &mut target)?;
            std::fs::remove_file(&active)?;
        } else {
            std::fs::rename(&active, &archive)?;
        }
        self.size = 0;
        Ok(())
    }

    fn active_path(&self) -> PathBuf {
        self.dir.join(format!("{}.log", self.name))
    }

    fn archive_path(&self, date: &str, index: u32) -> PathBuf {
        if self.indexed {
            self.dir
                .join(format!("{}.{}.{}.log", self.name, date, index))
        } else {
            self.dir.join(format!("{}.{}.log", self.name, date))
        }
    }

    fn next_index(&self, date: &str) -> u32 {
        if !self.indexed {
            return 0;
        }
        let mut next = 0;
        let Ok(entries) = std::fs::read_dir(&self.dir) else {
            return next;
        };
        let prefix = format!("{}.{}.", self.name, date);
        for entry in entries.flatten() {
            let name = entry.file_name();
            let Some(name) = name.to_str() else {
                continue;
            };
            let Some(rest) = name.strip_prefix(&prefix) else {
                continue;
            };
            let Some(number) = rest.strip_suffix(".log") else {
                continue;
            };
            if let Ok(index) = number.parse::<u32>() {
                next = next.max(index.saturating_add(1));
            }
        }
        next
    }

    fn flush(&mut self) -> io::Result<()> {
        if let Some(file) = self.file.as_mut() {
            file.flush()?;
        }
        Ok(())
    }

    /// Java logback `maxHistory`：删除早于 `today - max_history` 天的归档文件。
    fn cleanup(&self) {
        let today = Local::now().date_naive();
        let Some(cutoff) = today.checked_sub_days(Days::new(self.max_history as u64)) else {
            return;
        };
        let prefix = format!("{}.", self.name);
        let Ok(entries) = std::fs::read_dir(&self.dir) else {
            return;
        };
        for entry in entries.flatten() {
            let name = entry.file_name();
            let Some(name) = name.to_str() else {
                continue;
            };
            let Some(rest) = name.strip_prefix(&prefix) else {
                continue;
            };
            if rest.len() < DATE_LEN {
                continue;
            }
            let date_text = &rest[..DATE_LEN];
            let Ok(date) = NaiveDate::parse_from_str(date_text, "%Y-%m-%d") else {
                continue;
            };
            if date < cutoff {
                let _ = std::fs::remove_file(entry.path());
            }
        }
    }
}

fn local_date() -> String {
    Local::now().format("%Y-%m-%d").to_string()
}

/// Java: log.pattern / log.console.pattern。
#[derive(Debug, Clone, Copy)]
pub struct JavaLogFormat {
    pub console: bool,
    pub logger_width: usize,
    /// Java: `monitor.slow-sql-threshold`，用于慢 SQL 框里的「阈值」。
    pub slow_sql_threshold_ms: u64,
}

impl JavaLogFormat {
    fn write_prefix(
        &self,
        writer: &mut Writer<'_>,
        now: chrono::DateTime<Local>,
        level: &str,
        target: &str,
        line: u32,
    ) -> fmt::Result {
        if self.console {
            write!(
                writer,
                "{} [{}] {:<5} [{}] {} - ",
                now.format("%H:%M:%S%.3f"),
                thread_name(),
                level,
                current_trace_id(),
                abbreviate_logger(target, self.logger_width)
            )
        } else {
            write!(
                writer,
                "{} [{}] {:<5} [{}] {}:{} - ",
                now.format("%Y-%m-%d %H:%M:%S%.3f"),
                thread_name(),
                level,
                current_trace_id(),
                abbreviate_logger(target, self.logger_width),
                line
            )
        }
    }
}

impl<S, N> FormatEvent<S, N> for JavaLogFormat
where
    S: Subscriber + for<'a> LookupSpan<'a>,
    N: for<'a> FormatFields<'a> + 'static,
{
    fn format_event(
        &self,
        _ctx: &FmtContext<'_, S, N>,
        mut writer: Writer<'_>,
        event: &Event<'_>,
    ) -> fmt::Result {
        let metadata = event.metadata();
        let now = Local::now();
        let level = metadata.level().as_str();

        // SQLx 的 SQL 事件对应 Java SqlLogInterceptor：WARN 慢 SQL 框、
        // DEBUG 的 [SQL]/[SQL-Text] 两行（Java 默认 logger level=info 会抑制 DEBUG）。
        if metadata.target() == SQLX_QUERY_TARGET {
            let mut visitor = MessageVisitor::default();
            event.record(&mut visitor);
            match *metadata.level() {
                tracing::Level::WARN => {
                    self.write_prefix(
                        &mut writer,
                        now,
                        level,
                        SQL_LOG_TARGET,
                        SQL_WARN_LINE,
                    )?;
                    write_slow_sql_box(&mut writer, &visitor, self.slow_sql_threshold_ms)?;
                    return writeln!(writer);
                }
                tracing::Level::DEBUG => {
                    let (cost, sql) = sql_event_details(&visitor);
                    self.write_prefix(
                        &mut writer,
                        now,
                        level,
                        SQL_LOG_TARGET,
                        SQL_DEBUG_LINE,
                    )?;
                    write!(
                        &mut writer,
                        "[SQL] {} | 耗时: {}ms | TraceId: {}",
                        SQL_MAPPER_PLACEHOLDER,
                        cost,
                        current_trace_id()
                    )?;
                    writeln!(writer)?;
                    self.write_prefix(
                        &mut writer,
                        now,
                        level,
                        SQL_LOG_TARGET,
                        SQL_DEBUG_TEXT_LINE,
                    )?;
                    write!(&mut writer, "[SQL-Text] {sql}")?;
                    return writeln!(writer);
                }
                _ => {}
            }
        }

        self.write_prefix(
            &mut writer,
            now,
            level,
            display_target(metadata.target()),
            log_line(metadata.target(), metadata.line()),
        )?;
        let mut visitor = MessageVisitor::default();
        event.record(&mut visitor);
        if let Some(message) = visitor.message {
            write!(writer, "{message}")?;
        }
        for (key, value) in visitor.fields {
            write!(writer, " {key}={value}")?;
        }
        if let Some(throwable) = visitor.throwable {
            // logback: `%msg%n` 之后紧跟 ThrowableProxyConverter 的输出。
            writeln!(writer)?;
            write!(writer, "{throwable}")?;
        }
        writeln!(writer)
    }
}

/// Rust 模块 target -> Java 全类名。
/// 只收录在 Java 侧真实存在、且职责对应的类；Rust 特有的调度/分页诊断
/// （task/mod.rs、api/support.rs）以及启动日志没有同等 Java 类，保持原 target。
const JAVA_TARGETS: &[(&str, &str)] = &[
    (
        "car_monit_rust::api::base::cdc",
        "com.ruoyi.base.service.cdc.DeadLetterQueueService",
    ),
    (
        "car_monit_rust::api::base::geometry",
        "com.ruoyi.web.controller.base.GeometryController",
    ),
    (
        "car_monit_rust::api::base::ods_lwzxsfsj_fee_station_exit01",
        "com.ruoyi.web.controller.base.OdsLwzxsfsjFeeStationExit01Controller",
    ),
    (
        "car_monit_rust::api::common::common",
        "com.ruoyi.web.controller.common.CommonController",
    ),
    (
        "car_monit_rust::api::common::down_template",
        "com.ruoyi.web.controller.common.DownTemplateController",
    ),
    (
        "car_monit_rust::api::manager::buss_test",
        "com.ruoyi.web.controller.manager.BussTestController",
    ),
    (
        "car_monit_rust::api::system::sys_file",
        "com.ruoyi.system.service.impl.SysFileServiceImpl",
    ),
    (
        "car_monit_rust::auth::audit",
        "com.ruoyi.framework.manager.factory.AsyncFactory",
    ),
    (
        "car_monit_rust::service::hen_da",
        "com.ruoyi.base.service.impl.HenDaServiceImpl",
    ),
    (
        "car_monit_rust::service::job_invoke",
        "com.ruoyi.quartz.util.JobInvokeUtil",
    ),
    (
        "car_monit_rust::service::road_path",
        "com.ruoyi.base.service.impl.RoadPathImpl",
    ),
    (
        "car_monit_rust::service::snapshot_flow_enhanced",
        "com.ruoyi.base.service.enhanced.SnapshotFlowEnhancedService",
    ),
    (
        "car_monit_rust::task::partition_maintenance",
        "com.ruoyi.quartz.task.PartitionMaintenanceTask",
    ),
    (
        "car_monit_rust::task::remote",
        "com.ruoyi.base.service.forest.HttpOdsRtSzdnSnapshotFlowAddcodeService",
    ),
    (
        "car_monit_rust::task::sharding_table",
        "com.ruoyi.base.task.ShardingTableTask",
    ),
    (
        "car_monit_rust::task::snapshot_flow_sync",
        "com.ruoyi.quartz.task.SnapshotFlowSyncTask",
    ),
    (
        "car_monit_rust::task::view_maintenance",
        "com.ruoyi.base.task.ViewMaintenanceTask",
    ),
];

/// Rust 模块 target -> Java 全类名。没有 Java 对应类的模块保持原 target。
fn display_target(target: &str) -> &str {
    if target == SQLX_QUERY_TARGET {
        return SQL_LOG_TARGET;
    }
    for (rust, java) in JAVA_TARGETS {
        if let Some(rest) = target.strip_prefix(rust) {
            if rest.is_empty() || rest.starts_with("::") {
                return java;
            }
        }
    }
    target
}

/// Java logback 的 `%L`：SQLx 事件映射到 SqlLogInterceptor.java 的调用行。
fn log_line(target: &str, rust_line: Option<u32>) -> u32 {
    match target {
        SQLX_QUERY_TARGET => SQL_WARN_LINE,
        SQL_LOG_TARGET => SQL_ERROR_LINE,
        _ => rust_line.unwrap_or(0),
    }
}

fn sql_event_details(visitor: &MessageVisitor) -> (u64, String) {
    let cost = visitor
        .field("elapsed_secs")
        .and_then(|value| value.parse::<f64>().ok())
        .map(|secs| secs * 1000.0)
        .or_else(|| parse_elapsed_ms(visitor.field("elapsed")))
        .unwrap_or(0.0);
    let sql = visitor
        .field("db.statement")
        .filter(|value| !value.trim().is_empty())
        .or(visitor.message.as_deref())
        .unwrap_or_default();
    (cost as u64, normalize_sql(sql))
}

/// Java `getFullSql`：`replaceAll("[\\s]+", " ")` + 2000 字符截断。
fn normalize_sql(sql: &str) -> String {
    let collapsed = sql.split_whitespace().collect::<Vec<_>>().join(" ");
    if collapsed.chars().count() > 2000 {
        let mut truncated: String = collapsed.chars().take(2000).collect();
        truncated.push_str("...(已截断)");
        truncated
    } else {
        collapsed
    }
}

/// SQLx 的 `elapsed` 字段是 Debug 输出（如 `123.456ms` / `1.234s`），用于兜底。
fn parse_elapsed_ms(text: Option<&str>) -> Option<f64> {
    let text = text?.trim();
    if let Some(value) = text.strip_suffix("ms") {
        value.trim().parse::<f64>().ok()
    } else if let Some(value) = text.strip_suffix('s') {
        value.trim().parse::<f64>().ok().map(|secs| secs * 1000.0)
    } else if let Some(value) = text.strip_suffix("µs") {
        value.trim().parse::<f64>().ok().map(|micros| micros / 1000.0)
    } else if let Some(value) = text.strip_suffix("ns") {
        value.trim().parse::<f64>().ok().map(|nanos| nanos / 1_000_000.0)
    } else {
        text.parse::<f64>().ok()
    }
}

/// Java SqlLogInterceptor 的慢 SQL WARN 原始字符串（多行框）。
fn write_slow_sql_box(
    writer: &mut Writer<'_>,
    visitor: &MessageVisitor,
    threshold_ms: u64,
) -> fmt::Result {
    let (cost, sql) = sql_event_details(visitor);
    write!(
        writer,
        "\n╔══════════════════════════════════════════════════════════\n\
         ║ 【慢SQL告警】\n\
         ║  Mapper: {}\n\
         ║  耗时: {} ms (阈值: {} ms)\n\
         ║  SQL: {}\n\
         ║  TraceId: {}\n\
         ╚══════════════════════════════════════════════════════════",
        SQL_MAPPER_PLACEHOLDER,
        cost,
        threshold_ms,
        sql,
        current_trace_id()
    )
}

fn thread_name() -> String {
    current_log_thread()
}

/// Java logback `%logger{target}` 的 TargetLengthBasedClassNameAbbreviator。
///
/// 规则（逐段照搬 logback 1.2.3）：
/// 1. 名称长度 < target 时原样返回；
/// 2. 没有包分隔符（`.` / Rust 模块用 `::`）时原样返回；
/// 3. `toTrim = 总长度 - target`，从左到右处理除最后一段外的每一段：
///    `toTrim > 0` 时只保留首字符，否则整段保留；每处理一段扣减丢弃的字符数；
/// 4. 最后一段永远整段保留（允许最终长度超过 target，logback 就是这样）。
fn abbreviate_logger(name: &str, target: usize) -> String {
    let length = name.chars().count();
    if length < target {
        return name.to_string();
    }
    let separator = if name.contains("::") { "::" } else { "." };
    if !name.contains(separator) {
        return name.to_string();
    }
    let segments: Vec<&str> = name.split(separator).collect();
    if segments.len() == 1 {
        return name.to_string();
    }

    let mut to_trim = length.saturating_sub(target);
    let mut out = String::with_capacity(length);
    for (index, segment) in segments.iter().enumerate() {
        if index > 0 {
            out.push_str(separator);
        }
        if index == segments.len() - 1 {
            out.push_str(segment);
            break;
        }
        let available = segment.chars().count();
        let keep = if to_trim > 0 {
            if available < 1 {
                available
            } else {
                1
            }
        } else {
            available
        };
        to_trim = to_trim.saturating_sub(available.saturating_sub(keep));
        if keep > 0 {
            out.extend(segment.chars().take(keep));
        }
    }
    out
}

/// Java SLF4J 的 Throwable 追加格式：
/// `{类型}: {message}`，错误链逐层 `Caused by:`，栈帧 `\tat ...`。
///
/// Rust 的 `std::error::Error` 不携带栈（除非错误类型自己保存 Backtrace），
/// 这里在记录日志时捕获当前 Backtrace，按 logback 的形态输出；
/// 未开启符号化/被 strip 时帧可能为空。
pub struct Throwable<'a> {
    error: &'a (dyn Error + 'static),
    kind: &'static str,
    backtrace: Backtrace,
}

impl<'a> Throwable<'a> {
    pub fn new<E: Error + 'static>(error: &'a E) -> Self {
        Self {
            error,
            kind: std::any::type_name::<E>(),
            // Windows 上 `Backtrace::new()` 会立即对整条栈做全量符号化，
            // 在单测/大二进制里可能挂住数十秒；这里只捕获原始帧，
            // 由 `write_backtrace` 逐帧惰性解析。
            backtrace: Backtrace::new_unresolved(),
        }
    }
}

impl fmt::Display for Throwable<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.kind.replace("::", "."), self.error)?;
        write_backtrace(f, &self.backtrace)?;

        let mut source = self.error.source();
        let mut depth = 0usize;
        while let Some(cause) = source {
            if depth >= 16 {
                write!(f, "\nCaused by: [CIRCULAR REFERENCE]")?;
                break;
            }
            write!(f, "\nCaused by: {cause}")?;
            source = cause.source();
            depth += 1;
        }
        Ok(())
    }
}

fn write_backtrace(f: &mut fmt::Formatter<'_>, backtrace: &Backtrace) -> fmt::Result {
    // logback 会裁掉 cause 链公共尾部帧；Rust 异步栈远比 Java 深，
    // 这里同样限制最多输出 32 帧，避免日志被 runtime 帧淹没。
    for frame in backtrace.frames().iter().take(32) {
        let mut captured: Option<(String, Option<String>, u32)> = None;
        // `Backtrace` 是不可变借用，用地址惰性解析单帧，避免整条栈一次性符号化。
        backtrace::resolve(frame.ip(), |symbol| {
            if captured.is_none() {
                if let Some(name) = symbol.name() {
                    captured = Some((
                        name.to_string(),
                        symbol.filename().map(|path| path.to_string_lossy().into_owned()),
                        symbol.lineno().unwrap_or(0),
                    ));
                }
            }
        });
        let Some((name, file, line)) = captured else {
            continue;
        };
        // 去掉日志设施/panic 机制自身的帧，保留调用方（接近 Java 从抛出点开始的栈）。
        if name.contains("std::backtrace")
            || name.contains("std::panicking")
            || name.contains("core::panicking")
            || name.contains("backtrace::")
            || name.contains("tracing_subscriber")
            || name.contains("tracing_core")
            || name.contains("car_monit_rust::logging")
        {
            continue;
        }
        let file = file.unwrap_or_else(|| "<unknown>".to_string());
        write!(f, "\n\tat {name} ({file}:{line})")?;
    }
    Ok(())
}

thread_local! {
    /// panic hook 在 panic 线程上捕获的栈。
    /// unwind 之后原栈已展开，只能在 hook 里取；catch 点拿到的是中间件栈。
    static LAST_PANIC: std::cell::RefCell<Option<(String, Backtrace)>> =
        const { std::cell::RefCell::new(None) };
}

/// 安装全局 panic hook：保留默认的 stderr 输出，同时记录 panic 信息与原始栈。
pub fn install_panic_hook() {
    let previous = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let message = panic_payload_text(info.payload());
        LAST_PANIC.with(|slot| {
            *slot.borrow_mut() = Some((message, Backtrace::new_unresolved()));
        });
        previous(info);
    }));
}

/// `catch_unwind` 的 payload 是 `Box<dyn Any + Send>`。
pub fn panic_payload_text(payload: &(dyn std::any::Any + Send)) -> String {
    if let Some(text) = payload.downcast_ref::<&str>() {
        (*text).to_string()
    } else if let Some(text) = payload.downcast_ref::<String>() {
        text.clone()
    } else {
        "Box<dyn Any>".to_string()
    }
}

/// 取出 panic hook 捕获的信息。同一线程上未被请求捕获的 panic 不会残留到这里。
pub fn take_panic() -> Option<(String, Option<Backtrace>)> {
    LAST_PANIC
        .with(|slot| slot.borrow_mut().take())
        .map(|(message, backtrace)| (message, Some(backtrace)))
}

/// Java Throwable 的等价物：`panic: message` + `\tat` 栈帧。
pub struct PanicThrowable<'a> {
    pub message: &'a str,
    pub backtrace: Option<&'a Backtrace>,
}

impl fmt::Display for PanicThrowable<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "panic: {}", self.message)?;
        if let Some(backtrace) = self.backtrace {
            write_backtrace(f, backtrace)?;
        }
        Ok(())
    }
}

#[derive(Default)]
struct MessageVisitor {
    message: Option<String>,
    throwable: Option<String>,
    fields: Vec<(String, String)>,
}

impl MessageVisitor {
    fn record(&mut self, field: &Field, value: String) {
        match field.name() {
            "message" => self.message = Some(value),
            // SLF4J 的 throwable 是消息之后的独立区块，不作为 `key=value` 字段。
            "error" | "exception" => self.throwable = Some(value),
            _ => self.fields.push((field.name().to_string(), value)),
        }
    }

    fn field(&self, name: &str) -> Option<&str> {
        self.fields
            .iter()
            .find(|(key, _)| key == name)
            .map(|(_, value)| value.as_str())
    }
}

impl Visit for MessageVisitor {
    fn record_debug(&mut self, field: &Field, value: &dyn fmt::Debug) {
        self.record(field, format!("{value:?}"));
    }

    fn record_str(&mut self, field: &Field, value: &str) {
        self.record(field, value.to_string());
    }

    fn record_i64(&mut self, field: &Field, value: i64) {
        self.record(field, value.to_string());
    }

    fn record_u64(&mut self, field: &Field, value: u64) {
        self.record(field, value.to_string());
    }

    fn record_bool(&mut self, field: &Field, value: bool) {
        self.record(field, value.to_string());
    }

    fn record_f64(&mut self, field: &Field, value: f64) {
        self.record(field, value.to_string());
    }
}

pub fn is_slow_target(target: &str) -> bool {
    matches!(target, TRACE_ID_TARGET | SQL_LOG_TARGET)
}

/// SQLx 的 SQL 事件与 Java SqlLogInterceptor 共用 sys-slow（additivity=false）。
pub fn is_sql_query_target(target: &str) -> bool {
    target == SQLX_QUERY_TARGET
}

/// Java logback 中这两个 logger 设为 additivity=false，只挂 file_slow：
/// 因此既不进 console，也不进 sys-info / sys-error。
pub fn is_monitor_file_target(target: &str) -> bool {
    matches!(target, TRACE_ID_TARGET | SQL_LOG_TARGET | SQLX_QUERY_TARGET)
}

pub fn is_user_target(target: &str) -> bool {
    target == USER_LOG_TARGET
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sizes_follow_logback_units() {
        assert_eq!(parse_size("100MB"), 100 * 1024 * 1024);
        assert_eq!(parse_size("512KB"), 512 * 1024);
        assert_eq!(parse_size("1GB"), 1024 * 1024 * 1024);
        assert_eq!(parse_size("1024"), 1024);
        assert_eq!(parse_size("bad"), 100 * 1024 * 1024);
    }

    #[test]
    fn writer_uses_active_file_and_indexed_archive() {
        let dir = tempfile::tempdir().expect("tempdir");
        let handle = start_appender(dir.path(), "sys-info", true, 10, 60).expect("start");
        let mut writer = handle.writer().make_writer();
        writer.write_all(b"1234567890").expect("write first");
        writer.write_all(b"abcde").expect("write second");
        drop(writer);
        drop(handle);

        let mut files: Vec<_> = std::fs::read_dir(dir.path())
            .expect("read dir")
            .flatten()
            .map(|entry| entry.file_name().to_string_lossy().to_string())
            .collect();
        files.sort();
        assert!(files.iter().any(|name| name == "sys-info.log"), "{files:?}");
        assert!(
            files
                .iter()
                .any(|name| name.ends_with(".0.log") && name.starts_with("sys-info.")),
            "{files:?}"
        );
    }

    #[test]
    fn cleanup_removes_old_daily_files() {
        let dir = tempfile::tempdir().expect("tempdir");
        let old = dir.path().join("sys-info.2020-01-01.0.log");
        std::fs::write(&old, b"old").expect("write old");
        let handle = start_appender(dir.path(), "sys-info", true, 10, 1).expect("start");
        drop(handle);
        assert!(!old.exists(), "早于 maxHistory 的文件应被删除");
    }

    /// 期望值由 logback 1.2.3 TargetLengthBasedClassNameAbbreviator 算法逐段计算。
    #[test]
    fn logger_abbreviation_matches_logback_exactly() {
        assert_eq!(
            abbreviate_logger("com.ruoyi.common.core.monitor.TraceIdFilter", 36),
            "c.r.c.core.monitor.TraceIdFilter"
        );
        assert_eq!(
            abbreviate_logger("com.ruoyi.common.core.monitor.SqlLogInterceptor", 36),
            "c.r.c.core.monitor.SqlLogInterceptor"
        );
        assert_eq!(
            abbreviate_logger("com.ruoyi.common.core.monitor.TraceIdFilter", 20),
            "c.r.c.c.m.TraceIdFilter"
        );
        // 最后一段永远整段保留，允许超过 target（logback 的真实行为）。
        assert_eq!(
            abbreviate_logger("a.b.SuperLongClassNameHere", 10),
            "a.b.SuperLongClassNameHere"
        );
        // 没有分隔符时原样返回，不做左截断。
        assert_eq!(
            abbreviate_logger("averylongnamethatisverylong", 10),
            "averylongnamethatisverylong"
        );
        // Rust 模块路径把 `::` 当作包分隔符，规则与 Java 点号一致。
        assert_eq!(
            abbreviate_logger("car_monit_rust::api::system::sys_user", 36),
            "c::api::system::sys_user"
        );
    }

    #[derive(Debug)]
    struct TestError {
        message: &'static str,
        source: Option<Box<TestError>>,
    }

    impl fmt::Display for TestError {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            write!(f, "{}", self.message)
        }
    }

    impl Error for TestError {
        fn source(&self) -> Option<&(dyn Error + 'static)> {
            self.source
                .as_deref()
                .map(|error| error as &(dyn Error + 'static))
        }
    }

    #[tokio::test]
    async fn throwable_is_appended_after_message_like_logback() {
        use tracing_subscriber::layer::SubscriberExt;

        let dir = tempfile::tempdir().expect("tempdir");
        let handle = start_appender(dir.path(), "sys-info", true, 1024, 60).expect("start");
        let layer = tracing_subscriber::fmt::layer()
            .event_format(JavaLogFormat {
                console: false,
                logger_width: 36,
                slow_sql_threshold_ms: 1000,
            })
            .with_writer(handle.writer())
            .with_ansi(false);
        let subscriber = tracing_subscriber::registry().with(layer);
        let guard = tracing::subscriber::set_default(subscriber);

        with_trace_id("trace-err".to_string(), async {
            let cause = TestError {
                message: "boom",
                source: None,
            };
            let outer = TestError {
                message: "outer",
                source: Some(Box::new(cause)),
            };
            tracing::warn!(
                target: "car_monit_rust::auth::audit",
                error = %Throwable::new(&outer),
                "记录登录日志失败"
            );
        })
        .await;

        drop(guard);
        drop(handle);
        let files: Vec<_> = std::fs::read_dir(dir.path())
            .expect("read dir")
            .flatten()
            .map(|entry| entry.path())
            .collect();
        let text = std::fs::read_to_string(&files[0]).expect("read log");
        assert!(text.contains("记录登录日志失败\n"), "{text}");
        assert!(text.contains("TestError: outer"), "{text}");
        assert!(text.contains("\nCaused by: boom"), "{text}");
        // logback 的栈帧形态是 `\tat 类名(文件:行号)`。
        assert!(text.contains("\n\tat "), "{text}");
        assert!(!text.contains(" error="), "{text}");
    }

    #[test]
    fn module_targets_map_to_java_fqcn() {
        assert_eq!(
            display_target("car_monit_rust::task::snapshot_flow_sync"),
            "com.ruoyi.quartz.task.SnapshotFlowSyncTask"
        );
        assert_eq!(
            display_target("car_monit_rust::api::base::cdc"),
            "com.ruoyi.base.service.cdc.DeadLetterQueueService"
        );
        // 没有 Java 对应类的 Rust 模块保持原 target。
        assert_eq!(
            display_target("car_monit_rust::api::support"),
            "car_monit_rust::api::support"
        );
        assert_eq!(
            display_target("car_monit_rust::task"),
            "car_monit_rust::task"
        );
    }

    #[tokio::test]
    async fn format_contains_java_pattern_elements() {
        use tracing_subscriber::layer::SubscriberExt;

        let dir = tempfile::tempdir().expect("tempdir");
        let handle = start_appender(dir.path(), "sys-info", true, 1024, 60).expect("start");
        let layer = tracing_subscriber::fmt::layer()
            .event_format(JavaLogFormat {
                console: false,
                logger_width: 36,
                slow_sql_threshold_ms: 1000,
            })
            .with_writer(handle.writer())
            .with_ansi(false);
        let subscriber = tracing_subscriber::registry().with(layer);
        let guard = tracing::subscriber::set_default(subscriber);

        with_trace_id("abc123".to_string(), async {
            tracing::info!(target: "com.ruoyi.test", "hello {}", 1);
        })
        .await;

        drop(guard);
        drop(handle);
        let files: Vec<_> = std::fs::read_dir(dir.path())
            .expect("read dir")
            .flatten()
            .map(|entry| entry.path())
            .collect();
        let text = std::fs::read_to_string(&files[0]).expect("read log");
        assert!(text.contains("INFO "), "{text}");
        assert!(text.contains("[abc123]"), "{text}");
        assert!(text.contains("com.ruoyi.test:"), "{text}");
        assert!(text.contains("hello 1"), "{text}");
    }

    #[tokio::test]
    async fn slow_sql_uses_java_interceptor_box() {
        use tracing_subscriber::layer::SubscriberExt;

        let dir = tempfile::tempdir().expect("tempdir");
        let handle = start_appender(dir.path(), "sys-slow", false, u64::MAX, 60).expect("start");
        let layer = tracing_subscriber::fmt::layer()
            .event_format(JavaLogFormat {
                console: false,
                logger_width: 36,
                slow_sql_threshold_ms: 1000,
            })
            .with_writer(handle.writer())
            .with_ansi(false);
        let subscriber = tracing_subscriber::registry().with(layer);
        let guard = tracing::subscriber::set_default(subscriber);

        with_trace_id("abc123".to_string(), async {
            tracing::event!(
                target: SQLX_QUERY_TARGET,
                tracing::Level::WARN,
                summary = "SELECT * FROM sys_user",
                db.statement = "SELECT *\n  FROM sys_user\n  WHERE user_id = ?",
                elapsed_secs = 1.234f64,
                "slow statement: execution time exceeded alert threshold"
            );
        })
        .await;

        drop(guard);
        drop(handle);
        let files: Vec<_> = std::fs::read_dir(dir.path())
            .expect("read dir")
            .flatten()
            .map(|entry| entry.path())
            .collect();
        let text = std::fs::read_to_string(&files[0]).expect("read log");
        assert!(text.contains("SqlLogInterceptor:139"), "{text}");
        assert!(text.contains("【慢SQL告警】"), "{text}");
        assert!(text.contains("Mapper: sqlx::query"), "{text}");
        assert!(text.contains("耗时: 1234 ms (阈值: 1000 ms)"), "{text}");
        assert!(
            text.contains("SQL: SELECT * FROM sys_user WHERE user_id = ?"),
            "{text}"
        );
        assert!(text.contains("TraceId: abc123"), "{text}");
        assert!(!text.contains("elapsed_secs="), "{text}");
        assert!(!text.contains("slow_threshold="), "{text}");
    }

    #[tokio::test]
    async fn request_thread_names_follow_tomcat_shape() {
        let (first_trace, first_thread) = with_request_context("t1".to_string(), 9989, async {
            (current_trace_id(), current_log_thread())
        })
        .await;
        let second_thread =
            with_request_context("t2".to_string(), 9989, async { current_log_thread() }).await;

        assert_eq!(first_trace, "t1");
        assert!(
            first_thread.starts_with("http-nio-9989-exec-"),
            "{first_thread}"
        );
        assert!(
            second_thread.starts_with("http-nio-9989-exec-"),
            "{second_thread}"
        );
        assert_ne!(first_thread, second_thread);
        let first_number = first_thread
            .rsplit('-')
            .next()
            .and_then(|value| value.parse::<u64>().ok())
            .expect("请求序号");
        let second_number = second_thread
            .rsplit('-')
            .next()
            .and_then(|value| value.parse::<u64>().ok())
            .expect("请求序号");
        assert!(second_number > first_number);
    }

    #[tokio::test(flavor = "multi_thread", worker_threads = 1)]
    async fn tokio_worker_name_is_not_exposed() {
        let thread = tokio::spawn(async { current_log_thread() })
            .await
            .expect("join");
        assert_eq!(thread, "scheduling-1");

        let named = with_log_thread("quartzScheduler_Worker-1", async { current_log_thread() }).await;
        assert_eq!(named, "quartzScheduler_Worker-1");
    }

    #[test]
    fn sql_normalization_collapses_whitespace_and_truncates() {
        assert_eq!(normalize_sql("SELECT *\n\tFROM  t"), "SELECT * FROM t");
        let long = "x".repeat(2100);
        let normalized = normalize_sql(&long);
        assert_eq!(normalized.chars().count(), 2000 + "...(已截断)".chars().count());
        assert!(normalized.ends_with("...(已截断)"));
    }
}
