# MIGRATION_GUIDE —— Java → C++ 1:1 迁移对照

> 源项目：`car-monit-backend`（RuoYi 3.8.7 定制版）
> 目标项目：`car-monit-cpp`（C++20 / CMake 3.16+）
> 读者：原 Java 开发人员。本文按“层”组织，每层给出 Java 原写法 → C++ 新写法 →
> 一致性判断（✅/⚠️/❌）→ 差异补偿。
>
> 配套文档：`README_CPP.md`（启动）、`COMPATIBILITY.md`（差异清单）、
> `QUICK_REFERENCE.md`（一页纸速查）、`ENDPOINTS_INVENTORY.md`（端点覆盖）。

---

## 0. 技术栈扫描结果

### 0.1 源项目依赖（`pom.xml` 实测）

| 类别 | 依赖 | 版本 |
|---|---|---|
| 运行时 | Spring Boot | 2.5.15 |
| 语言 | Java | 8 |
| Web | spring-boot-starter-web（内嵌 Tomcat） | 2.5.15 |
| 持久层 | MyBatis-Plus / PageHelper | 3.x / 1.4.x |
| 连接池 | Druid | 1.2.x |
| 数据库 | MySQL | 8.x（`127.0.0.1:3307/carmonitdb`） |
| 缓存 | Redis（Lettuce） | 6.x |
| 分表 | ShardingSphere-JDBC | 5.x |
| 消息 | Spring Kafka | 2.8.x |
| 搜索 | Elasticsearch RestHighLevelClient | 7.x |
| 调度 | Quartz | 2.3.x |
| 安全 | Spring Security + jjwt | 5.7 / 0.9.1 |
| 序列化 | Jackson + fastjson2 | 2.13 / 2.0.x |
| 验证码 | Kaptcha | 2.3.2 |
| Excel | Apache POI | 4.1.2 |
| 系统信息 | OSHI | 5.x |
| 对象存储 | MinIO / 阿里云 OSS | — |
| 模板 | Velocity（代码生成） | 2.3 |
| HTTP 客户端 | Forest | 1.5.x |
| 文档 | springfox-swagger | 3.0 |

### 0.2 组件映射矩阵

| Java 侧 | C++ 生产候选 | 本项目选择 | 理由与差异 |
|---|---|---|---|
| Spring Boot / Spring MVC | Drogon、Paozhu、oat++ | **自研 `cm::web::Server` + `Router`** | 零外部依赖、可离线构建；逐行复刻 Filter 链顺序与错误封套，比引入框架更易做到字节级一致 |
| MyBatis / MyBatis-Plus | Drogon ORM、SOCI、sqlpp11 | **自研 `MySqlClient`（wire protocol）+ `Db`** | 同上；SQL 全部显式手写，与 mapper XML 一一对应，没有隐式 ORM 行为 |
| Druid 连接池 | HikariCP 无 C++ 版；自研池 | **`ConnectionPool`** | 支持 minIdle/maxActive/maxWait、借出前 ping 探活 |
| PageHelper | — | **`Db::queryPage`** | 精确复刻 count=0 跳过、reasonable、offset=0 语义 |
| Spring Security 过滤器链 | Drogon middleware、jwt-cpp | **`Server::dispatch`** | 顺序：CORS → LogoutFilter → JWT → 授权规则 → @PreAuthorize |
| jjwt 0.9.1 | jwt-cpp、libjwt | **OpenSSL HMAC + 自研 JWT** | 必须复刻 jjwt 的 Base64 secret 解码怪癖 |
| BCryptPasswordEncoder | libbcrypt、bcrypt-cpp | **vendored libbcrypt** | 与 Spring 同算法同格式 |
| Jackson | nlohmann/json、RapidJSON | **nlohmann ordered_json** | 保序输出、支持自定义桶序重排 |
| fastjson2（Redis） | — | **nlohmann** | ⚠️ 不写 `@type`，见 COMPATIBILITY §2.2 |
| application.yml | yaml-cpp | **自研最小 YAML 解析器** | 无系统 yaml-cpp 时仍可构建；支持嵌套/列表/行内注释 |
| @ConfigurationProperties | — | **`AppConfig`** | 显式绑定 + 环境变量覆盖（`CM_*` / Spring 风格） |
| SLF4J / Logback | spdlog、glog | **自研 `cm::log::Logger`** | 控制台+文件、按大小滚动、级别过滤 |
| JUnit 5 | GoogleTest、Catch2 | **自研断言 main**（`tests/main_test.cpp`） | 无网络依赖，`ctest` 可跑 |
| Maven | CMake + Conan/vcpkg | **CMake + vendored 第三方** | 离线可构建 |
| JVM 线程池 | std::thread / 线程池库 | **固定 worker 池** | ⚠️ 无 GC、无虚拟线程 |
| ThreadLocal | thread_local / 显式传递 | **thread_local `SecurityUtils`** | 同一请求在同一 worker 内串行执行 |
| Quartz | — | ❌ 不内置 | 见 COMPATIBILITY §2.4 |
| Kafka / ES / ShardingSphere | librdkafka / elasticlunr / — | ❌ 不内置 | 见 COMPATIBILITY §5 |
| Kaptcha | — | **自研 PNG 绘制** | ⚠️ JPEG→PNG |
| POI | libxlsxwriter / OpenXLSX | **自研最小 XLSX** | ⚠️ 单 sheet |
| OSHI | 读 `/proc`、`sysinfo` | **`/proc` 解析** | ✅ 字段结构一致 |
| springfox | — | ❌ | 以 `ENDPOINTS_INVENTORY.md` 取代 |
| Actuator | — | **`GET /health`（扩展）** | ⚠️ Java 无此端点 |

