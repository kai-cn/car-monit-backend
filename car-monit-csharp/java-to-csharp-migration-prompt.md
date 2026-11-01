# Java 后端项目 1:1 像素级移植为 C# 最新主流生产版本

你是一名资深 **Java/.NET 架构师、后端移植工程师和代码审查员**。请对指定 Java 后端项目执行“1:1 像素级移植”为 C# 最新主流生产版本，并产出便于原 Java 开发人员快速阅读 C# 代码、成功启动项目的完整交付物。

## 一、项目输入

| 项目项                              | 内容                                                         |
| :---------------------------------- | :----------------------------------------------------------- |
| Java 项目路径/仓库                  | `<填写>`                                                     |
| 目标 C# 版本                        | 以执行时官方最新稳定 LTS/主流生产版本为准，默认不低于 .NET 8 LTS；若已有更新 LTS 则使用更新 LTS。C#、[ASP.NET](https://asp.net/) Core、EF Core、NuGet 包均选稳定生产版并锁定版本，不使用 preview |
| 数据库及版本                        | `<填写>`                                                     |
| 部署环境                            | `<Docker/K8s/Windows/Linux/云>`                              |
| 是否要求 API 完全兼容原 Java 服务   | 是                                                           |
| 是否允许并行运行 Java/C# 做对照验证 | `<是/否>`                                                    |
| 其他约束                            | `<填写>`                                                     |

## 二、核心目标

1. 将 Java 后端按模块、接口、数据模型、配置、异常、日志、事务、并发、认证授权、中间件行为 **1:1 移植**为 C# 实现。
2. 对外行为必须尽量保持一致，包括但不限于：
   - HTTP 路径、方法、请求/响应字段
   - JSON 命名策略、日期时间格式、枚举值
   - null/空集合语义
   - 错误码、HTTP 状态码
   - 分页排序、文件上传下载
   - 认证 token/cookie/header、CORS/CSRF
   - 限流、幂等、事务边界、并发语义
   - 日志关键字段、配置项和默认值
3. 内部实现可使用 C# 惯用法，但必须通过注释和文档建立与 Java 类/方法/配置的逐项映射。无法 1:1 的地方必须标注差异、原因、兼容层方案和风险。
4. 不只输出方案，要实际创建/修改 C# 项目代码，执行 `restore/build/run/test`，提供可启动的运行手册和冒烟验证结果。

## 三、执行流程

1. 扫描 Java 项目：读取 `pom.xml/build.gradle`、`application*.yml/properties`、启动类、Controller/Service/Repository/Entity/DTO/Config/Security/Filter/Interceptor/AOP、SQL/迁移脚本、测试、Docker/K8s/CI 配置、API 文档。识别所有框架、中间件、第三方依赖及版本。
2. 先输出 **移植计划与阻塞问题清单**。信息不足时列出缺失项，不要臆测关键业务语义。
3. 建立 **Java→C# 总映射表**，再按模块小步移植。每个模块完成后更新迁移状态文档，标注：
   - 已完成
   - 部分完成
   - 未开始
   - 行为差异
   - 待验证
   - 风险
4. 为每个关键接口和关键业务规则编写兼容性测试或冒烟测试，先固定 Java 行为，再验证 C# 行为。
5. 完成 C# 解决方案骨架、依赖注入、配置系统、数据库访问、认证授权、日志、异常处理、健康检查、Swagger/OpenAPI、Docker/启动脚本。
6. 执行 `dotnet restore/build/test/run`，修复编译和启动问题，完成至少一轮接口冒烟测试。
7. 最终输出验收报告，说明如何启动、如何配置、如何验证、哪些未完全 1:1、后续建议。

## 四、必须交付的文档与代码要求

请生成以下文件/目录，文件名可按项目调整但内容必须完整：

| 交付物                      | 内容要求                                                     |
| :-------------------------- | :----------------------------------------------------------- |
| `MIGRATION_PLAN.md`         | 移植范围、模块清单、阶段计划、阻塞问题                       |
| `FRAMEWORK_COMPARISON.md`   | Java 框架/中间件 vs C# 对应框架/中间件对比表。必须基于项目实际依赖，不要只写通用表 |
| `JAVA_TO_CSHARP_MAPPING.md` | 逐包、逐类、逐关键方法映射，格式如 `Java: com.foo.Bar#baz → C#: Foo.Bar.BazAsync`；说明相似点、差异点、迁移注意 |
| `API_COMPATIBILITY.md`      | 逐接口对比表：路径、方法、鉴权、请求字段、响应字段、状态码、错误码、分页、幂等、备注 |
| `DB_MAPPING.md`             | 表、字段、类型、索引、约束、枚举、时间/精度/null 语义、事务边界、ORM 映射差异 |
| `CONFIG_MAPPING.md`         | Java 配置项 → C# `appsettings`/环境变量/Options，含默认值、优先级、密钥管理 |
| `JAVA_DEVELOPER_GUIDE.md`   | 给原 Java 开发人员的 C# 阅读指南，解释目录结构、命名空间、依赖注入、中间件、过滤器、AOP、事务、异步、LINQ、EF Core、日志、测试写法与 Java 的对应关系 |
| `RUNBOOK.md`                | 环境要求、依赖安装、数据库初始化、配置说明、`dotnet restore/build/run`、Docker Compose/K8s 启动、健康检查、Swagger 地址、常见问题 |
| `MIGRATION_STATUS.md`       | 模块/接口/表/配置/测试的迁移状态和差异清单                   |
| `TEST_MAPPING.md`           | Java 测试 → C# 测试映射，JUnit/Mockito/Testcontainers 等对应方案 |
| 验收报告                    | 启动结果、测试结果、冒烟结果、未完成项、风险                 |

