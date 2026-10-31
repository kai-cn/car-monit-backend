你是一名同时精通 Java/Spring Boot 与 Rust 生产级后端开发的架构师兼迁移工程师。

任务：将一个已有的 Java 后端项目，1:1 像素级重构为 Rust 最新主流生产版本。

核心约束：

- 行为必须与 Java 版完全一致（API 路径、请求/响应结构、状态码、错误码、数据库 schema 与查询语义、事务边界、缓存 key 与 TTL、消息格式与消费语义）。
- 不是“重新设计一个 Rust 服务”，而是“用 Rust 逐文件重写同一个服务”。
- Rust 侧选用 2026 年生产级主流技术栈，不引入实验性/非稳定 API。

请按以下四个阶段执行，每个阶段都必须产出结构化文档，再进入下一阶段。

────────────────────────────────────────
阶段一：通读 Java 项目，输出“迁移基线清单”
────────────────────────────────────────

在改动任何代码之前，先完整阅读 Java 项目源码、配置、SQL/DDL、接口文档（OpenAPI/Swagger）和部署脚本，输出以下清单：

1. 项目结构对照表
   逐文件/逐包列出：
   - Java 文件路径 → 对应 Rust 目标文件路径
   - 文件职责（Controller / Service / Repository / DTO / Config / Interceptor / Job / Listener …）
   - 是否为“纯逻辑文件”（可直接翻译）或“框架契约文件”（需要用 Rust 惯用法重写）

2. 接口清单
   每个 HTTP 端点列出：method、path、请求体/Query/Header、响应体、状态码、错误码、鉴权要求。
   同时标注 Java 侧对应的 Controller 方法和 Rust 侧计划对应的 handler 函数名。

3. 数据层清单
   - 数据库类型与版本（PostgreSQL / MySQL / …）
   - 全部表、索引、外键、迁移脚本
   - 每个 SQL 语句（MyBatis XML / JPA / JdbcTemplate / 手写 SQL）→ Rust 侧对应实现方式与具体 SQL
   - 事务边界：Java 的 @Transactional 方法 → Rust 侧的事务包裹位置

4. 中间件与外部依赖清单
   - 缓存（Redis / Caffeine / …）
   - 消息队列（Kafka / RabbitMQ / …）
   - 认证/授权方式（JWT / OAuth2 / Session / Spring Security）
   - 定时任务 / 后台 Worker
   - 文件存储、邮件、第三方 SDK 等

5. 配置项清单
   Java application.yml / application-{profile}.yml / 环境变量 → Rust 侧对应配置项名与默认值。

6. “不可 1:1 直接翻译”的阻塞点
   提前识别 Java 反射、AOP、运行时注解扫描、动态代理、JVM 特有 API、继承多态等无法直接映射的部分，并给出 Rust 替代方案。

────────────────────────────────────────
阶段二：输出“Java ↔ Rust 全量映射表”
────────────────────────────────────────

以表格形式输出，每一行包含：Java 用法 / Rust 对应写法 / 关键差异说明 / Java 开发者最容易踩的坑。

至少覆盖以下维度：

1. 语言与类型系统
   - String vs String / &str；Integer/int vs i32/Option<i32>；Long vs i64；boolean/Boolean vs bool/Option<bool>
   - List/ArrayList vs Vec；Map/HashMap vs HashMap；Set vs HashSet
   - class + 继承 → struct + impl + trait；interface → trait；abstract class → trait + 默认方法或 enum
   - 泛型擦除 vs 单态化；异常（Exception）→ Result<T, E>；null → Option<T>
   - 可变性：Java 默认可变 vs Rust 默认不可变（let mut）
   - 所有权 / 借用 / 生命周期：为什么“把变量赋给另一个变量后原变量不能再用”，E0382 / E0499 / E0502 / E0597 各自含义与读法[reference:0]

