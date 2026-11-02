# 阶段二交付：Java ↔ Rust 全量映射表

> 迁移源：`D:\work\IdeaProjects\car-monit-backend-new`（RuoYi 3.8.7 / Spring Boot 2.5.15 / Java 8）
> 目标：`car-monit-rust`（Axum + tokio + sqlx）
> 依据：`java-to-rust-refactor-prompt.md` 阶段二 11 个维度
> 基线：`docs/01-MIGRATION-BASELINE.md` + 附录 A–E
> 日期：2026-10-31
> 状态：**阶段二完成；尚未编写任何 Rust 实现代码**

本文件的每张表固定四列：**Java 用法 / Rust 对应写法 / 关键差异 / Java 开发者最容易踩的坑**。
全量明细不重复粘贴，按维度引用已完成的附录：

| 附录 | 全量内容 | 本文件对应维度 |
|---|---|---|
| [A 文件映射](01-baseline/01-file-map.md) | 696 个 Java 文件 → Rust 目标文件 | 1、9 |
| [B 端点清单](01-baseline/02-endpoints.md) | 501 个 HTTP 端点 → Rust handler | 3 |
| [C 数据层](01-baseline/03-data-layer.md) | 75 XML / 481 SQL / 78 表 → repository | 4 |
| [D 配置与中间件](01-baseline/04-config-middleware.md) | Redis/Kafka/ES/Quartz/鉴权/约 100 项配置 | 5、6、7 |
| [E 运行实测](01-baseline/05-runtime-probes.md) | 异常、错误码、封套字段顺序 | 3、8 |

---

## 0. 迁移约定与用户决策

### 0.1 路径约定

| 类别 | Rust 路径 |
|---|---|
| 启动与装配 | `src/main.rs`、`src/lib.rs`、`src/config.rs`、`src/state.rs` |
| HTTP 路由 | `src/api/{base,common,flow,generator,manager,monitor,quartz,system,tool}/**`（每个切片一个 `mod.rs` 汇总 `routes()`） |
| 业务服务 | 控制器内联 SQL（`src/api/<slice>/*.rs`）+ 跨切片复用查询 `src/repository/**` |
| 领域模型 | `src/domain/**` |
| 通用工具 | `src/common/**`（分页、Excel、雪花、密码规则、serde 助手） |
| 基础设施 | `src/db/**`（`redis_cache.rs`、`sharding.rs`、`rows.rs`）；Kafka/ES/OSS/SMS 为可选 feature，尚未接线 |
| 中间件 | `src/middleware/**` + `src/api/meta.rs`（@PreAuthorize/@Log 统一执行） |
| 配置 | `config/application.yaml`（`config` crate，`APP_` 环境变量前缀） |
| 资源 | 代码生成的 26 个 `vm/**.vm` 原样拷入 `car-monit-rust/templates/` 并用 `include_str!` 内嵌；`i18n`/`static` 未迁移（响应文案按 Java 默认 locale 直接内嵌中文） |

### 0.2 用户决策（覆盖基线中的“保持失效”建议）

| 项 | 决策 | 落地位置 |
|---|---|---|
| `@Scheduled` 6 个方法 | **启用** | `src/task/mod.rs`（`JobKind` + `start_scheduler`） |
| ShardingSphere 逻辑表 | **启用**（仓储层路由） | `src/db/sharding.rs` |
| 8 个死代码类 | **照样迁移** | 附录 A 对应行 |
| `/oss/**` | 默认不注册，`oss.info=true` 时注册 | `src/api/system/oss.rs`（未迁移） |
| 环境变量 | `APP_` + `__` | `src/config.rs` |
| 健康检查 | `/health`（新增，默认开启） | `src/api/health.rs` |
| 日志 | stdout + 滚动文件 | `src/main.rs#init_tracing` |
| MySQL TLS | `useSSL=true` → `ssl-mode=PREFERRED` | `config/application.yaml` |

### 0.3 状态标记

- **等价**：行为可逐字节/逐语义对齐。
- **等价（需验证）**：设计已对齐，阶段三需用黄金样本验证。
- **有意偏差**：用户决策或 Rust 生态限制导致，已在“关键差异”列注明。

---

## 1. 语言与类型系统

