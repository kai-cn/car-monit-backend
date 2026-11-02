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

* Java：Apache POI，支持多 sheet、样式、公式、日期格式、`@Excel` 注解驱动的列顺序。
* C++：`cm::utils::Excel` 自研最小 XLSX（zip + SpreadsheetML），支持单 sheet、字符串/数字、
  列宽与表头；不支持样式/公式/多 sheet/图片。
* 补偿：导出文件可被 Excel/WPS 正常打开；列头与 Java `@Excel(name=...)` 一致；`export`
  端点的文件名规则（`<业务名>_yyyyMMddHHmmss.xlsx`）一致。
* 导入：支持读取第一个 sheet 的字符串/数字单元格；日期单元格按文本解析。

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
| `Date`（无注解） | ISO-8601 带 `+08:00` | `formatIsoDate` |
| `@JsonFormat` | `yyyy-MM-dd HH:mm:ss` | `formatJsonDate` |
| `null` 字段 | Jackson 默认输出 `null` | `putStr/putI64` 输出 `null` |
| `@JsonInclude(NON_EMPTY)` VO | 空串/null/空集合不输出 | `RouterVo` 等按此实现 |
| `password` | `@JsonIgnore` 不输出 | `SysUser::toJson` 不输出 |

---

## 4. Java 侧“看起来一样、实际不一样”的陷阱（✅ 已按实测实现）

1. **`AuthenticationEntryPointImpl` 的 Content-Type 是小写 `utf-8`**，不是大写。
2. **`/logout` 在 JWT 过滤器之前**，无需有效 token，且始终返回 200 + `退出成功`。
3. **非法 JWT 会返回真实 HTTP 500**（过滤器异常无法被 `@ControllerAdvice` 捕获）。
4. **`anonymous()` 是“仅匿名可访问”**：已登录用户访问返回真实 HTTP 403。
5. **未匹配路由且无 token → 401**（Security 先于 DispatcherServlet 的 404）。
6. **`CustomException` / `UserException` / `BaseException` 不是 `ServiceException`**，
   一律被 `RuntimeException` 兜底为 code 500。
7. **`SysUser` 的校验注解被注释掉**，`POST /system/user {}` 是 NPE（`msg:null`），
   不要“顺手补校验”。
8. **PageHelper 在 count=0 时不执行数据查询**；`pageNum<=0` 时 offset=0；`reasonable=true`
   会把页码夹到有效范围。
9. **`AjaxResult` 是 HashMap**，`put` 顺序不等于输出顺序。
10. **`jjwt` 的 secret 先做 Base64 解码**，默认 26 字符 → 18 字节，见 §6。

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
| Forest（HTTP 客户端） | 调用第三方（恒达、腾讯地图、车辆监控） | ❌ | 未实现调用侧；相关控制器如迁移需补 HTTP 客户端（libcurl 或自研） |
| Druid 控制台 `/druid/**` | SQL 监控台 | ❌ | SecurityConfig 中本来就是 `denyAll()`，C++ 直接返回 403 |
| Swagger / springfox | API 文档 | ❌ | 以 `ENDPOINTS_INVENTORY.md` 取代 |
| Actuator | 健康检查 | ⚠️ | 新增 `GET /health`（C++ 扩展，Java 无此端点） |
| JVM `ThreadLocal` | 当前登录用户 | ⚠️ | C++ 使用 `thread_local`（`SecurityUtils`），同一 worker 内有效 |

---

## 6. 安全相关兼容性

### 6.1 JWT（jjwt 0.9.1）密钥解码

`Jwts.builder().signWith(SignatureAlgorithm.HS512, secret)` 内部用
`TextCodec.BASE64.decode(secret)`，默认 `abcdefghijklmnopqrstuvwxyz` 解码为 **18 字节**：

```
69 b7 1d 79 f8 21 8a 39 25 9a 7a 29 aa bb 2d ba fc 31
```

C++ `Jwt::decodeJavaBase64` 完全复刻该行为（末尾不足 4 字符的组丢弃），已在
`tests/main_test.cpp` 中断言。**若把 secret 换成合法的 32 字节 Base64（44 字符带 `=`），
Java 与 C++ 会得到不同的 key 长度**——这是 jjwt 的既有行为，C++ 保持一致。

### 6.2 BCrypt

Java `BCryptPasswordEncoder` 默认强度 10、前缀 `$2a$`。C++ 使用 libbcrypt
`bcrypt_gensalt(10)` + `bcrypt_hashpw`，输出同格式 `$2a$10$...`，可互相校验。

### 6.3 密码策略（登录入口）

Java `SysLoginController.login` 在调用登录服务前执行 `CommonUtil.checkPassword`：

```
^(?![A-Za-z0-9]+$)(?![a-z0-9\W]+$)(?![A-Za-z\W]+$)(?![A-Z0-9\W]+$)[a-zA-Z0-9\W]{8,20}$
```

不满足即返回 `对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！`（code 500）。
C++ 以等价逻辑实现（`SysLoginController.cpp::checkPasswordInvalid`），包含：
下划线不允许（属 `\w` 但不在字符类内）、非 ASCII 字符视为 `\W`（Java 默认 ASCII 口径）。

---

## 7. 覆盖状态

* 端点总数（Java 源码自动提取）：**326**，见 `ENDPOINTS_INVENTORY.md`。
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
```
