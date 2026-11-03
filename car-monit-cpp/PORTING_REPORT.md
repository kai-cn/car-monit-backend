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
| C++ 已注册路由（源码枚举，`方法+路径` 去重） | **504** |
| 已覆盖 | **433** |
| 未覆盖 | **64** |
| 机器校验 | `python scripts/verify_generated_sql.py` → 实体 59，异常 0 |
| 实机校验 | `python scripts/live_probe.py --port 9990 <路径…>`（复用 Redis 现存会话签发 token） |

三个口径要分清，不要用其中一个去否定另一个：
`endpoint_coverage.py` 按注解统计 Java 侧真实分母（497）；
`gen_inventory.py` 现在只是把同一份统计渲染成表格（以前它自己扫 ruoyi-admin 一个目录，
分母停在 326，漏掉 ruoyi-quartz/ruoyi-generator 与 `GET /{id}` 形态，属于工具缺陷，已修）；
`verify_generated_sql.py` 证明的是“生成的 SQL 在真实库上跑得通”，不等于响应体一致。

### 尚未迁移（64 条，逐条给出障碍）

| 控制器 | 条数 | 障碍 |
|---|---|---|
| GenController | 15 | 28 份 Velocity 模板 + zip 下载；C++ 侧没有模板引擎 |
| SysFileController | 9 | S3/MinIO 上传（SigV4）、`uploadFileEnc` 加解密、bucket 视图 |
| BigScreenController | 8 | carLocation 实时定位、raodTrail 路网最短路、topTen/incomeStatistic 多表统计 |
| CarSuspiciousController | 7 | 逐行二次查询、docx/xlsx 模板导出、外部同步任务与签名校验 |
| CarTrackInfoController | 4 | 轨迹来自外部 HTTP（`httpSysUtilApiService`），非本地库 |
| GeometryController | 3 | GeoServer 外部 HTTP |
| FlowCurrentNodeController | 3 | `saveFlowAuit`/`submitReturn`/`submitEntrustFlow`：多表事务 + 审批人解析 |
| CarConfimFreeController | 3 | 模板导出 + `except/{id}` 组合查询 |
| CarExceptRecordController | 3 | ListNew 是 join 派生查询；import 需 POI |
| CarAduitFreeController | 2 | 模板导出 |
| SysJobController / SysJobLogController | 3 | Quartz：`run` 走反射调 bean、`changeStatus` 需自建 cron 调度器 |
| 其它（earliest-time / tbFlow / busstest / carinfo.import） | 4 | 外部 HTTP、跨租户批量同步、POI 解析 |

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

## 5. 已知行为差异（完整清单见 COMPATIBILITY.md）

- ⚠️ Excel 导出：响应形态与 Java 一致（`data = "<uuid>.xlsx"`），文件内容当前是 CSV。
- ⚠️ 无 zlib 时验证码 PNG 不压缩（约 10KB），解码结果一致。
- ❌ Kafka/CDC、Elasticsearch、MinIO、Quartz 集群锁：C++ 侧无对应实现。
- ❌ 未迁移接口按 §2 表列出，**不会静默返回假数据**（未注册即 404）。
- ✅ 照抄的 Java 缺陷：`GET /base/tollStationIp/list` 因 XML `order by t.big_id`（列不存在）在 Java 侧本来就 500，C++ 保持一致；出处记在 `scripts/verify_generated_sql.py` 的 `EXPECTED_SQL_ERRORS`。

## 6. 下一步（按性价比排序）

1. SysFileController 9：S3 SigV4 上传（HMAC-SHA256 已具备），再做 `uploadFileEnc`。
2. GenController 15：先做只读的 list/db/list/column/getTableDetail，代码生成部分需要一个
   Velocity 等价模板渲染器 + zip（DEFLATE 已在库内，可凑 OOXML/zip 容器）。
3. flow 审批三件套：多表事务，建议先加一个最小的事务包装再逐个实现，比“半个审批流”更安全。
4. quartz：`changeStatus`/`jobLog/clean` 只动库可以先做；`run` 需要 Java 那套反射调 bean 的白名单，
   C++ 侧要么固定任务表 + 函数指针注册，要么明确不做。
5. BigScreen 剩余 8 条里，topTen / incomeStatistic / carVoList 是纯 SQL，可继续按 §2 的方式补；
   carLocation / raodTrail 依赖外部服务，属于 ❌ 类。
6. 真 `.xlsx` 写出器（复用已有 DEFLATE 做 OOXML zip），一次性解掉 6 条模板导出接口的“形态一致、内容不一致”。