> 全量文件级映射见附录 A（696 行）。本节覆盖项目中真实出现的类型与语言特性。

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| `String`（可为 null） | `String` / `Option<String>` | Java 的 null 与空串是两个值；Rust 用 `Option` 表达缺失，空串仍是 `Some("")` | 一律写 `String` 会在反序列化 `null` 时失败；需按字段实际可空性选择 |
| `private Integer direction;`（`OdsRtSzdnSnapshotFlowAddcode:88`） | `Option<i32>` | 包装类型对应 `Option`，基本类型 `int` 对应 `i32` | 把 `Integer` 写成 `i32`，DB 的 NULL 会直接报错 |
| `private Long siteid;`（同文件 `:112`） | `Option<i64>` | Java `Long`/`long` 统一为 `i64` | JS 前端对 >2^53 的雪花 ID 会丢精度；Java 现状就是数字，Rust 不要擅自改字符串 |
| `private BigDecimal lon;`（同文件 `:100`） | `rust_decimal::Decimal` | 保留十进制精度；不要用 `f64` | 用 `f64` 会导致经纬度/金额尾差，Excel 导出和 ES 写入都会漂移 |
| `private Date snapshottime;`（同文件 `:123`） | `chrono::NaiveDateTime` + 自定义 serde | Jackson 未加 `@JsonFormat` 的 `Date` 默认输出 epoch 毫秒数；加注解的按 pattern 输出 | Rust 默认 RFC3339，与 Java 的“毫秒数 / `yyyy-MM-dd HH:mm:ss`”都不同，必须逐字段标注 |
| `@JsonFormat(pattern="yyyy-MM-dd") private Date receivedtime;`（同文件 `:131`） | `NaiveDateTime` + `serialize_with = "date_only"` | 反序列化仍可能接收完整时间 | 只改序列化会破坏入参解析；需同时定义 `deserialize_with` |
| `boolean` / `Boolean` | `bool` / `Option<bool>` | 与 `Integer/Integer` 同理 | MyBatis 的 `tinyint(1)` 映射为 `bool` 时，NULL 需 `Option<bool>` |
| `List<T>` / `ArrayList<T>` | `Vec<T>` | 无容量/扩容语义差异 | 大量 `new ArrayList<>()` 只是习惯，Rust 用 `Vec::new()` |
| `Map<String,Object> params`（`BaseEntity:43`） | `serde_json::Map<String, Value>`（`preserve_order`） | Java `HashMap` 无稳定顺序；Rust 默认 `serde_json::Map` 是 BTreeMap | 若要复刻 Jackson 的 HashMap 桶序，需固定 key 集合并自定义序列化，不能依赖 Map 顺序 |
| `Set<T>` / `HashSet<T>` | `HashSet<T>` / `BTreeSet<T>` | 迭代顺序不同 | 导出/日志中若依赖顺序，Java 的 HashSet 顺序本身也不可靠 |
| `class SysUser extends BaseEntity` | `struct SysUser { #[serde(flatten)] base: BaseEntity, ... }` | Rust 无继承；组合 + `flatten` 保持 JSON 扁平结构 | 忘记 `flatten` 会多一层 `base` 字段，前端全部取不到值 |
| `interface Custom { String getId(); void setId(String id); }` | `trait Custom { fn id(&self)->&str; fn set_id(&mut self, id:String); }` | trait 无字段，只有方法 | 不要为了“像 Java”给每个实体造 trait；只在多实现/泛型边界使用 |
| 泛型 `R<T>`（`R.java:11`） | `struct R<T> { code:i32, msg:String, data:Option<T> }` | Java 泛型擦除；Rust 单态化，编译期生成具体类型 | `R<()>` 与 `R<Value>` 的 JSON 输出不同，需按端点选择 |
| `throw new ServiceException(msg)` | `Err(AppError::Service(msg))` | Rust 无受检异常；错误必须显式进入 `Result` | 不要在深层用 `panic!`；会被全局兜底成 500 且无法定制文案 |
| `null` | `Option<T>` | Rust 的 `Option` 是类型系统的一部分 | `unwrap()` 等于主动制造 NPE；生产代码禁止对 DB/请求数据 `unwrap` |
| `final` / 默认可变 | `let` / `let mut` | Rust 默认不可变 | 从 Java 直译时大量变量需要加 `mut`，但不要为了省事全部加 |
| `serialVersionUID` | 无对应 | Rust 无 Java 序列化协议 | 不要保留无用常量 |
| `Objects.equals(a,b)` / `StringUtils.isEmpty` | `a == b` / `s.is_empty()` | `Option` 的比较需显式处理 | `Option<String>` 不能用 `== ""` |
| `String.format("%s", x)` | `format!("{}", x)` | 格式符不同（`%d`→`{}`，`%02d`→`{:02}`） | 日期/金额格式化必须逐个核对 |
| `new Date()` / `System.currentTimeMillis()` | `chrono::Local::now()` / `Utc::now().timestamp_millis()` | Java 默认时区为 JVM 时区（本项目 GMT+8） | 混用 UTC 与本地时间会让 `snapshottime` 偏移 8 小时 |
| 继承多态 `BaseController` | 自由函数 + `PageQuery` 提取器 | 无父类方法继承 | `startPage()` 的隐式行为需显式化，不能“看起来没调用就忘了分页” |
| 受检异常 `throws Exception` | `Result<T, AppError>` | 调用方必须处理 | 用 `?` 传播时注意错误类型转换（`From` 实现） |
| 生命周期/所有权（E0382/E0499/E0502/E0597） | 克隆、`Arc`、拆分借用、`'static`/owned 数据 | Java 全靠 GC，Rust 编译期检查 | E0382=使用已移动值；E0499=同一对象多个可变借用；E0502=可变与不可变借用冲突；E0597=借用活得比所有者久。请求处理中优先 `clone` 小字段、`Arc` 共享大对象，避免跨 `.await` 持借用 |

**本维度结论**：类型映射的核心不是“找同宽类型”，而是**可空性**（`Option`）与**时间/金额精度**（`chrono`/`Decimal`）。阶段三需为 155 个 Domain/DTO/VO 逐字段生成映射并做 JSON 快照对比。

---

## 2. 并发与异步

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| `new Thread(r).start()` | `tokio::spawn(async move { ... })` | Rust task 由运行时调度，不保证 OS 线程 | 在 task 中做阻塞 IO 会卡住 worker；用 `spawn_blocking` |
| `ExecutorService` / `ThreadPoolExecutor` | `tokio::task::JoinSet` + `Semaphore` 限流 | tokio 无“核心/最大线程数 + 队列”同款模型 | 直接 `spawn` 无限任务会打爆 DB 连接池 |
| `ThreadPoolTaskExecutor` 核心 10 / 最大 20 / 队列 200 / `CallerRunsPolicy`（`ThreadPoolConfig:41`） | `Semaphore(20)` + 有界 `mpsc`（容量 200）；满时在调用方执行 | `CallerRunsPolicy` 需显式实现：`try_acquire` 失败则内联执行 | 只加 `Semaphore` 不加内联执行，会在高负载时静默丢任务或无限等待 |
| `ScheduledThreadPoolExecutor` 核心 10（`ThreadPoolConfig:48`） | `tokio::time::interval` + `JoinSet` | Java 的定时线程池是共享的；Rust 每个任务一个 future | 定时任务 panic 会终止该 task；需 `catch_unwind` 或 supervisor 重启 |
| `AsyncManager.execute(TimerTask)` + 10ms 延迟（`AsyncManager:24`） | `tokio::spawn(async { sleep(10ms); ... })` | 语义一致：异步落库登录/操作日志 | 用 `spawn_blocking` 包 SQLx 是反模式；SQLx 本身异步 |
| `CompletableFuture.supplyAsync` + `allOf`（`PartitionParallelQueryService:98-107`） | `futures::future::try_join_all(futs)` | Rust 的 `join_all` 不短路；`try_join_all` 遇错即返回 | 不要用 `tokio::join!` 拼动态数量；用 `JoinSet`/`join_all` |
| `synchronized long nextId()`（`SnowflakeIdWorker:83`） | `Mutex<SnowflakeState>` 或 `AtomicU64` + CAS | Java 锁是对象级；Rust 用显式锁 | 跨 `.await` 持 `std::sync::Mutex` 会编译不过/死锁；用 `parking_lot` 或缩小临界区 |
| `ConcurrentHashMap`（`DataConsistencyService:47/53`） | `DashMap` | 并发读写语义接近 | `DashMap` 的 guard 不能跨 `.await` 持有 |
| `ThreadLocal`：`SecurityUtils`、`TraceContext`、PageHelper | 请求扩展 `Extension<CurrentUser>` + `tracing` span + 显式 `PageQuery` | Rust 无隐式线程上下文 | 在 `tokio::spawn` 中丢失请求上下文；需要 `tracing::Span::current()` 或显式传参 |
| `@Async`（未启用） | 保持同步 `async fn` 顺序调用 | Java 实际同步；Rust 不要“顺手”并发化 | 并发化会改变异常抛出时机与事务边界 |
| Kafka 监听并发 3 | 3 个 consumer task（或 rdkafka 多 consumer） | 并发单位是 task，不是容器线程 | 同一 partition 内顺序必须保持；不要用无序 `join_all` 处理同分区消息 |
| Quartz 线程池 10 | tokio 多线程运行时 + 任务级 `Semaphore` | RAM JobStore 无集群语义 | 任务重入/并发策略需按 `sys_job.concurrent` 复刻 |
| `Runtime.getRuntime().addShutdownHook` | `tokio::signal::ctrl_c` + `axum::serve(...).with_graceful_shutdown` | 关闭顺序需显式编排 | 先停 HTTP，再停消费者/调度器，最后关连接池 |
| 虚拟线程（Loom） | 无对应；tokio task 已是轻量级 | 本项目 Java 8 无 Loom | 不要按 Loom 文章改造现有线程池语义 |

