# k3s 集群修复方案规划（对应 k3s-cluster-verification.md §6.6）

> 本文是**规划**，不是执行记录。执行前基线探测于 2026-11-14 完成；执行阶段另写记录。
> 约束（用户给定）：Java Pod 内存上限 **400M**；WSL 可按实际内存占用提高上限；Windows Redis 迁到 WSL 并装**最新稳定版**，支持**单节点**与**6 节点 Cluster**两种模式；**ES / Kafka 本期不接入**。

## 0. 基线事实（实测，非假设）

| 项 | 实测值 | 来源 |
| --- | --- | --- |
| WSL 发行版 | openEuler 24.03 LTS-SP4，systemd `running`（PID 1 = systemd），gcc 12.3.1 / make 4.4.1 / tcl 8.6.17 / fontconfig 2.15.0 已装 | `cat /etc/os-release`、`rpm -q` |
| `.wslconfig` | `memory=4GB`、`swap=2GB`、`processors=2`、`swapFile=D:\wsl\swap\swap.vhdx`、`localhostForwarding=true`、`vmIdleTimeout=3600000`、`instanceIdleTimeout=-1` | `%USERPROFILE%\.wslconfig` |
| WSL 内存现状 | total 3.8Gi / used 1.3Gi / available 2.5Gi；**swap 已用 1.0Gi / 2.0Gi**（说明 4GB 已发生换页）；`nproc=2` | `free -h` |
| Windows 宿主 | 13.84Gi 总内存、**1.31Gi 空闲**；12 逻辑 CPU | CIM |
| Windows 进程 | ES 9200 java 491MB、Kafka 9092 java 359MB、Redis 6379 49MB；9989/9902 两个 Java 已停 | `Get-NetTCPConnection` / `Get-Process` |
| Windows Redis | `Redis server v=8.10.2`（`D:\work\Redis-8.10.2-Windows-x64-msys2`），仅监听 127.0.0.1:6379 | `redis-server --version` |
| WSL 现有 Redis | 系统自带 **7.2.16**（旧），`:6380` 临时实例已停 | `redis-server --version` |
| **Redis 最新稳定版** | **8.10.3**（GitHub `redis/redis` latest release tag `8.10.3`，2026-10-26；`download.redis.io/releases/` 索引最高 `redis-8.10.3.tar.gz`） | 官方 API + 官方下载索引 |
| DB 容器 | `mysql_wsl` / `opengauss` 运行，`docker inspect HostConfig.Memory=0`（**无内存上限**） | `docker inspect` |
| k3d | `v3` 1 server + 2 agents，三个 k3d 节点容器同样无内存上限；CI 的 `v3-ci-probe` / `v3-api-ci-probe` 仍是 pause 占位 | `docker inspect` / `kubectl get pods -A` |
| 磁盘 | WSL `/` 1007G，可用 921G | `df -h` |
| 应用 Redis 配置 | 两端 yml 都是 `spring.data.redis.host/port=127.0.0.1:6379` + lettuce pool；api **另有** `rediscluster.clusterNodes`（默认 `${REDISCLUSTER_CLUSTERNODES:...}`），由 `RedisSourceFactory` 用 `JedisCluster` 按逗号分隔 host:port 解析 | 源码 |

## 1. 目标与验收标准

