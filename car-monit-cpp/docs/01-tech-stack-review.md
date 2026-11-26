# car-monit-cpp 技术与选型审阅报告

> 生成日期：2026-11-07
> 审阅对象：仓库 `car-monit-cpp-local` 分支下 `car-monit-cpp/`（最新提交 `b4e8c47`，C++ 相关共 53 个提交，2026-11-02 首个代码提交，约 6 天完成 351 个文件）
> 审阅方式：**全程只读**（`git ls-tree / show / grep`），未切换工作区分支、未改动任何代码
> 重点阅读文件：`main.cpp`、`Server.cpp`、`Router.cpp/.hpp`、`JsonUtils.hpp`、`FastJson2Compat.hpp`、`JavaCollections.hpp`、`Db.cpp/.hpp`、`MySqlClient.cpp`、`CrudSpec.hpp`、`CrudEngine.cpp`（关键行）、`MySqlClient.cpp` 连接池段、`ExceptionMapper.cpp`、`Errors.cpp`、`Jwt.cpp/.hpp`、`TokenService.cpp`（关键行）、`RedisClient.hpp`、`Logger.hpp`、`OperLogAspect.cpp`（关键行）、`HttpClient.cpp`（关键行）、`Xlsx.cpp`（头部）、`CMakeLists.txt`
> 配套文档：`00-migration-backlog.md`（剩余工作清单）、分支内 `FINAL_DIFFERENCES.md` / `COMPATIBILITY.md`

---

## 一、整体架构图景

### 1.1 进程与线程模型

单进程、多线程、**全阻塞 I/O**（无 epoll/IOCP/协程）：

```
main
 ├─ AppConfig::load(config/*.yaml)          自研 YAML 子集解析
 ├─ Logger::init                            同步日志（mutex + 双写 + 大小滚动）
 ├─ Db::init(conn pool)                     手写 MySQL 文本协议客户端 + 连接池
 ├─ RedisCache::init                        手写 RESP 客户端（单连接 + mutex）
 ├─ TokenService::configure                 自研 HS512 JWT（复刻 jjwt 0.9.1 语义）
 ├─ registerControllers(router)             564 条路由（含 /health 扩展）
 ├─ Server(host, port, 32 workers, backlog) ← 1 accept 线程 + N worker 线程
 ├─ OperLogAspect::start                    单后台线程 + 有界队列（5 万，溢出丢弃）
 └─ 主循环 sleep 200ms，SIGINT/SIGTERM → server.stop() → 排空操作日志队列
```

**连接生命周期**：accept 线程把 `(fd, peer)` 塞进 `std::queue`（**无界**）→ 空闲 worker 取走 → 在同一条连接上循环读请求/写响应（HTTP/1.1 keep-alive），socket 收发超时 60s，头部上限 64KB、请求体上限 200MB（对齐 Java multipart 配置），支持 chunked **响应**读取（出站）但**请求**侧 chunked 直接断开（见 §2.1 风险 R-3）。

### 1.2 请求生命周期（dispatch 管线，复刻 Spring 过滤器链顺序）

```
readRequest（解析请求行/头/体，URL 百分号解码、尾斜杠规范化）
  → ① CORS 预检短路（OPTIONS+Origin 直接 200）
  → ② /logout（LogoutFilter 语义，先于 JWT）
  → ③ JWT 过滤器（格式非法 → 真实 HTTP 500，复刻"过滤器异常到不了 advice"）
  → ④ URL 层 antMatchers 顺序裁决（permitAll/anonymous/denyAll，先命中先生效）
  → ⑤ 路由匹配（AntPathMatcher 分段语义 + 特异度排序，{var} 抽取）
  → ⑥ @PreAuthorize（hasPermi/hasAnyPermi/hasRole，在参数绑定之前，复刻 Spring 顺序）
  → ⑦ handler（try/catch 包裹）
  → ⑧ OperLogAspect.record（成功/失败双路径，NPE → error_msg 为 NULL）
  → ⑨ ExceptionMapper（异常→响应映射）+ applyCors → writeResponse
```

### 1.3 模块分层与依赖方向

```
cm/common        ← 最底层：常量、异常、核心 domain(AjaxResult/R/TableDataInfo)、
                   工具(StringUtils/Convert/DateUtils/Json/FastJson2Compat/
                   JavaCollections/crypto/Inflate/Deflate/Xlsx/Logger)
cm/framework     ← 依赖 common：config(Yaml/AppConfig)、net(Fd/Os/HttpClient/S3Client)、
                   db(MySqlClient/Db/Row)、redis、security(Jwt/TokenService)、
                   web(Server/Router/FileUpload/Errors/ExceptionMapper/CrudEngine)、aspect(OperLog)
cm/system        ← 依赖 framework：system 模块的 domain/mapper/service
cm/web           ← 依赖 system+framework：controller（按 Java 包分目录）、specs（CRUD spec 数据）、util
cm/base, cm/flow ← 同上：TrailGeometry、FlowApprovalService
main.cpp         ← 组装：只依赖以上各层
```

依赖方向单向、无环，与 Java 包结构镜像——这是 1:1 迁移的核心可维护性设计：**Java 开发者按包名即可定位 C++ 对应文件**。

---

## 二、逐组件评审

评分说明：★★★ 优秀 / ★★ 合格 / ★ 有明显短板。每项按"设计意图 → 实现质量 → 正确性风险 → 性能与并发边界 → 可维护性 → 可测试性"展开。

