// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarAduitFreeController.java
//       ruoyi-system/src/main/resources/mapper/manager/CarAduitFreeMapper.xml
// 职责: 追缴审核流水 CRUD、收入统计与明细。
// 对应关系: incomeStatistic/PCIncomeStatics/incomeDetailList -> 同名 SQL。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{Map, Value};
use sqlx::mysql::MySql;
use sqlx::QueryBuilder;

use crate::api::manager::car_confim_free;
use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

pub(crate) const SPEC: ListSpec = ListSpec {
    select: "t.id, t.confirm_id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.org_id, \
             t.user_ids, t.user_names, t.amount, t.back_col1, t.back_col2, t.remark, t.status, \
             t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, \
             t.update_time, t.tenant_id, d.dept_name org_name, \n             null as applyTime1, null as applyTime2",
    from: "from car_aduit_free t left join sys_dept d on d.dept_id = t.org_id and d.del_flag = '0'",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("confirmId", "t.confirm_id"),
        Filter::eq("carId", "t.car_id"),
        Filter::like("carNo", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::eq("orgId", "t.org_id"),
        Filter::like("orgName", "d.dept_name"),
        Filter::eq("userIds", "t.user_ids"),
        Filter::eq("userNames", "t.user_names"),
        Filter::eq("amount", "t.amount"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time, t.id",
    id_column: "t.id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "追缴审核",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarAduitFreeController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "追缴审核",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.CarAduitFreeController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "追缴审核",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarAduitFreeController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "追缴审核",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.CarAduitFreeController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/aduitfree/list",
            meta::get_route("/manager/aduitfree/list", None, None, list),
        )
        .route(
            "/manager/aduitfree/export",
            meta::get_route("/manager/aduitfree/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/manager/aduitfree/incomeStatics",
            meta::get_route(
                "/manager/aduitfree/incomeStatics",
                None,
                None,
                income_statics,
            ),
        )
        .route(
            "/manager/aduitfree/exportIncomeStatics",
            meta::get_route(
                "/manager/aduitfree/exportIncomeStatics",
                None,
                Some(&LOG_EXPORT),
                export_income_statics,
            ),
        )
        .route(
            "/manager/aduitfree/incomeDetailList",
            meta::get_route(
                "/manager/aduitfree/incomeDetailList",
                None,
                None,
                income_details,
            ),
        )
        .route(
            "/manager/aduitfree/exportIncomeDetailList",
            meta::get_route(
                "/manager/aduitfree/exportIncomeDetailList",
                None,
                Some(&LOG_EXPORT),
                export_income_details,
            ),
        )
        .route(
            "/manager/aduitfree/{ids}",
            meta::get_route("/manager/aduitfree/{ids}", None, None, get_info),
        )
        .route(
            "/manager/aduitfree",
            meta::post_route("/manager/aduitfree", None, Some(&LOG_ADD), add).merge(
                meta::put_route("/manager/aduitfree", None, Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/manager/aduitfree/{ids}",
            meta::delete_route("/manager/aduitfree/{ids}", None, Some(&LOG_REMOVE), remove),
        )
}

/// Java: CarAduitFree extends BasePlusEntity 的 Jackson 键顺序。
pub(crate) const ADUIT_FREE_KEYS: &[&str] = &[
    "id",
    "epsId",
    "delFlag",
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "sort",
    "tenantId",
    "confirmId",
    "carId",
    "carNo",
    "carType",
    "carVehicle",
    "orgId",
    "orgName",
    "userIds",
    "userNames",
    "amount",
    "backCol1",
    "backCol2",
    "status",
    "remark",
    "applyTime1",
    "applyTime2",
];

pub(crate) fn shape_aduit_free_row(row: Value) -> Value {
    support::shape_entity_row(row, ADUIT_FREE_KEYS)
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    let data = rows
        .into_iter()
        .map(shape_aduit_free_row)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "确认补缴id",
        "车辆id",
        "车牌号",
        "车型",
        "车种",
        "处理单位id",
        "处理单位",
        "处理人员ids",
        "处理人员",
        "拆分金额",
        "备用字段1",
        "备用字段2",
        "状态",
        "备注",
    ]
    .map(str::to_string);
    let fields = [
        "confirmId",
        "carId",
        "carNo",
        "carType",
        "carVehicle",
        "orgId",
        "orgName",
        "userIds",
        "userNames",
        "amount",
        "backCol1",
        "backCol2",
        "status",
        "remark",
    ];
    let data = rows
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_excel(&state, "补缴处理数据", &headers, &data)
}

/// 收入统计（单位维度）。
fn income_sql(params: &HashMap<String, String>) -> QueryBuilder<'static, MySql> {
    let mut builder = QueryBuilder::<MySql>::new(
        "select sum(t.amount) amount, count(distinct t.car_no) carNum, t.org_id, t.orgName \
         from (select ifnull(a.amount, 0) amount, a.car_no, a.org_id, d.dept_name orgName \
         from car_aduit_free a left join sys_dept d on d.dept_id = a.org_id \
         where a.del_flag = '0' and a.status = '0'",
    );
    push_detail_filters(&mut builder, params);
    builder.push(
        " union all select ifnull(a.amount, 0) amount, a.car_no, a.org_id, d.dept_name orgName \
         from car_confim_free a left join sys_dept d on d.dept_id = a.org_id \
         where a.del_flag = '0'",
    );
    push_detail_filters(&mut builder, params);
    builder.push(") t group by t.org_id, t.orgName order by amount desc");
    builder
}

fn push_detail_filters(builder: &mut QueryBuilder<'_, MySql>, params: &HashMap<String, String>) {
    if let Some(value) = params.get("orgId").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.org_id = ");
        builder.push_bind(value.clone());
    }
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
    if let Some(value) = params.get("carNo").filter(|v| !v.trim().is_empty()) {
        builder.push(" and a.car_no like concat('%', ");
        builder.push_bind(value.clone());
        builder.push(", '%')");
    }
}

/// Java: PCIncomeStaticsVO 的声明顺序（orgId, orgName, amount, carNum）。
fn shape_income_statics_row(row: Value) -> Value {
    let mut map = Map::new();
    for key in ["orgId", "orgName", "amount", "carNum"] {
        map.insert(
            key.to_string(),
            row.get(key).cloned().unwrap_or(Value::Null),
        );
    }
    Value::Object(map)
}

async fn income_statics(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    // Java: startPage() 恒为 (1,10)，先数分组行数，再 limit/offset 取页。
    let mut count_builder = QueryBuilder::<MySql>::new(
        "select count(0) from (select sum(t.amount) amount, count(distinct t.car_no) carNum, \
         t.org_id, t.orgName from (select ifnull(a.amount, 0) amount, a.car_no, a.org_id, \
         d.dept_name orgName from car_aduit_free a left join sys_dept d on d.dept_id = a.org_id \
         where a.del_flag = '0' and a.status = '0'",
    );
    push_detail_filters(&mut count_builder, &params);
    count_builder.push(
        " union all select ifnull(a.amount, 0) amount, a.car_no, a.org_id, d.dept_name orgName \
         from car_confim_free a left join sys_dept d on d.dept_id = a.org_id \
         where a.del_flag = '0'",
    );
    push_detail_filters(&mut count_builder, &params);
    count_builder.push(") t group by t.org_id, t.orgName) table_count");
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;
    let (offset, limit) = page.resolve(total);
    let mut builder = income_sql(&params);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows)
        .into_iter()
        .map(shape_income_statics_row)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
}

