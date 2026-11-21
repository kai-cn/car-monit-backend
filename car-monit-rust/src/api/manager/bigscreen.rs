// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java
//       ruoyi-system/src/main/resources/mapper/manager/{CarInfo,CarConfimFree,CarExceptRecord,CarAduitFree}Mapper.xml
// 职责: 大屏统计（重点关注、地图点位、堵漏增收、预警/异常车辆、Top10）。
// 对应关系: 各 mapper 的统计 SQL -> 直接查询返回 JSON。

use std::collections::HashMap;

use axum::extract::{RawQuery, State};
use axum::Router;
use serde_json::{json, Value};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::meta;
use crate::api::support;
use crate::db::rows::rows_to_json;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/bigScreen/carStatistics",
            meta::get_route(
                "/manager/bigScreen/carStatistics",
                None,
                None,
                car_statistics,
            ),
        )
        .route(
            "/manager/bigScreen/carLocation",
            meta::get_route("/manager/bigScreen/carLocation", None, None, car_location),
        )
        .route(
            "/manager/bigScreen/sectionList",
            meta::get_route("/manager/bigScreen/sectionList", None, None, section_list),
        )
        .route(
            "/manager/bigScreen/tollGantryFwqList",
            meta::get_route(
                "/manager/bigScreen/tollGantryFwqList",
                None,
                None,
                toll_gantry_fwq,
            ),
        )
        .route(
            "/manager/bigScreen/carVoList",
            meta::get_route("/manager/bigScreen/carVoList", None, None, car_vo_list),
        )
        .route(
            "/manager/bigScreen/carAudit",
            meta::get_route("/manager/bigScreen/carAudit", None, None, car_audit),
        )
        .route(
            "/manager/bigScreen/carWarning",
            meta::get_route("/manager/bigScreen/carWarning", None, None, car_warning),
        )
        .route(
            "/manager/bigScreen/exceptionCar",
            meta::get_route("/manager/bigScreen/exceptionCar", None, None, exception_car),
        )
        .route(
            "/manager/bigScreen/topTen",
            meta::get_route("/manager/bigScreen/topTen", None, None, top_ten),
        )
        .route(
            "/manager/bigScreen/orgList",
            meta::get_route("/manager/bigScreen/orgList", None, None, org_list),
        )
        .route(
            "/manager/bigScreen/incomeStatistic",
            meta::get_route(
                "/manager/bigScreen/incomeStatistic",
                None,
                None,
                income_statistic,
            ),
        )
        .route(
            "/manager/bigScreen/exceptRecordList",
            meta::get_route(
                "/manager/bigScreen/exceptRecordList",
                None,
                None,
                except_record_list,
            ),
        )
}

fn push_time_filters(
    builder: &mut QueryBuilder<'_, MySql>,
    params: &HashMap<String, String>,
    column: &str,
) {
    if let Some(value) = params.get("applyTime1").filter(|v| !v.trim().is_empty()) {
        builder.push(format!(" and {column} >= STR_TO_DATE("));
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d')");
    }
    if let Some(value) = params.get("applyTime2").filter(|v| !v.trim().is_empty()) {
        builder.push(format!(" and {column} < date_add(STR_TO_DATE("));
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d'), interval 1 day)");
    }
}

/// Java: CarConfimFreeMapper.getCarStatistics（按逃费类型汇总）。

