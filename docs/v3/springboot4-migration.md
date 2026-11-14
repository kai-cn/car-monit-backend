# Spring Boot 4.1.2 迁移与踩坑记录（backend / MySQL 8）

> 复核遗留项闭环见第 9 节。

> 分支：`car-monit-backend-jdk17`（本文件同时适用于后续 `jdk21` / `jdk25` 分支，差异只在 `java.version`）
> 迁移日期：2026-11-14　目标：把 Spring Boot 从 2.7.18 升到 **JDK 17 可运行的最新稳定版 4.1.2**，并实机跑通。
> 敏感信息（口令 / 令牌 / 密钥）一律由运行环境注入，本文不记录任何凭据值。

## 1. 版本结论

| 项 | 迁移前 | 迁移后 | 说明 |
| --- | --- | --- | --- |
| JDK | 17（toolchain, release=17） | 17（release=17） | JDK 21/25 分支只改 `java.version` / `maven.compiler.release` |
| Spring Boot | 2.7.18 | **4.1.2** | `spring-boot-starter-parent:4.1.2` 的 `java.version=17`，即 Boot 4.1.x 的 JDK 基线仍是 17，故 17/21/25 三支同版本 |
| Spring Framework | 5.3.39 | 7.0.10（BOM 管理，去掉手工 spring-framework-bom） | |
| Spring Security | 5.7.x | 7.1.2 | `WebSecurityConfigurerAdapter` 早已移除，必须重写为 `SecurityFilterChain` |
| JSON | Jackson 2.13 | **Jackson 3.1.7（`tools.jackson.*`）** | Boot 4 默认 Jackson 3；`com.fasterxml.jackson.annotation.*` 注解包保持不变 |
| Servlet / Validation | javax.* | jakarta.*（Servlet 6.1 / Validation 3.1） | |
| 内嵌容器 | Tomcat 9 | Tomcat 11 | |
| MyBatis-Plus | 3.5.7（`mybatis-plus-boot-starter`） | 3.5.18（`mybatis-plus-spring-boot4-starter`） | 3.5.9 起模块拆分，见第 3 节 |
| PageHelper | 2.1.0 | 4.1.1 | 4.x 才对应 Boot 4 / mybatis-spring-boot 4.0.x |
| Druid | `druid-spring-boot-starter` 1.2.20 | `druid-spring-boot-4-starter` 1.2.28 | 包名 `com.alibaba.druid.spring.boot4.autoconfigure.*` |
| dynamic-datasource | 3.5.2 | `dynamic-datasource-spring-boot4-starter` 4.6.0 | |
| 接口文档 | springfox 3.0.0 | springdoc-openapi 3.2.0 | springfox 在 Boot 3/4 无法启动 |
| JWT | jjwt 0.9.1 | jjwt 0.13.0（api/impl/jackson） | 0.9.1 依赖 `javax.xml.bind`，JDK 11+ 已移除 |
| easypoi | `easypoi-spring-boot-starter` 4.3.0 | 仅 `easypoi-base` | starter/web 依赖 javax.servlet + Boot 2 自动配置 |
| Forest | `forest-spring-boot-starter` 1.6.0 | `forest-spring-boot3-starter` 1.8.0 | 官方无 Boot 4 starter |
| ShardingSphere | `shardingsphere-jdbc-core-spring-boot-starter` 5.2.1 | `shardingsphere-jdbc` + `shardingsphere-sharding-core` 5.5.3 | 去掉了会拖进 Boot 2 自动配置的 starter |
| Elasticsearch | 7.15.2 HLRC | 7.15.2 HLRC（保留） | 客户端版本按服务端对齐 |
| MySQL 驱动 | `mysql:mysql-connector-java` 8.0.33 | `com.mysql:mysql-connector-j` 9.7.0（BOM） | |

## 2. POM 结构变化（`pom.xml`）

1. `dependencyManagement` 只 import `spring-boot-dependencies:4.1.2`，删除自管的 `spring-framework-bom`（避免 5.3.x 版本反压）。
2. 启动器更名：
   - `spring-boot-starter-web` → **`spring-boot-starter-webmvc`**（Boot 4 正式名，`-web` 已 deprecated）
   - `spring-boot-starter-aop` → **`spring-boot-starter-aspectj`**
   - `ruoyi-quartz` 引入 **`spring-boot-starter-quartz`**（Boot 4 把 `QuartzAutoConfiguration` 拆到独立模块）
   - `ruoyi-framework` 引入 **`spring-boot-starter-cache`**（`RedisConfig` 上有 `@EnableCaching`）
