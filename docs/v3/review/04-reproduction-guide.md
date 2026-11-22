<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# V3 审阅 / 修复 / 联调 复现指南

> 与 `01` ~ `03` 配套，在两侧 V3 分支各存一份。
> 记录日期：2026-11-09。**不写任何口令、令牌、密钥明文；凭据一律由运行环境注入。**

## 1. 环境清单

| 项 | 位置 / 地址 | 说明 |
| --- | --- | --- |
| Windows 工作树 | `d:/work/IdeaProjects/car-monit-backend-java-V3`、`d:/work/IdeaProjects/car-monit-api-java-V3` | 两个 git worktree，各自独立分支 |
| 主工作树 | `d:/work/IdeaProjects/car-monit-backend-new`、`d:/work/IdeaProjects/car-monit-api` | 参照用，V3 改动不落在这里 |
| JDK | `D:\jdk\` 下 8 / 21 / 25 | 本项目用 8；`JAVA_HOME=D:\jdk\jdk1.8.0_202` |
| Maven | `D:\work\apache-maven\bin\mvn.cmd` | 离线模式 `-o` |
| MySQL 8 | `D:\work\mysql-8.0.30-winx64`，端口 3307 | **只在现有实例建新 database，不在别的 data 目录另起实例** |
| Redis | `D:\work\Redis-8.10.2-Windows-x64-msys2` | 两端共享数据 |
| Elasticsearch 7.15.2 | `D:\work\elasticsearch-7.15.2` | 必须限制 JVM 堆内存 |
| Kafka 4.0.0 | `D:\work\kafka_2.13-4.0.0` | |
| 虚拟机 | `192.168.56.10:22`，CentOS 7 | Docker 中 `opengauss` 容器；不在跑就自行启动 |
| WSL | `openEuler-24.03-LTS-SP4` | 可用 `python -c "import paramiko"` 做 SSH 自动化 |
| 运行日志 / 启动脚本 | `D:\work\runtime-logs\` | `start-api-v3.ps1` 等，凭据不写入脚本文件 |

### 1.1 资源约束（必须遵守）

- **限制内存**：Java 服务用 `-Xms512m -Xmx1g` 级别参数；ES 单独限制堆。
- **不重复启动**：启动前先查端口 / 进程；若 java 服务已在跑，先复用或先停再起，绝不并存第二个实例。
- **Windows 本机最多一个 backend java + 一个 api java**，ES / Kafka / Redis 各仅一个实例。
- 所有需要删除的测试数据、构建产物、日志**直接删除，不进回收站**。

### 1.2 端口与链路

```
浏览器/大屏 → backend(9989, MySQL 8) ──HTTP + X-Internal-Token──> api(9902, openGauss)
                    │                                                  │
                    └──────────── Redis 共享 / ES / Kafka ─────────────┘
```

- backend 的 `vehicleMonitor.baseUrl` 指向 api 服务；backend 走 HTTP 查询 api 数据。
- 启用内部端点守卫时，两侧必须使用**同一个**令牌：
  api 侧 `TRAFFIC_INTERNAL_TOKEN`，backend 侧 `TRAFFIC_API_INTERNAL_TOKEN`；
  运维脚本 `es-init.ps1` 也从 `TRAFFIC_INTERNAL_TOKEN` 读取。令牌值不入库。
- backend 启动还需要导出下载签名密钥（fail-fast，禁止回退默认值），由环境注入。

## 2. 复现「审阅 → 修复 → 复核」

1. 按 `01-code-audit-record.md` 第 2 节逐项打开文件核对问题台账。
2. 按 `02-fix-record.md` 第 1 节在某条分支上执行：
   `git log --oneline -12`、`git show --stat <commit>`，核对提交与改动文件。
3. 按 `02-fix-record.md` 第 3 节复跑编译、单测、PowerShell 解析、回灌窗口计算、MySQL SQL。
4. 按 `03-independent-review-record.md` 第 1 节的方式，为**每侧**启动全新的只读
   `code-explorer` 会话（输入问题清单、要求文件:行号证据与门禁结论），核对三轮结论。
5. 门禁：只有所有会话都给出「可推送 / 无阻断项」，才执行第 4 节的 CI 触发。

## 3. 实机联调操作清单

> 每步都要先检查端口/进程，避免重复启动；令牌与口令用环境变量，不写进命令历史文件。

### 3.1 打包（先停掉占用 jar 的 java 进程，避免 Windows 文件锁）

```powershell
$env:JAVA_HOME = 'D:\jdk\jdk1.8.0_202'
$M = 'D:\work\apache-maven\bin\mvn.cmd'
& $M -f 'd:\work\IdeaProjects\car-monit-api-java-V3\pom.xml'      -o -B -q -DskipTests package
& $M -f 'd:\work\IdeaProjects\car-monit-backend-java-V3\pom.xml' -o -B -q -DskipTests package
```

### 3.2 依赖服务就绪检查

```powershell
# openGauss 容器（凭据由环境注入，不写入仓库）
python -c "import paramiko; c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy()); c.connect('192.168.56.10',22,'root',__import__('os').environ['VM_PWD'],timeout=10); i,o,e=c.exec_command('docker ps --format={{.Names}}'); print(o.read().decode()); c.close()"