---

## 1. 工程结构对照

```
car-monit-backend/                     car-monit-cpp/
├── ruoyi-admin/                       ├── src/cm/web/controller/{system,common,monitor,base,manager,flow,tool}/
│   └── .../controller/**              │
├── ruoyi-framework/                   ├── include/cm/framework/ + src/cm/framework/
│   ├── config/                        │   ├── config/          AppConfig, Yaml
│   ├── security/                      │   ├── security/        Jwt, TokenService, SecurityUtils
│   ├── web/service/                   │   └── web/             Server, Router, Errors, ExceptionMapper, service/
│   └── web/exception/                 │
├── ruoyi-system/                      ├── include/cm/system/ + src/cm/system/
│   ├── mapper/                        │   ├── mapper/          *Mapper
│   ├── service/impl/                  │   └── service/         *Service
│   └── domain/                        │       (domain 见 common/core/domain 与 system/domain)
├── ruoyi-common/                      ├── include/cm/common/
│   ├── core/domain/                   │   ├── core/domain/     AjaxResult, R, BaseEntity, entity/*
│   ├── core/page/                     │   ├── core/page/       PageDomain, TableDataInfo
│   ├── constant/                      │   ├── constant/        Constants, HttpStatus
│   ├── exception/                     │   ├── exception/       Exceptions.hpp
│   └── utils/                         │   └── utils/           DateUtils, StringUtils, IdUtils, JsonUtils, ...
├── ruoyi-quartz/                      │   ❌ 未迁移（见 COMPATIBILITY §2.4）
├── ruoyi-generator/                   │   ❌ 代码生成器未迁移
└── ruoyi-admin/src/main/resources/    ├── config/
    ├── application.yml                │   ├── application.yaml
    ├── application-druid.yml          │   └── application-druid.yaml
    ├── mapper/**/*.xml                │   → SQL 内联在 *Mapper.cpp（注释标注 XML 来源）
    └── logback.xml                    │   → AppConfig.logDir/logLevel
```

---

## 2. 层 1：语言与运行时

### 2.1 对象生命周期

**Java**

```java
SysUser user = userMapper.selectUserByUserName(name);
if (user != null) { return user.getUserName(); }
```

**C++**

```cpp
std::optional<cm::domain::SysUser> user =
    cm::system::mapper::SysUserMapper::selectUserByUserName(name);
if (user) return user->userName.value_or("");
```

✅ 语义一致：`null` → `std::optional` 的空状态。
⚠️ `SysUser` 是值类型；从函数返回时发生移动，**不要保存指向它的指针/引用**。

### 2.2 空值三层语义

