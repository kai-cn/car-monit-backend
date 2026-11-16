# README-MIGRATION：RuoYi car-monit 后端 Java → Rust

本目录是 `car-monit-backend-new`（Java 3.8.7 / Spring Boot 2.5.15 / MyBatis-Plus / MySQL 8 / Redis / ShardingSphere 5.2.1）
的 1:1 Rust 重写。目标不是“重新设计”，而是**用 Rust 逐文件重写同一个服务**：API 路径、method、请求/响应结构、
状态码、错误码、SQL 语义、事务边界、Redis key/TTL 全部对齐。

- 基线清单：`docs/01-MIGRATION-BASELINE.md`、`docs/01-baseline/*.md`
- Java ↔ Rust 全量映射：`docs/02-JAVA-RUST-MAPPING.md`
- 切片移植约定（维护者用）：`tools/porting-briefing.md`
- Java↔Rust GET 全量校验结论：`docs/03-INTERFACE-VERIFICATION.md`（297 条：160 OK / 109 仅顺序或错误文案 / 13 聚合类待补 / 12 环境受限）

---

## 1. 从零启动

### 1.1 前置组件

| 组件 | 版本 | 说明 |
|---|---|---|
| Rust | 1.90（见 `rust-toolchain.toml`） | `rustup default 1.90` |
| MySQL | 8.x | 与 Java 同一实例/库（默认 `carmonitdb`，端口 3307） |
| Redis | 6+ | 与 Java 共用（单库 `database=0`） |
| GaussDB/Forest 上游 | 可选 | `vehicleMonitor.baseUrl`，仅分表同步任务使用 |

### 1.2 构建与运行

```bash
rustup show                 # 确认工具链
cargo build --release
cargo run                   # 读取 config/application.yaml
```

- 默认监听 `9989`（与 Java `server.port` 一致）。
- 日志同时写 stdout 与 `log.dir` 下的按天滚动文件。
- 环境变量前缀 `APP_`、层级用 `__`，例如 `APP_DATABASE__PASSWORD=xxx`。
- 默认 feature：`excel`（导入/导出）与 `sysinfo`（服务器监控）；`kafka`/`oss`/`templates` 为可选 feature，当前未接线。

### 1.3 验证

```bash
cargo test                  # 单元测试（分页、JWT、cron、分片、视图 SQL 等）
curl -s localhost:9989/captchaImage
```

---

## 2. Java 配置 → Rust 配置对照

`config/application.yaml` 保留 Java 的键名与默认值；Rust 额外读取少量 Java 没有的开关（标注 rust-only）。

