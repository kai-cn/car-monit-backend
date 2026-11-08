# 日志形态对齐 Java logback —— 自主决策记录

本文件记录「把 Rust 迁移日志对齐 Java logback 运行时形态」过程中，所有需要拍板的取舍。
判定口径：**运行时落到日志文件里的形态**与 Java 一致或语义等价，而不是代码结构相似。
对应 Java 基线：`ruoyi-admin/src/main/resources/logback.xml`、
`ruoyi-system/.../common/core/monitor/SqlLogInterceptor.java`、
`ruoyi-system/.../common/core/filter/TraceIdFilter.java`、
`ruoyi-framework/.../config/SecurityConfig.java`、
`ruoyi-framework/.../web/exception/GlobalExceptionHandler.java`。

---

## 1. 慢 SQL（对齐 SqlLogInterceptor + logback 的 sys-slow appender）

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 慢 SQL 从哪里采 | ① 自建 SQL 执行包装层（每个 repository 手写耗时统计）② 用 sqlx 内建 `ConnectOptions` 日志 | ② | MyBatis 是全局 Executor 拦截器，等价物就是驱动层全局钩子；逐个包装 repository 必然漏采且侵入业务 | `state.rs` 建池处；仓库层零改动 |
| 普通 SQL / 慢 SQL 级别 | ① 全部 INFO ② Debug 普通、Warn 慢 | ② | Java 代码即 `log.debug("[SQL] ...")`、`log.warn(慢SQL框)`；MyBatis logger 级别 info 见 logback.xml | 输出到 sys-slow 的只有 WARN |
| `Mapper:` 字段 | ① 留空 ② 拼 Rust 函数路径 ③ 固定占位 | ③ `sqlx::query` | Rust 无 MyBatis `MappedStatement.getId()`；编造函数路径会与 Java 的 `com.ruoyi.*Mapper.xxx` 形态不符，固定占位最诚实 | 慢 SQL 框里 Mapper 一栏恒为 `sqlx::query` |
| SQL 文本 | ① 只打参数化 SQL ② 还原可执行 SQL | ② | 对齐 `getFullSql`：空白折叠、长度 2000 截断、TraceId 同框 | sqlx 只给参数化 SQL + 参数绑定，无法 100% 还原；已在慢框内保留 SQL 原文 |
| appender 路由 | ① 跟随 root ② 按 target 分流 | ② | logback 中 `SqlLogInterceptor`/`TraceIdFilter` 是 `additivity=false`，只挂 `file_slow`，不进 console/sys-info/sys-error | `logging.rs` 增加 `is_monitor_file_target` 等判定 |
| SQL 异常日志 | ① 追加 throwable ② 仅 message | ② | Java `SqlLogInterceptor` 的 `log.error("[SQL异常] {}, 耗时: {}ms, 异常: {}", ...)` 没把 Throwable 作为最后一个参数，logback 不会追加栈 | `error.rs` 保持 message 形态 |

## 2. 请求逻辑线程名（对齐 `%thread`）

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| Rust 无 Servlet 线程 | ① 透出 tokio worker 名 ② 构造请求逻辑线程名 | ② | tokio worker 名（`tokio-runtime-worker`）在日志里不可读且与 Java 形态完全不同；Java 的 `%thread` 语义是"处理该请求的线程" | 所有请求内日志的 `[%thread]` 段 |
| 命名形态 | ① `req-<n>` ② `http-nio-<port>-exec-<n>` | ② | 与 Tomcat 的 `http-nio-8080-exec-1` 完全同形，运维按线程名 grep 的习惯可直接复用 | 端口取 `server.port` |
| 编号分配 | ① 全局自增无上限 ② 每请求分配、按 Java 线程池规模复用 | ②（全局原子自增） | Tomcat `exec-n` 是线程池编号（复用）；异步模型下无法复用 OS 线程，用全局自增保证"同一请求内线程名稳定、不同请求可区分"。编号会持续增长，属可接受偏差 | 计数器为进程级 |
| 无请求上下文时 | ① 输出空 ② 回退 `scheduling-1` | ② | 对齐 Spring `@Scheduled` 默认单线程名 `scheduling-1`；启动/后台任务日志不能丢线程名 | 定时任务、启动日志 |
| 上下文传递 | ① 全局 thread_local ② task-local | ② | axum 处理链跨 await，thread_local 会在 await 点丢失 | `logging::with_request_context` |