2. 并发与异步
   - Thread / ExecutorService / CompletableFuture vs tokio::spawn / async/await / JoinHandle
   - Java CompletableFuture 回调链 vs Rust async fn 状态机 + .await 显式挂起点[reference:1]
   - 共享可变状态：synchronized / ConcurrentHashMap vs Arc<Mutex<T>> / Arc<RwLock<T>> / dashmap
   - 虚拟线程（Loom）vs tokio task 的差异与选型建议

3. Web 框架
   - Spring Boot MVC / WebFlux → Axum 或 Actix-web
   - @RestController / @GetMapping → Router + handler
   - @RequestBody / @PathVariable / @RequestParam / @RequestHeader → Axum extractor（Json / Path / Query / Header）
   - @ControllerAdvice / @ExceptionHandler → 中间件 + IntoResponse 统一错误映射
   - Spring Security Filter Chain → tower / axum middleware；JWT 用 jsonwebtoken，授权用 guard/extractor[reference:2]
   - 内置 Tomcat / Netty → tokio 运行时 + hyper（Axum 底层）

4. ORM / 数据访问
   - MyBatis / JPA / Hibernate / JdbcTemplate → SQLx / SeaORM / Diesel / Rbatis
   - 选型建议：SQLx 编译时 SQL 校验、性能最好，但需要手写 SQL；SeaORM 有 ActiveRecord 风格，适合从 JPA/Hibernate 迁来的开发者；Diesel 类型安全最强但异步支持弱；Rbatis 最接近 MyBatis 的动态 SQL 体验
   - @Entity / @Table / @Id / @Column → SeaORM Entity 派生或 SQLx FromRow
   - @Transactional → sqlx::Transaction / SeaORM Transaction
   - 分页（Pageable）→ limit/offset + count 查询

5. 中间件
   - Redis（Spring Data Redis / Lettuce）→ redis-rs（异步、连接池、cluster 支持）[reference:5]
   - Kafka（spring-kafka）→ rust-rdkafka（基于 librdkafka）
   - RabbitMQ（spring-amqp）→ lapin（AMQP 客户端）[reference:7]
   - 连接池：HikariCP → sqlx Pool / deadpool / bb8

6. 配置
   - @Value / @ConfigurationProperties / application.yml → config-rs + serde 反序列化，或 figment
   - profile（spring.profiles.active）→ 环境变量 APP_PROFILES_ACTIVE + 按 profile 加载不同配置文件[reference:8]
   - 优先级设计：命令行 > 环境变量 > profile 配置文件 > 默认值

7. 日志与可观测性
   - SLF4J + Logback/Log4j2 → tracing + tracing-subscriber
   - Logger / MDC → tracing::info_span! / #[instrument]
   - 分布式 trace id → tracing 的 span 上下文传播[reference:9]

8. 序列化
   - Jackson → serde + serde_json
   - @JsonProperty / @JsonIgnore / @JsonFormat → #[serde(rename = "...")] / #[serde(skip)] / serde 属性
   - 编译期派生 vs 运行时反射：serde 是零运行时开销的编译期代码生成[reference:10]

9. 依赖注入
   - Spring DI 容器 → Rust 没有运行时 DI 容器；用“组合根（composition root）+ 显式构造 + trait 抽象”替代
   - @Autowired / @Bean → 在 main 或 AppState 构建函数中显式创建依赖并注入 axum::extract::State
   - 说明：Spring 是运行时魔法，Rust 是编译期检查；依赖错误在 Rust 中编译期就会报错[reference:11]

10. 测试
    - JUnit 5 / Mockito / AssertJ → 内置 #[test] + cargo test；断言用 assert_eq! / pretty_assertions；mock 用 mockall 或 trait 手写 fake[reference:12]
    - @SpringBootTest → 集成测试用 #[tokio::test] + 真实测试数据库或 testcontainers

11. 构建与部署
    - Maven / Gradle → Cargo（Rust 唯一主流构建工具）
    - JVM fat jar / GraalVM native image → 单二进制可执行文件
    - 启动命令、环境变量、健康检查端点一一对应

────────────────────────────────────────
阶段三：逐文件移植，代码内嵌 Java↔Rust 对照注释
────────────────────────────────────────

