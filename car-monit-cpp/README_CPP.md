# README_CPP —— 写给 Java 开发者的上手指南

本项目是 `car-monit-backend`（RuoYi 3.8.7 / Spring Boot 2.5.15 / Java 8）的 **C++20 一比一迁移**。
目标不是“重写一个类似的服务”，而是让**同一个前端、同一套接口调用、同一个数据库**无感切换。

* 行为/接口差异清单：`COMPATIBILITY.md`
* 最终差异报告（含未迁移端点按能力对账）：`FINAL_DIFFERENCES.md`
* 分层迁移说明（含 Java↔C++ 代码对照）：`MIGRATION_GUIDE.md`
* 全部 497 个端点及其迁移状态：`ENDPOINTS_INVENTORY.md`
* 一页纸速查（注解 → C++ 位置）：`QUICK_REFERENCE.md`

---

## 1. 你能在多短时间内跑起来

```bash
cd car-monit-cpp
./start.sh                 # 配置 + 编译 + 单测 + 启动（默认 Release）
# 或
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j8
./build/carmonit_tests
./build/car-monit-cpp --config config
```

启动后：

```bash
curl -s http://127.0.0.1:9989/health
# {"status":"UP","db":"UP","redis":"UP"}
```

> `db`/`redis` 为 `DOWN` 时服务仍会启动（与 Spring Boot 的容错启动一致），
> 但依赖它们的接口会返回错误。详见 §7。

---

## 2. 依赖

> 构建只需要 CMake + 一个 C++20 编译器：clone 下来无需 Conan/vcpkg、无需 OpenSSL/zlib 开发包。
> 内置实现的正确性由 `bash scripts/verify_crypto_vs_openssl.sh` 与 OpenSSL CLI 对拍证明。

| 依赖 | 版本要求 | 用途 | 安装（Debian/Ubuntu） |
|---|---|---|---|
| CMake | ≥ 3.16 | 构建 | `apt install cmake` |
| GCC / Clang | 支持 C++20（GCC ≥ 10） | 编译 | `apt install g++` |
| OpenSSL | 1.1 / 3.x | JWT HS512、Base64、MD5 | `apt install libssl-dev` |
| zlib | 1.x | PNG / XLSX 压缩 | `apt install zlib1g-dev` |
| pthread | 系统自带 | 线程池 | — |
| MySQL | 8.0（端口 **3307**） | 业务库 `carmonitdb` | `docker compose up -d mysql` |
| Redis | 6/7（端口 **6379**） | token、验证码、字典缓存 | `docker compose up -d redis` |

CentOS/RHEL：`yum install cmake gcc-c++`（zlib-devel 可选）。
macOS：`brew install cmake`。Windows：MinGW-w64 GCC 13+（或 MSVC + CMake）均可，socket 走 Winsock2 兼容层。

**无需联网**：`third_party/` 已 vendor 了 nlohmann/json（`ordered_json`）与 libbcrypt。

---

## 3. 目录结构（按 Java 包名对照）

```
car-monit-cpp/
├── CMakeLists.txt
├── config/
│   ├── application.yaml          # ↔ ruoyi-admin/.../application.yml
│   └── application-druid.yaml    # ↔ application-druid.yml（数据源）
├── include/cm/                   # 所有头文件（接口声明）
│   ├── common/                   # ↔ ruoyi-common
│   │   ├── constant/             #   Constants / HttpStatus / UserConstants
│   │   ├── core/domain/          #   AjaxResult / R / TableDataInfo / entity/* / model/*
│   │   ├── core/page/            #   PageDomain
│   │   ├── exception/            #   Exceptions.hpp
│   │   └── utils/                #   StringUtils / DateUtils / sql / IdUtils / ...
│   ├── framework/                # ↔ ruoyi-framework
│   │   ├── config/               #   AppConfig（@ConfigurationProperties）
│   │   ├── db/                   #   MyBatis-Plus 的替代：Db / MySqlClient / Row
│   │   ├── http/                 #   HttpServletRequest / Response 的替代
│   │   ├── redis/                #   RedisTemplate 的替代
│   │   ├── security/             #   Jwt / TokenService / SecurityUtils
│   │   └── web/                  #   Router / Server / Errors / ExceptionMapper
│   ├── system/                   # ↔ ruoyi-system
│   │   ├── domain/               #   SysConfig / SysNotice / SysPost / ...
│   │   ├── mapper/               #   *Mapper（手写 SQL，对应 XML）
│   │   └── service/              #   *Service
│   └── web/                      # ↔ ruoyi-admin
│       ├── BaseController.hpp
│       └── controller/{common,system,monitor,tool}/
├── src/cm/                       # 与 include/cm 一一对应的 .cpp
├── tests/main_test.cpp           # 契约单测（JSON 顺序 / JWT / 日期 / 分页 / BCrypt）
├── third_party/                  # 已 vendor 的 json / bcrypt
├── scripts/gen_inventory.py      # 扫描 Java 控制器 + C++ 路由，生成覆盖率清单
├── Dockerfile / docker-compose.yml / start.sh / start.bat
└── *.md                          # 迁移文档
```

