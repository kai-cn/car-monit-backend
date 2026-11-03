# 迁移状态报告（car-monit-cpp）

> 本文件记录**当前真实状态**。旧版本描述的是 6 个 system 辅助模块的移植小结，
> 其中“无法构建 / 存在既有编译错误”的结论已过期。

## 1. 构建与运行（已验证）

| 项目 | 状态 | 证据 |
|---|---|---|
| 全量编译 | ✅ | `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build -j 8` 零错误 |
| 单元测试 | ✅ | `./build/carmonit_tests.exe` → `ALL TESTS PASSED` |
| 服务启动 | ✅ | `./build/car-monit-cpp.exe --config config`；`GET /health` → `{"status":"UP","db":"UP","redis":"UP"}` |
| 第三方依赖 | ✅ 零 | OpenSSL 与 zlib **不再是必需**（见 §3.2） |
| 跨平台 | ✅ | Windows(MinGW g++ 14.2) 与 Linux(gcc/Docker) 两条路都通 |

验证用环境：本机 MySQL 8 `127.0.0.1:3307`（库 `carmonitdb`，89 表，真实数据）、Redis `127.0.0.1:6379`。

## 2. 端点覆盖

| 指标 | 数值 |
|---|---|
| Java 端点（按 @*Mapping 注解逐条统计） | **497** |
| C++ 已注册路由（源码枚举，`方法+路径` 去重） | **533** |
| 已覆盖 | **462** |
| 未覆盖 | **35** |
| 机器校验 | `python scripts/verify_generated_sql.py` → 实体 59，异常 0；`scripts/audit_spec_keys.py` → 缺失 JSON 键 0 |
| 实机校验 | `python scripts/live_probe.py --port 9990 <路径…>`（复用 Redis 现存会话签发 token） |
| 审批流校验 | `python scripts/verify_flow_approval.py --port 9990` → 27 项断言全过 |
| 导出/下载校验 | `verify_cn_export.py` 16 项、`verify_user_excel.py` 14 项 |
| 操作日志校验 | `verify_operlog.py` 18 项 |
| 大屏校验 | `verify_bigscreen.py` 22 项（自带夹具并复原） |
| 代码生成校验 | `verify_gen.py` 31 项全过（环境恢复后已复验） |
| 模板导出校验 | `verify_template_export.py` 22 项全过（解开 xlsx 比对表头与行数） |

三个口径要分清，不要用其中一个去否定另一个：
`endpoint_coverage.py` 按注解统计 Java 侧真实分母（497）；
`gen_inventory.py` 现在只是把同一份统计渲染成表格（以前它自己扫 ruoyi-admin 一个目录，
分母停在 326，漏掉 ruoyi-quartz/ruoyi-generator 与 `GET /{id}` 形态，属于工具缺陷，已修）；
`verify_generated_sql.py` 证明的是“生成的 SQL 在真实库上跑得通”，不等于响应体一致。

### 尚未迁移（35 条，逐条给出障碍）

| 控制器 | 条数 | 障碍 |
|---|---|---|
| SysFileController | 9 | S3/MinIO 上传（SigV4）、`uploadFileEnc` 加解密、bucket 视图 |
| CarSuspiciousController | 7 | 逐行二次查询、docx/xlsx 模板导出、外部同步任务与 SHA1 签名 |
| GenController | 7 | importTable/editSave/synchDb 需 GenUtils 全量移植；preview/download/genCode/batchGenCode 需 28 份 Velocity 模板 + zip |
| CarTrackInfoController | 4 | 轨迹来自外部 HTTP（`httpSysUtilApiService`，`baseUrl=http://127.0.0.1:9901`），本机该服务未运行 |
| GeometryController | 3 | GeoServer 外部 HTTP（`hendaUrl`，公网地址不可达） |
| 3 条 import（carinfo / exceptrecord / user）+ earliest-time + tbFlow + busstest | 6 | 前 3 条需 xlsx 读取（要 INFLATE）；earliest-time/tbFlow/busstest 需外部 HTTP 或跨租户批量同步 |

