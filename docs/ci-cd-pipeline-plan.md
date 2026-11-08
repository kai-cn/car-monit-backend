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
- **Go lint 历史债 49 条**（2026-11-08 本机 `golangci-lint v2.1.6` 实测）：errcheck 6、ineffassign 1、staticcheck 12、unused 30。这些是代码问题，不在本轮 CI 修复范围；`golangci-lint` 已改为 `only-new-issues: true`，只拦新增问题，历史债需单独排期清理。

## 4.1 Actions 首次运行失败排查（2026-11-08）

无 `GH_TOKEN`/`GITHUB_TOKEN`，拿不到 run/job 日志，以下结论来自静态审查 + 本机复现。

**确定会失败（已修）**

| 项 | 证据 | 修复 |
|---|---|---|
| Go：`golangci-lint-action@v6` + `golangci-lint v2.1.6` | action v7 README 明确 v7 对应 golangci-lint v2；v6 只覆盖 v1.x | 升到 `@v7` |
| Go：49 条历史 lint 问题 | 本机 `golangci-lint run` 实测 49 issues | `only-new-issues: true`（保留门禁，只拦新增） |
| `changes`：`dorny/paths-filter` 在 push 下需要 push 前的提交 | 该 action 文档：push 走 git diff；默认 `fetch-depth: 1` 时基线 commit 不可达 | `changes` 与 Go job 的 checkout 改 `fetch-depth: 0` |

**本机复现通过（说明不是 CI 配置问题）**

| 项 | 结果 |
|---|---|
| Java `mvn -B -q -DskipTests compile`（JDK 8 / Maven 3.9.9） | 通过 |
| Java `mvn -B -DskipTests package` | 失败，但原因是 Windows 上 `ruoyi-admin.jar` 被本机运行中的 Java 进程占用（`rename` 失败），Linux runner 不受影响；jar 名为 `ruoyi-admin.jar`，与 workflow 的 `ruoyi-admin/target/*.jar` 匹配 |
| Go `go build ./...` / `go vet ./...` / `go test ./...` / `go mod tidy -diff` | 全部通过 |
| Python `pytest -m "not integration"`（3.12 venv） | 全部通过 |
| Rust `cargo test --lib`（本机 1.90.0，与 `rust-toolchain.toml` 一致） | 94 passed / 0 failed |
| `actionlint` 对全部 workflow | 无 schema / 表达式错误 |

> 本机 `gofmt -l` 会报 12 个文件未格式化，但 diff 是整文件换行差异：Windows `core.autocrlf=true` 且仓库无 `.gitattributes`，工作树是 CRLF。Linux checkout 为 LF，该项在 CI 上应通过，因此没有对 Go 代码做格式化改动。

**可能失败（无法在本机验证）**

- cd 的四个镜像构建：本机无 Docker；Docker Hub 在本机网络被阻断（curl SSL 35），无法核对 `maven:3.9-eclipse-temurin-8`、`rust:1.90-bookworm` 等 tag 是否真实存在。
- GHCR 推送权限：`GITHUB_TOKEN` + `packages: write` 是标准写法，但仓库/组织策略是否允许只能在首次运行确认。
- Rust job：本机已装 1.90.0（与 `rust-toolchain.toml` 一致），`cargo test --lib` **94 passed**。

**只是不规范（未改）**

- Java job 先 `mvn test` 后 `mvn package`，会重复编译一次；不影响正确性。
- Rust `fmt`/`clippy` 仍是非阻塞，属于迁移期既有约定。

## 4.2 真实日志定位（2026-11-08，只读 PAT）

拿到 run `42490893314`（ci/master）与 `42490893332`（cd/master）的 job 日志后确认：

| job | 失败点 | 根因 | 修复 |
|---|---|---|---|
| ci/rust | `cargo test --lib` | `oss_client.rs:515` 断言 `creationDate` 带 `+08:00`；runner TZ=UTC | job 级 `TZ: Asia/Shanghai`（应用目标时区，不动断言） |
| ci/go | 构建 Linux 二进制 | master 没有 `cmd/migrate`（只在 `car-monit-go-V2`） | 存在才构建；产物上传改 `dist/*` |
| ci/py | pytest | runner 的 `USER=runner` 被 `AppSettings.user` 当嵌套模型解析 | 仅测试进程 `env -u USER` |
| cd/image-java | `cp ruoyi-admin-*.jar` | 实际产物是 `ruoyi-admin.jar`（`finalName` 无版本号），glob 不匹配 | 取 `target/*.jar` 第一个 |
| cd/image-go/rust/py | 读取 Dockerfile | `file: ./Dockerfile` 按 workspace 根解析，不是相对 context | 改 `car-monit-*/Dockerfile` |

