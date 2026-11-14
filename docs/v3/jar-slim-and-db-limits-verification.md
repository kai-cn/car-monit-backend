# jar 瘦身 / 镜像减重 / ERROR 日志 / DB 内存上限实测记录

> 日期：2026-11-14　本文是 `k3s-remediation-plan.md` 中 §6.6-3「瘦身才是根本解」的**执行记录**。
> 约束：Java Pod 上限 400M、日志仅 ERROR、MySQL8 与 openGauss 内存上限 ≤500M 且按实测确定、ES/Kafka 不接入。

## 1. 基线（执行前实测）

| 项 | 数值 |
| --- | --- |
| fat jar | `api.jar` 275,304,862 B（BOOT-INF/lib 261.4MB / classes 2.3MB，330 个嵌套 jar）；`backend.jar` 199,749,333 B（libs 189.7MB / classes 0.9MB，340 个） |
| 镜像 | `car-monit-api:local` 1.04GB、`car-monit-backend:local` 965MB；基础层 `mysql:8.0.30` 449MB + Linux JDK 25 303MB |
| DB 容器 | `mysql_wsl` / `opengauss` 的 `HostConfig.Memory=0`（无上限）；空载 RSS 59.59MiB / 109MiB |
| 日志 | api `logback-spring.xml` root=INFO、MyBatis TRACE、yml `logging.level.web=DEBUG` + `StdOutImpl`；backend `logback.xml` root=info、`com.ruoyi=debug`、yml `com.ruoyi: debug`；p6spy `StdoutLogger` 直写 stdout，绕过日志级别 |

## 2. 瘦身手段与结果

### 2.1 fat jar（改 Maven 打包配置，不是删 jar 里的文件）
- **api**：`spring-boot-maven-plugin` 增加 `excludeGroupIds=org.apache.flink`。
  实测发现 `VehicleTrackFlinkJob` 的 21 个 `flink-*` 依赖虽为 `provided`，但 **Boot repackage 默认会把 provided 打进 `BOOT-INF/lib`**（约 50MB）；Job 由 `flink run` 提交到集群，运行时不需要。
  另用 10 条 `<excludes>` 按 classifier 去掉 macOS / Windows / aarch64 的 Netty native 包，只保留 `linux-x86_64`。
- **backend**：`excludeGroupIds=org.apache.calcite,org.apache.groovy,com.aliyun.mns`——三者代码引用数均为 0，分表开关默认关闭、阿里云 MNS 通道未启用；合计约 21MB。排除后通过启动 + 分页 / 导出接口回归确认无类缺失。

| jar | 前 | 后 | 减幅 | 嵌套 jar 数 |
| --- | --- | --- | --- | --- |
| api | 275,304,862 | **211,030,709 B** | **−64.3MB / −23.3%** | 330 → 297（`flink=0`、`foreign-native=0`） |
| backend | 199,749,333 | **178,301,071 B** | **−21.4MB / −10.7%** | 340 → 336 |

### 2.2 镜像（jlink + 扁平化系统层）
- `jdeps` 全量分析 523 个嵌套 jar 太慢且不稳定，改用**保守模块集** `jlink --strip-debug --no-man-pages --no-header-files --compress=zip-9` 生成自定义 runtime：**66MB**（原完整 JDK 303MB）。首版漏了 `jdk.net`，Lettuce 启动时报 `ClassNotFoundException: jdk.net.ExtendedSocketOptions`，补上后解决。
- 系统层：起临时容器删掉 `mysql:8.0.30` 里的 MySQL Server 文件后 `docker export | docker import` 拍平，得到 `car-monit-sys:local` **255MB**（原 449MB）。这一步是必要的——单纯 `RUN rm` 只会加白障层，不减少镜像体积。
- 字体：为修复验证码 `Fontconfig head is null`，从本机 `oracle_11g` 镜像（glibc 2.17，兼容 OL8 2.28）复制**真实 .so 文件**（不是符号链接）：`libfontconfig.so.1`、`libfreetype.so.6`、完整 `/etc/fonts`、`fc-cache/fc-list`，并把 WSL 的 `DejaVuSans.ttf` 放入 `/usr/share/fonts/dejavu/`，构建期 `fc-cache -f`。`fc-list` 能看到 `DejaVu Sans`，集群内 `/captchaImage` 已返回 uuid+img。
  - 中途两次失败已记录：只写 `$JAVA_HOME/lib/fontconfig.properties` 会因缺 `getInitELC` 所需键抛 NPE；只拷 `.so` 符号链接会导致库找不到，回退成 `Fontconfig head is null`。

