// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarConfimFreeController.java
//       ruoyi-system/src/main/resources/mapper/manager/CarConfimFreeMapper.xml
// 职责: 确认补缴 CRUD、关注名单、单位统计。
// 对应关系: selectConcernedList/getPCCarStatistics/selectCarConfimFreeByExceptIds/listCount。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use rust_decimal::{Decimal, RoundingStrategy};
use serde_json::{json, Map, Value};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::manager::{car_aduit_free, car_except_record};
use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

/// Java: CarConfimFree extends BasePlusEntity 的 Jackson 键顺序；
/// Mapper 未查询的属性也要输出（MyBatis 留 null，字段初始化值除外）。
pub(crate) const CONFIM_FREE_KEYS: &[&str] = &[
    "id", "epsId", "delFlag", "createBy", "createTime", "updateBy", "updateTime", "sort",
    "tenantId", "carId", "carNo", "carType", "carVehicle", "linkName", "linkPhone", "orgId",
    "orgName", "userIds", "userNames", "amount", "aduitAmount", "exceptIds", "escapedTypes",
    "backCol1", "backCol2", "status", "remark", "carAduitFreeList", "carExceptRecordList",
    "totalAmount", "chargeAmount", "difAmount", "applyTime1", "applyTime2", "applyTime3",
    "applyTime4", "carNoQuery", "confimFreeNum", "confimFreeAmount", "escapedType",
    "comfimFreeType", "number", "escapedAmount",
];

/// 按实体声明顺序补齐键；缺失补 null，多出的键追加在后。
pub(crate) fn shape_confim_free_row(row: Value) -> Value {
    let source = row.as_object().cloned().unwrap_or_default();
    let mut map = Map::new();
    for key in CONFIM_FREE_KEYS {
        map.insert(
            (*key).to_string(),
            source.get(*key).cloned().unwrap_or(Value::Null),
        );
    }
    // Java: `private Integer number = 0;` / `private BigDecimal escapedAmount = ZERO;`
    for key in ["number", "escapedAmount"] {
        if map.get(key).filter(|v| !v.is_null()).is_none() {
            map.insert(key.to_string(), json!(0));
        }
    }
    for (key, value) in source {
        map.entry(key).or_insert(value);
    }
    Value::Object(map)
}

/// Java: CommonUtil.deleteEnd —— trim 后去掉一个结尾逗号。
fn delete_end(value: Option<&Value>) -> String {
    let text = match value {
        Some(Value::String(text)) => text.trim().to_string(),
        Some(other) if !other.is_null() => other.to_string().trim().to_string(),
        _ => String::new(),
    };
    match text.strip_suffix(',') {
        Some(stripped) => stripped.to_string(),
        None => text,
    }
}

/// Java: BigDecimal 列在实体里的值。
fn decimal_of(value: Option<&Value>) -> Decimal {
    match value {
        Some(Value::Number(number)) => number.to_string().parse::<Decimal>().unwrap_or(Decimal::ZERO),
        Some(Value::String(text)) => text.trim().parse::<Decimal>().unwrap_or(Decimal::ZERO),
        _ => Decimal::ZERO,
    }
}

fn decimal_json(value: Decimal) -> Value {
    value
        .to_string()
        .parse::<serde_json::Number>()
        .map(Value::Number)
        .unwrap_or_else(|_| Value::String(value.to_string()))
}

/// Java: 差额合计非 0 时 `setScale(2, HALF_UP)`。
fn sum_dif_amount(rows: &[Value]) -> Value {
    let mut sum = Decimal::ZERO;
    for row in rows {
        if let Some(value) = row.get("difAmount") {
            if !value.is_null() {
                sum += decimal_of(Some(value));
            }
        }
    }
    if !sum.is_zero() {
        sum = sum.round_dp_with_strategy(2, RoundingStrategy::MidpointAwayFromZero);
    }
    decimal_json(sum)
}

/// Java: CarExceptRecordMapper.selectCarExceptRecordList(exceptIds)
async fn except_records_by_ids(
    state: &AppState,
    except_ids: &str,
) -> Result<Vec<Value>, AppError> {
    let mut params = HashMap::new();
    params.insert("exceptIds".to_string(), except_ids.to_string());
    let rows = support::query_all(&state.db, &params, &car_except_record::EXCEPT_SPEC).await?;
    Ok(support::shape_rows(
        rows,
        car_except_record::EXCEPT_RECORD_KEYS,
    ))
}

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
    // Java: 行是完整的 CarConfimFree POJO，键序按实体声明。
    let data = rows
        .into_iter()
        .map(shape_confim_free_row)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
}

