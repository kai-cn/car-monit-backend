# 附录 D：中间件、配置项与不可直接翻译点

> 依据：`ruoyi-admin/src/main/resources/application.yml`、`application-druid.yml`、`logback.xml`、`spy.properties`、各 `@ConfigurationProperties` / `@Value` 类，以及全部 `@KafkaListener`、`@Scheduled`、`@Scheduled` 调用点。
> 本文只描述**现状与迁移方案**，不改动 Java 代码。

---

## D1. 运行时组件总览

| # | 组件 | Java 实现 | 实际状态 | Rust 目标实现 |
|---|---|---|---|---|
| 1 | Web 容器 | 内置 Tomcat（端口 9989，context `/`） | 启用 | tokio + axum + hyper，端口/路径保持一致 |
| 2 | MVC | Spring MVC | 启用 | axum Router + extractor |
| 3 | 安全 | Spring Security + JWT（jjwt 0.9.1） | 启用 | tower 中间件 + `jsonwebtoken` + 显式权限守卫 |
| 4 | 数据源 | Druid 1.2.20 + P6Spy + MySQL 8 | 启用（从库关闭） | sqlx `MySqlPool`（连接池参数对齐） |
| 5 | ORM | MyBatis-Plus 3.5.5 + PageHelper 1.4.7 | 启用 | SQLx 手写 SQL + 显式分页 |
| 6 | 分表 | ShardingSphere 5.2.1 | **未启用**（缺少 `sharding.enabled`） | **用户决策启用**：仓储层逻辑表路由（快照流水按月、费用记录按日），默认 `sharding.enabled=true` |
| 7 | 手工分表查询 | `SnapshotFlowEnhancedService` + 动态表名 | 启用 | 按月份拼表名 + 逐表 COUNT/LIMIT + 归并排序 |
| 8 | Redis | Lettuce + `RedisTemplate` + FastJson2 序列化 | 启用 | redis-rs（tokio）连接池 + 兼容序列化器 |
| 9 | Kafka | spring-kafka 2.5.15 | **仅 2 个监听器启用**：`SnapshotFlowKafkaConsumerV2`、`CdcSyncService` | rust-rdkafka（librdkafka） |
| 10 | Elasticsearch | RestHighLevelClient 7.15.2 | 查询/写入代码启用；CDC 的 ES 写入被注释 | elasticsearch crate 或直连 REST |
| 11 | 定时任务 | Quartz（RAM JobStore） | 启用；启动时清空调度器并从 `sys_job` 重建 | tokio 定时器 + 任务注册表（见 D6） |
| 12 | `@Scheduled` | Spring Scheduling | **全部失效**（全仓库无 `@EnableScheduling`） | **用户决策启用**：6 个方法全部注册（cron 与注解一致） |
| 13 | 对象存储 | AWS S3 SDK（MinIO 兼容） | `OssTemplate` Bean 启用；`/oss/**` 端点未注册（`oss.info` 未配置） | aws-sdk-s3；`/oss` 端点默认不注册 |
| 14 | 短信 | 阿里云 Dysmsapi / MNS | 代码启用，模板全部为空串 | reqwest 直连 Dysmsapi（签名算法对齐）；空模板行为保持一致 |
| 15 | 外部 HTTP | Forest 1.6.0 | 启用 | reqwest + 显式客户端封装 |
| 16 | 验证码 | kaptcha 2.3.3（math/char） | 启用 | `captcha` crate 或自绘；**只保证语义一致**（算式/字符、2 分钟、一次性） |
| 17 | Excel | Apache POI 4.1.2 + EasyPOI + 模板导出 | 启用 | rust_xlsxwriter（导出）/ calamine（导入）；模板文件逐像素对齐 |
| 18 | 代码生成 | Velocity 2.3 + `gen_table` | 启用 | minijinja/tera + 模板文件；生成物需与 Java 模板一致 |
| 19 | 系统信息 | OSHI 6.5.0 | 启用 | `sysinfo` crate |
| 20 | UA 解析 | UserAgentUtils 1.21 | 启用 | `user-agent-parser` 或自实现映射表 |
| 21 | 接口文档 | springfox 3.0.0（`swagger.enabled=false`） | 关闭 | utoipa（默认关闭，路径 `/v3/api-docs` 不暴露） |
| 22 | 数据源切换 | dynamic-datasource + `@DataSource` | 从库关闭，实际恒为主库 | 单连接池，不实现动态数据源 |
| 23 | 异步 | `AsyncManager` + 自定义线程池；`@Async` **未启用** | `AsyncManager` 启用；`@Async` 无效（无 `@EnableAsync`） | tokio::spawn + `sleep(10ms)`；短信方法同步执行 |
| 24 | 本地文件 | `/profile/**` → `ruoyi.profile` | 启用 | tower-http `ServeDir`，路径映射一致 |
| 25 | 国际化 | `i18n/messages.properties` | 启用 | 内嵌静态消息表（或 rust-i18n），键名与文案一致 |
| 26 | 监控 | `TraceIdFilter`、`SqlLogInterceptor`、`MetricCollector`、`AlertEngine` | 启用 | tower 中间件 + tracing span + 内存指标结构 |
| 27 | Druid 控制台 | `/druid/*`（druidUser） | Servlet 注册，但 Security `denyAll` | **不迁移**；返回 403/404 等价行为 |

> 关键结论：Java 侧 `@Scheduled` 全部失效、ShardingSphere 未启用、CDC 的 ES 写入是空操作、`/oss/**` 未注册。用户已决策：**`@Scheduled` 与 ShardingSphere 在 Rust 侧启用**；CDC ES 写入继续保持空操作；`/oss/**` 默认不注册（`oss.info=true` 时注册）。

---

## D2. Redis：key、value、TTL、失效逻辑

序列化：key 使用 `StringRedisSerializer`；value 使用 `FastJson2JsonRedisSerializer`，即 `JSON.toJSONString(t, WriteClassName)`，对象会带 `@type` 字段；反序列化启用 `AUTO_TYPE_FILTER`，白名单前缀 `org.springframework`、`com.ruoyi`。

