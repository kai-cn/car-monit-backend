// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysMenu.java
// 职责: 菜单实体，JSON 与 MyBatis 列一一对应。
// 对应关系: SysMenu extends BaseEntity；children 默认空列表。

use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

use crate::common::serde_helpers::{
    deserialize_datetime, is_none_or_empty_map, serialize_datetime,
};

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct SysMenu {
    pub menu_id: Option<i64>,
    pub menu_name: Option<String>,
    pub parent_name: Option<String>,
    pub parent_id: Option<i64>,
    /// Java: `private String orderNum`（数据库为 int）
    pub order_num: Option<String>,
    pub path: Option<String>,
    pub component: Option<String>,
    /// 是否为外链（0是 1否）
    pub is_frame: Option<String>,
    /// 是否缓存（0缓存 1不缓存）
    pub is_cache: Option<String>,
    /// 类型（M目录 C菜单 F按钮）
    pub menu_type: Option<String>,
    /// 显示状态（0显示 1隐藏）
    pub visible: Option<String>,
    /// 菜单状态（0正常 1停用）
    pub status: Option<String>,
    pub perms: Option<String>,
    pub icon: Option<String>,
    /// Java 字段初始化为 new ArrayList<>()，始终序列化。
    pub children: Vec<SysMenu>,

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
