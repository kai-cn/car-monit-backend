# V3 原生镜像 / WSL 运维任务进度快照

> 快照时间：2026-11-15 18:41 (GMT+8)
> 用途：上下文中断后续接。所有数值来自实机日志，未执行项均显式标注。
> 主文档：`D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\native-image-mandrel-verification.md`
> 证据目录：`D:\work\runtime-logs\v3-ops\evidence\`

---

## 1. 任务目标（原始需求）

1. 清除 k3d `v3` 三个节点内 car-monit-backend/api 的过时镜像，每节点每仓库只保留一份最新版。
2. 单机版与 k3d 集群版同一时刻只启动一套；按实测分配内存/CPU，让 Windows 可用内存尽可能多。
3. 六个 JDK 分支（api/backend × jdk17/21/25）发版 jar 最小化打包。
4. WSL 磁盘回收（shutdown → set-sparse false → compact → fsutil）。
5. 【补充需求】先测试 Windows 原生镜像；下载 Linux 版 jdk25 Mandrel 构建 jdk25 原生镜像；测试原生镜像 CICD 与资源占用；如实记录文档/脚本/运维命令。Windows Maven：`D:\work\apache-maven`。授权自主决策，按 Java 最佳生产实践推进。

---

## 2. 已完成（实机执行，有证据）

### 2.1 镜像清理 / 互斥 / 配额 / 磁盘
| 项 | 结果 |
| --- | --- |
| 三节点镜像清理 | 保留 6 个 `ci-v2`，删除 12 个过时镜像；`crictl rmi --prune` 另清 untagged pause/coredns。证据 `prune-dryrun.log`、`prune-apply.log` |
| 单机/集群互斥 | 实测切到 standalone：WSL Mem.used 6019→3474 MB（−2545 MB），java 进程 10→4，k3d 节点 exited。证据 `switch-standalone.log` |
| `.wslconfig` | `8GB/4GB/4核` → **`4GB/2GB/2核`**；`wsl --shutdown` 后实测 `nproc=2`、`Mem.total=3919MB`、`Mem.used=968MB`。备份 `backup/.wslconfig.bak-20261115-1445` |
| VHDX compact | **42.812 GB → 38.315 GB（回收 4.497 GB）**，D 盘 8.7→13.2 GB；非稀疏校验通过。证据 `compact-20261115-152433.log`、`guest-clean.log`、`restore-after-compact.log` |
| 注意 | compact 后又经 Linux Mandrel 解压/编译，VHDX 现为 **42,029,023,232 B（39.15 GiB）**；D 盘现仅 **4.61 GB** 可用 |

### 2.2 jar 最小化
- 六分支 pom 排除规则一致；jdk21/25 的 4 个 jar 早于 pom 瘦身改动（STALE）。
- `api-jdk25` 已由 native 构建阶段一重建：215,881,278 → **211,027,173 B**（−4.63 MiB），非目标平台 native 13→3，STALE=no。证据 `jar-audit-after-rebuild.log`。
- **其余 3 个 jar（api/backend jdk21、backend jdk25）仍未重建**，各自 native 构建阶段一会自动重建。
- 陷阱：fat jar 的 `BOOT-INF/lib` 全为 ZIP_STORED，不可重压；`pulsar-client` 有真实代码引用，不可删。

### 2.3 Mandrel 工具链（Windows + Linux）
| 项 | 结果 |
| --- | --- |
| Windows 包 | `D:\jdk\mandrel-25.0.4.1-Final.7z` 是 **Windows x64**（native-image.cmd/.exe/.dll），已解压到 `D:\jdk\mandrel-25.0.4.1-Final`；`native-image 25.0.4.1` 可运行；VS2022 `vcvarsall.bat x64` + `cl.exe` 齐备 |
| Windows 冒烟 | Hello → 13.43 MB exe / 38 s / 峰值 RSS 1.21 GB |
| Windows Maven | `D:\work\apache-maven`（3.9.9）；本地仓库 `D:\work\maven-repo`（由 WSL `/home/dev/.m2/repository` 789 MB 复制）；`C:\Users\abelz\.m2\settings.xml` 指向该仓库 + 阿里云镜像 |
| Linux 包 | `mandrel-java25-linux-amd64-25.0.4.1-Final.tar.gz` **221,899,480 B**，sha256 `e47ff6bfe6a8dbb482fdc65c9a49fc6f3ba2fa61ef3cc8fb6229a88989054c31`（官方 API asset URL 下载校验通过）。关键点：curl 走代理 502、github.com 直链 RemoteDisconnected；**必须用 GitHub API asset 端点 + `Accept: application/octet-stream` + Range 续传** |
| Linux 安装 | 已解压到 WSL **ext4** `/home/dev/tools/mandrel-java25-25.0.4.1-Final`（575 MB），符号链接 `/home/dev/tools/mandrel-25`；`dnf` 装好 gcc/g++/glibc-devel/zlib-devel；Hello ELF 13,372,128 B / 2m48s / 峰值 1.13 GB。证据 `setup-mandrel-linux.log` |

### 2.4 Spring Boot 4 AOT + native-image 参数收敛（核心成果）
失败链逐轮收敛（每轮约 90 s，用 `native-retry-from-args.bat` 复用 `@argfile` 跳过 3 分钟 AOT；`native-iterate.py` 自动解析报错追加参数）：
1. tcnative JNI `UnsatisfiedLinkError` → `--initialize-at-run-time=io.grpc.netty.shaded`
2. Flink `VehicleTrackFlinkJob` 缺类 → Maven profile `native-flink-exclude` 编译期排除该类（Flink 依赖是 provided）
3. Logback 逐类报错无限循环 → **`--initialize-at-build-time=ch.qos.logback` 整包**一次收敛
4. fastjson2 逐类报错 → **`--initialize-at-build-time=com.alibaba.fastjson2` 整包** + 6 个具体类
5. 误加过 `--initialize-at-build-time=org.slf4j`（会使 SLF4J 在构建期绑定 NOP provider）——**已移除**；日志里 `SLF4J(W): No SLF4J providers` 是 native-image builder 自身告警，产物运行日志正常。

**最终 13 条 buildArgs** 见 `evidence/native-iterate-final.args`，已固化到六个分支模块 pom 的 `native-maven-plugin <buildArgs>`，XML 校验通过：
```
--initialize-at-run-time=io.grpc.netty.shaded
--initialize-at-run-time=io.grpc.netty.shaded.io.netty.internal.tcnative
--initialize-at-run-time=io.grpc.netty.shaded.io.netty.handler.ssl
--initialize-at-run-time=io.grpc.netty.shaded.io.netty.util.internal.SystemPropertyUtil
--initialize-at-run-time=io.grpc.netty.shaded.io.netty.util.ResourceLeakDetectorFactory
--initialize-at-build-time=ch.qos.logback
--initialize-at-build-time=com.alibaba.fastjson2
--initialize-at-build-time=ch.qos.logback.classic.Logger
--initialize-at-build-time=com.alibaba.fastjson2.JSONFactory$CacheItem
--initialize-at-build-time=com.alibaba.fastjson2.writer.ObjectWriterBaseModule
--initialize-at-build-time=com.alibaba.fastjson2.function.impl.ToDouble
--initialize-at-build-time=com.alibaba.fastjson2.reader.ObjectReaderImplString
--initialize-at-build-time=com.alibaba.fastjson2.JSONReader$Context
```
注意：`META-INF/native-image/.../native-image.properties` 里的 `Args =` 对 Spring Boot fat jar 不生效，必须用 pom buildArgs。

### 2.5 Windows 原生 exe（端到端成功，运行验证中断）
- 第一次产物（无 agent 元数据）：`pro-business-api.exe` **342,769,664 B / 326.89 MB**，sha256 `31135778d5e70bf9436ab22add750d968b7965fe38ecb4918f39fbfd86d064b7`；`Finished generating ... 9m56s`，峰值 RSS 9.78 GB。
- **启动失败**：`forest.retryer: com.dtflys.forest.retryer.BackOffRetryer` 按类名字符串绑定，类在 `forest-core-1.8.0.jar` 里但被 native-image 裁剪 → `ClassNotFoundException`。用 `--forest.retryer=java.lang.Object` 探测后遇到第二个阻塞：`ForestBeanRegister` 用 `Class.newInstance()` 反射实例化 `com.dtflys.forest.logging.DefaultLogHandler`（构造器未注册）。日志 `native-run-*`、`native-run-probeA.log`。
- **修复（GraalVM 官方 tracing agent）**：JVM fat jar 以 `-agentlib:native-image-agent=config-output-dir=...,config-write-period-secs=10` 运行，收集到 **1333 reflection + 806 resources**（`agent-config/reachability-metadata.json`），其中确认含 `BackOffRetryer`、`DefaultLogHandler`。已合并到六个分支 `src/main/resources/META-INF/native-image/com.ruoyi/<module>-agent/reachability-metadata.json`（**独立子目录**，避免与 Spring AOT 生成文件同名覆盖）。
- **端到端完整构建成功**：`native-api-jdk25-final.log` → BUILD SUCCESS，Total time **14:40**，Peak RSS **10.11 GB**，分析阶段可达 58,260 types / 20,219 reflection types（比上次 +627，证明 agent 元数据生效）。产物 `pro-business-api.exe` **348,528,640 B** + 8 个 JDK 配套 dll。
- **该最终 exe 尚未运行验证**（上次在探测 WSL 端口时被用户要求暂停）。

### 2.6 脚本 / CICD
- 六分支 `.github/workflows/native-image.yml` 已同步（backend 分支 runner 标签 `wsl-k3s-backend`）；含 `native-windows` / `native-linux` 两个 job 与 `workflow_dispatch` 参数 app/jdk/platform/run_bench。
- 新增脚本：`v3-native-build-linux.sh`（支持 `WORK_ROOT` 把源码同步到 ext4 避免 drvfs 慢）、`v3-setup-mandrel-linux.sh`、`v3-native-bench-linux.sh`、`v3-native-docker-build.sh`、`v3-native-cicd-local.ps1`、`templates/Dockerfile.native`、`download-mandrel-linux.py`、`native-iterate.py`、`native-retry-from-args.bat`、`collect-native-agent-config.sh`、`native-build.bat`（均带实机日志）。
- 静态校验：8 个 sh `bash -n` 全通过；3 个 py `py_compile` 通过；7 个 ps1 `[Parser]::ParseFile` 0 错误且纯 ASCII 无 BOM（PS 5.1 GBK 坑）。
- `v3-native-bench.ps1` 已修复 PowerShell 5.1 `Start-Process` 因 `HTTPS_PROXY`/`https_proxy` 大小写重复导致的字典冲突（用 `[System.Environment]::SetEnvironmentVariable` 清除），并增加 stdout/stderr 重定向。

---

## 3. 当前实机状态（18:41）

| 项 | 值 |
| --- | --- |
| 宿主 | 13.84 GB 总 / 可用 3.36 GB；vmmemWSL 3311 MB；无残留 java/native-image/python 进程 |
| WSL | Running（4GB/2GB/2核 配额），DB 容器 kafka/es/mysql_wsl/opengauss 自动恢复；`localhostForwarding=true` |
| D 盘 | **仅 4.61 GB 可用**（VHDX 42,029,023,232 B）；C 盘 8.47 GB |
| 服务模式 | standalone（k3d 节点 stopped）；WSL 重启后 systemd 单机服务是否自动拉起**未复核** |
| Linux 工具链 | Mandrel 25 + gcc 齐备，Hello 冒烟通过 |

---

## 4. 上次中断点

正在执行「从 Windows 侧探测 WSL 依赖端口 5432/3307/6379/9200/9092 是否可达」，命令超时被 SIGTERM，**未得到结果**。此前 agent 的 JVM 运行时报 `Connection refused: 127.0.0.1:5432`（当时 WSL 刚启动、opengauss 未就绪），因此 Windows exe 能否连到 WSL 内的库**尚未确认**。

---

## 5. 下一步（续接顺序）

1. 复核 Windows → WSL 端口可达性；若 5432 不可达，用 `--spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://<WSL-IP>:5432/RuoYi` 覆盖后再测。
2. 用 `v3-native-bench.ps1` 实测最终 Windows exe：启动到端口就绪时间、稳态/峰值 RSS、CPU；确认 Forest 反射修复生效、日志正常输出。
3. `v3-native-cicd-local.ps1` 收集 Windows artifact（exe + sha256 + zip + manifest）。
4. **临时提高 WSL 配额**（`v3-wsl-quota.ps1 -Profile custom -Memory 12GB -Swap 8GB -Processors 6 -Apply` + shutdown）→ 启动 WSL → 用 `v3-native-build-linux.sh api 25 ...` 构建 Linux ELF（预计 10–15 分钟、峰值约 10 GB）；磁盘紧张，建议先 compact 一次或确保 D 盘 ≥6 GB。
5. `v3-native-bench-linux.sh` 实测 Linux ELF；`v3-native-docker-build.sh` 打包最小容器镜像并对比体积。
6. CICD 如实记录：本机无 gh CLI/PAT，未触发云端 Actions run；按 workflow 等价命令本地实跑。
7. 恢复常态配额 `4GB/2GB/2核`（`v3-wsl-quota.ps1 -Profile cluster -Apply`），必要时再次 compact 回收 VHDX。
8. 更新 `docs/v3/native-image-mandrel-verification.md`（§7.4/7.5、§8、§9、§11 仍写着"待填写"/旧结论），补全部实测数据、13 条 buildArgs、agent 元数据、Linux 构建结果、风险与未解决项。
9. 追加工作区记忆日志。