| 镜像 | 前 | 后 | 减幅 |
| --- | --- | --- | --- |
| api | 1.04GB | **537MB** | **−48%** |
| backend | 965MB | **504MB** | **−48%** |

## 3. 日志级别统一为 ERROR

| 位置 | 改动 |
| --- | --- |
| api `logback-spring.xml` | root/MyBatis 四个 logger 全部 ERROR，加 `NopStatusListener` 抑制 logback 自身状态输出 |
| api `application.yml` | `logging.level.root=${LOG_ROOT_LEVEL:error}`、`web: error`；MyBatis `log-impl` 改 `NoLoggingImpl`；`forest.logEnabled=false`；`spring.datasource.dynamic.p6spy=${P6SPY_ENABLED:false}` |
| api `spy.properties` | appender 从 `StdoutLogger` 改 `Slf4JLogger`，使 SQL 日志受日志级别约束 |
| backend `logback.xml` | root、`com.ruoyi`、`TraceIdFilter`、`SqlLogInterceptor`、`org.springframework`、`org.mybatis`、`druid`、`sys-user` 全部 error，加 `NopStatusListener` |
| backend `application.yml` | `logging.level.root/com.ruoyi/org.springframework/org.mybatis/druid` 全部 error；`forest.logEnabled=false` |
| backend `spy.properties` | appender 改 `Slf4JLogger` |
| `manifests-final.yaml` | `--logging.level.root=ERROR` |

**踩坑**：第一次在 XML 注释里写了 `--logging.level.root`，触发 `The string "--" is not permitted within comments`，Logback 初始化失败导致两个容器直接退出；已改为不含 `--` 的措辞并用脚本扫描两个 XML 的所有注释块确认无残留。

**实测**：新 Pod 日志 api 24 行 / 2 条 ERROR / **0 条非 ERROR 业务日志**；backend 16 行 / 0 条 ERROR / 0 条非 ERROR 业务日志，仅剩 3 条 logback 内部 `|-WARN`（历史 `SizeAndTimeBasedFNATP` 弃用告警，非业务日志）与 1 条 JVM `CompressedClassSpaceSize adjusted` 提示（清单已把该值改为 32m 消除）。

## 4. DB 内存上限测定（用户要求「按实测」）

用 400m 容器 + 真实查询负载（api `gantry/section` 列表 + backend 用户列表，30 次采样 @1s）：

| 容器 | 空载 | **实测峰值** | 500m 硬限下回归 | 最终上限 | 上限后占用 |
| --- | --- | --- | --- | --- | --- |
| `mysql_wsl` | 59.59MiB | **32.02MiB** | 200 | **256m**（峰值+96MiB 余量，下限 256m） | 32.08MiB / 256MiB |
| `opengauss` | 109MiB | **81.02MiB** | 200 | **256m**（同上） | 80.71MiB / 256MiB |

- 先统一压到 **500m**（`docker update --memory=500m --memory-swap=500m`）验证接口仍 200、无 OOMKilled；再按「峰值 + 96MiB 余量、不低于 256m、不超过 500m」收紧到 **256m**，回归 `api gantry/section`、`backend user list` 全 200、`OOMKilled=false`。
- **两者都远低于用户给的 500M 上限**；取 256m 是给冷启动/DDL/备份留余量后的最小稳定值。
- `docker update` 只对运行中的容器生效；脚本 `D:\work\runtime-logs\set-db-memory-limits.sh` 固化了这两个值，容器若重建必须带 `--memory=256m --memory-swap=256m`（文档同步记录）。

