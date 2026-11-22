<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# WSL k3s 一主两从集群 + 自托管 Runner CI/CD 记录

> 在 `car-monit-backend-java-V3` 与 `car-monit-api-java-V3` 两个工作树的
> `docs/v3/review/` 下各存一份，内容一致。记录日期：2026-11-10。
> **本文件不写任何账号口令、GitHub PAT、runner 注册令牌、内部端点令牌明文。**

## 1. 目标与结论摘要

| 目标 | 状态 |
| --- | --- |
| WSL2 内 k3s 一主两从集群 | ✅ 建成并验证（1 control-plane + 2 agents，全 Ready） |
| GitHub 自托管 runner（backend 仓库） | ✅ `wsl-k3s` online |
| GitHub 自托管 runner（api 仓库） | ✅ `wsl-k3s-api` online |
| 绕过账号账单导致 GitHub-hosted runner 不可用 | ✅ **实证通过**：自托管 job `completed/success` |
| 两仓库 CI/CD 流水线（编译 + 单测 + 部署到 k3s） | ✅ 两条 run 均 `completed/success`，结果见第 8 节 |

**核心发现**：GitHub 账号 `recent account payments have failed` 只阻塞 GitHub-hosted runner 的
分配；自托管 runner 不消耗 Actions 分钟数，job 可正常派发与执行。这是本方案成立的前提，
已用探针 workflow（`run id=42816685567`，`completed/success`）实证。

## 2. 环境前提（实测）

| 项 | 值 |
| --- | --- |
| 物理内存 | 13.84GB，本轮开始时可用 4.65GB（前一轮的 4 个 java 实例均已停止） |
| 磁盘 | C: 11GB 可用；D: 33.5GB 可用 |
| CPU | 12 逻辑核 |
| WSL | 3.0.3 / WSL2 / 内核 `6.18.54.1-microsoft-standard-WSL2` / openEuler 24.03 LTS-SP4 |
| WSL 发行版位置 | `D:\wsl\openEuler-24.03-LTS-SP4\ext4.vhdx`（3.3GB，**已由并行会话从 C 盘迁移完成**，本轮未重复迁移） |
| 调整后 `.wslconfig` | `memory=6GB`、`swap=4GB`、`processors=4`、`swapFile=D:\\wsl\\swap\\swap.vhdx`、`localhostForwarding=true` |
| WSL 内实测 | 5928MB 可用 / 4 vCPU / systemd PID1 / cgroup v2 |

### 2.1 配置踩坑

- `.wslconfig` 的 `swapFile` 中单个反斜杠会被 WSL 当转义字符报「转义字符无效」，必须用
  **双反斜杠**（`D:\\wsl\\...`）。
- `[boot] systemd=true` 段在 `.wslconfig` 中不被 WSL 3.0.3 支持（报「键未知」）；
  该发行版本身 `PID1=systemd`，无需配置，已移除该段。

## 3. k3s 一主两从集群

### 3.1 技术选型

单 WSL2 VM 内实现 3 个独立节点，采用 **k3d**（Docker 内跑 k3s 节点）而非 3 个 WSL 发行版：
后者需要 3 份 VM 内存与 3 份 vhdx，宿主内存不允许。k3d 是本地多节点 k3s 的标准做法。

| 组件 | 版本 |
| --- | --- |
| Docker (openEuler `moby`) | 25.0.3，CgroupDriver=systemd，Storage=overlay2 |
| k3d | v5.9.0 |
| k3s | v1.35.5+k3s1，containerd 2.2.3-k3s1 |
| 集群 | `k3d cluster create v3 --servers 1 --agents 2 --port 6443:6443@loadbalancer`，禁用 traefik / metrics-server |

### 3.2 节点状态（实测）

```
NAME              STATUS   ROLES           VERSION        CONTAINER-RUNTIME
k3d-v3-server-0   Ready    control-plane   v1.35.5+k3s1   containerd://2.2.3-k3s1
k3d-v3-agent-0    Ready    <none>          v1.35.5+k3s1   containerd://2.2.3-k3s1
k3d-v3-agent-1    Ready    <none>          v1.35.5+k3s1   containerd://2.2.3-k3s1
```

