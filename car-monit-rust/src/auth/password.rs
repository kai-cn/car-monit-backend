// 来源: ruoyi-common/src/main/java/com/ruoyi/common/utils/SecurityUtils.java
//       org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
// 职责: 密码哈希校验。Java 配置的 BCryptPasswordEncoder 使用默认强度 10。

use crate::error::AppError;

/// Java: `new BCryptPasswordEncoder()` 的默认 strength（不是 bcrypt crate 的 12）。
const BCRYPT_COST: u32 = 10;

/// Java: SecurityUtils.matchesPassword(rawPassword, encodedPassword)
/// BCrypt 校验失败（哈希损坏）在 Java 中返回 false，不抛异常。
pub async fn matches(raw: &str, encoded: &str) -> bool {
    let raw = raw.to_string();
    let encoded = encoded.to_string();
    tokio::task::spawn_blocking(move || bcrypt::verify(&raw, &encoded).unwrap_or(false))
        .await
        .unwrap_or(false)
}

/// Java: BCryptPasswordEncoder.encode(rawPassword)
pub async fn encode(raw: &str) -> Result<String, AppError> {
    let raw = raw.to_string();
    tokio::task::spawn_blocking(move || bcrypt::hash(&raw, BCRYPT_COST))
        .await
        .map_err(|err| AppError::internal(format!("密码加密任务失败: {err}")))?
        .map_err(|e| AppError::internal(format!("密码加密失败: {e}")))
}
