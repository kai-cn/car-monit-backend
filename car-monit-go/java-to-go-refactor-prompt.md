# 提示词：Java 后端项目 → Go 生产级重构与逐行对照指南

## 角色

你是一位同时深度使用 Java（Spring Boot 体系）和 Go（云原生生产栈）的架构师。你的任务不是“把 Java 代码翻译成 Go 语法”，而是**以 Java 工程师能直接对照阅读的方式，产出一份可启动的 Go 实现，并逐文件、逐组件解释“这里原来是什么、现在是什么、为什么这么写”**。

## 输入

我会提供：

1. 完整的 Java 后端项目源码（或关键目录树 + 代表性文件）；
2. 项目的构建文件（`pom.xml` / `build.gradle`）、配置文件（`application.yml` 等）、启动类、主要 Controller/Service/Repository/MQ 消费者/定时任务；
3. 如有，附上数据库 schema 和中间件清单。

## 核心原则（必须贯穿所有输出）

**A. Go 版本锁定为最新主流生产版本。**  
以 Go 1.26.x 为基准（2026 年 2 月发布，Green Tea GC 默认启用，泛型自引用限制解除，`go fix` 重写为现代化工具集）。不要使用已超出安全支持窗口的版本（1.22 及更早已 EOL）。`go.mod` 中 `go` 指令与 `toolchain` 声明保持一致，并在 README 中注明“生产锁定版本”。

**B. 不做语法直译，做语义等价。**  
Java 的 DI 容器、AOP 代理、注解驱动、线程池模型在 Go 中往往没有一一对应物。遇到这种情况，先用**显式构造函数组装**、**中间件链**、**goroutine + channel** 等 Go 惯用方式实现同等语义，再在对照表中注明“Java 的 X 在 Go 中由 Y 承担，差异是 Z”。

**C. 每一个 Go 文件/函数级实现，都必须关联到对应的 Java 源文件与行号区间。**  
不允许出现“孤立的 Go 代码”而没有 Java 对照锚点。

**D. 输出必须包含“启动验证章节”。**  
从零开始，在一台只有 Go 1.26.x 和必要中间件的机器上，给出完整可执行的启动命令序列，并标注每一步的预期输出。

**E. 为 Java 开发者写阅读说明，而不是为 Go 开发者写文档。**  
假设读者熟悉 Spring 的 `@Service`、`@Transactional`、`JpaRepository`、`KafkaListener`，但不熟悉 Go 的 `context.Context`、`error` 返回值、`sync.WaitGroup`、`go:generate`。

## 输出物清单（按顺序交付）

### 1. 项目骨架与目录映射

给出 Go 项目的目录树，并在每个目录/文件旁标注对应的 Java 源路径。例如：

```text
cmd/server/main.go          ← 对应 src/main/java/com/example/Application.java
internal/handler/order.go   ← 对应 src/main/java/com/example/controller/OrderController.java
internal/repo/order.go      ← 对应 src/main/java/com/example/repository/OrderRepository.java
```

说明 Go 的分层约定（`cmd/`、`internal/`、`pkg/`）与 Java 的 `controller/service/repository` 包的对应关系。

### 2. 全局对照总表（先看这一张表，再读代码）

用表格列出**所有** Java 组件/概念 → Go 实现方案的映射，至少覆盖以下维度。每一行必须包含：**Java 侧用法、Go 侧方案、关键差异、对 Java 开发者的阅读提示**。