---

## 6. 已知风险 / 待如实标注

- 整包 `--initialize-at-build-time=com.alibaba.fastjson2` 带来多条 `RecomputeFieldValue.FieldOffset ... sun.misc.Unsafe.objectFieldOffset` 警告（JDKUtils / ObjectWriterImplMap），**运行时 fastjson2 行为需业务接口验证**，不能只凭启动成功下结论。
- 只有 Mandrel 25 一套工具链；jdk17/21 分支若用它编译，native 运行时语义是 JDK25，不等价于同版本 GraalVM。
- native-image 编译期 Windows 峰值 RSS 10.11 GB，必须关闭 WSL 才能编译；两个平台编译不能并行。
- D 盘空间紧张（4.61 GB），Linux 编译会继续增长 VHDX。
- 3 个 stale jar 未重建；4 个分支的 native 产物（backend × jdk17/21/25、api jdk17/21）尚未构建。

---

## 7. 续作完成状态（19:32 更新，任务收尾）

**已完成**：
1. Windows 最终 exe 运行验证：Forest 反射修复生效；但与 Linux ELF 一致卡在 MyBatis-Plus `sqlSessionFactory`（Spring Boot 4 AOT 兼容问题），业务未完整启动，稳态 RSS 未测得。Windows→WSL DB 需直连 WSL IP `172.29.27.7`。
2. DB 容器 256m 限额在重启压力下 OOM(137)，编译期临时 768m，常态调为 **512m**。
3. **Linux 原生 ELF 构建成功**：`340,921,056 B / 325.13 MB`，ELF x86-64 stripped，28m8s，峰值 RSS 10.11GB；已回拷 `D:\work\IdeaProjects\car-monit-api-jdk25\pro-business-api\target\pro-business-api`。日志 `native-api-jdk25-linux.log`。
4. Linux ELF 资源实测：启动阶段峰值 RSS **29.8 MB**（失败前）；容器镜像 `car-monit-api:native-jdk25` **493 MB**（对比 JVM `ci-v2` 645MB，−23.6%）。`debian:12-slim` 拉取超时，实际用本地 `car-monit-sys:local` 152MB 基础层。
5. CICD 本地等价实跑：双平台 artifact + sha256 + manifest 已入 `D:\work\runtime-logs\v3-ops\dist\`；确认无 gh CLI、workflow 未提交（`??`），**云端 run 未触发**。
6. 常态恢复：`4GB/2GB/2核`、单机服务 active、k3d 4 节点 Exited（互斥）、DB/中间件 Up；**宿主可用 5.12 GB**（初始 1.86 GB）。
7. 磁盘：清理 ext4 构建临时目录 + fstrim + compact，VHDX 41.045→39.79 GB（回收 1.255 GB），D 盘 4.59 GB。
8. 正式文档 `docs/v3/native-image-mandrel-verification.md` 已全量更新（含 §0 结论、§7 参数收敛、§8 资源、§9 CICD、§11 风险）。

**产物校验和**：
- Windows exe `8E505CAC08C9E615579B03F32B38545B4839BC7A21088FC4572EB3385C42AA1A`
- Linux ELF `9399D12952BEA5CB8622E209B1E308F44E1FA0C7F5E8CFC3C793E1573D00D7B1`

**仍未完成 / 需后续决策**：业务完整启动（MyBatis-Plus AOT 适配）、其余 5 个 JDK×app 组合的 native 构建、3 个 stale jar 重建、fastjson2 Unsafe 警告的业务接口验证、云端 CICD 触发、docker 未引用卷 4.995 GB 的清理（未擅自删）。

**当前交付文件**：主文档 + 进度快照 + `scripts/v3/ops/` 全部脚本 + `D:\work\runtime-logs\v3-ops\` 证据与产物。

---

## 8. 第二阶段（20:00–，CICD / 启动适配 / 对比实测）

新需求：六分支云 runner CICD（账单受限才用 self-host）、修复 jdk25 业务完整启动、
启动成功后做稳定性与 native/JVM 对比、再跑 jdk21/17、全程记录文档脚本。

**已完成（有证据）**：

1. **云 runner 账单受限实测**：`v3-github-actions-quota.py` 查到两仓库 private/admin、默认分支 master、billing REST 404。
   用 `v3-github-actions-dispatch.py ensure-default` 把云 workflow 写入两仓库 master，触发 canary
   `run 43711910286` → 1 秒失败、runner_name 空、annotation 明确写
   `recent account payments have failed or your spending limit needs to be increased`。
   **按用户预设条件切 self-host runner**。证据 `cloud-runner-blocked.log`、`canary-*.log`。
2. **AOT MyBatis 根因修复**：读 `Mapper__BeanDefinitions.java` 确认 AOT 丢掉 `AUTOWIRE_BY_TYPE`；
   反编译 mybatis-plus native-image 模块确认其 AOT 后处理器不注入 sqlSessionFactory。
   新增 `NativeMapperSqlSessionFactoryRegistrar`（六分支），`process-aot` 4m19s 验证
   23 个 mapper 生成 `new RuntimeBeanReference("sqlSessionFactory")`。证据 `aot-verify-1.log`、`aot-fix-propagate.log`。
3. **数据源认证坑**：`application.yml` 密码默认空；WSL2 localhostForwarding 实测
   `127.0.0.1:5432/3307/6379` OPEN，但源 IP 经 NAT 落 `md5` 规则。
   新增 `v3-read-db-password.py` + `v3-run-native-with-db.ps1` 运行时注入，密码不落盘。
4. **type alias 修复**：native 启动第二轮失败于 `Could not resolve type alias 'KafkaMessageRecord'`；
   JVM 版带 `--add-opens` 8 秒启动成功 → 证明 native 特有。根因是 native image 无 .class 文件，
   `type-aliases-package` 扫描失效。`v3-fix-mapper-type-aliases.py` 把六分支 90 个 XML、
   405 处简写别名改为 FQN（备份 `backup/mapper-xml-20261115-202608/`）。
   **预验证**：JVM 版加 `--mybatis-plus.type-aliases-package=` 仍 8 秒启动成功。
5. **CICD 落地**：`templates/native-image-cloud.yml`（canary/prepare 动态 matrix/build，
   setup-graalvm mandrel 17/21/25、MSVC、artifact+sha256+manifest）与
   `templates/native-image.yml`（self-host，修正 runner label、支持 21/17 Mandrel 自动安装）。
   已同步六分支；新建 `v3-github-actions-dispatch.py`、`v3-github-actions-quota.py`、
   `v3-publish-native-branches.sh`、`v3-push-pending-branches.sh`。
   六分支均已本地 commit；Windows Git schannel 经代理断连，用 openssl 后端 + 有界重试推送中。
6. **对比脚本**：`v3-compare-native-jvm.sh`（Linux，curl 探活 + RSS/CPU + 稳定性阶段）、
   `v3-compare-native-jvm.ps1`（Windows，复用 bench）。全部 sh/py/ps1 静态校验通过，ps1 纯 ASCII 无 BOM。
7. **文档**：`docs/v3/native-image-cicd-and-runtime-verification.md`（§8/§9 待实测数据补齐）。

**进行中**：Windows 原生 exe 第三次重编译（含 AOT 修复 + XML 别名修复），
后台任务 `aZ1Nd5`，日志 `native-api-jdk25-aliasfix.log`；六分支 push 重试 `0qcTJw`。

**下一步**：exe 编译完成 → 启动 WSL 恢复 DB → `v3-run-native-with-db.ps1` 验证业务完整启动 →
若通过则 `v3-compare-native-jvm.ps1` 做稳定性与 JVM 对比 → 触发 self-host CICD
（验证账单受限下自托管 job 是否仍可运行）→ 重建 Linux ELF → jdk21/17 → 补文档 §8/§9。

---

## 9. 21:14–21:26 续作：段错误根因定位 → 应用户要求暂停

**已定位的硬结论（本轮最大产出）**：段错误不是「参数没收敛够」，而是
**fastjson2 2.0.66 jar 自带的 `META-INF/native-image/com.alibaba.fastjson2/fastjson2/native-image.properties`**
把 `JSONFactory`、`JDKUtils`、`TypeUtils`、`ObjectReaderProvider`、`ObjectWriterProvider` 等
22 个类设为 build-time。`JDKUtils` / `ObjectWriterImplMap` 的类初始化调用
`sun.misc.Unsafe.objectFieldOffset`，GraalVM 重算失败（7 条 `RecomputeFieldValue.FieldOffset ... failed`），
构建期字段偏移被写进 image heap，运行时 GC `AlignedChunkRememberedSet.walkObjects` 踩坏引用。
项目额外加的整包 `--initialize-at-build-time=com.alibaba.fastjson2` 雪上加霜。
`native-iterate-pass3` 的 10 轮逐类追加（~16 分钟，`MAX_ROUNDS_REACHED`）方向错误：
只是把更多 fastjson2 对象合法塞进 heap，消除编译报错但保留坏引用。
`native-iterate-round01.log` 的对象溯源链根在 `JSONFactory.getDefaultObjectReaderProvider`
被常量折叠，经 `org.aspectj.util.LangUtil.<clinit>` 的 `Throwable.printStackTrace` 解析上下文进入 heap。

**正确修复**（脚本 `scripts/v3/ops/v3-fix-fastjson2-init.py`，默认 dry-run，
`--apply` 才写六分支 pom，自动备份 + XML 校验；**本轮未 `--apply`**）：
删掉 6 条 `--initialize-at-build-time=com.alibaba.fastjson2*`，改为
```
--exclude-config
.*fastjson2.*[.]jar
^/META-INF/native-image/
--initialize-at-run-time=com.alibaba.fastjson2
```

**两轮实机实验**：
| 轮 | 日志 | 结果 |
| --- | --- | --- |
| v1 | `native-fastjson2-runtime-build.log` | **FAIL 1m20s**：`\QD:\work\...\E` 经 `@argfile` 被改写成 `\QD:/work/.../E`，`--exclude-config` 未匹配；仍有 5 条 RecomputeFieldValue + 16 个 image-heap 对象错误 |
| v2 | `native-fastjson2-runtime-v2.log` | 改用无反斜杠正则；日志前 47 行 `JDKUtils` 的 `Unsafe::arrayBaseOffset` 告警消失、Recompute=0、image-heap 错误=0 → 排除生效迹象明确。**跑 3m44s 后按用户「暂停」主动终止，无 SUCCESS/FAIL 结论** |

**本轮新增/保存的产物**：
- `scripts/v3/ops/v3-fix-fastjson2-init.py`（新脚本，py_compile + dry-run 通过）
- `D:\work\IdeaProjects\car-monit-api-jdk25\target\tmp\native-image-fastjson2-runtime{,-v2}.args`
- 归档副本 `D:\work\runtime-logs\v3-ops\evidence\argfiles\`（3 份 args，防 `mvn clean` 删除）
- `evidence\fastjson2-2.0.66-native-image.properties.txt`（官方配置原文，sha256 `e1a56bb5…`）
- `docs/v3/native-image-cicd-and-runtime-verification.md` §0/§8.2/§8.3/§9/§10 已全量更新

**暂停时的机器状态（21:26 实测）**：后台任务 `ocmfdb` 已 killed；
`Get-Process java,native-image` 为空；WSL `openEuler-24.03-LTS-SP4` = Stopped；
未改 `.wslconfig`（仍是 4GB/2GB/2核）；未启 DB；未改任何分支 pom；
现有 exe 仍是 20:48 段错误版 `72AA5654…`。

**未完成事项（按续接优先级）**：
1. 重跑 v2 构建（命令见主文档 §8.2.2），确认是否 BUILD SUCCESS + 运行时无段错误。
2. 成功后 `python v3-fix-fastjson2-init.py --apply` → 六分支 commit + 重跑
   `v3-push-pending-branches.sh`（`car-monit-api-jdk21` 上次 STILL_PENDING）。
3. 启动 WSL → `v3-run-native-with-db.ps1` 验证业务完整启动（此前一直未达成）。
4. `v3-compare-native-jvm.ps1` 做稳定性 + native/JVM A/B 对比（前置条件 3）。
5. self-host CICD 真实 build job（此前只跑过 canary）。
6. jdk21/17：Mandrel 21/17 tarball 已下载校验但**未安装到 WSL ext4**、未冒烟、未编译；
   需临时 12GB/6核 配额，按主文档 §9 命令推进。
7. 主文档 §8.3 稳定性/对比数据、§9 编译结果仍为「未执行」，不得填推测值。
8. 收尾恢复常态配额 + 视情况 compact VHDX；追加工作区 memory 日志。