| Java（application.yml / application-druid.yml） | Rust 键 | 默认值 | 备注 |
|---|---|---|---|
| `server.port` | `server.port` | 9989 | |
| `ruoyi.name/version` | `ruoyi.name/version` | RuoYi / 3.8.7 | |
| `ruoyi.profile` | `ruoyi.profile` | `D:/ruoyi/uploadPath` | 上传/下载根目录 |
| `ruoyi.addressEnabled` | `ruoyi.addressEnabled` | false | 登录 IP 归属地查询 |
| `ruoyi.captchaType` | `ruoyi.captchaType` | math | |
| `user.password.maxRetryCount` | `user.password.maxRetryCount` | 5 | |
| `user.password.lockTime` | `user.password.lockTime` | 10（分钟） | |
| `token.header` | `token.header` | Authorization | |
| `token.secret` | `token.secret` | 由 `APP_TOKEN__SECRET` 注入 | HS512；按 jjwt 0.9.1 的 base64 怪癖复刻 |
| `token.expireTime` | `token.expireTime` | 120（分钟） | ≤20 分钟自动续期 |
| `spring.datasource.druid.url` | `database.url` | jdbc:mysql://127.0.0.1:3307/carmonitdb… | 仅用于解析 host/port/db |
| `spring.datasource.druid.username/password` | `database.username/password` | root/root | |
| `spring.datasource.druid.initialSize/minIdle/maxActive/maxWait` | `database.pool.*` | 5/10/200/60000 | |
| `spring.redis.host/port/database/password/timeout` | `redis.*` | 127.0.0.1/6379/0/""/10s | |
| `spring.kafka.*` | `kafka.*` | 见文件 | 消费者/生产者语义 |
| `cdc.*`（CdcService） | `cdc.*` | 见文件 | ES 同步开关 |
| `elasticsearch.*` | `elasticsearch.*` | 127.0.0.1:9200 | |
| `oss.*` | `oss.*` | enable=true, info=false | 可选 feature |
| `sms.*` | `sms.*` | 空 | 可选 |
| `forest.max-connections/connect-timeout/read-timeout/retry-count` | `forest.*` | 500/60000/60000/2 | reqwest 连接池映射 |
| `vehicleMonitor.baseUrl` | `vehicleMonitor.baseUrl` | http://127.0.0.1:9901 | Forest `@BaseRequest` |
| `monitor.*` | `monitor.*` | 见文件 | 慢请求/慢 SQL 阈值 |
| `xss.enabled/urlPatterns/excludes` | `xss.*` | true | |
| `spring.servlet.multipart.max-file-size/max-request-size` | `upload.*` | 40MB/200MB | |
| `logging.file.path` / `logback.xml` | `log.dir/max-history/max-file-size` | /home/ruoyi/logs | tracing-appender |
| — | `snapshot.flow.sharding.*`（rust-only） | 前缀/策略 | 替代 ShardingSphere 逻辑表 |
| — | `sharding.enabled`（rust-only） | true | |
| — | `app.scheduled_annotations_enabled`（rust-only） | true | 用决策：6 个 @Scheduled 必须生效 |
| — | `app.banner_enabled` / `app.health_endpoint_enabled`（rust-only） | true | |

---

## 3. 依赖组件映射总表

| Java / Spring | Rust | 落点 |
|---|---|---|
| Spring Boot MVC / DispatcherServlet | Axum 0.8 | `src/lib.rs#build_router`、`src/api/**` |
| `@RestController` / `@GetMapping` | `Router::route` + `meta::get_route` | `src/api/<slice>/*.rs` |
| `@RequestBody` / `@PathVariable` / `@RequestParam` | `Json<T>` / `Path<T>` / `Query<T>` + `RawQuery` | 各 handler |
| `@ControllerAdvice` / `GlobalExceptionHandler` | `IntoResponse for AppError` | `src/error.rs` |
| Spring Security 过滤器链 | axum middleware | `src/middleware/auth.rs` |
| `@PreAuthorize("@ss.hasPermi")` | 路由元数据 + 统一中间件 | `src/api/meta.rs` |
| `@Log` + LogAspect + AsyncManager | 路由元数据 + `audit::record_oper`（10ms 延迟） | `src/api/meta.rs`、`src/auth/audit.rs` |
| jjwt 0.9.1 HS512 | jsonwebtoken 9（复刻 DatatypeConverter 解码） | `src/auth/jwt.rs` |
| Spring Data Redis / FastJson2 | redis-rs + serde（保留 `@type`） | `src/db/redis_cache.rs` |
| MyBatis-Plus / MyBatis XML | SQLx 0.8 + QueryBuilder（手写 SQL） | `src/api/**`、`src/repository/**` |
| PageHelper `startPage()` | `PageDomain` + count/limit 显式分页 | `src/common/page.rs`、`src/api/support.rs` |
| `@Transactional` | `sqlx::Transaction` | 控制器/service |
| ShardingSphere 5.2.1 | 仓储层按月路由 | `src/db/sharding.rs` |
| Quartz RAM + `sys_job` | `quartz_cron`（Quartz 语义 cron）+ `job_invoke`（`JobInvokeUtil` 复刻）+ `quartz_runtime`（注册表 + 触发循环 + 执行日志） | `src/service/quartz_cron.rs`、`src/service/job_invoke.rs`、`src/service/quartz_runtime.rs`、`src/api/quartz/*.rs` |
| Spring `@Scheduled`（Java 从未生效） | tokio 调度循环（用户决策：启用） | `src/task/mod.rs` |
| Forest HTTP 客户端 | reqwest（同一连接池参数） | `src/state.rs`、`src/task/remote.rs` |
| Jackson | serde / serde_json（preserve_order） | `src/domain/**`、`src/response.rs` |
| POI Excel 导出/导入 | rust_xlsxwriter + calamine | `src/common/excel.rs` |
| Logback | tracing + tracing-appender | `src/main.rs` |
| BCryptPasswordEncoder | bcrypt crate | `src/auth/password.rs` |
| Snowflake `IdWorker` | 自实现雪花 | `src/common/snowflake.rs` |
| JUnit 5 | `#[test]` / `cargo test` | 各模块 `#[cfg(test)]` |
| Kafka（spring-kafka） | rdkafka（`kafka` feature，未接线） | — |
| Elasticsearch RestHighLevelClient | reqwest JSON（CDC 同步，未接线） | — |
| 阿里云 OSS SDK / 短信 SDK | aws-sdk-s3 / HTTP（`oss` feature，未接线） | — |

