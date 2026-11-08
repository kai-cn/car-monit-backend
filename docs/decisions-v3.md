# car-monit-backend-java-V3 设计决策记录

> 基线：`d081976`（master，2026-11-08）  
> 设计依据：`docs/architecture-traffic-query-design.md` v1.3  
> 范围：backend（后台管理 / 大屏展示层）阶段一，不涉及 api 数据层实现。

---

## 1. 工作树与隔离

| 项 | 决策 | 备注 |
|---|---|---|
| 工作树 | `d:\work\IdeaProjects\car-monit-backend-java-V3` | 独立 worktree |
| 分支 | `car-monit-backend-java-V3` | 基于 `d081976` |
| 原工作树 | 不改动 | 原树仅有未跟踪历史产物，已报告 |

---

## 2. 查询契约客户端

### 2.1 实现方式

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| 新增 `TrafficApiHttpClient` + `TrafficApiClient` + `ResilientApiExecutor` | 继续使用 Forest 接口；引入 Feign/Resilience4j | RestTemplate 可按场景配置连接/读超时（Forest 注解超时是编译期常量，无法按 Nacos/环境配置）；不新增三方库；统一错误码/熔断语义 | 旧 Forest 接口保留，详情/运维接口不受影响；新路径统一走执行器 |
| 连接/读超时按场景独立配置（`traffic-api.*`） | 全局 60s 或编译期固定值 | 避免统计 2s api 超时被 backend 1s 先截断；列表/统计/导出/下载预算独立 | 见 §11.5 超时预算表 |
| 仅幂等 GET 重试（按场景配置次数） | 所有请求重试 | 避免导出任务重复提交；统计默认不重试以快速降级 | `traffic-api.*-retry-count` |
| 熔断只统计超时/网络/5xx | 所有失败计数 | 404 表示 api 契约未上线，不应触发熔断 | 熔断打开期间直接降级，半开探测 |
| 404 映射 `NOT_FOUND`，不熔断 | 视为 5xx | 阶段一 api 尚未实现时需持续低频探测；现 api 已实现，冷却仅用于真实未上线端点 | 404 后按 endpoint 冷却 60s（`traffic-api.contract-probe-interval-ms`），避免每个缓存周期打无效请求 |

### 2.2 契约端点（backend → api）

| 能力 | 端点 | 状态 |
|---|---|---|
| 门架列表 / 导出 | `GET /base/snapshotflow/list`、`/listToExport` | api 已存在 |
| 收费列表 / 导出 | `GET /base/feerecords/list`、`/listToExport` | api 已存在 |
| 逃费类型统计 | `GET /api/v1/bigscreen/stats/escape` | **api 已实现** |
| 追缴统计 | `GET /api/v1/bigscreen/stats/audit` | **api 已实现** |
| 堵漏增收 | `GET /api/v1/bigscreen/stats/income` | **api 已实现** |
| 路段预警 Top-N | `GET /api/v1/bigscreen/stats/warning-top` | **api 已实现** |
| 实时预警列表 | `GET /api/v1/bigscreen/warning/list` | **api 已实现** |
| 导出提交 | `POST /api/v1/large/export/submit?type&startTime&endTime&mode` | api 已存在基础版；`mode` 为新增参数 |
| 导出状态 | `GET /api/v1/large/export/status/{taskId}` | api 已存在 |
| 导出下载 | `GET /api/v1/large/export/download/{taskId}` | **api 已实现** |

> 兼容性：api 现有导出提交只读取 `fuzzyFields.xxx` 扁平键，backend 已按该形态发送，同时附带 `fields`、`purpose`、`mode`；新增键对旧版 api 无副作用（被忽略）。

---

## 3. 大屏统计

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| `bigscreen.stats.mode=hybrid`：API 优先、legacy 兜底 | 直接切 API（api 未实现会全挂）；保持纯 DB | api 预聚合端点已实现，但 hybrid 仍保留故障回退能力 | 504/5xx/404 时回退本地业务表并输出 `X-Degrade`；确认稳定后可切 `api` 模式 |
| legacy 兜底保留 | 删除旧 SQL | 保证灰度期可用、可回滚 | 旧 `carStatistics/carAudit/incomeStatistic/topTen` SQL 保留 |
| `topTen` 默认最近 7 天，支持 `startTime/endTime` | 保持全历史 | 设计明确要求修复「无时间范围」 | 旧调用不传参仍可用，但语义从“全历史”变为“近 7 天” |
| `topTen` legacy SQL 增加时间过滤 + `LIMIT 10` | 只改 service 层 | SQL 层兜底，避免漏改调用方 | 新增 `getTopTenRange`，旧 `getTopTen` 也补了 7 天条件 |

---

## 4. 两级缓存与降级

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| 自研 `LocalTtlCache` + `TwoLevelCache` | Caffeine / Guava | 本机 `.m2` 无 caffeine；不新增依赖可保证离线可编译；语义覆盖 maximumSize + TTL + stale | 后续可平滑替换为 Caffeine |
| L1 进程内 + L2 Redis（JSON 字符串） | 仅 Redis；仅本地 | 设计 §4.4：共享 key 用 JSON，避免 Java/Go 序列化不兼容；L1 抗热点轮询 | Redis key 统一 `cm:{env}:{domain}:{id}`，env 取 `spring.profiles.active`（当前 `druid`） |
| TTL：统计 10s/60s/120s；实时列表 10s/30s/60s；地图点位 5s/10s/20s；字典 60s/300s/600s | 固定 30s | 按设计 §5.4.4 分层 | 缓存 key 含全部查询参数，禁止跨权限/跨筛选复用 |
| stale-while-revalidate + single-flight + TTL 抖动 + 空结果 30s + 1MB 上限 | 仅 TTL | 防击穿/防穿透/防大 key/防群集同时失效 | Redis 不可用时只走 L1/回源并标记降级 |
| `ETag` + `If-None-Match` → 304 | 前端自行比对 | 设计 §5.4.4「HTTP ETag/Last-Modified」 | 过滤器仅作用于 `/manager/bigScreen/**` GET；不缓存鉴权/下载 |
| 响应头 `X-Cache` / `X-Data-Age` / `X-Degrade` / `X-Data-As-Of` / `X-Data-Source` | 仅 body 标识 | 大屏可展示“数据截止时间/降级原因” | 已加 `Access-Control-Expose-Headers` |
| 缓存未命中 API 失败时优先返回 stale | 直接报错 | 设计 §5.4.4 降级阶梯 | `TwoLevelCache` 回源异常且存在 stale 时返回旧值并标记 `DEGRADED` |

---

## 5. 实时列表与地图点位

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| `carWarning` API 优先，回退 Redis 快照 | 只改 SQL | 设计 §5.4.4 要求实时列表走 ES | api 未上线时保持可用；缓存 10–30s |
| 本地 `selectCarWarningInfoListLimit100` 增加 `LIMIT #{limit}` | 仅 service 截断 | 方法名与 SQL 不一致，原 SQL 会把当天预警全部载入 Redis | mapper 签名改为 `(trackId, limit)`；额度 100 |
| `car_warning_list` / `car_list` 增加 600s TTL | 永久缓存 | 设计指出“无 TTL/无失效”是风险 | 快照过期后回源 DB 重建，避免长期陈旧 |
| `carLocation` 建版本化倒排索引 + 结果缓存 | 每请求 Java 全量过滤 | 设计 §5.4.4「预计算快照 + 结果缓存」 | 索引仅在 `car_list_version` 变化时重建；code/escaped 走 token 索引，carNo 精确未命中时回退子串扫描以保持原 contains 语义 |
| 版本键由 `updateRedisCarList` 写入 | 依赖列表内容哈希 | 避免每请求读取全量列表 | `Constants.car_list_version` |

