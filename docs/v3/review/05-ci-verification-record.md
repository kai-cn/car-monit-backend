# V3 GitHub CI 验证记录

> 与 `01` ~ `04` 配套，在两侧 V3 分支各存一份。
> 记录日期：2026-11-09。**不含任何口令、令牌、密钥明文。**

## 1. 门禁与推送

`03-independent-review-record.md` 第 5.3 节三轮独立复核均给出「可推送 / 无阻断项」后，
才执行推送；此前未向远端推送过本轮任何提交。

| 仓库 | 分支 | 推送范围 | 结果 |
| --- | --- | --- | --- |
| `kai-cn/car-monit-backend` | `car-monit-backend-java-V3` | `6db5fc2..07fdd65` | 成功 |
| `kai-cn/car-monit-api` | `car-monit-api-java-V3` | `22e3d19..ed14276` | 成功 |

工作流触发配置（本地核对）：

- backend `.github/workflows/ci.yml`：`on.push.branches` 含 `car-monit-backend-java-V3`。
- api `.github/workflows/master.yml`：`on.push.branches` 含 `["master", "car-monit-api-java-V3"]`。

凭据说明（不记录值）：两个仓库均为**私有**，匿名 API 返回 404；推送需要 `contents:write`。
本次提供的 fine-grained PAT 仅有读权限，推送返回
`403 Write access to repository not granted`；改用具备写权限的 classic token 后两条推送成功。
凭据仅通过进程内环境变量 / 一次性 URL 使用，未写入任何仓库文件、脚本、文档或日志。

## 2. CI 运行结果（如实）

| 仓库 | workflow | run id | event | head | status | conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| backend | `ci` | `42584712646` | push | `07fdd65` | completed | **failure** |
| api | `master` | `42584739339` | push | `ed14276` | completed | **failure** |

- backend：9 个 job，`changes` 为 `failure`，其余 8 个全部 `skipped`。
- api：14 个 job，`presence`、多个 `python/go/java/image` job 与 `Master Gate` 为 `failure`，
  其余 `skipped`。
- 所有失败 job 的 `steps` 数组为 **0**、`runner_name` 为空、`labels=ubuntu-latest`，
  从 `started_at` 到 `completed_at` 仅 2~3 秒，`actions/jobs/{id}/logs` 为空
  —— 即 **job 从未启动，不是任何构建/测试步骤失败**。

### 2.1 根因（check-run annotation 原文）

```
The job was not started because recent account payments have failed or your spending limit
needs to be increased. Please check the 'Billing & plans' section in your settings
```

两个仓库、所有失败 job 的 annotation 一致。另有 notice：
`The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026`（仅提示，非失败原因）。

### 2.2 与本次代码无关的佐证

1. 同一分支的**基线运行**也因同一原因失败：
   backend `42515763160`（`6db5fc2`）、api `42512378566`（`22e3d19`）均为 `failure`，
   且形态相同（job 秒级失败、steps=0）。
2. 仓库 Actions 权限正常：
   `GET /repos/{repo}/actions/permissions` → `enabled=true`、`allowed_actions=all`。
3. workflow 文件本地可读且触发器包含对应分支；`changes` / `presence` job 定义完整，
   并非 YAML 解析错误（解析错误会给出 annotation 文本，且不会创建 check-run）。
4. 失败发生在 runner 分配阶段，未执行 `actions/checkout` 及任何编译命令，
   因此无法归因到本轮任何 Java / SQL / PowerShell 改动。

### 2.3 结论

> **本次 CI 未实际执行任何构建或测试步骤，不能视为「CI 通过」，也不能视为「代码导致 CI 失败」。**
> 阻塞点是 GitHub 账号级账单 / 支出限额，需在 GitHub → Settings → Billing & plans
> 检查支付方式或提高 spending limit；恢复后对两个 run 执行 `Re-run all jobs`，
> 或用 `workflow_dispatch` 重新触发，再回填本文件的结果。

