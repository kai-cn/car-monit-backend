// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/ServerController.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/Server.java
// 职责: 服务器监控（cpu/mem/jvm/sys/sysFiles）。
// 对应关系: OSHI -> sysinfo；磁盘容量与 Java convertFileSize 文案保持一致。

use axum::extract::State;
use axum::Router;
use serde_json::{json, Value};

use crate::api::meta;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    Router::new().route(
        "/monitor/server",
        meta::get_route("/monitor/server", Some("monitor:server:list"), None, get_info),
    )
}

async fn get_info(State(_state): State<AppState>) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(server_info()))
}

#[cfg(feature = "sysinfo")]
fn server_info() -> Value {
    use sysinfo::{Disks, System};

    let mut system = System::new_all();
    system.refresh_all();
    let cpu_num = system.cpus().len() as i64;
    let used_cpu = system.global_cpu_usage() as f64;
    let total_memory = system.total_memory() as f64;
    let used_memory = system.used_memory() as f64;
    let free_memory = (total_memory - used_memory).max(0.0);

    let mut disks = Disks::new_with_refreshed_list();
    disks.refresh(true);
    let sys_files = disks
        .list()
        .iter()
        .map(|disk| {
            let total = disk.total_space() as i64;
            let free = disk.available_space() as i64;
            let used = total - free;
            let usage = if total > 0 {
                (used as f64 / total as f64 * 10000.0).round() / 100.0
            } else {
                0.0
            };
            json!({
                "dirName": disk.mount_point().to_string_lossy(),
                "sysTypeName": disk.file_system().to_string_lossy(),
                "typeName": disk.name().to_string_lossy(),
                "total": convert_file_size(total),
                "free": convert_file_size(free),
                "used": convert_file_size(used),
                "usage": usage,
            })
        })
        .collect::<Vec<_>>();

    json!({
        "cpu": {
            "cpuNum": cpu_num,
            "total": 100.0,
            "sys": 0.0,
            "used": used_cpu,
            "wait": 0.0,
            "free": (100.0 - used_cpu).max(0.0),
        },
        "mem": {
            "total": total_memory,
            "used": used_memory,
            "free": free_memory,
        },
        "jvm": {
            "total": used_memory,
            "max": total_memory,
            "free": free_memory,
            "version": env!("CARGO_PKG_VERSION"),
            "home": "rust",
        },
        "sys": {
            "computerName": System::host_name().unwrap_or_default(),
            "computerIp": local_ip(),
            "userDir": std::env::current_dir().map(|path| path.display().to_string()).unwrap_or_default(),
            "osName": System::name().unwrap_or_default(),
            "osArch": std::env::consts::ARCH,
        },
        "sysFiles": sys_files,
    })
}

#[cfg(not(feature = "sysinfo"))]
fn server_info() -> Value {
    json!({
        "cpu": { "cpuNum": 0, "total": 0.0, "sys": 0.0, "used": 0.0, "wait": 0.0, "free": 0.0 },
        "mem": { "total": 0.0, "used": 0.0, "free": 0.0 },
        "jvm": { "total": 0.0, "max": 0.0, "free": 0.0, "version": env!("CARGO_PKG_VERSION"), "home": "rust" },
        "sys": { "computerName": "", "computerIp": "", "userDir": "", "osName": "", "osArch": "" },
        "sysFiles": [],
    })
}

#[cfg(feature = "sysinfo")]
fn local_ip() -> String {
    use std::net::UdpSocket;
    // 仅用于选出默认出口网卡，不实际发包。
    UdpSocket::bind("0.0.0.0:0")
        .and_then(|socket| {
            socket.connect("8.8.8.8:80")?;
            socket.local_addr()
        })
        .map(|addr| addr.ip().to_string())
        .unwrap_or_default()
}

#[cfg(not(feature = "sysinfo"))]
fn local_ip() -> String {
    String::new()
}

/// Java: Server.convertFileSize。
fn convert_file_size(size: i64) -> String {
    const KB: i64 = 1024;
    const MB: i64 = KB * 1024;
    const GB: i64 = MB * 1024;
    if size >= GB {
        format!("{:.1} GB", size as f64 / GB as f64)
    } else if size >= MB {
        let value = size as f64 / MB as f64;
        if value > 100.0 {
            format!("{value:.0} MB")
        } else {
            format!("{value:.1} MB")
        }
    } else if size >= KB {
        let value = size as f64 / KB as f64;
        if value > 100.0 {
            format!("{value:.0} KB")
        } else {
            format!("{value:.1} KB")
        }
    } else {
        format!("{size} B")
    }
}
