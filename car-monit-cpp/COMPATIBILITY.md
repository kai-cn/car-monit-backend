# COMPATIBILITY —— 与 Java 版的行为差异与规避方式

> 基准：`car-monit-backend` 3.8.7（Spring Boot 2.5.15 / Java 8 / Maven）。
> C++ 目标：C++20 + CMake 3.16+，仅依赖系统 OpenSSL / zlib / pthread。
> 图例：✅ 完全一致　⚠️ 行为差异（有补偿）　❌ 未迁移（有替代方案）

---

## 0. 结论摘要

| 维度 | 状态 | 说明 |
|---|---|---|
| HTTP 方法 / 路径 / 查询参数 / 请求体 | ✅ | 逐条对齐 `@RequestMapping`，见 `ENDPOINTS_INVENTORY.md` |
| 响应字段名 / 字段顺序 / HTTP 状态码 | ✅ | `AjaxResult` 按 Java HashMap 桶序输出；`TableDataInfo` 固定 `total→rows→code→msg` |
| 鉴权头 / JWT 算法 / Redis key / 过期时间 | ✅ | `Authorization: Bearer`；HS512；`login_tokens:`；默认 120 分钟；20 分钟续期 |
| 密码哈希 | ✅ | BCrypt（libbcrypt，与 Spring `BCryptPasswordEncoder` 同算法、同 `$2a$10$` 格式） |
| 验证码 | ⚠️ | 校验码/交互一致，**图片格式由 JPEG 改为 PNG** |
| Redis value 序列化 | ⚠️ | Java 写 `@type` 标记，C++ 写纯 JSON；C++ 可读 Java，Java 不可读 C++ |
| 分页 | ✅ | PageHelper 语义（count=0 跳过查询、reasonable、pageNum≤0） |
| 文件上传/下载 | ✅ | 同一个 `/profile/**` 目录、同一 URL 形态、同名清理规则 |
| Excel 导入导出 | ⚠️ | 自研最小 XLSX 写入（单 sheet），不支持样式/公式/多 sheet |
| Kafka / Elasticsearch / ShardingSphere / Quartz / OSS | ❌ | 见 §5，均有明确替代或降级方案 |
| 内存 / 线程模型 | ⚠️ | 固定 worker 线程池，非虚拟线程；无 GC |

---

## 1. 已实测的 Java 运行时基线（C++ 已对齐）

以下为对原 Java 服务实测得到的响应（`car-monit-rust/docs/01-baseline/05-runtime-probes.md`），
C++ 侧 `Server::dispatch` / `Errors` / `ExceptionMapper` 按同一规则实现：

| # | 请求 | HTTP | Content-Type | 响应体 |
|---:|---|---:|---|---|
| 1 | `GET /getInfo`（无 token） | 200 | `application/json;charset=utf-8` | `{"msg":"请求访问：/getInfo，认证失败，无法访问系统资源","code":401}` |
| 2 | `GET /nonexistent-xyz`（无 token） | 200 | `application/json;charset=utf-8` | 同上（Security 先于 404） |
| 3 | `GET /login`（只允许 POST） | 200 | `application/json` | `{"msg":"Request method 'GET' not supported","code":500}` |
| 4 | `POST /login` body `{bad` | 200 | `application/json;charset=UTF-8` | `{"msg":"JSON parse error: ...","code":500}` |
| 5 | `POST /system/user`（无权限） | 200 | `application/json;charset=UTF-8` | `{"msg":"没有权限，请联系管理员授权","code":403}` |
| 6 | `POST /system/user` body `{}` | 200 | `application/json;charset=UTF-8` | `{"msg":null,"code":500}`（NPE） |
| 7 | `POST /system/config` body `{}` | 200 | `application/json;charset=UTF-8` | `{"msg":"参数键名长度不能为空","code":500}` |
| 8 | `GET /system/user/abc` | 200 | `application/json` | `{"msg":"请求参数类型不匹配，参数[userId]要求类型为：'java.lang.Long'，但输入值为：'abc'","code":500}` |
| 9 | `GET /system/user/list?orderByColumn=bad;drop` | 200 | `application/json` | `{"msg":"参数不符合规范，不能进行查询","code":500}` |
| 10 | `POST /login` 错误密码 | 200 | `application/json;charset=UTF-8` | `{"msg":"用户不存在/密码错误","code":500}` |
| 11 | `GET /nonexistent-xyz`（有效 token） | **404** | `application/json` | `{"timestamp":"...","status":404,"error":"Not Found","path":"/nonexistent-xyz"}` |
| 12 | `POST /login` 成功 | 200 | `application/json;charset=UTF-8` | `{"msg":"操作成功","code":200,"token":"..."}` |