## 3. 本地可复现的替代验证（已通过）

在 CI 不可用期间，以下验证已在本机完成，命令见 `02-fix-record.md` 第 3 节、
`04-reproduction-guide.md` 第 6 节：

| 验证 | 结果 |
| --- | --- |
| 两侧 `mvn compile`（离线、JDK 8） | 均 `0` |
| 两侧 `mvn test`（离线、JDK 8） | 均 `0` |
| `es-init.ps1` PowerShell 语法解析 | 0 错误 |
| 4 条 legacy 机构过滤 SQL（MySQL 3307 实机） | 执行成功，返回过滤后行数 |
| 回灌窗口 14 整月天数计算 | 426 天，已据此修正上限与分片 |
| 虚拟机 openGauss 容器 / 5432 端口 | 容器在跑 / 端口可达 |

## 4. 复现 / 重跑步骤

1. 在 GitHub 处理 Billing & plans 后，打开
   `https://github.com/kai-cn/car-monit-backend/actions/runs/42584712646` 与
   `https://github.com/kai-cn/car-monit-api/actions/runs/42584739339`，执行 `Re-run all jobs`。
2. 或调用 `POST /repos/{repo}/actions/workflows/{workflow_id}/dispatches`
   （`ref` 填对应 V3 分支）重新触发。
3. 用带 `contents:write` / `actions:read` 权限的凭据查询
   `GET /repos/{repo}/actions/runs?branch=<分支>&per_page=3` 与
   `GET /repos/{repo}/actions/runs/{run_id}/jobs`，回填本文件第 2 节表格。
4. 若 job 仍 `steps=0` 且秒级失败，查
   `GET /repos/{repo}/check-runs/{check_run_id}/annotations` 获取 annotation 原文。

> 凭据一律由运行环境 / 凭据管理器提供，**不写入仓库文件、不回显到日志**。

## 5. 实机联调执行结果（2026-11-09）

### 5.1 执行动作

- 重新打包两侧可运行 jar（离线、JDK 8）：`pro-business-api-1.0.jar` 与
  `ruoyi-admin.jar` 均成功，时间戳为本轮编译后。
- 启动前核查：9902 / 9989 均无监听；ES(9200) / Kafka(9092) / Redis(6379) /
  MySQL(3307) 已在运行，**未重复启动**任何依赖服务。
- 各启动**一个** java 实例，均限制 `-Xms512m -Xmx1g`：
  - api 9902（沿用 `D:\work\runtime-logs\start-api-v3.ps1`）
  - backend 9989（`java -Dserver.port=9989 -jar ruoyi-admin.jar`）
- 两侧注入**同一个临时内部令牌**、backend 注入临时下载签名密钥；值不记录、不写入仓库文件。
- 端口就绪：backend 约 22 秒、api 约 36 秒；联调结束时两端口各 1 个 listener。

### 5.2 验证结果

| # | 验证项 | 结果 |
| --- | --- | --- |
| 1 | 不带令牌 `GET /api/v3/es/readiness` | **HTTP 403**，内部端点守卫生效 |
| 2 | 带正确令牌请求同一端点 | **HTTP 200 / code=200** |
| 3 | 超窗回灌 `POST /api/v3/sync/backfill`（2020-01-01 ~ 2026-01-01） | `code=500`，消息「回灌时间范围不能超过 450 天」，未创建任务 |
| 4 | backend 启动 | 成功；说明 `EXPORT_DOWNLOAD_SECRET` 与 `TRAFFIC_API_INTERNAL_TOKEN` 被正确加载（缺失会 fail-fast） |
| 5 | backend 登录 / 需认证的大屏链路 | **未完成**：本机测试账号口令不符合系统强密码策略，若干常见候选口令均返回「用户不存在/密码错误」；未继续猜测、未伪造登录态 |

### 5.3 结论与边界