/// 以下三组是 Java Jackson 对 VO/实体的键序（实测自 Java 响应）。
const CAR_STATISTICS_KEYS: &[&str] = &["escapedType", "escapedTypeName", "number", "escapedAmount"];
const EXCEPTION_CAR_KEYS: &[&str] = &[
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
const INCOME_STATISTIC_KEYS: &[&str] = &["orgName", "amount", "carNum"];
const EXCEPT_RECORD_KEYS: &[&str] = &[
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
    "passType",
    "inStationId",
    "inStation",
    "inTime",
    "outStationId",
    "outStation",
    "outTime",
    "totalAmount",
    "chargeAmount",
    "difAmount",
    "escapedType",
    "remark",
    "backCol1",
    "backCol2",
    "status",
    "applyTime1",
    "applyTime2",
    "applyTime3",
    "applyTime4",
    "createTimeStr",
    "orgId",
    "supplementaryStatus",
    "exceptIds",
    "carNoQuery",
    "createInfo",
    "exceptNum",
    "exceptAmount",
    "inTimeStr",
    "outTimeStr",
];

async fn car_statistics(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let mut builder = QueryBuilder::<MySql>::new(
        "select a.escaped_type escapedType, sum(ifnull(a.dif_amount, 0)) escapedAmount, \
         count(distinct a.car_no) number from car_except_record a where a.del_flag = '0'",
    );
    push_time_filters(&mut builder, &params, "a.create_time");
    if let Some(value) = params.get("escapedType").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.escaped_type = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params.get("orgId").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.eps_id = ");
        builder.push_bind(value.clone());
    }
    builder.push(" group by a.escaped_type");
    let rows = builder.build().fetch_all(&state.db).await?;
    let stats = rows_to_json(&rows);

    // Java: CarConfimFreeServiceImpl.getCarStatistics() 以 sys_dict_data 的
    // escaped_type 字典为准，先按 dict_sort 建有序结果，再用 SQL 聚合结果填空；
    // 字典里存在但无流水的类型也要返回（number/escapedAmount 保持 VO 默认 0）。
    // 直接 group by 只在有数据时给出行，会把这些 0 值类型漏掉（跨语言 parity 失败）。
    let dict_rows: Vec<(Option<String>, Option<String>)> = sqlx::query_as(
        "select dict_value, dict_label from sys_dict_data \
         where dict_type = 'escaped_type' order by dict_sort asc",
    )
    .fetch_all(&state.db)
    .await?;
    let mut by_type: HashMap<String, Value> = HashMap::new();
    for row in &stats {
        if let Some(object) = row.as_object() {
            if let Some(key) = object.get("escapedType").and_then(Value::as_str) {
                by_type.insert(key.to_string(), row.clone());
            }
        }
    }
    let mut data: Vec<Value> = Vec::new();
    for (value, label) in dict_rows {
        let key = value.unwrap_or_default();
        let label = label.unwrap_or_default();
        let mut object = by_type
            .get(&key)
            .and_then(Value::as_object)
            .cloned()
            .unwrap_or_default();
        object.insert("escapedType".to_string(), json!(key));
        object.insert("escapedTypeName".to_string(), json!(label));
        object
            .entry("escapedAmount".to_string())
            .or_insert_with(|| json!(0));
        object.entry("number".to_string()).or_insert_with(|| json!(0));
        data.push(Value::Object(object));
    }
    Ok(AjaxResult::success_data(support::reorder_rows(
        data,
        CAR_STATISTICS_KEYS,
    )))
}