### 2.1 自研 Server / Router（HTTP 层） ★★

**设计意图**：不引第三方框架，用约 550 行阻塞线程池复刻"Tomcat + Spring 过滤器链 + DispatcherServlet 路由"的**可观察行为**（状态码、响应形态、鉴权语义、URL 规则顺序），而非复刻其内部机制。

**实现质量**：
- 过滤器链顺序复刻得非常细：CORS 预检 → logout → JWT → URL 规则 → 路由 → 方法级权限 → handler → 日志切面 → 异常映射，每一步都有对应 Java 组件的注释锚点。
- Router 的 AntPathMatcher 分段语义（`**` 跨段、`*` 段内、`?` 单字符、`{var}` 整段）实现正确；特异度排序（字面量 10000 > 变量 100 > 通配 10）对本仓库的路由形态足够（如 `/system/user/list/dept` 字面量路由能正确压过 `/system/user/{userId}`）。
- `dispatch()` 是静态函数、可脱离 socket 单测——测试性设计意识好。
- 错误路径全部走 `dumpLenient`（非法 UTF-8 替换 U+FFFD 而非抛异常），是吃过真实进程崩溃亏之后的加固（FINAL_DIFFERENCES §5 有事故记录）。

**正确性风险**（2026-11-08 状态更新）：
- ~~**R-1（中）** 内部连接队列无界~~ → **已修**（`5cf8294`）：上限 `max(workers*2, 100)`，满则 close + 溢出计数。
- ~~**R-2（中）** slowloris 面~~ → **已修**（`5c5c7dc`）：每请求 `steady_clock` 整体 60s 截止，头部读完恢复 body 空闲超时。
- ~~**R-3（低）** chunked 文档/代码不一致~~ → **已修**（`05fe02c`）：支持 chunked（chunk-ext + trailer），上限 200MB，⚠️8 已同步。
- ~~**R-4（低）** reason phrase 表不完整~~ → **已修**（`a6ec459`）：100–505 全表，未知码返回空串。
- ~~**R-5（低）** 静态文件整读内存~~ → **已修**（`d619d49`）：`file_path` + Content-Length + 64KB 分块流式；Range/ETag 仍无。

**性能与并发边界**：
- 全阻塞 + 32 worker，纯 JSON CRUD（单条 SQL 亚毫秒）量级估算在数千 RPS；瓶颈依次是：①外部调用占用 worker（Java 侧 Forest 超时 60s，一条慢上游理论上能冻住整站——⚠️5 已记录，要求外调必须设短超时）；②Redis 全局互斥（§2.6）；③同步日志（§2.7）。
- 路由匹配每请求做一次 linear scan + stable_sort（564 条），微秒级，可忽略。
- **结论**：支撑当前内部管理系统流量（数百并发内）没问题；到万级 RPS 或高并发慢上游场景会崩，需要 nginx 前置或换框架。

**可维护性**：代码紧凑、注释密度高、每个怪异行为都有 Java 侧出处。但 HTTP 协议细节（keep-alive 边界、头解析健壮性）的长期维护由本团队自己扛。

**可测试性**：好（dispatch 可单测；URL 规则顺序有单测钉住）。

### 2.2 JSON 层：ordered_json + javaMapOrder + FastJson2Compat ★★★

**设计意图**：单一 `cm::Json = nlohmann::ordered_json` 承载三种 Java 序列化形态——Jackson POJO 声明序（插入序）、HashMap 桶序（`javaMapOrder` 复刻 Java 8 `(h ^ h>>>16) & (cap-1)` 迭代序）、fastjson2 POJO 字母序（`compactJson` 显式开关）；另有 `normalizeFastJson2` 把 Redis 里 fastjson2 的 `Set[...]`/`25367L`/`@type` 扩展语法降级成严格 JSON。

**实现质量**：这是全工程最"不可替代"的一层。HashMap 桶序复刻属于极冷门但**契约必需**的知识（`AjaxResult` 继承 HashMap，`msg,code,data` 的输出顺序就是桶序）；fastjson2 WriteClassName 互操作直接决定与 Java 混跑时缓存是否可用（C++ 写严格 JSON 会让 Java 反序列化成 JSONObject → ClassCastException）。`dumpLenient`（错误路径不因非法字节 terminate）与 `jstr/jlong/jbool` 宽松取值器都是实战加固。

**正确性风险**：
- **R-6（中，已知并钉住）** BigDecimal 经 double：`116.500 → 116.5`，且这串文本会落库（⚠️7）。nlohmann 整数走 int64 原样输出，**19 位雪花 ID 精度无损**；风险只在浮点金额/标度。缓解是"金额透传原始文本 + ⚠️ 断言"，属于长期约束而非已修复项。
- **R-7（低）** `ordered_json` 的对象是 vector 存储，单键查找 O(n)；VO 一般 ≤60 键无碍，但若有大 Map 循环取键会有 O(n²) 隐患。

**性能**：nlohmann 在主流 JSON 库中偏慢（相比 simdjson/yyjson 慢一个量级），但当前业务单响应几十 KB，完全不是瓶颈。

**可维护性/可测试性**：头文件注释把"为什么必须这样"讲透了；`testAjaxResultOrder`/`testR`/`testOperLogAspect` 单测钉住三种键序。评价：**保留，不动**。