C++ 对应实现位置：

* 1/2 → `Errors::unauthorized()`（注意大小写：`charset=utf-8` 小写）
* 3/4/6/7/8/9/10 → `ExceptionMapper`（`application/json` 或 `...;charset=UTF-8` 视异常来源而定）
* 5 → `ExceptionMapper::map(AccessDeniedException)`
* 11 → `Errors::containerError(404, path)`（真实 HTTP 404，ISO+08:00 时间戳）
* 12 → `SysLoginController` + `AjaxResult` 桶序（`msg → code → token`）

> ⚠️ **Content-Type 大小写是真实差异**，Java 在 `AuthenticationEntryPointImpl` 中写死
> `application/json;charset=utf-8`（小写），而 Controller 返回值由 Spring 输出
> `application/json;charset=UTF-8`（大写）。C++ 已分别复刻，勿统一。

---

## 2. 逐项行为差异（⚠️）

### ⚠️ 2.1 验证码图片格式：JPEG → PNG

* Java：Kaptcha 用 `ImageIO.write(image, "jpg", os)`，前端拿到 `data:image/jpg;base64,...`。
* C++：无图像库，自绘 160×60 RGB 位图并用 zlib 编码为 **PNG**。
* 补偿：`/captchaImage` 返回字段 `uuid`、`img` 不变；`img` 仍是 base64 字符串，前端
  `<img :src="'data:image/gif;base64,'+img">` 依赖浏览器嗅探，可直接显示。若前端写死了
  MIME，请在网关层改写或增加 `imgType` 字段（见 `QUICK_REFERENCE.md`）。
* 字符集/算术题文本、校验码取值、Redis key `captcha_codes:{uuid}`、2 分钟 TTL 全部一致。

### ⚠️ 2.2 Redis value 序列化格式

* Java：`FastJson2JsonRedisSerializer` 使用 `JSONWriter.Feature.WriteClassName`，
  value 形如 `{"@type":"com.ruoyi.common.core.domain.model.LoginUser",...}`。
* C++：写入纯 JSON（无 `@type`）。
* 影响：**同一 Redis 实例中，C++ 写入的 `login_tokens:*` 无法被 Java 读取**；反向可读
  （C++ 解析时忽略未知字段）。
* 规避：迁移切换时使用独立 Redis DB（`spring.redis.database` / `CM_REDIS_DB`）或在切换期
  让流量只走一个实现。C++ 内部自洽，不影响单机功能。

### ⚠️ 2.3 Excel 导入导出

* Java：Apache POI 全功能（多 sheet、样式、公式、下拉校验、图片、`@Excel` 注解驱动列序）。
* C++：`cm::common::utils::Excel` 自研最小 OOXML（zip + SpreadsheetML）：单 sheet、
  inline string / 数字单元格、列宽、表头。**导出已经是真 .xlsx**（此前是"CSV 字节改名 .xlsx"），
  用 `python zipfile` 独立校验过 CRC 与部件表。
* 文件名与返回形态与 Java 一致：`ExcelUtil.encodingFilename` = `UUID.randomUUID() + "_" + sheetName + ".xlsx"`，
  响应 `{"msg":"<uuid>_操作日志.xlsx","code":200}` —— String 命中 `AjaxResult.success` 的 **msg 重载**，
  所以**没有 `data` 键**；文件写到 `profile/download/`，前端再走
  `GET /common/download?fileName=..&delete=true`（该 URL 是 `anonymous()`，见 §4）。
* 列的取舍照抄 `@Excel(type=...)`：`ALL` 两边都出，`IMPORT` 只进模板，`EXPORT` 只进导出；
  列序 = 字段声明序（本项目 `@Excel.sort` 全是默认值）；列宽取 `@Excel.width()`（`default 16`）。
* 单元格类型照抄：只有 `cellType=NUMERIC` 才是数字单元格，其余（含 `Long`/`BigDecimal`）
  Java 走 `ColumnType.STRING` 分支写成文本；`dateFormat` 先格式化再写文本；字段为 `null` 留空格。
* `readConverterExp` 的解析规则也照抄：先按 `,` 分段，段内按第一个 `=` 拆分，值取到第二个 `=`
  之前，不命中返回原值。因此 `userType` 的 `"1=机构用户2专家3供应商"` 只在值为 `1` 时整串替换。
* ❌ **导入仍未实现**：`POST /system/user/importData` 等显式返回错误，不伪装成功。
  缺的是 xlsx 读取（sharedStrings / inlineStr → 表头反查 `@Excel(name)`）加 `importUser` 的逐行校验。
* ❌ 未复刻：单元格样式、合并标题行、下拉校验（POI `createCombobox` 会多写一个隐藏 sheet），
  只影响观感，不影响数据与接口响应。

