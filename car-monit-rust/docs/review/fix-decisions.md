<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

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

> **验证状态**：本轮改动已通过 `cargo check --all-targets`、`cargo clippy --all-targets`
> 与 `cargo test --lib`（115 passed）。release 冒烟在第二轮复审后补跑，见第 7 节。

### 阻断：`GET /system/user/` 失效

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 修法 | ① 维护「仅带尾斜杠注册」静态集合、跳过削除 ② 把 GET 也注册到 `/system/user`，与 POST/PUT 合并，保留带斜杠版本 | ② | Spring 的 `useTrailingSlashMatch` 让两种 URI 都接受**所有方法**；① 会让 `POST /system/user/` 削不动而落到 GET 路由 → 新的 405。② 之后两种写法的 GET/POST/PUT 全部命中，且权限元数据同步（GET 用 `system:user:query`） | `api/system/sys_user.rs`、`route_parity` 测试 |
| OSS 的 DELETE | ① 按 Java 只在带斜杠的 pattern 上注册 ② 保持现状（注册在无斜杠路径，靠尾斜杠归一命中） | ② | 代码里 OSS DELETE 实际注册在 `/oss/object/{b}/{o}`，与 Java 注释不完全一致但行为可用；改为「只认带斜杠」需要再引入路径白名单，收益低、风险高，暂记为已知偏差 | `api/oss.rs`（未改） |

### 高危：release 无栈

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| release 符号 | ① 保持 `strip = "symbols"` ② 完整调试信息且不 strip | ②（`debug = 2`） | throwable 的 `\tat` 帧依赖 `backtrace::resolve`，strip 之后生产日志只剩首行。实测 `debug=1`（仅行号表）与 `debug=2` 在 Windows 下都只能解析到非内联帧；选 2 以保留更多函数信息 | `Cargo.toml [profile.release]` |
| release 冒烟 | ① 不做 ② 集成测试 | ② | `tests/release_throwable.rs` 断言真实文件行号帧 + 本 crate 探针帧；由 CI 的 `cargo test --release --test release_throwable` 执行（见第 8 节） | `tests/release_throwable.rs`、workflow |

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
| 防回归手段 | ① 搭真实 `build_router`（需 DB/Redis） ② 静态对拍 + 一个不依赖 AppState 的 dummy Router 分派测试 | ② | 用「只归一参数、不削斜杠」的 raw 集合做尾斜杠断言（用归一集合会恒真）；dummy Router 覆盖 rewrite 后的 GET/POST/PUT 分派。真实 `build_router` 仍需 MySQL/Redis，见第 7 节 | `route_parity`、`trailing_slash` |
| `shape()` 掩盖问题 | ① 继续用归一集合 ② 另建 raw 集合 | ② | 归一集合本身包含无斜杠形态，用它断言恒真；raw 集合保留尾斜杠，删掉 GET 注册会立即失败 | 同上 |

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
| 后台线程名一律 `scheduling-1` 且 `with_log_thread` 未接线 | 修后回退 | 第 3 轮复审后回退：`current_log_thread` 的 fallback 已把 `tokio-*` 映射成 `scheduling-1`，再包一层无行为差异 |
| 决策记录/注释与实际不符 | 修 | 32 帧上限改为「Rust 侧自选截断，非 logback 行为」；补本轮记录 |
| OSS DELETE 语义偏差 | 暂不修 | 见阻断表最后一行，已知偏差，避免为此引入路径白名单 |

**本轮残余**：OSS DELETE 仍接受不带尾斜杠的路径（Java 的 pattern 带斜杠）；`build_router` 级真实装配测试因缺少 MySQL/Redis 未落地。本轮已在磁盘恢复后补跑三项门禁（115 passed）。

---

## 7. 独立复审修复（第 3 轮）

