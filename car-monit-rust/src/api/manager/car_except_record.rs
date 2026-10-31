// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarExceptRecordController.java
//       ruoyi-system/src/main/resources/mapper/manager/CarExceptRecordMapper.xml
// 职责: 异常车辆流水列表/统计/导出/CRUD。
// 说明: Excel 导入依赖 ImportSysUtil 多模板校验，暂未迁移（返回明确错误）。

use std::collections::HashMap;

use axum::extract::{Multipart, Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.car_num, t.pass_type, \
             t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, \
             t.out_time, t.total_amount, t.charge_amount, t.dif_amount, t.escaped_type, \
             t.remark, t.back_col1, t.back_col2, t.status, t.sort, t.eps_id, t.del_flag, \
             t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id, \
             concat(sd.dept_name, ' ', su.nick_name) createInfo",
    from: "from car_except_record t left join sys_user su on su.user_id = t.create_by \
           left join sys_dept sd on t.eps_id = sd.dept_id",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("carId", "t.car_id"),
        Filter::eq("carNo", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::eq("carNum", "t.car_num"),
        Filter::eq("passType", "t.pass_type"),
        Filter::eq("inStationId", "t.in_station_id"),
        Filter::like("inStation", "t.in_station"),
        Filter::eq("inTime", "t.in_time"),
        Filter::eq("outStationId", "t.out_station_id"),
        Filter::like("outStation", "t.out_station"),
        Filter::eq("outTime", "t.out_time"),
        Filter::eq("totalAmount", "t.total_amount"),
        Filter::eq("chargeAmount", "t.charge_amount"),
        Filter::eq("difAmount", "t.dif_amount"),
        Filter::eq("escapedType", "t.escaped_type"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
        Filter::raw("applyTime1", " and t.in_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
        Filter::raw("applyTime2", " and t.out_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
        Filter::raw("applyTime3", " and t.out_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
        Filter::raw("applyTime4", " and t.out_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
        Filter::like("carNoQuery", "t.car_no"),
        Filter::raw("exceptIds", " and find_in_set(t.id, ?) > 0"),
    ],
    extra_where: "",
    order_by: "t.create_time desc, t.id",
    id_column: "t.id",
};

pub(crate) const EXCEPT_SPEC: ListSpec = SPEC;

static LOG_EXPORT: LogSpec = LogSpec::new(
    "异常车辆流水",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarExceptRecordController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "异常车辆流水",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.CarExceptRecordController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "异常车辆流水",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarExceptRecordController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "异常车辆流水",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.CarExceptRecordController.remove()",
);
static LOG_IMPORT: LogSpec = LogSpec::new(
    "异常车辆流水",
    BusinessType::Import,
    "com.ruoyi.web.controller.manager.CarExceptRecordController.doImport()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/exceptrecord/list",
            meta::get_route("/manager/exceptrecord/list", None, None, list),
        )
        .route(
            "/manager/exceptrecord/listCarNo",
            meta::get_route("/manager/exceptrecord/listCarNo", None, None, list_car_no),
        )
        .route(
            "/manager/exceptrecord/listCarOrgId",
            meta::get_route("/manager/exceptrecord/listCarOrgId", None, None, list_car_org_id),
        )
        .route(
            "/manager/exceptrecord/listExceptId",
            meta::get_route("/manager/exceptrecord/listExceptId", None, None, list_except_id),
        )
        .route(
            "/manager/exceptrecord/exceptRecordCount",
            meta::get_route("/manager/exceptrecord/exceptRecordCount", None, None, except_count),
        )
        .route(
            "/manager/exceptrecord/export",
            meta::get_route("/manager/exceptrecord/export", None, Some(&LOG_EXPORT), export),
        )
        .route(
            "/manager/exceptrecord/exportOrgId",
            meta::get_route("/manager/exceptrecord/exportOrgId", None, Some(&LOG_EXPORT), export_org),
        )
        .route(
            "/manager/exceptrecord/getConfirmId/{id}",
            meta::get_route("/manager/exceptrecord/getConfirmId/{id}", None, None, get_confirm_id),
        )
        .route(
            "/manager/exceptrecord/import",
            meta::post_route("/manager/exceptrecord/import", None, Some(&LOG_IMPORT), import),
        )
        .route(
            "/manager/exceptrecord/{ids}",
            meta::get_route("/manager/exceptrecord/{ids}", None, None, get_info),
        )
        .route(
            "/manager/exceptrecord",
            meta::post_route("/manager/exceptrecord", None, Some(&LOG_ADD), add).merge(
                meta::put_route("/manager/exceptrecord", None, Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/manager/exceptrecord/{ids}",
            meta::delete_route("/manager/exceptrecord/{ids}", None, Some(&LOG_REMOVE), remove),
        )
}

async fn query(
    state: &AppState,
    raw: Option<String>,
    mutate: impl FnOnce(&mut HashMap<String, String>),
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let mut params = support::query_map(&raw);
    mutate(&mut params);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    query(&state, raw, |_| {}).await
}

async fn list_car_no(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    query(&state, raw, |params| {
        if params.get("carNo").map(|v| v.trim().is_empty()).unwrap_or(true) {
            params.insert("carNo".to_string(), "-1".to_string());
        }
    })
    .await
}

async fn list_car_org_id(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    query(&state, raw, |params| {
        params.entry("epsId".to_string()).or_insert_with(|| "-1".to_string());
    })
    .await
}

async fn list_except_id(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    query(&state, raw, |params| {
        if params
            .get("exceptIds")
            .map(|v| v.trim().is_empty())
            .unwrap_or(true)
        {
            params.insert("exceptIds".to_string(), "-1".to_string());
        }
    })
    .await
}

async fn except_count(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let mut params = support::query_map(&raw);
    if params.get("carNo").map(|v| v.trim().is_empty()).unwrap_or(true) {
        params.insert("carNo".to_string(), "-1".to_string());
    }
    let car_no = params.get("carNo").cloned().unwrap_or_default();
    let mut sql = String::from(
        "select t.car_no, count(1) exceptNum, round(sum(t.dif_amount),2) exceptAmount, \
         round(sum(t.total_amount),2) total_amount, round(sum(t.charge_amount),2) charge_amount \
         from car_except_record t where t.del_flag = '0' and t.car_no = ?",
    );
    let status = params.get("status").cloned().unwrap_or_default();
    if !status.is_empty() {
        sql.push_str(" and t.status = ?");
    }
    sql.push_str(" group by t.car_no");
    let mut q = sqlx::query(&sql).bind(car_no);
    if !status.is_empty() {
        q = q.bind(status);
    }
    let rows = q.fetch_all(&state.db).await?;
    Ok(AjaxResult::success_data(crate::db::rows::rows_to_json(&rows)))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    export_rows(&state, &rows).await
}

async fn export_org(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let mut params = support::query_map(&raw);
    params.entry("epsId".to_string()).or_insert_with(|| "-1".to_string());
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    export_rows(&state, &rows).await
}

async fn export_rows(state: &AppState, rows: &[Value]) -> Result<AjaxResult, AppError> {
    let car_type = support::dict_map(&state.db, "car_type").await?;
    let car_vehicle = support::dict_map(&state.db, "car_vehicle").await?;
    let escaped_type = support::dict_map(&state.db, "escaped_type").await?;
    let status_map = support::dict_map(&state.db, "supplementary_status").await?;
    let headers = [
        "车辆id", "车牌号", "车型", "车种", "轴数", "通行标识", "入口站id", "入口站", "入口时间",
        "出口站id", "出口站", "出口时间", "应缴金额", "收费金额", "差额", "逃费类型", "备注",
        "备用字段1", "备用字段2", "状态", "异常流水ids", "车俩查询",
    ]
    .map(str::to_string);
    let fields = [
        "carId", "carNo", "carType", "carVehicle", "carNum", "passType", "inStationId",
        "inStation", "inTime", "outStationId", "outStation", "outTime", "totalAmount",
        "chargeAmount", "difAmount", "escapedType", "remark", "backCol1", "backCol2", "status",
        "backCol1", "carNoQuery",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            for (index, map) in [
                (2usize, &car_type),
                (3usize, &car_vehicle),
                (15usize, &escaped_type),
                (19usize, &status_map),
            ] {
                let key = values.get(index).and_then(Value::as_str).unwrap_or_default().to_string();
                if let Some(label) = map.get(&key) {
                    values[index] = Value::String(label.clone());
                }
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(state, "异常车辆流水数据", &headers, &data)
}

async fn get_confirm_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let found = sqlx::query_scalar::<_, String>(
        "select id from car_confim_free where del_flag = '0' and find_in_set(?, except_ids) > 0 limit 1",
    )
    .bind(&id)
    .fetch_optional(&state.db)
    .await?;
    Ok(AjaxResult::success_data(found))
}

async fn import(
    State(_state): State<AppState>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    // 读取并丢弃上传内容，保持与 Java 相同的 multipart 入口。
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        let _ = field.bytes().await;
    }
    Ok(AjaxResult::error(
        "异常流水导入依赖 ImportSysUtil 模板校验，Rust 迁移版本暂未提供",
    ))
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
    support::save_or_update(&state, &user, &body, "car_except_record", "id", true, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_except_record", "id", true, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_except_record", "id", &ids).await?;
    Ok(support::success_count(count))
}
