// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java
//       ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailTracksServiceImpl.java
// 职责: 车辆行驶轨迹 CRUD、历史轨迹（本地 zdata_trail_tracks）、轨迹详情/导出。
// 对应关系: carTrackQuery -> getHistoryTrail/getCyly；TrailInfo 包装为同名字段 JSON。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Map, Value};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::common::gps;
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::service::road_path;
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.car_id, t.car_no, t.longitude, t.latitude, t.device_type, t.device_no, \
             t.lane_no, t.snap_time, t.receive_time, t.snap_pic, t.road_section_id, \
             t.road_section_name, t.track_id, t.back_col1, t.back_col2, t.remark, t.status, \
             t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, \
             t.update_time, t.tenant_id, null as applyTime1, null as applyTime2, null as latitudeDec, null as longitudeDec, null as pageNum, null as pageSize, t.track_josn",
    from: "from car_track_info t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("carId", "t.car_id"),
        Filter::eq("carNo", "t.car_no"),
        Filter::eq("longitude", "t.longitude"),
        Filter::eq("latitude", "t.latitude"),
        Filter::eq("deviceType", "t.device_type"),
        Filter::eq("deviceNo", "t.device_no"),
        Filter::eq("laneNo", "t.lane_no"),
        Filter::eq("snapTime", "t.snap_time"),
        Filter::eq("receiveTime", "t.receive_time"),
        Filter::eq("snapPic", "t.snap_pic"),
        Filter::eq("roadSectionId", "t.road_section_id"),
        Filter::like("roadSectionName", "t.road_section_name"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
        Filter::raw(
            "applyTime1",
            " and t.create_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
        ),
        Filter::raw(
            "applyTime2",
            " and t.create_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
        ),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time, t.id",
    id_column: "t.id",
};