迁移分支的三条失败（go-V2 / rust-V2 / py-V2）来自首推时的旧 workflow：go 是 v6+v2 lint 不兼容、rust 同一个 TZ 用例、py 同一个 `USER` 冲突；旧 workflow 已在同步提交中删除，新 `ci.yml` 只在 `master`/PR 触发，因此分支不会再有新 run。

## 4.3 最终验证结果（2026-11-08，master `2449ce2`）

| workflow | 分支 | run | 结果 |
|---|---|---|---|
| `ci` | `master` | 42493225126 | **success**（changes / java / go / rust / py / cpp 全绿；integration、go-perms-audit、rust-parity 手动触发，跳过） |
| `cd` | `master` | 42493225088 | **success**（image-java / image-go / image-rust / image-py 四个镜像均构建并推送到 GHCR） |

迁移分支没有再触发新 run：它们的新 `ci.yml` 只在 `push: master` 与 `pull_request: master` 时运行，推到分支本身不会产生 run。历史三条失败来自首推时的旧 workflow，已在同步提交中删除：

| 分支 | 历史 run | 历史失败原因 | 现状 |
|---|---|---|---|
| `car-monit-go-V2` | 42485227575 | 旧 workflow 的 `golangci-lint`（v6 + golangci-lint v2 不兼容） | 旧 workflow 已删除；新 ci 未在此分支触发（未运行） |
| `car-monit-rust-V2` | 42485240651 | `oss_client` 的 `+08:00` 断言（runner UTC） | 同上（TZ 修复已同步到分支） |
| `car-monit-py-V2` | 42485257375 | `USER=runner` 与 pydantic-settings `user` 字段冲突 | 同上（`env -u USER` 已同步） |
| `car-monit-cpp-local` | 无 | 首次推送时无 workflow | 已新增统一 YAML；push 不触发，PR 到 master 时才跑 |

C++ 分支的 `vcpkg_installed` 被 `car-monit-cpp/.gitignore` 忽略、并未入库，因此 `_cpp.yml` 已补回退逻辑：仓库内有 `vcpkg_installed/x64-windows` 就直接用，没有则用 runner 自带的 vcpkg manifest 安装**（该回退路径尚未实跑验证）**。

## 7. openEuler x86 容器化（2026-11-08）

Linux 构建 job 改为 `runs-on: ubuntu-latest` + `container: openeuler/openeuler:24.03-lts`（GitHub 托管 runner 没有欧拉镜像，只能容器方式）。

**包可得性核实（openEuler 24.03-LTS 官方仓库索引实测）**

| 依赖 | 欧拉仓库 | 采用方式 |
|---|---|---|
| JDK 8 | 有 `java-1.8.0-openjdk-devel-1.8.0.412`（OpenJDK，非 Temurin） | `dnf install`；与 Temurin 8 同为 TCK 兼容实现，字节码目标仍为 1.8，仅 JVM 发行版构建号不同 |
| Maven | 仓库索引未找到 | Apache 官方 3.9.9 tarball |
| Go 1.24 | 仓库/epol 未找到 1.24 | go.dev 官方 tarball |
| Rust 1.90 | 无 | rustup 官方脚本（与 `rust-toolchain.toml` 一致） |
| Python 3.12 | 仓库只到 3.11 | python.org 源码编译（约 3-5 分钟） |
| librdkafka | 未找到 | Rust 默认特性不需要；C++ 不在容器链路内 |

**例外（工作流内已注明）**

| job | 运行环境 | 原因 |
|---|---|---|
| `cpp` | `windows-latest` | 工程是 MSVC 专用（`/utf-8`、`NOMINMAX`）+ `vcpkg_installed/x64-windows`，Linux 需另一套构建配置 |
| `cd` 的 image-* | 宿主 `ubuntu-latest` | job 容器内没有 Docker daemon，buildx 需要宿主 Docker |
| `changes` / `rust-parity` | 宿主 | 元数据/对拍 job，不产出构建物 |

**待办 / 未验证**

- `services` 在容器 job 里的网络语义（容器内需用服务名而非 `127.0.0.1`）尚未改写与实测；当前 `integration` / `go-perms-audit` 仍是宿主 + 端口映射。
- ARM64 按用户决定搁置：未引入 `ARCH` 参数/多架构 manifest/QEMU；待办清单见 §8。
- PR 自测与 release（`v0.0.0-citest`）验证仍未执行（详见 §8）。