---

## 6. 字典与 N+1

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| 字典/路段/机构/小结果统一走 `BigScreenDictService` 缓存 | 每次 `selectDictDataMap` 查库 | 设计 §5.4.4「字典接口重复查库」 | 字典变更依赖 TTL（最长 5–10 分钟）；后续可接 Pub/Sub 主动失效 |
| `exceptRecordList` 批量查 orgId + 补缴次数 | 保持 2P+1 查询 | 设计 §5.4.4「消除 N+1」 | 查询次数降到 2 次；分页行数不变 |
| 保留原 `find_in_set(except_ids, #{id})` 语义 | 修正为 `find_in_set(#{id}, except_ids)` | 避免在“性能改造”中擅自变更业务结果 | **疑似历史参数顺序问题**：当前语义实际要求 `except_ids` 等于行 id；如需修正应单独评审 |

---

## 7. 导出编排

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| 两条路径 `display` / `full` | 单一路径 | 设计 §5.5 双路径：ES PIT vs GaussDB 游标 | `mode` 透传 api；显示路径拒绝轨迹点/大文本，全字段路径不限字段 |
| 异步任务：backend 只做提交/状态/下载编排 | backend 自己写文件 | 设计明确导出不得占用请求线程；文件由 api/对象存储持有 | 任务元数据（归属/模式/时间/用途）落 Redis 7 天 |
| 下载 HMAC-SHA256 令牌 15 分钟 + 归属校验 + 6 次/分钟限流 | 仅登录态；匿名签名 URL | 设计 §5.5.2 签名 URL 绑定 taskId + 用户 | 令牌经 `X-Export-Download-Token` 请求头传递（query 仅兼容），响应带 `Referrer-Policy: no-referrer` + `Cache-Control: no-store`；令牌不替代登录态 |
| 全字段导出要求用途说明 + 权限（`manager:bigscreen:export` 且 `manager:bigscreen:exportFull`） | 不校验 | 设计 §5.5.3 审批/审计要求 | `/display` 与 `/full` 均有 `@PreAuthorize`；服务端按登录用户 `subCode` 强制注入 `orgcode`，非管理员不能越机构导出；初始权限 SQL 见 `ruoyi-system/src/main/resources/sql/v3-bigscreen-export-permissions.sql` |
| 下载流式代理，独立长超时 RestTemplate（**30 分钟**） | 先落本地再返回 | 避免大文件内存/磁盘；与在线查询线程隔离 | `export.download.read-timeout-ms=1800000`；依赖 api 提供 `/export/download/{taskId}` |

---

## 8. 流水查询边界

| 决策 | 理由 | 影响 |
|---|---|---|
| 门架抓拍列表/导出只走 api；移除 `SnapshotFlowEnhancedService` 请求期直查 MySQL 分表 | 设计 §1.1「backend 不直连 api 的数据库」；R9「模糊查询禁止回退 GaussDB」 | `SnapshotFlowEnhancedService` 等拆表代码保留给同步/运维任务，不再出现在在线查询路径 |
| 收费流水列表/导出走 api + 契约校验 + 崩溃隔离 | 原实现已 HTTP，但无超时/熔断/错误码 | 字典回填改为缓存 |
| 轨迹在线列表 api 优先、本地只读兜底 | api `/base/sysutil/carTrackQueryByCarNo` 已实现 ES 元数据 + 轨迹点批量回查 | **已完成（2026-11-08，见 §12.1）**：请求路径不再本地物化 |
| 省界/收费站抓拍等其他流水接口接入 api | 本次范围为三张核心表的 backend 侧阶段一 | **已完成（2026-11-08，见 §12.2）**：7 类流水分页统一走 api |

---

## 9. 已知缺口与验证

| 项 | 状态 |
|---|---|
| `mvn -pl ruoyi-common,ruoyi-system,ruoyi-framework,ruoyi-admin -am -DskipTests compile` | 通过 |
| 全模块编译（含 quartz/generator） | **已通过（2026-11-08，见 §17）** |
| api `/api/v1/bigscreen/**`、`/export/download/**` | **api 已实现**（见 §17 / §18） |
| 与运行中服务联调 | 已完成（见 §17：真实 api 端到端验证） |
| 单元测试 | **已补齐（2026-11-09）**：`ExportPolicy`、`TwoLevelCache`、`ResilientApiExecutor`、审批状态机 |
| 指标/告警接入 | 仅日志与响应头，未接 Prometheus/告警 |
| 提交 | 未 commit（按要求） |

---

## 10. 回滚

- 统计：`bigscreen.stats.mode=legacy` 即刻回到本地业务表（缓存仍生效）。
- 缓存：`TwoLevelCache` 为独立组件，可通过移除调用回退；L2 key 前缀 `cm:{env}:`，可按前缀清理。
- 查询：门架/收费控制器改动集中在两个 Controller；如需回退，恢复原 Controller 版本即可（本地拆表代码仍保留）。
- 导出：新增 Controller/Service，不改变旧导出端点；可直接下线新端点。

---

## 11. 与 api 阶段一的契约静态对齐（2026-11-08）

对齐对象：`d:\work\IdeaProjects\car-monit-api-java-V3`（只读核查，未修改 api 代码）。
结论：路径、请求参数、返回字段名/类型、时间/分页格式总体一致；发现 8 处需要 backend 修正或显式约束，已修正并记录如下。

### 11.1 对齐矩阵

| 能力 | api 实现 | 对齐结论 |
|---|---|---|
| `GET /api/v1/bigscreen/stats/escape` | `BigScreenStatsV3Controller#escape`，参数 `startDate/endDate/orgId/escapedType`，裸 JSON `List<Escape>` | 路径/参数/字段一致（`escapedType/escapedTypeName/number/escapedAmount`） |
| `GET /api/v1/bigscreen/stats/audit` | 参数 `startDate/endDate`，裸 JSON `Audit` | 一致（`totalCount/finishedCount/totalAmount/finishedAmount`） |
| `GET /api/v1/bigscreen/stats/income` | 参数 `queryDateType/startDate/applyTime1/applyTime2`，裸 JSON `List<Income>` | 字段一致（`orgName/amount/carNum`）；`startDate` 需 `yyyy-MM-dd` |
| `GET /api/v1/bigscreen/stats/warning-top` | 参数 `startTime/endTime/topN`，裸 JSON `List<WarningTop>` | 一致（`roadCode/sectionName/carNum/rank/rate`）；api 已自行拼接 `roadCode + 空格 + sectionName` |
| `GET /api/v1/bigscreen/warning/list` | `BigScreenWarningV3Controller` + `CarWarningSearchService`，参数 `roadCode/sectionCode/tollCode/gantryCode/fwqbm/escapedType/carNo/limit`，裸 JSON 数组 | 路径/参数一致；字段 snake→camel 后与 `CarWarningInfo` 对齐；索引缺失/无数据 200+[]，ES 不可达 503 |
| `POST /api/v1/large/export/submit?type&startTime&endTime&mode` | `mode=display/full` 走 V3；无 `mode` 走 legacy；body 支持 `fuzzyFields.*`、`fields`、`purpose` | 一致；backend 已按 `fuzzyFields.<field>` 扁平键发送 |
| `GET /api/v1/large/export/status/{taskId}` | 优先 V3，未命中回落 legacy；返回 `code/status/totalExported/filePartCount/submitTime/endTime/mode/type/totalRows/error` | 一致 |
| `GET /api/v1/large/export/download/{taskId}` | 200 `application/gzip` + `Content-Disposition`；不存在 404；未完成 409 | 一致；backend 流式代理 |