### 2.3 MySqlClient（手写 MySQL 文本协议） + Db + Transaction ★★（协议实现）/ ★★★（事务门面）

**设计意图**：为"clone 即可构建"（Windows 上装 MySQL C 库是 Java 同学第一道坎，CMakeLists 原话），手写 MySQL wire protocol：Handshake v10、`mysql_native_password` 与 `caching_sha2_password`（fast auth + RSA full auth，RSA-OAEP 也是自实现）、COM_QUERY 文本协议、多结果集、lenenc 编解码、utf8mb4。

**实现质量**：协议覆盖面超出预期（auth switch、full-auth RSA 路径都有）。连接池有 **ping-on-borrow**（借出前 ping，失效即销毁重建，规避 MySQL `wait_timeout` 杀空闲连接的经典坑）、`release` 时回滚泄漏事务、maxWait 语义。`Db::lit()` 转义覆盖 `\0 \n \r \\ ' " \Z`，在 utf8mb4 连接下是安全的转义集。

**正确性风险**：
- **R-8（高，结构性）** 文本协议 = 无预处理语句，**注入防护完全依赖每处调用都走 `Db::lit()`**。抽查 CrudEngine 全部值拼接均经 lit，标识符全部来自代码内 spec（可信），当前无洞；但这个约束靠纪律维持，每新增一处手写 SQL 都是潜在注入点。Db.hpp 头部明确警告，MIGRATION_GUIDE 有安全章节——意识到位，机制不到位。
- **R-9（中）** 协议长尾：无 TLS 到库（密码认证路径依赖 challenge-response / RSA，可接受，但数据明文传输）、无 COM_STMT、无压缩协议、字符集固定 utf8mb4_general_ci。auth 边界（RSA 公钥请求失败、auth switch 环）仅真实库环境验证过一两种组合。
- **R-10（低）** 池无最小空闲补齐/最大空闲淘汰（仅初始化时建 `max(initial,minIdle)` 条），空闲连接全保留到 maxActive——内存影响小。

**Transaction 门面 ★★★**：RAII + `thread_local` 事务连接绑定 + `PROPAGATION_REQUIRED` 并入外层 + "不显式 commit 即回滚"，精确复刻了 Java 侧"return error 而非 throw ⇒ 事务照常提交"这类反直觉语义（契约 27）；`release` 时自动回滚泄漏事务是双保险。

**可维护性**：协议层是全工程最大的长期负债候选（见 §四）；门面与池设计干净，与底层可解耦。

**可测试性**：协议层只能靠真实 MySQL 集成验证；`verify_generated_sql`（59 实体真库）承担了这个角色。

### 2.4 CrudEngine / CrudSpec（spec 驱动 CRUD） ★★★

**设计意图**（CrudSpec.hpp 头部自述）：Java 侧 60+ 控制器是 RuoYi 生成器产出的同构 CRUD，逐条手写 C++ 会产出上万行重复且易抄错的代码——把"Mapper XML 里有什么"变成**数据**（Field/Spec），引擎统一翻译成 SQL+JSON，spec 由 `scripts/gen_crud_spec.py` 从 Java 源码/ XML 抽取。

**实现质量**：这是全工程的**皇冠**。它把 MyBatis 最难对齐的语义编码成了可验证的数据契约：
- `inVo`（SELECT 投影列）与 `condColumn`（WHERE 左值列）分离——对应"MyBatis 只填结果集里出现的列，但 Vo 没投影的属性照样能当条件左值"这种 Java 冷知识（契约 20/21）；
- `auditFillInsert/Update` 由生成器**读实体父类源码**得出（只有 BasePlusEntity 系有 fill），注释直接点明"少写了 updateTime 就是旧值"（契约 33）；
- `dflt`（字段初值照输出）、`selectTail`（派生列）、`fastJson2CachedArray`（WriteClassName 缓存互写）；
- `verify_generated_sql.py` 把 59 个实体的生成 SQL 打到真库跑，0 异常——生成物有机器验证闭环。

**正确性风险**：
- **R-11（中，已自我暴露）** 生成器表达不了个别 Java 怪形态（`car_info` 的无条件 `not exists` 子查询、`createInfo` 派生列是手工补丁），注释明确警告"不要盲目重新生成"。spec 的"生成 + 手改"双轨制是脆弱点：改 Java 侧 XML 后必须人工 diff。
- **R-12（低）** 查询参数 → SQL 的路径上，`bindQuery` 把 HTTP 参数绑定为 Json 再由引擎按 lit 拼接，链条集中可控；但 spec 之外的手写控制器 SQL（如 BigScreen）要逐一自查转义。

**性能**：生成 SQL 与 Java 手写 SQL 同构，分页 `SELECT COUNT(1) + LIMIT/OFFSET` 复刻 PageHelper（含 total==0 不发数据查询、reasonable 夹页）。无 N+1 问题（列表一次查询 + selectTail join）。

**可维护性/可测试性**：spec 数据化 + 生成器 + 审计脚本（`audit_spec_keys` 0 缺口 / `audit_projection` / `audit_cond_columns`）构成罕见的可验证迁移基建。**保留，不动**；Java 侧变更时的同步流程需写进开发手册。

### 2.5 最小 OOXML（Xlsx/Excel + Inflate/Deflate） ★★