已经落地的"硬骨头"（不再列为障碍，只剩实现细节）：
flow 审批三件套（跨 6 张表 + 事务，夹具实测）、CDC 8 条（只读 Redis 队列）、
大屏 8 条全部落地（`carLocation`/`carVoList`/`topTen`/`incomeStatistic` 之外，本轮又补了
`carStatistics`/`carWarning`/`exceptRecordList`，剩下的只有依赖外部服务的）、
@Log 操作日志切面（234 条规则异步落库）、
quartz 的 changeStatus/jobLog clean（DB 语义一致）与 run（❌ 明确拒绝，见下）。

> 原则：没做完的接口不会静默返回假数据。已实现的降级点都在 `COMPATIBILITY.md` 里
> 用 ⚠️/❌ 标注并给了补偿方案，未实现的端点直接 404（而不是注册一个空壳路由）。

## 3. 本轮工程性改动（为什么现在能构建）

### 3.1 可移植性兼容层
- `include/cm/common/compat/Posix.hpp`：`localtime_r / gmtime_r / strptime / timegm / statvfs / usleep` 的 Windows 替身。此前 78 个源文件里 54 个因这些符号在 MinGW 缺失而编译失败。
- `include/cm/framework/net/{Fd.hpp,Os.hpp}`：socket 抽象。Winsock 的 `SOCKET` 是 64 位、必须用 `recv/send/closesocket`、`setsockopt` 超时参数是 `DWORD`、没有 `writev`。`Server` / `RedisClient` / `MySqlConnection` 改为只用 `cm::net::*`；头文件里句柄以 `long long` 存放，避免 `winsock2.h` 污染大量翻译单元。
- `HttpStatus::ERROR` 与 Windows `<winerror.h>` 的 `ERROR` 宏冲突：用 `#undef` 保住与 Java 同名的常量，而不是改名。

### 3.2 去掉 OpenSSL / zlib 硬依赖
- `src/cm/common/utils/crypto/{Digest,Base64,Rsa}.cpp`：MD5、SHA-1、SHA-256、SHA-512、HMAC、Base64、RSA-OAEP(SHA-1 + MGF1)、SPKI/PEM 解析、CSPRNG（Linux `getrandom`→`/dev/urandom`；Windows `SystemFunction036`）。支撑 JWT HS512 与 MySQL `caching_sha2_password` 的 full-auth。
- `src/cm/common/utils/Deflate.cpp`：zlib 兼容 DEFLATE；系统有 zlib 时优先用（`CM_HAVE_ZLIB`），没有时输出合法的 stored 块。
- 正确性不自证：`bash scripts/verify_crypto_vs_openssl.sh` 与 `openssl` CLI 逐条对拍 —— 摘要/HMAC/Base64 **完全一致**，RSA-OAEP 由本实现加密、`openssl pkeyutl -decrypt` 还原成功。SHA-256/SHA-512 的 K 表按 FIPS 180-4 定义（素数立方根小数前 32/64 位）整数运算生成并与公开表核对。

### 3.3 修复路由致命缺陷
`Router::match` 原先把 `{id}` 当字面量比较，导致**所有带路径变量的接口（getInfo / remove / configKey / dict type …）全部 404**。
现在 `{var}` 匹配单个路径段（Spring 语义），字面量优先级仍高于变量段。旧测试完全没覆盖这条，现由 `tests/crud_engine_test.cpp::testRouteShape` 守住。

### 3.4 spec 驱动的 CRUD 引擎
`include/cm/framework/web/crud/CrudSpec.hpp` + `src/cm/framework/web/crud/CrudEngine.cpp`：
- WHERE 形态来自 Mapper XML：空串不进条件、`like concat('%',?,'%')`、`date_format(col,'%Y%m%d')` 区间、XML 写死的 `order by`。
- 写入语义对齐 MyBatis-Plus `BaseMapper.insert/updateById`：`null` 跳过、空串照写、自增主键交给数据库。
- 分页对齐 PageHelper：`count(0)` 包同一个 dataSql；`total==0` 时不发数据查询。
- 50 份 spec 由 `scripts/gen_crud_spec.py` 从 Java 实体（`@TableName/@TableId/@Excel/@JsonFormat/@JsonIgnore/@TableField(exist=false)`）+ XML（resultMap 列映射、`<if>`、`order by`）+ 控制器（路径/方法/`@PathVariable` 名/`@PreAuthorize`）抽取；XML 中不存在的派生属性（`uitEmpName`、`userId` 等）自动跳过。

