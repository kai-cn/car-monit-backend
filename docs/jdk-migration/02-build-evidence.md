# 02 · 构建与静态校验证据

所有证据日志位于 `D:\work\runtime-logs`。最终构建命令统一为：

```bash
export JAVA_HOME="<该分支对应的 JDK>"
export PATH="$JAVA_HOME/bin:$PATH"
export MAVEN_OPTS="-Xmx768m -Dfile.encoding=UTF-8"
mvn -o -B -DskipTests clean package
```

> 注意：Git Bash 里 `java -version` 的便捷输出可能仍显示 JDK 8（PATH 解析与 shell 缓存），
> 因此**不以此判定工具链**，而是以 Maven 日志、产物 class 文件版本号、启动横幅和
> `jcmd VM.version` 为准。

## 1. 最终六侧 clean 构建结果

整改后的权威构建日志为
`D:\work\runtime-logs\jdk{17,21,25}-{api,backend}-build-final2.log`。
六个日志均 `BUILD SUCCESS`、无 `[ERROR]`；下表数字取自该轮最终 fat jar。

| 分支 | 最终构建日志 | 应用主类 | class major | fat jar 大小 | Spring core |
| --- | --- | --- | --- | --- | --- |
| `car-monit-api-jdk17` | `jdk17-api-build-final2.log` | `EcBusinessApiApplication` | **61** | 229,621,226 B | `spring-core-5.3.39.jar` |
| `car-monit-backend-jdk17` | `jdk17-backend-build-final2.log` | `RuoYiApplication` | **61** | 216,429,268 B | `spring-core-5.3.39.jar` |
| `car-monit-api-jdk21` | `jdk21-api-build-final2.log` | `EcBusinessApiApplication` | **65** | 229,617,563 B | `spring-core-5.3.39.jar` |
| `car-monit-backend-jdk21` | `jdk21-backend-build-final2.log` | `RuoYiApplication` | **65** | 216,427,791 B | `spring-core-5.3.39.jar` |
| `car-monit-api-jdk25` | `jdk25-api-build-final2.log` | `EcBusinessApiApplication` | **65** | 229,614,106 B | `spring-core-5.3.39.jar` |
| `car-monit-backend-jdk25` | `jdk25-backend-build-final2.log` | `RuoYiApplication` | **65** | 216,424,272 B | `spring-core-5.3.39.jar` |

产物矩阵已落盘 `D:\work\runtime-logs\evidence-build-artifacts.txt`。
api 生产 fat jar 不再包含 JUnit / Mockito / `spring-test` / AssertJ；
剩余 `hamcrest-2.2.jar`、`json-path-2.7.0.jar`、`json-smart-2.4.11.jar`
是 Boot 2.7.18 `spring-boot-starter-test` POM 的 compile-scope 传递依赖，
已在证据矩阵中显式列出。依赖树见 `api-dependency-tree.log` /
`api-dependency-tree-reactor.log`。

字节码版本取证方式（不依赖 `javap` 是否可用）：

```bash
od -An -t u1 -j 6 -N 2 <Application.class> | awk '{print "major="($1*256+$2)}'
# 17 → 61, 21 → 65, 25 → 69
```

Reactor 摘要示例（JDK17 backend）：

```text
ruoyi .............................................. SUCCESS
ruoyi-common ....................................... SUCCESS
ruoyi-system ....................................... SUCCESS
ruoyi-framework .................................... SUCCESS
ruoyi-quartz ....................................... SUCCESS
ruoyi-generator .................................... SUCCESS
ruoyi-admin ........................................ SUCCESS
BUILD SUCCESS
```

早期的 `jdk17-api-build.log`、`jdk21-api-build.log`、`jdk25-api-build2.log`、
`jdk25-backend-build3.log` 以及 `*-build-final.log` 均作为历史过程记录保留；
**最终交付判定只采用 `*-build-final2.log` 与其对应 jar**。

## 2. JDK25 运行时版本取证

最终 jar 复验时的启动横幅：

```text
jdk25-api-recheck.console.log
  Starting EcBusinessApiApplication v1.0 using Java 25.0.4.1 ...
jdk25-backend-recheck.console.log
  Starting RuoYiApplication using Java 25.0.4.1 ...
```

服务仍在运行时，对两个进程实际执行了 `jcmd <pid> VM.version`，输出已落盘
`D:\work\runtime-logs\evidence-jdk25-jcmd.txt`：

```text
=== pid 20148 ===
OpenJDK 64-Bit Server VM version 25.0.4.1+1-LTS
JDK 25.0.4.1
=== pid 35044 ===
OpenJDK 64-Bit Server VM version 25.0.4.1+1-LTS
JDK 25.0.4.1
```

强制换时间范围避开 Redis 缓存后的 backend→API 实链证据已落盘
`D:\work\runtime-logs\evidence-jdk25-cache-miss.txt`：