3. 子模块依赖收敛：
   - `ruoyi-quartz`：`org.quartz-scheduler:quartz` → `spring-boot-starter-quartz`
   - `ruoyi-system`：显式声明 `spring-webmvc`（`GlobalExceptionTraceHandler` 用 `HandlerExceptionResolver`，迁移前靠 easypoi-web 传递）
   - `ruoyi-system`：ShardingSphere 换成 `shardingsphere-sharding-core`
   - `ruoyi-admin`：springfox → springdoc；`mysql-connector-java` → `com.mysql:mysql-connector-j`；`spring-boot-maven-plugin` 版本 4.1.2
4. `maven-compiler-plugin` 3.14.0 + `maven-surefire-plugin` 3.5.4。

## 3. 代码改动清单

### 3.1 jakarta 命名空间
`javax.servlet*` / `javax.annotation.*` / `javax.validation*` → `jakarta.*`（脚本批量替换 93 个文件）。
注意 **不要**替换：`javax.sql.DataSource`、`javax.crypto.*`、`javax.net.ssl.*`、`javax.imageio.*`、`javax.naming.*`（这些仍在 JDK 里）。

### 3.2 MyBatis-Plus 3.5.18 的包迁移（踩坑点）
MP 3.5.9+ 起：
- `IService` / `ServiceImpl` 从 `com.baomidou.mybatisplus.extension.service[.impl]` 迁到 **`com.baomidou.mybatisplus.spring.service[.impl]`**（在 `mybatis-plus-spring` 里，starter 不再传递 `mybatis-plus-extension`）；
- `PaginationInnerInterceptor` 等依赖 jsqlparser 的拦截器拆到 `mybatis-plus-jsqlparser` / `mybatis-plus-jsqlparser-4.9`。
本工程 86 个文件做了包名替换，并显式引入 `mybatis-plus-extension` + **`mybatis-plus-jsqlparser-4.9`**（选 4.9 变体是为了与 PageHelper 6.1.x 共用同一份 `jsqlparser:4.9`，否则运行期分页插件会 `NoSuchMethodError`）。

### 3.3 Spring Security 7：`SecurityConfig` 重写
- `WebSecurityConfigurerAdapter` → `@Bean SecurityFilterChain`；
- `@EnableGlobalMethodSecurity` → `@EnableMethodSecurity`；
- `antMatchers` → `requestMatchers`；链式 `.and()` 全部改 lambda DSL；
- `AuthenticationManager` 改为从 `AuthenticationConfiguration` 取。

### 3.4 循环依赖：`allow-circular-references` 已不可用
Spring Framework 6.2 起循环引用**永久禁止**，`spring.main.allow-circular-references` 不再生效（配置已删）。
实机报错：`bussTestController → carTrackInfoServiceImpl → carInfoServiceImpl → carTrackInfoServiceImpl`。
处理：`CarInfoServiceImpl.carTrackInfoService` 字段加 `@Lazy`（用代理延迟解析，语义不变）。
> 排查方法：启动日志里的 `The dependencies of some of the beans in the application context form a cycle` 会直接画出环，按图加 `@Lazy` 或重构即可。

### 3.5 Jackson 3（`tools.jackson.*`）改动
| 迁移前 | 迁移后 |
| --- | --- |
| `com.fasterxml.jackson.databind.ObjectMapper` | `tools.jackson.databind.ObjectMapper` |
| `com.fasterxml.jackson.databind.JsonNode` | `tools.jackson.databind.JsonNode` |
| `com.fasterxml.jackson.core.type.TypeReference` | `tools.jackson.core.type.TypeReference` |
| `com.fasterxml.jackson.databind.JsonSerializer` | `tools.jackson.databind.ValueSerializer` |
| `com.fasterxml.jackson.databind.SerializerProvider` | `tools.jackson.databind.SerializationContext` |
| `com.fasterxml.jackson.databind.ser.ContextualSerializer` | 已删除：直接覆盖 `ValueSerializer#createContextual` |
| `com.fasterxml.jackson.core.JsonProcessingException` | `tools.jackson.core.JacksonException`（**非受检**） |
| `objectMapper.copy().configure(...)` | `objectMapper.rebuild().disable(...).build()` |
| `Jackson2ObjectMapperBuilderCustomizer` | `org.springframework.boot.jackson.autoconfigure.JsonMapperBuilderCustomizer` |
| `JsonNode.fieldNames()` | `JsonNode.propertyNames()` |
| `@JsonSerialize` / `ToStringSerializer` | `tools.jackson.databind.annotation.JsonSerialize` / `tools.jackson.databind.ser.std.ToStringSerializer` |