## 3. logger 名（对齐 `%logger{36}`）

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 模块→Java 类名 | ① 调用处逐个写 `target:` ② 集中映射表 | ② | 501 条端点的控制器分散在多个模块，集中表便于审查与补漏；个别非一一对应处（Quartz 调度）再用显式 target | `logging.rs::JAVA_TARGETS`（17 条） |
| 无 Java 对应类的模块 | ① 强行编一个类名 ② 保留 Rust target | ② | 编造类名会让日志指向不存在的 Java 类，误导排障；保留 `car_monit_rust::*` 并在此记录 | 调度/分页诊断、启动日志 |
| `%logger{36}` 缩写 | ① 简单截断 ② 逐字符复刻 logback 1.2.3 算法 | ② | logback 规则：保留末段、必要时保留右侧、`::` 与 `.` 同规则，简单截断会产出 Java 里不存在的形态 | 所有 logger 名 |
| 行号 `%L` | ① Rust 真实行号 ② 映射到 Java 调用行 | ②（SQL 事件） | SQL 事件不是 Rust 代码发出的，用 Rust 行号无意义；映射到 `SqlLogInterceptor.java` 的 log 调用行 | 仅 SQL 事件 |

## 4. Throwable 追加（对齐 logback 默认 ThrowableProxyConverter）

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 形态 | ① 保留 `error=` 字段 ② 消息后独立区块 | ② | logback 在 pattern 无 `%ex` 时自动把 throwable 追加在 `%msg%n` 之后 | 所有 `error = ...` 日志点 |
| 顶层类型名 | ① 不输出类型 ② 输出 Rust 类型路径 | ②（`::`→`.`） | 对齐 `java.lang.XxxException: msg` 的"类型: 消息"行 | `logging::Throwable` |
| cause 链 | ① 不展开 ② 逐层 `Caused by:` | ② | 对齐 logback 的 cause 链；`dyn Error` 无法拿到具体类型名，只能输出 message（见残余） | 错误链日志 |
| 栈捕获时机 | ① 错误构造时 ② 记录日志时 | ② | Rust `Error` 不保存栈；只能在日志点捕获当前栈（等价于 Java 的抛出点近似） | `Backtrace` |
| Windows 符号化 | ① `Backtrace::new()` 全量符号化 ② `new_unresolved()` + 逐帧 `resolve` | ② | `new()` 在本机把测试进程挂死（曾拖垮工具链）；惰性解析单帧可用 | 帧输出上限 32 |
| 帧上限 | ① 全量输出 ② 截断 | ② 32 帧 | **这是 Rust 侧的自选截断，不是 logback 行为**（logback 只裁 cause 链公共尾帧，没有帧数上限）；异步栈远深于 Java，全量会淹没日志 | 深栈场景尾部被截断 |
| 字段名约定 | ① 只认 `error` ② `error`/`exception` 都当 throwable | ② | 两种命名在 Rust 侧都有历史用法，统一收敛 | `MessageVisitor` |

**第 4 项残余（已知）**：`Caused by:` 只有 message 没有 Java 那样的 `java.lang.XxxException:` 前缀；每个 cause 没有独立栈帧与 `... N more`；栈帧是 Rust 符号 `\tat fn (file:line)` 而非 Java 类方法。以上受 `std::error::Error` 类型擦除与单一 Backtrace 限制，无法对齐。

---

