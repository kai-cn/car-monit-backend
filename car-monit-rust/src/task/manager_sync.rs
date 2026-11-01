// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/{VehicleMonitoringTask,OrgTask,TrackTask}.java
//       ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/{CarTrackInfoServiceImpl,CarSuspiciousServiceImpl,CarExceptRecordServiceImpl}.java
//       ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpBaseInfoApiService.java
// 职责: sys_job 里的基础信息同步、车辆实时/历史轨迹、可疑车辆迁移、逃费金额回写。
// 对应关系: Forest HttpBaseInfoApiService -> task::remote::get_json_owned；
//           Redis 轨迹缓存（car_curent_trail/car_history_trail/car_uspicious）由外部采集服务写入。

use chrono::NaiveDateTime;
use serde_json::{json, Map, Value};

use crate::api::support;
use crate::db::redis_cache::stamp_types;
use crate::error::AppError;
use crate::state::AppState;
use crate::task::remote;

const CAR_LIST_KEY: &str = "car_list";
const CAR_CURRENT_TRAIL: &str = "car_curent_trail:";
const CAR_HISTORY_TRAIL: &str = "car_history_trail:";
const WARNING_CONFIG_LIST: &str = "car_warning_config_list";
const WARNING_LIST: &str = "car_warning_list";
const SECTION_LIST: &str = "section_list";

const BORDER_WEIGHING_CAPTURE: &str = "BorderWeighingCapture";
const GANTRY_CAPTURE: &str = "GantryCapture";
const PROV_CAPTURE: &str = "ProvCapture";
const SERVICE_AREA_CAPTURE: &str = "ServiceAreaCapture";
const STATION_CAPTURE: &str = "StationCapture";

fn text(row: &Value, key: &str) -> String {
    match row.get(key) {
        Some(Value::String(value)) => value.clone(),
        Some(Value::Null) | None => String::new(),
        Some(other) => other.to_string(),
    }
}

fn opt_text(row: &Value, key: &str) -> Option<String> {
    match row.get(key) {
        Some(Value::String(value)) if !value.is_empty() => Some(value.clone()),
        Some(Value::Number(number)) => Some(number.to_string()),
        _ => None,
    }
}

fn number(row: &Value, key: &str) -> Option<i64> {
    row.get(key).and_then(|value| match value {
        Value::Number(number) => number.as_i64(),
        Value::String(text) => text.parse().ok(),
        _ => None,
    })
}

fn is_blank(value: &str) -> bool {
    value.trim().is_empty()
}

fn now() -> NaiveDateTime {
    chrono::Local::now().naive_local()
}

fn now_text() -> String {
    now().format("%Y-%m-%d %H:%M:%S").to_string()
}

fn parse_dt(value: &str) -> Option<NaiveDateTime> {
    NaiveDateTime::parse_from_str(value.trim(), "%Y-%m-%d %H:%M:%S").ok()
}

// ==================== 远端基础信息同步 ====================

async fn fetch_list(state: &AppState, path: &str) -> Result<Vec<Value>, AppError> {
    let value = remote::get_json_owned(state, path, &[]).await?;
    Ok(match value {
        Value::Array(items) => items,
        Value::Object(object) => object
            .get("data")
            .or_else(|| object.get("rows"))
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default(),
        _ => Vec::new(),
    })
}

/// 读取表的真实列名（下划线），用于剔除缓存/远端返回里的非表字段（如 exist=false 字段）。
async fn table_columns(state: &AppState, table: &str) -> Result<std::collections::HashSet<String>, AppError> {
    let rows: Vec<String> = sqlx::query_scalar(
        "select lower(column_name) from information_schema.columns          where table_schema = database() and table_name = ?",
    )
    .bind(table)
    .fetch_all(&state.db)
    .await?;
    Ok(rows.into_iter().collect())
}

