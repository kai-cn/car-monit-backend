// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarConfimFreeController.java
//       ruoyi-system/src/main/resources/mapper/manager/CarConfimFreeMapper.xml
// 职责: 确认补缴 CRUD、关注名单、单位统计。
// 对应关系: selectConcernedList/getPCCarStatistics/selectCarConfimFreeByExceptIds/listCount。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.link_name, t.link_phone, \
             t.org_id, sd.dept_name org_name, t.user_ids, t.user_names, t.amount, \
             t.aduit_amount, t.except_ids, t.escaped_types, t.back_col1, t.back_col2, t.remark, \
             t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, \
             t.update_time, t.tenant_id, 0 as number, 0 as escapedAmount, \
             null as carAduitFreeList, null as carExceptRecordList, \n             null as totalAmount, null as chargeAmount, null as difAmount, null as applyTime1, \n             null as applyTime2, null as applyTime3, null as applyTime4, null as carNoQuery, \n             null as confimFreeNum, null as confimFreeAmount, null as escapedType, \n             null as comfimFreeType",
    from: "from car_confim_free t left join sys_dept sd on sd.dept_id = t.org_id",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("carId", "t.car_id"),
        Filter::eq("carNo", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::like("linkName", "t.link_name"),
        Filter::eq("linkPhone", "t.link_phone"),
        Filter::eq("orgId", "t.org_id"),
        Filter::like("orgName", "sd.dept_name"),
        Filter::eq("userIds", "t.user_ids"),
        Filter::eq("userNames", "t.user_names"),
        Filter::eq("amount", "t.amount"),
        Filter::eq("escapedTypes", "t.escaped_types"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
        Filter::raw("exceptIds", " and find_in_set(t.id, ?) > 0"),
        Filter::like("carNoQuery", "t.car_no"),
        Filter::raw("applyTime1", " and t.create_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
        Filter::raw("applyTime2", " and t.create_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
        Filter::raw("applyTime3", " and t.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"),
        Filter::raw(
            "applyTime4",
            " and t.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)",
        ),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "确认补缴",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarConfimFreeController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "确认补缴",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.CarConfimFreeController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "确认补缴",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarConfimFreeController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "确认补缴",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.CarConfimFreeController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/confimfree/list",
            meta::get_route("/manager/confimfree/list", None, None, list),
        )
        .route(
            "/manager/confimfree/listCarNo",
            meta::get_route("/manager/confimfree/listCarNo", None, None, list_car_no),
        )
        .route(
            "/manager/confimfree/listCount",
            meta::get_route("/manager/confimfree/listCount", None, None, list_count),
        )
        .route(
            "/manager/confimfree/concernedList",
            meta::get_route("/manager/confimfree/concernedList", None, None, concerned_list),
        )
        .route(
            "/manager/confimfree/exportConcernedList",
            meta::get_route("/manager/confimfree/exportConcernedList", None, Some(&LOG_EXPORT), export_concerned),
        )
        .route(
            "/manager/confimfree/carStatics",
            meta::get_route("/manager/confimfree/carStatics", None, None, car_statics),
        )
        .route(
            "/manager/confimfree/exportCarStatics",
            meta::get_route("/manager/confimfree/exportCarStatics", None, Some(&LOG_EXPORT), export_car_statics),
        )
        .route(
            "/manager/confimfree/except/{exceptIds}",
            meta::get_route("/manager/confimfree/except/{exceptIds}", None, None, by_except_ids),
        )
        .route(
            "/manager/confimfree/export",
            meta::get_route("/manager/confimfree/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/manager/confimfree/{ids}",
            meta::get_route("/manager/confimfree/{ids}", None, None, get_info),
        )
        .route(
            "/manager/confimfree",
            meta::post_route("/manager/confimfree", None, Some(&LOG_ADD), add).merge(
                meta::put_route("/manager/confimfree", None, Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/manager/confimfree/{ids}",
            meta::delete_route("/manager/confimfree/{ids}", None, Some(&LOG_REMOVE), remove),
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

async fn list_car_no(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    if params.get("carNo").map(|v| v.trim().is_empty()).unwrap_or(true) {
        params.insert("carNo".to_string(), "-1".to_string());
    }
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_count(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let car_no = params.get("carNo").cloned().unwrap_or_default();
    let status = params.get("status").cloned().unwrap_or_default();
    let mut sql = String::from(
        "select t.car_no, count(1) confimFreeNum, \
         round(ifnull(sum(t.aduit_amount),0) + ifnull(sum(t.amount),0), 2) confimFreeAmount \
         from car_confim_free t where t.del_flag = '0' and t.car_no = ?",
    );
    if !status.is_empty() {
        sql.push_str(" and t.status = ?");
    }
    sql.push_str(" group by t.car_no");
    let mut query = sqlx::query(&sql).bind(car_no);
    if !status.is_empty() {
        query = query.bind(status);
    }
    let row = query.fetch_optional(&state.db).await?;
    Ok(match row {
        Some(row) => AjaxResult::success_data(crate::db::rows::row_to_json(&row)),
        None => AjaxResult::success(),
    })
}

fn concerned_sql(params: &HashMap<String, String>, count: bool) -> QueryBuilder<'static, MySql> {
    let mut builder = QueryBuilder::<MySql>::new(if count {
        "select count(0) from car_info t join (select t1.car_no, \
         sum(t1.total_amount) total_amount, sum(t1.charge_amount) charge_amount, \
         sum(t1.dif_amount) dif_amount, sum(case when t1.status = '0' then 1 else 0 end) except_num, \
         count(1) count_num, group_concat(t1.id separator ',') except_ids \
         from car_except_record t1 where t1.del_flag = '0' group by t1.car_no) k \
         on k.count_num > 0 and k.except_num = 0 and t.car_no = k.car_no \
         left join sys_dept sd on sd.dept_id = t.eps_id and sd.del_flag = '0' \
         where t.del_flag = '0'"
    } else {
        "select t.id, t.car_no, t.car_type, t.car_vehicle, t.escaped_type, t.org_id, \
         sd.dept_name org_name, k.total_amount totalAmount, k.charge_amount chargeAmount, \
         k.dif_amount difAmount, k.except_ids from car_info t join (select t1.car_no, \
         sum(t1.total_amount) total_amount, sum(t1.charge_amount) charge_amount, \
         sum(t1.dif_amount) dif_amount, sum(case when t1.status = '0' then 1 else 0 end) except_num, \
         count(1) count_num, group_concat(t1.id separator ',') except_ids \
         from car_except_record t1 where t1.del_flag = '0' group by t1.car_no) k \
         on k.count_num > 0 and k.except_num = 0 and t.car_no = k.car_no \
         left join sys_dept sd on sd.dept_id = t.eps_id and sd.del_flag = '0' \
         where t.del_flag = '0'"
    });
    if let Some(value) = params.get("carNo").filter(|v| !v.trim().is_empty()) {
        builder.push(" and t.car_no = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params.get("carNoQuery").filter(|v| !v.trim().is_empty()) {
        builder.push(" and t.car_no like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    builder
}

async fn concerned_list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let mut count_builder = concerned_sql(&params, true);
    let total: i64 = count_builder.build_query_scalar().fetch_one(&state.db).await?;
    let (offset, limit) = page.resolve(total);
    let mut builder = concerned_sql(&params, false);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(TableDataInfo::new(total, crate::db::rows::rows_to_json(&rows)))
}

async fn export_concerned(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    params.insert("pageNum".to_string(), "1".to_string());
    params.insert("pageSize".to_string(), i32::MAX.to_string());
    let result = concerned_list_all(&state, &params, &page).await?;
    let headers = ["车牌号", "车型", "车种", "逃费类型", "单位编码", "单位名称", "应缴金额", "收费金额", "差额", "异常流水ids"]
        .map(str::to_string);
    let fields = ["car_no", "car_type", "car_vehicle", "escaped_type", "org_id", "org_name", "totalAmount", "chargeAmount", "difAmount", "except_ids"];
    let data = result.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_download("关注车辆", &headers, &data)
}

async fn concerned_list_all(
    state: &AppState,
    params: &HashMap<String, String>,
    page: &crate::common::page::PageDomain,
) -> Result<Vec<Value>, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(
        "select t.id, t.car_no, t.car_type, t.car_vehicle, t.escaped_type, t.org_id, \
         sd.dept_name org_name, k.total_amount totalAmount, k.charge_amount chargeAmount, \
         k.dif_amount difAmount, k.except_ids \
         from car_info t join (select t1.car_no, sum(t1.total_amount) total_amount, \
         sum(t1.charge_amount) charge_amount, sum(t1.dif_amount) dif_amount, \
         sum(case when t1.status = '0' then 1 else 0 end) except_num, count(1) count_num, \
         group_concat(t1.id separator ',') except_ids from car_except_record t1 \
         where t1.del_flag = '0' group by t1.car_no) k on k.count_num > 0 \
         and k.except_num = 0 and t.car_no = k.car_no \
         left join sys_dept sd on sd.dept_id = t.eps_id and sd.del_flag = '0' \
         where t.del_flag = '0'",
    );
    if let Some(value) = params.get("carNoQuery").filter(|v| !v.trim().is_empty()) {
        builder.push(" and t.car_no like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
    let _ = page;
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(crate::db::rows::rows_to_json(&rows))
}

fn statistics_sql(params: &HashMap<String, String>) -> QueryBuilder<'static, MySql> {
    let mut builder = QueryBuilder::<MySql>::new(
        "select d.dept_id eps_id, d.dept_name org_name, a.escaped_type escapedType, \
         sum(ifnull(a.dif_amount, 0)) escapedAmount, count(distinct a.car_no) number \
         from car_except_record a inner join sys_dept d on a.eps_id = d.dept_id \
         and d.del_flag = '0' where a.del_flag = '0'",
    );
    if let Some(value) = params.get("applyTime1").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.create_time >= STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d')");
    }
    if let Some(value) = params.get("applyTime2").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.create_time < date_add(STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d'), interval 1 day)");
    }
    if let Some(value) = params.get("escapedType").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.escaped_type = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = params.get("orgId").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.eps_id = ");
        builder.push_bind(value.clone());
    }
    builder.push(" group by d.dept_id, d.dept_name, a.escaped_type");
    builder
}

async fn car_statics(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let params = support::query_map(&raw);
    let rows = statistics_sql(&params).build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows);
    Ok(TableDataInfo::new(data.len() as i64, data))
}

async fn export_car_statics(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let params = support::query_map(&raw);
    let rows = statistics_sql(&params).build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows);
    let headers = ["单位编码", "单位名称", "逃费类型", "金额", "车辆数"].map(str::to_string);
    let fields = ["eps_id", "org_name", "escapedType", "escapedAmount", "number"];
    let data = data.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_download("车辆统计", &headers, &data)
}

async fn by_except_ids(
    State(state): State<AppState>,
    Path(except_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {} from car_confim_free t left join sys_dept sd on sd.dept_id = t.org_id \
         where t.del_flag = '0' and (",
        SPEC.select
    ));
    let mut separated = builder.separated(" or ");
    for id in except_ids.split(',').filter(|id| !id.is_empty()) {
        separated.push("find_in_set(");
        separated.push_bind_unseparated(id.to_string());
        separated.push_unseparated(", t.except_ids) > 0");
    }
    builder.push(")");
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(AjaxResult::success_data(crate::db::rows::rows_to_json(&rows)))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "车辆id", "车牌号", "车型", "车种", "司机名称", "联系方式", "录入单位id", "录入单位",
        "录入人员ids", "录入人员", "拆分金额", "处理金额", "异常流水ids", "逃费类型s", "比例",
        "备用字段2", "状态", "备注", "应缴金额", "收费金额", "差额",
    ]
    .map(str::to_string);
    let fields = [
        "carId", "carNo", "carType", "carVehicle", "linkName", "linkPhone", "orgId", "org_name",
        "userIds", "userNames", "amount", "aduitAmount", "exceptIds", "escapedTypes", "backCol1",
        "backCol2", "status", "remark", "backCol1", "backCol2", "backCol1",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_download("确认补缴数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id).await?,
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let _ = json!({});
    support::save_or_update(&state, &user, &body, "car_confim_free", "id", true, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_confim_free", "id", true, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_confim_free", "id", &ids).await?;
    Ok(support::success_count(count))
}
