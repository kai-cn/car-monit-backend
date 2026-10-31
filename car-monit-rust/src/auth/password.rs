// 来源: ruoyi-common/src/main/java/com/ruoyi/common/utils/SecurityUtils.java
//       org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
// 职责: 密码哈希校验。Java 配置的 BCryptPasswordEncoder 使用默认强度 10。

use crate::error::AppError;

/// Java: SecurityUtils.matchesPassword(rawPassword, encodedPassword)
/// BCrypt 校验失败（哈希损坏）在 Java 中返回 false，不抛异常。
pub fn matches(raw: &str, encoded: &str) -> bool {
    bcrypt::verify(raw, encoded).unwrap_or(false)
}

/// Java: BCryptPasswordEncoder.encode(rawPassword)
pub fn encode(raw: &str) -> Result<String, AppError> {
    bcrypt::hash(raw, bcrypt::DEFAULT_COST)
        .map_err(|e| AppError::internal(format!("密码加密失败: {e}")))
}
