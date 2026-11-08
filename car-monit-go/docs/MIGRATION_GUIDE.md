# car-monit 后端 Java → Go 迁移指南

> 目标：在保留原有 HTTP 接口、响应结构和业务语义的前提下，把 Spring Boot 单体迁移到 Go。
> 本文档对应 `java-to-go-refactor-prompt.md` 的交付要求：启动/验证章节、Java 开发者速查、关键差异说明。
> 全局类映射与控制器清单见 [MAPPING.md](./MAPPING.md)。

## 1. 快速启动

### 1.1 环境要求

| 依赖 | 版本/地址 | 说明 |
|---|---|---|
| Go | 1.24+（模块声明 `go 1.24`） | 迁移规范以 Go 1.26 为生产目标；当前构建机为 Go 1.24.1，故未使用 1.25+ 新语法。升级工具链后可将 `go`/`toolchain` 提升到 1.26 |
| MySQL | `127.0.0.1:3307/carmonitdb`，root/root | 与 `application-druid.yml` 一致 |
| Redis | `127.0.0.1:6379`，db 0 | 登录态、验证码、限流、防重键 |

本地依赖可用 `docker-compose.yml` 启动（MySQL 映射 3307、Redis 6379）：

```bash
docker compose up -d
# 首次需导入表结构与数据：
mysql -h127.0.0.1 -P3307 -uroot -proot carmonitdb < carmonitdb.sql
```

### 1.2 命令

```bash
cd car-monit-go

# 依赖（首次或更新后）
go mod tidy

# 编译 / 静态检查
go build ./...
go vet ./...

# 启动（默认读取 configs/config.yaml）
go run ./cmd/server -c configs/config.yaml
# 或
go build -o bin/server ./cmd/server && ./bin/server -c configs/config.yaml
```

启动成功日志：

```
level=INFO msg=服务启动 addr=:9989 config=configs/config.yaml
```

### 1.3 配置

- 配置结构与 `application.yml` 键一一对应，见 `configs/config.yaml` 与 `internal/config/config.go`。
- `database.master.dsn` 为 Go 原生连接串；未填写时由 `database.master.{host,port,username,password}` 拼接。
- 环境变量覆盖（优先级高于 YAML）：
  - `CARMONIT_CONFIG`：配置文件路径
  - `CARMONIT_SERVER_PORT`
  - `CARMONIT_DATABASE_DSN`
  - `CARMONIT_REDIS_ADDR` / `CARMONIT_REDIS_PASSWORD`
  - `CARMONIT_TOKEN_SECRET`
  - `CARMONIT_KAFKA_BOOTSTRAP_SERVERS`
  - `CARMONIT_WORKER_ID` / `CARMONIT_DATACENTER_ID`：雪花 ID 机器位（0~31，见 §1.7）
- 注意：`logging.level.com.ruoyi` 这类含点号键会被 Viper 解析为嵌套 map，`internal/logx` 会递归读取并取最详细级别（debug > info > warn > error）。

### 1.4 验证清单

1. **探活**（Go 新增端点）：

   ```bash
   curl -s -w '\nHTTP %{http_code}\n' http://127.0.0.1:9989/healthz
   # {"code":200,"msg":"UP","data":{"database":"UP","redis":"UP","version":"3.8.7"}}
   # HTTP 200
   ```

   DB 或 Redis 不可用时返回 `{"code":500,"msg":"DOWN",...}` 且 **HTTP 503**，
   便于容器编排直接重启坏实例（Java 侧没有该端点，属 Go 新增）。

2. **验证码**：

   ```bash
   curl -s http://127.0.0.1:9989/captchaImage
   # {"msg":"操作成功","code":200,"uuid":"...","img":"<base64 JPEG>"}
   ```

   `img` 与 Java 一致为裸 Base64（前端自行拼 `data:image/gif;base64,`）。

3. **登录**（验证码为空时按 Java 逻辑跳过校验；密码策略在进入登录服务前生效）：

   ```bash
   curl -s -X POST http://127.0.0.1:9989/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"<满足策略的密码>","code":"","uuid":""}'
   # {"msg":"操作成功","code":200,"token":"<jwt>"}
   ```