---

## 4. 配置：YAML 一一对应

C++ 使用自带的极简 YAML 解析器，**支持 Java 配置文件的层级 key、列表与注释**，
每次启动读取 `config/application.yaml` + `config/application-druid.yaml`。

| Java（application.yml） | C++ key | 说明 |
|---|---|---|
| `server.port` | `server.port` | 默认 9989 |
| `server.servlet.context-path` | 同 | 仅用于日志，路由始终从 `/` 开始 |
| `ruoyi.name` | 同 | `/` 欢迎页文案 |
| `ruoyi.profile` | 同 | 上传根目录，**生产必须改成 Linux 路径** |
| `ruoyi.captchaType` | 同 | `math` / `char` |
| `token.header` / `secret` / `expireTime` | 同 | 头名、HS512 密钥、分钟数 |
| `spring.redis.*` | 同 | host/port/database/password/timeout |
| `spring.datasource.druid.master.*` | 同 | JDBC URL 解析出 host/port/db |
| `spring.servlet.multipart.*` | 同 | 40MB / 200MB |
| `user.password.maxRetryCount/lockTime` | 同 | 保留字段（见 `COMPATIBILITY.md`） |
| `logging.level.com.ruoyi` | 同（或 `cm.log.level`） | 日志级别 |
| — | `cm.log.dir` | 日志目录（默认 `logs`） |

### 4.1 环境变量覆盖规则

任意 key 都可以用环境变量覆盖，两种写法等价：

```
server.port        ->  CM_SERVER_PORT   或  SERVER_PORT
spring.redis.host  ->  CM_SPRING_REDIS_HOST 或 SPRING_REDIS_HOST
```

（`.` `-` `/` 转成 `_`，字母大写。）常用：

| 变量 | 作用 |
|---|---|
| `CM_CONFIG_DIR` | 配置目录，默认 `config` |
| `CM_SERVER_PORT` | HTTP 端口 |
| `CM_WORKERS` | 工作线程数（默认 32，建议 ≥ CPU×4） |
| `SPRING_REDIS_HOST/PORT/DATABASE/PASSWORD` | Redis |
| `SPRING_DATASOURCE_DRUID_MASTER_URL/USERNAME/PASSWORD` | MySQL |

### 4.2 数据源

`config/application-druid.yaml` 中的 `url` 形如：

```yaml
spring:
  datasource:
    druid:
      master:
        url: jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8
        username: root
        password: root
```

C++ 不解析 JDBC 语法，只从 `jdbc:mysql://host:port/db` 中提取 host/port/db。

---

## 5. 启动方式

### 5.1 本地

```bash
./start.sh            # Release + 单测 + 启动
./start.sh debug      # Debug 构建
SKIP_TESTS=1 ./start.sh
```

### 5.2 Docker Compose（推荐用于验证）

```bash
docker compose up -d mysql redis
docker compose --profile full up --build     # 含 app
```

`docker-compose.yml` 已设置 `TZ=Asia/Shanghai`（C++ 日期格式固定 `+08:00`，见 §7.6）。

### 5.3 作为 systemd 服务

```ini
[Service]
WorkingDirectory=/opt/car-monit-cpp
ExecStart=/opt/car-monit-cpp/build/car-monit-cpp --config /opt/car-monit-cpp/config
Environment=CM_SERVER_PORT=9989
Environment=TZ=Asia/Shanghai
Restart=always
```

---

## 6. 健康检查与自测

```bash
curl -s http://127.0.0.1:9989/health
./build/carmonit_tests        # 契约单测，全部 PASS 才算构建通过
python3 scripts/gen_inventory.py   # 重新生成端点覆盖率清单
```

`/health` 是 C++ 扩展端点（Java 侧无 actuator），返回：

```json
{"status":"UP","db":"UP","redis":"UP"}
```

---

## 7. 常见坑（按踩坑频率排序）

### 7.1 端口与 Java 冲突

Java 版和 C++ 版默认都监听 **9989**。同时启动会 `bind: Address already in use`。
用 `CM_SERVER_PORT=9990 ./build/car-monit-cpp` 或先停 Java。

### 7.2 把 `ruoyi.profile` 原样带到 Linux

`config/application.yaml` 里保留了 Java 默认值 `D:/ruoyi/uploadPath`（Windows）。
在 Linux 上请改成绝对路径（如 `/data/uploadPath`）或设置：

```bash
export CM_RUOYI_PROFILE=/data/uploadPath
```

否则上传接口会返回“上传文件失败”。

### 7.3 Redis 与 Java 混用同一个 DB

Java 用 `FastJson2JsonRedisSerializer` 写入带 `@type` 的值，C++ 写纯 JSON。
**C++ 可以读 Java 的 key，Java 读不了 C++ 的 key**。切换期请：

```yaml
spring:
  redis:
    database: 1     # C++ 用 1，Java 用 0
```

### 7.4 只复制了可执行文件，没带 `config/`

C++ 不会把配置编译进二进制。启动时按以下顺序查找：
`--config` 参数 → `CM_CONFIG_DIR` → `./config` → `../config`。
找不到时全部使用内置默认值（端口 9989、MySQL 127.0.0.1:3307、Redis 127.0.0.1:6379）。

