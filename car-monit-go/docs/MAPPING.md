# Java → Go 全局映射表

本文件对应 `java-to-go-refactor-prompt.md` 要求的「全局映射表 + 目录映射 + 逐文件实现锚点」。
逐文件锚点写在各 Go 文件头部的 `// JAVA 对照:` 注释中；本表提供总览与索引。

## 0. 技术栈总表（先看这一张）

| 维度 | Java 侧用法 | Go 侧方案 | 关键差异 / 阅读提示 |
|---|---|---|---|
| Web 框架 | Spring MVC `@RestController` + `@RequestMapping` | Gin v1.10 | 路由在 `internal/router` 与各模块 `register.go` 显式注册；没有注解扫描。中间件是 `gin.HandlerFunc`，不是 AOP 切面 |
| 依赖注入 | Spring IoC `@Autowired` / `@Resource` | `internal/app.App` 显式构造 | `main` 按顺序创建 DB/Redis/Tokens/Auth；模块通过构造参数拿依赖，不要找 `@ComponentScan` |
| ORM / 数据访问 | MyBatis-Plus + Mapper XML | GORM v2（`Raw`/`Exec` 为主） | 动态 SQL 由 Go 显式拼接占位符；分页不再由拦截器改写 SQL，需手写 COUNT + LIMIT/OFFSET |
| 事务 | `@Transactional` | `db.Transaction(func(tx *gorm.DB) error {...})` | 返回 error 即回滚；注意事务内不要使用带超时的外层 ctx 做长操作 |
| 配置 | `application.yml` + `@Value`/`@ConfigurationProperties` | Viper + `mapstructure` | 无 JSR-303；校验集中在 `LoadConfig`。含点号键（`logging.level.com.ruoyi`）会成为嵌套 map |
| 日志 | SLF4J + Logback | `log/slog` | 无 logback.xml；级别由 `logging.level` 推导；MDC → context 中的 traceId |
| 缓存 | Spring Cache 注解 / RedisTemplate | `internal/cache`（go-redis v9） | 无 `@Cacheable`，读写显式调用；键名与 Java 常量保持一致 |
| 消息队列 | Spring Kafka `@KafkaListener` | kafka-go（已接线，`kafka.enabled` 控制） | 显式消费循环、批处理后提交 offset、失败重试后进 DLQ；消费者随进程优雅停机 |
| 搜索引擎 | Elasticsearch Java Client | REST `_bulk`/`_doc`（`internal/stream/es`） | 以 `bigId` 为文档 ID；只由 Kafka 链路与同步任务写，`elasticsearch.enabled` 控制 |
| HTTP 客户端 | RestTemplate / Forest | `net/http` + 自定义 timeout | 每个出站请求必须带 context 与超时；禁止无超时的默认 client |
| 定时任务 | Quartz Scheduler | robfig/cron/v3 | 6 段 cron 近似；无 Quartz 集群锁/错过补偿，需要时用 Redis/DB 锁补 |
| 校验 | JSR-303 `@NotBlank`/`@Size` + `@Valid` | 手写校验 + 统一中文消息 | 错误消息必须与 Java 一致；不要用 gin binding 默认英文消息 |
| 序列化 | Jackson（含 `@JsonFormat`） | `encoding/json` + `web.DateTime` | 时间统一 `yyyy-MM-dd HH:mm:ss`；`AjaxResult` 用 `JavaMap` 复刻 HashMap 键序 |
| Excel | EasyExcel 注解 | excelize/v2 | 列顺序/表头保持一致；样式不追求逐像素一致 |
| 身份认证 | Spring Security + JJWT 0.9.1 | 自研中间件 + golang-jwt/v5 | JWT 仅承载 `login_user_key`；登录态在 Redis，支持自动续期 |
| 权限 | `@PreAuthorize("@ss.hasPermi('x')")` | `middleware.Perm("x")` | `*:*:*` 为超管；多个权限之间为「任一满足」 |
| 参数绑定 | `@RequestBody` / `@RequestParam` / `@PathVariable` | `ShouldBindJSON` / `c.Query` / `c.Param` | 绑定失败同样返回 HTTP 200 + 业务 code |
| AOP 能力 | 日志/限流/幂等切面 | 显式中间件 | 注册路由时选择挂载 `OperLog` / `RepeatSubmit` / `RateLimit` |
| 线程池 / 异步 | `AsyncManager` / `@Async` | goroutine + 超时 context | goroutine 必须自带超时与 recover 边界；进程退出时要能收敛 |
| 构建/检查 | Maven | `go mod` + `go build` + `go vet` | 生产建议追加 `golangci-lint`（errcheck/staticcheck）；本机仅验证 build/vet |

