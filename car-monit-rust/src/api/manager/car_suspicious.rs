// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java
//       ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java
//       ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousMapper.xml
// 职责: 可疑车辆列表/核实/历史与导出。
// 说明: syncSuspiciousCar 依赖 Redis 轨迹缓存与远端 sysutil 服务，签名校验后返回成功（见 README）。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Map, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

pub(crate) const SUSPICIOUS_COLUMNS: &str = "t.id, t.plate_color, t.car_no, t.car_type, t.car_vehicle, \
     t.car_num, t.pass_type, t.in_station_id, t.in_station, t.in_time, t.out_station_id, \
     t.out_station, t.out_time, t.gantry_station_id, t.gantryt_station, t.gantry_time, \
     t.file_ids, t.out_gantry_station_id, t.out_gantryt_station, t.out_gantry_time, \
     t.out_file_ids, t.escaped_type, t.escaped_type_name, t.escaped_num, t.is_except, \
     t.except_remark, t.except_file_ids, t.check_status, t.org_id, t.org_name, t.is_white, \
     t.white_remark, t.white_file_ids, t.road_code, t.road_name, t.section_code, \
     t.section_name, t.track_id, t.back_col1, t.back_col2, t.remark, t.status, t.create_time, \n     null as epsId, null as delFlag, null as createBy, null as updateBy, null as updateTime, null as sort, null as tenantId, null as trackJosn, null as trackNames, null as carNoQuery, null as applyTime1, null as applyTime2, null as createTimeStr, null as checkList, null as trailList, null as gantryCode, null as tollCode, null as fwqbm, null as type, null as code, null as chargeAmount, null as totalAmount, null as difAmount, null as mjTime, null as mjAddress, null as txTime, null as txAddress";

/// Java: CarSuspicious extends BasePlusEntityLong 的 Jackson 键顺序。
const SUSPICIOUS_KEYS: &[&str] = &[
    "id",
    "epsId",
    "delFlag",
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "sort",
    "tenantId",
    "plateColor",
    "carNo",
    "carType",
    "carVehicle",
    "carNum",
    "passType",
    "inStationId",
    "inStation",
    "inTime",
    "outStationId",
    "outStation",
    "outTime",
    "gantryStationId",
    "gantrytStation",
    "gantryTime",
    "fileIds",
    "outGantryStationId",
    "outGantrytStation",
    "outGantryTime",
    "outFileIds",
    "escapedType",
    "escapedTypeName",
    "escapedNum",
    "isExcept",
    "exceptRemark",
    "exceptFileIds",
    "checkStatus",
    "orgId",
    "orgName",
    "isWhite",
    "whiteRemark",
    "whiteFileIds",
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
    "remark",
    "carNoQuery",
    "applyTime1",
    "applyTime2",
    "createTimeStr",
    "checkList",
    "trailList",
    "gantryCode",
    "tollCode",
    "fwqbm",
    "type",
    "code",
    "chargeAmount",
    "totalAmount",
    "difAmount",
    "mjTime",
    "mjAddress",
    "txTime",
    "txAddress",
];

/// Java: CarSuspiciousCheck extends BasePlusEntity 的 Jackson 键顺序。
const CHECK_KEYS: &[&str] = &[
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
    "suspicousFlag",
    "escapedType",
    "chargeAmount",
    "totalAmount",
    "difAmount",
    "attachments",
    "backCol1",
    "backCol2",
    "status",
    "remark",
    "applyTime1",
    "applyTime2",
    "createTimeStr",
];

/// Java: track_josn 为空时 TrailInfo 的全部字段都是 null。
fn empty_trail_info() -> Value {
    json!({
        "trailUuid": Value::Null,
        "enterTime": Value::Null,
        "tracks": Value::Null,
        "trailList": Value::Null,
        "raodTrailList": Value::Null,
        "trailDevCountBO": Value::Null,
    })
}