| 编号 | 目标 | 验收标准 |
| --- | --- | --- |
| G1 | Java Pod 上限 400M 且**功能完整** | `limits.memory`=目标值；`crictl stats` 单 Pod workingSet ≤ 上限、无 OOMKilled；backend **captcha + 登录 + 认证列表 + 跨服务**全部 200；api 门禁/列表 200 |
| G2 | WSL 容量按实测提升 | `.wslconfig` 调整后 `free -h` / `nproc` 符合预期，swap 不再持续增长，Windows 空闲 ≥ 2Gi |
| G3 | Redis 迁移到 WSL 并升级到 8.10.3 | `redis-server --version` = 8.10.3；Windows 6379 下线；两端应用全部通过 WSL Redis 完成验证码/令牌读写 |
| G4 | Redis 单节点 / 6 节点 Cluster 可切换 | 两套配置与一键切换脚本；Cluster `CLUSTER INFO` = `cluster_state:ok`、3 主 3 从、`CLUSTER NODES` 可跨槽读写；切换后应用回归通过 |
| G5 | 字体/栈/CodeCache 等 6.6 根因消除 | `/captchaImage` 返回 uuid+img；Netty 不再栈溢出；JIT 不被禁用；`logging.level.root` 可恢复到 INFO |
| G6 | 故障自愈与 CI 接入 | 删 Pod / 停节点后 3/3 恢复；CI `deploy-to-k3s` 至少把 pause 占位替换为真实 Java 或新增 Java smoke job |
| G7 | ES/Kafka 不接入 | 集群侧 `traffic.query.engine=legacy`、`traffic.sync.enabled=false`，不配置 `spring.kafka` / ES 地址；ES/Kafka 进程与数据保持不动（可按需临时停用释放内存，但**不改配置、不删数据**） |

### 1.1 「400M」的单位决策（自主决策，记录备查）
- K8s `400M` = 400,000,000 B ≈ **381.5Mi**；`400Mi` = 419,430,400 B ≈ **419MB**。
- 上一轮用的是 `300Mi`，为保持单位一致并给 backend 登录链路留出余量，**采用 `400Mi`**（约 419MB，属于「上限 400M」的宽松口径）。
- 若必须严格不超过 400,000,000 B，改用 `400M` 并把第 4.2 节的 JVM 预算再压 20Mi（优先降 `-Xmx` 96→80m、CodeCache 32→24m）；两种取值都在清单里留成变量 `POD_MEM_LIMIT`，切换只改一处。
- **决策点**：本规划默认 `400Mi`；执行时若实测 workingSet 长期 < 360Mi，再收紧到 `400M`。

## 2. 内存预算（先算后改，避免 Windows 被拖垮）

WSL2 的 `memory=` 是**上限而非预占**，但 WSL 内 workload 会真实占用宿主内存，因此按峰值算：

| 负载 | 估算常驻 | 说明 |
| --- | --- | --- |
| 6 × Java Pod @400Mi | ≈ 2.1–2.4 Gi | 实测 300Mi 时 workingSet 259–289Mi；400Mi 下预计 320–360Mi |
| k3d 3 节点（k3s/containerd/pause） | ≈ 0.5 Gi | 控制面 ~0.25Gi，两 agent 各 ~0.12Gi |
| `mysql_wsl` | ≤ 1.0 Gi | 需补 `--memory=1g`（当前无限制） |
| `opengauss` | ≤ 1.5 Gi | 需补 `--memory=1500m`（当前无限制） |
| Redis 单节点 | ≈ 0.1 Gi | `maxmemory 256mb`，实际远低 |
| Redis 6 节点 Cluster | ≈ 0.6 Gi | 每节点 `maxmemory 64mb` + ~30MB 开销 |
| WSL OS / dockerd / 页缓存 | ≈ 0.6 Gi | |
| **合计峰值** | **≈ 5.5–6.3 Gi** | Cluster 模式取上限 |

Windows 侧：`13.84Gi − WSL 6.3Gi − ES 0.49Gi − Kafka 0.36Gi − Windows Redis 0.05Gi(迁走后为 0) − OS/IDE ≈ 3Gi` → 约 **3.7–4.2Gi 空闲**，满足 G2。

**建议容量**：`.wslconfig` → `memory=8GB`（上限，留 1.7Gi 突发余量）、`swap=4GB`、`processors=4`（宿主 12 逻辑 CPU，给 6 个 Java 冷启动并行度）、`swapFile` 路径不变；`localhostForwarding=true` 保持（Windows 可用 `127.0.0.1:6379` 访问 WSL Redis）。
**分级回退**：若改后 Windows 空闲 < 2Gi，先降到 `memory=7GB`，再降到 `6GB`；不要一次性给 10GB。