### 3.5 测试
新增 `tests/crypto_test.cpp`（标准向量）与 `tests/crud_engine_test.cpp`（WHERE/INSERT/UPDATE/行转 JSON/路由形状）。
断言口径对齐 Java：JSON 字段声明顺序、DB `NULL` 必须输出 `null`（不能塌成 0 或 `""`）、日期三态。

## 4. 带 token 的实机验证（本轮新增，发现 4 个只看代码看不出的缺陷）

Java 应用没在本机运行，但 Redis db0 里有它写入的 **现存登录会话**，于是可以离线签发一个
等价 token，把「JWT 验签 → FastJson2 LoginUser 反序列化 → 权限拦截 → 业务处理」整条链路跑通：

```bash
TOKEN=$(python scripts/make_token.py)                       # jjwt + HS512 + Base64 密钥解码
curl -s http://127.0.0.1:9990/getInfo -H "Authorization: Bearer $TOKEN"
MSYS_NO_PATHCONV=1 python scripts/live_probe.py --port 9990 /base/cdc/status /system/user/list
```

四个缺陷只有带着真实会话打真实数据才会暴露，全部已修并补了回归断言：

| 症状 | 根因 | 修法 |
|---|---|---|
| 带合法 token 仍 401 | `decodeJavaBase64` 把不足 4 字符的尾组整组丢弃，HS512 密钥算成 18 字节；JDK 实测是 **19 字节** | 尾组补零输出（`COMPATIBILITY.md` §6.1） |
| Java 建的会话在 C++ 里读不出 | fastjson2 的缓存值不是严格 JSON：`Set["*:*:*"]`、`25367L` | 新增 `normalizeFastJson2`/`parse_cached_json`，只用于读缓存 |
| 所有列表接口 `"code":0,"msg":null` | 漏了 `BaseController.getDataTable` 统一填的 200 / 查询成功 | `TableDataInfo(list,total)` 构造即对齐（§6.3） |
| rows 少一整排键 | spec 只描述实体自有字段，Jackson 先输出的父类字段（id/createBy/…/params）全缺 | 生成器按五种父类补全；resultMap 未映射的以 `column=nullptr` 输出 null |

顺带修掉一个查询语义错误：`find_in_set(t.id, #{exceptIds})`（列在左）被实现成
`find_in_set(值, 列)`，且该属性因“不是表列”被整个丢掉条件 —— 实测 `/manager/exceptrecord/list?exceptIds=…`
从 304 条（不过滤）纠正为 1 条。

同样在这一轮补上的还有两处只有跑数据才会显形的语义缺口：
`spec` 的 insertable/updatable 原先把父类审计列一律禁写（Java 的 `insertFlowXxx` 明明写
`create_by/create_time/eps_id/del_flag`），以及列表 SQL 漏掉 XML 里 `<if>` 之外的
`where t.del_flag = '0'`（实测 `/manager/exceptrecord/list` 304→273、carinfo 248→203）。
前者是 flow 审批落库的前置条件，后者影响所有列表接口。

审批三件套另外由 `scripts/verify_flow_approval.py` 做端到端验证：造一套两节点流程
（`QODER_FLOW_` 前缀）跑完 一审→委托→二审→重复审核→撤销→中途失败回滚，27 项断言全过，
夹具自动清理；其中回滚一项验证的正是 `cm::db::Transaction` —— 把业务表名改成不存在的表之后，
先前“删节点 + 写消息 + 写申请单”必须整体撤销（前后计数一致）。

## 4.1 导出链路的实机验证（本轮，又发现 4 个"看代码不会发现"的问题）

