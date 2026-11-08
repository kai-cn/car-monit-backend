# CI/CD 方案矩阵与实施进度

> 本文是 GitHub Actions 流水线的方案与进度记录。事实核查时间为 2026-11-08。
> 机器重启后从本文「实施进度」一节恢复即可。

## 1. 事实核查（先摸清，不假设）

### 1.1 仓库与远端

| 项 | 结果 | 证据 |
|---|---|---|
| remote | `https://github.com/kai-cn/car-monit-backend.git` | `git remote -v` |
| 当前分支 | `master`，本地 HEAD 与 `origin/master` 同为 `ca59188` | `git rev-parse HEAD` / `origin/master` |
| 远端分支 | 仅 `main`、`master`、`car-monit-cpp-local`、`qoder/car-monit-cpp` | `git ls-remote --heads origin` |
| 仓库可见性 | **私有**（匿名调 `api.github.com/repos/kai-cn/car-monit-backend` 返回 404） | WebFetch |
| Actions 历史 | **无法核实**：私有仓库 + 本机无 `gh`/token | `gh auth status` 不存在 |

### 1.2 迁移子项目的仓库归属（关键结论）

`car-monit-go-V2`、`car-monit-rust-V2` **不是子目录，而是同一仓库的另外两个工作树（独立 `.git`）**，
各自检出于独立分支，工作树里是整仓快照（同时含 `ruoyi-*`、`car-monit-py`、`car-monit-go`、`car-monit-rust`）。

| 目录 | 分支 | remote | 该分支是否在远端 | 工作区 |
|---|---|---|---|---|
| `car-monit-go-V2` | `car-monit-go-V2` | 同上 | **否** | clean |
| `car-monit-rust-V2` | `car-monit-rust-V2` | 同上 | **否** | clean |
| `car-monit-backend-new-v2`（任务描述里的名字） | — | — | **目录不存在**，实际指 `car-monit-go-V2` 工作树 | — |
| `car-monit-rust`（当前 master 工作树内） | — | — | 普通子目录 | — |

**推论**：两个 V2 分支从未 push，因此它们目录里的 workflow 文件**从未被执行过**（GitHub 只对远端存在的工作流触发）。

### 1.3 现有 workflow 清单与是否真在跑

| 文件 | 所在分支 | 状态 |
|---|---|---|
| `.github/workflows/car-monit-rust.yml` | `master`（已随 `099ef4b` 提交） | 文件在远端 master 上，理论可触发；**实际运行结果无法核实**（无 token） |
| `car-monit-go-V2/.github/workflows/car-monit-go-ci.yml` | 仅本地 `car-monit-go-V2` | **从未运行**（分支未 push） |
| `car-monit-go-V2/.github/workflows/car-monit-rust.yml` | 仅本地 `car-monit-go-V2` | 陈旧副本（无 release-only 步骤），**从未运行** |
| `car-monit-rust-V2/.github/workflows/car-monit-rust.yml` | 仅本地 `car-monit-rust-V2` | 最新版（含 `cargo test --release --test release_throwable`），**从未运行** |

### 1.4 各语言构建现状

| 语言 | 位置 | 构建事实 | 测试事实 |
|---|---|---|---|
| Java | 根 `pom.xml` + `ruoyi-*` 6 模块 | `packaging=pom`，Spring Boot `2.5.15`，`java.version=1.8` | **没有任何 `src/test`**，无单测可跑 |
| Go | `car-monit-go` | `go 1.24`，`cmd/server`、`cmd/migrate` | 有 `go test` 用例（含 parity 脚本） |
| Rust | `car-monit-rust` | crate，`edition 2021`，`rust-toolchain.toml` 锁 `1.90.0`，161 个 `.rs` | master **无 `tests/`**；`tests/release_throwable.rs` 只存在于 `car-monit-rust-V2` 分支 |
| Python | `car-monit-py` | `setuptools` 后端，`requires-python >=3.12`，`requirements.txt` 全量锁版本 | 89 个测试文件；`integration` 标记用例需真实 MySQL/Redis（默认 `127.0.0.1:3307/6379`） |
| C++ | `car-monit-cpp` | **只有 `docs/` 和两份 md，无任何源码，全仓无 `CMakeLists.txt`** | 无可构建、无可测试 |
| Kotlin | `car-monit-kotlin` | 只有一份迁移 prompt md | 无 |
| C# | `car-monit-csharp` | 只有一份迁移 prompt md | 无 |

