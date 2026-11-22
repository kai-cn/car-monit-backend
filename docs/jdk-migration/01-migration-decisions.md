# 01 · 迁移决策与改动清单

## 1. 总体策略

1. 先完成 JDK17 全链路（编译 → 起服务 → 角色化实机验证 → 文档），再把同一套改动传播到 21/25。
2. **保持 `javax.*` 命名空间**，不做 Jakarta EE 迁移；把 Spring Boot 升到 2.x 最终维护版 `2.7.18`，
   Spring Framework 锁 `5.3.39`，用最小侵入方式换取 JDK 9+ 兼容性。
3. 每个分支的 Maven `release`、CI JDK、启动脚本三者**必须一致**；工具链版本由分支名唯一决定。
4. 依赖版本显式锁定，避免 Boot BOM 与散落的子模块声明互相遮蔽。
5. 独立审查整改后：任何「构建成功」的结论都必须对应最终 jar；任何「实机通过」的结论都必须
   对应最终 jar 启动后的日志与冒烟结果，不以旧构建日志代替。

## 2. POM 变更（两侧）

### backend（根 `pom.xml`）

| 项 | 迁移前 | 迁移后 |
| --- | --- | --- |
| `java.version` / `maven.compiler.release` | 1.8 | 分支值 17 / 21 / **21（JDK25 分支）** |
| Spring Boot BOM | 2.5.15 | `2.7.18` |
| Spring Framework BOM | 跟随 Boot | 显式 `5.3.39` |
| `lombok.version` | 旧版 | `1.18.48` |
| `jaxb-api.version` | 缺失 | `2.3.1`（jjwt 0.9.1 依赖 `javax.xml.bind.DatatypeConverter`） |
| `servlet-api.version` | 缺失 | `4.0.1` |
| `mysql-connector-java.version` | 旧版 | `8.0.33` |
| jsqlparser / mybatis | 未锁 | `4.9` / `3.5.16` |
| `maven-compiler-plugin` | 旧版 | `3.13.0`，统一用 `<release>` + `<parameters>true</parameters>` |
| `maven-surefire-plugin` | 旧版 | `3.1.2` |

`ruoyi-admin/pom.xml`：`spring-boot-maven-plugin 2.5.15 → 2.7.18`、`maven-war-plugin 3.1.0 → 3.4.0`。

### api（根 `pom.xml`）

| 项 | 迁移前 | 迁移后 |
| --- | --- | --- |
| Spring Boot parent | `2.4.5` | `2.7.18` |
| `java.version` / release / source / target | 1.8 | 分支值 17 / 21 / **21（JDK25 分支）** |
| `druid` / `mybatis-plus` / `spring-kafka` | 旧版 | `1.2.20` / `3.5.5` / `2.8.11` |
| `rabbitmq.version` + 无版本 `spring-boot-starter-amqp` | 存在 | 删除（无版本声明会遮蔽父 BOM） |
| `forest-spring-boot-starter`（`pro-base-common`） | `1.5.9` | `1.8.1` |
| `lombok.version` | 旧版 | `1.18.48` |
| `spring-framework.version` | 继承 Boot 2.7.18 BOM 的 `5.3.31` | **显式覆盖为 `5.3.39`** |
| `maven-compiler-plugin` | 旧版 | `3.13.0` |

> api 侧以 `spring-boot-starter-parent:2.7.18` 为父 POM，原本解析到 Spring Framework 5.3.31，
> 与 backend 的 5.3.39 不一致（独立审查发现，fat jar 内 `spring-core-5.3.31.jar` 为证）。
> 由于是 parent 而非 BOM import，在子 POM `<properties>` 中覆盖 `spring-framework.version` 即可生效，
> 已在三个 api 分支统一对齐到 5.3.39，保持同一安全补丁级别。

`pro-business-api/pom.xml` 删除了模块级 compiler 配置，编译基线统一由父 POM 的 `release` 控制，
避免 21/25 分支出现「父 POM 改了但子模块仍按 1.8 编译」的漂移。

### api（`pro-base-common/pom.xml`）生产依赖范围整改

独立审查后的最终重建发现 `spring-boot-starter-test` 在 `pro-base-common` 中为**编译 scope**，
导致测试库参与生产依赖解析，并在离线重建时要求 `spring-test:5.3.39` 作为 compile 依赖存在。
三个 api 分支已统一改为：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <!-- 仅测试期使用：避免 JUnit / Mockito / spring-test / hamcrest 打进生产 fat jar -->
    <scope>test</scope>