**本维度结论**：并发迁移的关键是**限流与关闭顺序**。`CallerRunsPolicy`、Kafka 分区顺序、Quartz 并发策略三处必须显式实现，不能依赖 tokio 默认行为。

---

## 3. Web 框架

> 501 条端点的逐条映射见附录 B；本节给出框架契约映射。

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| Spring Boot MVC + 内置 Tomcat 9989 | `axum::serve(TcpListener::bind("0.0.0.0:9989"))` | 无 Servlet 容器；无 `web.xml`/Filter 链 | 端口必须保持 9989；健康检查不要占用根路径 |
| `@RestController` + `@RequestMapping("/system/user")` | `Router::new().nest("/system/user", user_routes())` | 路由是显式组合，不靠注解扫描 | 漏注册路由不会启动报错，只会在运行时 404 |
| `@GetMapping("/{id}")` | `.route("/:id", get(get_user))` | Axum 0.7/0.8 路径参数语法为 `:id`（0.8 也支持 `{id}`） | 混用 `{id}`/`:id` 会导致匹配失败；阶段三统一一种 |
| `@PathVariable Long id` | `Path(id): Path<i64>` | 类型解析失败由 extractor 返回 400（Axum 默认） | Java 实测是 HTTP 200 + `{"code":500,...}`；需自定义 rejection 映射 |
| `@RequestParam(required=false) String x` | `Query<FooQuery>`（字段 `Option<String>`） | Spring 的 `required/defaultValue` 需用 `Option` + `#[serde(default)]` | 数组参数 `a=1&a=2` 与 `a=1,2` 的兼容需自定义 deserializer |
| `@RequestBody SysUser user` | `Json<SysUser>` | 反序列化失败默认 400；Java 实测 200+500 | 需接住 `JsonRejection` 并转 `AppError::Internal` |
| `@RequestHeader("Authorization")` | `HeaderMap` 或自定义 `AuthHeader` extractor | 无隐式参数注入 | Bearer 前缀可省略的规则要在 extractor 内实现一次 |
| `MultipartFile` / `MultipartFile[]` | `Multipart` | 字段名、单/多文件、临时文件落盘行为不同 | 大文件（40MB/200MB）需流式处理，不能全量进内存 |
| `HttpServletResponse.getOutputStream()` | `Response<Body>` / `Body::from_stream` / `ServeFile` | Rust 需显式设置 header/状态 | `Content-Disposition` 的文件名编码（RFC 5987）必须与 Java 一致 |
| `@ControllerAdvice` + `@ExceptionHandler` | `AppError: IntoResponse` + `handle_error` | 无异常类型匹配，靠 enum | 404 不受 `AppError` 控制，需 `fallback` |
| `AuthenticationEntryPointImpl` | 认证中间件直接返回 `(StatusCode::OK, Json(...))` | 必须在中间件层返回 HTTP 200 | 抛 401 状态码会与 Java 实测不一致 |
| `@PreAuthorize("@ss.hasPermi('a:b:c')")` | 路由元数据 `permission` + 统一守卫 | 无 SpEL；权限字符串来自附录 B | 284 个权限点漏一个就是越权/误拒 |
| Spring Security Filter Chain | `tower::ServiceBuilder` 层：TraceId → CORS → Auth → XSS → 路由 | 层序即执行序 | CORS 必须在认证之前，否则预检请求被 401 |
| `CorsFilter`（`ResourcesConfig:55`） | `tower_http::cors::CorsLayer` | 允许任意 origin pattern、credentials=true、maxAge=1800 | `allow_credentials(true)` 不能配 `Any` origin；需 `AllowOrigin::mirror_request()` |
| `XssFilter` | 读体重写中间件 | 只清洗 `/system/*,/monitor/*,/tool/*`，排除 `/system/notice` | 不能清洗 multipart；GET/DELETE 跳过 |
| `RepeatableFilter` | `axum::body::Bytes` 天然可重放 | 无 `ContentCachingRequestWrapper` | 大 body 全量缓冲会增内存 |
| `SameUrlDataInterceptor`（`/**`） | `repeat_submit` 中间件 + Redis 5s | 仅 `SysConfigController.add` 使用 | 不要对全部 POST 生效，否则正常重复提交被拒 |
| `BaseController.startPage()` | `PageQuery` extractor + 显式 `count`/`limit` | 无 PageHelper 线程变量 | `orderByColumn` 必须过 `SqlUtil` 等价白名单 |
| `AjaxResult extends HashMap` | 自定义 `AjaxResult` 序列化器 | 字段顺序由 HashMap 桶序决定，不是插入序 | 实测错误为 `msg,code`；登录为 `msg,code,token`；不能统一成 `code,msg` |
| `TableDataInfo` | `#[derive(Serialize)] struct TableDataInfo { total, rows, code, msg }` | 字段声明顺序即输出顺序 | 顺序必须是 `total,rows,code,msg` |
| `R<T>` | `struct R<T> { code, msg, data }` | 仅 `/test/**` 使用 | 不要和 `AjaxResult` 混用 |
| 默认 404 `/error` | `Router::fallback(not_found)` | Java 实测 body 为 `timestamp,status,error,path` | 若前端依赖该结构，Rust 需自定义；否则可用 Axum 默认 |
| 静态资源 `/profile/**` | `tower_http::services::ServeDir` | 路径映射到 `ruoyi.profile` | 目录穿越防护、隐藏文件规则需对齐 |
| 文件上传 40MB / 请求 200MB | `DefaultBodyLimit::max(200MB)` + 单文件校验 | Axum 默认 2MB | 不加 `DefaultBodyLimit` 会直接 413 |
| 未登录访问不存在路径 | 认证中间件先于路由 | Java 实测返回 401（不是 404） | Axum 默认先匹配路由再跑中间件；需用全局 `middleware::from_fn` 而非路由级 |
| `@Validated @RequestBody` | `validator` crate + 手动 `validate()` | 无 AOP；校验失败需显式转错误 | `SysUser` 校验在 Java 中**被注释**，Rust 禁止补校验；`SysConfig` 校验生效 |

