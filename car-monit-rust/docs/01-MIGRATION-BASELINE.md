# 阶段一交付：Java → Rust 迁移基线清单

> 迁移源：`D:\work\IdeaProjects\car-monit-backend-new`（RuoYi 3.8.7，Spring Boot 2.5.15，Java 8）
> 目标目录：`car-monit-rust`
> 执行依据：`car-monit-rust/java-to-rust-refactor-prompt.md`
> 状态：**阶段一、阶段二完成；尚未创建任何 Rust 实现代码**
> 生成日期：2026-10-31

阶段二交付见 [`02-JAVA-RUST-MAPPING.md`](02-JAVA-RUST-MAPPING.md)（11 个维度四列映射表）。本清单对应提示词要求的 6 个部分。明细分别落在 4 份附录中，本文给出结论、口径与迁移决策：

| 附录 | 文件 | 内容 |
|---|---|---|
| A | [`01-baseline/01-file-map.md`](01-baseline/01-file-map.md) | 696 个 Java 文件 → Rust 目标文件、职责、纯逻辑/框架契约分类 |
| B | [`01-baseline/02-endpoints.md`](01-baseline/02-endpoints.md) | 501 个 HTTP 端点、权限点、`@Log`、参数与返回、Java 方法 → Rust handler |
| C | [`01-baseline/03-data-layer.md`](01-baseline/03-data-layer.md) | 75 个 Mapper XML、481 条 SQL、表清单、动态标签、resultMap |
| D | [`01-baseline/04-config-middleware.md`](01-baseline/04-config-middleware.md) | 中间件、Redis/Kafka/ES/Quartz、鉴权、配置项、阻塞点 |
| E | [`01-baseline/05-runtime-probes.md`](01-baseline/05-runtime-probes.md) | **Java 运行时异常/响应实测**：双 advice 顺序、错误码、字段顺序 |
| — | [`01-baseline/schema.carmonitdb.local.sql`](01-baseline/schema.carmonitdb.local.sql) | 本地运行库 DDL 只读快照（84 张表，仅结构） |
| — | [`01-baseline/data.sys_job.local.sql`](01-baseline/data.sys_job.local.sql) | 本地 `sys_job` 数据快照（19 条任务） |
| — | [`01-baseline/inventory.json`](01-baseline/inventory.json) | 机器可读统计，供阶段二/三校验 |

---

## 0. 执行摘要

### 0.1 迁移体量

| 指标 | 数量 |
|---|---:|
| Java 源文件 | 696 |
| REST Controller | 79（另含 `BaseController` = 80 个 Controller 文件） |
| HTTP 端点 | 501 |
| Mapper XML | 75 |
| Mapper SQL 语句 | 481 |
| 表名（含 2 个解析误报 `id`、`information_schema`） | 80 → **78 张真实表/视图** |
| `@Transactional` | 159 |
| `startPage()` 分页调用 | 100 |
| `@PreAuthorize` 权限点 | 284 |
| `@Log` 操作日志 | 239 |
| `BaseMapper` 泛型 CRUD | 43 |
| 单元/集成测试 | **0** |

### 0.2 必须保持“无效”的运行时行为

以下能力在 Java 中**实际不生效**。除标注“用户已决策启用”的项外，Rust 侧如果“顺手修好”，就是行为漂移：

1. **`@Scheduled` 全部失效**：全仓库没有 `@EnableScheduling`，6 个定时方法从未执行。→ **用户决策：Rust 侧启用**（2026-10-31，见 0.5）。
2. **`@Async` 全部失效**：没有 `@EnableAsync`，短信等方法实际同步执行。
3. **ShardingSphere 未启用**：没有 `sharding.enabled`；`snapshot.flow.sharding.*` 配置无代码读取。→ **用户决策：Rust 侧启用逻辑表路由**（见 0.5）。
4. **CDC 的 ES 写入被注释**：`CdcSyncService` 只打日志；`/oss/**` 端点未注册（缺 `oss.info`）。
5. **Swagger 关闭、Druid 控制台被 `denyAll`**：不迁移为可用端点。

### 0.5 用户决策记录（2026-10-31）

| 事项 | 决策 | 对迁移的影响 |
|---|---|---|
| `@Scheduled`（6 个方法） | **需要生效** | Rust 注册 6 个定时任务，cron 与 Java 注解一致；不再视为死代码 |
| ShardingSphere | **需要生效** | Rust 以仓储层“逻辑表 → 物理表”路由复刻两条规则（快照流水按月、费用记录按日），默认 `sharding.enabled=true` |
| 死代码（8 个类） | **照样迁移** | `PartitionMappingCache`、`PartitionParallelQueryService`、`ShardingQueryService`、`ShardingSyncService`、`DataConsistencyService`、`ViewMaintenanceOptimizationService`、`ShardingSnapshotFlowMapper`、`ShardingConfig`/`ShardingTableTask` 全部移植为内部能力 |
| `/oss/**` | 按最佳实践：保持默认不注册，保留 `oss.info=true` 时注册的能力 | 默认行为与 Java 一致 |
| 环境变量 | 采用 `APP_` + `__` | — |
| 部署 | 单二进制 + Docker，健康检查 `/health` | `/health` 为新增端点，配置开关 `app.health_endpoint_enabled` 默认 true |
| 日志 | stdout + 滚动文件，tracing；OTel 默认关闭 | — |
| MySQL TLS | 保留 `useSSL=true` 语义，映射为可配置 `ssl-mode`（默认 PREFERRED，不校验证书） | 与 Java 实际行为一致 |

### 0.3 三条行为红线

1. **Redis 值格式**：Java 用 FastJson2 `WriteClassName` 写入 `@type`；Rust 直接 serde 会导致灰度期间 Java 反序列化失败。
2. **JWT 签名**：jjwt 0.9.1 对 secret 的 Base64/截断处理有历史怪癖；必须用固定 token 交叉验证。
3. **SQL 语义**：PageHelper 改写、MyBatis 动态 SQL、`${tableName}` 拼接、跨月近似 COUNT 必须逐条复刻，不能“优化”。

### 0.4 阶段一新增的高风险发现（已实测确认）

**双 `@RestControllerAdvice` 的胜者已确定**：`GlobalExceptionHandler`（framework）与 `GlobalExceptionTraceHandler`（system）都标注了 `@RestControllerAdvice`，均无 `@Order`，且都能处理 `Exception`/`BindException`/`MethodArgumentNotValidException`/`MethodArgumentTypeMismatchException`/`HttpRequestMethodNotSupportedException`。两者返回结构完全不同：

- `GlobalExceptionHandler` → `AjaxResult`，HTTP 200；
- `GlobalExceptionTraceHandler` → `MonitorResponse`（字段 `code,message,data,traceId,timestamp,datetime,cost`），并用 `@ResponseStatus` 返回 400/405/500。

**2026-10-31 启动原始 Java 服务实测（附录 E）结论**：`GlobalExceptionHandler` 实际优先，因其含 `Exception` 兜底处理器，`GlobalExceptionTraceHandler` 在本运行时被**完全遮蔽**——实测 12 类请求（未登录、404、405、非法 JSON、403、NPE、校验失败、类型不匹配、SQL 注入排序、业务异常、登录成功）中 `MonitorResponse` **从未出现**。

由此固定：

