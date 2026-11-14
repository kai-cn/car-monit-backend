# k3s/k3d 真实部署 Java 服务与节点故障演练（方案 + 实机记录）

> 日期：2026-11-14　环境：WSL2 openEuler 24 内的 **k3d 集群 `v3`（1 control-plane + 2 agents，k3s v1.35.5+k3s1）**。
> 本文按「先规划、再执行、如实记录」组织：第 1–5 节为执行前方案，第 6 节起为实际结果，**包含所有失败、偏差与结论**。

## 1. 环境实况（执行前探测，不是假设）

| 项 | 实测值 |
| --- | --- |
| 集群 | `k3d cluster list` → `v3 1/1 servers 2/2 agents loadbalancer=true`；节点 `k3d-v3-server-0 / agent-0 / agent-1`，三个节点均**无污点**（控制面可调度） |
| k8s 版本 | `v1.35.5+k3s1`，containerd 2.2.3 |
| CI 的 deploy-to-k3s 实际内容 | `v3-ci-probe` / `v3-api-ci-probe` 各 3 副本，镜像 **`rancher/mirrored-pause:3.6`**（pause 占位，**没有任何 Java 进程**）——用户指出的缺口属实 |
| WSL 可用内存 | `free -h` → total 3.8Gi / available 2.3Gi（swap 2.0Gi）；Windows 侧可用约 2.2Gi / 13.84Gi（两者共享物理内存） |
| 本地 docker 镜像 | 只有 `mysql:8.0.30`、`enmotech/opengauss:3.0.0`、`rancher/k3s`、`k3d-tools/proxy`、`oracle11g`；**没有 JDK/JRE 基础镜像、没有 redis 镜像** |
| Linux JDK | CI runner 缓存已有 `/home/dev/.cache/ci-toolchain/jdk-17.0.21+9`、`jdk-21.0.13+9`、`jdk-25.0.5+8`（Temurin，Linux x64，均可运行） |
| 网络 | k3d 网络 `172.18.0.0/16`，网关 `172.18.0.1`。从 k3d 节点用 `wget` 实测：`172.18.0.1:3307` 拿到 MySQL 8.0.30 握手、`172.18.0.1:5432` 连通（非 HTTP 故无响应）；直接访问 `172.17.0.x:3306/5432` 超时 |
| Windows 侧 Redis | 只监听 `127.0.0.1:6379` / `::1`，**WSL/k3d 无法访问**；WSL VM 自带 `/usr/bin/redis-server` |
| ES / Kafka | ES 9200 从 WSL 不可达（Windows 绑定/防火墙）；Kafka 9092 从 WSL VM 可达、从 k3d 节点未确认 |

> 早先用 `nc` / `/dev/tcp` 探测得到「全部 FAIL」是**假阴性**：k3d 节点镜像里没有 `bash`/`nc`/`curl`，只有 `sh`/`wget`/`timeout`/`tar`。用 `wget -S --spider` 才得到真实结论。

## 2. 目标与约束

1. 用 k3s **真正部署 backend 与 api 的 Java 服务**（替换 pause 占位），各 **3 副本**。
2. 每个 Java 容器 **`resources.limits.memory: 300Mi`**（`requests` 同为 300Mi），JVM 参数必须让进程稳定在 300Mi 以内。
3. 实机集群接口验收：登录、分页、跨服务 backend→api、多副本负载均衡。
4. 模拟服务节点故障：删 Pod、停整个 agent 节点，验证 k3s 自愈；恢复节点后确认不产生多余副本。
5. 内存约束：迁入 k3s 前**先停掉 Windows 本机两个 Java 进程**（9989/9902），避免重复与浪费内存；ES/Kafka/Redis/DB 保持单实例。

## 3. 方案架构