4. **用户信息 / 路由**：

   ```bash
   TOKEN=<上一步 token>
   curl -s http://127.0.0.1:9989/getInfo -H "Authorization: Bearer $TOKEN"
   curl -s http://127.0.0.1:9989/getRouters -H "Authorization: Bearer $TOKEN"
   ```

5. **业务接口**：使用前端或 curl 调用对应模块路径（见 MAPPING.md 第 3 节）。
6. **登出**：`POST /logout`（携带 token），再次访问 `/getInfo` 应返回 `code=401`。

### 1.5 全量接口验证结果（admin 登录，MySQL 3307 + Redis 6379）

以启动日志里的路由表为基准逐条调用（脚本：`verify_final.py`，报告 `verify_final_report.json`）：

| 项 | 数量 | 说明 |
|---|---|---|
| 注册路由 | 499 | `go build` 后 gin 输出的全量映射 |
| GET 与只读接口返回 `code=200` | 289 | 列表/详情/统计/字典/缓存/监控等 |
| 导出与下载（二进制流/落盘文件名） | 26 | xlsx 附件流与 ExcelUtil 文件名信封 |
| 预期业务响应（校验失败、无数据、外部依赖 DIFF） | 155 | 含用畸形请求体探测的写接口，确保不改动数据 |
| 路由缺失 / 404 / panic | 0 | 无 404、无未捕获 panic |
| 与 Java 同源的 SQL 缺陷 | 13 | 见下表，不是 Go 侧引入 |

已知与 Java 行为一致的缺陷（照抄，不做「顺手修正」）：

| 接口 | 现象 | 根因 |
|---|---|---|
| `DELETE /base/{section,toll,gantry,org,fwqjcxx,sfsjcxx,sfzjcxx,geometry}/:ids` | `Unknown column 'del_flag'` | 生成器模板对所有表都写 `update ... set del_flag = '1'`，而这些 ODS/DWD/geometry 表没有 `del_flag` 列；Java 同样报错 |
| `/system/upgradeInfo/**` | `Table 'carmonitdb.sys_upgrade_info' doesn't exist` | 当前库缺少升级信息表（环境未导入该 DDL） |
| `GET /flow/messageinfo/exportShrz`、`DELETE /flow/flowtemplate/:ids` | `code=500 msg=系统异常` | Java 对空主数据直接 NPE，Go 保留同一落点（见 flow 包 `// DIFF:`） |

`GET /base/tollStationIp/list` 是唯一「照抄即 500」被主动修掉的接口：Java XML 的 `order by t.big_id` 指向不存在的列，Go 侧改为 `t.id` 并在 `specs.go` 写了 `// DIFF:` 说明。

### 1.6 与 Java 返回体逐字段对比（2026-11-02）

> 第三轮已在「共用 MySQL + **两端不同 Redis DB**（Java=db0 / Go=db2）」的设定下重跑，
> 路由覆盖、GET 288 条、写 32 资源的完整结果与本轮新发现的 5 项修复见
> **`docs/PARITY-2026-11-02.md`**；校验脚本在 `scripts/parity/`。下面两小节是前两轮记录。

以 Java 服务（9988）为基准，对 Go 服务（9989）做归一化后的深度逐字段比较（脚本 `cmp_api.py`，报告 `recheck*.json`，明细见 `docs/PROGRESS.md`）。

GET 响应：

| 模块 | GET 路由 | 完全一致 | 仍有差异 | 非 JSON/二进制 |
|---|---|---|---|---|
| `/manager/**` | 99 | 79 | 0 | 20 |
| `/base/**` | 70 | 57 | 8 | 5 |
| `/flow/**` | 30 | 30 | 0 | 0 |
| `/system/**` | 65 | 60 | 4 | 1 |
| `/monitor/**` | 13 | 10 | 3 | 0 |
| `/tool/**` | 10 | 10 | 0 | 0 |
| 合计 | 287 | 246 | 15 | 26 |