| Key 模式 | Value | TTL | 写入/读取位置 | 备注 |
|---|---|---|---|---|
| `login_tokens:{token}` | `LoginUser` JSON（含 `@type`、`user`、`permissions`、`loginTime`、`expireTime`、`ipaddr`、`loginLocation`、`browser`、`os`、`sessionId`） | `token.expireTime` 分钟（默认 120） | `TokenService.createToken/refreshToken` | 剩余 ≤ 20 分钟时自动续期并重写 TTL；`LoginUser.user.password` 为 BCrypt 密文，会进入 Redis |
| `captcha_codes:{uuid}` | 验证码字符串（math 为计算结果，char 为字符） | 2 分钟 | `CaptchaController` 写；`SysLoginService.login` 读后立即删除 | 一次性；`code` 为空时跳过校验 |
| `sys_config:{configKey}` | 配置值字符串 | 无过期 | `SysConfigServiceImpl` 启动预热；增删改同步 | 启动时全量加载 `sys_config` |
| `sys_dict:{dictType}` | `List<SysDictData>` JSON | 无过期 | `DictUtils` / `SysDictTypeServiceImpl` 启动预热 | 字典增删改时刷新 |
| `pwd_err_cnt:{username}` | 失败次数（整数） | `user.password.lockTime` 分钟（默认 10） | `SysPasswordService` | 每次失败重写 TTL；成功后删除 |
| `repeat_submit:{requestURI}{Authorization}` | `{ "{requestURI}": { "repeatParams": "...", "repeatTime": <ms> } }` | `@RepeatSubmit.interval()` 毫秒（默认 5000） | `SameUrlDataInterceptor` | 仅 1 处使用：`SysConfigController.add` |
| `snapshot:flow:idempotent_{bigId}` | `"1"` | `idempotent.redis.expire-time` 秒（默认 86400） | `IdempotentUtil` | Kafka 消费幂等；处理异常时删除标记 |
| `rate_limit:{key}` | 计数 | `@RateLimiter.time()` 秒 | `RateLimiterAspect` | 当前 0 处使用 |
| `partition:mapping:{bigId}` | 分区名（如 `p202508`） | 30 天 | `PartitionMappingCache` | 注意：该类当前**无调用方**（死代码） |
| `sharding:id:cache:snapshot:{bigId}` | 分表名（如 `ods_rt_szdn_snapshot_flow_202508`） | 7 天 | `ShardingIdCacheService` | 优先从雪花 ID 解析时间；解析失败才查缓存 |
| `sharding:id:cache:fee:{id}` | 费用分表名 | 7 天 | 同上 | 费用表按日分表 |
| `cdc:retry:{messageId}` | `CdcMessage` JSON（String 序列化） | 接口传入的延迟秒数 | `DeadLetterQueueService` | 使用 `RedisTemplate<String,String>`，**不是** FastJson2 对象序列化 |
| `cdc:dead:{messageId}` | `CdcMessage` JSON | 7 天 | 同上 | CDC 死信 |
| `gantry_list` / `gantry_list_data:{code}` | 门架对象/详情 | 无过期 | `OdsSzdnGantryServiceImpl` 等 | 门架数据变更时刷新 |
| `car_list` / `car_list_jc` | 重点车辆列表/简称 | 无过期 | `CarInfoServiceImpl` | 增删改时刷新 |
| `white_car_list` | 白名单列表 | 无过期 | `CarWhiteInfoServiceImpl` | 增删改时刷新 |
| `car_warning_list` / `car_warning_config_list` / `car_warning_rule:{...}` | 预警/规则缓存 | 无过期 | 预警相关 Service | 规则变更时刷新 |
| `lxbh_jdwd:{roadCode}` | 路线经纬度 | 无过期 | 路线查询 | |
| `car_curent_trail:{carNo}` / `car_history_trail:{carNo}` / `car_lxgh:{...}` | 轨迹/路径规划结果 | 无过期 | `CarTrackInfoServiceImpl` | 轨迹查询缓存 |
| `sys_config:sync_current_time` / `sys_config:api_map` / `sys_config:warning_trigger_timespan` | 业务阈值 | 无过期 | 预警任务直接读 Redis | 实际由 `sys_config` 预热产生 |

Rust 侧要求：
1. key 字符串逐字符一致；
2. TTL 单位/数值一致；
3. `login_tokens` 的 value 必须能被 Java 版本反序列化（滚动切换期间），因此需要复刻 FastJson2 的 `@type` 结构；或者切换时清空 `login_tokens:*`（需用户确认，见主文档“待确认项”）。
4. `null` 与空集合的写入/删除语义保持一致。

---

## D3. Kafka

### D3.1 生效的监听器

| 监听器 | Topic | Group | 并发 | Ack/提交 | 消息格式 | 处理语义 |
|---|---|---|---|---|---|---|
| `SnapshotFlowKafkaConsumerV2.consumeBatch` | `ods-rt-szdn-snapshot-flow` | `snapshot-flow-consumer-group` | 3 | 批量监听 + `MANUAL_IMMEDIATE`；整批处理完统一 `acknowledge()` | `{"operationType":"INSERT|UPDATE|DELETE","data":{...OdsRtSzdnSnapshotFlowAddcode...}}` | 解析 → `bigId` 必填 → Redis 幂等 → INSERT/UPDATE 收集批量写 MySQL + ES；DELETE 调 `removeById`；失败单条本地重试 3 次（间隔 1s）→ 仍失败发 DLQ；异常回滚已写幂等标记后抛出（不 ack） |
| `CdcSyncService.consumeCdcMessage` | `snapshot-flow-cdc` | `snapshot-flow-cdc-group` | 3 | 手动 `acknowledge()`；所有分支（成功/失败/异常）都 ack | `CdcMessage`（`messageId`、`operationType`、`beforeData`、`afterData`、`retryCount`） | 解析 → INSERT/UPDATE/DELETE 分支；**ES 写入代码全部注释**，仅打日志；失败进入重试队列但依然 ack |

### D3.2 配置与生产者

| 项 | 值 |
|---|---|
| bootstrap-servers | `127.0.0.1:9092` |
| consumer.enable-auto-commit | `false` |
| auto-offset-reset | `earliest` |
| max-poll-records | `500` |
| max-poll-interval-ms | `300000` |
| fetch-max-bytes | `52428800` |
| session-timeout-ms | `60000` |
| producer.acks | `all` |
| producer.retries | `3` |
| listener.ack-mode | `manual_immediate` |
| listener.concurrency | `3` |
| DLQ topic | `ods-rt-szdn-snapshot-flow-dlq` |
| DLQ 消息体 | `{originalTopic, partition, offset, timestamp, reason, value}`（FastJson2 序列化） |

### D3.3 其他监听器（均被注释，不迁移为活动消费者）

- `SnapshotFlowKafkaConsumer`（旧版）
- `DebeziumSnapshotFlowKafkaConsumer`
- `DebeziumReadonlyKafkaConsumer`

### D3.4 Rust 侧注意

- rust-rdkafka 的批量消费/手动提交需要显式 `commit_message`/`commit_consumer_state`；要复刻“整批成功才提交、抛异常不提交”的语义。
- 消费组 rebalance 期间的行为无法与 Spring Kafka 完全一致；需保证幂等键（`bigId`）承担最终一致性。
- DLQ 生产者的 key 为空、value 为 JSON 字符串；acks/retries 对齐。

---

## D4. Elasticsearch

| 项 | 值/语义 |
|---|---|
| 地址 | `127.0.0.1:9200` |
| 索引 | `snapshot-flow`（`elasticsearch.index`） |
| 写入 | `index`，文档 `_id = bigId`；批量使用 `BulkRequest` |
| 查询 | `bool.must`：`platenumber` wildcard（`*值*`）、`sectioncode`/`orgcode`/`gantrycode` term、`snapshottime` range；按 `snapshottime desc`；`from=(pageNum-1)*pageSize`、`size=pageSize` |
| 分页返回 | `TableDataInfo(total=hits.total, rows=source 列表, code=200, msg="查询成功")` |
| 可用性 | `ping` 失败时降级（调用方处理） |
| 当前调用方 | `SnapshotFlowKafkaConsumerV2.batchSaveData`（写入）；CDC 写入被注释；`searchPage` 暂无 Controller 调用（保留能力） |