```
Windows 本机                WSL VM (openEuler)                       k3d-v3 集群 (k3s)
─────────────────           ─────────────────────────────           ─────────────────────────────
ES 9200 / Kafka 9092        mysql_wsl :3307 (docker) ◄──┐           Deployment car-monit-backend (3)
Redis 6379 (127.0.0.1)     opengauss :5432 (docker) ◄──┼─ 172.18.0.1:3307 / :5432
                            redis-server :6380 (新增) ◄──┘           Deployment car-monit-api (3)
                                     ▲                               Service car-monit-api:9902 (ClusterDNS)
                                     └── 172.18.0.1:6380 ───────────► 两个 Deployment 共享缓存
```

### 3.1 镜像（无外网依赖）
- 本地没有 JDK 基础镜像，也不拉 Docker Hub。用**本地已有镜像 + 本地 JDK**：
  - `FROM mysql:8.0.30`（实测 GNU libc 2.28）构建基础层，`COPY` WSL 缓存里的 Linux JDK 到 `/opt/jdk`；
  - 再分别 `FROM` 基础层 + `COPY` 已打好的 fat jar，得到 `car-monit-backend:local` / `car-monit-api:local`；
  - `ENTRYPOINT ["/opt/jdk/bin/java"]`，JVM 与 Spring 参数全部由 Deployment 的 `args` 传入。
- `k3d image import` 把镜像导入 3 个节点的 containerd，Deployment 用 `imagePullPolicy: Never`。

### 3.2 外部依赖接入
- DB：容器里用 `172.18.0.1:3307`（MySQL） / `172.18.0.1:5432`（openGauss）覆盖 yml 里的 `127.0.0.1`。
- Redis：在 WSL VM 启动 `redis-server --bind 0.0.0.0 --port 6380 --protected-mode no`（仅本地测试缓存，无口令、非持久化、maxmemory 64mb），两个 Deployment 都通过 `172.18.0.1:6380` 连接；与 Windows 本机 Redis 隔离。
- ES / Kafka：集群版 api 采用 `traffic.query.engine=legacy`、`traffic.sync.enabled=false`，不依赖 ES/Kafka。**这是集群测试的范围边界**，如实记录。
- 跨服务：backend 的 `VEHICLE_MONITOR_BASE_URL=http://car-monit-api:9902`，走 K8s Service DNS；两端内部令牌由 Secret 注入同一值。
- 暴露：NodePort 30989 / 30902，从 WSL VM 访问 `172.18.0.2:<nodePort>`；服务间仍走 ClusterIP。
- 凭据：通过 `kubectl create secret generic --from-literal`（值仅来自进程环境变量）注入，清单与文档不含任何口令。

### 3.3 300Mi 预算（执行前预估）
Spring Boot 4 + 大 fat jar 默认会冲破 300Mi，初始方案为
`-Xms48m -Xmx112m -XX:MaxMetaspaceSize=72m -XX:ReservedCodeCacheSize=24m -XX:MaxDirectMemorySize=16m -Xss256k -XX:+UseSerialGC`。
**该预估在实机被证伪**，实际调优过程见第 6.2 节，最终参数见第 6.3 节。

### 3.4 副本与调度
- `replicas: 3`，`maxSurge: 1 / maxUnavailable: 0`，`podAntiAffinity` 用 `preferred`（尽量分散到 3 节点但不因节点不足而 Pending）。
- `readinessProbe` / `livenessProbe` 用 TCP，启动宽限期放大；`limits.cpu: 2000m` 避免单核限流拖慢冷启动。

## 4. 执行步骤

1. 停掉 Windows 本机 backend/api Java（9989/9902）。
2. WSL 启动 `redis-server :6380`；确认 `172.18.0.1:6380` 从 k3d 节点可达。
3. 构建 3 个本地镜像并 `k3d image import`。
4. 先起 1 副本验证能在 300Mi 内启动；再扩到 3 副本。
5. 接口验收。
6. 故障演练 A：`kubectl delete pod` 一个 api Pod → 立即重建。
7. 故障演练 B：`docker stop k3d-v3-agent-0` → 观察 NotReady、污点驱逐、其它节点新建 Pod；记录耗时。
8. 恢复节点，确认 3/3 稳定、无多余副本。
9. 清理测试负载，保留镜像/清单/脚本与文档供复现。

