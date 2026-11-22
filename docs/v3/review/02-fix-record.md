<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# V3 代码修复记录

> 与 `01-code-audit-record.md` 配套，在两侧 V3 分支各存一份。
> 记录日期：2026-11-09。**不含任何口令、令牌、密钥。**

## 1. 提交清单（`git log --oneline`，均为本地提交，未推送）

### 1.1 `car-monit-backend-java-V3`

| 提交 | 标题 | 对应审阅项 |
| --- | --- | --- |
| `6db5fc2` | fix(ci): rust 断言复原并按 api 方式固定 job 时区（本轮基线） | 基线 |
| `cf999cb` | fix(v3-export): 下载令牌强制绑定登录用户、重提重新收敛机构范围、审批与开关加固 | B-01 ~ B-05 |
| `058ebd2` | fix(v3-core): 单飞锁竞态、字典版本回退、统计跨机构串数据、熔断与限流计数 | B-06 ~ B-09 |
| `bb03187` | feat(v3-security): backend→api 全链路注入 X-Internal-Token | B-10 |
| `d733d2c` | fix(v3-review): 独立复审回补——重提机构收敛、审批快照、空响应契约 | 第一轮复审 3.2 / 3.3 |
| `6a91577` | fix(v3-review2): 第二轮复核阻断项——审批重复校验、字典版本跨节点回退、机构下推 | 第二轮复核 4.1 / 4.2 |
| 同批 | docs(v3-review): 审阅/修复/复核记录 + 注释与未使用导入清理（零行为变更） | 第三轮复核非阻断项 |

### 1.2 `car-monit-api-java-V3`

| 提交 | 标题 | 对应审阅项 |
| --- | --- | --- |
| `22e3d19` | fix(v3-migration): 回滚增量统计用 timestamp 字面量，兼容 openGauss（本轮基线） | 基线 |
| `6adebf6` | fix(v3-security): 内部端点令牌鉴权 + GaussDB/ES 一致性链路修复 | A-01 ~ A-11 |
| `ebf9c59` | fix(v3-review): 独立复审回补——回灌窗口、对账状态机、主键类型与 CSV 注入 | 第一轮复审 3.5 / 3.6 |
| `1854c35` | fix(v3-review2): 第二轮复核阻断项——回灌窗口、脚本分片与业务码校验 | 第二轮复核 4.3 |
| 同批 | docs(v3-review): 审阅/修复/复核记录 + 注释与日志措辞清理（零行为变更） | 第三轮复核非阻断项 |

## 2. 分批修复明细

### 2.1 第一批：安全边界（P0）

- **下载令牌**：`BigScreenExportController.download` 只接受 `@RequestHeader` 令牌，移除 query 兼容；
  `BigScreenExportService.verifyDownload` 校验 `tokenUserId == loginUserId` 后才允许下载；
  `DownloadTokenService` HMAC 绑定 `taskId|userId|expireAt`。
- **内部端点守卫**：新增 `InternalEndpointGuardConfig`，对 `/api/v3/**`、
  `/api/v1/large/export/**` 校验 `X-Internal-Token`；未配置令牌时只放行回环地址。
  配置名 `traffic.security.internal-token`，环境变量 `TRAFFIC_INTERNAL_TOKEN`。
- **出站注入**：`TrafficApiHttpClient` 按场景 RestTemplate 与 `ApplicationConfig` 的下载专用
  RestTemplate 统一加 `X-Internal-Token` 拦截器；backend 侧环境变量 `TRAFFIC_API_INTERNAL_TOKEN`。
- **响应脱敏**：`ExportV3Controller.submit/status` 经 `publicView` 移除 `filePath`。

### 2.2 第二批：导出权限与状态机

- `retry` / `resume` / `approve` 统一走 `scopedFiltersForResubmit`（最终实现复用
  `ExportPolicy.applyOrgScope`）：retry 按**当前登录账号**重新收敛机构；approve 保留
  **申请时冻结的授权快照**，拒绝无有效机构快照的审批，且不允许审批人扩大范围。
- `ExportApprovalStateMachine` 禁止 `APPROVING → APPROVING`；`ExportApprovalStateMachineTest` 同步断言。
- `assertSecuritySwitchAllowed` 覆盖 `overrideGray` / `override` / `clearGray` / `clear` 四个写接口。
- `ExportPolicy.validateFuzzy` 拒绝带首尾空白的键；下发时用 `entry.getKey().trim()`。