`@JsonFormat` / `@JsonIgnore` / `@JsonInclude` / `@JsonProperty` 等**注解不变**（仍在 `com.fasterxml.jackson.annotation`）。
另：`readValue/writeValueAsString` 抛的是非受检异常，原来 `catch (IOException)` 的位置要改（本工程 `TrafficApiHttpClient` 改为统一 `catch (RuntimeException)`）。

### 3.6 其它 Boot 4 / Framework 7 API 变更
| 位置 | 迁移前 | 迁移后 |
| --- | --- | --- |
| `ApplicationConfig` | `SimpleClientHttpRequestFactory#setConnectTimeout(int)` | `setConnectTimeout(Duration)`（6.1 起只有 Duration 重载） |
| `TrafficApiHttpClient` | `ResponseEntity#getStatusCodeValue()` / `ClientHttpResponse#getRawStatusCode()` | `getStatusCode().value()` |
| `TrafficApiHttpClient` | `DefaultResponseErrorHandler#handleError(ClientHttpResponse)` | 只保留 `handleError(URI, HttpMethod, ClientHttpResponse)` |
| `TrafficApiHttpClient` | `UriComponentsBuilder.fromHttpUrl(...)` | `fromUriString(...)` |
| `MultipartFileUtil` | `CommonsMultipartFile` | 自建 `FileItemMultipartFile` 适配器（Framework 6 移除了该类） |
| `OssAutoConfiguration` | 仅靠 `spring.factories` 注册 | 加 `@AutoConfiguration` + `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Boot 3 起只认 imports 文件） |
| `LoginUser#getAuthorities()` | `return null` | 返回 `permissions` 映射的 `GrantedAuthority`（Security 7 的 `createSuccessAuthentication` 会 `new LinkedHashSet<>(authorities)`，null 直接 NPE） |
| `TokenService` | `Jwts.builder().setClaims().signWith(SignatureAlgorithm.HS512, secret)` | `Jwts.builder().claims().signWith(SecretKey, Jwts.SIG.HS512)`；`Jwts.parser().verifyWith(key).build().parseSignedClaims()` |
| `SwaggerConfig` | springfox `Docket` | springdoc `OpenAPI` Bean（`@ConditionalOnProperty(swagger.enabled)`） |
| 控制器注解 | `@Api` / `@ApiOperation` / `@ApiImplicitParam(s)` / `@ApiModel(Property)` | `@Tag` / `@Operation` / `@Parameter(in=ParameterIn.*)` / `@Parameters` / `@Schema` |

JWT 密钥：jjwt 0.12+ 对 HS512 强制 ≥512bit 密钥。历史 `token.secret` 只有 26 字节，故 `TokenService#getSecretKey()` 在不足 64 字节时用 SHA-512 派生。
**副作用：升级后旧令牌全部失效，需要重新登录**（令牌本身 120 分钟过期）。

### 3.7 ShardingSphere 5.5.3 API 变化
- `getType()` / `getProps()` 不再需要覆盖（`TypedSPI` 默认实现），否则编译报 “method does not override”；
- `AlgorithmConfiguration` 包名 `org.apache.shardingsphere.infra.config.algorithm.*` → `org.apache.shardingsphere.infra.algorithm.core.config.*`；
- 5.5.x 起 `shardingsphere-jdbc` 不再自带分片实现，需额外引入 `shardingsphere-sharding-core`。

### 3.8 配置项变更（`application.yml` / `application-druid.yml`）
| 迁移前 | 迁移后 | 原因 |
| --- | --- | --- |
| `spring.redis.*` | `spring.data.redis.*` | Boot 3 起改名 |
| `spring.mvc.pathmatch.matching-strategy: ant_path_matcher` | 删除 | Framework 7 只有 PathPatternParser，该属性已下线 |
| `spring.main.allow-circular-references: true` | 删除 | Framework 6.2 起循环引用永久禁止 |
| （无） | `springdoc.api-docs.enabled/swagger-ui.enabled: false` | 与 `swagger.enabled=false` 保持一致 |
| `filter.wall.config.multi-statement-allow` | 追加 `select-where-alway-true-check: false` | druid 1.2.28 的 wall 对 `WHERE 1 = 1` 判为“恒真条件”直接抛 SQLException |

## 4. 踩坑时间线（按报错顺序，便于复现）