系统 Pod：`coredns` 1/1 Running、`local-path-provisioner` 1/1 Running。

### 3.3 镜像网络问题与解决（关键）

本机 **Docker Hub (`registry-1.docker.io`) 不可达**（curl 12s 超时），但以下源可达：
`ghcr.io`(401)、`docker.m.daocloud.io`(401)、`docker.1panel.live`(200)、
`registry.cn-hangzhou.aliyuncs.com`(401)。

需要**两层**加速，缺一不可：

1. Docker daemon `/etc/docker/daemon.json`：
   ```json
   { "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1panel.live"] }
   ```
   用于 `k3d` 拉取 `rancher/k3s`、`ghcr.io/k3d-io/k3d-tools` 等节点镜像。
2. **k3s 节点内 containerd 不走 Docker daemon 的 mirror**，需在每个节点容器内写
   `/etc/rancher/k3s/registries.yaml` 后重启节点：
   ```yaml
   mirrors:
     docker.io:
       endpoint:
         - https://docker.1panel.live
         - https://docker.m.daocloud.io
     ghcr.io:
       endpoint:
         - https://ghcr.io
     registry.k8s.io:
       endpoint:
         - https://registry.aliyuncs.com/google_containers
   ```
   未配置时系统 Pod 报
   `failed to get sandbox image "rancher/mirrored-pause:3.6" ... dial tcp registry-1.docker.io:443: i/o timeout`，
   coredns / local-path-provisioner 一直 `ContainerCreating`。配置并重启 3 个节点后恢复 Running。

## 4. 自托管 Runner

| 仓库 | 名称 | 标签 | 目录 | systemd 单元 |
| --- | --- | --- | --- | --- |
| `kai-cn/car-monit-backend` | `wsl-k3s` | `self-hosted,Linux,X64,wsl-k3s` | `/opt/actions-runner` | `actions-runner.service` |
| `kai-cn/car-monit-api` | `wsl-k3s-api` | `self-hosted,Linux,X64,wsl-k3s-api` | `/opt/actions-runner-api` | `actions-runner-api.service` |

- Runner 版本 `2.338.2`（`actions/runner` latest），从 GitHub releases 下载 217.5MB 归档；
  第二个 runner 直接复制已解压目录，不重复下载。
- 以**非 root 用户 `dev`** 运行（`config.sh` 明确拒绝 root/sudo）；`dev` 已加入 `docker` 组，
  使 CI 的 CD 步骤可执行 `docker exec ... kubectl`。
- 注册令牌通过 `WSLENV=RUNNER_TOK/u` 环境变量传入 WSL，**不写入任何文件**；
  仓库级 registration token 由 GitHub API 获取（1 小时有效）。
- `KillMode` 必须是 `control-group`。最初用了 `KillMode=process`，stop 后残留
  `Runner.Listener` / `run-helper.sh`，重启产生第二个实例，日志报
  `A session for this runner already exists ... Conflict`，runner 变 offline、job 一直 queued。
  修复方式为 `KillMode=control-group` + 删除 GitHub 侧旧 runner 记录 + 重新注册。

### 4.1 构建工具链

WSL 内安装 `java-1.8.0-openjdk-devel`（BiSheng 1.8.0_502）与 `maven 3.6.3`，
`/home/dev/.m2/settings.xml` 配置阿里云 public 镜像。

## 5. CI/CD 流水线

两仓库各新增 `.github/workflows/self-hosted-ci.yml`，结构一致：

```yaml
on:
  workflow_dispatch:
  push:
    branches: [ <V3 分支> ]
    paths: [ .github/workflows/self-hosted-ci.yml, pom.xml, <业务模块>/** ]

jobs:
  build:      # runs-on: [self-hosted, linux, x64, wsl-k3s | wsl-k3s-api]
    - Runner environment
    - actions/checkout@v4
    - Toolchain (java -version / mvn -v)
    - mvn compile   # backend: -pl ruoyi-common,ruoyi-system,ruoyi-framework,ruoyi-admin -am
                    # api:     -pl pro-business-api -am
    - mvn test
  deploy:     # needs: build
    - docker exec k3d-v3-server-0 kubectl get nodes
    - kubectl create deployment ... --replicas=3 --dry-run=client -o yaml | kubectl apply -f -
    - kubectl rollout status + get pods -o wide
```