### 11.2 已修正的 backend 侧不一致

| # | 问题 | 以哪边为准 | backend 修正 |
|---|---|---|---|
| 1 | api `listToExport` 使用 PageHelper 且默认 `pageSize=10`，若沿用前端分页参数会只导出单页 | 设计 §1.3 A8「旧导出过渡期展示字段、单次 1 万条」 | `TrafficApiClient.snapshotExport/feeExport` 显式设置 `pageNum=1, pageSize=10000`，恢复旧同步导出的 1 万条上限 |
| 2 | api 列表在 HTTP 200 内返回业务码（400/503），原实现一律映射 5xx | api 契约与设计 §4.3 | 新增 `businessException` 映射：400/422→INVALID_ARGUMENT、404→NOT_FOUND、429→RATE_LIMITED、5xx→UPSTREAM_ERROR |
| 3 | api 导出提交/状态在 HTTP 200 内返回 `code=400/404` | api 现有契约（提交/状态保持 code 语义） | `checkBusinessCode` 按业务码映射；不再误报 5xx |
| 4 | backend 展示字段默认值（camelCase 且与 api 默认列不一致） | api `displayColumns()` 为展示字段权威 | `ExportPolicy` 默认字段改为 api 的 snake_case 展示列；用户显式字段仍支持 camelCase 别名 |
| 5 | api 的 `income` 只接受 `yyyy-MM-dd`，前端可能传 `yyyy-MM` | 设计 §5.4.4 的月度口径 + api 参数格式 | `BigScreenStatsService` 将 `yyyy-MM` 归一化为 `yyyy-MM-01` |
| 6 | api 全字段导出仅下推车牌，维度过滤被忽略 | 安全优先：不能“带筛选导出全量” | `ExportPolicy.validateFullFilters`：full 模式仅允许车牌/颜色过滤，其他维度显式拒绝并提示待 api 补齐 |
| 7 | api `escape` 固定返回 5 类（无数据补 0），带 `escapedType` 时与 legacy 单类型语义不同 | legacy 现有 UI 语义 | backend 在 `escapedType` 非空时收窄结果；无数据返回空列表 |
| 8 | api 导出下载未完成返回 409、不存在返回 404；backend 原错误文案不区分 | api 状态码语义 | 409/404 已映射为 JSON 错误；下载读超时改为可配置（默认 30 分钟） |

### 11.3 未改动但需知悉的差异

| 项 | 说明 | 处理 |
|---|---|---|
| 服务端口 | backend `vehicleMonitor.baseUrl` 默认 `http://127.0.0.1:9902`；api V3 默认端口将改为 9902 | backend 已支持 `${VEHICLE_MONITOR_BASE_URL:http://127.0.0.1:9902}` 覆盖，默认值与 api 对齐 |
| 统计查询超时 | backend 统计读超时 3s > api `traffic.bigscreen.query-timeout-ms=2000` | 已修正倒挂；api 慢查询先由 api 返回 503/超时，backend 3s 内仍可拿到 api 的明确错误再降级 |
| `escapedTypeName` | api 使用内置静态映射（1 少轴…），backend 字典可能不同 | 字段名不变；文案以字典为准时由 api 侧替换，backend 不二次翻译 |
| 近似去重 | `dws_*.car_cnt` 按日求和，跨日非精确 distinct | 设计允许 HLL 近似（1–2%）；对比 legacy 时需按此口径解释 |
| `totalExported=-1` | api 重启后按已完成文件恢复任务时返回 -1 | backend 原样透传；前端应展示“未知/文件已生成”而非 0 |
| 旧同步导出 | `/base/*/listToExport` 仍是同步接口（backend 超时放宽到 30s） | 仅保留给旧页面；新导出走 `/manager/bigScreen/export` 异步双路径 |

### 11.4 降级路径确认（静态）

| api 返回 | backend 行为 |
|---|---|
| 404 | `ResilientApiExecutor` 按 endpoint 冷却 60s（`traffic-api.contract-probe-interval-ms`）；统计 `hybrid` 回退 legacy，`warning/list` 回退 Redis 快照；`mode=api` 时返回 503/404 语义错误 |
| 503（如 `stats-enabled=false`） | 映射 `UPSTREAM_ERROR`，按场景重试（统计/预警 0 次，列表/状态 1 次）→ 熔断计数 → `hybrid` 回退 legacy；`mode=api` 时返回 503 |
| 超时 | 映射 `TIMEOUT`，按场景重试（统计/预警 0 次，列表/状态 1 次）→ 熔断 → `hybrid` 回退 legacy；`mode=api` 时返回 503 |
| Redis 不可用 | `TwoLevelCache` 降级为 L1/回源，标记 `REDIS_UNAVAILABLE`；不阻断统计回退 |
| 熔断打开 | 直接抛 `CIRCUIT_OPEN`，`hybrid` 回退 legacy，不再打 api |

### 11.5 超时预算（2026-11-08 修正倒挂）

原则：**backend 读超时 > api 处理超时 + 缓冲**；重试只用于幂等 GET；POST 不重试；下载使用独立长超时。

| 场景 | 连接超时 | 读超时 | 重试次数 | 单次上限（连接+读） | 最坏调用预算 | 说明 |
|---|---:|---:|---:|---:|---:|---|
| 列表（门架/收费） | 1000ms | 2500ms | 1 | 3.5s | 3.5s×2+200ms = **7.2s** | api 列表 SLO ≤2s |
| 统计（escape/audit/income/warning-top） | 1000ms | 3000ms | 0 | 4.0s | **4.0s** | api `query-timeout-ms=2000`，读 3s 避免倒挂；超时即降级 |
| 实时预警列表 | 1000ms | 2000ms | 0 | 3.0s | **3.0s** | 404 后 endpoint 冷却 60s，Redis 快照兜底 |
| 导出提交 | 1000ms | 6000ms | 0 | 7.0s | **7.0s** | POST 非幂等，禁止重试 |
| 导出状态 | 1000ms | 2000ms | 1 | 3.0s | 3.0s×2+200ms = **6.2s** | 轮询接口 |
| 旧同步导出（1 万条） | 1000ms | 30000ms | 0 | 31.0s | **31.0s** | 仅旧页面；新导出走异步任务 |
| 导出下载（流式） | 3000ms | 1800000ms | 0 | 1800.3s | **1800.3s** | `export.download.*`，不缓冲到内存 |

其他预算：
- 重试退避：`retry-backoff-ms=200`，第 n 次重试前等待 `200×n` ms。
- 熔断：**按调用域隔离**（export / warning / stats / flow / default），各域独立计数；连续基础设施失败（超时/网络/5xx）**5 次** → 打开 **30s** → 半开 1 个探测许可；成功即关闭。导出 5xx 不再连坐统计/预警。
- 指标：同一次尝试的错误只计一次（响应分支与 catch 不重复累加）。
- 404：不计入熔断，按 endpoint 冷却 **60s**（`contract-probe-interval-ms`）。
- 限流：429 不重试，直接降级/报错。
- 下载：独立 `trafficApiDownloadRestTemplate`，连接 3s、读 30 分钟，可按 `export.download.*` 覆盖。

### 11.6 `warning/list` 契约对齐（2026-11-08 api 实现后）