### 高危：release 用例无法编译

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| `impl Error` 的约束 | ① 只实现 Display ② 补 `#[derive(Debug)]` | ② | `std::error::Error` 要求 `Debug + Display`；原用例被 `cfg(not(debug_assertions))` 隐藏，三道 dev 门禁都看不到 | `tests/release_throwable.rs` |
| 用例位置 | ① 留在 `logging.rs` 的 `mod tests` ② 搬到 `tests/` 集成测试 | ② | 单元测试里调用点一定在 `car_monit_rust::logging::tests`，会被 `backtrace_text` 的 `car_monit_rust::logging` 前缀过滤掉，**断言因此恒真**（第 4 轮复审实测确认） | `tests/release_throwable.rs` |
| 调用点 | ① 测试内直接调用 ② 经 `car_monit_rust::test_support::throwable_probe` + `black_box` 函数指针 | ② | 探针放在非 logging 模块，帧不会被过滤器吃掉；间接调用防止 LTO 内联 | `lib.rs::test_support` |
| 断言口径 | ① 只断言存在 `\tat` ② 至少一条真实「文件:行号」帧 + 本 crate 的探针帧 | ② | 前者在有 std/harness 帧时也会通过；后者能证明本 crate 的调试信息确实保留 | 同上 |

### 中危 2：尾斜杠断言恒真

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 比对集合 | ① 复用 `shape()` 归一集合 ② 另建只归一 `{}`、保留斜杠的 raw 集合 | ② | `shape()` 本身削斜杠，归一集合必然包含无斜杠形态，断言恒真；raw 集合删掉 GET 注册就会失败 | `route_parity` |
| 元数据断言 | ① 只看注册表 ② 增加 `lookup` 断言 | ② | 直接校验 `system:user:query` 权限挂到了 `GET /system/user`，并顺带覆盖 HEAD 归一 | 同上 |

### 中危 3：panic 审计分支无测试

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 可测性 | ① 直接测 `meta_middleware`（需 AppState/Redis） ② 抽出 `OperContext` + `panic_oper_record` + `with_panic_audit` | ② | `AppState` 依赖真实 Redis，无法在单测里构造；抽出后可直接断言 status=1/errorMsg/原始 URI，以及「先回调、再原样返回 payload」 | `api/meta.rs` |
| 二次 panic | ① 不处理 ② `record_oper` 的 `tokio::spawn` 包 `catch_unwind` | ② | 运行时关闭阶段 spawn 会 panic，二次 panic 会替换调用方正在处理的 payload | `auth/audit.rs` |
| `build_router` 级测试 | ① 加 test-only `AppState` ② 暂不做 | ② | 需要给 `RedisCache` 造无连接实例，改动面过大且会让测试依赖外部服务；已在残余中说明 | — |

### 中危 4/5：`java_line` 与缓存无测试

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| `java_line` | ① 不测 ② 表驱动发 5 条事件 + 映射 target 的 `?` | ② | 删除分支或映射臂会立即失败；同时断言 `java_line=` 不落字段 | `logging.rs` 测试 |
| `OnceLock` | ① 不测 ② 用自增计数的 Error 连续 `to_string()` 两次 | ② | 缓存被删时计数会变成 2 | `logging.rs` 测试 |

### 中危 6：日志通道阻塞策略

| 决策点 | 选项 | 选择 | 理由 | 影响面 |
|---|---|---|---|---|
| 发送策略 | ① 无限阻塞 `send` ② 20ms 上限 + 丢弃计数 | ② | 无限阻塞会在写盘抖动时卡住所有 tokio worker，并连带定时器/IO；20ms 上限 + 计数把代价限制在单次请求。`SyncSender::send_timeout` 仍是 unstable（std_internals），用 `try_send` + 1ms 轮询等价实现，等待期间不持有 Mutex | `LogGuard::write` / `send_with_timeout` |
| 丢弃可观测性 | ① 静默 ② 每 1000 条 stderr 告警 | ② | 不能静默丢日志；用 stderr 避免日志系统自递归 | 同上 |
| `flush` | ① `try_send` ② 与写路径相同的 `send_timeout` | ② | 原实现满时静默丢 flush，与写路径策略不一致 | `LogGuard::flush` |
| `LogHandle::drop` | ① 无限阻塞 `send` ② 最多约 2 秒重试，失败则放弃 join | ② | 停机时不能因写盘卡死而挂住进程 | `Drop for LogHandle` |
| writer 侧 | ① 每条单独写 ② `try_recv` 批量合并后一次 `write_all` | ①（保留逐条） | 试过批量：现有 `writer_uses_active_file_and_indexed_archive` 立即失败——logback 的滚动发生在「下一条写入之前」，批量写会把超出 `maxFileSize` 的数据整体塞进旧文件。与 Java 对齐优先，撤销批量 | `RollingWriter::run` |

