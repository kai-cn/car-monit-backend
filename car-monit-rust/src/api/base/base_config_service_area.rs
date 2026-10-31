// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/BaseConfigServiceAreaController.java
// 职责: 服务区 CRUD 与导出。
// 对应关系: list/export/getInfo/add/edit/remove -> 同名 handler；
//           selectBaseConfigServiceAreaList/ById -> BASE_SPEC；save/delete -> support::*。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SELECT: &str = "t.fwqbm, t.fwqmc, t.lon, t.lat, t.road_code, t.section_code, t.pile_no";

// Java: BaseConfigServiceAreaMapper.xml#selectBaseConfigServiceAreaList
const SPEC: ListSpec = ListSpec {
    select: SELECT,
    from: "from base_config_service_area t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("fwqbm", "t.fwqbm"),
        Filter::eq("fwqmc", "t.fwqmc"),
        Filter::eq("lon", "t.lon"),
        Filter::eq("lat", "t.lat"),
        Filter::eq("roadCode", "t.road_code"),
        Filter::eq("sectionCode", "t.section_code"),
        Filter::eq("pileNo", "t.pile_no"),
        Filter::eq_allow_empty("createBy", "t.create_by"),
    ],
    extra_where: "",
    order_by: "",
    id_column: "t.fwqbm",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "服务区",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.BaseConfigServiceAreaController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "服务区",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.BaseConfigServiceAreaController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "服务区",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.BaseConfigServiceAreaController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "服务区",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.BaseConfigServiceAreaController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/configServiceArea/list",
            meta::get_route(
                "/base/configServiceArea/list",
                Some("base:configServiceArea:list"),
                None,
                list,
            ),
        )
        .route(
            "/base/configServiceArea/listQuery",
            meta::get_route("/base/configServiceArea/listQuery", None, None, list_query),
        )
        .route(
            "/base/configServiceArea/export",
            meta::get_route(
                "/base/configServiceArea/export",
                Some("base:configServiceArea:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/configServiceArea/{fwqbms}",
            meta::get_route("/base/configServiceArea/{fwqbms}", None, None, get_info),
        )
        .route(
            "/base/configServiceArea",
            meta::post_route(
                "/base/configServiceArea",
                Some("base:configServiceArea:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/base/configServiceArea",
                Some("base:configServiceArea:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/base/configServiceArea/{fwqbms}",
            meta::delete_route(
                "/base/configServiceArea/{fwqbms}",
                Some("base:configServiceArea:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

// Java: startPage(); selectBaseConfigServiceAreaList
pub async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

// Java: listQuery —— 不分页，直接 AjaxResult.success(list)
pub async fn list_query(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    Ok(AjaxResult::success_data(rows))
}

// Java: ExcelUtil.exportExcel(list, "服务区数据")
pub async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "判定进入的服务区编码",
        "判定进入的服务区名称",
        "经度",
        "维度",
        "路线编码",
        "路段编码",
        "桩号",
    ]
    .map(str::to_string);
    let fields = ["fwqbm", "fwqmc", "lon", "lat", "roadCode", "sectionCode", "pileNo"];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "服务区数据", &headers, &data)
}

pub async fn get_info(
    State(state): State<AppState>,
    Path(fwqbm): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &fwqbm).await?,
    ))
}

// Java: service.saveBaseConfigServiceArea —— id 非空走 updateById，否则 insert。
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
    let id = body.get("id").cloned().unwrap_or(Value::Null);
    let blank = match &id {
        Value::Null => true,
        Value::String(text) => text.is_empty(),
        _ => false,
    };
    let id = if blank {
        let generated = uuid::Uuid::new_v4().simple().to_string();
        let mut entity = body.clone();
        if let Some(map) = entity.as_object_mut() {
            map.insert("id".to_string(), Value::String(generated.clone()));
        }
        support::insert_entity(&state.db, "base_config_service_area", &entity, fill).await?;
        generated
    } else {
        support::update_entity_by_id(&state.db, "base_config_service_area", "id", body, fill)
            .await?;
        id.as_str().unwrap_or_default().to_string()
    };
    Ok(AjaxResult::success_msg_data("操作成功！", id))
}

// Java: deleteBaseConfigServiceAreaByIds —— 物理删除。
pub async fn remove(
    State(state): State<AppState>,
    Path(fwqbms): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&fwqbms);
    let count = support::delete_by_ids(&state.db, "base_config_service_area", "fwqbm", &ids).await?;
    Ok(support::success_count(count))
}