**本维度结论**：Web 层最大的三个坑是**中间件顺序**、**错误/404 的 200 语义**、**封套字段顺序**。这三项都已有实测样本（附录 E），阶段三直接作为黄金用例。

---

## 4. ORM / 数据访问

> 75 个 Mapper XML、481 条 SQL、78 张表的逐条映射见附录 C。

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| MyBatis-Plus `BaseMapper<T>`（43 个） | `src/modules/**/repository.rs` 中的显式函数 | 无通用 CRUD 继承；每个方法手写 SQL | 以为 `insert/updateById/selectById` 免费；需按表生成 |
| `@TableName("car_info")` | `const TABLE: &str = "car_info"` 或 SQL 字面量 | 无注解扫描 | 表名拼错只在运行时报错 |
| `@TableId(value="big_id", type=IdType.INPUT)` | `big_id: String`，由调用方赋值 | `INPUT` 不生成 ID | 误用 `ASSIGN_ID` 会覆盖上游 ID |
| `IdType.ASSIGN_ID` | 雪花函数 `snowflake::next_id()` | Java 内置雪花 epoch/位宽需复刻 | 用不同 epoch 会与 Java 生成的 ID 冲突 |
| `@TableField(exist=false) private String id;` | `#[serde(skip)] id: Option<String>`（不参与 SQL） | 仅传输字段 | 误加入 INSERT/UPDATE 列会报未知列 |
| Mapper XML `#{}` | `?` 绑定（MySQL） | SQLx MySQL 使用 `?`，不是 `$1` | 从 PostgreSQL 示例照抄会全部报错 |
| `<if test="...">` | `QueryBuilder::push` + 条件 | 无 OGNL | `test="name != null and name != ''"` 需手写为 `if let Some` |
| `<foreach collection="ids">` | `QueryBuilder::push_values` / `separated` | 无集合表达式 | 空集合时 Java 生成 `IN ()` 还是跳过，需逐条确认 |
| `<where>` / `<set>` / `<trim>` | `QueryBuilder` 的 `push(" WHERE ")` + `separated(" AND ")` | 需手写前缀/后缀裁剪 | 多条件全空时可能生成 `WHERE` 悬挂 |
| `<sql>` / `<include>` | `const SQL_FRAGMENT: &str` | 编译期拼接 | 片段中的别名/表名需随上下文变化 |
| `resultMap` / `association` / `collection` | `FromRow` + 二次查询 + 分组 | 无嵌套映射 | 直接 `JOIN` 会改变行数/分页 total |
| `${tableName}` / `${column}` | 白名单/正则校验后拼接 | SQLx 不能绑定标识符 | 直接 `format!` 即 SQL 注入；附录 C 已列出所有动态表名 |
| PageHelper `startPage()`（100 处） | 显式 `SELECT COUNT(*)` + `LIMIT ? OFFSET ?` | 无隐式拦截器 | `reasonable=true` 会把页码纠正到合法范围；`pageSize=0` 行为需复刻 |
| `PageInfo.getTotal()` | count 查询结果 | 跨月查询的 total 是近似值 | 不要“修正”近似 COUNT |
| `@Transactional`（159 处） | `let mut tx = pool.begin().await?; ... tx.commit().await?` | Spring 只对 `RuntimeException` 回滚；Rust 所有 `Err` 都应回滚 | 自调用不生效：同类内部方法调用不会开新事务，Rust 需按实际边界包裹 |
| `@DataSource` / 从库 | 单 `MySqlPool` | 从库未启用 | 不要引入读写分离 |
| `ASSIGN_ID` + 分表雪花 | `src/common/snowflake.rs` | epoch `1672531200000`、shift `22`（分表服务另有实现） | 两套雪花用途不同，不能合并 |
| ShardingSphere 逻辑表（用户决策启用） | `src/infra/sharding.rs` 路由 | 无 JDBC 代理；路由发生在 repository 层 | `ods_rt_szdn_snapshot_flow` 按月、`ods_lwzxsfsj_fee_records` 按日；无分片键时广播 |
| 跨月手工查询（`SnapshotFlowEnhancedService`） | 逐表 count/limit + 内存归并 | 历史月用 `TABLE_ROWS` 近似，当前月精确 | 排序稳定性、边界月份、`total` 不精确 |
| `LIMIT #{offset}, #{size}` | `LIMIT ? OFFSET ?` | 参数顺序不同 | 写成 `LIMIT ?, ?` 语义是 `offset,size`，易错 |
| `CREATE TABLE IF NOT EXISTS ... LIKE ...` | 原样 DDL | MySQL DDL 隐式提交 | 不能放在事务里期待回滚 |
| `INFORMATION_SCHEMA.TABLES.TABLE_ROWS` | 原样 SQL | 近似行数 | 分页 total 可能跳变 |
| `useSSL=true` / `zeroDateTimeBehavior=convertToNull` | `ssl-mode=PREFERRED`；`Option<NaiveDateTime>` | 驱动行为不同 | 0000-00-00 必须映射为 `None` |
| `allowMultiQueries=true` | 拆分多条语句 | SQLx 默认不支持多语句 | 审计是否有依赖多语句的 Mapper |
| 本地 DDL 快照（84 表） | `migrations/` 只读快照 | 缺 7 张生产表 | 不要用快照创建生产库 |