| Java | C++ | 说明 |
|---|---|---|
| `null`（对象） | `std::optional<T>{}` | 可能不存在 |
| 空字符串 | `""` | 存在但为空 |
| `Long id` | `std::optional<long long>` | 区分 0 与不存在 |

⚠️ 常见错误：把 `optional` 隐式转成 `0`/`""` 后再判断“是否为空”，会丢失语义。
本项目所有实体的字段都是 `std::optional<T>`，JSON 输出保持 `null`。

### 2.3 字符串与编码

* Java `String` 是 UTF-16；C++ `std::string` 是 UTF-8 字节。
* `length()` 在 C++ 是字节数。需要“字符数”时用 `StringUtils` 或显式按 UTF-8 码点计数
  （登录密码长度校验即如此实现）。
* `substring` 按字节会切坏中文，务必使用 `StringUtils::substringAfter*` 或按码点处理。

### 2.4 异常

```java
throw new ServiceException("参数错误");
```

```cpp
throw cm::exception::ServiceException("参数错误");
```

✅ 统一由 `ExceptionMapper` 转 `AjaxResult`（HTTP 200）。
⚠️ C++ 析构函数中禁止抛异常；本项目所有析构均为 `noexcept`。

### 2.5 并发

* Java 请求线程由 Tomcat 提供；C++ 由 `Server` 的 worker 线程池提供（默认 32）。
* `SecurityUtils` 使用 `thread_local`：一个请求从进入到返回都在同一线程，安全。
* 不要在 handler 中创建 `std::thread` 后访问 `ctx`（引用会悬空）。

---

## 3. 层 2：请求处理与路由

### 3.1 路由声明

**Java**

```java
@RestController
@RequestMapping("/system/user")
public class SysUserController extends BaseController {
    @PreAuthorize("@ss.hasPermi('system:user:list')")
    @GetMapping("/list")
    public TableDataInfo list(SysUser user) { ... }
}
```

**C++**

```cpp
void registerSysUserController(cm::web::Router& r) {
    r.get("/system/user/list",
          [](cm::web::RequestContext& ctx) -> cm::http::ApiResponse {
              // ...
          })
        .permi("system:user:list");
}
```

✅ 路径拼接规则一致（类级 `@RequestMapping` 前缀 + 方法级路径）。
⚠️ C++ 没有注解扫描：注册函数需要在 `Controllers.hpp` 的汇总里显式调用。

### 3.2 参数绑定

| Spring | C++ |
|---|---|
| `@RequestParam String name` | `ctx.param("name")` |
| `@RequestParam(required=false) Long id` | `ctx.optParam("id")` + `Convert::toLong` |
| `@PathVariable Long userId` | `ctx.pathVarLong("userId")` |
| `@RequestBody LoginBody body` | `ctx.body()` → `LoginBody::fromJson` |
| `MultipartFile file` | `ctx.req.getPart("file")` |
| `HttpServletRequest` | `ctx.req` |
| `HttpServletResponse` | 直接构造 `ApiResponse` |

⚠️ Spring 对 `Long` 参数类型错误会抛 `MethodArgumentTypeMismatchException`；C++ 侧
`pathVarLong` 目前返回 0。需要严格一致的控制器请显式校验并抛
`cm::exception::MethodArgumentTypeMismatchException("userId","java.lang.Long",raw)`。

### 3.3 过滤链顺序（`Server::dispatch`）

```
CorsFilter 预检
  → /logout（LogoutFilter，先于 JWT）
  → JwtAuthenticationTokenFilter（非法 token → 真实 500）
  → SecurityConfig 规则（401 / denyAll / anonymous-only 403）
  → 路由匹配（404 / 405）
  → @PreAuthorize（403）
  → Handler（异常 → ExceptionMapper）
```

✅ 与 `SecurityConfig` + `JwtAuthenticationTokenFilter` + `LogoutFilter` 顺序一致。

### 3.4 CORS

**Java**（`ResourcesConfig`）：回显 `Origin`、`allowCredentials=true`、回显请求的
`Headers`/`Methods`、`maxAge=1800`。

**C++**（`Server::applyCors`）：同一策略；预检请求直接 200，不进入业务。

---

## 4. 层 3：序列化与契约

### 4.1 `AjaxResult`

**Java**