(Test-NetConnection -ComputerName 192.168.56.10 -Port 5432 -WarningAction SilentlyContinue).TcpTestSucceeded
# Windows：按需确认 MySQL 3307 / Redis / ES 9200 / Kafka 端口
```

### 3.3 启动（各仅一个实例）

- api：`D:\work\runtime-logs\start-api-v3.ps1`（`-Xms512m -Xmx1g`、`-Dserver.port=9902`、
  `--spring.config.additional-location=file:D:/work/runtime-logs/api-local.properties`）。
- backend：单独脚本，注入下载签名密钥与 `TRAFFIC_API_INTERNAL_TOKEN`，端口 9989。
- 两端启动后先看日志确认无 fail-fast，再继续。

### 3.4 端到端验证清单

| # | 验证 | 期望 |
| --- | --- | --- |
| 1 | 不带令牌直连 `GET /api/v3/es/readiness` | 403（或仅回环放行时远端拒绝） |
| 2 | 带 `X-Internal-Token` 调同一端点 | 200 且返回就绪信息 |
| 3 | backend 登录 → 大屏统计 / 告警 / 流水列表 | 200，`X-Data-Source` 与预期一致 |
| 4 | 导出提交 → 轮询 status → 下载 | 下载必须带下载令牌头；缺头 403；换用户令牌 403 |
| 5 | 重试 / 审批在同一机构、调岗后的机构 | 同机构可重提；跨机构被拒且状态不污染 |
| 6 | `GET /api/v3/export/capabilities`、指标 / 开关端点 | 200，开关删除接口需审批权限 |
| 7 | `POST /api/v3/sync/backfill` 超窗（>450 天） | 业务 `code != 200`，且不创建任务 |
| 8 | `POST /api/v3/sync/reconcile` 超桶数 | 被拒绝，不打满 DB/ES |
| 9 | `es-init.ps1 -Backfill`（不带 `-Activate`） | 按月提交 42 个分片，逐条打印成功；任一失败不切引擎 |
| 10 | 导出 CSV 含 `=SUM(...)` 开头 / 多行公式的字段 | 单元格前置 `'`，Excel/WPS 不执行公式 |
| 11 | 制造一次 ES bulk 失败 | 回灌任务 `FAILED` 且 `error` 含失败明细，游标不推进 |
| 12 | 制造一次 api 2xx 空响应体 | backend 统计回落 legacy，不返回空统计、不 500 |

> 第 9 / 11 / 12 项为破坏性验证，必须使用新建的测试 database 与测试索引，
> 结束后按第 5 节清理。

## 4. GitHub CI 触发与查看

- 工作流：backend `.github/workflows/ci.yml` 的 `push.branches` 含
  `car-monit-backend-java-V3`；api `.github/workflows/master.yml` 的 `push.branches` 含
  `car-monit-api-java-V3`。PR 门禁仍以 `master` 为基线。
- 触发方式：在门禁通过后 `git push origin <分支>`（两侧分别执行）。
- 查看结果：GitHub Actions 页面，或用 API 查询 runs/jobs。**凭据由运行环境或凭据管理器提供，
  不写入任何仓库文件、不回显到日志**；仓库为私有，匿名 API 返回 404 属正常。
- 需要重跑时可用 `workflow_dispatch`（backend `ci.yml` 支持 `java_base` / `rust_base` /
  `run_integration` 等输入）。

## 5. 清理