### ⚠️ 2.4 定时任务（Quartz）

* Java：`ruoyi-quartz` 使用 Quartz JDBC JobStore，`sys_job` 表驱动，支持 cron、暂停/恢复、
  立即执行、并发策略。
* C++：❌ 未内置调度器。补偿：
  * 保留 `/monitor/job/**` 的 CRUD（读写 `sys_job` 表）以便前端管理；
  * 任务触发交由外部调度（cron / systemd timer / K8s CronJob）调用 HTTP 端点；
  * 或由 Java 侧继续承担调度，C++ 只提供业务接口。

### ⚠️ 2.5 线程与内存模型

* Java：Tomcat `maxThreads=800`、平台线程、GC 自动回收。
* C++：固定工作线程池（默认 32，`CM_WORKERS` 可调），连接在 `std::shared_ptr` 管理下释放。
* 影响：长耗时请求会占满 worker；没有 GC，循环引用会泄漏（代码全部使用 `unique_ptr` /
  值语义，未引入 `shared_ptr` 环）。
* 调优：`CM_WORKERS` 建议 ≥ CPU 核数 × 4；慢 SQL 会直接降低并发。

### ⚠️ 2.6 时间与时区

* Java：JVM 默认时区（部署机为 Asia/Shanghai）；`@JsonFormat` 使用 JVM 时区。
* C++：所有日期格式化固定 `+08:00`（`DateUtils::formatJsonDate/formatIsoDate`），
  数据库时间按 `+08:00` 的 wall clock 解释（`parseDbDateTime`）。
* 影响：部署到其他时区的机器上，Java 会跟随系统时区而 C++ 不会。若需一致，请保持
  `TZ=Asia/Shanghai`（docker-compose 已设置）。

### ⚠️ 2.7 JSON 数字精度

* Java：`Long` 最大 2^63-1；`BigDecimal` 精确保留小数位。
* C++：整数用 `long long`；浮点用 `double` 并按最短表示输出。金额/费率字段若依赖
  `BigDecimal` 的精确小数位（如 `0.10` 输出为 `0.10`），C++ 会输出 `0.1`。
* 补偿：金额类字段在 SQL 中保持 `DECIMAL` 并仅做透传；若前端按字符串比较，请在
  `Db::Row` 读取时保留原始文本（`Row::str()`）而不是转 `double`。

### ⚠️ 2.8 请求体大小与分块传输

* Java：`max-request-size=200MB`，支持 `Transfer-Encoding: chunked`。
* C++：200MB 上限一致；**不支持 chunked 请求体**（返回 411 Length Required），需
  `Content-Length`。补偿：Nginx/网关层缓冲后转发。

### ⚠️ 2.9 静态资源与前端

* Java：`ResourcesConfig` 把 `classpath:/static` 与 `/profile/**` 映射出来。
* C++：`config/static` + `ruoyi.profile` 目录，路径穿越已防护（拒绝含 `..` 的解析结果）。
* 影响：前端产物需拷贝到 `config/static`；Java 的 `index.html` 欢迎页不迁移。

### ⚠️ 2.10 日志

* Java：Logback，`logback.xml` 中 `sys-user`、`sys-oper` 独立 logger，异步队列。
* C++：`cm::log::Logger`，按大小滚动（50MB × 10），同步写；`sys-user` 以 logger 名区分。
* 影响：日志格式为 `yyyy-MM-dd HH:mm:ss.SSS [LEVEL] logger - msg`，与 Logback pattern 接近
  但非逐字节一致；无 MDC/traceId 自动注入（monitor 的 traceId 需显式传递）。

### ⚠️ 2.11 Windows 下的文件路径编码（仅影响本地开发机，Linux/Docker 无此问题）

* 现象：`MinGW` 的 `std::filesystem` / `std::ofstream` 把窄字符串按**本地 ANSI 码页（GBK）**解释，
  而项目里所有路径片段（`profile` 目录、上传文件名、导出文件名）都是 UTF-8。
  结果是任何含中文的路径都"文件不存在"，而这套系统的导出名/头像目录名恰好全是中文
  （`<uuid>_操作日志.xlsx`）。写进去的是 GBK 码页下的乱码名，读的时候按 UTF-8 字节再转一遍，
  两边对不上。Java/JDK 不受影响（NIO 内部是 UTF-16）。
* 处理：`cm/common/compat/Path.hpp` 提供 `fsPath`（CP_UTF8 → UTF-16）与 `fsUtf8`（反向），
  所有落盘点（`Excel::writeDownloadFile`、`FileUpload::upload`、`CommonController` 两个下载、
  `Server` 的 `/profile/**` 静态服务）统一走这一层；路径穿越校验也改成比较 `fsUtf8` 结果，
  不再用 `path::string()`（它会按 ANSI 码页回转，中文直接毁掉）。
