// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysUser.java
//       ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDept.java
//       ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysRole.java
// 职责: 登录用户与系统用户/部门/角色的 serde + SQLx 映射。
// 对应关系: SysUser/SysDept/SysRole -> 同名 struct；BaseEntity 字段内联（flatten 到 JSON）。

use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

use crate::common::serde_helpers::{
    deserialize_datetime, deserialize_millis, is_none_or_empty_map, serialize_datetime,
    serialize_millis,
};
use crate::domain::sys_dept::SysDept;
use crate::domain::sys_role::SysRole;

/// Java: `SysUser extends BaseEntity`。Rust 无继承，BaseEntity 字段直接内联，
/// JSON 结构与 Java 的扁平结构一致。
#[derive(Debug, Clone, Default, Serialize, Deserialize, sqlx::FromRow)]
#[serde(rename_all = "camelCase", default)]
pub struct SysUser {
    /// FastJson2 WriteClassName 写入 Redis 时的类型标记；HTTP 响应不输出。
    #[serde(rename = "@type", skip_serializing_if = "Option::is_none")]
    #[sqlx(skip)]
    pub type_name: Option<String>,

    #[sqlx(default)]
    pub user_id: Option<i64>,
    #[sqlx(default)]
    pub user_no: Option<i64>,
    #[sqlx(default)]
    pub dept_id: Option<i64>,
    #[sqlx(default)]
    pub user_name: Option<String>,
    #[sqlx(default)]
    pub nick_name: Option<String>,
    #[sqlx(default)]
    pub user_type: Option<String>,
    #[sqlx(default)]
    pub email: Option<String>,
    #[sqlx(default)]
    pub phonenumber: Option<String>,
    #[sqlx(default)]
    pub sex: Option<String>,
    #[sqlx(default)]
    pub avatar: Option<String>,
    /// Java: getPassword() 上有 @JsonIgnore，HTTP 不输出；Redis 中需要保留。
    #[sqlx(default)]
    pub password: Option<String>,
    #[sqlx(default)]
    pub confirm_password: Option<String>,
    #[sqlx(default)]
    pub salt: Option<String>,
    #[sqlx(default)]
    pub status: Option<String>,
    #[sqlx(default)]
    pub del_flag: Option<String>,
    #[sqlx(default)]
    pub login_ip: Option<String>,
    #[serde(
        default,
        serialize_with = "serialize_millis",
        deserialize_with = "deserialize_millis"
    )]
    #[sqlx(default)]
    pub login_date: Option<NaiveDateTime>,
    #[sqlx(default)]
    pub cert_id: Option<String>,
    #[sqlx(default)]
    pub cert_entity_id: Option<String>,
    #[sqlx(default)]
    pub buss_id: Option<String>,
    #[sqlx(default)]
    pub buss_name: Option<String>,
    #[sqlx(default)]
    pub eps_name: Option<String>,
    #[sqlx(default)]
    pub tenant_id: Option<i64>,
    #[sqlx(default)]
    pub tenant_name: Option<String>,
    #[sqlx(default)]
    pub role_code: Option<String>,
    #[sqlx(default)]
    pub flag: Option<String>,
    #[sqlx(default)]
    pub data_id: Option<String>,
    #[sqlx(default)]
    pub sub_code: Option<String>,
    #[sqlx(default)]
    pub query_nick_name: Option<String>,
    #[sqlx(default)]
    pub exclude_self: Option<bool>,
    #[sqlx(default)]
    pub exclude_id: Option<i64>,
    #[sqlx(default)]
    pub head_office: Option<bool>,
    #[sqlx(default)]
    pub procurement_manager: Option<bool>,
    #[sqlx(default)]
    pub dept_name: Option<String>,
    #[sqlx(default)]
    pub pj_flag: i32,
    #[sqlx(default)]
    pub image_id: Option<String>,

    // BaseEntity（JSON 扁平）
    #[serde(skip_serializing)]
    #[sqlx(default)]
    pub search_value: Option<String>,
    #[sqlx(default)]
    pub create_by: Option<String>,
    #[serde(
        default,
        serialize_with = "serialize_datetime",
        deserialize_with = "deserialize_datetime"
    )]
    #[sqlx(default)]
    pub create_time: Option<NaiveDateTime>,
    #[sqlx(default)]
    pub update_by: Option<String>,
    #[serde(
        default,
        serialize_with = "serialize_datetime",
        deserialize_with = "deserialize_datetime"
    )]
    #[sqlx(default)]
    pub update_time: Option<NaiveDateTime>,
    #[sqlx(default)]
    pub remark: Option<String>,
    #[serde(skip_serializing_if = "is_none_or_empty_map")]
    #[sqlx(skip)]
    pub params: Option<serde_json::Map<String, serde_json::Value>>,

    // 关联对象/临时字段
    #[sqlx(skip)]
    pub dept: Option<SysDept>,
    #[sqlx(skip)]
    pub roles: Vec<SysRole>,
    #[sqlx(skip)]
    pub role_ids: Option<Vec<i64>>,
    #[sqlx(skip)]
    pub post_ids: Option<Vec<i64>>,
    /// Java: SysUser.isAdmin() —— Jackson 输出 boolean 属性 admin。
    #[serde(default)]
    #[sqlx(skip)]
    pub admin: bool,
}

impl SysUser {
    /// Java: SysUser.isAdmin() -> userId != null && userId == 1L
    pub fn is_admin(&self) -> bool {
        self.user_id == Some(1)
    }

    /// Java: LoginUser.getUsername() -> user.getUserName()
    pub fn username(&self) -> String {
        self.user_name.clone().unwrap_or_default()
    }

    /// HTTP 响应使用：Java 的 getPassword() 标注 @JsonIgnore，不会序列化。
    pub fn for_http(&self) -> Self {
        let mut copy = self.clone();
        copy.password = None;
        copy.confirm_password = None;
        copy.salt = None;
        copy.type_name = None;
        copy.admin = self.is_admin();
        copy
    }

    /// Redis 写入使用：FastJson2 WriteClassName 需要 @type。
    pub fn for_redis(&self) -> Self {
        let mut copy = self.clone();
        copy.type_name = Some("com.ruoyi.common.core.domain.entity.SysUser".to_string());
        copy.admin = self.is_admin();
        let params = || {
            let mut map = serde_json::Map::new();
            map.insert(
                "@type".to_string(),
                serde_json::Value::String("java.util.HashMap".into()),
            );
            Some(map)
        };
        if copy.params.is_none() {
            copy.params = params();
        }
        if let Some(dept) = copy.dept.as_mut() {
            if dept.params.is_none() {
                dept.params = params();
            }
        }
        for role in &mut copy.roles {
            if role.params.is_none() {
                role.params = params();
            }
            role.admin = role.role_id == Some(1);
        }
        copy
    }
}