CD 用 `rancher/mirrored-pause:3.6`（节点已缓存）部署 3 副本，验证一主两从调度。

## 6. 关键问题与解决台账

| 问题 | 处理 |
| --- | --- |
| GitHub-hosted runner 因账号账单秒级失败 | 改用自托管 runner，探针 run `42816685567` 全步骤 success，证实可绕过 |
| Docker Hub 不可达 | Docker daemon + k3s containerd 双层 registry mirror |
| runner session 冲突 / offline | `KillMode=control-group`、删除旧 runner 记录、以 dev 用户重新注册 |
| Windows 侧 `github.com` 连接重置 / 超时，`api.github.com` 正常 | 用 GitHub **Contents API** (`PUT /repos/{repo}/contents/...`) 落地 workflow 文件 |
| WSL 内 `wsl --exec bash -c` 复杂引号 / 管道易被 PowerShell 破坏 | 所有复杂 shell 逻辑写成 `D:\work\runtime-logs\wsl-setup\*.sh` 脚本文件后执行；长任务用 `systemd-run` 后台 |
| `Select-Object -First N` 会提前终止管道并杀掉 wsl 进程 | 诊断命令不用截断管道，或把输出写入文件再 tail |
| k3d 镜像 tag 过新（v1.35.5）拉取慢 | 脚本改为可指定镜像；实际镜像最终通过 mirror 拉取成功 |

## 7. 复现命令（凭据用环境变量）

```powershell
# WSL 配额（改后需 wsl --shutdown）
#   [wsl2] memory=6GB / swap=4GB / processors=4 / swapFile=D:\\wsl\\swap\\swap.vhdx

# 集群
wsl -d openEuler-24.03-LTS-SP4 -u root --exec bash -c '/usr/local/bin/k3d cluster create v3 --servers 1 --agents 2 --wait'
wsl -d openEuler-24.03-LTS-SP4 -u root --exec bash -c 'docker exec k3d-v3-server-0 kubectl get nodes'

# runner（令牌由 WSLENV 传入）
$env:RUNNER_TOK = (Invoke-RestMethod -Method Post -Uri "<repo>/actions/runners/registration-token" -Headers $hd).token
$env:WSLENV = 'RUNNER_TOK/u'
wsl -d openEuler-24.03-LTS-SP4 --exec bash -c '/mnt/d/work/runtime-logs/wsl-setup/07-reregister-dev.sh'

# 服务状态
wsl -d openEuler-24.03-LTS-SP4 -u root --exec bash -c 'systemctl is-active actions-runner.service actions-runner-api.service docker'
```

完整脚本清单见 `D:\work\runtime-logs\wsl-setup\01..16-*.sh` 与
`actions-runner.service` / `k3d-registries.yaml`（**均为本机运行配置，未纳入仓库**）。

## 8. 验证结果

| 项 | 结果 |
| --- | --- |
| 探针流水线（backend） | run `42816685567`，`completed/success`（Set up job / Runner environment / Checkout / Verify workspace / Post Checkout / Complete job 全部 success） |
| 集群节点 | 3/3 Ready（1 control-plane + 2 agents） |
| 系统 Pod | coredns、local-path-provisioner 均 1/1 Running |
| runner 在线 | backend `wsl-k3s` online；api `wsl-k3s-api` online |
| 完整 CI/CD 流水线 | 两仓库已通过 Contents API 落地（backend `a3fb900`、api `0a19829`），首次运行见下节「运行状态」 |

### 8.1 完整流水线运行结果（最终）

