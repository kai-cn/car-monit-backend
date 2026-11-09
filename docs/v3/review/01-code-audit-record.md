# V3 代码审阅记录

> 本文件在 `car-monit-backend-java-V3` 与 `car-monit-api-java-V3` 两个工作树的
> `docs/v3/review/` 下各存一份，内容一致，便于两条分支独立追溯。
> 记录日期：2026-11-09。范围：两条 V3 分支本轮「代码审核 → 修复 → 独立复核」全过程。
> **本文件不含任何口令、令牌、密钥；凭据一律由运行环境注入，不落盘到仓库。**

## 1. 审阅依据与范围

设计文档与运行约束：

- `car-monit-api-java-V3/docs/8亿级大表查询架构设计与落地方案.md`
- `car-monit-api-java-V3/docs/v3-auth-options.md`（运维端点无鉴权风险说明）
- 两侧 `docs/decisions-v3.md`、`docs/ops-runbook-v3.md`、`docs/ci-cd-pipeline-plan.md`
- `car-monit-api-java-V3/docs/CI-CD-PIPELINES.md`

审阅对象：

| 工作树 | 分支 | 角色 | 主库 |
| --- | --- | --- | --- |
| `car-monit-backend-java-V3` | `car-monit-backend-java-V3` | 后台管理 / 大屏展示层，HTTP 调 api | MySQL 8 |
| `car-monit-api-java-V3` | `car-monit-api-java-V3` | 数据层（openGauss / ES / Kafka / Redis） | openGauss |

审阅方式：按模块逐文件静态审阅 → 分类分批改码并编译 → **三轮彼此独立、只读、不修改文件**的
`code-explorer` 会话复审。每轮复审员与修复者分离，输入为工作树最终代码与明确的问题清单，
输出必须带「文件路径:行号」证据。

门禁规则（本轮追加）：**三轮独立复核全部确认无阻断项之后，才允许推送远端分支触发 CI。**
门禁状态与结论见 `03-independent-review-record.md`。

## 2. 首轮审阅发现台账（修复者自查）

### 2.1 backend（后台管理 / 大屏）

| 编号 | 级别 | 问题 | 主要证据 |
| --- | --- | --- | --- |
| B-01 | P0 | 导出下载令牌允许放在 query 参数，且不绑定登录用户，可越权下载他人任务 | `BigScreenExportController.download`、`BigScreenExportService.verifyDownload`、`DownloadTokenService` |
| B-02 | P0 | `retry` / `resume` / `approve` 沿用历史机构过滤，用户调岗后仍可导出原机构数据 | `BigScreenExportService.retry`、`approve`、`ExportTaskMeta` |
| B-03 | P1 | 审批状态机允许 `APPROVING → APPROVING` 重入 | `ExportApprovalStateMachine` |
| B-04 | P1 | 运维「删除类」写接口可不校验审批权限就清掉 `export-approval` 覆盖，关闭强管控 | `BigScreenOpsController` |
| B-05 | P1 | 过滤字段带首尾空白的键可绕过白名单，下发给 api 时未 trim | `ExportPolicy.validateFuzzy`、`BigScreenExportService` |
| B-06 | P1 | 两级缓存单飞锁按 key 对象取锁导致竞态；回源失败时未用 L2 stale 兜底 | `TwoLevelCache` |
| B-07 | P1 | 字典版本在 Redis key 重置 / 不可用时可能回退到更小值，旧缓存复活 | `DictVersionService` |
| B-08 | P1 | 统计缓存 key 缺机构 / 逃费类型维度；带机构条件仍走 api，导致跨机构串数据 | `BigScreenStatsService`、`BigScreenCacheSupport` |
| B-09 | P1 | 2xx 空响应体未判契约违规；income 单侧时间未校验；熔断按重试次数而非请求计数；灰度哈希只取首字节取模偏斜；限流 key TTL 不补导致永久 key | `TrafficApiHttpClient`、`ResilientApiExecutor`、`TrafficQueryContract`、`FeatureSwitchService`、`RedisCache` |
| B-10 | P1 | 与 api 侧内部端点守卫配套：backend 所有出站调用需注入 `X-Internal-Token` | `TrafficApiHttpClient`、`ApplicationConfig` |

### 2.2 api（数据层）

