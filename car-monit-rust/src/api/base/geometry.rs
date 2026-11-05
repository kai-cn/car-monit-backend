// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/GeometryController.java
//       ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml
// 职责: 路线几何点查询/维护，以及桩号批量转经纬度（恒达接口）。
// 对应关系: getHenDa/syncAllGeometry/syncAllGeometry1/list/export/get/add/edit/remove。
// 说明: Java 的 syncGeometry 用线程池 fire-and-forget；这里用 tokio::spawn，接口同样立即返回。

use axum::extract::{Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Value};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support::{self, AutoFill, FieldFormat, Filter, ListSpec};
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::service::hen_da;
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    // zhStr 是 Java 实体里的 transient 字段（Mapper 不查询，Jackson 输出 null）。
    select: "t.id, t.lxbh, t.lxfx, t.qdzh, t.zdzh, t.paths, null as zhStr",
    from: "from geometry t",
    filters: &[
        Filter::eq("id", "t.id"),
        Filter::eq("lxbh", "t.lxbh"),
        Filter::eq("lxfx", "t.lxfx"),
        Filter::eq("qdzh", "t.qdzh"),
        Filter::eq("zdzh", "t.zdzh"),
        Filter::eq("paths", "t.paths"),
    ],
    extra_where: "",
    order_by: "t.lxbh, t.qdzh",
    id_column: "t.id",
};

// Java 实体 id/qdzh/zdzh 为 Integer。
const FORMATS: &[(&str, FieldFormat)] = &[
    ("id", FieldFormat::Int),
    ("qdzh", FieldFormat::Int),
    ("zdzh", FieldFormat::Int),
];

