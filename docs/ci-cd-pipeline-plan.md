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

`car-monit-go-V2`、`car-monit-rust-V2` **不是子目录，而是同一仓库的 git worktree**（目录里的 `.git` 是工作树指针文件，`git worktree list` 可一次看全），
工作树里是整仓快照（同时含 `ruoyi-*`、`car-monit-py`、`car-monit-go`、`car-monit-rust`）。

| 工作树 | 分支 | 该分支是否在远端（推送前 → 推送后） | 工作区 |
|---|---|---|---|
| `car-monit-backend-new`（主工作树） | `master` | 是 | 有未跟踪调研文件 |
| `car-monit-backend-new/car-monit-go-V2` | `car-monit-go-V2` | 否 → **是（`e2d91f6`）** | clean |
| `car-monit-backend-new/car-monit-rust-V2` | `car-monit-rust-V2` | 否 → **是（`bf537c8`）** | clean |
| `car-monit-backend-new-V2` | `car-monit-py-V2` | 否 → **是（`8026faa`）** | clean |
| `car-monit-cpp-V2` | `car-monit-cpp-local` | 是（旧 `b4e8c47`）→ **快进到 `5d0e7df`** | clean |
| `car-monit-backend-java-V3` | `car-monit-backend-java-V3` | 否（本次推送范围外） | — |

**推论**：推送前这些迁移分支的 workflow 文件**从未被执行过**（GitHub 只对远端存在的分支触发）；推送后是否真的触发暂无法核实（见 §6）。

### 1.3 现有 workflow 清单与是否真在跑

| 文件 | 所在分支 | 状态 |
|---|---|---|
| `.github/workflows/car-monit-rust.yml` | `master` | 已被统一流水线取代并删除（`d081976`） |
| `.github/workflows/{ci,cd,deploy,release,_cpp}.yml` | `master` | 新增，**本地未 push**；master 按要求不推送 |
| `car-monit-go-V2/.github/workflows/car-monit-go-ci.yml` 与陈旧 `car-monit-rust.yml` | `car-monit-go-V2` | 已删除，替换为统一 5 个 YAML（`617a4c9`，已推送） |
| `car-monit-rust-V2/.github/workflows/car-monit-rust.yml` | `car-monit-rust-V2` | 已删除，release-only 用例并入 `ci.yml`（`9bfa622`，已推送） |
| `car-monit-py-V2` 的 `car-monit-py.yml` 与陈旧 `car-monit-rust.yml` | `car-monit-py-V2` | 已删除，替换为统一 5 个 YAML（`bc04688`，已推送） |
| `car-monit-cpp-local` 工作树 | `car-monit-cpp-local` | 原本没有 workflow，已新增统一 5 个 YAML（含 `_cpp.yml`，`bb4f8ee`，已推送） |

### 1.4 各语言构建现状

| 语言 | 位置 | 构建事实 | 测试事实 |
|---|---|---|---|
| Java | 根 `pom.xml` + `ruoyi-*` 6 模块 | `packaging=pom`，Spring Boot `2.5.15`，`java.version=1.8` | **没有任何 `src/test`**，无单测可跑 |
| Go | `car-monit-go` | `go 1.24`，`cmd/server`、`cmd/migrate` | 有 `go test` 用例（含 parity 脚本） |
| Rust | `car-monit-rust` | crate，`edition 2021`，`rust-toolchain.toml` 锁 `1.90.0`，161 个 `.rs` | master **无 `tests/`**；`tests/release_throwable.rs` 只存在于 `car-monit-rust-V2` 分支 |
| Python | `car-monit-py` | `setuptools` 后端，`requires-python >=3.12`，`requirements.txt` 全量锁版本 | 89 个测试文件；`integration` 标记用例需真实 MySQL/Redis（默认 `127.0.0.1:3307/6379`） |
| C++ | `car-monit-cpp` | **master 上只有 `docs/` 和两份 md，无源码**；但 `car-monit-cpp-local` 分支有完整 CMake 工程（`CMakeLists.txt`、`include/`、`src/`、`tests/`、`third_party/`、`vcpkg_installed/`） | master 无可测；分支的 `tests/` 未在 CI 中跑过 |
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
| C++ / Kotlin / C# | — | master 上**不建 job**：无 `CMakeLists.txt`/`gradle`/`csproj`，建了只能空跑。`car-monit-cpp-local` 分支已有完整 CMake 工程，需在该分支单独接 CMake/MSVC（`windows-latest`），本次未建 | — |

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