## 3. 修复项逐条方案（对应 §6.6 的 7 条建议）

### R1　单 Pod 400Mi + JVM 参数回归「可运维」
- 清单 `resources.requests/limits.memory: 400Mi`（变量化），`limits.cpu: 2000m` 保持。
- **不再需要极限压缩**：JDK 25 + `-XX:+UseCompactObjectHeaders` 保留（JEP 450，实测 31.9s 冷启动），但把上一轮为 300Mi 做的所有 hack 逐条评估：

| 参数 | 300Mi 值 | 400Mi 建议 | 理由 |
| --- | --- | --- | --- |
| `-Xms/-Xmx` | 20m/64m | **64m/96m** | 登录时 fastjson2 序列化 `LoginUser` 需要更多堆；96m 是 300Mi 下 OOM 的 64m 与 400Mi 预算的折中 |
| `MaxMetaspaceSize` | 136m | **144m** | 实测元数据 ~105MB + 类空间 ~14MB，留 25MB 余量 |
| `CompressedClassSpaceSize` | 24m | **24m** | JDK 25 下 12m 会 OOM，24m 实测可用 |
| `ReservedCodeCacheSize` | 12m（曾 4m） | **32m** | 4m 导致 `CodeCache is full / Compiler disabled`，冷启动 >150s |
| `MaxDirectMemorySize` | 2m | **16m** | 2m 会波及 Netty/Lettuce 直接缓冲 |
| `-Xss` | 192k | **512k** | 192k 触发 `AdaptiveByteBufAllocator` 栈溢出 |
| `-Dio.netty.allocator.type=unpooled` | 强制 | **去掉** | 栈恢复后用回默认池化分配器 |
| `-Dsun.zip.disableMemoryMapping=true` | 强制 | **去掉后实测** | 400Mi 有 file-cache 余量；若 workingSet 偏高再启用 |
| `spring.main.lazy-initialization` | true | **先关掉** | 避免懒加载导致的注入异常/首次请求尖峰；用 400Mi 预算验证 |
| `logging.level.root` | WARN | **INFO** | 恢复可观测性；若 INFO 下 heap 抖动大，降到 `INFO` + 关闭 p6spy/DEBUG 包 |
| Tomcat `threads.max=2`、`max-connections=32` | 强制 | **放宽到 8 / 200** | 恢复正常并发；探针与业务不再抢连接 |

- **预调优方法**：先在 `500Mi` 下用 `-XX:NativeMemoryTracking=summary` + `jcmd VM.native_memory summary` 量出 400Mi 下各区 committed，再按表压回 400Mi；不要直接凭感觉填数。
- **探针**：TCP 探针在 Tomcat 端口绑定期会误报 Ready（上一轮踩过）。方案 A（不改代码）：仍用 TCP 但 `initialDelaySeconds` 按实测冷启动时间 ×1.5（约 60–90s）、`failureThreshold` 放大；方案 B（推荐，小改动需复核）：引入 `spring-boot-starter-actuator` 或新增无鉴权 `GET /health`，改用 `httpGet` + `successThreshold`，并在 readiness 里覆盖 DB/Redis 依赖。本规划把 B 列为 P6 的代码项，A 作为 P4 临时方案。

### R2　WSL 容量上限（G2）
1. 备份 `%USERPROFILE%\.wslconfig` → `D:\work\runtime-logs\dot-wslconfig.bak`。
2. 先做**释放动作**（可选，取决于执行时 Windows 空闲）：ES/Kafka 只是「不接入集群」，如需腾内存可临时 `Stop-Process`，**保留 `config/` 与 `data/`，不删数据、不改配置**；Windows Redis 在 P3 正式下线。
3. 改 `memory=8GB / swap=4GB / processors=4`；`wsl --shutdown` 使配置生效。
4. 重启顺序：dockerd → `mysql_wsl`（补 `--memory=1g`）→ `opengauss`（补 `--memory=1500m`，数据在 `/srv/oracle/oradata`）→ `k3d cluster start v3` → 确认 3 节点 Ready。
5. 验证 `free -h`（total ≈ 8Gi、swap used 不增长）、`nproc=4`、Windows 空闲 ≥ 2Gi；不满足按 §2 分级回退。