fn filter_columns(
    columns: &std::collections::HashSet<String>,
    row: &Value,
) -> Option<Value> {
    let object = row.as_object()?;
    let mut out = Map::new();
    for (key, value) in object {
        if key.starts_with('@') || value.is_null() {
            continue;
        }
        let column = support::column_name(key);
        if columns.contains(&column) {
            out.insert(key.clone(), value.clone());
        }
    }
    (!out.is_empty()).then_some(Value::Object(out))
}

async fn insert_filtered(
    state: &AppState,
    table: &str,
    columns: &std::collections::HashSet<String>,
    row: &Value,
) -> Result<u64, AppError> {
    let Some(entity) = filter_columns(columns, row) else {
        return Ok(0);
    };
    support::insert_entity(&state.db, table, &entity, support::AutoFill::NONE).await
}

async fn replace_table(state: &AppState, table: &str, rows: &[Value]) -> Result<usize, AppError> {
    sqlx::query(&format!("truncate table {table}")).execute(&state.db).await?;
    let columns = table_columns(state, table).await?;
    let mut count = 0;
    for row in rows {
        if insert_filtered(state, table, &columns, row).await? > 0 {
            count += 1;
        }
    }
    Ok(count)
}

pub async fn sync_org(state: &AppState) -> Result<usize, AppError> {
    let rows = fetch_list(state, "/base/org/listAll").await?;
    replace_table(state, "ods_yhgl_v_base_org", &rows).await
}

pub async fn sync_section(state: &AppState) -> Result<usize, AppError> {
    let rows = fetch_list(state, "/base/section/listAll").await?;
    let count = replace_table(state, "ods_szdn_section", &rows).await?;
    // Java: 同步后刷新 section_list 缓存（收费站/门架/收费流水补名称依赖它）。
    // setCacheList 逐元素序列化，FastJson2 WriteClassName 会给每个元素写 @type；
    // 缺少 @type 时 Java getCacheList 得到 JSONObject 并抛 ClassCastException。
    let cached = stamp_types(rows.clone(), "com.ruoyi.base.domain.OdsSzdnSection");
    state.redis.set_list(SECTION_LIST, &cached).await?;
    Ok(count)
}

pub async fn sync_gantry(state: &AppState) -> Result<usize, AppError> {
    let rows = fetch_list(state, "/base/gantry/listAll").await?;
    replace_table(state, "ods_szdn_gantry", &rows).await
}

pub async fn sync_service_area(state: &AppState) -> Result<usize, AppError> {
    let rows = fetch_list(state, "/base/fwqjcxx/listAll").await?;
    replace_table(state, "dwd_lczt_fwqjcxx", &rows).await
}

pub async fn sync_toll_booth(state: &AppState) -> Result<usize, AppError> {
    let rows = fetch_list(state, "/base/sfsjcxx/listAll").await?;
    replace_table(state, "dwd_lczt_sfsjcxx", &rows).await
}

pub async fn sync_sfzjcxx(state: &AppState) -> Result<usize, AppError> {
    let rows = fetch_list(state, "/base/sfzjcxx/listAll").await?;
    replace_table(state, "dwd_lczt_sfzjcxx", &rows).await
}

pub async fn sync_toll_station(state: &AppState) -> Result<usize, AppError> {
    let rows = fetch_list(state, "/base/toll/listAll").await?;
    replace_table(state, "ods_szdn_toll", &rows).await
}

// ==================== 重点车辆列表 ====================

async fn car_list(state: &AppState) -> Result<Vec<Value>, AppError> {
    if let Ok(Some(Value::Array(items))) = state.redis.get_object::<Value>(CAR_LIST_KEY).await {
        return Ok(items);
    }
    let rows = sqlx::query(
        "select id, car_no, car_type, car_vehicle, car_num, plate_color, status, \
         last_pass_longitude, last_pass_latitude, gantry_code, track_josn \
         from car_info where del_flag = '0'",
    )
    .fetch_all(&state.db)
    .await?;
    Ok(crate::db::rows::rows_to_json(&rows))
}

fn car_text(car: &Value, key: &str) -> String {
    text(car, key)
}

// ==================== 历史轨迹 ====================

