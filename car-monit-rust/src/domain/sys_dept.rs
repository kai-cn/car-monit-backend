// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDept.java
// 职责: 部门实体的 JSON 映射（登录用户 dept 关联、getInfo 输出）。
// 对应关系: SysDept extends BaseEntity；字段内联，JSON camelCase。

use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

use crate::common::serde_helpers::{
    deserialize_datetime, is_none_or_empty_map, serialize_datetime,
};

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct SysDept {
    /// FastJson2 类型标记；HTTP 不输出。
    #[serde(rename = "@type", skip_serializing_if = "Option::is_none")]
    pub type_name: Option<String>,

    pub dept_id: Option<i64>,
    pub parent_id: Option<i64>,
    /// Java 字段名是 ancestors（复数 s）
    pub ancestors: Option<String>,
    pub dept_name: Option<String>,
    /// Java: `private String orderNum`
    pub order_num: Option<String>,
    pub leader_id: Option<i64>,
    pub leader: Option<String>,
    pub fgld_id: Option<i64>,
    pub fgld_name: Option<String>,
    pub bank_name: Option<String>,
    pub account: Option<String>,
    pub social_code: Option<String>,
    pub postal_code: Option<String>,
    pub address: Option<String>,
    pub phone: Option<String>,
    pub email: Option<String>,
    pub status: Option<String>,
    pub is_zbzg: Option<String>,
    pub is_uint: Option<String>,
    pub tree_leavel: Option<i32>,
    pub sub_code: Option<String>,
    pub dept_jc: Option<String>,
    pub del_flag: Option<String>,
    pub parent_name: Option<String>,
    pub children: Vec<SysDept>,
    pub tenant_id: Option<i64>,
    pub flag: Option<String>,
    pub data_id: Option<String>,
    pub dept_sub_code: Option<String>,

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

impl SysDept {
    /// Redis 写入使用：FastJson2 WriteClassName 需要 @type。
    pub fn for_redis(&self) -> Self {
        let mut copy = self.clone();
        copy.type_name = Some("com.ruoyi.common.core.domain.entity.SysDept".to_string());
        copy
    }
}