* 回归：`tests/main_test.cpp::testUtf8PathCompat` 校验往返，
  `scripts/verify_cn_export.py` 校验中文导出→下载的整条链路。

---

## 3. 序列化契约细节（✅ 已复刻）

| 契约 | Java | C++ |
|---|---|---|
| `AjaxResult` 字段顺序 | HashMap 桶序（16 容量，0.75 负载） | `JavaCollections::javaMapOrder` |
| `AjaxResult.success()` | `{"msg":"操作成功","code":200}` | 同 |
| `AjaxResult.error(msg)` | `{"msg":...,"code":500}` | 同 |
| `TableDataInfo` | `total, rows, code, msg` | 同 |
| `R` | `code, msg, data`（data=null 也输出） | 同 |
| `LoginUser` 缓存 | 含 `permissions`、`user`、`token`、`expireTime` | 同 |
| `Date`（无注解） | ISO-8601 带 `+08:00`（Spring Boot 关了 `WRITE_DATES_AS_TIMESTAMPS`，见 §4.6） | `formatIsoDate` |
| `@JsonFormat` | `yyyy-MM-dd HH:mm:ss` | `formatJsonDate` |
| `null` 字段 | Jackson 默认输出 `null` | `putStr/putI64` 输出 `null` |
| `@JsonInclude(NON_EMPTY)` VO | 空串/null/空集合不输出 | `RouterVo` 等按此实现 |
| `password` | `@JsonIgnore` 不输出 | `SysUser::toJson` 不输出 |

---

## 4. Java 侧“看起来一样、实际不一样”的陷阱（✅ 已按实测实现）

1. **`AuthenticationEntryPointImpl` 的 Content-Type 是小写 `utf-8`**，不是大写。
2. **`/logout` 在 JWT 过滤器之前**，无需有效 token，且始终返回 200 + `退出成功`。
3. **非法 JWT 会返回真实 HTTP 500**（过滤器异常无法被 `@ControllerAdvice` 捕获）。
4. **`anonymous()` 不是"允许匿名"，而是 `access("isAnonymous()")`——"只有没登录才放行"**。
   带合法 token 访问 `/common/download**`、`/system/notice/view/**`、`/system/file/view/**`
   会被 `AccessDeniedHandler` 判**真实 HTTP 403**，响应体是容器 `/error` 的
   `{"timestamp":..,"status":403,"error":"Forbidden","path":..}`，不是 `AjaxResult`。
   前端用 `<a href>` / `window.open` 下载，浏览器不会带 `Authorization` 头，所以能正常拿到文件。
5. **URL 层规则优先于控制器**，而且是 `antMatchers` 的**注册顺序**决定命中：
   * `/common/download**` 不会吞掉 `/common/download/resource`（AntPathMatcher 逐段匹配，
     段内通配 `download**` 不跨 `/`），所以后者仍走 `.authenticated()`；
   * 但 `/**/*.html`（静态资源 permitAll）注册在 `/druid/**` denyAll **之前**，
     于是 `GET /druid/index.html` 实际是 permitAll，而 `GET /druid/datasource.json` 才是 403；
   * `@Anonymous` 注解在本项目里**一个都没用**（`PermitAllUrlProperties` 收集到空集合），
     所以别把 `permitAll` 当成注解白名单的等价物。
6. **无 `@JsonFormat` 的 `java.util.Date` 输出 ISO-8601 带偏移文本**（`2024-05-17T14:15:52.000+08:00`），
   不是 epoch 毫秒。用真实依赖跑过：jackson-databind 2.11.4 + spring-web 5.3.6 +
   spring-boot-autoconfigure 2.4.5，按 Spring Boot 的 `StandardJackson2ObjectMapperBuilderCustomizer`
   再加 RuoYi 的 `timeZone(...)` 定制 → `WRITE_DATES_AS_TIMESTAMPS=false` → ISO 文本；
   而**裸** `new Jackson2ObjectMapperBuilder().build()` 会给 `1715926552000`。
   也就是说：这个形状是 Spring Boot 的默认值给的，别照 Jackson 自身默认值改。
7. **未匹配路由且无 token → 401**（Security 先于 DispatcherServlet 的 404）。
8. **`CustomException` / `UserException` / `BaseException` 不是 `ServiceException`**，
   一律被 `RuntimeException` 兜底为 code 500。
9. **`SysUser` 的校验注解被注释掉**，`POST /system/user {}` 是 NPE（`msg:null`），
   不要"顺手补校验"。