`scripts/verify_cn_export.py`（16 条断言）与 `scripts/verify_user_excel.py`（14 条）是把
导出的 xlsx 真下载回来、用 `zipfile` 解析后再逐列比对的，因此暴露的是数据面而非形态面的问题：

| 症状 | 根因 | 结论 |
|---|---|---|
| 中文文件名导出后下载 404/`文件不存在` | MinGW `std::filesystem` 按 GBK 解释 UTF-8 路径，写盘与判存在的两条转换路径不一致 | 新增 `cm::compat::fsPath/fsUtf8`，所有落盘点统一 UTF-16（§2.11） |
| 带 token 下载 `/common/download` 403 | 这不是 bug：Java `.anonymous()` == `access("isAnonymous()")` | 保留 403，并补断言；同时把 URL 层规则的**优先级**改成 Spring 的"先命中先生效" |
| `GET /druid/index.html` 竟然放行 | `/**/*.html` permitAll 注册在 `/druid/**` denyAll 之前 | 顺序照抄 Java，单元测试固化（含 `datasource.json` 才 403） |
| `user/export` 列头是"用户昵称/用户账号" | 列名是手写猜测的，没回到 `@Excel(name=)`；`type=IMPORT/EXPORT` 也没过滤 | 22 个 `@Excel` 字段按声明序 + type 过滤重写，`readConverterExp`、`cellType=NUMERIC`、`width=16`、`dateFormat` 全部照抄 |
| `/system/user/list` 的 `dept` 恒为 null | MyBatis `<association property="dept">` 会把 `dept_id/dept_name/leader` 组装成嵌套对象，C++ 的 `mapUser` 漏了 | 按"结果集里存在的列才填"实现（`parent_id/order_num/dept_status` 在 list SQL 里没有，保持 null） |

顺带纠正一条**差点改错**的结论：无 `@JsonFormat` 的 `java.util.Date`，裸 Jackson 默认输出 epoch
毫秒，但 Spring Boot 的 `StandardJackson2ObjectMapperBuilderCustomizer` 关掉了
`WRITE_DATES_AS_TIMESTAMPS`，所以真实输出是 `2024-05-17T14:15:52.000+08:00`。
这一点用本机 `~/.m2` 里的 jackson-databind 2.11.4 + spring-web 5.3.6 +
spring-boot-autoconfigure 2.4.5 实跑确认（见 COMPATIBILITY.md §4.6），C++ 现有实现是对的。

## 4.2 `@Log` 操作日志切面（补齐 Java 最大的静默缺口）

C++ 此前**只读不写** `sys_oper_log`：Java 侧每个带 `@Log` 的写接口都会异步落一行，
缺了它，`/monitor/operlog/*` 看到的永远只是 Java 时代的旧数据。本轮补完：

- `scripts/gen_operlog_table.py` 从 Java 控制器抽取 **234** 条规则（title / `businessType`
  与 `operatorType` 的 **ordinal** / `isSave*` / `excludeParamNames` / `类全名.方法()`），
  产出 `src/cm/web/specs/OperLogTable.cpp`。解析按"方法签名 + 上方注解块"而不是固定顺序，
  因为 `SysFileController` 把 `@PostMapping` 写在 `@Log` 之上；注释掉的 `@Log`（4 处）不计。
- `cm::aspect::OperLogAspect`：在派发层的 handler 正常返回与抛异常两条路径上调用，
  单线程队列串行落库（对应 `AsyncManager` 的单线程定时器）。
  未登录与权限不足**不写**（Java 的 `getLoginUser()` 抛异常被 `handleLog` 吞掉；
  `@PreAuthorize` 在切面外层，方法根本没执行）。
- 逐条语义见 COMPATIBILITY.md §6.6；其中三处刻意偏离（入参分支记请求体而非绑定后的实体、
  multipart 记空串、异步队列有界）已标明原因。