1. Rust 侧**只实现 `AjaxResult` 错误模型**，不迁移 `GlobalExceptionTraceHandler`/`MonitorResponse` 的任何 HTTP 状态分支。
2. 除 404 外，所有业务/鉴权/校验/运行异常均返回 **HTTP 200**，401/403 只是 body 内的 `code`。
3. 未匹配路由返回 Spring Boot 默认 `/error` JSON（`timestamp/status/error/path`，HTTP 404），且 Security 先于路由匹配——未登录访问不存在路径得到的是 401 而非 404。
4. 字段顺序也已实测（见 §2.2），Rust 需固定顺序，不能用 `HashMap`。
5. `SysUser` 的校验注解在源码中被注释，`{}` 会一路走到 NPE 返回 `{"msg":null,"code":500}`；**禁止在 Rust 侧补校验**。

---

## 1. 项目结构对照（对应要求 1）

### 1.1 源模块与 Rust 目标

| Maven 模块 | Java 文件 | 职责 | Rust 目标 |
|---|---:|---|---|
| `ruoyi-admin` | 89 | 启动类、Controller、Web 配置、分表配置 | `src/main.rs`、`src/bootstrap.rs`、`src/api/**`、`src/app/**` |
| `ruoyi-common` | 137 | 通用工具、常量、异常、Domain、注解、监控基础设施 | `src/common/**`、`src/error.rs`、`src/middleware/**` |
| `ruoyi-framework` | 48 | Security、JWT、Redis、MyBatis-Plus、AOP、过滤器、数据源 | `src/framework/**`、`src/infra/**`、`src/middleware/**` |
| `ruoyi-system` | 380 | 系统模块 + 业务 Service/Mapper/Domain/Kafka/CDC/分表查询 | `src/modules/**`、`src/domain/**` |
| `ruoyi-quartz` | 23 | Quartz 任务、`sys_job`/`sys_job_log` | `src/modules/quartz/**`、`src/infra/quartz_registry.rs` |
| `ruoyi-generator` | 19 | 代码生成（Velocity） | `src/modules/generator/**`、`resources/templates/generator/**` |

### 1.2 文件分类统计（附录 A）

| 分类 | 数量 | 迁移策略 |
|---|---:|---|
| 纯逻辑 | 256 | 按算法/数据结构逐行翻译，优先写单元测试 |
| 框架契约 | 304 | 用 Axum/tower/sqlx/redis-rs 等惯用法重写，不保留注解 |
| 混合 | 136 | 拆分“业务逻辑”与“框架胶水”，分别移植 |
| **合计** | **696** | |

### 1.3 包级映射规则

| Java 包/目录 | Rust 目录 | 说明 |
|---|---|---|
| `com.ruoyi.web.controller.**` | `src/api/**` | 按原切片分目录：base/common/flow/manager/monitor/quartz/system/tool/generator |
| `com.ruoyi.*.service` / `service.impl` | `src/modules/**/service.rs` | 接口与唯一实现合并，不强行造 trait |
| `com.ruoyi.*.mapper` | `src/modules/**/repository.rs` | Mapper 接口与 XML 合并为显式 SQL 函数 |
| `com.ruoyi.*.domain` / `bean` / `dto` / `vo` | `src/domain/**` | serde 结构体；日期/空值注解逐字段迁移 |
| `com.ruoyi.framework.**` | `src/framework/**`、`src/infra/**`、`src/middleware/**` | Security→middleware，Redis→infra，AOP→middleware |
| `com.ruoyi.common.core.monitor.**` | `src/middleware/monitor.rs`、`src/infra/metrics.rs` | TraceId/慢日志/指标/告警 |
| `com.ruoyi.quartz.**` | `src/modules/quartz/**` | `invoke_target` → 注册表 |
| `com.ruoyi.generator.**` | `src/modules/generator/**` | Velocity 模板 → minijinja/tera + 原模板 |
| `resources/mapper/**/*.xml` | 合并进 `src/modules/**/repository.rs` | 不保留 XML 运行时 |
| `resources/templates/**` | `resources/templates/**` | Excel/代码生成模板原样复用 |
| `resources/i18n/**` | `resources/i18n/**` | 键名与文案一致 |
| `resources/static/**` | `resources/static/**` | 静态资源 |
| `application.yml` / `application-druid.yml` | `config/application.yaml` / `config/application-druid.yaml` | 结构保持，键名按附录 D8 映射 |

### 1.4 不迁移 / 合并 / 改写清单

**不迁移**

- `RuoYiServletInitializer`（WAR 部署入口）→ 单二进制。
- Spring 配置类本身（`SecurityConfig`、`MyBatisPlusConfig`、`RedisConfig`、`DruidConfig`、`ApplicationConfig`、`ResourcesConfig`、`FilterConfig` 等）→ 由 `bootstrap.rs`/`middleware`/`infra` 替代。
- 注解定义（`@Log`、`@RepeatSubmit`、`@DataSource`、`@Anonymous`、`@RateLimiter` 等）→ 路由元数据/提取器。
- Mapper 接口（76 个）→ 合并为 repository 函数。
- Druid StatViewServlet / P6Spy / Swagger UI → 不暴露。
- `GlobalExceptionHandler` 与 `GlobalExceptionTraceHandler` 的“两个都生效”现状 → 实测后 `GlobalExceptionTraceHandler` 被完全遮蔽（附录 E），只需迁移 `GlobalExceptionHandler` 的 `AjaxResult` 模型，`MonitorResponse` 不迁移（见 0.4）。

**合并**

- Service 接口 + 唯一 `Impl` → 单文件 `service.rs`（原项目无多实现，不为测试强造 trait）。
- `@TableName` Domain + Mapper XML resultMap → 一个 serde `FromRow` 结构体 + 显式列别名。

**改写**

- Servlet Filter（TraceId/XSS/Repeatable）→ tower middleware。
- AOP（Log/DataScope/DataSource/RateLimiter）→ middleware + 显式服务层条件。
- `ThreadLocal`（`SecurityUtils`、`TraceContext`）→ 请求扩展 + `tracing` span。
- `HttpServletResponse` 流式下载 → Axum `Body::from_stream` / `ServeFile`。

### 1.5 纯逻辑优先移植顺序

1. `common`：常量、枚举、字符串/日期/文件/Excel/HTTP 工具、ID/雪花、树结构。
2. `domain`：155 个 Domain/DTO/VO 的 serde 结构与字段注解。
3. `system` 业务 Service 的纯计算部分（预警规则、轨迹、分表时间计算、跨月查询归并）。
4. `framework` 安全/缓存/分页/异常等契约层。
5. `api` 控制器与路由。
6. `quartz` / `generator` / Kafka / CDC / ES / OSS / SMS。
7. 启动装配、配置、可观测性。

### 1.6 死代码（用户决策：照样迁移）

以下类在当前仓库**无外部调用方**，但用户已明确要求“照样迁移”，因此全部保留为 Rust 内部能力，不删除：

- `PartitionMappingCache`（Redis `partition:mapping:*` 30 天）
- `PartitionParallelQueryService`（4 线程池）
- `ShardingQueryService`
- `ShardingSyncService`
- `DataConsistencyService`
- `ViewMaintenanceOptimizationService`
- `ShardingSnapshotFlowMapper`（逻辑表 CRUD）
- `ShardingConfig` / `ShardingTableTask`（分表策略与建表任务）

迁移要求：保持原有 public 方法签名与行为；无调用方不等于可以省略。