- 本轮实机验证覆盖：新构建产物可启动、内部端点令牌守卫、回灌窗口上限（第二轮回补项）、
  backend 启动期安全配置加载。
- **未覆盖**：需认证的大屏统计、导出提交-轮询-下载、审批与重试链路。这些在前序会话已跑通
  （`D:\work\runtime-logs\` 有历史产物），本轮代码改动后应在取得正确测试账号口令后，
  按 `04-reproduction-guide.md` 第 3.4 节补跑并追加记录。
- CI 侧因账号账单未执行任何 job（第 2 节），本地联调结果**不能替代 CI 门禁**。
- 本轮未新建测试库 / 测试索引 / 测试数据；推送产生的 4 个临时日志已直接删除（未进回收站）。
- **2026-11-10 已补齐 5.3 节列出的未覆盖项**：多角色越权 / 审批链路见本文第 7 节
  （由 13:16 的并行会话提交 `2a8957f` 记录），admin 视角、机构维度 SQL 下推与
  api 侧边界重跑见 `06-authenticated-e2e-record.md`；本节保留首轮联调的原始状态以便追溯。

## 6. CI 重试记录（2026-11-10）

按用户要求重新触发两仓库 CI，方式为 `workflow_dispatch`（`ref` 为各自 V3 分支），
而非 `rerun`，以排除旧 run 缓存影响。

| 仓库 | workflow | 新 run id | event | head | conclusion |
| --- | --- | --- | --- | --- | --- |
| `kai-cn/car-monit-backend` | `ci.yml` | `42735777383` | workflow_dispatch | `2b08d3f` | **failure** |
| `kai-cn/car-monit-api` | `master.yml` | `42735782495` | workflow_dispatch | `76eddf4` | **failure** |

- 首个 job（backend `changes`、api `presence`）均为 `failure`，`steps=0`、`runner_name` 为空，
  其余 job 全部 `skipped`，与第 2 节首次运行形态完全一致。
- check-run annotation 仍为：
  `The job was not started because recent account payments have failed or your spending limit needs to be increased.`
- **结论：账号账单 / 支出限额未恢复，重试不改变结果；再次重试在账单修复前没有意义。**
  需先在 GitHub → Settings → Billing & plans 处理付款方式或提高 spending limit，
  再执行 `Re-run all jobs` 或重新 `workflow_dispatch`，并回填本节。
- 本地替代验证（编译 / 单测 / SQL / 脚本语法 / 实机联调）状态见第 3、5 节，未因此发生变化。

## 7. 认证链路补跑（2026-11-10，补齐第 5.3 节未覆盖项）

> 本节补跑 `04-reproduction-guide.md` 第 3.4 节第 3/4/5/6 项。沿用 11-09 会话启动的
> api(9902) / backend(9989) 实例（代码无变更，仅 docs 提交，未重启、未重复启动）。

### 7.1 登录与测试账号

- `admin / Admin@2025-` 登录 9989 成功（登录接口仅在请求带 code 时才校验验证码，脚本联调不带 code）；
  `getInfo` 返回 `roles=[admin]`。
- 经 `POST /system/user` 创建用户失败，报
  `IndexOutOfBoundsException: No group 2`（HTTP 500）——**既有框架缺陷，记为 K-08**：
  p6spy 包装驱动（`jdbc:p6spy:mysql://`）对含 BCrypt 口令 `$2a$10$...` 的 SQL 做正则格式化，
  `$2` 被当组引用。与本轮 V3 改动无关，改用 MySQL CLI 直插 `sys_user` / `sys_user_role` 建号。
- 测试账号（口令同 admin 策略，BCrypt 同 admin 行复制）：
  - `v3audit_view`：common 角色，万安收费所（dept 25424）；
  - `v3audit_mgr`：project_manager 角色，吉安东管理中心（dept 25367）。