JDK：扫描全仓所有 `pom.xml`，**只有 `java.version=1.8` 一个值**；未发现 21 / 25 的任何引用（唯一出现 "Java 25" 的文本是 `MAPPING_QUARTZ.md` 里「Java 25 个文件」的计数）。

## 2. 流水线方案矩阵

统一放在根 `.github/workflows/`，**按路径分诊**；V2 分支只要 cherry-pick 同一套 YAML 即可复用（相对路径一致：`car-monit-go/`、`car-monit-rust/`、`car-monit-py/`）。

### 2.1 PR 流水线 `ci.yml`（`pull_request`）

| 语言 | 触发路径 | 检查项 | 目标时长 |
|---|---|---|---|
| 变更检测 | 全仓 | `dorny/paths-filter` 决定哪些 job 运行 | 秒级 |
| Java | `pom.xml`、`ruoyi-*/**` | `mvn -B compile` → `mvn -B test`（当前无测试源码，等价于编译门禁） | 2-4 min（缓存后） |
| Go | `car-monit-go/**` | `gofmt -l`、`go mod tidy` 无 diff、`go vet`、`go test`、`golangci-lint` | 2-4 min |
| Rust | `car-monit-rust/**` | `cargo fmt --check`（迁移期非阻塞）、`clippy -D warnings`（非阻塞）、`cargo test --lib`、**`cargo test --release --test release_throwable`（阻塞）** | 3-6 min |
| Python | `car-monit-py/**` | `compileall`（语法门禁）、`pytest -m "not integration"`（不含外部依赖） | 2-3 min |
| C++ / Kotlin / C# | — | **不建 job**：无源码、无 `CMakeLists.txt`/`gradle`/`csproj`，建了也只能空跑 | — |

### 2.2 主分支流水线（同一 `ci.yml`，`push` 到 `master`）

> 默认分支已确认为 `master`；`main` 不再作为主构建目标，`ci.yml` 的 PR 基线与 push 触发都只认 `master`。

不分诊，四种语言全跑，并在 PR 检查之上追加：

| 语言 | 追加动作 | 产物 |
|---|---|---|
| Java | `mvn -B test` + `mvn -B -DskipTests package` | `ruoyi-admin/target/*.jar` |
| Go | `CGO_ENABLED=0 GOOS=linux go build ./cmd/server ./cmd/migrate` | 两个 Linux 二进制 |
| Rust | `cargo build --release` | `car-monit-rust` 二进制 |
| Python | `pytest --cov=app --cov-report=xml` + `python -m build` | `*.whl`、`*.tar.gz`、`coverage.xml` |

覆盖率：Python 用 `pytest-cov`；Java 现状无测试源码，**不接 JaCoCo**（接了只会产出 0%），在 job summary 里显式写明；Rust/Go 先不做行覆盖率（引入 `cargo-llvm-cov` 会显著拉长时长，等测试量上来再加）。

### 2.3 发布流水线 `release.yml`（`push` tag `v*`）

四个 build job 并行产出 jar / Go 二进制 / Rust 二进制 / Python wheel+sdists，`release` job 汇总后创建 GitHub Release 并挂载全部产物。
镜像：仅 Go 有 `Dockerfile`（且只存在于 `car-monit-go-V2` 分支）；Java/Rust/Python 无 Dockerfile。因此镜像 job 用 `if: vars.IMAGE_REGISTRY != ''` 显式关闭，**不写任何真实 registry 地址**。

### 2.4 部署流水线 `deploy.yml`

