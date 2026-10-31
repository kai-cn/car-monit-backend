# 附录 E：Java 运行时异常基线实测

> 目的：解决“双 `@RestControllerAdvice` 谁生效”以及错误响应结构不确定的问题。
> 方法：启动原始 Java 服务，按真实 HTTP 请求抓取状态码、Content-Type 与响应体。
> 日期：2026-10-31
> 结论：**`GlobalExceptionHandler`（framework）实际优先，`GlobalExceptionTraceHandler`（system）在本运行时被完全遮蔽。**

---

## E1. 实测环境

| 项 | 值 |
|---|---|
| Java | 1.8.0_202 |
| 应用 | `ruoyi-admin/target/ruoyi-admin.jar`（源码构建） |
| 端口 | `9989` |
| MySQL | 8.0.30，`127.0.0.1:3307`，库 `carmonitdb` |
| Redis | 8.10.2，`127.0.0.1:6379` |
| Kafka | 未启动（消费者连接失败，不影响 HTTP 探测） |
| Elasticsearch | 未启动（无 HTTP 调用） |
| Quartz | 以 `--spring.quartz.auto-startup=false` 启动，未触发任务 |
| 认证 | 临时用户 `probe_admin`（授予 `system:user:add`、`system:config:add`）与 `probe_user`（无角色） |

> 临时用户/角色仅用于本次探测，测试后已从数据库删除；未修改生产数据。

---

## E2. 探测结果矩阵

| # | 请求 | HTTP | Content-Type | 响应体（原样） | 命中处理器 |
|---:|---|---:|---|---|---|
| 1 | `GET /getInfo`（无 token） | **200** | `application/json;charset=utf-8` | `{"msg":"请求访问：/getInfo，认证失败，无法访问系统资源","code":401}` | `AuthenticationEntryPointImpl` |
| 2 | `GET /nonexistent-xyz`（无 token） | **200** | `application/json;charset=utf-8` | `{"msg":"请求访问：/nonexistent-xyz，认证失败，无法访问系统资源","code":401}` | Security 先于 404 |
| 3 | `GET /login`（只允许 POST） | **200** | `application/json` | `{"msg":"Request method 'GET' not supported","code":500}` | `GlobalExceptionHandler.handleHttpRequestMethodNotSupported` |
| 4 | `POST /login`，body `{bad` | **200** | `application/json;charset=UTF-8` | `{"msg":"JSON parse error: Unexpected character ('b' (code 98)): was expecting double-quote to start field name; nested exception is com.fasterxml.jackson.core.JsonParseException: ...","code":500}` | `GlobalExceptionHandler.handleException` |
| 5 | `POST /system/user`，无权限，body `{}` | **200** | `application/json;charset=UTF-8` | `{"msg":"没有权限，请联系管理员授权","code":403}` | `GlobalExceptionHandler.handleAccessDeniedException` |
| 6 | `POST /system/user`，有权限，body `{}` | **200** | `application/json;charset=UTF-8` | `{"msg":null,"code":500}` | `GlobalExceptionHandler.handleRuntimeException`（`NullPointerException`，`getMessage()==null`） |
| 7 | `POST /system/config`，有权限，body `{}` | **200** | `application/json;charset=UTF-8` | `{"msg":"参数键名长度不能为空","code":500}` | `GlobalExceptionHandler.handleMethodArgumentNotValidException` |
| 8 | `GET /system/user/abc` | **200** | `application/json` | `{"msg":"请求参数类型不匹配，参数[userId]要求类型为：'java.lang.Long'，但输入值为：'abc'","code":500}` | `GlobalExceptionHandler.handleMethodArgumentTypeMismatchException` |
| 9 | `GET /system/user/list?orderByColumn=bad;drop` | **200** | `application/json` | `{"msg":"参数不符合规范，不能进行查询","code":500}` | `GlobalExceptionHandler.handleRuntimeException`（`UtilException`） |
| 10 | `POST /login`，`probe_admin` + `Wrong@1234` | **200** | `application/json;charset=UTF-8` | `{"msg":"用户不存在/密码错误","code":500}` | `GlobalExceptionHandler.handleServiceException` |
| 11 | `GET /nonexistent-xyz`（有效 token） | **404** | `application/json` | `{"timestamp":"2026-10-31T15:39:16.486+08:00","status":404,"error":"Not Found","path":"/nonexistent-xyz"}` | Spring Boot 默认 `/error` |
| 12 | `POST /login`，`probe_admin` + `Probe@1234` | **200** | `application/json;charset=UTF-8` | `{"msg":"操作成功","code":200,"token":"<redacted>"}` | `SysLoginController.login` |