</dependency>
```

整改后最终 fat jar 不再包含 JUnit、Mockito、`spring-test`、AssertJ。
`hamcrest-2.2.jar`、`json-path-2.7.0.jar`、`json-smart-2.4.11.jar` 仍来自
Boot 2.7.18 自带 `spring-boot-starter-test` POM 的 compile-scope 传递依赖，
属于上游 POM 设计，已在 `evidence-build-artifacts.txt` 中显式列出而非从文档中隐藏。
依赖树见 `D:\work\runtime-logs\api-dependency-tree.log` 与
`D:\work\runtime-logs\api-dependency-tree-reactor.log`。

## 3. 源码与配置改动（三个分支一致）

| 文件 | 改动 | 原因 |
| --- | --- | --- |
| `ruoyi-admin/.../Base64DecodeMultipartFile.java` | `sun.misc.BASE64Decoder` → `java.util.Base64.getMimeDecoder()`，去掉无意义的逐字节归一化循环 | JDK 9+ 移除 `sun.misc` |
| `ruoyi-system/.../SqlLogInterceptor.java` | `sql.replaceFirst("\\?", Matcher.quoteReplacement(paramValue))` | 参数值含 `$2a$10$...`（BCrypt）时会被当作正则分组引用而抛异常 |
| backend `application.yml` | 新增 `spring.mvc.pathmatch.matching-strategy: ant_path_matcher` | Boot 2.6+ 默认 PathPatternParser 与旧 Swagger/拦截器不兼容；**api 侧该配置迁移前已存在，本次只补 `main:` 块** |
| 两侧 `application.yml` | 新增 `spring.main.allow-circular-references: true`、`allow-bean-definition-overriding: true` | Boot 2.6+ 默认禁止循环引用与 Bean 覆盖 |
| 两侧 `application.yml` | 保留 `vehicleMonitor.baseUrl`、`traffic-api.internal-token` / `traffic.security.internal-token` 的环境变量注入形态 | 不改部署约定 |

## 4. JDK25 的上限（实测）与决策

**实测证据**（2026-11-11）：

- `--release 25` 编译时，api 侧 Lombok 注解处理器在 JDK25 下失效，出现 39 个「找不到符号」编译错误。
- backend 侧即便编译成功生成 class major 69，`spring-boot-maven-plugin:2.7.18:repackage` 也会失败：
  `Unsupported class file major version 69`；失败后残留一个 22 字节的空 `ruoyi-admin.jar`。
- Spring Framework 5.3.39 内嵌 `org.springframework.asm.Opcodes` 最高只有 `V21 = 65`，
  既不能打包 major 69 的类，运行时组件扫描也无法读取。

**决策**：JDK25 分支 = **JDK 25 构建工具链 + JDK 25 运行时 + Java 21 字节码基线**。

```xml
<!-- 语言/字节码基线 21；运行时 JDK 为 25，由 CI 与启动脚本保证 -->
<java.version>21</java.version>
<maven.compiler.release>21</maven.compiler.release>
```

JDK25 的 `maven-compiler-plugin` 只保留**真正生效**的一项配置 —— 显式 Lombok 注解处理器：

```xml
<annotationProcessorPaths>
    <path>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <version>${lombok.version}</version>
    </path>