### R3　Windows Redis → WSL Redis 8.10.3（G3）
**安装（离线可完成）**
- 下载 `https://download.redis.io/releases/redis-8.10.3.tar.gz`，与官方 GitHub Release 的 SHA256 / 发布说明核对（校验步骤不可跳过）。
- WSL 内 `make -j4 MALLOC=jemalloc BUILD_TLS=no`（jemalloc 随源码 deps 自带；gcc/make/tcl 已具备），`make test`（tcl 已装，可选）→ `make install PREFIX=/opt/redis-8.10.3`，软链到 `/usr/local/bin`。
- 目录：`/srv/redis/{bin,etc,data,logs,run}`；凭据只由环境注入（systemd `EnvironmentFile=/etc/carmonit/redis.env`，权限 600），配置与文档不含口令。
- systemd unit `redis-single.service` / `redis-cluster@.service`（模板），`Restart=always`，`LimitNOFILE=65535`；WSL systemd 已 running，可直接 `systemctl enable --now`。

**单节点模式（默认）**
- 端口 `6379`，`bind 127.0.0.1 172.18.0.1`（Windows 经 localhostForwarding 走 127.0.0.1；k3d Pod 走 172.18.0.1），`protected-mode yes` + `requirepass`（注入），`appendonly yes`，`maxmemory 256mb` + `allkeys-lru`，`save 900 1`。
- 应用侧：两端 `SPRING_DATA_REDIS_HOST=172.18.0.1`、`SPRING_DATA_REDIS_PORT=6379`、`SPRING_DATA_REDIS_PASSWORD`（Secret 注入）；api 的 `REDISCLUSTER_CLUSTERNODES` 单节点模式下保持不配置或指向单节点（见 R5 风险）。

**6 节点 Cluster 模式（可切换）**
- 端口 `7000–7005`，3 主 3 从；每节点独立 `dir`，`cluster-enabled yes`、`cluster-config-file nodes-<port>.conf`、`cluster-node-timeout 5000`、`appendonly yes`、`maxmemory 64mb`。
- **关键**：`cluster-announce-ip 172.18.0.1`、`cluster-announce-port <port>`、`cluster-announce-bus-port 1<port>`（如 17000），否则集群向 k3d Pod 广播 `127.0.0.1` 导致 `MOVED` 后连不上。
- 创建：`redis-cli --cluster create 172.18.0.1:7000 ... :7005 --cluster-replicas 1 --cluster-yes`；验证 `CLUSTER INFO`、`CLUSTER NODES`（3 master / 3 slave）、`redis-cli -c` 跨槽 `SET/GET`。
- 切换脚本 `switch-redis-mode.sh single|cluster`：启停对应 unit、改 K8s Secret（`SPRING_DATA_REDIS_CLUSTER_NODES` / 单节点 host:port）、滚动重启两个 Deployment（`kubectl rollout restart`），并跑回归用例。

**迁移与回滚**
- Windows Redis 先 `BGSAVE`，把 `dump.rdb` 复制到 `/srv/redis/data`，WSL 启动后核对 `DBSIZE` 与 `captcha_codes:*` 抽样；验证码/令牌本身短 TTL，也可选择「零数据切换」（需在文档注明选择）。
- Windows 侧：`redis-cli -h 127.0.0.1 -p 6379 shutdown nosave` → 停进程；**保留 `D:\work\Redis-8.10.2-Windows-x64-msys2` 整个目录作回滚源**（不删 data）。
- 回滚：启动 Windows Redis 8.10.2 → 应用 Secret 指回 `127.0.0.1:6379`（Windows 本机验证时）或保留 WSL 单节点。