/// Java: CarInfoMapper.getCarLocation。
async fn car_location(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let mut params = support::query_map(&raw);
    let section_code = params.get("sectionCode").cloned().unwrap_or_default();
    if section_code.contains("all") {
        params.insert("sectionCode".to_string(), String::new());
    }
    let type_value = params.get("type").cloned().unwrap_or_default();
    let code = params.get("code").cloned().unwrap_or_default();
    if !type_value.is_empty() {
        let (key, default) = match type_value.as_str() {
            "1" => ("tollCode", "StationCapture"),
            "2" => ("gantryCode", "GantryCapture"),
            "3" => ("fwqbm", "ServiceAreaCapture"),
            _ => ("", ""),
        };
        if !key.is_empty() {
            let value = if code.is_empty() {
                default.to_string()
            } else {
                code
            };
            params.insert(key.to_string(), value);
        }
    }

    // Java 从 car_list 缓存过滤；未命中时回源 `selectCarInfoList` 并回写缓存
    // （那条查询带 `not exists` 排除条件，直接拼一条简单 SQL 会多出被排除的车）。
    let cached = state.redis.get_object::<Value>("car_list").await?;
    let source = match cached {
        Some(Value::Array(items)) => items,
        _ => {
            let rows = crate::api::manager::car_info::car_info_cache_rows(&state).await?;
            state
                .redis
                .set_object(
                    "car_list",
                    &crate::db::redis_cache::stamp_types(
                        rows.clone(),
                        "com.ruoyi.manager.domain.CarInfo",
                    ),
                )
                .await?;
            rows
        }
    };
    let mut data = Vec::new();
    for row in source {
        if row
            .get("status")
            .and_then(Value::as_str)
            .unwrap_or_default()
            != "1"
        {
            continue;
        }
        let dev_codes = row
            .get("gantryCode")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let mut ok = true;
        for (param_key, row_key) in [
            ("roadCode", "gantryCode"),
            ("sectionCode", "gantryCode"),
            ("tollCode", "gantryCode"),
            ("gantryCode", "gantryCode"),
            ("fwqbm", "gantryCode"),
            ("escapedType", "escapedType"),
            ("carNoQuery", "carNo"),
        ] {
            let para = params.get(param_key).cloned().unwrap_or_default();
            let para = para.trim_end_matches(',').to_string();
            if para.trim().is_empty() {
                continue;
            }
            let value = if row_key == "gantryCode" {
                dev_codes.clone()
            } else {
                row.get(row_key)
                    .and_then(Value::as_str)
                    .unwrap_or_default()
                    .to_string()
            };
            if !para.split(',').any(|part| value.contains(part)) {
                ok = false;
                break;
            }
        }
        if !ok {
            continue;
        }
        let lon_str = row.get("lastPassLongitude").cloned().unwrap_or(Value::Null);
        let lat_str = row.get("lastPassLatitude").cloned().unwrap_or(Value::Null);
        let lon = lon_str
            .as_str()
            .and_then(|text| text.trim().parse::<f64>().ok())
            .and_then(serde_json::Number::from_f64)
            .map(Value::Number)
            .unwrap_or(Value::Null);
        let lat = lat_str
            .as_str()
            .and_then(|text| text.trim().parse::<f64>().ok())
            .and_then(serde_json::Number::from_f64)
            .map(Value::Number)
            .unwrap_or(Value::Null);
        data.push(json!({
            "id": row.get("id").cloned().unwrap_or(Value::Null),
            "carNo": row.get("carNo").cloned().unwrap_or(Value::Null),
            "carType": row.get("carType").cloned().unwrap_or(Value::Null),
            "lonStr": lon_str,
            "latStr": lat_str,
            "lastPassType": row.get("lastPassType").cloned().unwrap_or(Value::Null),
            "lon": lon,
            "lat": lat,
            "status": row.get("status").cloned().unwrap_or(Value::Null),
        }));
    }
    Ok(AjaxResult::success_data(data))
}

async fn section_list(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows = sqlx::query(
        "select distinct t.section_code sectionCode, concat(t.road_code, '', t.section_name) sectionName \
         from ods_szdn_section t",
    )
    .fetch_all(&state.db)
    .await?;
    let mut data = vec![json!({ "sectionCode": "all", "sectionName": "全部" })];
    data.extend(rows_to_json(&rows));
    Ok(AjaxResult::success_data(data))
}

async fn toll_gantry_fwq(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let section_code = params
        .get("sectionCode")
        .map(|value| value.trim().trim_end_matches(',').to_string())
        .unwrap_or_default();
    let type_value = params.get("type").cloned().unwrap_or_default();
    if type_value.trim().is_empty() {
        // Java: @RequestParam String type（required=true）缺失时由 Spring 返回 500。
        return Err(AppError::BadRequest(
            "Required request parameter 'type' for method parameter type String is not present"
                .to_string(),
        ));
    }
    if section_code.is_empty() {
        return Ok(AjaxResult::success_data(Vec::<Value>::new()));
    }
    let use_filter = !section_code.contains("all");
    let codes: Vec<String> = section_code
        .split(',')
        .filter(|item| !item.is_empty())
        .map(str::to_string)
        .collect();

    let (sql, code_columns) = match type_value.as_str() {
        "1" => (
            "select distinct toll_code code, toll_name name from ods_szdn_toll where 1=1",
            true,
        ),
        "2" => (
            "select distinct gantry_code code, gantry_name name from ods_szdn_gantry where 1=1",
            true,
        ),
        "3" => (
            "select distinct fwqbm code, fwqmc name from dwd_lczt_fwqjcxx where 1=1",
            true,
        ),
        _ => ("select 1 code, '' name from dual where 1=0", false),
    };
    let mut builder = QueryBuilder::<MySql>::new(sql);
    if use_filter && code_columns {
        builder.push(" and section_code in (");
        let mut separated = builder.separated(", ");
        for code in &codes {
            separated.push_bind(code.clone());
        }
        builder.push(")");
    }
    let rows = builder.build().fetch_all(&state.db).await?;
    let data = rows_to_json(&rows)
        .into_iter()
        .map(|row| {
            json!({
                "type": type_value,
                "code": row.get("code").cloned().unwrap_or(Value::Null),
                "name": row.get("name").cloned().unwrap_or(Value::Null),
            })
        })
        .collect::<Vec<_>>();
    Ok(AjaxResult::success_data(data))
}