**本维度结论**：数据层是迁移量最大、最不能“优化”的部分。阶段三按附录 C 的 481 条语句逐条产出 `repository` 函数，并保留 PageHelper/近似 COUNT/动态表名的原始语义。

---

## 5. 中间件

> 详细配置与 key/TTL 见附录 D2–D8。

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| Lettuce + `RedisTemplate` | `redis::aio::ConnectionManager` | 无 Spring 序列化器抽象 | 每个 key 的 value 格式必须逐字节一致 |
| `FastJson2JsonRedisSerializer` + `WriteClassName` | 自定义 `RedisCodec`，写入 `@type` | serde 默认无类型信息 | 不加 `@type`，灰度期间 Java 反序列化失败 |
| `AUTO_TYPE_FILTER` + 白名单 | 反序列化时识别 `@type` 并映射到 Rust 枚举 | Rust 无任意类加载 | 只支持白名单内的类型，未知类型报错 |
| `login_tokens:{token}` | 同 key，TTL 120 分钟 | 续期阈值 ≤20 分钟 | TTL 单位/刷新时机必须一致 |
| `captcha_codes:*` / `pwd_err_cnt:*` / `repeat_submit:*` | 同 key/TTL | 一次性删除时机 | 验证码校验失败是否删除需与 Java 一致 |
| spring-kafka `@KafkaListener` 批量 | rust-rdkafka `StreamConsumer` + 手动 commit | 无容器并发/ack 模式 | 整批成功才 commit；异常不 commit |
| `MANUAL_IMMEDIATE` + `acknowledge()` | `consumer.commit_message(msg, CommitMode::Async/Sync)` | 提交粒度不同 | 单条失败重试 3 次后进 DLQ，再提交 |
| DLQ topic `ods-rt-szdn-snapshot-flow-dlq` | 同 topic，JSON 消息体 | key 为空、value 为字符串 | 消息体字段顺序/时间格式需一致 |
| `CdcSyncService` 手动 ack | 所有分支都 commit | ES 写入被注释 | 不要“顺手”恢复 ES 写入 |
| RestHighLevelClient 7.15.2 | `elasticsearch` crate 或 `reqwest` | DSL 原样 | 索引 `snapshot-flow`、`_id=bigId`、`snapshottime desc` |
| Quartz RAM JobStore | tokio 定时器 + `sys_job` 注册表 | 无 Quartz API | 启动时 `clear` 再按表重建；未知 `invoke_target` 记错跳过 |
| `@Scheduled` 6 个方法（用户决策启用） | `tokio-cron-scheduler` 或 `cron` + interval | Spring cron 6 段含 `?`；Rust cron 需把 `?`→`*` | 时区必须是 GMT+8；`0 0 1 1 * ?` 是每月 1 日 01:00 |
| `OssTemplate` / AWS S3 | `aws-sdk-s3` | path-style/MinIO 兼容 | `/oss/**` 默认不注册；`oss.info=true` 才注册 |
| 阿里云 Dysmsapi | `reqwest` + ACS3 签名 | 签名算法易错 | 模板全空时行为需保持 |
| Forest 1.6.0 | `reqwest::Client` + 超时/重试 | 无注解式接口 | 超时 60s、重试 2 次 |
| kaptcha | `captcha` crate | 像素不一致 | 只保证算式/字符、2 分钟、一次性 |
| POI / EasyPOI | `rust_xlsxwriter` / `calamine` | 样式/公式支持有限 | 模板文件逐单元格对比 |
| Velocity 2.3 | 自研子集 `src/service/velocity.rs`（未引第三方模板引擎） | 仅覆盖 vm 模板用到的指令/表达式 | 逐模板与 Java 产物字节对拍（`tools/endpoint_parity/gen_preview_diff.py`、`gen_zip_diff.py`） |
| OSHI | `sysinfo` | 字段名/单位不同 | 监控页数值口径需对齐 |
| UserAgentUtils | `user-agent-parser` | 浏览器/OS 名称映射 | 登录日志的 browser/os 字段需一致 |
| 本地文件 `/profile/**` | `ServeDir` | 路径拼接 | 目录穿越与 URL 编码 |

**本维度结论**：中间件迁移的验收标准是**跨语言互操作**：Redis 值能被 Java 读、Kafka 消息能被 Java 消费、ES 文档字段一致。阶段四需做双向验证。

---

## 6. 配置