static LOG_EXPORT: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Export,
    "com.ruoyi.web.controller.base.GeometryController.export()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Insert,
    "com.ruoyi.web.controller.base.GeometryController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Update,
    "com.ruoyi.web.controller.base.GeometryController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "车辆信息",
    BusinessType::Delete,
    "com.ruoyi.web.controller.base.GeometryController.remove()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/geometry/getHenDa",
            meta::get_route(
                "/base/geometry/getHenDa",
                Some("base:geometry:list"),
                None,
                get_hen_da,
            ),
        )
        .route(
            "/base/geometry/syncAllGeometry",
            meta::get_route("/base/geometry/syncAllGeometry", None, None, sync_all),
        )
        .route(
            "/base/geometry/syncAllGeometry1",
            meta::get_route("/base/geometry/syncAllGeometry1", None, None, sync_one),
        )
        .route(
            "/base/geometry/list",
            meta::get_route(
                "/base/geometry/list",
                Some("base:geometry:list"),
                None,
                list,
            ),
        )
        .route(
            "/base/geometry/export",
            meta::get_route(
                "/base/geometry/export",
                Some("base:geometry:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/base/geometry/{ids}",
            meta::get_route("/base/geometry/{ids}", None, None, get_info),
        )
        .route(
            "/base/geometry",
            meta::post_route(
                "/base/geometry",
                Some("base:geometry:add"),
                Some(&LOG_ADD),
                add,
            )
            .merge(meta::put_route(
                "/base/geometry",
                Some("base:geometry:edit"),
                Some(&LOG_EDIT),
                edit,
            )),
        )
        .route(
            "/base/geometry/{ids}",
            meta::delete_route(
                "/base/geometry/{ids}",
                Some("base:geometry:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

async fn get_hen_da(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let pivot = hen_da::get_pile_to_lon_lat(
        &state,
        params.get("lxbh").map(String::as_str),
        params.get("zhStr").map(String::as_str),
        params.get("lxfx").map(String::as_str),
    )
    .await;
    Ok(AjaxResult::success_data(pivot))
}

/// Java: `syncAllGeometry()` —— 补齐 geometry_copy1 中落后于 geometry 的路线段。
async fn sync_all(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let rows: Vec<(Option<String>, Option<String>, Option<i32>)> = sqlx::query_as(
        "select t1.lxbh, t1.lxfx, IFNULL(t2.zdzh, t1.qdzh) qdzh \
         from (select lxbh, lxfx, min(qdzh) qdzh, max(zdzh) zdzh FROM geometry_copy1 \
               group by lxbh, lxfx) t1 \
         left join (select lxbh, lxfx, min(qdzh) qdzh, max(zdzh) zdzh FROM geometry \
                    group by lxbh, lxfx) t2 \
           on t1.lxbh = t2.lxbh and t1.lxfx = t2.lxfx \
         where t2.zdzh is null or t2.zdzh < t1.zdzh \
         order by t1.lxbh",
    )
    .fetch_all(&state.db)
    .await?;

    for (lxbh, lxfx, qdzh) in rows {
        spawn_sync(state.clone(), lxbh, lxfx, qdzh);
    }
    Ok(AjaxResult::success())
}

/// Java: `syncAllGeometry1(Geometry geometry)` —— 手动补齐单个起点桩号。
async fn sync_one(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    spawn_sync(
        state,
        params.get("lxbh").cloned(),
        params.get("lxfx").cloned(),
        params.get("qdzh").and_then(|value| value.parse().ok()),
    );
    Ok(AjaxResult::success())
}

fn spawn_sync(state: AppState, lxbh: Option<String>, lxfx: Option<String>, qdzh: Option<i32>) {
    tokio::spawn(async move {
        // Java: qdzh 为 null 时在 qdzh + 1 处拆箱 NPE，任务终止（被线程池吞掉）。
        let Some(mut start) = qdzh else { return };
        let lxbh = lxbh.unwrap_or_else(|| "null".to_string());
        let lxfx = lxfx.unwrap_or_else(|| "null".to_string());
        let mut points: Vec<(f64, f64)> = Vec::new();
        let mut count = 10;
        let mut i = 0;
        while count >= 7 {
            let pile = if i < 10 {
                format!("{start}.{i}")
            } else {
                format!("{}", start + 1)
            };
            if let Some(pivot) =
                hen_da::get_pile_to_lon_lat(&state, Some(&lxbh), Some(&pile), Some(&lxfx)).await
            {
                let lon = double_value(&pivot, "longitude");
                let lat = double_value(&pivot, "latitude");
                if let (Some(lon), Some(lat)) = (lon, lat) {
                    points.push((lon, lat));
                }
            }
            if i == 10 {
                count = points.len() as i32;
                if points.len() >= 5 {
                    let body = json!({
                        "lxbh": lxbh,
                        "lxfx": lxfx,
                        "qdzh": start,
                        "zdzh": start + 1,
                        "paths": deep_to_string(&points),
                    });
                    if let Err(err) =
                        support::insert_entity(&state.db, "geometry", &body, AutoFill::NONE).await
                    {
                        tracing::warn!("【恒达】写入 geometry 失败: {err}");
                    }
                }
                points.clear();
                start += 1;
                i = 0;
            } else {
                i += 1;
            }
        }
    });
}

/// Java: `JSONObject.getDoubleValue(key)` —— 缺失返回 0.0，非数字抛异常。
fn double_value(pivot: &Value, key: &str) -> Option<f64> {
    match pivot.get(key) {
        None | Some(Value::Null) => Some(0.0),
        Some(Value::String(text)) => text.parse().ok(),
        Some(other) => other.as_f64(),
    }
}

/// Java: `Arrays.deepToString(double[][])`。
fn deep_to_string(points: &[(f64, f64)]) -> String {
    let items = points
        .iter()
        .map(|(lon, lat)| format!("[{lon}, {lat}]"))
        .collect::<Vec<_>>();
    format!("[{}]", items.join(", "))
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
    let headers = ["路线编号", "路线方向", "起点桩号", "终点桩号", "经纬度"].map(str::to_string);
    let fields = ["lxbh", "lxfx", "qdzh", "zdzh", "paths"];
    let data = rows
        .iter()
        .map(|row| support::pick_fields(row, &fields))
        .collect::<Vec<_>>();
    support::export_excel(&state, "车辆信息数据", &headers, &data)
}

async fn get_info(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Integer ID`（变量名就叫 ID，报错文案里也是它）。
    let id = support::path_int("ID", &id)?.to_string();
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &id, FORMATS).await?,
    ))
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "geometry", "id", false, false).await
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    support::save_or_update(&state, &user, &body, "geometry", "id", false, false).await
}

async fn remove(
    State(state): State<AppState>,
    Path(ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Integer[] IDs` —— 任一段转不成 Integer 就整体失败，文案带整段原文。
    let ids = support::path_int_list("IDs", &ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    let count = support::soft_delete_by_ids(&state.db, "geometry", "id", &ids).await?;
    Ok(support::success_count(count))
}