**设计意图**：读写 xlsx 只需数据面（单元格值/类型/表头），自研最小 OOXML（inline string、自解 ZIP 局部——实际是自研 Inflate/Deflate + 手写 XML 实体反转义），换取零依赖。

**实现质量**：读取器覆盖了本项目导入模板所需路径（sharedStrings/inlineStr、日期格式），INFLATE 修过一个"距离基值表抄成长度表"的真 bug（有单测钉三种块类型）；写出器数据一致（`verify_template_export` 22 项），但**无样式/合并单元格/两级表头**（⚠️3，显式偏离）。

**正确性风险**：
- **R-13（中）** 模板导出版式与 Java 产物不一致（已记录为有意偏离，取决于业务是否接受，见 backlog D-03）。
- **R-14（低）** 手写 XML 解析无 DTD 支持（也就天然免疫 billion-laughs），但遇到非预期结构（样式表引用、富文本）会静默走默认值——导入面对"外来 xlsx"的健壮性未验证。

**性能**：纯 C++ 内存操作，比 POI 快得多；导出量级（当前导出接口都是分页内数据）无压力。

**可维护性**：Inflate/Deflate/ZIP/XML 四合一自制栈是中等负债（有一处真 bug 历史，但已被单测钉住）；若要版式保真，见 §三 Excel 对比与 §五建议。

### 2.6 鉴权与 Redis 会话（Jwt / TokenService / RedisClient / SecurityUtils） ★★

**设计意图**：与 Java **共用同一个 Redis 会话**：jjwt 0.9.1 的 Base64 宽松解码密钥 quirk（26 字符 → 19 字节）必须复刻，否则存量 token 全部失效；fastjson2 会话值用 normalize 降级后读取；20 分钟阈值刷新（`refreshToken`）与 Java `TokenService` 对齐。

**实现质量**：interop 细节全部命中（这是混跑方案的生死线）；anonymous 语义陷阱（带 token 反而容器级 403）、非法 JWT 真 500、URL 规则顺序都被单测/验证脚本钉住。

**正确性风险**：
- **R-15（文档级）** `Jwt.hpp` 注释写"18 字节"，`Jwt.cpp` 与 FINAL_DIFFERENCES 都是 19 字节——头文件注释陈旧，应修正（代码行为以 .cpp 为准，无功能影响）。
- **R-16（中）** `RedisClient` 是**单连接 + 全局 mutex**：32 个 worker 的每次 Redis 往返（每请求至少 token 读取 1 次，权限/缓存场景 2-5 次）全部串行。本地 Redis 单次 ~0.1-0.3ms，理论天花板约每秒数千次命令；请求 QPS × 命令数接近该值时全站延迟抬升。**这是 32-worker 之后第二明确的并发瓶颈**。无 pipeline、无连接池、无失败退避（ensureConnected 有重连）。
- **R-17（低，已知）** C++ 自写的非缓存键（登录会话等）是普通 JSON，Java 读不了（⚠️2，混跑注意事项，已记录）。

**可维护性/可测试性**：TokenService 逻辑简单清晰；Redis 客户端 RESP 解析独立可测（`command()` 原始命令口便于调试）。

### 2.7 日志与 @Log 切面（Logger / OperLogAspect） ★★

**设计意图**：Logger 对应 Logback 的"能用"子集（双写、50MB×10 滚动、级别过滤）；OperLogAspect 复刻 `@Log` 234 条规则（枚举 ordinal、URI 不含 query、内网 IP 判定、参数三分支、fastjson2 丢 null、按字符截断），异步落 `sys_oper_log`。

**实现质量**：234 条规则条目化且有 `verify_operlog` 18 项实机断言；异步队列有界 5 万、溢出丢弃并打本地错误（⚠️12，有意偏离保内存）。

**正确性风险**：
- **R-18（低）** 单 worker 逐条 INSERT（未见批量），高写入速率下队列堆积→丢日志；对比 Java 的无界 timer 队列（会 OOM），这是合理取舍。
- **R-19（中）** Logger 全局 mutex 同步写盘在请求路径上：高 QPS 下所有 worker 在日志锁上排队；且 50MB×10 对长期运行的排障偏小。无 MDC/traceId（⚠️9）。

### 2.8 错误码与异常映射（Errors / ExceptionMapper） ★★★

**设计意图**：复刻 Spring 的双 advice 行为与 Boot 默认错误 JSON，外加"错误路径绝不再抛"的加固。

**实现质量**：`unauthorized()` 精确复刻 RuoYi 的"HTTP 200 + body 401"（`ServletUtils.renderString` 写死 200 的行为）；`containerError` 复刻 Boot 的 `timestamp/status/error/path` 形态；ExceptionMapper 逐异常类型映射，**NPE → `{"msg":null,"code":500}`** 这种 Java 怪形态都照抄；全部响应体走 `dumpLenient`。测试性好（404/405/401/403/500 形态均有验证）。

**风险**：无。这一层是"为了 1:1 契约而必须自研"的正面典型。

### 2.9 出站 HttpClient（Forest 等价） ★

**设计意图**：支撑 Forest 接口（vehicleMonitor/恒达/roadPath/腾讯地图），复刻 `@Query(POJO)` 拍平规则（声明序、null 省略、BigDecimal 保标度、布尔小写、空串裸键名——契约 36）。

**实现质量**：连接/读超时、chunked 响应解码、`Transfer-Encoding` 优先级（RFC 7230 §3.3.3）都有；无连接池（每请求新建）。