async fn export_income_statics(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let params = support::query_map(&raw);
    let rows = income_sql(&params).build().fetch_all(&state.db).await?;
    let data = crate::db::rows::rows_to_json(&rows);
    let headers = ["金额", "车辆数", "单位编码", "单位名称"].map(str::to_string);
    let fields = ["amount", "carNum", "orgId", "orgName"];
    let data = data
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_download("收入统计", &headers, &data)
}

fn detail_sql(params: &HashMap<String, String>, count: bool) -> QueryBuilder<'static, MySql> {
    let first_select = "select ifnull(a.amount, 0) amount, a.car_no, a.org_id, \
         d.dept_name orgName, a.create_time from car_aduit_free a \
         left join sys_dept d on d.dept_id = a.org_id \
         where a.del_flag = '0' and a.status = '0'";
    let second_select = " union all select ifnull(a.amount, 0) amount, a.car_no, a.org_id, \
         d.dept_name orgName, a.create_time from car_confim_free a \
         left join sys_dept d on d.dept_id = a.org_id where a.del_flag = '0'";
    let mut builder = QueryBuilder::<MySql>::new(if count {
        format!("select count(0) from ({first_select}")
    } else {
        format!("select t.* from ({first_select}")
    });
    push_detail_filters(&mut builder, params);
    builder.push(second_select);
    push_detail_filters(&mut builder, params);
    builder.push(") t");
    if !count {
        builder.push(" order by t.create_time desc");
    }
    builder
}

async fn income_details(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    // Java: 控制器把空 orgId 替换成哨兵 "-1"，因此无参数时结果恒为空。
    if params
        .get("orgId")
        .map(|value| value.trim().is_empty())
        .unwrap_or(true)
    {
        params.insert("orgId".to_string(), "-1".to_string());
    }
    let mut count_builder = detail_sql(&params, true);
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;
    if total == 0 {
        // Java: PageHelper 在 count=0 时不再执行列表查询。
        return Ok(TableDataInfo::new(0, Vec::new()));
    }
    let mut builder = detail_sql(&params, false);
    let (offset, limit) = page.resolve(total);
    builder.push(" limit ");
    builder.push_bind(limit);
    builder.push(" offset ");
    builder.push_bind(offset);
    let rows = builder.build().fetch_all(&state.db).await?;
    // Java: 返回体是整个 CarConfimFree POJO（43 个键，未映射的为 null）。
    let data = crate::db::rows::rows_to_json(&rows)
        .into_iter()
        .map(car_confim_free::shape_confim_free_row)
        .collect::<Vec<_>>();
    Ok(TableDataInfo::new(total, data))
}

async fn export_income_details(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let params = support::query_map(&raw);
    let rows = detail_sql(&params, false)
        .build()
        .fetch_all(&state.db)
        .await?;
    let data = crate::db::rows::rows_to_json(&rows);
    let headers = ["金额", "车牌号", "单位编码", "单位名称", "时间"].map(str::to_string);
    let fields = ["amount", "carNo", "orgId", "orgName", "createTime"];
    let data = data
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_download("收入明细", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let row = support::query_by_id(&state.db, &SPEC, &id)
        .await?
        .map(shape_aduit_free_row);
    Ok(AjaxResult::success_data(row))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_aduit_free", "id", true, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_aduit_free", "id", true, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_aduit_free", "id", &ids).await?;
    Ok(support::success_count(count))
}