| 编号 | 级别 | 问题 | 主要证据 |
| --- | --- | --- | --- |
| A-01 | P0 | `/api/v3/**` 与 `/api/v1/large/export/**` 无鉴权，可切查询引擎、触发重负载回灌、删除 ES 孤儿文档 | `TrafficAdminV3Controller` 类注释、`docs/v3-auth-options.md` |
| A-02 | P1 | `bulkIndex` 失败 / 部分失败被吞掉后仍返回 `DONE` 并推进回灌游标，GaussDB 有而 ES 无，数据永久不一致 | `EsBulkIndexer`、`EsBackfillService` |
| A-03 | P1 | 孤儿文档对多索引 `*-read` 别名执行 delete 被 ES 拒绝，漂移永远无法收敛 | `TrafficReconciliationService.deleteFromEs` |
| A-04 | P1 | `DRIFT` 桶只补偿一次，回灌失败后漂移被永久固化 | `TrafficReconciliationService.alreadyDrift` |
| A-05 | P1 | Kafka 消费失败静默 `ack`，事件丢失且默认对账关闭时无人发现 | `SearchSyncConsumer` |
| A-06 | P1 | 回灌 / 对账 / 孤儿清理无时间窗口与桶数限制，单请求可打满 DB / ES | `TrafficAdminV3Controller`、各 Service |
| A-07 | P1 | 普通 `from/size` 查询也创建 PIT，异常路径不关闭，占满搜索上下文 | `TrafficSearchService` |
| A-08 | P1 | 导出 CSV 公式注入；颜色码直接拼 `LIKE '%_<code>'`，传 `%` 退化为全表 | `ExportTaskService.CsvWriter`、`runFull` |
| A-09 | P1 | 导出失败 / 超时留下半成品 `.csv.gz`，重启后被 `resolveFinishedFile` 当成完成文件下载 | `ExportTaskService` |
| A-10 | P1 | 展示字段导出的页大小被在线分页上限钳成 100，深翻页性能退化 | `ExportTaskService.runDisplay`、`TrafficSearchService.searchForExport` |
| A-11 | P1 | 导出任务状态 / 提交响应把服务端绝对路径 `filePath` 返回给调用方 | `ExportV3Controller` |

## 3. 第一轮独立复审发现（2 个独立会话）

复审员基于工作树最终代码逐条验证，输出「确认修复 / 仍有问题 / 新回归」。

### 3.1 backend：确认修复 6 条

下载令牌绑定用户、审批状态机与单测一致、过滤字段空白键拒绝 + trim、
`TwoLevelCache` 锁条带与括号配平 + L2 stale、令牌注入不影响 POST 头、
灰度哈希 / 限流 TTL / income 时间 / lambda 捕获与 `X-Data-Source`。

### 3.2 backend：仍有问题 5 条

1. `approve` 硬编码 `adminScope=true`，忽略 `storedOrgCode`；快照无 orgcode 时机构过滤完全不下发，放大为全量导出。
2. `scopedFiltersForResubmit` 整体绕过 `ExportPolicy.applyOrgScope`，接受 `"-1"`；管理员重试他人任务按历史 admin 标记跳过收敛。
3. `clearGray` / `clear` 未调用 `assertSecuritySwitchAllowed`，仅监控查看权限即可关掉审批开关。
4. `DictVersionService.bump` 中 `localBumps.merge(domain, next, Math::max)` 丢弃返回值，写路径版本不单调。
5. 2xx 空响应体仍被静默当成空列表；非 retryable 错误不参与熔断计数（后者符合设计「熔断只统计超时/网络/5xx」，判为可接受）。

### 3.3 backend：新回归 1 条

- income 缓存 key 仍缺 `escapedType`；`carStatistics` 无 `orgCode` 回落，而 api 的 escape 端点只支持 `orgId`，
  仅传 orgCode 时仍拿全机构数据。

### 3.4 api：确认修复 7 条

`EsDocRef` 全链路自洽、bulk 失败不再静默推进游标、DRIFT 可重复补偿且 `REPAIRED` 落库、
消费失败不再静默 ack、`.part` 原子发布与下载链路一致、导出其余修复 + 去掉 `filePath`、
PIT 首轮/后续轮次与普通分页均可用且 Guard 会被扫描。

### 3.5 api：仍有问题 3 条