| 仓库 | run id | 触发 | CI `compile-and-test` | CD `deploy-to-k3s` | 结论 |
| --- | --- | --- | --- | --- | --- |
| backend | `42823962291` | push（Contents API commit `a3fb900`） | `completed/success`：Checkout / Toolchain / Compile V3 modules / Unit tests 全 success | `completed/success`：Verify cluster / Roll out demo workload | **全链路通过** |
| api | `42823965689` | push（Contents API commit `0a19829`） | `completed/success`：Checkout / Toolchain / Compile V3 api module / Unit tests 全 success | `completed/success` | **全链路通过** |

**CD 集群实证**（`kubectl get deployments,pods -o wide`）：

```
NAME              READY   UP-TO-DATE   AVAILABLE
v3-ci-probe       3/3     3            3
v3-api-ci-probe   3/3     3            3
```

6 个 Pod 全为 `1/1 Running`，分布为 `k3d-v3-server-0` 2 个、
`k3d-v3-agent-0` 2 个、`k3d-v3-agent-1` 2 个 —— 一主两从**均参与调度**。
`actions-runner.service`、`actions-runner-api.service`、`docker` 三个服务均 `active`。

**对照**：同一时段 GitHub-hosted 的 `ci.yml` / `master.yml` 仍因账号账单秒级失败
（`steps=0`、runner 为空），而自托管流水线完整跑完编译、单测与部署，进一步确认第 1 节结论。

首次运行的 `Checkout` 曾受 `github.com` 网络抖动影响较慢（探针流水线约 6 分钟），
Maven 首次依赖下载亦耗时数分钟；`build` job timeout 设为 45 分钟，实际在超时前完成。

## 9. 已知限制与待办

- Windows 侧 `github.com` 的 git 传输当前不可用；两仓库 workflow 通过 **Contents API** 落地，
  与本地工作树存在「内容等价、hash 不同」的分叉。网络恢复后需执行
  `git fetch origin && git reset --hard origin/<V3 分支>` 同步（本地被替换的 commit 内容已在远端，无损失）。
- `actions/checkout@v4` 与 Maven 依赖均依赖外网；建议在 WSL 内配置稳定代理或预缓存依赖。
- 自托管 runner 为**仓库级**、运行于本机 WSL，机器休眠/关机时 CI 会排队；非高可用部署。
- k3s 集群为本地学习/联调用途，单点 server，未做持久化与备份。
- 凭据处理：GitHub PAT / registration token 仅通过进程环境变量传递，未写入仓库文件、
  脚本、文档或提交信息；推送临时日志已直接删除（未进回收站）。

## 10. 资源占用实测与配额调优（2026-11-10 追加）

### 10.1 实测数据（配额 6GB / 4 vCPU，74 个采样点，含一次 Maven 编译压测）

| 指标 | 空闲态 | CI / Maven 峰值 |
| --- | --- | --- |
| WSL 内 `Mem.used` | 1520MB | **1778MB** |
| WSL 内 `Mem.available` | 4408MB | 4149MB |
| 构建相关进程 RSS（`proc_mb`） | 982MB | 1253MB |
| 4 个 k3d 容器合计 | 662MB | 662MB（恒定） |
| `swap_used` | 0 | **0**（全程未换页） |
| 宿主 `vmmemWSL` 工作集 | 5478MB（均） | **5505MB（峰）** |
| 宿主可用内存 | **0.00GB** | **0.00GB** |

组件明细（空闲）：`k3s`×3 ≈ 840MB、`containerd`×3 ≈ 483MB、
`Runner.Listener`×2 ≈ 258MB、`dockerd` 109MB、coredns 59MB；
容器：server 355MB、agent-0 160MB、agent-1 140MB、serverlb 7MB。
磁盘：vhdx 7.46GB、Docker 镜像 346.6MB、卷 499.4MB。

**关键发现**：WSL 内实际用量峰值仅 1.78GB，但 `vmmem` 占 5.5GB —— 差额
约 3.8GB 是 Linux page cache，WSL2 默认不主动归还宿主，导致宿主可用内存被压到 0。

### 10.2 配额对比实测