### R4　字体与验证码（对应 §6.6-2）
`mysql:8.0.30` 基础镜像无 `fc-cache`/TTF，Temurin JDK 25 无 `lib/fonts`，导致 `Fontconfig head is null`。两条路线，优先 A：
- **A（无外网、无需改代码）**：把 WSL 的 `DejaVuSans.ttf` 拷进镜像 `$JAVA_HOME/lib/fonts/`，并写 `$JAVA_HOME/lib/fontconfig.properties` 把 `allfonts.*` 全部映射到该文件（Java 在无 native fontconfig 时读这个 properties）；镜像内验证 `java -cp ...` 能列出字体，再验 `/captchaImage` 返回 `uuid`+`img`。
- **B（需要网络/额外镜像）**：构建阶段 `dnf install -y fontconfig dejavu-sans-fonts`；或从本机 `oracle_11g` 镜像（自带 `fc-list` + `libfontconfig.so.1`，glibc 2.17 兼容 OL8 的 2.28）拷贝 `/usr/lib64/libfontconfig.so.1`、`/etc/fonts`、字体文件，并补齐 `libfreetype/libexpat` 依赖。
- **C（代码改动，最后手段）**：验证码生成改用 `Font.createFont(TRUETYPE_FONT, <classpath TTF>)`，绕开逻辑字体与系统 fontconfig；需要独立复核 + CI。
- 验收：集群内 `/captchaImage` 200 且返回 `uuid`、`img`；`login` 用该 uuid 的验证码能成功。

### R5　Cluster 模式的应用侧兼容性（**必须先查，否则 G4 会失败**）
api 存在**两条独立 Redis 访问路径**，切换 Cluster 前必须逐条验证：
1. `spring.data.redis.*` → Boot 4 自动配置 `RedisConnectionFactory` → `RedisConfiguration` 的 `RedisTemplate` / `CacheManager` / `RetRedisCacheWriter`。设 `SPRING_DATA_REDIS_CLUSTER_NODES=172.18.0.1:7000,...` 会自动切到 cluster 模式；注意**不要同时保留 `spring.data.redis.host/port`**（避免配置歧义），并确认 Lettuce 集群连接在当前 Spring Data Redis 4.1.2 下可用。
2. `rediscluster.clusterNodes`（`${REDISCLUSTER_CLUSTERNODES:...}`）→ `RedisSourceFactory` 用 `JedisCluster`（逗号分隔 `host:port`）→ `SysUtilServiceImpl` 的车辆缓存读写。Cluster 模式必须把 6 个节点全部列上，且 `Jedis 4.4.8` 与 Redis 8.10 协议兼容需实测。
3. **已知风险**：`RetRedisCacheWriter.clean()/clear()/remove()` 使用 `connection.keys(pattern)`；Cluster 模式下 `KEYS` 只查单节点、Lettuce `RedisClusterConnection` 甚至可能不支持。计划：Cluster 模式回归时专门覆盖「按前缀清理缓存」用例；若失败，改为遍历 master 做 `SCAN`，或将该能力限定在单节点模式并文档化。
4. 多 key / Lua / `KEYS` 的跨槽问题：检查 `RedisCache`、`RedisTemplate` 的批量操作是否带 hash tag；不带则在 cluster 模式下会 `CROSSSLOT`，需回归用例覆盖验证码、令牌、灰度开关、导出任务元数据。
5. **模式切换验收矩阵**：单节点 / Cluster 两种模式下都跑 `captchaImage → login → getInfo/getRouters → 分页列表 → 跨服务导出提交 → 前缀缓存清理`。

