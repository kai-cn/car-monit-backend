# 05 · 独立审查记录与整改闭环

> 本文件记录编译通过后启动的两轮只读首审、两轮只读独立复验、发现的问题、整改动作与最终结论。
> **审查完成前不 push、不触发 GitHub CI**；首审、整改、复验期间均未违反该红线。

## 1. 审查与复验会话

| 轮次 | 范围 | 结论 | 会话标识 |
| --- | --- | --- | --- |
| 首审 A | 构建 / 工具链 / CI 正确性 | `PASS_WITH_CONCERNS` | `agent-74eddbe1-5254-4a96-98f4-7c65089c22fe` |
| 首审 B | 配置 / 安全 / 证据可复核性 | `BLOCKED` | `agent-6cf24c95-efda-4d38-abd7-27e6c5c860fd` |
| 复验 A | 构建 / POM / 产物 / CI | `PASS_WITH_CONCERNS` | `agent-97686c28-a21c-4644-b3da-d0b6504d7c65` |
| 复验 B | 文档 / 配置安全 / 实机证据 / 清理 | `PASS_WITH_CONCERNS` | `agent-dc579805-288c-416d-8446-2ac5bbc41939` |

四个会话均为只读：未修改文件、未启动服务、未执行 push、未触发 CI。
首审 B 把 `self-hosted-ci.yml` 未固定 JDK 判定为阻断项，因此首审整体不能进入「review 完成」状态。
两轮复验最初曾被新的用户消息中断，后从各自原 transcript 恢复并继续完成，没有从头重跑、也没有重复创建任务。
复验 A / B 均确认首审的阻断项已关闭、**无剩余阻断项**。

首审同时确认的基线事实：

- 30 个 POM 均可解析，无 JDK8 残留，无 `rabbitmq.version`，无子模块 `release` 覆盖。
- class major `61/65/65`，六个 fat jar 与当时文档所列大小一致。
- 两侧 `application.yml` 的 Boot 2.6+ 兼容开关齐全；迁移 diff 没有新增明文口令。
- `SysUserController#list` 无 `@PreAuthorize` + `.anyRequest().authenticated()` 是迁移前既有设计，
  viewer 访问 `/system/user/list` 返回 200 不是 JDK 迁移回归。
- 六个 JDK 分支无 upstream、无本地迁移提交、无 staged 变更；没有 `origin/*jdk*` 远端跟踪引用。

## 2. 首审发现、整改与复验补充矩阵

