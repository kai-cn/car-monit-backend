// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsYhglVBaseOrgController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsYhglVBaseOrgMapper.xml
// 职责: 机构信息 CRUD 与导出。
// 对应关系: list/export/getInfo/add/edit/remove -> SPEC + save_or_update。

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
    select: "t.big_id, t.org_code, t.org_name, t.org_short_name, t.org_parent_id, \
             t.org_level_code, t.org_is_virtual, t.org_maintenance, t.org_sequence, \
             t.org_is_manager, t.org_is_deleted, t.org_category, t.org_is_authorized, \
             t.org_address, t.org_is_yh_autarky, t.load_time, t.grade_level, \
             (select t1.big_id from ods_yhgl_v_base_org t1 \
              where t1.org_code = t.org_parent_id) parentId",
    from: "from ods_yhgl_v_base_org t",
    filters: &[
        Filter::eq("bigId", "t.big_id"),
        Filter::eq("orgCode", "t.org_code"),
        Filter::like("orgName", "t.org_name"),
        Filter::like("orgShortName", "t.org_short_name"),
        Filter::eq("orgParentId", "t.org_parent_id"),
        Filter::eq("orgLevelCode", "t.org_level_code"),
        Filter::eq("orgIsVirtual", "t.org_is_virtual"),
        Filter::eq("orgMaintenance", "t.org_maintenance"),
        Filter::eq("orgSequence", "t.org_sequence"),
        Filter::eq("orgIsManager", "t.org_is_manager"),
        Filter::eq("orgIsDeleted", "t.org_is_deleted"),
        Filter::eq("orgCategory", "t.org_category"),
        Filter::eq("orgIsAuthorized", "t.org_is_authorized"),
        Filter::eq("orgAddress", "t.org_address"),
        Filter::eq("orgIsYhAutarky", "t.org_is_yh_autarky"),
        Filter::eq("loadTime", "t.load_time"),
        Filter::eq("gradeLevel", "t.grade_level"),
    ],
    extra_where: "",
    order_by: "t.big_id",
    id_column: "t.big_id",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "机构信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.OdsYhglVBaseOrgController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "机构信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.OdsYhglVBaseOrgController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "机构信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.OdsYhglVBaseOrgController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "机构信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.OdsYhglVBaseOrgController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/org/list",
            meta::get_route("/base/org/list", None, None, list),
        )
        .route(
            "/base/org/export",
            meta::get_route(
                "/base/org/export",
                Some("base:org:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/org/{bigIds}",
            meta::get_route("/base/org/{bigIds}", None, None, get_info),
        )
        .route(
            "/base/org",
            meta::post_route("/base/org", Some("base:org:add"), Some(&LOG_ADD), add).merge(
                meta::put_route("/base/org", Some("base:org:edit"), Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/base/org/{bigIds}",
            meta::delete_route(
                "/base/org/{bigIds}",
                Some("base:org:remove"),
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
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "机构代码", "机构名称", "机构简称", "上级机构ID", "层级代码",
        "是否虚机构 1：虚机构，0：非需机构", "是否是养护类", "机构顺序",
        "是否管理单位，主要指是否是路段管理单位(1：是,0：否)", "是否删除 1：是 0：否",
        "机构分类： 01集团 02公司 03管理中心 10部门 11所 12服务区 13养护区 14站 15项目办 16信息中心 17项目部  99其它",
        "是否授权机构 1：是 0：否", "机构地址", "是自营养护单位", "加载时间", "分类分级",
    ]
    .map(str::to_string);
    let fields = [
        "orgCode", "orgName", "orgShortName", "orgParentId", "orgLevelCode", "orgIsVirtual",
        "orgMaintenance", "orgSequence", "orgIsManager", "orgIsDeleted", "orgCategory",
        "orgIsAuthorized", "orgAddress", "orgIsYhAutarky", "loadTime", "gradeLevel",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            // @Excel(readConverterExp = "1=：是，0否")
            if let Some(Value::String(text)) = values.get(6).cloned() {
                values[6] = Value::String(match text.as_str() {
                    "1" => "：是".to_string(),
                    "0" => "否".to_string(),
                    _ => text,
                });
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "机构信息数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &big_id).await?,
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "ods_yhgl_v_base_org", "big_id", false, false)
        .await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "ods_yhgl_v_base_org", "big_id", false, false)
        .await
}

async fn remove(
    State(state): State<AppState>,
    Path(big_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&big_ids);
    let count =
        support::soft_delete_by_ids(&state.db, "ods_yhgl_v_base_org", "big_id", &ids).await?;
    Ok(support::success_count(count))
}
