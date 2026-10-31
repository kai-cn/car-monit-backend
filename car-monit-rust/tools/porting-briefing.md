# 切片移植约定（执行者必读）

你在把 Java（RuoYi 3.8.7 + MyBatis-Plus + Spring MVC）后端 1:1 迁移到 Rust（Axum 0.8 + sqlx 0.8 + tokio）。
基础设施（JWT/Redis/分页/分片/6 个 @Scheduled/路由权限与操作日志中间件/动态行映射/Excel 导出）已完成，**不要重写**。

## 路径

- Rust 项目根：`D:\work\IdeaProjects\car-monit-backend-new\car-monit-rust`
- Java 根：`D:\work\IdeaProjects\car-monit-backend-new`（ruoyi-admin / ruoyi-system / ruoyi-common / ruoyi-framework / ruoyi-quartz / ruoyi-generator）
- 端点清单（附录 B，method/path/权限/@Log/参数/返回）：`car-monit-rust/docs/01-baseline/02-endpoints.md`
- 表结构（附录 C）：`car-monit-rust/docs/01-baseline/03-data-layer.md`

## 必读 Rust 文件

`src/api/auth.rs`、`src/api/meta.rs`、`src/api/support.rs`、`src/db/rows.rs`、`src/repository/user_repo.rs`、`src/response.rs`、`src/error.rs`、`src/state.rs`、`src/api/<切片>/mod.rs`。

## 硬性约定

1. **只修改分配给你的文件**。切片 `mod.rs` 已预生成并 merge 了所有控制器路由，不要改。不要改 `lib.rs` / `Cargo.toml` / `src/api/mod.rs` / `meta.rs` / `support.rs` / `db/rows.rs` / 其他切片。不要新增依赖。
2. 每个控制器文件导出 `pub fn routes() -> Router<AppState>`：
   ```rust
   use crate::api::meta::{self, BusinessType, LogSpec};
   static LOG_ADD: LogSpec = LogSpec::new(
       "用户管理",
       BusinessType::Insert,
       "com.ruoyi.web.controller.system.SysUserController.add()",
   );
   pub fn routes() -> Router<AppState> {
       Router::new()
           .route("/system/user/list", meta::get_route("/system/user/list", Some("system:user:list"), None, list))
           .route("/system/user/{userId}", meta::get_route("/system/user/{userId}", None, None, get_info))
           .route(
               "/system/user",
               meta::post_route("/system/user", Some("system:user:add"), Some(&LOG_ADD), add)
                   .merge(meta::put_route("/system/user", Some("system:user:edit"), Some(&LOG_EDIT), edit)),
           )
   }
   ```
   - pattern 用 axum 0.8 语法：路径参数写 `{userId}`；`Router::route` 的 path 必须是同一字符串。
   - `permission` = `@PreAuthorize` 字符串（`@ss.hasPermi('x')` → `Some("x")`）；`hasAnyPermi` 这种“任一权限”请在 handler 内用 `support::require_permission` 逐个判断，meta 传 `None`。无注解 → `None`。
   - `log` = `@Log` 时 `Some(&static LogSpec)`，method 字段用 Java 全类名 + `.方法名()`；无注解 → `None`。
   - 同一路径多方法用 `MethodRouter::merge`，**不要**对同一路径调用两次 `Router::route`（会 panic）。
   - 权限与 @Log 由中间件统一执行，handler 内不要重复查权限（`hasAnyPermi` 除外）。
3. 列表端点：
   ```rust
   pub async fn list(
       State(state): State<AppState>,
       RawQuery(raw): RawQuery,
       Query(filter): Query<SysUserQuery>,
   ) -> Result<TableDataInfo<Value>, AppError> {
       let page = support::page_domain(&raw);
       // count ... + select ... 同一组 where；limit/offset 用 support::page_window(&page, total)
       let rows = crate::db::rows::rows_to_json(&rows);
       Ok(TableDataInfo::new(total, rows))
   }
   ```
   - 过滤结构体：`#[derive(Debug, Default, serde::Deserialize)] #[serde(rename_all = "camelCase", default)]`，字段全 `Option`。
   - `<if test="x != null and x != ''">` 对应 `filter.x.as_deref().is_some_and(|v| !v.is_empty())`（空串视为未传）。
   - order by：`let order = page.escape_order_by_sql()?;`，非空才追加；XML 没有 order by 且前端未传时不要自造排序。
   - 行数据一律 `crate::db::rows::rows_to_json(&rows)`（下划线列名自动转 camelCase，日期 `yyyy-MM-dd HH:mm:ss`）。
