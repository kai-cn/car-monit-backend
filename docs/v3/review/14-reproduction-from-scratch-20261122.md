<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# 从头复现步骤（2026-11-22 最终版）

## 1. 前置条件

- Windows 主机 + WSL `openEuler-24.03-LTS-SP4`，Docker daemon 可用。
- WSL 中已有本地容器：`mysql_wsl`（宿主端口 3307，库 `carmonitdb`，root/root）、`redis_wsl`（6379）、`opengauss`（5432）。
- JDK 8/11/17/21/25：WSL 默认 JDK8，Mandrel 17/21/25 位于 `/home/dev/tools/`。
- Python 3.10+，`pyyaml`；GitHub API token 从本地 `.gh_token_cache` 读取，不落盘、不回显。
- Git 凭证助手使用 `git-credential-ghcached.py`，避免 GitHub 账号选择弹框。

## 2. 云端 JUnit 全接口与压测复现

1. 准备 harness：
   - 将 `scripts/v3/ops/junit/generate_junit_suite.py`、`compare_load.py` 和端点清单放入两仓库 `master` 工作树。
   - 提交 `.github/workflows/java-junit-load-cloud.yml`（`target_ref/app/jdk/endpoints/load_threads/load_seconds/label` 输入）。
2. 派发矩阵：
   ```bash
   python D:\work\runtime-logs\dispatch-java-junit-matrix.py
   python D:\work\runtime-logs\collect-java-junit-runs.py
   ```
3. 结果应为 `java-junit-results.json` 16 条全部 `success`（backend 7、api 9）。
4. 关键口径：
   - Boot4 JVM jar 构建用 `-Dspring-boot.aot.skip=true` 跳过 process-aot。
   - JVM 启动需 `allow-circular-references`、`lazy-initialization`、Kafka 自动配置排除。
   - 全接口清单含鉴权/参数化端点，JUnit 只断言 HTTP 可达，业务状态码记录为证据。

## 3. Java25 Boot4 跨语言全量对拍复现

1. 准备 harness：
   - 两仓库 `master` 提交 `crosslang-full-parity-cloud.yml`。
   - baseline artifact 携带 `junit.jar`，候选直接复用，避免 Maven Central 429。
2. 派发与收集：
   ```bash
   python D:\work\runtime-logs\dispatch-crosslang-full.py
   python D:\work\runtime-logs\collect-crosslang-full.py
   python D:\work\runtime-logs\collect-crosslang-evidence.py
   ```
3. 结果：
   - `crosslang-full-results.json`：backend/api 两条 workflow `success`。
   - `crosslang-evidence.json` / `.md`：每个候选的 `status_match/exact/semantic/nondet/fails` 与 `rps/p95` 对比。
   - workflow job success 与接口对齐 DIFF/fails 是两回事，后者必须如实保留。

## 4. 本机重新编译打包复现

1. 从远端 ref 创建 16 个 detached worktree：
   ```bash
   bash D:\work\runtime-logs\wsl-local-package-all.sh
   ```
2. 每个分支使用匹配 JDK 执行 `mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true clean package`。
3. backend master 若 D 盘满导致 repackage I/O 错误，改用：
   ```bash
   bash D:\work\runtime-logs\wsl-rebuild-backend-master-ext4.sh
   ```
4. 汇总结果：
   - `local-package-evidence/local-package-results.json`：16/16 `rc=0`。

## 5. WSL 本机服务级复测

1. 启动容器：
   ```bash
   bash D:\work\runtime-logs\wsl-restore-docker.sh
   ```
2. 启动服务并跑套件：
   ```bash
   bash D:\work\runtime-logs\run-wsl-retest4.ps1   # Windows 侧启动 WSL 脚本
   bash D:\work\runtime-logs\wsl-local-service-retest4.sh
   ```
3. 证据：
   - `wsl-retest-evidence/junit-contract.json`：302 端点。
   - `wsl-retest-evidence/junit-load.json`：145354 请求、145354 ok、0 errors。
   - 本地复测使用 Boot2 backend master jar + MySQL 3307 + Redis 6379。

## 6. 生产级注释复现

1. 批量补文件头：
   ```bash
   python D:\work\runtime-logs\apply-production-headers.py
   python D:\work\runtime-logs\finalize-production-headers.py
   python D:\work\runtime-logs\patch-production-function-docs.py
   ```
2. 校验：
   ```bash
   python D:\work\runtime-logs\verify-production-headers.py
   ```
3. 当前结果：
   - `MISSING_HEADERS 0`
   - `PYTHON_SYNTAX_ERRORS 0`
   - `bad-selfhosted.yml` 是故意保留的负向审计样本，YAML 解析失败属于预期。
4. 文件头必须包含：`@description`、`@author`、`@date`、`@usage`、`@dependencies`。
5. Python 关键函数必须有中文 docstring；生成 Java 套件带 Javadoc；Shell 严格模式需解释原因。

## 7. 文档与证据索引

- 工作记忆：`D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-22.md`
- 任务清单：`D:\work\runtime-logs\公开仓库安全加固-任务清单.md`
- 脚本与证据索引：`D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md`
- 最终报告：`D:\work\runtime-logs\final-java-junit-crosslang-20261122.md`
- 会话交接：`D:\work\runtime-logs\SESSION-HANDOFF.md`

## 8. 仍待用户处理

- F1：在外部系统轮换真实凭据。
- F2：轮换后更新两仓库 GitHub Secrets。
- 本仓库和文档中只保存测试值/占位值，不保存生产凭据。