Rust 侧：优先使用 `elasticsearch` crate（7.x API）；如类型覆盖不足，直接用 `reqwest` 调 `_search`/`_bulk`，保证 DSL 与响应字段一致。

---

## D5. 定时任务与后台 Worker

### D5.1 Quartz（生效）

- 依赖 `org.quartz-scheduler:quartz` + Spring Boot QuartzAutoConfiguration；
- `ScheduleConfig` 整个文件被注释，因此使用 **RAM JobStore**，默认线程池（Spring Boot 默认 10 线程）；
- `SysJobServiceImpl.@PostConstruct init()`：`scheduler.clear()` → `selectJobAll()` → 逐条 `ScheduleUtils.createScheduleJob`；
- `invoke_target` 形如 `ryTask.ryParams('ry')` 或全类名；通过反射调用 Spring Bean 或 `Class.forName().newInstance()`；
- `sys_job`、`sys_job_log` 为持久化表；任务 CRUD 端点均在 `/monitor/job/**`；
- 并发策略：`@DisallowConcurrentExecution` / `@PersistJobDataAfterExecution` 由 `ScheduleUtils` 根据 `concurrent` 字段动态处理。

Java 侧可被 `invoke_target` 调用的 Bean/方法（当前代码内）：

| Bean | 方法 |
|---|---|
| `ryTask` | `ryMultipleParams`, `ryParams`, `ryNoParams`, `autoBuildGoodsHb` |
| `orgTask` | `syncOrgInfo` |
| `vehicleMonitoringTask` | `syncOrgInfo`, `syncSectionInfo`, `syncGantryInfo`, `syncServiceAreaInfoInfo`, `syncTollBoothInfoInfo`, `syncSfzjcxxInfoInfo`, `syncTollStationInfo` |
| `trackTask` | `syncCurrentTrack`, `syncSuspiciousCar`, `syncHistoryTrack`, `saveCarExcept`, `syncHistoryTrackNoCar`, `changeCarSuspicious` |
| `snapshotFlowSyncTask` | `syncFullData`, `syncIncrementalData`, `preCreateTables`, `checkDataConsistency` 等 public 方法 |
| `partitionMaintenanceTask` | `createFuturePartitions`, `checkPartitionHealth` |

> **阻塞点**：`sys_job` 的实际行不在仓库内。必须导出生产库 `sys_job` 数据，才能确定真实任务、cron、参数、并发策略。Rust 侧需要一张 `invoke_target` 字符串 → Rust 函数的注册表；未知 target 必须记录错误并跳过，行为与 Java 反射失败一致。

### D5.2 `@Scheduled`（Java 失效 → 用户决策 Rust 启用）

以下方法在 Java 中因**没有 `@EnableScheduling`** 从未执行；**用户已决策 Rust 侧全部启用**，cron 与注解一致：

- `PartitionMaintenanceTask.createFuturePartitions`（每月 1 日 01:00）
- `PartitionMaintenanceTask.checkPartitionHealth`（每周一 02:00）
- `SnapshotFlowSyncTask.syncIncrementalData`（每小时）
- `SnapshotFlowSyncTask.manualFullSync`（每 5 分钟，`cron = "0 0/5 * * * *"`；`preCreateTables` 没有 `@Scheduled`，只作为 `invoke_target` 可调用）
- `ShardingTableTask.createShardingTables`（每月 1 日 01:00）
- `ViewMaintenanceTask.scheduledViewMaintenance`（每月 1 日 02:00）

> `SnapshotFlowSyncTask.@PostConstruct init()` 会创建线程池；`SnapshotFlowSyncTask` 属于用户要求“照样迁移”的范围，Rust 启动时应同样初始化该线程池（用 tokio 任务池等价实现）。

### D5.3 异步线程池

| Bean/字段 | 配置 |
|---|---|
| `threadPoolTaskExecutor` | 核心 10、最大 20、队列 200、keepAlive 300s、`CallerRunsPolicy`、线程名前缀 `ry-task-` |
| `scheduledExecutorService` | 核心 10、`ScheduledThreadPoolExecutor`、`CallerRunsPolicy`、线程名前缀 `ry-schedule-` |
| `AsyncManager` | 10ms 延迟后执行登录日志/操作日志落库 |
| `PartitionParallelQueryService` | 4 线程固定池（当前无调用方） |
| `SnapshotFlowSyncTask.syncExecutor` | 4/8 线程、队列 100（仅启动时创建） |

Rust 侧：tokio 多线程运行时；日志落库使用 `tokio::spawn` + `sleep(Duration::from_millis(10))`；不要用 `spawn_blocking` 包装纯 SQLx 异步调用。

---

## D6. 认证、鉴权与密码

| 项 | 现状 |
|---|---|
| 认证方式 | 无状态 JWT；`Authorization: Bearer <token>`，前缀可省略 |
| JWT 算法 | HS512（jjwt 0.9.1） |
| secret | `token.secret`（默认 `abcdefghijklmnopqrstuvwxyz`） |
| Claims | 仅 `login_user_key = token(UUID)` |
| 有效期 | `token.expireTime` 分钟（默认 120）；剩余 ≤ 20 分钟自动续期 |
| 登出 | `POST /logout`，删除 `login_tokens:{token}`，异步记录登录日志 |
| 权限 | `@PreAuthorize("@ss.hasPermi('a:b:c')")`，共 284 处；管理员拥有 `*:*:*` |
| 密码 | BCrypt；登录前校验复杂度 8–20 位且含大小写/数字/特殊字符，失败返回 `AjaxResult.error("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！")` |
| 重试锁定 | 5 次 / 10 分钟（Redis `pwd_err_cnt:*`） |
| 登录验证码 | 仅当 `code` 非空才校验；2 分钟有效；一次性 |
| 失败响应 | HTTP 状态仍为 200，body `{"code":401,"msg":"请求访问：{uri}，认证失败，无法访问系统资源"}` |
| 无权限 | body `{"code":403,"msg":"没有权限，请联系管理员授权"}`（HTTP 200） |
| 白名单 | `/login`、`/captchaImage`、GET 静态资源、`/profile/**`、`/common/download**`、`/system/file/view/**`、`/system/notice/view/**`、`/manager/suspicious/syncSuspiciousCarTask`；`/swagger-ui.html`、`/swagger-resources/**`、`/webjars/**`、`/*/api-docs`、`/druid/**` 为 denyAll |

Rust 侧：
- `jsonwebtoken` 默认 header `typ=JWT`、`alg=HS512`；jjwt 0.9.1 对 secret 的 base64 处理有历史怪癖（按 4 字符分组截断），必须按 Java 实际字节复刻，否则旧 token 全部失效。
- 认证失败必须在**中间件层**直接返回 HTTP 200 + JSON，而不是抛 401 状态码。
- `@PreAuthorize` 改为每条路由的 `permission` 元数据 + 统一守卫；权限字符串从端点清单（附录 B）逐条迁移。

---

## D7. Servlet 过滤器 / 拦截器 / AOP 对照