## 1. 目录映射

| Java 目录/资源 | Go 目录 | 说明 |
|---|---|---|
| `ruoyi-admin/src/main/java/com/ruoyi/RuoYiApplication.java` | `cmd/server/main.go` | 进程入口、依赖装配、优雅停机 |
| `ruoyi-admin/.../web/controller/**` | `internal/modules/**`、`internal/handler/**` | 78 个控制器按业务域拆分 |
| `ruoyi-admin/.../web/util/**` | `internal/auth`、各模块 | CommonUtil、ExcelUtil 等工具 |
| `ruoyi-framework/.../config/**` | `internal/config`、`internal/middleware`、`internal/router` | 配置、安全链路、Web 配置 |
| `ruoyi-framework/.../web/service/**` | `internal/auth` | 登录、令牌、权限 |
| `ruoyi-framework/.../security/**` | `internal/middleware/security.go`、`internal/handler/auth.go` | 过滤器与登出处理器 |
| `ruoyi-framework/.../interceptor/**`、`aspectj/**` | `internal/middleware/ops.go` | 防重复提交、限流、操作日志 |
| `ruoyi-system/.../service/impl/**` | 各 `internal/modules/**` | 业务服务 |
| `ruoyi-system/src/main/resources/mapper/**` | 各 `internal/modules/**` | 原生参数化 SQL |
| `ruoyi-quartz/**` | `internal/modules/quartz` | 定时任务（robfig/cron 替代 Quartz） |
| `ruoyi-common/.../core/domain/**` | `internal/web`、`internal/model` | 响应信封、分页、实体 |
| `ruoyi-common/.../utils/**` | `internal/web`、`internal/auth`、各模块 | 日期、IP、文件、UUID |
| `ruoyi-admin/src/main/resources/application*.yml` | `configs/config.yaml` | 配置键一一对应（另有 `database`/`redis` 原生段） |
| `ruoyi-admin/src/main/resources/logback.xml` | `internal/logx/logger.go` | slog + `logging.level` 推导 |
| `ruoyi-admin/.../resources/i18n/messages.properties` | 各模块内联中文常量 | 单语言部署，未建 i18n 框架 |

## 2. 基础设施类映射