1. `程序包 org.springframework.web.multipart.commons 不存在` → `CommonsMultipartFile` 已删除，自建适配器。
2. `package lombok does not exist` → lombok 在 `ruoyi-common` 里改成 `provided` 后不再传递；保持 compile 作用域（或每个模块显式声明）。
3. `cannot access jakarta.servlet.ServletException` → `jakarta.servlet-api` 不能是 `provided`（不传递），改 compile 作用域。
4. `package com.baomidou.mybatisplus.extension.service does not exist` → 见 3.2。
5. `package org.apache.shardingsphere.sharding.api.sharding.standard does not exist` → 见 3.7。
6. `SpringSecurity: cannot find symbol WebSecurityConfigurerAdapter` → 见 3.3。
7. `NoSuchMethodError Memory.close()`（`/monitor/server`）→ Elasticsearch 7.15 的 `org.elasticsearch:jna` 与官方 `net.java.dev.jna` 同为 `com.sun.jna` 包名，旧类抢先加载。**在 dependencyManagement 里给两个 ES 依赖加 `<exclusion>org.elasticsearch:jna</exclusion>`**。
8. `No qualifying bean of type 'com.ruoyi.common.config.OssProperties'` → `spring.factories` 失效，见 3.6。
9. `No qualifying bean of type 'org.quartz.Scheduler'` → 需要 `spring-boot-starter-quartz`。
10. `No qualifying bean of type 'org.springframework.cache.CacheManager'` → 需要 `spring-boot-starter-cache`。
11. 登录报 `Cannot invoke "java.util.Collection.size()" because "c" is null` → `LoginUser#getAuthorities()` 不能返回 null。
12. `NoSuchMethodError 'void com.sun.jna.Memory.close()'` 已修为 200。
13. `APPLICATION FAILED TO START ... cycle` → `@Lazy`，见 3.4。

## 5. 实机验收记录（2026-11-14，Windows + JDK 17.0.21）

环境：backend 9989（MySQL 8 @127.0.0.1:3307）↔ api 9902（openGauss @127.0.0.1:5432，WSL docker），共享 Redis 6379；JVM 均 `-Xms512m -Xmx1024m`。

| # | 用例 | 结果 |
| --- | --- | --- |
| 1 | `GET /captchaImage` | 200，返回 base64 图形 + uuid |
| 2 | `POST /login`（admin） | 200，返回 token（184 字符） |
| 3 | `GET /getInfo`、`/getRouters` | 200，角色/权限/菜单树正常 |
| 4 | `GET /system/user/list`、`/system/role/list`、`/system/dict/type/list`、`/system/config/list`、`/system/notice/list` | 200，`total` 与 MySQL 行数一致（PageHelper 分页正常） |
| 5 | `POST /system/config` + `DELETE /system/config/{id}` | 200（Jackson 3 反序列化 + 校验 + MP 写入/删除） |
| 6 | `GET /monitor/server` | 200（OSHI/JNA 修复后） |
| 7 | `GET /manager/carinfo/list`、`/base/section/list`、`/base/gantry/list`、`/base/location/list` | 200，total 185 / 85 / 1526 / 1644 |
| 8 | `GET /manager/carinfo/export`、`/downTemplate/carinfo`、`/downTemplate/carExcept`、`/manager/exceptrecord/export` | 200，分别返回 15676 / 7178 / 13175 / 34679 字节 xlsx（POI 4.1.2 + easypoi-base 模板导出） |
| 9 | `POST /manager/bigScreen/export/display` | 200，返回 taskId（跨服务提交成功） |
| 10 | `GET /manager/bigScreen/topTen`、`/incomeStatistic` | 200，`X-Data-Source: LEGACY_DB`（api 侧 `traffic.bigscreen.stats-enabled=false` 返回 503，按契约回退 legacy，属预期） |
| 11 | `/base/snapshotflow/list` | 200（api 未起时是 503 降级，api 起后 200） |

## 6. 复现步骤

```powershell
# 1. 构建（JDK 17）
$env:JAVA_HOME='D:\jdk\temurin-17\jdk-17.0.21+9'
& 'D:\work\apache-maven\bin\mvn.cmd' -B -DskipTests package

# 2. 启动（凭据由环境注入；脚本在 D:\work\runtime-logs，不进仓库）
& 'D:\work\runtime-logs\rebuild-restart-backend.ps1'

# 3. 登录（验证码答案在 Redis captcha_codes:<uuid>）
#    见 D:\work\runtime-logs 下的验收脚本片段
```

> 生产/CI 需要注入：`EXPORT_DOWNLOAD_SECRET`（fail-fast，禁止默认值回退）、`TRAFFIC_API_INTERNAL_TOKEN`（与 api 侧 `TRAFFIC_INTERNAL_TOKEN` 一致）。

## 7. 回滚

