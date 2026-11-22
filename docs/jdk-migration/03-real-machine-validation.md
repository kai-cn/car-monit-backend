# 03 · 实机验证记录（admin 建号 → 角色化验证）

> 端口：backend `9989`、api `9902`；口令与内部令牌由运行环境注入，**不写入版本库文档**。
> 每轮验证只启动一个 backend Java + 一个 api Java（`-Xms512m -Xmx1g`），改构建后先停旧服务再启新服务。

## 1. 测试账号与角色

由 backend 管理员通过 `POST /system/user` 创建，验证完成后删除：

| 账号前缀 | 角色 | roleId | 权限数 | 菜单数 |
| --- | --- | --- | --- | --- |
| `jdk{17,21,25}e2e_view` | `common` | 2 | 3 | 0 |
| `jdk{17,21,25}e2e_mgr` | `project_manager` | 132 | 74 | 5 |

admin 自身：`getInfo` → `roles=['admin']`，`permissions=['*:*:*']`。

## 2. 复现步骤

```bash
# 1) 停掉旧 app Java，保留 MySQL/Redis/ES/Kafka
# 2) 启 api（以 JDK17 为例，21/25 换 java 路径与 jar 路径）
export TRAFFIC_INTERNAL_TOKEN=...        # 本地临时值
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=...
export TRAFFIC_QUERY_ENGINE=es TRAFFIC_BIGSCREEN_STATS_ENABLED=true
"<JDK>/bin/java" -Xms512m -Xmx1g -Dfile.encoding=UTF-8 \
  --add-opens java.base/java.lang=ALL-UNNAMED -Dserver.port=9902 \
  -jar "<worktree>/pro-business-api/target/pro-business-api-1.0.jar" \
  --spring.config.additional-location=file:D:/work/runtime-logs/api-local.properties \
  "--spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://127.0.0.1:15432/RuoYi?..."

# 3) 启 backend
export TRAFFIC_API_INTERNAL_TOKEN=...     # 与 api 侧同值
export EXPORT_DOWNLOAD_SECRET=...
"<JDK>/bin/java" -Xms512m -Xmx1g -Dfile.encoding=UTF-8 \
  -Dserver.port=9989 -jar "<worktree>/ruoyi-admin/target/ruoyi-admin.jar"

# 4) 就绪判定：GET / → 200；GET /api/v3/export/capabilities + X-Internal-Token → 200
# 5) 角色化验证脚本：D:/work/runtime-logs/smoke_jdk.py（17/21/25 复用）
```

## 3. JDK17 完整角色化 E2E（49 条结果行 + 1 条汇总，全部符合预期）

持久化结果：`D:\work\runtime-logs\jdk17-e2e-record.txt`（50 行报告 = 49 条结果行 + 1 条汇总）。

### 3.1 身份与菜单

| 检查 | 结果 |
| --- | --- |
| admin `/login` / `/getInfo` | HTTP 200，`token_len=184`，`*:*:*` |
| admin 创建 2 个测试账号 | HTTP 200 `code=200`，列表各 `total=1` |
| viewer `/login` / `/getInfo` / `/getRouters` | HTTP 200，`common`，3 权限，0 菜单 |
| mgr `/login` / `/getInfo` / `/getRouters` | HTTP 200，`project_manager`，74 权限，5 菜单 |

### 3.2 大屏与 backend→API 链路

| 接口 | viewer | mgr | 数据行数 |
| --- | --- | --- | --- |
| `/manager/bigScreen/carStatistics` | `X-Data-Source=API` | `CACHE`（二次请求命中 Redis） | 6 |
| `/manager/bigScreen/carAudit` | `API` | `CACHE` | — |
| `/manager/bigScreen/orgList` | 200 | 200 | 481 |
| `/manager/bigScreen/sectionList` | 200 | 200 | 86 |
| `/manager/bigScreen/carVoList` | 200 | 200 | 10 |
| `/manager/bigScreen/exceptionCar` | 200 | 200 | 2 |
| `/monitor/bigscreen/metrics` / `switches` | 200 | 200 | — |

首次 `API`、随后 `CACHE` 证明 backend 确实经 HTTP 从 api 取数并写入 Redis 共享缓存；
metrics：`circuit=CLOSED`、`apiErrorRate=0.0`、`apiTimeoutRate=0.0`、`cacheHitRate=0.5`、
`exportBacklog=1`，`switches` 3 项。