- 踩到的两个真问题：
  1. `error_msg` 原本写入字符串 `"null"` —— Java 的 `NullPointerException#getMessage()` 是
     `null`，`StringUtils.substring(null,..)` 还是 `null`，DB 里必须是 NULL。改成
     `Failure{std::optional<std::string>}`，把"抛了异常"和"异常有没有消息"分开。
  2. 规则匹配最初是"表里第一条命中即用"，`DELETE /monitor/jobLog/clean` 会被
     `/{jobLogIds}` 抢走（Java 的 `RequestMappingHandlerMapping` 是字面量优先）。
     改为两趟：先字面量、再带 `{var}` 的模式。
- 验证：`scripts/verify_operlog.py` 做真实的新增/删除/失败三类请求再从 `/monitor/operlog/list`
  读回，18 条断言覆盖 `status/business_type/operator_type/method/oper_url/oper_ip/
  oper_location/oper_name/dept_name/oper_param(排除 password)/json_result(丢 null)`；
  另有 2 组单测（`testOperLogHelpers` / `testOperLogBuild`）覆盖纯函数与 `build()` 全分支。

## 4.3 生成器的两处实体解析缺陷（`scripts/audit_spec_keys.py` 扫出来的）

新加的审计脚本把"Java 实体字段（Jackson 会全部序列化）"与"生成 spec 实际输出的 JSON 键"逐实体对拍，
一开始报出 8 个缺失键，根因都在解析器正则上：

| 缺陷 | 影响 | 修法 |
|---|---|---|
| 字段正则要求 `private T name;`，**带初值的声明整条漏掉** | `sys_job.misfire_policy` 是真实列，却根本没进 SELECT，列表里也没有这个键；`supplementaryStatus="0"`、`number=0`、`escapedAmount=ZERO`、`flag=false` 全部缺键 | 正则收 `= 初值`，新增 `json_literal()` 映射 Java 字面量（含 `BigDecimal.ZERO`、`new ArrayList<>()`），`Field` 增加 `dflt`，非列属性输出初值而不是 null |
| 类型字符类不含 `[]`，**数组字段整条漏掉** | `SysRole.menuIds/deptIds` 两个键整个不存在 | 类型类允许 `[]`；重跑五个 area 的生成 |

关键点：Java 的 `private String x = "0";` 经过 MyBatis（不填该属性）之后仍是 `"0"`，
Jackson 就输出 `"0"`，**不能退化成 null**；只有真的没有初值时才是 null。

回归：`audit_spec_keys.py` 现在报 0 缺失；`verify_generated_sql.py` 59 份 spec 全部在真库跑通；
`/monitor/job/list` 的 `misfirePolicy` 拿到真实值 `3`（此前该列没被选中），
`/system/role/list` 出现 `flag:false, menuIds:null, deptIds:null`，
`/manager/exceptrecord/list` 出现 `supplementaryStatus:"0"`，
`/manager/confimfree/list` 出现 `number:0, escapedAmount:0`；分页 total 与修复前一致（18/3/273/3/83）。

## 4.4 大屏最后 3 条（顺带挖出两个跨接口的引擎缺陷）

`carStatistics` / `carWarning` / `exceptRecordList` 落地后，大屏 8 条全部覆盖，覆盖率 445 → **448**。
为造夹具而走的写路径，暴露了两个影响面远大于这 3 条接口的问题：

**① `IdType.ASSIGN_UUID` 的主键从来没被生成过。**
`BasePlusEntity` / `BasePlusEntityNew` / `BaseUuidEntity` 的 `id` 都是
`@TableId(value="id", type=IdType.ASSIGN_UUID)`，MP 在**客户端**生成 32 位无横线小写 UUID。
而 `buildInsert` 的规矩是"body 里没有就跳过"，于是 INSERT 少了主键列，
`POST /manager/carwarning` 直接 500。这不是这 3 条接口的问题——**所有 uuid 主键表的 add 接口都是坏的**
（此前没有任何实机写请求打到它们，所以没暴露）。修法：字符串主键且 body 未带 id 时补 `simpleUuid()`，
带了就照用户的值（对应 MP 只在 id 为 null 时生成的行为）。