| 项 | api 契约 | backend 处理 | 结论 |
|---|---|---|---|
| 路径 | `GET /api/v1/bigscreen/warning/list` | 同路径 | 一致 |
| 参数 | `roadCode/sectionCode/tollCode/gantryCode/fwqbm/escapedType/carNo/limit(default 100)` 单值 `term` | 同参数；`limit` 固定 100（再 clamp） | 一致 |
| 字段 | ES `_source` snake_case → camelCase；日期字段 `yyyy-MM-dd HH:mm:ss` | `CarWarningInfo` 字段同名；日期有 `@JsonFormat`；未知字段忽略 | 一致 |
| 排序/上限 | `gantry_time desc, id asc`，`size≤100` | 透传 api 结果 | 一致 |
| 空结果 | 索引存在无数据 / 索引缺失 → **200 + []** | 视为权威空结果，**不触发 Redis 兜底**；空结果按 30s 负缓存 | 一致 |
| ES 不可达 | → **503** | `UPSTREAM_ERROR` → 熔断计数 → Redis 快照兜底，`X-Degrade` 标记 | 一致 |
| 其他错误 | 4xx/5xx | 按错误码降级或报错 | 一致 |
| 超时预算 | api 查询无独立超时配置 | backend 读 2s、重试 0 | 防倒挂 |

**原有两个 Redis 兜底分支已移除（2026-11-09 api 补齐后）：**

1. **抓拍类型哨兵**：api `BigScreenWarningV3Controller` 新增 `captureType` 参数，并自动从
   `tollCode/gantryCode/fwqbm` 中剥离 `StationCapture/GantryCapture/ServiceAreaCapture` 哨兵，
   按 `capture_type` terms 查询；backend 不再回退 Redis。
2. **多值过滤**：api `CarWarningSearchService` 对 `roadCode/sectionCode/tollCode/gantryCode/fwqbm/escapedType`
   均按逗号拆分为 terms；backend 直接透传逗号串，不再回退 Redis。

> 仍保留的 Redis 兜底仅限：api 超时/5xx/熔断（`X-Degrade=<CODE>`）与运行期 `warning-api=off`。
> `captureType`/`MULTI_VALUE_UNSUPPORTED` 两类降级标记已删除。

**其他语义说明：**
- `carNo` 过短/无法解析 → api 返回 `200 + []`（非错误）；backend 按空结果返回，不回退。
- `track_josn` 不在 ES 索引/`_source`；api 列表不返回该字段，backend `trackJosn` 为空（设计 §5.4.4 列表不返回大字段）。
- 旧 Redis 快照过滤仍是 `trackNames` 子串语义；ES 为编码/车牌 ngram 语义，单值正常码/完整车牌场景一致，边缘脏数据以 ES 主路径为准。
- 若要完全消除上述两个 Redis 兜底分支，api 需补 `captureType` 或 `terms` 过滤；backend 已把原因和触发条件记录在此。

---

## 12. 阶段一遗留项收口（2026-11-08）

### 12.1 轨迹在线列表去本地物化

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| `/manager/cartrackinfo/listByCarId`、`listByCarByTime` 改为 api 优先 | 保持本地表优先 | 设计 §4.3 / §5.8.4：列表走 api，详情按 cid 回 SoR | 首次请求延迟取决于 api（读超时 6s） |
| 主路径调用 `/base/sysutil/carTrackQueryByCarNo`（api D13 官方轨迹契约） | 新造 `/api/v3/traffic/list` 元数据接口 | api 侧已实现“ES 元数据 + `(cid,extime)` 批量回查 trailpoints”，且返回既有 `TrailInfo` 结构，前端无感 | 无需 api 新增接口；`carTrackQueryByCarNo` 由 `TrafficApiClient.trailPage` 类型化调用 |
| 移除请求路径的 `removeRealData + saveBatch`（本地物化） | 保留写回 | 写回会让 backend 变相保存业务流水，违反“backend 不直连/不落库流水” | 本地 `zdata_trail_tracks` 只作为 api 不可用时的**只读兜底**；后台 `syncHistoryTrack` 任务不再被在线请求放大 |
| `car_history_trail` Redis 缓存保留 | 一并移除 | `CarWarningInfoServiceImpl` 预警详情 `trailFwqList` 依赖该 key | 仅缓存、不落库；写入失败只告警不影响返回 |
| 时间-only 查询（无车牌）继续走本地只读 | 强制 api | api 轨迹接口要求 `carNo`，空车牌返回空数组，会改变旧页面语义 | 有车牌走 api；无车牌仍本地过滤 |
| 回滚 | `bigscreen.trail.mode=local` 或 Redis 开关 `trail-api=off` | 无需重启 | 两种方式都回到本地只读路径 |

> 术语澄清：本文所说的“`carTrackQueryByCarNo` 只作为兜底”落地为——**本地旧表/旧物化链路只做兜底**；
> api 侧 `/base/sysutil/carTrackQueryByCarNo` 是 api D13 指定的官方在线轨迹入口，因此作为主路径。
> 若后续 api 提供“V3 轨迹元数据列表 + 详情取点”两段式接口，可把主路径切过去，本接口继续作为兜底。

### 12.2 其他流水分表接入 api

| 接口 | api 端点 | 场景/预算 | 说明 |
|---|---|---|---|
| 省界抓拍 | `GET /base/provcapture/list` | `FLOW_EXTENDED`，连接 1s / 读 5s / 重试 0 | 请求线程不再直查 `ods_rt_szdn_snapshot_flow_provcapture_addcode` |
| 收费站抓拍 | `GET /base/stationcapture/list` | 同上 | 不再直查 `..._stationcapture_addcode` |
| 省界称重 | `GET /base/vehicleweight/list` | 同上 | 不再直查 `ods_szdn_province_border_vehicle_weight_newstructure` |
| 收费站入口/出口 | `GET /base/feeStationEnter/list`、`/base/feestationexit/list` | 同上 | 原 Forest 调用统一改类型化客户端 |
| 交易流水 | `GET /base/feeGantry/list` | 同上 | 原 Forest 调用统一改类型化客户端 |
| 服务区车辆流水 | `GET /manager/fwqclls/list` | 同上 | 空表/低频，api 侧仍走 GaussDB |
| 拟合轨迹 | `GET /base/fitting/list` | 同上 | 不再直查 `zdata_trail_fitting` |

- 详情接口：
  - `GET /base/provcapture/{bigId}`、`/base/stationcapture/{bigId}`、`/base/vehicleweight/{dataSource}`、`/base/feeStationEnter/{bigId}`、`/manager/fwqclls/{bigId}` 通过 `TrafficApiClient.flowDetail` 调 api 等价端点（API 来源，api 不可用返回明确错误）；
  - `GET /base/fitting/{cid}` **api 暂无等价详情端点**，仍读 backend 本地 `zdata_trail_fitting`。响应显式带 `dataSource=LOCAL_DB`、`realtime=false` 与“数据可能陈旧、无实时保证”提示；这是**已知数据时效缺口**，待 api 提供按 cid 的详情接口后再切换。
- `FLOW_EXTENDED` 读超时 5s、重试 0：这些表未进 ES，api 侧 GaussDB 分页可能慢；重试会放大数据库压力。
- 失败返回 `TableDataInfo(code!=200, msg)`，不静默回退本地分表；前端可展示“数据服务暂不可用”。

### 12.3 超时预算补充（接 §11.5）

| 场景 | 连接 | 读 | 重试 | 最坏预算 | 说明 |
|---|---:|---:|---:|---:|---|
| 扩展流水（7 类） | 1000ms | 5000ms | 0 | **6.0s** | api GaussDB 分页，不重试 |
| 轨迹在线 | 1000ms | 6000ms | 0 | **7.0s** | api ES 查询 + 轨迹点批量回查 |
| 能力探测（导出） | 1000ms | 2000ms | 0 | **3.0s** | 5 分钟一次，失败按“不支持”处理 |