---

## 4. Java 开发者最容易困惑的 10 个点

1. **所有权取代 GC**：赋值后原变量不可再用不是语法怪癖，而是编译期防双重释放。
   ```java
   List<String> a = new ArrayList<>(List.of("x"));
   List<String> b = a;            // 两个引用
   ```
   ```rust
   let a = vec!["x".to_string()];
   let b = a;                     // 移动；此后 a 不可用
   let c = b.clone();             // 需要两份才显式 clone
   ```

2. **null → Option<T>**：数据库可空列必须是 `Option<T>`。
   ```java
   String name = user.getNickName();
   if (name != null) { ... }
   ```
   ```rust
   if let Some(name) = user.nick_name.as_deref() { ... }
   ```

3. **异常 → Result + `?`**：没有 try/catch，错误沿 `Result<T, AppError>` 传播，最终由 `IntoResponse` 统一转成 AjaxResult。
   ```java
   try { return service.list(q); } catch (Exception e) { return AjaxResult.error(e.getMessage()); }
   ```
   ```rust
   let rows = sqlx::query("...").fetch_all(&state.db).await?; // ? 即向上传播
   ```

4. **运行时注解 → 显式元数据**：`@PreAuthorize` / `@Log` 不再是反射切面，而是注册在路由上的 `RouteMeta`，由中间件执行。
   ```java
   @PreAuthorize("@ss.hasPermi('system:user:list')") @GetMapping("/list")
   ```
   ```rust
   .route("/system/user/list", meta::get_route("/system/user/list", Some("system:user:list"), None, list))
   ```

5. **Spring DI → 组合根**：没有容器，`AppState` 在 `main` 中构造并注入；依赖错误在编译期暴露。
   ```java
   @Autowired private SysUserMapper mapper;
   ```
   ```rust
   pub async fn list(State(state): State<AppState>) { ... state.db ... }
   ```

6. **MyBatis 动态 SQL → QueryBuilder**：`<if>` 变成 Rust `if`，参数一律 `push_bind`。
   ```xml
   <if test="userName != null and userName != ''"> and u.user_name like concat('%',#{userName},'%')</if>
   ```
   ```rust
   if filter.user_name.as_deref().is_some_and(|v| !v.is_empty()) {
       qb.push(" and u.user_name like ").push_bind(format!("%{}%", v));
   }
   ```

7. **PageHelper → 两段 SQL**：Java 由插件改写 SQL；Rust 显式先 count、再 limit/offset，`reasonable` 语义在 `PageDomain::resolve`。
   ```java
   startPage(); List<SysUser> list = userService.selectUserList(user);
   ```
   ```rust
   let page = support::page_domain(&raw);
   let total: i64 = count_sql.fetch_one(&state.db).await?;
   let (offset, limit) = support::page_window(&page, total);
   ```

8. **`@Scheduled`/Quartz 反射 → 注册表**：`invoke_target` 字符串无法在 Rust 中反射调用，改为显式 match；未知 target 记错误并跳过（与 Java 反射失败一致）。

9. **Jackson 的字段顺序/日期格式**：`AjaxResult` 是 HashMap（Java 桶序），Rust 用 `IndexMap` 固定为实测顺序；日期统一 `yyyy-MM-dd HH:mm:ss`（与项目内 `@JsonFormat` 默认一致）。

