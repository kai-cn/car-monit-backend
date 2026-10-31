// 来源: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowAddcode.java
// 职责: 门架抓拍流水实体（分表/视图/远端同步共用）。
// 对应关系: MyBatis-Plus 实体 -> serde 结构体；@TableField(exist = false) 的查询字段
//           拆到 SnapshotFlowQuery，避免污染数据库映射。

use chrono::NaiveDateTime;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

use crate::common::serde_helpers::{
    deserialize_date, deserialize_millis, serialize_date, serialize_millis,
};

/// Java: `class OdsRtSzdnSnapshotFlowAddcode implements Custom`。
/// 字段顺序与实体一致；未标注 `@JsonFormat` 的 Date 沿用工程既有约定（epoch 毫秒）。
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct OdsRtSzdnSnapshotFlowAddcode {
    pub big_id: Option<String>,
    pub datasource: Option<String>,
    pub cameratype: Option<String>,
    pub deviceid: Option<String>,
    pub gantrycode: Option<String>,
    pub gantryname: Option<String>,
    pub roadcode: Option<String>,
    pub roadname: Option<String>,
    pub sectioncode: Option<String>,
    pub sectionname: Option<String>,
    pub tollcode: Option<String>,
    pub tollname: Option<String>,
    pub orgcode: Option<String>,
    pub orgname: Option<String>,
    pub direction: Option<i32>,
    pub hexcode: Option<String>,
    pub pileno: Option<String>,
    #[serde(with = "rust_decimal::serde::float_option")]
    pub lon: Option<Decimal>,
    #[serde(with = "rust_decimal::serde::float_option")]
    pub lat: Option<Decimal>,
    pub deviceip: Option<String>,
    pub siteid: Option<i32>,
    pub laneid: Option<i32>,
    pub snapshottimeunix: Option<i64>,
    #[serde(
        serialize_with = "serialize_millis",
        deserialize_with = "deserialize_millis"
    )]
    pub snapshottime: Option<NaiveDateTime>,
    pub receivedtimeunix: Option<i64>,
    #[serde(
        serialize_with = "serialize_date",
        deserialize_with = "deserialize_date"
    )]
    pub receivedtime: Option<NaiveDateTime>,
    pub platenumber: Option<String>,
    pub platecolor: Option<String>,
    pub platecolorcode: Option<i32>,
    pub platetype: Option<String>,
    pub platetypecode: Option<i32>,
    pub plateconfidence: Option<i32>,
    pub carbrand: Option<String>,
    pub carcolor: Option<String>,
    pub carcolorcode: Option<i32>,
    pub cartype: Option<String>,
    pub cartypecode: Option<i32>,
    pub cardirection: Option<String>,
    pub snappicturepath: Option<String>,
    #[serde(
        serialize_with = "serialize_date",
        deserialize_with = "deserialize_date"
    )]
    pub loadtime: Option<NaiveDateTime>,
    pub gradelevel: Option<i32>,
    pub datauuid: Option<String>,
    pub reserve3: Option<String>,
}

/// Java: 实体上的 `@TableField(exist = false)` 查询字段子集（Forest `@Query` / 列表查询用）。
/// 只包含分表同步会赋值的 4 个字段；其余查询字段在端点迁移时再补。
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct SnapshotFlowQuery {
    pub apply_time1: Option<String>,
    pub apply_time2: Option<String>,
    pub page_num: Option<i32>,
    pub page_size: Option<i32>,
}
