// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningInfoController.java
//       ruoyi-system/src/main/resources/mapper/manager/CarWarningInfoMapper.xml
// 职责: 预警车辆列表（按当天/历史与抓拍点过滤）、导出与 CRUD。
// 对应关系: selectCarWarningInfoList 的动态 flag/sectionCodeList/codeList -> QueryBuilder。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support;
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const COLUMNS: &str = "t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.car_num, \
     t.in_station_id, t.in_station, t.in_time, t.gantry_station_id, t.gantryt_station, \
     t.gantry_time, t.file_ids, t.next_pass_time, t.next_pass_type, t.next_pass_address, \
     t.next_pass_longitude, t.next_pass_latitude, t.road_code, t.road_name, t.section_code, \
     t.section_name, t.back_col1, t.back_col2, t.status, t.sort, t.eps_id, t.del_flag, \
     t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id, t.track_id, \
     t.track_names, c.escaped_type escapedType, c.escaped_amount escapedAmount, \
     c.plate_color plateColor";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "预警车辆",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarWarningInfoController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "预警车辆",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.CarWarningInfoController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "预警车辆",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarWarningInfoController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "预警车辆",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.CarWarningInfoController.remove()",
);

const STATION_CAPTURE: &str = "StationCapture";
const GANTRY_CAPTURE: &str = "GantryCapture";
const SERVICE_AREA_CAPTURE: &str = "ServiceAreaCapture";

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/carwarning/list",
            meta::get_route("/manager/carwarning/list", None, None, list),
        )
        .route(
            "/manager/carwarning/export",
            meta::get_route(
                "/manager/carwarning/export",
                Some("manager:carwarning:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/manager/carwarning/{ids}",
            meta::get_route("/manager/carwarning/{ids}", None, None, get_info),
        )
        .route(
            "/manager/carwarning",
            meta::post_route(
                "/manager/carwarning",
                Some("manager:carwarning:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/manager/carwarning",
                Some("manager:carwarning:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/manager/carwarning/{ids}",
            meta::delete_route(
                "/manager/carwarning/{ids}",
                Some("manager:carwarning:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java 的 list/export 共用预处理：flag、flagTime、sectionCode/code 列表。
fn normalize(params: &mut HashMap<String, String>) {
    let mut flag = params.get("queryRante").cloned().unwrap_or_default();
    if flag.trim().is_empty() {
        flag = "curDate".to_string();
    }
    let flag_time = chrono::Local::now().format("%Y%m%d").to_string();
    params.insert("flag".to_string(), flag);
    params.insert("flagTime".to_string(), flag_time);

    let section_code = params
        .get("sectionCode")
        .map(|value| value.trim().trim_end_matches(',').to_string())
        .unwrap_or_default();
    if !section_code.is_empty() {
        if !section_code.contains("all") {
            params.insert("sectionCodeList".to_string(), section_code);
        }
        params.insert("sectionCode".to_string(), String::new());
    }

    let code = params
        .get("code")
        .map(|value| value.trim().trim_end_matches(',').to_string())
        .unwrap_or_default();
    if !code.is_empty() {
        params.insert("codeList".to_string(), code);
        params.insert("code".to_string(), String::new());
    } else {
        let type_value = params.get("type").cloned().unwrap_or_default();
        let capture = match type_value.as_str() {
            "1" => STATION_CAPTURE,
            "2" => GANTRY_CAPTURE,
            "3" => SERVICE_AREA_CAPTURE,
            _ => "",
        };
        if !capture.is_empty() {
            params.insert("codeList".to_string(), capture.to_string());
        }
    }
}

fn build_query(
    params: &HashMap<String, String>,
    with_order: bool,
    count: bool,
) -> QueryBuilder<'static, MySql> {
    let head = if count {
        "select count(0) from car_warning_info t left join car_info c on t.car_id = c.id \
         where t.del_flag = '0'"
            .to_string()
    } else {
        format!(
            "select {COLUMNS} from car_warning_info t left join car_info c on t.car_id = c.id \
             where t.del_flag = '0'"
        )
    };
    let mut builder = QueryBuilder::<MySql>::new(head);
    let eq = |builder: &mut QueryBuilder<'_, MySql>, column: &str, key: &str| {
        if let Some(value) = params.get(key).filter(|value| !value.trim().is_empty()) {
            builder.push(format!(" and {column} = "));
            builder.push_bind(value.clone());
        }
    };
    let like = |builder: &mut QueryBuilder<'_, MySql>, column: &str, key: &str| {
        if let Some(value) = params.get(key).filter(|value| !value.trim().is_empty()) {
            builder.push(format!(" and {column} like concat('%', "));
            builder.push_bind(value.clone());
            builder.push(", '%')");
        }
    };
    eq(&mut builder, "t.id", "id");
    eq(&mut builder, "t.car_id", "carId");
    like(&mut builder, "t.car_no", "carNo");
    eq(&mut builder, "t.car_type", "carType");
    eq(&mut builder, "t.car_vehicle", "carVehicle");
    eq(&mut builder, "t.car_num", "carNum");
    eq(&mut builder, "t.in_station_id", "inStationId");
    eq(&mut builder, "t.in_station", "inStation");
    eq(&mut builder, "t.in_time", "inTime");
    eq(&mut builder, "t.gantry_station_id", "gantryStationId");
    like(&mut builder, "t.gantryt_station", "gantrytStation");
    eq(&mut builder, "t.gantry_time", "gantryTime");
    eq(&mut builder, "t.file_ids", "fileIds");
    eq(&mut builder, "t.next_pass_time", "nextPassTime");
    eq(&mut builder, "t.next_pass_type", "nextPassType");
    eq(&mut builder, "t.next_pass_address", "nextPassAddress");
    eq(&mut builder, "t.next_pass_longitude", "nextPassLongitude");
    eq(&mut builder, "t.next_pass_latitude", "nextPassLatitude");
    like(&mut builder, "t.track_names", "roadCode");
    like(&mut builder, "t.road_name", "roadName");
    like(&mut builder, "t.track_names", "sectionCode");
    like(&mut builder, "t.section_name", "sectionName");
    eq(&mut builder, "t.track_id", "trackId");
    eq(&mut builder, "t.track_josn", "trackJosn");
    like(&mut builder, "t.track_names", "trackNames");
    eq(&mut builder, "t.back_col1", "backCol1");
    eq(&mut builder, "t.back_col2", "backCol2");
    eq(&mut builder, "t.status", "status");
    eq(&mut builder, "t.sort", "sort");
    eq(&mut builder, "t.eps_id", "epsId");
    eq(&mut builder, "t.tenant_id", "tenantId");
    eq(&mut builder, "t.create_by", "createBy");
    if let Some(value) = params
        .get("applyTime1")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.in_time >= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d %H:%i:%s')");
    }
    if let Some(value) = params
        .get("applyTime2")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.in_time <= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d %H:%i:%s')");
    }
    like(&mut builder, "t.car_no", "carNoQuery");
    match params.get("flag").map(String::as_str) {
        Some("curDate") => {
            builder.push(" and c.status = '1' and t.back_col1 = ");
            builder.push_bind(params.get("flagTime").cloned().unwrap_or_default());
        }
        Some("histhory") => {
            builder.push(" and t.back_col1 != ");
            builder.push_bind(params.get("flagTime").cloned().unwrap_or_default());
        }
        _ => {}
    }
    like(&mut builder, "c.escaped_type", "escapedType");
    eq(&mut builder, "c.plate_color", "plateColor");
    for key in ["sectionCodeList", "codeList"] {
        if let Some(value) = params.get(key).filter(|value| !value.trim().is_empty()) {
            builder.push(" and (");
            let mut first = true;
            for item in value.split(',').filter(|item| !item.is_empty()) {
                if !first {
                    builder.push(" or ");
                }
                first = false;
                builder.push("t.track_names like concat('%', ");
                builder.push_bind(item.to_string());
                builder.push(", '%')");
            }
            builder.push(")");
        }
    }
    if with_order && !count {
        builder.push(" order by t.gantry_time desc, t.id");
    }
    builder
}

async fn query(
    state: &AppState,
    params: &HashMap<String, String>,
    page: Option<&crate::common::page::PageDomain>,
) -> Result<(i64, Vec<Value>), AppError> {
    let mut count_builder = build_query(params, false, true);
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;
    let mut builder = build_query(params, true, false);
    if let Some(page) = page {
        let (offset, limit) = page.resolve(total);
        builder.push(" limit ");
        builder.push_bind(limit);
        builder.push(" offset ");
        builder.push_bind(offset);
    }
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok((total, rows_to_json(&rows)))
}

/// Java Jackson 的 CarWarningInfo 键序（列表 VO 用查询列序，详情 VO 多了下面这些派生列）。
const CAR_WARNING_KEYS: &[&str] = &[
    "id",
    "epsId",
    "delFlag",
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "sort",
    "tenantId",
    "carId",
    "carNo",
    "carType",
    "carVehicle",
    "carNum",
    "inStationId",
    "inStation",
    "inTime",
    "gantryStationId",
    "gantrytStation",
    "gantryTime",
    "fileIds",
    "nextPassTime",
    "nextPassType",
    "nextPassAddress",
    "nextPassLongitude",
    "nextPassLatitude",
    "roadCode",
    "roadName",
    "sectionCode",
    "sectionName",
    "trackId",
    "trackJosn",
    "trackNames",
    "backCol1",
    "backCol2",
    "status",
    "gantryTimeStr",
    "applyTime1",
    "applyTime2",
    "escapedType",
    "escapedAmount",
    "carNoQuery",
    "createTimeStr",
    "inTimeStr",
    "flag",
    "flagTime",
    "queryRante",
    "gantryCode",
    "tollCode",
    "fwqbm",
    "type",
    "code",
    "plateColor",
    "trailFwqList",
    "sectionCodeList",
    "codeList",
    "needToWarnStr",
    "nextPassTimeStr",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    normalize(&mut params);
    let (total, rows) = query(&state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let mut params = support::query_map(&raw);
    normalize(&mut params);
    let (_, rows) = query(&state, &params, None).await?;

    let plate_color = support::dict_map(&state.db, "plate_color").await?;
    let car_type = support::dict_map(&state.db, "car_type").await?;
    let car_vehicle = support::dict_map(&state.db, "car_vehicle").await?;
    let escaped_type = support::dict_map(&state.db, "escaped_type").await?;

    let headers = [
        "车辆id",
        "车牌号",
        "车型",
        "车种",
        "轴数",
        "入口站id",
        "入口站",
        "入口时间",
        "门架id",
        "门架名称",
        "经过时间",
        "图片(附件ids)",
        "预计下一个通行时间",
        "预计下一个通行类型",
        "预计下一个通行地址",
        "预计下一个通行经度",
        "预计下一个通行维度",
        "所属路线编码",
        "所属路线名称",
        "所属路段编码",
        "所属路段名称",
        "行驶轨迹id",
        "行驶轨迹josn",
        "轨迹点集合",
        "同步日期",
        "备用字段2",
        "状态",
        "逃费类型",
        "逃费金额",
    ]
    .map(str::to_string);
    let fields = [
        "carId",
        "carNo",
        "carType",
        "carVehicle",
        "carNum",
        "inStationId",
        "inStation",
        "inTime",
        "gantryStationId",
        "gantrytStation",
        "gantryTime",
        "fileIds",
        "nextPassTime",
        "nextPassType",
        "nextPassAddress",
        "nextPassLongitude",
        "nextPassLatitude",
        "roadCode",
        "roadName",
        "sectionCode",
        "sectionName",
        "trackId",
        "backCol2",
        "trackNames",
        "backCol1",
        "backCol2",
        "status",
        "escapedType",
        "escapedAmount",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            for (index, map) in [(2usize, &car_type), (3, &car_vehicle), (26, &plate_color)] {
                let key = values
                    .get(index)
                    .and_then(Value::as_str)
                    .unwrap_or_default()
                    .to_string();
                values[index] = Value::String(map.get(&key).cloned().unwrap_or_default());
            }
            // 逃费类型 code 列表 -> 名称列表
            let escaped = values
                .get(27)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .trim_end_matches(',')
                .to_string();
            if !escaped.is_empty() {
                let names = escaped
                    .split(',')
                    .filter(|code| escaped_type.contains_key(*code))
                    .map(|code| escaped_type.get(code).cloned().unwrap_or_default())
                    .collect::<Vec<_>>()
                    .join(",");
                values[27] = Value::String(names.trim_end_matches(',').to_string());
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_download("预警车辆数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let row = sqlx::query(&format!(
        "select {COLUMNS}, t.track_josn, null as gantryTimeStr, null as applyTime1, \
         null as applyTime2, null as carNoQuery, null as createTimeStr, null as inTimeStr, \
         null as flag, null as flagTime, null as queryRante, null as gantryCode, \
         null as tollCode, null as fwqbm, null as type, null as code, \
         null as sectionCodeList, null as codeList, null as needToWarnStr, \
         null as nextPassTimeStr \
         from car_warning_info t left join car_info c on t.car_id = c.id where t.id = ?"
    ))
    .bind(&id)
    .fetch_optional(&state.db)
    .await?;
    Ok(AjaxResult::success_data(row.map(|row| {
        let mut value = crate::db::rows::row_to_json(&row);
        if let Some(object) = value.as_object_mut() {
            object.insert("trailFwqList".to_string(), serde_json::json!([]));
        }
        support::reorder_keys(value, CAR_WARNING_KEYS)
    })))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_warning_info", "id", true, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_warning_info", "id", true, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_warning_info", "id", &ids).await?;
    Ok(support::success_count(count))
}
