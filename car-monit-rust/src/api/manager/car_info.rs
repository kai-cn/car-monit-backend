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
            meta::get_route(
                "/manager/carinfo/list",
                Some("manager:carinfo:list"),
                None,
                list,
            ),
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
            meta::post_route("/manager/carinfo/import", None, Some(&LOG_IMPORT), import),
        )
        .route(
            "/manager/carinfo/{ids}",
            meta::get_route("/manager/carinfo/{ids}", None, None, get_info),
        )
        .route(
            "/manager/carinfo",
            meta::post_route("/manager/carinfo", None, Some(&LOG_ADD), add).merge(meta::put_route(
                "/manager/carinfo",
                Some("manager:carinfo:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
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
    "id",
    "epsId",
    "delFlag",
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "sort",
    "tenantId",
    "carNo",
    "carType",
    "carVehicle",
    "carNum",
    "escapedType",
    "escapedTypeName",
    "escapedAmount",
    "escapedNum",
    "returnAmount",
    "totalAmount",
    "chargeAmount",
    "difAmount",
    "auitOrgId",
    "auitOrgName",
    "isWhite",
    "whiteRemark",
    "fileIds",
    "brand",
    "plateColor",
    "plateType",
    "carColor",
    "dataSource",
    "dataSourceName",
    "lastPassTime",
    "lastPassPicture",
    "lastPassType",
    "lastPassAddress",
    "lastPassLongitude",
    "lastPassLatitude",
    "lastPassCardirection",
    "roadSectionId",
    "sectionCode",
    "roadSectionName",
    "nextPassTime",
    "nextPassType",
    "nextPassAddress",
    "nextPassLongitude",
    "nextPassLatitude",
    "trackId",
    "trackJosn",
    "orgId",
    "orgCode",
    "orgName",
    "gantryCode",
    "roadCode",
    "roadName",
    "tollCode",
    "tollName",
    "linkName",
    "linkPhone",
    "fwqbm",
    "fwqmc",
    "backCol1",
    "backCol2",
    "status",
    "remark",
    "applyTime1",
    "applyTime2",
    "carNoQuery",
    "createTimeStr",
    "createInfo",
    "trailList",
    "flag",
];

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, CAR_INFO_KEYS),
    ))
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
        "车牌号",
        "车型",
        "车种",
        "轴数",
        "逃费类型",
        "逃费类型名称",
        "逃费金额",
        "逃费次数(反改)",
        "累计追缴金额",
        "应缴金额",
        "收费金额",
        "差额",
        "处理单位id",
        "处理单位",
        "是否在白名单",
        "白名单原因",
        "图片(附件ids)",
        "车辆品牌",
        "车牌颜色",
        "车牌类型",
        "车辆颜色",
        "数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)",
        "来源名称",
        "最后通行时间",
        "最后通行图片",
        "最后通行类型(1?架2收费拍)3服务区)",
        "最后通行地址",
        "最后通行经度",
        "最后通行维度",
        "驾驶(1上行2下行3未知)",
        "管理中心路段id",
        "所属路段编码",
        "管理中心路段名称",
        "预计下一个通行时间",
        "预计下一个通行类型",
        "预计下一个通行地址",
        "预计下一个通行经度",
        "预计下一个通行维度",
        "行驶轨迹id",
        "行驶轨迹josn",
        "管理中心id",
        "所属管理中心机构编码",
        "管理中心名称",
        "门架编号",
        "所属路线编码",
        "所属路线名称",
        "所属收费站编码",
        "所属收费站名称",
        "司机名称",
        "联系方式",
        "服务区编码",
        "服务区名称",
        "备用字段1",
        "备用字段2",
        "状态",
        "备注",
    ]
    .map(str::to_string);
    let fields = [
        "carNo",
        "carType",
        "carVehicle",
        "carNum",
        "escapedType",
        "escapedTypeName",
        "escapedAmount",
        "escapedNum",
        "returnAmount",
        "totalAmount",
        "chargeAmount",
        "difAmount",
        "auitOrgId",
        "auitOrgName",
        "isWhite",
        "whiteRemark",
        "fileIds",
        "brand",
        "plateColor",
        "plateType",
        "carColor",
        "dataSource",
        "dataSourceName",
        "lastPassTime",
        "lastPassPicture",
        "lastPassType",
        "lastPassAddress",
        "lastPassLongitude",
        "lastPassLatitude",
        "lastPassCardirection",
        "roadSectionId",
        "sectionCode",
        "roadSectionName",
        "nextPassTime",
        "nextPassType",
        "nextPassAddress",
        "nextPassLongitude",
        "nextPassLatitude",
        "trackId",
        "backCol1",
        "orgId",
        "orgCode",
        "orgName",
        "gantryCode",
        "roadCode",
        "roadName",
        "tollCode",
        "tollName",
        "linkName",
        "linkPhone",
        "fwqbm",
        "fwqmc",
        "backCol1",
        "backCol2",
        "status",
        "remark",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            // 字典翻译与 Java 模板导出一致（null -> 空串）。
            let translate =
                |values: &mut Vec<Value>, index: usize, map: &HashMap<String, String>| {
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
    save_car_info(&state, &user, &body).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save_car_info(&state, &user, &body).await
}

/// Java: `CarInfoServiceImpl.saveCarInfo` —— add 与 edit 走同一个方法：
/// 先把车牌 `CommonUtil.isNull`（null→""、trim），再按车牌判重（编辑时排除自己），
/// 命中就整条不写、回「车牌号存在重复，请确定！」；写完刷 `car_list` 缓存。
async fn save_car_info(
    state: &AppState,
    user: &LoginUser,
    body: &Value,
) -> Result<AjaxResult, AppError> {
    let mut entity = body.clone();
    let car_no = text_of(&entity, "carNo").trim().to_string();
    put_text(&mut entity, "carNo", &car_no);
    let id = text_of(&entity, "id");
    let count: i64 = if id.is_empty() {
        sqlx::query_as::<_, (i64,)>(
            "select count(1) from car_info t where t.del_flag = '0' and t.car_no = ?",
        )
        .bind(&car_no)
        .fetch_one(&state.db)
        .await?
        .0
    } else {
        sqlx::query_as::<_, (i64,)>(
            "select count(1) from car_info t where t.del_flag = '0' and t.car_no = ? and t.id <> ?",
        )
        .bind(&car_no)
        .bind(&id)
        .fetch_one(&state.db)
        .await?
        .0
    };
    if count > 0 {
        return Ok(AjaxResult::error("车牌号存在重复，请确定！"));
    }
    // Java: `CommonUtil.isNotBlank(id)` 决定新增还是修改 —— 全空白的 id 也算空，
    // 走新增并由 service 重新 setUUID。
    if id.trim().is_empty() {
        // Java 的新增分支：显式 delFlag='0'，`escapedAmount == null` 时补 BigDecimal.ZERO，
        // 并写 updateBy/updateTime（自动填充在 INSERT 时同样写这两个）。
        if let Some(object) = entity.as_object_mut() {
            object.remove("id");
            object.insert("delFlag".to_string(), json!("0"));
            if object
                .get("escapedAmount")
                .unwrap_or(&Value::Null)
                .is_null()
            {
                object.insert("escapedAmount".to_string(), json!(0));
            }
            object.insert("updateBy".to_string(), json!(user.user.user_id));
            object.insert("updateTime".to_string(), json!(support::now_string()));
        }
    }
    let result =
        support::save_or_update(state, user, &entity, "car_info", "id", true, true).await?;
    update_redis_car_list(state).await?;
    Ok(result)
}

/// Java: `updateRedisCarList` —— 整体重写两个**无 TTL 的字符串键**：
/// `car_list`（`CarInfo` 全字段）与 `car_list_jc`（`CarVO` 只有 carId/carNo）。
/// Java: `carInfoMapper.selectCarInfoList(new CarInfo())` —— `car_list` 缓存与
/// 「缓存未命中时回源」用的是**同一条**查询（含 `not exists` 排除条件与 createInfo 拼接）。
pub async fn car_info_cache_rows(state: &AppState) -> Result<Vec<Value>, AppError> {
    let rows = support::query_all(&state.db, &HashMap::new(), &SPEC).await?;
    Ok(support::fastjson_rows(rows))
}

/// Java: `updateRedisCarList` —— 整体重写两个**无 TTL 的字符串键**：`car_list`（`CarInfo` 全字段）
/// 与 `car_list_jc`（`CarVO` 只有 carId/carNo）。
async fn update_redis_car_list(state: &AppState) -> Result<(), AppError> {
    let full = car_info_cache_rows(state).await?;
    state
        .redis
        .set_object(
            "car_list",
            &crate::db::redis_cache::stamp_types(full.clone(), "com.ruoyi.manager.domain.CarInfo"),
        )
        .await?;
    let brief: Vec<Value> = full
        .iter()
        .map(|row| {
            json!({
                "carId": row.get("id"),
                "carNo": row.get("carNo"),
            })
        })
        .collect();
    state
        .redis
        .set_object(
            "car_list_jc",
            &crate::db::redis_cache::stamp_types(brief, "com.ruoyi.base.domain.CarVO"),
        )
        .await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "car_info", "id", &ids).await?;
    Ok(support::success_count(count))
}

