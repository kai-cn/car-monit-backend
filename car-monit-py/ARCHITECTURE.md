# 迁移后架构说明（P1-2 决策记录）

> 适用分支：`car-monit-py-V2`。本文只描述 **Python 侧当前实际部署形态**，
> 以及后续扩到多 worker 的前置条件；逐条 Java ↔ Python 差异仍在
> [COMPATIBILITY.md](COMPATIBILITY.md)。

## 1. 当前部署形态（单进程）

```text
                    ┌──────────────────────── uvicorn (1 process) ───────────────────────┐
HTTP :9989 ────────▶│ XssMiddleware -> TraceId -> CORS -> RequestContext -> Security    │
                    │      -> FastAPI Router -> sync endpoint -> anyio thread pool(200) │
                    │                                              │                    │
                    │                    @transactional Service (ContextVar Session)    │
                    │                                              │                    │
                    │                     Mapper (SQLAlchemy Core + 手写 SQL)            │
                    └───────────────┬──────────────────┬──────────────────┬─────────────┘
                                    │                  │                  │
                              MySQL/Druid 等价     Redis（共享 keyspace）  Quartz（进程内）
                              QueuePool(200)      RedisCache(JSON)       RAMJobStore + 1s 轮询
```

- **入口**：`uvicorn app.main:app --port 9989`；`run.py` 读 `server.port`。
- **并发模型**：全部端点声明为同步 `def`（保留 JDBC/ThreadLocal 语义），
  Starlette 把它们派发到 anyio 线程池；上限由 `app.request_thread_limit`（默认 200，
  与 Druid `max-active=200` 对齐）控制。异步链路只有中间件本身。
- **进程内线程池**：
  - `AsyncManager`：50 个 `schedule-pool` 线程，审计/登录日志异步写；
  - `ThreadPoolTaskExecutor`：200 个 `task-pool` 线程，几何补桩等后台任务；
  - 两者均为**有界队列**（`app.executor_queue_capacity=1000`），满了由调用线程执行
    （Java `CallerRunsPolicy`）。
- **外部 HTTP**：Forest 等价层使用**进程级** `httpx.Client`（连接池上限
  `forest.max_connections=1000`），lifespan 收尾时关闭。
- **调度**：自研内存 Quartz（`app/quartz/util/scheduler.py`），启动时把 `sys_job`
  重建进 RAMJobStore；`app.scheduler_enabled=false` 可整体关闭。
- **缓存**：业务缓存全部在 Redis（`SECTION_LIST`、`gantry_list`、`white_car_list`、
  `car_warning_rule:<userId>type<noticeType>`、登录 token、字典/参数等）；
  进程内只有模板缓存、pydantic 自动映射缓存这类**幂等工具缓存**，不承载业务状态。
- **事务**：`@transactional` 方法级边界 + `ContextVar` 复用同一个 Session，
  嵌套调用按 REQUIRED 语义加入外层事务；未标注的方法保持"每条 SQL 自提交"的
  Java 原行为。
- **退出顺序**：`lifespan finally` → 停 Quartz → 停两个线程池 → 关 `httpx.Client`
  → dispose engine → close Redis。P2-16（连接先于异步任务关闭）已由此关闭。

## 2. 为什么本轮保持单进程（P1-2 决策 A）

`uvicorn --workers N` 能利用多核，但会直接打破以下假设：

1. **Quartz 会重复执行**：每个 worker 都会在启动时 `scheduler.clear()` 并把
   `sys_job` 整表注册进自己的 RAMJobStore；同一个 cron 到点会在 N 个进程里各跑一次。
2. **日志文件竞争**：`sys-info.log` 等 4 个文件由每个进程各自的
   `RotatingFileHandler` 打开，Windows 上直接冲突，Linux 上滚动/截断会互相踩。
3. **进程级单例语义变化**：`spring_utils` 注册表、`settings` 缓存、模板缓存都是
   每进程一份 —— 本身无害，但会让"改一次配置/注册一个任务"的行为看起来不一致。
4. **限流/幂等**：重复提交拦截已走 Redis，无进程内状态；但任何未来引入的进程内
   计数器/锁都会在 N 份之间失真。

### 扩到多 worker 的前置条件（按顺序）

1. **调度外置**：把 `app/quartz` 拆成独立进程（或选主 + DB/Redis 锁），只允许一个
   实例执行 `sys_job`；Web 进程只保留 `PUT /monitor/job/run` 的"立即触发一次"。
2. **日志收敛**：改为 stdout/JSON，交给 systemd/journald、Docker 日志或 Loki；
   若必须落盘，每个 worker 写独立文件（`sys-info.<pid>.log`）并由外部轮转。
3. **共享状态审计**：确认所有 `@lru_cache` / 模块级可变单例只做"可重建的缓存"，
   业务状态一律走 Redis/DB。
