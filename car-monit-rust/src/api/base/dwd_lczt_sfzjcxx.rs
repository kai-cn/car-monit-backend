// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfzjcxxController.java
// 职责: 收费站基础信息 CRUD 与导出。
// 对应关系: DwdLcztSfzjcxxMapper.xml -> SPEC / soft_delete_by_ids。

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
    select: "t.*",
    from: "from dwd_lczt_sfzjcxx t",
    filters: &[
        Filter::eq("agentPk", "t.agent_pk"),
        Filter::eq("yxtzj", "t.yxtzj"),
        Filter::eq("sfzdm", "t.sfzdm"),
        Filter::like("sfzmc", "t.sfzmc"),
        Filter::eq("jd", "t.jd"),
        Filter::eq("wd", "t.wd"),
        Filter::eq("sslxbh", "t.sslxbh"),
        Filter::eq("sslxmc", "t.sslxmc"),
        Filter::eq("ssldbh", "t.ssldbh"),
        Filter::eq("ssldmc", "t.ssldmc"),
        Filter::eq("sczhK", "t.sczh_k"),
        Filter::eq("sczhN", "t.sczh_n"),
        Filter::eq("ssglzxbm", "t.ssglzxbm"),
        Filter::eq("ssglzxmc", "t.ssglzxmc"),
        Filter::eq("lyxt", "t.lyxt"),
        Filter::eq("loadTime", "t.load_time"),
        Filter::eq("allColPk", "t.all_col_pk"),
    ],
    extra_where: "",
    order_by: "t.agent_pk",
    id_column: "t.agent_pk",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.DwdLcztSfzjcxxController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.DwdLcztSfzjcxxController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.DwdLcztSfzjcxxController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "收费站基础信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.DwdLcztSfzjcxxController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/sfzjcxx/list",
            meta::get_route("/base/sfzjcxx/list", None, None, list),
        )
        .route(
            "/base/sfzjcxx/export",
            meta::get_route(
                "/base/sfzjcxx/export",
                Some("base:sfzjcxx:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/sfzjcxx/{agentPks}",
            meta::get_route("/base/sfzjcxx/{agentPks}", None, None, get_info),
        )
        .route(
            "/base/sfzjcxx",
            meta::post_route("/base/sfzjcxx", Some("base:sfzjcxx:add"), Some(&LOG_ADD), add).merge(
                meta::put_route("/base/sfzjcxx", Some("base:sfzjcxx:edit"), Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/base/sfzjcxx/{agentPks}",
            meta::delete_route(
                "/base/sfzjcxx/{agentPks}",
                Some("base:sfzjcxx:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

pub async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
    Ok(TableDataInfo::new(total, rows))
}

pub async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let rows = support::query_all(&state.db, &params, &SPEC).await?;
    let headers = [
        "源系统主键", "收费站代码", "收费站名称", "经度", "纬度", "所属路线编号",
        "所属路线名称", "所属路段编号", "所属路段名称", "所处桩号(K格式)",
        "所处桩号(数值格式)", "所属管理中心编码", "所属管理中心名称", "来源系统", "加载日期",
        "全字段MD5",
    ]
    .map(str::to_string);
    let fields = [
        "yxtzj", "sfzdm", "sfzmc", "jd", "wd", "sslxbh", "sslxmc", "ssldbh", "ssldmc", "sczhK",
        "sczhN", "ssglzxbm", "ssglzxmc", "lyxt", "loadTime", "allColPk",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "收费站基础信息数据", &headers, &data)
}

pub async fn get_info(
    State(state): State<AppState>,
    Path(agent_pk): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id(&state.db, &SPEC, &agent_pk).await?,
    ))
}

pub async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "dwd_lczt_sfzjcxx", "agent_pk", false, false).await
}

pub async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "dwd_lczt_sfzjcxx", "agent_pk", false, false).await
}

pub async fn remove(
    State(state): State<AppState>,
    Path(agent_pks): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&agent_pks);
    let count = support::soft_delete_by_ids(&state.db, "dwd_lczt_sfzjcxx", "agent_pk", &ids).await?;
    Ok(support::success_count(count))
}