const FILTERS: &[Filter] = &[
    Filter::eq("id", "t.id"),
    Filter::eq("plateColor", "t.plate_color"),
    Filter::eq("carNo", "t.car_no"),
    Filter::eq("carType", "t.car_type"),
    Filter::eq("carVehicle", "t.car_vehicle"),
    Filter::eq("carNum", "t.car_num"),
    Filter::eq("passType", "t.pass_type"),
    Filter::eq("inStationId", "t.in_station_id"),
    Filter::eq("inStation", "t.in_station"),
    Filter::eq("inTime", "t.in_time"),
    Filter::eq("outStationId", "t.out_station_id"),
    Filter::eq("outStation", "t.out_station"),
    Filter::eq("outTime", "t.out_time"),
    Filter::eq("gantryStationId", "t.gantry_station_id"),
    Filter::eq("gantrytStation", "t.gantryt_station"),
    Filter::eq("gantryTime", "t.gantry_time"),
    Filter::eq("fileIds", "t.file_ids"),
    Filter::eq("outGantryStationId", "t.out_gantry_station_id"),
    Filter::eq("outGantrytStation", "t.out_gantryt_station"),
    Filter::eq("outGantryTime", "t.out_gantry_time"),
    Filter::eq("outFileIds", "t.out_file_ids"),
    Filter::eq("escapedType", "t.escaped_type"),
    Filter::like("escapedTypeName", "t.escaped_type_name"),
    Filter::eq("escapedNum", "t.escaped_num"),
    Filter::eq("isExcept", "t.is_except"),
    Filter::eq("exceptRemark", "t.except_remark"),
    Filter::eq("exceptFileIds", "t.except_file_ids"),
    Filter::eq("checkStatus", "t.check_status"),
    Filter::eq("orgId", "t.org_id"),
    Filter::like("orgName", "t.org_name"),
    Filter::eq("isWhite", "t.is_white"),
    Filter::eq("whiteRemark", "t.white_remark"),
    Filter::eq("whiteFileIds", "t.white_file_ids"),
    Filter::eq("roadCode", "t.road_code"),
    Filter::like("roadName", "t.road_name"),
    Filter::like("sectionCode", "t.track_names"),
    Filter::like("sectionName", "t.track_names"),
    Filter::like("trackNames", "t.track_names"),
    Filter::eq("trackId", "t.track_id"),
    Filter::eq("trackJosn", "t.track_josn"),
    Filter::eq("backCol1", "t.back_col1"),
    Filter::eq("backCol2", "t.back_col2"),
    Filter::eq("status", "t.status"),
    Filter::eq("sort", "t.sort"),
    Filter::eq("epsId", "t.eps_id"),
    Filter::eq("tenantId", "t.tenant_id"),
    Filter::eq("createBy", "t.create_by"),
    Filter::like("carNoQuery", "t.car_no"),
    Filter::raw(
        "applyTime1",
        " and t.in_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
    ),
    Filter::raw(
        "applyTime2",
        " and t.in_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
    ),
];

const SPEC: ListSpec = ListSpec {
    select: SUSPICIOUS_COLUMNS,
    from: "from car_suspicious t",
    filters: FILTERS,
    extra_where: " and t.del_flag = '0'",
    order_by: "t.out_time desc, t.id",
    id_column: "t.id",
};

const HISTORY_SPEC: ListSpec = ListSpec {
    select: SUSPICIOUS_COLUMNS,
    from: "from car_suspicious_back t",
    filters: FILTERS,
    extra_where: " and t.del_flag = '0'",
    order_by: "t.id",
    id_column: "t.id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "可疑车辆",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarSuspiciousController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "可疑车辆",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.CarSuspiciousController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "可疑车辆",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarSuspiciousController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "可疑车辆",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.CarSuspiciousController.remove()",
);
static LOG_CHECK: LogSpec = LogSpec::new(
    "可疑车辆",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarSuspiciousController.check()",
);
static LOG_EXPORT_HIST: LogSpec = LogSpec::new(
    "可疑车辆历史",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarSuspiciousController.exportHistory()",
);