pub async fn sync_history_track(state: &AppState) -> Result<usize, AppError> {
    let cars = car_list(state).await?;
    let mut car_nos: Vec<String> = Vec::new();
    let mut rows: Vec<Value> = Vec::new();
    for car in &cars {
        let car_no = car_text(car, "carNo");
        if car_no.is_empty() {
            continue;
        }
        let key = format!("{CAR_HISTORY_TRAIL}{car_no}");
        let Some(trails) = state.redis.get_object::<Vec<Value>>(&key).await? else {
            continue;
        };
        for trail in trails {
            let mut tracks = trail.get("tracks").cloned().unwrap_or(Value::Object(Map::new()));
            let trail_list = trail
                .get("trailList")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();
            let Some(object) = tracks.as_object_mut() else { continue };
            object.insert("plateKey".to_string(), json!(car_no));
            object.insert("pointCount".to_string(), json!(trail_list.len() as i64));
            object.insert(
                "trackJosn".to_string(),
                json!(serde_json::to_string(&trail_list).unwrap_or_default()),
            );
            car_nos.push(car_no.clone());
            rows.push(tracks);
        }
    }
    if car_nos.is_empty() {
        return Ok(0);
    }
    let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new(
        "delete from zdata_trail_tracks where plate_key in (",
    );
    let mut separated = builder.separated(", ");
    for car_no in &car_nos {
        separated.push_bind(car_no.clone());
    }
    builder.push(")");
    builder.build().execute(&state.db).await?;

    let columns = table_columns(state, "zdata_trail_tracks").await?;
    let mut count = 0;
    for row in &rows {
        count += insert_filtered(state, "zdata_trail_tracks", &columns, row).await? as usize;
    }
    Ok(count)
}

// ==================== 实时轨迹 ====================

async fn warning_configs(state: &AppState) -> Result<Vec<Value>, AppError> {
    if let Ok(Some(Value::Array(items))) =
        state.redis.get_object::<Value>(WARNING_CONFIG_LIST).await
    {
        return Ok(items);
    }
    // Java: CarWarningConfigMapper.xml#selectCarWarningConfigList
    let rows = sqlx::query(
        "select t.id, t.gantry_code_in, t.gantry_name_in, t.gantry_code_out, t.gantry_name_out, \
         t.time_span, t.remark, t.fwqbm, t1.fwqmc, t1.lon, t1.lat, t1.road_code, \
         t1.section_code, t1.pile_no \
         from car_warning_config t join base_config_service_area t1 on t.fwqbm = t1.fwqbm",
    )
    .fetch_all(&state.db)
    .await?;
    let values = stamp_types(
        crate::db::rows::rows_to_json(&rows),
        "com.ruoyi.base.domain.CarWarningConfig",
    );
    state
        .redis
        .set_object(WARNING_CONFIG_LIST, &values)
        .await?;
    Ok(values)
}

async fn sync_current_time_hours(state: &AppState) -> i64 {
    if let Ok(Some(value)) = state
        .redis
        .get_object::<Value>("sys_config:sync_current_time")
        .await
    {
        let text_value = match value {
            Value::String(text) => text,
            other => other.to_string(),
        };
        if let Ok(hours) = text_value.parse::<i64>() {
            return hours;
        }
    }
    12
}