### R6　CI 接入真实 Java（对应 §6.6-6）
- `self-hosted-ci.yml` 现有 `deploy-to-k3s` 部署的是 `rancher/mirrored-pause:3.6`；规划二选一（建议先做 a，低风险）：
  - a) 新增 `java-smoke` job：用本规划的镜像与 400Mi 清单起 1 副本，`httpGet /captchaImage` 与 `/api/v3/es/readiness` 断言 200/403，跑完清理；不改现有 pause 演示。
  - b) 把 `cd-standalone.yml` / `self-hosted-ci.yml` 的 workload 替换为真实 Deployment（需要 runner 侧 DB/Redis 稳定可达，且 CI 耗时增加）。
- CI 的 JDK 版本与镜像 tag 固定、镜像构建产物用 `k3d image import`；清单不含凭据，CI Secret 注入。
- 代码改动（actuator/health、缓存 SCAN、验证码字体）走「独立只读复核 → push → 跟进 CI」门禁。

### R7　ES / Kafka 明确不接入（G7）
- 集群侧保持 `traffic.query.engine=legacy`、`traffic.sync.enabled=false`；不设置 `SPRING_ELASTICSEARCH_*` / `SPRING_KAFKA_BOOTSTRAP_SERVERS`（或保持 yml 默认 localhost 但不放行网络）。
- Windows 上 ES 9200 / Kafka 9092 **不改动配置、不删数据**；仅在 §2 容量不足时临时停进程，恢复用原启动命令（堆已限制 512m）。
- 后续接入另立阶段：WSL 内起 ES/Kafka（或把 Windows 端口通过 `localhostForwarding` + `0.0.0.0` 绑定暴露给 172.18.0.1），再切 `engine=es` / `sync.enabled=true`，并补 `search-sync` 端到端用例。

### R8　长期瘦身（不阻塞本次）
AppCDS：Boot 4 支持 `-Dspring.context.exit=onRefresh` 训练 + `-XX:ArchiveClassesAtExit` / `-XX:SharedArchiveFile` 共享类元数据；裁剪 `ruoyi-generator` 等未使用嵌套 jar；评估 GraalVM native image。目标是把 400Mi 上限降到 256Mi 且不影响功能。

## 4. 分阶段执行计划（含停机顺序）

| 阶段 | 动作 | 前置 / 风险 |
| --- | --- | --- |
| P0 基线备份 | 备份 `.wslconfig`、Windows Redis `dump.rdb`、现有 `manifests-final.yaml`/脚本、`docker inspect` 输出；记录当前版本与端口 | 只读，不改环境 |
| P1 WSL 扩容 | 改 `.wslconfig` → `wsl --shutdown` → 按顺序拉起 docker / DB（补内存上限）/ k3d | **会中断 WSL 内所有服务**，需先确认 Windows 侧无正在跑的联调；`opengauss` 数据在 `/srv/oracle/oradata`，不可重建 |
| P2 Redis 8.10.3 单节点 | 源码编译 → systemd unit → 单节点 6379 起服 → Windows/k3d 双向连通与口令校验 | 校验官方 SHA256；`make test` 可选 |
| P3 迁移切换 | Windows Redis `BGSAVE` → RDB 导入 → 停 Windows Redis → 应用 Secret 指向 WSL → 单节点模式全量回归 | 保留 Windows Redis 目录作回滚源 |
| P4 Java Pod 400Mi | 改清单/JVM → 加字体层重建镜像 → `k3d image import` → 1 副本完整接口验收（含登录/验证码/跨服务）→ NMT 量内存 → 3+3 扩容 | 若 400Mi 仍不足，按 §1.1 决策或上报，不擅自超限 |
| P5 6 节点 Cluster | 起 7000–7005 → `--cluster create --replicas 1` → 应用切 cluster 配置 → R5 兼容矩阵 → 主从故障转移（停 1 master 观察提升）→ 切回单节点验证可回退 | R5 的 `KEYS`/跨槽风险是最大不确定项 |
| P6 故障演练 & CI | 删 Pod、停 agent 节点、恢复节点；接入 CI smoke job；复核后 push 并跟进 CI | 代码改动必须过独立复核门禁 |
| P7 收尾 | 汇总实测、更新 `k3s-cluster-verification.md` 的「遗留项」为「已闭环」，记录最终内存/耗时/版本 | 文档如实写未通过项 |

