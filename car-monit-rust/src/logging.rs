// 来源: ruoyi-admin/src/main/resources/logback.xml
// 职责: 复刻 logback 的四个文件 appender + 日志格式 + 本地时区按天/按大小滚动。
// 对应关系:
//   sys-info/sys-error/sys-slow/sys-user appender -> start_appender("sys-*")
//   log.pattern -> JavaLogFormat
//   SizeAndTimeBasedFNATP -> RollingWriter(max_bytes)
//   maxHistory -> cleanup()

use std::fmt;
use std::fs::{File, OpenOptions};
use std::future::Future;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
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
}

/// 让日志格式能读到当前请求的 traceId（Java 用 MDC）。
pub async fn with_trace_id<F>(trace_id: String, future: F) -> F::Output
where
    F: Future,
{
    TRACE_ID.scope(trace_id, future).await
}

pub fn current_trace_id() -> String {
    TRACE_ID.try_with(|value| value.clone()).unwrap_or_default()
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
        writeln!(writer)
    }
}

/// Rust 模块 target -> Java 全类名。没有 Java 对应类的模块保持原 target。
fn display_target(target: &str) -> &str {
    match target {
        SQLX_QUERY_TARGET => SQL_LOG_TARGET,
        other => other,
    }
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
    std::thread::current()
        .name()
        .unwrap_or_default()
        .to_string()
}

/// Java `%logger{36}`：超长时把左侧包名缩成首字母，保留最后一段。
fn abbreviate_logger(name: &str, width: usize) -> String {
    if name.chars().count() <= width {
        return name.to_string();
    }
    let separator = if name.contains("::") { "::" } else { "." };
    let parts: Vec<&str> = name.split(separator).collect();
    let Some(last) = parts.last() else {
        return name.to_string();
    };
    let mut out = last.to_string();
    for part in parts[..parts.len().saturating_sub(1)].iter().rev() {
        let first = part.chars().next().unwrap_or('?');
        out = format!("{first}{separator}{out}");
        if out.chars().count() > width {
            break;
        }
    }
    if out.chars().count() > width {
        out = out.chars().skip(out.chars().count() - width).collect();
    }
    out
}

#[derive(Default)]
struct MessageVisitor {
    message: Option<String>,
    fields: Vec<(String, String)>,
}

impl MessageVisitor {
    fn record(&mut self, field: &Field, value: String) {
        if field.name() == "message" {
            self.message = Some(value);
        } else {
            self.fields.push((field.name().to_string(), value));
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

    #[test]
    fn logger_abbreviation_keeps_last_segment() {
        let name = abbreviate_logger("com.ruoyi.common.core.monitor.TraceIdFilter", 36);
        assert!(name.ends_with("TraceIdFilter"), "{name}");
        assert!(name.chars().count() <= 36, "{name}");
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

    #[test]
    fn sql_normalization_collapses_whitespace_and_truncates() {
        assert_eq!(normalize_sql("SELECT *\n\tFROM  t"), "SELECT * FROM t");
        let long = "x".repeat(2100);
        let normalized = normalize_sql(&long);
        assert_eq!(normalized.chars().count(), 2000 + "...(已截断)".chars().count());
        assert!(normalized.ends_with("...(已截断)"));
    }
}