**② 大屏的设备编码过滤只认 `type`，把调用方直传的 `gantryCode`/`tollCode`/`fwqbm` 丢了。**
Spring 是先按参数名绑到 `CarLocationParam`，`type` 分支只是**覆盖**其中一路。
我此前实现成"只有 type 存在时才有这三个变量"，导致 `?gantryCode=xxx` 这种直接过滤完全无效。
`carLocation`（早已"验证过"的那条）同样有此缺陷，一并修。

其余逐条对齐的点：
- `carWarning` 走 `car_warning_list` 缓存（不设 TTL），没有才按 `trackId = 今天 yyyyMMdd` 回源并写回；
  缓存里是 fastjson2 形态（日期是毫秒数），必须按实体声明序重排、日期改回 Jackson 形态再输出，
  否则键序和形态都会跟 Java 不一致。
- 告警规则链路照抄：`car_warning_rule:{userId}type1` 命中门架 + `sys_config:warning_trigger_timespan`
  分钟内 ⇒ `needToWarnStr="1"`，间隔解析失败按 Java 抛 `NumberFormatException`。
- `exceptRecordList` 每行补 `orgId`（Java 的 `find_in_set(列, 传入值)` 顺序反直觉，照抄）
  与 `supplementaryStatus`（MP 的 `@TableLogic` 会给 count 自动加 `del_flag='0'`）。

验证：`scripts/verify_bigscreen.py` 22 条断言，自带夹具（临时把一台车置在线、造一条今日预警行、
写两个缓存键），跑完全部复原，并额外断言"清理已完成 + 车辆状态已复原"。

## 4.5 GenController 的 DB 侧 8 条（实机复验被环境中断，未完成）

覆盖率 448 → **456**。已落地：`GET /tool/gen/list`、`/tool/gen/all/list`、`/tool/gen/db/list`、
`/tool/gen/column/{talbleId}`、`/tool/gen/{talbleId}`、`POST /tool/gen/getColumnList`、
`POST /tool/gen/getAllColumnList`、`DELETE /tool/gen/{tableIds}`。
剩下 7 条（preview / download / genCode / batchGenCode / importTable / synchDb / editSave 之类
需要模板引擎或 GenUtils 全量移植的）没有做，也不会在没做完时返回假数据。

照源码抄的形态细节（都不是"看着合理"能推出来的）：
- `GenTable` / `GenTableColumn` 都继承 BaseEntity ⇒ 父类 5 个可见字段先输出
  （`searchValue` 是 `@JsonIgnore`、`params` 懒加载空 Map + `@JsonInclude(NON_EMPTY)`，两者都不出现）；
  自有字段按声明序；再往后是**只有 getter 的派生属性**：
  GenTable 的 `sub/tree/crud`，GenTableColumn 的 `capJavaField/pk/increment/required/insert/edit/
  list/query/superColumn/usableColumn`。所以 `isPk`（String）和 `pk`（boolean）会同时出现在一行里。
- `selectGenTableById / selectGenTableByName / selectGenTableAll` 与列 LEFT JOIN，而 resultMap 里
  只有 `<id property="tableId">`、没有 `<collection>` ⇒ MyBatis 按 table_id 把多行折叠成一个对象，
  列字段取首行；`getInfo` 的 `info.columnName` 因此等于第一列的名字，`columns` 恒为 null。
- `columnList` 是 `new TableDataInfo()` 只 setRows/setTotal ⇒ `code:0 / msg:null`
  （和走 `getDataTable` 的列表接口不同，那才是 200/查询成功）。
- `selectGenTableColumnList` 的 `tableId != null and tableId != ''`：OGNL 把 `''` 转成 0，
  所以 `tableId=0` 时条件不生效 —— 照抄。
- `getInfo` 的返回 Map 是 `HashMap` ⇒ data 的键序是桶序，不是插入顺序 info,rows,tables。
- `deleteGenTableByIds` 是硬删除，且先删 `gen_table` 再删 `gen_table_column`。