## 8. 待办清单（2026-11-08）

1. 容器内 services：把 `integration` / `go-perms-audit` 改为容器 job，服务用 `mysql` / `redis` 主机名，并实跑一次确认连通。
2. PR 自测：从 master 开噪声分支只改 `docs/ci-selftest.md`，验证 `ci` 的 paths-filter 分诊；完成后关闭 PR、删临时分支。
3. release 验证：打 `v0.0.0-citest`，确认 4 语言制品 + `SHA256SUMS` 上传；完成后删 tag 与 Release。
4. GHCR 回读：用 `read:packages` 凭据列出 `car-monit-{java,go,rust,py}` 与 tag。
5. ARM64（搁置）：`ARCH` 参数化、`linux/amd64,linux/arm64` manifest、QEMU 模拟、自托管 `[self-hosted, linux, arm64, openeuler]` 接入文档；注意 `vcpkg_installed/x64-windows` 在 ARM64 不可用。

## 9. 当前阻塞：Actions 无法分配 runner（2026-11-08 19:16 UTC）

**证据**

- run `42514187626`（cd，sha `5cbad2a`）的 4 个 image job 全部 `failure`，`started_at` 与 `completed_at` 相差 **2 秒**，`steps: []`，`runner_id: 0`、`runner_name: ""`。
- run `42514187641`（cd-standalone，同一 sha）4 个 build job 同样形态。
- 早前成功的 run（`42512484725`）同一 job 的 `runner_name` 是 `GitHub Actions 1000000524`、`steps` 11 个。
- 迁移分支的 `ci` run（`42512454499`）长期停在 `pending`，不进 `in_progress`。
- `GET /users/kai-cn/settings/billing/actions` 与 `GET /repos/.../actions/permissions` 均返回 **403**（PAT 无权限，无法确认剩余分钟数）。

**判断**：不是 YAML/代码问题，是私有仓库托管 runner 额度或并发额度耗尽（runner 未被分配）。需要在 GitHub 侧确认：

1. `Settings → Billing and plans → Actions` 看已用分钟数与 spending limit；
2. 若额度已满，提高 spending limit 或等下月重置；
3. `Settings → Actions → General` 确认 Actions 未被禁用。

**已做的成本收敛**（不削弱门禁，只减少重复构建）：

- `cd.yml` / `cd-standalone.yml` 的 `push` 加 `paths`：只有源码/打包输入变化才跑，docs 与 CI 注释类改动不再触发 4 个镜像 + 4 个安装包（tag 推送不受 paths 影响，发布不受限）。
- `ci.yml` 的路径分诊与门禁未放宽。

**因额度未完成的验证**

| 项 | 状态 |
|---|---|
| 单机 CD `verify` 四语言 | build 全过；verify 首轮因 go/rust 常驻进程挂住被取消，已加 `timeout 15`；新 run 因 runner 未分配无法验证 |
| 单机 CD `publish` 上传 Release | 未验证（依赖 verify 与可用 runner） |
| V3 新 run（`610ac5f`，rust/py 工装修复后） | 排队未开始 |
| PR 自测（`docs/ci-selftest.md` 噪声分支） | 未执行 |
| release（`v0.0.0-citest`） | 未执行 |

## 10. GHCR 回读结果（2026-11-08，classic token）

`GET /users/kai-cn/packages?package_type=container` 共 7 个包，其中本项目 4 个：

| 包 | 可见性 | 最新 tag | 最近更新时间 |
|---|---|---|---|
| `car-monit-java` | private | `sha-11675a7`、`latest` | 2026-11-08T18:56:55Z |
| `car-monit-go` | private | `sha-11675a7`、`latest` | 2026-11-08T18:56:56Z |
| `car-monit-rust` | private | `sha-11675a7`、`latest` | 2026-11-08T18:56:59Z |
| `car-monit-py` | private | `sha-11675a7`、`latest` | 2026-11-08T18:56:55Z |

每个包还保留历史 `sha-f73ce5b`、`sha-3a91876`、`sha-0f010c5` 等版本 tag；无 tag 的记录是同一 manifest 的多平台/子层对象。
另有 `car-monit-api*` 三个包（api 仓库产物），不在本次范围。

**结论**：`cd.yml` 的 GHCR 推送是真实落地的，四个镜像均可用 `ghcr.io/kai-cn/car-monit-<service>:<tag>` 拉取。
**注意**：包为 private，集群侧必须先建 imagePullSecret（见 [cd-ghcr-k8s.md](cd-ghcr-k8s.md) §3），否则 Pod 会 `ImagePullBackOff`。