写接口（`cmp_crud2.py`：两端各插一条 `PARITY_*` 记录，比 POST/详情/PUT/DELETE 四步响应，结束后按标记硬清理）：
32 个资源里 **24 个四步全一致**，其余 8 个的差异全部来自 Java 侧写入路径本身不可用（`IdType.INPUT` 主键未生成、
`POST /system/user` 因 SQL 日志拦截器把 BCrypt 串当正则替换而必然抛 `No group 2`、引用库里不存在的列等）。

Redis 共存（`internal/cache/fastjson.go` + `internal/cache/javatypes.go`）：

- Java 的缓存值是 FastJson2 `WriteClassName` 格式（`@type`、`25367L`、`Set[...]`、`{"@type":"java.util.HashMap"}`、null 成员不写）。
  Go 写标准 JSON 时，Java `getCacheObject` 得到 `JSONObject`，强转业务类型即 `ClassCastException`
  —— 这就是 `/monitor/online/list`、`/manager/bigScreen/carLocation` 在并行比对时 500 的根因，已修复
- 写入统一走 `Cache.SetJava/SetJavaString`，读取走 `Cache.Get/ListJava/GetStringJava`（容错解码 Java 原值）
- `login_tokens:*` 补齐 Java 才有的 `username`、`user.password` 与 fastjson2 的 `loginDate` 写法；
  `web.DateTime`/`ISODateTime` 额外接受裸毫秒时间戳（Java 老会话形态）
- 验收结果：两端在线列表 96/96 条且 tokenId 集合一致；Go 刷新的 `car_list` 等 Java 读得回；`sys_config`/`sys_dict` 双向可读

剩余 GET 差异全部属于「外部依赖不可复现」或「Java 自身缺陷」，逐条原因见 `docs/PROGRESS.md` §4，主要包括：
- 路网几何（`raodTrailList`）、恒达桩号转经纬度、外部 9901 费用服务等未迁移的外部依赖
- Java 侧框架/库缺陷：`sys_upgrade_info`/`geometry_copy1` 表缺失、`jobLog/{id}` 缺少路径变量、`/monitor/server` 的 JNA 版本冲突
- 26 项 Excel/Word/图片附件流：POI/EasyPOI 与 excelize 的二进制不可能逐字节一致（表头、列顺序、文件名信封已对齐）

实现要点（详细清单见 `docs/PROGRESS.md` §3）：响应信封与 `data` 键语义、`id`/`password`/`salt` 等可空字段、
三态日期（`yyyy-MM-dd` / `yyyy-MM-dd HH:mm:ss` / Jackson 默认 ISO-8601）、Jackson 派生属性（`admin`/`default`/`children`）、
各 Mapper XML 的投影列与排序，以及 MyBatis-Plus `insertFill/updateFill` 的审计字段边界（insert 不写 `update_by`/`update_time`）。

### 1.7 数据接入边界与实例标识（2026-11-08 加固）