async fn car_vo_list(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows = sqlx::query(
        "select t.car_no, t.car_type, t.escaped_type, t.escaped_amount \
         from car_info t where t.del_flag = '0' order by t.create_time desc, t.id limit 10",
    )
    .fetch_all(&state.db)
    .await?;
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
}

async fn car_audit(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let mut audit = QueryBuilder::<MySql>::new(
        "select sum(ifnull(a.dif_amount, 0)) escapedAmount, count(distinct a.car_no) number \
         from car_except_record a where a.del_flag = '0'",
    );
    push_time_filters(&mut audit, &params, "a.create_time");
    let audit_row = audit.build().fetch_optional(&state.db).await?;
    let audit_value = audit_row
        .map(|row| crate::db::rows::row_to_json(&row))
        .unwrap_or(Value::Null);

    let mut confirm = QueryBuilder::<MySql>::new(
        "select sum(ifnull(a.amount, 0) + ifnull(a.aduit_amount, 0)) escapedAmount, \
         count(distinct a.car_no) number from car_confim_free a \
         where a.del_flag = '0' and a.status = '0'",
    );
    push_time_filters(&mut confirm, &params, "a.create_time");
    let confirm_row = confirm.build().fetch_optional(&state.db).await?;
    let confirm_value = confirm_row
        .map(|row| crate::db::rows::row_to_json(&row))
        .unwrap_or(Value::Null);

    // Java 侧 CarStatisticsVO 的 number/BigDecimal 字段有默认值 0/BigDecimal.ZERO。
    // SQL 的 sum() 在无匹配行时返回 NULL（即使内层 ifnull 也没用，因为外层没有分组行），
    // Jackson 映射到 int/BigDecimal 后仍是 0；Rust 若直接透传会输出 null，跨语言 parity 判 DIFF。
    // 因此把每个数值字段的 NULL 统一回退为 0，与 Java VO 默认值保持一致。
    fn zero_if_null(value: Option<&Value>) -> Value {
        match value {
            Some(Value::Null) | None => json!(0),
            Some(v) => v.clone(),
        }
    }
    // Java 侧 VO 的声明顺序即 totalCount, finishedCount, totalAmount, finishedAmount。
    Ok(AjaxResult::success_data(json!({
        "totalCount": zero_if_null(audit_value.get("number")),
        "finishedCount": zero_if_null(confirm_value.get("number")),
        "totalAmount": zero_if_null(audit_value.get("escapedAmount")),
        "finishedAmount": zero_if_null(confirm_value.get("escapedAmount")),
    })))
}

async fn car_warning(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let track_id = params.get("trackId").cloned().unwrap_or_default();
    let rows = sqlx::query(
        "select t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.car_num, \
         t.in_station_id, t.in_station, t.in_time, t.gantry_station_id, t.gantryt_station, \
         t.gantry_time, t.file_ids, t.next_pass_time, t.next_pass_type, t.next_pass_address, \
         t.next_pass_longitude, t.next_pass_latitude, t.road_code, t.road_name, t.section_code, \
         t.section_name, t.back_col1, t.back_col2, t.status, t.sort, t.eps_id, t.del_flag, \
         t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id, t.track_id, \
         t.track_names, c.escaped_type escapedType, c.escaped_amount escapedAmount \
         from car_warning_info t inner join car_info c on c.del_flag = '0' and t.car_id = c.id \
         and c.status = '1' where t.del_flag = '0' and t.back_col1 = ? \
         order by t.gantry_time desc, t.id",
    )
    .bind(track_id)
    .fetch_all(&state.db)
    .await?;
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
}

async fn exception_car(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows = sqlx::query(&format!(
        "select {} from car_suspicious t \
         where t.del_flag = '0' and is_except = '1' and check_status = '1' \
         order by t.create_time desc, t.id limit 10",
        crate::api::manager::car_suspicious::SUSPICIOUS_COLUMNS
    ))
    .fetch_all(&state.db)
    .await?;
    let mut data = rows_to_json(&rows);
    let keep = ["carNo", "carType", "escapedType", "sectionName"];
    for row in &mut data {
        if let Some(object) = row.as_object_mut() {
            for (key, value) in object.iter_mut() {
                if !keep.contains(&key.as_str()) {
                    *value = Value::Null;
                }
            }
        }
    }
    Ok(AjaxResult::success_data(support::reorder_rows(
        data,
        EXCEPTION_CAR_KEYS,
    )))
}

