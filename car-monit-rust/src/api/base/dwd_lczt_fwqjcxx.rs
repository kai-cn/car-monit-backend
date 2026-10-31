// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztFwqjcxxController.java
// 职责: 服务区基础信息 CRUD 与导出。
// 对应关系: DwdLcztFwqjcxxMapper.xml -> SPEC / soft_delete_by_ids。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::Value;

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

// 实体只实现 Custom（无 BasePlusEntity 的 del_flag/审计字段），
// resultMap 列与表列一致，这里用 t.* 并依赖 rows->camelCase 映射。
const SPEC: ListSpec = ListSpec {
    select: "t.*",
    from: "from dwd_lczt_fwqjcxx t",
    filters: &[
        Filter::eq("agentPk", "t.agent_pk"),
        Filter::eq("yxtzj", "t.yxtzj"),
        Filter::eq("fwqbm", "t.fwqbm"),
        Filter::like("fwqmc", "t.fwqmc"),
        Filter::eq("wd", "t.wd"),
        Filter::eq("fxmc", "t.fxmc"),
        Filter::eq("fxdm", "t.fxdm"),
        Filter::eq("jd", "t.jd"),
        Filter::eq("sslxbh", "t.sslxbh"),
        Filter::eq("sslxmc", "t.sslxmc"),
        Filter::eq("ssldbh", "t.ssldbh"),
        Filter::like("ssldmc", "t.ssldmc"),
        Filter::eq("sczhkgs", "t.sczhkgs"),
        Filter::eq("sczhszgs", "t.sczhszgs"),
        Filter::eq("ssglzxbm", "t.ssglzxbm"),
        Filter::eq("ssglzxmc", "t.ssglzxmc"),
        Filter::eq("xzqhmc", "t.xzqhmc"),
        Filter::eq("yyrq", "t.yyrq"),
        Filter::eq("cws", "t.cws"),
        Filter::eq("sfszlkk", "t.sfszlkk"),
        Filter::eq("cdzs", "t.cdzs"),
        Filter::eq("sfcyfw", "t.sfcyfw"),
        Filter::eq("sftgzsfw", "t.sftgzsfw"),
        Filter::eq("sftgqxfw", "t.sftgqxfw"),
        Filter::eq("sftgcsfw", "t.sftgcsfw"),
        Filter::eq("sftgjyfw", "t.sftgjyfw"),
        Filter::eq("mj", "t.mj"),
        Filter::eq("sftgcshfw", "t.sftgcshfw"),
        Filter::eq("xzqhdm", "t.xzqhdm"),
        Filter::eq("synx", "t.synx"),
        Filter::eq("lyxt", "t.lyxt"),
        Filter::eq("loadTime", "t.load_time"),
        Filter::eq("allColPk", "t.all_col_pk"),
    ],
    extra_where: "",
    order_by: "t.fwqmc",
    id_column: "t.agent_pk",
};

static LOG_EXPORT: LogSpec = LogSpec::new(
    "服务区基础信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.DwdLcztFwqjcxxController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "服务区基础信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.DwdLcztFwqjcxxController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "服务区基础信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.DwdLcztFwqjcxxController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "服务区基础信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.DwdLcztFwqjcxxController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/fwqjcxx/list",
            meta::get_route("/base/fwqjcxx/list", None, None, list),
        )
        .route(
            "/base/fwqjcxx/export",
            meta::get_route(
                "/base/fwqjcxx/export",
                Some("base:fwqjcxx:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/fwqjcxx/{agentPks}",
            meta::get_route("/base/fwqjcxx/{agentPks}", None, None, get_info),
        )
        .route(
            "/base/fwqjcxx",
            meta::post_route("/base/fwqjcxx", Some("base:fwqjcxx:add"), Some(&LOG_ADD), add).merge(
                meta::put_route("/base/fwqjcxx", Some("base:fwqjcxx:edit"), Some(&LOG_EDIT), edit),
            ),
        )
        .route(
            "/base/fwqjcxx/{agentPks}",
            meta::delete_route(
                "/base/fwqjcxx/{agentPks}",
                Some("base:fwqjcxx:remove"),
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
        "源系统主键", "服务区编码", "服务区名称", "纬度", "方向名称", "方向代码", "经度",
        "所属路线编号", "所属路线名称", "所属路段编号", "所属路段名称", "所处桩号(K格式)",
        "所处桩号(数值格式)", "所属管理中心编码", "所属管理中心名称", "行政区划名称", "营业日期",
        "车位数", "是否设置了卡口", "充电桩数", "是否餐饮服务", "是否提供住宿服务",
        "是否提供汽修服务", "是否提供超市服务", "是否提供加油服务", "面积(平方米)",
        "是否提供厕所服务", "行政区划代码", "使用年限", "来源系统", "加载日期", "全字段MD5",
    ]
    .map(str::to_string);
    let fields = [
        "yxtzj", "fwqbm", "fwqmc", "wd", "fxmc", "fxdm", "jd", "sslxbh", "sslxmc", "ssldbh",
        "ssldmc", "sczhkgs", "sczhszgs", "ssglzxbm", "ssglzxmc", "xzqhmc", "yyrq", "cws",
        "sfszlkk", "cdzs", "sfcyfw", "sftgzsfw", "sftgqxfw", "sftgcsfw", "sftgjyfw", "mj",
        "sftgcshfw", "xzqhdm", "synx", "lyxt", "loadTime", "allColPk",
    ];
    let data = rows.iter().map(|row| support::pick_fields(row, &fields)).collect::<Vec<_>>();
    support::export_excel(&state, "服务区基础信息数据", &headers, &data)
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
    support::save_or_update(&state, &user, &body, "dwd_lczt_fwqjcxx", "agent_pk", false, false).await
}

pub async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "dwd_lczt_fwqjcxx", "agent_pk", false, false).await
}

pub async fn remove(
    State(state): State<AppState>,
    Path(agent_pks): Path<String>,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(&agent_pks);
    let count = support::soft_delete_by_ids(&state.db, "dwd_lczt_fwqjcxx", "agent_pk", &ids).await?;
    Ok(support::success_count(count))
}