</annotationProcessorPaths>
```

> **独立审查整改**：初版曾配置 `fork=true` + `<jvmArgs>`（`--add-opens` / `--enable-native-access`），
> 但 `maven-compiler-plugin:3.13.0` 根本没有 `jvmArgs` 参数，构建日志明确出现
> `Parameter 'jvmArgs' is unknown ...`，这些 JVM 参数被静默丢弃。
> 实测去掉 `fork` 与 `jvmArgs`、只保留 `annotationProcessorPaths` + Lombok 1.18.48 +
> `release=21`，在 JDK 25 上仍 `BUILD SUCCESS` 且无该警告。已删除这段无效配置。

另外，初版在 `car-monit-backend-jdk25/ruoyi-admin/pom.xml` 里为 repackage 插件加过
ASM 9.11.1 / `spring-boot-loader-tools` 覆盖（针对 major 69 的旧尝试）；改成 Java 21 字节码后
已无必要，且与 jdk17/21 分支产生无谓差异，独立审查后已删除。

> 独立复验补充：三个 backend `ruoyi-admin/pom.xml` 仍保留一个 `<fork>true</fork>`，
> 这是 `spring-boot-maven-plugin` 的 devtools 配置，与 `HEAD` 基线一致，不是
> `maven-compiler-plugin` 的 `fork`/`jvmArgs` workaround；复验已确认这一点，无需改动。

这样既拿到 JDK 25 运行时的 GC/安全/性能收益，又不会破坏 Boot 2.7 / Spring 5.3 的组件模型。
**若业务要求真正的 Java 25 字节码，必须先单独立项完成 Spring Boot 3.x + Jakarta EE 命名空间迁移**，
那属于另一次架构升级，不应混在本次 JDK 迁移里。

> 备注：XML 注释中不允许出现连续两个连字符 `--`。JDK25 backend POM 曾因注释里写了
> `--release 25` 导致 `Non-parseable POM`，已改为「不设置 release 25」，见
> [02-build-evidence.md](02-build-evidence.md#4-失败案例与修复)。

## 5. CI/CD 工具链对齐

| 侧 | 文件 | 改动 |
| --- | --- | --- |
| backend | `.github/workflows/ci.yml` | openEuler 容器：17/21 用 `dnf install -y java-{v}-openjdk-devel`；25 用 Adoptium Temurin 25 tarball（欧拉仓库无 JDK25）写入 `JAVA_HOME`/`GITHUB_PATH` |
| backend | `release.yml` | `java-version` 8 → 分支 JDK |
| backend | `self-hosted-ci.yml` | 补上各 JDK 分支的 push 触发；**新增 `actions/setup-java@v4` 按分支固定 JDK + 版本断言** |
| api | `_java.yml`（reusable） | `name`/`jdk-version` 默认值/描述改为分支 JDK；安装命令改为读取 `inputs.jdk-version`；增加版本断言；删除从未使用的 `jdk-distribution` 入参 |
| api | `master.yml` / `pr.yml` / `release.yml` | 调用 `_java.yml` 的 `jdk-version` 原本还是 `"8"`，已全部改为分支值 |
| api | `cd-standalone.yml` | `java-version` 改为分支值 |
| api | `self-hosted-ci.yml` | 补上各 JDK 分支的 push 触发；**新增按分支固定 JDK + 版本断言** |

共重写 **25** 个 workflow 文件；6 个分支合计 **54** 个 YAML 全部通过 js-yaml 解析校验。

**审查整改（阻断项）**：`self-hosted-ci.yml` 是**唯一**对 JDK 分支 push 生效的工作流，
原实现只打印 `java -version`/`mvn -v`，用 runner 的环境 JDK 编译，可能在 jdk17 分支上跑出 JDK21 构建。
现在每分支显式 `setup-java` 固定 `java-version`（17/21/25，temurin），并有
`java -version | grep -qE 'version "<v>\.'` 断言，不匹配直接失败。

**分支触发的设计取舍**：`ci.yml` / `master.yml` / `release.yml` 等主集成工作流仍只监听
`master` / `*-java-V3` / tag，不监听 `*-jdkNN` 分支，避免 push 一次同时跑两套重型 CI。
JDK 分支的门禁由 `self-hosted-ci.yml` 承担（编译 + 单测），待分支合并到 V3/master 后再走完整主 CI。
这是有意设计，不是遗漏；如需在 push 时同时跑主 CI，可单独为这些分支追加触发。

## 6. 明确不做的事

- 不做 Jakarta / Spring Boot 3.x 迁移。
- 不改业务接口、表结构、Redis key 约定、内部令牌头名称。
- 不创建第二个 MySQL 8 实例、不额外启动 ES/Kafka/Redis。
- **review 完成前不 push、不触发 GitHub CI**；6 个 JDK 分支目前都没有 upstream。

## 7. 最终离线依赖修复与全量重建

独立审查整改后的第一次 final 重建在三个 api 分支失败：

```text
Could not resolve dependencies for project com.ruoyi:pro-base-common
dependency: org.springframework:spring-test:jar:5.3.39 (compile)
Cannot access public ... in offline mode and the artifact ... has not been downloaded from it before.
```

排查结论与处理：

1. 本机实际生效的 Maven 本地仓库是 `D:\work\apache-maven\repository`，不是默认 `~/.m2/repository`。
2. Spring 5.3.39 的其他构件已缓存，但 `spring-test-5.3.39.jar` 缺失；这是 api 把
   `spring-boot-starter-test` 声明为 compile scope 的直接后果。
3. 已用可达的 Aliyun 镜像补取缺失构件，日志 `D:\work\runtime-logs\spring-test-fetch.log`：

   ```bash
   mvn -B org.apache.maven.plugins:maven-dependency-plugin:3.6.1:get \
     -Dartifact=org.springframework:spring-test:5.3.39 \
     -Dtransitive=false
   ```

4. 同步把三个 `pro-base-common/pom.xml` 的 starter-test 改为 `<scope>test</scope>`，消除根因。
5. 重新执行 6 个离线 clean 构建，日志为
   `D:\work\runtime-logs\jdk{17,21,25}-{api,backend}-build-final2.log`，全部 `BUILD SUCCESS`。
6. 用最终 jar 重启并跑 JDK17/21/25 冒烟，各 `checks=26 fails=0`；证据见
   [02-build-evidence.md](02-build-evidence.md) 与 [03-real-machine-validation.md](03-real-machine-validation.md#5-最终-jar-复验整改后)。
7. 最终只读闸门 `D:\work\runtime-logs\evidence-final-gate.txt` 共 146 项检查、0 失败，
   覆盖 POM 解析、版本矩阵、workflow、jar 内容、构建/冒烟日志、证据文件、git 卫生与清理状态。