**正确性风险**（2026-11-08 状态更新）：
- ~~**R-20（高）** 无 TLS~~ → **已修**（`2e86447`）：vendored mbedTLS 3.6.2 + cacert.pem，强制校验证书链与主机名，真实站点（腾讯）握手通过。
- ~~**R-21（中）** 无 Forest 重试~~ → **已修**（`c478d9d`）：retry-count=2、间隔封顶 1s、异常与非 2xx 都重试；非 GET 默认不重试是有意收紧（`retryNonIdempotent` 可开）。

### 2.10 配置（Yaml/AppConfig） ★★

手写 YAML 子集解析（扁平 key + 基本类型），覆盖 `application.yaml` 全部块 + `cm.*` 扩展段；`CM_SERVER_PORT`/`CM_WORKERS` 等环境变量覆盖。~~风险：非常规 YAML（锚点、多行字符串、嵌套列表）不支持，配置变复杂时会静默读缺省值~~ → **已修**（`67dd8f7`）：锚点/别名/块标量/多文档/Tab/重复键检测后经 `parse(text, warnings)` 上报，`AppConfig` 汇总 `LOG_WARN`，不再静默（**R-22**）。

---

## 三、与 C++ 主流技术栈对比

### 3.1 HTTP / Web 框架

| 维度 | 自研（现状） | Drogon | Paozhu | oat++ | Boost.Beast | Crow | Seastar | nginx 模块 |
|---|---|---|---|---|---|---|---|---|
| 并发模型 | 阻塞线程池×32，每连接独占 | epoll/kqueue Reactor + 线程池，异步 ORM | 同步+协程混合 | Reactor（own asio-like） | asio 异步（Proactor） | asio 线程池 | shared-nothing 异步，核级隔离 | 事件驱动（C） |
| TLS/HTTP2 | ✗ / ✗ | ✅ / ✅ | ✅ / ✅ | ✅ / ✅ | ✅ / ✅(beast http2 部分) | ✅ / ✗ | ✅ / ✅ | ✅ / ✅ |
| 生态成熟度 | —（自研，560 行） | 高（TechEmpower 头部，社区活跃） | 中（国内项目，全栈注解式） | 中（维护放缓） | 高（Boost，但偏底层） | 中（轻量易用） | 高（ScyllaDB 同源，陡峭） | 高（C，运维级） |
| 上手成本 | 低（团队已掌握） | 中（异步心智） | 中低（类 Spring 注解） | 中高 | 高（手写协议层） | 低 | 很高 | 很高（C + nginx 内核） |
| **迁移本项目代价** | — | **高**：过滤器链语义要重写为 Drogon 中间件/插件；564 路由迁移；阻塞式手写 SQL 与异步 ORM 模型冲突 | 中高：注解式路由映射直接，但 CRUD 引擎要适配 | 高 | 极高（等于重写 Server） | 中（同步 handler 兼容性好，但生态弱） | 极高 | 极高 |

**要点**：自研栈的核心资产不是"HTTP 服务器"本身，而是 **dispatch 管线里编码的 Spring 行为**（过滤器顺序、401/403 形态、antMatchers 顺序、@PreAuthorize 时机）。任何框架替代都要把这段语义重新落地一遍——这才是切换的真实成本，协议部分反而是小的。Drogon 是唯一值得认真考虑的替换项；**nginx 前置（TLS 终止 + 慢连接防护）是零代码改动的止血方案**。

### 3.2 JSON

| 维度 | nlohmann ordered_json（现状） | RapidJSON | simdjson | Boost.JSON | yyjson |
|---|---|---|---|---|---|
| 有序对象 | ✅（插入序） | ✅（文档序） | 只读 | ✅（插入序） | ✅ |
| 19 位整数精度 | ✅ int64 原样 | ✅（kParseFullPrecision） | ✅ | ✅ | ✅ |
| BigDecimal 保标度 | ✗（double） | ✗ | ✗ | ✗ | ✗ |
| fastjson2 扩展语法 | 需自研归一化（已有） | 需自研 | 需自研 | 需自研 | 需自研 |
| 性能 | 慢（1×基准） | 快（~5-10×） | 最快（只读，GB/s） | 快（~3-5×） | 很快（~5×） |
| 迁移代价 | — | 中（API 风格差异大，手写序列化点多） | 高（DOM 只读，需配合二级库） | 低中 | 中 |

**要点**：所有主流库都**不支持** BigDecimal 标度与 fastjson2 扩展——这两项无论选谁都得自研（现状已自研完）。nlohmann 的性能短板在当前量级不可感知。**无切换收益**；若未来出现大 JSON 热点，用 simdjson 做只读解析、nlohmann 做输出，是低风险混合路径。

### 3.3 数据库访问