/// Java: CarTrackInfoServiceImpl.syncCurrentTrack —— 读取外部采集写入的实时轨迹并落库/生成预警。
pub async fn sync_current_track(state: &AppState) -> Result<(), AppError> {
    let cars = car_list(state).await?;
    let configs = warning_configs(state).await?;
    let config_map: std::collections::HashMap<String, Value> = configs
        .into_iter()
        .filter_map(|config| {
            let code = text(&config, "gantryCodeIn");
            (!code.is_empty()).then_some((code, config))
        })
        .collect();
    let is_local = state.settings.is_localhost == "local";
    let sync_hours = sync_current_time_hours(state).await;

    let mut delete_track_ids: Vec<String> = Vec::new();
    let mut add_warnings: Vec<Value> = Vec::new();

    for car in &cars {
        let car_no = car_text(car, "carNo");
        let car_id = car.get("id").cloned().unwrap_or(Value::Null);
        let mut status = "0".to_string();
        let mut last_lon: Option<String> = None;
        let mut last_lat: Option<String> = None;
        let mut last_type: Option<String> = None;
        let mut track_json: Option<String> = None;
        let mut gantry_code: Option<String> = None;

        if !car_no.is_empty() {
            let key = format!("{CAR_CURRENT_TRAIL}{car_no}");
            if let Some(trail) = state.redis.get_object::<Value>(&key).await? {
                let mut trail_list = trail
                    .get("trailList")
                    .and_then(Value::as_array)
                    .cloned()
                    .unwrap_or_default();
                if !trail_list.is_empty() {
                    let trail_exits = trail_list.iter().any(|point| {
                        point.get("lon").map(|v| !v.is_null()).unwrap_or(false)
                            && point.get("lat").map(|v| !v.is_null()).unwrap_or(false)
                    });
                    let capture_last = trail_list
                        .iter()
                        .rev()
                        .map(|point| text(point, "captureTime"))
                        .find(|value| !is_blank(value))
                        .unwrap_or_default();
                    let mut is_exit = true;
                    if let Some(capture) = parse_dt(&capture_last) {
                        let diff = (now() - capture).num_minutes().abs();
                        if diff < sync_hours * 60 {
                            is_exit = false;
                        }
                    }

                    if is_exit && !is_local {
                        // 已驶出且非本地：保持 status=0。
                    } else if trail_exits {
                        // 服务区停留：最后一个设备命中配置且超时，补一个服务区抓拍点。
                        if let Some(last_point) = trail_list.last() {
                            let dev_code = text(last_point, "devCode");
                            let capture = text(last_point, "captureTime");
                            if !dev_code.is_empty() && !capture.is_empty() {
                                if let Some(config) = config_map.get(&dev_code) {
                                    let span = number(config, "timeSpan").unwrap_or(0);
                                    if let Some(capture_dt) = parse_dt(&capture) {
                                        if (now() - capture_dt).num_minutes() > span {
                                            trail_list.push(json!({
                                                "pointUuid": uuid::Uuid::new_v4().simple().to_string(),
                                                "stateType": SERVICE_AREA_CAPTURE,
                                                "captureTime": now_text(),
                                                "locationCode": "",
                                                "roadCode": config.get("roadCode").cloned().unwrap_or(Value::Null),
                                                "sectionCode": config.get("sectionCode").cloned().unwrap_or(Value::Null),
                                                "devCode": text(config, "fwqbm"),
                                                "devName": text(config, "fwqmc"),
                                                "pileno": text(config, "pileNo"),
                                                "lon": config.get("lon").and_then(Value::as_str).unwrap_or_default().parse::<f64>().ok(),
                                                "lat": config.get("lat").and_then(Value::as_str).unwrap_or_default().parse::<f64>().ok(),
                                            }));
                                        }
                                    }
                                }
                            }
                        }

                        let mut dev_codes = String::new();
                        let mut last_bo: Option<&Value> = None;
                        for point in &trail_list {
                            let has_position = point.get("lon").map(|v| !v.is_null()).unwrap_or(false)
                                && point.get("lat").map(|v| !v.is_null()).unwrap_or(false);
                            if has_position && !is_blank(&text(point, "devCode")) {
                                last_bo = Some(point);
                            }
                        }
                        let tracks_uuid = trail
                            .get("tracks")
                            .and_then(|tracks| tracks.get("uuid"))
                            .and_then(Value::as_str)
                            .unwrap_or_default()
                            .to_string();
                        if let Some(last_bo) = last_bo {
                            status = "1".to_string();
                            last_lon = opt_text(last_bo, "lon");
                            last_lat = opt_text(last_bo, "lat");
                            last_type = opt_text(last_bo, "stateType");
                            track_json = Some(serde_json::to_string(&json!({
                                "tracks": trail.get("tracks").cloned().unwrap_or(Value::Null),
                                "trailList": trail_list,
                            })).unwrap_or_default());

                            if !is_blank(&text(last_bo, "devCode")) {
                                dev_codes.push_str(&format!(
                                    "{}:{},",
                                    text(last_bo, "stateType"),
                                    text(last_bo, "devCode")
                                ));
                            }
                            for (kind, key) in [("roadCode", "roadCode"), ("sectionCode", "sectionCode")] {
                                let value = text(last_bo, key);
                                if !is_blank(&value) {
                                    let token = format!("{kind}:{value}");
                                    if !dev_codes.contains(&token) {
                                        dev_codes.push_str(&token);
                                        dev_codes.push(',');
                                    }
                                }
                            }
                            gantry_code = Some(dev_codes.trim_end_matches(',').to_string());

                            // 第一个抓拍点（省界/收费站优先）
                            let first = trail_list
                                .iter()
                                .find(|point| {
                                    matches!(
                                        text(point, "stateType").as_str(),
                                        BORDER_WEIGHING_CAPTURE | PROV_CAPTURE | STATION_CAPTURE
                                    )
                                })
                                .cloned()
                                .unwrap_or(Value::Object(Map::new()));
                            let mut warning = Map::new();
                            warning.insert(
                                "id".to_string(),
                                json!(uuid::Uuid::new_v4().simple().to_string()),
                            );
                            warning.insert("carId".to_string(), car_id.clone());
                            warning.insert("carNo".to_string(), json!(car_no));
                            warning.insert("carType".to_string(), json!(car_text(car, "carType")));
                            warning.insert("carVehicle".to_string(), json!(car_text(car, "carVehicle")));
                            warning.insert("carNum".to_string(), car.get("carNum").cloned().unwrap_or(Value::Null));
                            warning.insert("trackId".to_string(), json!(tracks_uuid));
                            warning.insert(
                                "trackJosn".to_string(),
                                json!(serde_json::to_string(last_bo).unwrap_or_default()),
                            );
                            warning.insert("trackNames".to_string(), json!(dev_codes.trim_end_matches(',')));
                            warning.insert("inStationId".to_string(), json!(text(&first, "devCode")));
                            warning.insert("inStation".to_string(), json!(text(&first, "devName")));
                            if let Some(capture) = parse_dt(&text(&first, "captureTime")) {
                                warning.insert(
                                    "inTime".to_string(),
                                    json!(capture.format("%Y-%m-%d %H:%M:%S").to_string()),
                                );
                            }
                            warning.insert("gantryStationId".to_string(), json!(text(last_bo, "devCode")));
                            warning.insert("gantrytStation".to_string(), json!(text(last_bo, "devName")));
                            if let Some(capture) = parse_dt(&text(last_bo, "captureTime")) {
                                warning.insert(
                                    "gantryTime".to_string(),
                                    json!(capture.format("%Y-%m-%d %H:%M:%S").to_string()),
                                );
                            }
                            warning.insert("fileIds".to_string(), json!(text(last_bo, "imagesArry")));
                            warning.insert("delFlag".to_string(), json!("0"));
                            warning.insert("createBy".to_string(), json!(1));
                            warning.insert("createTime".to_string(), json!(now_text()));
                            warning.insert("updateBy".to_string(), json!(1));
                            warning.insert("updateTime".to_string(), json!(now_text()));
                            warning.insert("roadCode".to_string(), json!(text(last_bo, "roadCode")));
                            warning.insert("sectionCode".to_string(), json!(text(last_bo, "sectionCode")));

                            let point_uuid = tracks_uuid.clone();
                            if !point_uuid.is_empty() {
                                delete_track_ids.push(point_uuid.clone());
                            }
                            let mut flag_date = chrono::Local::now().format("%Y%m%d").to_string();
                            if let Some((_, suffix)) = point_uuid.split_once("@@") {
                                flag_date = suffix.to_string();
                            }
                            warning.insert("backCol1".to_string(), json!(flag_date));
                            add_warnings.push(Value::Object(warning));
                        }
                    }
                }
            }
        }

        // Java: updateBatchById(car)，仅更新有变化的字段。
        let Some(id) = car.get("id").cloned().filter(|value| !value.is_null()) else {
            continue;
        };
        let mut entity = Map::new();
        entity.insert("id".to_string(), id);
        entity.insert("status".to_string(), json!(status));
        entity.insert("lastPassLongitude".to_string(), json!(last_lon));
        entity.insert("lastPassLatitude".to_string(), json!(last_lat));
        entity.insert("lastPassType".to_string(), json!(last_type));
        entity.insert("trackJosn".to_string(), json!(track_json));
        entity.insert("gantryCode".to_string(), json!(gantry_code));
        support::update_entity_by_id(
            &state.db,
            "car_info",
            "id",
            &Value::Object(entity),
            support::AutoFill::NONE,
        )
        .await?;
    }

    // 删除旧预警
    if !delete_track_ids.is_empty() {
        let mut builder = sqlx::QueryBuilder::<sqlx::MySql>::new(
            "delete from car_warning_info where track_id in (",
        );
        let mut separated = builder.separated(", ");
        for id in &delete_track_ids {
            separated.push_bind(id.clone());
        }
        builder.push(")");
        builder.build().execute(&state.db).await?;
    }

    // 计算下一通行点并插入预警
    for warning in &mut add_warnings {
        compute_next_pass(state, warning).await?;
        support::insert_entity(
            &state.db,
            "car_warning_info",
            warning,
            support::AutoFill::NONE,
        )
        .await?;
    }

    // 刷新预警缓存（Java: updateRedisWarningList 取当天 track_id 的前 100 条）
    let today = chrono::Local::now().format("%Y%m%d").to_string();
    let rows = sqlx::query(
        "select t.*, c.escaped_type escapedType, c.escaped_amount escapedAmount \
         from car_warning_info t inner join car_info c on c.del_flag = '0' and t.car_id = c.id \
         and c.status = '1' where t.del_flag = '0' and t.back_col1 = ? \
         order by t.gantry_time desc, t.id limit 100",
    )
    .bind(today)
    .fetch_all(&state.db)
    .await?;
    let cached = stamp_types(
        crate::db::rows::rows_to_json(&rows),
        "com.ruoyi.manager.domain.CarWarningInfo",
    );
    state.redis.set_object(WARNING_LIST, &cached).await?;
    Ok(())
}