## 5. 验收清单（执行前定义）

| # | 用例 | 通过标准 |
| --- | --- | --- |
| 1 | `kubectl get deploy` | backend/api 均 `READY 3/3` |
| 2 | `crictl stats` | 单 Pod workingSet ≤ 300Mi，无 OOMKilled |
| 3 | `kubectl get pods -o wide` | 副本分布在多个节点 |
| 4 | backend `captchaImage` + `login` + 认证列表 | 200 |
| 5 | api `readiness`（403/200）、section/gantry 列表 | 200 |
| 6 | backend→api 跨服务 | 200 或按契约降级 |
| 7 | 连续 N 次请求 | NodePort 全部成功、Endpoints 为 3 |
| 8 | 删 Pod | 自动重建，副本回 3 |
| 9 | 停 agent 节点 | 节点 NotReady 后 k3s 补齐 3 副本 |
| 10 | 恢复节点 | 节点 Ready，Deployment 仍 3/3，总 Pod 数 6 |

## 6. 实机执行记录（如实，含失败）

### 6.1 环境与镜像
- 镜像实测大小：`car-monit-jre17:local` 782MB、`car-monit-backend:local` 981MB、`car-monit-api:local` 1.06GB；导入 3 个节点成功，节点内 `java -version` 确认可用。
- Windows 侧 9989/9902 的 Java 进程已停止；WSL `redis-server :6380` 启动后需加 `--protected-mode no`，否则外部连接被拒（第一次探测即踩到此坑）。
- 三个 k3d 节点 `Taints: <none>`，控制面可调度，故障演练时剩余 2 节点能容纳 6 个 Pod。

### 6.2 300Mi 调优过程（全部实测，不是推断）
用 `docker run --memory=300m --memory-swap=300m` 做单容器硬限迭代，再用 k8s 复验：

| 轮次 | 参数要点 | 结果 |
| --- | --- | --- |
| 1 | 初始方案 `-Xmx112m / MaxMetaspace=72m` | 两个服务都 `OutOfMemoryError: Metaspace`（fat jar 类太多） |
| 2 | `-Xmx88m / Metaspace=128m / Code=16m` | 稳态 ~290MiB，随后 cgroup `OOMKilled` |
| 3 | `-Xmx48m / Metaspace=112m / Code=8m / -Dsun.zip.disableMemoryMapping=true` | 稳态 273.7MiB 不 OOM，但请求 `Java heap space` OOM |
| 4 | `-Xmx64m / Metaspace=120m`，放宽到 400m 做 NMT 测量 | 启动成功、readiness 200；**NMT**：Java Heap 64MB、Class Metadata used 104.8MB、Class space 14.2MB、Code 10.5MB、71 线程栈 7.3MB、committed 合计 268MiB；`docker stats` 峰值 RSS **357MiB**（含 275MB fat jar 的文件页缓存） |
| 5 | `-Xmx56m / Metaspace=120m / Code=12m / lazy-init / root=WARN` | JDK 17 下 api 成功（稳态 282.2MiB，403/200/section 200）；backend 仍反复 `OOMKilled` |
| 6 | backend 去掉 p6spy 驱动（直连 `com.mysql.cj.jdbc.Driver`）、`ReservedCodeCache=4m` | 能启动并 captcha 200（279.8MiB），但 `CodeCache is full. Compiler has been disabled`，k8s 内冷启动 >150s 并被 OOMKilled |
| 7 | `-Xss192k` | 触发 `StackOverflowError` → `ExceptionInInitializerError` → `NoClassDefFoundError: io.netty.buffer.ByteBufAllocator`（Netty AdaptiveByteBufAllocator 递归初始化栈溢出）；加 `-Dio.netty.allocator.type=unpooled` 规避 |
| 8 | **换 JDK 25 + `-XX:+UseCompactObjectHeaders`（JEP 450）** | backend 在 300m 容器内 **31.9s 启动、captcha 200、稳态 287.3MiB、无 OOMKilled**；随后重建两个镜像为 JDK 25 运行时并重新 `k3d image import` |