10. **PageHelper 在 count=0 时不执行数据查询**；`pageNum<=0` 时 offset=0；`reasonable=true`
    会把页码夹到有效范围。
11. **`AjaxResult` 是 HashMap**，`put` 顺序不等于输出顺序。
12. **`jjwt` 的 secret 先做 Base64 解码**，默认 26 字符 → **19 字节**（末尾不完整组补零），见 §6.1。
13. **MyBatis 的 `<association>` 只填结果集里存在的列**：`selectUserList` 没 join
    `parent_id/order_num/dept_status`，所以 `dept` 对象里这几项是 `null`，而 `deptId`
    取的是 `u.dept_id`；扁平的 `SysUser.deptName` 属性 resultMap 里根本没映射，恒为 `null`。

---

## 5. 未迁移组件（❌）与替代方案

| Java 组件 | 用途 | C++ 状态 | 替代 / 补偿 |
|---|---|---|---|
| Apache Kafka（`spring-kafka`） | 快照流水消费、Debezium CDC | ❌ | 保留 HTTP 查询接口；消费侧由独立服务（Java/Python）承担，C++ 只读库 |
| Elasticsearch（`RestHighLevelClient`） | 轨迹/流水检索 | ❌ | 用 MySQL 分区表 + 索引查询替代；接口路径与响应结构不变（若实现） |
| ShardingSphere（月表/日表路由） | 快照流水按月分表 | ❌ | SQL 中的月表后缀由 `AppConfig.shardingTablePrefix` 拼接；跨月查询由业务 SQL 显式 UNION |
| Quartz | 定时任务调度 | ❌ | 见 §2.4 |
| Apache POI | Excel | ⚠️ | 自研最小 XLSX |
| MinIO / 阿里云 OSS | 对象存储 | ❌ | 本地磁盘 `ruoyi.profile`；如需 OSS，可在 `FileUpload` 层加适配器 |
| Forest（HTTP 客户端） | 调用第三方（恒达、腾讯地图、车辆监控） | ❌ | 见 §5.1：调用侧的异常边界已逐条分析；C++ 有 `cm::net` 传输原语，缺一个 HTTP/1.1 客户端 |
| Druid 控制台 `/druid/**` | SQL 监控台 | ❌ | SecurityConfig 中本来就是 `denyAll()`，C++ 直接返回 403 |
| Swagger / springfox | API 文档 | ❌ | 以 `ENDPOINTS_INVENTORY.md` 取代 |
| Actuator | 健康检查 | ⚠️ | 新增 `GET /health`（C++ 扩展，Java 无此端点） |
| JVM `ThreadLocal` | 当前登录用户 | ⚠️ | C++ 使用 `thread_local`（`SecurityUtils`），同一 worker 内有效 |
| `LogAspect` + `AsyncManager` | `@Log` 写操作日志 | ✅ | 234 条规则由 `scripts/gen_operlog_table.py` 从 Java 源码抽取，`cm::aspect::OperLogAspect` 单线程异步落库，细节见 §6.6 |

### 5.1 外部 HTTP 调用的异常边界（逐条读 Java 源码所得，移植时按此对齐）

Java 侧配置（`application.yml:182-193`）：Forest + httpclient，`timeout=60s`、
`connect-timeout=60s`、`BackOffRetryer`、`retry-count=2`、`max-retry-interval=1s`。
即**一次外部调用最坏可占住请求线程约 3×60s**；C++ 的 worker 池同样有限（32），
所以这些接口一旦上游抖动就是整站排队，移植时必须显式设超时而不是沿用 60s。