---

## 2. HTTP 接口清单（对应要求 2）

完整 501 条见附录 B。本节给出契约口径。

### 2.1 切片统计

| 切片 | Controller | 端点 |
|---|---:|---:|
| base | 25 | 106 |
| common | 3 | 6 |
| flow | 7 | 55 |
| generator | 1 | 15 |
| manager | 20 | 160 |
| monitor | 5 | 12 |
| quartz | 2 | 13 |
| system | 15 | 129 |
| tool | 1 | 5 |
| **合计** | **79** | **501** |

### 2.2 响应封套（字段顺序已实测）

| 封套 | 使用场景 | 字段顺序（Java 实际输出，附录 E） |
|---|---|---|
| `AjaxResult extends HashMap<String,Object>` | 绝大多数 Controller（383 处返回） | Java `HashMap` 桶序：错误为 **`msg` → `code`**；成功带数据为 **`msg` → `code` → `data`**；登录成功为 **`msg` → `code` → `token`**；`getInfo` 为 **`msg` → `code` → `pjFlag` → `overdue` → `permissions` → `roles` → `user`**；`/system/user/1` 为 **`msg` → `code` → `roleIds` → `data` → `postIds` → `roles` → `posts`** |
| `TableDataInfo` | 分页列表（100 处） | 声明顺序：**`total` → `rows` → `code` → `msg`**（实测一致） |
| `R<T>` | 仅 `/test/**` 5 个端点 | 声明顺序：**`code` → `msg` → `data`** |
| `MonitorResponse<T>` | 理论上仅 `GlobalExceptionTraceHandler` 命中时 | **实测从未出现**；双 advice 中 `GlobalExceptionHandler` 胜出（附录 E） |

约定值：

- `AjaxResult.success()`：`code=200`，`msg="操作成功"`；带数据时 `data` 为业务对象。
- `AjaxResult.error()`：`code=500`，`msg` 为错误文案。
- `TableDataInfo`：`code=200`，`msg="查询成功"`，`total` 来自 `PageInfo.getTotal()`。
- `R.ok()`：`code=200`，`msg="操作成功"`。

> `AjaxResult` 的顺序来自 Java `HashMap` 桶序，不是插入序，也不是字母序。Rust 侧应显式固定上述顺序（自定义 `Serialize` 或按场景的有序结构），不能依赖 `HashMap` 随机序。上表的 `getInfo`/`user/{id}` 等动态键场景需在阶段二按“key 集合 + 实测顺序”逐一登记。

### 2.3 HTTP 状态与错误语义（已实测）

| 场景 | Java 处理 | HTTP | Body（原样） |
|---|---|---:|---|
| 正常成功 | Controller 返回封套 | 200 | 200 封套 |
| 未登录/Token 失效 | `AuthenticationEntryPointImpl` | **200** | `{"msg":"请求访问：{uri}，认证失败，无法访问系统资源","code":401}` |
| 无权限 | `GlobalExceptionHandler.handleAccessDeniedException` | **200** | `{"msg":"没有权限，请联系管理员授权","code":403}` |
| 业务异常 `ServiceException` | `GlobalExceptionHandler.handleServiceException` | **200** | 有 `code` 用自定义，否则 500；实测登录失败 `{"msg":"用户不存在/密码错误","code":500}` |
| 校验失败 `BindException` / `MethodArgumentNotValidException` | `GlobalExceptionHandler` | **200** | `{"msg":"<第一条错误>","code":500}`；实测 `POST /system/config {}` → `{"msg":"参数键名长度不能为空","code":500}` |
| 请求方法不支持 | `GlobalExceptionHandler.handleHttpRequestMethodNotSupported` | **200** | `{"msg":"Request method 'GET' not supported","code":500}` |
| 路径变量缺失/类型不匹配 | `GlobalExceptionHandler` | **200** | 实测 `{"msg":"请求参数类型不匹配，参数[userId]要求类型为：'java.lang.Long'，但输入值为：'abc'","code":500}` |
| 运行时/未知异常 | `GlobalExceptionHandler` | **200** | `{"msg":"<e.getMessage()>","code":500}`；NPE 时为 `{"msg":null,"code":500}` |
| 请求体 JSON 非法 | `GlobalExceptionHandler.handleException`（`HttpMessageNotReadableException` 被兜底） | **200** | 实测 `{"msg":"JSON parse error: ...","code":500}`，**不是** `GlobalExceptionTraceHandler` 的 400 `MonitorResponse` |
| 路由不存在（已登录） | Spring Boot 默认 `/error` | **404** | `{"timestamp":"...","status":404,"error":"Not Found","path":"/nonexistent-xyz"}` |
| 路由不存在（未登录） | Security 先于路由匹配 | **200** | `{"msg":"请求访问：{uri}，认证失败，无法访问系统资源","code":401}` |
| 排序字段非法 | `SqlUtil.escapeOrderBySql` 抛 `UtilException` | **200** | `{"msg":"参数不符合规范，不能进行查询","code":500}` |

**已定论（附录 E）**：`GlobalExceptionTraceHandler` 在本运行时被 `GlobalExceptionHandler` 完全遮蔽，`MonitorResponse` 与 400/405/500 的 HTTP 状态分支**均不会出现**。Rust 错误模型只需覆盖 HTTP 200 + `AjaxResult`，404 需要单独实现 Spring 默认错误体（若前端依赖）。

**鉴权/校验顺序**：Security → `@PreAuthorize` → 参数绑定/校验 → handler。实测无权限时即使 body 非法也先返回 403。

### 2.4 鉴权与白名单

- 认证：无状态 JWT，Header `Authorization: Bearer <token>`，`Bearer ` 前缀可省略。
- 权限：284 个 `@PreAuthorize("@ss.hasPermi('a:b:c')")`；管理员 `*:*:*`。
- **无 `@PreAuthorize` ≠ 匿名**：绝大多数此类端点仍要求登录。
- 真正的白名单（`SecurityConfig`）：
  - `/login`、`/captchaImage`
  - GET `/profile/**` 静态文件
  - `anonymous`：`/common/download**`、`/system/file/view/**`、`/system/notice/view/**`、`/manager/suspicious/syncSuspiciousCarTask`
  - `denyAll`：`/swagger-ui.html`、`/swagger-resources/**`、`/webjars/**`、`/*/api-docs`、`/druid/**`

### 2.5 请求绑定约定

| Java | Rust |
|---|---|
| `@PathVariable` | `Path<T>` |
| `@RequestParam` | `Query<T>`（注意 Spring 对同名参数的绑定/默认值） |
| `@RequestBody` | `Json<T>` |
| `@RequestHeader` | `HeaderMap` / 自定义提取器 |
| Query 绑定到 POJO（含嵌套 `params[...]`） | `Query<T>` + `serde` 重命名；数组参数需兼容 `a=1&a=2` 与 `a=1,2` |
| `MultipartFile` / `MultipartFile[]` | `Multipart`（字段名、单/多文件差异逐端点对齐） |
| `HttpServletResponse` 直接写流 | `Response<Body>`/`ServeFile`；`Content-Disposition` 文件名编码需一致 |

### 2.6 分页约定