/// Java: syncCurrentTrack 的 nextPassTime/nextPassAddress 计算（3 分钟去重后取最新低频点）。
async fn compute_next_pass(state: &AppState, warning: &mut Value) -> Result<(), AppError> {
    let car_no = text(warning, "carNo");
    let station_id = text(warning, "gantryStationId");
    let gantry_time = warning
        .get("gantryTime")
        .and_then(Value::as_str)
        .and_then(parse_dt);
    let key = format!("{CAR_HISTORY_TRAIL}{car_no}");
    let Some(trails) = state.redis.get_object::<Vec<Value>>(&key).await? else {
        return Ok(());
    };
    let mut candidates: Vec<Value> = Vec::new();
    for trail in trails {
        let Some(points) = trail.get("trailList").and_then(Value::as_array) else {
            continue;
        };
        let mut dedup: std::collections::HashMap<String, NaiveDateTime> =
            std::collections::HashMap::new();
        let mut filtered: Vec<Value> = Vec::new();
        for point in points {
            let state_type = text(point, "stateType");
            if !matches!(
                state_type.as_str(),
                BORDER_WEIGHING_CAPTURE | GANTRY_CAPTURE | PROV_CAPTURE | SERVICE_AREA_CAPTURE
                    | STATION_CAPTURE
            ) {
                continue;
            }
            let capture = text(point, "captureTime");
            let Some(capture_dt) = parse_dt(&capture) else { continue };
            let dev_code = text(point, "devCode");
            if let Some(previous) = dedup.get(&dev_code) {
                if (capture_dt - *previous).num_minutes().abs() <= 3 {
                    continue;
                }
            }
            dedup.insert(dev_code, capture_dt);
            filtered.push(point.clone());
        }
        for index in 0..filtered.len() {
            if text(&filtered[index], "devCode") == station_id && index + 1 < filtered.len() {
                let mut next = filtered[index + 1].clone();
                next["preCaptureTime"] = json!(text(&filtered[index], "captureTime"));
                if is_blank(&text(&next, "captureTime")) {
                    next["captureTime"] = json!("2000-10-10 10:00:00");
                }
                candidates.push(next);
                break;
            }
        }
    }
    if candidates.is_empty() {
        return Ok(());
    }
    let mut counts: std::collections::HashMap<String, i64> = std::collections::HashMap::new();
    for candidate in &candidates {
        *counts.entry(text(candidate, "devCode")).or_insert(0) += 1;
    }
    for candidate in &mut candidates {
        let dev_code = text(candidate, "devCode");
        candidate["countNum"] = json!(counts.get(&dev_code).copied().unwrap_or(0));
    }
    candidates.sort_by(|left, right| {
        let left_count = number(left, "countNum").unwrap_or(0);
        let right_count = number(right, "countNum").unwrap_or(0);
        right_count
            .cmp(&left_count)
            .then_with(|| text(right, "captureTime").cmp(&text(left, "captureTime")))
    });
    let best = &candidates[0];
    if let Some(object) = warning.as_object_mut() {
        object.insert(
            "nextPassAddress".to_string(),
            json!(text(best, "devName")),
        );
        if let (Some(gantry_time), Some(current), Some(previous)) = (
            gantry_time,
            parse_dt(&text(best, "captureTime")),
            parse_dt(&text(best, "preCaptureTime")),
        ) {
            let next = gantry_time + (current - previous);
            object.insert(
                "nextPassTime".to_string(),
                json!(next.format("%Y-%m-%d %H:%M:%S").to_string()),
            );
        }
    }
    Ok(())
}