---

## E3. 关键结论

### E3.1 异常 advice 顺序

`GlobalExceptionHandler` 含 `Exception` 与 `RuntimeException` 兜底处理器，且在运行时**先于** `GlobalExceptionTraceHandler` 被解析。因为 Spring 在多个 advice 命中同一异常时取第一个 advice 的匹配方法，所以：

- `GlobalExceptionTraceHandler` 的 `MonitorResponse`（400/404/405/500）在本运行环境**从未出现**；
- 非法 JSON、NPE、SQL/运行异常、业务异常、校验异常全部走 `GlobalExceptionHandler`；
- 未匹配路由不会进入 `NoHandlerFoundException` 处理器（未开启 `throw-exception-if-no-handler-found`），由 Spring Boot 默认 `/error` 返回 404。

Rust 侧应**只实现 `AjaxResult` 错误模型**，不要实现 `MonitorResponse` 的 HTTP 状态分支。`GlobalExceptionTraceHandler` 可作为“不迁移”的框架契约文件记录在案。

### E3.2 响应封套字段顺序（实测）

| 封套 | 实测字段顺序 |
|---|---|
| `AjaxResult`（错误） | `msg` → `code` |
| `AjaxResult`（登录成功） | `msg` → `code` → `token` |
| `/getInfo` | `msg` → `code` → `pjFlag` → `overdue` → `permissions` → `roles` → `user` |
| `TableDataInfo` | `total` → `rows` → `code` → `msg` |
| Spring 默认 404 | `timestamp` → `status` → `error` → `path` |

> `AjaxResult extends HashMap`，顺序来自 Java HashMap 桶序，不是插入序。Rust 若要字节级兼容，必须固定上述顺序，而不是使用 `HashMap`。

### E3.3 鉴权与校验的先后

- Security 过滤链先于路由匹配：未登录访问不存在的路径返回 **401**，不是 404。
- `@PreAuthorize` 先于 `@Validated @RequestBody`：无权限时返回 **403**，不会先报参数错误。
- `SysUser` 的校验注解在源码中被注释掉（`@NotBlank`/`@Size`/`@Email` 均无效），因此 `{}` 不会触发校验，最终在 `checkUserNameUnique(null)` 处 NPE，返回 `{"msg":null,"code":500}`。Rust 迁移时**不要补上加严校验**，否则行为漂移。
- `SysConfig` 的校验注解有效，`{}` 的首条错误实测为 `参数键名长度不能为空`（`configKey` 先于 `configName`）。

### E3.4 错误码与 HTTP 状态

- 除 404 外，所有业务/鉴权/校验/运行异常都返回 **HTTP 200**。
- 401/403 是 body 内的 `code`，不是 HTTP 状态。
- `ServiceException` 未携带自定义 code 时为 500。
- NPE 的 `msg` 为 JSON `null`（不是空串）。

---

## E4. 复现命令（脱敏）

```bash
# 未登录
curl -i http://127.0.0.1:9989/getInfo

# 405
curl -i http://127.0.0.1:9989/login

# 非法 JSON
curl -i -X POST -H 'Content-Type: application/json' --data-binary '{bad' \
  http://127.0.0.1:9989/login

# 校验失败（需要 system:config:add）
curl -i -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' --data-binary '{}' \
  http://127.0.0.1:9989/system/config

# 类型不匹配
curl -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:9989/system/user/abc

# 运行时异常
curl -i -H "Authorization: Bearer $TOKEN" \
  'http://127.0.0.1:9989/system/user/list?orderByColumn=bad;drop'

# 404（有效 token）
curl -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:9989/nonexistent-xyz
```

---

## E5. 对阶段二/三的影响

1. 删除 `MonitorResponse` 迁移分支；错误统一为 `AjaxResult` 结构。
2. `AppError` 只需映射：`401`、`403`、`500`（含 `msg=null` 的 NPE 场景）；404 交给 Axum 的默认 404 JSON（但字段结构需与 Spring Boot 默认错误体一致，或明确不复刻默认错误体，需确认）。
3. 路由守卫顺序固定为：**认证 → 权限 → 参数绑定/校验 → handler**。
4. 不要为 `SysUser` 补校验；按原样保留“校验缺失 + NPE”的行为。
5. 404 的默认错误体包含 `timestamp/status/error/path`；如果前端依赖该结构，Rust 需自定义 404 fallback，否则可用 Axum 默认。
