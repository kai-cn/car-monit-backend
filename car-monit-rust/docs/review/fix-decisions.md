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
| 帧上限 | ① 全量输出 ② 截断 | ② 32 帧 | 对齐 logback 对公共尾帧的裁剪意图；Rust 异步栈远深于 Java | 深栈场景尾部被截断 |
| 字段名约定 | ① 只认 `error` ② `error`/`exception` 都当 throwable | ② | 两种命名在 Rust 侧都有历史用法，统一收敛 | `MessageVisitor` |

**第 4 项残余（已知）**：`Caused by:` 只有 message 没有 Java 那样的 `java.lang.XxxException:` 前缀；每个 cause 没有独立栈帧与 `... N more`；栈帧是 Rust 符号 `\tat fn (file:line)` 而非 Java 类方法。以上受 `std::error::Error` 类型擦除与单一 Backtrace 限制，无法对齐。

---

## 5. 404 / 405 / panic→500 的完成日志

（本节在第 5 项完成后补写）