| 参数 | 默认值 | 说明 |
|---|---|---|
| `pageNum` | 1 | `PageDomain` |
| `pageSize` | 10 | |
| `orderByColumn` | 空 | 转 snake_case 后拼接 |
| `isAsc` | `asc` | 接受 `ascending`/`descending` |
| `reasonable` | `true` | PageHelper 页码合理化 |

`BaseController.startPage()` → `PageUtils.startPage()` → PageHelper；`startOrderBy()` 用 `SqlUtil.escapeOrderBySql` 防注入；`getDataTable(list)` 用 `new PageInfo(list).getTotal()`。

Rust 侧：显式 `count` + `limit/offset`；必须逐条确认 PageHelper 的 `countSql`、`reasonable`、`pageSize=0`、`total=0` 行为。**不要用“先查全量再切片”替代**。

### 2.7 特殊端点

- 下载/流式：`/common/download`、`/common/download/resource`、`/tool/gen/download/{tableName}`、`/tool/gen/batchGenCode`、`/system/file/{bucket}/{fileName}`、`/system/file/view/**`、`/manager/suspicious/exportAbnormalPassage`。
- 上传：`/common/upload(s)`、`/system/file/upload*`、`/system/user/profile/avatar`、`/system/user/importData`、`/manager/carinfo/import`、`/manager/exceptrecord/import`。
- 导出：各 `export` 端点；模板文件来自 `resources/templates/export/**`，需逐单元格对齐。
- Kafka/CDC 运维：`/base/cdc/status|dead-letters|retry-messages|retry/{id}|retry-all|dead-letters/{id}|dead-letters/clear|config`。

### 2.8 代表性端点（完整见附录 B）

| Method | Path | Java 方法 | Rust handler | 权限 |
|---|---|---|---|---|
| POST | `/login` | `SysLoginController.login` | `login` | 匿名 |
| GET | `/getInfo` | `SysLoginController.getInfo` | `get_info` | 登录 |
| GET | `/captchaImage` | `CaptchaController.getCode` | `get_code` | 匿名 |
| GET | `/base/snapshotflow/list` | `OdsRtSzdnSnapshotFlowAddcodeController.list` | `list` | 登录 |
| GET | `/base/snapshotflow/earliest-time` | `earliestTime` | `earliest_time` | 登录 |
| POST | `/base/snapshotflow/export` | `export` | `export` | `base:snapshotflow:export` |
| GET | `/manager/carinfo/list` | `CarInfoController.list` | `list` | `manager:carinfo:list` |
| GET | `/system/user/list` | `SysUserController.list` | `list` | `system:user:list` |
| GET | `/monitor/job/list` | `SysJobController.list` | `list` | `monitor:job:list` |
| GET | `/tool/gen/list` | `GenController.list` | `list` | `tool:gen:list` |

---

## 3. 数据层清单（对应要求 3）

完整表、Mapper、语句见附录 C。

### 3.1 数据库与连接

| 项 | 值 |
|---|---|
| 类型/版本 | MySQL 8.x |
| 库 | `carmonitdb` |
| 时区 | `serverTimezone=GMT+8` |
| URL 参数 | `useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&allowMultiQueries=true` |
| 驱动 | `com.p6spy.engine.spy.P6SpyDriver`（Rust 不需要） |
| 连接池 | Druid：initial 5 / minIdle 10 / maxActive 200 / maxWait 60s / connectTimeout 30s / socketTimeout 60s |
| 从库 | `slave.enabled=false`，实际恒为主库 |
| 分表中间件 | ShardingSphere 5.2.1，**未启用** |

Rust：`sqlx::MySqlPool`，`max_connections=200`，`acquire_timeout=60s`；TLS、时区、`zeroDateTimeBehavior` 需在连接串与 `chrono` 解码层对齐。`allowMultiQueries=true` 暗示可能存在多语句 SQL，阶段三需审计（sqlx 默认不支持多语句）。

### 3.2 表、索引、外键、迁移脚本

- 仓库**没有完整 DDL**，只有 2 份 PostgreSQL/openGauss 分区脚本，不能作为 MySQL 生产 schema。
- 已识别 **78 张真实表/视图**（80 条清单含 `id`、`information_schema` 两个解析误报），来源：47 个 `@TableName` + 75 个 Mapper XML。
- 索引、外键、字符集、默认值、自增/主键策略**无法从仓库恢复**。

**本地运行库快照（2026-10-31 导出，仅供校验）**：

| 文件 | 内容 |
|---|---|
| [`01-baseline/schema.carmonitdb.local.sql`](01-baseline/schema.carmonitdb.local.sql) | 本地 `carmonitdb` **84 张表**的 `SHOW CREATE TABLE`（含索引/字符集/默认值，仅结构，无数据） |
| [`01-baseline/data.sys_job.local.sql`](01-baseline/data.sys_job.local.sql) | 本地 `sys_job` 19 条任务数据（用于确定真实 cron/`invoke_target`） |

**代码引用表集（78）与本地库（84）的差异**：

- 交集 71 张。
- **代码引用但本地缺失 7 张**：`geometry_copy1`、`ods_rt_szdn_snapshot_flow_view`、`sys_upgrade_info`、`t_waybill`、`t_waybill_detail`、`t_waybill_item`、`t_waybill_status`（后 4 张为同一张表名的解析变体，需按 Mapper 原文核对）。
- **本地存在但代码未引用 13 张**：11 张 `qrtz_*`（Quartz 持久化表，但本项目实际使用 RAM JobStore）、`ods_rt_szdn_snapshot_flow_202508`（按月分表产物）、`t_disaster_threshold`。

> 本地快照是**开发/测试库**，不保证与生产一致；尤其 7 张缺失表与索引/外键/字符集仍需生产 DDL。Rust `migrations/` 只能作为**只读快照/校验**，默认不执行。

**阶段二前建议提供**：生产库 78 张表的 `SHOW CREATE TABLE` 或 `mysqldump --no-data --routines --triggers`；若无法提供，则以本地快照 + Mapper 反推补全，并在 README-MIGRATION 标注差异。

### 3.3 SQL 迁移规则（MyBatis XML → sqlx）

| Java/MyBatis | Rust/sqlx |
|---|---|
| `#{}` 占位符 | MySQL 继续用 `?` 绑定（不是 `$1`） |
| `<if test="...">` | `QueryBuilder::push` + 条件拼接 |
| `<foreach>` | `QueryBuilder::push_values` / `separated` |
| `<where>` / `<set>` / `<trim>` | `QueryBuilder` 的 `push(" WHERE ")` + `separated(" AND ")` |
| `<sql>` / `<include>` | Rust 常量 `const SQL_FRAGMENT: &str` |
| `resultMap` / 嵌套集合 | `FromRow` + 显式列别名；嵌套集合用二次查询 + 分组（保持原 N+1 语义） |
| `${tableName}` / `${column}` | **标识符白名单/正则校验后拼接**；表名只能来自月份计算 |
| `find_in_set(...)` | 原样 SQL |
| `WITH ROLLUP` | 原样 SQL |
| `LIMIT #{offset}, #{size}` | `LIMIT ? OFFSET ?` |
| `INFORMATION_SCHEMA.TABLES.TABLE_ROWS` | 原样 SQL（近似行数语义） |
| `CREATE TABLE IF NOT EXISTS ... LIKE ...` | 原样 DDL；MySQL DDL 隐式提交，**不能被事务回滚** |
| `ON DUPLICATE KEY UPDATE` / 批量插入 | 原样 SQL / `QueryBuilder` 批量绑定 |

