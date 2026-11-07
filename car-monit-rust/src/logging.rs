// 来源: ruoyi-admin/src/main/resources/logback.xml（按天 + 单文件 100MB + maxHistory）
// 职责: tracing-subscriber 的文件 writer：按 UTC 日期滚动、单文件按大小切分、按天保留。
// 为什么不用 flexi_logger：flexi_logger 接的是 `log` 门面，tracing 事件要经 `tracing-log`
// 桥接后才进得去，会丢掉 span/结构化字段，且与当前 fmt layer 的格式/EnvFilter 产生两套输出。
// 这里实现一个 `MakeWriter` 直接挂到 `tracing_subscriber::fmt::layer`，格式、路径、按天行为不变。

use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::sync::mpsc::{sync_channel, Receiver, SyncSender, TrySendError};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;

use chrono::{Days, NaiveDate, Utc};
use tracing_subscriber::fmt::MakeWriter;

const CHANNEL_CAPACITY: usize = 1024;
const DATE_LEN: usize = 10;

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
            // 阻塞发送，保证后台线程收到 Shutdown 后再 join。
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
        // 与 tracing-appender 的 non_blocking 一致：缓冲满/线程退出时丢弃，不让日志拖垮业务。
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

/// 启动文件日志后台线程；`dir` 仍来自 `log.dir`，prefix 仍为 `car-monit.log`。
pub fn start(
    dir: impl AsRef<Path>,
    prefix: &str,
    max_bytes: u64,
    max_history: u32,
) -> io::Result<LogHandle> {
    let dir = dir.as_ref().to_path_buf();
    std::fs::create_dir_all(&dir)?;
    let (tx, rx) = sync_channel(CHANNEL_CAPACITY);
    let writer = RollingWriter {
        dir,
        prefix: prefix.to_string(),
        max_bytes: max_bytes.max(1),
        max_history: max_history.max(1),
        date: String::new(),
        index: 0,
        file: None,
        size: 0,
    };
    let join = std::thread::Builder::new()
        .name("car-monit-log".to_string())
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
    prefix: String,
    max_bytes: u64,
    max_history: u32,
    date: String,
    index: u32,
    file: Option<File>,
    size: u64,
}

impl RollingWriter {
    fn run(mut self, rx: Receiver<Command>) {
        self.cleanup();
        while let Ok(command) = rx.recv() {
            match command {
                Command::Write(bytes) => {
                    if let Err(err) = self.write_bytes(&bytes) {
                        eprintln!("写日志文件失败: {err}");
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
        let today = Utc::now().format("%Y-%m-%d").to_string();
        if self.date != today {
            self.file = None;
            self.date = today;
            self.index = 0;
            self.size = 0;
            self.cleanup();
        }
        if self.file.is_none() {
            self.open_segment()?;
        }
        if self.size > 0 && self.size.saturating_add(bytes.len() as u64) > self.max_bytes {
            self.index = self.index.saturating_add(1);
            self.open_segment()?;
        }
        let file = self.file.as_mut().expect("日志文件已打开");
        file.write_all(bytes)?;
        self.size = self.size.saturating_add(bytes.len() as u64);
        Ok(())
    }

    fn open_segment(&mut self) -> io::Result<()> {
        loop {
            let path = self.segment_path();
            let size = std::fs::metadata(&path).map(|meta| meta.len()).unwrap_or(0);
            if size >= self.max_bytes {
                self.index = self.index.saturating_add(1);
                continue;
            }
            let file = OpenOptions::new().create(true).append(true).open(&path)?;
            self.file = Some(file);
            self.size = size;
            return Ok(());
        }
    }

    fn segment_path(&self) -> PathBuf {
        let name = if self.index == 0 {
            format!("{}.{}", self.prefix, self.date)
        } else {
            format!("{}.{}.{}", self.prefix, self.date, self.index)
        };
        self.dir.join(name)
    }

    fn flush(&mut self) -> io::Result<()> {
        if let Some(file) = self.file.as_mut() {
            file.flush()?;
        }
        Ok(())
    }

    /// Java logback `maxHistory`：删除早于 `today - max_history` 天的文件（含旧命名）。
    fn cleanup(&self) {
        let today = Utc::now().date_naive();
        let Some(cutoff) = today.checked_sub_days(Days::new(self.max_history as u64)) else {
            return;
        };
        let prefix = format!("{}.", self.prefix);
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
    fn writer_rotates_by_size_and_keeps_daily_name() {
        let dir = tempfile::tempdir().expect("tempdir");
        let handle = start(dir.path(), "car-monit.log", 10, 60).expect("start");
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
        assert_eq!(files.len(), 2, "{files:?}");
        assert!(
            files[0].starts_with("car-monit.log."),
            "第一天文件沿用原命名: {files:?}"
        );
        assert!(files[1].ends_with(".1"), "超过 10 字节后切到 .1: {files:?}");
    }

    #[test]
    fn cleanup_removes_old_daily_files() {
        let dir = tempfile::tempdir().expect("tempdir");
        let old = dir.path().join("car-monit.log.2020-01-01");
        std::fs::write(&old, b"old").expect("write old");
        let handle = start(dir.path(), "car-monit.log", 10, 1).expect("start");
        drop(handle);
        assert!(!old.exists(), "早于 maxHistory 的文件应被删除");
    }
}
