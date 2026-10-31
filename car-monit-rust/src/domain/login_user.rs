// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/model/LoginUser.java
// 职责: 登录态对象（Redis login_tokens:* 的 value）与权限判断。
// 对应关系: LoginUser -> LoginUser；FastJson2 WriteClassName -> @type 字段。

use serde::{Deserialize, Serialize};

use crate::common::constants::ALL_PERMISSION;
use crate::domain::sys_user::SysUser;

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct LoginUser {
    /// FastJson2 WriteClassName 根类型标记；Java 反序列化依赖它。
    #[serde(rename = "@type", skip_serializing_if = "Option::is_none")]
    pub type_name: Option<String>,

    pub token: String,
    pub session_id: Option<String>,
    pub login_time: i64,
    pub expire_time: i64,
    pub ipaddr: Option<String>,
    pub login_location: Option<String>,
    pub browser: Option<String>,
    pub os: Option<String>,
    pub permissions: Vec<String>,
    pub user: SysUser,

    /// Java LoginUser.getUsername() 没有 @JsonIgnore，FastJson2 会写出该字段。
    /// Rust 侧重写入以保持 Redis JSON 形状一致；读取时可为空。
    #[serde(skip_serializing_if = "Option::is_none")]
    pub username: Option<String>,
    /// Java getAuthorities() 返回 null，FastJson2 输出 "authorities":null。
    #[serde(skip_serializing_if = "Option::is_none")]
    pub authorities: Option<serde_json::Value>,
}

impl LoginUser {
    /// Java: new LoginUser(SysUser user, Set<String> permissions)
    pub fn new(user: SysUser, permissions: Vec<String>) -> Self {
        let username = user.user_name.clone();
        Self {
            type_name: None,
            token: String::new(),
            session_id: None,
            login_time: 0,
            expire_time: 0,
            ipaddr: None,
            login_location: None,
            browser: None,
            os: None,
            permissions,
            user,
            username,
            authorities: None,
        }
    }

    /// 写入 Redis 前补齐 @type 与 username。
    pub fn for_redis(mut self) -> Self {
        self.type_name = Some("com.ruoyi.common.core.domain.model.LoginUser".to_string());
        if self.username.is_none() {
            self.username = self.user.user_name.clone();
        }
        self.user = self.user.for_redis();
        self
    }

    /// Java: SysUser.isAdmin()
    pub fn is_admin(&self) -> bool {
        self.user.is_admin()
    }

    /// Java: SecurityUtils.hasPermi(permission)
    pub fn has_permission(&self, permission: &str) -> bool {
        self.permissions
            .iter()
            .any(|p| p == ALL_PERMISSION || p == permission)
    }

    /// 供 UserAgent/Audit 使用：Java LoginUser.getUsername()
    pub fn username(&self) -> String {
        self.user.username()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn redis_json_carries_fastjson2_type_markers() {
        let mut user = SysUser::default();
        user.user_id = Some(1);
        user.user_name = Some("admin".into());
        user.password = Some("$2a$10$hash".into());

        let value = serde_json::to_value(LoginUser::new(user, vec!["*:*:*".into()]).for_redis())
            .expect("serialize");

        assert_eq!(
            value["@type"],
            "com.ruoyi.common.core.domain.model.LoginUser"
        );
        assert_eq!(value["username"], "admin");
        assert_eq!(
            value["user"]["@type"],
            "com.ruoyi.common.core.domain.entity.SysUser"
        );
        // FastJson2 不识别 Jackson @JsonIgnore，Redis 中保留密码。
        assert_eq!(value["user"]["password"], "$2a$10$hash");
        assert_eq!(value["permissions"][0], "*:*:*");
    }

    #[test]
    fn java_style_unknown_fields_are_ignored() {
        // Java 版本会额外写入 authorities/roles 等字段，Rust 读取时不能失败。
        let json = r#"{
            "@type":"com.ruoyi.common.core.domain.model.LoginUser",
            "token":"t","loginTime":1,"expireTime":2,"permissions":["a"],
            "authorities":null,"username":"admin",
            "user":{"@type":"com.ruoyi.common.core.domain.entity.SysUser",
                    "userId":1,"userName":"admin","unexpected":"ignored"}
        }"#;
        let login_user: LoginUser = serde_json::from_str(json).expect("deserialize");
        assert_eq!(login_user.token, "t");
        assert_eq!(login_user.user.user_id, Some(1));
        assert!(login_user.permissions.contains(&"a".to_string()));
    }
}