10. **异步与线程池**：`new ThreadPoolExecutor(...)` → `tokio::spawn` + `Semaphore`（并发上限）；`AsyncManager`（延迟 10ms 落库）→ `tokio::spawn` + `sleep(10ms)`。不要用 `spawn_blocking` 包纯异步 SQL。

---

## 5. 自检清单

- [x] 认证/JWT（含 jjwt 0.9.1 secret 解码怪癖）、登录失败锁定、验证码
- [x] Redis 值格式（FastJson2 `@type`）与 Java 共存
- [x] AjaxResult / TableDataInfo / R 字段与顺序
- [x] 全局异常模型：除 404 外 HTTP 200
- [x] 分页/排序注入校验、分表路由、视图维护
- [x] 6 个 `@Scheduled` 任务 cron 解析与调度（用户决策：生效）
- [x] 501 条端点全部落地（九个切片）+ `route_parity` 自检按附录 B 逐条对拍通过
- [x] `sys_job` 调度循环接线（启动装载**全部**行、暂停的也能立即执行；增改/启停/删除同步 tokio 调度；`docs/03` §7 四张矩阵 0 不一致）
- [ ] Kafka 消费者 / ES 同步接线（可选 feature）
- [ ] OSS 对象存储 / SMS 短信（可选 feature）
- [x] 代码生成器的 Velocity 模板渲染（`src/service/velocity.rs` 自研子集 + 26 个 vm 模板内嵌；`gen_table` 全 53 张表的 preview/download 产物与 Java 逐字节一致）
- [x] 本地联调冒烟：MySQL 3307 + Redis 6379 启动服务，完成登录（验证码换取 token）、`/getInfo`、系统/基础/管理/流程/监控/定时任务/生成器 40+ 代表性端点读写验证
- [ ] 与 Java 的完整黄金样本对拍（需 GaussDB 联调环境）

### 5.1 冒烟联调中发现并修复的问题

| 问题 | 修复 |
|---|---|
| tower-http CORS：`allow_credentials=true` 不能与 `Allow-Headers/Methods: *` 共存，启动即 panic | 改为 `mirror_request()`（等价 Java 的反射通配） |
| FastJson2 Redis 缓存里 Long 写成 `6L`，serde 无法解析字典缓存 | `redis_cache` 读取前剥离整数字面量后缀 |
| `sys_menu.is_frame/is_cache` 在库里是 INT，实体是 String | `menu_repo` 显式转字符串 |
| 登录日志 `status` 写 `Success/Error` 超出 `char(1)` | 按 Java AsyncFactory 映射为 `0/1` |
| PageHelper 式 count 用 `QueryBuilder::sql()` 二次包装导致占位符重复（`near '?'`） | 同一个 QueryBuilder 一次性渲染 `select count(0) from (...) tmp_count`，参数只绑定一次 |
| 分表 `COUNT`/`TABLE_ROWS` 的 BIGINT/BIGINT UNSIGNED 类型随版本变化 | 统一 `CAST(... AS CHAR)` 后解析 |
| `@Log` 中间件读取请求体后把 body 置空，导致所有带 `@Log` 的 POST/PUT 返回 400 | 捕获后原样回填 `Body::from(bytes)` |

## 6. 已知偏差与欠账

