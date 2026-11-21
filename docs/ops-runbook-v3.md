# car-monit-backend-java-V3 运维手册（查询/大屏/导出）

> 适用：backend V3 工作树 `d:\work\IdeaProjects\car-monit-backend-java-V3`  
> 配套设计与决策：`docs/architecture-traffic-query-design.md`、`docs/decisions-v3.md`  
> api 默认地址：`http://127.0.0.1:9902`（`VEHICLE_MONITOR_BASE_URL` 可覆盖）

## 1. 关键端点

| 用途 | 端点 |
|---|---|
| api 指标/开关 | `GET /monitor/bigscreen/metrics`、`GET /monitor/bigscreen/switches` |
| 全局开关 | `POST /monitor/bigscreen/switches/{name}?enabled=true|false`、`DELETE /monitor/bigscreen/switches/{name}` |
| 灰度（租户/比例） | `POST /monitor/bigscreen/gray/{name}?percent=0-100&tenants=1001,1002`、`DELETE /monitor/bigscreen/gray/{name}` |
| 导出审批列表 | `GET /manager/bigScreen/export/approvals` |
| 审批通过/驳回 | `POST /manager/bigScreen/export/approvals/{requestId}/approve|reject?reason=` |
| 导出重试/续传 | `POST /manager/bigScreen/export/{taskId}/retry`、`POST .../{taskId}/resume` |
| 下载签名 | `POST /manager/bigScreen/export/{taskId}/download-url`（返回 `downloadToken` + `tokenHeader`） |
| 下载文件 | `GET /manager/bigScreen/export/download/{taskId}`，令牌放请求头 `X-Export-Download-Token`（query `token` 仅兼容） |

权限：指标/开关需 `monitor:server:list`；导出审批需 `manager:bigscreen:exportApprove`；
展示导出需 `manager:bigscreen:export`；全字段导出还需 `manager:bigscreen:exportFull`。

## 2. 开关清单

| 开关 | 默认 | 作用 |
|---|---|---|
| `stats-api-first` | true | 统计 api 优先；关闭=立即 legacy（不读缓存） |
| `warning-api` | true | 预警列表走 api；关闭=Redis 快照 |
| `location-index` | true | 地图点位倒排索引；关闭=逐条扫描 |
| `export-v3` | true | 新导出端点；关闭=返回 503 |
| `dict-version` | true | 字典版本化主动失效；关闭=纯 TTL |
| `trail-api` | true | 轨迹在线 api 优先；关闭=本地只读 |
| `export-approval` | false | 非 admin 全字段导出先审批 |
| `trail-materialize` | false | Quartz 轨迹本地物化；默认关闭 |

灰度高优先级：**全局开关 > 租户白名单 > percent 稳定哈希 > 配置默认值**。  
Redis key：`cm:{env}:switch:{name}`、`cm:{env}:gray:{name}:percent`、`cm:{env}:gray:{name}:tenants`。

## 3. 一键回退 legacy

```bash
# 1) 全局关闭统计 api 优先（立即生效，不读缓存）
curl -X POST 'http://backend:port/monitor/bigscreen/switches/stats-api-first?enabled=false' -H 'Authorization: Bearer ...'

# 2) 或按比例灰度回退（percent=0 等价关闭）
curl -X POST 'http://backend:port/monitor/bigscreen/gray/stats-api-first?percent=0' -H 'Authorization: Bearer ...'

# 3) 或按租户回退（仅这些租户继续走 api）
curl -X POST 'http://backend:port/monitor/bigscreen/gray/stats-api-first?percent=100&tenants=1001' -H 'Authorization: Bearer ...'

# 4) 恢复
curl -X DELETE 'http://backend:port/monitor/bigscreen/gray/stats-api-first' -H 'Authorization: Bearer ...'
```

验证：统计接口响应头应出现 `X-Data-Source=LEGACY_DB`、无 `X-Cache`（回退时直接走库）、无 `X-Degrade`。

## 4. `stats-enabled` 从 false 切 true

现状：api `traffic.bigscreen.stats-enabled=false`，四个统计端点返回 503；backend `hybrid` 模式回退 legacy，响应头 `X-Degrade=UPSTREAM_ERROR/TIMEOUT`、`X-Data-Source=LEGACY_DB`、`X-Cache=MISS`。

切换条件：
1. Flink/批量任务已回填 `dws_*`，且 api 侧统计 SQL 校验通过；
2. api 配置 `traffic.bigscreen.stats-enabled=true` 并重启（api 侧操作，backend 不重启）；
3. 验证 `curl http://127.0.0.1:9902/api/v1/bigscreen/stats/escape?...` 返回 200。

验证步骤：
1. `GET /manager/bigScreen/carStatistics?applyTime1=...`：预期 `X-Data-Source=API`、无 `X-Degrade`、`X-Cache=MISS`（首次）；
2. 10s 内再次请求：`X-Cache=L1`、`X-Data-Source=CACHE`；
3. 其余三个统计同样检查；
4. `GET /monitor/bigscreen/metrics`：`api.upstream_error` 不再增长，`api.success` 增长，熔断保持 CLOSED；
5. 对比 legacy 数值，允许 HLL 近似差异（设计 §11.3）。

回退：
- 快速：`stats-api-first=off` / `gray percent=0`；
- 彻底：api `stats-enabled=false` 或 backend `bigscreen.stats.mode=legacy`（需重启 backend）。

## 5. 导出审批 / 保留期 / 重试 / 清理

