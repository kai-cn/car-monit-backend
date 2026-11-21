# V3 需认证大屏 / 导出链路实机验证记录

> 在 `car-monit-backend-java-V3` 与 `car-monit-api-java-V3` 两个工作树的
> `docs/v3/review/` 下各存一份，内容一致。记录日期：2026-11-10。
> **本文件不写任何账号口令、会话令牌、下载令牌、内部端点令牌或 GitHub 凭据明文。**

## 1. 目的与前置状态

- 目标：用具备权限的 `admin` 账号跑通需认证的大屏统计、导出提交 → 轮询 → 下载、
  全字段导出、重试状态机、审批列表、运维指标，并复跑 api 侧守卫与边界限制；
  随后复用本机已有的多角色测试账号补跑越权用例。
- **与 `05` 第 7 节的关系（如实说明并行记录）**：同一工作树在 2026-11-10 13:16 有另一会话
  提交 `2a8957f`（backend）/ `39525be`（api），已在 `05` 第 7 节记录更完整的多角色越权与
  审批通过/驳回链路，并新建测试账号 `v3audit_view` / `v3audit_mgr`、补插权限菜单 3020~3022。
  本文件是**独立复跑**，重点在 admin 视角、机构维度 SQL 下推实证、api 侧边界重跑，
  以及用同一批测试账号复核令牌绑定 / 跨机构拒绝；两份记录互补，**未覆盖或改写第 7 节内容**。
- 账号：用户提供的 `admin` 账号；**口令仅通过命令内变量传入，不写入文档、脚本或仓库文件**。
- 服务状态（启动前核查，未重复启动）：

| 端口 | 服务 | listeners |
| --- | --- | --- |
| 9902 | api java（`-Xmx1g`） | 1 |
| 9989 | backend java（`-Xmx1g`） | 1 |
| 9200 / 9092 / 6379 / 3307 | ES / Kafka / Redis / MySQL 8 | 各 1（6379 为 IPv4+IPv6 双 listener） |

- 两侧使用同一个临时内部端点令牌（`X-Internal-Token`），backend 另有临时下载签名密钥；
  值不记录。api 侧未配置令牌时守卫只放行回环，本次为验证 403 而显式配置了令牌。

## 2. 复现命令（口令由环境注入）

```powershell
# 口令不落盘：由运行环境提供，命令与文档均不出现明文
$pw = $env:E2E_PASSWORD
$body = @{ username = 'admin'; password = $pw } | ConvertTo-Json
$lg = Invoke-RestMethod -Uri 'http://127.0.0.1:9989/login' `
        -Method Post -Body $body -ContentType 'application/json'
$h = @{ Authorization = "Bearer $($lg.token)" }

# 大屏统计（示例）
Invoke-RestMethod -Uri 'http://127.0.0.1:9989/manager/bigScreen/carStatistics?applyTime1=2025-01-01&applyTime2=2025-12-31' -Headers $h

# 展示字段导出
$req = @{ type='snapshot'; startTime='2025-01-01'; endTime='2025-01-31' } | ConvertTo-Json
$sub = Invoke-RestMethod -Uri 'http://127.0.0.1:9989/manager/bigScreen/export/display' `
        -Method Post -Headers $h -Body $req -ContentType 'application/json'
$tid = $sub.data.taskId
Invoke-RestMethod -Uri "http://127.0.0.1:9989/manager/bigScreen/export/status/$tid" -Headers $h

# 下载：令牌只走请求头
$di = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:9989/manager/bigScreen/export/$tid/download-url" -Headers $h
$dh = @{ Authorization = "Bearer $($lg.token)"; 'X-Export-Download-Token' = $di.data.downloadToken }
Invoke-WebRequest -Uri "http://127.0.0.1:9989/manager/bigScreen/export/download/$tid" -Headers $dh -OutFile <file>

# api 侧内部端点
$ah = @{ 'X-Internal-Token' = $env:V3_INTERNAL_TOKEN }
Invoke-RestMethod -Uri 'http://127.0.0.1:9902/api/v3/export/capabilities' -Headers $ah
```

每批验证都重新登录取会话令牌，**未把任何 token 写入临时文件**（唯一落盘的 `taskId`
临时文件在用完后已直接删除）。

## 3. 验证结果

### 3.1 登录与鉴权

| # | 验证 | 结果 |
| --- | --- | --- |
| 1 | `POST /login` | `code=200 操作成功`，取得会话令牌 |
| 2 | 不带认证头 `GET /monitor/bigscreen/metrics` | **HTTP 200 + 业务 `code=401`**「认证失败，无法访问系统资源」；RuoYi 的 AjaxResult 风格，HTTP 200 不代表放行 |

### 3.2 需认证的大屏统计链路（8 个接口全部 200）

