# JDK 17 / 21 / 25 迁移总览（car-monit backend + api）

> 记录日期：2026-11-11；独立复验完成：2026-11-12
> 范围：6 个本地工作树/分支，backend（MySQL 8）与 api（openGauss/GaussDB）两侧同步升级。
> 状态：**独立复验通过（PASS_WITH_CONCERNS，无阻断项）；编译、实机验证与整改全部完成；未 push、未触发 GitHub CI。**

## 1. 交付范围

| 侧 | 分支 / 工作树 | 构建 JDK | 字节码基线 | class major |
| --- | --- | --- | --- | --- |
| backend | `car-monit-backend-jdk17` | Temurin 17.0.21 | Java 17 | 61 |
| backend | `car-monit-backend-jdk21` | Temurin 21.0.12.1 | Java 21 | 65 |
| backend | `car-monit-backend-jdk25` | **Temurin 25.0.4.1** | Java 21 | 65 |
| api | `car-monit-api-jdk17` | Temurin 17.0.21 | Java 17 | 61 |
| api | `car-monit-api-jdk21` | Temurin 21.0.12.1 | Java 21 | 65 |
| api | `car-monit-api-jdk25` | **Temurin 25.0.4.1** | Java 21 | 65 |

**关键说明**：JDK25 分支是「JDK 25 工具链 + 运行时，Java 21 字节码」，不是 Java 25 字节码。
原因见 [01-migration-decisions.md](01-migration-decisions.md#4-jdk25-的上限实测与决策)。

## 2. 文档索引

| 文档 | 内容 |
| --- | --- |
| [01-migration-decisions.md](01-migration-decisions.md) | 架构决策、POM/源码改动清单、Boot 2.7 兼容开关、CI 工具链、JDK25 字节码上限、最终依赖范围整改 |
| [02-build-evidence.md](02-build-evidence.md) | 最终 `*-build-final2.log` 六侧构建证据、class major、fat jar、Spring 版本、失败案例与修复、54 个 workflow YAML 校验 |
| [03-real-machine-validation.md](03-real-machine-validation.md) | admin 建号 → 角色化实机验证、backend→API 链路、导出状态机、API 查询、最终 jar 复验与清理记录 |
| [04-review-checklist.md](04-review-checklist.md) | 独立审查清单、判定标准与两轮复验结论 |
| [05-independent-review-record.md](05-independent-review-record.md) | 两轮首审、两轮独立复验、阻断/关注项整改闭环与最终结论 |

证据根目录：`D:\work\runtime-logs`。总闸门记录：
[`evidence-final-gate.txt`](file:///D:/work/runtime-logs/evidence-final-gate.txt)（`FINAL_GATE_CHECKS=146 FINAL_GATE_FAILS=0 FINAL_GATE_VERDICT=PASS`）。
当前运行时状态另见 [`evidence-current-runtime-state.txt`](file:///D:/work/runtime-logs/evidence-current-runtime-state.txt)。

## 3. 结论摘要

- 整改后 6 个分支再次执行 `mvn -o -B -DskipTests clean package`，全部 `BUILD SUCCESS`，
  日志为 `jdk{17,21,25}-{api,backend}-build-final2.log`；产物 class major 为 `61/65/65`。
- 6 个 fat jar 内均为 `spring-core-5.3.39.jar`；api 生产 fat jar 不再包含 JUnit / Mockito /
  spring-test / AssertJ；`hamcrest`、`json-path`、`json-smart` 作为 Boot starter-test POM 的
  compile-scope 传递依赖保留并已在证据矩阵中显式记录，未隐藏。
- 54 个 GitHub Actions workflow YAML 全部通过 js-yaml 解析，分支触发与各自 JDK 版本一致；
  `self-hosted-ci.yml` 已按分支固定 JDK 并加版本断言。
- 用最终 jar 重跑 JDK17 / JDK21 / JDK25 实机冒烟，各 `checks=26 fails=0`。
- JDK25 运行时由落盘的 `jcmd VM.version` 证实为 `OpenJDK 25.0.4.1+1-LTS`，且强制避开缓存后
  `X-Data-Source=API`，证明 Spring 5.3.39 在 Java 25 运行时可正常完成组件扫描与 HTTP 调用链。
- 两轮验证共 14 个 E2E 测试账号已从 MySQL `carmonitdb.sys_user` **物理删除**；验证时复核
  `remaining_e2e=0`、`total_users=8`。RuoYi 的 REST 删除只是软删，不能直接视为清理完成。
- 验证结束时 app Java 进程为 0，MySQL 3307 / Redis 6379 / ES 9200 / Kafka 9092 / openGauss 15432
  各一个实例。2026-11-12 独立复验时再次只读复核：当前 app Java 与 infra 监听端口均为 0，
  无重复实例；E2E 物理删除结果是验证时通过 live MySQL 取得的历史结论，当前 MySQL 已停止，
  未重启服务强行复询，见 `evidence-current-runtime-state.txt`。
- 6 个 JDK 分支当前均无 upstream、无本地提交、无 staged/untracked 文件；**没有 push，也没有触发 GitHub CI**。
- 两轮独立复验结论均为 `PASS_WITH_CONCERNS`、**无阻断项**；所有非阻断关注项已在 05 中记录。

## 4. 复现（口令由环境注入，不落盘）

```bash
# 以 JDK17 为例；21/25 只需替换 JAVA_HOME、工作树路径与 java 可执行文件
export JAVA_HOME="D:/jdk/temurin-17/jdk-17.0.21+9"
export PATH="$JAVA_HOME/bin:$PATH"
export MAVEN_OPTS="-Xmx768m -Dfile.encoding=UTF-8"
cd "D:/work/IdeaProjects/car-monit-backend-jdk17"
mvn -o -B -DskipTests clean package

# 启动（本机最多 1 backend + 1 api）
# backend 9989 / api 9902，均 -Xms512m -Xmx1g；改代码后先停旧 app Java 再启新服务
```

更完整的启动参数与 E2E 步骤见 [03-real-machine-validation.md](03-real-machine-validation.md#2-复现步骤)。

## 5. 约束与红线

- Windows 本机最多一个 backend Java + 一个 api Java；ES/Kafka/Redis/MySQL 各一个实例。
- 不在另一个 data 目录启动第二个 MySQL 8；需要新库用 3307 现有实例。
- 测试数据、构建产物、日志直接删除，不放回收站；凭据/令牌不写入版本库文档。
- **代码 review 完成前不推送远端分支、不触发 GitHub CI**；6 个 JDK 分支当前均无 upstream。

## 6. 相关 V3 文档路径的处理

用户列出的以下目录均已作为参考文档读取，但**没有在 V3 仓库内另写迁移索引**：

- `D:\work\IdeaProjects\car-monit-backend-java-V3\docs`
- `D:\work\IdeaProjects\car-monit-api-java-V3\docs`
- `D:\work\IdeaProjects\car-monit-backend-new\docs`

原因：六个迁移工作树本身已经包含 V3 基线文档副本；再向两个 V3 主工作区追加索引会出现
「同一事实多处维护」，且 backend V3 的 `docs/` 被本地 `.git/info/exclude` 忽略、
api V3 的 `docs/` 不被忽略，会造成跟踪状态不对称。因此本次以
`car-monit-backend-new/docs/jdk-migration/` 作为唯一权威文档目录，V3 既有文档仅作背景参考。