4. SQL：`sqlx::QueryBuilder<MySql>` + `push_bind`。严格照 MyBatis XML 的 join / where / like / 排序 / `params.dataScope` 语义。禁止把用户输入拼进 SQL。
   - `@DataScope`：Java 在 service 里拼 `params.dataScope`（形如 `and (u.dept_id in (...))`），照 `SysUserServiceImpl.selectUserList` / `SysRoleServiceImpl` 的构造逻辑复刻；至少覆盖 admin 与“本部门及以下”。
5. 单表 CRUD 可用：
   - `support::insert_entity(&state.db, "sys_user", &json, fill)`
   - `support::update_entity_by_id(&state.db, "sys_user", "user_id", &json, fill)`
   - `support::delete_by_ids(&state.db, "sys_user", "user_id", &ids)`
   （MyBatis-Plus NOT_NULL 语义；实体继承 BaseEntity 时用 `support::AutoFill { enabled: true, username: Some(&user.username()) }`，否则 `AutoFill::NONE`。）
6. 返回封套：`AjaxResult::success()/success_msg()/success_data(v)/error(msg)`。业务错误 `AppError::Service("...".into())`（HTTP 仍 200，body code=500）；参数/校验错误 `AppError::Validation`。Java `AjaxResult.success(count)` 用 `support::success_count(rows)`；`toAjax(rows)` 用 `support::to_ajax(rows)`。
7. Redis：service 里出现 `redisCache.setCacheObject/getCacheObject/deleteObject` 时用 `state.redis` 复刻，**key 必须去 Java `Constants` / `CacheConstants` 查真实字符串**，TTL 一致。
8. 导出：`support::export_excel(&state, "<sheetName>", &headers, &rows)` → `AjaxResult`（data=文件名）。
   - `headers` 按实体 `@Excel(name=...)` 顺序；`rows` 用 `support::pick_fields(&row, &["fieldA", ...])` 从 JSON 行取 camelCase 字段。
   - `@Excel(readConverterExp = "0=男,1=女")` / `dateFormat` 需要等价的字符串转换。
   - Java 的 sheetName 就是 `exportExcel(list, "XXX数据")` 里的字符串。
9. Java 自身 bug（空转、列不存在、死代码）按原样复刻，代码里一行中文注释说明。用户决策：6 个 @Scheduled 必须生效（已实现）、死代码类照样迁移、其余按最佳实践。依赖未迁移外部系统（Kafka/ES/OSS/SMS）的端点，实现可编译的等价版本并注释欠账，不要 panic。
10. 文件头注释（参考 `src/api/auth.rs`）：
    ```rust
    // 来源: ruoyi-system/src/main/java/com/ruoyi/system/controller/SysUserController.java
    // 职责: 用户管理 CRUD + 导入导出 + 授权。
    // 对应关系: @GetMapping("/list") -> list；selectUserList -> ...
    ```
    关键 SQL 上方一行 `// Java: SysUserMapper.xml#selectUserList`。

## 编译验证

全部写完后运行：

```bash
cd /d/work/IdeaProjects/car-monit-backend-new/car-monit-rust
CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo check --lib
```

修掉所有指向你文件的 error/warning。若报错来自别的切片目录（其他 agent 正在并行写），忽略并在报告里注明；可隔一会儿重跑。
纯函数可写 `#[cfg(test)]` 单测；不要为依赖 DB 的 handler 造 mock。

## 最终报告（≤400 字）

逐控制器列出：已实现端点数量、未实现/存疑项、有意偏差。