/// Java: `CarInfoController.initList()` —— 8 列的「列名 / 属性 / 校验规则」。
const IMPORT_FIELDS: &[crate::common::import_util::ImportField] = &[
    crate::common::import_util::field("车牌颜色", "plateColor", "1"),
    crate::common::import_util::field("车牌号", "carNo", "1"),
    crate::common::import_util::field("车型", "carType", "1"),
    crate::common::import_util::field("车种", "carVehicle", ""),
    crate::common::import_util::field("轴数", "carNum", "3"),
    crate::common::import_util::field("逃费类型", "escapedType", "1"),
    crate::common::import_util::field("逃费金额（元）", "escapedAmount", "2"),
    crate::common::import_util::field("备注", "remark", ""),
];

/// Java: doImport —— 规则校验走 `ImportUtil.importExcel`，字典翻译在没有任何规则错误时才做，
/// 再按车牌号决定新增/修改（与 `CarInfoServiceImpl.doImport` 的填充一致）。
async fn import(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    use crate::common::import_util::{apply_rules, data_rows, header_at, read_sheet};

    let mut file_name = String::new();
    let mut bytes = Vec::new();
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        if field.file_name().is_some() {
            let upload = support::read_multipart_field(field).await?;
            file_name = upload.file_name;
            bytes = upload.bytes;
        }
    }
    if !file_name.contains(".xlsx") {
        return Ok(AjaxResult::error("请上传Excel文件(.xlsx)"));
    }
    let rows = read_sheet(&bytes)?;
    let header: Vec<&'static str> = IMPORT_FIELDS.iter().map(|item| item.col_name).collect();
    // Java: colVdaExcel07 —— 表头在第一行。
    if !header_at(&rows, 0, &header) {
        return Ok(AjaxResult::error("导入失败,模板不正确,请下载对应的模板！"));
    }
    let sheet_rows = data_rows(&rows, 1, IMPORT_FIELDS.len(), &[]);
    if sheet_rows.is_empty() {
        return Ok(AjaxResult::error(
            "导入失败,模板excel没有数据可以导入，请确定！",
        ));
    }

    let mut errors: Vec<Value> = Vec::new();
    let mut cars: Vec<Value> = Vec::new();
    for (index, strs) in sheet_rows.iter().enumerate() {
        // Java: 报错行号 = 数据行下标 + 2；有错后就不再转换后续行。
        if let Some(object) = apply_rules(IMPORT_FIELDS, strs, index + 1, &mut errors) {
            cars.push(numberize_entity(object));
        }
        if errors.len() > 100 {
            break;
        }
    }

    if errors.is_empty() {
        let plate_color = label_value_map(&state, "plate_color").await?;
        let car_type = label_value_map(&state, "car_type").await?;
        let car_vehicle = label_value_map(&state, "car_vehicle").await?;
        let escaped_type = label_value_map(&state, "escaped_type").await?;
        for (index, car) in cars.iter_mut().enumerate() {
            let row_no = index as i64 + 2;
            for (key, label, map) in [
                ("plateColor", "车牌颜色", &plate_color),
                ("carType", "车型", &car_type),
                ("carVehicle", "车种", &car_vehicle),
            ] {
                let text = text_of(car, key);
                if text.is_empty() {
                    continue;
                }
                match map.get(&text) {
                    Some(value) => put_text(car, key, value),
                    None => errors.push(crate::common::import_util::error_item(
                        row_no,
                        label,
                        format!("{text} {label}不存在,请在字典菜单维护！"),
                    )),
                }
            }

            // 逃费类型允许多值（中文逗号先换成英文），逐段翻译后再去掉结尾逗号。
            let escaped = trim_trailing_comma(&text_of(car, "escapedType").replace('，', ","));
            if !escaped.is_empty() {
                let mut translated = String::new();
                for part in escaped.split(',') {
                    match escaped_type.get(part) {
                        Some(value) => {
                            translated.push_str(value);
                            translated.push(',');
                        }
                        None => errors.push(crate::common::import_util::error_item(
                            row_no,
                            "逃费类型",
                            format!("{part} 逃费类型不存在,请在字典菜单维护！"),
                        )),
                    }
                }
                put_text(car, "escapedType", &trim_trailing_comma(&translated));
            }
            if errors.len() > 100 {
                break;
            }
        }
    }

    if !errors.is_empty() {
        return Ok(AjaxResult::error("error").put("data", errors));
    }

    let user_id = user.user.user_id;
    let eps_id = user.user.dept_id;
    let mut payload = Vec::with_capacity(cars.len());
    for mut car in cars {
        let car_no = text_of(&car, "carNo");
        // Java: carInfoService.selectCarInfoList(carNo) —— 与列表接口同一条排除条件。
        let existing: Option<String> = sqlx::query_scalar(
            "select t.id from car_info t where t.del_flag = '0' \
             and not exists (select 1 from (select t1.car_no, \
                 sum(case when t1.status = '0' then 1 else 0 end) except_num, count(1) count_num \
                 from car_except_record t1 where t1.del_flag = '0' group by t1.car_no) k \
                 where t.car_no = k.car_no and k.count_num > 0 and k.except_num = 0) \
             and t.car_no = ? limit 1",
        )
        .bind(&car_no)
        .fetch_optional(&state.db)
        .await?;
        let object = car.as_object_mut().expect("对象");
        match existing {
            Some(id) => {
                object.insert("id".to_string(), json!(id));
                object.insert("updateBy".to_string(), json!(user_id));
                object.insert("updateTime".to_string(), json!(support::now_string()));
                support::update_entity_by_id(
                    &state.db,
                    "car_info",
                    "id",
                    &car,
                    support::AutoFill::NONE,
                )
                .await?;
            }
            None => {
                // Java: doImport 的新增分支自己补 uuid/delFlag/createBy/epsId，逃费金额缺省 0。
                let id = uuid::Uuid::new_v4().simple().to_string();
                if !object.contains_key("escapedAmount") {
                    object.insert("escapedAmount".to_string(), json!(0));
                }
                object.insert("id".to_string(), json!(id));
                object.insert("delFlag".to_string(), json!("0"));
                object.insert("createBy".to_string(), json!(user_id));
                // Java: doImport 的新增分支显式写入 epsId。
                object.insert("epsId".to_string(), json!(eps_id));
                object.insert("createTime".to_string(), json!(support::now_string()));
                // Java: 自动填充在 INSERT 时也写 update 字段；tenantId 不由填充写入。
                object.insert("updateBy".to_string(), json!(user_id));
                object.insert("updateTime".to_string(), json!(support::now_string()));
                support::insert_entity(&state.db, "car_info", &car, support::AutoFill::NONE)
                    .await?;
            }
        }
        payload.push(car);
    }
    Ok(AjaxResult::success_msg_data(
        "数据导入成功",
        support::reorder_rows(payload, CAR_INFO_KEYS),
    ))
}

