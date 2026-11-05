// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CarWarningConfigController.java
// 职责: 服务区判定规则 CRUD 与导出。
// 对应关系: selectCarWarningConfigList/ById -> SPEC；saveCarWarningConfig/delete* -> support::*。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SELECT: &str = "t.id, t.gantry_code_in, t.gantry_name_in, t.gantry_code_out, \
     t.gantry_name_out, t.time_span, t.remark, t.fwqbm, t1.fwqmc, t1.lon, t1.lat, \
     t1.road_code, t1.section_code, t1.pile_no";

// Java: CarWarningConfigMapper.xml#selectCarWarningConfigList
const SPEC: ListSpec = ListSpec {
    select: SELECT,
    from: "from car_warning_config t join base_config_service_area t1 on t.fwqbm = t1.fwqbm",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("gantryCodeIn", "t.gantry_code_in"),
        Filter::like("gantryNameIn", "t.gantry_name_in"),
        Filter::eq("gantryCodeOut", "t.gantry_code_out"),
        Filter::like("gantryNameOut", "t.gantry_name_out"),
        Filter::eq_allow_empty("timeSpan", "t.time_span"),
        Filter::eq("fwqbm", "t.fwqbm"),
        Filter::like("fwqmc", "t1.fwqmc"),
        Filter::eq("lon", "t.lon"),
        Filter::eq("lat", "t.lat"),
        Filter::eq("roadCode", "t.road_code"),
        Filter::eq("sectionCode", "t.section_code"),
        Filter::eq("pileNo", "t.pile_no"),
    ],
    extra_where: "",
    order_by: "",
    id_column: "t.id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "服务区判定规则",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.CarWarningConfigController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "服务区判定规则",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.CarWarningConfigController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "服务区判定规则",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.CarWarningConfigController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "服务区判定规则",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.CarWarningConfigController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/config/list",
            meta::get_route("/base/config/list", Some("base:config:list"), None, list),
        )
        .route(
            "/base/config/export",
            meta::get_route(
                "/base/config/export",
                Some("base:config:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/config/{ids}",
            meta::get_route("/base/config/{ids}", None, None, get_info),
        )
        .route(
            "/base/config",
            meta::post_route("/base/config", Some("base:config:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/base/config",
                    Some("base:config:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/base/config/{ids}",
            meta::delete_route(
                "/base/config/{ids}",
                Some("base:config:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java Jackson 的 BaseConfig 键序：实体声明顺序，`remark` 排在业务列之后。
const BASE_CONFIG_KEYS: &[&str] = &[
    "id",
    "gantryCodeIn",
    "gantryNameIn",
    "gantryCodeOut",
    "gantryNameOut",
    "timeSpan",
    "fwqbm",
    "fwqmc",
    "lon",
    "lat",
    "roadCode",
    "sectionCode",
    "pileNo",
    "remark",
];

pub async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(
        total,
        support::reorder_rows(rows, BASE_CONFIG_KEYS),
    ))
}

pub async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "进入门架编号",
        "进入门架名称",
        "出去门架编号",
        "出去门架名称",
        "判定时间间隔",
        "判定进入的服务区编码",
        "判定进入的服务区名称",
        "经度",
        "维度",
        "路线编码",
        "路段编码",
        "桩号",
        "备注",
    ]
    .map(str::to_string);
    let fields = [
        "gantryCodeIn",
        "gantryNameIn",
        "gantryCodeOut",
        "gantryNameOut",
        "timeSpan",
        "fwqbm",
        "fwqmc",
        "lon",
        "lat",
        "roadCode",
        "sectionCode",
        "pileNo",
        "remark",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut cells = support::pick_fields(row, &fields);
            // @Excel(readConverterExp = "分=离") / ("分=钟")
            cells[0] = convert(&cells[0], "分", "离");
            cells[2] = convert(&cells[2], "分", "离");
            cells[4] = convert(&cells[4], "分", "钟");
            cells
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "服务区判定规则数据", &headers, &data)
}

fn convert(value: &Value, from: &str, to: &str) -> Value {
    match value.as_str() {
        Some(text) if text == from => Value::String(to.to_string()),
        _ => value.clone(),
    }
}

pub async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &id)
            .await?
            .map(|row| support::reorder_keys(row, BASE_CONFIG_KEYS)),
    ))
}

pub async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save(&state, &user, &body).await
}

pub async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    save(&state, &user, &body).await
}

async fn save(state: &AppState, user: &LoginUser, body: &Value) -> Result<AjaxResult, AppError> {
    let fill = support::AutoFill::from_user(user);
    let id_value = body.get("id").cloned().unwrap_or(Value::Null);
    let id_text = id_value.as_str().unwrap_or_default().to_string();
    if id_text.is_empty() {
        let mut entity = body.clone();
        let generated = uuid::Uuid::new_v4().simple().to_string();
        if let Some(map) = entity.as_object_mut() {
            map.insert("id".to_string(), Value::String(generated.clone()));
        }
        support::insert_entity(&state.db, "car_warning_config", &entity, fill).await?;
        Ok(AjaxResult::success_msg_data("操作成功！", generated))
    } else {
        support::update_entity_by_id(&state.db, "car_warning_config", "id", body, fill).await?;
        Ok(AjaxResult::success_msg_data("操作成功！", id_text))
    }
}

pub async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::delete_by_ids(&state.db, "car_warning_config", "id", &ids).await?;
    Ok(support::success_count(count))
}