```java
public class AjaxResult extends HashMap<String, Object> {
    public static AjaxResult success() { ... put("msg","操作成功"); put("code",200); }
}
```

**C++**

```cpp
class AjaxResult {
    Json obj_;   // ordered_json
    int code_;
public:
    static AjaxResult success();
    AjaxResult& put(const std::string& key, const Json& value);
    Json toJson() const;   // 按 Java HashMap 桶序重排
};
```

✅ 输出顺序与 Java 完全一致：
`success()` → `{"msg":"操作成功","code":200}`；
`error("x")` → `{"msg":"x","code":500}`；
登录成功 → `{"msg":"操作成功","code":200,"token":"..."}`。

> 为什么不是插入序？`AjaxResult extends HashMap`，Jackson 遍历 HashMap 得到桶序。
> C++ 用 UTF-16 `String#hashCode` + 异或高位 + `&15` 复刻，见
> `src/cm/common/utils/JavaCollections.cpp`。

### 4.2 `TableDataInfo`

```java
public class TableDataInfo {
    private long total;
    private Object rows;
    private int code;
    private String msg;
}
```

```cpp
Json toJson() const {
    Json j = Json::object();
    j["total"] = total;  // -> rows -> code -> msg
    ...
}
```

✅ 字段顺序固定，`rows` 为数组，`code=200`，`msg="查询成功"`。

### 4.3 日期

| Java | C++ |
|---|---|
| `@JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")` | `putJsonDate(j,"createTime",ms)` |
| 无注解 `Date`（StdDateFormat） | `putIsoDate(j,"loginDate",ms)` → `2024-05-17T14:15:52.000+08:00` |
| `DateUtils.getTime()` | `DateUtils::getTime()` |
| `DateUtils.parseDate(str)` | `DateUtils::parseDate(str)` → `optional<TimePoint>` |

⚠️ 时区固定 `+08:00`，见 `COMPATIBILITY.md §2.6`。

### 4.4 `@JsonIgnore` / `@JsonProperty`

`SysUser.password` 在 Java 中 `@JsonIgnore`（只写不读）。C++ `SysUser::toJson()` 不输出
`password`，但 `fromJson()` 仍读取（用于登录）。✅

### 4.5 `HashSet` 顺序

`/getInfo` 的 `roles`、`permissions` 是 `Set<String>`，Jackson 按 HashSet 迭代序输出。
C++ 用 `javaSetOrder` 复刻（容量 16、负载 0.75）。✅

---

## 5. 层 4：数据访问与事务

### 5.1 Mapper

**Java**

```xml
<select id="selectUserByUserName" resultMap="SysUserResult">
  <include refid="selectUserVo"/>
  where u.user_name = #{userName}
</select>
```

**C++**

```cpp
std::optional<cm::domain::SysUser> SysUserMapper::selectUserByUserName(const std::string& name) {
    return loadFirstUser(std::string(kSelectUserVo) +
                         " where u.user_name = " + cm::db::Db::lit(name));
}
```

✅ SQL 文本与 XML 逐段一致（列顺序、别名、join、`ifnull(d.tenant_id,-1)`）。
⚠️ 没有 MyBatis 的 `<if>` 动态 SQL：每个条件分支在 C++ 里是显式 `if` 拼接。

### 5.2 分页

**Java**

```java
startPage();
List<SysUser> list = userService.selectUserList(user);
return getDataTable(list);   // PageHelper 执行 count + limit
```

**C++**

```cpp
auto page = ctx.pageRequest();
auto res = cm::db::queryPage(countSql, dataSql, page);
return BaseController::ok(BaseController::dataTable(rowsToArray(res.rows, toJson), res.total));
```

✅ `queryPage` 复刻 PageHelper：
1. 先执行 `select count(0) from (...)`；
2. `total <= 0` 直接返回空 rows，**不执行数据查询**；
3. `reasonable=true` 时把 pageNum 夹到 `[1, ceil(total/size)]`；
4. `pageNum <= 0` 时 offset=0；
5. 仅当 dataSql 不含 `order by` 时才追加 `ctx.pageRequest().orderBy`；
6. 追加 `limit offset,size`。

### 5.3 事务

**Java**

```java
@Transactional
public int insertUser(SysUser user) { ... }
```

**C++**