---

## 13. 字典主动失效与车牌颜色字典（2026-11-08）

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| 版本号主动失效：`cm:{env}:dict:version:{domain}` + INCR | Redis Pub/Sub | 无需额外连接/订阅容器；多节点最终一致；实现简单可回滚 | 写入端立即加版本；各节点最多 5s 感知。该 ≤5s 仅对**经 backend 后台写入**（字典/路段/机构等控制器 hook）成立；api 直接改库不会触发 hook，需等 TTL 或手动失效 |
| 缓存 key 加版本段 `v{n}:` | 逐 key 删除 | 避免 SCAN/批量删除；避免删除期间穿透 | 版本变化后短时间存在两套 key，内存可接受 |
| 版本域：section / toll / gantry / fwq / org / sysdict / plate_color | 全局单一版本 | 维度变更只失效对应域；系统字典变更失效 sysdict | 写入 hook：SysDictData、SysDictType、Section、Toll、Gantry、Fwqjcxx、BaseOrg 控制器 |
| 版本读取本地缓存 5s | 每请求读 Redis | 降低 Redis QPS | 失效传播 ≤5s（仅 backend 写入路径）；Redis 不可用时退化为本地版本 + TTL |
| 运行期开关 `dict-version=off` | 仅配置 | 回滚到纯 TTL | 无需重启 |
| 车牌颜色以 `sys_dict_data(dict_type=plate_color)` 为准 | 硬编码颜色枚举 | 用户明确 3307 `carmonit` 库字典表为权威 | 列表/导出 `plateColorName` 取字典 label |
| 未知颜色码回退原始码并标记 `plateColorMark=UNKNOWN` | 丢弃行/置空 | 不因字典缺失丢业务数据 | 前端可对 UNKNOWN 做提示；字典恢复后自动正确 |
| 字典查询失败降级 | 报错阻断列表 | 列表可用性优先 | 返回原始码 + UNKNOWN；缓存层 `REDIS_UNAVAILABLE`/回源失败按既有降级策略 |
| 列表富化位置 | 各控制器重复实现 | 统一在 `TrafficApiClient.deserializeRows` 反射补齐 `plateColorName`/`plateColorMark` | 覆盖门架/收费/抓拍/称重/服务区等所有 api 列表；预警列表在 `BigScreenRealtimeService` 单独富化 |
| 主动失效验证（E2E） | — | 调用 `DELETE /system/dict/type/clearCache` 后 Redis `cm:druid:dict:version:sysdict` 由空→1；随后路段/机构列表正常（85/481 行） | 版本 hook 生效，缓存 key 已切换 |
| V3 展示字段导出列 | 期望 api 直接输出 `plate_color_name` | api 已在 snapshot/fee `displayFields`/`displayAliases` 声明该列（`plateColorNameByTable.snapshot=true`） | snapshot/fee 展示导出默认自动追加 `plate_color_name`；trail 未声明，请求该列会被拒绝 |

---

## 14. 指标与告警（2026-11-08）

| 指标 | 采集点 | 输出 |
|---|---|---|
| `api.request/success/timeout/unavailable/upstream_error/not_found/rate_limited/contract_violation` | `ResilientApiExecutor` 每次尝试 | `/monitor/bigscreen/metrics` counters |
| `api.circuit.state`（0 关 / 1 开 / 2 半开）、`api.circuit_open` | `ResilientApiExecutor` 按调用域（export/warning/stats/flow/default） | 整体最高级别 gauge；`/metrics` 另返回 `circuitScenarios` 各域状态 |
| `cache.hit/L1/L2/STALE/MISS`、`cache.l2.read_failed/write_failed` | `TwoLevelCache` | counters；命中率统一为 `(L1+L2+STALE)/(L1+L2+STALE+MISS)`，即 `1 - MISS/总`，告警任务同公式 |
| `degrade` + `degrade.{REASON}` | `CacheContext.markDegrade` | counters（熔断/超时/Redis 不可用/MULTI_VALUE 等） |
| `export.submitted/full.submitted/completed/failed/active` | `BigScreenExportService` | 积压 = `export.active` gauge |
| `export.approval.pending/approved/rejected` | 审批流程 | counters |
| `export.capability.gate_closed` | 能力探测失败/未支持 | counter |

- 指标端点：`GET /monitor/bigscreen/metrics`（`monitor:server:list` 权限），返回 counters、gauges、api 超时率、缓存命中率、导出积压、整体熔断状态与各调用域状态。
- 告警任务：`TrafficMetricsAlertTask` 每 60s 比较增量，超阈值写 WARN 并累加 `alert.*`；阈值 `traffic-api.metrics.*`。
- **调度方式**：本工程没有 `@EnableScheduling`（历史 `@Scheduled` 不触发），因此新任务显式复用 RuoYi `scheduledExecutorService`，避免全局启用调度改变既有 Quartz 行为。
- 接入 Prometheus 时可直接把 counters 映射为文本格式；当前不新增依赖。

---

## 15. 全字段导出维度过滤能力门（2026-11-08）

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| 默认 `auto`：探测 `GET /api/v3/export/capabilities` | 永久拒绝；永久放开 | 满足“api 支持后自动放开”，api 未实现时 404 → 保持拒绝 | 探测 5 分钟一次，失败/非 2xx 按未支持 |
| 按表/字段能力矩阵放开 | 只看全局布尔 | api 返回 `dimensionFilters` 按表声明（trail 为空），全局 true 不能代表每张表 | `trail` 维度过滤仍拒绝，snapshot/fee 放开 |
| `plateColorName` 能力驱动展示列 | 固定请求该列 | api 在 snapshot/fee `displayFields` 声明 `plate_color_name`（`plateColorNameByTable.snapshot=true`） | snapshot/fee 默认展示字段自动追加；trail 请求该列会 400 |
| 配置 `bigscreen.export.full-dimension-filters=true/false` 强制覆盖 | 只能自动 | 灰度/回滚/应急 | true=按全表全字段放行；false=全部拒绝 |
| 未放开时拒绝维度过滤并返回明确提示 | 静默忽略筛选导出全量 | 安全优先：不能“带筛选导出全量” | 错误码 400，提示 api 能力矩阵未声明 |
| 放开后允许 org/section/road/gantry/toll 编码与名称 | 允许任意字段 | api `buildV3ExportRequest` 解析这些维度 | 未知字段仍 400 |

> api 已实现该端点（2026-11-09）：`fullDimensionFilters=true`、`multiValueDimensionFilters=true`、
> `plateColorName=true`；`dimensionFilters={snapshot:[...], fee:[...], trail:[]}`。
> backend 已从全局布尔改为按表/字段矩阵，trail 维度过滤仍拒绝并明确提示。

---

## 16. 阶段二/三：预聚合预热、导出审批与保留期、灰度回滚（2026-11-08）