| 调用点 | 失败时的 Java 行为 | 移植要点 |
|---|---|---|
| `HenDaServiceImpl.getPileToLonLat`（GeoServer CQL） | 整个方法 `try/catch(Exception) → return null`：连不上、非 2xx、返回非 JSON、缺 `data` 键、`data` 里没有 `x/y` —— 全部塌缩成同一个 null，调用方无法区分"查不到"与"服务挂了" | 返回值必须保持 null 语义，不能改成抛异常；另外 `filter=lxbh='<用户输入>'` 是拼进远端 CQL 的，移植时不得原样拼接（Java 没做转义，属于其缺陷） |
| 同上，`data` 存在但 `x/y` 为空 | `getDoubleValue` 把 null 变成 **0.0** → `syncAllGeometry` 会写入 (0,0) 坐标 | 照抄该行为才算一致；修复要单独标注为"偏离 Java" |
| `GeometryController.syncAllGeometry / syncAllGeometry1` | 立即 `return success()`，真正的工作在 `executor` 线程池里 fire-and-forget；lambda 里抛异常只会打到默认 uncaught handler，**响应已经发出去了** | 移植成"同步执行"会改变响应时延与语义；要保持异步 + 响应先行，并明确失败不可见 |
| 同上的循环条件 `while (count >= 7)` + 每 10 个桩号取 1 个点 | 上游半路超时会让 `doubleList` 填不满 → 静默少写数据（源码注释自己写了"跑到一半 hengda 接口批量超时"）；重复调用同一 (lxbh,lxfx,qdzh) 会插入重复行 | 幂等性由调用方负责，C++ 不额外加去重（加了就和 Java 结果不同） |
| `LonLatPathsUtils`（腾讯地图 direction） | 同样 `catch(Exception) → return null`；`status!=0` 只 `System.err` 打印；polyline 少于 2 个点会 AIOOBE 也被吞掉 | 注意它做的是 gcj02→wgs84 转换并**交换经纬度**，移植时坐标顺序极易抄反 |
| `CarSuspiciousController.syncSuspiciousCarTask`（permitAll） | 签名 = `SHA1(signatureKey + timeStamp)`；两者都由请求方提供 ⇒ 任何人都能自证；没有时间窗（可无限重放）；拼接有歧义（"a1"+2 与 "a"+12 同号） | 这是 Java 的既有安全缺陷，按"照抄不擅自修正"处理，但要写进安全评审；C++ 已有 `sha1` 原语，可实现 |
| `OdsRtSzdnSnapshotFlowAddcodeController` 的 `/earliest-time` | 通过 Forest 取 GaussDB 的 `Date`，**没有 try/catch** ⇒ 上游失败直接 500；成功时 `data` 是 ISO-8601 字符串，失败无数据时是字面量 `"暂无数据"` | 响应体类型会在"日期串"和"中文提示串"之间切换，前端按字符串处理；移植别统一成 null |
| `carInfoService.getRedisCarList`（大屏 `carLocation` 的数据源） | 走 **Redis + DB 回源**，不是外部 HTTP；`setCacheObject(key, list)` **不带过期时间** ⇒ 永久缓存；缓存里若是别的类型，`(List) obj` 强转抛 ClassCastException → 500 | C++ 可直接实现（Redis + 同一 DB 查询）；但必须同样不设 TTL，否则数据新鲜度行为与 Java 不同 |

---

## 6. 安全相关兼容性

### 6.1 JWT（jjwt 0.9.1）密钥解码

`Jwts.builder().signWith(SignatureAlgorithm.HS512, secret)` 内部把 secret 当作 **Base64 文本**解码。
默认 `abcdefghijklmnopqrstuvwxyz`（26 个字符，无填充）解码为 **19 字节**：

```
69 b7 1d 79 f8 21 8a 39 25 9a 7a 29 aa bb 2d ba fc 31 cb
```

> ✅ 本机用 JDK 1.8 实测：`Base64.getDecoder().decode("abcdefghijklmnopqrstuvwxyz")`
> 返回 19 字节、末尾 `...31cb`；jjwt 0.9 内置的 Tomcat 派生 codec 同样按“末尾不完整组补零输出”。
> ⚠️ 早期实现把不足 4 字符的尾组整组丢弃（得到 18 字节），Java 签发的 token 会被 C++ 判为签名不符，
> 表现为“带着合法 token 仍然 401”。`tests/main_test.cpp::testJwt` 现固定断言 19 字节。

C++ `Jwt::decodeJavaBase64` 与上面保持一致。**若把 secret 换成合法的 44 字符 Base64（带 `=`），
Java 与 C++ 仍解码一致**；换成非 Base64 字面量时两边都会退化，不要依赖。

### 6.2 读取 Java 写入的 Redis 缓存值

Java 侧 `FastJson2JsonRedisSerializer` 打开 `WriteClassName`，写出的值**不是严格 JSON**：

```
"permissions":Set["*:*:*"]     "deptId":25367L     "tenantId":-1L     "params":{"@type":"java.util.HashMap"}
```

Jackson / nlohmann 都读不了。C++ 侧用 `cm::utils::normalizeFastJson2` 把类型前缀与
`L/F/D` 数值后缀降级成严格 JSON 后再解析（`parse_cached_json`），只用于**读缓存**：
请求体解析仍走严格的 `cm::parse_json`，Java 会拒绝的非法入参 C++ 同样拒绝。

> ✅ 实测依据：Redis db0 里由 Java 应用写入的会话（含 `Set[...]` / `25367L`）
> 现在可被 C++ 解析并放行，`scripts/live_probe.py` 全链路可用。

### 6.3 分页响应体的 code / msg

`TableDataInfo` 的 `code`/`msg` 不是业务代码设置的，而是 `BaseController.getDataTable` 统一填的：

```java
rspData.setCode(HttpStatus.SUCCESS);   // 200
rspData.setMsg("查询成功");
```

