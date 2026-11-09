# V3 独立复核（review）记录

> 与 `01-code-audit-record.md` / `02-fix-record.md` 配套，在两侧 V3 分支各存一份。
> 记录日期：2026-11-09。**不含任何口令、令牌、密钥。**

## 1. 复核机制

| 项 | 说明 |
| --- | --- |
| 复核员 | `code-explorer` 子代理，每侧每轮一个**全新独立会话**，与修复者会话隔离 |
| 权限 | 只读：明确要求「不得修改文件」，仅返回结论与证据 |
| 输入 | 工作树最终代码绝对路径、目标提交号、精确问题清单与重点核对项 |
| 输出要求 | 每条结论必须附「文件路径:行号」证据；给出「确认修复 / 仍有问题 / 新回归」分类；第二轮起必须给出「可推送 / 暂不可推送」门禁结论 |
| 门禁规则 | **代码没有 review 完成并确认无阻断项之前，不推送远端分支、不触发 CI** |
| 轮次 | 共三轮；每轮发现阻断项 → 回补 → 重新编译验证 → 下一轮重新复核 |

## 2. 门禁状态机

| 轮次 | backend 结论 | api 结论 | 处置 |
| --- | --- | --- | --- |
| 第一轮独立复审 | 确认修复 6 / 仍有问题 5 / 新回归 1 | 确认修复 7 / 仍有问题 3（含 1 误报）/ 新回归 2 | 回补，提交 `d733d2c` / `ebf9c59` |
| 第二轮独立复核 | **暂不可推送**（阻断 2） | **暂不可推送**（阻断 1 + 新回归 1） | 回补，提交 `6a91577` / `1854c35` |
| 第三轮最终门禁 | **可推送，无阻断项** | **可推送，无阻断项** | 允许推送两分支触发 CI |

三轮之间均执行了编译 + 单元测试 + 针对性实机验证，见 `02-fix-record.md` 第 3 节。

## 3. 第一轮独立复审（回补前 → 回补后）

### 3.1 backend 结论要点

- 确认修复：下载令牌绑定用户、审批状态机与单测一致、过滤字段空白键、`TwoLevelCache`
  锁条带与 L2 stale、令牌拦截器、灰度/限流/income/lambda。
- 仍有问题：`approve` 硬编码 `adminScope=true` 可放大为全量导出；
  `scopedFiltersForResubmit` 绕过 `applyOrgScope` 且接受 `"-1"`；
  `clearGray` / `clear` 缺审批权限校验；`DictVersionService` 写路径版本不单调；
  2xx 空响应体仍静默。
- 新回归：income 缓存 key 缺 `escapedType`；`carStatistics` 无 `orgCode` 回落。

### 3.2 api 结论要点

- 确认修复：`EsDocRef` 链路自洽、bulk 失败不推进游标、DRIFT 重复补偿、消费不静默 ack、
  `.part` 原子发布、PIT 与 Guard 配置一致。
- 仍有问题：String 主键绑 `bigint` 列报错；CSV 公式注入不完整；
  「backend 未注入令牌」——**误报**，见第 6 节。
- 新回归：`REPAIRED` 把 `ERROR` 伪装成已修复且状态永久停留；365 天窗口挡掉初始化回灌。

### 3.3 本轮回补

`d733d2c`（backend）与 `ebf9c59`（api），明细见 `02-fix-record.md` 第 2 节。

## 4. 第二轮独立复核（针对回补代码）

### 4.1 backend：暂不可推送

- 【新回归·阻断】`approve` 重复 `validateFullFilters`：能力探测返回 `none()` 时误拒合法审批并回退 `PENDING`。
- 【仍有问题·阻断】`DictVersionService` 抬升版本只存本地，未写回 Redis，跨节点 / 重启后仍回退。
- 【非阻断】`localBumps.put` 并发非原子；`orgCode` 回落 legacy 后 4 条 SQL 未过滤。
- 确认修复 8 条（含 `applyOrgScope` 收敛语义、开关权限、`contractViolation` 降级链路、
  `carAudit`/`income` 回落判定、`TwoLevelCache` 括号与标记释放等）。

### 4.2 api：暂不可推送

- 【阻断】`es-init.ps1 -Backfill` 默认窗口 14 个整月（实测 426 天，理论 424~428 天）
  > `backfill-max-days: 400`，三张表回灌全被拒；建议按月分片或调大默认值到 ≥430。
- 【新回归】脚本不校验业务 `code`，HTTP 200 + `code:500` 被当成功，`-Activate` 会误切 `es`。
- 【非阻断】`EsBulkIndexer` 异常明细被外层包装丢失；Kafka 重投重复插 DLQ；
  `CAST(pk AS VARCHAR)` 索引失效（单桶 1 分钟窗口可接受）；`ERROR` 覆盖 `DRIFT` 审计。
- 确认修复：`alreadyDrift` 只认 `DRIFT`、`REPAIRED` 不误标 `ERROR`、CAST 主键参数一致、
  CSV 多行/伪负数转义、Guard 属性名与脚本三处请求头一致、`.part` 不误发布、Kafka 不会无限重投。

### 4.3 本轮回补

`6a91577`（backend）与 `1854c35`（api），含 4 条 legacy SQL 实机验证。

## 5. 第三轮最终门禁复核（针对第二轮回补）

### 5.1 backend：可推送

确认修复 8 条：

1. 过滤条件是 `submit → createApproval` 时序列化到 Redis 的独立快照，`retry` 同样校验；
   审批 Controller 只收 `requestId`，无注入新过滤字段的入口。