| 项 | 操作 |
|---|---|
| 开启审批 | `export-approval=on`；非 admin full 导出返回 `pending_approval` + `requestId` |
| 审批 | `GET /manager/bigScreen/export/approvals`；`POST .../approve` 按原申请人身份提交；`POST .../reject?reason=` |
| 保留期 | `export.retention-days=7`，任务元数据与审批请求 Redis TTL；文件保留由 api/对象存储负责 |
| 失败重试 | `POST /manager/bigScreen/export/{taskId}/retry`；仅 `failed/canceled/paused` 可重试，新 taskId，attempts+1；**重试会重新校验 `export-v3` 开关、`export`/`exportFull` 权限、限流与机构范围**；审批开启时非 admin 的 full 重试重新进入审批 |
| 断点续传 | `POST .../{taskId}/resume`；api 无字节级续传，按原参数重新提交，返回 `resumeMode=resubmit` |
| 积压清理 | `ExportTaskCleanupTask` 每小时清理超过保留期未轮询终态的本地 active 计数；Redis TTL 自然过期 |

> 注意：重试/续传会产生**新 taskId**，原任务与文件不删除，便于审计；下载仍用新 taskId 的签名令牌。
> 审批并发：同一 requestId 同一时刻只允许一个审批提交（Redis CAS + `approving` 状态）；重复点击返回“审批正在处理中”。

## 6. 指标与告警

| 指标 | 含义 | 默认告警阈值 |
|---|---|---|
| `api.timeout / api.request` | api 超时率 | ≥20%/分钟 |
| `degrade` | 降级次数 | ≥10/分钟 |
| `cache.hit - cache.hit.MISS` vs `cache.hit.MISS` | 缓存命中率（统一公式 `(L1+L2+STALE)/总`） | <50%（样本≥10） |
| `export.active` | 导出积压 | ≥20 |
| `api.circuit.state` | 0 关/1 开/2 半开（各域最高级别） | 打开即告警 |

端点：`GET /monitor/bigscreen/metrics` 返回 counters/gauges/超时率/命中率/积压/整体熔断状态，以及 `circuitScenarios`（export/warning/stats/flow/default 各域状态）。  
告警任务：`TrafficMetricsAlertTask` 每 60s 输出 WARN 并累加 `alert.*`；阈值 `traffic-api.metrics.*`。

## 7. 字典主动失效

- 写入 hook：系统字典、路段、收费站、门架、服务区、机构的新增/修改/删除后 INCR 版本号；
- 生效时间：各节点 ≤5s（本地版本缓存）。**该时限只对经 backend 后台写入的变更成立**；api 直接改库不触发 hook，需等 TTL 或手动失效；
- 验证：`/monitor/bigscreen/switches` 确认 `dict-version=true`；修改字典后 5s 内列表颜色/名称变化；
- 回退：`dict-version=off`，回到 TTL 失效。

## 8. 联调/巡检清单

1. 四个统计：200，`X-Data-Source` 与 `X-Degrade` 符合预期；
2. `carWarning`：200，`X-Data-Source=API`，无降级；索引空时 200+[]，ES 不可达 503 才降级；
   `captureType` 哨兵与逗号多值由 api terms 处理，backend 不再回退 Redis（仅 api 故障时回退）；
3. 流水列表：门架/收费/省界/收费站/称重/出入口/交易/服务区/拟合轨迹均 200，`total` 合理；
4. 双路径导出：提交→状态 done→签名下载，gzip 魔数 `1F 8B`；
5. 轨迹在线：`listByCarId` 返回 trailList 点数；本地表不再增长（物化关闭）；
6. 指标与开关端点可访问，灰度 percent=0 时统计立即 legacy。

## 9. 已知缺口（待 api 补齐）

| 缺口 | 当前 backend 行为 | api 补齐后 |
|---|---|---|
| 展示导出 `plate_color_name` | snapshot/fee 均按 api 能力声明自动追加；trail 请求该列返回 400 | — |
| `/api/v3/export/capabilities` | **已实现**：按表矩阵放开（trail 维度过滤仍拒绝） | — |
| 导出字节级续传 | `/resume` 按原参数重新提交（`resumeMode=resubmit`） | api 提供 pause/resume 后改为真正续传 |
| `/base/fitting/{cid}` 详情 | api 无等价端点，读 backend 本地表；响应 `dataSource=LOCAL_DB`、`realtime=false`，数据可能陈旧 | api 提供按 cid 详情后切换 |
| 轨迹表机构维度 | api trail 无维度过滤，非管理员轨迹导出被拒绝（403） | api 提供机构维度后放开 |

## 10. 上线前检查（必须）

1. **执行权限初始化 SQL**：`ruoyi-system/src/main/resources/sql/v3-bigscreen-export-permissions.sql`
   （幂等；按需修改 `@grant_role_keys`），否则非超管无法使用导出。
2. **配置下载密钥**：设置环境变量 `EXPORT_DOWNLOAD_SECRET`（≥16 位，且不得为 `abcdefghijklmnopqrstuvwxyz`）。
   未配置时应用**启动失败**，这是预期行为，不要回退到 `token.secret`。
3. **确认导出开关**：`export-v3=true`；按需开启 `export-approval`。
4. **确认机构绑定**：非管理员用户必须有 `subCode`（≠ `-1`），否则导出返回 403。
5. **确认无 TTL 共享键**：Redis `car_list`/`car_list_jc` 不应带 TTL；api `TrackTask`/`SysUtil` 只读消费。
6. **确认轨迹私有键**：backend 在线查询只写 `car_history_trail_page:{carNo}`，不写 api 的 `car_history_trail:{carNo}`。
7. **确认对账任务**：如需 GaussDB/ES 一致性保障，按 `docs/decisions-v3.md §22.2` 显式开启 api 侧对账 cron。
