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
| Java 端点注解总数 | **498** |
| C++ 已注册路由（去重 `方法+路径`） | **383**（GET 197 / POST 61 / PUT 58 / DELETE 66） |
| 本轮新增 | base 24 + manager 19 + flow 7 = **50 个实体 × 6 动作 = 300 条** |
| 机器校验 | `python scripts/verify_generated_sql.py --base http://127.0.0.1:9993` → 实体 50，异常 0 |

校验脚本做三件事：把每个实体生成的投影/计数/WHERE SQL **拿到真实 MySQL 上执行**；
把 6 条路由打到运行中的服务上确认**不是 404**；对已知 Java 缺陷给出白名单。

> ⚠️ `ENDPOINTS_INVENTORY.md` 的“Java 326 方法 / 已注册 48”不可用于排期：
> `scripts/gen_inventory.py` 的方法签名正则漏掉了约 144 个 `GET /{id}` 形态端点，
> 也没扫 ruoyi-generator（15）与 ruoyi-quartz（13）。498 是按注解逐条统计的结果
> （排除注释掉的映射与类级 `@RequestMapping`）。

### 尚未迁移

| 区域 | 端点 | 障碍 |
|---|---|---|
| system | user 16、role 8、dept 7、post 5、menu 4、profile 3、indexmenu 5 | 实体与 service 基本齐备，缺控制器接线 |
| quartz | job 8、jobLog 5 | Java 用 Quartz + JDBC JobStore，需自建 cron 调度 |
| generator | gen 15 | 依赖 28 份 Velocity 模板 |
| bigscreen | 12 | 依赖路网最短路/外部地图服务 |
| cdc/kafka | 8 | C++ 无 Kafka 客户端；Java 侧是 Debezium + 死信队列 |
| 生成区域内的非标接口 | `listQuery` / `listAll` / `saveFlowAuit` / `submitReturn` 等 | 生成器只产出 6 个标准动作，这些必须手写；**未伪装成已实现** |

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

## 4. 已知行为差异（完整清单见 COMPATIBILITY.md）

- ⚠️ Excel 导出：响应形态与 Java 一致（`data = "<uuid>.xlsx"`），文件内容当前是 CSV。
- ⚠️ 无 zlib 时验证码 PNG 不压缩（约 10KB），解码结果一致。
- ❌ Kafka/CDC、Elasticsearch、MinIO、Quartz 集群锁：C++ 侧无对应实现。
- ❌ 未迁移接口按 §2 表列出，**不会静默返回假数据**（未注册即 404）。
- ✅ 照抄的 Java 缺陷：`GET /base/tollStationIp/list` 因 XML `order by t.big_id`（列不存在）在 Java 侧本来就 500，C++ 保持一致；出处记在 `scripts/verify_generated_sql.py` 的 `EXPECTED_SQL_ERRORS`。

## 5. 下一步（按性价比排序）

1. system 区域控制器接线（约 48 端点）。
2. 生成区域内非标接口逐个手写。
3. quartz 自建 cron 调度。
4. 真 `.xlsx` 写出器（复用已有 DEFLATE 做 OOXML zip）。
5. 与运行中的 Java 做逐端点差分；**差分脚本必须入库**，不能只留在临时目录。