### 3.3 权限与导出状态机

| 检查 | 期望 | 实测 |
| --- | --- | --- |
| viewer `GET /manager/bigScreen/export/approvals` | 无权限 | HTTP 200 / 业务 `code=403` |
| viewer `POST /monitor/bigscreen/switches/export-approval` | 无权限 | HTTP 200 / 业务 `code=403` |
| `POST /export/display` | 生成任务 | HTTP 200 `code=200`，`taskId` 返回 |
| `GET /export/status/{taskId}` | 轮询至完成 | `running → done` |
| `POST /export/{taskId}/download-url` | 签发下载令牌 | `X-Export-Download-Token`，`expiresIn=900` |
| `GET /export/download` 无令牌 | 403 | **403** |
| `GET /export/download` 有效令牌 | 200 gzip | **200，132 B，gzip magic=true** |
| `GET /export/download` 跨用户令牌 | 403 | **403** |
| `POST /export/{taskId}/retry` on done | 业务拒绝 | `code=400 仅 failed/canceled/paused 任务可重试` |

> 首轮曾因任务仍 `running` 时下载得到 HTTP 409，补做轮询后结果见上表，属预期异步行为而非缺陷。

### 3.4 API 侧

| 检查 | 结果 |
| --- | --- |
| `GET /api/v3/export/capabilities` 无 `X-Internal-Token` | **403** |
| 同上带令牌 | 200，`modes=[display, full]`，`tables=[snapshot, fee, trail]` |
| `GET /api/v3/es/readiness` 带令牌 | 200 `code=200` |
| `/base/snapshotflow/list`、`/base/feerecords/list`、`/base/sysutil/carTrackQueryByCarNo` | 均 200 `code=200`，`msg=查询成功`（测试库当期无匹配数据，`total=0`） |
| `/api/v1/large/carTrackQueryByCarNo` | 200，返回结构正常 |

### 3.5 一个需要澄清的观察（非迁移回归）

viewer 调 `GET /system/user/list` 返回 HTTP 200 / `total=12`，不是 403。排查结果：
`SysUserController#list` 没有 `@PreAuthorize`，`SecurityConfig` 使用 `.anyRequest().authenticated()`，
角色 `2` 也无 `system:user*` 权限 —— 该接口在当前设计下是「登录即可访问」。
**这是迁移前就有的行为，与 JDK 升级无关**；若从最小权限角度需要收紧，应作为独立安全项处理。

## 4. 首轮 JDK21 / JDK25 顺序冒烟（各 26/26 PASS）

脚本 `D:/work/runtime-logs/smoke_jdk.py`，日志 `jdk21-smoke.log`、`jdk25-smoke.log`。

| 检查组 | JDK21 | JDK25 |
| --- | --- | --- |
| admin 登录 / getInfo | PASS | PASS |
| 创建 common / project_manager 账号并登录 | PASS（3 / 74 权限，0 / 5 菜单） | PASS（3 / 74 权限，0 / 5 菜单） |
| 大屏 4 个接口 | PASS，`carStatistics`/`carAudit` 为 `X-Data-Source=API` | PASS，首次为 `CACHE`（Redis 已被 JDK21 预热） |
| metrics | PASS，`circuit=CLOSED`，`apiErrorRate=0.0` | PASS，`circuit=CLOSED`，`cacheHitRate=1.0` |
| viewer 导出审批无权限 | PASS `code=403` | PASS `code=403` |
| api 内部令牌守卫（无令牌 403 / 有令牌 200） | PASS | PASS |
| api capabilities / es readiness | PASS | PASS |
| 4 个查询接口 | PASS 200 | PASS 200 |
| 测试账号清理与复核 | PASS `total=0` | PASS `total=0` |

**JDK25 补强验证**：为避免 `CACHE` 掩盖真实 HTTP 调用，改用不同时间范围强制 miss，得到
`X-Data-Source=API`；该观察在最终 jar 复验中又重新取证并落盘。

## 5. 最终 jar 复验（整改后）