> 约 100 项逐项映射见附录 D8。

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| `application.yml` / `application-druid.yml` | `config/application.yaml` / `config/application-druid.yaml` | 文件可保留原结构 | YAML 缩进错误会导致启动失败 |
| `@Value("${server.port}")` | `Config::get::<u16>("server.port")` | 启动期读取，失败即退出 | 不要在请求期反复读配置 |
| `@ConfigurationProperties(prefix="token")` | `#[derive(Deserialize)] struct TokenConfig` | 无松散绑定 | `expireTime` 与 `expire-time` 需 `serde(alias)` |
| `spring.profiles.active` | `APP_PROFILE` + `application-{profile}.yaml` | 加载顺序需显式 | 默认 profile 缺失时行为 |
| 环境变量（Spring relaxed binding） | `APP_` + `__`，如 `APP_SERVER__PORT` | 大小写/分隔符规则不同 | `-`→`_`、`.`→`__` 的转换要统一 |
| 优先级：命令行 > 环境变量 > profile > 默认 | `config-rs` 的 builder 顺序 | 需显式 `.add_source` 顺序 | 顺序写反会导致环境变量被 YAML 覆盖 |
| `server.port=9989` | 同值 | 必须一致 | 改成 8080 会导致前端/探针失效 |
| `token.secret` 默认 `abcdefghijklmnopqrstuvwxyz` | 同默认值，部署覆盖 | jjwt 的 Base64 处理怪癖 | 不能直接用 secret 字节签名 |
| `token.expireTime=120` | 120 分钟 | 续期阈值 20 分钟 | 单位是分钟，不是秒 |
| Druid 池 5/10/200/60s | `max_connections=200`、`acquire_timeout=60s` | 无 initial/minIdle 概念 | 启动预热连接需显式 |
| Redis `127.0.0.1:6379/0` | 同 | 无 password 时不要传空串 | 连接串格式 |
| Kafka `127.0.0.1:9092` | 同 | rdkafka 配置项名不同 | `enable.auto.commit=false` 必须显式 |
| ES `127.0.0.1:9200` / `snapshot-flow` | 同 | 无 | 索引不存在时的降级 |
| `oss.enable=true` / `oss.info=false` | 同默认值 | 端点注册开关 | 默认不能注册 `/oss/**` |
| `monitor.slow-request-threshold=3000` 等 | 同 | 单位毫秒 | 慢 SQL 阈值 1000ms |
| `xss.enabled=true` / 排除 `/system/notice` | 同 | 规则逐字符 | 不能清洗 multipart |
| `upload.max-file-size=40MB` / `max-request-size=200MB` | 同 | Axum 默认 2MB | 必须设置 `DefaultBodyLimit` |
| `log.dir` / 滚动 100MB/60 天 | `tracing-appender` + 文件轮转 | 无 Logback 表达式 | 路径/文件名规则 |
| `snapshot.flow.sharding.*`（Java 死配置） | 同键保留，供手工分表读取 | 用户决策启用路由 | 不要删除，部署脚本可能引用 |
| `sharding.enabled`（Java 无） | 新增，默认 true | 用户决策 | 关闭时退化为直接访问同名表 |

**本维度结论**：配置层要做到“同名、同默认值、同优先级”。新增项只有 `sharding.enabled`、`app.health_endpoint_enabled`、`APP_PROFILE` 三个，需在 README 标注。

---

## 7. 日志与可观测性

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| SLF4J `LoggerFactory.getLogger` | `tracing::info!` / `#[instrument]` | 无 logger 层级对象 | 每条日志都要带 target/字段 |
| Logback `logback.xml` | `tracing-subscriber` + `EnvFilter` | 配置语法不同 | 包名过滤规则需映射 |
| MDC `put("traceId", ...)` | `tracing::span!(Level::INFO, "request", trace_id=%id)` | 无 MDC | 跨 task 需显式传播 span |
| `TraceIdFilter` | tower 中间件 + `X-Trace-Id` 响应头 | 生成/透传规则 | 必须回写响应头 |
| `LogAspect`（239 处 `@Log`） | 路由元数据 `operation_log` + 中间件 | 无 AOP | `oper_param`/`json_result` 截断 2000 字符 |
| 登录日志 `sys_logininfor` | 异步 task 落库 | 10ms 延迟 | 不能阻塞登录响应 |
| 操作日志 `sys_oper_log` | 异步 task 落库 | IP/地点/浏览器/OS 规则 | 失败不能影响主流程 |
| `SqlLogInterceptor` / P6Spy | SQLx `tracing` + 计时 | 慢 SQL 阈值 1000ms | 日志中不能泄露密码 |
| `MetricCollector` / `AlertEngine` | 内存指标结构 + 定时上报 | 无 Micrometer | 指标名/标签需一致 |
| 慢请求 3000ms / 慢方法 500ms | 中间件计时 + WARN | 单位毫秒 | 阈值从配置读 |
| 日志滚动 100MB/60 天 | `tracing-appender` 按天/大小 | 无内置 60 天清理 | 需额外清理任务 |
| 控制台启动 banner | `tracing::info!` 启动摘要 | 无 Spring banner | 不要输出敏感配置 |

**本维度结论**：可观测性不是“能打日志”即可，`traceId`、操作日志字段、慢阈值三项是对外可观察行为，需按附录 D 逐项对齐。

---

## 8. 序列化

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| Jackson `ObjectMapper` | `serde_json` | 无运行时反射 | 字段名默认就是 Rust 字段名，需 `rename` |
| `@JsonProperty("x")` | `#[serde(rename="x")]` | 编译期生成 | 漏标导致前端字段缺失 |
| `@JsonIgnore` | `#[serde(skip)]` | 反序列化也跳过 | 只 skip 序列化需 `skip_serializing` |
| `@JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")`（96 处） | `serialize_with` / `deserialize_with` | 无全局模块自动生效 | 每个字段都要标；漏一个就是时间戳 |
| `@JsonInclude(NON_EMPTY)` | `#[serde(skip_serializing_if="Option::is_none")]` + 空串/空集合判断 | NON_EMPTY 还省略空串/空集合 | 只判 `None` 会多输出 `""`/`[]` |
| `@JsonInclude(NON_NULL)` | `skip_serializing_if = "Option::is_none"` | 语义接近 | `Some("")` 仍会输出 |
| `SysFile.id` 的 `ToStringSerializer` | `serialize_with = "to_string"` | Java 把 Long 输出为字符串 | 漏标会让前端丢精度 |
| `Sensitive` + `SensitiveJsonSerializer` | 自定义 `serialize_with` + 脱敏策略 | 注解在字段上 | 脱敏规则（手机/身份证/银行卡）需逐条 |
| `AjaxResult extends HashMap` | 自定义 `Serialize` 固定顺序 | HashMap 桶序 | 不能按字母序/插入序猜 |
| `TableDataInfo` 字段顺序 | struct 字段声明顺序 | serde 按声明序 | 顺序错会导致快照测试失败 |
| `Date` 默认序列化 | epoch 毫秒（与 Java 一致）或指定格式 | 需逐字段确认 | Rust 默认 RFC3339 是错的 |
| `BigDecimal` | `Decimal` + `serde-with-float` 或字符串 | Jackson 默认数字 | 用字符串会改变前端类型 |
| Java enum `name()` | `#[serde(rename="VALUE")]` | 默认 Rust 变体名 | 大小写/下划线需逐项 |
| `null` 字段 | `Option` + 按注解省略 | Jackson 默认输出 `null` | 不要全局 `skip_none` |
| FastJson2 `WriteClassName` | 自定义 Redis 序列化器 | `@type` 字段 | 只影响 Redis，不影响 HTTP |
| `JSON.toJSONString` 日期格式 | FastJson2 默认 `yyyy-MM-dd HH:mm:ss` | 与 Jackson 可能不同 | Redis 中的值要与 Java 完全一致 |
| `@JsonFormat(timezone=...)` | `chrono-tz` 转换 | 时区偏移 | 统一 GMT+8 |
| `Long` 精度 | 数字（保持 Java 行为） | JS 可能丢精度 | 不要“好心”改字符串 |