### 2.3 发布流水线

| 文件 | 触发 | 产出 |
|---|---|---|
| `release.yml` | tag `v*.*.*` | jar / Go 二进制 / Rust 二进制 / wheel+sdist，创建 GitHub Release |
| `cd.yml` | push `master`、tag `v*.*.*`、手动 | 构建并推 GHCR 镜像：`sha-<短哈希>`、版本号、`latest`（仅 master） |

镜像：`ghcr.io/kai-cn/car-monit-{java,go,rust,py}`，用 `GITHUB_TOKEN` + `packages: write`，不依赖 PAT。C++ 不产镜像（原因见 [cd-ghcr-k8s.md](cd-ghcr-k8s.md) §5）。

### 2.4 部署流水线 `deploy.yml`

`workflow_dispatch`：选择 service / image_tag / environment，前置校验 `vars.K8S_NAMESPACE`、`vars.K8S_DEPLOYMENT`、`vars.K8S_CONTAINER`、`vars.K8S_IMAGE_PULL_SECRET` 与 `secrets.KUBE_CONFIG`，检查 Deployment 与 imagePullSecret 存在后执行 `kubectl set image` + `kubectl rollout status`。只更新已存在的 Deployment，首次部署需人工 bootstrap（见 [cd-ghcr-k8s.md](cd-ghcr-k8s.md) §4）。

### 2.5 集成测试

`integration` job 用 GitHub `services` 起 MySQL/Redis（端口与仓库默认配置对齐 `3307`/`6379`），ES/Kafka 作为可选服务，**不指向任何固定 IP**。
当前**仅 `workflow_dispatch` 且勾选 `run_integration` 时执行**，避免一个尚未验证的重活把主分支门禁长期打红；验证通过后再改成主分支门禁。

## 3. 需要用户确认的未知项（阻塞部署与镜像，不阻塞 PR/主分支）

1. **镜像推送目标**：已确认 GHCR，`ghcr.io/kai-cn/car-monit-<service>`（见 [cd-ghcr-k8s.md](cd-ghcr-k8s.md)）。
2. **部署目标形态**：已确认 K8s，只更新已存在的 Deployment（见 `deploy.yml`）。
3. **默认分支**：已确认 `master`（见 §2.2）。`main` 保留在远端但不再作为主构建目标。
4. **JDK 21 / 25 的归属**：本仓库只查到 `1.8`。如果 21/25 属于未入库的子项目或 `car-monit-api`，请指明，否则 Java 流水线固定用 Temurin 8。
5. **V2 分支是否推到远端**：已执行，见 §6（`car-monit-go-V2`、`car-monit-rust-V2`、`car-monit-py-V2`、`car-monit-cpp-local`）。
6. **统一 workflow 是否同步到迁移分支**：已执行，见 §6；四条分支都换成了统一 YAML，旧的分支专属 workflow 已删除。
7. 私有仓库 Actions 配额 / 是否自托管 runner（影响带 services 的集成测试可用性）。

## 4. 已知缺口与风险（如实记录，不靠改业务代码变绿）

- Java：无单测、无 checkstyle/spotless 配置 → PR 只有编译门禁，静态检查为 0。
- Python：无 ruff/flake8/mypy 配置 → 静态检查只有 `compileall` 语法门禁，等确定规则集后再接。
- Rust：`fmt`/`clippy` 现存告警未清零，沿用**非阻塞**（与仓库既有 workflow 一致），仅提示。
- Rust `release-only`：master 分支缺 `tests/release_throwable.rs`，该步骤在主分支降级为 warning 并写入 job summary；**在迁移分支（`car-monit-rust-V2` 等）缺文件直接失败**，防止 `#[cfg(not(debug_assertions))]` 用例再次逃逸。
- C++ / Kotlin / C#：master 无源码，无法建 CMake/MSVC / Gradle / dotnet 流水线；`car-monit-cpp-local` 分支有 CMake 工程，已接 `_cpp.yml`（windows-latest），但**未实跑**。
- CD 覆盖 Java / Go / Rust / Python 四个镜像；**C++ 不产镜像**（仓库只有 `vcpkg_installed/x64-windows`，Linux 依赖方案未验证）。
- 镜像构建、GHCR 推送、K8s 部署**均未实跑**（本机无 Docker/集群）。
- 全部 YAML **已写好但未在 GitHub 上实跑**（本机不做长构建，仓库为私有且无 token），首次运行结论需在推送后回填。
- `go mod tidy` 校验失败可能源于真实依赖漂移，不是 CI 配置问题。

