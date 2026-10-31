// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/model/LoginBody.java
// 职责: POST /login 请求体。Java 中 uuid 默认空串，其余为 null。

use serde::Deserialize;

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct LoginBody {
    pub username: Option<String>,
    pub password: Option<String>,
    pub code: Option<String>,
    pub uuid: String,
}

impl LoginBody {
    /// Java: 方法参数上的 username/password 直接传给 loginService。
    pub fn username(&self) -> String {
        self.username.clone().unwrap_or_default()
    }

    pub fn password(&self) -> String {
        self.password.clone().unwrap_or_default()
    }

    pub fn code(&self) -> String {
        self.code.clone().unwrap_or_default()
    }
}