| Java 类 | Go 文件 | 关键差异 |
|---|---|---|
| `RuoYiApplication` | `cmd/server/main.go` | 显式依赖装配；`signal.Notify` 优雅停机 |
| `AjaxResult`（extends HashMap） | `internal/web/javamap.go` + `response.go` | 复刻 HashMap 桶顺序，保证 JSON 键序与 Java 一致 |
| `TableDataInfo` | `internal/web/response.go` | `total,rows,code,msg` 字段序保持 |
| `R` | `internal/web/response.go` | `code,msg,data` |
| `BaseEntity` | `internal/model/base.go` | `params` 支持；`searchValue` 不序列化 |
| `PageDomain` / `TableSupport` / `PageUtils` | `internal/web/pagination.go` | PageHelper ThreadLocal → 显式 count + LIMIT/OFFSET |
| `ServiceException` / `GlobalExceptionHandler` | `internal/web/errors.go` | 异常穿透 → error 返回值 |
| `SecurityUtils` | `internal/auth/context.go` | ThreadLocal → `gin.Context` + `context.Context` |
| `TokenService` | `internal/auth/token.go` | JJWT → golang-jwt/v5；Redis 键名保持不变 |
| `SysLoginService` / `UserDetailsServiceImpl` / `SysPermissionService` | `internal/auth/service.go` | AuthenticationManager → 显式 bcrypt 校验 |
| `SysPasswordService` | 未实现 | 该 Bean 在 Java 中未被使用（死代码），登录无重试锁定 |
| `SecurityConfig` / `JwtAuthenticationTokenFilter` / `PermissionService` | `internal/middleware/security.go` | 过滤器链 → gin 中间件；`*:*:*` 超级权限 |
| `AuthenticationEntryPointImpl` | `internal/web/errors.go` + `middleware/security.go` | HTTP 200 + code 401 |
| `LogoutSuccessHandlerImpl` | `internal/handler/auth.go` | `/logout` 始终返回「退出成功」 |
| `CaptchaController` / `CaptchaConfig` / `KaptchaTextCreator` | `internal/auth/captcha.go` + `internal/handler/auth.go` | Kaptcha JPEG → 内置点阵字体 JPEG；响应结构不变 |
| `SysMenuServiceImpl` | `internal/service/menusvc/menu.go` | 菜单树 / RouterVo 规则逐行对齐 |
| `DruidConfig` / `application-druid.yml` | `internal/database/database.go` | Druid + P6Spy → database/sql 池 + GORM Logger |
| `RedisCache` | `internal/cache/redis.go` | RedisTemplate → go-redis v9 |
| `AsyncManager` / `AsyncFactory` | `internal/auth/service.go`（goroutine） | 异步线程池 → goroutine + 3s 超时 |
| `RepeatSubmitInterceptor` | `internal/middleware/ops.go` | 相同语义（Redis 键 + 参数摘要） |
| `RateLimiterAspect` | `internal/middleware/ops.go` | Redis INCR + TTL |
| `LogAspect`（操作日志） | `internal/middleware/ops.go` | 显式路由中间件 |
| `XssFilter` | `internal/middleware/common.go` | query 清洗（与 Java 一致仅处理 query） |
| `CorsFilter` / `ResourcesConfig` | `internal/middleware/common.go` | 反射 Origin + credentials |
| `ExcelUtil` | 各模块内使用 `github.com/xuri/excelize/v2` | 注解驱动 → 显式列定义 |
| `FileUtils` / `FileUploadUtils` | `internal/modules/ops` | 路径穿越校验保持一致 |
| Quartz `Scheduler` / `ScheduleUtils` | `internal/modules/quartz` | robfig/cron/v3（Quartz 语义近似，见 DIFF） |
| `SqlUtil.escapeOrderBySql` | `internal/web/pagination.go` | 列名白名单正则 |
| `AddressUtils`（ip2region） | `internal/auth/token.go` | 未内置离线库：内网 IP 返回「内网IP」，其余为空 |

## 3. 控制器 → Go 包

所有控制器默认挂在 `internal/router.Registry.Authed`（JWT 认证后）；匿名端点显式挂 `reg.Engine`。

### 3.1 认证与核心（internal/handler）

| Java 控制器 | 路径 | Go |
|---|---|---|
| `SysLoginController` | `/login` `/getInfo` `/getRouters` | `internal/handler/auth.go` |
| `CaptchaController` | `/captchaImage` | `internal/handler/auth.go` |
| `SysIndexController` | `/` | `internal/handler/auth.go` |
| Spring Security `LogoutFilter` | `/logout` | `internal/handler/auth.go` |

### 3.2 系统管理（internal/modules/system、internal/modules/systemaux）