## 五、框架/中间件对比要求

遇到 Java 组件时，列出 C# 生产可用对应方案并对比相似点和差异点，至少覆盖实际项目出现的：

- Spring Boot / Spring MVC
- Spring Data JPA / MyBatis / Hibernate
- Spring Security
- Spring Cloud / Feign
- 配置中心 / 服务发现 / 网关
- Maven / Gradle
- Tomcat / Jetty
- Logback / Log4j2
- Redis
- Kafka / RabbitMQ / RocketMQ
- Quartz / XXL-JOB
- Actuator
- Swagger / OpenAPI
- JUnit / Mockito / Testcontainers
- Flyway / Liquibase
- Docker 等

对比表列建议：

| Java 组件及版本 | 用途 | C# 对应组件及版本 | 相似点 | 差异点 | 迁移注意 | 替代方案 | 风险等级 |
| :-------------- | :--- | :---------------- | :----- | :----- | :------- | :------- | :------- |
|                 |      |                   |        |        |          |          |          |

常见对应可参考，但必须以实际项目为准：

| Java                        | C#                                                           |
| :-------------------------- | :----------------------------------------------------------- |
| Spring Boot                 | [ASP.NET](https://asp.net/) Core                             |
| Spring MVC                  | [ASP.NET](https://asp.net/) Core MVC / Minimal APIs          |
| Spring Data JPA / Hibernate | EF Core                                                      |
| MyBatis                     | Dapper / EF Core                                             |
| Spring Security             | [ASP.NET](https://asp.net/) Core Authentication/Authorization/Identity |
| Maven / Gradle              | .NET SDK / NuGet                                             |
| Logback / Log4j2            | Serilog / NLog / Microsoft.Extensions.Logging                |
| Redis                       | StackExchange.Redis                                          |
| Kafka                       | Confluent.Kafka                                              |
| RabbitMQ                    | RabbitMQ.Client / MassTransit                                |
| Quartz                      | [Quartz.NET](https://quartz.net/) / Hangfire                 |
| Feign                       | Refit / HttpClientFactory                                    |
| Actuator                    | HealthChecks                                                 |
| Swagger                     | Swashbuckle / NSwag                                          |
| JUnit                       | xUnit / NUnit                                                |
| Mockito                     | Moq / NSubstitute                                            |
| Flyway / Liquibase          | EF Core Migrations / [Flyway.NET](https://flyway.net/)       |

## 六、代码规范与映射要求

- C# 代码中在关键类/方法上方添加注释：`// Java: <全限定类名#方法名>`，并简述行为差异。
- 命名空间和目录尽量按 Java 包结构映射，便于对照。
- 不要为了像 Java 而破坏 C# 生产实践；需要模拟 Java 行为时使用适配器/Facade/中间件/过滤器。
- 保留原 Java 项目，不删除、不覆盖。
- 数据库 schema 默认不改；确需改动必须列入差异和迁移脚本。
- 所有 NuGet 包锁定稳定版本，集中管理版本。
- 敏感配置使用环境变量/Secret，不硬编码。
- 提交按模块小步进行，提交信息说明对应 Java 模块。

## 七、验收标准

1. C# 项目可成功 `restore/build/test/run`。
2. 数据库可初始化或连接成功，关键接口可通过 Swagger/curl 冒烟验证。
3. API 契约、错误结构、认证授权、配置项、日志关键字段与 Java 版一致或有明确兼容说明。
4. 文档中的映射表覆盖实际项目的主要包、类、接口、表、配置和中间件。
5. 原 Java 开发人员根据 `JAVA_DEVELOPER_GUIDE.md` 和 `RUNBOOK.md` 能快速定位代码并启动项目。
6. 所有无法 1:1 的点均有差异说明、影响范围、兼容层或后续建议。

## 八、现在开始

请现在开始：

1. 先读取项目并输出 **移植计划、依赖清单和阻塞问题**；
2. 随后按计划实际创建 C# 项目、移植代码、运行验证；
3. 持续更新上述文档；
4. 全程使用中文输出。