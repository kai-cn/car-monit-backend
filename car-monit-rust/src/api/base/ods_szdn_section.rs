// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnSectionController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsSzdnSectionMapper.xml
// 职责: 路段信息 CRUD 与导出。
// 对应关系: list/listAll/export/getInfo/add/edit/remove -> SPEC + save_or_update。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, FieldFormat, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.road_code, t.road_name, t.section_code, t.section_name, t.start_pile_no, \
             t.end_pile_no, t.org_code, t.org_name, t.org_level_code, t.org_category, t.mileage, \
             t.open_date",
    from: "from ods_szdn_section t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("roadCode", "t.road_code"),
        Filter::like("roadName", "t.road_name"),
        Filter::eq("sectionCode", "t.section_code"),
        Filter::like("sectionName", "t.section_name"),
        Filter::eq("startPileNo", "t.start_pile_no"),
        Filter::eq("endPileNo", "t.end_pile_no"),
        Filter::eq("orgCode", "t.org_code"),
        Filter::like("orgName", "t.org_name"),
        Filter::eq("orgLevelCode", "t.org_level_code"),
        Filter::eq("orgCategory", "t.org_category"),
        Filter::eq("mileage", "t.mileage"),
        Filter::eq("openDate", "t.open_date"),
    ],
    extra_where: "",
    order_by: "t.road_code, t.section_code",
    id_column: "t.id",
};

// Java 实体 startPileNo/endPileNo/mileage 为 Integer，openDate 为 LocalDate。
const FORMATS: &[(&str, FieldFormat)] = &[
    ("startPileNo", FieldFormat::Int),
    ("endPileNo", FieldFormat::Int),
    ("mileage", FieldFormat::Int),
    ("openDate", FieldFormat::DateOnly),
];

static LOG_EXPORT: LogSpec = LogSpec::new(
    "路段信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.OdsSzdnSectionController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "路段信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.OdsSzdnSectionController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "路段信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.OdsSzdnSectionController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "路段信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.OdsSzdnSectionController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/section/list",
            meta::get_route("/base/section/list", None, None, list),
        )
        .route(
            "/base/section/listAll",
            meta::get_route("/base/section/listAll", None, None, list),
        )
        .route(
            "/base/section/export",
            meta::get_route(
                "/base/section/export",
                Some("base:section:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/section/{ids}",
            meta::get_route("/base/section/{ids}", None, None, get_info),
        )
        .route(
            "/base/section",
            meta::post_route("/base/section", Some("base:section:add"), Some(&LOG_ADD), add).merge(
                meta::put_route("/base/section", Some("base:section:edit"), Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/base/section/{ids}",
            meta::delete_route(
                "/base/section/{ids}",
                Some("base:section:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all_fmt(&state.db, &params, &SPEC, FORMATS).await?;
    let headers = [
        "路线编码", "路线名称", "路段编码", "路段名称", "起点桩号", "终点桩号", "机构代码",
        "机构名称", "层级代码", "机构分类", "里程", "通车日期",
    ]
    .map(str::to_string);
    let fields = [
        "roadCode", "roadName", "sectionCode", "sectionName", "startPileNo", "endPileNo",
        "orgCode", "orgName", "orgLevelCode", "orgCategory", "mileage", "openDate",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "路段信息数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &id, FORMATS).await?,
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "ods_szdn_section", "id", false, false).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "ods_szdn_section", "id", false, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "ods_szdn_section", "id", &ids).await?;
    Ok(support::success_count(count))
}
