// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysRole.java
// 职责: 角色实体的 JSON 映射（登录用户 roles 关联、权限查询）。
// 对应关系: SysRole extends BaseEntity；字段内联，JSON camelCase。

use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

use crate::common::serde_helpers::{
    deserialize_datetime, is_none_or_empty_map, serialize_datetime,
};

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct SysRole {
    /// FastJson2 类型标记；HTTP 不输出。
    #[serde(rename = "@type", skip_serializing_if = "Option::is_none")]
    pub type_name: Option<String>,

    pub role_id: Option<i64>,
    pub role_name: Option<String>,
    pub role_key: Option<String>,
    /// Java: `private String roleSort`
    pub role_sort: Option<String>,
    pub data_scope: Option<String>,
    pub menu_check_strictly: bool,
    pub dept_check_strictly: bool,
    pub status: Option<String>,
    pub del_flag: Option<String>,
    pub flag: bool,
    pub menu_ids: Option<Vec<i64>>,
    pub dept_ids: Option<Vec<i64>>,
    /// Java: SysRole.isAdmin()。
    #[serde(default)]
    pub admin: bool,

    // BaseEntity
    #[serde(skip_serializing)]
    pub search_value: Option<String>,
    pub create_by: Option<String>,
    #[serde(
        serialize_with = "serialize_datetime",
        deserialize_with = "deserialize_datetime"
    )]
    pub create_time: Option<NaiveDateTime>,
    pub update_by: Option<String>,
    #[serde(
        serialize_with = "serialize_datetime",
        deserialize_with = "deserialize_datetime"
    )]
    pub update_time: Option<NaiveDateTime>,
    pub remark: Option<String>,
    #[serde(skip_serializing_if = "is_none_or_empty_map")]
    pub params: Option<serde_json::Map<String, serde_json::Value>>,
}

impl SysRole {
    /// Redis 写入使用：FastJson2 WriteClassName 需要 @type。
    pub fn for_redis(&self) -> Self {
        let mut copy = self.clone();
        copy.type_name = Some("com.ruoyi.common.core.domain.entity.SysRole".to_string());
        copy
    }
}