/// Java 的实体类型：轴数是 Long、逃费金额是 BigDecimal，表格里读来的是字符串。
fn numberize_entity(mut object: Value) -> Value {
    let Some(map) = object.as_object_mut() else {
        return object;
    };
    for key in ["carNum", "escapedAmount"] {
        if let Some(text) = map.get(key).and_then(Value::as_str).map(str::to_string) {
            let normalized = match text.strip_prefix('.') {
                Some(rest) => format!("0{rest}"),
                None => text.clone(),
            };
            match serde_json::from_str::<Value>(&normalized) {
                Ok(number) => {
                    map.insert(key.to_string(), number);
                }
                Err(_) => {
                    map.remove(key);
                }
            }
        }
    }
    object
}

fn text_of(record: &Value, key: &str) -> String {
    match record.get(key) {
        Some(Value::String(text)) => text.clone(),
        Some(value) if !value.is_null() => value.to_string(),
        _ => String::new(),
    }
}

fn put_text(record: &mut Value, key: &str, value: &str) {
    if let Some(object) = record.as_object_mut() {
        object.insert(key.to_string(), json!(value));
    }
}

/// Java: `CommonUtil.deleteEnd` —— 只去掉一个结尾逗号。
fn trim_trailing_comma(text: &str) -> String {
    text.strip_suffix(',').unwrap_or(text).to_string()
}

/// 字典 label -> value（Java: selectDictDataLaleMap）。
async fn label_value_map(
    state: &AppState,
    dict_type: &str,
) -> Result<HashMap<String, String>, AppError> {
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