规则：

1. 每个 Rust 文件顶部用块注释写明：
   // 来源: src/main/java/.../XxxService.java
   // 职责: ...
   // 对应关系: 本文件的函数 A ↔ Java 的 A 方法；B ↔ B

2. 在每个关键代码块上方或行尾，用简洁注释标出 Java 等价物。例如：

   // Java: public ResponseEntity<User> getUser(@PathVariable Long id)
   async fn get_user(Path(id): Path<i64>, State(db): State<PgPool>) -> Result<Json<User>, AppError> {
       // Java: userRepository.findById(id).orElseThrow(() -> new NotFoundException());
       let user = sqlx::query_as::<_, User>("SELECT ... WHERE id = $1")
           .bind(id).fetch_optional(&db).await?
           .ok_or(AppError::NotFound)?;
       Ok(Json(user))
   }

3. 凡是“行为上必须一致但写法必须变”的地方，额外加一段注释解释“为什么不能照搬”：

   - Java 的 null 返回 → Rust 用 Option<T> 表达
   - Java 的 try/catch → Rust 用 ? 传播 Result
   - Java 的运行时 AOP → Rust 用显式中间件/tower layer
   - Java 的继承复写 → Rust 用 trait 组合或 enum 分派

4. 保持 1:1 行为，但不保留反模式：

   - 不把 Java 的 Service 层强行拆成“trait 接口 + impl”，除非原项目确实有多个实现或测试 mock 需要
   - 不引入 Rust 中不必要的 Arc<Mutex<>>；能用所有权和借用解决就不用共享可变状态
   - 不在请求路径上做 Java 式的反射/动态代理等价物

5. 数据库 schema 和 SQL 语义必须一致；如果为了适配 Rust 驱动需要改占位符（? → $1），在注释中说明。

────────────────────────────────────────
阶段四：交付“可启动”的完整产物
────────────────────────────────────────

最终必须提供：

1. 完整可编译的 Rust 项目：
   - Cargo.toml（依赖版本锁定到 2026 年稳定主流版本）
   - src/ 下全部代码
   - migrations/ 或 schema.sql
   - .env.example
   - 启动命令与所需环境变量说明

2. 一份 README-MIGRATION.md，包含：
   - 如何从零启动（rustup / cargo run / docker-compose 如有）
   - Java 配置 → Rust 配置的逐项对照表
   - 依赖组件映射总表（Spring→Axum、MyBatis→SQLx、Redis→redis-rs、Kafka→rdkafka、RabbitMQ→lapin、Jackson→serde、Logback→tracing、JUnit→#[test] 等）
   - Java 开发者阅读 Rust 代码时最容易困惑的 10 个点，每个点给出一段 Java vs Rust 的短代码对照

3. 自检清单（逐项打勾确认）：
   [ ] 所有 API 路径、method、请求/响应结构一致
   [ ] 所有状态码和错误码一致
   [ ] 数据库查询语义一致，事务边界一致
   [ ] 缓存 key、TTL、失效逻辑一致
   [ ] 消息格式、消费组、偏移提交语义一致
   [ ] 配置项均有对应，默认值一致
   [ ] 应用可以成功启动并监听相同端口
   [ ] 关键路径至少有一个集成测试通过

关键心态提醒（请写进给 Java 开发者的说明中）：

- Rust 替代 GC 的不是“另一种 GC”，而是编译期所有权 + 析构；赋值“原变量不能再用”不是语法怪癖，是防双重释放[reference:14]。
- Spring 的注解 + 反射 + 容器在 Rust 中通常变为“显式路由 + 显式构造 + 编译期类型检查”；代码看起来更长，但错误在编译期暴露，不需要启动后才炸[reference:15]。
- 不要试图在 Rust 中复刻 Spring 的运行时魔法；用 Rust 的显式组合来达到同样的解耦效果，同时保留 1:1 的外部行为。

现在开始执行阶段一。输出迁移基线清单后，等我确认再进入阶段二。