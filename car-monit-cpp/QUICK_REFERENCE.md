# QUICK_REFERENCE —— 一页纸速查（Spring Boot → C++）

> 看到 Java 代码里的这个东西，去 C++ 的哪里找？语义以 `COMPATIBILITY.md` 为准。

## 1. 启动 / 请求生命周期

| Java | C++ | 说明 |
|---|---|---|
| `RuoYiApplication`（`@SpringBootApplication`） | `src/cm/main.cpp` | 配置 → 日志 → DB/Redis → Token → 路由 → Server |
| `application.yml` / `application-druid.yml` | `config/application.yaml` / `application-druid.yaml` | key 名保持一致；环境变量 `CM_XXX` / `XXX` 可覆盖 |
| `DispatcherServlet` | `cm::web::Router` + `Router::match` | 手写三段式匹配 `/{var}` |
| `@RestController` / `@RequestMapping` | `Router` + `registerXxxController(Router&)` | 聚合入口 `cm::web::registerControllers` |
| `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` | `.get()` / `.post()` / `.put()` / `.del()` | `@RequestMapping(method=…)` 用 `.add(method, …)` |
| `@PathVariable` | `ctx.pathVar("id")` / `ctx.pathVarLong("id")` | 类型不匹配的报错文案已复刻 |
| `@RequestParam` | `ctx.param("x")` / `ctx.optParam` / `ctx.params` | 缺失返回 `""`，不是 400 |
| `@RequestBody` | `ctx.body()`（`nlohmann::ordered_json`） | 解析失败 → `JSON parse error…` code 500 |
| `@RequestHeader` | `ctx.getHeader("X-…")` | 头名大小写不敏感 |
| `HttpServletRequest` / `ResponseEntity` | `cm::http::HttpRequest` / `ApiResponse` | `ApiResponse::json/text/…` |

## 2. 鉴权 / Security

| Java | C++ |
|---|---|
| `SecurityConfig`（antMatchers） | `Router::securityRule` + `cm::web::Server` 分发 |
| `JwtAuthenticationTokenFilter` | `Server` 认证阶段 + `TokenService::getLoginUser` |
| `AuthenticationEntryPointImpl` | `cm::web::Errors::unauthorized`（小写 `charset=utf-8`） |
| `TokenService`（`createToken/verifyToken/refreshToken`） | `cm::security::TokenService` |
| `JwtUtils`（jjwt 0.9.1 HS512） | `cm::security::Jwt`（Base64 解码 secret，19 字节） |
| `SecurityUtils.getLoginUser()/getUserId()/hasPermi()` | `cm::security::SecurityUtils`（`thread_local`） |
| `@PreAuthorize("@ss.hasPermi('a:b:c')")` | `.permi("a:b:c")` |
| `@PreAuthorize("@ss.hasAnyPermi('a,b')")` | `.anyPermi("a,b")` |
| `@PreAuthorize("@ss.hasRole('admin')")` | `.role("admin")` |
| `permitAll()` / `anonymous()` / `denyAll()` | `.permitAll()` / `.anonymous()` / `.denyAll()` |

## 3. 返回值 / 序列化

| Java | C++ | 关键点 |
|---|---|---|
| `AjaxResult`（继承 HashMap） | `cm::core::domain::AjaxResult` | 输出 `msg` 在 `code` 之前（HashMap 桶序） |
| `TableDataInfo` | `cm::core::page::TableDataInfo` | 固定 `total → rows → code → msg` |
| `R<T>` | `cm::core::domain::R` | 固定 `code → msg → data`（null 也输出） |
| `BaseController.success/error/warn/toAjax` | `cm::web::BaseController::*` | 同文案 |
| `BaseController.getDataTable(list)` | `BaseController::dataTable(rows, total)` | `rows` 必须是 `Json::array()` |
| `BaseEntity`（createBy/createTime/params） | `cm::common::core::domain::BaseEntity` | `params` 用于 `dataScope` |
| `@JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")` | `DateUtils::formatJsonDate` | 时区固定 `+08:00` |
| `Date` 默认序列化 | `DateUtils::formatIsoDate` | `2024-05-17T14:15:52.000+08:00` |
| `@JsonIgnore`（password） | `SysUser::toJson` 不输出 | 手写序列化，无反射 |
| `@JsonInclude(NON_EMPTY)`（RouterVo/MetaVo） | `SysMenuService::buildMenus` | 空字段不输出 |