| Java 机制 | 作用 | Rust 替代 | 注意 |
|---|---|---|---|
| `TraceIdFilter`（order=1） | 读取/生成 `X-Trace-Id`，写 MDC、响应头，记录请求耗时 | tower 中间件 + `tracing::info_span!` + task-local | 每个请求一个 span；响应头同名 |
| `XssFilter`（`/system/*,/monitor/*,/tool/*`，排除 `/system/notice`） | 包装 request，清洗 body/parameter 中的 XSS；GET/DELETE 跳过 | tower 中间件读取并重写 body | 保留排除规则；JSON body 才清洗，避免破坏 multipart |
| `RepeatableFilter` | 包装 body 支持重复读取 | axum `Bytes` 天然可克隆 | 与重复提交拦截配合 |
| `SameUrlDataInterceptor`（`/**`） | `@RepeatSubmit` 防重 | 路由层提取器/中间件读 Redis | 仅 `SysConfigController.add` 使用 |
| `LogAspect`（239 处 `@Log`） | 操作日志落 `sys_oper_log` | 路由元数据 `operation_log` + 中间件异步落库 | `oper_param`/`json_result` 截断 2000 字符；IP/地点/浏览器/OS 规则一致 |
| `DataScopeAspect`（3 处） | 把数据权限 SQL 片段塞进 `params.dataScope` | 服务层显式拼接 SQL 条件 | 仅 `SysDeptServiceImpl.selectDeptList`、`SysRoleServiceImpl.selectRoleList`、`SysUserServiceImpl.selectUserList` |
| `RateLimiterAspect`（0 处） | Redis 限流 | 不实现或保留空能力 | 无注解使用，不影响行为 |
| `DataSourceAspect`（`@DataSource`） | 主从切换 | 单池 | 从库关闭 |
| `@Transactional`（159 处） | 事务边界 | `sqlx::Transaction` 显式包裹 | Spring 默认仅对 RuntimeException/Error 回滚；Rust 中所有 `Err` 都应回滚（除非显式 commit） |
| `@PostConstruct` | 启动预热 | `main` 启动序列（DB 连接 → 缓存预热 → 调度器 → 监听器） | 预热失败是否阻止启动需与 Java 对齐（Java 会阻止） |
| `SpringUtils.getBean` / `SecurityUtils.getLoginUser` | 静态取 Bean/当前用户 | `AppState` + 请求扩展（`Extension<CurrentUser>`） | 禁止全局可变单例 |

---

## D8. 配置项清单（Java → Rust）

### D8.1 命名约定（建议，待确认）

- Rust 默认读取 `config/application.yaml`（结构与 Java 相同），可选 `config/application-{APP_PROFILE}.yaml`；
- 环境变量覆盖：前缀 `APP_`，层级用 `__`，大写；`-` 在环境变量中写作 `_`；
- 例：`server.port` → `APP_SERVER__PORT`；`kafka.topic.snapshot-flow` → `APP_KAFKA__TOPIC__SNAPSHOT_FLOW`；
- 优先级：命令行 > 环境变量 > profile 文件 > 默认文件 > 代码默认值。

### D8.2 逐项对照