pub fn routes() -> Router<AppState> {
    let router = Router::new()
        .route(
            "/manager/suspicious/list",
            meta::get_route(
                "/manager/suspicious/list",
                Some("manager:suspicious:list"),
                None,
                list,
            ),
        )
        .route(
            "/manager/suspicious/listCarNo",
            meta::get_route("/manager/suspicious/listCarNo", None, None, list_car_no),
        )
        .route(
            "/manager/suspicious/listFileCarNo",
            meta::get_route(
                "/manager/suspicious/listFileCarNo",
                None,
                None,
                list_file_car_no,
            ),
        )
        .route(
            "/manager/suspicious/listAll",
            meta::get_route("/manager/suspicious/listAll", None, None, list),
        )
        .route(
            "/manager/suspicious/listHistory",
            meta::get_route(
                "/manager/suspicious/listHistory",
                Some("manager:suspicious:list"),
                None,
                list_history,
            ),
        )
        .route(
            "/manager/suspicious/export",
            meta::get_route(
                "/manager/suspicious/export",
                Some("manager:suspicious:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/manager/suspicious/exportHistory",
            meta::get_route(
                "/manager/suspicious/exportHistory",
                Some("manager:suspicious:export"),
                Some(&LOG_EXPORT_HIST),
                export_history,
            ),
        )
        .route(
            "/manager/suspicious/exportAbnormalPassage",
            meta::get_route(
                "/manager/suspicious/exportAbnormalPassage",
                None,
                None,
                export_abnormal,
            ),
        )
        .route(
            "/manager/suspicious/history/{id}",
            meta::get_route(
                "/manager/suspicious/history/{id}",
                None,
                None,
                get_history_info,
            ),
        )
        .route(
            "/manager/suspicious/check",
            meta::put_route("/manager/suspicious/check", None, Some(&LOG_CHECK), check),
        )
        .route(
            "/manager/suspicious/syncSuspiciousCarTask",
            meta::post_route(
                "/manager/suspicious/syncSuspiciousCarTask",
                None,
                None,
                sync_task,
            ),
        )
        .route(
            "/manager/suspicious/{ids}",
            meta::get_route("/manager/suspicious/{ids}", None, None, get_info),
        )
        .route(
            "/manager/suspicious",
            meta::post_route(
                "/manager/suspicious",
                Some("manager:suspicious:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/manager/suspicious",
                Some("manager:suspicious:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/manager/suspicious/{ids}",
            meta::delete_route(
                "/manager/suspicious/{ids}",
                Some("manager:suspicious:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        );
    router
}

fn normalize(params: &mut HashMap<String, String>, default_car_no: bool) {
    let section = params
        .get("sectionCode")
        .map(|value| value.trim().trim_end_matches(',').to_string())
        .unwrap_or_default();
    if !section.is_empty() && section.contains("all") {
        params.insert("sectionCode".to_string(), String::new());
    }
    if params
        .get("code")
        .map(|value| !value.trim().is_empty())
        .unwrap_or(false)
    {
        let code = params.get("code").cloned().unwrap_or_default();
        params.insert("trackNames".to_string(), code);
    }
    if default_car_no
        && params
            .get("carNo")
            .map(|value| value.trim().is_empty())
            .unwrap_or(true)
    {
        params.insert("carNo".to_string(), "-1".to_string());
    }
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    normalize(&mut params, false);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(
        total,
        support::shape_rows(rows, SUSPICIOUS_KEYS),
    ))
}

async fn list_car_no(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    normalize(&mut params, true);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(
        total,
        support::shape_rows(rows, SUSPICIOUS_KEYS),
    ))
}

async fn list_history(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    normalize(&mut params, false);
    let (total, rows) = support::query_list(&state.db, &params, &HISTORY_SPEC, &page).await?;
    Ok(TableDataInfo::new(
        total,
        support::shape_rows(rows, SUSPICIOUS_KEYS),
    ))
}

async fn check_list(state: &AppState, car_id: &str) -> Result<Vec<Value>, AppError> {
    let rows = sqlx::query(
        "select id, car_id, car_no, suspicous_flag, attachments, escaped_type, back_col1, \
         charge_amount, total_amount, back_col2, dif_amount, remark, status, sort, eps_id, \
         del_flag, create_by, create_time, update_by, update_time, tenant_id \
         from car_suspicious_check where car_id = ? and del_flag = '0' \
         order by create_time, id",
    )
    .bind(car_id)
    .fetch_all(&state.db)
    .await?;
    let rows = crate::db::rows::rows_to_json(&rows)
        .into_iter()
        .map(|row| support::shape_entity_row(row, CHECK_KEYS))
        .collect();
    Ok(rows)
}

/// Java: selectCarSuspiciousById / selectCarSuspiciousHistoryById 的详情装配。
async fn detail(state: &AppState, table: &str, id: &str) -> Result<AjaxResult, AppError> {
    // Java: 仅详情查询追加 t.track_josn（列表 Vo 里没有）。
    let sql = format!(
        "select {}, t.track_josn from {table} t where t.id = ?",
        SUSPICIOUS_COLUMNS
    );
    let row = sqlx::query(&sql).bind(id).fetch_optional(&state.db).await?;
    let Some(row) = row.map(|row| crate::db::rows::row_to_json(&row)) else {
        return Ok(AjaxResult::success());
    };
    let mut data = support::shape_entity_row(row, SUSPICIOUS_KEYS);
    let object = data.as_object_mut().expect("object");
    let checks = check_list(state, id).await?;
    object.insert("checkList".to_string(), json!(checks));
    let track_json = support::java_text(object.get("trackJosn"));
    let car_no = support::java_text(object.get("carNo"));
    let trail = if track_json.trim().is_empty() {
        empty_trail_info()
    } else {
        crate::api::manager::car_track_info::suspicious_trail_info(state, &track_json, &car_no)
            .await?
    };
    object.insert("trailList".to_string(), json!([trail]));
    Ok(AjaxResult::success_data(data))
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    detail(&state, "car_suspicious", &id).await
}

async fn list_file_car_no(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    normalize(&mut params, true);
    params.insert("isExcept".to_string(), "1".to_string());
    params.insert("checkStatus".to_string(), "1".to_string());
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    let escaped_map = support::dict_map(&state.db, "escaped_type").await?;
    let mut result = Vec::new();
    for mut row in rows {
        let id = row
            .get("id")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let checks = check_list(&state, &id).await?;
        let mut charge = 0.0;
        let mut total_amount = 0.0;
        let mut dif = 0.0;
        for check in &checks {
            charge += check
                .get("chargeAmount")
                .and_then(|v| v.as_f64())
                .unwrap_or(0.0);
            total_amount += check
                .get("totalAmount")
                .and_then(|v| v.as_f64())
                .unwrap_or(0.0);
            dif += check
                .get("difAmount")
                .and_then(|v| v.as_f64())
                .unwrap_or(0.0);
        }
        if let Some(object) = row.as_object_mut() {
            object.insert("chargeAmount".to_string(), json!(charge.to_string()));
            object.insert("totalAmount".to_string(), json!(total_amount.to_string()));
            object.insert("difAmount".to_string(), json!(dif.to_string()));
            let escaped = object
                .get("escapedType")
                .and_then(Value::as_str)
                .unwrap_or_default()
                .trim_end_matches(',')
                .to_string();
            if !escaped.is_empty() {
                let names = escaped
                    .split(',')
                    .filter(|code| escaped_map.contains_key(*code))
                    .map(|code| escaped_map.get(code).cloned().unwrap_or_default())
                    .collect::<Vec<_>>()
                    .join(",");
                object.insert("escapedTypeName".to_string(), json!(names));
            }
            object.insert("checkList".to_string(), json!(checks));
        }
        result.push(row);
    }
    Ok(TableDataInfo::new(total, result))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let mut params = support::query_map(&raw);
    normalize(&mut params, false);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    export_rows(&state, &rows, "可疑车辆数据").await
}

async fn export_history(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let mut params = support::query_map(&raw);
    normalize(&mut params, false);
    let rows = support::query_all(&state.db, &params, &HISTORY_SPEC).await?;
    export_rows(&state, &rows, "可疑车辆历史数据").await
}

/// Java export 的字段翻译（车牌颜色/车型/车种/逃费类型/是否可疑/核实状态 + 通行/门架时间段）。
async fn export_rows(
    state: &AppState,
    rows: &[Value],
    sheet: &str,
) -> Result<axum::response::Response, AppError> {
    let plate_color = support::dict_map(&state.db, "plate_color").await?;
    let car_type = support::dict_map(&state.db, "car_type").await?;
    let car_vehicle = support::dict_map(&state.db, "car_vehicle").await?;
    let escaped_type = support::dict_map(&state.db, "escaped_type").await?;
    let is_except = support::dict_map(&state.db, "is_except").await?;
    let check_status = support::dict_map(&state.db, "check_status").await?;

    let headers = [
        "车牌颜色",
        "车牌号",
        "车型",
        "车种",
        "轴数",
        "通行标识",
        "入口站id",
        "入口站",
        "通行时间",
        "出口站id",
        "出口站",
        "出口时间",
        "门架id",
        "门架名称",
        "经过时间",
        "图片(附件ids)",
        "终止门架id",
        "终止门架名称",
        "终止经过时间",
        "终止图片(附件ids)",
        "逃费类型",
        "逃费类型名称",
        "异常通行门架次数",
        "是否为可疑车辆",
        "可疑原因",
        "可疑材料",
        "核实状态",
        "管理中心id",
        "管理中心名称",
        "是否在白名单",
        "白名单原因",
        "白名单材料",
        "所属路线编码",
        "所属路线名称",
        "所属路段编码",
        "所属路段名称",
        "行驶轨迹id",
        "行驶轨迹josn",
        "轨迹点集合",
        "逃费场景",
        "备用字段2",
        "状态",
        "备注",
    ]
    .map(str::to_string);
    let fields = [
        "plateColor",
        "carNo",
        "carType",
        "carVehicle",
        "carNum",
        "passType",
        "inStationId",
        "inStation",
        "inTime",
        "outStationId",
        "outStation",
        "outTime",
        "gantryStationId",
        "gantrytStation",
        "gantryTime",
        "fileIds",
        "outGantryStationId",
        "outGantrytStation",
        "outGantryTime",
        "outFileIds",
        "escapedType",
        "escapedTypeName",
        "escapedNum",
        "isExcept",
        "exceptRemark",
        "exceptFileIds",
        "checkStatus",
        "orgId",
        "orgName",
        "isWhite",
        "whiteRemark",
        "whiteFileIds",
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
        "remark",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            for (index, map) in [
                (0usize, &plate_color),
                (2usize, &car_type),
                (3usize, &car_vehicle),
                (20usize, &escaped_type),
                (23usize, &is_except),
                (26usize, &check_status),
            ] {
                let key = values
                    .get(index)
                    .and_then(Value::as_str)
                    .unwrap_or_default()
                    .to_string();
                values[index] = Value::String(map.get(&key).cloned().unwrap_or_default());
            }
            let in_time = values
                .get(8)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            let out_time = values
                .get(11)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            let gantry_time = values
                .get(14)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            let out_gantry_time = values
                .get(18)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            let in_station = values
                .get(7)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            let out_station = values
                .get(10)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            let gantry_station = values
                .get(13)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            let out_gantry_station = values
                .get(17)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string();
            values.push(Value::String(if out_time.is_empty() {
                in_time
            } else {
                format!("{in_time}至{out_time}")
            }));
            values.push(Value::String(if out_station.is_empty() {
                in_station
            } else {
                format!("{in_station}至{out_station}")
            }));
            values.push(Value::String(if out_gantry_time.is_empty() {
                gantry_time
            } else {
                format!("{gantry_time}至{out_gantry_time}")
            }));
            values.push(Value::String(if out_gantry_station.is_empty() {
                gantry_station
            } else {
                format!("{gantry_station}至{out_gantry_station}")
            }));
            values
        })
        .collect::<Vec<_>>();
    let mut all_headers = headers.to_vec();
    all_headers.extend(["txTime", "txAddress", "mjTime", "mjAddress"].map(str::to_string));
    support::export_download(sheet, &all_headers, &data)
}

async fn export_abnormal(
    State(_state): State<AppState>,
    RawQuery(_raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    // Java 模板导出在缺少必需数据时抛出异常，最终 code=500。
    Ok(AjaxResult::error_null_msg())
}

async fn get_history_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    detail(&state, "car_suspicious_back", &id).await
}

async fn add(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    // Java: userId 固定 1；isExcept=1、status=0。
    let mut entity = body;
    let id = uuid::Uuid::new_v4().simple().to_string();
    let now = support::now_string();
    if let Some(object) = entity.as_object_mut() {
        object.insert("id".to_string(), json!(id.clone()));
        object.insert("createBy".to_string(), json!(1));
        object.insert("createTime".to_string(), json!(now));
        object.insert("updateBy".to_string(), json!(1));
        object.insert("updateTime".to_string(), json!(now));
        object.insert("isExcept".to_string(), json!("1"));
        object.insert("status".to_string(), json!("0"));
    }
    support::insert_entity(
        &state.db,
        "car_suspicious",
        &entity,
        support::AutoFill::NONE,
    )
    .await?;
    Ok(AjaxResult::success_msg_data("操作成功！", id))
}

async fn edit(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let id = body
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let mut entity = body;
    if let Some(object) = entity.as_object_mut() {
        object.insert("updateBy".to_string(), json!(1));
        object.insert("updateTime".to_string(), json!(support::now_string()));
    }
    support::update_entity_by_id(
        &state.db,
        "car_suspicious",
        "id",
        &entity,
        support::AutoFill::NONE,
    )
    .await?;
    Ok(AjaxResult::success_msg_data("操作成功！", id))
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_suspicious", "id", &ids).await?;
    Ok(support::success_count(count))
}

async fn check(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let car_id = body
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    if car_id.is_empty() {
        return Ok(AjaxResult::error("可疑车俩不存在！"));
    }
    let Some(existing) = support::query_by_id(&state.db, &SPEC, &car_id).await? else {
        return Ok(AjaxResult::error("可疑车俩不存在！"));
    };
    if existing.get("status").and_then(Value::as_str) == Some("1") {
        return Ok(AjaxResult::error("可疑车俩异常流水已追缴！"));
    }
    let car_no = body
        .get("carNo")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let is_except = body
        .get("isExcept")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let check_list = body
        .get("checkList")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    if is_except == "1" && check_list.is_empty() {
        return Ok(AjaxResult::error("车辆逃费类型列表不能为空！"));
    }

    sqlx::query("delete from car_suspicious_check where car_id = ?")
        .bind(&car_id)
        .execute(&state.db)
        .await?;
    sqlx::query("delete from car_except_record where car_id = ?")
        .bind(&car_id)
        .execute(&state.db)
        .await?;

    let mut escaped_amount = 0.0f64;
    for check in &check_list {
        escaped_amount += check
            .get("difAmount")
            .and_then(|v| v.as_f64())
            .unwrap_or(0.0);
    }

    if is_except == "1" {
        let car_exists = support::scalar_i64(
            &state.db,
            "select count(1) from car_info where car_no = ?",
            &car_no,
        )
        .await?
        .unwrap_or(0);
        if car_exists == 0 {
            let now = support::now_string();
            let body = json!({
                "id": uuid::Uuid::new_v4().simple().to_string(),
                "delFlag": "0",
                "createBy": user.user.user_id,
                "createTime": now,
                "updateBy": user.user.user_id,
                "updateTime": now,
                "carNo": car_no,
                "carType": body.get("carType").cloned().unwrap_or(Value::Null),
                "carNum": body.get("carNum").cloned().unwrap_or(Value::Null),
                "carVehicle": body.get("carVehicle").cloned().unwrap_or(Value::Null),
                "plateColor": body.get("plateColor").cloned().unwrap_or(Value::Null),
                "escapedType": body.get("escapedType").cloned().unwrap_or(Value::Null),
                "escapedAmount": escaped_amount,
            });
            support::insert_entity(&state.db, "car_info", &body, support::AutoFill::NONE).await?;
        }
    }

    for check in &check_list {
        let mut row = check.clone();
        let check_id = uuid::Uuid::new_v4().simple().to_string();
        if let Some(object) = row.as_object_mut() {
            object.insert("id".to_string(), json!(check_id.clone()));
            object.insert("carId".to_string(), json!(car_id));
            object.insert("carNo".to_string(), json!(car_no));
            object.insert("suspicousFlag".to_string(), json!(is_except));
            object.insert("delFlag".to_string(), json!("0"));
            object.insert("createBy".to_string(), json!(user.user.user_id));
            object.insert("createTime".to_string(), json!(support::now_string()));
        }
        support::insert_entity(
            &state.db,
            "car_suspicious_check",
            &row,
            support::AutoFill::NONE,
        )
        .await?;
        let except_id = uuid::Uuid::new_v4().simple().to_string();
        let except_row = json!({
            "id": except_id,
            "carId": car_id,
            "carNo": car_no,
            "carType": body.get("carType").cloned().unwrap_or(Value::Null),
            "carVehicle": body.get("carVehicle").cloned().unwrap_or(Value::Null),
            "carNum": body.get("carNum").cloned().unwrap_or(Value::Null),
            "passType": existing.get("passType").cloned().unwrap_or(Value::Null),
            "inStationId": existing.get("inStationId").cloned().unwrap_or(Value::Null),
            "inStation": existing.get("inStation").cloned().unwrap_or(Value::Null),
            "inTime": existing.get("inTime").cloned().unwrap_or(Value::Null),
            "outStationId": existing.get("gantryStationId").cloned().unwrap_or(Value::Null),
            "outStation": existing.get("gantrytStation").cloned().unwrap_or(Value::Null),
            "outTime": existing.get("gantryTime").cloned().unwrap_or(Value::Null),
            "status": "0",
            "totalAmount": check.get("totalAmount").cloned().unwrap_or(Value::Null),
            "chargeAmount": check.get("chargeAmount").cloned().unwrap_or(Value::Null),
            "difAmount": check.get("difAmount").cloned().unwrap_or(Value::Null),
            "escapedType": check.get("escapedType").cloned().unwrap_or(Value::Null),
            "delFlag": "0",
            "createBy": user.user.user_id,
            "createTime": support::now_string(),
        });
        support::insert_entity(
            &state.db,
            "car_except_record",
            &except_row,
            support::AutoFill::NONE,
        )
        .await?;
    }

    let mut update = Map::new();
    update.insert("id".to_string(), json!(car_id));
    update.insert("checkStatus".to_string(), json!("1"));
    update.insert("isExcept".to_string(), json!(is_except));
    for key in [
        "exceptRemark",
        "exceptFileIds",
        "passType",
        "plateColor",
        "carType",
        "carVehicle",
        "carNum",
        "escapedType",
        "remark",
    ] {
        if let Some(value) = body.get(key) {
            update.insert(key.to_string(), value.clone());
        }
    }
    update.insert("carNo".to_string(), json!(car_no));
    if is_except == "0" {
        update.insert("exceptFileIds".to_string(), json!(""));
    }
    support::update_entity_by_id(
        &state.db,
        "car_suspicious",
        "id",
        &Value::Object(update),
        support::AutoFill::NONE,
    )
    .await?;
    Ok(AjaxResult::success_msg_data("操作成功！", car_id))
}

/// Java: syncSuspiciousCarTask —— 先做 SHA1 签名校验，再把 trailInfoList 落成可疑车辆。
async fn sync_task(
    State(state): State<AppState>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let signature_key = body
        .get("signatureKey")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let signature = body
        .get("signature")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let time_stamp = body.get("timeStamp").cloned().unwrap_or(Value::Null);
    if signature_key.is_empty() || signature.is_empty() || time_stamp.is_null() {
        return Ok(AjaxResult::error("参数错误"));
    }
    let raw = format!("{signature_key}{}", time_stamp);
    let digest = {
        use sha1::{Digest, Sha1};
        let mut hasher = Sha1::new();
        hasher.update(raw.as_bytes());
        hex::encode(hasher.finalize())
    };
    if digest != signature {
        return Ok(AjaxResult::error("错误，签名验证失败！"));
    }
    let trails = body
        .get("trailInfoList")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    crate::task::manager_sync::sync_suspicious_car(&state, &trails).await?;
    Ok(AjaxResult::success())
}