已知高风险点：`${}` 注入面、`ods_rt_szdn_snapshot_flow_*` 动态表名、`information_schema` 查询、跨月 COUNT 近似、分页 count 语句。

### 3.4 事务边界

- 159 处 `@Transactional`。Spring 默认**只对 `RuntimeException`/`Error` 回滚**；受检异常不自动回滚。
- Spring AOP 是代理式：**同类内部自调用不会开启/传播事务**。Rust 必须按“实际生效的边界”包 `sqlx::Transaction`，而不是按注解数量机械照搬。
- 159 处事务分布在 Service 写路径；阶段三会产出“方法 → 事务开始/提交/回滚点 → SQL 列表”的矩阵。
- 特别注意：
  - Kafka 消费中的批量写：Java 逐条/批量写 MySQL，异常后回滚幂等标记并抛出不 ack；Rust 需显式事务 + 成功后再提交 offset。
  - DDL（建表/分区）不参与回滚。
  - `@Async` 未启用，不要把日志落库等移出事务/请求线程。

### 3.5 分表与跨月查询

**ShardingSphere（用户决策：需要生效）**：Java 仅在 `sharding.enabled=true` 时创建 `@Primary` 的 ShardingSphere 数据源（当前未配置）。Rust 不引入中间件，改为在仓储层实现等价路由：

- 逻辑表 `ods_rt_szdn_snapshot_flow` → `ds.ods_rt_szdn_snapshot_flow_yyyyMM`，按 `snapshottime` 分钟/月路由；
- 逻辑表 `ods_lwzxsfsj_fee_records` → `ds.ods_lwzxsfsj_fee_records_yyyyMMdd`，按 `record_time` 路由；
- 主键 `big_id`/`id` 使用雪花；
- 无分片键的查询按 ShardingSphere 语义广播到全部实际数据节点；Rust 侧以 `information_schema` 探测实际存在的物理表，避免 2025–2099 全表清单造成无谓查询（差异需在阶段三验收中记录）；
- `sharding.enabled` 默认 `true`；关闭时退化为当前 Java 行为（直接访问同名表）。

**手工分表查询**（`SnapshotFlowEnhancedService`）：

1. 表名：`ods_rt_szdn_snapshot_flow_yyyyMM`（另有 `_provcapture_`、`_stationcapture_` 变体）。
2. 跨月时按时间范围枚举月份表。
3. **历史月**：无额外过滤条件时用 `INFORMATION_SCHEMA.TABLES.TABLE_ROWS` 近似 `total`；当前月用精确 `COUNT`。
4. 逐表 `LIMIT offset, size`，再在内存按 `snapshottime desc` 归并排序。
5. 时间范围不得超过当前时间；异常时回退外部 Forest 接口。
6. `total` 可能不精确——这是 Java 现状，Rust 必须保留，不能“修正”。

### 3.6 主键与 ID

- MyBatis-Plus `id-type: ASSIGN_ID` → 内置雪花（epoch/位宽按其默认实现）。
- 分表服务另有自定义雪花解析：epoch `1672531200000`、shift `22`（`ShardingIdCacheService`）。
- 两者用途不同，阶段二分别列出；迁移时需保证生成的 ID 与 Java 不冲突。

### 3.7 缓存与数据一致性

- 启动预热：`sys_config` 全量、`sys_dict` 全量；失败会阻止启动（Java `@PostConstruct` 行为）。
- 字典/配置增删改同步刷新 Redis；业务缓存（门架、车辆、白名单、预警规则、轨迹）多为**无 TTL**。
- 多实例下 Java 只刷新本机 + Redis，存在本地缓存不一致风险；Rust 若引入进程内缓存需保持同等语义或明确改进（需确认）。

---

## 4. 中间件与外部依赖（对应要求 4）

完整清单见附录 D1–D7。

### 4.1 组件状态矩阵

| 组件 | Java | 状态 | Rust 目标 |
|---|---|---|---|
| Web | Tomcat 9989 | 启用 | Axum + tokio + hyper |
| 安全 | Spring Security + JWT | 启用 | tower 中间件 + `jsonwebtoken` |
| 数据源 | Druid + P6Spy + MySQL 8 | 启用（从库关闭） | sqlx MySQL Pool |
| ORM | MyBatis-Plus + PageHelper | 启用 | sqlx 手写 SQL + 显式分页 |
| 分表 | ShardingSphere | **未启用** | **用户决策启用**：仓储层路由（`sharding.enabled=true`） |
| 手工分表查询 | `SnapshotFlowEnhancedService` | 启用 | 逐表 COUNT/LIMIT + 归并 |
| 缓存 | Redis（Lettuce） | 启用 | redis-rs |
| MQ | Kafka（spring-kafka） | **2 个监听器生效** | rust-rdkafka |
| 搜索 | ES RestHighLevelClient 7.15.2 | 查询/写入代码启用；CDC 写入注释 | `elasticsearch` crate 或 REST |
| 定时 | Quartz RAM | 启用 | tokio 定时器 + 目标注册表 |
| `@Scheduled` | Spring Scheduling | **全部失效** | **用户决策启用**：注册 6 个定时任务 |
| `@Async` | Spring Async | **全部失效** | 保持同步 |
| 对象存储 | AWS S3 SDK/MinIO | Template 启用；`/oss/**` 未注册 | aws-sdk-s3 |
| 短信 | 阿里云 Dysmsapi/MNS | 代码启用，模板全空 | reqwest + ACS3 签名 |
| 外部 HTTP | Forest 1.6.0 | 启用 | reqwest |
| 验证码 | kaptcha | 启用 | captcha crate（仅语义一致） |
| Excel | POI/EasyPOI/模板 | 启用 | rust_xlsxwriter/calamine |
| 代码生成 | Velocity | 启用 | minijinja/tera |
| 系统信息 | OSHI | 启用 | sysinfo |
| UA | UserAgentUtils | 启用 | UA 解析 crate |
| 文档 | springfox | 关闭 | utoipa（默认关闭） |

### 4.2 Redis

完整 key/TTL 见附录 D2。重点：

- key 名称、TTL 数值/单位必须逐字符一致。
- `login_tokens:{token}` 值含 `LoginUser`（**含 BCrypt 密码密文**）、`permissions`、`sessionId` 等。
- `captcha_codes:*` 2 分钟、一次性；`pwd_err_cnt:*` 10 分钟；`repeat_submit:*` 5 秒；`snapshot:flow:idempotent_*` 24 小时。
- 业务缓存无 TTL：`car_list`、`white_car_list`、`car_warning_list`、`gantry_list*`、`lxbh_jdwd:*`、`car_curent_trail:*` 等。
- CDC 死信：`cdc:retry:*`（延迟）、`cdc:dead:*`（7 天），使用 String 序列化，**不是** FastJson2 对象格式。

### 4.3 Kafka

- 生效监听器：
  - `SnapshotFlowKafkaConsumerV2`：topic `ods-rt-szdn-snapshot-flow`，group `snapshot-flow-consumer-group`，并发 3，批量 + `MANUAL_IMMEDIATE`，整批成功才 `acknowledge()`。
  - `CdcSyncService`：topic `snapshot-flow-cdc`，group `snapshot-flow-cdc-group`，并发 3，手动 ack，**所有分支都 ack**，ES 写入是空操作。
