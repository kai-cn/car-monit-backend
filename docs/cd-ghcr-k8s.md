# CD：GHCR + K8s

本文配合 `.github/workflows/cd.yml`（构建并推镜像）与 `.github/workflows/deploy.yml`（滚动更新已存在的 Deployment）。

## 1. 镜像与 tag

| 服务 | 镜像 | Dockerfile | 基础镜像 |
|---|---|---|---|
| Java 8 | `ghcr.io/kai-cn/car-monit-java` | `docker/java.Dockerfile` | 构建 `maven:3.9-eclipse-temurin-8` / 运行 `eclipse-temurin:8-jre` |
| Go | `ghcr.io/kai-cn/car-monit-go` | `car-monit-go/Dockerfile` | 构建 `golang:1.24-alpine` / 运行 `gcr.io/distroless/static-debian12:nonroot` |
| Rust | `ghcr.io/kai-cn/car-monit-rust` | `car-monit-rust/Dockerfile` | 构建 `rust:1.90-bookworm` / 运行 `debian:bookworm-slim` |
| Python | `ghcr.io/kai-cn/car-monit-py` | `car-monit-py/Dockerfile` | `python:3.12-slim` |
| C++ | **不覆盖** | 无 | 见 §5 |

tag 规则（`docker/metadata-action`）：

- `sha-<7 位短哈希>`：每次构建都有，便于回溯。
- `v*.*.*` tag 触发的版本号，例如 `1.2.3`。
- `latest`：仅 `master` 分支推送时打。

**基础镜像选择理由**

- Java 用 Temurin 8 JRE：仓库所有 `pom.xml` 只有 `java.version=1.8`，运行阶段不需要 JDK（省 ~200 MB）。
- Go 用 distroless static：`CGO_ENABLED=0` 产物是纯静态二进制，distroless 没有 shell/包管理器，攻击面最小。
- Rust 用 debian-slim：二进制动态链接 glibc，需要 `ca-certificates`（HTTPS）与 `tzdata`；distroless 排障成本更高。默认特性不启用 `kafka`，所以构建阶段不需要 librdkafka/cmake。
- Python 用 `python:3.12-slim`：依赖全是 manylinux wheel（PyMySQL / bcrypt / Pillow / psutil），无需编译工具链。

所有镜像都建了非 root 用户（uid 10001）并暴露 9989。

## 2. GHCR 推送权限

`cd.yml` 只用 `GITHUB_TOKEN`，不引入 PAT：

```yaml
permissions:
  contents: read
  packages: write
```

登录用 `${{ github.actor }}` + `${{ secrets.GITHUB_TOKEN }}`。首次推送后，包会挂在仓库的 Packages 下；如果组织策略要求，需要管理员把包可见性/权限调成与仓库一致。

## 3. 集群侧：私有 GHCR 必须建 imagePullSecret

GHCR 包默认私有。目标命名空间必须先有拉取凭据，否则 Pod 会 `ImagePullBackOff`。

由运维在目标命名空间执行（**不要把凭据写进仓库**）：

```bash
kubectl -n <K8S_NAMESPACE> create secret docker-registry <K8S_IMAGE_PULL_SECRET> \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=<PAT-with-read:packages> \
  --docker-email=<email>
```

然后确认 Deployment 的 Pod 模板引用了它：

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
        - name: <K8S_IMAGE_PULL_SECRET>
```

`deploy.yml` 会在更新镜像前检查该 secret 是否存在，缺了就显式失败。

## 4. 首次部署需要人工 bootstrap

仓库里**没有 K8s manifest**（只有 workflow）。因此 `deploy.yml` 只做 `kubectl set image` + `kubectl rollout status`，不创建资源。首次部署前需要运维预先准备：

1. 命名空间。
2. Deployment（容器名要与 `vars.K8S_CONTAINER` 一致，镜像字段可先用占位值）。
3. Service / Ingress（按需）。
4. imagePullSecret（见 §3）。

之后在仓库 Variables 配置：

| Variable | 含义 |
|---|---|
| `K8S_NAMESPACE` | 目标命名空间 |
| `K8S_DEPLOYMENT` | Deployment 名 |
| `K8S_CONTAINER` | Deployment 内的容器名 |
| `K8S_IMAGE_PULL_SECRET` | 已存在的 imagePullSecret 名 |

Secrets：`KUBE_CONFIG`（kubeconfig 的 base64）。workflow 里不写任何集群地址。

## 5. C++ 为什么不在 CD 覆盖

`car-monit-cpp` 的依赖走 vcpkg manifest，仓库里入库的是 `vcpkg_installed/x64-windows`（Windows triple，30 MB）。Linux 镜像需要重新构建 librdkafka 及其依赖，构建时长与产物可用性都未验证。因此：

- CI 仍会在 `windows-latest` 上跑 C++ 的 CMake/MSVC 构建与 ctest（`.github/workflows/_cpp.yml`）。
- CD **不产出 C++ 镜像**。需要时先补 Linux 依赖方案（自建 vcpkg 缓存或改用 `librdkafka-dev`）与 Dockerfile，再往 `cd.yml` 加 job。

## 6. 部署流程

1. `master` 合并 → `cd.yml` 推 `sha-xxxxxxx` 与 `latest`。
2. 在 Actions 里手动跑 `deploy`，选择 `service` / `image_tag`（建议用 `sha-xxxxxxx`，可回溯）/ `environment`。
3. workflow 依次校验变量与凭据 → 检查 Deployment 与 imagePullSecret → `kubectl set image` → `kubectl rollout status`（300s 超时）。

回滚：用上一个 `sha-xxxxxxx` 重跑 `deploy`。

## 7. 未验证项

- 本机没有 Docker 与集群，所有镜像构建、GHCR 推送、K8s 部署均**已写好但未实跑**。
- Java 镜像首次构建会全量下载 Maven 依赖，耗时取决于网络。
- Rust 镜像 `cargo build --release` 可能 10 分钟以上。
- C++ CI（`_cpp.yml`）未实跑，`vcpkg_installed` 能否被 MSVC 直接复用需要在首次运行确认。