> ⚠️ 早期 C++ 实现只构造 `total/rows`，导致所有列表接口输出 `"code":0,"msg":null`
> （HTTP 仍是 200，前端 `res.code !== 200` 会判失败）。现在 `TableDataInfo(list,total)` 构造即对齐。

### 6.4 BCrypt

Java `BCryptPasswordEncoder` 默认强度 10、前缀 `$2a$`。C++ 使用 libbcrypt
`bcrypt_gensalt(10)` + `bcrypt_hashpw`，输出同格式 `$2a$10$...`，可互相校验。

### 6.5 密码策略（登录入口）

Java `SysLoginController.login` 在调用登录服务前执行 `CommonUtil.checkPassword`：

```
^(?![A-Za-z0-9]+$)(?![a-z0-9\W]+$)(?![A-Za-z\W]+$)(?![A-Z0-9\W]+$)[a-zA-Z0-9\W]{8,20}$
```

不满足即返回 `对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！`（code 500）。
C++ 以等价逻辑实现（`SysLoginController.cpp::checkPasswordInvalid`），包含：
下划线不允许（属 `\w` 但不在字符类内）、非 ASCII 字符视为 `\W`（Java 默认 ASCII 口径）。

### 6.6 操作日志切面（`@Log` → `sys_oper_log`）

Java：`LogAspect` 以 `@annotation(Log)` 为切点，`@AfterReturning` / `@AfterThrowing` 各记一次，
经 `AsyncManager`（单线程定时器）异步 `insertOperlog`。共 **234** 个端点带 `@Log`
（`scripts/gen_operlog_table.py` 从 Java 源码抽取；注释掉的 `@Log` 不算，`SysFileController`
那种 `@PostMapping` 写在 `@Log` 之上的顺序也能解析）。

C++：`cm::aspect::OperLogAspect` 在派发层的 handler 前后各调一次 `record()`，
单线程队列串行落库，规则表 `src/cm/web/specs/OperLogTable.cpp`。逐条对齐的细节：

| 字段 | Java 取值 | C++ |
|---|---|---|
| `status` | `BusinessStatus.SUCCESS/FAIL.ordinal()` = 0 / 1 | 同 |
| `business_type` / `operator_type` | 枚举 **ordinal**（`OTHER0 INSERT1 UPDATE2 DELETE3 GRANT4 EXPORT5 IMPORT6 FORCE7 GENCODE8 CLEAN9`；operatorType 默认 `MANAGE`=1） | 同（表里存的是数字） |
| `method` | `joinPoint.getTarget().getClass().getName() + "." + name + "()"` | 生成器按 `package + 类名 + 方法名` 拼 |
| `oper_url` | `getRequestURI()`，**不含 query、不解码**，截 255 | 取 `req.target` 的 `?` 前段（保持百分号形态） |
| `oper_ip` | `IpUtils.getIpAddr()`：`x-forwarded-for`→`Proxy-Client-IP`→`X-Forwarded-For`→`WL-Proxy-Client-IP`→`X-Real-IP`→`remoteAddr`，`0:0:0:0:0:0:0:1`→`127.0.0.1`，多级代理取第一段 | 复用 `cm::utils::ipAddr` |
| `oper_location` | `AddressUtils.getRealAddressByIP(ip)`；`ruoyi.addressEnabled=false` ⇒ 内网 `内网IP`，其余 `XX XX`；解析不出来的串（如 `unknown`）也算内网 | 同，且**不发外部定位请求** |
| `oper_name` / `dept_name` | `loginUser.getUsername()` / `loginUser.user.dept.deptName` | 同（取自 Redis 里的 Java 会话） |
| `oper_param` | 参数表为空 **且** PUT/POST ⇒ 序列化方法入参（`argsArrayToString`，空格分隔）；否则 ⇒ `JSON.toJSONString(paramMap)`，其中同名多值按 `,` 合并、键序是 **HashMap 桶序**、DELETE 只有路径变量时是 `{}` | 同（桶序复用 `javaMapOrder`） |
| `json_result` | `JSON.toJSONString(返回值)`，**fastjson2 默认丢 null**（与 HTTP 响应的 Jackson 相反） | 同（`fastJsonCompact`） |
| 截断 | `StringUtils.substring(s,0,2000)`（`oper_param`/`json_result`/`error_msg`），`oper_url` 255 —— 按**字符**不按字节 | `subAtMost` 按码点截断且不切断 UTF-8 序列 |
| 敏感字段 | `EXCLUDE_PROPERTIES = password/oldPassword/newPassword/confirmPassword` + `excludeParamNames` | 同 |
| `oper_time` | SQL 里写死 `sysdate()`（DB 时钟，不是应用时钟） | 同 |
| 未登录 | `SecurityUtils.getLoginUser()` 抛 `CustomException`，被 `handleLog` 的 `catch` 吞掉 ⇒ **整行不写** | `build()` 返回 `nullopt`，同 |
| 权限不足 | `@PreAuthorize` 在切面外层，方法根本没执行 ⇒ **不写** | 只在 handler 前后调用，同 |
| 异常消息 | `e.getMessage()`；`NullPointerException` 的消息是 **null** ⇒ `error_msg` 写 NULL | `Failure{std::optional<std::string>}` 区分"无消息"与"空串" |