- 消息：`{"operationType":"INSERT|UPDATE|DELETE","data":{...}}`；CDC 为 `CdcMessage`。
- 处理链：解析 → `bigId` 必填 → Redis 幂等 → MySQL/ES 批量写 → DELETE；失败单条重试 3 次（1s 间隔）→ DLQ；异常删除幂等标记并抛出不 ack。
- DLQ：`ods-rt-szdn-snapshot-flow-dlq`，消息体 `{originalTopic,partition,offset,timestamp,reason,value}`。
- 3 个旧/CDC 监听器已注释，不迁移为活动消费者。

### 4.4 Elasticsearch

- `127.0.0.1:9200`，索引 `snapshot-flow`，文档 `_id=bigId`。
- 写入：单条 `index` / 批量 `BulkRequest`。
- 查询 DSL：`bool.must` 的 `platenumber` wildcard、`sectioncode/orgcode/gantrycode` term、`snapshottime` range；`snapshottime desc`；`from=(pageNum-1)*pageSize`。
- `searchPage` 当前无 Controller 调用，仅保留能力。
- CDC 的 ES 写入被注释，Rust 同样不写。

### 4.5 Quartz / 定时 / 线程池

- Quartz RAM JobStore；启动 `scheduler.clear()` → 读 `sys_job` → 逐条注册。
- `invoke_target` 是反射字符串（`ryTask.ryParams('ry')` 或全类名）；Rust 用 `match` 注册表，未知 target 记录错误并跳过。
- 可被调用的 Bean/方法清单见附录 D5.1（`ryTask`、`orgTask`、`vehicleMonitoringTask`、`trackTask`、`snapshotFlowSyncTask`、`partitionMaintenanceTask`）。
- `@Scheduled` 6 个方法：**用户决策启用**，Rust 注册为独立定时任务（cron 与注解一致）。
- 线程池：`threadPoolTaskExecutor` 10/20/200、`CallerRunsPolicy`；`AsyncManager` 10ms 后写登录/操作日志；Rust 用 `tokio::spawn + sleep(10ms)`。

### 4.6 认证、JWT、密码

- HS512，Claims 仅 `login_user_key=token(UUID)`；有效期 120 分钟；剩余 ≤20 分钟自动续期。
- `sessionId` 由 `HttpSession.getId()` 生成（Tomcat 32 位大写十六进制）→ Rust 合成同格式。
- 登录：验证码可选（`code` 为空则跳过）、密码复杂度、BCrypt、失败 5 次锁 10 分钟。
- 登出删除 Redis token，异步写登录日志。
- 白名单与错误响应见 2.3/2.4。

### 4.7 文件、短信、外部 HTTP

- 本地文件：`/profile/**` → `ruoyi.profile`（默认 `D:/ruoyi/uploadPath`）。
- OSS：`OssTemplate` 由 `oss.enable`（缺省 true）创建；`/oss/**` 只有在 `oss.info=true` 时才注册，当前未配置。
- 短信：阿里云 Dysmsapi/MNS；所有模板配置为空串，实际行为需逐方法核对（可能直接报错/空发送）。
- Forest：9 个接口，调用外部车辆监控、路网、地图、海大 GeoServer；超时 60s、重试 2 次、最大连接 1000。

### 4.8 过滤器 / AOP 对照

| Java | Rust |
|---|---|
| `TraceIdFilter`（order=1） | tower middleware + `tracing` span + 响应头 |
| `XssFilter`（`/system/*,/monitor/*,/tool/*`，排除 `/system/notice`） | 读体重写 middleware；GET/DELETE 跳过 |
| `RepeatableFilter` | Axum `Bytes` 天然可重放 |
| `SameUrlDataInterceptor` | 路由提取器 + Redis（仅 1 处使用） |
| `LogAspect`（239 处） | 路由元数据 + 异步写 `sys_oper_log`，参数/结果截断 2000 |
| `DataScopeAspect`（3 处） | 服务层显式 SQL 条件 |
| `RateLimiterAspect`（0 处） | 不实现 |
| `DataSourceAspect` | 单连接池 |
| `@Transactional`（159 处） | 显式 `sqlx::Transaction` |
| `@PostConstruct` | `main` 启动序列 |

---

## 5. 配置项清单（对应要求 5）

完整逐项对照见附录 D8（约 100 项）。

### 5.1 命名约定（建议，待确认）

- 配置文件：`config/application.yaml`，可选 `config/application-{APP_PROFILE}.yaml`。
- 环境变量：前缀 `APP_`，层级 `__`，大写，`-` → `_`。
  - `server.port` → `APP_SERVER__PORT`
  - `kafka.topic.snapshot-flow` → `APP_KAFKA__TOPIC__SNAPSHOT_FLOW`
- 优先级：命令行 > 环境变量 > profile 文件 > 默认文件 > 代码默认值。
- 加载失败即退出（对应 Java 启动期 `@ConfigurationProperties` 校验）。

### 5.2 关键配置分组

| 分组 | 关键项 | 默认值/说明 |
|---|---|---|
| 服务 | `server.port` | `9989`，必须一致 |
| 应用 | `ruoyi.profile` | `D:/ruoyi/uploadPath` |
| 数据源 | `database.url/username/password/pool.*` | MySQL `carmonitdb`，池 5/10/200/60s |
| Redis | `redis.host/port/database/password/pool.*` | `127.0.0.1:6379/0` |
| Token | `token.header/secret/expire_time` | `Authorization`、120 分钟；secret 必须部署覆盖 |
| 分页 | 无配置 | 参数默认 1/10 |
| Kafka | `kafka.bootstrap_servers/topic.*/consumer.*` | `127.0.0.1:9092`；手动 ack；并发 3 |
| CDC | `cdc.kafka.*`、`cdc.es_sync.*`、`cdc.retry.*` | 默认 `localhost:9092`、group `snapshot-flow-cdc-group`、topic `snapshot-flow-cdc` |
| ES | `elasticsearch.host/port/index` | `127.0.0.1:9200`、`snapshot-flow` |
| OSS | `oss.endpoint/access_key/secret_key/bucket_name/enable/info` | `enable` 缺省 true；`info` 缺省 false |
| 短信 | `sms.signature/*_template` | 全空 |
| Forest | `forest.*`、`forest.variables.henda_url` | 超时 60s、重试 2 |
| 监控 | `monitor.*` | 慢请求 3000ms、慢方法 500ms、慢 SQL 1000ms、trace 头 `X-Trace-Id` |
| XSS | `xss.enabled/url_patterns/excludes` | 启用；`/system/*,/monitor/*,/tool/*`；排除 `/system/notice` |
| 上传 | `upload.max_file_size/max_request_size` | 40MB / 200MB |
| 日志 | `log.dir` | Java `/home/ruoyi/logs`；滚动 100MB/60 天 |
| 死配置 | `snapshot.flow.sharding.*` | 无代码读取，保留但不生效 |

### 5.3 部署时必须覆盖的敏感项

- 数据库账号/密码。
- `token.secret`。
- OSS access/secret。
- `hengda.secret`。
- Druid 控制台账号密码（不迁移，但需从旧部署中移除）。
- 短信 access key/secret。

---

## 6. 不可 1:1 直接翻译的阻塞点（对应要求 6）

完整 41 条见附录 D9。按风险分级：

### 6.1 高风险（行为可能直接不一致）