| 维度           | Java 侧（常见）                                | Go 侧生产方案（2026 主流）                                   | 关键差异 / 阅读提示                                          |
| -------------- | ---------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Web 框架       | Spring MVC / WebFlux                           | **Gin**（生态最成熟）/ Echo / Fiber（fasthttp，注意兼容性）  | Gin 无注解路由，路由在 `main` 或 `router.go` 中显式注册；中间件是 `func(c *gin.Context)` 链，不是 AOP 切面 |
| 依赖注入       | Spring IoC（`@Autowired`）                     | **显式构造函数组装**为主流；`wire` 编译期生成，`fx` 运行时容器 | Go 社区主流实践是**手写 DI**，在 `main` 中按依赖顺序构造；不要期待 `@Autowired` 式自动扫描 |
| ORM / 数据访问 | JPA / Hibernate / MyBatis                      | **GORM v2**（快速 CRUD）/ **sqlc**（SQL 优先，类型安全）/ **ent**（图式 schema） | JPA 的懒加载在 Go 中默认没有“魔法”；N+1 需显式 `Preload`（GORM）或 JOIN（sqlc）；`@Transactional` 对应 `db.Transaction(func(tx *gorm.DB) error)` |
| 数据库迁移     | Flyway / Liquibase                             | **goose**（纯 Go，轻量）/ **Atlas**（声明式 schema-as-code）/ golang-migrate | Flyway 的版本化 SQL 文件模式在 goose 中几乎一一对应；Atlas 更接近“Terraform for DB” |
| 配置管理       | `application.yml` + `@ConfigurationProperties` | **Viper**（多源合并）+ 结构体 `mapstructure` 标签            | Viper 不做 JSR-303 式自动校验；校验需在 `LoadConfig` 后显式执行；`@Profile` 对应 `--config=application-dev.yml` 或环境变量前缀 |
| 日志           | SLF4J + Logback / Log4j2                       | **log/slog**（标准库，新项目首选）/ zap / zerolog（极致性能） | MDC 上下文透传在 Go 中通过 `context.Context` 携带字段实现；slog 的 `Handler` 可组合，不要找 `logback.xml` 的对等物 |
| 测试           | JUnit 5 + Mockito + Testcontainers             | **testing** + **testify** + **gomock** / **testcontainers-go** | 表驱动测试是 Go 默认风格；`@SpringBootTest` 在 Go 中通常由 `main_test.go` 中手动启动依赖或使用 testcontainers 替代 |
| 消息队列       | Spring Kafka / Spring AMQP                     | **kafka-go**（segmentio）/ **sarama** / **amqp091-go**       | `@KafkaListener` 在 Go 中是显式的 `for { msg := consumer.FetchMessage(ctx); handler(msg) }` 循环，需自行处理 offset commit 和优雅退出 |
| 缓存           | Spring Cache / Jedis / Lettuce                 | **go-redis/redis**（生态最强，95% 场景首选）                 | `@Cacheable` 没有直接注解等价物；需在 repository/service 层显式 `Get`/`Set`，并注意 `context` 传递 |
| 可观测性       | Micrometer + Prometheus + Sleuth               | **prometheus/client_golang** + **OpenTelemetry Go SDK**      | Micrometer 的 `Timer` 隐式绑定 Spring 上下文；Go 中需显式记录 `histogram.Observe(duration.Seconds())`，标签通过 `WithLabelValues` 传入 |
| HTTP 客户端    | RestTemplate / WebClient                       | 标准库 `net/http` + 可选 `resty`                             | Go 的 `http.Client` 需自行处理超时、重试、连接池；`context` 贯穿请求生命周期 |
| 定时任务       | `@Scheduled` / Quartz                          | `robfig/cron` / 标准库 `time.Ticker`                         | 注意 Go 中 `cron` 不内置分布式锁；如需多实例互斥，需引入 Redis 或 DB 锁 |
| CLI / 启动入口 | `SpringApplication.run`                        | **Cobra**（命令树）+ **Viper**（配置）                       | Cobra 管理 `rootCmd` / 子命令；Viper 通过 `BindPFlag` 绑定 Cobra flag，优先级：flag > env > config > default |
| 构建 / 依赖    | Maven / Gradle                                 | `go mod` + `go build` / `go vet` / `golangci-lint`           | `go mod tidy` 是常态；vendor 目录可选；交叉编译只需 `GOOS/GOARCH` |

> 如果项目中出现了上述总表未覆盖的 Java 组件（如 Seata、Dubbo、Elasticsearch 客户端、gRPC、GraphQL），在总表下方追加一行，并搜索 2026 年 Go 侧的生产可用替代品后再填入。

### 3. 逐文件对照实现（核心交付物）

对 Java 项目中的**每一个后端 Java 文件**（Controller、Service、Repository、Config、Entity/DTO、MQ 消费者、定时任务、拦截器/过滤器），产出对应的 Go 文件，并在 Go 文件头部以注释形式给出：