## 11. V3 分支（car-monit-backend-java-V3）验证结论

远端分支已创建（最新 `610ac5f`），首次完整 run **42509946030** → `failure`：

| job | 结论 | 说明 |
|---|---|---|
| `changes` | 通过 | |
| `java` | **通过** | V3 的 Java 实现（类型化客户端、两级缓存等）在欧拉容器内编译/测试通过 |
| `cpp / build` | 通过 | 该分支 `car-monit-cpp` 无 `CMakeLists.txt`，presence 守卫正常跳过 |
| `go` | **失败（V3 代码问题）** | `golangci-lint` 报分支自身引入的问题，原始行示例：`internal/modules/flow/process.go:270` `func (*Service).saveFlowApply is unused`、`process.go:286` `doFlowApply is unused`、`repo_messagedispose.go:55` `selectMessageDisposeAll is unused`、`modules/generator/service.go:42` `var errNoSuchElement = errors.New("No value present") (ST1005)`、`internal/web/upload.go:24` `errors.New("Current request is not a multipart request") (ST1005)`。按约束**未修改 V3 业务代码** |
| `rust` | 失败（工装） | `oss_client.rs:515` 旧版 `+08:00` 硬断言，已同步 master 的 UTC 瞬间断言 |
| `py` | 失败（工装） | `gen_mapping_docs.py` / `test_mapping_docs.py` 用反斜杠匹配 Java 路径，Linux 上产出空表；已同步 master 的 posix 比较 |

工装修复提交 `610ac5f` 已推送，其 run **42512454499** 的 `changes` job 因 **runner 未分配**失败（`runner_name` 为空），后续 job 全部 skipped，**未验证**。

> 结论：V3 的 Java 目标实现本身可构建；剩余红灯一半是 V3 自身的 lint 债（需 V3 负责人清理），一半是已修好的跨平台工装。后者需等 runner 恢复后复验。

## 12. 两类红灯的区分（务必分开读）

| 形态 | 判定依据 | 含义 |
|---|---|---|
| **额度/runner 未分配** | job `started_at` 与 `completed_at` 相差 1–2 秒、`steps: []`、`runner_id: 0`、`runner_name: ""`；run 长期 `pending` | **代码没跑过**，不是失败。不要当成代码红 |
| **代码/工装失败** | job 有 `runner_name`（如 `GitHub Actions 1000000524`）、有具体失败 step、日志可下载 | 真实失败，需要修 |

本轮出现的 `changes` job 连续两次 2 秒 failure 属于**第一类**（run `42512454499`、`42514310305`），后续 job 全部 skipped。

## 13. rust / py 两处既有债的处理（2026-11-09）

### rust：按 api 侧方式固定时区，不改断言

- `oss_client::bucket_rows_take_owner_from_root` 断言 `+08:00`，runner 默认 UTC。
- **处理**：恢复原断言（`starts_with("2021-05-06T08:36:40.000")` + `ends_with("+08:00")`），在 rust job 加 `env: TZ: Asia/Shanghai`；容器内**显式安装 `tzdata`**，否则 chrono 的 `Local` 会退回 UTC 造成假失败。
- 本地验证：`TZ=Asia/Shanghai cargo test --lib oss_client` → **5 passed**。
- 已同步：master `2e05d12`、V3 `6db5fc2`、rust-V2 `d2338ac`、go-V2 `099cf01`、py-V2 `f099ee1`、cpp-local `824936d`。

### py：两个独立原因，都已根治

1. **生成器路径分隔符**：`gen_mapping_docs.py` 用 `config["controller_dir"].replace("/", "\\")` 匹配 Java 路径，Linux 上是 `/` → 匹配为 0，产出空表。改为两侧统一 posix 比较（`test_mapping_docs.py` 同步同口径）。
2. **文档确实过期**：V3 分支新增 `BigScreenExportController`（`ruoyi-admin/.../manager/bigscreen/`），但 `MAPPING_MANAGER.md` §4 没有它。已在 V3 工作树重跑生成器，`MAPPING_BASE.md` / `MAPPING_MANAGER.md` 更新。
- 本地验证（V3 工作树）：`pytest tests/test_mapping_docs.py` → **16 passed**（含 `test_generator_is_idempotent`）。

**V3 上仍存在的真实失败（未改业务代码）**：`go` job 的 `golangci-lint` 报 V3 自身引入的 unused / ST1005 问题，属 V3 代码质量债。

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