- 构建产物：`target/` 下本轮生成的 jar / class；日志：`D:\work\runtime-logs\` 下本轮日志。
- 测试数据：只在 3307 现有 MySQL 实例里新建的测试 database、ES 测试索引、Kafka 测试 topic。
- **一律直接删除，不放回收站**；`.codebuddy` 目录是项目数据，禁止删除。

## 6. 本轮已完成的静态 / 环境验证（未涉及服务重启）

| 项 | 结果 |
| --- | --- |
| 两侧 `compile` + `test` | 全部 `LASTEXITCODE=0` |
| `es-init.ps1` PowerShell 解析 | 0 错误 |
| 回灌窗口计算 | 426 天（14 个整月），据此把上限调为 450 并改为按月分片 |
| 4 条 legacy 机构过滤 SQL（MySQL 3307 实机） | 均执行成功，返回过滤后行数 |
| `sys_dept.sub_code` / `eps_id` / `org_id` 列 | 存在，SQL 未引用不存在的 `org_code` 列 |
| 虚拟机 openGauss 容器 / 5432 端口 | 容器在跑 / 端口可达 |
| WSL 发行版 | `openEuler-24.03-LTS-SP4` |
| CI 触发器分支配置 | 两侧 workflow 均包含对应 V3 分支 |
| 远端分支推送 / CI 触发 | **门禁通过后才执行，见 `03` 第 5.3 节** |

## 7. 一键启动脚本（backend + api + 中间件）

脚本 `scripts/v3/start-v3-all.ps1` 在两个 V3 工作树各存一份（内容一致），
并同步到 `D:\work\runtime-logs\start-v3-all.ps1` 便于与历史启动脚本一起调用。
**PowerShell 5.1 需 UTF-8 BOM**（文件已带 BOM），否则中文会被按 GBK 解析导致语法错误。

### 7.1 用法

```powershell
$S = 'd:\work\IdeaProjects\car-monit-backend-java-V3\scripts\v3\start-v3-all.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File $S -Status    # 只看状态
powershell -NoProfile -ExecutionPolicy Bypass -File $S             # 全量一键启动
powershell -NoProfile -ExecutionPolicy Bypass -File $S -Minimal   # 不主动启 ES/Kafka
powershell -NoProfile -ExecutionPolicy Bypass -File $S -Build     # 先 mvn package 再启动
powershell -NoProfile -ExecutionPolicy Bypass -File $S -Stop      # 只停本脚本启动的进程
```

其它参数：`-MemoryProfile Low|Normal`、`-TimeoutSec`、`-SkipOpenGauss`、`-SkipApi`、
`-SkipBackend`、`-EnvFile <本地凭据脚本>`、`-LogDir`。

### 7.2 启动顺序与幂等规则

```
openGauss(仅检查) → MySQL8 3307(仅检查) → Redis → Kafka → ES → api 9902 → backend 9989
```

- 每一步先查端口、再查 java 进程命令行（`ruoyi-admin.jar` / `pro-business-api-1.0.jar`），
  已在跑一律 `SKIP`，**不会重复启动第二个实例**。
- MySQL8 **只检查 3307**（当前由 WSL 端口转发提供），绝不另起 `mysqld` / 使用其它 data 目录；
  openGauss 同理只检查 5432，仅当设置 `V3_VM_PASSWORD` 时才尝试 SSH `docker start opengauss`。
- `-Stop` 只按 `D:\work\runtime-logs\v3-pids.json` 停止本脚本启动的进程，无该文件时不误杀。
- 日志统一 `D:\work\runtime-logs\v3-<name>.{out,err}.log`；启动前**直接删除**旧日志，不进回收站。

### 7.3 内存与中间件细节

| 项 | 处理 |
| --- | --- |
| 默认 `Low` 档 | 两个 java 各 `-Xms256m -Xmx768m`、ES 512m、Kafka 512m，预算 ≈2.6GB |
| `Normal` 档 | 两个 java 各 `-Xms512m -Xmx1g`，预算 ≈3.3GB |
| 宿主内存不足 | 启动时打印可用内存与预算并告警，建议 `-Minimal` 或先释放内存 |
| ES 限堆 | 首次运行幂等写入 `config\jvm.options.d\v3-heap.options`（`-Xms512m/-Xmx512m`） |
| Kafka | 用 `config\server.properties`（KRaft 单节点，`log.dirs=D:\work\kafka-data-20261108` 已 format）、`JAVA_HOME` 指向 JDK21、`KAFKA_HEAP_OPTS=-Xms256M -Xmx512M` |
| api / backend | JDK8；api 注入 ES/stats/sync/reconcile 开关，backend 注入 `VEHICLE_MONITOR_BASE_URL` |

### 7.4 凭据（不入库）

- `TRAFFIC_INTERNAL_TOKEN` / `TRAFFIC_API_INTERNAL_TOKEN`：两者不一致直接报错；
  都缺失时生成会话级随机值并同时注入两侧，保证 backend→api 不被守卫 403。
- `EXPORT_DOWNLOAD_SECRET`：缺失时生成会话级随机值（backend 启动 fail-fast 需要）。
- `CARMONIT_MYSQL_USERNAME/PASSWORD`：环境变量优先；未设时从既有
  `D:\work\runtime-logs\start-api-v3.ps1` 中按正则提取，**不在新脚本中写入明文**。
- api 的 openGauss 口令：需 `SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD`
  环境变量或非空的 `api-local.properties`；脚本检测到缺失会打印 WARN。
- 可选 `-EnvFile D:\work\runtime-logs\v3-env.ps1` 集中放本地凭据（该文件不入库）。

### 7.5 验证记录（2026-11-13）

| 验证 | 结果 |
| --- | --- |
| PowerShell 语法解析（三份副本） | 均 `PARSE_ERRORS=0` |
| `-Status` | 正确列出 7 个端口状态、端口属主（`wslrelay` / `redis-server`）、java 实例数与宿主可用内存 |
| 主流程零副作用演练 `-Minimal -SkipApi -SkipBackend -SkipOpenGauss` | 正确输出内存告警、令牌就绪、各服务 `SKIP`、汇总；退出码 0 |
| `-Stop`（无 PID 文件） | `WARN` 且不停止任何进程，退出码 0 |

> 本次**未执行全量启动**：演练时宿主可用内存仅 1.7~1.9GB（低于 Low 档 2.6GB 预算），
> 且 `api-local.properties` 为空文件（openGauss 口令未配置）。脚本已就绪，
> 补齐口令并释放内存后可直接执行全量启动。