```text
/manager/bigScreen/carStatistics -> HTTP 200 code=200 X-Data-Source=API
/manager/bigScreen/carAudit      -> HTTP 200 code=200 X-Data-Source=API
```

即：**运行时确实是 JDK 25，而产物字节码是 Java 21（major 65）**，与
[01-migration-decisions.md](01-migration-decisions.md#4-jdk25-的上限实测与决策) 的决策一致。
`evidence-jdk25-runtime.txt` 仅保存更早一轮 Spring Boot 启动横幅；独立复验指出其中曾有一条
硬编码 `jcmd` 注释，现已删除。真实的 `jcmd VM.version` 输出只保存在
`evidence-jdk25-jcmd.txt`，两者用途已明确区分。

## 3. CI workflow 与 XML 静态校验

- 工具：`js-yaml`（本地临时安装，仅用于校验，不进入版本库）。
- 范围：6 个分支 `.github/workflows/*.yml` 共 **54** 个文件。
- 断言：可解析、存在 `on:` 触发、存在 `jobs`、无 TAB 缩进。
- 结果：`YAML_TOTAL=54 YAML_BAD=0`（`D:\work\runtime-logs\evidence-yaml-validation.txt`）。
- 抽查：backend `ci.yml` 9 个 job；api `master.yml` 12 个 job；
  六个 `self-hosted-ci.yml` 的 push 分支分别包含对应的 JDK 分支，并有
  `actions/setup-java@v4` + `java -version` 版本断言。

另对 6 个工作树的全部 XML 做了 well-formed 校验：405 个文件中 6 个解析失败，
均为**迁移前就存在的**非 POM 文件（`分区表分页查询Mapper示例.xml`、空的
`PulsarMessageRecordMapper.xml`，三个分支各一份），与本次迁移无关，未改动。
输出落盘 `D:\work\runtime-logs\evidence-xml-validation.txt`；最终复核
`POM_TOTAL=30 POM_BAD=0`。

最终只读闸门 `D:\work\runtime-logs\evidence-final-gate.txt`：
`FINAL_GATE_CHECKS=146 FINAL_GATE_FAILS=0 FINAL_GATE_VERDICT=PASS`。
覆盖 POM 版本矩阵、无效 compiler 参数残留、ASM 残留、starter-test scope、
workflow JDK 钉死、最终构建/冒烟日志、jar 内容、git 卫生、文档敏感信息与清理状态。
当前运行时状态见 `evidence-current-runtime-state.txt`。

## 4. 失败案例与修复

| # | 现象 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | `spring-boot-maven-plugin:2.7.18:repackage` 报 `Unsupported class file major version 69`，并残留 22 字节空 `ruoyi-admin.jar` | Spring 5.3.39 内嵌 ASM 上限 `V21=65` | JDK25 分支改 Java 21 字节码基线，保持 JDK 25 工具链/运行时 |
| 2 | api `jdk25-api-build.log` 39 个「找不到符号」 | JDK25 下 Lombok 注解处理器未生效 | 有效修复是显式 `annotationProcessorPaths` + Lombok 1.18.48 + `release=21`；初版 `fork`/`jvmArgs` 为无效配置，审查后已删除 |
| 3 | `Non-parseable POM ... in comment after two dashes (--) next character must be > not r` | JDK25 backend POM 注释中写了 `--release 25`，XML 注释禁止 `--` | 注释改为「不设置 release 25」，重新 clean 构建成功（`jdk25-backend-build3.log`） |
| 4 | api 调用方工作流仍是 `jdk-version: "8"` | `_java.yml` 默认值改了但 caller 未同步 | 重写 `master.yml`/`pr.yml`/`release.yml`，三分支全部对齐 |
| 5 | JDK21/25 工作流仍有 JDK8 引用 | 传播时只改了根目录 POM | 用脚本统一重写 25 个 workflow 文件 |
| 6 | **独立审查**：`self-hosted-ci.yml`（唯一对 JDK 分支 push 生效的 CI）只打印 `java -version`，不装/不钉 JDK | runner 上的环境 JDK 可能与分支不符 | 六个分支新增 `actions/setup-java@v4` 按分支钉 17/21/25 + `java -version` 断言，不匹配直接失败 |
| 7 | **独立审查**：api 三个分支 fat jar 内是 `spring-core-5.3.31.jar`，backend 是 `5.3.39.jar` | api 继承 `spring-boot-starter-parent:2.7.18` 默认 5.3.31 | api 根 POM 增加 `<spring-framework.version>5.3.39</spring-framework.version>` 覆盖，重建后六侧统一 |
| 8 | **独立审查**：JDK25 两个 POM 的 `<jvmArgs>` 触发 `Parameter 'jvmArgs' is unknown for plugin 'maven-compiler-plugin:3.13.0'`，flags 被静默丢弃 | 该插件没有 `jvmArgs` 参数 | 删除 `fork` + `jvmArgs`；只保留 `annotationProcessorPaths` + Lombok 1.18.48，重建成功且无警告 |
| 9 | **独立审查**：backend-jdk25 `ruoyi-admin/pom.xml` 残留 ASM 9.11.1 / loader-tools 覆盖，jdk17/21 没有 | `--release 25` 时期的遗留，改 major 65 后已无用 | 删除该 39 行块，三个 backend 分支可对齐 |
| 10 | **独立审查**：api `_java.yml` 的 `jdk-version` 入参未被安装步骤使用，`jdk-distribution` 从未生效 | 无法阻止「传入 A 却装了 B」 | dnf 包名与 Temurin tarball URL 改为读取 `inputs.jdk-version`，新增版本断言，删除无效入参 |
| 11 | **独立审查**：`jcmd VM.version`、`YAML_TOTAL=54`、50 行 E2E 报告（49 条结果行 + 1 条汇总）、物理删除等结论当时只有模板字符串或脚本，没有持久化输出 | 证据不可复核 | 新增 `jdk17-e2e-record.txt`、`evidence-yaml-validation.txt`、`evidence-xml-validation.txt`、`evidence-jdk25-jcmd.txt`、`evidence-jdk25-cache-miss.txt` 等；删除含硬编码结论的分支文档生成器 |
| 12 | **最终重建**：三个 api 分支 offline 报 `spring-test:jar:5.3.39 (compile)` 未下载 | `pro-base-common` 把 `spring-boot-starter-test` 声明为 compile scope，且本地仓库缺该构件 | 用 `maven-dependency-plugin:3.6.1:get` 从可达 Aliyun 镜像补取 `spring-test:5.3.39`（`spring-test-fetch.log`），并把三个 POM 改为 `<scope>test</scope>` 消除根因 |
| 13 | **最终重建**：`*-build-final.log` 中 api 三侧失败，不能作为交付依据 | 上一条依赖问题尚未闭环 | 全量重跑为 `*-build-final2.log`，六侧 `BUILD SUCCESS`；随后用最终 jar 重跑三套 26/26 冒烟 |
| 14 | **独立复验**：`evidence-jdk25-runtime.txt` 残留一条硬编码 `jcmd` 注释；`jdk17-e2e-record.txt` 被文档误称为「50 条结果行」 | 早期证据生成脚本把汇总行也计入结果数 | 删除硬编码注释，汇总行改为 `RESULT_LINES=49 REPORT_LINES=50`，文档统一改为「50 行报告（49 条结果行 + 1 条汇总）」 |

失败日志 `jdk25-api-build.log`、`jdk25-backend-build.log`、`jdk25-backend-build2.log`、
`*-build-final.log` 作为决策依据保留；成功交付日志见第 1 节表格。

## 5. 持久化证据文件索引

| 文件 | 内容 |
| --- | --- |
| `evidence-yaml-validation.txt` | 54 个 workflow YAML 解析结果 |
| `evidence-xml-validation.txt` | 405 个 XML / 30 个 POM 解析结果 |
| `evidence-build-artifacts.txt` | 最终 6 个 jar 的 class major、大小、Spring core、剩余 compile-scope test 传递依赖 |
| `evidence-jdk25-runtime.txt` | 更早一轮 JDK25 Spring Boot 启动横幅；已删除硬编码 `jcmd` 注释 |
| `evidence-jdk25-jcmd.txt` | 最终 jar 运行时两个进程的真实 `jcmd VM.version` 输出 |
| `evidence-jdk25-cache-miss.txt` | 强制 cache miss 后的 `X-Data-Source=API` |
| `evidence-final-gate.txt` | 146 项最终整改闸门检查 |
| `evidence-current-runtime-state.txt` | 2026-11-12 当前 app Java / infra 监听 / DB 可复核状态 |
| `jdk17-e2e-record.txt` | JDK17 完整角色化 E2E 的 50 行报告（49 条结果行 + 1 条汇总） |
| `jdk{17,21,25}-recheck-smoke.stdout.log` | 最终 jar 的三套 `checks=26 fails=0` |
| `spring-test-fetch.log` | `spring-test:5.3.39` 离线依赖补取记录 |
| `api-dependency-tree*.log` | starter-test scope 整改后的依赖树 |

## 6. 资源约束执行记录

- Maven：`MAVEN_OPTS=-Xmx768m`；app Java：`-Xms512m -Xmx1g`。
- 每轮验证前先停掉旧的 backend/api app Java（不重复启动），验证时只保留 MySQL 3307、Redis 6379、
  ES 9200、Kafka 9092、openGauss 15432 各一个实例。
- 验证结束时 app Java 为 0、infra 各一个实例；2026-11-12 独立复验时这些中间件也已停止，
  当前 app Java 与 infra 监听端口均为 0，无重复实例。DB 清理结论为验证时 live MySQL 结果，
  当前未重启 MySQL 强行复询。见 `evidence-current-runtime-state.txt`。