**本维度结论**：序列化是“看不见但最容易回归”的维度。阶段三为每个 Domain 生成 JSON 黄金样本（Java 输出 vs Rust 输出），逐字段 diff。

---

## 9. 依赖注入

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| Spring IoC 容器 | `bootstrap::build_app()` 组合根 | 编译期显式构造 | 循环依赖在 Rust 中会变成构造死循环/编译错误 |
| `@Autowired` 字段注入 | 构造函数参数 / `AppState` 字段 | 无反射注入 | 不要用全局 `static mut` 模拟容器 |
| `@Service` / `@Component` | 普通 struct + `impl` | 无扫描 | 忘记在 `AppState` 中注册 |
| `@Bean` | 工厂函数 | 生命周期显式 | 连接池需在 `main` 创建并共享 |
| `@ConfigurationProperties` | `Config` 结构体 | 启动期反序列化 | 未知字段默认忽略，需 `deny_unknown_fields`？按 Java 行为决定 |
| `@ConditionalOnProperty` | `if config.x { ... }` | 编译期分支/运行时分支 | OSS/health/sharding 三个开关 |
| `@Primary DataSource` | 单一 `MySqlPool` + `ShardingRouter` | 无多数据源代理 | 从库关闭，不要引入读写分离 |
| `SpringUtils.getBean(...)` | `State<AppState>` / 显式传参 | 无全局容器 | 禁止全局可变单例 |
| `SecurityUtils.getLoginUser()` | `Extension<CurrentUser>` | 无 ThreadLocal | 在 service 层不要直接取请求上下文；由 handler 传入 |
| `@PostConstruct` | `bootstrap` 启动序列 | 失败即退出（与 Java 一致） | 缓存预热失败是否阻止启动需保持 |
| `@Scope("prototype")` | 每次 `new` | 无作用域概念 | 有状态 Bean 不能放进 `AppState` |
| AOP `@Log` / `@DataScope` / `@RepeatSubmit` | 中间件 / 服务层显式条件 | 无代理 | 自调用不会触发，Rust 需显式调用 |
| `ApplicationEventPublisher` | `tokio::sync::broadcast` / 显式调用 | 无事件总线 | 事件顺序/失败处理 |

**本维度结论**：Rust 的依赖注入是“显式优于隐式”。`AppState` 是唯一共享入口，禁止 `lazy_static` 可变全局。

---

## 10. 测试

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| JUnit 5 `@Test` | `#[test]` / `#[tokio::test]` | 无测试类生命周期 | 异步测试必须用 tokio 宏 |
| Mockito | `mockall` 或手写 fake trait | 无运行时 mock | 过度 mock 会掩盖 SQL 语义 |
| AssertJ | `assert_eq!` + `pretty_assertions` | 无流式断言 | 失败信息需包含上下文 |
| `@SpringBootTest` | `#[tokio::test]` + testcontainers | 启动整个 app 成本高 | 集成测试需真实 MySQL/Redis |
| 现有测试 0 个 | 先补“特征测试” | 无历史测试可依赖 | 以附录 E 的实测响应为黄金样本 |
| 分页测试 | 同一数据集逐页对比 | PageHelper 行为复杂 | `reasonable`、`pageSize=0`、空结果 |
| SQL 测试 | 逐条语句对拍 | 动态 SQL 组合多 | `<if>/<foreach>` 全分支 |
| Redis 兼容测试 | Java 写 → Rust 读；Rust 写 → Java 读 | `@type` | 灰度共存必测 |
| JWT 测试 | 固定 token 双向校验 | jjwt secret 怪癖 | 存量 token 不能失效 |
| Kafka 测试 | 内嵌/容器 | 手动 ack/DLQ | 异常不提交、重试 3 次 |
| ES 测试 | 容器或 mock REST | DSL 字段 | 分页/排序 |
| Excel 测试 | 生成物解包对比 | 样式/合并 | 模板逐单元格 |
| 代码生成测试 | 生成目录快照 | 模板差异 | 换行/缩进 |
| 性能/并发测试 | `tokio::test` + 多任务 | 无线程池模型 | 连接池耗尽 |

**本维度结论**：项目原本 0 测试，阶段三/四必须“边迁移边补特征测试”，否则无法证明 1:1。

---

## 11. 构建与部署

