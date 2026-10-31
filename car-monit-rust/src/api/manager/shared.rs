// 来源: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/*ServiceImpl.java 的统一 CRUD 片段。
// 职责: manager 切片里 12 张 BasePlusEntity 表的「列表/导出/详情/增改/逻辑删除」模板。
// 对应关系: mapper XML list + saveXxx + deleteXxxByIds。

/// 生成一个完整的 manager CRUD 控制器（路由 + 处理器）。
///
/// `readConverterExp` 在这些实体上多为畸形串（如 "0=正常1停用"），
/// 这里导出原始值，不做翻译。
#[macro_export]
macro_rules! manager_crud {
    (
        route: $route:literal,
        perm: $perm:literal,
        title: $title:literal,
        class: $class:literal,
        sheet: $sheet:literal,
        table: $table:literal,
        select: $select:literal,
        from: $from:literal,
        order: $order:literal,
        filters: [$($filter:expr),* $(,)?],
        headers: [$($header:literal),* $(,)?],
        fields: [$($field:literal),* $(,)?]
        $(,)?
    ) => {
        use $crate::api::support::{self, Filter, ListSpec};

        const SPEC: ListSpec = ListSpec {
            select: $select,
            from: $from,
            filters: &[$($filter),*],
            extra_where: "",
            order_by: $order,
            id_column: "t.id",
        };

        static LOG_EXPORT: $crate::api::meta::LogSpec = $crate::api::meta::LogSpec::new(
            $title,
            $crate::api::meta::BusinessType::Export,
            concat!($class, ".export()"),
        );
        static LOG_ADD: $crate::api::meta::LogSpec = $crate::api::meta::LogSpec::new(
            $title,
            $crate::api::meta::BusinessType::Insert,
            concat!($class, ".add()"),
        );
        static LOG_EDIT: $crate::api::meta::LogSpec = $crate::api::meta::LogSpec::new(
            $title,
            $crate::api::meta::BusinessType::Update,
            concat!($class, ".edit()"),
        );
        static LOG_REMOVE: $crate::api::meta::LogSpec = $crate::api::meta::LogSpec::new(
            $title,
            $crate::api::meta::BusinessType::Delete,
            concat!($class, ".remove()"),
        );

        pub fn routes() -> axum::Router<$crate::state::AppState> {
            use $crate::api::meta;
            #[allow(unused_mut)]
            let mut router = axum::Router::new()
                .route(
                    concat!($route, "/list"),
                    meta::get_route(concat!($route, "/list"), Some(concat!($perm, ":list")), None, list),
                )
                .route(
                    concat!($route, "/export"),
                    meta::get_route(
                        concat!($route, "/export"),
                        Some(concat!($perm, ":export")),
                        Some(&LOG_EXPORT),
                        export,
                    ),
                )
                .route(
                    concat!($route, "/{ids}"),
                    meta::get_route(concat!($route, "/{ids}"), None, None, get_info),
                )
                .route(
                    $route,
                    meta::post_route($route, Some(concat!($perm, ":add")), Some(&LOG_ADD), add)
                        .merge(meta::put_route(
                            $route,
                            Some(concat!($perm, ":edit")),
                            Some(&LOG_EDIT),
                            edit,
                        )),
                )
                .route(
                    concat!($route, "/{ids}"),
                    meta::delete_route(
                        concat!($route, "/{ids}"),
                        Some(concat!($perm, ":remove")),
                        Some(&LOG_REMOVE),
                        remove,
                    ),
                );
            router
        }

        async fn list(
            axum::extract::State(state): axum::extract::State<$crate::state::AppState>,
            axum::extract::RawQuery(raw): axum::extract::RawQuery,
        ) -> Result<$crate::response::TableDataInfo<serde_json::Value>, $crate::error::AppError> {
            let page = support::page_domain(&raw);
            let params = support::query_map(&raw);
            let (total, rows) = support::query_list(&state.db, &params, &SPEC, &page).await?;
            Ok($crate::response::TableDataInfo::new(total, rows))
        }

        async fn export(
            axum::extract::State(state): axum::extract::State<$crate::state::AppState>,
            axum::extract::RawQuery(raw): axum::extract::RawQuery,
        ) -> Result<$crate::response::AjaxResult, $crate::error::AppError> {
            let params = support::query_map(&raw);
            let rows = support::query_all(&state.db, &params, &SPEC).await?;
            let headers = [$($header.to_string()),*];
            let fields = [$($field),*];
            let data = rows
                .iter()
                .map(|row| support::pick_fields(row, &fields))
                .collect::<Vec<_>>();
            support::export_excel(&state, $sheet, &headers, &data)
        }

        async fn get_info(
            axum::extract::State(state): axum::extract::State<$crate::state::AppState>,
            axum::extract::Path(id): axum::extract::Path<String>,
        ) -> Result<$crate::response::AjaxResult, $crate::error::AppError> {
            Ok($crate::response::AjaxResult::success_data(
                support::query_by_id(&state.db, &SPEC, &id).await?,
            ))
        }

        async fn add(
            axum::extract::State(state): axum::extract::State<$crate::state::AppState>,
            axum::Extension(user): axum::Extension<$crate::domain::LoginUser>,
            axum::Json(body): axum::Json<serde_json::Value>,
        ) -> Result<$crate::response::AjaxResult, $crate::error::AppError> {
            support::save_or_update(&state, &user, &body, $table, "id", true, true).await
        }

        async fn edit(
            axum::extract::State(state): axum::extract::State<$crate::state::AppState>,
            axum::Extension(user): axum::Extension<$crate::domain::LoginUser>,
            axum::Json(body): axum::Json<serde_json::Value>,
        ) -> Result<$crate::response::AjaxResult, $crate::error::AppError> {
            support::save_or_update(&state, &user, &body, $table, "id", true, false).await
        }

        async fn remove(
            axum::extract::State(state): axum::extract::State<$crate::state::AppState>,
            axum::extract::Path(ids): axum::extract::Path<String>,
        ) -> Result<$crate::response::AjaxResult, $crate::error::AppError> {
            let ids = support::ids_param(&ids);
            let count = support::soft_delete_by_ids(&state.db, $table, "id", &ids).await?;
            Ok(support::success_count(count))
        }
    };
}