| 配置 | `vmmem` 峰值 | 宿主可用内存 | 集群/runner |
| --- | --- | --- | --- |
| 6GB / 4CPU，无回收 | 5505MB | 0.00GB | 稳定，两仓库 CI/CD 全绿 |
| 3GB / 2CPU + `autoMemoryReclaim=gradual` | 1620~2200MB | 4.38~5.24GB | 重启后 k3s 冷启动慢、runner 反复 offline |
| 4GB / 2CPU + 自动回收 | 1700~2500MB | 4.2~5.1GB | apiserver 间歇 `ServiceUnavailable`、runner 失联 |
| **4GB / 2CPU，无自动回收（最终采用）** | 1709~2500MB | 4.33GB | **稳定**：3 节点 Ready、系统 Pod 1/1、双 runner online |

- `[experimental] autoMemoryReclaim=gradual` 确实能把 `vmmem` 压到接近实际用量，
  但实测伴随 k3s apiserver 间歇不可用与 runner 反复掉线，**不建议在跑集群时常开**。
- WSL 内 `sync; echo 3 > /proc/sys/vm/drop_caches` 能把 buff/cache 从 1745MB 降到 619MB，
  但 `vmmem` 不会随之回落（实测反而 2.5GB），**对释放宿主内存无效**。
- 因此**唯一可靠手段是调低 `.wslconfig memory` 上限**。

### 10.3 最低稳定运行资源（结论）

| 资源 | 最低 | 推荐 | 依据 |
| --- | --- | --- | --- |
| WSL 内存 | **3GB** | **4GB** | 峰值 1.78GB；3GB 可持续运行但冷启动/重建余量不足，4GB 稳定 |
| vCPU | 2 | 2~4 | Maven 单线程编译，2 核无瓶颈（宿主 12 核） |
| swap | 1GB | 2GB | 实测 `swap_used=0`，仅作兜底 |
| 磁盘 | 12GB | 15GB | vhdx 7.46GB + 镜像/卷 ~850MB + CI 工作区与依赖缓存 |
| 宿主可用内存 | ≥2GB | ≥3GB | 6GB 配额时宿主 0GB 可用，系统重度换页（pagefile 峰值 10.79GB） |

### 10.4 Win 侧内存不够的处理建议

1. **可以调低**：把 `memory` 从 6GB 降到 **4GB**（`processors=2`、`swap=2GB`），
   宿主可用内存从 0GB 恢复到约 4GB；这是本次最终采用的稳定配置。
2. 不必降到 3GB 以下：实际用量 1.78GB，但 k3s 冷启动需重建证书/恢复 sqlite，
   低于 4GB 时重启后 apiserver 需要 8 分钟以上才稳定，且易与 runner session 问题叠加。
3. **不要为了省内存反复 `wsl --shutdown`**：每次重启都会触发
   k3s 冷启动（5~8 分钟）与 runner 服务端 session 残留（需删除记录 + 重新注册）。
4. 若确需临时释放：优先停掉 Windows 侧非必要进程，或在不跑 CI 时
   `k3d cluster stop v3`（容器停止后 WSL 内 `used` 可降到 ~440MB）。
5. 后台长任务不要用 `systemd-run` + 管道截断组合执行：本项目曾因
   `Select-Object -First N` 提前终止 `wsl` 管道，导致集群重建到一半、
   `k3d-v3-serverlb` 缺 `/etc/confd/values.yaml` 一直重启，apiserver 报 503。
   改用同步执行完整脚本（`28-recreate-sync.sh`）后集群 19 秒建成、节点 9 秒 Ready。
6. **4GB 下的 CI 复跑（如实）**：两仓库 `workflow_dispatch` 均已由各自 runner 接单，
   但 `actions/checkout` 受 `github.com` 网络抖动长时间停在 `in_progress`，与内存配额无关
   （6GB 时首次 Checkout 也曾耗时约 6 分钟）。4GB 下已验证稳定的是：3 节点 Ready、
   系统 Pod 1/1 Running、双 runner online、三个 systemd 服务 active；
   CI 编译与 CD 部署在 6GB 配置下已两次全绿，低配下待外网恢复后复跑确认。