| Java 配置键 | 默认值 | Rust 配置键 | 环境变量 | 说明 |
|---|---|---|---|---|
| `ruoyi.name` | `系统` | `ruoyi.name` | `APP_RUOYI__NAME` | 仅展示 |
| `ruoyi.version` | `3.8.7` | `ruoyi.version` | `APP_RUOYI__VERSION` | 仅展示 |
| `ruoyi.copyrightYear` | `2024` | `ruoyi.copyright_year` | `APP_RUOYI__COPYRIGHT_YEAR` | 仅展示 |
| `ruoyi.profile` | `D:/ruoyi/uploadPath` | `ruoyi.profile` | `APP_RUOYI__PROFILE` | 上传根目录，`/profile/**` 映射 |
| `ruoyi.addressEnabled` | `false` | `ruoyi.address_enabled` | `APP_RUOYI__ADDRESS_ENABLED` | false 时地点为 `XX XX`；内网为 `内网IP` |
| `ruoyi.captchaType` | `math` | `ruoyi.captcha_type` | `APP_RUOYI__CAPTCHA_TYPE` | math/char |
| `server.port` | `9989` | `server.port` | `APP_SERVER__PORT` | 必须一致 |
| `server.servlet.context-path` | `/` | `server.context_path` | `APP_SERVER__CONTEXT_PATH` | 保持一致 |
| `server.tomcat.uri-encoding` | `UTF-8` | `server.uri_encoding` | `APP_SERVER__URI_ENCODING` | |
| `server.tomcat.accept-count` | `1000` | `server.accept_count` | `APP_SERVER__ACCEPT_COUNT` | 映射为 listen backlog |
| `server.tomcat.threads.max` | `800` | `server.max_threads` | `APP_SERVER__MAX_THREADS` | tokio worker 线程数参考 |
| `server.tomcat.threads.min-spare` | `100` | `server.min_spare_threads` | `APP_SERVER__MIN_SPARE_THREADS` | 仅记录 |
| `logging.level.com.ruoyi` | `debug` | `logging.level.com_ruoyi` | `APP_LOGGING__LEVEL__COM_RUOYI` | tracing filter |
| `logging.level.org.springframework` | `warn` | — | — | 无对应 |
| `monitor.enabled` | `true` | `monitor.enabled` | `APP_MONITOR__ENABLED` | |
| `monitor.slow-request-threshold` | `3000` | `monitor.slow_request_threshold` | `APP_MONITOR__SLOW_REQUEST_THRESHOLD` | ms |
| `monitor.slow-method-threshold` | `500` | `monitor.slow_method_threshold` | `APP_MONITOR__SLOW_METHOD_THRESHOLD` | ms |
| `monitor.slow-sql-threshold` | `1000` | `monitor.slow_sql_threshold` | `APP_MONITOR__SLOW_SQL_THRESHOLD` | ms |
| `monitor.trace-id-header` | `X-Trace-Id` | `monitor.trace_id_header` | `APP_MONITOR__TRACE_ID_HEADER` | |
| `monitor.alert-window-ms` | `60000` | `monitor.alert_window_ms` | `APP_MONITOR__ALERT_WINDOW_MS` | |
| `monitor.alert-max-count` | `5` | `monitor.alert_max_count` | `APP_MONITOR__ALERT_MAX_COUNT` | |
| `user.password.maxRetryCount` | `5` | `user.password.max_retry_count` | `APP_USER__PASSWORD__MAX_RETRY_COUNT` | |
| `user.password.lockTime` | `10` | `user.password.lock_time` | `APP_USER__PASSWORD__LOCK_TIME` | 分钟 |
| `spring.profiles.active` | `druid` | `app.profile` | `APP_PROFILE` | 只影响数据源文件加载 |
| `spring.messages.basename` | `i18n/messages` | `app.messages` | `APP_MESSAGES` | 内嵌资源 |
| `spring.servlet.multipart.max-file-size` | `40MB` | `upload.max_file_size` | `APP_UPLOAD__MAX_FILE_SIZE` | Spring 限制 |
| `spring.servlet.multipart.max-request-size` | `200MB` | `upload.max_request_size` | `APP_UPLOAD__MAX_REQUEST_SIZE` | Spring 限制 |
| `spring.devtools.restart.enabled` | `true` | — | — | 不迁移 |
| `spring.redis.host` | `127.0.0.1` | `redis.host` | `APP_REDIS__HOST` | |
| `spring.redis.port` | `6379` | `redis.port` | `APP_REDIS__PORT` | |
| `spring.redis.database` | `0` | `redis.database` | `APP_REDIS__DATABASE` | |
| `spring.redis.password` | 空 | `redis.password` | `APP_REDIS__PASSWORD` | |
| `spring.redis.timeout` | `10s` | `redis.timeout_ms` | `APP_REDIS__TIMEOUT_MS` | |
| `spring.redis.lettuce.pool.min-idle` | `0` | `redis.pool.min_idle` | `APP_REDIS__POOL__MIN_IDLE` | |
| `spring.redis.lettuce.pool.max-idle` | `8` | `redis.pool.max_idle` | `APP_REDIS__POOL__MAX_IDLE` | |
| `spring.redis.lettuce.pool.max-active` | `8` | `redis.pool.max_active` | `APP_REDIS__POOL__MAX_ACTIVE` | |
| `spring.redis.lettuce.pool.max-wait` | `-1ms` | `redis.pool.max_wait_ms` | `APP_REDIS__POOL__MAX_WAIT_MS` | |
| `token.header` | `Authorization` | `token.header` | `APP_TOKEN__HEADER` | |
| `token.secret` | `abcdefghijklmnopqrstuvwxyz` | `token.secret` | `APP_TOKEN__SECRET` | 部署时务必覆盖 |
| `token.expireTime` | `120` | `token.expire_time` | `APP_TOKEN__EXPIRE_TIME` | 分钟 |
| `mybatis-plus.global-config.db-config.id-type` | `ASSIGN_ID` | — | — | Rust 自实现雪花/ASSIGN_ID |
| `mybatis-plus.typeAliasesPackage` | `com.ruoyi.**.domain,com.ruoyi.**.bean` | — | — | 无对应 |
| `mybatis-plus.mapperLocations` | `classpath*:mapper/**/*Mapper.xml` | — | — | 改为 Rust 代码内 SQL |
| `pagehelper.helperDialect` | `mysql` | — | — | 改为显式分页 |
| `generator-code.mybatis-plus.enable` | `true` | `generator.mybatis_plus.enable` | `APP_GENERATOR__MYBATIS_PLUS__ENABLE` | 代码生成开关 |
| `swagger.enabled` | `false` | `openapi.enabled` | `APP_OPENAPI__ENABLED` | 默认关闭 |
| `swagger.pathMapping` | `/dev-api` | `openapi.path_mapping` | `APP_OPENAPI__PATH_MAPPING` | |
| `xss.enabled` | `true` | `xss.enabled` | `APP_XSS__ENABLED` | |
| `xss.excludes` | `/system/notice` | `xss.excludes` | `APP_XSS__EXCLUDES` | 逗号分隔 |
| `xss.urlPatterns` | `/system/*,/monitor/*,/tool/*` | `xss.url_patterns` | `APP_XSS__URL_PATTERNS` | 逗号分隔 |
| `oss.endpoint` | `http://172.30.100.102:9002` | `oss.endpoint` | `APP_OSS__ENDPOINT` | 部署时覆盖 |
| `oss.accessKey` | `jtwl_access_key` | `oss.access_key` | `APP_OSS__ACCESS_KEY` | 部署时覆盖 |
| `oss.secretKey` | `minio.prod` | `oss.secret_key` | `APP_OSS__SECRET_KEY` | 部署时覆盖 |
| `oss.bucketName` | `developer` | `oss.bucket_name` | `APP_OSS__BUCKET_NAME` | |
| `oss.enable` | 缺省 → `true` | `oss.enable` | `APP_OSS__ENABLE` | `OssTemplate` 是否创建 |
| `oss.info` | 缺省 → `false` | `oss.info` | `APP_OSS__INFO` | `/oss/**` 是否注册 |
| `oss.pathStyleAccess` | `true` | `oss.path_style_access` | `APP_OSS__PATH_STYLE_ACCESS` | |
| `oss.maxConnections` | `100` | `oss.max_connections` | `APP_OSS__MAX_CONNECTIONS` | |
| `sms.signature` | 空 | `sms.signature` | `APP_SMS__SIGNATURE` | |
| `sms.accessKeyId` | 空 | `sms.access_key_id` | `APP_SMS__ACCESS_KEY_ID` | |
| `sms.accessKeySecret` | 空 | `sms.access_key_secret` | `APP_SMS__ACCESS_KEY_SECRET` | |
| `sms.sendCodeTemplete` | 空 | `sms.send_code_template` | `APP_SMS__SEND_CODE_TEMPLATE` | |
| `sms.sendCheckPersonNoticeTemplete` | 空 | `sms.send_check_person_notice_template` | `APP_SMS__SEND_CHECK_PERSON_NOTICE_TEMPLATE` | |
| `sms.sendExpertNoticeTemplete` | 空 | `sms.send_expert_notice_template` | `APP_SMS__SEND_EXPERT_NOTICE_TEMPLATE` | |
| `sms.sendSupplierInvitationsNoticeTemplete` | 空 | `sms.send_supplier_invitations_notice_template` | `APP_SMS__SEND_SUPPLIER_INVITATIONS_NOTICE_TEMPLATE` | |
| `sms.sendInvitationSupplierTemplate` | 空 | `sms.send_invitation_supplier_template` | `APP_SMS__SEND_INVITATION_SUPPLIER_TEMPLATE` | |
| `sms.sendYckbSupplierTemplate` | 空 | `sms.send_yckb_supplier_template` | `APP_SMS__SEND_YCKB_SUPPLIER_TEMPLATE` | |
| `forest.bean-id` | `forestConfiguration` | `forest.bean_id` | `APP_FOREST__BEAN_ID` | |
| `forest.backend` | `httpclient` | `forest.backend` | `APP_FOREST__BACKEND` | |
| `forest.max-connections` | `1000` | `forest.max_connections` | `APP_FOREST__MAX_CONNECTIONS` | reqwest 连接池 |
| `forest.max-route-connections` | `500` | `forest.max_route_connections` | `APP_FOREST__MAX_ROUTE_CONNECTIONS` | |
| `forest.timeout` | `60000` | `forest.timeout_ms` | `APP_FOREST__TIMEOUT_MS` | |
| `forest.connect-timeout` | `60000` | `forest.connect_timeout_ms` | `APP_FOREST__CONNECT_TIMEOUT_MS` | |
| `forest.logEnabled` | `true` | `forest.log_enabled` | `APP_FOREST__LOG_ENABLED` | |
| `forest.retryer` | `BackOffRetryer` | `forest.retryer` | `APP_FOREST__RETRYER` | |
| `forest.retry-count` | `2` | `forest.retry_count` | `APP_FOREST__RETRY_COUNT` | |
| `forest.max-retry-interval` | `1000` | `forest.max_retry_interval_ms` | `APP_FOREST__MAX_RETRY_INTERVAL_MS` | |
| `forest.variables.hendaUrl` | `http://36.200.20.14:7890/8809/geoserver-pg/rest` | `forest.variables.henda_url` | `APP_FOREST__VARIABLES__HENDA_URL` | |
| `hengda.appid` | `YHZS` | `hengda.appid` | `APP_HENGDA__APPID` | |
| `hengda.secret` | 见 yml | `hengda.secret` | `APP_HENGDA__SECRET` | 部署时覆盖 |
| `vehicleMonitor.baseUrl` | `http://127.0.0.1:9901` | `vehicle_monitor.base_url` | `APP_VEHICLE_MONITOR__BASE_URL` | |
| `isLocalhost` | `local` | `is_localhost` | `APP_IS_LOCALHOST` | 分支逻辑需逐处确认 |
| `tx-service-url` | `https://apis.map.qq.com` | `tx_service_url` | `APP_TX_SERVICE_URL` | |
| `roadPathUrl` | `http://36.200.30.117:8080` | `road_path_url` | `APP_ROAD_PATH_URL` | |
| `kafka.bootstrap-servers` | `127.0.0.1:9092` | `kafka.bootstrap_servers` | `APP_KAFKA__BOOTSTRAP_SERVERS` | |
| `kafka.topic.snapshot-flow` | `ods-rt-szdn-snapshot-flow` | `kafka.topic.snapshot_flow` | `APP_KAFKA__TOPIC__SNAPSHOT_FLOW` | |
| `kafka.topic.snapshot-flow-dlq` | `ods-rt-szdn-snapshot-flow-dlq` | `kafka.topic.snapshot_flow_dlq` | `APP_KAFKA__TOPIC__SNAPSHOT_FLOW_DLQ` | |
| `kafka.consumer.group-id` | `snapshot-flow-consumer-group` | `kafka.consumer.group_id` | `APP_KAFKA__CONSUMER__GROUP_ID` | |
| `kafka.consumer.enable-auto-commit` | `false` | `kafka.consumer.enable_auto_commit` | `APP_KAFKA__CONSUMER__ENABLE_AUTO_COMMIT` | |
| `kafka.consumer.auto-offset-reset` | `earliest` | `kafka.consumer.auto_offset_reset` | `APP_KAFKA__CONSUMER__AUTO_OFFSET_RESET` | |
| `kafka.consumer.max-poll-records` | `500` | `kafka.consumer.max_poll_records` | `APP_KAFKA__CONSUMER__MAX_POLL_RECORDS` | |
| `kafka.consumer.max-poll-interval-ms` | `300000` | `kafka.consumer.max_poll_interval_ms` | `APP_KAFKA__CONSUMER__MAX_POLL_INTERVAL_MS` | |
| `kafka.consumer.fetch-max-bytes` | `52428800` | `kafka.consumer.fetch_max_bytes` | `APP_KAFKA__CONSUMER__FETCH_MAX_BYTES` | |
| `kafka.consumer.session-timeout-ms` | `60000` | `kafka.consumer.session_timeout_ms` | `APP_KAFKA__CONSUMER__SESSION_TIMEOUT_MS` | |
| `kafka.producer.acks` | `all` | `kafka.producer.acks` | `APP_KAFKA__PRODUCER__ACKS` | |
| `kafka.producer.retries` | `3` | `kafka.producer.retries` | `APP_KAFKA__PRODUCER__RETRIES` | |
| `kafka.listener.ack-mode` | `manual_immediate` | `kafka.listener.ack_mode` | `APP_KAFKA__LISTENER__ACK_MODE` | |
| `kafka.listener.concurrency` | `3` | `kafka.listener.concurrency` | `APP_KAFKA__LISTENER__CONCURRENCY` | |
| `elasticsearch.host` | `127.0.0.1` | `elasticsearch.host` | `APP_ELASTICSEARCH__HOST` | |
| `elasticsearch.port` | `9200` | `elasticsearch.port` | `APP_ELASTICSEARCH__PORT` | |
| `elasticsearch.index` | `snapshot-flow` | `elasticsearch.index` | `APP_ELASTICSEARCH__INDEX` | |
| `idempotent.redis.prefix` | `snapshot:flow:idempotent_` | `idempotent.redis.prefix` | `APP_IDEMPOTENT__REDIS__PREFIX` | |
| `idempotent.redis.expire-time` | `86400` | `idempotent.redis.expire_time` | `APP_IDEMPOTENT__REDIS__EXPIRE_TIME` | 秒 |
| `snapshot.flow.sharding.enabled` | `true` | `snapshot.flow.sharding.enabled` | `APP_SNAPSHOT__FLOW__SHARDING__ENABLED` | **当前无代码读取，属死配置** |
| `snapshot.flow.sharding.table-prefix` | `ods_rt_szdn_snapshot_flow_` | `snapshot.flow.sharding.table_prefix` | `APP_SNAPSHOT__FLOW__SHARDING__TABLE_PREFIX` | 同上 |
| `snapshot.flow.sharding.sharding-field` | `snapshottime` | `snapshot.flow.sharding.sharding_field` | `APP_SNAPSHOT__FLOW__SHARDING__SHARDING_FIELD` | 同上 |
| `snapshot.flow.sharding.sharding-type` | `month` | `snapshot.flow.sharding.sharding_type` | `APP_SNAPSHOT__FLOW__SHARDING__SHARDING_TYPE` | 同上 |
| `spring.datasource.druid.master.url` | `jdbc:p6spy:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true` | `database.url` | `APP_DATABASE__URL` | Rust 使用 `mysql://...`，参数逐项对齐 |
| `spring.datasource.druid.master.username` | `root` | `database.username` | `APP_DATABASE__USERNAME` | |
| `spring.datasource.druid.master.password` | `root` | `database.password` | `APP_DATABASE__PASSWORD` | 部署时覆盖 |
| `spring.datasource.druid.initialSize` | `5` | `database.pool.initial_size` | `APP_DATABASE__POOL__INITIAL_SIZE` | sqlx 无 initial；启动时预热连接 |
| `spring.datasource.druid.minIdle` | `10` | `database.pool.min_idle` | `APP_DATABASE__POOL__MIN_IDLE` | |
| `spring.datasource.druid.maxActive` | `200` | `database.pool.max_connections` | `APP_DATABASE__POOL__MAX_CONNECTIONS` | sqlx `max_connections=200` |
| `spring.datasource.druid.maxWait` | `60000` | `database.pool.acquire_timeout_ms` | `APP_DATABASE__POOL__ACQUIRE_TIMEOUT_MS` | |
| `spring.datasource.druid.connectTimeout` | `30000` | `database.pool.connect_timeout_ms` | `APP_DATABASE__POOL__CONNECT_TIMEOUT_MS` | |
| `spring.datasource.druid.socketTimeout` | `60000` | `database.pool.socket_timeout_ms` | `APP_DATABASE__POOL__SOCKET_TIMEOUT_MS` | |
| `spring.datasource.druid.validationQuery` | `SELECT 1 FROM DUAL` | `database.pool.validation_query` | `APP_DATABASE__POOL__VALIDATION_QUERY` | sqlx `test_before_acquire` |
| `spring.datasource.druid.statViewServlet.enabled` | `true` | — | — | 不迁移 |
| `spring.datasource.druid.statViewServlet.login-username` | `druidUser` | — | — | 不迁移 |
| `spring.datasource.druid.statViewServlet.login-password` | 见 yml | — | — | 不迁移 |
| `cdc.kafka.bootstrap-servers` | `localhost:9092` | `cdc.kafka.bootstrap_servers` | `APP_CDC__KAFKA__BOOTSTRAP_SERVERS` | 默认值来自类字段 |
| `cdc.kafka.consumer-group-id` | `snapshot-flow-cdc-group` | `cdc.kafka.consumer_group_id` | `APP_CDC__KAFKA__CONSUMER_GROUP_ID` | |
| `cdc.kafka.topic` | `snapshot-flow-cdc` | `cdc.kafka.topic` | `APP_CDC__KAFKA__TOPIC` | |
| `cdc.kafka.auto-commit` | `true` | `cdc.kafka.auto_commit` | `APP_CDC__KAFKA__AUTO_COMMIT` | |
| `cdc.kafka.auto-commit-interval` | `1000` | `cdc.kafka.auto_commit_interval` | `APP_CDC__KAFKA__AUTO_COMMIT_INTERVAL` | ms |
| `cdc.kafka.session-timeout` | `30000` | `cdc.kafka.session_timeout` | `APP_CDC__KAFKA__SESSION_TIMEOUT` | ms |
| `cdc.kafka.concurrency` | `3` | `cdc.kafka.concurrency` | `APP_CDC__KAFKA__CONCURRENCY` | |
| `cdc.es-sync.enabled` | `true` | `cdc.es_sync.enabled` | `APP_CDC__ES_SYNC__ENABLED` | 写入被注释，实际无效 |
| `cdc.es-sync.batch-size` | `500` | `cdc.es_sync.batch_size` | `APP_CDC__ES_SYNC__BATCH_SIZE` | |
| `cdc.es-sync.batch-interval` | `5000` | `cdc.es_sync.batch_interval` | `APP_CDC__ES_SYNC__BATCH_INTERVAL` | ms |
| `cdc.es-sync.async-threads` | `2` | `cdc.es_sync.async_threads` | `APP_CDC__ES_SYNC__ASYNC_THREADS` | |
| `cdc.retry.max-attempts` | `3` | `cdc.retry.max_attempts` | `APP_CDC__RETRY__MAX_ATTEMPTS` | |
| `cdc.retry.interval` | `1000` | `cdc.retry.interval` | `APP_CDC__RETRY__INTERVAL` | ms |
| `cdc.retry.multiplier` | `2.0` | `cdc.retry.multiplier` | `APP_CDC__RETRY__MULTIPLIER` | |
| `cdc.retry.max-interval` | `30000` | `cdc.retry.max_interval` | `APP_CDC__RETRY__MAX_INTERVAL` | ms |
| `sharding.tables.*` | 空 | `sharding.tables.*` | — | 无配置，走默认月度策略；相关同步服务为死代码 |
| Quartz 默认 | RAM、10 线程 | `quartz.thread_count` | `APP_QUARTZ__THREAD_COUNT` | 与 Spring Boot 默认对齐 |
| `logback` 路径 | `/home/ruoyi/logs` | `log.dir` | `APP_LOG__DIR` | 文件滚动/级别对齐 |