- 代码：`git revert` 对应迁移提交（迁移在单个提交内，便于整体回滚）。
- 运行期无需改库：本次没有任何 DDL/DML 变更（仅 `sys_config` 的临时测试数据已删除）。
- 旧 jar 仍在 CI/制品库中，回滚即换制品。

## 8. JDK 21 / 25 分支说明

`car-monit-backend-jdk21` / `car-monit-backend-jdk25` 与本分支的差异仅两处属性：

```xml
<java.version>21</java.version>
<maven.compiler.release>21</maven.compiler.release>
```

Spring Boot 4.1.2 的 JDK 支持范围是 17–27，因此三支同版本；若后续 Boot 5 提高基线，再按分支分别取“该 JDK 能跑的最新稳定版”。

### 8.1 JDK 25 分支必须加 `-proc:full`
**JDK 23 起 `javac` 默认不再自动执行注解处理器**（只在不显式指定时才隐式关闭），后果是 Lombok 生成的
构造器/Getter/`log` 全部缺失，报错形态是成片的
`constructor Xxx in class Xxx cannot be applied to given types` / `cannot find symbol: variable log`。
因此 `car-monit-backend-jdk25/pom.xml` 的 `maven-compiler-plugin` 增加了：

```xml
<configuration>
    <proc>full</proc>
</configuration>
```

> `-proc:full` 是 JDK 21 才有的取值，所以**只在 jdk25 分支声明**；17/21 分支加了会直接 `invalid flag`。

### 8.2 其它 JDK 版本差异
- JDK 24+ 移除了 `SecurityManager`，本工程未使用；
- 需要 `--add-opens` 的库（如 api 侧的 Orika）要在启动参数显式声明；
- JDK 25 分支的字节码基线是 25（Boot 4.1 的 ASM 支持 major 69），17/21 分支分别是 17/21。

### 8.3 三支实机验收结论（2026-11-14）
| 分支 | 编译/打包 | 启动 | 登录 | getInfo/getRouters | 分页列表 | /monitor/server | 业务列表 | Excel 导出 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jdk17 (17.0.21) | ✅ | ✅ | 200 | 200 | 200 | 200 | 200 | 15676B |
| jdk21 (21.0.12) | ✅ | ✅ | 200 | 200 | 200 | 200 | 200 | 15676B |
| jdk25 (25.0.4.1) | ✅（含 `-proc:full`） | ✅ | 200 | 200 | 200 | 200 | 200 | 15676B |

## 9. 独立复核遗留项闭环（2026-11-14 第二轮）

| # | 复核发现 | 处理 |
| --- | --- | --- |
| 1 | `ResilientApiExecutor` 仍导入 Jackson 2 的 `JsonProcessingException`，Jackson 3 下错误码分类语义漂移 | 改为 `tools.jackson.core.JacksonException`（Jackson 3 的非受检异常），`instanceof` 同步调整 |
| 2 | `LoginUser#getAuthorities()` 未过滤空白权限串，`SimpleGrantedAuthority` 遇空串会抛异常 | 加 `filter(p != null && !p.isBlank())` + `trim` + `distinct` |
| 3 | 根 pom 注释写「PageHelper 6.x / jsqlparser 4.7/4.9」，实际是 4.1.1 + 4.9 | 注释订正 |
| 4 | CI 触发覆盖需书面确认 | **口径**：`car-monit-backend-jdk17/21/25` 的 push 只触发 `self-hosted-ci`（compile + test + 工具链断言）；`ci.yml` / `release.yml` 的托管流水线在对应分支合入/发布时执行。当前托管 runner 账单受限，不把三个 jdk 分支追加进托管触发列表 |
| 5 | `token.secret` 等历史明文凭据仍在仓库（迁移前的基线，非本轮引入） | 列为**安全债，单独整改**：应改为 `${TOKEN_SECRET}` 强制注入 + 长度/随机性校验并轮换；本轮不动，避免影响既有部署与令牌签发。运维须按注入凭据的规范执行，禁止把新凭据写回仓库 |
| 6 | `ShardingSphereConfig` 需 `sharding.enabled=true`，而配置里只有 `snapshot.flow.sharding.enabled`，分表 Bean 静默不注册 | 与迁移前基线一致、属既有设计，不擅自改变运行期行为；如需启用分表，必须显式设置顶层 `sharding.enabled=true` 并做回归 |

### 9.1 本轮验证
- 三分支 `mvn -DskipTests=false test` 通过；改动均为编译期/注释/文档层面。
- 启动前置 smoke（`--add-opens` 生效性、字节码 major、交付入口参数）由 api 侧 `self-hosted-ci` 覆盖；backend 无 Orika 依赖，不需要该参数。