| # | 阻塞点 | Rust 替代 | 验收方法 |
|---|---|---|---|
| 1 | ~~双 `@RestControllerAdvice` 顺序不确定~~ **已实测解决** | `GlobalExceptionHandler` 胜出，只实现 `AjaxResult` + HTTP 200；`MonitorResponse` 不迁移 | 附录 E 已记录 12 类请求的 HTTP + body |
| 2 | FastJson2 `WriteClassName` + `@type` | 自定义兼容序列化器，或切换时清空缓存 | Java 写入 → Rust 读出；Rust 写入 → Java 读出 |
| 3 | jjwt 0.9.1 secret Base64/截断 | 用 Java 生成固定 token 反推签名字节 | 同一 token 在 Java/Rust 双向校验 |
| 4 | MyBatis 动态 SQL + `${}` | `QueryBuilder` + 标识符白名单 | SQL 日志逐条比对；注入用例 |
| 5 | PageHelper `startPage()` 100 处 | 显式 count/limit/offset + reasonable 语义 | 同一数据集分页结果逐页比对 |
| 6 | 跨月分表近似 COUNT + 内存归并 | 逐表查询 + 归并；保留近似语义 | 历史月/当前月/跨月/边界时间用例 |
| 7 | `@Transactional` 代理自调用 | 按实际生效边界显式事务 | 异常注入，核对回滚范围 |
| 8 | Quartz 反射 `invoke_target` | 字符串 → 函数注册表 | 按 `sys_job` 快照逐任务比对 |
| 9 | 缺失 DDL/索引/外键（**部分缓解**） | 本地 84 表 DDL 快照已导出；7 张引用表仍缺 | 生产 `SHOW CREATE TABLE` 全量对比 |
| 10 | 缺失 `sys_job` 数据（**本地已导出**） | 本地 19 条快照见 `data.sys_job.local.sql`；生产仍需核对 | cron/参数/并发策略逐条一致 |
| 11 | Redis 灰度共存 | 兼容 `@type` 或统一切换清缓存 | 滚动切换演练 |

### 6.2 中风险

- `@JsonFormat` 96 处、`@JsonIgnore`、`@JsonInclude(NON_EMPTY)`：日期格式/空值省略逐字段核对。
- `BeanUtils.copyProperties`：显式 `From/Into`，字段遗漏会导致数据丢失。
- XSS 过滤器：清洗规则需逐字符对齐，且不能破坏 multipart。
- Excel 模板/POI：样式、合并单元格、公式可能无法像素一致。
- Velocity 模板：换行/缩进/转义差异。
- 阿里云短信签名：ACS3 签名易错；空模板行为需保持。
- ES DSL/日期格式：字段映射与 7.15 行为对齐。
- `@Async` 失效：不要“顺手启用”；`@Scheduled` 已由用户决策启用，属例外。
- 多语句 SQL / `useSSL=true` / `zeroDateTimeBehavior`：sqlx 行为差异需实测。
- `ThreadLocal`：禁止跨 `.await` 持有；请求扩展替代。

### 6.3 低风险

- OSHI / UserAgentUtils / kaptcha：字段/语义对齐即可，不要求像素一致。
- WAR 入口、Druid/P6Spy、Swagger：不迁移。
- 日志格式：不要求逐字符，但 traceId/慢日志/文件路径需可用。

---

## 7. 目标 Rust 架构（阶段三落地蓝图）

### 7.1 技术栈

| 领域 | Crate |
|---|---|
| Web/运行时 | `axum`、`tokio`、`hyper`、`tower`、`tower-http` |
| 序列化 | `serde`、`serde_json`、`serde_yaml`、`indexmap` |
| 数据库 | `sqlx`（mysql, runtime-tokio-rustls, chrono, uuid, json, macros） |
| 缓存 | `redis`（tokio-comp, connection-manager） |
| MQ | `rdkafka` |
| 搜索 | `elasticsearch` 或 `reqwest` 直连 REST |
| HTTP 客户端 | `reqwest`（rustls, json, multipart） |
| 认证 | `jsonwebtoken`、`bcrypt`、`uuid` |
| 配置 | `config` |
| 日志/追踪 | `tracing`、`tracing-subscriber`、`tracing-appender` |
| 错误 | `thiserror`（对外错误模型）、`anyhow`（启动期） |
| 校验 | `validator` |
| 文档 | `utoipa`（默认关闭） |
| Excel | `rust_xlsxwriter`、`calamine` |
| 模板 | `minijinja` 或 `tera` |
| 系统信息 | `sysinfo` |
| 对象存储 | `aws-sdk-s3`、`aws-config` |
| 并发容器 | `dashmap`、`parking_lot` |
| 时间 | `chrono`、`chrono-tz` |
| 测试 | `pretty_assertions`、`mockall`、`testcontainers`（dev） |

版本策略：阶段四锁定到 2026-10 的最新稳定版，提交 `Cargo.lock` 与 `rust-toolchain.toml`；不使用 nightly/实验 API。

### 7.2 目录结构

```text
car-monit-rust/
  Cargo.toml
  Cargo.lock
  rust-toolchain.toml
  config/
    application.yaml
    application-druid.yaml
  migrations/                  # 只读快照，默认不执行
  resources/
    templates/{export,generator,...}
    static/
    i18n/
  src/
    main.rs
    bootstrap.rs               # 组合根：配置→DB→Redis→缓存预热→调度→监听器
    config.rs
    state.rs                   # AppState
    error.rs                   # AppError + IntoResponse
    router.rs                  # 501 条路由注册
    middleware/
      trace_id.rs
      xss.rs
      auth.rs
      permission.rs
      operation_log.rs
      repeat_submit.rs
      monitor.rs
    api/{base,common,flow,manager,monitor,quartz,system,tool,generator}/
    modules/{base,manager,system,flow,quartz,generator}/
      {service,repository,domain}.rs
    infra/
      db.rs
      redis.rs
      kafka/{consumer_v2,cdc,dlq}.rs
      es.rs
      s3.rs
      sms.rs
      forest.rs
      excel.rs
      captcha.rs
      snowflake.rs
      quartz_registry.rs
      sharding.rs
    common/
      constants.rs
      enums.rs
      utils/
      i18n.rs
  tests/
```

### 7.3 请求生命周期

```text
TraceId → XSS → Auth(JWT+Redis+续期) → Permission → RepeatSubmit
        → Handler → OperationLog(async) → AppError → 响应封套
```

- 认证失败在中间件直接返回 **HTTP 200 + code 401**，不抛 401 状态。
- 权限守卫读取路由元数据 `permission`，管理员 `*:*:*`。
- 日志中间件异步写 `sys_oper_log`，参数/结果截断 2000。

### 7.4 错误模型

```rust
enum AppError {
    Unauthorized(String),          // 200 + code 401
    Forbidden(String),             // 200 + code 403
    Business(Option<i32>, String), // 200 + code 自定义/500
    Validation(String),            // 待 0.4 实测后确定 200+500 或 400+MonitorResponse
    MethodNotSupported(String),
    BadRequest(String),
    Internal(String),
}
```

每个变体实现 `IntoResponse`，集中维护“HTTP 状态 + body 结构 + 字段顺序”。阶段二确认 0.4 后，只保留一套错误响应。

---

## 8. 阶段二计划（等待确认后执行）

### 8.1 交付物