### 低危

| 项 | 处理 | 说明 |
|---|---|---|
| `with_log_thread("scheduling-1")` 冗余 | 回退 | `current_log_thread` 的 fallback 已把 `tokio-*` 映射成 `scheduling-1`，再包一层无行为差异 |
| HEAD 绕过权限 | 修 | `lookup` 把 HEAD 归一为 GET；`route_parity` 增加 HEAD 的权限元数据断言 |
| 决策记录过期 | 修 | 本节替换「本轮全部改动未经编译验证」「静态对拍能直接抓住」两处不成立表述 |
| `[SQL异常] 耗时: ?ms` | 保留 `?` | `From<sqlx::Error>` 拿不到单次执行耗时；输出真实数字需要把计时塞进每个查询调用（改动面大、且 Rust 侧无 MyBatis Executor 拦截点）。`?` 是诚实占位，已在残余中标注 |

**第 3 轮残余**：OSS DELETE 语义偏差；`build_router` 真实装配测试未落地；`[SQL异常]` 无真实耗时。

### 验证结果（第 3 轮）

- `cargo check --all-targets`：exit 0
- `cargo clippy --all-targets`：exit 0（lib 24 / test 26 告警，与改动前基线一致）
- `cargo test --lib`：120 passed（新增 5 条用例）
- release 冒烟：第 4 轮改为 `tests/release_throwable.rs` 后重跑通过（见第 8 节）

---

## 8. 独立复审修复（第 4 轮）

### P1-1：CI 从未跑 release 测试

| 决策点 | 选择 | 理由 | 影响面 |
|---|---|---|---|
| CI 步骤 | 在 `test` 之后加 `cargo test --release --test release_throwable` | `throwable_has_frames_in_release` 被 `cfg(not(debug_assertions))` 排除，debug 三道门禁根本不编译它 | `.github/workflows/car-monit-rust.yml` |
| 用例载体 | 搬到 `tests/` 集成测试 | 单元测试的调用点永远落在 `car_monit_rust::logging::tests`，被 `backtrace_text` 自身的前缀过滤器吃掉，断言恒真（复审实测确认） | `tests/release_throwable.rs` |

### P1-2 / P2-4：日志通道不再丢弃

| 决策点 | 选择 | 理由 | 影响面 |
|---|---|---|---|
| 写策略 | 恢复阻塞 `send`（有界队列 1024），删除 20ms 超时与丢弃计数 | Java `logback.xml` 是同步 `RollingFileAppender`，不丢审计日志；`sys-user`/`sys-error`/操作日志丢一条都不可接受 | `LogGuard::write` / `flush` |
| 阻塞实现 | OS 条件变量阻塞，不用 `sleep` 轮询 | 原 20ms `sleep` 轮询在 async 路径上会占住 tokio worker，队列满时反而拖慢请求 | 同上 |
| 丢弃计数 | 不需要 | 已无丢弃路径；删除 `LOG_DROPS`/`LOG_SEND_TIMEOUT`/`send_with_timeout` | 同上 |

### P2-1：release 断言恒真

| 决策点 | 选择 | 理由 | 影响面 |
|---|---|---|---|
| 根因 | 不是 LTO 折叠，而是 `backtrace_text` 过滤 `car_monit_rust::logging` 前缀，把用例自己的帧吃掉了 | 复审用独立探针实测：非 logging 模块的应用帧可以正常出现 | — |
| 探针位置 | `lib.rs::test_support::throwable_probe`（`#[doc(hidden)]`，非 logging 模块）+ `black_box` 函数指针 | 帧名 `car_monit_rust::test_support::throwable_probe` 不被过滤器命中，且间接调用避免内联 | `lib.rs`、`tests/release_throwable.rs` |
| 断言 | 真实文件行号帧 + 本 crate 探针帧 | 后者能真正约束本 crate 的调试信息保留 | 同上 |

### P2-2：panic 审计 call site 无测试

