// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarInfoController.java
//       ruoyi-system/src/main/resources/mapper/manager/CarInfoMapper.xml
// 职责: 车辆信息 CRUD、列表/导出、Excel 导入。
// 对应关系: selectCarInfoList -> SPEC；import -> excel::read_rows + 字典翻译。

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
    select: "t.id, t.car_no, t.car_type, t.car_vehicle, t.car_num, t.escaped_type, \
             t.escaped_type_name, t.escaped_amount, t.escaped_num, t.return_amount, \
             t.total_amount, t.charge_amount, t.dif_amount, t.auit_org_id, t.auit_org_name, \
             t.is_white, t.white_remark, t.file_ids, t.brand, t.plate_color, t.plate_type, \
             t.car_color, t.data_source, t.data_source_name, t.last_pass_time, \
             t.last_pass_picture, t.last_pass_type, t.last_pass_address, \
             t.last_pass_longitude, t.last_pass_latitude, t.last_pass_cardirection, \
             t.road_section_id, t.section_code, t.road_section_name, t.next_pass_time, \
             t.next_pass_type, t.next_pass_address, t.next_pass_longitude, \
             t.next_pass_latitude, t.track_id, t.org_id, t.org_code, t.org_name, t.gantry_code, \
             t.road_code, t.road_name, t.toll_code, t.toll_name, t.link_name, t.link_phone, \
             t.fwqbm, t.fwqmc, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, \
             t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id, \
             concat(sd.dept_name, ' ', su.nick_name) createInfo, \n             null as trackJosn, null as applyTime1, null as applyTime2, null as carNoQuery, \n             null as createTimeStr, null as trailList, null as flag",
    from: "from car_info t left join sys_user su on su.user_id = t.create_by \
           left join sys_dept sd on t.eps_id = sd.dept_id",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("carNo", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::eq("carNum", "t.car_num"),
        Filter::like("escapedType", "t.escaped_type"),
        Filter::like("escapedTypeName", "t.escaped_type_name"),
        Filter::eq("escapedAmount", "t.escaped_amount"),
        Filter::eq("escapedNum", "t.escaped_num"),
        Filter::eq("returnAmount", "t.return_amount"),
        Filter::eq("totalAmount", "t.total_amount"),
        Filter::eq("chargeAmount", "t.charge_amount"),
        Filter::eq("difAmount", "t.dif_amount"),
        Filter::eq("auitOrgId", "t.auit_org_id"),
        Filter::like("auitOrgName", "t.auit_org_name"),
        Filter::eq("isWhite", "t.is_white"),
        Filter::eq("whiteRemark", "t.white_remark"),
        Filter::eq("fileIds", "t.file_ids"),
        Filter::eq("brand", "t.brand"),
        Filter::eq("plateColor", "t.plate_color"),
        Filter::eq("plateType", "t.plate_type"),
        Filter::eq("carColor", "t.car_color"),
        Filter::eq("dataSource", "t.data_source"),
        Filter::like("dataSourceName", "t.data_source_name"),
        Filter::eq("lastPassTime", "t.last_pass_time"),
        Filter::eq("lastPassPicture", "t.last_pass_picture"),
        Filter::eq("lastPassType", "t.last_pass_type"),
        Filter::eq("lastPassAddress", "t.last_pass_address"),
        Filter::eq("lastPassLongitude", "t.last_pass_longitude"),
        Filter::eq("lastPassLatitude", "t.last_pass_latitude"),
        Filter::eq("lastPassCardirection", "t.last_pass_cardirection"),
        Filter::eq("roadSectionId", "t.road_section_id"),
        Filter::eq("sectionCode", "t.section_code"),
        Filter::like("roadSectionName", "t.road_section_name"),
        Filter::eq("nextPassTime", "t.next_pass_time"),
        Filter::eq("nextPassType", "t.next_pass_type"),
        Filter::eq("nextPassAddress", "t.next_pass_address"),
        Filter::eq("nextPassLongitude", "t.next_pass_longitude"),
        Filter::eq("nextPassLatitude", "t.next_pass_latitude"),
        Filter::eq("orgId", "t.org_id"),
        Filter::eq("orgCode", "t.org_code"),
        Filter::like("orgName", "t.org_name"),
        Filter::eq("gantryCode", "t.gantry_code"),
        Filter::eq("roadCode", "t.road_code"),
        Filter::like("roadName", "t.road_name"),
        Filter::eq("tollCode", "t.toll_code"),
        Filter::like("tollName", "t.toll_name"),
        Filter::like("linkName", "t.link_name"),
        Filter::eq("linkPhone", "t.link_phone"),
        Filter::eq("fwqbm", "t.fwqbm"),
        Filter::eq("fwqmc", "t.fwqmc"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
        Filter::like("carNoQuery", "t.car_no"),
        Filter::raw(
            "applyTime1",
            " and t.create_time >= STR_TO_DATE(?, '%Y-%m-%d')",
        ),
        Filter::raw(
            "applyTime2",
            " and t.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)",
        ),
        Filter::raw("createInfo", " and sd.dept_name like concat('%', ?, '%')"),
        Filter::raw(
            "flag",
            " and not exists ( select 1 from zdata_trail_tracks tr where tr.plate_key = t.car_no )",
        ),
    ],
    extra_where: " and t.del_flag = '0' and not exists ( select 1 from (select t1.car_no, \
                  sum(case when t1.status = '0' then 1 else 0 end) except_num, \
                  count(1) count_num from car_except_record t1 where t1.del_flag = '0' \
                  group by t1.car_no) k where t.car_no = k.car_no and k.count_num > 0 \
                  and k.except_num = 0 )",
    order_by: "t.create_time desc, t.id",
    id_column: "t.id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.manager.CarInfoController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.manager.CarInfoController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.manager.CarInfoController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.manager.CarInfoController.remove()",
);
static LOG_IMPORT: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Import,
    "com.ruoyi.web.controller.manager.CarInfoController.doImport()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/manager/carinfo/list",
            meta::get_route("/manager/carinfo/list", Some("manager:carinfo:list"), None, list),
        )
        .route(
            "/manager/carinfo/listAll",
            meta::get_route("/manager/carinfo/listAll", None, None, list),
        )
        .route(
            "/manager/carinfo/export",
            meta::get_route(
                "/manager/carinfo/export",
                Some("manager:carinfo:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/manager/carinfo/import",
            meta::post_route(
                "/manager/carinfo/import",
                None,
                Some(&LOG_IMPORT),
                import,
            ),
        )
        .route(
            "/manager/carinfo/{ids}",
            meta::get_route("/manager/carinfo/{ids}", None, None, get_info),
        )
        .route(
            "/manager/carinfo",
            meta::post_route("/manager/carinfo", None, Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/manager/carinfo",
                    Some("manager:carinfo:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/manager/carinfo/{ids}",
            meta::delete_route(
                "/manager/carinfo/{ids}",
                Some("manager:carinfo:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java Jackson 的 CarInfo 键序（实体声明顺序 + 派生 applyTime*/carNoQuery/createInfo/trailList/flag）。
const CAR_INFO_KEYS: &[&str] = &[
    "id", "epsId", "delFlag", "createBy", "createTime", "updateBy", "updateTime", "sort",
    "tenantId", "carNo", "carType", "carVehicle", "carNum", "escapedType", "escapedTypeName",
    "escapedAmount", "escapedNum", "returnAmount", "totalAmount", "chargeAmount", "difAmount",
    "auitOrgId", "auitOrgName", "isWhite", "whiteRemark", "fileIds", "brand", "plateColor",
    "plateType", "carColor", "dataSource", "dataSourceName", "lastPassTime", "lastPassPicture",
    "lastPassType", "lastPassAddress", "lastPassLongitude", "lastPassLatitude",
    "lastPassCardirection", "roadSectionId", "sectionCode", "roadSectionName", "nextPassTime",
    "nextPassType", "nextPassAddress", "nextPassLongitude", "nextPassLatitude", "trackId",
    "trackJosn", "orgId", "orgCode", "orgName", "gantryCode", "roadCode", "roadName",
    "tollCode", "tollName", "linkName", "linkPhone", "fwqbm", "fwqmc", "backCol1", "backCol2",
    "status", "remark", "applyTime1", "applyTime2", "carNoQuery", "createTimeStr",
    "createInfo", "trailList", "flag",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, support::reorder_rows(rows, CAR_INFO_KEYS)))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let plate_color = support::dict_map(&state.db, "plate_color").await?;
    let car_type = support::dict_map(&state.db, "car_type").await?;
    let car_vehicle = support::dict_map(&state.db, "car_vehicle").await?;
    let escaped_type = support::dict_map(&state.db, "escaped_type").await?;
    let run_status = support::dict_map(&state.db, "car_run_status").await?;

    let headers = [
        "车牌号", "车型", "车种", "轴数", "逃费类型", "逃费类型名称", "逃费金额", "逃费次数(反改)",
        "累计追缴金额", "应缴金额", "收费金额", "差额", "处理单位id", "处理单位", "是否在白名单",
        "白名单原因", "图片(附件ids)", "车辆品牌", "车牌颜色", "车牌类型", "车辆颜色",
        "数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)", "来源名称", "最后通行时间",
        "最后通行图片", "最后通行类型(1?架2收费拍)3服务区)", "最后通行地址", "最后通行经度",
        "最后通行维度", "驾驶(1上行2下行3未知)", "管理中心路段id", "所属路段编码",
        "管理中心路段名称", "预计下一个通行时间", "预计下一个通行类型", "预计下一个通行地址",
        "预计下一个通行经度", "预计下一个通行维度", "行驶轨迹id", "行驶轨迹josn", "管理中心id",
        "所属管理中心机构编码", "管理中心名称", "门架编号", "所属路线编码", "所属路线名称",
        "所属收费站编码", "所属收费站名称", "司机名称", "联系方式", "服务区编码", "服务区名称",
        "备用字段1", "备用字段2", "状态", "备注",
    ]
    .map(str::to_string);
    let fields = [
        "carNo", "carType", "carVehicle", "carNum", "escapedType", "escapedTypeName",
        "escapedAmount", "escapedNum", "returnAmount", "totalAmount", "chargeAmount",
        "difAmount", "auitOrgId", "auitOrgName", "isWhite", "whiteRemark", "fileIds", "brand",
        "plateColor", "plateType", "carColor", "dataSource", "dataSourceName", "lastPassTime",
        "lastPassPicture", "lastPassType", "lastPassAddress", "lastPassLongitude",
        "lastPassLatitude", "lastPassCardirection", "roadSectionId", "sectionCode",
        "roadSectionName", "nextPassTime", "nextPassType", "nextPassAddress",
        "nextPassLongitude", "nextPassLatitude", "trackId", "backCol1", "orgId", "orgCode",
        "orgName", "gantryCode", "roadCode", "roadName", "tollCode", "tollName", "linkName",
        "linkPhone", "fwqbm", "fwqmc", "backCol1", "backCol2", "status", "remark",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            // 字典翻译与 Java 模板导出一致（null -> 空串）。
            let translate = |values: &mut Vec<Value>, index: usize, map: &HashMap<String, String>| {
                let key = values
                    .get(index)
                    .and_then(Value::as_str)
                    .unwrap_or_default()
                    .to_string();
                values[index] = Value::String(map.get(&key).cloned().unwrap_or_default());
            };
            translate(&mut values, 1, &car_type);
            translate(&mut values, 2, &car_vehicle);
            translate(&mut values, 18, &plate_color);
            translate(&mut values, 54, &run_status);
            // 逃费类型：逗号分隔的 code -> 名称。
            let escaped = values
                .get(4)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .trim_end_matches(',')
                .to_string();
            if !escaped.is_empty() {
                let names = escaped
                    .split(',')
                    .filter(|code| escaped_type.contains_key(*code))
                    .map(|code| escaped_type.get(code).cloned().unwrap_or_default())
                    .collect::<Vec<_>>()
                    .join(",");
                values[4] = Value::String(names.trim_end_matches(',').to_string());
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_download("车辆信息数据", &headers, &data)
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
    support::save_or_update(&state, &user, &body, "car_info", "id", true, true).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "car_info", "id", true, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_info", "id", &ids).await?;
    Ok(support::success_count(count))
}

/// Java: doImport —— 车牌颜色/车型/车种/逃费类型按字典标签->值翻译后 upsert。
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
    if !file_name.ends_with(".xlsx") {
        return Ok(AjaxResult::error("请上传Excel文件(.xlsx)"));
    }
    let rows = crate::common::excel::read_rows(&bytes)?;
    if rows.is_empty() {
        return Ok(AjaxResult::error("导入失败,模板excel没有数据可以导入，请确定！"));
    }
    let expected = [
        "车牌颜色", "车牌号", "车型", "车种", "轴数", "逃费类型", "逃费金额（元）", "备注",
    ];
    let header = rows[0].clone();
    if header.len() < expected.len()
        || expected
            .iter()
            .zip(header.iter())
            .any(|(want, got)| got.trim() != *want)
    {
        return Ok(AjaxResult::error("导入失败,模板不正确,请下载对应的模板！"));
    }

    let plate_color = label_value_map(&state, "plate_color").await?;
    let car_type = label_value_map(&state, "car_type").await?;
    let car_vehicle = label_value_map(&state, "car_vehicle").await?;
    let escaped_type = label_value_map(&state, "escaped_type").await?;

    let mut errors: Vec<Value> = Vec::new();
    let mut import_list: Vec<Value> = Vec::new();
    for (index, row) in rows.iter().skip(1).enumerate() {
        if row.iter().all(|cell| cell.trim().is_empty()) {
            continue;
        }
        let cell = |position: usize| row.get(position).cloned().unwrap_or_default().trim().to_string();
        let mut entity = serde_json::Map::new();
        let mut row_errors: Vec<(&str, String)> = Vec::new();
        let plate = cell(0);
        if plate.is_empty() {
            row_errors.push(("车牌颜色", "车牌颜色不能为空".to_string()));
        } else if let Some(value) = plate_color.get(&plate) {
            entity.insert("plateColor".to_string(), json!(value));
        } else {
            row_errors.push((
                "车牌颜色",
                format!("{plate} 车牌颜色不存在,请在字典菜单维护！"),
            ));
        }
        let car_no = cell(1);
        if car_no.is_empty() {
            row_errors.push(("车牌号", "车牌号不能为空".to_string()));
        } else {
            entity.insert("carNo".to_string(), json!(car_no));
        }
        let car_type_text = cell(2);
        if let Some(value) = car_type.get(&car_type_text) {
            entity.insert("carType".to_string(), json!(value));
        } else {
            row_errors.push((
                "车型",
                format!("{car_type_text} 车型不存在,请在字典菜单维护！"),
            ));
        }
        let car_vehicle_text = cell(3);
        if !car_vehicle_text.is_empty() {
            if let Some(value) = car_vehicle.get(&car_vehicle_text) {
                entity.insert("carVehicle".to_string(), json!(value));
            } else {
                row_errors.push((
                    "车种",
                    format!("{car_vehicle_text} 车种不存在,请在字典菜单维护！"),
                ));
            }
        }
        let car_num = cell(4);
        if let Ok(number) = car_num.parse::<i64>() {
            entity.insert("carNum".to_string(), json!(number));
        }
        let escaped_text = cell(5).replace('，', ",");
        let mut escaped_value = String::new();
        for code in escaped_text.trim_end_matches(',').split(',') {
            if code.is_empty() {
                continue;
            }
            if let Some(value) = escaped_type.get(code) {
                escaped_value.push_str(value);
                escaped_value.push(',');
            } else {
                row_errors.push((
                    "逃费类型",
                    format!("{code} 逃费类型不存在,请在字典菜单维护！"),
                ));
            }
        }
        entity.insert(
            "escapedType".to_string(),
            json!(escaped_value.trim_end_matches(',')),
        );
        let escaped_amount = cell(6);
        if let Ok(amount) = escaped_amount.parse::<f64>() {
            entity.insert("escapedAmount".to_string(), json!(amount));
        }
        let remark = cell(7);
        if !remark.is_empty() {
            entity.insert("remark".to_string(), json!(remark));
        }
        for (field, message) in row_errors {
            errors.push(json!({
                "rowNum": index + 1,
                "colName": field,
                "errorMsg": message,
            }));
        }
        if errors.len() > 100 {
            break;
        }
        if errors.is_empty() {
            import_list.push(Value::Object(entity));
        }
    }

    if errors.is_empty() {
        for addbo in &import_list {
            let car_no = addbo.get("carNo").and_then(Value::as_str).unwrap_or_default();
            let existing = support::scalar_string(
                &state.db,
                "select id from car_info where del_flag = '0' and car_no = ? limit 1",
                car_no,
            )
            .await?;
            if let Some(id) = existing {
                let mut entity = addbo.clone();
                if let Some(object) = entity.as_object_mut() {
                    object.insert("id".to_string(), json!(id));
                }
                support::update_entity_by_id(&state.db, "car_info", "id", &entity, support::AutoFill::from_user(&user))
                    .await?;
            } else {
                support::insert_entity(
                    &state.db,
                    "car_info",
                    addbo,
                    support::AutoFill::from_user(&user),
                )
                .await?;
            }
        }
    }

    if !errors.is_empty() {
        return Ok(AjaxResult::error("error").put("data", errors));
    }
    Ok(AjaxResult::success_msg_data("数据导入成功", import_list))
}

/// 字典 label -> value（Java: selectDictDataLaleMap）。
async fn label_value_map(state: &AppState, dict_type: &str) -> Result<HashMap<String, String>, AppError> {
    let rows: Vec<(Option<String>, Option<String>)> = sqlx::query_as(
        "select dict_value, dict_label from sys_dict_data where dict_type = ? order by dict_sort asc",
    )
    .bind(dict_type)
    .fetch_all(&state.db)
    .await?;
    Ok(rows
        .into_iter()
        .map(|(value, label)| (label.unwrap_or_default(), value.unwrap_or_default()))
        .collect())
}