| 维度 | 自研 MySqlClient（现状） | libmysqlclient / MariaDB Connector/C | SOCI | ODB | sqlpp11 | Drogon ORM | nanodbc(ODBC) |
|---|---|---|---|---|---|---|---|
| 协议/驱动 | 手写文本协议 | 官方驱动（二进制协议 + COM_STMT） | 基于底层 C 驱动 | 编译期 ORM | 编译期 DSL | 自带连接管理 | ODBC 桥 |
| 预处理语句 | ✗（手工转义防注入） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| TLS 到库 | ✗ | ✅ | 随底层 | 随底层 | 随底层 | ✅ | 随驱动 |
| 动态 SQL / MyBatis `<if>` 语义 | CrudEngine 已实现 | 需在应用层拼（同现状） | 应用层 | 编译期映射（不适合动态） | 编译期（不适合动态） | 应用层 | 应用层 |
| PageHelper 语义 | CrudEngine 已实现 | 应用层 | 应用层 | — | — | 应用层 | 应用层 |
| 依赖重量 | 零（自研 ~900 行） | 系统包（Windows 需装开发库） | 轻中 | 需编译器插件（重） | 头文件+生成器 | 中（拉入框架） | ODBC 驱动链 |
| 迁移代价 | — | **中低**：`MySqlConnection` 接口窄（connect/query/execute/begin/commit/rollback/ping），池与 Db 门面原样保留，只换协议层 | 中 | 不适用 | 不适用 | 高（绑框架） | 中 |

**要点**：MyBatis 动态 SQL/PageHelper 语义**无论如何都在应用层**（CrudEngine 已解决且不可替代）；可替换的只有"协议层"。libmysqlclient 带来 COM_STMT（结构性消除 R-8 注入面）、TLS、协议长尾健壮性，而 `MySqlConnection` 的窄接口让替换成本可控。**这是性价比最高的替换候选**。CMakeLists 的"零依赖"初衷可用"可选 find_package：找到 libmysqlclient 用之，否则回退自研"两全。

### 3.4 Excel / Word

| 维度 | 自研最小 OOXML（现状） | libxlsxwriter | OpenXLSX / QXlsx | LibreOffice headless 转换 | docx 生态 |
|---|---|---|---|---|---|
| 读取 | ✅（本项目模板路径） | ✗（只写） | ✅（含样式读取） | — | — |
| 写出（数据） | ✅ 已对拍 | ✅ | ✅ | — | — |
| **版式保真**（样式/合并/两级表头/模板填充） | ✗（⚠️3） | ✅（样式/合并强；无"打开现有模板再填充"） | QXlsx 可改现有文件保留大部分样式 | 可做格式转换，不适合逐格填充 | **无成熟 C++ 库**（docx4j=Java、python-docx、phpword；模板填充基本要自己拆 OOXML） |
| 依赖重量 | 零 | 轻（C，需 zlib） | 轻中（QXlsx 可独立） | 外部进程/容器 | — |
| 迁移代价 | — | 低（writer 接口窄：`exportExcel` 单点） | 低中 | 运维面变化 | `exportAbnormalPassage` 无论选谁都要自研填充逻辑 |

**要点**：**xlsx 版式保真的现实路径**是"拿 Java 的真模板文件 + QXlsx/OpenXLSX 原位填值"（样式随模板走），而不是用代码重建样式；`exportAbnormalPassage` 的 docx+图片填充没有现成 C++ 库，需自研（工作量与现有 Xlsx 层同量级）。Word 是整个 Excel/Word 面最不划算的部分，backlog D-03 建议先做业务裁剪决策。

### 3.5 其他组件

| 组件 | 现状（自研） | 主流替代 | 对比结论 |
|---|---|---|---|
| JWT | 自研 HS512，复刻 jjwt 0.9.1 Base64-密钥 quirk | jwt-cpp | **保留自研**：换库省下的只是 HMAC/Base64 胶水，而**必须自研的密钥派生 quirk 一样要留**；jwt-cpp 反而引入"标准实现"的诱惑（用标准解码就与 Java 不互通） |
| Redis | 自研 RESP 单连接 + mutex | hiredis / redis-plus-plus（连接池、pipeline） | **建议替换**：全局互斥是明确的并发瓶颈（R-16）；hiredis 轻且成熟，包一层池即可，接口可保持现有形状 |
| 日志 | 自研同步 Logger | spdlog（异步 sink、滚动、pattern、按需 MDC） | **建议替换**：R-19；保留 `LOG_*` 宏名做薄适配层，调用点零改动 |
| 配置 | 自研 YAML 子集 | yaml-cpp | 低优先级：当前配置形态简单够用；若配置复杂化（嵌套/列表）再换 |
| 测试 | 自研断言宏（11 文件/514 断言） | GoogleTest / Catch2 | 保留现状可用；若断言规模继续增长，Catch2 迁移成本低（宏相似） |
| 构建/依赖 | CMake + vendored（bcrypt/nlohmann） | vcpkg / Conan | **保留 vendored**："clone 即可构建、不依赖网络"是这个团队环境（Windows、离线友好）下的真实收益；引入包管理器反而破坏 CMakeLists 头部承诺。仅当引入 libmysqlclient/spdlog/hiredis 时用 `find_package + 可选回退` 折中 |
| 加密（SHA/HMAC/RSA） | 自研 + `verify_crypto_vs_openssl.sh` 对拍 | OpenSSL | **保留自研**：CMakeLists 的零依赖承诺核心；已有对 OpenSSL 的对拍脚本兜底。RSA-OAEP 仅用于 MySQL full-auth，面窄 |
| S3 客户端 | 自研 SigV4（fake S3 40 项对拍） | AWS SDK for C++ | **保留自研**：AWS SDK 依赖巨重（几百 MB、构建复杂），与零依赖哲学冲突；真实 MinIO 验证是欠账而非代码问题 |

---

## 四、"必须自研" vs "本可用成熟库"的判定