其它真实踩坑：
- `docker/java.Dockerfile` 里没有字体，`/captchaImage` 在集群中返回业务 500：`Fontconfig head is null, check your fonts or fonts configuration`。基础镜像 `mysql:8.0.30` 既无 `fc-cache` 也无 TTF，Temurin JDK 25 也没有 `lib/fonts`。**未修复**（见 6.6 建议）。
- `spring.main.lazy-initialization=true` 是为压低启动峰值而启用的；`SysLoginService.login` 在 `code` 为空时跳过验证码校验，因此登录流程可以绕开字体问题，但**仍需要足够堆**。

### 6.3 最终清单参数
两个 Deployment 统一（backend 额外直连 MySQL 驱动、api 额外 `--add-opens`）：

```
-XX:+UseCompactObjectHeaders  -Xms20m -Xmx64m
-XX:MaxMetaspaceSize=136m -XX:CompressedClassSpaceSize=24m
-XX:ReservedCodeCacheSize=12m -XX:MaxDirectMemorySize=2m
-XX:MaxHeapFreeRatio=10 -XX:MinHeapFreeRatio=5 -Xss192k
-XX:CICompilerCount=2 -XX:+UseSerialGC -XX:-UsePerfData
-Dsun.zip.disableMemoryMapping=true -Djdk.nio.maxCachedBufferSize=65536
-Djava.util.concurrent.ForkJoinPool.common.parallelism=1
-Dio.netty.allocator.type=unpooled
--spring.main.lazy-initialization=true --logging.level.root=WARN
--server.tomcat.threads.max=2 --server.tomcat.max-connections=32
resources: requests/limits memory=300Mi, cpu limits=2000m
```

