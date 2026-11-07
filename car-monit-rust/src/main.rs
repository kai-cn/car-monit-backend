// 来源: ruoyi-admin/src/main/java/com/ruoyi/RuoYiApplication.java
//       ruoyi-admin/src/main/resources/logback.xml（日志落地）
// 职责: 进程入口 —— 配置加载、DB/Redis 连接、日志初始化、优雅停机。
// 对应关系: SpringApplication.run -> tokio main；logback -> tracing-subscriber。

use std::net::SocketAddr;

use car_monit_rust::config::Settings;
use car_monit_rust::state::AppState;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let settings = Settings::load()?;
    let _log_guard = init_tracing(&settings);

    if settings.app.banner_enabled {
        tracing::info!(
            "{} {} (Rust) starting on port {}",
            settings.ruoyi.name,
            settings.ruoyi.version,
            settings.server.port
        );
    }

    let state = AppState::connect(settings.clone()).await?;
    // Java 4 个任务类里的 6 个 @Scheduled（用户决策：Rust 侧必须真正生效）。
    car_monit_rust::task::start_scheduler(&state);
    // Java: SysJobServiceImpl.init —— 把 sys_job 中 status=0 的任务装入调度器。
    car_monit_rust::service::quartz_runtime::start_jobs(&state);
    let app = car_monit_rust::build_router(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], settings.server.port));
    let listener = tokio::net::TcpListener::bind(addr).await?;
    tracing::info!("listening on {}", addr);

    axum::serve(
        listener,
        app.into_make_service_with_connect_info::<SocketAddr>(),
    )
    .with_graceful_shutdown(shutdown_signal())
    .await?;
    Ok(())
}

/// 日志同时写 stdout 与按天/按大小滚动的文件；与 Java logback 的双通道一致。
/// 返回的 handle 必须存活到进程结束，否则后台写线程会被提前关闭。
fn init_tracing(settings: &Settings) -> Option<car_monit_rust::logging::LogHandle> {
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("info,car_monit_rust=debug"));

    let stdout_layer = tracing_subscriber::fmt::layer();

    match std::fs::create_dir_all(&settings.log.dir) {
        Ok(()) => {
            let handle = match car_monit_rust::logging::start(
                &settings.log.dir,
                "car-monit.log",
                car_monit_rust::logging::parse_size(&settings.log.max_file_size),
                settings.log.max_history,
            ) {
                Ok(handle) => handle,
                Err(err) => {
                    eprintln!("日志文件 writer 初始化失败，仅输出到 stdout: {err}");
                    let _ = tracing_subscriber::registry()
                        .with(filter)
                        .with(stdout_layer)
                        .try_init();
                    return None;
                }
            };
            let file_layer = tracing_subscriber::fmt::layer()
                .with_writer(handle.writer())
                .with_ansi(false);
            let _ = tracing_subscriber::registry()
                .with(filter)
                .with(stdout_layer)
                .with(file_layer)
                .try_init();
            Some(handle)
        }
        Err(err) => {
            eprintln!(
                "日志目录 {} 不可用，仅输出到 stdout: {err}",
                settings.log.dir
            );
            let _ = tracing_subscriber::registry()
                .with(filter)
                .with(stdout_layer)
                .try_init();
            None
        }
    }
}

async fn shutdown_signal() {
    // Java: Spring Boot 优雅停机同时响应 SIGTERM（容器/K8s 滚动发布）。
    #[cfg(unix)]
    {
        use tokio::signal::unix::{signal, SignalKind};
        if let Ok(mut terminate) = signal(SignalKind::terminate()) {
            tokio::select! {
                _ = tokio::signal::ctrl_c() => {}
                _ = terminate.recv() => {}
            }
            tracing::info!("shutdown signal received");
            return;
        }
    }
    let _ = tokio::signal::ctrl_c().await;
    tracing::info!("shutdown signal received");
}