| # | 级别 | 发现 | 整改 |
| --- | --- | --- | --- |
| 1 | 阻断 / 关注 | 六个 `self-hosted-ci.yml` 是唯一监听 JDK 分支 push 的工作流，却只打印 `java -version`/`mvn -v`，使用 runner 环境 JDK | 六个分支新增 `actions/setup-java@v4` 按分支固定 `17/21/25` + `Assert toolchain matches branch` 版本断言 |
| 2 | 关注 | api 三个分支实际解析 Spring Framework `5.3.31`，fat jar 为 `spring-core-5.3.31.jar`，与 backend `5.3.39` 不一致 | 三个 api 根 POM 增加 `<spring-framework.version>5.3.39</spring-framework.version>`；最终六个 fat jar 均为 `spring-core-5.3.39.jar` |
| 3 | 关注 | JDK25 两个 POM 的 `<jvmArgs>` 是 `maven-compiler-plugin:3.13.0` 的未知参数，`--add-opens` / `--enable-native-access` 被静默丢弃 | 删除 compiler plugin 的 `fork` + `jvmArgs`；只保留显式 Lombok `annotationProcessorPaths` + 1.18.48 + `release=21`；文档同步修正 |
| 4 | 关注 | backend-jdk25 `ruoyi-admin/pom.xml` 残留 39 行 ASM 9.11.1 / `spring-boot-loader-tools` 覆盖，是 major 69 时期的遗留 | 删除该块，三个 backend 分支插件配置对齐 |
| 5 | 关注 | api `_java.yml` 的 `jdk-version` 入参未被安装步骤使用，`jdk-distribution` 入参从未生效 | 安装命令与 Temurin tarball URL 改为读取 `inputs.jdk-version`，新增版本断言，删除无效入参 |
| 6 | 关注 | `ci.yml` / `master.yml` / `release.yml` 等主 CI 未监听 `*-jdkNN` 分支 | 复核为**有意设计**：JDK 分支门禁由 `self-hosted-ci.yml` 承担，合并到 V3/master 后再走主 CI；已在 `01-migration-decisions.md` 明确记录，不追加重复重型 CI |
| 7 | 细节 | backend-jdk21 / api-jdk21 POM 头注释仍写「JDK 17 迁移说明（…jdk17）」 | 改为对应 JDK21 分支说明 |
| 8 | 细节 | api 侧 `pathmatch: ant_path_matcher` 迁移前已存在，文档误写为两侧本次新增 | `01-migration-decisions.md` 已更正为「api 侧仅补 `main:` 块」 |
| 9 | 细节 | 六个分支内的 `docs/jdk-migration-README.md` 是生成式临时文档，api 侧还错误声称 Spring 5.3.39；另有 jdk17-only `08-jdk17-migration-verify.md` | 六个分支文档与 jdk17-only 文档均已直接删除；含硬编码 `jcmd` 结论的 `_gen_branch_docs.py` 已删除；权威文档只保留在 `car-monit-backend-new/docs/jdk-migration/` |
| 10 | 关注 | `jcmd VM.version`、`YAML_TOTAL=54`、50 行 E2E 报告（49 条结果行 + 1 条汇总）、26/26 冒烟、物理删除等结论当时缺少持久化输出，审查人无法复核 | 新增/保留 `jdk17-e2e-record.txt`、`evidence-yaml-validation.txt`、`evidence-xml-validation.txt`、`evidence-jdk25-jcmd.txt`、`evidence-jdk25-cache-miss.txt`、`evidence-build-artifacts.txt`、`*-recheck-smoke.stdout.log` 等；最终 jar 运行时重新采集真实 `jcmd` 输出 |
| 11 | 关注 | 首审 B 指出 `jcmd VM.version` 只存在于生成器硬编码字符串，不是命令输出 | 在最终 JDK25 服务运行时对 api pid `20148`、backend pid `35044` 实际执行并落盘 `evidence-jdk25-jcmd.txt` |
| 12 | 最终重建新增 | 第一次整改后 final 重建在三个 api 分支离线失败：`spring-test:jar:5.3.39 (compile)` 未下载 | 定位实际本地仓库 `D:\work\apache-maven\repository`；用 `maven-dependency-plugin:3.6.1:get` 从可达 Aliyun 镜像补取（`spring-test-fetch.log`）；同时把三个 `pro-base-common/pom.xml` 的 `spring-boot-starter-test` 改为 `<scope>test</scope>`，消除根因 |
| 13 | 最终重建新增 | `spring-boot-starter-test` 的 compile scope 会把测试库带入生产依赖/fat jar 解析 | 最终 api fat jar 不再含 JUnit / Mockito / spring-test / AssertJ；剩余 `hamcrest`、`json-path`、`json-smart` 作为上游 POM compile-scope 传递依赖显式记录，另列开放项 |
| 14 | 独立复验 | `jdk17-e2e-record.txt` 被文档误称为「50 条结果行」；`evidence-jdk25-runtime.txt` 残留一条硬编码 `jcmd` 注释 | 汇总行改为 `RESULT_LINES=49 REPORT_LINES=50`；文档统一改为「50 行报告（49 条结果行 + 1 条汇总）」；删除硬编码注释，真实 `jcmd` 输出只保留在 `evidence-jdk25-jcmd.txt` |
| 15 | 独立复验 | 2026-11-12 当前 infra 服务已停止，无法重新查询 MySQL 清理计数；原文档把验证时状态写成当前状态 | 新增 `evidence-current-runtime-state.txt`；README / 02 / 03 / 04 明确区分「验证时 live MySQL 结论」与「当前只读复核状态」，未重启服务强行复询 |

## 3. 整改后的重建与实机复验