| 项 | 说明 |
|---|---|
| 6 个 `@Scheduled` | Java 无 `@EnableScheduling` 从未执行；用户决策 Rust 启用，cron 与注解一致 |
| 分表同步 | Java `convertToEntityList` 恒空（空转）、INSERT 引用 19 个不存在的列；用户决策任务必须生效，Rust 做真实同步，并修正月末分区漏月问题 |
| 视图维护 | Java `executeDDL` 是空操作；Rust 真正执行 `CREATE OR REPLACE VIEW` |
| 死代码类 | 8 个类照样迁移：`ShardingConfig`/`ShardingTableTask` 在 `db::sharding`、`task::sharding_table`；`PartitionMappingCache`、`PartitionParallelQueryService`、`ShardingQueryService`、`ShardingSyncService`、`DataConsistencyService`、`ViewMaintenanceOptimizationService` 在 `service::legacy_sharding`（无路由引用，与 Java 一致） |
| Kafka/ES | Java 中 `CdcSyncService` 对 ES 的写入全部被注释，Kafka 消费实际只记日志；Rust 保留 `/base/cdc/*` 队列管理端点（Redis 重试/死信），不启动消费者。`kafka` feature 只声明依赖、没有接线代码，且实测在 Windows 上编不过（rdkafka-sys 的 build.rs 报“%1 不是有效的 Win32 应用程序”） |
| OSS/SMS | Java `SysFileServiceImpl` 走 S3（OssTemplate）；Rust 用 `ruoyi.profile/upload` 本地落盘并保持相同响应结构；`AliyunSMSUtil` 在 Java 中无调用方，未迁移。`oss` feature 仍是只声明依赖的占位（S3 调用用 reqwest + SigV4 自己写，不依赖它）。**本轮补上基线漏掉的控制器**：`ruoyi-common/.../OssEndpoint.java`（`@RequestMapping("/oss")`，9 条）不在 501 条清单里，Rust 原先整块缺失 —— 由 `pathvar_matrix.py` 探出、`controller_coverage.py` 确认「全仓库只漏这一个控制器」。补成 `src/service/oss_client.rs`（path-style、`us-east-1`、`SignedHeaders=host;x-amz-content-sha256;x-amz-date`，预签名走离线 SigV4）+ `src/api/oss.rs`；真实 MinIO（`172.30.100.102:9002`）不在网内，改用 `tools/endpoint_parity/fake_s3_full.py` 顶上游，把 `Bucket`/`S3ObjectSummary` 键序、`Date` 的 Jackson 写法、预签名参数顺序、`POST /oss/object/**` 必回 `{"msg":null,"code":500}`、`DELETE /oss/bucket/{n}` 的 202 全部**实测**对齐（细节与残余的尾斜杠差异见 `docs/03` §10.8） |
| sys_job | 启动时加载 status=0 的任务并按 cron 调度；`invoke_target` 覆盖 6 个 @Scheduled 方法、`vehicleMonitoringTask` 全量基础信息同步、`trackTask` 历史轨迹/实时轨迹/逃费回写/可疑车迁移与 `ryTask`。`orgTask.syncOrgInfo` 与 `syncHistoryTrackNoCar` 在 Java 中方法体已注释，按空操作迁移。留白已收口：cron 校验与触发时间改用 `src/service/quartz_cron.rs`（按 Quartz `CronExpression` 逐分支移植，含 `?x` 逃过越界检查、第 8 段被丢弃、年字段不做范围校验三个怪癖）；`invoke_target` 改用 `src/service/job_invoke.rs` 复刻 `JobInvokeUtil` 的 bean/方法/参数解析与 Java 异常首行；注册表按 Java 的 `JobKey(jobId, jobGroup)` 建模，启动时装**全部**行（暂停的任务也能「立即执行」）。Java 侧没有 target 白名单（`JOB_WHITELIST_STR`/`JOB_ERROR_STR` 在本仓库无调用方），Rust 原先多出的 `目标字符串不在白名单内` 拒绝已删除。写入端点语义见 `docs/03-INTERFACE-VERIFICATION.md` §7 |
| 新增主键取回 | `select last_insert_id()` 的列元信息是 `BIGINT UNSIGNED`，按 `i64` 解码会报 `mismatched types` —— 5 处（sys_user/sys_role/sys_dept/sys_job/gen_table 的新增）统一改为 `u64` 再转 `i64`，由 `tools/endpoint_parity/post_smoke_matrix.py` 验证两端一致 |
| information_schema 列名 | 结果集元信息里是**大写**（`TABLE_NAME`），必须像 Java mapper 那样起驼峰别名，否则按 `table_name` 取不到值。受影响的是 `/tool/gen/importTable` 与 `createNew` 的「按表名同步列」：原先会登记出 `table_name=''` 的脏行、且不写任何 `gen_table_column`，接口却回「操作成功」。已修，脏行已清理 |
| TIMESTAMP 会话时区 | `car_*`/`gantry_*` 的 `create_time`/`update_time` 是 `timestamp(3)`（`sys_*`/`flow_*` 是 `datetime`）。SQLx 建连接默认 `SET time_zone='+00:00'`，而 Java 的 JDBC URL 写的是 `serverTimezone=GMT%2B8`：Rust 按本地墙上时钟写入会被当成 UTC 存，读出来差 8 小时，列表按 `create_time desc` 排序的基准也随之改变；另外 `NaiveDateTime` 与 `ColumnType::Timestamp` 类型不匹配，`db/rows.rs` 原先解码失败后落到兜底分支，**所有** manager 切片出参的 `createTime` 都是 `null`。现在按 Java 那条 URL 解析出会话时区覆盖 SQLx 默认（`Settings::mysql_session_timezone`），并给 `TIMESTAMP` 补 `DateTime<Utc>` 解码 |
| 请求体非列字段 | RuoYi 前端的每个 `add`/`edit` 请求体都带 `params`（`BaseEntity.params`），MP 的 `@TableField(exist = false)` 字段（`applyTime1` 等）同理。Java 的 Jackson 忽略它们，Rust 原先原样拼进 `INSERT` → `1054 Unknown column 'params'`，即**真实前端请求下所有新增/修改只有 Rust 是 500**。`insert_entity`/`update_entity_by_id` 先用 `information_schema` 的列集合（进程内缓存）过滤；自己拼 SQL 的路径（`sys_role` 的 add/edit/changeStatus 要在同一事务写 `sys_role_menu`、`sys_dept` 同理）改走 `support::entity_for_table`。`sys_user`/`sys_profile` 按字段白名单取值，本来就不带非列字段 |
| 共享缓存写入形状 | Java 用 FastJson2 写 Redis 缓存的形状是「`@type` 在最前 + 字段名字典序 + null 不写」，且命中缓存的接口是「拿缓存元素直接出参」（元素级 `@type` 被消费，`params` 里的 `{"@type":"java.util.HashMap"}` 会留在响应里）。Rust 原先按实体顺序写、连 null 一起写，导致同一个键被哪端写过就决定另一端怎么读。`sys_dict:*`、`car_list`、`car_list_jc` 统一走 `support::fastjson_rows()`，实测两种缓存来源下两端响应逐字节一致（`docs/03` §9.1） |
| 车辆新增 | `POST/PUT /manager/carinfo` 原先缺 Java `saveCarInfo` 的三段语义：车牌判重（`isExitsCar`，编辑时排除自己，命中则整条不写并回「车牌号存在重复，请确定！」）、新增分支 `escapedAmount` 补 `0` 且显式写 `updateBy/updateTime`、写完刷 `car_list`/`car_list_jc` 缓存。缓存实测与 Java 写的**键集合/键序/取值一致**；残留差异只有 FastJson2 的 Long `L` 后缀（`100L` vs `100`，两端类型化读写都不受影响） |
| 空表掩盖的出参缺陷 | `car_fee_record`/`car_route_detail`/`car_route_info`/`car_split_record` 库里 0 行，GET 全量比不出值。造出探针行后暴露三处：实体 `exist=false` 字段（`applyTime1`/`applyTime2`/`createTimeStr`）在 Java 出参里是显式 `null` 键、`@JsonFormat(pattern="yyyy-MM-dd")` 的 `inTime`/`outTime`/`lastPassTime`/`nextPassTime` 未截断、键序未按实体声明。四个宏块已补 `null as …` + `dates:` + `keys:` |
| 可疑车备份新增 | Java 的 `POST /manager/carsuspiciousback` 不带 `id` 时**必失败**：实体继承 `BasePlusEntityInput`（`@TableId(type = IdType.INPUT)`），`saveCarSuspiciousBack` 又不 `setUUID`，MP 仍把 `id` 放进列清单 → `Column 'id' cannot be null`。按「Java 的 bug 照抄」复刻：`support::ID_INPUT_TABLES` 关掉该表主键生成并显式写 `id = NULL`，两端同一 MySQL 报错、同样不写行。（`car_info` 也继承该基类，但其 service 显式 `setUUID`，不在其列） |
| 数据库报错包装 | 同一 SQL 约束错误，Java 出 MyBatis 整段包装（`### Error updating database. …### SQL: …`），Rust 出 `error returned from database: 1364 (HY000): …`。**HTTP 码、是否执行 SQL、写没写行、`data` 有无都一致**，只差文本模板；复刻需在 Rust 里重算 MP 随请求体变化的动态列清单，故记为已知偏差（对拍脚本判 WARN） |
| 远端透传成型 | `/base/feerecords|feeGantry|snapshotflow/{bigId}`：Java 经 Forest 反序列化成实体再由 Jackson 输出，实体字段恒出现、上游多给的字段被丢弃；Rust 原先原样透传。现在用 `support::entity_shape` 按 Java 实测键序成型（146/79/53 键），桩上游下两端逐字节一致。`/base/feestationexit/*` 两端都不成型（hutool `JSONObject` 透传，Java 键序是 `HashMap` 迭代序），只比结构 |
| 新增用户 | Java 侧 `POST /system/user` **任何**入参都失败（MyBatis 设置参数阶段抛 `IndexOutOfBoundsException: No group 2`），即 Java 的新增用户功能整体不可用；Rust 按正确行为实现，不复刻这条缺陷（但「部门不存在 → NPE → `{"msg":null}`」仍逐条对齐） |
| 模板导出 | EasyPOI 模板导出（gantry/snapshotFlow/feeRecords/carInfo/carSuspicious 等）改为标准 xlsx 工作簿，列顺序与模板一致；返回 `data=文件名` 而非二进制响应体 |
| 代码生成器 | `preview/download/genCode/batchGenCode` 已迁移：`src/service/velocity.rs`（Velocity 2.3 指令与空格吞噬子集）+ `src/api/generator/gen_render.rs`（prepareContext/getTemplateList/getImportList 桶序/dictionaryKeyToCamelCase/setPkColumn/init* 与 getFileName/getGenPath）+ `gen_link.rs`（`initLinkTableInfo`：`field_map_string` + `link_table_id` → LinkTableField/linkTable/tableFileInfo 与 GenColumnDialog 汇总）+ `gen_zip.rs`（STORE ZIP）。Java 的 DEFLATE 与 Rust 的 STORE 压缩包字节不同，按解压后的条目名与内容对拍：53 张表 x 10 模板逐字节一致；关联表配置在本库无实例，`gen_link` 按 Java 分支逐条实现并做了单测 |
| 实时/可疑车轨迹 | `trackTask` 已接线：实时轨迹读 `car_curent_trail:*`、历史轨迹读 `car_history_trail:*`、可疑车读请求体 `trailInfoList`。这些 Redis 缓存由外部采集服务写入；缓存为空时任务正常完成但不产生数据（与 Java 一致） |
| 车辆导入 | 两个 Excel 导入端点都已迁移并双端对拍：`src/common/import_util.rs` 移植 `ImportSysUtil`（`#.##` / 两种日期格式的取值规则、表头行可按行号复用、`break`/`结束` 提前终止）与 `ImportUtil.importExcel` 的 8 条规则码；`/manager/carinfo/import` 与 `/manager/exceptrecord/import`（双表头变体、字典翻译、按车牌补建车辆、差额与时间互校）逐条对齐。**修掉一处既有缺陷**：carinfo 的导入错误项原先用 `rowNum/errorMsg` 且消息是自己编的，Java 的 `ImportErrorEntity` 是 `rowNo/colName/message` 且消息来自规则码（“不能为空”“不是正整数”“不是小数”），且业务字典翻译只在没有任何规则错误时才跑。细节见 `docs/03-INTERFACE-VERIFICATION.md` §8 |
| 车辆轨迹 | `listByCarId/listByCarByTime` 走本地 `zdata_trail_tracks`；远端 sysutil 回退、`changeTrailInfo` 的 Geometry 计算、`carSnapShot` 远端抓拍返回空/原结构 |
| 可疑车辆同步 | `syncSuspiciousCarTask` 完成 SHA1 签名校验；依赖 Redis 轨迹缓存的生成逻辑未迁移（无缓存时 Java 同样不产出数据） |
| 路由参数名 | 同一路径的 GET 与 DELETE 在 axum 中必须使用相同占位符名（如 `/base/section/{ids}`），Java 的 `{id}`/`{ids}` 差异被统一；对客户端 URL 无影响。`route_parity` 测试按「method + 路径形状」校验 501 条端点 |
| 外部路径服务 | 轨迹绘制要调两个外部服务：`roadPathUrl` 的 `POST /api/routes/query`（`getCarGeometryByPlanNew`）与 `tx-service-url` 的腾讯 direction（`getCarGeometryByPlan`，含 `sig` 签名、polyline 增量解码、GCJ-02→WGS84、六位 HALF_UP）。Rust 原先只读 `car_lxgh:` 缓存、读不到就直接落本地桩号绘制，而这台机器出得了公网 —— 于是同一个可疑车辆 id，Java 返回一条整段路径、Rust 返回 6 段。现按 Java 的分支顺序补齐（`src/common/gps.rs` + `src/service/road_path.rs`，失败才回落，成功要回写缓存），清缓存后同一时间窗内两端逐字节一致；跨窗差几个点属路网结果刷新，`compare.py` 用 `VALUE_FREE` 只比结构（`docs/03` §10.2） |
| 方法不匹配 | Spring 把 `HttpRequestMethodNotSupportedException` 交给 `GlobalExceptionHandler`，回 HTTP **200** + `{"msg":"Request method 'POST' not supported","code":500}`；axum 是裸 405 空响应体还带 `Allow`。`build_router` 最内层加了翻译层（鉴权仍在外层先跑，未登录照旧 401），`web_filter` 再把 Java 从不发的 `Allow` 摘掉（`docs/03` §10.4） |
| 路径变量类型 | Java 的 `@PathVariable Long jobId` 遇 `1x` 在进控制器前失败，文案 `请求参数类型不匹配，参数[jobId]要求类型为：'java.lang.Long'，但输入值为：'1x'`（数组是 `[Ljava.lang.Long;`，第三个占位是**整段**原文）。Rust 原先一律 `Path<String>` 再宽松转换，`/monitor/job/1x` 会**真的返回 jobId=1 的数据**（MySQL 把 `'1x'` 当 1）。新增 `support::path_long/path_int/path_long_list/path_int_list`（按 Spring 的 `trimAllWhitespace`、`Long.valueOf` 语义）并改到 Java 侧 48 个数字路径变量端点；`tools/endpoint_parity/pathvar_matrix.py` 从 Java 源码解析类型后只用非法值探 GET |
| 两种「没权限」 | RuoYi 只定制了 `authenticationEntryPoint`（401 是 AjaxResult），授权失败仍走默认 `AccessDeniedHandlerImpl` → `sendError(403)` → `/error` 的 `{"timestamp","status":403,"error":"Forbidden","path"}`（HTTP 403）。命中 `anonymous()`（`/system/notice/view/**`、`/system/file/view/**`、`/common/download**`）与 `denyAll()` 的**已认证**请求是这一种；`@PreAuthorize` 的失败才是 AjaxResult。`error::forbidden_error_page` 与 `AppError::forbidden` 分别对应 |
| 响应头与 Content-Type | Java 每条响应带 `X-Trace-Id`（`TraceIdFilter`：非空透传、否则 32 位小写十六进制 UUID）、`X-Content-Type-Options: nosniff`、`X-XSS-Protection: 1; mode=block`；CORS 只有 `Vary: Origin`，不带 `Origin` 时不回 `Access-Control-Allow-Credentials`，`Access-Control-Allow-Headers` 用 `", "` 回显。Content-Type 分三类：控制器与 MVC 异常 = `application/json`，安全入口 401 = `application/json;charset=utf-8`，`/error` 错误页 = GET/DELETE 无 charset、POST/PUT/PATCH 带 `;charset=UTF-8`。落在 `src/middleware/web_filter.rs`（最外层） |