| 项 | 决策 | 说明 |
|---|---|---|
| 统计预聚合消费 | 仍由 api `dws_*` 端点提供，backend 两级缓存首层 10s/60s/120s | 不新增本地聚合表；`topTen` 时间范围已在阶段一修复 |
| 统计预热 | `BigScreenStatsPrewarmTask`，默认关闭（`bigscreen.stats.prewarm.enabled=false`） | 启用后按间隔预热 escape/audit/income/topN 默认窗口；失败静默 |
| 导出审批 | `bigscreen.switches.export-approval=true` 时，非 admin 的 full 导出先落 `pending_approval`，不调用 api | 审批接口 `GET /manager/bigScreen/export/approvals`、`POST .../{requestId}/approve|reject`；权限 `manager:bigscreen:exportApprove` |
| 审批通过 | 按原申请人身份提交，审批人只做授权 | 任务归属仍是申请人；审批记录回写 taskId |
| 保留期 | `export.retention-days=7`，任务元数据与审批请求都按该 TTL | 文件保留期由 api/对象存储负责；backend 只清元数据 |
| 灰度/回滚开关 | Redis `cm:{env}:switch:{name}`，10s 本地缓存，缺省读 `bigscreen.switches.*` | 开关：stats-api-first / warning-api / location-index / export-v3 / dict-version / trail-api / export-approval |
| 运维入口 | `GET /monitor/bigscreen/switches`、`POST/DELETE /monitor/bigscreen/switches/{name}` | 权限 `monitor:server:list`；修改无需重启 |
| 导出 V3 关闭 | `export-v3=off` 时新导出端点返回 503 语义，旧导出端点不受影响 | 快速回滚 |
| 地图索引关闭 | `location-index=off` 走逐条扫描 + 结果缓存（旧语义） | 回滚 O(N) 路径 |
| 预警 API 关闭 | `warning-api=off` 直接走 Redis 快照 | 回滚 ES 路径 |
| 统计 API 关闭 | `stats-api-first=off` 强制 legacy（缓存仍生效） | 与 `bigscreen.stats.mode=legacy` 叠加 |

---

## 17. 编译与验证（2026-11-08）

| 项 | 结果 |
|---|---|
| `mvn -q -DskipTests compile`（全模块） | **通过** |
| 工作树 | 仅 `d:\work\IdeaProjects\car-monit-backend-java-V3`；未 commit/push |
| 运行中服务 | 未重启/未停止 |
| 单元测试 | **已新增（2026-11-09）**：`ExportPolicyTest`、`TwoLevelCacheTest`、`ResilientApiExecutorTest`、`ExportApprovalStateMachineTest`，`mvn -o -B test -pl ruoyi-common,ruoyi-system -am` 通过（29 个用例） |
| 联调 | **已执行**（backend V3 @9990 → api V3 @9902），详见 §18 |
| 运维手册 | `docs/ops-runbook-v3.md`（开关/回退/stats-enabled/导出/指标） |
| 遗留 | api 能力端点已实现并按表矩阵自动放开；snapshot/fee 展示导出均已支持 `plate_color_name`；预警 captureType/terms 兜底已于 2026-11-09 移除；`/base/fitting/{cid}` 详情仍读本地（api 无等价端点） |

---

## 18. 真实端到端联调（2026-11-08，backend V3 @9990 → api V3 @9902）

> 环境：api `activeEngine=es`；ES 实际文档数 `trail 682 / snapshot 900 / fee 1016 / car-warning 1627`；
> 样本数据时间为 **2025 年**（2026 年查询为空属数据口径，不是链路问题）。
> backend 以临时测试实例跑在 9990（未触碰 9989 旧实例、未重启 9902），联调结束后已停止。

### 18.1 调用结果

| 链路 | 端点 | 状态 | 耗时 | 结果/响应头 |
|---|---|---:|---:|---|
| 逃费统计 | `/manager/bigScreen/carStatistics` | 200 | 486ms | 6 行；`X-Cache=MISS`、`X-Degrade=UPSTREAM_ERROR`、`X-Data-Source=LEGACY_DB` |
| 追缴统计 | `/manager/bigScreen/carAudit` | 200 | 55ms | 1 对象；同上降级头 |
| 堵漏增收 | `/manager/bigScreen/incomeStatistic` | 200 | 49ms | 3 行；同上降级头 |
| 路段预警 Top-N | `/manager/bigScreen/topTen` | 200 | 88ms | 10 行；同上降级头 |
| 实时预警 | `/manager/bigScreen/carWarning` | 200 | 522ms | 100 行；`X-Data-Source=API`、无 `X-Degrade` |
| 轨迹在线 | `/manager/cartrackinfo/listByCarId`（鲁Q76639, 2025） | 200 | 403ms | total=1、trailList=3 点；api ES+SoR 路径 |
| 拟合轨迹 | `/base/fitting/list`（2025 窗） | 200 | 43–209ms | total=682、3 行（改为 V3 查询后） |
| 门架/收费 | `/base/snapshotflow|feerecords/list` | 200 | 86–246ms | total=0（2026 样本无数据，ES 为空） |
| 省界抓拍 | `/base/provcapture/list` | 200 | 67ms | total=356 |
| 收费站抓拍 | `/base/stationcapture/list` | 200 | 93ms | total=851 |
| 省界称重 | `/base/vehicleweight/list` | 200 | 70ms | total=300 |
| 收费站入口/出口 | `/base/feeStationEnter|feestationexit/list` | 200 | 87–89ms | total=317/270 |
| 交易流水 | `/base/feeGantry/list` | 200 | 107ms | total=200 |
| 服务区流水 | `/manager/fwqclls/list` | 200 | 84ms | total=3 |
| 展示导出 | `POST /manager/bigScreen/export/display`（trail 2025） | 200 | 105ms 提交 | done、682 行、1 分片；下载 49,441B gzip |
| 全字段导出 | `POST /manager/bigScreen/export/full`（trail 2025） | 200 | 169ms 提交 | done、682 行；下载 614,121B gzip |
| 维度过滤拒绝 | full + `sectioncode` | 200/code 400 | — | “全字段导出当前仅支持车牌/颜色过滤…” |
| 时间窗拒绝 | full + 7 年范围 | 200/code 400 | — | “时间范围不能超过 365 天” |
| 未知任务 | `GET /export/status/does-not-exist` | 200/code 404 | — | “导出任务不存在或已过期” |
| 重试保护 | `POST /export/{done}/retry` | 200/code 400 | — | “仅 failed/canceled/paused 任务可重试，当前状态: done” |
| 缓存命中 | 统计第二次 | 200 | — | `X-Cache=L1`、`X-Data-Source=CACHE`、ETag 304 生效 |
| 指标端点 | `/monitor/bigscreen/metrics` | 200 | — | `api.request=14`、`api.upstream_error=8`、`cache.hit.L1=99`、`cacheMiss=6`、`degrade=4`、`export.active=0`、`circuit=CLOSED` |

### 18.2 降级触发确认

| 场景 | 实际表现 | 结论 |
|---|---|---|
| api stats 503（`stats-enabled=false`） | `X-Degrade=UPSTREAM_ERROR`（一次冷调用为 `TIMEOUT`），`LEGACY_DB`，200 | 预期；api 恢复后 10s 缓存周期内自动切回 API |
| warning 正常 | `X-Data-Source=API`，无降级 | 正常路径不降级 |
| Redis/缓存命中 | `X-Cache=L1/L2/STALE`，来源 `CACHE` | 正常 |
| 开关关闭（灰度 percent=0） | 无 `X-Cache`，`LEGACY_DB`，无 `X-Degrade` | 一键回退立即生效（统计方法已跳过缓存） |
| 租户白名单不命中 | 同上 | 灰度按租户生效 |

### 18.3 联调发现与修正