`docs/02-JAVA-RUST-MAPPING.md`，按提示词要求的 **11 个维度**输出全量映射表，每行四列：**Java 用法 / Rust 对应写法 / 关键差异 / Java 开发者最容易踩的坑**。

| # | 维度 | 本项目重点 |
|---:|---|---|
| 1 | 语言与类型系统 | `Integer`→`Option<i32>`、`Long`→`i64`、`BigDecimal`、`Date`/`LocalDateTime`、继承体系→`struct+trait/enum`、异常→`Result` |
| 2 | 并发与异步 | `AsyncManager`、线程池、`CompletableFuture`、`Arc<RwLock>`、禁止跨 `.await` 持锁 |
| 3 | Web 框架 | 501 条路由、extractor、`@ControllerAdvice`→`AppError`、Security Filter→tower、封套字段顺序 |
| 4 | ORM/数据访问 | MyBatis-Plus/PageHelper→sqlx、动态 SQL、resultMap、事务、雪花、分表 |
| 5 | 中间件 | Redis `@type`、Kafka 批量/手动 ack、ES DSL、Quartz、OSS、短信、Forest |
| 6 | 配置 | `@ConfigurationProperties`/`@Value`→`config-rs`、`APP_`+`__`、profile、默认值 |
| 7 | 日志与可观测性 | Logback→tracing、MDC→span、TraceId、慢 SQL/慢请求、日志滚动 |
| 8 | 序列化 | Jackson→serde、`@JsonFormat` 96 处、`@JsonIgnore`、`NON_EMPTY`、`HashMap` 顺序 |
| 9 | 依赖注入 | 组合根、`AppState`、`State`、trait 抽象边界 |
| 10 | 测试 | JUnit→`#[test]`/`#[tokio::test]`、testcontainers、无测试现状的补测策略 |
| 11 | 构建与部署 | Maven→Cargo、fat jar→单二进制、启动命令、环境变量、健康检查 |

### 8.2 项目专属映射（必须逐条覆盖）

- 响应封套：`AjaxResult` / `TableDataInfo` / `R`（`MonitorResponse` 已实测不生效，不迁移）。
- 异常：`GlobalExceptionHandler` 唯一生效（附录 E），错误矩阵已固定。
- 鉴权：`@PreAuthorize` 284 处、`SecurityUtils`、`LoginUser`、JWT 续期、sessionId。
- 日志：`@Log` 239 处、`LogAspect` 字段截断/UA/IP/地点。
- 数据权限：`@DataScope` 3 处 → 显式 SQL 条件。
- 分页：`startPage()` 100 处 → count/limit/offset/reasonable。
- 事务：159 处 → 实际生效边界矩阵。
- 动态 SQL：`<if>/<foreach>/<sql>`、`${tableName}` 白名单。
- 跨月查询：近似/精确 COUNT、逐表分页、内存归并、Forest 回退。
- 缓存：全部 key/TTL、FastJson2 `@type`、预热/刷新。
- Kafka：批量、幂等、重试、DLQ、手动 ack。
- Quartz：`invoke_target` 注册表。
- Excel/代码生成：模板文件与生成物对比。
- 配置：约 100 项逐项表。

### 8.3 阶段二验收标准

1. 11 个维度均有表格，且每行有 Java 证据（文件:行）与 Rust 目标文件。
2. 501 条端点全部能对应到阶段三的 Rust 模块/函数。
3. 78 张表的每张表至少有一条 CRUD/查询映射。
4. 159 处事务全部标注“生效/不生效/自调用”及 Rust 包裹位置。
5. 双 advice 问题已实测并给出唯一结论（附录 E：`GlobalExceptionHandler` 胜出）。
6. 用户确认后，才进入阶段三写代码。

---

## 9. 需要在阶段二前确认的事项

> 状态更新（2026-10-31）：第 3、4、13 项已由用户决策/实测覆盖（共存 + 启动实测）；第 1、2 项已有本地快照，生产导出仍建议提供。

| # | 事项 | 建议/影响 | 状态 |
|---:|---|---|---|
| 1 | 生产库 DDL（78 张表） | 本地 84 表 DDL 已导出，覆盖 71/78；缺 7 张，索引/外键/字符集仍以生产为准 | **部分解决** |
| 2 | `sys_job` 数据导出 | 本地 19 条已导出（`data.sys_job.local.sql`）；生产任务需核对 | **部分解决** |
| 3 | Redis 灰度策略 | 用户已选**共存** → Rust 必须复刻 FastJson2 `@type` | **已决策** |
| 4 | 双异常 advice | 已启动 Java 实测：`GlobalExceptionHandler` 胜出，只实现 `AjaxResult` | **已解决**（附录 E） |
| 5 | `/oss/**` | **已决策**：默认不注册，保留 `oss.info=true` 时注册端点 | 已决策 |
| 6 | `@Scheduled` / ShardingSphere | **已决策：需要生效**（6 个定时任务 + 逻辑表路由） | 已决策 |
| 7 | 死代码 | **已决策：照样迁移**（8 个类全部保留） | 已决策 |
| 8 | 环境变量命名 | `APP_` + `__` 是否与现有部署脚本兼容 | 待确认 |
| 9 | 运行环境 | 本地已具备 MySQL/Redis；Kafka/ES 未启动，集成测试需补 | **部分具备** |
| 10 | 部署形态 | systemd / Docker / K8s；是否要求单二进制、健康检查路径 | 待确认 |
| 11 | 日志与可观测性 | 是否继续写本地文件，还是 stdout + 采集；是否接入 OTel | 待确认 |
| 12 | MySQL TLS | `useSSL=true` 是否真实启用证书校验；Rust 侧 TLS 配置需对齐 | 待确认 |
| 13 | Java 基线运行 | 已用 `admin` 账号实测登录/异常/封套顺序，见附录 E | **已解决** |

---

## 10. 阶段一结论

- **迁移面已完全盘点**：696 文件、501 端点、75 XML/481 SQL、78 张表、159 事务、284 权限点、239 日志点。
- **纯逻辑与框架契约已分离**：256 纯逻辑可优先逐行翻译；304 框架契约需 Rust 惯用法重写；136 混合需拆分。
- **运行时“无效能力”已识别**：`@Scheduled`、`@Async`、ShardingSphere、CDC ES 写入、`/oss/**` 必须保持无效。
- **高风险兼容点已前置**：FastJson2 `@type`、jjwt secret、动态 SQL/PageHelper、跨月近似 COUNT、事务自调用。
- **运行时行为已实测固定**：`GlobalExceptionHandler` 唯一生效、仅 `AjaxResult`、除 404 外 HTTP 恒 200、封套字段顺序已记录、鉴权→权限→校验顺序已确认（附录 E）。
- **用户决策已落账（0.5）**：`@Scheduled` 6 项启用、ShardingSphere 逻辑表路由启用、8 个死代码类照样迁移；其余按最佳实践执行。
- **数据缺口部分缓解**：本地 DDL（84 表）与 `sys_job`（19 条）已导出；代码引用但本地缺失 7 张表，生产 DDL/任务清单仍建议提供以完成 1:1 校验。

**阶段一确认完毕，开始阶段二。** 下一阶段输出 `docs/02-JAVA-RUST-MAPPING.md`，按提示词 11 个维度给出“Java 用法 / Rust 对应写法 / 关键差异 / 易踩坑”四列表，并引用附录 A–E 作为全量明细。