// ==================== 可疑车辆同步（简化核心） ====================

/// Java: syncSuspiciousCar —— 只处理传入的轨迹列表（Redis 分支随后会被入参覆盖）。
pub async fn sync_suspicious_car(state: &AppState, trails: &[Value]) -> Result<usize, AppError> {
    if trails.is_empty() {
        return Ok(0);
    }
    let cars = car_list(state).await?;
    let car_map: std::collections::HashMap<String, Value> = cars
        .into_iter()
        .map(|car| (text(&car, "carNo"), car))
        .collect();
    let plate_color = support::dict_map(&state.db, "plate_color").await?;
    let white: Vec<String> = sqlx::query_scalar(
        "select car_no from car_white_info where del_flag = '0'",
    )
    .fetch_all(&state.db)
    .await?;
    let mut count = 0;
    for trail in trails {
        let tracks = trail.get("tracks").cloned().unwrap_or(Value::Object(Map::new()));
        let car_no = text(&tracks, "plateKey");
        let track_id = text(&tracks, "uuid");
        if car_no.is_empty() || track_id.is_empty() || white.contains(&car_no) {
            continue;
        }
        let existing: Option<(String, Option<String>)> = sqlx::query_as(
            "select id, check_status from car_suspicious where del_flag = '0' and car_no = ? \
             and track_id = ? limit 1",
        )
        .bind(&car_no)
        .bind(&track_id)
        .fetch_optional(&state.db)
        .await?;
        if existing
            .as_ref()
            .and_then(|(_, status)| status.as_deref())
            == Some("1")
        {
            continue;
        }
        let mut row = Map::new();
        if let Some((id, _)) = &existing {
            row.insert("id".to_string(), json!(id));
        } else {
            row.insert("id".to_string(), json!(uuid::Uuid::new_v4().simple().to_string()));
            row.insert("carNo".to_string(), json!(car_no));
            row.insert("isExcept".to_string(), json!("1"));
            row.insert("checkStatus".to_string(), json!("0"));
            row.insert("status".to_string(), json!("0"));
            row.insert("delFlag".to_string(), json!("0"));
            row.insert("createBy".to_string(), json!(1));
            row.insert("createTime".to_string(), json!(now_text()));
        }
        row.insert("trackId".to_string(), json!(track_id));
        row.insert(
            "trackJosn".to_string(),
            json!(serde_json::to_string(trail).unwrap_or_default()),
        );
        row.insert("backCol1".to_string(), json!(text(&tracks, "escapedTfcj")));

        if let Some(car) = car_map.get(&car_no) {
            row.insert("plateColor".to_string(), json!(car_text(car, "plateColor")));
            row.insert("carType".to_string(), json!(car_text(car, "carType")));
            row.insert("carVehicle".to_string(), json!(car_text(car, "carVehicle")));
        } else {
            let plate = text(&tracks, "plateColor");
            row.insert(
                "plateColor".to_string(),
                json!(plate_color.get(&plate).cloned().unwrap_or_else(|| "9".to_string())),
            );
        }
        let axle = number(&tracks, "enaxlecount")
            .or_else(|| number(&tracks, "carNum"))
            .unwrap_or_default();
        row.insert("carNum".to_string(), json!(axle));
        row.insert("passType".to_string(), json!(text(&tracks, "passType")));
        for (key, default) in [("plateColor", "9"), ("carType", "99"), ("carVehicle", "99")] {
            if is_blank(&text(&Value::Object(row.clone()), key)) {
                row.insert(key.to_string(), json!(default));
            }
        }
        row.insert("updateBy".to_string(), json!(1));
        row.insert("updateTime".to_string(), json!(now_text()));

        let entity = Value::Object(row);
        if existing.is_some() {
            support::update_entity_by_id(
                &state.db,
                "car_suspicious",
                "id",
                &entity,
                support::AutoFill::NONE,
            )
            .await?;
        } else {
            support::insert_entity(
                &state.db,
                "car_suspicious",
                &entity,
                support::AutoFill::NONE,
            )
            .await?;
        }
        count += 1;
    }
    Ok(count)
}

