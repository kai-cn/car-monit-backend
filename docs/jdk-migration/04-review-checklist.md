# 04 · 独立审查清单（review 完成前禁止 push / 触发 CI）

> 本清单供**独立审查会话**使用。审查人不应依赖迁移执行者的结论，请自行读取 6 个工作树的实际文件、
> `D:\work\runtime-logs` 下的证据日志以及 `D:\work\IdeaProjects\car-monit-backend-new\docs\jdk-migration`，
> 逐项判定并给出「通过 / 关注 / 阻断」三类结论。
>
> 当前状态：两轮首审 + 两轮独立复验均已完成，结论 `PASS_WITH_CONCERNS`、**无阻断项**；
> 仍禁止 push / 触发 CI，直至用户决定后续 commit/push。

## A. 分支与提交卫生

- [ ] 6 个本地分支 `car-monit-{backend,api}-jdk{17,21,25}` 存在且互不为 upstream 关系。
- [ ] `git branch -vv` 显示 JDK 分支**没有 upstream**；`git log` 中不存在本任务的 push 痕迹。
- [ ] 工作树里的改动全部与 JDK 迁移相关，没有误入的临时脚本、口令、令牌或构建产物。
- [ ] 没有把 `D:\work\runtime-logs\api-local.properties` 等含口令文件复制进版本库。
- [ ] 六个分支内的 `docs/jdk-migration-README.md` 与 jdk17-only
      `docs/v3/review/08-jdk17-migration-verify.md` 已清理；权威文档只在
      `car-monit-backend-new/docs/jdk-migration/`。
- [ ] `git status --porcelain` 无 `??` untracked 文件、无 staged 变更。

## B. 编译基线与依赖

- [ ] 每个根 POM 的 `java.version` / `maven.compiler.release` / （api 侧 `source`/`target`）一致且符合分支策略。
- [ ] 子模块没有残留覆盖 `release` 的 `maven-compiler-plugin` 配置。
- [ ] Boot `2.7.18`、Spring `5.3.39`、Lombok `1.18.48`、jaxb-api、servlet-api 版本一致；
      六个最终 fat jar 内均为 `spring-core-5.3.39.jar`。
- [ ] 三个 api `pro-base-common/pom.xml` 的 `spring-boot-starter-test` 为 `<scope>test</scope>`；
      最终 api 生产 fat jar 不含 JUnit / Mockito / spring-test / AssertJ。
- [ ] 没有无版本的依赖声明遮蔽父 BOM；`rabbitmq.version` 残留已清理。
- [ ] `sun.misc.BASE64Decoder` 已彻底移除；`Matcher.quoteReplacement` 修复正确。
- [ ] `application.yml` 的 Boot 2.6+ 三项兼容开关两侧齐全；
      api 侧 `pathmatch: ant_path_matcher` 被正确标注为迁移前既有配置。

## C. JDK25 决策正确性（重点）

- [ ] JDK25 分支 `maven.compiler.release=21` 且注释清楚解释「工具链 25 / 字节码 21」。
- [ ] **compiler plugin 的 `fork` + `jvmArgs`（`--add-opens` / `--enable-native-access`）已删除**；
      `maven-compiler-plugin:3.13.0` 不支持 `jvmArgs`，首审发现这些参数被静默丢弃。
      有效配置只剩 `annotationProcessorPaths` + Lombok 1.18.48 + `release=21`，
      且最终构建日志不再出现 `Parameter 'jvmArgs' is unknown`。
      独立复验确认三个 backend `ruoyi-admin/pom.xml` 中仍存在的 `<fork>true</fork>` 是
      `spring-boot-maven-plugin` devtools 基线配置，与 compiler workaround 无关。
- [ ] POM 注释中**不含 `--`**（XML 规范），曾导致 `Non-parseable POM` 的问题不再复现。
- [ ] 没有任何残留的 major 69 class 或 22 字节占位 `ruoyi-admin.jar`。
- [ ] `ruoyi-admin/pom.xml` 中针对 major 69 的 ASM 9.11.1 / loader-tools 覆盖已删除。
- [ ] 最终 JDK25 运行时由 `evidence-jdk25-jcmd.txt` 证实为
      `OpenJDK 25.0.4.1+1-LTS`，且 `evidence-jdk25-cache-miss.txt` 有两条
      `X-Data-Source=API`。
- [ ] 文档明确写出「真 Java 25 字节码需 Spring Boot 3.x / Jakarta 迁移」这一后续约束。

## D. CI/CD

- [ ] backend `ci.yml` / `release.yml` / `self-hosted-ci.yml` 的 JDK 与分支一致。
- [ ] API `_java.yml` 默认值/描述与 `master.yml`、`pr.yml`、`release.yml` 的 `jdk-version` 一致（不能有 `"8"` 残留）。
- [ ] `_java.yml` 的安装命令与版本断言实际读取 `inputs.jdk-version`；无死的 `jdk-distribution` 入参。
- [ ] `cd-standalone.yml` 的 `java-version` 与分支一致。
- [ ] 六个 `self-hosted-ci.yml` 均有 `actions/setup-java@v4` 按分支固定 17/21/25，并有版本断言。
- [ ] openEuler 缺 JDK25 的处理（Temurin tarball 写 `JAVA_HOME` / `GITHUB_PATH`）语法正确。
- [ ] 所有 workflow YAML 可解析；`YAML_TOTAL=54 YAML_BAD=0` 有持久化输出。
- [ ] **没有实际推送，也没有触发任何 GitHub Actions run**。