async fn top_ten(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows = sqlx::query(
        "select t1.road_code roadCode, concat(t1.road_code, ' ', t1.section_name) sectionName, \
         count(1) carNum from car_warning_info t, ods_szdn_section t1 \
         where t.del_flag = '0' and t.section_code = t1.section_code \
         group by t1.road_code, t1.section_name order by carNum desc limit 10",
    )
    .fetch_all(&state.db)
    .await?;
    let mut data = rows_to_json(&rows);
    let total: f64 = data
        .first()
        .and_then(|row| row.get("carNum"))
        .and_then(Value::as_f64)
        .unwrap_or(0.0);
    for (index, row) in data.iter_mut().enumerate() {
        if let Some(object) = row.as_object_mut() {
            let count = object.get("carNum").and_then(Value::as_f64).unwrap_or(0.0);
            object.insert("rank".to_string(), json!(index + 1));
            let rate = if total > 0.0 {
                (count * 100.0 / total) as i64
            } else {
                0
            };
            object.insert("rate".to_string(), json!(rate.to_string()));
        }
    }
    Ok(AjaxResult::success_data(data))
}

async fn org_list(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows = sqlx::query("select org_code orgCode, org_name orgName from ods_yhgl_v_base_org")
        .fetch_all(&state.db)
        .await?;
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
}

async fn income_statistic(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let mut params = support::query_map(&raw);
    let date_type = params
        .get("queryDateType")
        .cloned()
        .filter(|v| !v.trim().is_empty())
        .unwrap_or_else(|| "suo".to_string());
    params.insert("queryDateType".to_string(), date_type.clone());

    let mut builder = QueryBuilder::<MySql>::new(
        "select sum(ifnull(amount, 0)) amount, count(distinct car_no) carNum, \
         d.dept_name orgName from ( \
         select t.car_no, t.amount, t.org_id, t.create_time, t.del_flag, t.status \
         from car_confim_free t where t.del_flag = '0' and t.status = '0' \
         union all select t.car_no, t.amount, t.org_id, t.create_time, t.del_flag, t.status \
         from car_aduit_free t where t.del_flag = '0') a \
         left join sys_dept d on d.dept_id = a.org_id and d.del_flag = '0' \
         where a.del_flag = '0'",
    );
    if date_type == "suo" {
        builder.push(" and a.status = '0'");
    }
    if let Some(value) = params.get("startDate").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.create_time >= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d') and a.create_time < LAST_DAY(");
        builder.push_bind(value.clone());
        builder.push(")");
    }
    if date_type == "suo" {
        builder.push(" and d.tree_leavel = 2");
    } else if date_type == "zhan" {
        builder.push(" and d.tree_leavel = 3");
    }
    push_time_filters(&mut builder, &params, "a.create_time");
    builder.push(" group by a.org_id order by amount desc");
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(AjaxResult::success_data(support::reorder_rows(
        rows_to_json(&rows),
        INCOME_STATISTIC_KEYS,
    )))
}

async fn except_record_list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let spec = crate::api::manager::car_except_record::EXCEPT_SPEC;
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, mut rows) = support::query_list(&state.db, &params, &spec, &page).await?;
    for row in &mut rows {
        let car_id = row.get("carId").cloned().unwrap_or(Value::Null);
        let id = row.get("id").cloned().unwrap_or(Value::Null);
        let org_id: Option<String> = sqlx::query_scalar(
            "select org_id from car_confim_free where car_id = ? and find_in_set(except_ids, ?) > 0 limit 1",
        )
        .bind(car_id.as_str().unwrap_or_default())
        .bind(id.as_str().unwrap_or_default())
        .fetch_optional(&state.db)
        .await?;
        let count: i64 = sqlx::query_scalar(
            "select count(1) from car_aduit_free where car_id = ? and del_flag = '0'",
        )
        .bind(car_id.as_str().unwrap_or_default())
        .fetch_one(&state.db)
        .await?;
        if let Some(object) = row.as_object_mut() {
            object.insert("orgId".to_string(), json!(org_id));
            object.insert(
                "supplementaryStatus".to_string(),
                json!(if count > 0 { "1" } else { "0" }),
            );
        }
    }
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, EXCEPT_RECORD_KEYS),
    ))
}