| 接口 | code | 数据 | `X-Data-Source` |
| --- | --- | --- | --- |
| `/manager/bigScreen/carStatistics` | 200 | 6 组 | `API` / 命中缓存时 `CACHE` |
| `/manager/bigScreen/carAudit` | 200 | 对象 | `API` |
| `/manager/bigScreen/incomeStatistic` | 200 | 0 行 | `API` |
| `/manager/bigScreen/topTen` | 200 | 0 行 | `API` |
| `/manager/bigScreen/orgList` | 200 | 481 行 | — |
| `/manager/bigScreen/sectionList` | 200 | 86 行 | — |
| `/manager/bigScreen/exceptionCar` | 200 | 2 行 | — |
| `/manager/bigScreen/carVoList` | 200 | 10 行 | — |

**关键结论**：统计接口 `X-Data-Source: API` 且 `circuit=CLOSED`、`apiErrorRate=0.0`，
说明 backend → api 的出站请求成功通过了 api 侧 `X-Internal-Token` 守卫（否则会被 403 拒绝），
`TrafficApiHttpClient` / `ApplicationConfig` 的令牌注入在实机生效。

### 3.3 机构维度回落 legacy 与 SQL 下推（本轮修复项）

| 接口（带 `orgCode=0000001100530008`） | code | `X-Data-Source` |
| --- | --- | --- |
| `carStatistics` | 200 | `LEGACY_DB` |
| `carAudit` | 200 | `LEGACY_DB` |
| `incomeStatistic` | 200 | `LEGACY_DB` |

- 三条新加 `EXISTS (sys_dept d ... d.sub_code like concat(#{orgCode},'%'))` 的 SQL 实机执行无报错。
- 过滤生效实证：同一时间范围 `carStatistics` 的 `sum(number)`
  由 **112（不带 orgCode）降为 94（带 orgCode）**；分组行数均为 6（按 `escaped_type` 分组）。
- `api/v3/export/capabilities` 返回 HTTP 200，含 `modes`、`tables`、
  `fullDimensionFilters`、`multiValueDimensionFilters`、`plateColorName` 等字段
  （该端点直接返回 JSON 对象，不是 `{code,data}` 包装）。

### 3.4 导出全链路

| # | 验证 | 结果 |
| --- | --- | --- |
| 1 | `POST /manager/bigScreen/export/display`（snapshot，2025-01） | `code=200`，返回 `taskId/mode/status/message`，任务 ID `749ad669…` |
| 2 | 轮询 `/export/status/{taskId}` | 首次即 `done` |
| 3 | `POST /manager/bigScreen/export/full`（trail，2025 全年 + purpose） | `code=200`，任务 ID `c8882642…`，轮询 `done` |
| 4 | `POST /export/{taskId}/download-url` | `code=200`，`tokenHeader=X-Export-Download-Token`、`expiresIn=900` |
| 5 | 不带下载令牌 `GET /export/download/{taskId}` | **HTTP 403** |
| 6 | 令牌放 query `?token=…` | **HTTP 403**（query 兼容已移除） |
| 7 | 令牌放 `X-Export-Download-Token` 请求头 | **HTTP 200**，gzip 132 字节 |
| 8 | 下载响应安全头 | `X-Content-Type-Options: nosniff`、`Referrer-Policy: no-referrer` |
| 9 | 解压 CSV 表头 | 23 列：`big_id, snapshottime, platenumber, …, plate_color_name` |
| 10 | CSV 数据行 | 本次时间范围（2025-01）无匹配数据，仅表头；`CSV_ROW1` 为空 |
| 11 | `POST /export/{done任务}/retry` | `code=400`「仅 failed/canceled/paused 任务可重试，当前状态: done」 |
| 12 | `POST /export/{done任务}/resume` | 同上 `code=400`，终态守卫正确 |
| 13 | `GET /export/approvals` | `code=200`，0 条（admin 全字段导出不进审批队列，符合设计） |

> 控制台出现中文乱码（如 `ä» failed/...`）是 PowerShell 5.1 对无 charset 响应体的解码问题，
> 业务码与状态机行为正确，非功能缺陷。

### 3.5 api 侧守卫与边界限制（重跑）

| 验证 | 结果 |
| --- | --- |
| 不带 `X-Internal-Token` 访问 `/api/v3/es/readiness` | **HTTP 403** |
| 带正确令牌访问同一端点 | **HTTP 200 / code=200** |
| 超窗回灌（2020-01-01 ~ 2026-01-01） | `code=500`「回灌时间范围不能超过 **450 天**」，未创建任务 |
| 对账 2025 全年 + `bucketMinutes=1` | `code=400`「对账桶数过多（**524160** 桶/表，上限 10000）」 |
| 孤儿清理超范围（2020-01-01 ~ 2026-01-01） | `code=400`「孤儿清理时间范围非法或超过 **365 天**」 |