**顺带修掉一个全局缺陷**：`information_schema` 的列标签是全大写（`TABLE_NAME`），
而 resultMap / 代码里写的是 `table_name`；MyBatis 与 JDBC 的列名匹配本来不区分大小写，
我的 `cm::db::Row` 却是精确匹配 ⇒ 所有读 information_schema 的接口拿到的是 null。
Row 现在"先精确、再小写"匹配（同名冲突保留第一个）。

⚠️ **状态未闭环**：`verify_gen.py` 首轮跑出 3 个 FAIL，定位到上面两处（大写列名、折叠逻辑）并修了，
但修完这台机器的 MySQL(127.0.0.1:3307，服务名 mysql5/mysql8，Manual 启动) 与 Redis(6379) 停了，
其余参考服务（9989/9990）也不在，**修改后没有实机复验过**。
编译与 34 项单测通过，`verify_generated_sql`/`audit_spec_keys` 不依赖这些接口。
环境恢复后要做的：`python scripts/verify_gen.py 9991 "$TOKEN"`（31 项断言，只读 + 一次打不存在 id 的
DELETE，不会破坏数据），以及重跑 `verify_bigscreen.py` / `verify_cn_export.py` 全量回归。

✅ **已闭环**：MySQL(`mysql8` 服务 / 3307) 与 Redis(6379) 恢复后重跑 `verify_gen.py` → 31 项断言全过，
两处修复（大小写列名匹配、按 table_id 折叠）实机确认。

## 4.6 生成器丢掉两类 WHERE 条件（影响所有 CRUD 列表）

做 `listCarOrgId` 时用真实数据交叉对比才发现：`/manager/exceptrecord/list?epsId=25367` 返回 273 行，
而按 eps_id 过滤应是 249 行 —— **过滤条件被静默丢掉了**。根因有两条，都在 `gen_crud_spec.py`：

1. **父类字段一律写死 `Cond::None`**。`epsId / tenantId / createBy / createTime / delFlag / sort`
   这些来自 `BasePlusEntity*` 的列在 XML 里明明有 `<if>`，生成时被当成"父类字段不过滤"处理掉了。
   现在父类字段与自有字段走同一套条件解析（eq / like / eq_notnull / find_in_set / find_in_set_col / range）。
2. **`params.beginTime` / `params.endTime` 区间条件的键写成了元组**
   （`conds[("range", "createTime")] = "range"`），而查条件时用的是 `conds.get(字段名)` —— 永远取不到，
   于是所有列表的时间区间过滤都没生效（全库 `Cond::DateRange` 出现 0 次）。改为按字段名登记。

重新生成 5 个 area 后：新增 **166 个 Eq + 2 个 EqNotNull + 4 个 DateRange** 条件；
`verify_generated_sql` 59/59 仍全通过，实机核对 `list?epsId=25367` 249 行、不带条件 273 行，
`listCarOrgId` 与 `list` 在同一 epsId 下总数一致。

顺带一条本轮新代码里就暴露的问题：新写的手写 SQL 少拼了一个空格（`...dept_idWHERE 1=1`），
`verify_template_export.py` 直接把 0 行抓了出来 —— 但**为什么是 0 行而不是 500**？因为引擎与多数手写
控制器的 `run()` 把"查询失败"吞成空结果，而 Java 是 `BadSqlGrammarException` → code 500。
本轮把模板导出这条路径改成失败即抛（与 Java 一致）；引擎级别的同一偏离记在 COMPATIBILITY.md §2.12，
待后续统一处理（改动面波及所有手写控制器，需要单独一轮）。

新增 6 条端点：`GET /manager/exceptrecord/listCarOrgId`、`GET /manager/exceptrecord/exportOrgId`、
`GET /manager/confimfree/exportConcernedList`、`GET /manager/confimfree/exportCarStatics`、
`GET /manager/aduitfree/exportIncomeStatics`、`GET /manager/aduitfree/exportIncomeDetailList`。
模板导出按 easypoi 的 `{{$fe:entitylist ...}}` 标记行取列，响应是
`application/octet-stream;charset=UTF-8` + `Content-Disposition: attachment` 的裸 xlsx 字节
（Java 方法 `return null`，所以不包 AjaxResult）；⚠️ 模板的标题行/两级表头/合并单元格/样式不复刻。