1. 孤儿回查把 ES `_id`（String）绑到 `bigint` 主键列，openGauss 报类型不匹配，异常被吞成 `return 0`。
2. CSV 公式注入只看首字符，未覆盖多行单元格与 `-1+1` 这类伪负数表达式。
3. 「backend 侧未注入 `X-Internal-Token`」—— **经核为误报**：该会话检索的是
   `car-monit-backend-new` 主工作树而非 `car-monit-backend-java-V3` 工作树；
   注入实际存在于 `TrafficApiHttpClient` 与 `ApplicationConfig`，已编译验证。

### 3.6 api：新回归 2 条

1. `REPAIRED` 条件未排除 `ERROR`，DB/ES 故障会被写成「已修复」；且状态永久停在 `REPAIRED`。
2. 新加的 365 天回灌窗口把 `es-init.ps1` 的 13+1 个月初始化整体挡掉。

## 4. 第二轮独立复核发现（2 个独立会话）

两会话门禁结论均为「**暂不可推送**」。

### 4.1 backend：阻断 2 条

1. 【新回归】`approve` 新增的重复 `validateFullFilters` 会在能力探测失败 / 返回 `none()` 时误拒合法审批，
   把请求回退成 `PENDING`（入队时已校验过同一条件）。
2. 【仍有问题】`DictVersionService` 只在本地抬升版本，未写回 Redis；其它节点或本节点重启后
   `readRemote` 仍读到小版本，`segment()` 切回旧 key。

### 4.2 backend：非阻断建议 2 条

- `localBumps.put` 覆盖并发 `merge` 结果，可能把大版本改小。
- `orgCode` 回落 legacy 后，4 条统计 SQL 均无 `orgCode` 条件，仍返回全机构统计。

### 4.3 api：阻断 1 条 + 新回归 1 条

1. 【阻断】`es-init.ps1 -Backfill` 默认窗口为 14 个整月：实测 `2025-11-01 00:00:00` →
   `2027-01-01 00:00:00` = **426 天**（理论区间 424~428 天），大于 `backfill-max-days: 400`，
   三张表回灌全部被拒。
2. 【新回归】脚本只 catch 传输异常；管理端点失败时返回 HTTP 200 + `code:500`，PowerShell 不进 catch，
   随后 `-Activate` 会在数据未回灌时切到 `es`。

### 4.4 api：非阻断 4 条

`EsBulkIndexer` 异常明细被外层包装丢失；Kafka 10 次重投会重复插 DLQ 且类注释与 Boot 默认
`enable-auto-commit=false` 不符；`CAST(pk AS VARCHAR)` 使主键索引失效（单桶 1 分钟窗口 + 单次上限，
判为可接受）；`ERROR` 覆盖 `DRIFT` 审计且回灌 `tasks` 无清理。

## 5. 第三轮最终门禁复核发现（2 个独立会话）

两侧门禁结论均为「**可推送 / 无阻断项**」。详见 `03-independent-review-record.md`。
剩余均为非阻断的注释漂移、未使用导入、脚本日志措辞，以及下列**既有遗留项**。

## 6. 已知遗留项（非本轮引入，不阻断本次交付，如实留痕）

| 编号 | 侧 | 说明 |
| --- | --- | --- |
| K-01 | backend | `hasOrgScope` 把 `orgId` / `escapedType` 也算作机构维度，但 `carAudit` / `incomeStatistic` / `getCarConfirm` 的 legacy SQL 只补了 `orgCode`；仅传 `orgId` 时仍可能返回全机构聚合。需结合业务列（`car_confim_free` / `car_aduit_free` 是否有 `escaped_type`）确认后再下推。 |
| K-02 | backend | 管理端点存在未接 fallback 的链路（如 `exportStatus` 2xx 空体）会落到通用 500，统计链路有 `withFallback` 不受影响。 |
| K-03 | api | `CAST(pk AS VARCHAR)` 使主键索引失效；依赖 `time` 列索引，需在大数据量下监控慢 SQL。 |
| K-04 | api | `search_sync_dlq` 无 `event_id` 唯一约束，Kafka 重投会插入重复死信（写 DLQ 时主键冲突被吞）。 |
| K-05 | api | `EsBackfillService.tasks` 无清理，长期 DRIFT 会按每轮最多 12 个任务累加。 |
| K-06 | api | 管理端点失败返回 HTTP 200 + 业务 `code:400/500`，调用方必须按 body.code 判断；`es-init.ps1` 已按此实现。 |
| K-07 | api | `DictVersionService` 版本写回为无条件 `SET` 而非 CAS，极端组合（key 重置 + 多节点并发 bump + SET 乱序）存在最终一致窗口；建议后续改 Lua。 |
