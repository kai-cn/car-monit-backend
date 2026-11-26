<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# Rust 迁移评审报告（car-monit-rust）

> 评审对象：`d:\work\IdeaProjects\car-monit-backend-new\car-monit-rust`（master，commit `ca59188`，2026-11-07）
> 对照基线：Java `car-monit-backend-new`（RuoYi 3.8.7 / Spring Boot 2.5.15 / Java 8）
> 评审方式：静态阅读全部核心模块 + 对照 Java 源码与既有对拍文档 + `cargo check/clippy/test`
> 报告口径：**「已验证事实」指我实际读到的代码/命令结果；「推断」单独标注**，见 §6

---

## 0. 结论摘要

### 0.1 总体判断

这是一次**契约级完整度很高、工程级健壮性中等偏上**的 1:1 迁移：响应封套、字段顺序、JWT/FastJson2 兼容、PageHelper 分页语义、Quartz cron 怪癖、事务边界、MyBatis 动态 SQL 都被逐条复刻，且有相当强的双端对拍证据。代码中 `unsafe` 为 0，`cargo check` 干净，94 个单元测试全绿。

风险不在「接口形状」，而在三类地方：

1. **Java 里有、Rust 里没迁（或多迁）的分支**：数据权限的实际生效面被反过来了——Java 只有 `sys_role` 生效，Rust 还给 `sys_dept` 加了过滤（§3.6.2）；XSS 过滤器（§3.6.3）、`@RepeatSubmit`（§3.6.4）未实现；`/oss/**` 默认被无条件注册（§3.6.5）。
2. **Rust 运行时模型带来的形态差异**：bcrypt/Excel/ZIP/文件 IO 全部在 async 任务里同步执行，没有 `spawn_blocking`/并发闸门（§3.3）；`@Log` 中间件会把最大 64MB 的响应体整体缓冲再拷贝（§3.3）；所有 body extractor 实际走 axum **2MB 默认上限**，与 Java 的 40MB/200MB 不符（§3.6.7）。
3. **运维与可观测性欠账**：日志滚动上限、慢请求/慢 SQL 阈值等配置解析了但没接线；只有 Ctrl-C 没有 SIGTERM；没有 CI（§3.7–§3.9）。

### 0.2 关键数字（已验证）

| 指标 | 数值 | 来源 |
|---|---:|---|
| Rust 源文件 | 167 个 / 41,822 行 | `Get-ChildItem src -Include *.rs` |
| 其中 API 层 | 100 个文件 / 28,690 行（约 69%） | 同上 |
| 基线端点 | 510 条（501 控制器端点 + 9 条 `/oss/**`） | [lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L247) 断言 |
| `sqlx::query` 调用点 | 202 处；`query!` 宏 0 处；`query_as::<_,T>` 仅 4 处 | 全仓 grep |
| 事务相关语句 | 50 处，集中在 7 个文件 | 全仓 grep |
| `#[test]` | 94 个（32 个文件），`cargo test --lib` 94 passed | 实际运行 |
| clippy | 26 条告警（24 条 lib + 2 条 test 独有），全部为风格类 | 实际运行 |
| `unsafe` | 0 处 | 全仓 grep |
| 非测试 `unwrap/expect/panic!` | 40 处（不变量/常量/锁操作，未见外部可触发） | 脚本统计 |
| Cargo.lock 包数 | 476 | `Select-String Cargo.lock` |
| `cargo check --all-targets` | 通过，无 warning（2m02s） | 实际运行 |

### 0.3 评级（主观，按维度）

| 维度 | 评级 | 一句话理由 |
|---|---|---|
| 接口契约对齐 | **强** | 510 路由、封套/键序/状态码/错误文案都有对拍与单测支撑 |
| 事务与一致性 | **强** | `sys_user`/`sys_role`/`sys_job` 都是 `&mut tx` + 正确的提交/回滚分支 |
| Java 怪癖复刻 | **强** | jjwt Base64、FastJson2 `@type`/`L` 后缀、HashMap 桶序、Quartz cron 全部显式实现 |
| 鉴权/数据权限 | **中** | 认证链完整；`sys_dept` 多做了 Java 未生效的数据范围过滤 |
| 运行时健壮性 | **中** | 同步重活占 worker、响应体全量缓冲、panic 无兜底、Redis 单连接 |
| 可观测性/运维 | **偏弱** | 慢 SQL/慢请求、日志滚动上限、SIGTERM 未接 |
| 测试/CI | **中偏弱** | 纯函数覆盖好，handler/DB/事务零集成测试，无 CI |
| 依赖卫生 | **中** | 476 包、多个未使用直接依赖、未接线 feature |

---

## 1. 评审范围与方法

### 1.1 实际执行的验证命令

| 命令 | 结果 | 说明 |
|---|---|---|
| `cargo check --all-targets` | ✅ 通过，2m02s，无 warning | lib + tests 均编译 |
| `cargo clippy --all-targets --message-format=short` | ⚠️ 26 条 warning，0 error | 全部为 `clippy::style`/`complexity` 级 |
| `cargo test --lib` | ✅ 94 passed / 0 failed / 0.11s | 纯单元测试，无需 DB/Redis |
| `cargo fmt --check` | ✅ 通过（exit 0） | 全仓 rustfmt 干净 |
| `cargo tree -d` | 部分输出 | 存在 `base64 0.22/0.23` 等重复版本；cargo 全局缓存报 “database or disk is full”，与项目无关 |

### 1.2 未做/做不到的验证（影响结论强度）

- **未启动服务做端到端复核**：MySQL 3307、Redis 6379 未确认在线，Java 对照端也未启动。所有「响应头/行为差异」结论来自静态代码 + axum 0.8.9 源码，未用 `curl` 实测。
- **未做压测/内存剖析**：`spawn_blocking`、响应体缓冲、Redis 单连接的影响是**基于代码形态的推断**，没有吞吐/内存数据。
- **未逐表核对 DDL**：自动填充列存在性是抽样+DDL 脚本分析，不是逐表验证。
- 环境未做在线依赖版本核查（不判断是否应升级 major）。

---

## 2. 技术选型横向对比

### 2.1 当前实际技术栈（依据 `Cargo.toml` + `src/` 用法）

| 领域 | 当前选型 | 实际用法要点 |
|---|---|---|
| Web 框架 | **axum 0.8 + tower-http 0.6 + hyper 1** | 每个切片导出 `Router<AppState>` 后 `merge`；`MatchedPath` 驱动全局路由元数据；5 层中间件；3 处 Spring MVC 兼容层 |
| 数据库访问 | **sqlx 0.8（runtime query + QueryBuilder）** | 202 处手写 SQL；0 处编译期 `query!`；动态列→JSON（`db/rows.rs`）；`information_schema` 列过滤 |
| 序列化 | **serde + serde_json（preserve_order + float_roundtrip）+ IndexMap** | 复刻 Java `HashMap`/`Properties` 桶序；实体键序常量表；FastJson2 形状 |
| 认证 | **jsonwebtoken 9 + bcrypt 0.16** | 手写 jjwt 0.9.1 的 JAXB Base64 解码；无 Spring Security，过滤器链自研 |
| 缓存 | **redis-rs 0.27 + ConnectionManager（单连接多路复用）** | 键/TTL 对齐；`@type` 注入/剥离、`123L`、`Set[...]` 容错 |
| 日志 | **tracing + tracing-subscriber + tracing-appender** | stdout + 按天滚动文件；`json` feature 未启用 |
| 调度 | **tokio 循环 + 自研 Quartz cron（37KB）+ 自研 job 注册表** | 6 个 `@Scheduled` + `sys_job` 两套调度；暂停/恢复/立即执行 |
| Excel | **rust_xlsxwriter 0.79（导出）+ calamine 0.26（导入）** | 只写值+表头样式；模板导出改为标准工作簿；`zip` 钉死 `=2.2.2` |
| HTTP 客户端 | **reqwest 0.12（rustls）** | 映射 Forest 连接池/超时；重试逻辑只在 `task/remote.rs` 手写 |
| 配置 | **config 0.15 + 内嵌 YAML + `APP_`/`__` 环境变量** | 键名/默认值对齐 Java；未做范围校验 |
| 其它 | dashmap、parking_lot、thiserror 2、anyhow、uuid、chrono、rust_decimal、image(jpeg)、sysinfo | 雪花 ID 自研；验证码自绘并 JPEG 编码 |

### 2.2 逐项横评

#### 2.2.1 Web 框架：axum vs actix-web / rocket / poem

**为什么 axum 在这个项目里是对的**

- 这个迁移的核心不是「写新服务」，而是**复刻一条 Servlet Filter + Spring MVC 的判定顺序**。axum 的 `tower::Layer` 可以精确表达「TraceId → CORS → 鉴权 → @PreAuthorize/@Log → 405 翻译 → 路由」的洋葱顺序（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L125-L147)），这比 actix-web 的 `App::wrap` 更接近 Java 的语义模型。
- `MatchedPath` 是整套 `@PreAuthorize`/`@Log` 方案的支点：路由注册时把元数据写进全局 `DashMap`，中间件按「method + 匹配到的 pattern」查表（[meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L86-L126)、[meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L158-L167)）。actix-web 要在 `Resource` 上做等价的事，需要自定义 guard/扩展，成本更高。
- `ConnectInfo<SocketAddr>` 直接支撑 Java `IpUtils.getIpAddr` 的审计字段；axum 的 `Multipart`/`Json`/`Path`/`Query` 提取器与 Spring 的参数绑定一一对得上。

**axum 的代价（已实际发生）**