> 环境变量名是本阶段提出的**约定**，阶段二会逐项落实到 `Config` 结构体与 `.env.example`。如甲方已有部署脚本使用固定变量名，请提前给出。

---

## D9. 不可 1:1 直接翻译的阻塞点与替代方案

| # | Java 机制/用法 | 为什么不能照搬 | Rust 替代方案 | 行为风险 |
|---|---|---|---|---|
| 1 | Spring DI、`@Autowired`、`@ComponentScan`、`@Bean`、`SpringUtils.getBean` | Rust 无运行时容器与反射注入 | 组合根 `main` 显式构造；`AppState` 注入 axum `State`；需要替换实现时用 trait | 低；依赖错误提前到编译期 |
| 2 | `@RestControllerAdvice` + 异常继承体系 | 无异常、无 AOP | `AppError` 枚举 + `IntoResponse`；所有 handler 返回 `Result<_, AppError>` | 中；需逐条对齐错误码/文案/HTTP 状态 |
| 3 | `@PreAuthorize("@ss.hasPermi('...')")` 284 处 | SpEL + 运行时方法拦截 | 路由元数据 `permission` + 统一守卫；权限字符串来自附录 B | 中；漏迁会导致越权或误拒 |
| 4 | `@Log` AOP 239 处 | 运行时切面 | 路由元数据 + 中间件异步写 `sys_oper_log` | 中；字段截断、IP/UA/参数序列化需逐项对齐 |
| 5 | `@DataScope` 3 处 | 切面改写入参 `params.dataScope`，MyBatis XML 拼 SQL | 服务层显式构造条件并绑定参数 | 高；SQL 语义与角色数据权限必须逐条比对 |
| 6 | `@Transactional` 159 处 | 注解式代理、传播行为、仅 RuntimeException 回滚 | `sqlx::Transaction` 显式包裹；每个写路径明确 commit/rollback | 高；嵌套调用、异步、Kafka 消费内事务需单独核对 |
| 7 | MyBatis XML 动态 SQL（481 条、`<if>/<foreach>/<where>/<sql>`） | Rust 无 MyBatis 运行时 | SQLx `QueryBuilder` 或手写条件拼接 + 绑定；动态表名用白名单拼接标识符 | 高；`${}` 注入点、`find_in_set`、`WITH ROLLUP`、`LIMIT offset,size` 需逐条复刻 |
| 8 | PageHelper `startPage()` 100 处 | ThreadLocal 拦截下一条 SQL 自动改写 | 显式 `limit/offset` + `count` 查询；排序字段白名单 | 高；`count=countSql` 的 count 语句、`total=0` 行为、`order by` 注入防护需对齐 |
| 9 | MyBatis-Plus `BaseMapper` 43 个 + `ASSIGN_ID` | 运行时代码生成/雪花 ID | 手写 CRUD SQL；实现同参数雪花算法（epoch、位宽） | 中；主键生成规则不一致会导致跨系统 ID 冲突 |
| 10 | FastJson2 `WriteClassName` + `@type` | Rust serde 默认无类型信息 | 自定义序列化器复刻 `@type`；或切换时清空相关 key | **高**；滚动发布期间 Java/Rust 共享 Redis 会反序列化失败 |
| 11 | jjwt 0.9.1 HS512 secret 处理 | 旧版 jjwt 对 secret 做 base64 解码并按 4 字符截断 | 按 Java 实际签名字节复刻；用固定 token 做交叉验证 | **高**；否则所有存量 token 失效 |
| 12 | `HttpSession.getId()` 生成 `sessionId` | Rust 无 Servlet 会话 | 按 Tomcat 格式合成 32 位大写十六进制并缓存在请求上下文 | 低；仅日志/会话标识用途 |
| 13 | Quartz 反射 `invoke_target` | Rust 无反射调用任意方法 | `match` 注册表：字符串 → 函数指针；未知 target 记错并跳过 | 高；需生产 `sys_job` 数据 |
| 14 | `@Scheduled` | 依赖 `@EnableScheduling`（当前缺失） | **用户决策启用**：6 个方法全部注册，cron 与注解一致 | 中；需验证与 Quartz 任务不重复 |
| 15 | Servlet Filter（XSS、Repeatable、TraceId） | Servlet API | tower 中间件 + `http_body_util` 缓冲/重放 | 中；XSS 清洗规则需逐字符对齐 |
| 16 | `HashMap` 响应体（`AjaxResult extends HashMap`） | Jackson 的 Map 顺序即插入顺序 | 自定义 `AjaxResult` 序列化，字段顺序 `msg → code → data`（构造顺序） | 中；前端若依赖 key 顺序会受影响 |
| 17 | `@JsonFormat` 96 处、`@JsonIgnore`、`@JsonInclude(NON_EMPTY)` | 注解运行时反射 | serde 属性 + 自定义日期模块；逐字段标注 | 中；日期格式/空值省略必须逐字段核对 |
| 18 | `BeanUtils.copyProperties` 大量使用 | 运行时反射按名复制 | 显式 `From/Into` 或宏；字段名不一致处逐个处理 | 中；漏字段会导致数据丢失 |
| 19 | Excel/POI/EasyPOI 模板导出 | JVM 库与模板 | rust_xlsxwriter/calamine；模板文件原样复用并逐单元格校验 | 中；样式/合并单元格/公式可能不完美 |
| 20 | Velocity 代码生成 | JVM 模板引擎 | minijinja/tera + 同模板；生成物需做快照对比 | 中；换行/缩进/转义差异 |
| 21 | ShardingSphere 逻辑表 | 中间件代理 JDBC | **用户决策启用**：仓储层按 `snapshottime`/`record_time` 路由到物理表；无分片键时广播 | 高；物理表覆盖 2025–2099，需按 `information_schema` 实际存在表过滤 |
| 22 | 手工跨月分表查询 | 逐表 COUNT/LIMIT + 内存排序 | 逐表查询 + 归并；保留“历史月近似 COUNT、当前月精确 COUNT”的差异 | 高；`total` 可能不精确，前端分页表现需一致 |
| 23 | 动态表名 `${tableName}` | SQL 标识符不能绑定参数 | 表白名单/正则校验后拼接 | 高；必须防止 SQL 注入 |
| 24 | Spring Kafka 批量监听/手动 ack | 框架封装 | rust-rdkafka 手动 `commit`；批次成功才提交 | 高；重复消费/丢失边界 |
| 25 | ES RestHighLevelClient | JVM 客户端 | `elasticsearch` crate 或 REST；DSL 原样 | 中；字段映射/日期格式 |
| 26 | AWS S3 SDK / MinIO | JVM SDK | aws-sdk-s3；path-style 配置 | 低；`/oss` 端点默认不启用 |
| 27 | 阿里云短信 SDK | JVM SDK + 专有签名 | reqwest + ACS3 签名；空模板行为保持一致 | 中；签名算法易错 |
| 28 | OSHI / UserAgentUtils | JVM 系统库 | `sysinfo` / UA 解析 crate；字段名和取值映射需对齐 | 低 |
| 29 | kaptcha 图片 | Java 绘图 | `captcha` crate；只保证语义，不保证像素一致 | 低；前端只展示图片 |
| 30 | `ThreadLocal`（`AuthenticationContextHolder`、`TraceContext`、PageHelper） | 异步/线程池下易泄漏 | 请求扩展 + `tracing` span；禁止跨 `.await` 持有 | 中；必须逐处审计 |
| 31 | `@Async`（未启用） | 无 `@EnableAsync`，实际同步 | 保持同步；不要“顺手”改成异步 | 中；短信失败抛出时机不同 |
| 32 | `@PostConstruct` 预热 | 生命周期回调 | `main` 启动序列；失败即退出 | 中；启动顺序影响缓存一致性 |
| 33 | Druid/P6Spy SQL 日志 | JDBC 代理 | sqlx `tracing` + 慢 SQL 计时中间件 | 低；日志格式不要求逐字符 |
| 34 | WAR 部署入口 `RuoYiServletInitializer` | Servlet 容器 | 单二进制；不迁移 | 无 |
| 35 | Spring profiles | 运行时 profile | `APP_PROFILE` + 配置文件选择 | 低 |
| 36 | `RuoYiConfig` 静态字段 | 全局可变静态 | `AppState` 中的不可变配置 | 低 |
| 37 | `SecurityUtils.getLoginUser()` 静态取当前用户 | ThreadLocal | `Extension<CurrentUser>` 提取器 | 低 |
| 38 | `BaseController.startPage()` / `getDataTable()` | 父类工具方法 | 显式分页参数 + `TableDataInfo` 构造器 | 中；`PageInfo` 的 total 来源 |
| 39 | 文件下载 `HttpServletResponse` 流式写出 | Servlet API | axum `Body::from_stream` / `ServeFile`；Content-Disposition 对齐 | 中；文件名编码 |
| 40 | `@Validated` / JSR-303 | 运行时校验 | `validator` crate + serde；错误文案逐条对齐 | 中；字段顺序影响首条错误 |
| 41 | **双 `@RestControllerAdvice`（已实测解决）**：`GlobalExceptionHandler`（framework）与 `GlobalExceptionTraceHandler`（system）均无 `@Order`，都能处理 `Exception`/`BindException`/`MethodArgumentNotValidException`/`MethodArgumentTypeMismatchException`/`HttpRequestMethodNotSupportedException` | Spring 按 advice Bean 顺序取第一个匹配 | **实测结论**：`GlobalExceptionHandler` 优先且含 `Exception` 兜底，`GlobalExceptionTraceHandler` 被完全遮蔽；Rust 只实现 `AjaxResult` + HTTP 200（404 除外） | 已消除；详见附录 E |

