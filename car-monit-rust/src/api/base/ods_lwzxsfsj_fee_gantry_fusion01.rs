// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java
//       ruoyi-system/.../base/service/forest/HttpOdsLwzxsfsjFeeGantryFusion01Service.java
// 职责: 门架交易流水（转发 vehicleMonitor.baseUrl 远端服务）。
// 对应关系: Forest @Get -> task::remote::get_json_owned；本地 mapper 仅保留列定义。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;
use crate::task::remote;

/// Java Jackson 的 `OdsLwzxsfsjFeeGantryFusion01` 键序（实体声明顺序，含 `exist=false` 的查询字段）。
const FEE_GANTRY_KEYS: &[&str] = &[
    "bigId",
    "actualfeeclass",
    "axlecount",
    "createtime",
    "discountfee",
    "electricalpercentage",
    "enaxlecount",
    "entime",
    "entolllanehex",
    "entolllaneid",
    "entollstationid",
    "entollstationname",
    "envehicleclass",
    "envehicleid",
    "envehicleidcolor",
    "envehicletype",
    "enweight",
    "entryoperatorid",
    "extime",
    "extolllaneid",
    "extollstationid",
    "extollstationname",
    "exvehicleclass",
    "exvehicleid",
    "exvehicletype",
    "exweight",
    "exitid",
    "fee",
    "feeboardplay",
    "feemileage",
    "feerate",
    "fusiondesc",
    "fusionflag",
    "id",
    "identification",
    "identifyvehicleid",
    "identifyvehicleidcolor",
    "lanetype",
    "mediano",
    "mediatype",
    "nocardcount",
    "obuid",
    "obusign",
    "obutotalamount",
    "obutotaldiscountamount",
    "operid",
    "params",
    "passid",
    "paycardid",
    "payfee",
    "paytype",
    "provfee",
    "provtranscount",
    "provincecount",
    "receivetime",
    "shift",
    "shortfee",
    "shortfeemileage",
    "signstatus",
    "spcrateversion",
    "specialtype",
    "splitprovince",
    "tac",
    "terminalno",
    "terminaltransno",
    "transfee",
    "transpaytype",
    "transtype",
    "vehiclesign",
    "vehiclesignid",
    "vid",
    "loadTime",
    "gradeLevel",
    "inApplyTime1",
    "inApplyTime2",
    "outApplyTime1",
    "outApplyTime2",
    "pageNum",
    "pageSize",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    // Java: pageNum/pageSize 为空时补 1/10。
    params
        .entry("pageNum".to_string())
        .or_insert_with(|| page.page_num.to_string());
    params
        .entry("pageSize".to_string())
        .or_insert_with(|| page.page_size.to_string());
    let value = remote::get_json_owned(
        &state,
        "/base/feeGantry/list",
        &remote::owned_params(&params),
    )
    .await?;
    Ok(remote::page_from_value(&value))
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let path = format!("/base/feeGantry/{}", urlencoding(&big_id));
    let value = remote::get_json_owned(&state, &path, &[]).await?;
    // Java: 详情要让 Forest 的 FastJson2 把响应反序列化成 `OdsLwzxsfsjFeeGantryFusion01`，
    // 而 `entime/extime/receivetime/loadTime` 是 `@JsonFormat(pattern = "yyyy-MM-dd")` 的 Date，
    // 上游给的是 `2024-10-26 08:53:57` —— 严格解析在第 10 个字符处遇到多余文本就抛
    // `ForestConvertException`，所以这个接口对**任何**真实行都是 500（实测 id=59/58 都如此）。
    // 照抄结果：同样 500、同样不返回 data；前缀那段 Forest 栈无法也不必复刻。
    for field in ["entime", "extime", "receivetime", "loadTime"] {
        if let Some(text) = value.get(field).and_then(Value::as_str) {
            if forest_date_reject(text).is_some() {
                return Ok(AjaxResult::error(format!(
                    "Text '{text}' could not be parsed, unparsed text found at index 10"
                )));
            }
        }
    }
    // Java: Forest 反序列化成实体再交给 Jackson，上游缺的字段是显式 null、多给的字段被丢掉。
    Ok(AjaxResult::success_data(support::entity_shape(
        value,
        FEE_GANTRY_KEYS,
    )))
}

fn urlencoding(value: &str) -> String {
    url::form_urlencoded::byte_serialize(value.as_bytes()).collect()
}

/// Java 的 FastJson2 在「前 10 个字符是合法 `yyyy-MM-dd`、后面还拖着时间」时抛
/// `unparsed text found at index 10`。别的一律不猜（宁可继续宽容解析，
/// 也不凭空造出一个 Java 不会报的 500）。
fn forest_date_reject(text: &str) -> Option<()> {
    let head = text.get(..10)?;
    if chrono::NaiveDate::parse_from_str(head, "%Y-%m-%d").is_ok() && text.len() > 10 {
        Some(())
    } else {
        None
    }
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/feeGantry/list",
            meta::get_route(
                "/base/feeGantry/list",
                Some("base:feeGantry:list"),
                None,
                list,
            ),
        )
        .route(
            "/base/feeGantry/{bigId}",
            meta::get_route("/base/feeGantry/{bigId}", None, None, get_info),
        )
}

#[cfg(test)]
mod tests {
    use super::forest_date_reject;

    /// Java 的 FastJson2 对 `@JsonFormat(pattern = "yyyy-MM-dd")` 是严格解析：
    /// 上游给 `2024-10-26 08:53:57` 就在 index 10 抛错（实测 id=59/58 全部 500）。
    #[test]
    fn date_only_pattern_rejects_trailing_time() {
        assert!(forest_date_reject("2024-10-26 08:53:57").is_some());
        assert!(forest_date_reject("2024-11-11T10:09:21.000+00:00").is_some());
        // 恰好是日期、或更短/更乱的写法：不猜 Java 会报什么，继续宽容解析。
        assert!(forest_date_reject("2024-10-26").is_none());
        assert!(forest_date_reject("2024-10-2").is_none());
        assert!(forest_date_reject("").is_none());
    }
}