4. **压测**：先单进程压到 CPU 饱和，再决定 worker 数；不要凭核数直接开。
5. **健康检查**：每个 worker 暴露同一 `/health`，由反向代理做就绪探测。

> 结论：当前单进程 + 200 请求线程 + 200 DB 连接的容量，先用真实流量验证；
> 未达到 CPU 瓶颈前不建议引入多 worker。多 worker 属于"架构级变更"，需单独立项。

## 3. 未实施的高风险优化（方案说明）

以下两项评审建议本轮**明确不实施**（决策：保持现状，直到前置条件满足）。
原因与可验证的验收门槛记录在此，避免下一轮重复讨论。

| 项 | 决策 | 满足以下条件才重新评估 |
|---|---|---|
| P2-10 行映射 `model_construct` / 直接 `ORJSONResponse` | 不实施 | 先有"列值类型自检"开关 + 10 个最大列表端点的响应字节对拍基线；压测证明校验开销占请求耗时 >15% |
| P2-11 合并 3 层 `BaseHTTPMiddleware` | 不实施 | 先有并发用例覆盖 traceId 不串号 / 401 后上下文清理 / 预检不鉴权；每层可独立灰度 |

### 3.1 P2-10：行映射 `model_construct` + 直接 `ORJSONResponse`

**目标**：30k+ 行的大列表少一次逐行 pydantic 校验、少一次 `jsonable_encoder` 遍历。

**为什么暂不做**：`map_row()` / `map_result_row()` 现在用 `entity_cls(**fields)`，
这一步同时承担了：

- 类型强制（`Decimal` / `date` / `datetime` / `Optional`）；
- `BaseEntity` 的日期字符串解析与 `JavaScript String` 强制转换；
- `JavaDecimal` / `JavaString` 的序列化语义。

直接换 `model_construct` 会**绕过全部校验器**，SQL 驱动返回的 `bytes` / `str`
可能被原样带进响应，字节级对拍无法保证；而响应直接返回 `ORJSONResponse`
还要把 `AjaxResult`（dict + 嵌套模型）手工转成 JSON 安全结构。

**可控的前置条件**：先为 `map_row` 增加"列值类型自检"开关（仅当所有列值已是
模型声明的类型时走 `model_construct`），并对 10 个最大列表端点做响应字节对拍；
通过后再推广。该工作应与 P2-2 的分表优化一起压测，单独做收益有限。

### 3.2 P2-11：合并 3 层 `BaseHTTPMiddleware`

**目标**：把 TraceId / RequestContext / Security 合成一个纯 ASGI 中间件，减少
task group 与请求上下文复制。

**为什么暂不做**：三个中间件依赖 `contextvars`（traceId、SecurityContext、
RequestContext）的自动传播；纯 ASGI 改写需要手工在 `scope` 生命周期内
`ContextVar.set/reset`，并保持"XSS 最外层 → CORS 在 Security 外 → 预检不鉴权"的
顺序。任何一处 `reset` 遗漏都会造成跨请求串号，属于高回归风险。

**可控的前置条件**：先补"并发请求 traceId 不串号 / 401 后上下文已清理 / 预检
不触发鉴权"的并发测试，再逐层替换；每层单独提交、单独压测。

## 4. 部署配置 checklist

| 配置 | 生产建议 |
|---|---|
| `IS_LOCALHOST` | 生产设为 `prod`（DB 口令不能再用 `root`） |
| `TOKEN__SECRET` / DB 口令 / `HENGDA__SECRET` | **必填**：缺失或仍是仓库内置值则拒绝启动（所有环境） |
| `APP__CORS__ALLOWED_ORIGINS` | 填前端域名（JSON 数组）；留空 = 拒绝跨域 |
| `APP__REQUEST_THREAD_LIMIT` | 默认 200；需复刻 Tomcat 800 时显式设置 |
| `APP__EXECUTOR_QUEUE_CAPACITY` | 默认 1000，按审计写入量调整 |
| `LOGGING__FILE_MAX_BYTES` / `FILE_BACKUP_COUNT` / `FILE_MAX_TOTAL_BYTES` | 默认 100MB / 30 / 2GB |
| `APP__SCHEDULER_ENABLED` | 无 MySQL 或外置调度时设 `false` |
| `/profile` 目录 | 由 `RUOYI__PROFILE` 指向；不存在也能启动，但头像会 404 |
| Alembic | 已有库执行一次 `alembic stamp 0001_baseline`，不做自动迁移 |

**必填密钥**：`TOKEN__SECRET`、`SPRING__DATASOURCE__DRUID__MASTER__PASSWORD`、
`HENGDA__SECRET` 必须显式提供；缺失或仍是仓库内置演示值时，应用在**任何环境**都
拒绝启动（本地开发复制 `.env.example` 为 `.env` 即有一份开发占位值）。启用 OSS 时
还需 `OSS__ACCESS_KEY` / `OSS__SECRET_KEY`。完整清单见 `.env.example` 顶部。