## 5. 实施进度

| 阶段 | 状态 | 文件 |
|---|---|---|
| 事实核查 | 完成 | 本文 §1 |
| 方案矩阵 | 完成 | 本文 §2 |
| PR 流水线 | YAML 完成，未实跑 | `.github/workflows/ci.yml` |
| 主分支流水线 | YAML 完成，未实跑 | `.github/workflows/ci.yml` |
| C++ 检查 | YAML 完成，未实跑 | `.github/workflows/_cpp.yml` |
| tag 发布 | YAML 完成，未实跑 | `.github/workflows/release.yml` |
| 镜像构建 + GHCR 推送 | YAML 与 4 个 Dockerfile 完成，未实跑 | `.github/workflows/cd.yml`、`docker/java.Dockerfile`、各语言 `Dockerfile` |
| K8s 部署 | YAML 完成，未实跑 | `.github/workflows/deploy.yml`、[cd-ghcr-k8s.md](cd-ghcr-k8s.md) |
| 迁移分支同步 | 完成（4 条分支已推送） | 见 §6 |
| YAML 语法校验 | 完成（PyYAML `safe_load` 通过） | 2026-11-08 |

旧的 `.github/workflows/car-monit-rust.yml` 已删除，其 `parity` job 原样迁入 `ci.yml` 的 `rust-parity`（仅手动触发）。

> 恢复约定：重启后先看本节状态列；未完成项按 §2 表格实现，完成后把状态改为「完成」并补一行提交哈希。

## 6. 分支推送记录（2026-11-08）

推送前先 `git fetch origin --prune` + `git ls-remote --heads origin` 核对；全部**非 force push**，`master` 未推送。

| 分支 | 本地 HEAD | 推送结果 | 远端确认 |
|---|---|---|---|
| `car-monit-go-V2` | `e2d91f6` | 新建远端分支 | `e2d91f6d52a6b024b7b0ee45e2ecf5c33b09fae0` |
| `car-monit-rust-V2` | `bf537c8` | 新建远端分支 | `bf537c8a64faa4c412c34bf420e2dc0605fc51f7` |
| `car-monit-py-V2` | `8026faa` | 新建远端分支 | `8026faa0d5963271ceaa0e5025c4617cd9badcd0` |
| `car-monit-cpp-local` | `5d0e7df` | 快进 `b4e8c47..5d0e7df` | `5d0e7dfb42aed4c25d6c89a1c20edd7d06ca665b` |

未推送 / 未处理：

- `master`：本地比远端多 8 个提交（含本轮 CI/CD 改动），按要求不 push。
- `main`：远端旧分支，不再作为主构建目标，未改动。
- `qoder/car-monit-cpp`：远端与本地同 SHA（`9206daa`），无需推送。
- `car-monit-backend-java-V3`：不在本次四种语言范围，未推送。

### 6.1 统一 workflow 同步（第二轮推送）

| 分支 | 同步提交 | 处理 | 远端确认 |
|---|---|---|---|
| `car-monit-go-V2` | `617a4c9` | 删除 `car-monit-go-ci.yml` + 陈旧 `car-monit-rust.yml`，新增 5 个统一 YAML + 4 语言 Dockerfile | `617a4c95c6ce88c953d114ea2aa516f5eb6ea056` |
| `car-monit-rust-V2` | `9bfa622` | 删除 `car-monit-rust.yml`（release-only 用例并入 `ci.yml`） | `9bfa622005e9e9ea55e54ab5613edc8097e909bc` |
| `car-monit-py-V2` | `bc04688` | 删除 `car-monit-py.yml` + 陈旧 `car-monit-rust.yml` | `bc046886c4c32ee619c5401972465e4b8ce87bb7` |
| `car-monit-cpp-local` | `bb4f8ee` | 原本无 workflow，新增统一 5 个 YAML（含 `_cpp.yml`） | `bb4f8eeb37c17ecc32352f096587af8b4d22159f` |

`car-monit-cpp-local` 工作树里另有他人未提交的 `MySqlClient.hpp/.cpp` 改动与 `.qoder/`，本次没有纳入提交。

**触发验证**：本机没有 `gh`，仓库私有且匿名 API 返回 404，因此四条分支的同步推送都是**已推送，未验证 workflow 是否触发、是否通过**。`master` 及其统一 YAML 仍只在本地，未推送。
