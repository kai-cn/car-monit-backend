// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java
//       ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysPermissionService.java
// 职责: 复刻 Spring Security 的路由放行顺序与权限判断。
// 对应关系: authorizeRequests().antMatchers(...) -> access()；
//           @PreAuthorize("@ss.hasPermi") -> require_permission。

use axum::http::Method;

use crate::domain::LoginUser;
use crate::error::AppError;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Access {
    /// 任意请求均可访问
    PermitAll,
    /// 仅未认证可访问（Spring anonymous()）
    Anonymous,
    /// 必须已认证
    Authenticated,
    /// 拒绝访问（Spring denyAll()）
    DenyAll,
}

/// 按 SecurityConfig 的声明顺序判断。
pub fn access(method: &Method, path: &str) -> Access {
    // .antMatchers("/login", "/captchaImage").permitAll()
    if path == "/login" || path == "/captchaImage" {
        return Access::PermitAll;
    }

    // GET 静态资源，可匿名访问
    if method == Method::GET
        && (path == "/"
            || ends_with_any(path, &[".html", ".css", ".js"])
            || path == "/profile"
            || path.starts_with("/profile/"))
    {
        return Access::PermitAll;
    }

    // swagger/druid 一律拒绝
    if path == "/swagger-ui.html"
        || path.starts_with("/swagger-resources/")
        || path == "/swagger-resources"
        || path.starts_with("/webjars/")
        || path.starts_with("/druid/")
        || path == "/druid"
        || is_api_docs(path)
    {
        return Access::DenyAll;
    }

    // .antMatchers("/common/download**").anonymous()
    if path.starts_with("/common/download") {
        return Access::Anonymous;
    }
    // .antMatchers("/system/file/view/**").anonymous()
    if path.starts_with("/system/file/view/") {
        return Access::Anonymous;
    }
    // .antMatchers("/system/notice/view/**").anonymous()
    if path.starts_with("/system/notice/view/") {
        return Access::Anonymous;
    }
    // .antMatchers("/manager/suspicious/syncSuspiciousCarTask").permitAll()
    if path == "/manager/suspicious/syncSuspiciousCarTask" {
        return Access::PermitAll;
    }

    Access::Authenticated
}

fn ends_with_any(path: &str, suffixes: &[&str]) -> bool {
    suffixes.iter().any(|suffix| path.ends_with(suffix))
}

/// Spring: `/*/api-docs` —— 恰好两段且第二段为 api-docs。
fn is_api_docs(path: &str) -> bool {
    let mut segments = path.trim_matches('/').split('/');
    matches!(
        (segments.next(), segments.next(), segments.next()),
        (Some(first), Some("api-docs"), None) if !first.is_empty()
    )
}

/// Java: `@PreAuthorize("@ss.hasPermi('system:user:list')")`
pub fn require_permission(user: &LoginUser, permission: &str) -> Result<(), AppError> {
    if user.has_permission(permission) {
        Ok(())
    } else {
        Err(AppError::forbidden())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn security_order_matches_java() {
        assert_eq!(access(&Method::POST, "/login"), Access::PermitAll);
        assert_eq!(access(&Method::GET, "/captchaImage"), Access::PermitAll);
        assert_eq!(access(&Method::GET, "/index.html"), Access::PermitAll);
        assert_eq!(access(&Method::GET, "/a/b/app.js"), Access::PermitAll);
        assert_eq!(access(&Method::POST, "/index.html"), Access::Authenticated);
        // SecurityConfig 中 GET *.html 的 permitAll 先于 swagger denyAll。
        assert_eq!(access(&Method::GET, "/swagger-ui.html"), Access::PermitAll);
        assert_eq!(access(&Method::POST, "/swagger-ui.html"), Access::DenyAll);
        assert_eq!(
            access(&Method::GET, "/swagger-resources/x.js"),
            Access::PermitAll
        );
        assert_eq!(access(&Method::GET, "/v2/api-docs"), Access::DenyAll);
        assert_eq!(
            access(&Method::GET, "/common/download/1"),
            Access::Anonymous
        );
        assert_eq!(
            access(&Method::GET, "/system/user/list"),
            Access::Authenticated
        );
    }
}