## 5. 验收清单（执行阶段逐条打勾）

1. `redis-server --version` = **8.10.3**；Windows 6379 不再监听；`redis-cli -h 172.18.0.1 -p 6379 PING` = PONG。
2. 单节点：`DBSIZE` 与迁移前一致（或明确选择零数据切换）；两端应用验证码/令牌读写正常。
3. Cluster：`CLUSTER INFO` = ok、3 主 3 从；`redis-cli -c` 跨槽 SET/GET；停 1 主后副本自动提升；应用 R5 矩阵全绿。
4. `kubectl get deploy` = api/backend 3/3，`RESTARTS=0`；`crictl stats` 单 Pod workingSet ≤ 400Mi。
5. backend：`captchaImage` 200（有 uuid/img）→ `login` 200（token）→ `getInfo/getRouters`、分页列表、`/monitor/server`、Excel 导出全部 200。
6. api：无令牌 403 / 带令牌 200、`section`/`gantry`/`snapshotflow` 列表 200。
7. 跨服务：backend `/manager/bigScreen/export/display` 返回 taskId；`topTen` 有 `X-Data-Source` 且按契约降级。
8. 冷启动时间、`CodeCache is full`、`StackOverflowError`、OOMKilled 均为 0；`logging.level.root=INFO` 下仍稳定。
9. 故障演练：删 Pod 立即重建；停节点约 5 分钟污点驱逐后 3/3 恢复；恢复节点总 Pod 数仍为 6。
10. ES/Kafka 未接入：无相关环境变量、无 `engine=es`、无 `sync.enabled=true`。

## 6. 风险与回滚

| 风险 | 触发点 | 缓解 / 回滚 |
| --- | --- | --- |
| `wsl --shutdown` 打断所有容器 | P1 | 先停 Windows 侧联调；按固定顺序拉起；DB 数据目录只读挂载、不重建 |
| WSL 内存升高拖垮 Windows | P1/P4 | 分级回退 8→7→6GB；Windows 空闲 < 2Gi 时暂停扩容，先停 ES/Kafka |
| Redis 8.10 源码编译失败 | P2 | `MALLOC=libc` 重试；`dnf install redis`(7.2.16) 仅作兜底并明确标注偏离「最新稳定版」 |
| Cluster 广播 127.0.0.1 | P5 | 强制 `cluster-announce-ip 172.18.0.1` |
| `KEYS`/跨槽导致缓存清理失败 | P5 | R5 用例先行；失败则单节点模式为准，Cluster 仅用于验证，不切生产默认 |
| 400Mi 仍不够 backend 登录 | P4 | 先用 500Mi 做 NMT 定位，再压参数；仍不足则上报，不擅自超上限 |
| 字体方案 A 无效 | P4 | 依次回退到 B、C；C 需要代码复核与 CI |
| 凭据泄漏 | 全程 | `redis.env` / K8s Secret / 脚本环境变量注入；文档与清单只写占位符；日志不打印 |

**统一回滚**：`.wslconfig.bak` 还原 → 启动 Windows Redis 8.10.2 → 应用 Secret 指回原地址 → `kubectl rollout undo`/删除新 Deployment → 镜像 tag 保留旧版不覆盖。

## 7. 本期不做（边界）

- ES / Kafka 接入集群（含 `engine=es`、Kafka `search-sync` 消费者、ILM/模板回灌）。
- AppCDS / 裁剪嵌套 jar / native image（列为 R8 长期项）。
- 修改 `pr.yml` / `master.yml` 的 GitHub 托管流水线触发分支（托管 runner 账单受限，口径已在 `springboot4-migration.md` §9.1 书面确认）。
- 任何未经过独立只读复核的代码 push。
