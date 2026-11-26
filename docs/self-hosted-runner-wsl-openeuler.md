# 自托管 runner（WSL openEuler）接入说明

> 现状：**只准备，不注册**。当前所有 CI 仍跑在 GitHub 托管 runner（`ubuntu-latest` + `openeuler/openeuler:24.03-lts` 容器）。

## 1. 标签约定

| 标签 | 含义 |
|---|---|
| `self-hosted` | GitHub 必需 |
| `linux` | OS |
| `x64` | 架构（不是 `arm64`） |
| `wsl` | 跑在 WSL2 里 |
| `openeuler` | 发行版 |

引用方式：`runs-on: [self-hosted, linux, x64, wsl, openeuler]`

## 2. WSL2 + openEuler 前置

1. 安装发行版：`wsl --install -d openEuler`（或导入官方 rootfs）。
2. **启用 systemd**（单机 CD 的 `install.sh` 依赖它）：

```ini
# /etc/wsl.conf
[boot]
systemd=true
```

```powershell
wsl --shutdown   # 在 Windows 侧执行，然后重开
```

3. 校验：`systemctl is-system-running` 应返回 `running` 或 `degraded`（不是报错）。

## 3. 预装工具清单

```bash
sudo dnf install -y git curl tar gzip unzip jq \
  gcc gcc-c++ make \
  openssl-devel libffi-devel bzip2-devel zlib-devel xz-devel sqlite-devel \
  java-1.8.0-openjdk-devel \
  libicu
```

按需补装（与流水线保持一致）：

> **2026-11-26 本机 WSL（`openEuler-24.03-LTS-SP4`）语言环境已更新**：
> Go 1.27.4、Rust 最新 stable（rustup）、Python 3.15（uv 管理）已成为本机默认。
> 旧的 Go 1.24.x / 系统 Rust / 源码编译 Python 3.12 不再作为本机默认工具链。
> 项目版本已同步：`car-monit-go/go.mod` 为 `go 1.27` + `toolchain go1.27.4`，
> `car-monit-rust/rust-toolchain.toml` 为 `1.100.0`，与本机全局工具链一致。

| 工具 | 本机版本（2026-11-26） | 安装方式 / 关键环境变量 |
|---|---|---|
| Go | 1.27.4 | `sudo tar -C /usr/local -xzf /home/dev/go1.27.4.linux-amd64.tar.gz`；`GOROOT=/usr/local/go`、`GOPATH=/home/dev/go`（保留原有 `pkg/mod` 缓存）、`PATH=$GOROOT/bin:$GOPATH/bin:$PATH` |
| Rust | latest stable = 1.100.0（rustup） | 删除旧 Rust 后安装 rustup 并 `rustup default stable`（profile minimal + rustfmt/clippy）；`CARGO_HOME=$HOME/.cargo`、`RUSTUP_HOME=$HOME/.rustup`、`PATH=$CARGO_HOME/bin:$PATH` |
| Python | 3.15（uv 管理） | `uv python install 3.15`；`uv` 在 `$HOME/.local/bin`（加入 PATH），用 `uv venv` 建隔离环境，不再源码编译 |
| Docker | 可选 | 跑 `cd.yml` 的 buildx 需要；否则把镜像构建留给托管 runner |
| kubectl | 可选 | 仅在自托管上做 K8s 部署时需要 |

版本校验：

```bash
go version                 # go1.27.4 linux/amd64
rustup show                # default toolchain: stable 1.100.0（项目目录内同为 1.100.0）
uv python list             # 含 cpython-3.15.x
uv python find 3.15        # 3.15 解释器路径
```

## 4. 注册 runner

```bash
# 1) 取注册 token（在 GitHub 仓库 Settings → Actions → Runners → New self-hosted runner 页面）
#    或：gh api -X POST repos/kai-cn/car-monit-backend/actions/runners/registration-token --jq .token

# 2) 下载并解包
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -fsSLO https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64.tar.gz
tar -xzf actions-runner-linux-x64.tar.gz

# 3) 配置（标签一次写全）
./config.sh \
  --url https://github.com/kai-cn/car-monit-backend \
  --token <REGISTRATION_TOKEN> \
  --name wsl-openeuler-x64 \
  --labels self-hosted,linux,x64,wsl,openeuler \
  --work _work \
  --unattended

# 4) 前台试跑（先确认能接活）
./run.sh
```

注册成功后：`gh api repos/kai-cn/car-monit-backend/actions/runners --jq '.runners[] | [.name,.status,.labels[].name] | @tsv'`

## 5. 常驻与自启（WSL 特有）

WSL **不随 Windows 启动**，重启后 runner 会离线。

- **手动**：`wsl -d openEuler -u <user> -- bash -lc 'cd ~/actions-runner && ./run.sh'`
- **systemd 服务**（推荐，需 WSL 已启用 systemd）：

```ini
# /etc/systemd/system/gha-runner.service
[Unit]
Description=GitHub Actions Runner (wsl openeuler)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<your-user>
WorkingDirectory=/home/<your-user>/actions-runner
ExecStart=/home/<your-user>/actions-runner/run.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now gha-runner
```

- **Windows 侧计划任务**（WSL 不自启时的兜底）：登录时执行
  `wsl.exe -d openEuler -u <user> -- bash -lc "sudo systemctl start gha-runner"`

> 注意：WSL 关闭后 systemd 一并停止，`Restart=always` 只在 WSL 内部有效。

## 6. WSL2 网络限制

- **入站默认不可达**：宿主访问用 `localhost`；局域网/公网访问需在 Windows 上做
  `netsh interface portproxy add v4tov4 listenport=9989 listenaddress=0.0.0.0 connectport=9989 connectaddress=<WSL IP>`，
  并且 WSL IP 每次重启会变（用 `wsl hostname -I` 取）。
- 出站正常，但 `docker`/`dnf` 走代理时要在 WSL 内单独配置。

## 7. 哪些 job 适合放自托管

| job | 建议 | 原因 |
|---|---|---|
| `cd-standalone` 的 `build` | 可以 | 与托管 runner 等价，但私有仓库 Actions 分钟数可省 |
| `cd-standalone` 的 `verify` | 可以（真正贴目标机） | 能验证 systemd unit 在欧拉上的实际行为 |
| `ci` 的 java/go/rust/py | 暂不放 | 容器化已覆盖欧拉；自托管只有 1 台，会成为串行瓶颈 |
| `ci` 的 `cpp` | **不能** | 需要 Windows + MSVC |
| `cd` 的 image-* | 需要 Docker | WSL 内需自行装 Docker 并确认 buildx 可用 |
| `deploy`（K8s） | 可以 | 需要 `kubectl` 与 `secrets.KUBE_CONFIG` |

## 8. 切换方式（托管 → 自托管）

把对应 job 的 `runs-on` 换掉即可，其余不变：

```yaml
# 托管（现状）
runs-on: ubuntu-latest
container:
  image: openeuler/openeuler:24.03-lts

# 自托管（WSL openEuler）
runs-on: [self-hosted, linux, x64, wsl, openeuler]
# 注意：自托管上不要再写 container:，否则等于容器套容器，且 systemd 不可用
```

同时删掉"安装 JDK/Go/Rust/Python"的步骤（预装清单已覆盖），否则会重复安装。