**① 数据接入已接线（2026-11-08 更新）。** Kafka 消费、MySQL 月度分表写入、ES 索引、分表预创建、
`vehicleMonitoringTask` / `snapshotFlowSyncTask` 均已实现，入口见
[MAPPING.md §4](./MAPPING.md#4-消息队列--搜索引擎--分表)。

| 能力 | 开关 | 行为 |
|---|---|---|
| Kafka → 分表 + ES | `kafka.enabled` | 启动消费者；未启用时日志提示“接入仍由 Java 承担” |
| ES 索引 | `elasticsearch.enabled` | 只由 Kafka 消费链路与 ES 客户端写；关闭时跳过 |
| GaussDB 同步 | `snapshot.flow.sync.enabled` + `source` | `source=http` 走 vehicleMonitor HTTP 适配层；`disabled` 时任务返回明确错误 |
| 分表预创建 | `shardingTableTask.*` / `snapshotFlowSyncTask.preCreateTables(n)` | 由 sys_job 配置触发（Java 的 `@Scheduled` 因缺 `@EnableScheduling` 从未生效） |

Kafka 消费开关示例（`configs/config.yaml`）：

```yaml
kafka:
  enabled: true
snapshot:
  flow:
    sync:
      enabled: true       # 仅影响同步任务，不阻塞 Kafka 消费
      source: http        # http | disabled
      base-url: ""        # 空则回退 vehicleMonitor.baseUrl
      page-size: 1000
      workers: 4
```

未配置 Redis 时消费者仍可启动，但会打印“失去幂等保护”的告警；生产环境必须先确认 Redis 可用。
GaussDB / ES / `section_list` 的未验证点见 MAPPING §4.1，联调前不要下线 Java 数据接入实例。

`unmigratedTargets` 现在只剩 `trackTask.syncHistoryTrack`（依赖 `ICarTrackInfoService`/`IGeometryService`），
保存该任务仍会直接被拒绝：

```
任务 trackTask.syncHistoryTrack 尚未迁移到 Go 版本（历史轨迹同步依赖 ...）；
该能力仍由 Java 数据接入服务承担，请在 Java 侧配置或等待后续版本
```

**② 多副本必须区分雪花 ID 机器位。** `sys_*.id` 与业务表的 19 位主键由
`internal/idgen` 生成（与 MyBatis-Plus `IdWorker` 位宽一致：41 位毫秒 + 5 位机房 + 5 位机器 + 12 位序列）。

| 配置项 | 环境变量 | 默认 | 说明 |
|---|---|---|---|
| `instance.worker-id` | `CARMONIT_WORKER_ID` | -1（按主机名哈希） | 0~31；多副本必须唯一 |
| `instance.datacenter-id` | `CARMONIT_DATACENTER_ID` | -1（回落 0） | 0~31；跨机房部署时区分 |

启动时会打印实际生效的标识与来源：

```
level=INFO msg="雪花 ID 实例标识" workerId=7 datacenterId=0 source=hostname
```

- 单实例：保持 -1 即可（主机名推导稳定）。
- 多副本：**必须**为每个副本显式设置不同的 `CARMONIT_WORKER_ID`（或不同的组合），
  否则同一毫秒内可能生成重复主键，表现为插入时 `Duplicate entry`。
- 取值范围越界会在配置校验阶段直接启动失败，而不是运行期才暴露。

### 1.5 常见问题

| 现象 | 原因/处理 |
|---|---|
| `连接 MySQL 失败: dial tcp 127.0.0.1:3307 ... refused` | MySQL 未启动或端口不是 3307；改 `database.master.dsn` |
| `初始化 Redis 失败` | Redis 未启动；改 `redis.host/port` |
| 启动即报 `unmarshal config` | 配置键类型不匹配；对照 `internal/config/config.go` |
| 所有业务接口 401 | 确认 `Authorization: Bearer <token>`，且 Redis 中 `login_tokens:<uuid>` 未过期 |
| 验证码校验失败 | 验证码 2 分钟过期且校验一次即删除；`math` 类型答案是算式结果 |

## 2. Java 开发者速查

### 2.1 概念对照

| Spring / Java | Go | 说明 |
|---|---|---|
| `@RestController` + `@RequestMapping` | `router.RegisterModule` 中显式注册 | `internal/modules/*/register.go` |
| `@Autowired` 字段注入 | 构造参数注入（`*app.App`） | `app.New` 显式装配 |
| `@RequestBody` | `c.ShouldBindJSON(&req)` | 解析失败返回业务错误 |
| `@RequestParam` / `@PathVariable` | `c.Query("x")` / `c.Param("id")` | 查询参数可用 `ShouldBindQuery` 绑定结构体 |
| `@PreAuthorize("@ss.hasPermi('x')")` | `middleware.Perm("x")` | 支持 `*:*:*` 超级权限 |
| `SecurityUtils.getLoginUser()` | `auth.CurrentUser(c)` | 登录态存 `gin.Context` |
| `SecurityUtils.getUserId()` | `auth.CurrentUserID(c)` | |
| `AjaxResult.success(data)` | `web.SuccessData(data)` | HashMap 键序已复刻 |
| `BaseController.getDataTable(list)` | `web.Table(rows, total)` | 分页由调用方显式 count |
| `R.ok(data)` / `R.fail(msg)` | `web.ROK(data)` / `web.RFailMsg(msg)` | 部分 ODS/流程接口使用 |
| `ServiceException` | `*web.ServiceError`（`web.NewServiceError`） | 统一由 `web.ErrorResult` 转 200+code |
| `PageHelper.startPage` | `pd := web.Page(c)` + count/limit SQL | 仅当 `pageNum` 与 `pageSize` 同时存在才分页 |
| `SecurityContextHolder` | `context.Context` + `gin.Context` | 不跨 goroutine 传递 gin.Context |
| `@Transactional` | `a.DB.Transaction(func(tx *gorm.DB) error {...})` | 多写操作显式事务 |
| `@Cacheable/@CacheEvict` | `a.Cache.Get/Set/Delete/Keys` | 键名保持 Java 常量 |
| `AsyncManager.execute` | `go func(){ ctx, cancel := context.WithTimeout(...) }()` | 后台任务必须自带超时 |
| `ExcelUtil.exportExcel` | `excelize`（`internal/modules/*` 内） | 列定义显式写出 |
| `IpUtils.getIpAddr` | `auth.ClientIP(c)` | X-Forwarded-For → X-Real-IP → RemoteAddr |
| `Date` + `@JsonFormat` | `web.DateTime` | JSON 形如 `2024-01-01 12:00:00` |
| SLF4J + MDC | `slog` + `logx.WithTrace` | traceId 由 `middleware.TraceID` 注入 |

### 2.2 分层约定

```
cmd/server/main.go          启动、依赖装配、优雅停机
internal/config             配置加载（application.yml 对应）
internal/database           连接池（Druid 对应）
internal/cache              Redis（RedisCache 对应）
internal/auth               登录、JWT、权限装载、验证码
internal/middleware         认证、权限、XSS、CORS、限流、防重、操作日志
internal/web                AjaxResult / TableDataInfo / R / 分页 / 错误
internal/model              共享实体（sys_user、sys_role 等）
internal/service/menusvc    菜单树与 RouterVo
internal/handler            认证与核心端点（login/getInfo/getRouters/captcha）
internal/modules/<域>        业务控制器 + 服务 + SQL
internal/router             路由注册表
```

业务模块新增步骤：

1. 在 `internal/modules/<域>` 下实现 `Register(reg *router.Registry)`，文件内 `func init(){ router.RegisterModule(Register) }`；
2. 在 `cmd/server/main.go` 增加空导入：`_ "car-monit-go/internal/modules/<域>"`；
3. 每个 Go 文件头写 `// JAVA 对照:`，有行为差异写 `// DIFF:`。

### 2.3 权限与匿名路径

- 匿名路径与 `SecurityConfig` 对齐：`/login`、`/captchaImage`、`/common/download**`、`/system/file/view/**`、`/system/notice/view/**`、`/manager/suspicious/syncSuspiciousCarTask`、静态资源等（见 `internal/middleware/security.go`）。
- 匿名端点若需要读取登录用户（如文件下载记录操作人），仍会尝试解析 token，但不会因缺少 token 而拒绝。
- 权限中间件挂载位置与 URL 直接决定鉴权，务必对照 Java 的 `@PreAuthorize`。

### 2.4 调试与排查

| Java 手段 | Go 对照 |
|---|---|
| 断点/远程调试 | `dlv debug ./cmd/server`（Delve）；VS Code/GoLand 直接附加 |
| `jstack` / 线程转储 | `kill -QUIT <pid>` 或用 Delve 查看 goroutine；`net/http/pprof` 可按需引入 |
| `-XX:+HeapDump` | `go tool pprof` + `runtime/pprof`；`GODEBUG=gctrace=1` 观察 GC |
| JUnit | `go test ./...`；并发问题加 `-race` |
| 接口调试 | `curl` 或前端；错误响应固定为 HTTP 200 + `code` |
| 日志排查 | `slog` 文本日志按时间/键值检索；traceId 由 `X-Trace-Id` 透传 |

### 2.5 响应与错误

- 除文件下载/上传、Excel 导出外，所有接口 HTTP 状态均为 200，业务状态看 `code`。
- 401/403 也走 200 + code，消息分别对应 `AuthenticationEntryPointImpl` 与 `AccessDeniedException`。
- 业务错误优先返回 `*web.ServiceError`；只有系统级错误才记录 `Error` 日志。
- 禁止 `panic` 处理业务错误；`middleware.Recovery` 仅兜底未预期 panic。

## 3. 关键行为差异（DIFF 汇总）

| 领域 | Java | Go | 影响 |
|---|---|---|---|
| 密码重试锁定 | `SysPasswordService` 从未被注入使用 | 不实现 | 行为一致（Java 实际也无锁定） |
| 验证码图片 | Kaptcha JPEG（AWT 字体） | 点阵字体 JPEG | 前端协议不变；样式不同 |
| 验证码 UUID | `IdUtils.simpleUUID()` | `uuid.NewString()`（带连字符） | 仅内部标识，无兼容要求 |
| 数据库访问 | MyBatis + PageHelper 拦截 | 原生 SQL + 显式 count/limit | 分页语义保持一致（双参数才分页、上限 500） |
| 多数据源 | `@DataSource` 切换 | 单主库（从库配置保留） | 现有代码未实际使用从库 |
| 定时任务 | Quartz（含集群/错过策略） | robfig/cron/v3 | 6 段 cron 近似；错过策略简化 |
| 文件存储 | 本地 `ruoyi.profile` | 同上 | 一致 |
| IP 归属地 | ip2region 离线库 | 内网识别，其余为空 | 登录日志「登录地点」可能为空 |
| Excel | EasyExcel / EasyPOI 模板 | excelize 显式列 | 列顺序/表头保持一致；模板排版与 Word 图片不逐像素复刻 |
| 外部轨迹服务 | `HttpSysUtilApiService` 远端查询 | 未接入 | `/manager/cartrackinfo/listByCarId` 本地无数据时返回空列表；`carSnapShot` 返回空 data |
| 基础数据收费接口 | Forest 调用 `vehicleMonitor.baseUrl` | `net/http` 反向代理同名路径 | `/base/feerecords`、`/base/feeGantry`、`/base/feestationexit` 依赖上游 9901 服务 |
| 几何同步 | HenDa 外部接口 | 返回 DIFF 提示，不做外呼 | `/base/geometry/getHenDa`、`syncAllGeometry*` 不落库 |
| 快照流水分表 | ShardingSphere/MyBatis 月表 | 原生 SQL 拼月表名 | 跨表分页与 `TABLE_ROWS` 计数按 Java 语义实现 |
| Flow SQL 别名 | camelCase 别名 + resultMap | snake_case 别名 + gorm 标签 | JSON 字段名不变；`@Excel` 转换表达式格式异常处保留原值 |
| 轨迹几何/设备统计 | 路网 Geometry + TrailDevBO | 返回空数组/0 | `changeTrailInfo`、`carLocation` 等仍返回完整轨迹点，仅缺路网叠加 |
| 图片证明材料 | Word 模板嵌入图片 | 纯文本 docx | `exportAbnormalPassage` 下载协议一致，内容简化为关键字段 |
| CORS | 反射 Origin + credentials | 相同 | 无变化 |
| 操作日志 | AOP 切面 + AsyncManager 线程池 | 显式路由中间件 + 固定 2 worker / 1024 队列 | 需在注册路由时选择是否挂载；超过 2000 字节的请求/响应只截断不完整落库，文件流不采集 |
| 事务边界 | `@Transactional` 方法级代理 | `db.Transaction` 显式包裹 | 用户/角色/部门/字典/流程/任务/可疑车辆核实/异常流水/代码生成已对齐；新增多写逻辑必须显式加事务 |
| 权限与审计 | `@PreAuthorize` / `@Log` 注解 | `middleware.Perm` / `middleware.OperLog` | 2026-11-08 已逐条对齐 manager 手写控制器；Java 中被注释的注解（如 `/manager/suspicious/check`）仍不挂 |
| 雪花 ID | MyBatis-Plus `IdWorker`（MAC/进程推导） | `internal/idgen`（配置/主机名推导） | 多副本必须设置唯一 `CARMONIT_WORKER_ID`，见 §1.7 |
| 未迁移的数据接入任务 | 保存成功、执行时报错 | **保存阶段直接拒绝** | 有意偏离：避免“保存成功但永不成功”的假象 |
| Kafka/ES | Spring Kafka / ES Client | 已接线（`kafka.enabled` 控制） | 分表写失败不再静默 ack：本地重试 3 次后进死信队列；ES 失败仍只告警（同 Java），见 §1.7 与 MAPPING §4 |
| 分表路由 | ShardingSphere 按 `snapshottime` 自动路由 | 按月份直接计算物理表 | 语义等价；不再依赖逻辑表与分片配置 |
| 分表写入幂等 | 裸 INSERT（重复即失败） | `ON DUPLICATE KEY UPDATE big_id=big_id` | 有意偏离：让 Kafka 重试与重叠同步安全 |
| 分表创建 | 依赖 ShardingTableTask 预创建 | 写入前按需 `CREATE TABLE ... LIKE` | 防止跨月首条消息因表不存在丢数据 |
| `section_list` 缓存 | `rightPushAll`（不删除旧值） | 先 DEL 再 RPUSH | 修复 Java 侧每日同步无限追加的问题 |
| 死信消息 | `{originalTopic,partition,offset,timestamp,reason,value}` | 相同信封 | 补 reason 字段，便于人工排查 |
| 健康检查 | 无 | 新增 `/healthz`，DOWN 时 HTTP 503 | 仅新增，不影响既有接口 |

## 4. 迁移进度

| 范围 | 状态 |
|---|---|
| 基础设施：配置/日志/数据库/Redis/JWT/验证码/权限/分页/响应信封 | 已完成，`go build`、`go vet` 通过 |
| 认证核心：`/login` `/logout` `/getInfo` `/getRouters` `/captchaImage` `/` | 已完成 |
| 系统管理：用户/角色/菜单/部门/岗位 | 已完成 |
| 系统辅助：参数/字典/公告/个人中心/首页菜单/文件/升级信息 | 已完成 |
| 监控与工具：缓存/服务器/登录日志/操作日志/在线用户/通用上传下载/代码生成测试 | 已完成 |
| 定时任务：Quartz 控制器与任务 | 已完成 |
| 车辆监管：20 个 manager 控制器 + 大屏 | 已完成（含 admin 登录联调） |
| 数据接入：ODS/DWD 基础数据与快照流水（26 控制器） | 已完成（含 list/detail/export 联调） |
| 流程：7 个 flow 控制器（55 个映射） | 已完成（含申请→委托→审批链路测试） |
| Kernel/数据接入：Kafka 消费 / ES 索引 / 月分表写路径 | 已接线（默认关闭 Kafka），离线单测覆盖路由/幂等/重试；真实 Kafka/ES/GaussDB 未联调 |
| 定时任务：`vehicleMonitoringTask` / `snapshotFlowSyncTask` / `shardingTableTask` | 8+6+2 个方法已注册为任务 Bean；`trackTask.syncHistoryTrack` 仍拒绝 |

> 各模块完成后，本表状态与实际 `internal/modules/**` 目录、路由清单同步更新；未完成的接口不会静默返回假数据。

## 5. Java 退役后的清理清单

双端共存期为了“逐字节/逐格一致”引入了若干兼容层，Java 服务下线后可按下列顺序清理（每步都有测试或对拍兜底）：

| 兼容层 | 位置 | 退役动作 |
|---|---|---|
| HashMap 桶序序列化 | `internal/web/javamap.go` | 删除，`AjaxResult` 改普通 struct（前端不依赖键序） |
| Fastjson2 缓存格式 | `internal/cache/fastjson.go` | 删除 `ToJava/SetJava` 路径，改回 `encoding/json`；保留 `FromJava` 一个版本消化历史键 |
| POI 单元格怪癖 | `internal/excelx/cell.go` | 只保留 Excel 必需规则；删除非法字符落 `?`、`= - + @` 补 TAB 等对拍规则 |
| 错误消息的 Java 原文 | `internal/web/errors.go`、各模块 | 逐步替换为业务化文案；`msg` 变化会影响前端提示，需同步前端 |
| JSON 键序 / 字段语义的 `DIFF` 注释 | 全仓库 300+ 处 | 保留关键差异说明，删除纯对拍用途的注释 |

**清理前置条件**：至少一个完整回归周期内不再需要与 Java 双端比对（`scripts/parity/**` 全部停用），
且前端已完成一次联调。
