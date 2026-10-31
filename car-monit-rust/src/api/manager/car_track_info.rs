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
use crate::db::rows::rows_to_json;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.car_id, t.car_no, t.longitude, t.latitude, t.device_type, t.device_no, \
             t.lane_no, t.snap_time, t.receive_time, t.snap_pic, t.road_section_id, \
             t.road_section_name, t.track_id, t.back_col1, t.back_col2, t.remark, t.status, \
             t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, \
             t.update_time, t.tenant_id",
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
    extra_where: "",
    order_by: "t.create_time, t.id",
    id_column: "t.id",
};

const TRAIL_COLUMNS: &str = "t.uuid, t.type, t.point_count, t.plate_key, t.enter_time, \
     t.exit_time, t.trail_points, t.create_time, t.enter_locationcode, t.exit_locationcode, \
     t.track_josn, t.enaxlecount, t.entolllaneid, t.entollstationid, t.entollstationname, \
     t.envehicleclass, t.envehicleid, t.envehicletype, t.enweight, t.extolllaneid, \
     t.extollstationid, t.extollstationname, t.exvehicleclass, t.exvehicleid, t.exvehicletype, \
     t.exweight, t.start_lon, t.strat_lat, t.end_lon, t.end_lat";

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
                list_by_car,
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
            meta::get_route("/manager/cartrackinfo/carSnapShot", None, None, car_snapshot),
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

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "车辆id", "车牌号", "经度", "维度", "设备类型", "设备编号", "车道编号", "抓拍时间",
        "接收时间", "抓拍图片", "管理中心路段id", "管理中心路段名称", "行驶轨迹id",
        "行驶轨迹josn", "备用字段1", "备用字段2", "状态", "备注",
    ]
    .map(str::to_string);
    let fields = [
        "carId", "carNo", "longitude", "latitude", "deviceType", "deviceNo", "laneNo",
        "snapTime", "receiveTime", "snapPic", "roadSectionId", "roadSectionName", "trackId",
        "backCol2", "backCol1", "backCol2", "status", "remark",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
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
    Ok(AjaxResult::success_data(
        row.map(|row| crate::db::rows::row_to_json(&row)),
    ))
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
    if let Some(value) = params.get("plateKey").filter(|value| !value.trim().is_empty()) {
        builder.push(" and t.plate_key like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    if let Some(value) = params.get("applyTime1").filter(|value| !value.trim().is_empty()) {
        builder.push(" and t.enter_time >= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d')");
    }
    if let Some(value) = params.get("applyTime2").filter(|value| !value.trim().is_empty()) {
        builder.push(" and t.enter_time < date_add(STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d'), interval 1 day)");
    }
    if let Some(value) = params.get("entollstationid").filter(|value| !value.trim().is_empty()) {
        builder.push(" and t.entollstationid = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params.get("uuidList").filter(|value| !value.trim().is_empty()) {
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
    if let Some(value) = params.get("applyTime1").filter(|value| !value.trim().is_empty()) {
        builder.push(" and t.enter_time >= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d')");
    }
    if let Some(value) = params.get("applyTime2").filter(|value| !value.trim().is_empty()) {
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
    let total: i64 = count_builder.build_query_scalar().fetch_one(&state.db).await?;
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
                        object.insert("plateKey".to_string(), json!(format!("{plate}(通行{count}次)")));
                    }
                }
            }
        }
    }
    Ok((total, data))
}

/// TrailInfo: tracks/trailList/trailUuid/raodTrailList/trailDevCountBO。
fn wrap_trail(row: &Value) -> Value {
    let track_json = row.get("trackJosn").and_then(Value::as_str).unwrap_or_default();
    let trail_list: Vec<Value> = serde_json::from_str(track_json).unwrap_or_default();
    let mut tracks = row.clone();
    if let Some(object) = tracks.as_object_mut() {
        object.insert("trailPoints".to_string(), json!(""));
        object.insert("trackJosn".to_string(), json!(""));
        for key in ["startLon", "stratLat", "endLon", "endLat"] {
            if let Some(text) = object.get(key).and_then(Value::as_str) {
                if let Ok(number) = text.parse::<f64>() {
                    object.insert(format!("{key}Dec"), json!(number));
                }
            }
        }
    }
    json!({
        "trailUuid": row.get("plateKey").cloned().unwrap_or(Value::Null),
        "tracks": tracks,
        "trailList": trail_list,
        "raodTrailList": Vec::<Value>::new(),
        "trailDevCountBO": {
            "exceptNum": 0,
            "TrailDevList": Vec::<Value>::new(),
        },
    })
}

async fn list_by_car(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    // Java: carNo 为空时用 "-1"。
    params
        .entry("carNo".to_string())
        .or_insert_with(|| "-1".to_string());
    if params.get("carNo").map(String::as_str) == Some("") {
        params.insert("carNo".to_string(), "-1".to_string());
    }
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
        object.entry("trailDevCountBO".to_string()).or_insert_with(|| {
            json!({ "exceptNum": 0, "TrailDevList": [] })
        });
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