| # | 问题 | 处理 |
|---|---|---|
| 1 | api 没有 `/base/fitting/list`（404），backend 拟合轨迹列表报“契约未就绪” | 改走 `POST /api/v3/traffic/list`（table=trail），`entime/extime` 映射为时间范围，字段 `ZdataTrailFitting` 对齐；见 `TrafficApiClient.trailFittingPage` |
| 2 | 缓存命中时 `X-Data-Source` 为空 | `TwoLevelCache.markHit` 在非 MISS 且来源未知时标记 `CACHE` |
| 3 | 样本数据为 2025 年，2026 查询全 0 | 联调统一使用 2025 时间窗；非代码缺陷，已记录数据口径 |
| 4 | 统计回退后仍可能命中旧缓存 | 统计四方法在开关关闭时直接 legacy、不读缓存，回退即时生效 |

### 18.4 `stats-enabled=true` 切换与回退

见运维手册 `docs/ops-runbook-v3.md` §4；要点：
1. dws 回填完成 → api 开关置 true（api 重启）；
2. backend 无需改动，`hybrid` 自动使用 API；验证 `X-Data-Source=API` 且无 `X-Degrade`；
3. 回退：`stats-api-first=off` 或灰度 percent=0（即时）；彻底回退可设 api `stats-enabled=false` 或 backend `mode=legacy`。

---

## 19. 灰度、导出重试与清理（2026-11-08）

| 决策 | 备选 | 理由 | 影响 |
|---|---|---|---|
| 灰度维度：全局开关 → 租户白名单 → percent 稳定哈希 → 配置默认 | 只做全局开关 | 支持先小范围租户验证，再按比例放量 | Redis 覆盖 10s 本地缓存；`开关名+租户` SHA-256 稳定分桶，避免同一租户闪烁 |
| 统计开关关闭时不读缓存、直接 legacy | 保留缓存等 TTL | 一键回退要即时 | 关闭期间无 `X-Cache`，不返回旧 API 数据 |
| 导出元数据保存原 `fuzzyFields/fields` | 只存 taskId | 支持失败重试/续传按原参数重提 | `ExportTaskMeta` 扩展字段；Redis TTL 保留期 |
| 重试仅允许 failed/canceled/paused | 任意状态可重试 | 防止重复导出与资源浪费 | 生成新 taskId，attempts+1，原任务保留审计 |
| 断点续传 = 按原参数重新提交 | 等待 api 支持字节续传 | api 无续传/暂停恢复接口 | 返回 `resumeMode=resubmit`；真正续传待 api |
| 清理任务每小时清理本地 active 计数 | 不清理 | 防止未轮询任务让 `export.active` 虚高 | Redis 元数据仍由保留期 TTL 清理 |
| 轨迹本地物化开关默认关闭 | 删除代码 | 保留回滚能力；Quartz 仍可手动触发 | `trail-materialize=false`，`saveTrailTracksHistory` 跳过写库 |

### 19.1 新增/变更端点

- `GET/POST/DELETE /monitor/bigscreen/gray/{name}`（percent/tenants）
- `GET /monitor/bigscreen/switches` 增加 `gray` 快照
- `POST /manager/bigScreen/export/{taskId}/retry`、`/resume`
- `GET /monitor/bigscreen/metrics`（指标/熔断/积压）
- 运维手册：`docs/ops-runbook-v3.md`

---

## 20. 9989 受控替换记录（2026-11-09）

| 项 | 旧实例 | 新实例 |
|---|---|---|
| PID | 21032（已停止） | **47532** |
| 启动命令 | `java -Xms512m -Xmx1g -jar D:\work\IdeaProjects\car-monit-backend-new\ruoyi-admin\target\ruoyi-admin.jar` | `java -Xms512m -Xmx1g -jar D:\work\IdeaProjects\car-monit-backend-java-V3\ruoyi-admin\target\ruoyi-admin.jar` |
| JDK | 1.8.0_202 | 1.8.0_202 |
| jar | 511,356B（thin jar，SHA256 `F299880C…950E`） | 210,045,213B（fat jar，SHA256 `9FD4DAF7…1DFF`） |
| 配置 | jar 内 `application.yml`/`application-druid.yml`，无外部参数 | 同上，端口/DB/Redis/Kafka 沿用 |
| 堆 | -Xms512m -Xmx1g | -Xms512m -Xmx1g |

验证结果（api 9902 在替换期间短暂停机，恢复后已补齐）：
- 登录页 `/` 200；`admin` 登录 200；
- **api 恢复后补验**：
  - 流水列表 7 类全部 200：provcapture 356 / stationcapture 851 / vehicleweight 300 / fwqclls 3 / stationEnter 317 / stationExit 270 / feeGantry 200 / fitting 682（2025 窗）；
  - 展示导出：submit 133ms、done 682 行、下载 49,441B gzip；
  - 全字段导出：submit 103ms、done 682 行、下载 614,121B gzip；
  - 统计：`carStatistics` 命中旧 API 缓存（STALE），`carAudit/income/topTen` 为 `X-Data-Source=API`、`X-Cache=MISS`、无 `X-Degrade`；
  - `carWarning` 200、100 行、`X-Data-Source=API`、无降级；
  - ETag 条件请求 **304**；
  - `/monitor/bigscreen/metrics`：`circuit=CLOSED`、`api.success=18`、`api.timeout=12`（停机期历史值）、`degrade=6`（历史值）、`export.active=0`；
  - 熔断恢复：首次 warning 请求成功后半开→CLOSED，后续统计/流水/导出全部正常。
- api 停机期间的表现（已记录）：统计 `X-Degrade=TIMEOUT` + `LEGACY_DB`，预警 `REDIS_SNAPSHOT`，流水/导出 `CIRCUIT_OPEN` 500/503，无异常崩溃。

> api 重启后 `stats-enabled` 实际已为 **true**（四个 stats 端点 200 且返回 dws 数据），backend 自动切到 `X-Data-Source=API`；此前“仍为 false 走 legacy”的预期未再出现，legacy 回退路径已在停机窗口验证。

处理决定：**不回滚旧 jar**。旧 jar 是 511KB thin jar，运行期已出现 `NoClassDefFoundError: io/lettuce/core`，回滚只会得到不可用实例；新实例启动正常且 api 恢复后全部补验通过。若未来仍需回滚：
```powershell
Stop-Process -Id 47532 -Force
& 'D:\jdk\jdk1.8.0_202\bin\java.exe' -Xms512m -Xmx1g -jar 'D:\work\IdeaProjects\car-monit-backend-new\ruoyi-admin\target\ruoyi-admin.jar'
```
约束遵守：未重启 9902、未新增重复实例（9990 临时联调实例已停止）、未 commit。

---

## 21. 与 api 能力补齐后的最终收敛（2026-11-09）

api 已提交 `plate_color_name`、`/api/v3/export/capabilities`、全字段维度过滤、warning `captureType` 与多值 terms。
backend 收敛并复测如下（9989 V3，带登录 token）：

| 项 | 结果 |
|---|---|
| warning 兜底 | `captureType=StationCapture`、`tollCode=StationCapture`、`roadCode=G45,G6011` 均 200/100 行、`X-Data-Source=API`、无 `X-Degrade`；`CAPTURE_TYPE_UNSUPPORTED`/`MULTI_VALUE_UNSUPPORTED` 分支已删除 |
| 展示导出 `plate_color_name` | fee 展示导出 816 行，CSV 表头末尾包含 `plate_color_name`（实测）；snapshot 按 api 能力声明自动追加，**代码推断，未单独实测** |
| 全字段维度过滤 | `fee/snapshot + sectioncode` 提交 200；`trail + sectioncode` 返回 400“按表能力矩阵未声明” |
| 统计鉴权复测 | 四个统计 200、`X-Data-Source=API`、`X-Cache=MISS`、无 `X-Degrade` |
| 指标 | `circuit=CLOSED`、`api.success` 正常增长、`degrade` 无新增 |
| 配置 | `bigscreen.export.full-dimension-filters` 恢复 `auto`，5 分钟探测能力端点 |