| Java 控制器 | 路径前缀 | Go 包 |
|---|---|---|
| `SysUserController` | `/system/user` | `internal/modules/system` |
| `SysRoleController` | `/system/role` | `internal/modules/system` |
| `SysMenuController` | `/system/menu` | `internal/modules/system` |
| `SysDeptController` | `/system/dept` | `internal/modules/system` |
| `SysPostController` | `/system/post` | `internal/modules/system` |
| `SysConfigController` | `/system/config` | `internal/modules/systemaux` |
| `SysDictTypeController` | `/system/dict/type` | `internal/modules/systemaux` |
| `SysDictDataController` | `/system/dict/data` | `internal/modules/systemaux` |
| `SysNoticeController` | `/system/notice` | `internal/modules/systemaux` |
| `SysProfileController` | `/system/user/profile` | `internal/modules/systemaux` |
| `SysIndexMenuController` | `/system/indexmenu` | `internal/modules/systemaux` |
| `SysFileController` | `/system/file` | `internal/modules/systemaux` |
| `SysUpgradeInfoController` | `/system/upgradeInfo` | `internal/modules/systemaux` |

### 3.3 监控与工具（internal/modules/ops、internal/modules/quartz）

| Java 控制器 | 路径前缀 | Go 包 |
|---|---|---|
| `CacheController` | `/monitor/cache` | `internal/modules/ops` |
| `ServerController` | `/monitor/server` | `internal/modules/ops` |
| `SysLogininforController` | `/monitor/logininfor` | `internal/modules/ops` |
| `SysOperlogController` | `/monitor/operlog` | `internal/modules/ops` |
| `SysUserOnlineController` | `/monitor/online` | `internal/modules/ops` |
| `CommonController` | `/common` | `internal/modules/ops` |
| `DownTemplateController` | `/downTemplate` | `internal/modules/ops` |
| `TestController` | `/test/user` | `internal/modules/ops` |
| `SysJobController` | `/monitor/job` | `internal/modules/quartz` |
| `SysJobLogController` | `/monitor/jobLog` | `internal/modules/quartz` |

### 3.4 车辆监管（internal/modules/manager、internal/modules/manager）

| Java 控制器 | 路径前缀 | Go 包 |
|---|---|---|
| `CarInfoController` | `/manager/carinfo` | `internal/modules/manager` |
| `CarFeeRecordController` | `/manager/feerecord` | `internal/modules/manager` |
| `CarExceptRecordController` | `/manager/exceptrecord` | `internal/modules/manager` |
| `CarQueryLogController` | `/manager/querylog` | `internal/modules/manager` |
| `CarSplitRecordController` | `/manager/splitrecord` | `internal/modules/manager` |
| `CarWhiteInfoController` | `/manager/whiteinfo` | `internal/modules/manager` |
| `CarWarningInfoController` | `/manager/carwarning` | `internal/modules/manager` |
| `CarWarningRuleController` | `/manager/warningrule` | `internal/modules/manager` |
| `CarAduitFreeController` | `/manager/aduitfree` | `internal/modules/manager` |
| `CarConfimFreeController` | `/manager/confimfree` | `internal/modules/manager` |
| `CarRouteDetailController` | `/manager/routedetail` | `internal/modules/manager` |
| `CarRouteInfoController` | `/manager/routeinfo` | `internal/modules/manager` |
| `CarSuspiciousController` | `/manager/suspicious` | `internal/modules/manager` |
| `CarSuspiciousBackController` | `/manager/carsuspiciousback` | `internal/modules/manager` |
| `CarSuspiciousCheckController` | `/manager/suspiciouscheck` | `internal/modules/manager` |
| `CarTrackInfoController` | `/manager/cartrackinfo` | `internal/modules/manager` |
| `GantryCarController` | `/manager/gantrycar` | `internal/modules/manager` |
| `GantryTradeInfoController` | `/manager/gantrytrade` | `internal/modules/manager` |
| `BigScreenController` | `/manager/bigScreen` | `internal/modules/manager` |
| `BussTestController` | `/manager/busstest` | `internal/modules/manager` |

### 3.5 数据接入/基础数据（internal/modules/base）