- **发现迁移遗漏，记为 K-09**：V3 新增权限 `manager:bigscreen:export` / `exportFull` /
  `exportApprove` 未播种 `sys_menu`，任何角色均无法取得导出/审批入口。联调补插
  menu 3020~3022（F 类型，父 3005 大屏）并授权 role 132（mgr）与 role 2（view，
  用于越权用例）；另授 `monitor:server:list`（menu 112）给两角色用于运维端点用例。

### 7.2 验证矩阵（全部符合预期）

| # | 用例 | 结果 |
| --- | --- | --- |
| 1 | admin `getInfo` / 大屏统计 / metrics | 200；`carStatistics` 命中缓存 `X-Data-Source: CACHE`，metrics 显示 cacheHitRate=0.96、熔断全部 CLOSED |
| 2 | view 首次 `carStatistics` | 200，`X-Data-Source: API`（两级缓存 MISS→回源→后续命中，链路正确） |
| 3 | view（无导出权限）`POST /export/display` | **403**，权限门生效 |
| 4 | mgr 提交 display 导出（snapshot，2h 窗口） | 200，taskId=f3e8eb88…，轮询一次即 `done`（totalExported=0，该窗口 ES 无数据，链路通） |
| 5 | `POST /export/{taskId}/download-url` | 200，返回 15 分钟 `downloadToken` + `tokenHeader: X-Export-Download-Token` |
| 6 | 下载缺令牌头 | **403** |
| 7 | 下载带损坏令牌 | **403**（「下载令牌格式非法」） |
| 8 | 下载：有效令牌 + 换登录用户（view 用 mgr 的令牌） | **403**（「下载令牌与当前登录用户不匹配」，B-01 令牌绑定用户实证） |
| 9 | 下载：本人 + 有效令牌 | **200**，132B gz 文件（0 行空导出） |
| 10 | 跨机构 retry：view（万安）重试 mgr（吉安东）的任务 | **403**（「无权访问该导出任务」，B-02 实证） |
| 11 | view 开安全开关 `gray/export-approval?enabled=true`（无 exportApprove 权限） | **403**（B-04 实证） |
| 12 | mgr 开 export-approval | 200，开关生效 |
| 13 | view 提交 full 导出 | 200，`pending_approval`；快照 `fuzzyFields` 被服务端自动注入 `orgcode=0000001100530008-001`（本机构收敛） |
| 14 | mgr 审批列表 / approve | 200；审批通过自动提交任务 aeac45b3…，轮询 `done` |
| 15 | view 再提交 full（fee）→ mgr reject（带 reason） | 200；审批单状态更新为 rejected |
| 16 | view `DELETE /switches/export-approval`（有 server:list 无 exportApprove） | **403**（B-04 删除路径实证） |
| 17 | view 翻转非安全开关 `stats-api-first=false` → 恢复 true | 均 200（安全/非安全开关权限不对称，符合设计） |
| 18 | admin `DELETE /switches/export-approval` | 200，恢复默认值 false |

### 7.3 清理与结论

- 导出产物（3 个 0 行 `.csv.gz`）已从 `%TEMP%\car-monit-export` 直接删除，未进回收站；
  `export-approval` 等开关全部恢复默认；Redis 中审批单/任务元数据随 TTL 过期，不手工清理。
- 测试账号 `v3audit_view` / `v3audit_mgr` 与 menu 3020~3022 授权**保留**（后续联调复用），
  如需回收：`delete from sys_user where user_name like 'v3audit%';` + 对应 `sys_user_role` /
  `sys_role_menu(3020~3022)` 行。
- **第 5.3 节的「未覆盖」三项（认证后大屏统计、导出提交-轮询-下载、审批与重试链路）本轮全部补齐通过**；
  破坏性用例（指南 3.4 第 9/11/12 项）仍按原计划待专用测试库执行，不在本机生产联调库做。
- 新增遗留 K-08（p6spy 建用户 500）/ K-09（导出权限未播种）见 `01-code-audit-record.md` 第 6 节。