### 为了 1:1 契约而必须自研（换任何库都躲不掉，属合理取舍）

| 组件 | 为什么必须自己写 |
|---|---|
| `javaMapOrder`（HashMap 桶序） | 任何 C++ JSON 库都不复刻 Java 8 HashMap 迭代序；`AjaxResult` 键序是逐字节契约 |
| `FastJson2Compat`（normalize + WriteClassName 写出） | fastjson2 扩展语法与"按名排序+丢 null+Long 带 L"是阿里私货，无库支持，且直接决定 Redis 缓存互操作成败 |
| `AjaxResult/R/TableDataInfo` 信封 + `dumpLenient` | 响应形态即契约；错误路径不抛是 Java 侧没有而 C++ 必须补的健壮性 |
| CrudEngine/CrudSpec | MyBatis XML 动态 SQL / `<if>` OGNL / `@TableLogic` / PageHelper / MetaObjectHandler 语义无任何 C++ 库可映射；spec 化还换来机器验证闭环 |
| JWT 的 jjwt 密钥派生（Base64 宽松解码→19 字节） | 与存量 Java 令牌互通的生死线；jwt-cpp 用标准解码即不互通 |
| dispatch 管线（过滤器链顺序/anonymous 陷阱/权限在绑定前） | Spring 行为即契约，任何框架都要重写这段（区别只是写成谁的 middleware） |
| `Db::lit` 转义族 | 仅在文本协议前提下必要——换成 COM_STMT 后大部分消失（见 §五） |

### 本可以用成熟库但自己造了（切换收益为正）

| 组件 | 成熟替代 | 自研的真实动因 | 债务评级 |
|---|---|---|---|
| **MySqlClient 协议层** | libmysqlclient/MariaDB | "clone 即可构建"（Windows 免装开发库）——动因成立但可用可选依赖两全 | **高**：注入面靠纪律、协议长尾、无 TLS |
| **HTTP Server** | Drogon（或 nginx 前置） | 零依赖 + 行为可控——动因成立 | **高**：无界队列/slowloris/无 TLS，均为安全运维面 |
| **Redis 客户端** | hiredis + 小连接池 | 零依赖 | **中**：全局互斥是明确瓶颈 |
| **Logger** | spdlog | 零依赖 | **中**：同步锁在请求路径 |
| **Xlsx 写出器** | libxlsxwriter / QXlsx | 零依赖 | **中**：版式能力缺失是已知业务缺口 |
| Inflate/Deflate/ZIP、YAML 子集、S3 SigV4、crypto | zlib/OpenSSL/yaml-cpp/AWS SDK | 零依赖哲学 + 已有对拍兜底 | **低-中**：面窄、有测试钉住、真 bug 已修 |

**判断依据小结**：这个团队的自研不是"不会用库"，而是把"clone 即可构建"（CMakeLists 头注明言：Windows 上装 OpenSSL 开发包是 Java 同学第一道坎）当成显式产品需求。因此评价标准不应是"该不该自研"，而是"**该自研的边界划在哪**"。当前边界把"协议基础设施"（MySQL/HTTP/Redis）也圈进了自研——这三块恰恰是隐蔽 bug 单价最高、成熟库收益最大的地方；而契约层（JSON 键序、fastjson2、MyBatis 语义、jjwt quirk）的自研是被迫且正确的。

---

## 五、结论与分组件建议

### 5.1 建议矩阵

| 组件 | 建议 | 切换代价 | 收益 | 优先级 | 状态（2026-11-08） |
|---|---|---|---|---|---|
| JSON 层（nlohmann/桶序/fastjson2 兼容） | **保留** | — | — | — | 保留；补了空/非法输入防护（`7baba72`） |
| CrudEngine/Spec + 生成器/审计脚本 | **保留**（补"Java 变更→spec 同步"流程文档） | — | — | — | 流程已写入 `MIGRATION_GUIDE §5.7`（`9ad648b`） |
| ExceptionMapper/Errors/信封 | **保留** | — | — | — | 保留 |
| Transaction/Db 门面 + 连接池 | **保留**（接口不变） | — | — | — | 保留 |
| Jwt/TokenService | **保留**（修正 .hpp 的 18/19 字节注释） | — | — | P3 文档 | ✅ 注释已修（`fa5e1c9`）；`login_tokens` 已双向互读（`e17b056`） |
| MySqlClient 协议层 | **替换**为 libmysqlclient（COM_STMT + TLS），`MySqlConnection` 接口保持，池复用；CMake 可选依赖，找不到则回退自研 | 中低：协议实现隔离在单文件，门面/池/spec 全不动；回归靠 verify_generated_sql + e2e 全套 | 结构性消除注入纪律依赖、TLS 到库、auth/协议长尾由官方维护 | **P1** | ❌ 未开始（TD-05） |
| Redis 客户端 | **替换**为 hiredis + 连接池（3-8 连接），保持现有 API 形状 | 低：调用点全在 RedisCache 单类内 | 去掉全局互斥，Redis 吞吐 ×池大小；为 pipeline 留路 | **P1** | ❌ 未开始（TD-06） |
| Logger | **替换**为 spdlog，保留 LOG_* 宏薄适配 | 低：调用点宏名不变 | 异步写盘出请求路径、滚动/pattern 免费、为 traceId 铺路 | **P2** | 🟡 异步单后台线程已做（`4a0f2a8`），未换 spdlog（TD-07） |
| Xlsx 写出 | **视 D-03 决策**：要求版式保真→QXlsx/OpenXLSX 原位填模板（样式随模板走）；不要求→保留现状 | 低中：`exportExcel` 单点收口 | 关闭 ⚠️3 业务缺口 | P2（等决策） | 未变 |
| HTTP Server | **混合**：短期 nginx 前置（TLS/慢连接/限流/大文件，零代码改动）；中期若量级上来再评估 Drogon（届时真正成本是移植 dispatch 管线语义，不是换协议） | 低（nginx）/ 高（Drogon） | 立即关掉 R-1/R-2/R-5 三个运维风险面 | **P0（nginx）** | 🟡 队列/超时/流式/chunked 已自修（`5cf8294`/`5c5c7dc`/`d619d49`/`05fe02c`）；入站 TLS 与限流仍靠 nginx |
| Inflate/Deflate/crypto/Yaml/S3 | **保留** | — | 已有对拍兜底，动它们反而引入回归风险 | — | 保留；YAML 静默失败已修（`67dd8f7`） |
| 测试框架 | 保留，规模翻倍再迁 Catch2 | 低 | — | P3 | 保留 |