> 26 个 Java 控制器（ODS/DWD/几何/服务区/预警配置/CDC/Kafka 管理）迁移到 `internal/modules/base`。

| Java 控制器 | 路径前缀 | Go 包 |
|---|---|---|
| `OdsCxztFwqcllsController` | `/manager/fwqclls` | `internal/modules/base` |
| `OdsLwzxsfsjFeeGantryFusion01Controller` | `/base/feeGantry` | `internal/modules/base` |
| `OdsLwzxsfsjFeeRecords01Controller` | `/base/feerecords` | `internal/modules/base` |
| `OdsLwzxsfsjFeeStationEnter01Controller` | `/base/feeStationEnter` | `internal/modules/base` |
| `OdsLwzxsfsjFeeStationExit01Controller` | `/base/feestationexit` | `internal/modules/base` |
| `OdsRtSzdnSnapshotFlowAddcodeController` | `/base/snapshotflow` | `internal/modules/base` |
| `OdsRtSzdnSnapshotFlowProvcaptureAddcodeController` | `/base/provcapture` | `internal/modules/base` |
| `OdsRtSzdnSnapshotFlowStationcaptureAddcodeController` | `/base/stationcapture` | `internal/modules/base` |
| `OdsSzdnGantryController` | `/base/gantry` | `internal/modules/base` |
| `OdsSzdnGantryIpController` | `/base/gantryIp` | `internal/modules/base` |
| `OdsSzdnProvinceBorderVehicleWeightNewstructureController` | `/base/vehicleweight` | `internal/modules/base` |
| `OdsSzdnSectionController` | `/base/section` | `internal/modules/base` |
| `OdsSzdnTollController` | `/base/toll` | `internal/modules/base` |
| `OdsSzdnTollStationIpController` | `/base/tollStationIp` | `internal/modules/base` |
| `BaseConfigServiceAreaController` | `/base/configServiceArea` | `internal/modules/base` |
| `CarWarningConfigController` | `/base/config` | `internal/modules/base` |
| `CdcController` | `/base/cdc` | `internal/modules/base` |
| `DwdLcztFwqjcxxController` | `/base/fwqjcxx` | `internal/modules/base` |
| `DwdLcztSfsjcxxController` | `/base/sfsjcxx` | `internal/modules/base` |
| `DwdLcztSfzjcxxController` | `/base/sfzjcxx` | `internal/modules/base` |
| `GeometryController` | `/base/geometry` | `internal/modules/base` |
| `OdsYhglVBaseOrgController` | `/base/org` | `internal/modules/base` |
| `ZdataLocationDictController` | `/base/location` | `internal/modules/base` |
| `ZdataTrailFittingController` | `/base/fitting` | `internal/modules/base` |
| `ZdataTrailTracksController` | `/base/trailtracks` | `internal/modules/base` |

### 3.6 流程（internal/modules/flow）

| Java 控制器 | 路径前缀 | Go 包 |
|---|---|---|
| `FlowApplyInfoController` | `/flow/applyinfo` | `internal/modules/flow` |
| `FlowCurrentNodeController` | `/flow/currentnode` | `internal/modules/flow` |
| `FlowListController` | `/flow/flowlist` | `internal/modules/flow` |
| `FlowMessageDisposeController` | `/flow/messagedispose` | `internal/modules/flow` |
| `FlowMessageInfoController` | `/flow/messageinfo` | `internal/modules/flow` |
| `FlowNameController` | `/flow/flowname` | `internal/modules/flow` |
| `FlowTemplateController` | `/flow/flowtemplate` | `internal/modules/flow` |

## 4. 消息队列 / 搜索引擎 / 分表

