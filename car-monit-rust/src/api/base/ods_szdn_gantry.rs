// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryMapper.xml
// 职责: 门架信息 CRUD、导出；列表用 section_list 缓存补路线/路段名称。
// 对应关系: list/listAll/export/getInfo/add/edit/remove -> SPEC + save_or_update。
// 说明: Java 的导出走 EasyPOI 模板并把字节写进响应；Rust 统一用 profile/download 工作簿，
//       返回文件名（AjaxResult.success(filename)），列顺序与模板一致。

use std::collections::HashMap;

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.gantry_code, t.gantry_name, t.road_code, t.section_code, t.toll_code, \
             t.org_code, t.hex_code, t.direction, t.pile_no, t.lon, t.lat, t.remark, \
             t.is_virtual, t.mileage, t.boundary_gantry_type, t.gantry_type, t.city_code, \
             t.district_name, t.belong_group, t.gantry_code_merge, t.gantry_name_alias, \
             null as sectionCodeList, null as isData, null as tollName, null as orgName, \
             null as roadName, null as sectionName",
    from: "from ods_szdn_gantry t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("gantryCode", "t.gantry_code"),
        Filter::like("gantryName", "t.gantry_name"),
        Filter::eq("roadCode", "t.road_code"),
        Filter::eq("sectionCode", "t.section_code"),
        Filter::eq("tollCode", "t.toll_code"),
        Filter::eq("orgCode", "t.org_code"),
        Filter::eq("hexCode", "t.hex_code"),
        Filter::eq("direction", "t.direction"),
        Filter::like("pileNo", "t.pile_no"),
        Filter::eq("lon", "t.lon"),
        Filter::eq("lat", "t.lat"),
        Filter::eq("isVirtual", "t.is_virtual"),
        Filter::eq("mileage", "t.mileage"),
        Filter::eq("boundaryGantryType", "t.boundary_gantry_type"),
        Filter::eq("gantryType", "t.gantry_type"),
        Filter::eq("cityCode", "t.city_code"),
        Filter::like("districtName", "t.district_name"),
        Filter::eq("belongGroup", "t.belong_group"),
        Filter::eq("gantryCodeMerge", "t.gantry_code_merge"),
        Filter::eq("gantryNameAlias", "t.gantry_name_alias"),
        Filter::raw(
            "sectionName",
            " and t.section_code in ( select t1.section_code from ods_szdn_section t1 \
             where t1.section_name like concat('%', ?, '%') )",
        ),
    ],
    extra_where: "",
    order_by: "t.gantry_name",
    id_column: "t.id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "门架信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.OdsSzdnGantryController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "门架信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.OdsSzdnGantryController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "门架信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.OdsSzdnGantryController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "门架信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.OdsSzdnGantryController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/gantry/list",
            meta::get_route("/base/gantry/list", None, None, list),
        )
        .route(
            "/base/gantry/listAll",
            meta::get_route("/base/gantry/listAll", None, None, list_all),
        )
        .route(
            "/base/gantry/export",
            meta::get_route(
                "/base/gantry/export",
                Some("base:gantry:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/gantry/{ids}",
            meta::get_route("/base/gantry/{ids}", None, None, get_info),
        )
        .route(
            "/base/gantry",
            meta::post_route("/base/gantry", Some("base:gantry:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/base/gantry",
                    Some("base:gantry:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/base/gantry/{ids}",
            meta::delete_route(
                "/base/gantry/{ids}",
                Some("base:gantry:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java: `sectionList.stream().collect(toMap(roadCode, roadName, (k1,k2)->k1))`。
async fn section_maps(state: &AppState) -> (HashMap<String, String>, HashMap<String, String>) {
    let mut road = HashMap::new();
    let mut section = HashMap::new();
    if let Ok(list) = state.redis.get_list::<Value>("section_list").await {
        for item in list {
            let road_code = item
                .get("roadCode")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let road_name = item
                .get("roadName")
                .and_then(Value::as_str)
                .unwrap_or_default();
            road.entry(road_code.to_string())
                .or_insert_with(|| road_name.to_string());
            let section_code = item
                .get("sectionCode")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let section_name = item
                .get("sectionName")
                .and_then(Value::as_str)
                .unwrap_or_default();
            section
                .entry(section_code.to_string())
                .or_insert_with(|| section_name.to_string());
        }
    }
    (road, section)
}

/// Java Jackson 的 BaseGantryInfo 键序（实体声明顺序 + 派生 sectionCodeList/isData/名称字段）。
const GANTRY_KEYS: &[&str] = &[
    "id",
    "gantryCode",
    "gantryName",
    "roadCode",
    "sectionCode",
    "tollCode",
    "orgCode",
    "hexCode",
    "direction",
    "pileNo",
    "lon",
    "lat",
    "isVirtual",
    "mileage",
    "boundaryGantryType",
    "gantryType",
    "cityCode",
    "districtName",
    "belongGroup",
    "gantryCodeMerge",
    "gantryNameAlias",
    "remark",
    "sectionCodeList",
    "isData",
    "roadName",
    "sectionName",
    "tollName",
    "orgName",
];
async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, mut rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    let (road_map, section_map) = section_maps(&state).await;
    for row in &mut rows {
        let Some(object) = row.as_object_mut() else {
            continue;
        };
        let road_name = object
            .get("roadCode")
            .and_then(Value::as_str)
            .and_then(|code| road_map.get(code))
            .cloned()
            .unwrap_or_default();
        let section_name = object
            .get("sectionCode")
            .and_then(Value::as_str)
            .and_then(|code| section_map.get(code))
            .cloned()
            .unwrap_or_default();
        object.insert("roadName".to_string(), Value::String(road_name));
        object.insert("sectionName".to_string(), Value::String(section_name));
    }
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, GANTRY_KEYS),
    ))
}

async fn list_all(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, GANTRY_KEYS),
    ))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(_raw): RawQuery,
) -> Result<axum::response::Response, AppError> {
    // Java: List obj = redisCache.getCacheObject(Constants.gantry_list);
    let mut rows: Vec<Value> = match state.redis.get_object::<Value>("gantry_list").await? {
        Some(Value::Array(items)) => items,
        _ => Vec::new(),
    };
    if rows.is_empty() {
        return Ok(axum::response::Response::builder()
            .status(axum::http::StatusCode::OK)
            .body(axum::body::Body::empty())
            .unwrap());
    }

    let (road_map, section_map) = section_maps(&state).await;
    let toll_map =
        code_name_map(&state.db, "select toll_code, toll_name from ods_szdn_toll").await?;
    let org_map = code_name_map(
        &state.db,
        "select org_code, org_name from ods_yhgl_v_base_org",
    )
    .await?;

    for row in &mut rows {
        let Some(object) = row.as_object_mut() else {
            continue;
        };
        let text = |key: &str| {
            object
                .get(key)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string()
        };
        let road_name = road_map.get(&text("roadCode")).cloned().unwrap_or_default();
        let section_name = section_map
            .get(&text("sectionCode"))
            .cloned()
            .unwrap_or_default();
        let toll_name = toll_map.get(&text("tollCode")).cloned().unwrap_or_default();
        let org_name = org_map.get(&text("orgCode")).cloned().unwrap_or_default();
        let boundary = if text("boundaryGantryType") == "0" {
            "边界入口门架"
        } else {
            "边界出口门架"
        };
        let virtual_text = if text("isVirtual") == "0" {
            "否"
        } else {
            "是"
        };
        let mut is_data = "否";
        let key = format!("gantry_list_data:{}", text("gantryCode"));
        if let Some(value) = state.redis.get_object::<Value>(&key).await? {
            let raw = match &value {
                Value::String(text) => text.clone(),
                other => other.to_string(),
            };
            let count: i64 = raw
                .trim()
                .parse()
                .map_err(|_| AppError::Service(format!("gantry_list_data 缓存不是整数: {raw}")))?;
            if count > 0 {
                is_data = "是";
            }
        }
        object.insert("roadName".to_string(), Value::String(road_name));
        object.insert("sectionName".to_string(), Value::String(section_name));
        object.insert("tollName".to_string(), Value::String(toll_name));
        object.insert("orgName".to_string(), Value::String(org_name));
        object.insert(
            "boundaryGantryType".to_string(),
            Value::String(boundary.to_string()),
        );
        object.insert(
            "isVirtual".to_string(),
            Value::String(virtual_text.to_string()),
        );
        object.insert("isData".to_string(), Value::String(is_data.to_string()));
    }

    // Java: orgCode -> roadCode -> sectionCode -> tollCode -> gantryCode。
    rows.sort_by_key(|row| {
        let field = |key: &str| {
            row.get(key)
                .and_then(Value::as_str)
                .unwrap_or_default()
                .to_string()
        };
        (
            field("orgCode"),
            field("roadCode"),
            field("sectionCode"),
            field("tollCode"),
            field("gantryCode"),
        )
    });

    // 表头逐字取自 Java 的 EasyPOI 模板 `templates/export/gantry.xlsx` 第 1 行。
    let headers = [
        "所属管理中心编号",
        "所属管理中心名称",
        "所属路线编号",
        "所属路线名称",
        "所属路段编码",
        "所属路段名称",
        "收费站编号",
        "收费站名称",
        "门架编号",
        "门架名称",
        "边界门架类型",
        "是否虚门架",
        "是否有交易流水",
    ]
    .map(str::to_string);
    let fields = [
        "orgCode",
        "orgName",
        "roadCode",
        "roadName",
        "sectionCode",
        "sectionName",
        "tollCode",
        "tollName",
        "gantryCode",
        "gantryName",
        "boundaryGantryType",
        "isVirtual",
        "isData",
    ];
    let data = rows
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_download("门架信息数据", &headers, &data)
}

async fn code_name_map(
    pool: &sqlx::MySqlPool,
    sql: &str,
) -> Result<HashMap<String, String>, AppError> {
    let rows: Vec<(Option<String>, Option<String>)> = sqlx::query_as(sql).fetch_all(pool).await?;
    Ok(rows
        .into_iter()
        .map(|(code, name)| (code.unwrap_or_default(), name.unwrap_or_default()))
        .collect())
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id)
            .await?
            .map(|row| support::reorder_keys(row, GANTRY_KEYS)),
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "ods_szdn_gantry", "id", false, false).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "ods_szdn_gantry", "id", false, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "ods_szdn_gantry", "id", &ids).await?;
    Ok(support::success_count(count))
}