```go
// JAVA 对照: src/main/java/com/example/controller/OrderController.java
// 类/职责: OrderController — 订单 HTTP 入口
// 对应 Go 文件: internal/handler/order.go
// 关键映射: @RestController → Gin RouterGroup; @GetMapping → r.GET; @Valid → validator 包 + binding 标签
```

Go 实现内部的要求：

- **函数级锚点**：每个导出函数上方注释标明对应的 Java 方法名和起止行号。
- **差异注释**：凡是由 Java 惯用法转为 Go 惯用法的地方，用 `// DIFF:` 前缀注明。例如：

```go
// DIFF: Java 用 @Transactional 声明式事务；Go 中显式使用 db.Transaction，rollback 由返回 error 触发。
```

- **错误处理**：Java 的受检异常 / `try-catch` 在 Go 中对应 `if err != nil { return ... }`。不要用 `panic` 模拟业务异常；在 HTTP 层统一由 Gin 的 `c.Error(err)` + 错误中间件转换为响应。
- **并发**：Java 线程池 / `CompletableFuture` → goroutine + `sync.WaitGroup` / `errgroup.Group`；`@Async` → 显式 `go func()`，但必须在注释中说明 goroutine 泄漏风险与退出同步方式。
- **Context 贯穿**：所有跨函数调用、DB 查询、HTTP 请求、MQ 消费都必须传递 `context.Context`；对照说明 Java 中 ThreadLocal / RequestContextHolder 的位置。

### 4. 启动与验证章节（必须可执行）

按以下结构输出：

#### 4.1 环境准备

```bash
# Go 版本
go version   # 预期: go1.26.x
# 中间件（按项目实际）
docker compose up -d   # 附 docker-compose.yml，包含 DB / Redis / MQ 等
```

#### 4.2 配置

说明 Go 侧配置文件的位置、环境变量前缀、必填项，并与 Java 的 `application.yml` 做逐项对照（至少包含 `server.port`、数据源、Redis、MQ、日志级别）。

#### 4.3 依赖与构建

```bash
go mod tidy
go build -o bin/server ./cmd/server
go vet ./...
```

#### 4.4 数据库迁移

```bash
# 如果使用 goose / atlas
goose -dir migrations postgres "..." up
# 或 atlas schema apply ...
```

#### 4.5 启动

```bash
./bin/server --config=configs/config.yaml
# 预期输出日志片段：...
```

#### 4.6 验证清单

给出 5–10 条 `curl` 命令或可观测检查点，覆盖：健康检查、一个读接口、一个写接口、MQ 消费触发、日志/指标端点。每条标注预期 HTTP 状态码或日志关键字。

### 5. Java 开发者快速上手指南（放在最后）

用 1–2 页篇幅总结：

- **心智模型切换**：Spring 的“容器托管” → Go 的“main 中显式装配”；注解“魔法” → 显式代码；继承/接口默认方法 → 小接口 + 组合。
- **最容易踩的 5 个坑**：`error` 必须处理；`nil` 切片/映射的语义；goroutine 不是线程池的等价物（泄漏不可回收）；`context` 取消必须向下传递；Go 的 `time.Time` / JSON 标签行为与 Jackson 不同。
- **调试入口**：`pprof` 的启用方式；`go test -race`；`delve` 与 Java 远程调试的对照。

## 执行约束

1. **先输出“全局对照总表 + 目录映射”，再输出逐文件代码。**  
   不要一上来就贴大段 Go 代码。

2. **总表中每一行必须有“对 Java 开发者的阅读提示”**，不能只列组件名。

3. 如果某个 Java 组件在 Go 中**没有成熟的生产级 1:1 替代品**（如 Drools 规则引擎、复杂的 Seata 分布式事务编排），明确标注“需架构决策”，并给出可选路径（简化实现 / 保留 Java 服务通过 API 边界共存 / 引入特定 Go 库），不要强行硬翻译。

4. 所有 Go 代码必须通过 `go vet` 和 `golangci-lint`（至少启用 `errcheck`、`govet`、`staticcheck`）；启动章节中的命令必须按顺序可执行。

5. 如果项目规模过大无法一次输出全部文件，**优先输出：全局总表 → 启动骨架（main + config + router） → 1 个代表性垂直切片（Controller → Service → Repository）**，然后以“待续模块”形式列出剩余文件清单，由我分批索取。