> **归属更新（2026-11-08 数据面批次）**：Go 版本已接线 Kafka 消费 → MySQL 月度分表 → ES 索引，
> 并实现 `vehicleMonitoringTask` / `snapshotFlowSyncTask` / `shardingTableTask` 三个数据面任务。
> 实现集中在 `internal/modules/base/datasync*.go`，复用 `internal/stream/{kafka,es,idempotent,sharding}`。
>
> - **Kafka 消费**：`kafka.enabled=true` 时 `cmd/server/main.go` 启动消费者，批次交给
>   `DataSync.HandleSnapshotFlowBatch`；失败消息本地重试 3 次后进死信队列，offset 始终在批处理后提交。
> - **分表写入**：按 `snapshottime` 月份直接计算物理表（`ShardingTableUtil` 语义），写入前按需
>   `CREATE TABLE ... LIKE ods_rt_szdn_snapshot_flow_addcode`；INSERT 追加
>   `ON DUPLICATE KEY UPDATE big_id=big_id` 保证重试/重叠同步幂等。
> - **ES 索引**：`elasticsearch.enabled=true` 时以 `bigId` 为文档 ID 写 `_bulk`；失败只告警，
>   不回滚 MySQL（与 Java `batchSave` 一致）。
> - **GaussDB 同步**：通过 `snapshot.flow.sync.*` 配置的 HTTP 适配层读取 vehicleMonitor 的
>   `/base/snapshotflow/*`，不直连 GaussDB。**该项未在本地验证**（见 §4.1）。
> - **任务注册**：`vehicleMonitoringTask`、`snapshotFlowSyncTask`、`shardingTableTask` 已注册为
>   quartz 任务 Bean，`unmigratedTargets` 只剩 `trackTask.syncHistoryTrack`。

### 4.1 数据接入状态与未验证点

| Java 组件 | Go 目标 | 状态 |
|---|---|---|
| `SnapshotFlowKafkaConsumerV2` | `internal/stream/kafka` + `base.DataSync.HandleSnapshotFlowBatch` | 已接线；`kafka.enabled=false` 时不启动 |
| ES 索引写入 | `internal/stream/es` + `DataSync` | 已接线；`elasticsearch.enabled=false` 时不写 |
| 幂等键（Redis SETNX） | `internal/stream/idempotent` | 已接线；Redis 未初始化时消费者启动告警并降级为无幂等 |
| ShardingSphere 月分表规则 | `internal/stream/sharding` + `base.DataSync` | 已接线；分表按日期直接路由（不再依赖 ShardingSphere 逻辑表） |
| `ShardingTableTask` | `base.DataSync.PreCreateTables` / `shardingTableTask.*` | 已注册；Java 的 `@Scheduled` 因缺 `@EnableScheduling` 从未生效 |
| `vehicleMonitoringTask`（7 个方法） | `base.DataSync.Sync*Info` | 已注册，由现有 `sys_job` 记录（103~109、111）触发 |
| `snapshotFlowSyncTask`（6 个方法） | `base.DataSync.Sync*` | 已注册为任务 Bean；Java 侧同样未真正自动运行 |
| `trackTask.syncHistoryTrack` | — | **仍未迁移**（依赖 `ICarTrackInfoService`/`IGeometryService`），保存时拒绝 |

**未验证点（必须在联调环境复核）**：
1. `GET /base/snapshotflow/earliest-time` 与 `/base/snapshotflow/list` 的真实响应结构：
   当前按 Java `Date` / `TableDataInfo` 声明做兼容解析；本仓库没有 vehicleMonitor 实例。
2. ES 文档时间字段按 fastjson2 默认写成**毫秒时间戳**；若线上索引 mapping 期望日期字符串，
   需同步调整 `snapshotFlowESDoc`。
3. `section_list` 缓存改为“先删后写”（Java 是 `rightPushAll` 无限追加），需确认无其他组件依赖旧行为。
4. MySQL `TRUNCATE` 为 DDL 隐式提交，7 张基础表的“清空 + 重灌”在插入失败时仍会留下空表
   （与 Java 实际行为一致，日志会告警）。

**Java 下线前置条件**：在联调环境跑通上述 4 项，并用真实 Kafka/ES/GaussDB 流量完成一轮对拍。