## 5. 400Mi Pod 集群实机验收

清单 `manifests-final.yaml`：`:slim` 镜像、`requests/limits.memory=400Mi`、JVM 参数由 300Mi 极限配置放宽为
`-Xms32m -Xmx96m / MaxMetaspace=144m / ClassSpace=32m / CodeCache=32m / Direct=16m / -Xss512k / SerialGC`，
保留 JDK 25 `-XX:+UseCompactObjectHeaders`、`lazy-initialization`，Tomcat 并发放宽到 8 线程 / 200 连接，去掉 `-Dio.netty.allocator.type=unpooled` 等 300Mi hack。

| 用例 | 结果 |
| --- | --- |
| 400m 容器冒烟（docker） | api 350.3MiB、backend 318.9MiB，均 `oom=false`；`captchaImage` 返回 img |
| 完整验证码登录（docker） | captcha uuid+img → Redis 取答案 → `login` 200（token 184 字符） |
| 认证接口（docker） | `getInfo` / `getRouters` / `system/user/list` / `manager/carinfo/list` / `monitor/server` / `carinfo/export` 全 200 |
| 跨服务（docker） | `export/display` 200 + taskId |
| k3s 3+3 副本 | 6 个 Pod 全 `1/1 Running`、`RESTARTS=0`，分布在 3 个节点 |
| Pod workingSet | api 311–336MiB、backend 283–338MiB，**全部 ≤400Mi** |
| NodePort | 403（无令牌）/ 200（带令牌）/ 200（captcha）；扩容后连续 8 次全 200 |
| 集群完整登录 | captcha 200（有 img）→ `login` 200（token）→ 6 个认证接口全 200 → 跨服务 `export/display` 200 + taskId |
| DB 上限 | 两容器均为 256m、`OOMKilled=false` |

> 对比上一轮 300Mi：`backend` 在 300Mi 下 `TokenService.createToken` 抛 `Java heap space`、登录不可用；**400Mi + 瘦身 jar + jlink runtime 后完整功能已打通**，这正是「瘦身才是根本解」的实证。

## 6. 变更文件与验证范围

- 6 个分支（backend/api × jdk17/21/25）同步修改了：`pro-business-api/pom.xml` 或 `ruoyi-admin/pom.xml`、`application.yml`、`logback(-spring).xml`、`spy.properties`；均执行 `mvn -B -DskipTests=false test`，**6/6 通过**。
- 集群侧只在 `D:\work\runtime-logs\manifests-final.yaml` 与镜像层，未改仓库内 CI workflow；ES/Kafka 仍未接入（`engine=legacy`、`sync.enabled=false`），本期不改动其进程与数据。
- Windows 本机 9989/9902 Java 仍停止；WSL 共享缓存用临时 `redis-server :6380`（7.2.16），**Redis 8.10.3 迁移与 6 节点 Cluster 仍属 `k3s-remediation-plan.md` 的待执行项**。

## 7. 遗留 / 建议

1. backend 仍有 3 条 logback 内部 `|-WARN`（`SizeAndTimeBasedFNATP` 弃用）；如需绝对零噪声，改 `SizeAndTimeBasedRollingPolicy`（需独立复核）。
2. `docker update` 的 DB 上限不随容器重建持久化；若 WSL 重启，需重跑 `set-db-memory-limits.sh`，或在容器启动命令里显式带 `--memory=256m`。
3. 镜像仍有 `mysql:8.0.30` 的 glibc 系统层 255MB；若允许联网，可换成 `oraclelinux:8-slim` / distroless base 再降约 150MB。
4. jlink 用的是保守模块集；若要进一步缩小，可用 Spring Boot `jarmode=tools extract` + 全量 `jdeps` 精确计算模块（本次 523 个嵌套 jar 的 jdeps 全量扫描超时，未采用）。
5. AppCDS / 裁剪更多未使用嵌套 jar 仍是长期方向（规划 §R8）。
