// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarExceptRecordController.java
//       ruoyi-system/src/main/resources/mapper/manager/CarExceptRecordMapper.xml
// 职责: 异常车辆流水列表/统计/导出/CRUD。
// 说明: Excel 导入依赖 ImportSysUtil 多模板校验，暂未迁移（返回明确错误）。

use std::collections::HashMap;

use axum::extract::{Multipart, Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

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
             concat(sd.dept_name, ' ', su.nick_name) createInfo, \n             null as applyTime1, null as applyTime2, null as applyTime3, null as applyTime4, \n             null as createTimeStr, null as orgId, null as exceptIds, null as carNoQuery, \n             null as exceptNum, null as exceptAmount, null as inTimeStr, null as outTimeStr, '0' as supplementaryStatus",
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
        Filter::raw(
            "applyTime1",
            " and t.in_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
        ),
        Filter::raw(
            "applyTime2",
            " and t.out_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
        ),
        Filter::raw(
            "applyTime3",
            " and t.out_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
        ),
        Filter::raw(
            "applyTime4",
            " and t.out_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')",
        ),
        Filter::like("carNoQuery", "t.car_no"),
        Filter::raw("exceptIds", " and find_in_set(t.id, ?) > 0"),
    ],
    extra_where: " and t.del_flag = '0'",
    order_by: "t.create_time desc, t.id",
    id_column: "t.id",
};

pub(crate) const EXCEPT_SPEC: ListSpec = SPEC;

