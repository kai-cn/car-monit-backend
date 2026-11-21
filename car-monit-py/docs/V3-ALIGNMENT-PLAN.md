# backend Python 镜像对齐 Java V3 —— 实施计划与端点差距矩阵

> 创建时间：2026-11-20
> 工作树：`d:/work/IdeaProjects/car-monit-py-V2-wt`（分支 `py-v3-align`，源自 `car-monit-py-V2`）
> 对齐目标：`d:/work/IdeaProjects/car-monit-backend-java-V3`（分支 `car-monit-backend-java-V3`）
> 原则：**行为等价 > 结构镜像 > 可追溯**。Java 的缺陷照抄，差异写在注释与对照手册里。

---

## 1. 基线确认（已实测）

Python 迁移基线为 master（Java 1.8 / Spring Boot 2.4.5），498 个 `@router.*` 端点。Java V3 相对 master：

- `108 files changed, +11201/-943`（`*.java/xml/yml/properties`）
- **真正新增的 HTTP 路径只有两组**：`/manager/bigScreen/export/**`（10）与 `/monitor/bigscreen/**`（6）
- `GET /manager/bigScreen/topTen` 增加 `startTime` / `endTime` 可选参数（默认最近 7 天）
- 新增 `BigScreenResponseFilter`：为 `/manager/bigScreen` 前缀 GET 增加 ETag/304 与可观测响应头
- 字典写操作增加版本自增（`DictVersionService.bump`）
- 多个 base Controller 数据源从本地表切到 api 的 HTTP 接口；`ZdataTrailFittingController` 保留本地库

## 2. 端点差距矩阵

### 2.1 新增 `/manager/bigScreen/export/**`（10）

| HTTP + 路径 | Java 方法 | 权限 | 行为要点 |
|---|---|---|---|
| POST `/manager/bigScreen/export/display` | `display` | `manager:bigscreen:export` | 展示字段 ES PIT 异步导出，返回 taskId |
| POST `/manager/bigScreen/export/full` | `full` | `export`+`exportFull` | 全字段 GaussDB 游标异步导出 |
| GET `/manager/bigScreen/export/status/{taskId}` | `status` | 登录 | 任务状态 |
| POST `/manager/bigScreen/export/{taskId}/retry` | `retry` | `export` | 按原参数重提 |
| POST `/manager/bigScreen/export/{taskId}/resume` | `resume` | `export` | 伪续传，结果附加 `resume=true` 与固定 message |
| POST `/manager/bigScreen/export/{taskId}/download-url` | `downloadUrl` | 登录 | 15 分钟签名信息 |
| GET `/manager/bigScreen/export/download/{taskId}` | `download` | 登录+令牌头 | 令牌**只走** `X-Export-Download-Token` 头；query 不再兼容 |
| GET `/manager/bigScreen/export/approvals` | `approvals` | `exportApprove` | 待审批列表 |
| POST `/manager/bigScreen/export/approvals/{requestId}/approve` | `approve` | `exportApprove` | 审批通过 |
| POST `/manager/bigScreen/export/approvals/{requestId}/reject` | `reject` | `exportApprove` | 驳回，`reason` 可选 |

错误码映射（`ApiClientException` → HTTP）：`INVALID_ARGUMENT→400`、`NOT_FOUND→404`、`FORBIDDEN→403`、`RATE_LIMITED→429`、`UNAVAILABLE/CIRCUIT_OPEN/TIMEOUT/UPSTREAM_ERROR→503`、其它 `500`。`download` 特例：403 或 404，写 `AjaxResult.error(msg)` JSON。

### 2.2 新增 `/monitor/bigscreen/**`（6）

| HTTP + 路径 | Java 方法 | 行为要点 |
|---|---|---|
| GET `/monitor/bigscreen/metrics` | `metrics` | counters/gauges、`apiTimeoutRate`、`apiErrorRate`、`cacheHitRate`、`exportBacklog`、`circuitState(s)` |
| GET `/monitor/bigscreen/switches` | `switches` | `effective`/`defaults`/`gray` |
| POST `/monitor/bigscreen/gray/{name}` | `overrideGray` | `percent` 默认 100；`tenants` 逗号分隔 |
| DELETE `/monitor/bigscreen/gray/{name}` | `clearGray` | — |
| POST `/monitor/bigscreen/switches/{name}` | `override` | `enabled` 必填 |
| DELETE `/monitor/bigscreen/switches/{name}` | `clear` | — |

全部要求 `monitor:server:list`；`export-approval` 开关改/删额外要求 `manager:bigscreen:exportApprove`。
比率计算：`round(x * 10000) / 10000`（Java `Math.round` 的 4 位小数）；分母 ≤ 0 返回 0。

### 2.3 既有端点修改

- `GET /manager/bigScreen/topTen`：新增 `startTime`/`endTime`（默认最近 7 天），走 `getTopTenRange`。
- `BigScreenResponseFilter`：路径前缀 `/manager/bigScreen`（**驼峰**），GET 响应增加 ETag/304、`X-Cache`、`X-Degrade`、`X-Data-*`；下载流排除。
- `SysDictDataController` `:112/:126/:139`、`SysDictTypeController` `:78/:96/:109/:122` 写操作后字典版本自增。
- base 14 个 Controller 数据源切 API；`ZdataTrailFittingController` 响应带 `dataSource=LOCAL_DB`。

## 3. 实施顺序

1. P0：两个新 Router + topTen 参数，注册进 `app/main.py`，路由计数门禁通过。
2. P1：`BigScreenExportService` / `FeatureSwitchService` / `MetricsRegistry` / `DictVersionService` 镜像。
3. P2：响应头/ETag Filter、权限点、错误码映射、内部守卫。
4. P3：测试脚本、文档索引、独立复核、推送。

## 4. 验证命令

```powershell
cd d:\work\IdeaProjects\car-monit-py-V2-wt\car-monit-py
python -m pytest -q tests
python scripts/smoke_test.py
```

## 5. 交接

任务中断时更新同目录 `HANDOVER.md`。