清单与脚本位于 `D:\work\runtime-logs\`：`manifests-final.yaml`、`step4-deploy.sh`、`step6-rebuild-jdk25.sh`、`step7-scale.sh`、`step8-fault.sh`、`step9-evidence.sh`（均不进仓库，凭据由环境变量注入）。

### 6.4 3 副本集群验收结果

| # | 用例 | 实测结果 |
| --- | --- | --- |
| 1 | `kubectl get deploy` | api **3/3**、backend **3/3**，`RESTARTS=0` |
| 2 | 每 Pod workingSet（crictl） | api 271 / 279 / 289 MiB；backend 259 / 262 / 263 MiB，**全部 ≤ 300Mi**，最终配置下无 OOMKilled |
| 3 | 分布 | api 分布在 server-0 / agent-0 / agent-1；backend 同样跨 3 节点 |
| 4 | Endpoints | 两个 Service 各 3 个 endpoint |
| 5 | api 门禁 | 无令牌 **403**，带令牌 **200** |
| 6 | api 数据 | `/base/section/list` 200 total=85；`/base/gantry/list` 200 total=1526；NodePort 连续 15 次全部 200 |
| 7 | backend `captchaImage` | **失败（业务 500 / 无响应）**：容器缺字体 + 300Mi 下堆不足，见 6.2 |
| 8 | backend 登录与认证列表 | **失败**：`TokenService.createToken` → fastjson2 序列化 `LoginUser` 时 `Java heap space`，Tomcat Acceptor 亦 OOM。**300Mi 下 backend 完整请求链路不可用**，这是本轮最重要的如实结论 |
| 9 | backend→api 跨服务 | 因 backend 登录不可用，**未完成**（未伪造结果） |

> 结论：**api 服务在 300Mi × 3 副本下完整可用；backend 服务能启动、能被调度与自愈，但在 300Mi 硬限制下无法完成登录等业务请求**。要获得完整功能，必须提高单 Pod 内存或显著瘦身（见 6.6）。

### 6.5 故障演练结果（k3s 自愈）

**A. 删除单个 Pod**
- `kubectl delete pod car-monit-api-d657dbcb8-n278v` 后，ReplicaSet 立即创建新 Pod（`car-monit-api-d657dbcb8-lcwrz`，创建时间 `12:00:53Z`），api 恢复 `3/3`。

**B. 停掉整个节点 `docker stop k3d-v3-agent-0`**
- 事件时间线（UTC）：`NodeNotReady`（约 12:05Z）→ `TaintManagerEviction`（约 12:09:4xZ，约 **5 分钟**，即默认 `default-not-ready-toleration-seconds=300`）→ 新 Pod `car-monit-api-...-vmp82` 与 `car-monit-backend-...-xlndl` 在 `12:09:47Z` 被创建，调度到仍存活的 `server-0` / `agent-1`。
- 节点停机期间两个 Deployment 始终保持 `3/3`、`Pending=0`；NodePort 请求未中断（api 持续 200）。
- **结论：k3s 会在节点故障后自动驱逐并在健康节点拉起新服务**；不是秒级，受 5 分钟污点容忍期约束。

**C. 恢复节点 `docker start k3d-v3-agent-0`**
- `NodeReady`、`NodeHasSufficientMemory` 等事件恢复；3 节点全 Ready。
- 最终 6 个 Pod（api 3 + backend 3）、两个 Deployment 均 `3/3`、总 Pod 数 **6**（没有出现多余副本），持续观察 4 分钟稳定。

### 6.6 偏差、根因与后续建议

1. **300Mi 是这两个 Spring Boot 4 fat jar 的极限甚至不足**：NMT 显示仅类元数据就 ~105MB，堆最小要 64MB，加上 CodeCache/线程/JVM 自身与 jar 文件页，实测完整功能需要约 350–360MiB。建议把 backend 的 limit 提到 **360Mi**（或至少 384Mi），api 保持 300Mi 时也应留更多余量。
2. **容器缺字体**：基础镜像是精简 Oracle Linux 8，无 fontconfig/TTF。建议改用带 `fontconfig + dejavu-sans-fonts` 的基础镜像，或把 TTF 与 `fontconfig.properties` 打进 `$JAVA_HOME/lib/fonts`。
3. **瘦身才是根本解**：移除未使用的 `ruoyi-generator` 等嵌套 jar、生成 AppCDS 归档（Spring Boot 4 支持 `-Dspring.context.exit=onRefresh` 训练 + `-XX:SharedArchiveFile`）共享类元数据，可把元空间与文件页显著降下来。
4. **不要用 192k 线程栈**：Netty 4.2 的 `AdaptiveByteBufAllocator` 会栈溢出；若保留小栈必须配 `-Dio.netty.allocator.type=unpooled`。
5. **不要用 4m CodeCache**：JIT 被禁用后冷启动从 ~32s 恶化到 >150s，反而更容易被探针/内存压垮。
6. **CI 的 `deploy-to-k3s` 只是 pause 占位**：如要让它真正验收 Java，应把本清单接入 `cd-standalone.yml` / `self-hosted-ci.yml`，并给 runner 准备外部 DB/Redis 或引入 testcontainers。
7. ES/Kafka 未接入集群（Windows 端口不可达），集群测试使用 `engine=legacy` + `sync.enabled=false`；这是范围边界，不是功能结论。

### 6.7 现场清理与复现
- 演练结束后删除 `car-monit-api` / `car-monit-backend` 的 Deployment、Service、Secret，并停止 WSL 的 `redis-server :6380`，释放约 1.8Gi 内存；镜像、`manifests-final.yaml` 与全部脚本保留，可随时 `kubectl apply` 复现。
- 复现顺序：`step6-rebuild-jdk25.sh` → `step4-deploy.sh`（注入 4 个环境变量与 `WSLENV`）→ `step7-scale.sh` → `step8-fault.sh`。
- 本文档记录的是**实测**，未把未通过的项目写成通过；backend 功能降级与 k3s 自愈成功是两件独立的事实。