| 项 | 结果 | 证据 |
| --- | --- | --- |
| 六侧离线 clean 构建 | 全部 `BUILD SUCCESS` | `jdk{17,21,25}-{api,backend}-build-final2.log` |
| class major | `61 / 65 / 65` | `evidence-build-artifacts.txt`、`evidence-final-gate.txt` |
| Spring core | 六侧均 `spring-core-5.3.39.jar` | 同上 |
| 生产测试库 | api fat jar 无 JUnit / Mockito / spring-test / AssertJ | 同上 + `api-dependency-tree*.log` |
| 最终 jar 实机冒烟 | JDK17/21/25 各 `checks=26 fails=0` | `jdk{17,21,25}-recheck-smoke.stdout.log` |
| JDK25 运行时 | `OpenJDK 25.0.4.1+1-LTS`（两个进程） | `evidence-jdk25-jcmd.txt` |
| backend→API 实链 | 强制 cache miss 后两条 `X-Data-Source=API` | `evidence-jdk25-cache-miss.txt` |
| 静态闸门 | `FINAL_GATE_CHECKS=146 FINAL_GATE_FAILS=0 FINAL_GATE_VERDICT=PASS` | `evidence-final-gate.txt` |
| 清理（验证时） | `remaining_e2e=0`、`total_users=8`、app Java `0`、infra 单例 | `evidence-final-gate.txt` |
| 当前运行时（2026-11-12） | app Java `0`、infra 监听端口 `0`、无重复实例；DB 清理为验证时历史结论 | `evidence-current-runtime-state.txt` |
| 远端红线 | 六分支无 upstream、无提交、无 staged/untracked；未 push、未触发 CI | `git status` / `git rev-parse @{u}` + 上述闸门 |

> `evidence-final-gate.txt` 是执行者在整改后做的只读自检，**不代替独立复验会话的结论**。

## 4. 仍保留为「关注 / 技术债」的开放项

1. JDK25 是「JDK 25 运行时 + Java 21 字节码」；若业务定义要求 Java 25 字节码，
   必须另立 Spring Boot 3.x / Jakarta 迁移项目。
2. `spring.main.allow-circular-references` / `allow-bean-definition-overriding` 是兼容性开关，
   长期应排期消除循环依赖与 Bean 覆盖。
3. `/system/user/list` 登录即可访问，属于迁移前既有最小权限债务，建议单独补 `@PreAuthorize`。
4. api fat jar 中 `hamcrest` / `json-path` / `json-smart` 来自 Boot starter-test POM 的
   compile-scope 传递依赖，是否用 exclusion 清理属于独立依赖治理项。
5. 三个 backend `ruoyi-admin/pom.xml` 的 `<fork>true</fork>` 是 `spring-boot-maven-plugin`
   devtools 基线配置，与 compiler plugin 的 `fork`/`jvmArgs` workaround 无关；复验已确认。
6. `jdk17-e2e-record.txt` 是 50 行报告（49 条结果行 + 1 条汇总），不是 50 条结果行；
   文档与汇总行已修正。
7. 2026-11-12 当前 infra 服务已停止，DB 清理计数为验证时历史结论；未重启服务强行复询。
8. 六个分支改动尚未本地 commit；review 完成后的提交、push 顺序需由用户另行决定。

## 5. 独立复验结论

两轮独立复验均已完成并回填：

```text
RECHECK_SESSION=agent-97686c28-a21c-4644-b3da-d0b6504d7c65 / agent-dc579805-288c-416d-8446-2ac5bbc41939
RECHECK_VERDICT=PASS_WITH_CONCERNS / PASS_WITH_CONCERNS
BLOCKERS_REMAINING=0
OPEN_CONCERNS=5 non-blocking items (devtools fork baseline, Boot starter-test compile transitives,
               50-line E2E report wording, evidence-jdk25-runtime hardcoded comment removed,
               current infra stopped / DB counts historical)
NO_PUSH_NO_CI_CONFIRMED=YES (local evidence only; GitHub remote run history cannot be queried offline)
```

复验 A 独立核对了 30 个 POM 解析、版本矩阵、starter-test scope、6 个 fat jar 的 class major /
Spring core / 大小、6 个 final2 构建日志、54 个 workflow YAML、6 个 `setup-java` 钉版本、
git 无 upstream / 无提交 / 无 staged/untracked，并交叉验证了 `evidence-final-gate.txt` 的
POM / jar / CI / git 结论。复验 B 独立核对了文档无过时声明、无明文口令、配置兼容开关、
viewer `/system/user/list` 为迁移前既有设计、JDK25 `jcmd` 与强制 cache miss 为真实持久化输出、
三套 26/26 冒烟、14 个 E2E 账号物理删除记录、分支文档清理以及 V3 文档不重复维护的说明。

**最终判定**：首审 `BLOCKED` 已关闭，两轮复验均无阻断项，迁移正确性审查完成。
所有非阻断关注项已在本文件与 `04-review-checklist.md` 中记录。
按红线要求，**仍未 push、仍未触发 GitHub CI、仍未创建本地提交**；
是否进入 commit / push 阶段由用户后续决定。