## 5. 已知行为差异（完整清单见 COMPATIBILITY.md）

- ✅ Excel **导出**已是真 `.xlsx`（自研 OOXML，`python zipfile` 独立校验过），响应形态、文件名
  规则、列集合（`@Excel(type=)`）、列序、列宽、数字/文本单元格、`readConverterExp` 全部对齐 Java；
  模板导出（`importTemplate`）同样落真文件。
- ✅ **操作日志切面（`@Log`）已实现**：234 条规则由 `scripts/gen_operlog_table.py` 从 Java 源码抽取，
  `cm::aspect::OperLogAspect` 按 `LogAspect` 的语义（枚举 ordinal、`getRequestURI` 不含 query、
  `IpUtils.getIpAddr` 口径、参数三分支、fastjson2 丢 null、按字符截断、未登录不写、
  权限不足不写）在派发层记录，单线程异步落 `sys_oper_log`。逐条对照与三处刻意偏离见
  COMPATIBILITY.md §6.6。
- ❌ Excel **导入**仍未实现：`POST /system/user/importData` 一类接口显式返回错误，不伪装成功。
- ⚠️ 无 zlib 时验证码 PNG 不压缩（约 10KB），解码结果一致。
- ⚠️ Windows 本地开发机上 `std::filesystem` 按 GBK 解释窄路径，中文文件名会失败；
  已由 `cm::compat::fsPath/fsUtf8` 在所有落盘点解决（COMPATIBILITY.md §2.11）。
- ❌ Kafka/CDC、Elasticsearch、MinIO、Quartz 集群锁：C++ 侧无对应实现。
- ❌ 未迁移接口按 §2 表列出，**不会静默返回假数据**（未注册即 404）。
- ✅ 照抄的 Java 缺陷：`GET /base/tollStationIp/list` 因 XML `order by t.big_id`（列不存在）在 Java 侧本来就 500，C++ 保持一致；出处记在 `scripts/verify_generated_sql.py` 的 `EXPECTED_SQL_ERRORS`。
- ✅ 照抄的 Java 安全语义：`anonymous()` == `isAnonymous()`，带 token 访问 `/common/download**`
  与 `/system/notice/view/**` 是真实 HTTP 403（容器 `/error` 形状），不带 token 才放行。

## 6. 下一步（按性价比排序）

1. SysFileController 9：S3 SigV4 上传（HMAC-SHA256 已具备），再做 `uploadFileEnc`。
2. GenController 15：先做只读的 list/db/list/column/getTableDetail，代码生成部分需要一个
   Velocity 等价模板渲染器 + zip（DEFLATE 已在库内，zip 写出器本轮已为 xlsx 落地）。
3. xlsx **读取器** + `importUser` 校验，解掉 `importData` 一类导入接口。
4. 大屏剩余 8 条里，`carLocation`（Redis 车辆列表 + DB 回源）与 `topTen` / `incomeStatistic` /
   `carVoList`（Mapper 里的统计 SQL）共 4 条不需要外部依赖，应先补这 4 条；另 4 条才真正受
   外部服务限制，逐条异常边界见 `COMPATIBILITY.md` §5.1。
5. 要让外部 HTTP 类接口可用，缺的只是一个出站 HTTP/1.1 客户端：`cm::net` 已有
   `connectTcp(host, port, connect_timeout)` / `setTimeout` / `readSome` / `writeAll`，
   足够实现带超时与响应上限的 GET/POST，不必引 libcurl。
6. quartz 的 `run` 与 `changeStatus` 的调度侧效应：需要一张"任务名 → C++ 函数"的注册表，
   否则反射调 bean 这条路在 C++ 里无法等价（当前 run 明确返回未实现，不假装成功）。
7. 把 `Transaction` 用到已有的多表写路径上：sys_user 新增/修改（user_role）、
   sys_role 修改（role_menu）、sys_dept/menu 的级联，Java 都是 @Transactional。