// ==================== 逃费金额回写 ====================

/// Java: CarExceptRecordServiceImpl.saveCarExcept —— 按车牌汇总后回写 car_info。
pub async fn save_car_except(state: &AppState) -> Result<usize, AppError> {
    let rows = sqlx::query(
        "select t.car_no, count(1) exceptNum, round(sum(t.dif_amount), 2) exceptAmount, \
         group_concat(distinct t.escaped_type separator ',') escaped_type \
         from car_except_record t where t.del_flag = '0' group by t.car_no",
    )
    .fetch_all(&state.db)
    .await?;
    let aggregated = crate::db::rows::rows_to_json(&rows);
    let mut count = 0;
    for row in aggregated {
        let car_no = text(&row, "car_no");
        if car_no.is_empty() {
            continue;
        }
        let escaped_type = text(&row, "escaped_type");
        let escaped_amount = row.get("exceptAmount").cloned().unwrap_or(Value::Null);
        let affected = sqlx::query(
            "update car_info set escaped_type = ?, escaped_amount = ? \
             where del_flag = '0' and car_no = ?",
        )
        .bind(escaped_type)
        .bind(escaped_amount)
        .bind(&car_no)
        .execute(&state.db)
        .await?
        .rows_affected();
        count += affected as usize;
    }
    Ok(count)
}

// ==================== 可疑车辆迁移 ====================

/// Java: CarTrackInfoServiceImpl / CarSuspiciousServiceImpl.changeCarSuspicious —— 保留一个月。
pub async fn change_car_suspicious(state: &AppState) -> Result<(u64, u64), AppError> {
    let cutoff = (now() - chrono::Duration::days(30))
        .format("%Y-%m-%d 00:00:00")
        .to_string();
    let moved = sqlx::query(
        "insert into car_suspicious_back select * from car_suspicious t \
         where t.del_flag = '0' and t.in_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
    )
    .bind(&cutoff)
    .execute(&state.db)
    .await?
    .rows_affected();
    let removed = sqlx::query(
        "delete from car_suspicious where in_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
    )
    .bind(&cutoff)
    .execute(&state.db)
    .await?
    .rows_affected();
    Ok((moved, removed))
}