| Java 用法 | Rust 对应写法 | 关键差异 | Java 开发者最容易踩的坑 |
|---|---|---|---|
| Maven 多模块 | Cargo（单 crate 或 workspace） | 无 `pom.xml` | 模块边界用 `mod`/crate 显式声明 |
| `mvn package` fat jar | `cargo build --release` 单二进制 | 无 JVM | 体积/启动时间不同 |
| `resources/` 打包 | `include_str!` / `include_bytes!` / `resources/` 目录 | 运行时路径 | 模板/静态资源需随二进制或部署目录 |
| `java -jar ruoyi-admin.jar` | `./car-monit-rust --config config/application.yaml` | 无 `-D` 系统属性 | 参数解析用 `clap` |
| 环境变量 | `APP_` + `__` | 命名规则 | 部署脚本需同步 |
| `server.port=9989` | 同 | — | 健康检查 `/health` 新增 |
| Spring Actuator（无） | `/health`（新增，开关） | Java 无 | 监控系统需知晓 |
| Logback 文件 | stdout + 文件 | 容器日志采集 | 双写需配置 |
| WAR 部署 | 单二进制 / Docker | 无 Servlet 容器 | `RuoYiServletInitializer` 不迁移 |
| 优雅停机 | `with_graceful_shutdown` | 无 Spring 生命周期 | 先停 HTTP 再停消费者 |
| 时区 | `TZ=Asia/Shanghai` | JVM 默认时区 | 容器默认 UTC 会偏移 8 小时 |
| 字符集 | UTF-8 | — | 文件/DB 连接 |
| Docker | `Dockerfile`（debian-slim + 二进制） | — | CA 证书/librdkafka 依赖 |
| systemd | unit 文件 | — | 重启策略/环境变量 |
| 健康检查 | `GET /health` | Java 无 | 返回 200 + 简单 JSON |
| 迁移脚本 | `migrations/` 只读 | 不自动执行 | 生产 DDL 仍需人工核对 |
| CI | `cargo fmt --check`、`clippy -D warnings`、`cargo test` | — | 无 Java 构建链 |

**本维度结论**：部署形态为“单二进制 + 可选 Docker”，端口 9989，时区 GMT+8，`/health` 为唯一新增端点。

---

## 12. 项目专属映射索引（必须逐条覆盖）

| 项目机制 | 数量 | Rust 落点 | 验收 |
|---|---:|---|---|
| HTTP 端点 | 501 | `src/api/**` | 附录 B 逐条路由 + 权限 |
| Java 文件 | 696 | 附录 A 目标文件 | 文件存在且职责对应 |
| Mapper XML / SQL | 75 / 481 | `src/api/<slice>/*.rs`（控制器内联）+ `src/repository/*.rs` | SQL 对拍 |
| 表/视图 | 78 | `src/domain/**` + 控制器 SQL / `src/db/rows.rs` 动态映射 | CRUD/查询覆盖 |
| `@Transactional` | 159 | `sqlx::Transaction` | 回滚边界矩阵 |
| `@PreAuthorize` | 284 | `src/api/meta.rs` 路由元数据 | 权限守卫测试 |
| `@Log` | 239 | `src/api/meta.rs` + `src/auth/audit.rs` | `sys_oper_log` 字段一致 |
| `startPage()` | 100 | `src/common/page.rs` + 显式分页 | 逐页对比 |
| `@JsonFormat` | 96 | `src/common/serde_helpers.rs`、`src/db/rows.rs` | JSON 快照 |
| `BaseEntity` 子类 | 大量 | `#[serde(flatten)]` / 控制器查询结构体 | 字段扁平 |
| `AjaxResult` / `TableDataInfo` / `R` | 383 / 100 / 5 | `src/response.rs` | 字段顺序 |
| 双 advice | 1 组 | 仅 `GlobalExceptionHandler` 模型 | 附录 E |
| `@Scheduled` | 6 | `src/task/mod.rs` | cron 触发 |
| `sys_job` | 19（本地） | `src/api/quartz/registry.rs`（`invoke_target` 注册表） | 任务行为 |
| Redis key | 见 D2 | `src/db/redis_cache.rs` + 控制器内缓存逻辑 | key/TTL/值格式 |
| Kafka 监听器 | 2 | `src/task/kafka.rs`（可选 feature，未接线） | ack/DLQ |
| 死代码类 | 8 | 附录 A | public 方法存在 |

---

## 13. 阶段二验收清单

- [x] 11 个维度均有四列表格。
- [x] 501 条端点有 Rust handler 计划（附录 B）。
- [x] 78 张表有数据访问映射（附录 C）。
- [x] 159 处事务有边界说明。
- [x] 双 advice 已实测并固定（附录 E）。
- [x] 用户决策已记录（0.2）。
- [ ] 阶段三：按附录 A 逐文件移植，代码内嵌 Java↔Rust 注释。
- [ ] 阶段四：编译、测试、README-MIGRATION、自检。

> 下一步进入阶段三：先搭 `Cargo.toml` + `main.rs` + 配置/错误/响应封套，再按切片移植 Controller → Service → Repository。

---

## 移植完成度（收尾）

| 切片 | 控制器 | 状态 | 落点 |
|---|---|---|---|
| base | 25 | 完成 | `src/api/base/*.rs`（含分表增强查询、HenDa、CDC） |
| system | 14 | 完成 | `src/api/system/*.rs`（含字典缓存、Dept sub_code/tenant 维护） |
| manager | 19 | 完成 | `src/api/manager/*.rs`（12 张表共享 `manager_crud!` 宏） |
| flow | 7 | 完成 | `src/api/flow/*.rs`（审批引擎 saveFlowAuit/submitReturn/submitEntrustFlow） |
| monitor | 5 | 完成 | `src/api/monitor/*.rs`（sysinfo / Redis INFO / login_tokens 扫描） |
| quartz | 2 + 调度器 | 完成 | `src/api/quartz/*.rs`、`src/service/quartz_runtime.rs` |
| common | 2 | 完成 | `src/api/common/*.rs`（下载/上传/模板下载） |
| tool | 1 | 完成 | `src/api/tool/test.rs` |
| generator | 1 | 完成 | `src/api/generator/{gen,gen_render,gen_zip}.rs` + `src/service/velocity.rs`（preview/download/genCode/batchGenCode 已与 Java 一致） |
| 死代码 6 类 | — | 完成 | `src/service/legacy_sharding.rs` |

已用 `route_parity` 单测按附录 B 的 501 条端点逐条对拍（method + 路径形状），全部注册成功。

已接线：`sys_job` 的 `vehicleMonitoringTask` 全量基础信息同步、`trackTask` 实时/历史轨迹与逃费回写/可疑车迁移（远端 baseInfo 走 `vehicleMonitor.baseUrl`，轨迹读 Redis 缓存）。

仍未接入：Kafka/ES（Java 侧 ES 写入被注释、Kafka 消费无业务效果）、OSS（Rust 用本地存储等价实现）、代码生成里的关联表回查（`field_map_string`/`link_table_id`）。详见 README-MIGRATION §6。