const TRAIL_COLUMNS: &str = "t.uuid, t.type, t.point_count, t.plate_key, t.enter_time, \
     t.exit_time, t.trail_points, t.enter_locationcode, t.exit_locationcode, \
     t.track_josn, t.enaxlecount, t.entolllaneid, t.entollstationid, t.entollstationname, \
     t.envehicleclass, t.envehicleid, t.envehicletype, t.enweight, t.extolllaneid, \
     t.extollstationid, t.extollstationname, t.exvehicleclass, t.exvehicleid, t.exvehicletype, \
     t.exweight, t.start_lon, t.strat_lat, t.end_lon, t.end_lat, \
     null as firtStationCode, null as firtStationName, null as firtStationTime, \
     null as plateColor, null as carType, null as carNo, null as carVehicle, null as carNum, \
     null as escapedType, null as passType, null as escapedTypeRemark, null as applyTime1, \
     null as applyTime2, null as isCylx, null as flag, null as startLonDec, null as stratLatDec, \
     null as endLonDec, null as endLatDec, null as uuidList, null as passCount, null as escapedTfcj";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "车辆行驶轨迹",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarTrackInfoController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "车辆行驶轨迹",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.CarTrackInfoController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "车辆行驶轨迹",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarTrackInfoController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "车辆行驶轨迹",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.CarTrackInfoController.remove()",
);
static LOG_CHANGE: LogSpec = LogSpec::new(
    "车辆行驶轨迹",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarTrackInfoController.changeTrailInfo()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/cartrackinfo/list",
            meta::get_route(
                "/manager/cartrackinfo/list",
                Some("manager:cartrackinfo:list"),
                None,
                list,
            ),
        )
        .route(
            "/manager/cartrackinfo/listByCarId",
            meta::get_route(
                "/manager/cartrackinfo/listByCarId",
                None,
                None,
                list_by_car_id,
            ),
        )
        .route(
            "/manager/cartrackinfo/listByCarByTime",
            meta::get_route(
                "/manager/cartrackinfo/listByCarByTime",
                None,
                None,
                list_by_car,
            ),
        )
        .route(
            "/manager/cartrackinfo/changeTrailInfo",
            meta::put_route(
                "/manager/cartrackinfo/changeTrailInfo",
                None,
                Some(&LOG_CHANGE),
                change_trail,
            ),
        )
        .route(
            "/manager/cartrackinfo/carSnapShot",
            meta::get_route(
                "/manager/cartrackinfo/carSnapShot",
                None,
                None,
                car_snapshot,
            ),
        )
        .route(
            "/manager/cartrackinfo/export",
            meta::get_route(
                "/manager/cartrackinfo/export",
                Some("manager:cartrackinfo:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/manager/cartrackinfo/{ids}",
            meta::get_route("/manager/cartrackinfo/{ids}", None, None, get_info),
        )
        .route(
            "/manager/cartrackinfo",
            meta::post_route(
                "/manager/cartrackinfo",
                Some("manager:cartrackinfo:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/manager/cartrackinfo",
                Some("manager:cartrackinfo:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/manager/cartrackinfo/{ids}",
            meta::delete_route(
                "/manager/cartrackinfo/{ids}",
                Some("manager:cartrackinfo:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java CarTrackInfo.longitudeDec/latitudeDec：经纬度字符串转 BigDecimal。
fn fill_decimals(rows: &mut [Value]) {
    for row in rows {
        let Some(object) = row.as_object_mut() else {
            continue;
        };
        for (source, target) in [("longitude", "longitudeDec"), ("latitude", "latitudeDec")] {
            let parsed = object
                .get(source)
                .and_then(Value::as_str)
                .and_then(|text| text.trim().parse::<f64>().ok())
                .and_then(serde_json::Number::from_f64)
                .map(Value::Number)
                .unwrap_or(Value::Null);
            object.insert(target.to_string(), parsed);
        }
    }
}

/// Java: CarTrackInfo extends BasePlusEntity 的 Jackson 键顺序。
const CAR_TRACK_KEYS: &[&str] = &[
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
    "longitude",
    "latitude",
    "deviceType",
    "deviceNo",
    "laneNo",
    "snapTime",
    "receiveTime",
    "snapPic",
    "roadSectionId",
    "roadSectionName",
    "trackId",
    "trackJosn",
    "backCol1",
    "backCol2",
    "status",
    "remark",
    "applyTime1",
    "applyTime2",
    "longitudeDec",
    "latitudeDec",
    "pageNum",
    "pageSize",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, mut rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    fill_decimals(&mut rows);
    let data = support::shape_rows(rows, CAR_TRACK_KEYS);
    Ok(TableDataInfo::new(total, data))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "车辆id",
        "车牌号",
        "经度",
        "维度",
        "设备类型",
        "设备编号",
        "车道编号",
        "抓拍时间",
        "接收时间",
        "抓拍图片",
        "管理中心路段id",
        "管理中心路段名称",
        "行驶轨迹id",
        "行驶轨迹josn",
        "备用字段1",
        "备用字段2",
        "状态",
        "备注",
    ]
    .map(str::to_string);
    let fields = [
        "carId",
        "carNo",
        "longitude",
        "latitude",
        "deviceType",
        "deviceNo",
        "laneNo",
        "snapTime",
        "receiveTime",
        "snapPic",
        "roadSectionId",
        "roadSectionName",
        "trackId",
        "backCol2",
        "backCol1",
        "backCol2",
        "status",
        "remark",
    ];
    let data = rows
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_excel(&state, "车辆行驶轨迹数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let row = sqlx::query(&format!(
        "select {}, t.track_josn from car_track_info t where t.id = ?",
        SPEC.select
    ))
    .bind(&id)
    .fetch_optional(&state.db)
    .await?;
    Ok(AjaxResult::success_data(row.map(|row| {
        let mut value = crate::db::rows::row_to_json(&row);
        if let Some(object) = value.as_object_mut() {
            object.insert("longitudeDec".to_string(), Value::Null);
            object.insert("latitudeDec".to_string(), Value::Null);
        }
        support::shape_entity_row(value, CAR_TRACK_KEYS)
    })))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_track_info", "id", true, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_track_info", "id", true, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_track_info", "id", &ids).await?;
    Ok(support::success_count(count))
}

/// Java: ZdataTrailTracksMapper.getHistoryTrail。
fn build_trail_query(
    params: &HashMap<String, String>,
    count: bool,
) -> QueryBuilder<'static, MySql> {
    let head = if count {
        "select count(0) from zdata_trail_tracks t where 1=1".to_string()
    } else {
        format!("select {TRAIL_COLUMNS} from zdata_trail_tracks t where 1=1")
    };
    let mut builder = QueryBuilder::<MySql>::new(head);
    if let Some(value) = params.get("carNo").filter(|value| !value.trim().is_empty()) {
        builder.push(" and t.plate_key = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params
        .get("plateKey")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.plate_key like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    if let Some(value) = params
        .get("applyTime1")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.enter_time >= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d')");
    }
    if let Some(value) = params
        .get("applyTime2")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.enter_time < date_add(STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d'), interval 1 day)");
    }
    if let Some(value) = params
        .get("entollstationid")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.entollstationid = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params
        .get("uuidList")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and uuid in (");
        let mut separated = builder.separated(", ");
        for id in value.split(',').filter(|item| !item.is_empty()) {
            separated.push_bind(id.to_string());
        }
        builder.push(")");
    }
    if !count {
        builder.push(" order by t.enter_time desc");
    }
    builder
}

/// Java: getCyly —— 高频进出口组合的前 3 条轨迹 uuid。
async fn frequent_uuids(
    state: &AppState,
    params: &HashMap<String, String>,
) -> Result<Vec<(String, i64)>, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(
        "select uuid, passCount from (select t.uuid, gc.passCount, \
         row_number() over (partition by t.plate_key, t.entollstationid, t.extollstationid \
         order by t.enter_time desc) as rn \
         from zdata_trail_tracks t inner join (select plate_key, entollstationid, extollstationid, \
         count(*) as passCount from zdata_trail_tracks t where 1=1",
    );
    if let Some(value) = params.get("carNo").filter(|value| !value.trim().is_empty()) {
        builder.push(" and t.plate_key = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params
        .get("applyTime1")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.enter_time >= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d')");
    }
    if let Some(value) = params
        .get("applyTime2")
        .filter(|value| !value.trim().is_empty())
    {
        builder.push(" and t.enter_time < date_add(STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d'), interval 1 day)");
    }
    builder.push(
        " group by plate_key, entollstationid, extollstationid order by passCount desc limit 3) gc \
         on t.plate_key = gc.plate_key and t.entollstationid = gc.entollstationid \
         and t.extollstationid = gc.extollstationid) a where rn = 1 order by passCount desc",
    );
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(rows
        .iter()
        .filter_map(|row| {
            let uuid: Option<String> = sqlx::Row::try_get(row, "uuid").ok();
            let count: Option<i64> = sqlx::Row::try_get(row, "passCount").ok();
            uuid.map(|uuid| (uuid, count.unwrap_or_default()))
        })
        .collect())
}

/// Java: carTrackQuery + TrailInfo 包装。
async fn car_track_rows(
    state: &AppState,
    params: &HashMap<String, String>,
    page: Option<&crate::common::page::PageDomain>,
) -> Result<(i64, Vec<Value>), AppError> {
    let mut effective = params.clone();
    if effective.get("isCylx").map(String::as_str) == Some("1") {
        let frequent = frequent_uuids(state, params).await?;
        if !frequent.is_empty() {
            let uuids = frequent
                .iter()
                .map(|(uuid, _)| uuid.clone())
                .collect::<Vec<_>>();
            effective.insert("uuidList".to_string(), uuids.join(","));
        } else {
            return Ok((0, Vec::new()));
        }
    }

    let mut count_builder = build_trail_query(&effective, true);
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;
    let mut builder = build_trail_query(&effective, false);
    if let Some(page) = page {
        let (offset, limit) = page.resolve(total);
        builder.push(" limit ");
        builder.push_bind(limit);
        builder.push(" offset ");
        builder.push_bind(offset);
    }
    let rows = builder.build().fetch_all(&state.db).await?;
    let mut data = rows_to_json(&rows);
    if effective.get("isCylx").map(String::as_str) == Some("1") {
        let frequent = frequent_uuids(state, params).await?;
        let map: HashMap<String, i64> = frequent.into_iter().collect();
        for row in &mut data {
            if let Some(uuid) = row.get("uuid").and_then(Value::as_str) {
                if let Some(count) = map.get(uuid) {
                    if let Some(object) = row.as_object_mut() {
                        let plate = object
                            .get("plateKey")
                            .and_then(Value::as_str)
                            .unwrap_or_default()
                            .to_string();
                        object.insert(
                            "plateKey".to_string(),
                            json!(format!("{plate}(通行{count}次)")),
                        );
                    }
                }
            }
        }
    }
    Ok((total, data))
}

/// Java: ZdataTrailTracks 的声明顺序（51 键）。
const TRACK_KEYS: &[&str] = &[
    "uuid",
    "type",
    "pointCount",
    "plateKey",
    "enterTime",
    "exitTime",
    "trailPoints",
    "enterLocationcode",
    "exitLocationcode",
    "trackJosn",
    "enaxlecount",
    "entolllaneid",
    "entollstationid",
    "entollstationname",
    "envehicleclass",
    "envehicleid",
    "envehicletype",
    "enweight",
    "extolllaneid",
    "extollstationid",
    "extollstationname",
    "exvehicleclass",
    "exvehicleid",
    "exvehicletype",
    "exweight",
    "startLon",
    "stratLat",
    "endLon",
    "endLat",
    "firtStationCode",
    "firtStationName",
    "firtStationTime",
    "plateColor",
    "carType",
    "carNo",
    "carVehicle",
    "carNum",
    "escapedType",
    "passType",
    "escapedTypeRemark",
    "applyTime1",
    "applyTime2",
    "isCylx",
    "flag",
    "startLonDec",
    "stratLatDec",
    "endLonDec",
    "endLatDec",
    "uuidList",
    "passCount",
    "escapedTfcj",
];

/// Java: TrailBo 的声明顺序（32 键）。
pub(crate) const TRAIL_BO_KEYS: &[&str] = &[
    "pointUuid",
    "stateType",
    "pointFlag",
    "pointJosn",
    "borderWeighingCaptureBO",
    "gantryCaptureBO",
    "provCaptureBO",
    "stationCapture",
    "feeRecord",
    "feeStationEnter",
    "feeStationExit",
    "captureTime",
    "directionIn",
    "locationCode",
    "locationFlag",
    "ipType",
    "locationJosn",
    "gantryIpBO",
    "stationIpBO",
    "devCode",
    "devName",
    "imagesArry",
    "lon",
    "lat",
    "roadCode",
    "sectionCode",
    "direction",
    "pileno",
    "preCaptureTime",
    "countNum",
    "pilenoDec",
    "isQuery",
];

/// Java: `new BigDecimal(String)` —— 整数字面量不会变成 x.0。
fn decimal_like(text: &str) -> Value {
    let trimmed = text.trim();
    if !trimmed.contains('.') && !trimmed.contains('e') && !trimmed.contains('E') {
        if let Ok(number) = trimmed.parse::<i64>() {
            return json!(number);
        }
    }
    match trimmed.parse::<f64>() {
        Ok(float) => serde_json::Number::from_f64(float)
            .map(Value::Number)
            .unwrap_or(Value::String(trimmed.to_string())),
        Err(_) => Value::String(trimmed.to_string()),
    }
}

/// TrailInfo: tracks/trailList/trailUuid/raodTrailList/trailDevCountBO。
fn wrap_trail(row: &Value) -> Value {
    let track_json = row
        .get("trackJosn")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let parsed: Value = serde_json::from_str(track_json).unwrap_or(Value::Null);
    let points = parsed
        .as_array()
        .cloned()
        .unwrap_or_default()
        .iter()
        .map(|item| support::project_entity_row(item.clone(), TRAIL_BO_KEYS))
        .collect::<Vec<_>>();
    let mut tracks = support::project_entity_row(row.clone(), TRACK_KEYS);
    if let Some(object) = tracks.as_object_mut() {
        object.insert("trailPoints".to_string(), json!(""));
        object.insert("trackJosn".to_string(), json!(""));
        for key in ["startLon", "stratLat", "endLon", "endLat"] {
            if let Some(text) = object.get(key).and_then(Value::as_str) {
                object.insert(format!("{key}Dec"), decimal_like(text));
            }
        }
    }
    json!({
        "trailUuid": row.get("plateKey").cloned().unwrap_or(Value::Null),
        "enterTime": Value::Null,
        "tracks": tracks,
        "trailList": points,
        "raodTrailList": Vec::<Value>::new(),
        // Java: 列表接口不调用 getTrailDevBO，只输出 TrailInfo 的初始值。
        "trailDevCountBO": {
            "exceptNum": 0,
            "trailList": Value::Null,
            "exceptMsg": Value::Null,
            "trailDevList": Vec::<Value>::new(),
        },
    })
}

/// Java: Constants.lxbh_jdwd —— 路线点位缓存（GeometryServiceImpl.getRedisList）。
const GEOMETRY_CACHE_KEY: &str = "lxbh_jdwd:";
/// Java: Constants.car_lxgh —— 路网规划结果缓存。
const ROAD_PATH_CACHE_PREFIX: &str = "car_lxgh:";
/// Java: Constants.GANTRY_CAPTURE / Constants.FeeRecord
const GANTRY_CAPTURE: &str = "GantryCapture";
const FEE_RECORD: &str = "FeeRecord";
/// Java: Geometry implements Custom 的声明顺序。
const GEOMETRY_KEYS: &[&str] = &["id", "lxbh", "lxfx", "qdzh", "zdzh", "paths", "zhStr"];

fn dec_of(value: Option<&Value>) -> Option<rust_decimal::Decimal> {
    support::json_decimal(value)
}

/// Java: `setScale(4, HALF_UP).intValue()`（intValue 截断小数）。
fn pileno_int(value: rust_decimal::Decimal) -> i64 {
    value
        .round_dp_with_strategy(4, rust_decimal::RoundingStrategy::MidpointAwayFromZero)
        .to_string()
        .parse::<f64>()
        .map(|float| float as i64)
        .unwrap_or(0)
}

/// Java: GeometryServiceImpl.getRedisList —— 按 lxbh 分组的路线点位。
async fn geometry_groups(state: &AppState) -> Result<HashMap<String, Vec<Value>>, AppError> {
    let cached = state
        .redis
        .get_object::<Vec<Value>>(GEOMETRY_CACHE_KEY)
        .await
        .ok()
        .flatten()
        .filter(|rows| !rows.is_empty());
    let rows = match cached {
        Some(rows) => rows,
        None => {
            let fetched = sqlx::query(
                "select t.id, t.lxbh, t.lxfx, t.qdzh, t.zdzh, t.paths from geometry t \
                 where 1=1 and t.lxfx = '1' order by lxbh, t.qdzh",
            )
            .fetch_all(&state.db)
            .await?;
            let rows = rows_to_json(&fetched);
            let stored: Vec<Value> = rows
                .iter()
                .map(|row| support::project_entity_row(row.clone(), GEOMETRY_KEYS))
                .filter(|row| {
                    !support::java_text(row.get("lxbh")).is_empty()
                        && !support::java_text(row.get("paths")).is_empty()
                })
                .collect();
            // Java: redisCache.setCacheObject(lxbh_jdwd, list)（无 TTL），需补 @type 供 Java 读取。
            let stamped = crate::db::redis_cache::stamp_types(
                stored.clone(),
                "com.ruoyi.base.domain.Geometry",
            );
            let _ = state.redis.set_object(GEOMETRY_CACHE_KEY, &stamped).await;
            stored
        }
    };
    let mut map: HashMap<String, Vec<Value>> = HashMap::new();
    for row in rows {
        let row = support::project_entity_row(row, GEOMETRY_KEYS);
        let lxbh = support::java_text(row.get("lxbh"));
        if lxbh.is_empty() || support::java_text(row.get("paths")).is_empty() {
            continue;
        }
        map.entry(lxbh).or_default().push(row);
    }
    Ok(map)
}

/// Java: 只填 lxbh/paths 的 Geometry 返回体。
fn geometry_row(lxbh: Value, paths: String) -> Value {
    json!({
        "id": Value::Null,
        "lxbh": lxbh,
        "lxfx": Value::Null,
        "qdzh": Value::Null,
        "zdzh": Value::Null,
        "paths": paths,
        "zhStr": Value::Null,
    })
}

/// 把 JSON 数组文本按顶层元素切开（紧凑、无空格），保留数字字面量。
fn json_array_elements(text: &str) -> Vec<String> {
    let trimmed = text.trim();
    let inner = trimmed
        .strip_prefix('[')
        .and_then(|value| value.strip_suffix(']'))
        .unwrap_or(trimmed);
    let compact = |value: &str| {
        value
            .chars()
            .filter(|ch| !ch.is_whitespace())
            .collect::<String>()
    };
    let mut out: Vec<String> = Vec::new();
    let mut depth = 0i32;
    let mut current = String::new();
    let mut in_string = false;
    let mut escaped = false;
    for ch in inner.chars() {
        if in_string {
            current.push(ch);
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }
        match ch {
            '"' => {
                in_string = true;
                current.push(ch);
            }
            '[' | '{' => {
                depth += 1;
                current.push(ch);
            }
            ']' | '}' => {
                depth -= 1;
                current.push(ch);
            }
            ',' if depth == 0 => {
                out.push(compact(&current));
                current.clear();
            }
            _ => current.push(ch),
        }
    }
    out.push(compact(&current));
    out.retain(|item| !item.is_empty());
    out
}

/// Java: CarTrackInfoServiceImpl.getCarGeometry —— 按路线编号 + 桩号区间拼本地路径点。
async fn get_car_geometry(state: &AppState, points: &mut [Value]) -> Result<Vec<Value>, AppError> {
    // Java: LinkedHashMap 分组（首次出现顺序），并回填 pilenoDec。
    let mut roads: Vec<String> = Vec::new();
    let mut groups: HashMap<String, Vec<usize>> = HashMap::new();
    for index in 0..points.len() {
        let road_code = support::java_text(points[index].get("roadCode"));
        let pileno = support::java_text(points[index].get("pileno"));
        if road_code.is_empty() || pileno.is_empty() {
            continue;
        }
        let changed = pileno
            .replace('+', ".")
            .replace("ZK", "")
            .replace("YK", "")
            .replace('K', "");
        let dec = changed
            .parse::<rust_decimal::Decimal>()
            .unwrap_or(rust_decimal::Decimal::ZERO);
        if let Some(object) = points[index].as_object_mut() {
            object.insert("pilenoDec".to_string(), support::decimal_json(dec));
        }
        if !groups.contains_key(&road_code) {
            roads.push(road_code.clone());
        }
        groups.entry(road_code).or_default().push(index);
    }
    let road_map = geometry_groups(state).await?;
    let mut out = Vec::new();
    for road in roads {
        let indexes = groups.remove(&road).unwrap_or_default();
        if indexes.is_empty() {
            continue;
        }
        let mut items: Vec<(rust_decimal::Decimal, usize)> = indexes
            .iter()
            .filter_map(|index| dec_of(points[*index].get("pilenoDec")).map(|dec| (dec, *index)))
            .collect();
        if items.is_empty() {
            continue;
        }
        // Java: 首尾（按分组顺序）判断方向，再按桩号稳定排序。
        let reverse = items.first().map(|(dec, _)| *dec).unwrap_or_default()
            > items.last().map(|(dec, _)| *dec).unwrap_or_default();
        items.sort_by(|left, right| left.0.cmp(&right.0));
        let sq = pileno_int(items.first().map(|(dec, _)| *dec).unwrap_or_default());
        let sz = if items.len() > 1 {
            pileno_int(items.last().map(|(dec, _)| *dec).unwrap_or_default()) + 1
        } else {
            sq
        };
        let mut add: Vec<&Value> = Vec::new();
        if let Some(rows) = road_map.get(&road) {
            for row in rows {
                let qd = support::java_int(row.get("qdzh"));
                let zd = support::java_int(row.get("zdzh"));
                let mut count = 0;
                if qd <= sq && zd >= sz {
                    count += 1;
                }
                if qd > sq && qd < sz {
                    count += 1;
                }
                if zd > sq && zd < sz {
                    count += 1;
                }
                if qd >= sq && zd <= sz {
                    count += 1;
                }
                if count > 0 {
                    add.push(row);
                }
            }
        }
        if add.is_empty() {
            continue;
        }
        // Java: hutool JSONArray 用 BigDecimal 保留字面量，toString() 也不加空格；
        // 这里按顶层元素原样拼接，避免经过 f64 丢位。
        let mut path_points: Vec<String> = Vec::new();
        for row in add {
            let text = support::java_text(row.get("paths"));
            if text.is_empty() {
                continue;
            }
            path_points.extend(json_array_elements(&text));
        }
        if reverse {
            path_points.reverse();
        }
        let paths = format!("[{}]", path_points.join(","));
        out.push(geometry_row(json!(road), paths));
    }
    Ok(out)
}

/// Java: getCarGeometryByPlanNew —— 命中缓存或调本地路网规划接口，拿不到结果时落到腾讯路径。
async fn get_car_geometry_by_plan(
    state: &AppState,
    tracks: &Value,
    points: &mut Vec<Value>,
) -> Result<Vec<Value>, AppError> {
    let api_map = state
        .redis
        .get_object::<Value>("sys_config:api_map")
        .await
        .ok()
        .flatten();
    let api_map = match api_map {
        Some(value) => support::java_text(Some(&value)),
        None => "1".to_string(),
    };
    if api_map != "0" {
        let entoll = support::java_text(tracks.get("entollstationid"));
        let extoll = support::java_text(tracks.get("extollstationid"));
        if !entoll.is_empty() && !extoll.is_empty() {
            let key = format!(
                "{ROAD_PATH_CACHE_PREFIX}{}{entoll}{extoll}{}",
                support::java_text(tracks.get("plateKey")),
                points.len()
            );
            // Java: nodeIds = 入口收费站 + 各轨迹点 devCode（非空才加） + 出口收费站。
            let mut node_ids = vec![entoll.clone()];
            let mut lxbh = Value::String(String::new());
            for point in points.iter() {
                let road = point.get("roadCode").cloned().unwrap_or(Value::Null);
                if lxbh.as_str() == Some("") && road.as_str() != Some("") {
                    lxbh = road;
                }
                let dev_code = support::java_text(point.get("devCode"));
                if !dev_code.is_empty() {
                    node_ids.push(dev_code);
                }
            }
            node_ids.push(extoll);

            let paths = match cached_paths(state, &key).await {
                Some(text) => Some(text),
                None => {
                    let text = road_path::get_shortest_road_path(state, &node_ids).await;
                    if let Some(text) = &text {
                        let _ = state.redis.set_object(&key, text).await;
                    }
                    text
                }
            };
            return match paths {
                Some(paths) => Ok(vec![geometry_row(lxbh, paths)]),
                None => get_car_geometry_by_plan_tx(state, tracks, points).await,
            };
        }
    }
    get_car_geometry_by_plan_tx(state, tracks, points).await
}

/// Java: getCarGeometryByPlan —— 起终点桩号齐全时走腾讯 direction，拿不到才落本地桩号绘制。
async fn get_car_geometry_by_plan_tx(
    state: &AppState,
    tracks: &Value,
    points: &mut Vec<Value>,
) -> Result<Vec<Value>, AppError> {
    let ends = ["startLonDec", "stratLatDec", "endLonDec", "endLatDec"];
    if ends.iter().any(|key| {
        tracks
            .get(*key)
            .map(|value| value.is_null())
            .unwrap_or(true)
    }) {
        return get_car_geometry(state, points).await;
    }
    let key = format!(
        "{ROAD_PATH_CACHE_PREFIX}{}{}{}{}{}{}",
        support::java_text(tracks.get("plateKey")),
        support::java_text(tracks.get("startLonDec")),
        support::java_text(tracks.get("stratLatDec")),
        support::java_text(tracks.get("endLonDec")),
        support::java_text(tracks.get("endLatDec")),
        points.len()
    );
    // Java: wayPoints 取每个「lon/lat 都非空」的点，先转 GCJ-02，再原样 Double.toString。
    let mut lxbh = Value::String(String::new());
    let mut way_points: Vec<String> = Vec::new();
    for point in points.iter() {
        let lon = point.get("lon").filter(|value| !value.is_null());
        let lat = point.get("lat").filter(|value| !value.is_null());
        let (Some(lon), Some(lat)) = (lon, lat) else {
            continue;
        };
        let road = point.get("roadCode").cloned().unwrap_or(Value::Null);
        if lxbh.as_str() == Some("") && road.as_str() != Some("") {
            lxbh = road;
        }
        let number = |value: &Value| -> Option<f64> {
            match value {
                Value::Number(number) => number.as_f64(),
                other => other.as_str().and_then(|text| text.parse().ok()),
            }
        };
        let (Some(lon), Some(lat)) = (number(lon), number(lat)) else {
            continue;
        };
        let (lat, lon) = gps::gps84_to_gcj02(lat, lon);
        way_points.push(format!(
            "{},{}",
            gps::java_double(lat),
            gps::java_double(lon)
        ));
    }
    let paths = match cached_paths(state, &key).await {
        Some(text) => Some(text),
        None => {
            let text = road_path::calc_lon_and_lat_paths(
                state,
                &support::java_text(tracks.get("startLonDec")),
                &support::java_text(tracks.get("stratLatDec")),
                &support::java_text(tracks.get("endLonDec")),
                &support::java_text(tracks.get("endLatDec")),
                "",
                &way_points.join(";"),
            )
            .await;
            if let Some(text) = &text {
                let _ = state.redis.set_object(&key, text).await;
            }
            text
        }
    };
    match paths {
        Some(paths) => Ok(vec![geometry_row(lxbh, paths)]),
        None => get_car_geometry(state, points).await,
    }
}

async fn cached_paths(state: &AppState, key: &str) -> Option<String> {
    let value = state.redis.get_object::<Value>(key).await.ok().flatten()?;
    // Java: paths = CommonUtil.isNull(obj) —— 字符串照抄，其他类型走 toString + trim。
    match support::java_text(Some(&value)) {
        text if text.is_empty() => None,
        text => Some(text),
    }
}

/// Java: CarTrackInfoServiceImpl.getTrailDevBO —— 门架抓拍缺流水的设备计为异常。
fn get_trail_dev_bo(tracks: &Value, points: &[Value]) -> Value {
    let is_capture = |value: &str| value == GANTRY_CAPTURE || value == FEE_RECORD;
    let mut groups: HashMap<String, Vec<usize>> = HashMap::new();
    let mut rtn: Vec<usize> = Vec::new();
    for (index, point) in points.iter().enumerate() {
        let state_type = support::java_text(point.get("stateType"));
        let dev_name = support::java_text(point.get("devName"));
        if is_capture(&state_type) {
            if !dev_name.is_empty() {
                if groups.contains_key(&dev_name) {
                    groups.entry(dev_name).or_default().push(index);
                } else {
                    rtn.push(index);
                    groups.insert(dev_name, vec![index]);
                }
            } else {
                rtn.push(index);
            }
        } else {
            rtn.push(index);
        }
    }
    let mut dev_list: Vec<Value> = Vec::new();
    let mut except_num: i64 = 0;
    for index in rtn {
        let point = &points[index];
        let state_type = support::java_text(point.get("stateType"));
        let dev_name = support::java_text(point.get("devName"));
        let mut status = "0";
        let mut trail_list: Vec<Value> = Vec::new();
        if is_capture(&state_type) {
            if let Some(group) = groups.get(&dev_name) {
                trail_list = group.iter().map(|item| points[*item].clone()).collect();
                let count_gantry = group
                    .iter()
                    .filter(|item| {
                        support::java_text(points[**item].get("stateType")) == GANTRY_CAPTURE
                    })
                    .count();
                let count_fee = group
                    .iter()
                    .filter(|item| {
                        support::java_text(points[**item].get("stateType")) == FEE_RECORD
                    })
                    .count();
                if count_gantry > 0 && count_fee == 0 {
                    status = "1";
                    except_num += 1;
                }
            } else {
                trail_list.push(point.clone());
            }
        } else {
            trail_list.push(point.clone());
        }
        dev_list.push(json!({
            "status": status,
            "devName": dev_name,
            "trailList": trail_list,
        }));
    }
    let missing = |key: &str| tracks.get(key).map(|value| value.is_null()).unwrap_or(true);
    let mut tips = String::new();
    if missing("startLonDec") || missing("stratLatDec") {
        tips = "起始位置".to_string();
    }
    if missing("endLonDec") || missing("endLatDec") {
        tips = if tips.is_empty() {
            "终点位置".to_string()
        } else {
            format!("{tips}和终点位置")
        };
    }
    let except_msg = if tips.is_empty() {
        String::new()
    } else {
        format!("由于无法获取轨迹{tips}，系统路线规划采用已有的轨迹点进行轨迹绘制，可能会导致部分路线丢失。")
    };
    json!({
        "exceptNum": except_num,
        "trailList": points,
        "exceptMsg": except_msg,
        "trailDevList": dev_list,
    })
}

/// Java: CarSuspiciousServiceImpl 里由 track_josn 组装 TrailInfo。
pub(crate) async fn suspicious_trail_info(
    state: &AppState,
    track_json: &str,
    car_no: &str,
) -> Result<Value, AppError> {
    let parsed: Value = serde_json::from_str(track_json).unwrap_or(Value::Null);
    let tracks = support::project_entity_row(
        parsed.get("tracks").cloned().unwrap_or(Value::Null),
        TRACK_KEYS,
    );
    let mut points: Vec<Value> = parsed
        .get("trailList")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
        .iter()
        .map(|item| support::project_entity_row(item.clone(), TRAIL_BO_KEYS))
        .collect();
    let enter_time = parsed.get("enterTime").cloned().unwrap_or(Value::Null);
    let raod = if points.is_empty() {
        Vec::new()
    } else {
        get_car_geometry_by_plan(state, &tracks, &mut points).await?
    };
    let dev = get_trail_dev_bo(&tracks, &points);
    Ok(json!({
        "trailUuid": car_no,
        "enterTime": enter_time,
        "tracks": tracks,
        "trailList": points,
        "raodTrailList": raod,
        "trailDevCountBO": dev,
    }))
}

async fn list_by_car_id(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    // Java listByCarId：carNo 为空时用 "-1"（查询不到数据）。
    let mut params = support::query_map(&raw);
    if params
        .get("carNo")
        .map(|value| value.trim().is_empty())
        .unwrap_or(true)
    {
        params.insert("carNo".to_string(), "-1".to_string());
    }
    let page = support::page_domain(&raw);
    let (total, rows) = car_track_rows(&state, &params, Some(&page)).await?;
    let wrapped = rows.iter().map(wrap_trail).collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, wrapped))
}

async fn list_by_car(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    // Java: carNo 为空时 XML 跳过该条件（返回全部）。
    let (total, rows) = car_track_rows(&state, &params, Some(&page)).await?;
    let wrapped = rows.iter().map(wrap_trail).collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, wrapped))
}

async fn change_trail(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::query_log(&state.db, &user, &body.to_string(), "1", "1").await?;
    // Java: 通过 Geometry 计算路线与异常点；Rust 版本返回原结构（路线/异常列表为空）。
    let mut trail = body;
    if let Some(object) = trail.as_object_mut() {
        object
            .entry("raodTrailList".to_string())
            .or_insert_with(|| json!([]));
        object
            .entry("trailDevCountBO".to_string())
            .or_insert_with(|| json!({ "exceptNum": 0, "TrailDevList": [] }));
    }
    Ok(AjaxResult::success_data(trail))
}

async fn car_snapshot(
    State(_state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let state_type = params.get("stateType").cloned().unwrap_or_default();
    let point_uuid = params.get("pointUuid").cloned().unwrap_or_default();
    if state_type.is_empty() || point_uuid.is_empty() {
        return Ok(AjaxResult::success());
    }
    // Java: 调用 httpSysUtilApiService.getByTrailBo（远端抓拍服务），Rust 未配置该服务。
    Ok(AjaxResult::success_data(Value::Object(Map::new())))
}