⚠️ 三处不可完全等价，已按最小偏离处理：

1. **入参分支记录的是请求体本身**（丢掉 null 与敏感键后的紧凑 JSON），Java 序列化的是**绑定后的实体**
   —— 字段顺序（声明序 vs 请求顺序）与未知键的取舍会不同。值集合一致，形态可能不同。
2. **multipart 上传类接口 `oper_param` 记空串**：Java 的 `isFilterObject` 会跳过 `MultipartFile`
   只留其余标量入参，而 C++ 侧不掌握方法签名，无法区分哪些参数是文件。
3. **异步队列有界**（5 万条）：Java 的 timer 队列无界。溢出时丢日志并打本地错误，
   避免内存被拖垮——这是刻意偏离，不改（生产上宁可降级）。

---

## 7. 覆盖状态

* 端点总数（Java 源码自动提取）：**497**，见 `ENDPOINTS_INVENTORY.md`。
* 已迁移端点：见该文件 `C++ 状态` 列（`✅` 已注册 / `❌` 未注册）。
* 框架层（路由、鉴权、JWT、分页、异常、CORS、静态资源、上传下载）**100% 对齐**。
* 认证链路（`/captchaImage`、`/login`、`/getInfo`、`/getRouters`、`/logout`）**100% 对齐**。

> 覆盖状态表在每次新增控制器后由 `scripts/gen_inventory.py` 重新生成。

---

## 8. 验证清单

```bash
# 1. 单元测试（JSON 顺序、JWT、日期、SQL 转义、分页、验证码、BCrypt）
./build/carmonit_tests

# 2. 健康检查（C++ 扩展）
curl -s http://127.0.0.1:9989/health
# {"status":"UP","db":"UP","redis":"UP"}

# 3. 未登录访问受保护接口 → 200 + code 401
curl -i http://127.0.0.1:9989/getInfo

# 4. 验证码
curl -s http://127.0.0.1:9989/captchaImage | head -c 120

# 5. 登录（需数据库中的真实用户与 BCrypt 密码）
curl -s -X POST http://127.0.0.1:9989/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin@1234","code":"","uuid":""}'

# 6. 带 token 获取用户信息
curl -s http://127.0.0.1:9989/getInfo -H "Authorization: Bearer $TOKEN"

# 7. 不登录也能拿到可用 token：直接复用 Redis 里现存的 Java 会话
#    （make_token.py 复刻 jjwt + HS512 + Base64 密钥解码，与 Java TokenService 等价）
TOKEN=$(python scripts/make_token.py)
curl -s http://127.0.0.1:9989/getInfo -H "Authorization: Bearer $TOKEN"

# 8. 批量实机探针：逐条路径打印 HTTP 状态 + 业务 code，非 200 高亮
#    （Windows 下必须关掉 MSYS 的路径转换，否则 /base/cdc 会变成 D:/base/cdc）
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' \
  python scripts/live_probe.py --port 9990 /base/cdc/status /system/user/list

# 9. 中文导出文件名的端到端回归（xlsx 落盘 + UTF-8 路径 + anonymous()/authenticated() 规则）
python scripts/verify_cn_export.py "$TOKEN"          # 16 条断言，含"带 token 下载 403"这条 Java 语义

# 10. SysUser 的 @Excel 列集合/列序/单元格类型/转换器/dept 关联
python scripts/verify_user_excel.py "$TOKEN"         # 14 条断言，直接解析下载的 xlsx

# 11. 生成的 59 份 CRUD Spec：逐条把 SQL 打到真实库上跑，报告异常
python scripts/verify_generated_sql.py

# 12. flow 审批三件套（多表事务 + 失败回滚，27 条断言）
python scripts/verify_flow_approval.py --port 9991

# 13. @Log 操作日志切面：做真实新增/删除/失败请求，再读回 sys_oper_log 的字段
python scripts/verify_operlog.py 9991 "$TOKEN"       # 18 条断言
# 规则表（234 条）由 Java 源码生成，改动 Java 控制器后重新执行：
python scripts/gen_operlog_table.py
```