### 3.6 运维可观测性

| 接口 | code | 关键值 |
| --- | --- | --- |
| `/monitor/bigscreen/metrics` | 200 | `circuitState=CLOSED`、`apiTimeoutRate=0.0`、`apiErrorRate=0.0`、`cacheHitRate=0.8571`、`exportBacklog=1` |
| `/monitor/bigscreen/switches` | 200 | 8 个开关：`stats-api-first, warning-api, location-index, export-v3, dict-version, trail-api, export-approval, trail-materialize` |

### 3.7 多角色越权用例（复用并行会话保留的测试账号，独立复跑）

账号：`v3audit_view`（common 角色、dept 25424）、`v3audit_mgr`（project_manager、dept 25367），
口令策略与 admin 一致（值不记录）。两者登录与 `getInfo` 均返回 `code=200`。

| # | 用例 | 本轮结果 | 说明 |
| --- | --- | --- | --- |
| 1 | view 提交 `POST /export/display` | `HTTP 200 / code=200` | **与 `05` 第 7 节记录的 403 不同**：第 7 节在补插 menu 3020~3022 **之前**测得 403，随后为越权用例给 role 2（view）授权了导出权限且按该节说明「保留」。本轮复跑时 view 已具备 `manager:bigscreen:export`，故 200 符合当前权限种子，不是权限门失效。 |
| 2 | view 修改安全开关 `POST /monitor/bigscreen/switches/export-approval?enabled=true` | `HTTP 200 / code=403`「没有权限，请联系管理员授权」 | B-04 安全开关权限校验生效（view 无 `exportApprove`） |
| 3 | mgr 提交 display 导出 | `code=200`，taskId `23f06015…`，轮询 `done` | 链路通 |
| 4 | view 使用 mgr 的下载令牌下载 | **HTTP 403** | B-01 下载令牌绑定登录用户实证 |
| 5 | view 重试 mgr 的任务 | `HTTP 200 / code=403`「无权访问该导出任务」 | B-02 跨机构 / 跨用户重拒绝实证 |
| 6 | mgr 本人 + 有效令牌下载 | **HTTP 200**，gzip 132 字节 | 正常路径 |
| 7 | 临时下载文件 | 直接删除，`exists=False` | 未进回收站 |

> 本轮未改动任何权限种子、运行期开关或测试账号；若需要恢复「view 无导出权限」的初始状态，
> 参见 `05` 第 7.3 节的回收 SQL。

## 4. 未覆盖 / 边界（如实）

| 项 | 状态 |
| --- | --- |
| 换用户下载令牌 403 | **本轮已覆盖**（3.7 #4，HTTP 403）；`05` 第 7 节 #8 亦独立验证 |
| 跨机构 / 跨用户 retry 403 | **本轮已覆盖**（3.7 #5，code=403）；`05` 第 7 节 #10 亦独立验证 |
| 运维写接口权限负向路径 | **本轮已覆盖安全开关正向拒绝**（3.7 #2，code=403）；`05` 第 7 节 #11/#16 覆盖了 gray 写入与删除两条路径 |
| 审批通过 / 驳回链路 | 本轮 admin 视角 `approvals=0`（admin 不入审批队列）；**已由 `05` 第 7 节 #13~#15 用 view/mgr 双角色验证通过并驳回**，本轮未重复 |
| retry / resume 的成功路径 | 仍需先构造 `failed/canceled/paused` 任务；本轮导出均一次 `done`，只验证了终态拒绝守卫（3.4 #11/#12） |
| CSV 公式注入实证 | 需构造含 `=SUM(...)` 的业务数据；本次结果集为空，转义逻辑由静态复核与单测覆盖 |
| 破坏性用例（指南 3.4 #9/#11/#12） | 按 `05` 第 7.3 节约定，需专用测试库 / 测试索引，不在本机联调库执行 |
| GitHub CI | 仍因账号账单 / 支出限额未启动任何 job，见 `05` 第 2、6 节；本轮 E2E 不替代 CI 门禁 |

## 5. 清理与凭据处理

- 下载的 gzip 测试文件、`taskId` 临时文件、推送临时日志均**直接删除**（未进回收站），
  核查 `exists=False`。
- 账号口令、会话 JWT、下载签名令牌、内部端点令牌、GitHub 凭据**均未写入**任何文档、
  脚本、提交信息或残留日志；会话令牌仅在单条命令的内存变量中传递，各批验证重新登录。
- 本轮未新建测试库 / 测试索引 / 测试 topic，未产生需要清理的测试数据。
- 联调结束后 9902 / 9989 各保留 1 个 java 实例（符合「最多一个 backend + 一个 api」约束），
  未重复启动 ES / Kafka / Redis / MySQL。