## E. 实机验证与清理

- [ ] 6 个 `*-build-final2.log` 全部 `BUILD SUCCESS`；`evidence-build-artifacts.txt` 中
      class major（61/65/65）、fat jar 大小与 `spring-core-5.3.39.jar` 可复核。
- [ ] JDK17 角色化 E2E：admin 建号 → 登录 → 大屏 → 导出状态机 → 下载令牌 → API 查询 → 清理；
      50 行报告（49 条结果行 + 1 条汇总）见 `jdk17-e2e-record.txt`。
- [ ] 用最终 jar 重跑的 JDK17 / JDK21 / JDK25 三套冒烟均 `checks=26 fails=0`，
      日志为 `*-recheck-smoke.stdout.log`。
- [ ] `common` 角色访问 `/system/user/list` 返回 200 已确认为**迁移前既有设计**，不是回归。
- [ ] 两轮共 14 个 E2E 账号已在 `carmonitdb.sys_user` 物理删除；验证时 `remaining_e2e=0`、
      `total_users=8`；未新建测试库、未启动第二个 MySQL。
- [ ] 验证结束时 app Java 为 0、infra 各一个实例；2026-11-12 复验时当前 app Java 与 infra
      监听端口均为 0，无重复实例；DB 清理为验证时 live MySQL 历史结论，见
      `evidence-current-runtime-state.txt`。

## F. 待审查人自行判断的开放项

1. JDK25 采用 Java 21 字节码是否满足「升级到 JDK 25」的业务定义？若不满足，需要单独立项 Boot 3.x / Jakarta 迁移。
2. `spring.main.allow-circular-references` / `allow-bean-definition-overriding` 是兼容性开关，
   长期应否排期消除循环依赖？
3. `/system/user/list` 登录即可访问，是否应补 `@PreAuthorize`？
4. 本地分支改动目前**未提交**。review 通过后是否需要本地 commit、以及后续 push 的时机与顺序。
5. `hamcrest` / `json-path` / `json-smart` 仍作为 Boot `spring-boot-starter-test` POM 的
   compile-scope 传递依赖存在于 api fat jar；是否需要在更高层 POM 用 exclusion 清理，
   应作为独立依赖治理项评估，不影响本次 JDK 迁移正确性。
6. 三个 backend `ruoyi-admin/pom.xml` 的 `<fork>true</fork>` 是 devtools 基线配置，不是
   compiler workaround；独立复验已确认并作为非阻断关注项记录。
7. `jdk17-e2e-record.txt` 是 50 行报告（49 条结果行 + 1 条汇总），不是 50 条结果行；
   文档已按实际行数修正。
8. 2026-11-12 当前 infra 服务已停止，DB 清理计数为验证时历史结论；未重启服务强行复询，
   已在 `evidence-current-runtime-state.txt` 中说明。

## G. 判定口径

| 级别 | 含义 | 处理 |
| --- | --- | --- |
| 阻断 | 编译/启动失败、字节码与声明不符、CI 会跑错 JDK、口令入库、误 push | 修复后重新走构建 + 冒烟 |
| 关注 | 设计取舍或技术债，不影响本次迁移正确性 | 文档记录，另立任务 |
| 通过 | 与清单一致且有证据 | 允许进入「review 完成」状态，之后才讨论 push |

## H. 独立复验结论

| 复验会话 | 范围 | 结论 | 会话标识 |
| --- | --- | --- | --- |
| 复验 A | 构建 / POM / 产物 / CI | `PASS_WITH_CONCERNS` | `agent-97686c28-a21c-4644-b3da-d0b6504d7c65` |
| 复验 B | 文档 / 配置安全 / 实机证据 / 清理 | `PASS_WITH_CONCERNS` | `agent-dc579805-288c-416d-8446-2ac5bbc41939` |

两轮复验均确认 **无阻断项**，首审的 `BLOCKED` 已关闭；本地无 push / CI 触发证据，
no-push/no-CI 红线保持完整。复验中提出的非阻断关注项及闭环：

1. `<fork>true</fork>` 为 `spring-boot-maven-plugin` devtools 基线配置，非 compiler workaround；
   已在 `01` / `04` / `05` 中澄清。
2. `hamcrest` / `json-path` / `json-smart` 为 Boot starter-test POM 的 compile-scope 传递依赖；
   已显式记录并列入独立依赖治理开放项。
3. `jdk17-e2e-record.txt` 的「50 条结果行」表述更正为「50 行报告（49 条结果行 + 1 条汇总）」，
   汇总行改为 `RESULT_LINES=49 REPORT_LINES=50`。
4. `evidence-jdk25-runtime.txt` 的硬编码 `jcmd` 注释已删除；真实输出只在
   `evidence-jdk25-jcmd.txt`。
5. 2026-11-12 当前 infra 服务已停止，DB 清理计数为验证时历史结论；新增
   `evidence-current-runtime-state.txt` 记录当前只读复核结果。

详见 [05-independent-review-record.md](05-independent-review-record.md)。
