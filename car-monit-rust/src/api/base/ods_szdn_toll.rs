// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollMapper.xml
// 职责: 收费站基础信息 CRUD、导出，列表用 section_list 缓存补路段名称。
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

const SELECT: &str = "t.id, t.road_code, t.id_card, t.toll_code, t.toll_name, t.pile_no, \
     t.org_name, t.hex_code, t.state_code, t.org_code, t.longitude, t.latitude, t.open_date, \
     t.toll_alias_name, t.in_monitor_resource, t.lane_monitor_resource, t.square_monitor_resource, \
     t.dynamic_monitor_resource, t.toll_code_merge, t.state_code_merge, t.toll_name_merge, \
     t.section_code, t.toll_org_code, t.is_access, \n     null as sectionCodeList, null as sectionName";

const SPEC: ListSpec = ListSpec {
    select: SELECT,
    from: "from ods_szdn_toll t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("roadCode", "t.road_code"),
        Filter::eq("idCard", "t.id_card"),
        Filter::eq("tollCode", "t.toll_code"),
        Filter::like("tollName", "t.toll_name"),
        Filter::eq("pileNo", "t.pile_no"),
        Filter::like("orgName", "t.org_name"),
        Filter::eq("hexCode", "t.hex_code"),
        Filter::eq("stateCode", "t.state_code"),
        Filter::eq("orgCode", "t.org_code"),
        Filter::eq("longitude", "t.longitude"),
        Filter::eq("latitude", "t.latitude"),
        Filter::eq("openDate", "t.open_date"),
        Filter::like("tollAliasName", "t.toll_alias_name"),
        Filter::eq("inMonitorResource", "t.in_monitor_resource"),
        Filter::eq("laneMonitorResource", "t.lane_monitor_resource"),
        Filter::eq("squareMonitorResource", "t.square_monitor_resource"),
        Filter::eq("dynamicMonitorResource", "t.dynamic_monitor_resource"),
        Filter::eq("tollCodeMerge", "t.toll_code_merge"),
        Filter::eq("stateCodeMerge", "t.state_code_merge"),
        Filter::like("tollNameMerge", "t.toll_name_merge"),
        Filter::eq("sectionCode", "t.section_code"),
        Filter::eq("tollOrgCode", "t.toll_org_code"),
        Filter::eq("isAccess", "t.is_access"),
        Filter::raw(
            "sectionName",
            " and t.section_code in ( select t1.section_code from ods_szdn_section t1 \
             where t1.section_name like concat('%', ?, '%') )",
        ),
    ],
    extra_where: "",
    order_by: "t.toll_name",
    id_column: "t.id",
};

// Java 实体 openDate 为 LocalDate。
const FORMATS: &[(&str, FieldFormat)] = &[("openDate", FieldFormat::DateOnly)];

static LOG_EXPORT: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.OdsSzdnTollController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.OdsSzdnTollController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.OdsSzdnTollController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.OdsSzdnTollController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/toll/list",
            meta::get_route("/base/toll/list", None, None, list),
        )
        .route(
            "/base/toll/listAll",
            meta::get_route("/base/toll/listAll", None, None, list_all),
        )
        .route(
            "/base/toll/export",
            meta::get_route(
                "/base/toll/export",
                Some("base:toll:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/toll/{ids}",
            meta::get_route("/base/toll/{ids}", None, None, get_info),
        )
        .route(
            "/base/toll",
            meta::post_route("/base/toll", Some("base:toll:add"), Some(&LOG_ADD), add).merge(
                meta::put_route("/base/toll", Some("base:toll:edit"), Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/base/toll/{ids}",
            meta::delete_route(
                "/base/toll/{ids}",
                Some("base:toll:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

/// Java: `redisCache.getCacheList(Constants.SECTION_LIST)` 建 sectionCode -> sectionName。
async fn section_names(state: &AppState) -> std::collections::HashMap<String, String> {
    let mut map = std::collections::HashMap::new();
    if let Ok(list) = state.redis.get_list::<Value>("section_list").await {
        for section in list {
            let code = section.get("sectionCode").and_then(Value::as_str).unwrap_or_default();
            let name = section.get("sectionName").and_then(Value::as_str).unwrap_or_default();
            map.entry(code.to_string()).or_insert_with(|| name.to_string());
        }
    }
    map
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, mut rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    let names = section_names(&state).await;
    for row in &mut rows {
        if let Some(object) = row.as_object_mut() {
            let code = object.get("sectionCode").and_then(Value::as_str).unwrap_or_default();
            let name = names.get(code).cloned().unwrap_or_default();
            object.insert("sectionName".to_string(), Value::String(name));
        }
    }
    Ok(TableDataInfo::new(total, rows))
}

async fn list_all(
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
        "路线编号", "收费站业务唯一编码", "收费站编号", "收费站名称", "桩号", "所属机构名称",
        "收费站HEX编码", "国网编号", "机构编码", "经度", "纬度", "开通日期", "收费站别名",
        "入口治超监控资源，多个以英文逗号分割", "车道抓拍监控资源，多个以英文逗号分割",
        "广场监控资源，多个以英文逗号分割", "动环监控资源，多个以英文逗号分割", "收费站编号",
        "国网编号", "收费站名称", "所属路段编码", "收费站对应机构编码", "流水是否接入",
    ]
    .map(str::to_string);
    let fields = [
        "roadCode", "idCard", "tollCode", "tollName", "pileNo", "orgName", "hexCode",
        "stateCode", "orgCode", "longitude", "latitude", "openDate", "tollAliasName",
        "inMonitorResource", "laneMonitorResource", "squareMonitorResource",
        "dynamicMonitorResource", "tollCodeMerge", "stateCodeMerge", "tollNameMerge",
        "sectionCode", "tollOrgCode", "isAccess",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            // @Excel(readConverterExp = "内=部")
            for index in [2usize, 3, 7] {
                if let Some(Value::String(text)) = values.get(index).cloned() {
                    values[index] = Value::String(convert(&text, "内", "部"));
                }
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "收费站基础信息数据", &headers, &data)
}

fn convert(value: &str, from: &str, to: &str) -> String {
    if value == from {
        to.to_string()
    } else {
        value.to_string()
    }
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
    support::save_or_update(&state, &user, &body, "ods_szdn_toll", "id", false, false).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "ods_szdn_toll", "id", false, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&ids);
    let count = support::soft_delete_by_ids(&state.db, "ods_szdn_toll", "id", &ids).await?;
    Ok(support::success_count(count))
}