### 7.5 响应头 `Content-Type` 的大小写

这不是 bug，是对 Java 的复刻：

* 未登录/认证失败：`application/json;charset=utf-8`（**小写**，来自 `AuthenticationEntryPointImpl`）
* Controller 正常/异常返回：`application/json;charset=UTF-8`（**大写**）

如果前端按字符串严格比较，请保持原样，不要“统一”。

### 7.6 时区

C++ 所有日期固定按 `+08:00` 格式化与解析。部署到 UTC 机器上时，
Java 版会跟随系统时区而 C++ 不会。**请设置 `TZ=Asia/Shanghai`**。

### 7.7 MySQL/Redis 没起来也能启动

为了让前端在依赖缺失时仍能拿到 JSON 错误而不是连接拒绝，服务会继续启动。
此时 `/health` 显示 `"db":"DOWN"`，登录接口返回 500。排查顺序：
`/health` → 日志 `logs/app.log` → 端口/账号。

### 7.8 验证码图片是 PNG 不是 JPEG

Kaptcha 在 Java 里输出 JPEG；C++ 自绘 PNG。`uuid`/`img`(base64) 字段不变，
浏览器 `<img :src="'data:image/gif;base64,'+img">` 靠内容嗅探仍可显示。
若网关/前端写死了 MIME 类型，需要放行 PNG。

### 7.9 大文件上传

C++ 不支持 `Transfer-Encoding: chunked` 请求体（返回 411），需要 `Content-Length`。
浏览器表单上传、curl `-F` 都带长度，正常；部分流式客户端需在网关缓冲。

### 7.10 不要“顺手修复”Java 的怪行为

例如：

* `POST /system/user` 空 body 在 Java 里是 NPE（`{"msg":null,"code":500}`），因为校验注解被注释掉；
* `CustomException`/`BaseException` 不是 `ServiceException`，统一落 500；
* `anonymous()` 是“仅匿名可访问”，已登录访问返回真实 403；
* 未知路径 + 无 token 先返回 401 而不是 404。

这些都在 C++ 中**刻意保留**，详见 `COMPATIBILITY.md` §4。

---

## 8. 调试

| 场景 | 方法 |
|---|---|
| 崩溃定位 | `cmake -S . -B build-asan -DCAR_MONIT_BUILD_ASAN=ON && cmake --build build-asan` |
| 断点 | `gdb --args ./build/car-monit-cpp --config config` |
| 日志 | `logs/app.log`，格式 `yyyy-MM-dd HH:mm:ss.SSS [LEVEL] logger - msg` |
| 慢请求 | `monitor.slow-request-threshold`（默认 3000ms） |
| 慢 SQL | `monitor.slow-sql-threshold`（默认 1000ms） |
| 路由是否存在 | `grep -n '"/system/user"' src/cm/web/controller/system/SysUserController.cpp` |
| 覆盖率 | `python3 scripts/gen_inventory.py` |

---

## 9. 新增一个接口（示例）

Java：

```java
@PreAuthorize("@ss.hasPermi('system:user:list')")
@GetMapping("/list")
public TableDataInfo list(SysUser user) { ... }
```

C++（`src/cm/web/controller/system/SysUserController.cpp`）：

```cpp
router.get("/system/user/list",
    [](RequestContext& ctx) -> ApiResponse {
        auto page = ctx.pageRequest();
        auto res = cm::db::queryPage(
            "select count(1) from sys_user where del_flag = '0'",
            "select ... from sys_user where del_flag = '0'", page);
        Json rows = Json::array();
        for (const auto& row : res.rows) rows.push_back(sysUserToJson(row));
        return BaseController::ok(BaseController::dataTable(rows, res.total));
    })
    .permi("system:user:list");
```

所有外部输入用 `cm::db::Db::lit()` 包一层，禁止字符串拼接未转义的值。

然后 `python3 scripts/gen_inventory.py` 刷新 `ENDPOINTS_INVENTORY.md`。

---

## 10. 文档索引

| 文档 | 内容 |
|---|---|
| `README_CPP.md` | 本文：构建、配置、启动、排错 |
| `MIGRATION_GUIDE.md` | 分层（运行时/路由/序列化/数据访问/横切）对照，10 类高风险差异 |
| `COMPATIBILITY.md` | 实测基线、⚠️ 差异与补偿、❌ 未迁移清单、安全语义 |
| `FINAL_DIFFERENCES.md` | **最终差异报告**：逐条 ✅/⚠️/❌ 汇总、35 条未迁移按"缺什么能力"对账、验证矩阵与复验步骤 |
| `PORTING_REPORT.md` | 工程过程记录：每一轮改了什么、怎么发现的（含 §4.1–4.6 的实机发现） |
| `ENDPOINTS_INVENTORY.md` | 497 个端点的路径/方法/权限/迁移状态 |
| `QUICK_REFERENCE.md` | 一页纸：Spring 注解/类 → C++ 位置 |
| `PORTING_GUIDE.md` | 内部约定（命名、SQL 转义、分页、异常） |