独立审查整改、Spring 版本对齐、starter-test scope 修复与 `spring-test:5.3.39` 离线依赖补取完成后，
重新构建出 6 个 `*-build-final2.log` 对应 jar。按「先停旧 app Java，再启一对新服务」的顺序，
再次跑 JDK17 → JDK21 → JDK25 实机冒烟。

| 分支 | 启动日志 | 运行时横幅 | 最终冒烟日志 | 结果 |
| --- | --- | --- | --- | --- |
| JDK17 | `jdk17-api-recheck.console.log` / `jdk17-backend-recheck.console.log` | `using Java 17.0.21` | `jdk17-recheck-smoke.stdout.log` | `checks=26 fails=0` |
| JDK21 | `jdk21-api-recheck.console.log` / `jdk21-backend-recheck.console.log` | `using Java 21.0.12.1` | `jdk21-recheck-smoke.stdout.log` | `checks=26 fails=0` |
| JDK25 | `jdk25-api-recheck.console.log` / `jdk25-backend-recheck.console.log` | `using Java 25.0.4.1` | `jdk25-recheck-smoke.stdout.log` | `checks=26 fails=0` |

每轮覆盖：admin 登录/建号、common 与 project_manager 登录、大屏接口、metrics、
viewer 导出审批无权限、api 内部令牌守卫、capabilities / es readiness、4 个查询接口、
REST 软删与列表复核。最终三套日志的摘要行：

```text
=== JDK17 SMOKE SUMMARY: checks=26 fails=0 ===
=== JDK21 SMOKE SUMMARY: checks=26 fails=0 ===
=== JDK25 SMOKE SUMMARY: checks=26 fails=0 ===
```

JDK25 最终服务仍在运行时，对 api pid `20148`、backend pid `35044` 执行 `jcmd VM.version`，
输出落盘 `D:\work\runtime-logs\evidence-jdk25-jcmd.txt`：

```text
OpenJDK 64-Bit Server VM version 25.0.4.1+1-LTS
JDK 25.0.4.1
```

并重新强制 cache miss，输出落盘 `D:\work\runtime-logs\evidence-jdk25-cache-miss.txt`：

```text
/manager/bigScreen/carStatistics -> HTTP 200 code=200 X-Data-Source=API
/manager/bigScreen/carAudit      -> HTTP 200 code=200 X-Data-Source=API
```

配合最终 jar 的 class major `65`，证明 **Spring 5.3.39 在 Java 25 运行时**
可正常完成组件扫描、AOP、MyBatis、Kafka 监听、Redis 与 backend→api HTTP 调用链。

## 6. 测试数据清理

1. 每轮先通过 `DELETE /system/user/{ids}` 软删，复核用户列表 `total=0`。
2. RuoYi 是软删（`del_flag=1`），DB 中仍会残留行，因此必须再物理删除。
3. 首轮 8 个软删账号已在 3307 现有实例 `carmonitdb` 中直接删除
   （`user_id` 990186–990193）。
4. 最终 jar 复验又生成 6 个账号（`user_id` 990194–990199），同样在最终服务停止后直接执行：

   ```sql
   DELETE FROM carmonitdb.sys_user_role WHERE user_id IN (
       SELECT user_id FROM carmonitdb.sys_user
       WHERE user_name LIKE 'jdk%e2e%' OR user_name LIKE 'jdk17\_%'
   );
   DELETE FROM carmonitdb.sys_user
   WHERE user_name LIKE 'jdk%e2e%' OR user_name LIKE 'jdk17\_%';
   ```

5. 验证时复核：

   ```text
   remaining_e2e=0
   total_users=8
   ```

导出任务为内存/Redis 态，无 MySQL 落库表；未新建任何测试数据库、未启动第二个 MySQL 实例。
验证结束时 app Java 进程为 0，MySQL / Redis / ES / Kafka / openGauss 各一个实例；
上述验证时状态写入 `D:\work\runtime-logs\evidence-final-gate.txt`。
2026-11-12 独立复验时再次只读复核：当前 app Java 与 infra 监听端口均为 0，无重复实例；
`remaining_e2e=0`、`total_users=8` 是验证时通过 live MySQL 取得的历史结论，当前 MySQL 已停止，
未重启服务强行复询。见 `D:\work\runtime-logs\evidence-current-runtime-state.txt`。
所有删除均为直接删除，未使用回收站。