### 5.2 长期负债清单（自研且建议中期出手）

1. **MySqlClient 文本协议**（R-8 注入纪律依赖 + R-9 协议长尾）——最高优先替换。
2. **Server 内核**（R-1 无界队列 / R-2 slowloris / R-3 chunked 断开与文档不符 / R-5 整文件内存缓冲）——R-1/R-2/R-3/R-5 **已全部自修**（`5cf8294`/`5c5c7dc`/`05fe02c`/`d619d49`）；nginx 前置仍建议用于入站 TLS 与限流。
3. **Redis 单连接互斥**（R-16）——并发天花板，未动。
4. **BigDecimal-as-double**（R-6）——不是库问题而是契约问题；**已决策保留**（`MIGRATION_GUIDE §9-⑪`），金额链路若需保真另立十进制类型并靠 ⚠️ 断言守卫。
5. ~~HttpClient 无 TLS（R-20）~~ → **已补**（`2e86447` vendored mbedTLS），并复刻 Forest 重试（`c478d9d`）。

### 5.3 合理自研（不建议动）

JSON 三态键序层、CrudEngine/Spec、异常映射/信封、JWT 密钥 quirk、crypto/Inflate（有 OpenSSL 对拍）、S3 SigV4（有 fake S3 对拍）。这一层的共同特征是：**行为即契约，且已被自动化对拍钉住**。

### 5.4 无法从代码确认、需实测/问团队的推断（如实标注）

| 编号 | 推断 | 为什么无法确认 |
|---|---|---|
| U-1 | 吞吐量级"数千 RPS、内管够用" | 仓库无任何压测数据；worker 阻塞模型下上限取决于 SQL/Redis 延迟分布 |
| U-2 | 慢上游会占满 32 worker 导致整站排队 | 来自 ⚠️5 与代码结构推断，未实测外调 60s 超时下的雪崩形态 |
| U-3 | ~~HttpClient 未复刻 Forest 的 BackOffRetryer 重试语义~~ | ✅ 已由实现与单测关闭（`c478d9d`）：retry-count=2、间隔封顶 1s、异常与非 2xx 重试；非 GET 默认不重试 |
| U-4 | ~~Jwt 密钥 19 字节而非 18~~ | ✅ 已用 JDK 1.8 实测并修注释（`fa5e1c9`）；`make_token.py` 与 C++ 双向验证 |
| U-5 | Redis 单连接互斥是实际瓶颈 | 代码确认互斥存在；实际 QPS 下的排队量级未压测 |
| U-6 | ~~手写 YAML 解析对非常规语法静默取缺省~~ | ✅ 已修（`67dd8f7`）：不支持语法带行号告警，AppConfig 汇总 |
| U-7 | auth-switch/RSA full-auth 在全部服务端组合下可用 | 仅 native 一种组合验证过（2026-11-08 8.0.30 临时实例 27/27 仍为 native） |
| U-8 | 末次 3 提交后 e2e 全套未复跑（380 项断言的有效性停在 11-04 之前状态） | FINAL_DIFFERENCES 自述 MySQL/Redis 当时已下线；本轮仅复跑单测与 db_verify，e2e 仍未整套复跑 |

---

## 附：审阅覆盖清单

全文精读：main.cpp、Server.hpp/cpp、Router.hpp/cpp、JsonUtils.hpp、FastJson2Compat.hpp、JavaCollections.hpp、Db.hpp/cpp、CrudSpec.hpp、ExceptionMapper.cpp、Errors.cpp、Jwt.hpp/cpp（关键行）、RedisClient.hpp、Logger.hpp、CMakeLists.txt。
关键行扫描 + 局部精读：MySqlClient.cpp（协议头 + 连接池段）、CrudEngine.cpp（转义/分页）、TokenService.cpp（刷新）、OperLogAspect.cpp（队列）、HttpClient.cpp（能力边界）、Xlsx.cpp（头部）。
未逐行审阅（不影响结论，已在正文标注推断边界）：业务 specs（Base/Manager/System/FlowCrudSpecs）、各业务 controller、BigScreen/TrailGeometry/FlowApprovalService、S3Client、Yaml.cpp 全文、SecurityUtils.cpp。
