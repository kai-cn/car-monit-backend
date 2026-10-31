// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/JobInvokeUtil.java
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/ScheduleUtils.java
// 职责: `invoke_target` 字符串 -> Rust 任务的注册表（替代 Java 反射）。
// 对应关系: JobInvokeUtil.invokeMethod(bean.method(params)) -> invoke()。

use crate::state::AppState;

/// 委托给服务层调度器（实现见 `service::quartz_runtime`）。
pub async fn invoke(state: &AppState, invoke_target: &str) -> Result<(), String> {
    crate::service::quartz_runtime::dispatch_job(state, invoke_target).await
}