---

## D10. 需要在阶段二前确认的事项

1. **数据库 DDL**：仓库无完整建表语句，无法恢复索引、外键、字符集、默认值。需要生产库 `SHOW CREATE TABLE`（78 张业务表）或 mysqldump `--no-data`。
2. **`sys_job` 数据**：Quartz 实际任务完全由该表驱动，必须导出。
3. **Redis 兼容策略**：是否要求 Java/Rust 灰度共存？若是，必须复刻 FastJson2 `@type`；若否，可在切换时清空 `login_tokens:*`、`sys_config:*`、`sys_dict:*` 等缓存。
4. **`/oss/**` 与 OSS（已决策）**：默认端点不注册；`oss.info=true` 时注册。
5. **`@Scheduled` 与 ShardingSphere（已决策）**：Rust 侧启用（6 个定时任务 + 逻辑表路由）。
6. **死代码（已决策）**：全部照样迁移，保持 public 方法行为。
7. **环境变量命名**：确认 D8.1 的 `APP_` + `__` 约定是否与现有部署脚本兼容。
8. ~~**双异常 advice 顺序**~~ **已解决**：启动 Java 实测，`GlobalExceptionHandler` 优先、`GlobalExceptionTraceHandler` 完全遮蔽，`MonitorResponse` 从未出现；Rust 只迁移 `AjaxResult` 错误模型。详见 `05-runtime-probes.md`。
