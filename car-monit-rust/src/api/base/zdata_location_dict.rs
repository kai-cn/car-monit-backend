// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataLocationDictController.java
//       ruoyi-system/src/main/resources/mapper/base/ZdataLocationDictMapper.xml
// 职责: 车辆位置字典只读查询。
// 对应关系: selectZdataLocationDictList/ById -> SPEC。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, FieldFormat, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.id, t.type, t.name, t.raw_code, t.standard_code, t.roadcode, t.roadname, \
             t.sectioncode, t.sectionname, t.tollcode, t.tollname, t.orgcode, t.orgname, \
             t.created_at, t.updated_at",
    from: "from zdata_location_dict t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("type", "t.type"),
        Filter::like("name", "t.name"),
        Filter::eq("rawCode", "t.raw_code"),
        Filter::eq("standardCode", "t.standard_code"),
        Filter::eq("roadcode", "t.roadcode"),
        Filter::like("roadname", "t.roadname"),
        Filter::eq("sectioncode", "t.sectioncode"),
        Filter::like("sectionname", "t.sectionname"),
        Filter::eq("tollcode", "t.tollcode"),
        Filter::like("tollname", "t.tollname"),
        Filter::eq("orgcode", "t.orgcode"),
        Filter::like("orgname", "t.orgname"),
        Filter::eq("createdAt", "t.created_at"),
        Filter::eq("updatedAt", "t.updated_at"),
    ],
    extra_where: "",
    order_by: "",
    id_column: "t.id",
};

// Java 实体 createdAt/updatedAt 为 LocalDate。
const FORMATS: &[(&str, FieldFormat)] = &[
    ("createdAt", FieldFormat::DateOnly),
    ("updatedAt", FieldFormat::DateOnly),
];

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/location/list",
            meta::get_route("/base/location/list", None, None, list),
        )
        .route(
            "/base/location/{id}",
            meta::get_route("/base/location/{id}", None, None, get_info),
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

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long id` —— 非数字在进控制器前就被 Spring 拦下。
    let id = support::path_long("id", &id)?.to_string();
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &id, FORMATS).await?,
    ))
}