## 5. 404 / 405 / panic→500 的完成日志

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 404 怎么进日志链路 | ① 在 fallback 里直接写日志 ② 让 fallback 被中间件包住 | ② | 直接写会拿不到 traceId/线程名（这些在 web_filter 的 task-local 里）；让 fallback 在 `.layer()` 之前装配即可被包住 | `lib.rs::build_router` |
| 装配顺序 | ① 先 `.layer()` 再 `.fallback()` ② 先 `.fallback()` 再 `.layer()` | ② | axum 的 `.layer()` 只包住「调用时已存在」的路由；后设的 fallback 不带中间件（原来 404 就是因此漏日志） | 同上 |
| 未知路径是否经过鉴权 | ① 跳过鉴权直接 404 ② 走 SecurityConfig 的 anyRequest().authenticated() | ② | Java 的 Filter 在 DispatcherServlet 之外：无 token 的未知路径是 401，有 token 才是 404 | 未知路径的响应码 |
| 尾斜杠（useTrailingSlashMatch） | ① fallback 里削掉再二次路由 ② 路由前统一削 | ② | 二次路由会让中间件跑两遍：@Log 重复写、重复提交检测互相冲突、鉴权重复；路由前削则只跑一次 | `lib.rs::strip_trailing_slash`（`MapRequestLayer` 包住整个 router） |
| 原始 URI | ① 重写后就按新路径记 ② 保留原 URI | ② | Java 日志/错误页用的是 `getRequestURI()`；用 `OriginalPath` extension 带给 web_filter 和 404 页 | 日志里的 `Path`、404 JSON 的 `path` |
| panic 捕获位置 | ① tower-http `CatchPanicLayer` ② web_filter 内 `catch_unwind` | ② | CatchPanicLayer 的 handler 拿不到 request，写不了带 Path/TraceId 的日志，也保证不了完成日志 | `web_filter` |
| panic 栈来源 | ① catch 点抓栈 ② 全局 hook 在 panic 线程抓栈 | ② | unwind 之后原栈已展开，catch 点只剩中间件帧；hook 里抓才是抛出点 | `logging::install_panic_hook`（main 启动时安装） |
| panic 响应 | ① 200 + AjaxResult（GlobalExceptionHandler 形态） ② 500 + `/error` 错误页 | ② | panic 等价于逃出异常解析链的 Error；用户明确要求「panic 转 500」；与 404/403 共用同一套 BasicErrorController 输出 | HTTP 状态与响应体 |
| panic 的日志条数 | ① 只记 `[未捕获异常]`（Java TraceIdFilter 形态） ② 再加一条完成日志 | ② | 用户要求所有响应都有完成日志；`[服务器错误响应] Status=500` 由 web_filter 统一补 | sys-slow / sys-error 各一条 |
| web_filter 的 State | ① `AppState` ② 只要端口 `u16` | ② | 中间件实际只用到 `server.port`；收窄后可以在单测里装配真实中间件做端到端断言 | 中间件签名与装配处 |

**第 5 项残余（已知）**：Java 的 RuntimeException 走 `GlobalExceptionHandler`，HTTP 状态是 200 + `AjaxResult`；Rust panic 统一 500 + `/error` 错误页，属于有意偏离（按用户要求）。Java 只为异常记 `[未捕获异常]`（不记完成日志），Rust 多一条 `[服务器错误响应]`，同样是有意补充。

---

## 6. 独立复审修复（第 2 轮）

> **验证状态**：本轮改动**未执行** `cargo check/clippy/test`。本机 D 盘只剩 1.4 MB、
> C 盘 3.8 GB，`cargo clean` 释放的 2.9 GB 进入回收站后并未真正归还空间；按用户指示
> 停止一切编译与写盘动作，待磁盘缓解后补跑。`--release` 冒烟同理未执行。

### 阻断：`GET /system/user/` 失效

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 修法 | ① 维护「仅带尾斜杠注册」静态集合、跳过削除 ② 把 GET 也注册到 `/system/user`，与 POST/PUT 合并，保留带斜杠版本 | ② | Spring 的 `useTrailingSlashMatch` 让两种 URI 都接受**所有方法**；① 会让 `POST /system/user/` 削不动而落到 GET 路由 → 新的 405。② 之后两种写法的 GET/POST/PUT 全部命中，且权限元数据同步（GET 用 `system:user:query`） | `api/system/sys_user.rs`、`route_parity` 测试 |
| OSS 的 DELETE | ① 按 Java 只在带斜杠的 pattern 上注册 ② 保持现状（注册在无斜杠路径，靠尾斜杠归一命中） | ② | 代码里 OSS DELETE 实际注册在 `/oss/object/{b}/{o}`，与 Java 注释不完全一致但行为可用；改为「只认带斜杠」需要再引入路径白名单，收益低、风险高，暂记为已知偏差 | `api/oss.rs`（未改） |

### 高危：release 无栈

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| release 符号 | ① 保持 `strip = "symbols"` ② `debug = 1` 且不 strip | ② | throwable 的 `\tat` 帧依赖 `backtrace::resolve`，strip 之后生产日志只剩首行；体积换取可排障性 | `Cargo.toml [profile.release]` |
| release 冒烟 | ① 不做 ② 加 release-only 单测 | ② | `#[cfg(not(debug_assertions))]` 的 `throwable_has_frames_in_release` 断言 `\tat`；只在 `cargo test --release --lib` 下编译 | `logging.rs` 测试模块 |