async fn list_car_no(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    if params
        .get("carNo")
        .map(|value| value.trim().is_empty())
        .unwrap_or(true)
    {
        params.insert("carNo".to_string(), "-1".to_string());
    }
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    let data = rows
        .into_iter()
        .map(shape_confim_free_row)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
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

fn push_param_eq(
    builder: &mut QueryBuilder<'_, MySql>,
    params: &HashMap<String, String>,
    key: &str,
    column: &str,
) {
    if let Some(value) = params.get(key).filter(|value| !value.is_empty()) {
        builder.push(" and ");
        builder.push(column);
        builder.push(" = ");
        builder.push_bind(value.clone());
    }
}

fn push_param_like(
    builder: &mut QueryBuilder<'_, MySql>,
    params: &HashMap<String, String>,
    key: &str,
    column: &str,
) {
    if let Some(value) = params.get(key).filter(|value| !value.is_empty()) {
        builder.push(" and ");
        builder.push(column);
        builder.push(" like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
}

fn push_param_date(
    builder: &mut QueryBuilder<'_, MySql>,
    params: &HashMap<String, String>,
    key: &str,
    comparator: &str,
) {
    if let Some(value) = params.get(key).filter(|value| !value.is_empty()) {
        builder.push(" and t.create_time ");
        builder.push(comparator);
        builder.push(" STR_TO_DATE(");
        builder.push_bind(value.clone());
        builder.push(", '%Y-%m-%d %H:%i:%s')");
    }
}

/// Java: selectConcernedList 的 `<if>` 分支（t 是 car_info；
/// carId/userIds/... 在 car_info 中不存在，Java 同样会抛 Unknown column）。
fn push_concerned_filters(
    builder: &mut QueryBuilder<'_, MySql>,
    params: &HashMap<String, String>,
) {
    push_param_eq(builder, params, "id", "t.id");
    push_param_eq(builder, params, "carId", "t.car_id");
    push_param_eq(builder, params, "carNo", "t.car_no");
    push_param_eq(builder, params, "carType", "t.car_type");
    push_param_eq(builder, params, "carVehicle", "t.car_vehicle");
    push_param_like(builder, params, "linkName", "t.link_name");
    push_param_eq(builder, params, "linkPhone", "t.link_phone");
    push_param_eq(builder, params, "orgId", "t.org_id");
    push_param_like(builder, params, "orgName", "sd.dept_name");
    push_param_eq(builder, params, "userIds", "t.user_ids");
    push_param_eq(builder, params, "userNames", "t.user_names");
    push_param_eq(builder, params, "amount", "t.amount");
    push_param_eq(builder, params, "escapedTypes", "t.escaped_types");
    push_param_eq(builder, params, "backCol1", "t.back_col1");
    push_param_eq(builder, params, "backCol2", "t.back_col2");
    push_param_eq(builder, params, "status", "t.status");
    push_param_eq(builder, params, "sort", "t.sort");
    push_param_eq(builder, params, "epsId", "t.eps_id");
    push_param_eq(builder, params, "tenantId", "t.tenant_id");
    push_param_eq(builder, params, "createBy", "t.create_by");
    if let Some(value) = params.get("exceptIds").filter(|value| !value.is_empty()) {
        builder.push(" and find_in_set(t.id, ");
        builder.push_bind(value.clone());
        builder.push(") > 0");
    }
    push_param_like(builder, params, "carNoQuery", "t.car_no");
    push_param_date(builder, params, "applyTime1", ">=");
    push_param_date(builder, params, "applyTime2", "<=");
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
    push_concerned_filters(&mut builder, params);
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
    let data = crate::db::rows::rows_to_json(&rows)
        .into_iter()
        .map(shape_confim_free_row)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
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

fn statistics_sql(params: &HashMap<String, String>, count: bool) -> QueryBuilder<'static, MySql> {
    let select = "select d.dept_id eps_id, d.dept_name org_name, a.escaped_type escapedType, \
         sum(ifnull(a.dif_amount, 0)) escapedAmount, count(distinct a.car_no) number \
         from car_except_record a inner join sys_dept d on a.eps_id = d.dept_id \
         and d.del_flag = '0' where a.del_flag = '0'";
    let mut builder = QueryBuilder::<MySql>::new(if count {
        format!("select count(0) from ({select}")
    } else {
        select.to_string()
    });
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
    if count {
        builder.push(") table_count");
    }
    builder
}

/// Java: CommonUtil.isNull —— null 转空串，其余 toString + trim。
fn text_of(value: Option<&Value>) -> String {
    match value {
        Some(Value::String(text)) => text.trim().to_string(),
        Some(Value::Null) | None => String::new(),
        Some(other) => other.to_string().trim().to_string(),
    }
}

fn int_of(value: Option<&Value>) -> i64 {
    match value {
        Some(Value::Number(number)) => number.as_i64().unwrap_or(0),
        Some(Value::String(text)) => text.trim().parse::<f64>().map(|v| v as i64).unwrap_or(0),
        _ => 0,
    }
}

/// Java: CarConfimFreeServiceImpl.getPCCarStatistics —— 按单位透视为固定 6 类。
fn pivot_car_statistics(rows: &[Value]) -> Vec<Value> {
    let types = ["10", "20", "30", "40", "50", "60"];
    let mut orgs: Vec<(String, String)> = Vec::new();
    let mut cell: HashMap<String, &Value> = HashMap::new();
    for row in rows {
        let eps_id = text_of(row.get("epsId"));
        if eps_id.is_empty() {
            continue;
        }
        if !orgs.iter().any(|(id, _)| id == &eps_id) {
            orgs.push((eps_id.clone(), text_of(row.get("orgName"))));
        }
        let key = format!("{eps_id}{}", text_of(row.get("escapedType")));
        cell.insert(key, row);
    }
    let mut out = Vec::with_capacity(orgs.len());
    for (org_id, org_name) in orgs {
        let mut map = Map::new();
        map.insert("orgId".to_string(), json!(org_id));
        map.insert("orgName".to_string(), json!(org_name));
        let mut total_num: i64 = 0;
        let mut total_amount = Decimal::ZERO;
        for escaped_type in types {
            // Java: 合计恒为 BigDecimal，未命中的类型保持初始值 0 / ZERO。
            let key = format!("{org_id}{escaped_type}");
            let number = match cell.get(&key) {
                Some(row) => int_of((*row).get("number")),
                None => 0,
            };
            let amount = match cell.get(&key) {
                Some(row) => decimal_of((*row).get("escapedAmount")),
                None => Decimal::ZERO,
            };
            map.insert(format!("escapedType{escaped_type}Num"), json!(number));
            map.insert(format!("escapedType{escaped_type}Amount"), decimal_json(amount));
            total_num += number;
            total_amount += amount;
        }
        map.insert("totalNum".to_string(), json!(total_num));
        map.insert(
            "totalAmount".to_string(),
            decimal_json(total_amount.round_dp_with_strategy(
                2,
                RoundingStrategy::MidpointAwayFromZero,
            )),
        );
        map.insert("detailVOList".to_string(), Value::Null);
        out.push(Value::Object(map));
    }
    out
}

async fn car_statics(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    // Java: startPage() 先分页「分组行」，再在内存里透视；total 取透视后的单位数。
    let mut count_builder = statistics_sql(&params, true);
    let group_total: i64 = count_builder.build_query_scalar().fetch_one(&state.db).await?;
    let (offset, limit) = page.resolve(group_total);
    let mut builder = statistics_sql(&params, false);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    let grouped = crate::db::rows::rows_to_json(&rows);
    let data = pivot_car_statistics(&grouped);
    Ok(TableDataInfo::new(data.len() as i64, data))
}

async fn export_car_statics(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let params = support::query_map(&raw);
    let rows = statistics_sql(&params, false).build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows);
    let headers = ["单位编码", "单位名称", "逃费类型", "金额", "车辆数"].map(str::to_string);
    let fields = ["epsId", "orgName", "escapedType", "escapedAmount", "number"];
    let data = data.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_download("车辆统计", &headers, &data)
}

/// Java: CarConfimFreeMapper.selectCarConfimFreeByExceptIds —— 是否已生成过补缴单。
async fn already_confirmed(state: &AppState, except_ids: &str) -> Result<bool, AppError> {
    let ids: Vec<&str> = except_ids.split(',').filter(|id| !id.trim().is_empty()).collect();
    if ids.is_empty() {
        return Ok(false);
    }
    let mut builder = QueryBuilder::<MySql>::new(
        "select t.id from car_confim_free t where t.del_flag = '0' and (",
    );
    let mut separated = builder.separated(" or ");
    for id in &ids {
        separated.push("find_in_set(");
        separated.push_bind_unseparated(id.to_string());
        separated.push_unseparated(", t.except_ids) > 0");
    }
    builder.push(")");
    let rows = builder.build().fetch_all(&state.db).await?;
    Ok(!rows.is_empty())
}

/// Java: Long 的字符串形式（null 时 `epsList.get(0)+""` 得到 "null"）。
fn java_to_string(value: Option<&Value>) -> String {
    match value {
        None | Some(Value::Null) => "null".to_string(),
        Some(Value::String(text)) => text.clone(),
        Some(other) => other.to_string(),
    }
}

async fn by_except_ids(
    State(state): State<AppState>,
    Path(except_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: CarConfimFreeServiceImpl.selectCarConfimFreeByExceptIds 的校验顺序。
    let cleaned = delete_end(Some(&Value::String(except_ids)));
    if cleaned.trim().is_empty() {
        return Ok(AjaxResult::error("请选择车辆异常流水！"));
    }
    let records = except_records_by_ids(&state, &cleaned).await?;
    if records.is_empty() {
        return Ok(AjaxResult::error("异常车辆流水不存在！"));
    }
    let distinct = |key: &str| -> Vec<String> {
        let mut out: Vec<String> = Vec::new();
        for record in &records {
            let value = java_to_string(record.get(key));
            if !out.contains(&value) {
                out.push(value);
            }
        }
        out
    };
    if distinct("carNo").len() > 1 {
        return Ok(AjaxResult::error("请勿选择多辆车！"));
    }
    let eps_list = distinct("epsId");
    if eps_list.len() > 1 {
        return Ok(AjaxResult::error("选择的异常流水存在多个录入单位，请确认！"));
    }
    if already_confirmed(&state, &cleaned).await? {
        return Ok(AjaxResult::error("车辆补缴单已追缴，请勿重复补缴！"));
    }

    let first = records.first().cloned().unwrap_or(Value::Null);
    let mut map = Map::new();
    for key in ["carId", "carNo", "carType", "carVehicle"] {
        map.insert(key.to_string(), first.get(key).cloned().unwrap_or(Value::Null));
    }
    map.insert("exceptIds".to_string(), json!(cleaned));
    map.insert(
        "orgId".to_string(),
        match eps_list.first() {
            Some(value) if value != "null" => json!(value.clone()),
            Some(_) => Value::Null,
            None => Value::Null,
        },
    );
    map.insert("carExceptRecordList".to_string(), Value::Array(records.clone()));

    let mut raw_sum = Decimal::ZERO;
    for record in &records {
        if record.get("difAmount").map(|v| !v.is_null()).unwrap_or(false) {
            raw_sum += decimal_of(record.get("difAmount"));
        }
    }
    // Java: new BigDecimal("0.3")
    let bite = Decimal::new(3, 1);
    let amount = raw_sum * bite;
    let mut dif_amount = raw_sum;
    if !dif_amount.is_zero() {
        dif_amount = dif_amount.round_dp_with_strategy(2, RoundingStrategy::MidpointAwayFromZero);
    }
    map.insert("difAmount".to_string(), decimal_json(dif_amount));
    map.insert("backCol1".to_string(), json!("0.3"));
    map.insert(
        "amount".to_string(),
        decimal_json(amount.round_dp_with_strategy(2, RoundingStrategy::MidpointAwayFromZero)),
    );
    Ok(AjaxResult::success_data(shape_confim_free_row(Value::Object(
        map,
    ))))
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
    // Java: CarConfimFreeServiceImpl.selectCarConfimFreeById —— 详情要回填异常流水与审核明细。
    let Some(mut row) = support::query_by_id(&state.db, &SPEC, &id).await? else {
        return Ok(AjaxResult::success());
    };
    let has_id = row
        .get("id")
        .and_then(Value::as_str)
        .map(|value| !value.is_empty())
        .unwrap_or(false);
    if has_id {
        let except_ids = delete_end(row.get("exceptIds"));
        if !except_ids.trim().is_empty() {
            let records = except_records_by_ids(&state, &except_ids).await?;
            row.as_object_mut()
                .expect("object")
                .insert("carExceptRecordList".to_string(), Value::Array(records.clone()));
            row.as_object_mut().expect("object").insert(
                "difAmount".to_string(),
                sum_dif_amount(&records),
            );
        }
        let mut params = HashMap::new();
        params.insert("confirmId".to_string(), id.clone());
        let aduits = support::query_all(&state.db, &params, &car_aduit_free::SPEC).await?;
        let aduits = support::shape_rows(aduits, car_aduit_free::ADUIT_FREE_KEYS);
        row.as_object_mut()
            .expect("object")
            .insert("carAduitFreeList".to_string(), Value::Array(aduits));
    }
    Ok(AjaxResult::success_data(shape_confim_free_row(row)))
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