## 4. 数据访问

| Java | C++ |
|---|---|
| Druid `DataSource` | `cm::db::Db` + `MySqlClient`（连接池） |
| MyBatis `@Mapper` + `XxxMapper.xml` | `cm::system::mapper::XxxMapper`（`.cpp` 里手写 SQL） |
| `#{}` 参数绑定 | `cm::db::Db::lit(value)` 拼字面量（**必须**） |
| `${params.dataScope}` | 直接拼接 `DataScopeAspect` 产出的片段 |
| `PageHelper.startPage()` + `getDataTable()` | `ctx.pageRequest()` + `cm::db::queryPage(countSql, dataSql, page)` |
| `PageDomain` / `TableSupport` | `cm::core::page::PageDomain` / `RequestContext::pageDomain` |
| `SqlUtil.escapeOrderBySql` | `cm::utils::sql::SqlUtil`（`orderByColumn` 非法 → “参数不符合规范，不能进行查询”） |
| `@Transactional` | `MySqlConnection::begin/commit/rollback`（`ConnectionPool` 借出连接） |
| `LambdaQueryWrapper` / MyBatis-Plus | 直接写 SQL；无 ORM 映射层 |
| ShardingSphere 月表 | `AppConfig::shardingTablePrefix` 手拼后缀（❌ 无路由） |

## 5. 工具类

| Java | C++ |
|---|---|
| `StringUtils` | `cm::utils::StringUtils` |
| `DateUtils` | `cm::utils::DateUtils` |
| `IdUtils`（`simpleUuid/fastUUID`） | `cm::utils::simpleUuid` / `fastUuid` |
| `JsonUtils` | `cm::jstr/jlong/jbool/…` + `cm::Json` |
| `Convert` / `ServletUtils` | `cm::utils::Convert` / `cm::http::*` |
| `Constants` / `UserConstants` / `HttpStatus` | `cm::constant::Constants` / `UserConstants` / `HttpStatus` |
| `CacheConstants` | `cm::constant::Constants::*_KEY` |
| `BCryptPasswordEncoder` | `cm::security::SecurityUtils::encryptPassword/matchesPassword`（libbcrypt） |
| `Kaptcha` | `cm::utils::CaptchaUtil`（PNG，⚠️ 非 JPEG） |
| POI `ExcelUtil` | `cm::utils::Excel`（最小 XLSX，⚠️ 单 sheet） |
| `RedisTemplate` / `RedisCache` | `cm::redis::RedisCache`（纯 JSON，⚠️ 无 `@type`） |
| Logback + `logback.xml` | `cm::log::Logger`（`logs/app.log`，50MB×10） |

## 6. 异常

| Java | C++ | HTTP / code |
|---|---|---|
| `ServiceException("msg")` | `cm::exception::ServiceException` | 200 / 500 |
| `CustomException` / `BaseException` / `UserException` | 同名异常 | 200 / 500（**不是** 403） |
| `AccessDeniedException` | `cm::exception::AccessDeniedException` | 200 / 403 |
| `MethodArgumentTypeMismatchException` | 路由层类型解析 | 200 / 500 + 原文案 |
| 未捕获 `RuntimeException` | `ExceptionMapper` 兜底 | 200 / 500 |
| `AuthenticationException` | `Errors::unauthorized` | 200 / 401，小写 charset |
| 无匹配路由（已认证） | `Errors::containerError(404, path)` | **真实 404** |

## 7. 五个最容易写错的点

1. **`AjaxResult` 是 HashMap**：`msg` 先于 `code`，不要按 `put` 顺序输出。
2. **SQL 必须 `Db::lit`**：没有 PreparedStatement；漏转义 = SQL 注入。
3. **分页 `total=0` 时不要查数据**：`queryPage` 已实现 PageHelper 语义。
4. **401 的 `Content-Type` 是小写 `utf-8`**，Controller 返回是大写 `UTF-8`。
5. **`anonymous()` 是“仅匿名可访问”**，已登录访问返回真实 403。

---

配套：`README_CPP.md`（跑起来）· `MIGRATION_GUIDE.md`（分层细节）· `COMPATIBILITY.md`（差异清单）· `ENDPOINTS_INVENTORY.md`（端点状态）