- **没有 `useTrailingSlashMatch`**：只能「先按原样路由，404 后削一个尾斜杠再 oneshot 一次」（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L152-L186)）。这段重路由是全部兼容层里最复杂、也最容易埋坑的一处（见 §3.6.6）。
- **405 语义不同**：axum 原生 405 空体 + `Allow`，需要一层翻译成 Java 的 HTTP 200 + `{"msg":"Request method 'POST' not supported","code":500}`（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L51-L70)）。
- **同一路径多方法必须共用参数名**：Java 的 `{id}`/`{ids}` 差异被迫统一，对客户端无影响，但迁移时要记得（README §6 已记录）。

**结论**：axum 是正确选择。若用 actix-web，上述 3 处兼容层依然要写，而 tower 生态与 `MatchedPath` 的便利会失去。rocket 的显式路由/公平性模型更难做「全局元数据查表」；poem/salvo 偏 OpenAPI 优先，对本项目没有增益。

#### 2.2.2 数据库访问：sqlx + 手写 SQL vs sea-orm / diesel / rbatis

**当前为什么只能这么选**

- 本项目有 75 个 Mapper XML、481 条 SQL、`<if>` 动态条件、`${tableName}` 动态表名、PageHelper 的 `select count(0) from (原 SQL) tmp_count`、按月的物理分表（2025-01～2099-12，最多约 900 张物理表）。这些都不是 ORM 的舒适区。
- `support::query_list` 用同一个 `QueryBuilder` 先渲染 count 再渲染分页查询，避免 `.sql()` 二次绑定占位符翻倍的坑（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L400-L441)），这类细节只有手写 SQL 能精确控制。
- 动态行→JSON（[rows.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/db/rows.rs#L35-L139)）让 60+ 张宽表不必逐列写实体，代价是类型安全为零。

**代价（真实技术债）**

- **0 处编译期 SQL 校验**：`sqlx` 的 `macros` feature 已开，但没有任何 `query!`。202 条 SQL 的列名/类型错误只能在运行时暴露；好消息是双端对拍基本覆盖了 GET 路径。
- `rows.rs` 按 `type_info().name()` 的字符串匹配（`"INT UNSIGNED"`、`"TINYINT"`…）来选解码器，遇到新的 MySQL 类型/版本差异会落到 `null` 兜底（README 已记录 TIMESTAMP 那次事故）。
- 用 `information_schema` 在运行时过滤请求体里的非列字段（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L870-L934)）是「让前端 `params` 能提交」的实用解，但把「实体字段→列」的契约从编译期推到了运行期。

**替代方案评估**

| 方案 | 对本项目的适配度 | 主要问题 |
|---|---|---|
| sea-orm | 低 | 动态物理表名、`${}`、PageHelper count 都要退化到 `raw_sql`；引入大依赖但收益有限 |
| diesel / diesel-async | 低 | 需要为 84 张表 + 900 分片建 schema，且动态 SQL 表达力不足 |
| rbatis | 中 | 动态 SQL 像 MyBatis，但生态/维护与 `Send` 约束风险高于 sqlx |
| **sqlx（现状）** | **高** | SQL 控制力最强；缺编译期校验 |

**建议**：保留 sqlx 与手写 SQL；在登录、用户详情、字典等**高频稳定查询**上加 `query!`/`FromRow` 做类型护栏，不要全面改 ORM。

#### 2.2.3 序列化：serde 复刻 Jackson vs 直接 serde