**仍保留的故障兜底**：api 超时/5xx/熔断、`warning-api=off` 时实时预警回退 Redis；统计回退 legacy；
导出提交/查询按错误码降级或报错。上述均只由真实故障触发，不再由“能力缺失/多值/哨兵”触发。

**仍存在的缺口**：`/base/fitting/{cid}` 详情 api 无等价端点，仍读本地表并在响应标注 `dataSource=LOCAL_DB`；api 无导出字节级 pause/resume，`/resume` 仍按原参数重新提交。

---

## 22. 2026-11-09 审阅修复：P0/P1 安全与一致性

### 22.1 修复清单

| 编号 | 问题 | 修复 | 验证方式 |
|---|---|---|---|
| P0 | `/display`、`/full` 仅登录态，任意用户可批量导出 | 控制器加 `@PreAuthorize`；`/display` 需 `manager:bigscreen:export`，`/full` 还需 `manager:bigscreen:exportFull`；服务层二次校验 | 单测 `ExportPolicyTest`（权限策略/机构范围）+ 代码推断（注解在控制器） |
| P0 | 导出无机构范围约束 | `ExportPolicy.applyOrgScope`：非管理员强制注入登录用户 `subCode` 到 `fuzzyFields.orgcode`；越机构 403；trail 表 api 无维度，非管理员拒绝 | 单测 `ExportPolicyTest`（6 个机构范围用例） |
| P0 | 上线后非超管无法使用导出 | 新增幂等权限 SQL：`ruoyi-system/src/main/resources/sql/v3-bigscreen-export-permissions.sql` | SQL 执行后附带核对查询；未在本次环境执行（无 DB 写权限） |
| P1-1 | retry/resume 绕过开关/限流/权限；审批后无限重试 | `retry()` 重新校验 `export-v3` 开关、`export`/`exportFull` 权限、限流与机构范围；审批开启时 full 重试重新入审批队列；`approve()` 校验开关 | 代码推断 + 单测覆盖审批状态机；无 API 联调 |
| P1-2 | 并发审批重复提交 api | Redis `setIfAbsent` CAS + 先落 `approving` 再提交；失败回退 `pending`；状态机禁止 pending→approved 跳转 | 单测 `ExportApprovalStateMachineTest`；Redis 原子性依赖 Redis 实现（代码推断） |
| P1-3 | 下载密钥回退公开默认值；令牌在 query string | 密钥缺失/等于历史默认值/长度<16 时启动失败；令牌改 `X-Export-Download-Token` 头（query 兼容）；响应加 `Referrer-Policy: no-referrer`、`Cache-Control: no-store` | 代码推断（启动自检在 `@PostConstruct`） |
| P1-4 | 给 api 共享键 `car_list*` 加 600s TTL | 撤销 TTL，恢复 master 无 TTL 语义 | 代码推断；需 api 侧 TrackTask/SysUtil 联调确认 |
| P1-5 | 轨迹当前页写入 `car_history_trail` 污染 api 全量 | 新增 backend 私有 `car_history_trail_page:{carNo}`；预警/物化读共享键优先、私有键兜底 | 代码推断 |
| P1-6 | 未知过滤键被 api 静默忽略导致导出全量；`plateColor=1` 被拒 | `ExportPolicy.validateFuzzy` 字段白名单：未知键 400；码值类精确字段允许单字符；车牌/名称仍 ≥2 字符 | 单测 `ExportPolicyTest`（5 个过滤用例） |
| P1-7 | 6 个详情端点仍直连本地 MyBatis | 5 个改走 api `flowDetail`；`fitting` api 无等价端点，保留本地并标注 `dataSource=LOCAL_DB`/`realtime=false` | 代码推断（api 端点已只读确认存在） |
| P2 | 空结果 30s 叠加 stale 变 150s；回源失败不返回 stale | 空结果 L1/L2 TTL 固定 30s；L1 过期后保留 5 分钟 grace，回源失败返回 stale | 单测 `TwoLevelCacheTest`（3 用例） |
| P2 | 全局熔断连坐；错误重复计数 | 熔断按 export/warning/stats/flow/default 隔离；同一次尝试只计一次错误 | 单测 `ResilientApiExecutorTest`（4 用例） |
| P2 | 审批列表 `KEYS` 阻塞 Redis | `RedisCache.scan` 使用 SCAN 游标 | 代码推断（单测未覆盖 Redis 连接） |
| P2 | 命中率两套公式 | 统一 `(L1+L2+STALE)/(L1+L2+STALE+MISS)`；告警任务改为 `cache.hit - cache.hit.MISS` | 代码推断；公式在 `BigScreenOpsController` 与 `TrafficMetricsAlertTask` 一致 |

### 22.2 GaussDB 与 ES 一致性方案（硬要求）

V3 的读取路径是**双源**：列表/展示导出走 ES，全字段导出走 GaussDB。两者不是强一致事务，必须按以下规则判定与处理：

1. **真源（SoR）**：GaussDB 是唯一真源；ES 只是检索副本。任何校正方向只能是 GaussDB → ES，禁止反向覆盖。
2. **写入链路与延迟**：
   - 主链路：Kafka 消费后应用双写 GaussDB + ES，ES `_id` 用业务主键保证幂等；
   - 补偿链路：Redis 水位增量同步（at-least-once + 幂等）、Debezium CDC 兜底；
   - ES 可见时间**晚于** GaussDB 落库，延迟取决于 Kafka 消费与 bulk 批次，当前**未声明硬性 SLA**；因此“刚写入的数据列表暂时查不到”属于预期窗口，不等于数据丢失。
3. **对账/回填**：
   - 分钟桶对账：`TrafficReconciliationService`（api，默认关闭，`traffic.reconcile.enabled`），按桶比较 GaussDB `count(*)` 与 ES range count；偏差超阈值写 `search_sync_reconcile` 并触发 `EsBackfillService` 以 GaussDB 为准回灌；
   - 月度全量对账：`GaussEsConsistencyService`（api，默认关闭，`consistency.reconcile.enabled`），按 `drift-ratio`（默认 0.01）判定 DRIFT；
   - 两者默认关闭，**上线/排障时必须显式开启并确认 cron**；仅“最终一致”四个字不能作为验收结论。
4. **列表与全字段导出结果不一致时的判定**：
   - 若差异发生在写入后短时间内（消费延迟窗口内）：判定为**预期滞后**，不做修复；以全字段导出（GaussDB）为准确认业务数据。
   - 若同一时间窗在延迟窗口后仍不一致：判定为 **ES 漂移**，执行分钟桶/全量对账 → 回灌 → 重跑展示导出；全字段导出结果不变（GaussDB 未受影响）。
   - 若 GaussDB 本身与业务系统不一致：不属于 ES 一致性问题，按数据接入/Kafka DLQ 排查，禁止用 ES 反推。
   - backend 不做二次合并或静默修正；对账/回填动作由 api 侧负责，backend 只消费结果。
5. **可观测**：api 侧对账结果、回灌任务、DLQ 需纳入监控；backend 侧导出任务保留 `totalRows`（api status）便于与另一路径行数比对。

**已知契约缺口**（不在 backend 侧硬造）：
- `/base/fitting/{cid}` api 无等价详情端点；
- api 无导出字节级 pause/resume；
- api trail 表无任何维度过滤，非管理员轨迹导出暂不支持机构收敛。