2. 移除 approve 内重复能力校验后，`submitInternal` 仍承担最终 `validateFullFilters`，能力兜底完好。
3. `DictVersionService` 正常 Redis 路径 `next == redisValue` 不写回，不破坏 INCR 单调；
   `(int) 31_536_000` 不溢出，TTL 统一为 `TimeUnit.SECONDS`，写回值序列化为裸数字可继续 INCR。
4. key 重置后写回带 TTL，其它节点 `readRemote` 最多 5 秒本地 TTL 延迟即可读到新版本。
5. 并发 `merge(..., Math::max)` 保证单节点严格单调；残余的「SET 乱序」为最终一致窗口，非持久回退。
6. 4 条 SQL 的 `concat(#{orgCode}, '%')` 与既有 `SysDeptMapper.xml` 同写法；参数 `orgCode` 存在；
   未引入不存在的 `org_code` 列。
7. 三个缓存 key 均含 `orgCode`，「key 区分 → 回落 → SQL 下推」形成闭环。
8. 全局扫描 `TwoLevelCache` / `ApiHttpResult` / `TrafficApiHttpClient` / `BigScreenOpsController` /
   审批状态机，无编译风险、无括号不配平、无空指针、无死锁。

仍有问题 / 新回归：**无阻断项**。非阻断 3 条：注释漂移（已修）、`orgId` / `escapedType`
维度未随 `orgCode` 一并下推（既有遗留 K-01）、未使用导入（已删）。

### 5.2 api：可推送

确认修复 8 条：

1. `backfillMaxDays` 默认值、`application.yml` 值、`submit` 的 `Math.max` 三处一致（450 天），注释一致。
2. 环境变量无法把上限改小到影响脚本：`Math.max` 被 365 兜底，且按月分片单任务 ≤31 天。
3. 分片数 14 片 × 3 表 = 42；`chunkEnd(m) == chunkStart(m+1)` 配合左闭右开，完整覆盖原整段无重叠缺口。
4. `$now` 在脚本先于回灌块定义；时间串由 `yyyy-MM-dd HH:mm:ss` 精确解析，不退化成当日 23:59:59。
5. `$resp.code -ne 200` 与管理端点 `Map(code/message/data)` 结构成立，且有 null 兜底。
6. `$backfillFailed` 在 `if ($Backfill)` 之外无条件定义；`if/elseif` 分支与花括号配对无误。
7. `catch (IllegalStateException)` 位于 `catch (Exception)` 之前，明细保留到 `task.error`；
   建索引失败的异常不经该 catch 仍正确传播。
8. 全局扫描 SQL 占位符（回灌 6/6、DLQ 8/8、对账 UPDATE/INSERT 8/8、outbox 2/2、
   car-warning 6/6、DWS 6/6+6/6+4/4）、任务状态机、`.part` 发布、PIT 关闭，均无阻断。

仍有问题 / 新回归：**无阻断项**。非阻断 2 条：管理端点注释漂移（已修）、
`$backfillFailed` 只反映提交阶段是否成功（脚本已要求人工轮询异步任务）与日志措辞（已修）。

### 5.3 最终门禁结论

> **两侧均无阻断项，允许推送 `car-monit-backend-java-V3` 与 `car-monit-api-java-V3` 分支并触发 CI。**
> 第三轮之后仅做注释、未使用导入、日志措辞三类零行为变更清理，并重新编译通过；
> 该清理不改变被复核的运行时语义。

## 6. 误报与澄清（如实留痕）

| 轮次 | 误报内容 | 澄清 |
| --- | --- | --- |
| 第一轮 api | 「backend 侧 `X-Internal-Token` 注入不存在，跨机部署必然 403」 | 该只读会话检索的是 `car-monit-backend-new` 主工作树，而非 `car-monit-backend-java-V3` 工作树。注入实际位于 `TrafficApiHttpClient`（按场景 RestTemplate）与 `ApplicationConfig`（下载专用 RestTemplate），配置见 `ruoyi-admin/src/main/resources/application.yml`；已编译验证。 |
| 第一轮 backend | 「非 retryable 错误（429/4xx）不参与熔断计数」 | 设计约定熔断只统计超时 / 网络 / 5xx，429 不应触发熔断，判为符合设计而非缺陷。 |
| 第二轮 api | 「`CAST(pk AS VARCHAR)` 使主键索引失效」 | 确认性能影响存在，但单桶为 1 分钟窗口且单次扫描有上限、对账默认关闭，判为可接受，记为 K-03 并建议监控慢 SQL。 |

## 7. 凭据处理声明

- 本轮所有审阅 / 修复 / 复核文档、代码、提交信息、脚本、日志中**均未写入** GitHub PAT、
  GitHub token、数据库口令、内部端点令牌或任何密钥明文。
- CI 状态查询与远端推送所需凭据由运行环境 / 凭据管理器提供，仅通过进程内环境变量或
  Git 凭据机制使用，不落盘到仓库文件，不回显到输出。
- 本机 `git config credential.helper = manager-core`；匿名访问 GitHub API 返回 404，
  仓库为私有，故 CI 状态查询必须携带凭据（值不记录）。

## 8. 复核签署

| 轮次 | backend 会话 | api 会话 | 结论 |
| --- | --- | --- | --- |
| 第一轮 | 独立只读会话 A1 | 独立只读会话 A2 | 发现 5+3 项仍有问题、1+2 项新回归，回补 |
| 第二轮 | 独立只读会话 B1 | 独立只读会话 B2 | 暂不可推送，发现 2+1 项阻断，回补 |
| 第三轮 | 独立只读会话 C1 | 独立只读会话 C2 | 可推送，无阻断项 |

记录人：本轮编码会话（修复者）。复核结论均为独立会话原文摘要，未做有利化改写。