### 2.3 第三批：缓存、字典版本、统计一致性

- `TwoLevelCache`：256 个固定锁条带 + 双检；L2 stale 兜底；`triggerRefresh` 用 try/catch 包裹
  `refreshPool.submit`，线程池拒绝时释放 `refreshing` 标记。
- `DictVersionService.bump`：`Math.max(next, floor+1)` → `localBumps.merge(..., Math::max)`
  → 版本被抬升时 `setCacheObject` 带 TTL 写回 Redis → 写本地，保证单节点严格单调与跨节点收敛。
- `BigScreenStatsService`：三个缓存 key 补齐 `orgId` / `orgCode` / `escapedType`；
  `hasOrgScope` 为真时回落 legacy 并标 `X-Data-Source: LEGACY_DB`；`carStatistics` 在
  仅传 `orgCode` 时直接回落（api 的 escape 端点只支持 `orgId`）。
- **legacy SQL 下推**（`CarConfimFreeMapper.xml` / `CarAduitFreeMapper.xml` 共 4 条）：
  `getCarStatistics` / `getCarAudit` / `getCarConfirm` 用 `EXISTS (sys_dept d where ... d.sub_code
  like concat(#{orgCode},'%'))`，`incomeStatistic` 复用已 join 的 `d.sub_code`；
  替换原本被注释掉的、指向不存在列 `d.org_code` 的条件。
- `FeatureSwitchService` 灰度改用 SHA-256 前 8 字节取模；`RedisCache` 限流 key 每次 INCR 后补 TTL；
  `ResilientApiExecutor` 熔断按请求计数；`TrafficQueryContract` 补 income 单侧时间校验。

### 2.4 第四批：GaussDB ↔ ES 一致性

- `EsBulkIndexer.bulkIndex`：建索引失败、bulk 部分失败、调用异常一律抛异常；
  `catch (IllegalStateException)` 优先重抛以保留「首个失败 id + 原因」明细。
- `EsBackfillService.run`：仅在 `indexed == docs.size()` 后推进游标，否则任务置 `FAILED`。
- `TrafficReconciliationService`：孤儿扫描保存 `EsDocRef(id, index)`，按**具体月索引**删除；
  回查 SQL 把主键 `CAST(... AS VARCHAR)` 以兼容 `bigint` / `varchar` 两类主键；
  `alreadyDrift` 只认 `DRIFT`，`REPAIRED` 仅在 `status=="OK"` 且上轮 DRIFT 时写入；
  DRIFT 桶允许重复补偿；对账窗口 365 天 + 每表 10000 桶上限。
- `SearchSyncConsumer`：`indexOne` 返回 false 时抛异常（不再静默 ack），car-warning 分支写 DLQ。
- `EsBackfillService.submit` 用 `max(query.max-days, sync.backfill-max-days)` 校验窗口。

### 2.5 第五批：导出生命周期与查询

- `ExportTaskService`：写 `<taskId>.csv.gz.part`，成功才 `renameTo` 发布并置 `done`；
  失败 / 取消 / 超时删除 `.part`，`resolveFinishedFile` 只认最终文件；终态任务不可取消。
- CSV 转义 `looksLikeFormula` 逐行检查行首 `= + - @ TAB CR`，`isNumericLiteral` 放行合法负数；
  颜色码校验 `[0-9]{1,3}` 防止 LIKE 通配符退化。
- `TrafficSearchService`：只在 `searchAfter` 或 `keepPit` 时创建 PIT，异常路径一律关闭；
  `searchForExport` 允许导出专用页大小（1000），校验时临时钳到在线上限再恢复。
- `es-init.ps1 -Backfill`：按月分片（默认 14 片 × 3 表 = 42 个任务，单任务窗口 1 个月）；
  校验 HTTP 200 中的业务 `code`；存在失败分片时拒绝 `-Activate` 切换 `es`；
  从 `TRAFFIC_INTERNAL_TOKEN` 取令牌并加到 backfill / readiness / activate 三处请求头。

## 3. 验证记录（可复现命令）

> 口令、令牌一律由运行环境/凭据管理器注入，以下命令行不写明文。
> 例：MySQL 用 `--password=$env:MYSQL_PWD`；GitHub 凭据用本机凭据管理器或 CI 令牌。