```cpp
auto conn = cm::db::Db::instance().pool().borrow();
conn->begin();
try { ...; conn->commit(); }
catch (...) { conn->rollback(); throw; }
```

⚠️ 没有声明式事务；多语句写操作需显式 `begin/commit/rollback`。
✅ 隔离级别使用 MySQL 默认（REPEATABLE READ），与 Java 相同。

### 5.4 连接池

| Druid | C++ |
|---|---|
| initialSize=5 | `initial` 参数 |
| minIdle=10 | `minIdle` |
| maxActive=200 | `maxActive` |
| maxWait=60000 | `maxWaitMs` |
| validationQuery=SELECT 1 | 借出时 `ping()`（等价 `testWhileIdle` + `testOnBorrow`） |

⚠️ 探活策略略有差异：C++ 在借出时 ping 失效连接并重建；Druid 默认
`testOnBorrow=false`、`testWhileIdle=true`。对业务无影响。

---

## 6. 层 5：横切关注点

| 关注点 | Java | C++ | 一致性 |
|---|---|---|---|
| 日志 | SLF4J + Logback | `cm::log::Logger` | ⚠️ 格式接近，非逐字节 |
| 鉴权 | Spring Security 过滤器链 | `Server::dispatch` | ✅ |
| 异常 | `@RestControllerAdvice` | `ExceptionMapper` | ✅（实测 12 条全部对齐） |
| 限流 | Redis Lua `limitScript` | ❌ 未实现（控制器内可用 `RedisCache::incr` 实现） | ❌ |
| 防重复提交 | `@RepeatSubmit` + Redis | ❌ 未实现 | ❌ |
| 操作日志 | `@Log` + AOP + `sys_oper_log` | ❌ 未实现 AOP | ❌ |
| 数据权限 | `@DataScope` + 切面 | 部分（mapper 内显式拼接） | ⚠️ |
| 监控埋点 | `GlobalExceptionTraceHandler` | ❌（实测被遮蔽，无需实现） | ✅（不实现即一致） |
| 配置刷新 | `@RefreshScope` | ❌ 需重启 | ❌ |
| XSS 过滤 | `XssFilter` | ❌ 未实现（前端/网关负责） | ⚠️ |

---

## 7. 模块对照表

| Java 模块 | C++ 位置 | 状态 |
|---|---|---|
| `ruoyi-common/utils/{Date,String,Id,Ip,Json}` | `include/cm/common/utils/` | ✅ |
| `ruoyi-common/core/domain/AjaxResult` | `include/cm/common/core/domain/AjaxResult.hpp` | ✅ |
| `ruoyi-common/core/page/*` | `include/cm/common/core/page/` | ✅ |
| `ruoyi-common/exception/*` | `include/cm/common/exception/Exceptions.hpp` | ✅ |
| `ruoyi-framework/config/SecurityConfig` | `cm::web::Router::securityRule` | ✅ |
| `ruoyi-framework/security/*` | `include/cm/framework/security/` | ✅ |
| `ruoyi-framework/web/service/{Token,SysLogin,SysPermission,SysPassword,UserDetails}` | `include/cm/framework/web/service/` | ✅ |
| `ruoyi-framework/web/exception/GlobalExceptionHandler` | `cm::web::ExceptionMapper` | ✅ |
| `ruoyi-framework/config/{Druid,Redis,Kaptcha}` | `cm::config::AppConfig` + `MySqlClient` + `RedisClient` + `CaptchaUtil` | ✅ |
| `ruoyi-system/mapper/*` | `include/cm/system/mapper/` | 按切片推进 |
| `ruoyi-system/service/impl/*` | `include/cm/system/service/` | 按切片推进 |
| `ruoyi-admin/controller/{system,common,monitor}` | `src/cm/web/controller/` | 按切片推进 |
| `ruoyi-admin/controller/{base,manager,flow}` | 同上 | 见 `ENDPOINTS_INVENTORY.md` 状态列 |
| `ruoyi-quartz` | — | ❌ |
| `ruoyi-generator` | — | ❌ |

---

## 8. 启动闭环（摘要）

完整步骤见 `README_CPP.md`；最小路径：

