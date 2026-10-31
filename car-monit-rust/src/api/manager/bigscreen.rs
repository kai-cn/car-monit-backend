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
            meta::get_route("/manager/bigScreen/carStatistics", None, None, car_statistics),
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
            meta::get_route("/manager/bigScreen/incomeStatistic", None, None, income_statistic),
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
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
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
            let value = if code.is_empty() { default.to_string() } else { code };
            params.insert(key.to_string(), value);
        }
    }

    let mut builder = QueryBuilder::<MySql>::new(
        "select t.id, t.car_no, t.car_type, t.last_pass_longitude as lonStr, \
         t.last_pass_latitude as latStr, t.status from car_info t \
         where t.del_flag = '0' and t.status = '1'",
    );
    for (key, column) in [
        ("fwqbm", "t.gantry_code"),
        ("gantryCode", "t.gantry_code"),
        ("tollCode", "t.gantry_code"),
        ("roadCode", "t.gantry_code"),
        ("escapedType", "t.escaped_type"),
        ("carNoQuery", "t.car_no"),
    ] {
        if let Some(value) = params.get(key).filter(|v| !v.trim().is_empty()) {
            builder.push(format!(" and {column} like concat('%', "));
            builder.push_bind(value.clone());
            builder.push(", '%')");
        }
    }
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
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
    if section_code.is_empty() {
        return Ok(AjaxResult::success_data(Vec::<Value>::new()));
    }
    let type_value = params.get("type").cloned().unwrap_or_default();
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
        "select t.id, t.car_no, t.car_type, t.escaped_type, t.escaped_type_name, t.escaped_amount \
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
    let audit_value = audit_row.map(|row| crate::db::rows::row_to_json(&row)).unwrap_or(Value::Null);

    let mut confirm = QueryBuilder::<MySql>::new(
        "select sum(ifnull(a.amount, 0) + ifnull(a.aduit_amount, 0)) escapedAmount, \
         count(distinct a.car_no) number from car_confim_free a \
         where a.del_flag = '0' and a.status = '0'",
    );
    push_time_filters(&mut confirm, &params, "a.create_time");
    let confirm_row = confirm.build().fetch_optional(&state.db).await?;
    let confirm_value =
        confirm_row.map(|row| crate::db::rows::row_to_json(&row)).unwrap_or(Value::Null);

    Ok(AjaxResult::success_data(json!({
        "totalAmount": audit_value.get("escapedAmount").cloned().unwrap_or(Value::Null),
        "totalCount": audit_value.get("number").cloned().unwrap_or(Value::Null),
        "finishedAmount": confirm_value.get("escapedAmount").cloned().unwrap_or(Value::Null),
        "finishedCount": confirm_value.get("number").cloned().unwrap_or(Value::Null),
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
    let rows = sqlx::query(
        "select t.car_no, t.car_type, t.escaped_type, t.section_name from car_suspicious t \
         where t.del_flag = '0' and is_except = '1' and check_status = '1' \
         order by t.create_time desc, t.id limit 10",
    )
    .fetch_all(&state.db)
    .await?;
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
}

async fn top_ten(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows = sqlx::query(
        "select t1.road_code roadCode, t1.section_name sectionName, count(1) carNum \
         from car_warning_info t, ods_szdn_section t1 \
         where t.del_flag = '0' and t.section_code = t1.section_code \
         group by t1.road_code, t1.section_name order by carNum desc limit 10",
    )
    .fetch_all(&state.db)
    .await?;
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
}

async fn org_list(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows =
        sqlx::query("select org_code orgCode, org_name orgName from ods_yhgl_v_base_org")
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
         d.dept_name orgName, a.org_id from ( \
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
    Ok(AjaxResult::success_data(rows_to_json(&rows)))
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
            if count > 0 {
                object.insert("supplementaryStatus".to_string(), json!("1"));
            }
        }
    }
    Ok(TableDataInfo::new(total, rows))
}