/// Java: CarExceptRecord extends BasePlusEntity 的 Jackson 键顺序。
pub(crate) const EXCEPT_RECORD_KEYS: &[&str] = &[
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

pub(crate) fn shape_except_record_row(row: Value) -> Value {
    support::shape_entity_row(row, EXCEPT_RECORD_KEYS)
}

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
    // Java 侧只有导入用的是「新增流水导入」，其余仍是「异常车辆流水」。
    "新增流水导入",
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
            meta::get_route(
                "/manager/exceptrecord/listCarOrgId",
                None,
                None,
                list_car_org_id,
            ),
        )
        .route(
            "/manager/exceptrecord/listExceptId",
            meta::get_route(
                "/manager/exceptrecord/listExceptId",
                None,
                None,
                list_except_id,
            ),
        )
        .route(
            "/manager/exceptrecord/exceptRecordCount",
            meta::get_route(
                "/manager/exceptrecord/exceptRecordCount",
                None,
                None,
                except_count,
            ),
        )
        .route(
            "/manager/exceptrecord/export",
            meta::get_route(
                "/manager/exceptrecord/export",
                None,
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/manager/exceptrecord/exportOrgId",
            meta::get_route(
                "/manager/exceptrecord/exportOrgId",
                None,
                Some(&LOG_EXPORT),
                export_org,
            ),
        )
        .route(
            "/manager/exceptrecord/getConfirmId/{id}",
            meta::get_route(
                "/manager/exceptrecord/getConfirmId/{id}",
                None,
                None,
                get_confirm_id,
            ),
        )
        .route(
            "/manager/exceptrecord/import",
            meta::post_route(
                "/manager/exceptrecord/import",
                None,
                Some(&LOG_IMPORT),
                import,
            ),
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
            meta::delete_route(
                "/manager/exceptrecord/{ids}",
                None,
                Some(&LOG_REMOVE),
                remove,
            ),
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
    let data = support::shape_rows(rows, EXCEPT_RECORD_KEYS);
    Ok(TableDataInfo::new(total, data))
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
        if params
            .get("carNo")
            .map(|v| v.trim().is_empty())
            .unwrap_or(true)
        {
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
        params
            .entry("epsId".to_string())
            .or_insert_with(|| "-1".to_string());
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
    if params
        .get("carNo")
        .map(|v| v.trim().is_empty())
        .unwrap_or(true)
    {
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
    let row = q.fetch_optional(&state.db).await?;
    Ok(match row {
        Some(row) => AjaxResult::success_data(crate::db::rows::row_to_json(&row)),
        None => AjaxResult::success(),
    })
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    export_rows(&state, &rows).await
}

async fn export_org(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let mut params = support::query_map(&raw);
    params
        .entry("epsId".to_string())
        .or_insert_with(|| "-1".to_string());
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    export_rows(&state, &rows).await
}

async fn export_rows(
    state: &AppState,
    rows: &[Value],
) -> Result<axum::response::Response, AppError> {
    let car_type = support::dict_map(&state.db, "car_type").await?;
    let car_vehicle = support::dict_map(&state.db, "car_vehicle").await?;
    let escaped_type = support::dict_map(&state.db, "escaped_type").await?;
    let status_map = support::dict_map(&state.db, "supplementary_status").await?;
    let headers = [
        "车辆id",
        "车牌号",
        "车型",
        "车种",
        "轴数",
        "通行标识",
        "入口站id",
        "入口站",
        "入口时间",
        "出口站id",
        "出口站",
        "出口时间",
        "应缴金额",
        "收费金额",
        "差额",
        "逃费类型",
        "备注",
        "备用字段1",
        "备用字段2",
        "状态",
        "异常流水ids",
        "车俩查询",
    ]
    .map(str::to_string);
    let fields = [
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
        "backCol1",
        "carNoQuery",
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
                let key = values
                    .get(index)
                    .and_then(Value::as_str)
                    .unwrap_or_default()
                    .to_string();
                if let Some(label) = map.get(&key) {
                    values[index] = Value::String(label.clone());
                }
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_download("异常车辆流水数据", &headers, &data)
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

/// Java: `CarExceptRecordController.initListTwo()` —— 21 列的「列名 / 属性 / 校验规则」。
/// 规则码：1 必填、2 小数、3 正整数、4 日期、5 身份证、6 年月、7 数值、8 年月日时分秒。
const IMPORT_FIELDS: &[crate::common::import_util::ImportField] = &[
    field("序号", "", ""),
    field("出口收费站", "outStation", ""),
    field("出口时间", "outTime", "1,8"),
    field("通行PASSID", "passType", ""),
    field("车牌", "carNo", "1"),
    field("交易车型", "carType", ""),
    field("车种", "carVehicle", ""),
    field("入口站", "inStation", ""),
    field("入口时间", "inTime", "1,8"),
    field("漏交通行费类型", "backCol1", ""),
    field("", "escapedType", "1"),
    field("交易金额", "", ""),
    field("", "", ""),
    field("", "chargeAmount", "1,2"),
    field("应交金额", "", ""),
    field("", "", ""),
    field("", "totalAmount", "1,2"),
    field("实际追交金额", "", ""),
    field("", "", ""),
    field("", "", ""),
    field("备注", "remark", ""),
];

/// Java: `strName` 的长度决定每行读几列（22），`strNum` 是不读的列下标。
const IMPORT_WIDTH: usize = 22;
const IMPORT_SKIP: &[usize] = &[0, 11, 12, 14, 15, 17, 18, 19, 21];
/// Java: `dataRtnExcel08(sheet, strName, strNum, 3)` —— 数据从第 4 行开始。
const IMPORT_DATA_START: usize = 3;

use crate::common::import_util::field;

/// Java: `colVdaExcel08` 用的表头串取自 `initListTwo()` 的列名。
fn import_header() -> Vec<&'static str> {
    IMPORT_FIELDS.iter().map(|field| field.col_name).collect()
}

/// Java: doImport —— 模板校验（第 2 或第 3 行表头）+ 逐行规则校验 + 字典/站点/车辆翻译 + upsert。
async fn import(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    let mut file_name = String::new();
    let mut bytes = Vec::new();
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        if field.file_name().is_some() {
            file_name = field.file_name().unwrap_or_default().to_string();
            bytes = field
                .bytes()
                .await
                .map_err(|err| AppError::BadRequest(err.to_string()))?
                .to_vec();
        }
    }
    // Java: `fileName.lastIndexOf(".xlsx") == -1`
    if !file_name.contains(".xlsx") {
        return Ok(AjaxResult::error("请上传Excel文件(.xlsx)"));
    }

    let rows = crate::common::import_util::read_sheet(&bytes)?;
    let header = import_header();
    if !(crate::common::import_util::header_at(&rows, 1, &header)
        || crate::common::import_util::header_at(&rows, 2, &header))
    {
        return Ok(AjaxResult::error("导入失败,模板不正确,请下载对应的模板！"));
    }
    let sheet_rows =
        crate::common::import_util::data_rows(&rows, IMPORT_DATA_START, IMPORT_WIDTH, IMPORT_SKIP);
    if sheet_rows.is_empty() {
        return Ok(AjaxResult::error(
            "导入失败,模板excel没有数据可以导入，请确定！",
        ));
    }

    let mut errors: Vec<Value> = Vec::new();
    let mut records: Vec<Value> = Vec::new();
    for (index, strs) in sheet_rows.iter().enumerate() {
        // Java: 报错行号实测是「数据行下标 + 2」（`dataRtnExcel08` 从第 4 行读，`getErrorBO` 再 +1）。
        // Java: 只有整份导入还没有任何错误时才会把行转成实体。
        if let Some(object) =
            crate::common::import_util::apply_rules(IMPORT_FIELDS, strs, index + 1, &mut errors)
        {
            records.push(object);
        }
        if errors.len() > 100 {
            break;
        }
    }

    if errors.is_empty() {
        translate_records(&state, &mut records, &mut errors).await?;
    }
    if !errors.is_empty() {
        return Ok(AjaxResult::error("error").put("data", errors));
    }

    save_records(&state, &user, &mut records).await?;
    Ok(AjaxResult::success_msg_data("数据导入成功", records))
}

/// Java: 控制器里 `errorList.size() == 0` 之后的那段字典/站点/车辆翻译。
async fn translate_records(
    state: &AppState,
    records: &mut [Value],
    errors: &mut Vec<Value>,
) -> Result<(), AppError> {
    use crate::common::import_util::error_item;

    // Java: carInfoService.selectCarInfoList(new CarInfo()) —— 带「全部流水都已处理完」的排除条件。
    let cars: Vec<(String, String, Option<i64>)> = sqlx::query_as(
        "select t.car_no, t.id, t.car_num from car_info t where t.del_flag = '0' \
         and not exists (select 1 from (select t1.car_no, \
             sum(case when t1.status = '0' then 1 else 0 end) except_num, count(1) count_num \
             from car_except_record t1 where t1.del_flag = '0' group by t1.car_no) k \
             where t.car_no = k.car_no and k.count_num > 0 and k.except_num = 0)",
    )
    .fetch_all(&state.db)
    .await?;
    let car_map: HashMap<String, (String, Option<i64>)> = cars
        .into_iter()
        .map(|(car_no, id, car_num)| (car_no, (id, car_num)))
        .collect();

    // Java: odsSzdnTollService.selectOdsSzdnTollListNew —— distinct toll_code/toll_name。
    let tolls: Vec<(Option<String>, Option<String>)> =
        sqlx::query_as("select distinct t.toll_code, t.toll_name from ods_szdn_toll t")
            .fetch_all(&state.db)
            .await?;
    let mut toll_map: HashMap<String, String> = HashMap::new();
    for (code, name) in tolls {
        toll_map.insert(name.unwrap_or_default(), code.unwrap_or_default());
    }

    let car_type_map = label_map(&state.db, "car_type_change").await?;
    let escaped_type_map = label_map(&state.db, "escaped_type").await?;
    let plate_color_map = label_map(&state.db, "plate_color").await?;

    for (index, record) in records.iter_mut().enumerate() {
        let row_no = index as i64 + 2;
        // 车型：字典标签 -> 值，再由值推車种。
        let car_type = text_of(record, "carType");
        let car_type = car_type_map.get(&car_type).cloned().unwrap_or(car_type);
        let car_vehicle = match car_type.as_str() {
            "1" | "2" | "3" | "4" => "1",
            "11" | "12" | "13" | "14" | "15" | "16" => "2",
            "21" | "22" | "23" | "24" | "25" | "26" => "3",
            _ => "99",
        };
        put(record, "carType", &car_type);
        put(record, "carVehicle", car_vehicle);

        // 车牌：`车牌_颜色` 形式时拆出颜色并按字典翻译。
        let raw_car_no = text_of(record, "carNo");
        let (car_no, plate_color) = match raw_car_no.split_once('_') {
            Some((head, tail)) => {
                let color = plate_color_map
                    .get(tail)
                    .cloned()
                    .unwrap_or_else(|| tail.to_string());
                (head.to_string(), color)
            }
            None => (raw_car_no.clone(), String::new()),
        };
        put(record, "carNo", &car_no);

        if !car_no.is_empty() {
            match car_map.get(&car_no) {
                Some((id, car_num)) => {
                    put(record, "carId", id);
                    if let Some(car_num) = car_num {
                        put(record, "carNum", &car_num.to_string());
                    }
                }
                // Java: 「车牌号在重点车辆库不存在」的报错行是注释掉的，改为自动补建车辆。
                None => {
                    let mut added = serde_json::Map::new();
                    added.insert("carNo".to_string(), json!(car_no));
                    added.insert("plateColor".to_string(), json!(plate_color));
                    added.insert("carType".to_string(), json!(car_type));
                    added.insert("carVehicle".to_string(), json!(car_vehicle));
                    record
                        .as_object_mut()
                        .expect("对象")
                        .entry("newCar")
                        .or_insert(Value::Object(added));
                }
            }
        }

        // 逃费类型
        let escaped_type = text_of(record, "escapedType");
        if !escaped_type.is_empty() {
            match escaped_type_map.get(&escaped_type) {
                Some(value) => put(record, "escapedType", value),
                None => errors.push(error_item(
                    row_no,
                    "逃费类型",
                    format!("{escaped_type} 逃费类型不存在,请在字典菜单维护！"),
                )),
            }
        }

        // 入口/出口收费站名 -> 编码（Java 只在命中字典时回填 id）。
        for (name_field, id_field) in [("inStation", "inStationId"), ("outStation", "outStationId")]
        {
            let station = text_of(record, name_field);
            if !station.is_empty() {
                if let Some(code) = toll_map.get(&station) {
                    put(record, id_field, code);
                }
            }
        }

        // 金额：应缴 < 实缴 报错；差额 = 应缴 - 实缴（Java 用 BigDecimal）。
        let total = text_of(record, "totalAmount");
        let charge = text_of(record, "chargeAmount");
        if let (Some(total_cents), Some(charge_cents)) =
            (parse_amount(&total), parse_amount(&charge))
        {
            if total_cents < charge_cents {
                errors.push(error_item(
                    row_no,
                    "缴费金额",
                    "收费金额不能大于应缴金额".to_string(),
                ));
            }
        }

        // 时间：入口晚于出口报错。
        let in_time = parse_time(&text_of(record, "inTime"));
        let out_time = parse_time(&text_of(record, "outTime"));
        if let (Some(in_time), Some(out_time)) = (in_time, out_time) {
            if in_time > out_time {
                errors.push(error_item(
                    row_no,
                    "时间",
                    "入口时间大于出口时间，请确认!".to_string(),
                ));
            }
        }

        if errors.len() > 100 {
            break;
        }
    }
    Ok(())
}

/// Java: 无错后先补建车辆，再逐条算差额并按「车牌+入口时间」决定新增还是修改。
async fn save_records(
    state: &AppState,
    user: &LoginUser,
    records: &mut [Value],
) -> Result<(), AppError> {
    for record in records.iter_mut() {
        if let Some(new_car) = record.get("newCar").cloned() {
            // Java: 重复车牌会被 saveCarInfo 内部挡掉，返回值在这里被忽略。
            let _ =
                support::save_or_update(state, user, &new_car, "car_info", "id", true, true).await;
        }
        if let Some(object) = record.as_object_mut() {
            object.remove("newCar");
        }

        let total = text_of(record, "totalAmount");
        let charge = text_of(record, "chargeAmount");
        if let (Some(total), Some(charge)) = (parse_amount(&total), parse_amount(&charge)) {
            put(record, "difAmount", &format_amount(total - charge));
        }

        // Java: 按 carNo + inTime 查已有流水，命中则带 id 走修改。
        let car_no = text_of(record, "carNo");
        let in_time = text_of(record, "inTime");
        if !car_no.is_empty() {
            let existing: Option<String> = sqlx::query_scalar(
                "select id from car_except_record where del_flag = '0' and car_no = ? \
                 and in_time = ? limit 1",
            )
            .bind(&car_no)
            .bind(&in_time)
            .fetch_optional(&state.db)
            .await?;
            if let Some(id) = existing {
                put(record, "id", &id);
            }
        }

        let body = record.clone();
        // Java 响应里带的是内存实体：金额是 BigDecimal，标度取自表格字符串（20 就是 20，不是 20.00），
        // 回读库行会把它们变成 DECIMAL(x,2)，所以先留着保存后再覆盖回去。
        let amounts: Vec<(String, String)> = ["totalAmount", "chargeAmount", "difAmount"]
            .iter()
            .map(|key| ((*key).to_string(), text_of(record, key)))
            .collect();
        // Java: saveCarExceptRecord —— 区间时间重复时直接返回错误、不落库，导入流程忽略它。
        if let Ok(result) =
            support::save_or_update(state, user, &body, "car_except_record", "id", true, true).await
        {
            // 用库里回读的行替换内存值：create_by/create_time/del_flag 等由填充逻辑写入。
            let saved_id = match result.0.get("data") {
                Some(Value::String(text)) => Some(text.clone()),
                _ => None,
            }
            .or_else(|| {
                let current = text_of(record, "id");
                (!current.is_empty()).then_some(current)
            });
            if let Some(id) = saved_id {
                let mut row =
                    support::query_by_id(&state.db, &except_record_lookup_spec(), &id).await?;
                if let Some(row) = row.as_mut() {
                    clear_create_info(&mut Some(row.clone()));
                    *record = shape_except_record_row(row.clone());
                    // Java 返回的是内存实体：MP 的插入填充不会写 delFlag，库里是默认值 '0'。
                    if let Some(object) = record.as_object_mut() {
                        object.insert("delFlag".to_string(), Value::Null);
                    }
                    for (key, value) in &amounts {
                        if value.is_empty() {
                            continue;
                        }
                        // `DecimalFormat("#.##")` 会给出 ".5" 这种写法，补成 0.5 才是合法 JSON 数字。
                        let normalized = match value.strip_prefix('.') {
                            Some(rest) => format!("0{rest}"),
                            None => value.clone(),
                        };
                        let normalized = match value.strip_prefix("-.") {
                            Some(rest) => format!("-0.{rest}"),
                            None => normalized,
                        };
                        match serde_json::from_str::<Value>(&normalized) {
                            Ok(number) => {
                                if let Some(object) = record.as_object_mut() {
                                    object.insert(key.clone(), number);
                                }
                            }
                            // Java: BigDecimal.toPlainString 是数字串；解析不动就原样给。
                            Err(_) => put(record, key, value),
                        }
                    }
                }
            }
        }
    }
    Ok(())
}

/// Java: `selectDictDataLaleMap` —— 标签到值。
async fn label_map(
    pool: &sqlx::MySqlPool,
    dict_type: &str,
) -> Result<HashMap<String, String>, AppError> {
    let rows: Vec<(Option<String>, Option<String>)> = sqlx::query_as(
        "select dict_label, dict_value from sys_dict_data where dict_type = ? order by dict_sort asc",
    )
    .bind(dict_type)
    .fetch_all(pool)
    .await?;
    Ok(rows
        .into_iter()
        .map(|(label, value)| (label.unwrap_or_default(), value.unwrap_or_default()))
        .collect())
}

fn text_of(record: &Value, key: &str) -> String {
    match record.get(key) {
        Some(Value::String(text)) => text.clone(),
        Some(value) if !value.is_null() => value.to_string(),
        _ => String::new(),
    }
}

fn put(record: &mut Value, key: &str, value: &str) {
    if let Some(object) = record.as_object_mut() {
        object.insert(key.to_string(), json!(value));
    }
}

/// Java: `DecimalFormat("#.##")` 出来的串最多两位小数，这里按「分」精确解析。
fn parse_amount(text: &str) -> Option<i64> {
    let text = text.trim();
    if text.is_empty() {
        return None;
    }
    let (sign, body) = match text.strip_prefix('-') {
        Some(rest) => (-1i64, rest),
        None => (1i64, text),
    };
    let body = body.strip_prefix('.').unwrap_or(body);
    let (integer, fraction) = body.split_once('.').unwrap_or((body, ""));
    let integer: i64 = if integer.is_empty() {
        0
    } else {
        integer.parse().ok()?
    };
    let mut fraction = fraction.to_string();
    while fraction.len() < 2 {
        fraction.push('0');
    }
    let fraction: i64 = fraction[..2].parse().ok()?;
    Some(sign * (integer * 100 + fraction))
}

/// Java: `BigDecimal.subtract` 保留两个操作数的最大标度，再去掉多余的尾随 0。
fn format_amount(cents: i64) -> String {
    let sign = if cents < 0 { "-" } else { "" };
    let absolute = cents.abs();
    let integer = absolute / 100;
    let fraction = absolute % 100;
    if fraction == 0 {
        format!("{sign}{integer}")
    } else if fraction % 10 == 0 {
        format!("{sign}{integer}.{}", fraction / 10)
    } else {
        format!("{sign}{integer}.{fraction:02}")
    }
}

fn parse_time(text: &str) -> Option<chrono::NaiveDateTime> {
    chrono::NaiveDateTime::parse_from_str(text.trim(), "%Y-%m-%d %H:%M:%S").ok()
}

/// 回读整行时复用列表查询的列集合。
fn except_record_lookup_spec() -> ListSpec {
    ListSpec {
        select: SPEC.select,
        from: SPEC.from,
        filters: &[],
        extra_where: SPEC.extra_where,
        order_by: "",
        id_column: SPEC.id_column,
    }
}

fn clear_create_info(row: &mut Option<Value>) {
    if let Some(Value::Object(object)) = row.as_mut() {
        object.insert("createInfo".to_string(), Value::Null);
    }
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mut row = support::query_by_id(&state.db, &SPEC, &id)
        .await?
        .map(shape_except_record_row);
    clear_create_info(&mut row);
    Ok(AjaxResult::success_data(row))
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