只做 `workflow_dispatch` 占位：校验 `vars.IMAGE_REGISTRY` / `vars.DEPLOY_TARGET` 是否配置，未配置即以明确错误信息退出，真实部署步骤全部注释留缺口。

### 2.5 集成测试

`integration` job 用 GitHub `services` 起 MySQL/Redis（端口与仓库默认配置对齐 `3307`/`6379`），ES/Kafka 作为可选服务，**不指向任何固定 IP**。
当前**仅 `workflow_dispatch` 且勾选 `run_integration` 时执行**，避免一个尚未验证的重活把主分支门禁长期打红；验证通过后再改成主分支门禁。

## 3. 需要用户确认的未知项（阻塞部署与镜像，不阻塞 PR/主分支）

1. **镜像推送目标**：GHCR 还是私有 registry？命名空间与镜像名（如 `ghcr.io/kai-cn/car-monit-<lang>`）？
2. **部署目标形态**：K8s / 单机 systemd / 只出产物不部署？
3. **默认分支**：已确认 `master`（见 §2.2）。`main` 保留在远端但不再作为主构建目标。
4. **JDK 21 / 25 的归属**：本仓库只查到 `1.8`。如果 21/25 属于未入库的子项目或 `car-monit-api`，请指明，否则 Java 流水线固定用 Temurin 8。
5. **V2 分支是否推到远端**：不 push 就永远不会有该分支的 CI。是否需要 push（本任务约定不 push，需你确认后另行处理）？
6. **统一 workflow 是否同步到 `car-monit-go-V2` / `car-monit-rust-V2` 分支**（否则分支上仍是旧文件）。
7. 私有仓库 Actions 配额 / 是否自托管 runner（影响带 services 的集成测试可用性）。

## 4. 已知缺口与风险（如实记录，不靠改业务代码变绿）

- Java：无单测、无 checkstyle/spotless 配置 → PR 只有编译门禁，静态检查为 0。
- Python：无 ruff/flake8/mypy 配置 → 静态检查只有 `compileall` 语法门禁，等确定规则集后再接。
- Rust：`fmt`/`clippy` 现存告警未清零，沿用**非阻塞**（与仓库既有 workflow 一致），仅提示。
- Rust `release-only`：master 分支缺 `tests/release_throwable.rs`，该步骤在主分支降级为 warning 并写入 job summary；**在迁移分支（`car-monit-rust-V2` 等）缺文件直接失败**，防止 `#[cfg(not(debug_assertions))]` 用例再次逃逸。
- C++ / Kotlin / C#：无源码，无法建 CMake/MSVC / Gradle / dotnet 流水线；等有 `CMakeLists.txt` 等构建入口再接。
- 全部 YAML **已写好但未在 GitHub 上实跑**（本机不做长构建，仓库为私有且无 token），首次运行结论需在推送后回填。
- `go mod tidy` 校验失败可能源于真实依赖漂移，不是 CI 配置问题。

## 5. 实施进度

| 阶段 | 状态 | 文件 |
|---|---|---|
| 事实核查 | 完成 | 本文 §1 |
| 方案矩阵 | 完成 | 本文 §2 |
| PR 流水线 | YAML 完成，未实跑 | `.github/workflows/ci.yml` |
| 主分支流水线 | YAML 完成，未实跑 | `.github/workflows/ci.yml` |
| tag 发布 | YAML 完成，未实跑 | `.github/workflows/release.yml` |
| 部署占位 | YAML 完成，未实跑 | `.github/workflows/deploy.yml` |
| YAML 语法校验 | 完成（PyYAML `safe_load` 通过） | 2026-11-08 |

旧的 `.github/workflows/car-monit-rust.yml` 已删除，其 `parity` job 原样迁入 `ci.yml` 的 `rust-parity`（仅手动触发）。

> 恢复约定：重启后先看本节状态列；未完成项按 §2 表格实现，完成后把状态改为「完成」并补一行提交哈希。