### 3.1 编译与单元测试

```powershell
$env:JAVA_HOME = 'D:\jdk\jdk1.8.0_202'
$M = 'D:\work\apache-maven\bin\mvn.cmd'
$B = 'd:\work\IdeaProjects\car-monit-backend-java-V3\pom.xml'
$A = 'd:\work\IdeaProjects\car-monit-api-java-V3\pom.xml'

& $M -f $B -o -B -q -DskipTests -pl ruoyi-common,ruoyi-system,ruoyi-framework,ruoyi-admin -am compile
& $M -f $B -o -B -q -pl ruoyi-common,ruoyi-system -am test
& $M -f $A -o -B -q -DskipTests -pl pro-business-api -am compile
& $M -f $A -o -B -q -DskipTests=false -pl pro-business-api -am test
```

结果：四步 `LASTEXITCODE` 均为 `0`。测试日志中的
`TwoLevelCache - [缓存] 回源失败 key=stale reason=api down` 是
`TwoLevelCacheTest.loaderFailureReturnsRetainedStaleValue` 的预期断言输出，非失败。

### 3.2 PowerShell 脚本语法

```powershell
$t = $null; $e = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  'd:\work\IdeaProjects\car-monit-api-java-V3\scripts\v3\es-init.ps1', [ref]$t, [ref]$e) | Out-Null
$e.Count   # 0
```

### 3.3 回灌窗口实测

```powershell
$now = Get-Date '2026-11-09'
$start = $now.AddMonths(-12).ToString('yyyy-MM-01 00:00:00')  # 2025-11-01 00:00:00
$end   = $now.AddMonths(2).ToString('yyyy-MM-01 00:00:00')    # 2027-01-01 00:00:00
([datetime]$end - [datetime]$start).TotalDays                 # 426
```

14 个整月理论区间 424~428 天，故 `backfill-max-days` 由 400 调为 450，并让脚本按月分片。

### 3.4 legacy 机构过滤 SQL（MySQL 8 / 本机 3307 库）

```powershell
& 'D:\work\mysql-8.0.30-winx64\bin\mysql.exe' `
  --host=127.0.0.1 --port=3307 --user=root --password=$env:MYSQL_PWD `
  --database=carmonitdb -N -e "<4 条带 EXISTS/sub_code 的统计 SQL>"
```

实机结果（本机数据集，仅证明语法与过滤生效）：
`stats=273`、`confirm=60`、`audit=273`、`incomeStatistic=144`。
同时确认 `sys_dept.sub_code varchar(500)`（41 行非空）、`car_except_record.eps_id bigint`、
`car_confim_free.org_id varchar(100)` 三列存在，SQL 中未引入不存在的 `org_code` 列。

### 3.5 环境连通性核查

| 项 | 方法 | 结果 |
| --- | --- | --- |
| 虚拟机 openGauss 容器 | Python `paramiko` 连 192.168.56.10:22 执行 `docker ps --format={{.Names}}` | 输出 `opengauss`，容器在跑 |
| openGauss 端口 | `Test-NetConnection 192.168.56.10 -Port 5432` | `True` |
| WSL 发行版 | `wsl -l -q` | `openEuler-24.03-LTS-SP4` |
| 本机 api 服务 9902 | `Get-NetTCPConnection -LocalPort 9902 -State Listen` | 核查时未监听（未重复启动） |
| CI 触发器 | 读两侧 workflow | backend `.github/workflows/ci.yml` push 含 `car-monit-backend-java-V3`；api `.github/workflows/master.yml` push 含 `car-monit-api-java-V3` |

## 4. 第三轮复核后的零行为变更收尾

- 删除 `BigScreenExportService` 未使用的 `TrafficQueryContract` 导入。
- 修正 `approve` 注释（说明「去掉的是重复探测，最终能力校验仍由 `submitInternal` 承担」）。
- 修正 `TrafficAdminV3Controller` 类注释中的回灌窗口说明。
- 修正 `es-init.ps1` 日志把布尔值称作「数」的措辞。

以上四项不改动任何运行时行为，随文档同批提交，提交前后均重新编译通过。

## 5. 未在本轮修复的项

见 `01-code-audit-record.md` 第 6 节「已知遗留项」（K-01 ~ K-07），均为既有问题或
非阻断的运维/性能约束，已如实留痕，不隐瞒、不计入「确认无问题」的范围之外。