- 现状是「为字节级对拍付出的兼容税」：`AjaxResult` 用 Java `HashMap` 桶序重排（[response.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/response.rs#L113-L137)），实体按 Java 声明顺序重排，`Properties` 另有 Hashtable 序。这不是「过度设计」，而是把「键顺序也是契约」当成验收标准后的必然结果。
- 成本：每次 `AjaxResult` 序列化都克隆+排序（对象很小，可接受）；`reorder_rows` 在宽表大列表上会多一次 Map 重建；`float_roundtrip` 保证 `115.86275068219831` 不被写成 `…32`，是解决实际 FAIL 的正确手段（[docs/03-INTERFACE-VERIFICATION.md](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/docs/03-INTERFACE-VERIFICATION.md) §4）。
- 替代方案（默认 serde、simd-json）都会破坏键序/浮点字面量对拍，**不建议换**。若后续放弃字节级对拍，可移除这套排序逻辑并用 `#[serde(rename_all)]` 简化。

#### 2.2.4 认证：jsonwebtoken + bcrypt vs 现成框架

- 选型没问题：必须兼容 jjwt 0.9.1 的 HS512 与 secret 解码怪癖，`jsonwebtoken` 允许手工构造 key（[jwt.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/auth/jwt.rs#L60-L118)），比 `jwt-compact`/`oauth2` 更合适。
- 安全链是自研的，顺序复刻得相当细（401 AjaxResult vs 403 `/error` 页、`anonymous()` 命中已认证返回 403 等，[security.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/auth/security.rs#L25-L71)）。代价是没有审计过的成熟安全框架，后续加功能（限流、会话并发控制）都要自己写。

> **一处需要澄清的「看起来缺失」**：Java 的 `SysPasswordService`（登录失败次数锁定）在本仓库**没有任何调用方**（全仓只有类定义，`pwd_err_cnt` 也只出现在常量定义里）。因此 Rust 不实现失败锁定是**正确的 1:1 对齐**，不是缺陷；Rust 里遗留的 `PWD_ERR_CNT_KEY` 常量（[constants.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/constants.rs#L31-L32)）只是无害的僵尸常量。

#### 2.2.5 缓存：redis-rs ConnectionManager vs bb8/deadpool

- `ConnectionManager` 是单条多路复用连接 + 自动重连，克隆成本极低（[redis_cache.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/db/redis_cache.rs#L17-L19)）。这与 Java 侧 Lettuce 的默认模型一致，**属于忠实复刻而不是偷懒**。
- 风险在于**队头阻塞**：`keys(pattern)`（[redis_cache.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/db/redis_cache.rs#L136-L140)）、`lrange(key,0,-1)`、`INFO` 都跑在同一条连接上；`/base/cdc/*` 有 4 处 `KEYS`，大 key 空间下会同时拖慢所有请求。Java 侧同样是单连接，所以这是「一致性换性能」，不是 Rust 独有缺陷。
- `redis.timeout: 10s` 解析后未使用：连接/命令没有超时，Redis 卡住会挂住请求。这是一个**真实的配置缺口**（低概率、高影响）。
- bb8/deadpool 能缓解队头阻塞，但会引入「多连接下 Java 侧看不到的并发语义」；除非放弃与 Java 的等价性，否则不建议改。

#### 2.2.6 日志：tracing vs log+env_logger

- `tracing` 支持 span/结构化字段，是正确方向；但当前只做了「stdout + 按天文件」两路输出（[main.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/main.rs#L48-L83)），`log.max-history`/`log.max-file-size` 解析了却没用（[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L308-L315)），`json` feature 也没开。结果：**日志文件会无限增长**，与 logback 的滚动/保留行为不一致。
- 与 Java 的 `SqlLogInterceptor` / `MetricCollector` / `AlertEngine` 对应，Rust 完全没有慢 SQL/慢请求采集；`monitor.*`（[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L279-L290)）是死配置。
- `log`+`env_logger` 更轻但没有 span，不建议退回；若要补齐滚动策略，`flexi_logger`/`tracing-appender` 的带保留策略构造器都可以，不必换生态。

#### 2.2.7 调度：自研 Quartz 复刻 vs tokio-cron-scheduler

- **自研 cron 是对的**：Quartz 的 `?`、第 8 段被丢弃、年份越界、`0 0 2 * * MON` 等语义，第三方 cron 库基本都对不上；[quartz_cron.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_cron.rs) 的 37KB 换来了可验证的行为等价。
- 但运行时（[quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L215-L236)）只是「每任务一个 `tokio::spawn` 循环」：没有超时、没有 panic 后的重启、没有 supervisor；`misfire_policy` 只做合法性校验，执行行为统一是「跑完立刻补下一次」（[quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L174-L206)），与 Quartz 的 IGNORE/DO_NOTHING 不等价。
- `tokio-cron-scheduler` 只能省掉 `run_loop` 的几十行，仍要自己写 Quartz 解析和 `sys_job` 注册表，收益小、语义损失大。

#### 2.2.8 Excel：rust_xlsxwriter + calamine vs umya-spreadsheet

- 纯 Rust 不可能复刻 POI 的完整样式/公式/模板能力；当前策略是「值对齐、结构对齐，二进制不必逐字节一致」，`gen_zip` 也已明确 STORE vs DEFLATE 的差异，这是务实取舍。
- 风险：导出模板从 EasyPOI 模板改成「新建工作簿 + 列顺序对齐」，遇到依赖模板样式/合并单元格的下游流程会有观感差异；导入侧则要自己复刻 POI 的日期序列号、`#.##`、`break/结束` 等规则，[import_util.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/import_util.rs) 已经做了，但仍建议保留对拍样本。
- `zip = "=2.2.2"` 是 calamine 的签名约束，锁死版本会阻塞安全更新；建议在 calamine 升级时一起解锁。

#### 2.2.9 HTTP 客户端：reqwest vs awc/ureq

- reqwest 选择正确；`forest.max-connections` 映射成 `pool_max_idle_per_host`（[state.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/state.rs#L61-L66)）只是近似（不是总连接上限）。Java yml 实际是 `max-connections: 1000` / `max-route-connections: 500`（[application.yml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-admin/src/main/resources/application.yml#L182-L192)），Rust 配的是 `500`，语义上更接近 per-route，但 README「值一致」的说法不成立。
- 重试只在 `task/remote.rs` 手写了 `retry_count+1`，`road_path`/`hen_da`/`oss_client` 走的是另一套调用；Forest 的全局重试语义没有统一封装，属于中低风险的不一致。

#### 2.2.10 配置：config crate vs figment

- `config` 足够；真正的问题不是库，而是**配置与代码脱节**：`app.scheduler_enabled`、`app.kafka_enabled`、`app.elasticsearch_enabled`、`app.oss_enabled`、`monitor.*`、`log.max-*`、`xss.*`、`upload.*`、`database.pool.connect_timeout/socket_timeout`、`redis.timeout` 全部只反序列化、不参与运行（见 §3.7）。
- 这类「看着能配、实际无效」的键比缺配置更危险，运维会据此做错误决策。

#### 2.2.11 其它：validator / 并发原语 / 依赖卫生

- `validator 0.19` 声明但**0 引用**；`once_cell`、`chrono-tz` 同样 0 引用；`hyper`、`bytes` 作为直接依赖也没有实际 import（类型来自 axum/http）。
- `parking_lot` 只用于 `/test` 的内存表；`dashmap` 只用于路由元数据。
- `kafka`/`oss`/`templates` 三个 feature 均未接线（`templates` 的 minijinja 也没有使用；代码生成用的是自研 velocity）；`rdkafka` 在 Windows 上编不过（README 已记录）。
- 结果：476 个包、更长的冷编译、更大的供应链审计面，换来的运行能力为零。

**选型总结（3 句）**

1. **axum + sqlx + serde + redis-rs + tracing 这套组合，对这个「复刻 Spring 语义」的项目是贴合度最高的组合**，替换任何一项都会丢掉关键的语义控制力。
2. 真正的选型代价不在库，而在**兼容层**（axum 的 405/尾斜杠/404 页）和**运行时形态**（同步重活、全量缓冲、单连接 Redis）。
3. 依赖清单里有明显的「声明了但没用」项，说明依赖是随切片增长堆上去的，需要一次清理。

---

## 3. 迁移质量评价

### 3.1 分层与模块组织

**已验证事实**

- 目录按 Java 包结构切：`api/{system,monitor,quartz,tool,common,base,manager,flow,generator}` + `auth`/`db`/`domain`/`repository`/`service`/`task`。100 个 API 文件按 9 个切片组织，对应 Java 79 个 Controller 的粒度，**文件头都写了「来源/职责/对应关系」**，可追溯性很好。
- `repository` 只有 4 个文件 / 429 行，绝大多数 SQL 直接写在 handler 所在文件（`sys_user.rs` 1,552 行、`gen.rs` 1,444 行、`support.rs` 1,327 行）。
- 11 个单表 CRUD 用 `manager_crud!` 宏生成（[shared.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/manager/shared.rs#L10-L187)），减少了重复。

**判断**

- 「Controller + Service + Mapper」三合一，是**1:1 切片迁移的合理代价**：MyBatis XML 的 `<if>` 与 Java service 的分支交错，强行拆 service/repository 反而要跨文件追语义。文件头注释 + 与 Java 方法名一一对应，弥补了分层弱化。
- 但 `sys_user.rs` 1.5k 行、`gen.rs` 1.4k 行、`velocity.rs` 1.5k 行已经到了「改一处要读半天」的程度；`repository` 名存实亡（4 个文件里 3 个是特定领域），说明后续演进没有清晰落点。**这是技术债，不是当前缺陷。**

### 3.2 错误处理与 AppError 收敛

**已验证事实**

- 9 个变体覆盖 Java 的异常族，`IntoResponse` 统一转 `AjaxResult`，401/403 单独设 `application/json;charset=utf-8`，NPE 用 `Internal(None)` 输出 `{"msg":null}`（[error.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/error.rs#L13-L125)），非常贴合附录 E 的实测。
- 405 翻译层与 404/403 错误页分别处理「MVC 异常」与「Spring Security sendError」两条路径（[error.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/error.rs#L165-L203)）。
- `From<sqlx::Error>` 一律落 `Database(String)`，`From<anyhow::Error>` 落 `Internal`（[error.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/error.rs#L141-L163)）。

**问题**

- 数据库错误丢失 SQLSTATE 分类，所有 DB 错误都是 code 500；这与 Java 的 MyBatis 包装一致（README 已记为已知偏差），但意味着**无法在应用层区分「唯一键冲突/死锁/表不存在」**做重试或友好提示。
- `Database(msg)` 会把底层错误文本直接回给客户端（Java 亦然）。在灰度期可接受，生产上建议日志保留完整、响应脱敏——**这会改变 Java 文案，属于需谨慎的改动**。
- `Internal(Option<String>)` 的设计很巧，但 `From<anyhow::Error>` 会把启动期的任何上下文错误变成 500 文案，若未来在请求路径里用 `anyhow` 会丢分类。

**判断**：整体属于**良好收敛**；`Database` 分类缺失是技术债，不是实现缺陷。

### 3.3 异步与连接池

**已验证事实**

- 连接池参数按 Java Druid 映射：`maxActive=200`、`minIdle=10`、`maxWait=60s`（[state.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/state.rs#L48-L53)），会话时区按 JDBC `serverTimezone` 覆盖 SQLx 默认（[state.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/state.rs#L41-L46)），这是本轮最有价值的修复之一。
- **全仓 0 处 `spawn_blocking`**。同步重活分布在：
  - `bcrypt::verify`（默认 cost 12，单次约几十到上百毫秒）直接在 handler 里跑（[password.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/auth/password.rs#L10-L16)），登录与改密都会触发；
  - Excel 生成/写入（[excel.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/excel.rs#L27-L83)）与 `std::fs::write`（[common.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/common/common.rs#L145-L153)）；
  - ZIP 生成（`gen_zip.rs`）、Velocity 渲染（`velocity.rs`）、OSS SigV4 计算。
- `@Log` 中间件把请求体最多 16MB、响应体最多 64MB 全量读入内存再重建（[meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L28-L33)、[meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L199-L233)）。
- 未显式配置 `DefaultBodyLimit`：axum 的 body extractor（含 `Multipart`）走 **2MB 默认上限**（`with_limited_body` 的 `DEFAULT_LIMIT = 2_097_152`，axum-core 0.5.6 源码），与 Java `max-file-size: 40MB`/`max-request-size: 200MB` 不一致；而 `field.bytes()` 一旦放开上限就会把整个文件读进内存（[sys_file.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_file.rs#L385-L399)）。

**判断**

- **同步重活占 worker** 是真实的技术债：tokio 默认 worker 数 = CPU 核数，Java 侧是 200 线程的 Servlet 池。8 核机器上 8 个并发的 40MB 导出或 8 个 bcrypt 登录就能把请求处理拖住（**影响幅度是推断，代码形态是事实**）。
- **@Log 全量缓冲**对「列表 + 小 JSON」无害，但 manager 的二进制导出也挂了 `@Log`，64MB 上限 + 二次拷贝在高并发下会放大内存峰值。Java LogAspect 对响应主要是 `JSON.toJSONString` 小对象，且导出走 `HttpServletResponse` 流，形态更省。
- **上传/JSON body 的 2MB 默认上限**是「Java 40MB/200MB，Rust 2MB」的直接缺口（见 §3.6.7）；调大上限后需要自己加内存闸门。

### 3.4 事务边界与一致性

**已验证事实（做得好的部分）**

- `sys_user` 新增/修改/删除都是 `state.db.begin()` → `&mut tx` → `commit`，关联表 `sys_user_role`/`sys_user_post` 与主表在同一事务（[sys_user.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_user.rs#L1226-L1232)、[sys_user.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_user.rs#L1285-L1301)、[sys_user.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_user.rs#L1348-L1372)）。
- `sys_role` 授权、`sys_dept`、`sys_profile`、`gen` 的导入都正确使用 `&mut tx`/`&mut *tx`（agent 抽查 + 我复核 `sys_role.rs`）。
- `sys_job` 的增改/启停把「数据库事务」和「调度器注册」的 Java 语义复刻得非常细：`misfire_policy=null` 的 NPE 才回滚，checked 异常提交但返回错误，调度注册不被事务管辖（[job.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/quartz/job.rs#L420-L450)、[job.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/quartz/job.rs#L556-L580)）。这不是「照着写」，而是真的理解了 Java 的回滚规则。
- 批量写入 `snapshot_flow_repo::insert_batch_to_table` 用 `pool.begin()` + 分块 `push_values` + `INSERT IGNORE`，并有表名白名单（[snapshot_flow_repo.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/repository/snapshot_flow_repo.rs#L82-L146)），质量高于多数手写迁移。

**问题**

1. `task/manager_sync.rs::replace_table` 是 `truncate table` 后逐行 `insert`，**没有事务**（[manager_sync.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/task/manager_sync.rs#L127-L139)）。中途失败会留下「空表或半张表」。Java 对应的同步任务是否事务化需要按 Java 源码核对；从形态看大概率也没有，因此更接近**合理代价**，但 N 行 = N 次往返是可优化的性能债。
2. `sys_file` 的上传是「先 `file_log` 写库，再 `store_file` 落盘」（[sys_file.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_file.rs#L402-L431)）；Java `SysFileServiceImpl.uploadFiles` 也是 `fileLog` → `putObject`（[SysFileServiceImpl.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysFileServiceImpl.java#L202-L205)），顺序一致，落盘失败都会留下孤儿 DB 行。**属合理代价（低影响）**。
3. DB 写 + Redis 缓存刷新天然非原子（`car_info` 保存后刷 `car_list`）。Java 同样如此，**属合理代价**；缓存窗口期由下一次读取回源修复。
4. `support::insert_entity` 的自动填充会无条件追加 `id/create_time/create_by/eps_id/tenant_id`，`update_entity_by_id` 会无条件追加 `del_flag='0'`（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L971-L1005)、[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L1140-L1143)），**不校验目标表是否真有这些列**。当前使用 `audit=true` 的表恰好都有这些列（DDL 抽样核对），但这是一颗埋给未来新表的雷。

**判断**：事务边界整体**忠实且质量高**；`replace_table` 的逐行写是性能债；`insert_entity` 的列假设是低概率技术债。

### 3.5 SQL 与分页实现

**已验证事实**

- `PageDomain::from_map` 的默认值、`isAsc` 归一、`reasonable` 语义（[page.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/page.rs#L48-L137)）与 PageHelper 对齐；`orderByColumn` 走 Java `SqlUtil.SQL_PATTERN` 的字符白名单与 500 长度上限（[page.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/page.rs#L100-L114)）。
- count 查询用 `select count(0) from (<原 SQL>) tmp_count`，分页用 `limit ? offset ?`，两者共用同一个 builder，参数不会重复（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L406-L439)）。
- 动态 SQL 的 `Filter` 抽象覆盖 `eq/like/likeRight/gt/ge/lt/le/raw`，`raw` 只允许静态 SQL 片段 + 单值绑定（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L231-L375)）。
- 动态标识符有校验：`checked_table`/`checked_identifier` 只允许字母数字下划线（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L1306-L1328)）；分表表名走 `validate_table_name`（[snapshot_flow_repo.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/repository/snapshot_flow_repo.rs#L148-L160)）；`flow_current_node` 的 `backCol1` 动态表名也先 `valid_identifier`（[flow_current_node.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/flow/flow_current_node.rs#L282-L303)、[flow_current_node.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/flow/flow_current_node.rs#L340-L346)）。
- 数据权限 SQL 内联的是登录态里的数字 `role_id`/`dept_id`/`user_id`（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L163-L212)），**不是外部可控字符串**，注入风险可接受。

**问题**

- `query_all`（导出）不分页，宽表大结果集会一次性 `fetch_all` 进内存再转 JSON；Java 导出同样是全量，但 POI 是流式写，Rust 是「先全量 Value 再写 xlsx」，内存形态更差（技术债）。
- `query_by_id` 用 `format!` 拼静态 `select/from/id_column`（[support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L804-L816)），因为片段全是 `'static` 常量，**不构成注入**；但形态上容易被后人误用。
- 未发现外部可控制的 SQL 拼接：所有 `format!` 进 SQL 的地方，要么是常量列清单，要么经过标识符白名单，要么是服务端配置。

**判断**：分页与 SQL 语义**忠实度高**；`query_all` 内存形态是性能债。

### 3.6 鉴权与中间件

#### 3.6.1 做得好的部分

- 认证链顺序正确：`web_filter（最外）→ CORS → auth → @PreAuthorize/@Log → 405 翻译 → 路由`（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L125-L147)）。
- `/logout` 在鉴权前处理（LogoutFilter 语义）；`anonymous()`/`denyAll()` 命中已认证时返回 403 `/error` 页而不是 AjaxResult；401 的文案含请求路径（[auth.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/middleware/auth.rs#L23-L68)、[security.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/auth/security.rs#L25-L71)）。
- 权限点与 `@Log` 由路由元数据统一执行，239 条日志、284 条权限只实现一次（[meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L152-L290)）。
- 审计写入用 `tokio::spawn` + 10ms 延迟，失败只打日志，不阻塞主流程（[audit.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/auth/audit.rs#L81-L114)）。

#### 3.6.2 【高】数据权限的实际生效面与 Java 相反：`sys_dept` 多过滤

**已验证事实**

- Java `DataScopeAspect` 是 `@Aspect` + `@Component`，`@DataScope` 确实会往查询对象的 `params.dataScope` 写 SQL（[DataScopeAspect.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/DataScopeAspect.java#L27-L67)）。
- 但真正把 `${params.dataScope}` 拼进 SQL 的 mapper **只有 `SysRoleMapper`**（[SysRoleMapper.xml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml#L51-L52) 是独立的一行）；`SysUserMapper` 与 `SysDeptMapper` 里的同一片段写在 **XML 注释**里（[SysUserMapper.xml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml#L209)、[SysDeptMapper.xml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml#L97)），MyBatis 不会插值注释内容。
- 结论（已验证）：Java 的 `/system/user/list` 与 `/system/dept/list` 对非 admin **没有任何数据范围过滤**；只有 `/system/role/list` 有。`SysUserServiceImpl`/`SysDeptServiceImpl` 上的 `@DataScope` 是**空转**的。
- Rust：`sys_role` 正确应用（[sys_role.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_role.rs#L232-L264)）；`sys_user` 未应用（与 Java 一致）；但 `sys_dept` **应用了**（[sys_dept.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_dept.rs#L175-L177)），且 6 个调用点覆盖 7 条路由：`/system/dept/list`、`/getList`、`/list/exclude/{deptId}`、`/treeselect`、`/treeselectNew`、`/roleDeptTreeselect/{roleId}`、`/getCompanyList`（[sys_dept.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_dept.rs#L244-L342)）。

**影响**

- 非 admin 调用 `/system/dept/list`、`/getList`、`/list/exclude/{deptId}`、`/treeselect`、`/treeselectNew`、`/roleDeptTreeselect/{roleId}`、`/getCompanyList` 时，Rust 会按角色数据范围裁剪部门，Java 返回全部部门。表现为「部门树少了节点/下拉选项变少」——不是越权，而是**过度限制**，属于行为偏离。
- `/system/user/list` 两侧都不过滤，所以「非 admin 看到全部用户」**不是 Rust 缺陷**，而是 Java 自身把 `${params.dataScope}` 注释掉的历史 bug；Rust 照抄是对的。
- 与 admin 对拍无法发现此差异（admin 的 `data_scope=1` 直接跳过过滤）。

**判断**：`sys_dept` 属**实现偏差（多做了 Java 未生效的过滤）**；`sys_user`/`sys_role` 对齐。修复方向是**移除 sys_dept 的过滤**（恢复 Java），而不是给 sys_user 加过滤。若产品确实希望 dept 有数据权限，需把它当作有意偏离写进 README §6，并同时改 Java 侧，否则就不是 1:1。

#### 3.6.3 【中】XSS 过滤器未迁移

**已验证事实**

- Java：`FilterConfig` 在 `xss.enabled=true` 时注册 `XssFilter`（`HIGHEST_PRECEDENCE`），`application.yml` 里 `xss.enabled: true`，`urlPatterns: /system/*,/monitor/*,/tool/*`，`excludes: /system/notice`（[FilterConfig.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-framework/src/main/java/com/ruoyi/framework/config/FilterConfig.java#L29-L44)、[application.yml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-admin/src/main/resources/application.yml#L155-L162)）。
- `XssHttpServletRequestWrapper` 对 JSON body 整体 `EscapeUtil.clean`（去 HTML 标签），对参数值 `clean + trim`；GET/DELETE 跳过（[XssHttpServletRequestWrapper.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/filter/XssHttpServletRequestWrapper.java#L30-L66)、[XssFilter.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/filter/XssFilter.java#L58-L68)）。
- Rust：`config.rs` 只是反序列化 `xss`（[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L292-L298)），全仓无任何 HTML 清洗代码；`web_filter` 只加了 `X-XSS-Protection` 响应头（[web_filter.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/middleware/web_filter.rs#L51-L54)）。

**影响**

- 含 `<...>` 的 JSON 字段（备注、名称、通知内容等）在 Java 会被剥掉标签后入库，Rust 原样入库 → **同一个请求两端存储不同**；对前端展示与后续导出都有影响。
- 也失去了一层输入侧防御。

**判断**：**实现缺陷（行为不一致）**，优先级中高。修复需先移植 `HTMLFilter` 的清洗规则，注意「只去标签、保留标签外文本」，并只对 `application/json` 且匹配 pattern、非 GET/DELETE、非 multipart 的请求生效。

#### 3.6.4 【中低】`@RepeatSubmit` 未迁移

- Java `SysConfigController.add` 有 `@RepeatSubmit`（[SysConfigController.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java#L77-L81)），`ResourcesConfig` 注册 `SameUrlDataInterceptor` 全路径拦截。
- Rust 全仓无 `repeat_submit`/`RepeatSubmit` 相关代码（grep 0 命中）。
- 影响：5 秒内重复 `POST /system/config` 在 Java 返回「不允许重复提交，请稍候再试」，Rust 会真的插入两条。**低概率、可复现**。

#### 3.6.5 【中】`/oss/**` 默认被注册，而 Java 默认不注册

**已验证事实**

- Java：`OssEndpoint` 只在 `@ConditionalOnProperty(name="oss.info", havingValue="true")` 时创建 Bean（[OssAutoConfiguration.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/config/OssAutoConfiguration.java#L32-L36)）；`application.yml` 的 `oss:` 段没有 `info` 键 → 默认 404。
- Rust：`build_api_routes` 无条件 `.merge(api::oss::routes())`（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L107-L108)），`config/application.yaml` 里 `oss.info: false`（[application.yaml](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/config/application.yaml#L81-L90)）。
- README/docs 口径是「`/oss/**` 默认不注册（`oss.info=true` 时注册）」（[01-MIGRATION-BASELINE.md](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/docs/01-MIGRATION-BASELINE.md) §0.5、[README-MIGRATION.md](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/README-MIGRATION.md) §6），**与代码矛盾**。

**影响**：默认部署下 Rust 多出 9 条可控 S3 端点（需登录），Java 是 404；调用会打向配置里的 MinIO（不可达时 500）。既是行为差异，也是攻击面扩大。

#### 3.6.6 【低】404 响应可能绕过最外层中间件（推断，待一次 curl 复核）

- `build_router` 先 `fallback(any(fallback))`，再 `layer(...)` ×5，最后又 `router.fallback(retry_with_trimmed_trailing_slash)`（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L125-L157)）。
- axum 0.8.9 的 `Router::layer` 只包装**当时已存在**的 `path_router`/`fallback_router`/`catch_all_fallback`；`Router::fallback` 之后再设置的是**未被层包住的新 fallback**（`fallback_endpoint` 直接 `set_fallback`）。因此「非尾斜杠的未匹配请求」会直接走 `not_found_response`，**不经过 `web_filter`/CORS**。
- 后果（推断）：404 响应缺少 `X-Trace-Id`、`nosniff`、`X-XSS-Protection`、`Vary: Origin`；与 docs/03 §10.4「每条响应都带」的结论冲突。带尾斜杠且重路由成功的请求会走完整链，不受影响。
- 建议：把 404 的内层 helper 也手动套上 `web_filter` 的头，或把 fallback 设置移到 `.layer()` 之前、尾斜杠重试改为在 fallback 内直接构造带头的响应。**这是一次 `curl -i /nope` 就能确认的项**。

#### 3.6.7 【高】上传缺少扩展名白名单、文件名清洗，且体积上限与 Java 不一致

**已验证事实**

- Java `FileUploadUtils.upload` 用 `DEFAULT_ALLOWED_EXTENSION` 校验扩展名，`extractFilename` 用 `FilenameUtils.getBaseName` 去掉路径并用序列号重命名（[FileUploadUtils.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java#L61-L81)、[FileUploadUtils.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java#L123-L126)、[FileUploadUtils.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java#L168-L169)）。
- Java `spring.servlet.multipart.max-file-size: 40MB`、`max-request-size: 200MB`（[application.yml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-admin/src/main/resources/application.yml#L77-L81)）。
- Rust `/common/upload`/`/common/uploads` 直接用客户端文件名拼路径，**不校验扩展名**（[common.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/common/common.rs#L127-L143)、[common.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/common/common.rs#L156-L219)）；`upload.*` 配置只解析不生效（[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L300-L306)）；全仓无 `DefaultBodyLimit` 配置，实际生效的是 axum 的 **2MB 默认上限**，`field.bytes()` 在放开上限后会全量进内存（[sys_file.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_file.rs#L385-L399)）。

**影响**

1. 可上传任意后缀（`.jsp`/`.svg`/可执行文件），若 `/profile` 静态目录可访问则是存储型风险；
2. `original` 里的 `../` 会被拼进 `PathBuf`，**可写出上传目录之外**（认证用户）；
3. 实际生效的上限是 axum 默认 **2MB**（未配置 `DefaultBodyLimit`），**小于** Java 的 40MB/200MB：合法的 3MB 车辆照片/附件在 Rust 会在 extractor 层失败（本项目把 rejection 映射成 HTTP 200 + code 500，文案类似 `length limit exceeded`），Java 则正常落盘；若简单调大，`field.bytes()` 又会把整个文件读进内存。
4. 同一限制也作用于所有 `Json<T>` 端点（axum `Json` 经 `Bytes` → `into_limited_body`）：>2MB 的 JSON 在 Rust 会先失败（同样 HTTP 200 + code 500），而 Java 的 `max-request-size` 是 200MB；若有批量轨迹/流程 JSON，这是功能性差异。

`/system/file/upload*` 系列已用 UUID 文件名 + `ALLOWED_EXT`（[sys_file.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_file.rs#L224-L240)），是安全的；问题集中在 `/common/upload*`。

**判断**：**实现缺陷 + 安全风险**，高优先级。

### 3.7 配置与启动流程

**已验证事实（对齐的部分）**

- 大部分键名与默认值一致：`server.port=9989`、`ruoyi.profile`、`token.*`、`database.*`、`redis.*`，且内嵌 YAML 保证磁盘文件缺失时仍有默认值（[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L13-L18)、[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L361-L378)）。例外见下方问题 2（`redis.database` 与 `forest.max-connections`）。
- JDBC URL 的 `serverTimezone=GMT+8` 被解析成 MySQL `SET time_zone`，修复了 `timestamp(3)` 的 8 小时偏差（[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L422-L445)），并有单测。

**问题**

1. **大量配置只解析不生效**（grep 结果）：`app.scheduler_enabled`、`app.kafka_enabled`、`app.elasticsearch_enabled`、`app.oss_enabled`、`monitor.slow_*`/`enabled`/`trace_header`、`log.max_history`/`max_file_size`、`xss.*`、`upload.*`、`database.pool.connect_timeout`/`socket_timeout`、`redis.timeout`、`forest.retry_count`（只有 `task/remote.rs` 用）；`ruoyi.addressEnabled` 虽被读取，但 `real_address` 无论开关都返回回退值 `XX XX`（[utils.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/utils.rs#L77-L87)）。
2. **README 与配置不一致**：README §2 写 `redis.database` 默认 `0`，`config/application.yaml` 是 `15`（[application.yaml](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/config/application.yaml#L35-L44)），`.env.example` 也写 `0`。按 README 配会连到 Java 的 db0，破坏「两端分库」的拓扑假设。另外 `forest.max-connections` Java 是 1000、Rust 是 500（映射为 per-host），README 的「键名/默认值一致」并不成立。
3. `.env.example` 的 `APP_DATABASE__URL=mysql://root:root@127.0.0.1:3307/...` 与 `mysql_endpoint()` 的「jdbc URL 解析」假设不一致；密码含 `@`/`:` 时会解析错（推断）。
4. 明文密钥入库：`config/application.yaml` 含 DB root 密码、OSS access/secret、恒达 secret（与 Java 侧一致，但仍是风险）。
5. 启动**没有 schema 迁移/校验**：`sqlx` 的 `migrate` feature 开了但 0 处 `migrate!`；表不存在时启动成功、首个请求 500。Java 也是外部 DDL，但 Rust 若部署到新环境容易踩空。
6. 优雅停机只监听 Ctrl-C（[main.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/main.rs#L85-L88)），**没有 SIGTERM**；容器/K8s 滚动发布时会硬切，可能在事务/落盘中被杀。`/health` 只 `select 1`（[state.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/state.rs#L79-L83)），不检查 Redis。

### 3.8 定时任务与后台线程

**已验证事实**

- 6 个 `@Scheduled` 的 cron 与 Java 注解逐字一致，`start_scheduler` 逐个 `tokio::spawn`（[task/mod.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/task/mod.rs#L116-L139)）；`run_loop` 是「算下次→sleep→执行→以当前时间为基准再算」（[task/mod.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/task/mod.rs#L141-L159)）。
- `sys_job` 的注册表按 Java `JobKey(jobId, jobGroup)` 建模，暂停只移除句柄、保留注册；启停/新增/删除与 DB 事务的先后关系复刻得很细（§3.4）。
- `quartz_cron` 有 5 个单测覆盖 Java 的合法/非法表达式与 `?x` 等怪癖；`job_invoke` 复刻 `JobInvokeUtil` 的参数解析。
- `misfire_policy` 只在 `create_schedule_job` 做合法性校验（[quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L174-L206)），调度循环不区分 IGNORE/DO_NOTHING，统一「跑完立即补下一次」。
- `REGISTERED`/`LOOPS` 用 `std::sync::Mutex` + `.unwrap()`（[quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L28-L33)、[quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L217-L256)）。
- 两套调度（`@Scheduled` 与 `sys_job`）默认都开；本地 `sys_job` 快照的 19 行只有 `ryTask`/`vehicleMonitoringTask`/`trackTask`，**没有** 6 个 `@Scheduled` 目标，所以当前不会重复执行；但生产库若配置了同名 `invoke_target`，同一任务会被两套调度各跑一次（部署核对项）。

**问题**

- **panic 会静默杀掉任务**：`run_job`/`kind.run` 里没有 catch_unwind，tokio 任务 panic 后该 job 再也不触发，Java Quartz 会记录并继续。
- **无执行超时**：一个卡住的同步任务会占住该 job 的循环（也会占住 worker，见 §3.3）。
- **无 supervisor**：`JoinHandle` 存进 `LOOPS` 但从不观察退出；进程级没有停机时 join。
- `concurrent=0` 允许并发在 Java 中可重叠，Rust 串行（已在文件头记录，属已知偏差）。

**判断**：cron/注册表部分**忠实度高**；运行时监管是技术债；`misfire` 语义是未记录的已知偏差。

### 3.9 测试覆盖

**已验证事实**

- 94 个 `#[test]`，集中在纯函数：分页、JWT、cron、分片路由、GPS/polyline、Velocity、OSS SigV4、FastJson2 形状、导入规则、`route_parity`（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L188-L274)）。
- `route_parity` 用 [02-endpoints.md](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/docs/01-baseline/02-endpoints.md) 做「method + 路径形状」对拍，并断言 510 条、缺失/多余都失败，这是**非常好的回归护栏**。
- 没有 `tests/` 目录，0 个 HTTP 层测试、0 个 DB 集成测试、0 个事务/并发测试。
- 没有 CI 配置（仓内只有 `config/application.yaml` 一个 yml；无 `.github/workflows`）。
- 双端对拍依赖 `tools/endpoint_parity/*.py` + 运行中的 Java/MySQL/Redis，不在 CI 内。

**问题**

- 所有 handler（占代码 69%）没有单测；`route_parity` 只证明「路由注册了」，不证明「行为对」。
- 对拍以 admin 登录（[docs/03](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/docs/03-INTERFACE-VERIFICATION.md)），数据权限、非 admin 角色、错误分支（403/404/405 的响应头）覆盖不足。
- 关键并发/事务语义（如 `sys_job` 的 rollback/commit 分支）只有人工对拍，没有可重复测试。

**判断**：纯函数测试质量好，**整体覆盖是技术债**。至少要补：HTTP 层 smoke（可在 CI 用 mock state 或 testcontainers）、`sys_user` 数据权限用例、上传安全用例、404/405 头用例。

### 3.10 unsafe / unwrap / expect / panic

**已验证事实**

- `unsafe`：0。
- 非测试 panic 类调用 40 处，逐类核对：
  - **常量/不变量**：`db/sharding.rs` 的 `from_ymd_opt(...).expect("valid year")`、`period_start` 的 midnight（[sharding.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/db/sharding.rs#L78-L104)）；[serde_helpers.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/serde_helpers.rs#L95)；[import_util.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/import_util.rs#L92)（固定 1899-12-30）。
  - **逻辑不变量**：[sys_profile.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_profile.rs#L208) 的 `entity.as_object().unwrap()`（entity 刚由上方的 `Value::Object` 构造）；[car_info.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/manager/car_info.rs#L722) 等 `as_object_mut().expect("object")`（DB 行必为对象）；[menu_service.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/menu_service.rs#L41) 的 `slots[index].take().expect(...)`（索引来自同一结构）。
  - **锁**：[quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L51) 的 5 处 `Mutex::lock().unwrap()`；只有「持锁期间 panic」才会 poison，当前临界区都是简单集合操作，风险低。
  - **协议常量**：[redis_cache.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/db/redis_cache.rs#L242) 按 `char_len` 推进后的 `next()`；[oss_client.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/oss_client.rs#L331) HMAC `new_from_slice`；[ods_szdn_gantry.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/base/ods_szdn_gantry.rs#L250) 的 `Response::builder().status(200).body(...).unwrap()`。
- **没有发现可由外部请求直接触发的 panic**（这是优点）。但也没有 `CatchPanicLayer`：`tower-http` 的 `catch-panic` feature 已在 [Cargo.toml](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/Cargo.toml#L13-L20) 打开，却未使用（全仓无 `CatchPanic`）。一旦未来引入 panic，axum 会直接断连接，而不是 Java 的 500 JSON。

**判断**：现状**良好**；建议加 panic 兜底把「连接被断」变成 `{"msg":null,"code":500}`。

### 3.11 clippy / 依赖 / 体积

**clippy（实际运行）**

- 26 条 warning，全部风格类：`empty line after doc comment`、`unnecessary Ok/?`、`useless format!`、`&mut Vec` → `&mut [_]`、`manual range contains`、`contains_key` 后 `insert`、`redundant binding`、`err().expect()` 等。
- 0 条 correctness/suspicious，`cargo fmt --check` 也通过。说明代码在「能编译、格式一致且不踩常见坑」层面是干净的；没有 `-D warnings`/CI 强制。

**依赖（实际清单）**

- 476 个包；直接依赖里 `validator`/`once_cell`/`chrono-tz` 0 引用，`hyper`/`bytes` 无直接 import；`kafka`/`oss`/`templates` 三个 feature 未接线；`rdkafka` 在 Windows 编不过（README 记录）。
- `zip = "=2.2.2"` 版本钉死，会阻塞后续安全升级。
- release profile 有 `lto="thin"`、`codegen-units=1`、`strip="symbols"`，是正确设置；但**未构建 release，二进制体积未实测**（`target/` 只有 debug）。

**判断**：依赖卫生是**技术债**；clippy 是**风格债**，不影响正确性。

---

## 4. 问题清单（按优先级）

> 类型：**缺陷**=与 Java 行为不一致或安全/稳定性问题；**技术债**=可维护性/性能/运维；**合理代价**=为 1:1 对齐必须接受；**待确认**=证据不足。

| ID | 级别 | 问题 | 证据 | 类型 |
|---|---|---|---|---|
| H1 | **高** | `sys_dept` 列表多加了数据范围过滤（Java 的 `${params.dataScope}` 在 XML 注释里不生效） | Rust [sys_dept.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_dept.rs#L175-L177)；Java [SysDeptMapper.xml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml#L97)（注释）、[SysRoleMapper.xml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml#L51-L52)（生效） | 缺陷（偏离） |
| H2 | **高** | `/common/upload*` 无扩展名白名单、文件名可含 `../`；所有 body extractor 实际 2MB（Java 40MB/200MB） | Rust [common.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/common/common.rs#L127-L219)、[config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L300-L306)；Java [FileUploadUtils.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java#L61-L126)、[application.yml](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-admin/src/main/resources/application.yml#L77-L81) | 缺陷（含安全） |
| H3 | **高** | `/oss/**` 默认注册，Java 默认不注册；README 与代码矛盾 | Rust [lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L107-L108)；Java [OssAutoConfiguration.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/config/OssAutoConfiguration.java#L32-L36) | 缺陷 |
| H4 | **中高** | XSS 过滤器未迁移（JSON body/参数清洗缺失） | Rust [config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L292-L298)、[web_filter.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/middleware/web_filter.rs#L51-L54)；Java [XssHttpServletRequestWrapper.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-common/src/main/java/com/ruoyi/common/filter/XssHttpServletRequestWrapper.java#L30-L66) | 缺陷 |
| M1 | 中 | bcrypt/Excel/ZIP/fs 在 async 任务里同步执行，无 `spawn_blocking`/闸门 | [password.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/auth/password.rs#L10-L16)、[excel.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/common/excel.rs#L27-L83)、全仓 grep 0 | 技术债 |
| M2 | 中 | `@Log` 对最多 64MB 响应体全量缓冲 + 二次拷贝（含二进制导出） | [meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L28-L33)、[meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L226-L289) | 技术债 |
| M3 | 中 | 日志滚动上限/慢 SQL/慢请求/指标告警未接线 | [config.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/config.rs#L279-L315)、[main.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/main.rs#L48-L83)；Java `SqlLogInterceptor`/`MetricCollector` | 技术债 |
| M4 | 中 | 只有 Ctrl-C，无 SIGTERM；`/health` 不查 Redis | [main.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/main.rs#L85-L88)、[state.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/state.rs#L79-L83) | 技术债（运维） |
| M5 | 中 | 调度任务无 panic 重启/超时/misfire 语义 | [quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L215-L236)、[task/mod.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/task/mod.rs#L141-L159) | 技术债 + 已知偏差 |
| M6 | 中 | 无 HTTP/DB/事务集成测试、无 CI | 94 tests/32 files、无 `tests/`、无 CI 配置 | 技术债 |
| M7 | 中 | 202 条 SQL 无任何编译期校验 | `query!` 0 处、`query_as::<_,T>` 4 处 | 技术债 |
| M8 | 中 | Redis 单连接 + 无命令超时，`KEYS`/大 `LRANGE` 会队头阻塞 | [redis_cache.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/db/redis_cache.rs#L17-L19)、[redis_cache.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/db/redis_cache.rs#L136-L140) | 技术债（与 Java 同构） |
| M9 | 中 | `@RepeatSubmit` 未迁移 | Java [SysConfigController.java](file:///d:/work/IdeaProjects/car-monit-backend-new/ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java#L77-L81)；Rust grep 0 | 缺陷 |
| L1 | 低 | 404 响应可能缺少 TraceId/安全头/CORS 头 | [lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L125-L157) + axum 0.8.9 `Router::layer/fallback` 源码 | 缺陷（待 curl 确认） |
| L2 | 低 | 大量配置只解析不生效 | §3.7 | 技术债 |
| L3 | 低 | README/`.env.example` 的 Redis db、端口/URL 写法不一致 | [.env.example](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/.env.example#L5-L10)、[application.yaml](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/config/application.yaml#L35-L44) | 文档债 |
| L4 | 低 | 未使用依赖/未接线 feature | [Cargo.toml](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/Cargo.toml#L53-L100) | 技术债 |
| L5 | 低 | 26 条 clippy 风格告警 | clippy 输出 | 风格债 |
| L6 | 低 | `misfire_policy` 只校验不生效；`concurrent=0` 串行 | [quartz_runtime.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/service/quartz_runtime.rs#L174-L206) | 已知偏差（未文档化） |
| L7 | 低 | `insert_entity` 自动填充不校验列是否存在 | [support.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/support.rs#L971-L1005) | 技术债 |
| L8 | 低 | `manager_sync::replace_table` truncate + 逐行 insert，无事务 | [manager_sync.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/task/manager_sync.rs#L127-L139) | 合理代价 + 性能债 |
| L9 | 低 | ASCII/代理对细节：日志截断按 `chars` 而非 Java UTF-16 code unit | [meta.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/meta.rs#L313-L315) | 合理代价（边界极小） |

### 4.1 属于「忠实复刻 Java 的合理代价」（不应按缺陷处理）

| 项 | 说明 |
|---|---|
| 手写 Java `HashMap`/`Properties` 键序 | 为字节级对拍必须保留；去掉就改变契约 |
| jjwt 0.9.1 的 Base64 截断怪癖 | Java 实测行为，必须复刻 |
| FastJson2 `@type`/`L` 后缀/`Set[...]` | 灰度共存刚需 |
| 复刻 PageHelper `count(0) from (...)` | 先 count 再 limit，多一次查询，但语义一致 |
| 复刻 Java 自身 bug（`car_suspicious_back` 的 `id NULL`、`sys_job` NPE 回滚、`sys_user` 被注释掉的 `${params.dataScope}`） | 用户决策「Java 的 bug 照抄」；`sys_dept` 的例外见 H1（那是没照抄） |
| 8 个死代码类照样迁移（`legacy_sharding.rs`） | 用户决策 |
| 6 个 `@Scheduled` 在 Java 从未执行、Rust 启用 | 用户决策（2026-10-31） |
| ShardingSphere 未启用、Rust 启用 | 用户决策 |
| 无 POI 级 Excel 样式/模板 | 纯 Rust 的能力边界 |
| 清空 Redis 的 `KEYS` | Java 也是 `keys(pattern)` |
| 全量导出先 `fetch_all` | Java 导出也是全量，形态差异可接受 |

---

## 5. 优化建议（按优先级）

> 每条都标注「是否破坏 Java 一比一语义」。原则：**恢复 Java 已有行为 = 安全**；**改变 Java 行为 = 谨慎/需决策**。

### 5.1 高优先级（正确性/安全/稳定性）

#### H1. 移除 `sys_dept` 的多余数据权限（恢复 Java 行为）

- **落点**：`src/api/system/sys_dept.rs::select_dept_list`（[L175-L177](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/api/system/sys_dept.rs#L175-L177)）。
- **改法**：删掉 `support::data_scope_sql(user, "d", None)` 的调用。Java 的 `SysDeptMapper.xml` 把 `${params.dataScope}` 写在 XML 注释里，`@DataScope` 虽然执行了但 SQL 里没有它；`sys_role` 的过滤**必须保留**（Java 生效）。**不要**顺手给 `sys_user` 补过滤（它在 Java 里同样被注释掉）。
- **收益**：非 admin 的部门树/下拉/排除节点与 Java 一致，消除「选择器少节点」的隐性偏差。
- **对齐影响**：**恢复对齐**。
- **验证**：用非 admin（data_scope=2/3/4/5）双端对拍 `/system/dept/list`、`/getList`、`/list/exclude/{deptId}`、`/treeselect`、`/treeselectNew`、`/roleDeptTreeselect/{roleId}`、`/getCompanyList` 的 rows 数量与层级；admin 不受影响。
- **注意**：若产品确实希望 dept 有数据权限，这属于**有意偏离**，需要同时改 Java mapper 并写进 README §6，否则就不是 1:1。

#### H2. 上传安全（恢复 Java 校验 + 修路径穿越）

- **落点**：`src/api/common/common.rs`（`upload_path`/`upload`/`uploads`）；如需统一，`src/api/system/sys_file.rs` 的 `stored_name` 可复用。
- **改法**：
  1. 用 UUID + 白名单扩展名生成文件名（与 `sys_file` 的 `stored_name` 一致），**丢弃客户端路径**（只取 `file_name()` 的 basename）；
  2. 复用 `ALLOWED_EXT`（Java `MimeTypeUtils.DEFAULT_ALLOWED_EXTENSION`）；
  3. 给 multipart 路由单独加 `DefaultBodyLimit::max(40MB)`（axum 0.8 的 `Multipart` 走 `with_limited_body`，该层生效），总请求上限 200MB 可按路由/全局分别配置；同时在逐字段读取时检查累计大小，避免「上限放开后全量进内存」；
  4. **不要**全局把 `DefaultBodyLimit` 放到 200MB：先按实际业务找出可能 >2MB 的 JSON 端点（轨迹/流程提交等），只给这些路由单独放宽，其余保持小上限。
- **收益**：消除任意后缀上传、路径穿越、内存打满；与 Java 的 40MB/200MB、扩展名白名单一致。
- **对齐影响**：**恢复对齐**；唯一差异是恶意文件名的处理（Java 也会拒绝）。
- **验证**：`curl -F "file=@x.jsp"`、`-F "file=@../../evil.png"`、>2MB 与 >40MB 文件，双端对比状态与文案。

#### H3. `/oss/**` 按 `oss.info` 门控（恢复 Java 默认行为）

- **落点**：`src/lib.rs`。`api::oss::routes()` 当前在 `build_api_routes()` 里无条件 merge（[lib.rs](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/src/lib.rs#L107-L108)），需要把它移到 `build_router(state)` 并按 `state.settings.oss.info && state.settings.oss.enable` 条件 merge；`route_parity` 改为「默认不注册 / 显式开启时注册」两组断言。
- **收益**：默认部署不再暴露 9 条 S3 端点，与 Java 默认 404 一致；README 的「默认不注册」不再自相矛盾。
- **对齐影响**：**恢复对齐**。
- **注意**：`oss.enable=false` 时 Java 连 `OssTemplate` 都不创建，端点即使 `info=true` 也会启动失败；Rust 建议 `info && enable` 双条件。

#### H4. 移植 XSS 过滤器（恢复 Java 行为）

- **落点**：新增 `src/middleware/xss.rs`（或并入 `web_filter.rs`），放在 **`meta` 中间件之前**（可以位于 `auth` 内外，只要保证 body 在被 `@Log` 读取之前已清洗）。
- **改法**：
  - 仅对 `POST/PUT/PATCH`、`Content-Type: application/json`、路径匹配 `xss.urlPatterns` 且不命中 `xss.excludes` 的请求生效；
  - 读 body → 按 Java `HTMLFilter` 规则去标签/注释 → 回填 `Body`（同时把 `Content-Length` 设为新长度）；
  - 对 query/form 参数值做 `clean + trim`（Java 的 `getParameterValues` 包装）；
  - multipart 跳过（Java 对非 JSON 直接返回原流）。
- **收益**：同一请求两端入库值一致；恢复输入侧防御。
- **对齐影响**：**恢复对齐**；需要逐条移植 `HTMLFilter`，不要用第三方 sanitizer（规则不同会引入新偏差）。
- **注意**：顺序必须在 `@Log` 读 body 之前或复用同一份已清洗 body，否则 `oper_param` 与业务入参不一致。

#### H5. panic 兜底与任务监管

- **落点**：`src/lib.rs`，把 `CatchPanicLayer` 加在 `web_filter` 的内侧（即 `web_filter` 包住 CatchPanic，保证 panic 响应也能补上 `X-Trace-Id`/安全头），自定义返回 `{"msg":null,"code":500}`；`quartz_runtime::register`/`task::run_loop` 用 `std::panic::AssertUnwindSafe + catch_unwind` 或 supervisor 重启。
- **收益**：panic 不再断连接/静默停任务，行为接近 Java 的 `Exception` 兜底。
- **对齐影响**：**恢复对齐**（Java RuntimeException → 500 JSON）；自定义 panic body 需与 Java 的 `{"msg":null}` 对齐。

#### H6. SIGTERM + 健康检查

- **落点**：`src/main.rs::shutdown_signal` 同时等待 `tokio::signal::unix::signal(SignalKind::terminate())`（`#[cfg(unix)]`）；`AppState::check_health` 增加 `redis.ping()`。
- **收益**：容器滚动发布不硬切；健康检查能发现 Redis 故障。
- **对齐影响**：无 API 变化；`/health` 是 rust-only 端点。

### 5.2 中优先级（可维护性/性能）

#### M1. 把同步重活移出 async worker

- **落点**：`src/auth/password.rs`（`verify`/`hash` 包 `spawn_blocking`）；`src/api/support.rs::export_excel`/`export_download`；`src/common/excel.rs`；`src/api/generator/gen_zip.rs`；`src/api/common/common.rs` / `src/api/system/sys_file.rs` 的 `std::fs` 调用；`oss_client` 的签名计算。
- **改法**：`tokio::task::spawn_blocking(move || ...)`；导出路径加 `Semaphore`（例如 4 个并发），避免 40MB 工作簿同时驻留。
- **收益**：避免 CPU/内存密集请求拖垮所有请求；与 Java 200 线程池的实际并发能力更接近。
- **对齐影响**：无行为变化；仅调度方式改变。
- **注意**：`spawn_blocking` 闭包要 `'static`，`rows: Vec<Value>` 需要 move；导出文件名/路径要提前算好。

#### M2. `@Log` 跳过二进制响应

- **落点**：`src/api/meta.rs`。
- **改法**：当响应 `Content-Type` 为 `application/octet-stream` 或带 `Content-Disposition: attachment` 时，不读 body（`save_response_data=false` 的等价语义），直接 `Body::from_stream`/原 body 传递；或至少把上限从 64MB 降到 1MB。
- **收益**：大导出不再全量缓冲/二次拷贝，降低 OOM 风险。
- **对齐影响**：`json_result` 在导出日志里会是 `null`；Java LogAspect 对二进制响应本来也拿不到有意义的 JSON（需核对 Java 实测日志，属可接受的偏差）。

#### M3. 日志与监控接线

- **落点**：`src/main.rs::init_tracing`、新增慢请求中间件、SQL 计时包装。
- **改法**：用支持 `max_files` 的 rolling appender（或启动时清理过期文件），启用 `json` 输出（可选）；加一个 tower 中间件记录 `elapsed > monitor.slow-request-threshold` 的 warn；在 `support` 的查询 helper 里记录 `elapsed > slow-sql-threshold`。
- **收益**：日志不再无限增长；慢请求/慢 SQL 可观测，补齐 Java `SqlLogInterceptor` 的核心价值。
- **对齐影响**：无 API 变化；日志格式差异不影响契约。

#### M4. 批量写入 `replace_table`

- **落点**：`src/task/manager_sync.rs::replace_table`。
- **改法**：`truncate` 后按 100~500 行一批 `QueryBuilder::push_values`；是否包事务需决策（Java 若没有事务，加了会改变失败时的「部分可见」语义）。
- **收益**：N 行从 N 次往返降到 N/100，同步任务耗时显著下降。
- **对齐影响**：**谨慎**。保持无事务则只改性能；加事务会改变「中途失败留下半表」的 Java 行为。

#### M5. 调度监管

- **落点**：`src/service/quartz_runtime.rs`、`src/task/mod.rs`。
- **改法**：每个 job 用 supervisor 循环包 `catch_unwind` + `tokio::time::timeout`（超时可配置）；记录连续失败并告警；实现 `IGNORE` 的「跳过错过触发」。
- **收益**：单个任务崩溃/卡死不再永久停摆；misfire 行为可解释。
- **对齐影响**：**谨慎**。Quartz 的 misfire 语义本来就有多种策略，按 `misfire_policy` 实现才是恢复对齐；当前统一补跑是偏差。

#### M6. 测试与 CI

- **落点**：新增 `tests/`（HTTP 层）、`tools/ci`；补 `cargo clippy -D warnings`、`cargo test`、`cargo fmt --check`。
- **改法**：用 `tower::ServiceExt::oneshot` 直接调用 `build_router`（需要能构造 `AppState`；可把 DB/Redis 依赖拆成 trait 或用 testcontainers）。优先补：
  1. 404/405/401/403 的 body + 头；
  2. 非 admin 数据权限；
  3. 上传白名单/大小；
  4. `sys_job` 的 rollback/commit 分支（可用事务单测）。
- **收益**：把当前靠人工的保证变成可重复回归。
- **对齐影响**：无。

#### M7. 关键查询加类型护栏

- **落点**：`src/repository/user_repo.rs`、`src/auth/login_service.rs`、`src/api/system/sys_user.rs` 的稳定查询。
- **改法**：对 10~20 条不变 SQL 用 `sqlx::query!`/`query_as!`（需要 `DATABASE_URL` 或 `.sqlx` 离线缓存）或 `#[derive(FromRow)]`；动态 SQL 继续用 QueryBuilder。
- **收益**：列名/类型错误从「运行时 500」提前到「编译期」。
- **对齐影响**：无行为变化。

#### M8. Redis 超时与隔离

- **落点**：`src/db/redis_cache.rs::connect`、`src/api/base/cdc.rs`、`src/api/monitor/cache.rs`。
- **改法**：给连接设置 `response_timeout`/`connection_timeout`（redis-rs 支持）；把 `KEYS` 类管理操作放到单独连接或限流；`/monitor/cache` 的 `INFO` 可接受。
- **收益**：Redis 卡顿不会无限挂住请求；管理操作不拖慢业务。
- **对齐影响**：无 API 变化；若改用 `SCAN` 会与 Java 的 `KEYS` 语义有细微差异（**谨慎**）。

### 5.3 低优先级（风格/体验/卫生）

| 建议 | 落点 | 收益 | 对齐影响 |
|---|---|---|---|
| 清 26 条 clippy 告警 | `clippy` 列表 | 可读性；为 `-D warnings` 铺路 | 无 |
| 移除未使用依赖/feature | `Cargo.toml` | 缩短编译、减小供应链面 | 无 |
| 修 README/`.env.example` 的 Redis db/URL | README §2、`.env.example` | 避免运维连错库 | 无 |
| 把 404 helper 的头补齐 | `src/lib.rs`/`error.rs` | 与 Java「每条响应带头」一致 | 恢复对齐 |
| `insert_entity` 自动填充前查列集合 | `src/api/support.rs` | 防止未来新表 1054 | 恢复 Java 行为（MP 只填实体有的字段） |
| 文档化 `misfire`/`concurrent` 偏差 | README §6 | 降低误判 | 无 |
| `truncate` 表名走 `checked_table` | `task/manager_sync.rs` | 防御性 | 无 |
| 把生成物 `src/main`/`src/vue` 移出 crate | `.gitignore` 已覆盖 | 避免误提交 | 无 |

---

## 6. 已验证事实 vs 推断

| 结论 | 状态 | 依据 |
|---|---|---|
| `cargo check` 通过、94 测试通过、clippy 26 条风格告警 | **已验证** | 实际命令输出 |
| 510 条路由全部注册且无多余 | **已验证** | `route_parity` 测试通过（lib.rs:188-248） |
| Java `sys_user`/`sys_dept` 的 `${params.dataScope}` 在 XML 注释里不生效；Rust `sys_user` 一致、`sys_dept` 多过滤 | **已验证** | SysUserMapper.xml:209、SysDeptMapper.xml:97（注释）vs Rust sys_dept.rs:175；SysRoleMapper.xml:52 生效 |
| XSS/RepeatSubmit 未实现 | **已验证** | 全仓 grep 0 + Java 过滤器/拦截器注册代码 |
| `/oss/**` 无条件注册、Java 条件注册 | **已验证** | lib.rs:108 + OssAutoConfiguration:32-36 + yml 无 `oss.info` |
| `/common/upload*` 无白名单/无 basename 清洗；所有 body（含 JSON）实际上限 2MB（axum 默认） | **已验证** | common.rs:127-219；Java FileUploadUtils:61-169；无 `DefaultBodyLimit` 配置 + axum-core `DEFAULT_LIMIT=2MB` + `Json` 经 `Bytes::into_limited_body` |
| 同步重活无 `spawn_blocking` | **已验证** | 全仓 grep 0；调用点均在 async fn |
| 事务使用 `&mut tx` 且提交/回滚分支正确 | **已验证** | 逐块阅读 sys_user/sys_role/job/snapshot_flow_repo |
| 0 unsafe；非测试 panic 类 40 处且多为不变量 | **已验证** | 全仓 grep + 逐条抽样 |
| 404 响应缺 TraceId/安全头/CORS 头 | **推断（高置信）** | axum 0.8.9 `Router::layer` 只包当时 fallback，`fallback()` 之后替换不套层；**未 curl 实测** |
| bcrypt/Excel 阻塞会导致吞吐下降 | **推断** | 代码形态 + tokio 默认 worker 数；**未压测** |
| Redis 单连接会造成队头阻塞 | **推断** | ConnectionManager 单连接；影响取决于 KEYS/大 LRANGE 的实际调用频率 |
| 上传路径穿越可写出目录外 | **推断** | `PathBuf::join` + 未清洗文件名；取决于 OS 与实际调用 |
| `insert_entity` 列假设会在缺列表上 1054 | **推断（当前表未触发）** | 自动填充不查列集合；DDL 抽样显示当前 audit 表都有列 |
| `.env.example` 在密码含 `@`/`:` 时解析失败 | **推断** | `mysql_endpoint` 按 `:` 切 host/port，未处理 userinfo |
| 「sys_job 与 @Scheduled 双跑」 | **条件风险（未验证）** | 本地快照无同名 target；生产库需核对 |

---

## 7. 对拍与残余风险评估

### 7.1 既有对拍强在哪

- [docs/03](file:///d:/work/IdeaProjects/car-monit-backend-new/car-monit-rust/docs/03-INTERFACE-VERIFICATION.md) 的 297 条 GET + §10 的写入矩阵（19 OK / 0 WARN / 0 FAIL、业务表零变动）覆盖了**接口形状、值、键序、状态码**，并且对「Java 自身 bug」和「环境不可用」做了 KNOWN 分类，方法论是可信的。
- `route_parity` 把 510 条端点变成代码里的断言，防止后续新增/删除路由时静默漂移。
- `post_smoke_matrix.py`、`pathvar_matrix.py`、`db_snapshot.py` 这类工具把「写路径/类型转换/副作用」也纳入了验证，超出一般迁移项目的水平。

### 7.2 对拍没覆盖到的地方（本报告发现的问题正好落在这里）

1. **只用 admin**：`sys_dept` 多过滤这类非 admin 差异不可见（H1）。
2. **GET 为主**：XSS/RepeatSubmit/上传这类写路径未被覆盖（H4/M9/H2）。
3. **异常/头**：404/405/401/403 的响应头、上传大小限制，脚本不一定比较。
4. **并发/长任务**：`@Log` 缓冲、同步重活、调度 panic 没有压测/故障注入。
5. **默认配置**：对拍时 Java 侧显然以 `oss.info=true` 启动（否则 `/oss` 是 404），Rust 也指向假 S3；默认部署行为（`oss.info=false`）没人测（H3，**推断**）。

### 7.3 部署前核对清单（建议）

- [ ] 确认 `redis.database` 与 Java 分库拓扑（0 vs 15）一致，并修正 README/.env。
- [ ] 确认 `oss.info` 与 `/oss/**` 的暴露策略。
- [ ] 用非 admin 角色冒烟 `/system/dept/list`、`/treeselect`、`/system/role/list`、`/system/user/list`、`/export`。
- [ ] 用含 `<script>` 的 JSON 提交 `/system/*`，对比两端入库值。
- [ ] 用 5 秒内重复 `POST /system/config` 对比两端。
- [ ] `curl -i /nope` 检查 404 头。
- [ ] 上传 `.jsp`、`../../evil.png`、>40MB 文件；再用 >2MB 的 JSON/上传请求验证 body 上限行为差异（Rust 预期 200 + code 500，Java 正常处理）。
- [ ] 检查容器 SIGTERM 下的在途事务/导出。
- [ ] 核对生产 `sys_job` 是否含 6 个 `@Scheduled` 同名 target（双跑）。

---

## 8. 一句话总结

**这是一个「接口契约可以打 95 分、工程形态 75 分」的迁移**：作者对 Java 运行时怪癖的复刻（JWT Base64、FastJson2、HashMap 桶序、Quartz cron、事务回滚条件）达到了少见的细致程度；但「只迁了 happy path 的鉴权/中间件分支」（数据权限生效面、XSS、RepeatSubmit、OSS 门控）和「Rust 异步模型下的同步重活/全量缓冲」是当前最值得投入的两块。优先做 H1/H2/H3/H4，再补 M1/M2/M6，就能把「对拍通过」提升为「生产可信」。