```bash
# 1) 依赖（Ubuntu/Debian）
sudo apt-get install -y build-essential cmake libssl-dev zlib1g-dev

# 2) 构建
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j8

# 3) 测试
./build/carmonit_tests

# 4) 依赖服务（可选，docker）
docker compose up -d mysql redis

# 5) 启动
./build/car-monit-cpp --config config
# 或
./start.sh

# 6) 验证
curl -s http://127.0.0.1:9989/health
curl -i http://127.0.0.1:9989/getInfo
```

---

## 9. Java 开发人员必须警惕的 10 个非对称差异（按风险降序）

### ① 内存所有权与悬空引用（风险：极高）

Java 对象由 GC 管理；C++ 中 `ctx.req`、`Route`、`LoginUser` 都有明确生命周期。

```cpp
// ❌ 错误：捕获 ctx 的引用并在异步线程使用
std::thread([&ctx]{ use(ctx.req); }).detach();

// ✅ 正确：值拷贝需要的数据
std::string body = ctx.body().dump();
std::thread([body]{ use(body); }).detach();
```

补偿：框架内所有 handler 同步执行；不要跨线程持有 `RequestContext&`。

### ② 线程模型（风险：高）

Java 习惯“每请求一线程 + 阻塞 IO”；C++ 是固定 worker 池。一个慢 SQL 会占满一个 worker，
32 个慢请求会阻塞整个服务。补偿：设置 `CM_WORKERS`；对慢查询加索引/分页限制。

### ③ 空值与 `optional`（风险：高）

```cpp
// ❌ s 是 optional<string>，value_or("") 会把“不存在”变成“空串”
if (user->nickName.value_or("").empty()) { ... }

// ✅ 保留语义
if (!user->nickName || user->nickName->empty()) { ... }
```

### ④ 序列化字段顺序（风险：高）

`AjaxResult` 不是插入序。不要用 `Json{{"code",200},{"msg","..."}}` 手工构造响应；
统一用 `AjaxResult` / `TableDataInfo`。

### ⑤ 异常层级（风险：中高）

`CustomException` / `UserException` 不是 `ServiceException`，在 Java 中落到
`RuntimeException` 兜底（code 500）。C++ `ExceptionMapper` 复刻了这一点；**不要**
把 `CustomException` 当成 `ServiceException` 处理成自定义 code。

### ⑥ SQL 注入（风险：中高）

C++ 没有 PreparedStatement，所有值必须 `Db::lit()`。禁止：

```cpp
std::string sql = "select * from sys_user where user_name='" + name + "'"; // ❌
```

必须：

```cpp
std::string sql = "select * from sys_user where user_name=" + cm::db::Db::lit(name); // ✅
```

### ⑦ 析构函数与异常安全（风险：中）

C++ 析构函数不能抛异常；`std::terminate` 会直接杀进程。本项目资源全部用 RAII
（`std::lock_guard`、`shared_ptr` 自定义删除器）管理。

### ⑧ 编译/链接模型（风险：中）

* 新增 `.cpp` 由 `GLOB_RECURSE` 自动收集，但**新增文件后需要重新 `cmake -S . -B build`**
  （CMake 会提示 `GLOB mismatch`）。
* 头文件改动会触发依赖重编；模板错误信息很长，先看第一条 `error:`。
* 没有热部署，改完必须重新编译并重启。

### ⑨ 时区与日期（风险：中）

Java 跟随 JVM 时区；C++ 固定 `+08:00`。部署时保持 `TZ=Asia/Shanghai`。

### ⑩ `null` vs 缺省字段（风险：中低）

Jackson 默认输出 `null`；`@JsonInclude(NON_EMPTY)` 的 VO 才省略。C++ 用
`putStr/putI64`（保留 null）与 `RouterVo` 的条件写入（省略空值）分别复刻。

---

## 10. 迁移状态与后续工作

* 端点清单与逐条状态：`ENDPOINTS_INVENTORY.md`（`python3 scripts/gen_inventory.py` 重新生成）。
* 已 100% 对齐：框架层、认证链路、系统模块的登录/权限/路由。
* 按切片推进：system CRUD、common、monitor、base、manager、flow。
* 明确不迁移：Quartz、Generator、Kafka、ES、ShardingSphere、OSS、Forest、Swagger。
