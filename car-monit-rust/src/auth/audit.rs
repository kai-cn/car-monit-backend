// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/manager/factory/AsyncFactory.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/LogAspect.java
//       ruoyi-system/src/main/resources/mapper/system/SysLogininforMapper.xml#insertLogininfor
//       ruoyi-system/src/main/resources/mapper/monitor/SysOperLogMapper.xml#insertOperlog
// 职责: 异步写登录审计与操作日志（Java 使用 AsyncManager 线程池，延迟 10ms）。
// 对应关系: AsyncManager.me().execute(AsyncFactory.recordLogininfor/recordOper) -> record_*。

use std::time::Duration;

use sqlx::MySqlPool;

use crate::common::utils::ClientMeta;

/// Java: AsyncFactory.recordLogininfor
/// 审计写入失败只记录日志，不影响登录主流程。
pub fn record_logininfor(
    pool: &MySqlPool,
    username: &str,
    status: &str,
    message: &str,
    meta: &ClientMeta,
) {
    let pool = pool.clone();
    let username = username.to_string();
    let log_username = username.clone();
    let log_status = status.to_string();
    let log_message = message.to_string();
    // Java: AsyncFactory.recordLogininfor 先写 sys-user 日志，再落库。
    // Java: AsyncFactory 把登录结果映射为 sys_logininfor.status（0 成功 / 1 失败）。
    let status = match status {
        "Success" | "Logout" | "Register" => "0",
        "Error" => "1",
        other => other,
    }
    .to_string();
    let message = message.to_string();
    let ip = meta.ip.clone();
    let location = meta.login_location.clone();
    let browser = meta.browser.clone();
    let os = meta.os.clone();

    tokio::spawn(async move {
        // Java: `sys_user_logger.info("[" + ip + "][" + address + "][" + username + "][" + status + "][" + message + "]")`
        tracing::info!(
            target: "sys-user",
            "[{}][{}][{}][{}][{}]",
            ip,
            location,
            log_username,
            log_status,
            log_message
        );
        let result = sqlx::query(
            r#"
            insert into sys_logininfor
                (user_name, status, ipaddr, login_location, browser, os, msg, login_time)
            values (?, ?, ?, ?, ?, ?, ?, sysdate())
            "#,
        )
        .bind(&username)
        .bind(&status)
        .bind(&ip)
        .bind(&location)
        .bind(&browser)
        .bind(&os)
        .bind(&message)
        .execute(&pool)
        .await;

        if let Err(err) = result {
            tracing::warn!(
                error = %crate::logging::Throwable::new(&err),
                "记录登录日志失败"
            );
        }
    });
}

/// Java: SysOperLog 中由 LogAspect 填充的字段。
#[derive(Debug, Clone)]
pub struct OperRecord {
    pub title: &'static str,
    pub business_type: i32,
    pub method: &'static str,
    pub request_method: String,
    pub oper_name: String,
    pub dept_name: String,
    pub oper_url: String,
    pub oper_ip: String,
    pub oper_param: Option<String>,
    pub json_result: Option<String>,
    pub status: i32,
    /// Java: SysOperLog 无 costTime 字段、`sys_oper_log` 表也没有 cost_time 列，
    /// 本库的 insertOperlog 只写到 oper_time 为止。
    pub error_msg: Option<String>,
}

/// Java: AsyncFactory.recordOper —— AsyncManager 固定延迟 10ms 后落库。
pub fn record_oper(pool: &MySqlPool, record: OperRecord) {
    let pool = pool.clone();
    tokio::spawn(async move {
        tokio::time::sleep(Duration::from_millis(10)).await;
        let result = sqlx::query(
            r#"
            insert into sys_oper_log
                (title, business_type, method, request_method, operator_type, oper_name,
                 dept_name, oper_url, oper_ip, oper_location, oper_param, json_result,
                 status, error_msg, oper_time)
            values (?, ?, ?, ?, 1, ?, ?, ?, ?, '', ?, ?, ?, ?, sysdate())
            "#,
        )
        .bind(record.title)
        .bind(record.business_type)
        .bind(record.method)
        .bind(&record.request_method)
        .bind(&record.oper_name)
        .bind(&record.dept_name)
        .bind(&record.oper_url)
        .bind(&record.oper_ip)
        .bind(&record.oper_param)
        .bind(&record.json_result)
        .bind(record.status)
        .bind(&record.error_msg)
        .execute(&pool)
        .await;

        if let Err(err) = result {
            tracing::warn!(
                error = %crate::logging::Throwable::new(&err),
                "记录操作日志失败"
            );
        }
    });
}
