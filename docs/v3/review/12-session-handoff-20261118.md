<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# 12. 会话交接（2026-11-18 起，含 11-20 Java POM 升级收口）

## 11-18 基线
- workflow 全量扫描 `BAD=0`；H9 Go/Python 通过；H8 后续已在 11-20 收官。
- 工作记忆与脚本索引位于 `D:/work/runtime-logs/`。

## 2026-11-20 Java POM 升级收口
- api/backend master 升级到 Spring Boot 2 最终版 2.7.18；全部 Java 分支 POM 依赖以 Boot BOM 为版本基准。
- api 所有 Java 分支完成 Jedis → Lettuce（`spring-boot-starter-data-redis` + LettuceClusterClient）。
- 新增 Java-only workflow `java-upgrade-verify.yml`，避免 Boot2 分支被 Python/DB fixture/native clean 等非 Java job 阻断。
- 16/16 Java 分支云 runner run success，证据 `D:/work/runtime-logs/java-upgrade-runs.json`。
- GitHub 认证改为本地 token 缓存 helper，git credential fill/push 不再弹账号选择框。
- 当日工作记忆：`.workbuddy/memory/2026-11-20.md`。


## 2026-11-21 Native/跨语言重跑
- Boot3/Boot4 10 个 Java 分支 native success；Boot2 无 native profile，N/A。
- crosslang-parity-cloud success；11/11 云任务 success，证据 `native-crosslang-status.json`。
- Mandrel25 + Lombok annotationProcessorPaths + LOG_PATH 修复完成。
- 157 个历史脚本补齐注释，复扫 0 缺失。

## 2026-11-22 生产级注释、复现与证据索引

- 已办：历史脚本与新生成工程代码统一补齐生产级文件头；Python 关键函数补中文 docstring；生成 Java 套件补 Javadoc。
- 校验：`MISSING_HEADERS 0`、`PYTHON_SYNTAX_ERRORS 0`；`bad-selfhosted.yml` 为负向审计样本，YAML 解析失败是预期。
- 从头复现：`D:\work\runtime-logs\从头复现步骤-20261122.md`，覆盖云端 JUnit、跨语言、本机打包、WSL 服务复测、注释校验。
- 测试与压测证据：
  - `java-junit-results.json`：16/16 cloud success。
  - `crosslang-full-results.json` / `crosslang-evidence.json`：跨语言 workflow 与真实对齐差异。
  - `local-package-evidence/local-package-results.json`：本机 16/16 打包成功。
  - `wsl-retest-evidence/junit-contract.json`、`junit-load.json`：本机 302/302、145354 请求、0 errors。
- 待办：F1/F2 用户侧真实凭据外部轮换与 Secrets 更新。


## 2026-11-22 生产级注释、复现与证据索引

- 已办：历史脚本与新生成工程代码统一补齐生产级文件头；Python 关键函数补中文 docstring；生成 Java 套件补 Javadoc。
- 校验：`MISSING_HEADERS 0`、`PYTHON_SYNTAX_ERRORS 0`；`bad-selfhosted.yml` 为负向审计样本，YAML 解析失败是预期。
- 从头复现：`D:\work\runtime-logs\从头复现步骤-20261122.md`，覆盖云端 JUnit、跨语言、本机打包、WSL 服务复测、注释校验。
- 测试与压测证据：
  - `java-junit-results.json`：16/16 cloud success。
  - `crosslang-full-results.json` / `crosslang-evidence.json`：跨语言 workflow 与真实对齐差异。
  - `local-package-evidence/local-package-results.json`：本机 16/16 打包成功。
  - `wsl-retest-evidence/junit-contract.json`、`junit-load.json`：本机 302/302、145354 请求、0 errors。
- 待办：F1/F2 用户侧真实凭据外部轮换与 Secrets 更新。

