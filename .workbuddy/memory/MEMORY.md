# car-monit-api 项目长期笔记

> **交接提示（2026-11-17 收尾）**：最新一轮是"云端全接口+资源性能对比"，进度见
> `D:/work/runtime-logs/公开仓库安全加固-任务清单.md` H 段、`公开仓库安全加固-脚本与证据索引.md` H 节、
> 当日日志 `2026-11-17.md` 末节；方法与结果见两仓库 jdk25 分支 `docs/v3/review/11-*.md`。
> 全部 run 已结束、文档已推送、两仓库仍 public。待办仅剩技术增强（backend native Druid AOT、saveRedis 反射、
> Rust/Python 探针、Go 端点对齐、凭据真实轮换）——非阻塞，下一会话从上述 H 段接续即可。
> 原生矩阵/JDK 覆盖任务的已办/待办确认见当日日志 `2026-11-17.md` 末节（含本地提交 hash 与 ext4 性能结论）。

## 分支布局（git worktree）

| 目录 | 分支 | 用途 |
| --- | --- | --- |
| `car-monit-api-java-V3` | `car-monit-api-java-V3` | 主工作区，文档/脚本在此（`docs/v3/`、`scripts/v3/ops/`） |
| `car-monit-api-jdk25` | `car-monit-api-jdk25` | Spring Boot 4.1.2 + JDK25 线 |
| `car-monit-api-jdk21` | `feature/springboot3` | Spring Boot 3.5.6 + JDK21（native 主攻方向） |
| `car-monit-api-jdk17` | `feature/springboot3-jdk17` | Spring Boot 3.5.6 + JDK17（代码已同步，构建未跑） |

## 已确认的技术结论（别再重复验证）

1. **Spring Boot 4 的 native 只支持 Java 25**。JDK17/21 编 Boot4 native 运行必报
   `NativeImageRequirementsException: must support at least Java 25`。JDK17/21 要 native 只能走 Boot3。
2. **Boot3 native 三处不兼容及解法**：Forest 1.8（无 native 支持）→ 换 `RestClient` 整包移除；
   Druid（`setConnectProperties(null)` NPE）→ 清空 `druid.filters`/`connectionProperties` +
   排除 `DruidDataSourceAutoConfigure`；Hibernate Validator（JBoss Logging 反射）→
   排除 `ValidationAutoConfiguration`。
3. **MyBatis-Plus 3.5.18 AOT 全 classpath 扫描**在 fat jar 下会扫出上百个埋雷类 →
   用 `v3-patch-mybatis-aot-scan.py` 字节码改写 `CollectUtils.findMainClasses()` 只认 `-H:Class`。
4. **`native-maven-plugin` 版本校验**：Boot 3.5 BOM 管到 0.10.6 会误判 Mandrel 21，
   必须固定 `1.1.14` + `<requiredVersion>21.0</requiredVersion>`。
5. **JDK25 Boot4 native 已完整跑通**（2026-11-16）：此前"native 内 JDBC 失败"是运行脚本
   漏注入 MySQL 凭据。`PlateColorDictionary` 单独连 MySQL 3307，需要
   `CARMONIT_MYSQL_USERNAME/PASSWORD`（从 `mysql_wsl` 容器 `MYSQL_ROOT_PASSWORD` 运行时读取）；
   主数据源 openGauss 用 `GS_PASSWORD`。验证端口统一 19902，且必须做启动前端口预检。
6. **Boot4 native 只能 Java 25**：JDK21/17 即使 native 构建成功，运行必报
   `NativeImageRequirementsException`；这两个 JDK 的 Boot4 线以 JVM jar 交付，native 走 Boot3。

## 环境硬约束

- 宿主 13.8 GB 内存 / WSL 12 GB。native-image 分析期需 10 GB+，
  **构建前必须 `docker stop es-wsl kafka-wsl mysql_wsl`，只留 `opengauss`**，否则构建从 8 min 劣化到 38 min。
- WSL 发行版名：`openEuler-24.03-LTS-SP4`。
- 端口 9902 被 `[::]:9902`（IPv6 双栈，uid 0，非本项目）占用且 `ss -lntp` 看不到，
  读 `/proc/net/tcp6` 才能定位；**所有 native/JVM 运行验证统一用 19902**。
- 构建脚本第一步必须是 `clean install`，否则已删除类的旧 class 残留会导致 native `NoClassDefFoundError`。

## 关键入口

- 构建：`scripts/v3/ops/v3-native-build-linux.sh <api|backend> <25|21|17> <dir> [label]`
- 运行：`v3-run-native-linux.sh` / `v3-run-jvm-linux.sh`；对比：`v3-compare-native-jvm.sh`
- 业务对比：`D:/work/runtime-logs/v3-ops/v3-compare-business.sh --app api|backend --native <elf> --jar <jar> --java <java> --label <l>`
- 证据日志：`D:/work/runtime-logs/v3-ops/evidence/`（WSL 侧 `/mnt/d/work/runtime-logs/v3-ops/evidence`）
- 主文档：`docs/v3/native-image-cicd-and-runtime-verification.md`（根因全链）
- 进度交接：`docs/v3/boot3-native-progress-and-handover.md`（状态快照，每轮更新这里）
- 公开加固+CICD 验收：`docs/v3/review/09-public-repo-hardening.md`（凭据轮换清单）、
  `docs/v3/review/10-public-cicd-native-verification.md`（本轮全记录）

## 公开仓库 + 云 runner CICD（2026-11-16~17 已验证）
- 两仓库目前 **public**（用户决定公开一段时间，不频繁切换避免风控）；无自动改回 private 的看门狗。
- GitHub 账号账单失败时私有仓库云 runner 全部 job 3s failure、runner_id=0；公开后免费分钟恢复。
- native workflow 在 `jdk{17,21,25}` + `master` 分支；V3 分支是 Boot2/JDK8 无 native profile。
- **native artifact 体积坑**：`find target -perm -u+x -print -quit` 会先命中 9KB libjvm.so shim；
  已改为按 artifactId 精确定位 `target/<module>` + 10MB 下限门禁（否则 artifact 仅 1331B）。
- `native-image-cloud.yml` 支持 `release_tag` 输入直接 `gh release upload`（platform=linux/windows）。
- 云产物 native（368MB）vs 同版 JVM jar：7/7 端点字节级一致；native 启动 2.65s/305MB vs JVM 16.9s/598MB。
- 凭据：本轮 Secrets 用测试值；**公开前必须外部轮换真实凭据**（见 09 号文档），轮换后用
  `D:/work/runtime-logs/update_gh_secrets.py` 更新。HTTPS git push 被网络重置，用 SSH:443 + deploy key。