### 中危 1：慢 SQL 短语句

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| SQL 文本回退顺序 | ① `db.statement` → message ② `db.statement` → summary → message | ② | SQLx 在 `summary == sql` 时 `db.statement` 为空，直接退到 message 会把告警文案当成 SQL 打出来 | `sql_event_details`，新增单测 `slow_sql_uses_summary_when_statement_is_empty` |

### 中危 2：`%L` 行号

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 映射到 Java 全类名的 target | ① 照旧输出 Rust 行号 ② 输出 `?` | ② | 类名是 Java 的、行号是 Rust 的，会指到不存在的 Java 行；logback 拿不到行号时也输出 `?` | `log_line` / `write_prefix` |
| TraceIdFilter 的行号 | ① 输出 Rust 行号 ② 各日志点显式声明 Java 行号 | ② | 各分支对应 `TraceIdFilter.java` 的 159/175/258/262/267，`%L` 才有意义 | 新增 `java_line` 字段（不落 `key=value`） |

### 中危 3：panic 跳过 @Log 审计

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 审计位置 | ① web_filter 统一补 ② `meta_middleware` 捕获后记录再抛回 | ② | `@Log` 元数据在 meta 中间件里，web_filter 拿不到 title/businessType/oper_param；在 meta 里 `catch_unwind` → `record_oper(status=1, error_msg=panic: ...)` → `resume_unwind`，web_filter 仍负责 500 与日志 | `api/meta.rs`；panic 与审计的顺序变成「先落库、再抛」 |

### 中危 4：测试没覆盖真实装配

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 防回归手段 | ① 搭真实 `build_router`（需 DB/Redis） ② 对基线做「尾斜杠必须有无斜杠同方法注册」的静态对拍 + 保留 web_filter 级端到端测试 | ② | `AppState` 需要可用的 MySQL/Redis，单测环境不具备；静态对拍能直接抓住这类阻断，web_filter 级测试覆盖 404/405/panic 的日志与状态码 | `route_parity::baseline_endpoints_are_registered` 新增断言 |
| `shape()` 掩盖问题 | ① 继续用形状归一 ② 在归一之外单独检查尾斜杠形态 | ② | 形状归一本身没错，错在只比对归一后的集合；新增 `slashed` 列表逐条要求无斜杠同方法注册 | 同上 |

### 中危 5：Throwable 重复符号化

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 多 layer 重复解析 | ① 保持每个 layer 各解析一次 ② 渲染结果缓存 | ② | console/sys-info/sys-error 会各调用一次 `Display`；用 `OnceLock<String>` 只符号化一次，仍在请求线程（与 Java 同步 appender 一致） | `Throwable::fmt` |

### 低危（本轮一并处理）

| 项 | 处理 | 说明 |
|---|---|---|
| `RUST_LOG=debug` 时普通 SQL 写入 sys-slow | 修 | `slow_only` 对 SQLx 事件只放行 WARN/ERROR（Java logger level=info 会丢弃 DEBUG） |
| 日志通道满静默丢弃 | 修 | `LogGuard::write` 改为阻塞 `send`，对齐 logback 同步 appender |
| `parse_elapsed_ms` 的 µs/ns 分支不可达 | 修 | 先判 `ms`/`µs`/`ns` 再判 `s`，并加单测 |
| `take_panic` 残留陈旧值 | 修 | 请求进入时 `clear_panic()`，panic 后 `take_panic()` 仍负责消费 |
| `[SQL异常]` 缺 sqlId 与耗时 | 修 | 输出 `[SQL异常] sqlx::query, 耗时: ?ms, 异常: ...`；耗时无法从 `From<sqlx::Error>` 取得，用 `?` 而不是编造数字 |
| 401/403 错误页与 `oper_url` 丢原始 URI | 修 | `OriginalPath` 同时供给 auth 的 401/403 文案与 `record_oper.oper_url` |
| 后台线程名一律 `scheduling-1` 且 `with_log_thread` 未接线 | 修 | `run_loop` 用 `with_log_thread("scheduling-1", kind.run(...))` 包住任务体 |
| 决策记录/注释与实际不符 | 修 | 32 帧上限改为「Rust 侧自选截断，非 logback 行为」；补本轮记录 |
| OSS DELETE 语义偏差 | 暂不修 | 见阻断表最后一行，已知偏差，避免为此引入路径白名单 |

**本轮残余**：OSS DELETE 仍接受不带尾斜杠的路径（Java 的 pattern 带斜杠）；`build_router` 级真实装配测试因缺少 MySQL/Redis 未落地；本轮全部改动未经编译验证。