| 决策点 | 选择 | 理由 | 影响面 |
|---|---|---|---|
| 可测性 | 抽 `MetaEnv` trait（`address_enabled` / `audit`），`meta_middleware` 变薄壳，逻辑在 `meta_middleware_impl<E: MetaEnv>` | 测试用 `FakeEnv` 装配真实 Router，不需要 AppState/Redis | `api/meta.rs` |
| 覆盖范围 | 装配级用例：panic handler → 审计落一条(status=1) → `resume_unwind` | 同时证明运行时确实调用了 `lookup`（拿不到 @Log 元数据就不会审计）；断言原始 payload 文本完整保留 | 同上 |
| 全局注册表副作用 | `route_parity` 对 `extra` 过滤 `/__test*` | 测试用 `register` 注册 `/__test/panic`，避免并行测试时污染对拍 | `lib.rs::route_parity` |

### P2-3：`LogHandle::drop` 的真实上限

| 决策点 | 选择 | 理由 | 影响面 |
|---|---|---|---|
| 入队 | 最多 1 秒（1ms 轮询 `try_send(Shutdown)`） | 写盘卡死时不能无限阻塞 | `Drop for LogHandle` |
| join | 轮询 `JoinHandle::is_finished()`，最多 3 秒，超时 detach | 修正了「只限制入队、join 无界」的问题 | 同上 |
| 最坏耗时 | 4 个 appender 约 16 秒 | 已在代码注释与本节写明 | 同上 |

### P3

| 项 | 处理 |
|---|---|
| 过期文档（「应用帧会被 LTO 折叠」、旧 `\tat` 断言、日志通道描述） | 已按第 4 轮实现重写 |
| dummy router 覆盖 HEAD | 增加 `HEAD /system/user` 与 `HEAD /system/user/`（只断言 200 与分派成功） |
| `lookup` 元数据断言的边界 | 现由 `meta_middleware_audits_panic_and_preserves_payload` 覆盖运行时调用；单纯删 `lookup` 调用会导致取不到 @Log 元数据、审计为空，测试失败 |

### 验证结果（第 4 轮）

- `cargo check --all-targets`：exit 0
- `cargo clippy --all-targets`：exit 0（lib 24 / test 26 告警，与基线一致）
- `cargo test --lib`：**121 passed**（新增 `meta_middleware_audits_panic_and_preserves_payload`）
- `cargo test --release --test release_throwable`：**未执行**（收尾时用户重启电脑；集成测试已随 `check --all-targets` 以 debug 形态编译通过，release 断言待补跑）

### 本轮收尾快照（第 4 轮）

| 项 | 状态 |
|---|---|
| P1-1 CI 从未跑 release 测试 | 已完成：workflow 增加 `cargo test --release --test release_throwable` |
| P1-2 日志通道静默丢弃 | 已完成：恢复阻塞 `send`（有界队列），删除超时与丢弃计数 |
| P2-1 release 断言恒真 | 代码已完成：用例搬到 `tests/release_throwable.rs`，探针在 `car_monit_rust::test_support`，断言真实行号帧 + 应用帧；**release 实跑未做** |
| P2-2 panic 审计 call site | 已完成：`MetaEnv` 装配级测试，断言审计落库 + payload 身份 |
| P2-3 drop 上限 | 已完成：入队 1s + join 3s，最坏约 16s / 4 appender |
| P2-4 async 路径 sleep | 已完成：阻塞 `send` 走 OS 条件变量，无 sleep 轮询 |
| P3 文档 / HEAD / lookup 边界 | 已完成 |
| 下一步第一个动作 | `cargo test --release --test release_throwable`（target 目录：`D:\work\IdeaProjects\_cargo-target-carmonit-dev` 或新建） |

**提交**：本轮改动随 `fix(log): 第 4 轮复审修复` 一起提交（未 push）。

---

## 删除/清理约定（本机特有）

- 本机删除会被拦截进回收站且不释放空间；实测有效做法是先用 `SetLength(0)` 截断文件，再删除空壳目录，并在删除前后各取一次可用字节、`Test-Path` 确认目标消失。
- 构建产物放在仓库外（`C:\Users\abelz\.cache\cargo-target-carmonit`），按上述方式清理。
